#!/usr/bin/env python3
"""/slack/ field notes, batch U - the writing.

Four notes about one WebSocket, separated by which part of its life goes wrong.
All four are Socket Mode notes, which is exactly why each one is pinned to a
different moment and a different number.

The first is a connection that never exists. The value in SLACK_APP_TOKEN is
not an app-level token at all - a bot token in the wrong slot, the same string
pasted into both variables, a value still wearing the quotes it was copied
with - so apps.connections.open is refused before any scope is consulted, the
client retries a permanent fault forever, and the app is deaf from its first
second. The reading is a prefix and a slot, and the workspace-side shape is a
step: silence that starts at a deploy and never lifts.

The second is a connection that exists too many times. Ten is the ceiling, a
reconnect that does not close its predecessor leaves the old registration
standing, and Slack picks one of the registrations per payload. The reading is
arithmetic: replicas times sockets, against ten - and then the observed loss
fraction run backwards to estimate how many of the ten nobody is listening on.
Uniform, unclustered loss, no duplicates.

The third is a connection Slack itself takes away. Every few hours it sends
disconnect with reason refresh_requested, ten seconds after a warning, and a
client that closes before it opens loses whatever arrives in the gap. The
reading is periodicity: misses in tight clusters at a regular multi-hour
interval, which is a different statistic from the second note's even scatter
and the only one of the four that keeps a clock.

The fourth is a connection per replica. Three pods, three sockets, and Slack
routes each payload to one of them without a distribution guarantee - so the
same channel shows duplicates and misses together. The reading is the spacing
between duplicates: sub-second means several pods acted at once, and the
familiar 1, 30, 60 and 300 second spacings mean Slack retried, which is a
different note entirely.

Read only throughout, and more strictly than usual for this section. Nothing
here calls apps.connections.open. That method mints a WebSocket URL: it is a
write, it consumes one of the ten permitted connections, and in the note about
the cap it would be a measurement that changes the thing measured. Every
finding below is reached from an exported manifest, from the deployment's own
declared shape, from log lines the caller supplies, and from
conversations.history - never by opening a socket.
"""

CITE_SOCKET_MODE = ("Using Socket Mode - Slack Docs",
                    "https://docs.slack.dev/apis/events-api/using-socket-mode")
CITE_CONNECTIONS_OPEN = ("apps.connections.open method reference - Slack Docs",
                         "https://docs.slack.dev/reference/methods/"
                         "apps.connections.open")
CITE_CONV_HISTORY = ("conversations.history method reference - Slack Docs",
                     "https://docs.slack.dev/reference/methods/conversations.history")
CITE_AUTH_TEST = ("auth.test method reference - Slack Docs",
                  "https://docs.slack.dev/reference/methods/auth.test")
CITE_TOKENS = ("Token types - Slack Docs",
               "https://docs.slack.dev/authentication/tokens")
CITE_EVENTS_API = ("Events API - Slack Docs", "https://docs.slack.dev/apis/events-api/")
CITE_MANIFEST_EXPORT = ("apps.manifest.export method reference - Slack Docs",
                        "https://docs.slack.dev/reference/methods/apps.manifest.export")
CITE_BOLT_1748 = ("bolt-js #1748: Socket Mode retries a permanent auth failure forever",
                  "https://github.com/slackapi/bolt-js/issues/1748")
CITE_NODE_1495 = ("node-slack-sdk #1495: app-level token errors surface as reconnects",
                  "https://github.com/slackapi/node-slack-sdk/issues/1495")
CITE_PY_1940 = ("python-slack-sdk #1940: too_many_websockets after leaked reconnects",
                "https://github.com/slackapi/python-slack-sdk/issues/1940")
CITE_NODE_1654 = ("node-slack-sdk #1654: old socket not closed before the new one opens",
                  "https://github.com/slackapi/node-slack-sdk/issues/1654")
CITE_NODE_1243 = ("node-slack-sdk #1243: refresh_requested handled as a fatal disconnect",
                  "https://github.com/slackapi/node-slack-sdk/issues/1243")
CITE_BOLT_2496 = ("bolt-js #2496: reconnect drops payloads in the swap window",
                  "https://github.com/slackapi/bolt-js/issues/2496")
CITE_BOLT_2487 = ("bolt-js #2487: multiple instances each receive some of the events",
                  "https://github.com/slackapi/bolt-js/issues/2487")
CITE_BOLT_PY_445 = ("bolt-python #445: scaling Socket Mode horizontally duplicates work",
                    "https://github.com/slackapi/bolt-python/issues/445")

GUIDES = []

GUIDES.append({
"slug": "connections-open-unusable",
"title": "The value in SLACK_APP_TOKEN is not an app-level token",
"description": "apps.connections.open takes one credential class and refuses every other. Classify the token in each slot by prefix, never by opening a connection.",
"h1": "The value in SLACK_APP_TOKEN is not an app-level token",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack not_allowed_token_type apps.connections.open",
             "SLACK_APP_TOKEN xapp prefix",
             "slack socket mode reconnect loop no events",
             "slack app level token wrong app",
             "slack bot token in app token variable"],
"deps": "Python 3.9+ with requests, or Node.js 18+; a bot token with channels:history and channels:read to read the silence, and the environment the app actually runs with",
"lead": "The deploy went out on a Tuesday and the service has been green ever since. The pod is running, the readiness probe passes, the log says <em>connecting to Slack</em> and then says it again a few seconds later, and again, and has been saying it for nine days. Nobody reads that line because nothing about it is an error.</p><p>In the channel, eleven people have typed <code>@releasebot status</code> since Tuesday and none of them has had an answer. The bot has not posted a single message since the deploy. It is not slow, not rate limited and not stuck &mdash; it never opened a connection at all, because the string in <code>SLACK_APP_TOKEN</code> begins with <code>xoxb-</code>.",
"short_answer": """<p><code>apps.connections.open</code> accepts <strong>one</strong> credential class: an app-level token, minted on Basic Information, always prefixed <code>xapp-</code>, always sent in the <code>Authorization</code> header. Hand it a bot token and it answers <code>not_allowed_token_type</code>. Hand it a token from a different app and it answers with an auth mismatch. Hand it nothing usable and no WebSocket is ever minted, so no event is ever delivered, and none of that raises anything your monitoring understands.</p>
<p>You can settle the commonest form of this from the environment alone, with <strong>no call at all</strong>. A Slack credential announces its class in its first characters: <code>xapp-</code> app-level, <code>xoxb-</code> bot, <code>xoxp-</code> user, <code>xoxe-</code> a rotation refresh token. Read what is in each variable, compare it against the class that variable's consumer requires, and the wrong-slot and same-string-in-both cases fall out immediately. Nothing is sent anywhere, so the credential under suspicion is never exercised and no connection is consumed.</p>
<p>The workspace confirms it in a shape no other Socket Mode fault produces: <strong>a step</strong>. Page <code>conversations.history</code> for a channel the bot is in and the app's last message sits just before a deploy, with every mention after it unanswered. Not a fraction of them. All of them, from one timestamp onward, for as long as you look.</p>""",
"problem": """<p>The reason this survives a code review is that every individual piece of it is correct. There is an app-level token in the app configuration. There is a variable called <code>SLACK_APP_TOKEN</code> in the deployment. Somebody filled it in. The failure is a pairing error between two strings that look interchangeable at a glance, and the shell will happily hold either one in either name.</p>
<p>Four shapes account for nearly all of it. The first is the swap: <code>SLACK_BOT_TOKEN</code> and <code>SLACK_APP_TOKEN</code> set from each other, usually while copying a secret block between two environments. The second is the duplicate: the same <code>xoxb-</code> value pasted into both, because somebody was looking for &ldquo;the Slack token&rdquo; and there was only one in the password manager. The third is the quotes: a value copied out of a <code>.env</code> file with its surrounding quotation marks still attached, so the token Slack receives has a literal <code>"</code> at each end and matches nothing. The fourth is the wrong app: two Slack apps exist because Slack has no notion of environments and duplicating the app is the supported way to get one &mdash; and the staging app's <code>xapp-</code> token ends up beside the production app's <code>xoxb-</code>.</p>
<p>What turns a five-minute fix into nine days is the reconnect loop. Socket Mode clients are built to survive network trouble, so a failed connection attempt is retried by design. <code>not_allowed_token_type</code> is not network trouble &mdash; it is a permanent statement about a credential, and it will be true on the ten thousandth attempt too &mdash; but the client cannot tell those apart without special-casing the error, and several of them historically did not. The process therefore stays up, exits nonzero never, and passes every liveness check you have, while doing nothing whatsoever.</p>
<p>And the failure happens <strong>before your application code exists</strong>. There is no handler to instrument, no middleware to log from, no event to trace. The first line of your business logic has never run. That is why the only two places this is visible are the environment your process was handed and the silence in the channel &mdash; and why the check below reads exactly those two things.</p>""",
"why": """<p><strong>The prefix is the class, and the class is the whole question here.</strong> Slack's token types are distinguishable by their first characters by design, which means a script can classify a credential without transmitting it. That matters more than convenience: the audit never sends the suspect value to Slack, never risks a lockout on a bad string, and never touches the connection budget. The check that costs nothing is also the check that cannot do harm.</p>
<p><strong>This is not the missing-scope note, and the difference is which question gets to be asked.</strong> If the token in the slot is a genuine <code>xapp-</code> token belonging to this app, then the question becomes which app-level scopes it was minted with, and that is a different note with a different probe. This note ends where that one begins: it settles the credential's <em>class</em> and <em>slot</em>, and hands over the moment those are right.</p>
<p><strong>The error strings from a real attempt are readable without making one.</strong> Most teams already have the failure in a log. <code>not_allowed_token_type</code> means the wrong class of token. <code>invalid_auth</code> means an app-level token that has been revoked, or an app that was deleted and recreated. An auth mismatch means the token belongs to another app. <code>missing_scope</code> means the class and app are right and the scopes are not. Exactly one of the answers Slack can give here is worth retrying, and it is <code>ratelimited</code>.</p>
<p><strong>Total silence is a different fingerprint from partial loss, and the script insists on the distinction.</strong> A connection that was never opened loses <em>everything</em> from a single timestamp. A leaked connection pool loses a steady fraction. A refresh mishandled loses a cluster every few hours. Several replicas produce duplicates and misses together. Reporting &ldquo;the bot missed some messages&rdquo; is useless; reporting &ldquo;the bot has answered nothing at all since 14:02 on the 9th, across 11 mentions&rdquo; names this note and no other.</p>
<p><strong>The script prints no token, ever.</strong> Not truncated, not masked, not the last four characters. It prints the variable name, the class it detected, and the length. A diagnostic that leaks the credential it is diagnosing into a terminal buffer, a CI log and a screenshot has made the situation worse.</p>
<p><strong>Opening a connection to test the connection is not available to us, and would not help.</strong> <code>apps.connections.open</code> mints a URL and consumes one of the app's ten permitted connections. A read-only audit does not call it, and an audit that did would be answering a question the prefix already answered, at a price.</p>""",
"steps": [
 {"h": "Classify what is in each variable without sending any of it",
  "body": """<p><code>credential_class</code> maps a value to <code>app-level</code>, <code>bot</code>, <code>user</code>, <code>refresh</code>, <code>quoted</code>, <code>absent</code> or <code>unknown</code> from its opening characters. It is a pure function over a string; no request leaves the machine, so the suspect credential is never exercised and no connection is consumed by the act of asking.</p>"""},
 {"h": "Hold each class against the slot it was put in",
  "body": """<p><code>slot_verdict</code> knows that <code>SLACK_APP_TOKEN</code> feeds <code>apps.connections.open</code> and therefore needs an app-level token, and that <code>SLACK_BOT_TOKEN</code> feeds the Web API and needs a bot token. The output is per-variable and names the consumer, because &ldquo;wrong token&rdquo; is unhelpful and &ldquo;this one goes to the WebSocket opener, which takes only <code>xapp-</code>&rdquo; is not.</p>"""},
 {"h": "Check for the same string in two slots",
  "body": """<p><code>duplicate_slots</code> compares the values by identity rather than by class, because two variables holding one <code>xoxb-</code> token is a distinct mistake with a distinct cause &mdash; somebody looked for <em>the</em> Slack token &mdash; and it is worth saying out loud rather than reporting twice as a wrong class.</p>"""},
 {"h": "Read the error you already have in the log",
  "body": """<p><code>open_error</code> turns a logged <code>apps.connections.open</code> failure into a cause and a repair, and marks whether it is worth retrying. Pass it with <code>--logged-error</code>. This is the one place a real attempt informs the check, and the attempt was made by your app rather than by this script.</p>"""},
 {"h": "Confirm the step in the channel",
  "body": """<p><code>silence_profile</code> pages <code>conversations.history</code>, counts mentions of the bot, counts the app's own messages, and returns <code>never-answered</code>, <code>stopped</code> with the timestamp it stopped at, <code>answering</code>, or <code>no-traffic</code>. A step from a single moment, with nothing after it, is this note. A fraction lost is somebody else's.</p>"""},
 {"h": "Make the connection failure fatal",
  "body": """<p>The repair the script prints is two lines of startup code, not a token change: assert the <code>xapp-</code> prefix before constructing the client, and treat a non-<code>ratelimited</code> failure from <code>apps.connections.open</code> as a reason to exit rather than to reconnect. A process that crashes on a permanent credential fault is discovered in minutes; one that retries it is discovered by a customer.</p>"""},
],
"verify": """<p>Fix the variable, redeploy, and run it again against the same channel. The line to watch is the last one: the step should have an end.</p>
<pre><code class="language-bash">python3 slack_socket_credential.py --channel C05REL9QT --logged-error not_allowed_token_type
# identity   U07BOT9QD (releasebot) in Northwind
# slot       SLACK_APP_TOKEN     wrong-class  holds a bot token (56 chars); this variable
#                                feeds apps.connections.open, which takes only xapp-
# slot       SLACK_BOT_TOKEN     ok           holds a bot token (56 chars)
# slot       duplicate           SLACK_APP_TOKEN and SLACK_BOT_TOKEN hold the same string
# logged     wrong-class         not_allowed_token_type: a bot or user token was sent to a
#                                method that accepts only an app-level token. Not a retry
# history    412 message(s) from C05REL9QT
# silence    never-answered      11 mention(s) of U07BOT9QD and 0 reply from the app
# verdict    Socket Mode has never connected with this environment
#   repair: put the xapp- token in SLACK_APP_TOKEN and restart
#   repair: assert the xapp- prefix at startup, and exit rather than reconnect on
#           not_allowed_token_type, invalid_auth or an auth mismatch</code></pre>""",
"code_intro": "Two reads, and neither of them touches the credential under suspicion. <code>credential_class</code> and <code>slot_verdict</code> are pure string work over the environment, which is the point: the app-level token is classified, never transmitted, so the audit costs nothing and consumes none of the app's ten permitted connections. <code>open_error</code> exists so the error already sitting in your log becomes a sentence. <code>silence_profile</code> is the corroboration, and it is written to return a shape rather than a count, because the shape is what tells this note apart from the other three.",
"py_file": "slack_socket_credential.py",
"py": '''"""Decide whether Socket Mode can connect at all, without connecting.

Read only, and deliberately more careful than that. apps.connections.open mints
a WebSocket URL: it is a write, it consumes one of the ten connections an app is
allowed, and this script never calls it. The app-level token is classified from
its first characters and is never sent anywhere, so the value under suspicion is
not exercised by the act of auditing it.

Two GETs are made, both with the bot token: auth.test to learn the app's own
user id, and conversations.history to see whether the workspace has been talking
to a bot that stopped answering. Nothing is written, and no token value is ever
printed - only its variable, its detected class and its length.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_socket_credential")

API = "https://slack.com/api/"

# Longest first, so xoxe.xoxp- is not read as a user token. Slack's token types
# are distinguishable by prefix by design, which is what lets this script answer
# the question without transmitting the credential.
PREFIXES = (
    ("xoxe.xoxp-", "refresh"),
    ("xoxe-", "refresh"),
    ("xapp-", "app-level"),
    ("xoxb-", "bot"),
    ("xoxp-", "user"),
    ("xoxa-", "legacy-workspace"),
    ("xoxr-", "legacy-refresh"),
    ("xoxc-", "browser"),
)

# What each variable's consumer requires. The consumer is named in the output
# because "wrong token" is not a finding and "this one is handed to the method
# that opens the WebSocket" is.
SLOTS = {
    "SLACK_APP_TOKEN": ("app-level", "apps.connections.open, which accepts only an "
                                     "app-level token"),
    "SLACK_BOT_TOKEN": ("bot", "the Web API as your app's bot user"),
    "SLACK_USER_TOKEN": ("user", "the Web API as the installing person"),
}

# One of these is transient. The other five are permanent statements about a
# credential, and a client that reconnects on them will reconnect forever.
OPEN_ERRORS = {
    "not_allowed_token_type": (
        "wrong-class", False,
        "a bot or user token was sent to a method that accepts only an app-level "
        "token. The value in the app token slot is not an xapp- token"),
    "invalid_auth": (
        "dead-credential", False,
        "the app-level token is not valid: revoked from Basic Information, or "
        "belonging to an app that was deleted and recreated"),
    "auth_mismatch": (
        "wrong-app", False,
        "this app-level token was minted by a different app. Duplicating an app is "
        "how Slack does environments, and this is how the halves get crossed"),
    "token_revoked": (
        "dead-credential", False,
        "the token was revoked. Generate a new one and redeploy"),
    "missing_scope": (
        "wrong-scopes", False,
        "the class and the app are right and the scope set is not. That is a "
        "different problem with a different check"),
    "ratelimited": (
        "transient", True,
        "the only answer on this list worth retrying. Back off and try again"),
}


def credential_class(value):
    """What kind of Slack credential is this string? Pure, and offline.

    Returns (klass, detail). Nothing is transmitted: the class is read from the
    prefix, so the token under suspicion is never exercised, never rate limited
    and never able to consume one of the app's ten Socket Mode connections just
    by being checked.

    "quoted" is its own answer because a value copied out of a .env file with
    its quotation marks attached is a real and common failure that would
    otherwise be reported as an unrecognisable string.
    """
    if value is None:
        return ("absent", "the variable is not set at all")
    raw = str(value)
    if not raw.strip():
        return ("absent", "the variable is set to an empty value")
    text = raw.strip()
    if len(text) >= 2 and text[0] in ('"', "'") and text[-1] == text[0]:
        return ("quoted", "the value still carries the quotation marks it was copied "
                          "with, so Slack receives a string that matches no token")
    for prefix, klass in PREFIXES:
        if text.startswith(prefix):
            return (klass, "prefix %s" % prefix)
    return ("unknown", "no recognised Slack token prefix; this is not a Slack "
                       "credential, or it was truncated on the way in")


def slot_verdict(name, value):
    """Does this variable hold the class its consumer requires? Pure.

    Returns (state, detail). States: ok, empty, quoted, wrong-class,
    unrecognised, unknown-slot. The length is reported and the value never is.
    """
    want = SLOTS.get(name)
    klass, why = credential_class(value)
    size = len(str(value or "").strip())
    if want is None:
        return ("unknown-slot", "no requirement is known for %s" % name)
    need, consumer = want
    if klass == "absent":
        return ("empty", "nothing is set, and it is handed to %s" % consumer)
    if klass == "quoted":
        return ("quoted", "%s (%d chars)" % (why, size))
    if klass == "unknown":
        return ("unrecognised", "%s (%d chars)" % (why, size))
    if klass != need:
        return ("wrong-class", "holds a %s token (%d chars); this variable feeds %s"
                % (klass, size, consumer))
    return ("ok", "holds a %s token (%d chars)" % (klass, size))


def duplicate_slots(env):
    """Which variables hold the identical string? Pure.

    Compared by value rather than by class, because one token pasted into two
    variables has a different cause from two wrong tokens - somebody went
    looking for "the Slack token" and there was only one - and saying so is
    more use than reporting the same wrong class twice.
    """
    seen = {}
    for name in sorted(env):
        value = str(env.get(name) or "").strip()
        if not value:
            continue
        seen.setdefault(value, []).append(name)
    return sorted(tuple(names) for names in seen.values() if len(names) > 1)


def open_error(error):
    """Read a logged apps.connections.open failure. Pure, and no call is made.

    Returns (cause, retryable, detail). The script never produces one of these
    errors itself; it reads the one your app already logged, which is the only
    way to have the evidence without minting a connection to get it.
    """
    text = str(error or "").strip()
    if not text:
        return ("unreported", False, "no error was supplied; the environment check "
                                     "above stands on its own")
    if text in OPEN_ERRORS:
        cause, retryable, detail = OPEN_ERRORS[text]
        return (cause, retryable, "%s: %s" % (text, detail))
    return ("unclassified", False, "%s is not one of the documented refusals; read it "
                                   "against the method reference" % text)


def silence_profile(messages, bot_user_id, min_mentions=1):
    """What shape is the app's absence in this channel? Pure.

    Returns (state, detail, counts). The states exist to keep this note apart
    from its neighbours, because every Socket Mode fault looks like "the bot
    missed something" from a distance:

      never-answered  mentions exist and the app has posted nothing at all. A
                      connection that was never opened. This is the note.
      stopped         the app posted, then stopped, and every mention after its
                      last message went unanswered. A step, with a timestamp.
      answering       some mentions after the last app message, some before. A
                      fraction lost is a different failure entirely.
      no-traffic      nobody addressed the bot in this window, so there is
                      nothing to conclude and the script says so.
    """
    mentions, own = [], []
    marker = "<@%s>" % bot_user_id if bot_user_id else None
    for m in messages or []:
        ts = str((m or {}).get("ts") or "")
        if not ts:
            continue
        author = (m or {}).get("user") or ""
        if (bot_user_id and author == bot_user_id) or (m or {}).get("bot_id"):
            own.append(ts)
            continue
        if marker and marker in str((m or {}).get("text") or ""):
            mentions.append(ts)
    counts = {"mentions": len(mentions), "app_messages": len(own)}
    if len(mentions) < max(1, min_mentions):
        return ("no-traffic", "nobody addressed this bot in the messages read, so its "
                              "silence proves nothing", counts)
    if not own:
        return ("never-answered", "%d mention(s) of the bot and not one message from "
                                  "the app. Nothing has ever been delivered to it in "
                                  "this window" % len(mentions), counts)
    last_own = max(float(t) for t in own)
    after = [t for t in mentions if float(t) > last_own]
    counts["mentions_after_last_reply"] = len(after)
    if len(after) >= max(1, min_mentions) and len(after) == len(mentions):
        return ("never-answered", "%d mention(s), all of them after the app's last "
                                  "message at %s" % (len(mentions), min(after)),
                counts)
    if after:
        return ("stopped", "the app last posted at %.0f and %d mention(s) since then "
                           "have gone unanswered" % (last_own, len(after)), counts)
    return ("answering", "the app has replied more recently than the last mention; "
                         "this is not a connection that never opened", counts)


def page_history(session, channel, limit, max_pages):
    """Page conversations.history. A read, and one of two calls made."""
    out, cursor, pages = [], "", 0
    while pages < max_pages:
        params = {"channel": channel, "limit": str(limit)}
        if cursor:
            params["cursor"] = cursor
        body = session.get(API + "conversations.history", params=params,
                           timeout=30).json()
        if body.get("ok") is not True:
            log.error("history    unavailable    %s", body.get("error"))
            return out
        out.extend(body.get("messages") or [])
        cursor = ((body.get("response_metadata") or {}).get("next_cursor") or "")
        pages += 1
        if not cursor:
            break
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN",
                    help="environment variable holding the bot token used to read")
    ap.add_argument("--slots", default="SLACK_APP_TOKEN,SLACK_BOT_TOKEN",
                    help="comma separated variable names to classify")
    ap.add_argument("--logged-error", default="",
                    help="an apps.connections.open error your app already logged")
    ap.add_argument("--channel", default="",
                    help="a channel the bot is in, to confirm the silence")
    ap.add_argument("--limit", type=int, default=200)
    ap.add_argument("--max-pages", type=int, default=3)
    args = ap.parse_args()

    names = [n.strip() for n in args.slots.split(",") if n.strip()]
    env = {n: os.environ.get(n) for n in names}

    faults = 0
    for name in names:
        state, detail = slot_verdict(name, env.get(name))
        line = ("slot       %-19s %-12s %s", name, state, detail)
        if state == "ok":
            log.info(*line)
        else:
            log.warning(*line)
            faults += 1
    for pair in duplicate_slots(env):
        log.warning("slot       duplicate           %s hold the same string",
                    " and ".join(pair))
        faults += 1

    cause, retryable, detail = open_error(args.logged_error)
    if cause != "unreported":
        log.warning("logged     %-19s %s", cause, detail)
        log.info("logged     retryable           %s", "yes" if retryable else "no")
        if not retryable:
            faults += 1

    if args.channel:
        token = os.environ.get(args.token_env)
        if not token:
            log.error("set %s to a bot token with channels:history", args.token_env)
            return 2
        s = requests.Session()
        s.headers.update({"Authorization": "Bearer " + token})
        who = s.get(API + "auth.test", timeout=30).json()
        if who.get("ok") is not True:
            log.error("auth.test  unavailable    %s", who.get("error"))
            return 2
        log.info("identity   %s (%s) in %s", who.get("user_id"), who.get("user"),
                 who.get("team"))
        messages = page_history(s, args.channel, args.limit, args.max_pages)
        log.info("history    %d message(s) from %s", len(messages), args.channel)
        state, detail, counts = silence_profile(messages, who.get("user_id"))
        log.warning("silence    %-19s %s", state, detail)
        log.info("silence    counts              %s", counts)
        if state in ("never-answered", "stopped"):
            faults += 1

    if not faults:
        log.info("verdict    clean               every slot holds the class its "
                 "consumer requires")
        return 0
    log.warning("verdict    Socket Mode cannot connect with this environment")
    log.warning("  repair: put the xapp- token from Basic Information in "
                "SLACK_APP_TOKEN and the xoxb- token in SLACK_BOT_TOKEN, then restart")
    log.warning("  repair: assert the xapp- prefix at startup, and exit rather than "
                "reconnect on not_allowed_token_type, invalid_auth or auth_mismatch")
    log.warning("  note:   no connection was opened to establish this; "
                "apps.connections.open is a write and would consume one of ten")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-socket-credential.mjs",
"js": '''/**
 * Decide whether Socket Mode can connect at all, without connecting.
 *
 * Read only, and deliberately more careful than that. apps.connections.open
 * mints a WebSocket URL: it is a write, it consumes one of the ten connections
 * an app is allowed, and this script never calls it. The app-level token is
 * classified from its first characters and is never sent anywhere.
 *
 * Two GETs, both with the bot token: auth.test for the app's own user id, and
 * conversations.history for the silence. No token value is ever printed.
 */

const API = 'https://slack.com/api/';

// Longest first, so xoxe.xoxp- is not read as a user token.
export const PREFIXES = [
  ['xoxe.xoxp-', 'refresh'],
  ['xoxe-', 'refresh'],
  ['xapp-', 'app-level'],
  ['xoxb-', 'bot'],
  ['xoxp-', 'user'],
  ['xoxa-', 'legacy-workspace'],
  ['xoxr-', 'legacy-refresh'],
  ['xoxc-', 'browser'],
];

// What each variable's consumer requires, named so the output can say which
// method is being handed the wrong thing.
export const SLOTS = {
  SLACK_APP_TOKEN: ['app-level',
    'apps.connections.open, which accepts only an app-level token'],
  SLACK_BOT_TOKEN: ['bot', 'the Web API as your app bot user'],
  SLACK_USER_TOKEN: ['user', 'the Web API as the installing person'],
};

// One of these is transient. The other five are permanent statements about a
// credential, and a client that reconnects on them reconnects forever.
export const OPEN_ERRORS = {
  not_allowed_token_type: ['wrong-class', false,
    'a bot or user token was sent to a method that accepts only an app-level token. '
    + 'The value in the app token slot is not an xapp- token'],
  invalid_auth: ['dead-credential', false,
    'the app-level token is not valid: revoked from Basic Information, or belonging '
    + 'to an app that was deleted and recreated'],
  auth_mismatch: ['wrong-app', false,
    'this app-level token was minted by a different app. Duplicating an app is how '
    + 'Slack does environments, and this is how the halves get crossed'],
  token_revoked: ['dead-credential', false,
    'the token was revoked. Generate a new one and redeploy'],
  missing_scope: ['wrong-scopes', false,
    'the class and the app are right and the scope set is not. That is a different '
    + 'problem with a different check'],
  ratelimited: ['transient', true,
    'the only answer on this list worth retrying. Back off and try again'],
};

/**
 * What kind of Slack credential is this string? Pure, and offline.
 * Returns [klass, detail]. Nothing is transmitted.
 */
export function credentialClass(value) {
  if (value === null || value === undefined) {
    return ['absent', 'the variable is not set at all'];
  }
  const raw = String(value);
  if (!raw.trim()) return ['absent', 'the variable is set to an empty value'];
  const text = raw.trim();
  const first = text[0];
  if (text.length >= 2 && (first === '"' || first === "'") && text.endsWith(first)) {
    return ['quoted', 'the value still carries the quotation marks it was copied with, '
      + 'so Slack receives a string that matches no token'];
  }
  for (const [prefix, klass] of PREFIXES) {
    if (text.startsWith(prefix)) return [klass, `prefix ${prefix}`];
  }
  return ['unknown', 'no recognised Slack token prefix; this is not a Slack credential, '
    + 'or it was truncated on the way in'];
}

/** Does this variable hold the class its consumer requires? Pure. */
export function slotVerdict(name, value) {
  const want = SLOTS[name];
  const [klass, why] = credentialClass(value);
  const size = String(value ?? '').trim().length;
  if (!want) return ['unknown-slot', `no requirement is known for ${name}`];
  const [need, consumer] = want;
  if (klass === 'absent') {
    return ['empty', `nothing is set, and it is handed to ${consumer}`];
  }
  if (klass === 'quoted') return ['quoted', `${why} (${size} chars)`];
  if (klass === 'unknown') return ['unrecognised', `${why} (${size} chars)`];
  if (klass !== need) {
    return ['wrong-class',
      `holds a ${klass} token (${size} chars); this variable feeds ${consumer}`];
  }
  return ['ok', `holds a ${klass} token (${size} chars)`];
}

/** Which variables hold the identical string? Pure. */
export function duplicateSlots(env) {
  const seen = new Map();
  for (const name of Object.keys(env ?? {}).sort()) {
    const value = String(env[name] ?? '').trim();
    if (!value) continue;
    if (!seen.has(value)) seen.set(value, []);
    seen.get(value).push(name);
  }
  return [...seen.values()].filter((names) => names.length > 1);
}

/**
 * Read a logged apps.connections.open failure. Pure, and no call is made.
 * Returns [cause, retryable, detail].
 */
export function openError(error) {
  const text = String(error ?? '').trim();
  if (!text) {
    return ['unreported', false,
      'no error was supplied; the environment check above stands on its own'];
  }
  if (Object.prototype.hasOwnProperty.call(OPEN_ERRORS, text)) {
    const [cause, retryable, detail] = OPEN_ERRORS[text];
    return [cause, retryable, `${text}: ${detail}`];
  }
  return ['unclassified', false,
    `${text} is not one of the documented refusals; read it against the method `
    + 'reference'];
}

/**
 * What shape is the app absence in this channel? Pure.
 * Returns [state, detail, counts]; states never-answered, stopped, answering,
 * no-traffic. The shape is what separates this note from its neighbours.
 */
export function silenceProfile(messages, botUserId, minMentions = 1) {
  const mentions = [];
  const own = [];
  const marker = botUserId ? `<@${botUserId}>` : null;
  for (const m of messages ?? []) {
    const ts = String((m ?? {}).ts ?? '');
    if (!ts) continue;
    const author = (m ?? {}).user ?? '';
    if ((botUserId && author === botUserId) || (m ?? {}).bot_id) {
      own.push(ts);
      continue;
    }
    if (marker && String((m ?? {}).text ?? '').includes(marker)) mentions.push(ts);
  }
  const counts = { mentions: mentions.length, app_messages: own.length };
  const floor = Math.max(1, minMentions);
  if (mentions.length < floor) {
    return ['no-traffic', 'nobody addressed this bot in the messages read, so its '
      + 'silence proves nothing', counts];
  }
  if (!own.length) {
    return ['never-answered', `${mentions.length} mention(s) of the bot and not one `
      + 'message from the app. Nothing has ever been delivered to it in this window',
    counts];
  }
  const lastOwn = Math.max(...own.map(Number));
  const after = mentions.filter((t) => Number(t) > lastOwn);
  counts.mentions_after_last_reply = after.length;
  if (after.length >= floor && after.length === mentions.length) {
    return ['never-answered', `${mentions.length} mention(s), all of them after the `
      + `app last message at ${after.slice().sort()[0]}`, counts];
  }
  if (after.length) {
    return ['stopped', `the app last posted at ${lastOwn.toFixed(0)} and `
      + `${after.length} mention(s) since then have gone unanswered`, counts];
  }
  return ['answering', 'the app has replied more recently than the last mention; this '
    + 'is not a connection that never opened', counts];
}

function arg(args, name, fallback = null) {
  const i = args.indexOf(name);
  return i === -1 ? fallback : args[i + 1];
}

async function pageHistory(headers, channel, limit, maxPages) {
  const out = [];
  let cursor = '';
  for (let page = 0; page < maxPages; page += 1) {
    const params = new URLSearchParams({ channel, limit: String(limit) });
    if (cursor) params.set('cursor', cursor);
    const body = await (await fetch(`${API}conversations.history?${params}`,
      { headers })).json();
    if (body.ok !== true) {
      console.error(`history    unavailable    ${body.error}`);
      return out;
    }
    out.push(...(body.messages ?? []));
    cursor = (body.response_metadata ?? {}).next_cursor ?? '';
    if (!cursor) break;
  }
  return out;
}

async function main() {
  const args = process.argv.slice(2);
  const names = String(arg(args, '--slots', 'SLACK_APP_TOKEN,SLACK_BOT_TOKEN'))
    .split(',').map((n) => n.trim()).filter(Boolean);
  const env = {};
  for (const n of names) env[n] = process.env[n];

  let faults = 0;
  for (const name of names) {
    const [state, detail] = slotVerdict(name, env[name]);
    const line = `slot       ${name.padEnd(19)} ${state.padEnd(12)} ${detail}`;
    if (state === 'ok') console.log(line);
    else { console.warn(line); faults += 1; }
  }
  for (const pair of duplicateSlots(env)) {
    console.warn(`slot       duplicate           ${pair.join(' and ')} hold the same `
      + 'string');
    faults += 1;
  }

  const [cause, retryable, detail] = openError(arg(args, '--logged-error', ''));
  if (cause !== 'unreported') {
    console.warn(`logged     ${cause.padEnd(19)} ${detail}`);
    console.log(`logged     retryable           ${retryable ? 'yes' : 'no'}`);
    if (!retryable) faults += 1;
  }

  const channel = arg(args, '--channel', '');
  if (channel) {
    const tokenEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
    const token = process.env[tokenEnv];
    if (!token) {
      console.error(`set ${tokenEnv} to a bot token with channels:history`);
      process.exitCode = 2;
      return;
    }
    const headers = { Authorization: `Bearer ${token}` };
    const who = await (await fetch(`${API}auth.test`, { headers })).json();
    if (who.ok !== true) {
      console.error(`auth.test  unavailable    ${who.error}`);
      process.exitCode = 2;
      return;
    }
    console.log(`identity   ${who.user_id} (${who.user}) in ${who.team}`);
    const messages = await pageHistory(headers, channel,
      Number(arg(args, '--limit', '200')), Number(arg(args, '--max-pages', '3')));
    console.log(`history    ${messages.length} message(s) from ${channel}`);
    const [state, why, counts] = silenceProfile(messages, who.user_id);
    console.warn(`silence    ${state.padEnd(19)} ${why}`);
    console.log(`silence    counts              ${JSON.stringify(counts)}`);
    if (state === 'never-answered' || state === 'stopped') faults += 1;
  }

  if (!faults) {
    console.log('verdict    clean               every slot holds the class its '
      + 'consumer requires');
    return;
  }
  console.warn('verdict    Socket Mode cannot connect with this environment');
  console.warn('  repair: put the xapp- token from Basic Information in '
    + 'SLACK_APP_TOKEN and the xoxb- token in SLACK_BOT_TOKEN, then restart');
  console.warn('  repair: assert the xapp- prefix at startup, and exit rather than '
    + 'reconnect on not_allowed_token_type, invalid_auth or auth_mismatch');
  console.warn('  note:   no connection was opened to establish this; '
    + 'apps.connections.open is a write and would consume one of ten');
  process.exitCode = 1;
}

// Only run when invoked directly, so importing this module in the tests does
// not execute main() and fail the file on a missing token.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Every fixture token here is obviously fake and shorter than any real one, because a test file is the last place a working credential should end up. The assertions worth reading are the ones about restraint: <code>credential_class</code> is tested for the quoted value and the truncated value, which are the two shapes a prefix check gets wrong if it only looks for <code>xapp-</code>; <code>open_error</code> is tested for the single retryable answer among six; and <code>silence_profile</code> is tested for the case where the bot is still replying, because reporting a step that is not there would send somebody to rotate a token that was never wrong.",
"test_py_file": "test_slack_socket_credential.py",
"test_py": '''from slack_socket_credential import (
    credential_class, duplicate_slots, open_error, silence_profile, slot_verdict,
)

APP = "xapp-1-A-fake"
BOT = "xoxb-fake"
USER = "xoxp-fake"


def test_the_prefix_names_the_class_without_any_call():
    assert credential_class(APP)[0] == "app-level"
    assert credential_class(BOT)[0] == "bot"
    assert credential_class(USER)[0] == "user"


def test_a_rotation_refresh_token_is_not_read_as_a_user_token():
    assert credential_class("xoxe.xoxp-fake")[0] == "refresh"
    assert credential_class("xoxe-fake")[0] == "refresh"


def test_a_value_that_kept_its_quotes_is_its_own_answer():
    klass, detail = credential_class('"xoxb-fake"')
    assert klass == "quoted"
    assert "quotation marks" in detail


def test_an_unset_or_empty_variable_is_absent_rather_than_unknown():
    assert credential_class(None)[0] == "absent"
    assert credential_class("   ")[0] == "absent"


def test_a_truncated_value_is_unknown_and_says_so():
    assert credential_class("1-A-fake")[0] == "unknown"


def test_a_bot_token_in_the_app_slot_is_the_finding():
    state, detail = slot_verdict("SLACK_APP_TOKEN", BOT)
    assert state == "wrong-class"
    assert "apps.connections.open" in detail


def test_the_right_class_in_the_right_slot_passes():
    assert slot_verdict("SLACK_APP_TOKEN", APP)[0] == "ok"
    assert slot_verdict("SLACK_BOT_TOKEN", BOT)[0] == "ok"


def test_the_length_is_reported_and_the_value_is_not():
    _state, detail = slot_verdict("SLACK_BOT_TOKEN", BOT)
    assert str(len(BOT)) in detail
    assert BOT not in detail


def test_an_empty_slot_names_the_consumer_that_will_go_hungry():
    state, detail = slot_verdict("SLACK_APP_TOKEN", "")
    assert state == "empty"
    assert "apps.connections.open" in detail


def test_one_token_in_two_variables_is_reported_once_as_itself():
    assert duplicate_slots({"SLACK_APP_TOKEN": BOT, "SLACK_BOT_TOKEN": BOT}) == [
        ("SLACK_APP_TOKEN", "SLACK_BOT_TOKEN")]


def test_different_tokens_are_not_duplicates_and_blanks_are_ignored():
    assert duplicate_slots({"SLACK_APP_TOKEN": APP, "SLACK_BOT_TOKEN": BOT}) == []
    assert duplicate_slots({"A": "", "B": ""}) == []


def test_the_wrong_token_type_error_is_permanent():
    cause, retryable, _detail = open_error("not_allowed_token_type")
    assert cause == "wrong-class"
    assert retryable is False


def test_a_token_from_another_app_is_named_as_such():
    assert open_error("auth_mismatch")[0] == "wrong-app"


def test_ratelimited_is_the_only_answer_here_worth_retrying():
    assert open_error("ratelimited")[1] is True
    for err in ("not_allowed_token_type", "invalid_auth", "auth_mismatch",
                "missing_scope", "token_revoked"):
        assert open_error(err)[1] is False


def test_a_missing_scope_is_handed_to_the_other_check():
    cause, _retryable, detail = open_error("missing_scope")
    assert cause == "wrong-scopes"
    assert "scope set" in detail


def test_no_logged_error_is_not_a_finding():
    assert open_error("")[0] == "unreported"
    assert open_error(None)[0] == "unreported"


def test_mentions_with_no_reply_at_all_is_the_step_this_note_owns():
    msgs = [{"ts": "10", "user": "U1", "text": "hello <@UBOT>"},
            {"ts": "20", "user": "U2", "text": "<@UBOT> status"}]
    state, detail, counts = silence_profile(msgs, "UBOT")
    assert state == "never-answered"
    assert counts == {"mentions": 2, "app_messages": 0}
    assert "not one message" in detail


def test_a_bot_that_replied_before_the_deploy_and_not_after_is_a_stop():
    msgs = [{"ts": "10", "user": "U1", "text": "<@UBOT> hi"},
            {"ts": "11", "user": "UBOT", "text": "hello"},
            {"ts": "20", "user": "U2", "text": "<@UBOT> status"}]
    assert silence_profile(msgs, "UBOT")[0] == "stopped"


def test_a_bot_that_is_still_answering_is_not_this_note():
    msgs = [{"ts": "10", "user": "U1", "text": "<@UBOT> hi"},
            {"ts": "11", "user": "UBOT", "text": "hello"}]
    assert silence_profile(msgs, "UBOT")[0] == "answering"


def test_a_message_posted_by_a_bot_id_counts_as_the_app_speaking():
    msgs = [{"ts": "10", "user": "U1", "text": "<@UBOT> hi"},
            {"ts": "11", "bot_id": "B1", "text": "hello"}]
    assert silence_profile(msgs, "UBOT")[2]["app_messages"] == 1


def test_a_quiet_channel_proves_nothing_and_says_so():
    assert silence_profile([{"ts": "10", "user": "U1", "text": "morning"}],
                           "UBOT")[0] == "no-traffic"
    assert silence_profile([], "UBOT")[0] == "no-traffic"
''',
"test_js_file": "slack-socket-credential.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  credentialClass, duplicateSlots, openError, silenceProfile, slotVerdict,
} from './slack-socket-credential.mjs';

const APP = 'xapp-1-A-fake';
const BOT = 'xoxb-fake';
const USER = 'xoxp-fake';

test('the prefix names the class without any call', () => {
  assert.equal(credentialClass(APP)[0], 'app-level');
  assert.equal(credentialClass(BOT)[0], 'bot');
  assert.equal(credentialClass(USER)[0], 'user');
});

test('a rotation refresh token is not read as a user token', () => {
  assert.equal(credentialClass('xoxe.xoxp-fake')[0], 'refresh');
  assert.equal(credentialClass('xoxe-fake')[0], 'refresh');
});

test('a value that kept its quotes is its own answer', () => {
  const [klass, detail] = credentialClass('"xoxb-fake"');
  assert.equal(klass, 'quoted');
  assert.match(detail, /quotation marks/);
});

test('an unset or empty variable is absent rather than unknown', () => {
  assert.equal(credentialClass(null)[0], 'absent');
  assert.equal(credentialClass('   ')[0], 'absent');
});

test('a truncated value is unknown and says so', () => {
  assert.equal(credentialClass('1-A-fake')[0], 'unknown');
});

test('a bot token in the app slot is the finding', () => {
  const [state, detail] = slotVerdict('SLACK_APP_TOKEN', BOT);
  assert.equal(state, 'wrong-class');
  assert.match(detail, /apps.connections.open/);
});

test('the right class in the right slot passes', () => {
  assert.equal(slotVerdict('SLACK_APP_TOKEN', APP)[0], 'ok');
  assert.equal(slotVerdict('SLACK_BOT_TOKEN', BOT)[0], 'ok');
});

test('the length is reported and the value is not', () => {
  const [, detail] = slotVerdict('SLACK_BOT_TOKEN', BOT);
  assert.match(detail, new RegExp(String(BOT.length)));
  assert.equal(detail.includes(BOT), false);
});

test('an empty slot names the consumer that will go hungry', () => {
  const [state, detail] = slotVerdict('SLACK_APP_TOKEN', '');
  assert.equal(state, 'empty');
  assert.match(detail, /apps.connections.open/);
});

test('one token in two variables is reported once as itself', () => {
  assert.deepEqual(duplicateSlots({ SLACK_APP_TOKEN: BOT, SLACK_BOT_TOKEN: BOT }),
    [['SLACK_APP_TOKEN', 'SLACK_BOT_TOKEN']]);
});

test('different tokens are not duplicates and blanks are ignored', () => {
  assert.deepEqual(duplicateSlots({ SLACK_APP_TOKEN: APP, SLACK_BOT_TOKEN: BOT }), []);
  assert.deepEqual(duplicateSlots({ A: '', B: '' }), []);
});

test('the wrong token type error is permanent', () => {
  const [cause, retryable] = openError('not_allowed_token_type');
  assert.equal(cause, 'wrong-class');
  assert.equal(retryable, false);
});

test('a token from another app is named as such', () => {
  assert.equal(openError('auth_mismatch')[0], 'wrong-app');
});

test('ratelimited is the only answer here worth retrying', () => {
  assert.equal(openError('ratelimited')[1], true);
  for (const err of ['not_allowed_token_type', 'invalid_auth', 'auth_mismatch',
    'missing_scope', 'token_revoked']) {
    assert.equal(openError(err)[1], false);
  }
});

test('a missing scope is handed to the other check', () => {
  const [cause, , detail] = openError('missing_scope');
  assert.equal(cause, 'wrong-scopes');
  assert.match(detail, /scope set/);
});

test('no logged error is not a finding', () => {
  assert.equal(openError('')[0], 'unreported');
  assert.equal(openError(null)[0], 'unreported');
});

test('mentions with no reply at all is the step this note owns', () => {
  const msgs = [{ ts: '10', user: 'U1', text: 'hello <@UBOT>' },
    { ts: '20', user: 'U2', text: '<@UBOT> status' }];
  const [state, detail, counts] = silenceProfile(msgs, 'UBOT');
  assert.equal(state, 'never-answered');
  assert.deepEqual(counts, { mentions: 2, app_messages: 0 });
  assert.match(detail, /not one message/);
});

test('a bot that replied before the deploy and not after is a stop', () => {
  const msgs = [{ ts: '10', user: 'U1', text: '<@UBOT> hi' },
    { ts: '11', user: 'UBOT', text: 'hello' },
    { ts: '20', user: 'U2', text: '<@UBOT> status' }];
  assert.equal(silenceProfile(msgs, 'UBOT')[0], 'stopped');
});

test('a bot that is still answering is not this note', () => {
  const msgs = [{ ts: '10', user: 'U1', text: '<@UBOT> hi' },
    { ts: '11', user: 'UBOT', text: 'hello' }];
  assert.equal(silenceProfile(msgs, 'UBOT')[0], 'answering');
});

test('a message posted by a bot_id counts as the app speaking', () => {
  const msgs = [{ ts: '10', user: 'U1', text: '<@UBOT> hi' },
    { ts: '11', bot_id: 'B1', text: 'hello' }];
  assert.equal(silenceProfile(msgs, 'UBOT')[2].app_messages, 1);
});

test('a quiet channel proves nothing and says so', () => {
  assert.equal(silenceProfile([{ ts: '10', user: 'U1', text: 'morning' }],
    'UBOT')[0], 'no-traffic');
  assert.equal(silenceProfile([], 'UBOT')[0], 'no-traffic');
});
''',
"faq": [
 ("Why not just call apps.connections.open and read the error?",
  "Because it is a write. The method mints a WebSocket URL, which changes state on Slack's side and consumes one of the ten concurrent connections your app is allowed. On a healthy app that is rude; on an app that is already near the cap it can displace a live connection and cause the outage you were investigating. The prefix in the environment answers the same question for free, and the error you are curious about is almost certainly already in your log, where open_error will read it for you."),
 ("The token starts with xapp- and it still does not connect. Now what?",
  "Then this note is finished and the next question is the scope set. An app-level token is minted per scope on the Basic Information page and cannot be edited afterwards, so a token created for authorizations:read does not carry connections:write. That gap has its own check, which probes the one read method an app-level token can call rather than opening a connection. The note on the underscoped xapp- token is linked below."),
 ("Our health check passes. How can it not be connected?",
  "Because nothing crashed. Socket Mode clients treat a failed connection as something to retry, and a credential error is not distinguishable from a network error without special-casing it. The process is alive, the port is open, the readiness probe answers, and the connection has never been established once. This is why the repair is a startup assertion rather than a monitoring change: the only reliable signal is the one you create yourself, by refusing to boot with a token that cannot possibly work."),
 ("We have two Slack apps, one for staging and one for production. Is that the problem?",
  "It is a very common cause of the wrong-app variant, and it is not a mistake in itself. Slack has no concept of environments, so duplicating the app is the supported way to get one, and the cost is two app ids and two complete sets of credentials that look identical to the eye. When the xapp- token from one app meets the xoxb- token from the other, apps.connections.open answers with an auth mismatch, and everything else about the deployment looks fine. Label the secrets by app id, not by purpose."),
 ("Could the silence in the channel have some other cause?",
  "Yes, and that is why the script reports a shape rather than a number. Total silence from a single timestamp with nothing after it is what a connection that never opened looks like. A steady fraction of unanswered mentions points at leaked connections filling the cap. Losses that cluster every few hours point at a refresh that was not overlapped. Duplicates and misses together point at several replicas each holding a socket. All four are linked from this section, and the script tells you which shape it actually found instead of assuming yours."),
],
"related": [
 ("/slack/app-level-token-missing-connections-write/", "the same token, right class and wrong scopes"),
 ("/slack/not-allowed-token-type/", "the error itself, across the rest of the API"),
 ("/slack/no-event-subscriptions/", "a transport that works and nothing subscribed to it"),
],
"citations": [CITE_CONNECTIONS_OPEN, CITE_TOKENS, CITE_SOCKET_MODE, CITE_BOLT_1748],
})
GUIDES.append({
"slug": "socket-connection-cap",
"title": "too_many_websockets: ten is the ceiling and ghosts fill it",
"description": "Slack allows ten concurrent Socket Mode connections. Count them from the deployment, then run the observed loss fraction backwards to find the leaked ones.",
"h1": "too_many_websockets: ten is the ceiling and ghosts fill it",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack too_many_websockets",
             "slack socket mode 10 connection limit",
             "slack socket mode dropped interactions",
             "slack websocket not closed reconnect leak",
             "slack socket mode intermittent missing events"],
"deps": "Python 3.9+ with requests, or Node.js 18+; a bot token with channels:history, plus the replica count and any disconnect reasons your logs already hold",
"lead": "Roughly three button clicks in four do nothing. Not the same button, not the same person, not the same time of day &mdash; three in four, forever, with no pattern anybody can find. Events mostly work. The handler is never invoked for the ones that vanish, so there is nothing to debug: no error, no timeout, no partial write, just a payload that was never delivered to this process.</p><p>The app runs on a single pod. It has been restarted eleven times this week by a rolling deploy, and each restart opened a new WebSocket without the old one ever being closed on Slack's side. There are now four registrations for one listener, and Slack sends each payload to exactly one of them.",
"short_answer": """<p>An app gets <strong>ten</strong> concurrent Socket Mode connections. That is the whole budget, per app, and it is not per workspace, per replica or per token. Exceed it and the eleventh attempt is refused, the disconnect reason is <code>too_many_websockets</code>, and the connections already registered stay exactly where they are.</p>
<p>The part that produces the symptom is what happens <em>below</em> the cap. Slack routes each payload to <strong>one</strong> of the open connections, so a registration that no process is reading &mdash; a socket left standing by a reconnect that did not close its predecessor, a client behind NAT whose close never reached Slack &mdash; is a hole that swallows its share of the traffic. Three ghosts beside one live socket loses three payloads in four, and nothing anywhere reports a failure.</p>
<p>You cannot count the open connections with a read token, and you must not count them by opening one: <code>apps.connections.open</code> mints a connection, so the measurement would consume the resource being measured and could itself be the eleventh. <strong>Count them from the deployment instead</strong> &mdash; replicas times sockets per replica &mdash; and then run the observed loss fraction backwards. If three quarters of your triggers get no answer and exactly one socket is live, the arithmetic says four registrations exist and three of them are ghosts.</p>""",
"problem": """<p>The loss is uniform, which is why every instinct about it is wrong. There is no bad channel, no bad user, no bad message type, no time of day. Each payload is an independent draw against the same set of registrations, so the failures scatter evenly across everything, and every hypothesis a team forms &mdash; it only fails for long messages, it only fails in the busy channel, it only fails after lunch &mdash; survives about ten minutes of testing before the counter-example arrives.</p>
<p>Interactions feel worse than events even though the loss rate is identical, and the reason is human. A button click has a person standing in front of it who expects something to happen within a second. A missed <code>message</code> event has nobody watching. So the bug is reported as &ldquo;buttons are flaky&rdquo; and diagnosed against the interactivity configuration, which is fine, because the interactivity configuration is not the problem.</p>
<p>The leak itself is unglamorous. A reconnect is supposed to close the old socket and open a new one; several client versions have got the ordering wrong, or have opened the replacement and left the original to time out on Slack's side, or have lost the close frame entirely because the process died before sending it. Every rolling deploy, every OOM kill, every network blip is an opportunity to leave a registration behind, and Slack has no way to know that the process at the other end of a quiet connection has been gone for a day. The registrations accumulate until either the cap refuses a new one or the loss rate becomes unbearable, whichever a human notices first.</p>
<p>Replicas make it arithmetic rather than accidental. Ten is not much: three pods with a client that opens two connections each is six before anything leaks, and a rolling deploy briefly doubles the count while the old pods drain. Teams that reach for horizontal scaling here are usually surprised to learn there is a small integer involved at all, because nothing else in their stack has a ceiling that low.</p>""",
"why": """<p><strong>The cap is unobservable and the consequence is not.</strong> No read method returns the number of open Socket Mode connections. So the check is built out of two things you do have: the shape of the deployment, which you can state exactly, and the fraction of triggers that go unanswered, which the workspace records for you in <code>conversations.history</code>. Neither requires a connection to be opened.</p>
<p><strong>Measuring by opening a socket would be self-defeating twice over.</strong> It consumes one of the ten, so the number it returns is one higher than the number it was asked about; and on an app already at the cap it would be refused, or would displace something live. This is the clearest case in the section for the rule the whole section runs on: the audit must not be capable of causing the incident.</p>
<p><strong>The loss fraction is a measurement of the ghost count, not just a symptom.</strong> If payloads are distributed across N registrations of which L are live, the probability that any given payload is lost is <code>(N - L) / N</code>. Turn that around: given an observed loss fraction <code>f</code> and the number of sockets you believe are live, <code>N = L / (1 - f)</code>. Three quarters lost with one live socket means four registrations; a quarter lost with three live sockets means four as well, and one ghost. That is a number you can hold against ten, and it is the only estimate of the leak available from outside.</p>
<p><strong>Even scatter is the fingerprint, and the script checks for it rather than assuming it.</strong> Losses spread uniformly across the window are consistent with random routing across a leaky set. Losses bunched into a few tight clusters are not &mdash; those are a connection being taken away and replaced badly, which is a different note. The script buckets the window, measures how many buckets contain a miss, and refuses to blame the cap when the misses arrive in a huddle.</p>
<p><strong>No duplicates. That matters as much as the misses.</strong> A leaked connection pool loses payloads; it never delivers one twice, because each payload goes to exactly one registration. If the same channel shows duplicated app responses as well as missing ones, several live listeners are involved and the diagnosis is different. The script says so instead of quietly fitting the evidence to this note.</p>
<p><strong>The disconnect reason, if you have it, is the one piece of direct proof.</strong> <code>too_many_websockets</code> in your own logs is Slack saying the cap was hit. The script takes the reasons you have already collected and reports whether the cap is confirmed or merely implied, because an implied cap and a confirmed one deserve different confidence in the write-up.</p>""",
"steps": [
 {"h": "State the connection budget from the deployment, not from Slack",
  "body": """<p><code>sockets_declared</code> multiplies replicas by sockets per replica and holds the result against the documented ten. It is arithmetic on facts you already know, and it is the only counting method available: there is no read that returns the live connection count, and the write that would is the one this section refuses to call.</p>"""},
 {"h": "Pair every mention with the reply that should have followed it",
  "body": """<p><code>trigger_pairs</code> walks <code>conversations.history</code> and marks each mention of the bot as answered if the app posted anything within <code>--window</code> seconds. <code>loss_fraction</code> reduces that to one number. A window is needed because the app is allowed to be slow; the default is generous on purpose, since counting a slow answer as a loss inflates the ghost estimate.</p>"""},
 {"h": "Check the losses are actually scattered",
  "body": """<p><code>loss_scatter</code> divides the observed window into buckets and reports how many of them contain a miss. Even occupancy is what random routing across a leaky set looks like. A low occupancy means the misses arrived in a huddle, which is a refresh handled badly rather than a cap, and the script hands you to that note instead of proceeding.</p>"""},
 {"h": "Run the loss fraction backwards into a ghost count",
  "body": """<p><code>phantom_estimate</code> takes the loss fraction and the number of sockets you believe are live and returns the implied number of registrations and how many of them nobody is reading. A total loss is refused as out of range: that is a connection that never opened, not a leaked one, and it is a different note.</p>"""},
 {"h": "Say whether the cap is confirmed or only implied",
  "body": """<p><code>cap_evidence</code> reads whatever disconnect reasons you already have and looks for <code>too_many_websockets</code>. Present, and the cap is confirmed by Slack itself. Absent, and the finding is an inference from the arithmetic, which is worth stating as such rather than blurring.</p>"""},
 {"h": "Close before you open, and keep the count small",
  "body": """<p>The repair is one connection per instance and a small number of instances, with the client forced to close the old socket before opening the new one. Ten does not stretch, and Socket Mode does not scale horizontally: if the workload genuinely needs many processing nodes, one receiver that enqueues and many workers that drain is the shape that works, and a public Request URL behind a load balancer is the shape that scales.</p>"""},
],
"verify": """<p>After the SDK upgrade and the replica reduction, re-run against the same channel and the same window. The number that should move is the implied registration count, and it should converge on the number of sockets you actually run.</p>
<pre><code class="language-bash">python3 slack_socket_headroom.py --channel C05OPS9QT --replicas 3 --sockets-per-replica 1 \\
    --reasons too_many_websockets,too_many_websockets
# identity   U07BOT9QD (opsbot) in Northwind
# budget     fine         3 replica(s) x 1 socket = 3 of 10, 7 left before the cap
# triggers   64 mention(s) read, 48 answered within 45s
# loss       0.250        16 of 64 trigger(s) went unanswered
# scatter    scattered    misses touch 83% of the buckets in the window
# phantom    leaked       4.0 registration(s) implied for 3 live socket(s): 1.0 ghost
# cap        confirmed    too_many_websockets appears 2 time(s) in the supplied reasons
# verdict    4.0 of the 10 permitted connection(s) are implied, and 25% of payloads
#            land on one nobody reads
#   repair: force-close the previous socket before opening the replacement
#   repair: one connection per instance, and fewer instances; ten does not stretch
#   note:   nothing here opened a connection to count them; that would consume one</code></pre>""",
"code_intro": "The interesting function is <code>phantom_estimate</code>, and it is four lines of arithmetic. Slack picks one registration per payload, so the loss fraction <em>is</em> the ghost proportion, and inverting it turns an unexplained flakiness rate into a count you can compare with ten. <code>loss_scatter</code> is the guard around it: it refuses to blame the cap when the misses arrive in clusters rather than evenly, because that shape belongs to a different failure. Two GETs, no writes, and nothing that opens a socket.",
"py_file": "slack_socket_headroom.py",
"py": '''"""Estimate how much of your ten-connection Socket Mode budget is wasted.

Read only. Slack does not expose the number of open Socket Mode connections to
any read method, and the method that would tell you - apps.connections.open -
mints a connection: calling it consumes one of the ten and could itself be the
one that trips the cap. So this script never calls it. The count comes from the
deployment you describe on the command line, and the leak comes from arithmetic
on the loss fraction the workspace already recorded.

Two GETs with a bot token: auth.test and conversations.history. No writes.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_socket_headroom")

API = "https://slack.com/api/"

# Documented, per app, and not negotiable. Ten is small enough that a rolling
# deploy over four replicas can breach it without anything having leaked.
CAP = 10


def sockets_declared(replicas, per_replica, cap=CAP):
    """How much of the budget does this deployment ask for? Pure.

    Returns (in_use, cap, left, state). There is no read method that returns
    the live connection count, so this arithmetic on facts you already know is
    the only counting available. States: over, at-the-cap, tight, fine.
    """
    count = max(0, int(replicas or 0)) * max(0, int(per_replica or 0))
    left = cap - count
    if count > cap:
        state = "over"
    elif count == cap:
        state = "at-the-cap"
    elif count >= cap - 2:
        state = "tight"
    else:
        state = "fine"
    return (count, cap, left, state)


def trigger_pairs(messages, bot_user_id, window=45.0):
    """Every mention of the bot, marked answered or not. Pure.

    A mention counts as answered when the app posted anything within `window`
    seconds of it. The window is generous on purpose: counting a slow answer as
    a loss inflates the ghost estimate that the rest of this script builds on
    top of it.

    Returns [(ts, answered), ...] oldest first.
    """
    marker = "<@%s>" % bot_user_id if bot_user_id else None
    own, mentions = [], []
    for m in messages or []:
        ts = str((m or {}).get("ts") or "")
        if not ts:
            continue
        author = (m or {}).get("user") or ""
        if (bot_user_id and author == bot_user_id) or (m or {}).get("bot_id"):
            own.append(float(ts))
        elif marker and marker in str((m or {}).get("text") or ""):
            mentions.append(float(ts))
    own.sort()
    out = []
    for ts in sorted(mentions):
        out.append((ts, any(ts <= o <= ts + float(window) for o in own)))
    return out


def loss_fraction(pairs):
    """What proportion of triggers got no answer? Pure. Returns (missed, total, f)."""
    total = len(pairs or [])
    missed = sum(1 for _ts, ok in pairs or [] if not ok)
    return (missed, total, 0.0 if not total else round(missed / float(total), 3))


def loss_scatter(miss_ts, buckets=12, min_misses=4):
    """Are the misses spread evenly, or bunched? Pure.

    Random routing across a set of registrations loses payloads uniformly, so
    even occupancy is the fingerprint of a leaked pool. Misses that arrive in a
    huddle are a connection being taken away and replaced badly, which is a
    different failure with a different repair, and this function exists so the
    script cannot quietly attribute that shape to the cap.

    Returns (shape, occupancy). Shapes: scattered, clustered, mixed, too-few.
    """
    stamps = sorted(float(t) for t in miss_ts or [])
    if len(stamps) < max(2, min_misses):
        return ("too-few", 0.0)
    span = stamps[-1] - stamps[0]
    if span <= 0:
        return ("clustered", round(1.0 / buckets, 3))
    n = max(2, int(buckets))
    hit = set()
    for t in stamps:
        idx = int((t - stamps[0]) / span * n)
        hit.add(min(idx, n - 1))
    occupancy = round(len(hit) / float(n), 3)
    if occupancy >= 0.5:
        return ("scattered", occupancy)
    if occupancy <= 0.34:
        return ("clustered", occupancy)
    return ("mixed", occupancy)


def phantom_estimate(fraction, live, cap=CAP):
    """Turn an observed loss fraction into a registration count. Pure.

    Slack routes each payload to one of the open connections, so with N
    registrations of which L are read by a process, the chance a payload is
    lost is (N - L) / N. Inverted: N = L / (1 - f). Three quarters of payloads
    lost with one live socket means four registrations and three ghosts; a
    quarter lost with three live sockets means four registrations and one.

    Returns (ghosts, registrations, state). States: none, leaked, over-cap,
    out-of-range.
    """
    f = float(fraction or 0.0)
    listeners = max(0, int(live or 0))
    if listeners <= 0:
        return (0.0, 0.0, "out-of-range")
    if f <= 0:
        return (0.0, float(listeners), "none")
    if f >= 0.999:
        return (0.0, 0.0, "out-of-range")
    registrations = round(listeners / (1.0 - f), 1)
    ghosts = round(registrations - listeners, 1)
    if registrations > cap:
        return (ghosts, registrations, "over-cap")
    return (ghosts, registrations, "leaked" if ghosts >= 0.5 else "none")


def cap_evidence(reasons):
    """Did Slack itself say the cap was hit? Pure. Returns (state, hits).

    too_many_websockets in your own disconnect logs is direct proof. Its
    absence leaves the finding as an inference from arithmetic, and the two
    deserve different confidence in whatever you write up afterwards.
    """
    hits = sum(1 for r in reasons or [] if str(r or "").strip() == "too_many_websockets")
    return (("confirmed" if hits else "implied"), hits)


def page_history(session, channel, limit, max_pages):
    """Page conversations.history. A read, and one of two calls made."""
    out, cursor, pages = [], "", 0
    while pages < max_pages:
        params = {"channel": channel, "limit": str(limit)}
        if cursor:
            params["cursor"] = cursor
        body = session.get(API + "conversations.history", params=params,
                           timeout=30).json()
        if body.get("ok") is not True:
            log.error("history    unavailable    %s", body.get("error"))
            return out
        out.extend(body.get("messages") or [])
        cursor = ((body.get("response_metadata") or {}).get("next_cursor") or "")
        pages += 1
        if not cursor:
            break
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN")
    ap.add_argument("--channel", required=True,
                    help="a channel the bot answers in")
    ap.add_argument("--replicas", type=int, default=1)
    ap.add_argument("--sockets-per-replica", type=int, default=1)
    ap.add_argument("--window", type=float, default=45.0,
                    help="seconds an answer is allowed to take")
    ap.add_argument("--reasons", default="",
                    help="comma separated disconnect reasons from your own logs")
    ap.add_argument("--limit", type=int, default=200)
    ap.add_argument("--max-pages", type=int, default=5)
    args = ap.parse_args()

    token = os.environ.get(args.token_env)
    if not token:
        log.error("set %s to a bot token with channels:history", args.token_env)
        return 2
    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + token})
    who = s.get(API + "auth.test", timeout=30).json()
    if who.get("ok") is not True:
        log.error("auth.test  unavailable    %s", who.get("error"))
        return 2
    log.info("identity   %s (%s) in %s", who.get("user_id"), who.get("user"),
             who.get("team"))

    live, cap, left, budget = sockets_declared(args.replicas, args.sockets_per_replica)
    log.info("budget     %-12s %d replica(s) x %d socket = %d of %d, %d left before "
             "the cap", budget, args.replicas, args.sockets_per_replica, live, cap,
             left)

    messages = page_history(s, args.channel, args.limit, args.max_pages)
    pairs = trigger_pairs(messages, who.get("user_id"), args.window)
    missed, total, fraction = loss_fraction(pairs)
    log.info("triggers   %d mention(s) read, %d answered within %.0fs",
             total, total - missed, args.window)
    if not total:
        log.info("verdict    nothing to measure; this channel has no mentions in the "
                 "window read")
        return 0
    log.info("loss       %-12.3f %d of %d trigger(s) went unanswered", fraction,
             missed, total)

    shape, occupancy = loss_scatter([ts for ts, ok in pairs if not ok])
    log.info("scatter    %-12s misses touch %.0f%% of the buckets in the window",
             shape, occupancy * 100)
    if shape == "clustered":
        log.warning("verdict    the misses are bunched rather than spread, which is "
                    "not what a leaked connection pool looks like")
        log.warning("  next:   read the note on refresh_requested disconnects; "
                    "periodic clusters are a swap that was not overlapped")
        return 1

    ghosts, registrations, state = phantom_estimate(fraction, live)
    if state == "out-of-range":
        log.warning("phantom    out-of-range the loss is total or the live count is "
                    "zero; that is a connection that never opened, not a leaked one")
        return 1
    log.info("phantom    %-12s %.1f registration(s) implied for %d live socket(s): "
             "%.1f ghost", state, registrations, live, ghosts)

    evidence, hits = cap_evidence([r.strip() for r in args.reasons.split(",")])
    log.info("cap        %-12s too_many_websockets appears %d time(s) in the supplied "
             "reasons", evidence, hits)

    if state == "none" and budget in ("fine", "tight"):
        log.info("verdict    clean        the budget fits and the loss does not imply "
                 "a leak")
        return 0
    log.warning("verdict    %.1f of the %d permitted connection(s) are implied, and "
                "%.0f%% of payloads land on one nobody reads", registrations, cap,
                fraction * 100)
    log.warning("  repair: force-close the previous socket before opening the "
                "replacement, and upgrade past the known close-path regressions")
    log.warning("  repair: one connection per instance and fewer instances; for real "
                "horizontal scale use the HTTP Events API behind a load balancer")
    log.warning("  note:   nothing here opened a connection to count them; doing so "
                "would consume one of the ten it is trying to measure")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-socket-headroom.mjs",
"js": '''/**
 * Estimate how much of your ten-connection Socket Mode budget is wasted.
 *
 * Read only. Slack exposes no read method for the number of open Socket Mode
 * connections, and the method that would tell you - apps.connections.open -
 * mints one: calling it consumes part of the budget it is measuring and could
 * itself trip the cap. So this script never calls it. The count comes from the
 * deployment you describe, the leak from arithmetic on the observed losses.
 */

const API = 'https://slack.com/api/';

// Documented, per app, and not negotiable.
export const CAP = 10;

/**
 * How much of the budget does this deployment ask for? Pure.
 * Returns [inUse, cap, left, state]; states over, at-the-cap, tight, fine.
 */
export function socketsDeclared(replicas, perReplica, cap = CAP) {
  const count = Math.max(0, Number(replicas) || 0) * Math.max(0, Number(perReplica) || 0);
  const left = cap - count;
  let state = 'fine';
  if (count > cap) state = 'over';
  else if (count === cap) state = 'at-the-cap';
  else if (count >= cap - 2) state = 'tight';
  return [count, cap, left, state];
}

/**
 * Every mention of the bot, marked answered or not. Pure.
 * The window is generous on purpose: a slow answer counted as a loss inflates
 * the ghost estimate built on top of it. Returns [[ts, answered], ...].
 */
export function triggerPairs(messages, botUserId, window = 45) {
  const marker = botUserId ? `<@${botUserId}>` : null;
  const own = [];
  const mentions = [];
  for (const m of messages ?? []) {
    const ts = String((m ?? {}).ts ?? '');
    if (!ts) continue;
    const author = (m ?? {}).user ?? '';
    if ((botUserId && author === botUserId) || (m ?? {}).bot_id) own.push(Number(ts));
    else if (marker && String((m ?? {}).text ?? '').includes(marker)) {
      mentions.push(Number(ts));
    }
  }
  own.sort((a, b) => a - b);
  return mentions.sort((a, b) => a - b)
    .map((ts) => [ts, own.some((o) => o >= ts && o <= ts + Number(window))]);
}

/** What proportion of triggers got no answer? Pure. [missed, total, f]. */
export function lossFraction(pairs) {
  const rows = pairs ?? [];
  const total = rows.length;
  const missed = rows.filter(([, ok]) => !ok).length;
  const f = total ? Math.round((missed / total) * 1000) / 1000 : 0;
  return [missed, total, f];
}

/**
 * Are the misses spread evenly, or bunched? Pure.
 * Random routing across registrations loses payloads uniformly, so even
 * occupancy is the fingerprint of a leaked pool. A huddle is a connection
 * replaced badly, which is a different note. Returns [shape, occupancy].
 */
export function lossScatter(missTs, buckets = 12, minMisses = 4) {
  const stamps = (missTs ?? []).map(Number).sort((a, b) => a - b);
  if (stamps.length < Math.max(2, minMisses)) return ['too-few', 0];
  const span = stamps[stamps.length - 1] - stamps[0];
  if (span <= 0) return ['clustered', Math.round((1000 / buckets)) / 1000];
  const n = Math.max(2, Math.trunc(buckets));
  const hit = new Set();
  for (const t of stamps) {
    hit.add(Math.min(Math.trunc(((t - stamps[0]) / span) * n), n - 1));
  }
  const occupancy = Math.round((hit.size / n) * 1000) / 1000;
  if (occupancy >= 0.5) return ['scattered', occupancy];
  if (occupancy <= 0.34) return ['clustered', occupancy];
  return ['mixed', occupancy];
}

/**
 * Turn an observed loss fraction into a registration count. Pure.
 * With N registrations of which L are read, loss = (N - L) / N, so
 * N = L / (1 - f). Returns [ghosts, registrations, state].
 */
export function phantomEstimate(fraction, live, cap = CAP) {
  const f = Number(fraction) || 0;
  const listeners = Math.max(0, Number(live) || 0);
  if (listeners <= 0) return [0, 0, 'out-of-range'];
  if (f <= 0) return [0, listeners, 'none'];
  if (f >= 0.999) return [0, 0, 'out-of-range'];
  const registrations = Math.round((listeners / (1 - f)) * 10) / 10;
  const ghosts = Math.round((registrations - listeners) * 10) / 10;
  if (registrations > cap) return [ghosts, registrations, 'over-cap'];
  return [ghosts, registrations, ghosts >= 0.5 ? 'leaked' : 'none'];
}

/** Did Slack itself say the cap was hit? Pure. Returns [state, hits]. */
export function capEvidence(reasons) {
  const hits = (reasons ?? [])
    .filter((r) => String(r ?? '').trim() === 'too_many_websockets').length;
  return [hits ? 'confirmed' : 'implied', hits];
}

function arg(args, name, fallback = null) {
  const i = args.indexOf(name);
  return i === -1 ? fallback : args[i + 1];
}

async function pageHistory(headers, channel, limit, maxPages) {
  const out = [];
  let cursor = '';
  for (let page = 0; page < maxPages; page += 1) {
    const params = new URLSearchParams({ channel, limit: String(limit) });
    if (cursor) params.set('cursor', cursor);
    const body = await (await fetch(`${API}conversations.history?${params}`,
      { headers })).json();
    if (body.ok !== true) {
      console.error(`history    unavailable    ${body.error}`);
      return out;
    }
    out.push(...(body.messages ?? []));
    cursor = (body.response_metadata ?? {}).next_cursor ?? '';
    if (!cursor) break;
  }
  return out;
}

async function main() {
  const args = process.argv.slice(2);
  const tokenEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
  const token = process.env[tokenEnv];
  const channel = arg(args, '--channel', '');
  if (!token || !channel) {
    console.error(`set ${tokenEnv} to a bot token with channels:history, and pass `
      + '--channel');
    process.exitCode = 2;
    return;
  }
  const headers = { Authorization: `Bearer ${token}` };
  const who = await (await fetch(`${API}auth.test`, { headers })).json();
  if (who.ok !== true) {
    console.error(`auth.test  unavailable    ${who.error}`);
    process.exitCode = 2;
    return;
  }
  console.log(`identity   ${who.user_id} (${who.user}) in ${who.team}`);

  const replicas = Number(arg(args, '--replicas', '1'));
  const perReplica = Number(arg(args, '--sockets-per-replica', '1'));
  const window = Number(arg(args, '--window', '45'));
  const [live, cap, left, budget] = socketsDeclared(replicas, perReplica);
  console.log(`budget     ${budget.padEnd(12)} ${replicas} replica(s) x ${perReplica} `
    + `socket = ${live} of ${cap}, ${left} left before the cap`);

  const messages = await pageHistory(headers, channel,
    Number(arg(args, '--limit', '200')), Number(arg(args, '--max-pages', '5')));
  const pairs = triggerPairs(messages, who.user_id, window);
  const [missed, total, fraction] = lossFraction(pairs);
  console.log(`triggers   ${total} mention(s) read, ${total - missed} answered within `
    + `${window}s`);
  if (!total) {
    console.log('verdict    nothing to measure; this channel has no mentions in the '
      + 'window read');
    return;
  }
  console.log(`loss       ${String(fraction).padEnd(12)} ${missed} of ${total} `
    + 'trigger(s) went unanswered');

  const [shape, occupancy] = lossScatter(pairs.filter(([, ok]) => !ok).map(([ts]) => ts));
  console.log(`scatter    ${shape.padEnd(12)} misses touch `
    + `${Math.round(occupancy * 100)}% of the buckets in the window`);
  if (shape === 'clustered') {
    console.warn('verdict    the misses are bunched rather than spread, which is not '
      + 'what a leaked connection pool looks like');
    console.warn('  next:   read the note on refresh_requested disconnects; periodic '
      + 'clusters are a swap that was not overlapped');
    process.exitCode = 1;
    return;
  }

  const [ghosts, registrations, state] = phantomEstimate(fraction, live);
  if (state === 'out-of-range') {
    console.warn('phantom    out-of-range the loss is total or the live count is zero; '
      + 'that is a connection that never opened, not a leaked one');
    process.exitCode = 1;
    return;
  }
  console.log(`phantom    ${state.padEnd(12)} ${registrations} registration(s) implied `
    + `for ${live} live socket(s): ${ghosts} ghost`);

  const [evidence, hits] = capEvidence(String(arg(args, '--reasons', '')).split(','));
  console.log(`cap        ${evidence.padEnd(12)} too_many_websockets appears ${hits} `
    + 'time(s) in the supplied reasons');

  if (state === 'none' && (budget === 'fine' || budget === 'tight')) {
    console.log('verdict    clean        the budget fits and the loss does not imply a '
      + 'leak');
    return;
  }
  console.warn(`verdict    ${registrations} of the ${cap} permitted connection(s) are `
    + `implied, and ${Math.round(fraction * 100)}% of payloads land on one nobody reads`);
  console.warn('  repair: force-close the previous socket before opening the '
    + 'replacement, and upgrade past the known close-path regressions');
  console.warn('  repair: one connection per instance and fewer instances; for real '
    + 'horizontal scale use the HTTP Events API behind a load balancer');
  console.warn('  note:   nothing here opened a connection to count them; doing so '
    + 'would consume one of the ten it is trying to measure');
  process.exitCode = 1;
}

// Only run when invoked directly, so importing this module in the tests does
// not execute main() and fail the file on a missing token.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The arithmetic gets the attention it deserves: a quarter lost with one live socket must come out as four registrations and three ghosts, and a loss of zero must come out as no leak rather than as a rounding artefact. Beyond that the tests are mostly about refusals. <code>phantom_estimate</code> refuses a total loss, because that is a connection that never opened and belongs to another note. <code>loss_scatter</code> refuses to call a huddle of misses scattered. And <code>cap_evidence</code> keeps <em>Slack said so</em> and <em>we worked it out</em> in separate words, because those are not the same claim.",
"test_py_file": "test_slack_socket_headroom.py",
"test_py": '''from slack_socket_headroom import (
    CAP, cap_evidence, loss_fraction, loss_scatter, phantom_estimate,
    sockets_declared, trigger_pairs,
)


def test_the_documented_ceiling_is_ten():
    assert CAP == 10


def test_the_budget_is_replicas_times_sockets():
    assert sockets_declared(3, 1)[:3] == (3, 10, 7)
    assert sockets_declared(3, 2)[0] == 6


def test_more_than_ten_is_over_and_exactly_ten_is_at_the_cap():
    assert sockets_declared(11, 1)[3] == "over"
    assert sockets_declared(5, 2)[3] == "at-the-cap"


def test_eight_of_ten_is_called_tight_rather_than_fine():
    assert sockets_declared(8, 1)[3] == "tight"
    assert sockets_declared(2, 1)[3] == "fine"


def test_a_mention_answered_inside_the_window_is_not_a_loss():
    msgs = [{"ts": "100", "user": "U1", "text": "<@UBOT> go"},
            {"ts": "110", "user": "UBOT", "text": "on it"}]
    assert trigger_pairs(msgs, "UBOT", 45) == [(100.0, True)]


def test_an_answer_after_the_window_is_a_loss():
    msgs = [{"ts": "100", "user": "U1", "text": "<@UBOT> go"},
            {"ts": "500", "user": "UBOT", "text": "on it"}]
    assert trigger_pairs(msgs, "UBOT", 45) == [(100.0, False)]


def test_an_earlier_bot_message_does_not_answer_a_later_mention():
    msgs = [{"ts": "90", "user": "UBOT", "text": "morning"},
            {"ts": "100", "user": "U1", "text": "<@UBOT> go"}]
    assert trigger_pairs(msgs, "UBOT", 45) == [(100.0, False)]


def test_the_loss_fraction_is_missed_over_total():
    assert loss_fraction([(1, True), (2, False), (3, True), (4, False)]) == (2, 4, 0.5)
    assert loss_fraction([]) == (0, 0, 0.0)


def test_three_quarters_lost_with_one_live_socket_implies_four_registrations():
    ghosts, registrations, state = phantom_estimate(0.75, 1)
    assert (ghosts, registrations) == (3.0, 4.0)
    assert state == "leaked"


def test_a_quarter_lost_with_three_live_sockets_implies_one_ghost():
    ghosts, registrations, _state = phantom_estimate(0.25, 3)
    assert (ghosts, registrations) == (1.0, 4.0)


def test_an_implied_count_above_ten_is_flagged_against_the_cap():
    assert phantom_estimate(0.5, 6)[2] == "over-cap"


def test_no_loss_means_no_ghosts():
    assert phantom_estimate(0.0, 3) == (0.0, 3.0, "none")


def test_a_total_loss_is_out_of_range_because_it_is_a_different_note():
    assert phantom_estimate(1.0, 3)[2] == "out-of-range"
    assert phantom_estimate(0.25, 0)[2] == "out-of-range"


def test_misses_spread_across_the_window_are_scattered():
    shape, occupancy = loss_scatter([0, 100, 200, 300, 400, 500, 600, 700])
    assert shape == "scattered"
    assert occupancy >= 0.5


def test_misses_in_one_huddle_are_clustered_and_belong_elsewhere():
    assert loss_scatter([0, 1, 2, 3, 4, 5, 1000])[0] == "clustered"


def test_too_few_misses_to_judge_says_so_rather_than_guessing():
    assert loss_scatter([1, 2])[0] == "too-few"
    assert loss_scatter([])[0] == "too-few"


def test_identical_timestamps_are_a_huddle_and_not_a_spread():
    assert loss_scatter([5, 5, 5, 5])[0] == "clustered"


def test_slack_saying_too_many_websockets_is_confirmation():
    assert cap_evidence(["too_many_websockets", "refresh_requested"]) == ("confirmed", 1)


def test_without_that_reason_the_finding_is_only_implied():
    assert cap_evidence(["refresh_requested"]) == ("implied", 0)
    assert cap_evidence([]) == ("implied", 0)
''',
"test_js_file": "slack-socket-headroom.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  CAP, capEvidence, lossFraction, lossScatter, phantomEstimate, socketsDeclared,
  triggerPairs,
} from './slack-socket-headroom.mjs';

test('the documented ceiling is ten', () => {
  assert.equal(CAP, 10);
});

test('the budget is replicas times sockets', () => {
  assert.deepEqual(socketsDeclared(3, 1).slice(0, 3), [3, 10, 7]);
  assert.equal(socketsDeclared(3, 2)[0], 6);
});

test('more than ten is over and exactly ten is at the cap', () => {
  assert.equal(socketsDeclared(11, 1)[3], 'over');
  assert.equal(socketsDeclared(5, 2)[3], 'at-the-cap');
});

test('eight of ten is called tight rather than fine', () => {
  assert.equal(socketsDeclared(8, 1)[3], 'tight');
  assert.equal(socketsDeclared(2, 1)[3], 'fine');
});

test('a mention answered inside the window is not a loss', () => {
  const msgs = [{ ts: '100', user: 'U1', text: '<@UBOT> go' },
    { ts: '110', user: 'UBOT', text: 'on it' }];
  assert.deepEqual(triggerPairs(msgs, 'UBOT', 45), [[100, true]]);
});

test('an answer after the window is a loss', () => {
  const msgs = [{ ts: '100', user: 'U1', text: '<@UBOT> go' },
    { ts: '500', user: 'UBOT', text: 'on it' }];
  assert.deepEqual(triggerPairs(msgs, 'UBOT', 45), [[100, false]]);
});

test('an earlier bot message does not answer a later mention', () => {
  const msgs = [{ ts: '90', user: 'UBOT', text: 'morning' },
    { ts: '100', user: 'U1', text: '<@UBOT> go' }];
  assert.deepEqual(triggerPairs(msgs, 'UBOT', 45), [[100, false]]);
});

test('the loss fraction is missed over total', () => {
  assert.deepEqual(lossFraction([[1, true], [2, false], [3, true], [4, false]]),
    [2, 4, 0.5]);
  assert.deepEqual(lossFraction([]), [0, 0, 0]);
});

test('three quarters lost with one live socket implies four registrations', () => {
  const [ghosts, registrations, state] = phantomEstimate(0.75, 1);
  assert.deepEqual([ghosts, registrations], [3, 4]);
  assert.equal(state, 'leaked');
});

test('a quarter lost with three live sockets implies one ghost', () => {
  const [ghosts, registrations] = phantomEstimate(0.25, 3);
  assert.deepEqual([ghosts, registrations], [1, 4]);
});

test('an implied count above ten is flagged against the cap', () => {
  assert.equal(phantomEstimate(0.5, 6)[2], 'over-cap');
});

test('no loss means no ghosts', () => {
  assert.deepEqual(phantomEstimate(0, 3), [0, 3, 'none']);
});

test('a total loss is out of range because it is a different note', () => {
  assert.equal(phantomEstimate(1, 3)[2], 'out-of-range');
  assert.equal(phantomEstimate(0.25, 0)[2], 'out-of-range');
});

test('misses spread across the window are scattered', () => {
  const [shape, occupancy] = lossScatter([0, 100, 200, 300, 400, 500, 600, 700]);
  assert.equal(shape, 'scattered');
  assert.ok(occupancy >= 0.5);
});

test('misses in one huddle are clustered and belong elsewhere', () => {
  assert.equal(lossScatter([0, 1, 2, 3, 4, 5, 1000])[0], 'clustered');
});

test('too few misses to judge says so rather than guessing', () => {
  assert.equal(lossScatter([1, 2])[0], 'too-few');
  assert.equal(lossScatter([])[0], 'too-few');
});

test('identical timestamps are a huddle and not a spread', () => {
  assert.equal(lossScatter([5, 5, 5, 5])[0], 'clustered');
});

test('Slack saying too_many_websockets is confirmation', () => {
  assert.deepEqual(capEvidence(['too_many_websockets', 'refresh_requested']),
    ['confirmed', 1]);
});

test('without that reason the finding is only implied', () => {
  assert.deepEqual(capEvidence(['refresh_requested']), ['implied', 0]);
  assert.deepEqual(capEvidence([]), ['implied', 0]);
});
''',
"faq": [
 ("Can I just count the open connections?",
  "Not from outside. No read method returns the live Socket Mode connection count, and the only method that touches connections at all is apps.connections.open, which mints one. Calling it to count would add to the number it was asked about, and on an app already at ten it would either be refused or displace something live. The two available substitutes are the deployment's own arithmetic and the loss fraction the workspace recorded, which is what this script uses."),
 ("Where does the ghost estimate come from?",
  "From the routing rule. Slack sends each payload to one of the open connections, so if N registrations exist and only L of them are attached to a running process, the chance any payload is lost is (N minus L) over N. Observe the loss fraction f and you can invert it: N equals L over (1 minus f). Three quarters lost with one live socket means four registrations, three of them ghosts; a quarter lost with three live sockets means four registrations and one ghost. It is an estimate, not a measurement, and it is the only number of its kind available without opening a connection."),
 ("We run one pod. How can we be near a limit of ten?",
  "Because registrations outlive processes. A reconnect that opens the replacement before closing the original, a pod killed before its close frame is sent, a NAT timeout that leaves Slack believing a socket is still there: each of those leaves a registration standing that nothing will ever read. Eleven restarts in a week on a client with a broken close path is enough to fill most of the budget on its own, and Slack has no way to know the far end is gone."),
 ("Why does the script refuse to conclude anything when the misses are clustered?",
  "Because clustered misses are somebody else's failure. A leaked connection pool loses payloads at random, so the misses spread evenly across whatever window you look at. Losses that arrive in a few tight bunches, especially at a regular interval, are a connection being taken away and replaced without overlap, which is the refresh_requested note. Fitting that evidence to the cap would produce a confident, wrong ghost count and send somebody to upgrade an SDK that was fine."),
 ("Would moving to the HTTP Events API fix this?",
  "It removes the ceiling, yes, because HTTP delivery scales with your load balancer rather than with a per-app connection budget. It also costs you the reason most teams chose Socket Mode: no public endpoint, no URL verification, nothing to expose from behind a firewall. The cheaper repair is usually to keep Socket Mode with one connection per instance and a small instance count, and to put concurrency behind the receiver in a queue you control."),
],
"related": [
 ("/slack/rtm-legacy-still-used/", "the transport Socket Mode replaced, and its own limits"),
 ("/slack/three-second-timeout/", "the other deadline that silently drops work"),
 ("/slack/retry-storm-from-event-retries/", "what happens when the misses turn into repeats"),
],
"citations": [CITE_SOCKET_MODE, CITE_PY_1940, CITE_NODE_1654, CITE_CONV_HISTORY],
})
GUIDES.append({
"slug": "refresh-requested-unhandled",
"title": "refresh_requested: Slack takes the socket back every few hours",
"description": "Socket Mode connections are refreshed on a schedule. A client that closes before it opens loses whatever arrives in the gap, in clusters you can time.",
"h1": "refresh_requested: Slack takes the socket back every few hours",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack refresh_requested disconnect",
             "slack socket mode reconnect every few hours",
             "slack link_disabled socket mode",
             "slack socket mode missed events after reconnect",
             "slack socket mode disconnect warning 10 seconds"],
"deps": "Python 3.9+ with requests, or Node.js 18+; a bot token with channels:history, and the disconnect reasons your client already logs",
"lead": "The dashboard has a sawtooth in it. Every few hours the bot's response count drops to nothing for about forty seconds and then recovers on its own, and because it recovers on its own nobody has ever opened a ticket. The supervisor restarts the process, the restart is logged as normal, and the four or five messages that arrived during the restart are simply not in the app's database.</p><p>Slack did that on purpose. It sends a <code>disconnect</code> message with <code>reason: &quot;refresh_requested&quot;</code>, warns you about ten seconds beforehand so you can have a replacement connection ready, and expects you to overlap the two. A client that treats the disconnect as an error, or that closes the old socket before opening the new one, drops everything that arrives in the seam.",
"short_answer": """<p>Socket Mode connections are not meant to be permanent. Slack refreshes them every few hours by sending a <code>disconnect</code> frame with <code>reason: "refresh_requested"</code>, preceded by a <code>warning</code> roughly ten seconds earlier. That warning exists for exactly one purpose: <strong>open the replacement connection first, and close the old one only once the new one has received <code>hello</code></strong>. Overlap, do not swap.</p>
<p>Two things go wrong. A client that treats any disconnect as a fault dies and is restarted, losing everything that arrives during the restart. A client that reconnects politely but serially &mdash; close, then open &mdash; loses whatever arrives in between, which is shorter and just as invisible. Both produce the same workspace-side signature and neither logs anything an operator would read as a problem.</p>
<p><strong>The signature is periodicity, and that is what distinguishes this from every other Socket Mode fault.</strong> Group the unanswered mentions into clusters, take the interval between cluster starts, and measure how regular it is. A leaked connection pool loses payloads uniformly at random. This loses them in tight bunches, a few tens of seconds wide, arriving on a clock. <code>link_disabled</code>, the other documented reason, is the opposite: it never recovers, because Socket Mode was switched off in the app configuration and reconnecting will not bring it back.</p>""",
"problem": """<p>What makes this expensive is that it self-heals. Every symptom disappears before anyone can look at it. The process comes back, the connection re-establishes, the queue drains, and the graph returns to normal, so the incident never becomes an incident &mdash; it becomes a shrug. Meanwhile the messages that landed in the seam are gone for good: Socket Mode has no redelivery, no acknowledgement window, and no replay. A payload sent to a connection that is closing is not resent to the one that opens next.</p>
<p>The clue everybody misses is the warning frame. Slack tells you ten seconds in advance, which is a strange thing to do unless the client is expected to act on it, and most hand-rolled Socket Mode implementations ignore it entirely. They handle <code>events_api</code> messages, acknowledge them, and treat every other frame as noise. The warning arrives, is discarded, the disconnect arrives ten seconds later, and the client now has to build a connection from scratch while payloads are already being routed elsewhere or dropped.</p>
<p>The serial reconnect is the subtler version and it is written by careful people. Close the socket cleanly, wait for the close handshake, then call <code>apps.connections.open</code> and connect to the URL it returns. That is correct WebSocket hygiene and it is wrong here, because it puts a hole of a second or two between the two connections and Slack has nowhere to put a payload that arrives in it. The gap is small enough that a low-traffic app can go months without noticing and a busy one loses a handful of events every few hours forever.</p>
<p>Then there is <code>link_disabled</code>, which lands in the same handler and means something entirely different. It is not a refresh. It means Socket Mode has been turned off in the app configuration, and every reconnect attempt from here to the heat death of the universe will fail the same way. A client that treats disconnects as uniformly transient will retry that forever, which is how an app ends up silent for a week after somebody toggled a setting.</p>""",
"why": """<p><strong>Periodicity is the whole diagnosis.</strong> Every Socket Mode failure looks like missing messages. What separates them is <em>when</em> the messages are missing. Uniform scatter across the window is a connection pool with ghosts in it. A single step with nothing after it is a connection that never opened. Duplicates alongside misses is several replicas. Tight clusters arriving on a regular multi-hour clock is this, and nothing else produces that shape.</p>
<p><strong>The width of each cluster says which of the two mistakes you made.</strong> A serial reconnect leaves a seam of seconds; a process that died and was restarted by a supervisor leaves tens of seconds to a few minutes; a gap of a quarter of an hour is not a reconnect at all. The script classifies each cluster by width and reports the mix, because &ldquo;handle the disconnect&rdquo; and &ldquo;stop crashing on the disconnect&rdquo; are different pieces of work.</p>
<p><strong>The reasons are not interchangeable and the client must branch on them.</strong> <code>refresh_requested</code> is routine and wants an overlap. <code>link_disabled</code> is permanent and wants an alarm, not a retry. <code>too_many_websockets</code> is the cap and wants a different note entirely. A single <code>catch</code> around the whole thing is what turns three distinct conditions into one reconnect loop.</p>
<p><strong>Regularity has to be measured, not eyeballed.</strong> Three clusters is the minimum from which an interval can be claimed at all, and the script says <code>too-few</code> rather than inventing a cadence from two. Beyond that it uses the coefficient of variation of the intervals, so a genuinely regular refresh passes and a coincidental pair of outages does not.</p>
<p><strong>A cadence outside the plausible range is a different problem wearing this one's clothes.</strong> Clusters every four minutes are not Slack refreshing your connection; clusters every eleven days are not either. The script bounds what it will call a refresh cadence and reports the measured interval when it refuses, because the interval itself is usually the clue to whatever is really happening.</p>
<p><strong>None of this requires a socket.</strong> The disconnect frames are yours &mdash; they arrived at your client and your client logged them, or did not. The gaps are the workspace's, and <code>conversations.history</code> hands them over. Opening a connection to watch for a refresh would mean holding one open for hours and consuming one of the ten the app is allowed, to observe an event the log already recorded.</p>""",
"steps": [
 {"h": "Read the disconnect reasons you already have",
  "body": """<p><code>disconnect_meaning</code> maps each documented reason to what the client should have done: overlap for <code>refresh_requested</code>, stop and alarm for <code>link_disabled</code>, and a pointer elsewhere for <code>too_many_websockets</code>. Pass the reasons your client logged with <code>--reasons</code>. This is the direct evidence, and it costs nothing to collect because it has already been collected.</p>"""},
 {"h": "Find the mentions that never got an answer",
  "body": """<p><code>unanswered_mentions</code> pages <code>conversations.history</code> and returns the timestamps of mentions with no app reply inside the window. It returns timestamps rather than a count, because the count is not the finding here and the arrangement of them is.</p>"""},
 {"h": "Group them into gaps",
  "body": """<p><code>clusters</code> splits the timestamps wherever more than <code>--cluster-gap</code> seconds pass without a miss. Each resulting group is one outage. Everything after this step is about the groups rather than the individual losses.</p>"""},
 {"h": "Measure how regular the groups are",
  "body": """<p><code>regularity</code> takes the cluster start times and returns the mean interval and its coefficient of variation. A refresh schedule produces a small coefficient; unrelated outages produce a large one. Fewer than three clusters returns <code>too-few</code>, because two points make a line whether or not there is a pattern.</p>"""},
 {"h": "Classify each gap by how wide it is",
  "body": """<p><code>gap_kind</code> sorts a cluster width into <code>swap-gap</code>, <code>restart</code> or <code>outage</code>. Seconds mean a serial reconnect; tens of seconds to minutes mean the process died and came back; longer means something that is not a reconnect at all and should not be filed under this note.</p>"""},
 {"h": "Open the new connection before closing the old one",
  "body": """<p>The repair is an ordering change. On <code>warning</code>, or at the latest on <code>disconnect</code> with <code>refresh_requested</code>, open a replacement connection and keep the old one until the new one has received <code>hello</code>. On <code>link_disabled</code>, stop reconnecting and raise a configuration error. The official Socket Mode clients already do the overlap, which is why the honest repair for most apps is to stop hand-rolling the WebSocket layer.</p>"""},
],
"verify": """<p>After the change, run it again over a window that spans several refreshes. The clusters should stop being periodic, because they should stop existing.</p>
<pre><code class="language-bash">python3 slack_socket_refresh_gaps.py --channel C05OPS9QT --reasons refresh_requested,refresh_requested,refresh_requested
# identity   U07BOT9QD (opsbot) in Northwind
# reason     refresh_requested  scheduled    Slack refreshes connections on its own
#                               clock. Overlap the replacement; do not swap it
# history    1000 message(s) from C05OPS9QT
# misses     14 mention(s) with no reply inside 45s
# clusters   4 gap(s) in the window
# width      swap-gap     3 of 4 gap(s) are seconds wide
# width      restart      1 of 4 gap(s) is tens of seconds wide
# interval   periodic     mean 4h 02m between gaps, variation 0.06
# verdict    refresh-not-overlapped  the losses arrive on Slack's refresh clock
#   repair: on warning and on refresh_requested, open the new connection first and
#           close the old one only after it receives hello
#   repair: branch on the disconnect reason; link_disabled is permanent and is not
#           a retry
#   note:   no connection was opened to establish this; the frames are from your log</code></pre>""",
"code_intro": "The statistic is the point. <code>clusters</code> turns a list of losses into a list of outages, and <code>regularity</code> asks whether those outages arrive on a clock &mdash; which is the one measurement that separates this failure from every other way a Socket Mode app loses messages. <code>gap_kind</code> then says whether each outage is a seam or a restart, because those want different fixes. <code>disconnect_meaning</code> handles the direct evidence, and it exists mainly to keep <code>link_disabled</code> from being retried alongside <code>refresh_requested</code>.",
"py_file": "slack_socket_refresh_gaps.py",
"py": '''"""Find the periodic gaps a mishandled Socket Mode refresh leaves behind.

Read only. Nothing here opens a WebSocket: observing a refresh directly would
mean holding a connection open for hours, consuming one of the ten an app is
allowed, in order to watch a frame your own client already logged. The frames
come from that log, and the gaps come from conversations.history.

The question is not whether messages were lost - every Socket Mode fault loses
messages. The question is whether they were lost on a schedule, because that is
what Slack refreshing your connection looks like from the workspace side.
"""
import argparse
import logging
import math
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_socket_refresh_gaps")

API = "https://slack.com/api/"

# The documented reasons, and what the client was supposed to do about each.
# A single catch around all of them is how three distinct conditions become one
# reconnect loop that never surfaces any of them.
REASONS = {
    "refresh_requested": (
        "scheduled",
        "Slack refreshes connections on its own clock, every few hours, and warns "
        "about ten seconds ahead. Open the replacement first and close the old one "
        "once the new one has received hello"),
    "warning": (
        "notice",
        "the ten second warning before a refresh. This is the frame to act on, and "
        "the one most hand-rolled clients discard as noise"),
    "link_disabled": (
        "configuration",
        "Socket Mode was switched off in the app configuration. Reconnecting will "
        "never succeed. Stop retrying and raise a configuration error"),
    "too_many_websockets": (
        "cap",
        "the app is at its ten connection ceiling. That is a leak or a replica count, "
        "and it is a different problem from a refresh"),
}

# Widths. A serial reconnect leaves seconds; a process that died and was
# restarted leaves tens of seconds to minutes; anything longer is not a
# reconnect and should not be filed under this note.
SWAP_SECONDS = 90.0
RESTART_SECONDS = 900.0


def disconnect_meaning(reason):
    """What did this disconnect frame mean, and what should follow it? Pure.

    Returns (kind, detail). The value of this function is that link_disabled
    and refresh_requested arrive in the same handler and want opposite
    responses: one is routine and wants an overlapping reconnect, the other is
    permanent and wants an alarm.
    """
    text = str(reason or "").strip()
    if not text:
        return ("unreported", "no reason was supplied; the timing evidence below "
                              "stands on its own")
    if text in REASONS:
        return REASONS[text]
    return ("unknown", "%s is not one of the documented reasons; read it against the "
                       "Socket Mode reference before treating it as transient" % text)


def unanswered_mentions(messages, bot_user_id, window=45.0):
    """Timestamps of mentions the app never answered. Pure.

    Timestamps rather than a count, because for this note the arrangement is
    the finding and the total is almost meaningless.
    """
    marker = "<@%s>" % bot_user_id if bot_user_id else None
    own, mentions = [], []
    for m in messages or []:
        ts = str((m or {}).get("ts") or "")
        if not ts:
            continue
        author = (m or {}).get("user") or ""
        if (bot_user_id and author == bot_user_id) or (m or {}).get("bot_id"):
            own.append(float(ts))
        elif marker and marker in str((m or {}).get("text") or ""):
            mentions.append(float(ts))
    return sorted(ts for ts in mentions
                  if not any(ts <= o <= ts + float(window) for o in own))


def clusters(stamps, gap=120.0):
    """Group losses into outages. Pure.

    A new group starts wherever more than `gap` seconds pass without a miss.
    Everything after this point is reasoning about groups rather than about
    individual lost messages, which is the shift that makes the diagnosis
    possible at all.
    """
    ordered = sorted(float(t) for t in stamps or [])
    if not ordered:
        return []
    groups, current = [], [ordered[0]]
    for ts in ordered[1:]:
        if ts - current[-1] > float(gap):
            groups.append(current)
            current = [ts]
        else:
            current.append(ts)
    groups.append(current)
    return groups


def gap_kind(width):
    """How wide is this outage, and what does that width mean? Pure."""
    seconds = float(width or 0.0)
    if seconds <= SWAP_SECONDS:
        return ("swap-gap", "seconds wide: a serial reconnect that closed before it "
                            "opened")
    if seconds <= RESTART_SECONDS:
        return ("restart", "tens of seconds to minutes: the process treated the "
                           "disconnect as fatal and was restarted")
    return ("outage", "too wide to be a reconnect of any kind; this belongs to some "
                      "other failure")


def regularity(starts, min_clusters=3, tolerance=0.25):
    """Do these outages arrive on a clock? Pure.

    Returns (state, mean_interval, cv). The coefficient of variation is the
    whole test: a refresh schedule produces a small one and coincidental
    outages produce a large one. Fewer than three clusters returns too-few,
    because two points describe an interval whether or not a pattern exists.
    """
    ordered = sorted(float(t) for t in starts or [])
    if len(ordered) < max(3, min_clusters):
        return ("too-few", 0.0, 0.0)
    gaps = [b - a for a, b in zip(ordered, ordered[1:])]
    mean = sum(gaps) / len(gaps)
    if mean <= 0:
        return ("irregular", 0.0, 0.0)
    variance = sum((g - mean) ** 2 for g in gaps) / len(gaps)
    cv = round(math.sqrt(variance) / mean, 3)
    return (("periodic" if cv <= tolerance else "irregular"), round(mean, 1), cv)


def refresh_verdict(state, mean_interval, kinds, low=1800.0, high=86400.0):
    """Put the timing and the widths together. Pure. Returns (verdict, detail).

    The bounds matter. Clusters every four minutes are not Slack refreshing a
    connection and neither are clusters every eleven days, so the function
    refuses those and reports the interval it measured, because the interval is
    usually the clue to whatever is actually happening.
    """
    if state == "too-few":
        return ("too-few", "fewer than three outages in this window; there is no "
                           "cadence to claim yet")
    if state != "periodic":
        return ("not-periodic", "the outages do not arrive on a clock. Evenly "
                                "scattered losses point at a leaked connection pool "
                                "instead")
    if mean_interval < low or mean_interval > high:
        return ("wrong-cadence", "regular, at %.0f seconds apart, which is outside "
                                 "the few-hours cadence a Socket Mode refresh runs "
                                 "on" % mean_interval)
    if kinds and all(k == "outage" for k in kinds):
        return ("outage-shaped", "regular and on a plausible cadence, but every gap "
                                 "is too wide to be a reconnect. Something else runs "
                                 "on that schedule")
    return ("refresh-not-overlapped",
            "the losses arrive on Slack's refresh clock, every %.0f seconds, in gaps "
            "narrow enough to be the seam between two connections" % mean_interval)


def page_history(session, channel, limit, max_pages):
    """Page conversations.history. A read, and one of two calls made."""
    out, cursor, pages = [], "", 0
    while pages < max_pages:
        params = {"channel": channel, "limit": str(limit)}
        if cursor:
            params["cursor"] = cursor
        body = session.get(API + "conversations.history", params=params,
                           timeout=30).json()
        if body.get("ok") is not True:
            log.error("history    unavailable    %s", body.get("error"))
            return out
        out.extend(body.get("messages") or [])
        cursor = ((body.get("response_metadata") or {}).get("next_cursor") or "")
        pages += 1
        if not cursor:
            break
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN")
    ap.add_argument("--channel", required=True)
    ap.add_argument("--reasons", default="",
                    help="comma separated disconnect reasons your client logged")
    ap.add_argument("--window", type=float, default=45.0)
    ap.add_argument("--cluster-gap", type=float, default=120.0)
    ap.add_argument("--limit", type=int, default=200)
    ap.add_argument("--max-pages", type=int, default=10)
    args = ap.parse_args()

    seen = set()
    for raw in args.reasons.split(","):
        reason = raw.strip()
        if not reason or reason in seen:
            continue
        seen.add(reason)
        kind, detail = disconnect_meaning(reason)
        log.info("reason     %-18s %-12s %s", reason, kind, detail)

    token = os.environ.get(args.token_env)
    if not token:
        log.error("set %s to a bot token with channels:history", args.token_env)
        return 2
    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + token})
    who = s.get(API + "auth.test", timeout=30).json()
    if who.get("ok") is not True:
        log.error("auth.test  unavailable    %s", who.get("error"))
        return 2
    log.info("identity   %s (%s) in %s", who.get("user_id"), who.get("user"),
             who.get("team"))

    messages = page_history(s, args.channel, args.limit, args.max_pages)
    log.info("history    %d message(s) from %s", len(messages), args.channel)
    misses = unanswered_mentions(messages, who.get("user_id"), args.window)
    log.info("misses     %d mention(s) with no reply inside %.0fs", len(misses),
             args.window)

    groups = clusters(misses, args.cluster_gap)
    log.info("clusters   %d gap(s) in the window", len(groups))
    kinds, notes = [], {}
    for group in groups:
        kind, detail = gap_kind(group[-1] - group[0])
        kinds.append(kind)
        notes[kind] = detail
    for kind in sorted(set(kinds)):
        log.info("width      %-12s %d of %d gap(s): %s", kind, kinds.count(kind),
                 len(kinds), notes[kind])

    state, mean_interval, cv = regularity([g[0] for g in groups])
    log.info("interval   %-12s mean %.0f seconds between gaps, variation %.3f",
             state, mean_interval, cv)

    verdict, detail = refresh_verdict(state, mean_interval, kinds)
    if verdict != "refresh-not-overlapped":
        log.info("verdict    %-12s %s", verdict, detail)
        if verdict == "not-periodic":
            log.info("  next:   read the note on the ten connection cap; evenly "
                     "spread losses are a leaked pool rather than a refresh")
        return 0
    log.warning("verdict    %s  %s", verdict, detail)
    log.warning("  repair: on warning and on refresh_requested, open the new "
                "connection first and close the old one after it receives hello")
    log.warning("  repair: branch on the disconnect reason; link_disabled is "
                "permanent and reconnecting on it loops forever")
    log.warning("  note:   no connection was opened to establish this; the frames "
                "are from your own log and the gaps are from the workspace")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-socket-refresh-gaps.mjs",
"js": '''/**
 * Find the periodic gaps a mishandled Socket Mode refresh leaves behind.
 *
 * Read only. Nothing here opens a WebSocket: observing a refresh directly
 * would mean holding a connection open for hours, consuming one of the ten an
 * app is allowed, to watch a frame your own client already logged. The frames
 * come from that log and the gaps come from conversations.history.
 *
 * The question is not whether messages were lost. It is whether they were lost
 * on a schedule, because that is what a refresh looks like from outside.
 */

const API = 'https://slack.com/api/';

// The documented reasons, and what the client was supposed to do about each.
export const REASONS = {
  refresh_requested: ['scheduled',
    'Slack refreshes connections on its own clock, every few hours, and warns about '
    + 'ten seconds ahead. Open the replacement first and close the old one once the '
    + 'new one has received hello'],
  warning: ['notice',
    'the ten second warning before a refresh. This is the frame to act on, and the '
    + 'one most hand-rolled clients discard as noise'],
  link_disabled: ['configuration',
    'Socket Mode was switched off in the app configuration. Reconnecting will never '
    + 'succeed. Stop retrying and raise a configuration error'],
  too_many_websockets: ['cap',
    'the app is at its ten connection ceiling. That is a leak or a replica count, and '
    + 'it is a different problem from a refresh'],
};

export const SWAP_SECONDS = 90;
export const RESTART_SECONDS = 900;

/** What did this disconnect frame mean, and what should follow it? Pure. */
export function disconnectMeaning(reason) {
  const text = String(reason ?? '').trim();
  if (!text) {
    return ['unreported',
      'no reason was supplied; the timing evidence below stands on its own'];
  }
  if (Object.prototype.hasOwnProperty.call(REASONS, text)) return REASONS[text];
  return ['unknown', `${text} is not one of the documented reasons; read it against `
    + 'the Socket Mode reference before treating it as transient'];
}

/** Timestamps of mentions the app never answered. Pure. */
export function unansweredMentions(messages, botUserId, window = 45) {
  const marker = botUserId ? `<@${botUserId}>` : null;
  const own = [];
  const mentions = [];
  for (const m of messages ?? []) {
    const ts = String((m ?? {}).ts ?? '');
    if (!ts) continue;
    const author = (m ?? {}).user ?? '';
    if ((botUserId && author === botUserId) || (m ?? {}).bot_id) own.push(Number(ts));
    else if (marker && String((m ?? {}).text ?? '').includes(marker)) {
      mentions.push(Number(ts));
    }
  }
  return mentions
    .filter((ts) => !own.some((o) => o >= ts && o <= ts + Number(window)))
    .sort((a, b) => a - b);
}

/** Group losses into outages. Pure. */
export function clusters(stamps, gap = 120) {
  const ordered = (stamps ?? []).map(Number).sort((a, b) => a - b);
  if (!ordered.length) return [];
  const groups = [];
  let current = [ordered[0]];
  for (const ts of ordered.slice(1)) {
    if (ts - current[current.length - 1] > Number(gap)) {
      groups.push(current);
      current = [ts];
    } else current.push(ts);
  }
  groups.push(current);
  return groups;
}

/** How wide is this outage, and what does that width mean? Pure. */
export function gapKind(width) {
  const seconds = Number(width) || 0;
  if (seconds <= SWAP_SECONDS) {
    return ['swap-gap', 'seconds wide: a serial reconnect that closed before it opened'];
  }
  if (seconds <= RESTART_SECONDS) {
    return ['restart', 'tens of seconds to minutes: the process treated the disconnect '
      + 'as fatal and was restarted'];
  }
  return ['outage', 'too wide to be a reconnect of any kind; this belongs to some '
    + 'other failure'];
}

/**
 * Do these outages arrive on a clock? Pure.
 * Returns [state, meanInterval, cv]; the coefficient of variation is the test.
 */
export function regularity(starts, minClusters = 3, tolerance = 0.25) {
  const ordered = (starts ?? []).map(Number).sort((a, b) => a - b);
  if (ordered.length < Math.max(3, minClusters)) return ['too-few', 0, 0];
  const gaps = ordered.slice(1).map((b, i) => b - ordered[i]);
  const mean = gaps.reduce((a, b) => a + b, 0) / gaps.length;
  if (mean <= 0) return ['irregular', 0, 0];
  const variance = gaps.reduce((a, g) => a + ((g - mean) ** 2), 0) / gaps.length;
  const cv = Math.round((Math.sqrt(variance) / mean) * 1000) / 1000;
  return [cv <= tolerance ? 'periodic' : 'irregular', Math.round(mean * 10) / 10, cv];
}

/** Put the timing and the widths together. Pure. Returns [verdict, detail]. */
export function refreshVerdict(state, meanInterval, kinds, low = 1800, high = 86400) {
  if (state === 'too-few') {
    return ['too-few',
      'fewer than three outages in this window; there is no cadence to claim yet'];
  }
  if (state !== 'periodic') {
    return ['not-periodic', 'the outages do not arrive on a clock. Evenly scattered '
      + 'losses point at a leaked connection pool instead'];
  }
  if (meanInterval < low || meanInterval > high) {
    return ['wrong-cadence', `regular, at ${Math.round(meanInterval)} seconds apart, `
      + 'which is outside the few-hours cadence a Socket Mode refresh runs on'];
  }
  if (kinds && kinds.length && kinds.every((k) => k === 'outage')) {
    return ['outage-shaped', 'regular and on a plausible cadence, but every gap is too '
      + 'wide to be a reconnect. Something else runs on that schedule'];
  }
  return ['refresh-not-overlapped',
    `the losses arrive on Slack refresh clock, every ${Math.round(meanInterval)} `
    + 'seconds, in gaps narrow enough to be the seam between two connections'];
}

function arg(args, name, fallback = null) {
  const i = args.indexOf(name);
  return i === -1 ? fallback : args[i + 1];
}

async function pageHistory(headers, channel, limit, maxPages) {
  const out = [];
  let cursor = '';
  for (let page = 0; page < maxPages; page += 1) {
    const params = new URLSearchParams({ channel, limit: String(limit) });
    if (cursor) params.set('cursor', cursor);
    const body = await (await fetch(`${API}conversations.history?${params}`,
      { headers })).json();
    if (body.ok !== true) {
      console.error(`history    unavailable    ${body.error}`);
      return out;
    }
    out.push(...(body.messages ?? []));
    cursor = (body.response_metadata ?? {}).next_cursor ?? '';
    if (!cursor) break;
  }
  return out;
}

async function main() {
  const args = process.argv.slice(2);
  const seen = new Set();
  for (const raw of String(arg(args, '--reasons', '')).split(',')) {
    const reason = raw.trim();
    if (!reason || seen.has(reason)) continue;
    seen.add(reason);
    const [kind, detail] = disconnectMeaning(reason);
    console.log(`reason     ${reason.padEnd(18)} ${kind.padEnd(12)} ${detail}`);
  }

  const tokenEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
  const token = process.env[tokenEnv];
  const channel = arg(args, '--channel', '');
  if (!token || !channel) {
    console.error(`set ${tokenEnv} to a bot token with channels:history, and pass `
      + '--channel');
    process.exitCode = 2;
    return;
  }
  const headers = { Authorization: `Bearer ${token}` };
  const who = await (await fetch(`${API}auth.test`, { headers })).json();
  if (who.ok !== true) {
    console.error(`auth.test  unavailable    ${who.error}`);
    process.exitCode = 2;
    return;
  }
  console.log(`identity   ${who.user_id} (${who.user}) in ${who.team}`);

  const window = Number(arg(args, '--window', '45'));
  const messages = await pageHistory(headers, channel,
    Number(arg(args, '--limit', '200')), Number(arg(args, '--max-pages', '10')));
  console.log(`history    ${messages.length} message(s) from ${channel}`);
  const misses = unansweredMentions(messages, who.user_id, window);
  console.log(`misses     ${misses.length} mention(s) with no reply inside ${window}s`);

  const groups = clusters(misses, Number(arg(args, '--cluster-gap', '120')));
  console.log(`clusters   ${groups.length} gap(s) in the window`);
  const kinds = groups.map((g) => gapKind(g[g.length - 1] - g[0])[0]);
  for (const kind of [...new Set(kinds)].sort()) {
    console.log(`width      ${kind.padEnd(12)} `
      + `${kinds.filter((k) => k === kind).length} of ${kinds.length} gap(s)`);
  }

  const [state, meanInterval, cv] = regularity(groups.map((g) => g[0]));
  console.log(`interval   ${state.padEnd(12)} mean ${Math.round(meanInterval)} seconds `
    + `between gaps, variation ${cv}`);

  const [verdict, detail] = refreshVerdict(state, meanInterval, kinds);
  if (verdict !== 'refresh-not-overlapped') {
    console.log(`verdict    ${verdict.padEnd(12)} ${detail}`);
    if (verdict === 'not-periodic') {
      console.log('  next:   read the note on the ten connection cap; evenly spread '
        + 'losses are a leaked pool rather than a refresh');
    }
    return;
  }
  console.warn(`verdict    ${verdict}  ${detail}`);
  console.warn('  repair: on warning and on refresh_requested, open the new connection '
    + 'first and close the old one after it receives hello');
  console.warn('  repair: branch on the disconnect reason; link_disabled is permanent '
    + 'and reconnecting on it loops forever');
  console.warn('  note:   no connection was opened to establish this; the frames are '
    + 'from your own log and the gaps are from the workspace');
  process.exitCode = 1;
}

// Only run when invoked directly, so importing this module in the tests does
// not execute main() and fail the file on a missing token.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The tests are written around the two ways this check could be wrong in public. It could claim a schedule that is not there, so <code>regularity</code> is tested with two clusters and must answer <code>too-few</code>, and with wildly uneven intervals and must answer <code>irregular</code>. Or it could claim this note for evidence that belongs to a neighbour, so <code>refresh_verdict</code> is tested against a four-minute cadence and against gaps that are hours wide, and refuses both. The reason table is tested for the one pairing that matters: <code>link_disabled</code> and <code>refresh_requested</code> must not come back as the same kind of thing.",
"test_py_file": "test_slack_socket_refresh_gaps.py",
"test_py": '''from slack_socket_refresh_gaps import (
    clusters, disconnect_meaning, gap_kind, refresh_verdict, regularity,
    unanswered_mentions,
)

FOUR_HOURS = 14400.0


def test_a_refresh_is_scheduled_and_wants_an_overlap():
    kind, detail = disconnect_meaning("refresh_requested")
    assert kind == "scheduled"
    assert "hello" in detail


def test_link_disabled_is_permanent_and_not_the_same_kind_of_thing():
    assert disconnect_meaning("link_disabled")[0] == "configuration"
    assert disconnect_meaning("link_disabled")[0] != disconnect_meaning(
        "refresh_requested")[0]


def test_the_cap_reason_is_handed_to_the_other_note():
    assert disconnect_meaning("too_many_websockets")[0] == "cap"


def test_the_ten_second_warning_is_its_own_frame():
    assert disconnect_meaning("warning")[0] == "notice"


def test_an_unknown_reason_is_not_assumed_transient():
    kind, detail = disconnect_meaning("something_new")
    assert kind == "unknown"
    assert "transient" in detail


def test_no_reason_at_all_is_not_a_finding():
    assert disconnect_meaning("")[0] == "unreported"
    assert disconnect_meaning(None)[0] == "unreported"


def test_only_mentions_without_a_reply_are_returned():
    msgs = [{"ts": "100", "user": "U1", "text": "<@UBOT> a"},
            {"ts": "110", "user": "UBOT", "text": "ok"},
            {"ts": "200", "user": "U2", "text": "<@UBOT> b"}]
    assert unanswered_mentions(msgs, "UBOT", 45) == [200.0]


def test_losses_close_together_are_one_outage():
    assert clusters([100, 110, 120], 120) == [[100.0, 110.0, 120.0]]


def test_a_long_quiet_stretch_starts_a_new_outage():
    assert clusters([100, 110, 5000], 120) == [[100.0, 110.0], [5000.0]]


def test_no_losses_means_no_outages():
    assert clusters([]) == []


def test_a_seam_of_seconds_is_a_swap_gap():
    assert gap_kind(20)[0] == "swap-gap"


def test_tens_of_seconds_is_a_restart():
    assert gap_kind(300)[0] == "restart"


def test_a_gap_of_hours_is_not_a_reconnect_at_all():
    assert gap_kind(7200)[0] == "outage"


def test_evenly_spaced_outages_are_periodic():
    state, mean, cv = regularity([0, FOUR_HOURS, 2 * FOUR_HOURS, 3 * FOUR_HOURS])
    assert state == "periodic"
    assert mean == FOUR_HOURS
    assert cv == 0.0


def test_wildly_uneven_outages_are_irregular():
    assert regularity([0, 100, 50000, 50100])[0] == "irregular"


def test_two_outages_are_not_enough_to_claim_a_cadence():
    assert regularity([0, FOUR_HOURS])[0] == "too-few"
    assert regularity([])[0] == "too-few"


def test_a_periodic_multi_hour_cadence_of_narrow_gaps_is_the_finding():
    verdict, detail = refresh_verdict("periodic", FOUR_HOURS,
                                      ["swap-gap", "swap-gap", "restart"])
    assert verdict == "refresh-not-overlapped"
    assert "seam" in detail


def test_scattered_losses_are_handed_to_the_connection_cap_note():
    verdict, detail = refresh_verdict("irregular", FOUR_HOURS, ["swap-gap"])
    assert verdict == "not-periodic"
    assert "leaked connection pool" in detail


def test_a_four_minute_cadence_is_regular_and_is_not_a_refresh():
    assert refresh_verdict("periodic", 240.0, ["swap-gap"])[0] == "wrong-cadence"


def test_gaps_too_wide_to_be_a_reconnect_are_refused_even_when_periodic():
    assert refresh_verdict("periodic", FOUR_HOURS, ["outage", "outage"])[0] == (
        "outage-shaped")


def test_too_few_outages_survives_into_the_verdict():
    assert refresh_verdict("too-few", 0.0, [])[0] == "too-few"
''',
"test_js_file": "slack-socket-refresh-gaps.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  clusters, disconnectMeaning, gapKind, refreshVerdict, regularity,
  unansweredMentions,
} from './slack-socket-refresh-gaps.mjs';

const FOUR_HOURS = 14400;

test('a refresh is scheduled and wants an overlap', () => {
  const [kind, detail] = disconnectMeaning('refresh_requested');
  assert.equal(kind, 'scheduled');
  assert.match(detail, /hello/);
});

test('link_disabled is permanent and not the same kind of thing', () => {
  assert.equal(disconnectMeaning('link_disabled')[0], 'configuration');
  assert.notEqual(disconnectMeaning('link_disabled')[0],
    disconnectMeaning('refresh_requested')[0]);
});

test('the cap reason is handed to the other note', () => {
  assert.equal(disconnectMeaning('too_many_websockets')[0], 'cap');
});

test('the ten second warning is its own frame', () => {
  assert.equal(disconnectMeaning('warning')[0], 'notice');
});

test('an unknown reason is not assumed transient', () => {
  const [kind, detail] = disconnectMeaning('something_new');
  assert.equal(kind, 'unknown');
  assert.match(detail, /transient/);
});

test('no reason at all is not a finding', () => {
  assert.equal(disconnectMeaning('')[0], 'unreported');
  assert.equal(disconnectMeaning(null)[0], 'unreported');
});

test('only mentions without a reply are returned', () => {
  const msgs = [{ ts: '100', user: 'U1', text: '<@UBOT> a' },
    { ts: '110', user: 'UBOT', text: 'ok' },
    { ts: '200', user: 'U2', text: '<@UBOT> b' }];
  assert.deepEqual(unansweredMentions(msgs, 'UBOT', 45), [200]);
});

test('losses close together are one outage', () => {
  assert.deepEqual(clusters([100, 110, 120], 120), [[100, 110, 120]]);
});

test('a long quiet stretch starts a new outage', () => {
  assert.deepEqual(clusters([100, 110, 5000], 120), [[100, 110], [5000]]);
});

test('no losses means no outages', () => {
  assert.deepEqual(clusters([]), []);
});

test('a seam of seconds is a swap gap', () => {
  assert.equal(gapKind(20)[0], 'swap-gap');
});

test('tens of seconds is a restart', () => {
  assert.equal(gapKind(300)[0], 'restart');
});

test('a gap of hours is not a reconnect at all', () => {
  assert.equal(gapKind(7200)[0], 'outage');
});

test('evenly spaced outages are periodic', () => {
  const [state, mean, cv] = regularity([0, FOUR_HOURS, 2 * FOUR_HOURS,
    3 * FOUR_HOURS]);
  assert.equal(state, 'periodic');
  assert.equal(mean, FOUR_HOURS);
  assert.equal(cv, 0);
});

test('wildly uneven outages are irregular', () => {
  assert.equal(regularity([0, 100, 50000, 50100])[0], 'irregular');
});

test('two outages are not enough to claim a cadence', () => {
  assert.equal(regularity([0, FOUR_HOURS])[0], 'too-few');
  assert.equal(regularity([])[0], 'too-few');
});

test('a periodic multi hour cadence of narrow gaps is the finding', () => {
  const [verdict, detail] = refreshVerdict('periodic', FOUR_HOURS,
    ['swap-gap', 'swap-gap', 'restart']);
  assert.equal(verdict, 'refresh-not-overlapped');
  assert.match(detail, /seam/);
});

test('scattered losses are handed to the connection cap note', () => {
  const [verdict, detail] = refreshVerdict('irregular', FOUR_HOURS, ['swap-gap']);
  assert.equal(verdict, 'not-periodic');
  assert.match(detail, /leaked connection pool/);
});

test('a four minute cadence is regular and is not a refresh', () => {
  assert.equal(refreshVerdict('periodic', 240, ['swap-gap'])[0], 'wrong-cadence');
});

test('gaps too wide to be a reconnect are refused even when periodic', () => {
  assert.equal(refreshVerdict('periodic', FOUR_HOURS, ['outage', 'outage'])[0],
    'outage-shaped');
});

test('too few outages survives into the verdict', () => {
  assert.equal(refreshVerdict('too-few', 0, [])[0], 'too-few');
});
''',
"faq": [
 ("Is refresh_requested a bug on Slack's side?",
  "No, it is documented behaviour and it is not going away. Socket Mode connections are refreshed periodically by design, and Slack goes out of its way to make it survivable: it sends a warning roughly ten seconds before the disconnect so a client has time to open a replacement. The bug is on the client side, and it is always one of two things. Either the disconnect is treated as an error and the process dies, or the reconnect is done in the wrong order, closing before opening."),
 ("Why not just reconnect faster?",
  "Because the gap is not the problem, the ordering is. However fast a serial reconnect is, there is an interval during which your app has no open connection, and a payload that arrives then is gone: Socket Mode has no redelivery, no acknowledgement window and no replay. Making the gap a hundred milliseconds instead of two seconds reduces the loss rate and does not remove it. Overlapping the two connections removes it, because there is never a moment with nothing listening."),
 ("How is this different from a leaked connection pool?",
  "By when the losses happen. A pool with dead registrations in it loses payloads uniformly at random, spread evenly across whatever window you look at, because each payload is an independent draw. A mishandled refresh loses payloads in tight bunches on a regular multi-hour clock, with normal service in between. The script measures the coefficient of variation of the intervals between outages precisely so it can tell you which one you have instead of asserting one."),
 ("Our client logs link_disabled, not refresh_requested. Same fix?",
  "No, and this is the pairing worth getting right. link_disabled means Socket Mode has been switched off in the app configuration. There is no replacement connection to open, no overlap to arrange, and no number of retries that will help; the app will stay silent until somebody turns Socket Mode back on or configures a Request URL. It arrives in the same handler as a refresh and it wants an alarm rather than a reconnect, which is why the script keeps the two reasons in different categories."),
 ("The gaps are periodic but they are twenty minutes wide. Is that this?",
  "Probably not, and the script refuses to call it this. A swap between two connections leaves a seam of seconds; a process that crashed and was restarted by a supervisor leaves tens of seconds to a few minutes. Twenty minutes is something else that runs on a schedule: a deploy, a cron job, a node rotation, a dependency with its own maintenance window. The measured interval and the gap width are both printed, because at that point the interval is the most useful clue you have."),
],
"related": [
 ("/slack/event-subscriptions-auto-disabled/", "the other way delivery stops without an error"),
 ("/slack/rtm-legacy-still-used/", "the same reconnect problem on the retired transport"),
 ("/slack/http-200-ok-false/", "why nothing in the log looked like a failure"),
],
"citations": [CITE_SOCKET_MODE, CITE_NODE_1243, CITE_BOLT_2496, CITE_EVENTS_API],
})
GUIDES.append({
"slug": "socket-mode-single-instance",
"title": "Socket Mode does not load balance: replicas duplicate and drop",
"description": "Several open connections means Slack picks one per payload, without a distribution guarantee. Measure how often a trigger got exactly one answer.",
"h1": "Socket Mode does not load balance: replicas duplicate and drop",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack socket mode multiple instances",
             "slack socket mode horizontal scaling",
             "slack bot answers twice after scaling",
             "slack socket mode replicas duplicate events",
             "bolt socket mode single instance"],
"deps": "Python 3.9+ with requests, or Node.js 18+; a bot token with channels:history, and the replica count the deployment actually runs",
"lead": "The app was scaled from one pod to three on Thursday afternoon, for headroom before a launch. By Friday morning the support channel had two complaints that the bot had answered the same request twice and one that it had not answered at all. Restarting a pod changes which of those happens. Rolling back to one pod makes both stop.</p><p>Nothing is wrong with the code. Three pods, three Socket Mode connections, and Slack sends each payload to <em>one</em> of them &mdash; with, in its own words, no predictable distribution pattern. That is not a work queue. There is no consumer group, no acknowledgement-based redelivery to a different consumer, and no ordering guarantee anywhere in it.",
"short_answer": """<p>Socket Mode is not a load balancer and it is not a message queue. When several connections are open for one app, Slack routes each payload to one of them and does not promise which. Add replicas and you do not get work sharing &mdash; you get a lottery.</p>
<p>The losses come from the lottery: a payload routed to a pod that is restarting, draining or wedged is gone, because there is no redelivery to a different consumer. <strong>The duplicates come from the retry landing somewhere else.</strong> When a delivery is not acknowledged in time Slack retries it, and with three connections open the retry can arrive on a different pod from the original. Each pod's dedupe cache is perfectly correct and completely blind: neither saw both copies. A per-process cache cannot deduplicate across processes, so the work is done twice and every individual component behaves exactly as designed.</p>
<p><strong>The measurement is the fraction of triggers that got exactly one answer.</strong> Page <code>conversations.history</code>, count the app's replies inside a window after each mention, and sort them into none, one and many. Duplicates <em>and</em> misses in the same channel is the fingerprint no other Socket Mode failure produces: retries alone give duplicates without misses, a leaked connection pool gives misses without duplicates.</p>""",
"problem": """<p>The reason teams walk into this is that every other part of their stack rewards adding replicas. HTTP behind a load balancer shares work. A queue consumer group shares work. A Kafka partition assignment shares work. Socket Mode looks like a long-lived consumer connection and is nothing of the kind: it is a delivery channel, and having three of them means Slack has three places it might put a payload, not three workers splitting a stream.</p>
<p>The non-determinism is what makes it so hard to pin down. The same message, sent twice, behaves differently. A pod restart changes the outcome. A quiet afternoon looks fine because there is enough headroom that nothing is ever slow enough to be retried. Then a busy morning produces four complaints in an hour and nobody can reproduce any of them. Every hypothesis fits some of the evidence, which is the signature of a routing problem rather than a logic problem.</p>
<p>Idempotency keys are the usual first attempt and they usually fail, for a reason worth understanding. A dedupe cache in process memory is per-pod. Pod A handles the original, pod B handles the retry, and neither one has ever seen the other's copy, so both are certain they are handling something new. Moving the cache to Redis fixes it &mdash; and at that point you have built the coordination layer that Socket Mode was supposed to save you from, in front of a transport that still drops payloads when a pod is restarting.</p>
<p>And the losses do not announce themselves. There is no dead-letter queue, no unacknowledged-message metric, no consumer lag. A payload routed to a pod that is thirty seconds into a rolling restart is simply never processed by anything, and the only record it existed is the human message in Slack that nobody replied to. That is why the check has to be built out of the workspace's own history rather than out of the app's telemetry: the app has no telemetry for events it never received.</p>""",
"why": """<p><strong>Duplicates and misses together is the fingerprint, and no other note here produces it.</strong> Retries without replicas duplicate but do not lose. A leaked connection pool loses but does not duplicate, because each payload still goes to exactly one registration. A mishandled refresh loses in periodic bunches. Only several live listeners give you both at once, in the same channel, in the same hour. The script checks for the pair rather than for either half.</p>
<p><strong>The determinism fraction is a better number than a duplicate count.</strong> &ldquo;Fourteen duplicates this week&rdquo; invites somebody to add a dedupe key. &ldquo;Sixty-two per cent of triggers got exactly one answer&rdquo; says the delivery path is non-deterministic, which is the actual finding, and it moves in the right direction as soon as the replica count comes down.</p>
<p><strong>Spacing separates this from the retry note, and the script makes that call explicitly.</strong> Duplicates a few seconds apart, or one minute or five minutes apart, are Slack's retry schedule; if there are no misses beside them, one listener is mishandling retries and that is a different note. Duplicates less than a second apart with no misses are usually two subscriptions to the same conversation, which is a third note. The verdict names which of the three it found.</p>
<p><strong>The replica count is an input, not an inference.</strong> The script cannot see your deployment and does not pretend to. You state how many replicas hold a connection, and the finding is reported against that number, because the repair is expressed in replicas and a diagnosis expressed in anything else is not actionable.</p>
<p><strong>A per-process dedupe cache is not a fix and the script says so in the repair.</strong> The cache is correct; it is simply in the wrong place. If the app must run more than one instance, the deduplication has to live somewhere all of them can see, and even then the routing losses remain. That is why the repair is one receiver and a queue you control, not a smarter cache.</p>
<p><strong>Nothing here opens a connection.</strong> Counting live connections would require minting one, which consumes part of the app's ten-connection budget and is a write. Everything above is read from the workspace and from a replica count you already know.</p>""",
"steps": [
 {"h": "Count the replies to each mention rather than the duplicates overall",
  "body": """<p><code>reply_counts</code> walks <code>conversations.history</code> and returns, for every mention of the bot, how many app-authored messages followed it inside the window. That per-trigger count is what makes the rest possible: a total number of duplicates cannot tell you about the mentions that got nothing.</p>"""},
 {"h": "Sort the outcomes into none, once and many",
  "body": """<p><code>outcome_mix</code> reduces those counts to four numbers and a fraction. The fraction &mdash; triggers answered exactly once, over all triggers &mdash; is the finding. A healthy app sits at one. Anything materially below it has a delivery path that is not deterministic, whichever direction the errors go.</p>"""},
 {"h": "Look at the gaps between repeated answers",
  "body": """<p><code>repeat_runs</code> groups the app's own messages by identical text within a window and returns the intervals between them. <code>spacing_kind</code> then labels each run <code>simultaneous</code>, <code>retry</code> or <code>spread</code>. This is where the diagnosis stops being about counts and starts being about mechanism.</p>"""},
 {"h": "Let the combination pick the note",
  "body": """<p><code>fingerprint</code> takes the outcome mix and the spacings and returns one of five verdicts. Duplicates with misses is this note. Retry-spaced duplicates without misses is the retry note. Sub-second duplicates without misses is a double subscription. Misses alone is the connection cap or a refresh. Nothing at all is clean, and the script will say that too.</p>"""},
 {"h": "Read the verdict against the replica count you gave it",
  "body": """<p>The output states the finding in replicas because that is what you can change. Three replicas each holding a connection is three places a payload might land and two of them are wrong at any moment; the number to get to is one.</p>"""},
 {"h": "One receiver, then scale behind it",
  "body": """<p>The repair the script prints is architectural. Run Socket Mode as a singleton, restarted on failure, and have it do nothing but enqueue payloads into something you control; scale the workers that drain that queue as far as you like. If ingress genuinely has to be multi-node, that is what the HTTP Events API and a load balancer are for. A shared dedupe cache is a patch on the duplicates and does nothing for the drops.</p>"""},
],
"verify": """<p>Scale back to one replica, wait for a busy period, and run it again. The fraction is the number to watch; the duplicate count will follow it.</p>
<pre><code class="language-bash">python3 slack_socket_replica_fingerprint.py --channel C05SUP9QT --replicas 3
# identity   U07BOT9QD (helpbot) in Northwind
# triggers   84 mention(s) read, answered inside 45s
# outcome    none 9   once 63   many 12   of 84
# exactly-once   0.750
# spacing    retry        7 run(s) repeated at Slack retry intervals
# spacing    simultaneous 5 run(s) repeated less than a second apart
# verdict    several-live-connections  duplicates and misses in the same channel
# replicas   3 replica(s) hold a connection, so a payload has 3 places to land
#   repair: run Socket Mode as a singleton and enqueue payloads into a queue you
#           control; scale the workers, not the receiver
#   repair: a dedupe cache in process memory cannot see the copy another pod
#           handled; if instances must be plural, the cache has to be shared
#   note:   nothing here opened a connection; counting them would consume one</code></pre>""",
"code_intro": "The number this script exists to produce is <code>exactly-once</code>: the proportion of triggers that got one answer, no more and no less. Counting duplicates alone would hide the drops, and counting drops alone would hide the duplicates, and it is the pair that identifies the failure. <code>spacing_kind</code> is the second half of the argument, because duplicates at Slack's retry intervals with no drops beside them belong to a different note, and <code>fingerprint</code> is where those two observations are turned into a verdict that names which note you are in.",
"py_file": "slack_socket_replica_fingerprint.py",
"py": '''"""Tell several live Socket Mode connections apart from retries and drops.

Read only. Nothing here opens a connection: apps.connections.open mints one and
counts against the ten an app is allowed, so the number of live connections is
supplied by you as a replica count rather than measured. Everything else comes
from conversations.history, which is where the consequences are recorded.

The measurement is the fraction of triggers that got exactly one answer. Slack
routes each payload to one of the open connections without a distribution
guarantee, so more connections means more places a payload can land and more
places a retry can land separately from its original.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_socket_replica_fingerprint")

API = "https://slack.com/api/"

# Slack retries an unacknowledged event on a schedule. Duplicates spaced like
# this, with no drops beside them, are one listener mishandling retries - a
# different problem with a different repair.
RETRY_SPACINGS = (60.0, 300.0)
RETRY_TOLERANCE = 0.25

# Below this, two answers were produced at the same moment rather than in
# sequence, which points at two subscriptions rather than two connections.
SIMULTANEOUS_SECONDS = 1.0


def reply_counts(messages, bot_user_id, window=45.0):
    """How many answers did each mention get? Pure.

    Per trigger rather than in total, because a total duplicate count cannot
    say anything about the mentions that got nothing at all, and it is the two
    together that identify this failure.

    Returns [(mention_ts, replies), ...] oldest first.
    """
    marker = "<@%s>" % bot_user_id if bot_user_id else None
    own, mentions = [], []
    for m in messages or []:
        ts = str((m or {}).get("ts") or "")
        if not ts:
            continue
        author = (m or {}).get("user") or ""
        if (bot_user_id and author == bot_user_id) or (m or {}).get("bot_id"):
            own.append(float(ts))
        elif marker and marker in str((m or {}).get("text") or ""):
            mentions.append(float(ts))
    out = []
    for ts in sorted(mentions):
        out.append((ts, sum(1 for o in own if ts <= o <= ts + float(window))))
    return out


def outcome_mix(counts):
    """Sort trigger outcomes into none, once and many. Pure.

    Returns (mix, exactly_once). The fraction is the finding: a delivery path
    that works answers every trigger once, and a fraction materially below one
    is non-deterministic whichever direction the errors go in.
    """
    rows = [int(n) for _ts, n in counts or []]
    mix = {"none": sum(1 for n in rows if n == 0),
           "once": sum(1 for n in rows if n == 1),
           "many": sum(1 for n in rows if n > 1),
           "total": len(rows)}
    fraction = 0.0 if not rows else round(mix["once"] / float(len(rows)), 3)
    return (mix, fraction)


def repeat_runs(messages, bot_user_id, gap=600.0):
    """Runs of identical app-authored messages, and the gaps between them. Pure.

    Text is compared after trimming and lowercasing, which is crude and is
    enough: the duplicates this note is about are the same answer produced
    twice by two processes running the same code.

    Returns [(text, [delta, ...]), ...] for runs of two or more.
    """
    said = {}
    for m in messages or []:
        ts = str((m or {}).get("ts") or "")
        author = (m or {}).get("user") or ""
        is_app = (bot_user_id and author == bot_user_id) or (m or {}).get("bot_id")
        text = str((m or {}).get("text") or "").strip().lower()
        if not ts or not is_app or not text:
            continue
        said.setdefault(text, []).append(float(ts))
    runs = []
    for text, stamps in said.items():
        stamps.sort()
        current = [stamps[0]]
        for ts in stamps[1:]:
            if ts - current[-1] <= float(gap):
                current.append(ts)
            else:
                if len(current) > 1:
                    runs.append((text, [b - a for a, b in zip(current, current[1:])]))
                current = [ts]
        if len(current) > 1:
            runs.append((text, [b - a for a, b in zip(current, current[1:])]))
    return sorted(runs)


def spacing_kind(deltas):
    """What produced this run of identical answers? Pure.

    simultaneous  under a second apart: two handlers acted on the same payload
                  at the same moment, which is usually two subscriptions.
    retry         at Slack's retry intervals: one listener that did not
                  acknowledge in time, which is a different note.
    spread        neither, so the run says nothing on its own.
    """
    gaps = [float(d) for d in deltas or []]
    if not gaps:
        return "single"
    if all(g < SIMULTANEOUS_SECONDS for g in gaps):
        return "simultaneous"
    for g in gaps:
        for expected in RETRY_SPACINGS:
            if abs(g - expected) <= expected * RETRY_TOLERANCE:
                return "retry"
    return "spread"


def fingerprint(mix, kinds):
    """Which failure is this? Pure. Returns (verdict, detail).

    The combination is the whole diagnosis. Duplicates beside drops is the only
    shape several live connections produce; retries duplicate without dropping,
    and a leaked connection pool drops without duplicating.
    """
    mix = mix or {}
    many, none = int(mix.get("many") or 0), int(mix.get("none") or 0)
    kinds = list(kinds or [])
    if many and none:
        return ("several-live-connections",
                "duplicates and misses in the same channel. A retry landing on a "
                "different instance from its original is handled twice, and a payload "
                "routed to an instance that is restarting is handled by nobody")
    if many and "retry" in kinds:
        return ("retries-one-listener",
                "duplicates at Slack's retry intervals with nothing dropped. One "
                "listener that did not acknowledge in time, which is a different note")
    if many and "simultaneous" in kinds:
        return ("double-subscription",
                "duplicates under a second apart with nothing dropped. Two "
                "subscriptions delivering the same conversation, not two connections")
    if many:
        return ("duplicates-unclassified",
                "repeats that match neither the retry schedule nor a simultaneous "
                "pair; read the runs before concluding anything")
    if none:
        return ("losses-only",
                "drops with no duplicates. Each payload still went to exactly one "
                "place, so look at the connection cap or a mishandled refresh")
    return ("clean", "every trigger in this window got exactly one answer")


def page_history(session, channel, limit, max_pages):
    """Page conversations.history. A read, and one of two calls made."""
    out, cursor, pages = [], "", 0
    while pages < max_pages:
        params = {"channel": channel, "limit": str(limit)}
        if cursor:
            params["cursor"] = cursor
        body = session.get(API + "conversations.history", params=params,
                           timeout=30).json()
        if body.get("ok") is not True:
            log.error("history    unavailable    %s", body.get("error"))
            return out
        out.extend(body.get("messages") or [])
        cursor = ((body.get("response_metadata") or {}).get("next_cursor") or "")
        pages += 1
        if not cursor:
            break
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN")
    ap.add_argument("--channel", required=True)
    ap.add_argument("--replicas", type=int, default=1,
                    help="how many instances hold a Socket Mode connection")
    ap.add_argument("--window", type=float, default=45.0)
    ap.add_argument("--repeat-gap", type=float, default=600.0)
    ap.add_argument("--limit", type=int, default=200)
    ap.add_argument("--max-pages", type=int, default=5)
    args = ap.parse_args()

    token = os.environ.get(args.token_env)
    if not token:
        log.error("set %s to a bot token with channels:history", args.token_env)
        return 2
    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + token})
    who = s.get(API + "auth.test", timeout=30).json()
    if who.get("ok") is not True:
        log.error("auth.test  unavailable    %s", who.get("error"))
        return 2
    log.info("identity   %s (%s) in %s", who.get("user_id"), who.get("user"),
             who.get("team"))

    messages = page_history(s, args.channel, args.limit, args.max_pages)
    counts = reply_counts(messages, who.get("user_id"), args.window)
    mix, fraction = outcome_mix(counts)
    log.info("triggers   %d mention(s) read, answered inside %.0fs", mix["total"],
             args.window)
    if not mix["total"]:
        log.info("verdict    nothing to measure; no mentions in the window read")
        return 0
    log.info("outcome    none %d   once %d   many %d   of %d", mix["none"],
             mix["once"], mix["many"], mix["total"])
    log.info("exactly-once   %.3f", fraction)

    runs = repeat_runs(messages, who.get("user_id"), args.repeat_gap)
    kinds = [spacing_kind(deltas) for _text, deltas in runs]
    for kind in sorted(set(kinds)):
        log.info("spacing    %-12s %d run(s) of repeated answers", kind,
                 kinds.count(kind))

    verdict, detail = fingerprint(mix, kinds)
    if verdict == "clean":
        log.info("verdict    clean        %s", detail)
        return 0
    if verdict != "several-live-connections":
        log.info("verdict    %-12s %s", verdict, detail)
        return 0
    log.warning("verdict    %s  %s", verdict, detail)
    log.warning("replicas   %d replica(s) hold a connection, so a payload has %d "
                "places to land and %d of them are wrong at any moment",
                args.replicas, args.replicas, max(0, args.replicas - 1))
    log.warning("  repair: run Socket Mode as a singleton and enqueue payloads into a "
                "queue you control; scale the workers, not the receiver")
    log.warning("  repair: a dedupe cache in process memory cannot see the copy "
                "another instance handled; if instances must be plural, share it")
    log.warning("  repair: for genuinely multi-node ingress use the HTTP Events API "
                "behind a load balancer, which does distribute")
    log.warning("  note:   nothing here opened a connection; counting them would "
                "consume one of the ten this app is allowed")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-socket-replica-fingerprint.mjs",
"js": '''/**
 * Tell several live Socket Mode connections apart from retries and drops.
 *
 * Read only. Nothing here opens a connection: apps.connections.open mints one
 * and counts against the ten an app is allowed, so the number of live
 * connections is supplied as a replica count rather than measured. Everything
 * else comes from conversations.history, where the consequences are recorded.
 *
 * The measurement is the fraction of triggers that got exactly one answer.
 */

const API = 'https://slack.com/api/';

// Slack retries an unacknowledged event on a schedule. Duplicates spaced like
// this, with no drops beside them, are one listener mishandling retries.
export const RETRY_SPACINGS = [60, 300];
export const RETRY_TOLERANCE = 0.25;
export const SIMULTANEOUS_SECONDS = 1;

/**
 * How many answers did each mention get? Pure.
 * Per trigger rather than in total, because a total duplicate count says
 * nothing about the mentions that got nothing at all.
 */
export function replyCounts(messages, botUserId, window = 45) {
  const marker = botUserId ? `<@${botUserId}>` : null;
  const own = [];
  const mentions = [];
  for (const m of messages ?? []) {
    const ts = String((m ?? {}).ts ?? '');
    if (!ts) continue;
    const author = (m ?? {}).user ?? '';
    if ((botUserId && author === botUserId) || (m ?? {}).bot_id) own.push(Number(ts));
    else if (marker && String((m ?? {}).text ?? '').includes(marker)) {
      mentions.push(Number(ts));
    }
  }
  return mentions.sort((a, b) => a - b)
    .map((ts) => [ts, own.filter((o) => o >= ts && o <= ts + Number(window)).length]);
}

/** Sort trigger outcomes into none, once and many. Pure. [mix, exactlyOnce]. */
export function outcomeMix(counts) {
  const rows = (counts ?? []).map(([, n]) => Number(n));
  const mix = {
    none: rows.filter((n) => n === 0).length,
    once: rows.filter((n) => n === 1).length,
    many: rows.filter((n) => n > 1).length,
    total: rows.length,
  };
  const fraction = rows.length ? Math.round((mix.once / rows.length) * 1000) / 1000 : 0;
  return [mix, fraction];
}

/**
 * Runs of identical app-authored messages, and the gaps between them. Pure.
 * Returns [[text, [delta, ...]], ...] for runs of two or more.
 */
export function repeatRuns(messages, botUserId, gap = 600) {
  const said = new Map();
  for (const m of messages ?? []) {
    const ts = String((m ?? {}).ts ?? '');
    const author = (m ?? {}).user ?? '';
    const isApp = (botUserId && author === botUserId) || (m ?? {}).bot_id;
    const text = String((m ?? {}).text ?? '').trim().toLowerCase();
    if (!ts || !isApp || !text) continue;
    if (!said.has(text)) said.set(text, []);
    said.get(text).push(Number(ts));
  }
  const runs = [];
  const deltas = (run) => run.slice(1).map((b, i) => b - run[i]);
  for (const [text, stamps] of said) {
    stamps.sort((a, b) => a - b);
    let current = [stamps[0]];
    for (const ts of stamps.slice(1)) {
      if (ts - current[current.length - 1] <= Number(gap)) current.push(ts);
      else {
        if (current.length > 1) runs.push([text, deltas(current)]);
        current = [ts];
      }
    }
    if (current.length > 1) runs.push([text, deltas(current)]);
  }
  return runs.sort((a, b) => (a[0] < b[0] ? -1 : 1));
}

/** What produced this run of identical answers? Pure. */
export function spacingKind(deltas) {
  const gaps = (deltas ?? []).map(Number);
  if (!gaps.length) return 'single';
  if (gaps.every((g) => g < SIMULTANEOUS_SECONDS)) return 'simultaneous';
  for (const g of gaps) {
    for (const expected of RETRY_SPACINGS) {
      if (Math.abs(g - expected) <= expected * RETRY_TOLERANCE) return 'retry';
    }
  }
  return 'spread';
}

/** Which failure is this? Pure. Returns [verdict, detail]. */
export function fingerprint(mix, kinds) {
  const m = mix ?? {};
  const many = Number(m.many) || 0;
  const none = Number(m.none) || 0;
  const seen = kinds ?? [];
  if (many && none) {
    return ['several-live-connections',
      'duplicates and misses in the same channel. A retry landing on a different '
      + 'instance from its original is handled twice, and a payload routed to an '
      + 'instance that is restarting is handled by nobody'];
  }
  if (many && seen.includes('retry')) {
    return ['retries-one-listener',
      'duplicates at Slack retry intervals with nothing dropped. One listener that '
      + 'did not acknowledge in time, which is a different note'];
  }
  if (many && seen.includes('simultaneous')) {
    return ['double-subscription',
      'duplicates under a second apart with nothing dropped. Two subscriptions '
      + 'delivering the same conversation, not two connections'];
  }
  if (many) {
    return ['duplicates-unclassified',
      'repeats that match neither the retry schedule nor a simultaneous pair; read '
      + 'the runs before concluding anything'];
  }
  if (none) {
    return ['losses-only',
      'drops with no duplicates. Each payload still went to exactly one place, so '
      + 'look at the connection cap or a mishandled refresh'];
  }
  return ['clean', 'every trigger in this window got exactly one answer'];
}

function arg(args, name, fallback = null) {
  const i = args.indexOf(name);
  return i === -1 ? fallback : args[i + 1];
}

async function pageHistory(headers, channel, limit, maxPages) {
  const out = [];
  let cursor = '';
  for (let page = 0; page < maxPages; page += 1) {
    const params = new URLSearchParams({ channel, limit: String(limit) });
    if (cursor) params.set('cursor', cursor);
    const body = await (await fetch(`${API}conversations.history?${params}`,
      { headers })).json();
    if (body.ok !== true) {
      console.error(`history    unavailable    ${body.error}`);
      return out;
    }
    out.push(...(body.messages ?? []));
    cursor = (body.response_metadata ?? {}).next_cursor ?? '';
    if (!cursor) break;
  }
  return out;
}

async function main() {
  const args = process.argv.slice(2);
  const tokenEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
  const token = process.env[tokenEnv];
  const channel = arg(args, '--channel', '');
  if (!token || !channel) {
    console.error(`set ${tokenEnv} to a bot token with channels:history, and pass `
      + '--channel');
    process.exitCode = 2;
    return;
  }
  const headers = { Authorization: `Bearer ${token}` };
  const who = await (await fetch(`${API}auth.test`, { headers })).json();
  if (who.ok !== true) {
    console.error(`auth.test  unavailable    ${who.error}`);
    process.exitCode = 2;
    return;
  }
  console.log(`identity   ${who.user_id} (${who.user}) in ${who.team}`);

  const window = Number(arg(args, '--window', '45'));
  const replicas = Number(arg(args, '--replicas', '1'));
  const messages = await pageHistory(headers, channel,
    Number(arg(args, '--limit', '200')), Number(arg(args, '--max-pages', '5')));
  const counts = replyCounts(messages, who.user_id, window);
  const [mix, fraction] = outcomeMix(counts);
  console.log(`triggers   ${mix.total} mention(s) read, answered inside ${window}s`);
  if (!mix.total) {
    console.log('verdict    nothing to measure; no mentions in the window read');
    return;
  }
  console.log(`outcome    none ${mix.none}   once ${mix.once}   many ${mix.many}   of `
    + `${mix.total}`);
  console.log(`exactly-once   ${fraction}`);

  const runs = repeatRuns(messages, who.user_id, Number(arg(args, '--repeat-gap',
    '600')));
  const kinds = runs.map(([, deltas]) => spacingKind(deltas));
  for (const kind of [...new Set(kinds)].sort()) {
    console.log(`spacing    ${kind.padEnd(12)} `
      + `${kinds.filter((k) => k === kind).length} run(s) of repeated answers`);
  }

  const [verdict, detail] = fingerprint(mix, kinds);
  if (verdict !== 'several-live-connections') {
    console.log(`verdict    ${verdict.padEnd(12)} ${detail}`);
    return;
  }
  console.warn(`verdict    ${verdict}  ${detail}`);
  console.warn(`replicas   ${replicas} replica(s) hold a connection, so a payload has `
    + `${replicas} places to land and ${Math.max(0, replicas - 1)} of them are wrong `
    + 'at any moment');
  console.warn('  repair: run Socket Mode as a singleton and enqueue payloads into a '
    + 'queue you control; scale the workers, not the receiver');
  console.warn('  repair: a dedupe cache in process memory cannot see the copy another '
    + 'instance handled; if instances must be plural, share it');
  console.warn('  repair: for genuinely multi-node ingress use the HTTP Events API '
    + 'behind a load balancer, which does distribute');
  console.warn('  note:   nothing here opened a connection; counting them would '
    + 'consume one of the ten this app is allowed');
  process.exitCode = 1;
}

// Only run when invoked directly, so importing this module in the tests does
// not execute main() and fail the file on a missing token.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Every test here is about a boundary between this note and one of its neighbours, because the evidence is nearly the same in all of them and only the combination differs. Duplicates with drops must come back as several connections; the same duplicates without drops must come back as retries or as a double subscription, depending on their spacing; drops without duplicates must be handed to the connection cap. <code>outcome_mix</code> is tested for the fraction on a clean run, which has to be exactly one, because a check that cannot say <em>this is fine</em> is not usable on a healthy app.",
"test_py_file": "test_slack_socket_replica_fingerprint.py",
"test_py": '''from slack_socket_replica_fingerprint import (
    fingerprint, outcome_mix, repeat_runs, reply_counts, spacing_kind,
)


def test_a_mention_answered_once_counts_once():
    msgs = [{"ts": "100", "user": "U1", "text": "<@UBOT> go"},
            {"ts": "110", "user": "UBOT", "text": "on it"}]
    assert reply_counts(msgs, "UBOT", 45) == [(100.0, 1)]


def test_two_answers_inside_the_window_count_as_two():
    msgs = [{"ts": "100", "user": "U1", "text": "<@UBOT> go"},
            {"ts": "110", "user": "UBOT", "text": "on it"},
            {"ts": "111", "bot_id": "B1", "text": "on it"}]
    assert reply_counts(msgs, "UBOT", 45) == [(100.0, 2)]


def test_a_mention_with_nothing_after_it_counts_as_zero():
    msgs = [{"ts": "100", "user": "U1", "text": "<@UBOT> go"}]
    assert reply_counts(msgs, "UBOT", 45) == [(100.0, 0)]


def test_a_clean_run_is_exactly_one():
    mix, fraction = outcome_mix([(1, 1), (2, 1), (3, 1)])
    assert mix == {"none": 0, "once": 3, "many": 0, "total": 3}
    assert fraction == 1.0


def test_the_fraction_falls_for_drops_and_for_duplicates_alike():
    _mix, fraction = outcome_mix([(1, 0), (2, 1), (3, 2), (4, 1)])
    assert fraction == 0.5


def test_an_empty_window_divides_by_nothing():
    assert outcome_mix([]) == ({"none": 0, "once": 0, "many": 0, "total": 0}, 0.0)


def test_identical_answers_close_together_are_one_run():
    msgs = [{"ts": "100", "user": "UBOT", "text": "Done"},
            {"ts": "100.4", "user": "UBOT", "text": "done"}]
    runs = repeat_runs(msgs, "UBOT", 600)
    assert len(runs) == 1
    assert round(runs[0][1][0], 1) == 0.4


def test_a_single_answer_is_not_a_run():
    assert repeat_runs([{"ts": "100", "user": "UBOT", "text": "done"}], "UBOT") == []


def test_the_same_answer_hours_apart_is_two_separate_runs_of_one():
    msgs = [{"ts": "100", "user": "UBOT", "text": "done"},
            {"ts": "99999", "user": "UBOT", "text": "done"}]
    assert repeat_runs(msgs, "UBOT", 600) == []


def test_human_messages_are_never_counted_as_repeats():
    msgs = [{"ts": "100", "user": "U1", "text": "same"},
            {"ts": "101", "user": "U2", "text": "same"}]
    assert repeat_runs(msgs, "UBOT") == []


def test_sub_second_repeats_are_simultaneous():
    assert spacing_kind([0.2, 0.4]) == "simultaneous"


def test_a_one_minute_gap_is_slacks_retry_schedule():
    assert spacing_kind([61.0]) == "retry"
    assert spacing_kind([290.0]) == "retry"


def test_a_gap_that_is_neither_says_nothing_on_its_own():
    assert spacing_kind([17.0]) == "spread"
    assert spacing_kind([]) == "single"


def test_duplicates_beside_drops_is_this_note():
    verdict, detail = fingerprint({"none": 4, "once": 60, "many": 6, "total": 70},
                                  ["retry", "simultaneous"])
    assert verdict == "several-live-connections"
    assert "different instance" in detail


def test_retry_spaced_duplicates_without_drops_belong_to_the_retry_note():
    assert fingerprint({"none": 0, "once": 60, "many": 6, "total": 66},
                       ["retry"])[0] == "retries-one-listener"


def test_simultaneous_duplicates_without_drops_are_a_double_subscription():
    assert fingerprint({"none": 0, "once": 60, "many": 6, "total": 66},
                       ["simultaneous"])[0] == "double-subscription"


def test_drops_without_duplicates_are_handed_to_the_cap_note():
    verdict, detail = fingerprint({"none": 9, "once": 60, "many": 0, "total": 69}, [])
    assert verdict == "losses-only"
    assert "connection cap" in detail


def test_repeats_that_match_no_pattern_are_left_unclassified():
    assert fingerprint({"none": 0, "once": 5, "many": 2, "total": 7},
                       ["spread"])[0] == "duplicates-unclassified"


def test_a_healthy_channel_is_reported_as_clean():
    assert fingerprint({"none": 0, "once": 70, "many": 0, "total": 70}, [])[0] == "clean"
    assert fingerprint({}, [])[0] == "clean"
''',
"test_js_file": "slack-socket-replica-fingerprint.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  fingerprint, outcomeMix, repeatRuns, replyCounts, spacingKind,
} from './slack-socket-replica-fingerprint.mjs';

test('a mention answered once counts once', () => {
  const msgs = [{ ts: '100', user: 'U1', text: '<@UBOT> go' },
    { ts: '110', user: 'UBOT', text: 'on it' }];
  assert.deepEqual(replyCounts(msgs, 'UBOT', 45), [[100, 1]]);
});

test('two answers inside the window count as two', () => {
  const msgs = [{ ts: '100', user: 'U1', text: '<@UBOT> go' },
    { ts: '110', user: 'UBOT', text: 'on it' },
    { ts: '111', bot_id: 'B1', text: 'on it' }];
  assert.deepEqual(replyCounts(msgs, 'UBOT', 45), [[100, 2]]);
});

test('a mention with nothing after it counts as zero', () => {
  const msgs = [{ ts: '100', user: 'U1', text: '<@UBOT> go' }];
  assert.deepEqual(replyCounts(msgs, 'UBOT', 45), [[100, 0]]);
});

test('a clean run is exactly one', () => {
  const [mix, fraction] = outcomeMix([[1, 1], [2, 1], [3, 1]]);
  assert.deepEqual(mix, {
    none: 0, once: 3, many: 0, total: 3,
  });
  assert.equal(fraction, 1);
});

test('the fraction falls for drops and for duplicates alike', () => {
  const [, fraction] = outcomeMix([[1, 0], [2, 1], [3, 2], [4, 1]]);
  assert.equal(fraction, 0.5);
});

test('an empty window divides by nothing', () => {
  assert.deepEqual(outcomeMix([]), [{
    none: 0, once: 0, many: 0, total: 0,
  }, 0]);
});

test('identical answers close together are one run', () => {
  const msgs = [{ ts: '100', user: 'UBOT', text: 'Done' },
    { ts: '100.4', user: 'UBOT', text: 'done' }];
  const runs = repeatRuns(msgs, 'UBOT', 600);
  assert.equal(runs.length, 1);
  assert.equal(Math.round(runs[0][1][0] * 10) / 10, 0.4);
});

test('a single answer is not a run', () => {
  assert.deepEqual(repeatRuns([{ ts: '100', user: 'UBOT', text: 'done' }], 'UBOT'), []);
});

test('the same answer hours apart is two separate runs of one', () => {
  const msgs = [{ ts: '100', user: 'UBOT', text: 'done' },
    { ts: '99999', user: 'UBOT', text: 'done' }];
  assert.deepEqual(repeatRuns(msgs, 'UBOT', 600), []);
});

test('human messages are never counted as repeats', () => {
  const msgs = [{ ts: '100', user: 'U1', text: 'same' },
    { ts: '101', user: 'U2', text: 'same' }];
  assert.deepEqual(repeatRuns(msgs, 'UBOT'), []);
});

test('sub second repeats are simultaneous', () => {
  assert.equal(spacingKind([0.2, 0.4]), 'simultaneous');
});

test('a one minute gap is Slack retry schedule', () => {
  assert.equal(spacingKind([61]), 'retry');
  assert.equal(spacingKind([290]), 'retry');
});

test('a gap that is neither says nothing on its own', () => {
  assert.equal(spacingKind([17]), 'spread');
  assert.equal(spacingKind([]), 'single');
});

test('duplicates beside drops is this note', () => {
  const [verdict, detail] = fingerprint({
    none: 4, once: 60, many: 6, total: 70,
  }, ['retry', 'simultaneous']);
  assert.equal(verdict, 'several-live-connections');
  assert.match(detail, /different instance/);
});

test('retry spaced duplicates without drops belong to the retry note', () => {
  assert.equal(fingerprint({
    none: 0, once: 60, many: 6, total: 66,
  }, ['retry'])[0], 'retries-one-listener');
});

test('simultaneous duplicates without drops are a double subscription', () => {
  assert.equal(fingerprint({
    none: 0, once: 60, many: 6, total: 66,
  }, ['simultaneous'])[0], 'double-subscription');
});

test('drops without duplicates are handed to the cap note', () => {
  const [verdict, detail] = fingerprint({
    none: 9, once: 60, many: 0, total: 69,
  }, []);
  assert.equal(verdict, 'losses-only');
  assert.match(detail, /connection cap/);
});

test('repeats that match no pattern are left unclassified', () => {
  assert.equal(fingerprint({
    none: 0, once: 5, many: 2, total: 7,
  }, ['spread'])[0], 'duplicates-unclassified');
});

test('a healthy channel is reported as clean', () => {
  assert.equal(fingerprint({
    none: 0, once: 70, many: 0, total: 70,
  }, [])[0], 'clean');
  assert.equal(fingerprint({}, [])[0], 'clean');
});
''',
"faq": [
 ("Does Slack really not distribute payloads across connections?",
  "It routes each payload to one of the open connections, and the documentation is explicit that there is no predictable distribution pattern. That is a routing decision, not a work-sharing contract: there is no consumer group, no acknowledgement-based redelivery to a different consumer, and no ordering guarantee. Two connections do not mean half the load each; they mean two places a payload might arrive, one of which is chosen for you."),
 ("Why do duplicates happen at all if each payload goes to one connection?",
  "Because retries are separate deliveries. When an event is not acknowledged in time Slack sends it again, and with several connections open the retry can be routed to a different instance from the original. The first instance may well have finished the work; the second has no idea it exists. That is also why a dedupe cache in process memory does not help: neither instance ever saw both copies, so both are correct in believing the payload is new."),
 ("Would a shared Redis dedupe cache fix it?",
  "It fixes the duplicates and leaves the drops. A payload routed to an instance that is restarting, draining or wedged is not redelivered anywhere, and no cache can recover something that was never received. It is also worth noticing what a shared cache costs: at that point you have built a coordination layer in front of a transport chosen specifically to avoid needing infrastructure. One receiver and a queue you control is less code and loses nothing."),
 ("How is this different from the note about duplicate processing on retry?",
  "By the drops. A single listener that mishandles retries produces duplicates and no misses, because every payload still reaches the one process that exists. Several live connections produce duplicates and misses together, in the same channel, in the same hour. The script checks for the combination and, when it finds duplicates without drops, sends you to the retry note instead of claiming this one."),
 ("We need more than one instance for availability. What then?",
  "Keep one Socket Mode receiver and make it cheap to restart, so a failure is a short gap rather than a lost workload, and run your redundancy behind it: the receiver acknowledges and enqueues, and as many workers as you like drain the queue. If you need genuinely redundant ingress with no single receiver, that is the case for the HTTP Events API, where a load balancer distributes deliveries properly and the connection budget stops being a factor."),
],
"related": [
 ("/slack/duplicate-processing-on-retry/", "the same duplicates without the drops"),
 ("/slack/app-mention-vs-message-double-fire/", "two subscriptions rather than two connections"),
 ("/slack/duplicate-messages-no-dedupe/", "the key that stops a repeat becoming a second message"),
],
"citations": [CITE_SOCKET_MODE, CITE_BOLT_2487, CITE_BOLT_PY_445, CITE_CONV_HISTORY],
})

