#!/usr/bin/env python3
"""/slack/ field notes, batch V - the writing.

Four notes about the app configuration screen, separated by which promise it
quietly fails to keep.

The first is an app with no transport at all. Socket Mode is off, no Request
URL replaced it, and Slack has nowhere to put an event, so it drops them.
The sibling note on this section owns the opposite arrangement - both
transports live at once, and events arriving twice - and names this state only
in passing. Here it is worked out: which surfaces went dark and which kept a
URL of their own, how many subscriptions the manifest declares that can never
arrive, and the date the app's own posting series ended.

The second is an app with a transport and half a configuration. Events arrive,
mentions get answered, buttons render exactly as they should, and clicking one
does nothing at all, because Interactivity is a separate switch on a separate
screen with a separate URL and nobody ever turned it on. The reading is an
asymmetry between two surfaces of one app, which is a different statistic from
the first note's total silence.

The third is an app that exists twice. There is a manifest in the repository
and a manifest in production, they are not the same document, and neither one
knows about the other. This note diffs them - actually diffs them, path by
path, with the arrays sorted so a reordering is not a finding - and then adds
the third column nobody remembers, which is the scope set the installed token
is actually carrying. Three lists that drift independently.

The fourth is an app that was never let out. It is not blocked from being
distributed, which is the neighbouring note and a different failure entirely:
its transport is fine, its code is fine, and public distribution is simply a
gate that nobody walked through. No redirect URL, one workspace, and a bot
token in an environment variable where an installation store needs to be.

Read only throughout. Every manifest here is read with apps.manifest.export,
which is a read; apps.manifest.update appears in the printed repairs and in no
script. Nothing opens a socket, nothing sends anything to a Request URL, and
nothing writes a manifest back.
"""

CITE_MANIFEST_EXPORT = ("apps.manifest.export method reference - Slack Docs",
                        "https://docs.slack.dev/reference/methods/apps.manifest.export")
CITE_MANIFEST_UPDATE = ("apps.manifest.update method reference - Slack Docs",
                        "https://docs.slack.dev/reference/methods/apps.manifest.update")
CITE_MANIFESTS = ("App manifests - Slack Docs",
                  "https://docs.slack.dev/reference/manifests")
CITE_SOCKET_MODE = ("Using Socket Mode - Slack Docs",
                    "https://docs.slack.dev/apis/events-api/using-socket-mode")
CITE_EVENTS_API = ("Events API - Slack Docs", "https://docs.slack.dev/apis/events-api/")
CITE_INTERACTIVITY = ("Handling user interaction - Slack Docs",
                      "https://docs.slack.dev/interactivity/handling-user-interaction")
CITE_OAUTH_INSTALL = ("Installing with OAuth - Slack Docs",
                      "https://docs.slack.dev/authentication/installing-with-oauth")
CITE_AUTH_TEST = ("auth.test method reference - Slack Docs",
                  "https://docs.slack.dev/reference/methods/auth.test")
CITE_CONV_HISTORY = ("conversations.history method reference - Slack Docs",
                     "https://docs.slack.dev/reference/methods/conversations.history")
CITE_TOOLING_ROTATE = ("tooling.tokens.rotate method reference - Slack Docs",
                       "https://docs.slack.dev/reference/methods/tooling.tokens.rotate")
CITE_BOLT_2437 = ("bolt-js #2437: the deployed manifest and the checked-in one diverge",
                  "https://github.com/slackapi/bolt-js/issues/2437")
CITE_JAVA_1189 = ("java-slack-sdk #1189: block actions never reach the handler",
                  "https://github.com/slackapi/java-slack-sdk/issues/1189")
CITE_SO_INTERACTIVITY = ("Stack Overflow 73738612: Slack button click does nothing",
                         "https://stackoverflow.com/questions/73738612")
CITE_SO_DISTRIBUTION = ("Stack Overflow 45523707: installing a Slack app in another "
                        "workspace",
                        "https://stackoverflow.com/questions/45523707")

GUIDES = []

GUIDES.append({
"slug": "socket-mode-off-but-no-request-url",
"title": "Socket Mode off, no Request URL, and nowhere to deliver",
"description": "Delivery needs exactly one transport and there is no fallback between them. Count the transports in the manifest, then find the date the app went quiet.",
"h1": "Socket Mode off, no Request URL, and nowhere to deliver",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack socket mode disabled no events",
             "slack app stopped receiving events after toggle",
             "slack link_disabled reconnect loop",
             "slack no request url event subscriptions",
             "slack app silent no errors anywhere"],
"deps": "Python 3.9+ with requests, or Node.js 18+; an app configuration token with app_configurations:read for the manifest, and a bot token with channels:history to date the silence",
"lead": "Somebody turned Socket Mode off. It was a reasonable thing to do &mdash; the team is preparing to submit the app, and a listed app has to receive events over HTTPS, so the switch had to move eventually. It moved on a Thursday afternoon and nothing happened, which everyone took as a good sign.</p><p>Nine days later a support ticket says the release bot has not announced a release since the 12th. It has not. It has not done anything since the 12th. There is no error in the logs, no failed delivery, no alert, no red banner on the configuration screen. The app is running, healthy, subscribed to fourteen events, and Slack has had nowhere to send a single one of them since the switch moved.",
"short_answer": """<p>Event delivery needs <strong>exactly one</strong> transport, and Slack does not fall back from one to the other. Either Socket Mode is on and your process holds a WebSocket, or an HTTPS Request URL is configured and verified and Slack posts to it. Turning Socket Mode off does not promote a Request URL, because there may not be one &mdash; and when there is not, Slack has no destination for your app's events and drops them where they are.</p>
<p>The finding is two fields held against each other. <code>apps.manifest.export?app_id=A...</code> returns <code>settings.socket_mode_enabled</code> and <code>settings.event_subscriptions.request_url</code>. <strong>Both false and empty, with a populated <code>bot_events[]</code>, is the whole diagnosis</strong>: the app is asking Slack for fourteen kinds of traffic and has given Slack no way to hand any of it over.</p>
<p>The consequence is not uniform, which is why it gets misread. Interactivity carries its own <code>request_url</code>, and every slash command carries a <code>url</code> of its own, so a command configured back when the app spoke HTTP keeps working while events go dark. The app is half alive, and the half that still answers is the half people test with.</p>
<p>The workspace dates it for you. The app's own message series does not thin out or start missing a fraction &mdash; it <strong>ends</strong>, at a timestamp you can hand to whoever reads the audit log. The script below measures that as a rate change rather than as unanswered mentions, because a transport that was removed produces a cliff and a transport that is struggling produces a slope.</p>""",
"problem": """<p>The reason this survives for days is that every part of it reports success. The process starts. The manifest is valid. The subscriptions are still listed on the Event Subscriptions screen, all fourteen of them, in a box that looks exactly as it did last week. No call fails, because your app is not making any &mdash; it is waiting to be called, and nothing is calling.</p>
<p>If the app was running a Socket Mode client when the switch moved, there is one signal and it is easy to throw away. The client's next connection attempt comes back with a disconnect whose reason is <code>link_disabled</code>, which means precisely &ldquo;Socket Mode is off for this app and reconnecting will never work.&rdquo; A client that treats every disconnect as weather retries it forever at one line of <code>INFO</code> per attempt. The signal exists, it is correct, it is specific, and it is indistinguishable in a log viewer from the reconnect chatter of a perfectly healthy service.</p>
<p>The half-alive shape does the rest of the damage. Slash commands each store their own URL, so <code>/deploy</code> still opens its dialog and the on-call engineer concludes that the app is up. Interactivity stores its own URL too, so if that one was set the buttons keep working. What has actually stopped is one specific surface &mdash; the events subscription, the only surface with no URL of its own to fall back on &mdash; and the events surface is the one nobody clicks.</p>
<p>Then there is the direction of the mistake. Teams arrive at this state while doing the right thing: moving off Socket Mode because a Marketplace listing requires it, or turning the switch off to test the HTTP path, or copying a manifest between apps and dropping a field. Nobody sets out to configure zero transports. It happens because the two settings live on two screens and neither screen mentions the other, so it is entirely possible to remove the last route into your application without any single click looking wrong.</p>""",
"why": """<p><strong>Zero is a state, and it needs to be counted rather than inferred.</strong> The check is not &ldquo;is Socket Mode on&rdquo; and it is not &ldquo;is there a Request URL&rdquo;. It is how many transports there are, and the answer has four values: none, socket, http, both. One is healthy. Two is the note on <a href="/slack/socket-mode-and-request-url-both-on/">both delivery paths at once</a>, which names this state in passing and is about the opposite problem. Zero is this note, and it is the only one of the four that produces silence.</p>
<p><strong>Surfaces do not all fail together, so the script reports them one at a time.</strong> The events subscription has no URL of its own. Interactivity has one. Every slash command has one. That asymmetry is the difference between an engineer concluding &ldquo;the app is down&rdquo; and concluding &ldquo;the app is up, therefore this is not a configuration problem&rdquo; &mdash; and the second conclusion is the one that costs a week. Reporting per surface makes the half-alive shape visible instead of confusing.</p>
<p><strong>The declaration count is the part that makes it undeniable.</strong> An empty <code>bot_events[]</code> beside no transport is an app that does nothing and was never meant to; that is the <a href="/slack/no-event-subscriptions/">nothing subscribed</a> note, and it is the exact inverse of this one. A <em>populated</em> <code>bot_events[]</code> beside no transport is a contradiction the app is carrying in writing: it has told Slack which events it wants and given Slack nowhere to put them. The script prints the number and the names.</p>
<p><strong>A cliff is a different statistic from a gap, and only one of them dates the change.</strong> Counting unanswered mentions tells you the app is not replying. Measuring the app's own posting rate before and after tells you <em>when it stopped</em> and how confident you can be that it stopped rather than paused: an app that posted four times a day for a month and has posted nothing for nine days is not slow. The output is a timestamp somebody can take to the audit log and match against who moved which switch.</p>
<p><strong>Nothing here dials your Request URL, because there is no Request URL to dial.</strong> That is the point of the note. Where a URL does exist and is broken, the question is whether it verified (a <a href="/slack/request-url-unverified/">handshake that failed</a>) or whether it points at a laptop that closed (a <a href="/slack/http-or-dead-tunnel-request-url/">tunnel that died</a>). Both of those notes are about the quality of a string. This one is about the absence of the string.</p>
<p><strong>The repair is an assertion, not a setting.</strong> Setting the switch back takes ten seconds and does not stop it happening again, because the same two screens will still be there next quarter. An app that reads its own manifest at startup and refuses to boot with zero transports turns a nine-day silence into a failed deploy, which is the only version of this failure anybody notices in time.</p>""",
"steps": [
 {"h": "Count the transports rather than checking either one",
  "body": """<p><code>transport_state</code> reads <code>settings.socket_mode_enabled</code> and <code>settings.event_subscriptions.request_url</code> together and returns <code>none</code>, <code>socket</code>, <code>http</code> or <code>both</code>. Four states, one of which is healthy, one of which is this note and one of which is a different note. A boolean check on either field alone cannot tell those apart.</p>"""},
 {"h": "Say which surfaces went dark and which kept a route",
  "body": """<p><code>dark_surfaces</code> walks the events subscription, interactivity and every slash command, and marks each <code>dark</code>, <code>routed</code> or <code>absent</code>. Slash commands and interactivity carry URLs of their own; the events subscription does not. This is why the app looks up while being deaf, and printing it per surface is what stops the investigation going the wrong way.</p>"""},
 {"h": "Count what the app has declared it can never receive",
  "body": """<p><code>undeliverable_declarations</code> counts <code>bot_events[]</code> plus <code>user_events[]</code> and names them. A populated subscription list beside a transport count of zero is the app contradicting itself in its own configuration, and it is the sentence to put in the incident notes.</p>"""},
 {"h": "Date the cliff from the app's own messages",
  "body": """<p><code>posting_cliff</code> takes the timestamps of the app's own messages and the timestamp of the newest message in the channel, and returns <code>cliff</code> with a date, <code>steady</code>, <code>never-posted</code> or <code>sparse</code>. The test is the quiet period measured in the app's own average gap, so a chatty app and a once-a-week app are judged on their own habits rather than against a fixed threshold.</p>"""},
 {"h": "Read the disconnect reason if a client was running",
  "body": """<p>If a Socket Mode client was live when the switch moved, its log holds <code>link_disabled</code>, which means the setting was turned off rather than the network having a bad day. Pass it with <code>--disconnect-reason</code> and the script grades the finding as confirmed rather than inferred. Absent, the manifest still settles it.</p>"""},
 {"h": "Make a transport count of zero a failed deploy",
  "body": """<p>The printed repair is a startup assertion: read your own manifest with a configuration token, count the transports, and refuse to boot on zero. It costs one call at startup and converts the entire failure mode from a silence somebody reports in nine days into a crash loop somebody sees in nine seconds.</p>"""},
],
"verify": """<p>Turn the switch back on, or configure and verify a Request URL, and run it again. The two lines to watch are <code>transport</code>, which should read <code>socket</code> or <code>http</code>, and <code>cliff</code>, which should have stopped being a cliff.</p>
<pre><code class="language-bash">python3 slack_event_transport.py --app-id A05RELB0T --channel C05REL9QT \\
    --disconnect-reason link_disabled
# manifest   socket mode off, event Request URL: not set
# transport  none            neither transport is configured, so Slack has no
#                            destination for this app's events and drops them
# declared   14 subscription(s) that cannot arrive: app_mention, message.channels,
#            reaction_added, team_join, ...
# surface    event subscriptions  dark    14 subscription(s) and no route of its own
# surface    interactivity        dark    enabled with an empty request_url
# surface    /deploy              routed  carries its own URL, so it still answers
# surface    /rollback            routed  carries its own URL, so it still answers
# disconnect link_disabled   Socket Mode was switched off underneath a running client
# identity   U07BOT9QD (releasebot) in Northwind
# history    486 message(s) from C05REL9QT
# cliff      cliff           4.1 message(s) a day for 31 days, then nothing for 9.2
#                            days; the series ends at 1755012340.000200
# verdict    the app declares 14 event(s) and has nowhere to receive them
#   repair: switch Socket Mode back on, or configure and verify an HTTPS Request URL
#   repair: assert the transport count at startup and refuse to boot on zero</code></pre>""",
"code_intro": "The whole diagnosis is <code>transport_state</code>, and it is deliberately a count rather than a pair of booleans, because the four values are four different notes. Everything after it exists to make the count believable to somebody who did not run it: <code>dark_surfaces</code> explains why the app still answers <code>/deploy</code>, <code>undeliverable_declarations</code> turns the contradiction into a number, and <code>posting_cliff</code> puts a date on it. Three reads, all GETs, none of them aimed at your own endpoint.",
"py_file": "slack_event_transport.py",
"py": '''"""Decide whether Slack has anywhere to deliver this app's events.

Read only. apps.manifest.export, auth.test and conversations.history are reads.
Nothing here writes a manifest, opens a socket, or sends anything at all to a
Request URL - there is no Request URL to send to, which is the finding.

Delivery needs exactly one transport: Socket Mode on and a WebSocket held, or
an HTTPS Request URL configured and verified. There is no fallback between
them. Switching Socket Mode off does not promote the Request URL, because there
may not be one, and Slack drops what it cannot deliver.
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_event_transport")

API = "https://slack.com/api/"

DAY = 86400.0

# How much quiet, measured in the app's own average gap between messages, counts
# as the series having ended rather than merely being slow. Six is generous on
# purpose: an app that posts four times a day has to be silent for a day and a
# half before this script will call it a cliff.
QUIET_MULTIPLE = 6.0
# ...and never less than an hour, so a chatty app that paused over lunch is not
# reported as dead.
QUIET_FLOOR = 3600.0

# The one disconnect reason that means the setting moved rather than the network
# wobbled. A client that treats it as transient reconnects forever.
DISCONNECT_REASONS = {
    "link_disabled": ("confirmed",
                      "Socket Mode was switched off for this app while a client was "
                      "connected. Reconnecting will never succeed"),
    "refresh_requested": ("unrelated",
                          "a routine scheduled refresh, which every long-lived "
                          "connection gets. Not this note"),
    "too_many_websockets": ("unrelated",
                            "the ten connection cap, which is a different note. "
                            "Socket Mode is on in that case, not off"),
    "warning": ("unrelated",
                "the ten second notice before a scheduled refresh. Not a failure"),
}


def transport_state(manifest):
    """How many transports can deliver an event to this app? Pure.

    Returns (state, detail, facts). The four states are four different notes,
    which is why this is a count and not a pair of boolean checks:

      none    neither is configured. Slack has no destination and drops events.
      socket  Socket Mode only. One of the two supported shapes.
      http    a Request URL only. The other supported shape.
      both    the switch is on and a URL is still stored underneath it, so two
              paths exist and duplicates follow. A different note entirely.
      unknown no manifest was available to read.
    """
    if manifest is None:
        return ("unknown", "no manifest was read, so the transports cannot be "
                           "counted; an app configuration token is what reads them",
                {})
    settings = manifest.get("settings") or {}
    socket = bool(settings.get("socket_mode_enabled"))
    events = settings.get("event_subscriptions") or {}
    url = str(events.get("request_url") or "").strip()
    facts = {"socket_mode": socket, "request_url": url}
    if socket and url:
        return ("both", "Socket Mode is on and a Request URL is still stored "
                        "underneath it; that is two delivery paths, not none", facts)
    if socket:
        return ("socket", "Socket Mode carries every event, interaction and command",
                facts)
    if url:
        return ("http", "events are delivered to the stored Request URL", facts)
    return ("none", "neither transport is configured, so Slack has no destination "
                    "for this app's events and drops them", facts)


def dark_surfaces(manifest):
    """Which inbound surfaces still have a route, and which do not? Pure.

    Returns [(surface, state, detail), ...] with state dark, routed or absent.

    They do not fail together, and that is the whole reason this failure is
    misread. The events subscription has no URL of its own; interactivity keeps
    one; every slash command keeps one. Turn Socket Mode off and the commands
    carry on answering while events stop, so the app looks up and is deaf.
    """
    if manifest is None:
        return []
    settings = manifest.get("settings") or {}
    features = manifest.get("features") or {}
    socket = bool(settings.get("socket_mode_enabled"))
    out = []

    events = settings.get("event_subscriptions") or {}
    declared = list(events.get("bot_events") or []) + list(events.get("user_events") or [])
    events_url = str(events.get("request_url") or "").strip()
    if not declared:
        out.append(("event subscriptions", "absent", "nothing is subscribed"))
    elif socket:
        out.append(("event subscriptions", "routed", "the socket carries them"))
    elif events_url:
        out.append(("event subscriptions", "routed", "a Request URL of its own"))
    else:
        out.append(("event subscriptions", "dark",
                    "%d subscription(s) and no route of its own" % len(declared)))

    inter = settings.get("interactivity") or {}
    inter_url = str(inter.get("request_url") or "").strip()
    if not inter.get("is_enabled"):
        out.append(("interactivity", "absent", "the switch is off"))
    elif socket:
        out.append(("interactivity", "routed", "the socket carries clicks too"))
    elif inter_url:
        out.append(("interactivity", "routed", "carries its own URL"))
    else:
        out.append(("interactivity", "dark", "enabled with an empty request_url"))

    for cmd in features.get("slash_commands") or []:
        name = str((cmd or {}).get("command") or "?")
        cmd_url = str((cmd or {}).get("url") or "").strip()
        if socket:
            out.append((name, "routed", "the socket carries commands too"))
        elif cmd_url:
            out.append((name, "routed", "carries its own URL, so it still answers"))
        else:
            out.append((name, "dark", "no URL of its own and no socket"))
    return out


def undeliverable_declarations(manifest, state):
    """What has the app asked for that it cannot receive? Pure.

    Returns (count, names). Only meaningful when the transport count is zero: a
    populated subscription list beside no transport is the app contradicting
    itself in writing, and an empty one is a different note about an app that
    subscribes to nothing at all.
    """
    if manifest is None or state != "none":
        return (0, [])
    events = (manifest.get("settings") or {}).get("event_subscriptions") or {}
    names = sorted({str(e) for e in (list(events.get("bot_events") or [])
                                     + list(events.get("user_events") or []))})
    return (len(names), names)


def posting_cliff(app_timestamps, newest_ts, min_messages=4):
    """Did the app's own message series end, and when? Pure.

    Returns (state, detail, facts). States:

      cliff        a steady rate, then quiet for far longer than that rate
                   predicts. A transport that was removed ends the series.
      steady       the app is still posting near the end of the window.
      never-posted the app has posted nothing in what was read.
      sparse       too few messages to measure a rate honestly.

    A rate change rather than a count of unanswered mentions, on purpose. A
    transport that struggles produces a slope and loses a fraction; a transport
    that was removed produces a step, and the step has a date on it that can be
    matched against whoever moved the switch.
    """
    stamps = sorted(float(t) for t in (app_timestamps or []))
    now = float(newest_ts or 0.0)
    facts = {"messages": len(stamps)}
    if not stamps:
        return ("never-posted", "the app has posted nothing in the messages read, so "
                                "there is no series to have ended", facts)
    if len(stamps) < max(2, min_messages):
        return ("sparse", "%d message(s) from the app is too few to measure a rate "
                          "against" % len(stamps), facts)
    span = stamps[-1] - stamps[0]
    if span <= 0:
        return ("sparse", "every message from the app carries the same timestamp",
                facts)
    mean_gap = span / (len(stamps) - 1)
    quiet = max(0.0, now - stamps[-1])
    rate = len(stamps) / (span / DAY)
    facts.update({"per_day": round(rate, 2), "quiet_days": round(quiet / DAY, 2),
                  "last_ts": stamps[-1]})
    if quiet > max(QUIET_FLOOR, QUIET_MULTIPLE * mean_gap):
        return ("cliff", "%.1f message(s) a day for %.0f days, then nothing for %.1f "
                         "days; the series ends at %.6f"
                % (rate, span / DAY, quiet / DAY, stamps[-1]), facts)
    return ("steady", "%.1f message(s) a day and still posting near the end of the "
                      "window" % rate, facts)


def disconnect_meaning(reason):
    """Read a Socket Mode disconnect reason your client already logged. Pure.

    Returns (grade, detail). No connection is opened to produce one: the reason
    is in your log if a client was running when the switch moved, and absent if
    one was not, in which case the manifest settles it alone.
    """
    text = str(reason or "").strip()
    if not text:
        return ("not-supplied", "no disconnect reason was given; the manifest read "
                                "stands on its own")
    if text in DISCONNECT_REASONS:
        grade, detail = DISCONNECT_REASONS[text]
        return (grade, "%s: %s" % (text, detail))
    return ("unrecognised", "%s is not a documented disconnect reason" % text)


def load_manifest(args):
    """Read the live manifest. A read: export returns it and changes nothing."""
    if args.manifest:
        return json.loads(open(args.manifest, encoding="utf-8").read())
    token = os.environ.get(args.config_token_env)
    if not token or not args.app_id:
        log.warning("manifest   unavailable     set %s and --app-id, or pass "
                    "--manifest", args.config_token_env)
        return None
    body = requests.get(API + "apps.manifest.export",
                        headers={"Authorization": "Bearer " + token},
                        params={"app_id": args.app_id}, timeout=30).json()
    if body.get("ok") is not True:
        log.error("manifest   unavailable     %s", body.get("error"))
        return None
    return body.get("manifest") or {}


def page_history(session, channel, limit, max_pages):
    """Page conversations.history. A read."""
    out, cursor, pages = [], "", 0
    while pages < max_pages:
        params = {"channel": channel, "limit": str(limit)}
        if cursor:
            params["cursor"] = cursor
        body = session.get(API + "conversations.history", params=params,
                           timeout=30).json()
        if body.get("ok") is not True:
            log.error("history    unavailable     %s", body.get("error"))
            return out
        out.extend(body.get("messages") or [])
        cursor = ((body.get("response_metadata") or {}).get("next_cursor") or "")
        pages += 1
        if not cursor:
            break
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", default="", help="path to an exported manifest")
    ap.add_argument("--config-token-env", default="SLACK_CONFIG_TOKEN",
                    help="environment variable holding an app configuration token")
    ap.add_argument("--app-id", default="", help="app id, for the manifest read")
    ap.add_argument("--channel", default="",
                    help="a channel the app posts into, to date the silence")
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN",
                    help="environment variable holding a bot token, for the history")
    ap.add_argument("--disconnect-reason", default="",
                    help="a Socket Mode disconnect reason your client already logged")
    ap.add_argument("--limit", type=int, default=200)
    ap.add_argument("--max-pages", type=int, default=4)
    args = ap.parse_args()

    manifest = load_manifest(args)
    state, detail, facts = transport_state(manifest)
    if facts:
        log.info("manifest   socket mode %s, event Request URL: %s",
                 "on" if facts.get("socket_mode") else "off",
                 facts.get("request_url") or "not set")
    (log.warning if state in ("none", "both") else log.info)(
        "transport  %-15s %s", state, detail)

    count, names = undeliverable_declarations(manifest, state)
    if count:
        log.warning("declared   %d subscription(s) that cannot arrive: %s", count,
                    ", ".join(names[:6]) + (", ..." if count > 6 else ""))
    for surface, surface_state, surface_detail in dark_surfaces(manifest):
        (log.warning if surface_state == "dark" else log.info)(
            "surface    %-20s %-7s %s", surface, surface_state, surface_detail)

    grade, grade_detail = disconnect_meaning(args.disconnect_reason)
    if grade != "not-supplied":
        (log.warning if grade == "confirmed" else log.info)(
            "disconnect %-15s %s", grade, grade_detail)

    cliff = "unmeasured"
    if args.channel:
        token = os.environ.get(args.token_env)
        if not token:
            log.warning("history    set %s to date the silence", args.token_env)
        else:
            s = requests.Session()
            s.headers.update({"Authorization": "Bearer " + token})
            who = s.get(API + "auth.test", timeout=30).json()
            if who.get("ok") is not True:
                log.error("auth.test  unavailable     %s", who.get("error"))
                return 2
            log.info("identity   %s (%s) in %s", who.get("user_id"), who.get("user"),
                     who.get("team"))
            messages = page_history(s, args.channel, args.limit, args.max_pages)
            log.info("history    %d message(s) from %s", len(messages), args.channel)
            mine = [m.get("ts") for m in messages
                    if m.get("bot_id") or m.get("user") == who.get("user_id")]
            newest = max([float(m.get("ts") or 0) for m in messages] or [0.0])
            cliff, cliff_detail, cliff_facts = posting_cliff(mine, newest)
            (log.warning if cliff == "cliff" else log.info)(
                "cliff      %-15s %s", cliff, cliff_detail)
            log.info("cliff      facts           %s", cliff_facts)

    if state == "none":
        log.warning("verdict    the app declares %d event(s) and has nowhere to "
                    "receive them", count)
        log.warning("  repair: switch Socket Mode back on, or configure and verify an "
                    "HTTPS Request URL under Event Subscriptions")
        log.warning("  repair: set the Interactivity Request URL too if clicks are "
                    "expected; it is a separate field on a separate screen")
        log.warning("  repair: assert the transport count at startup and refuse to "
                    "boot on zero, so this fails at deploy time rather than in a week")
        return 1
    if state == "both":
        log.warning("verdict    two transports, not none; read the note on both "
                    "delivery paths being live at once")
        return 1
    if cliff == "cliff":
        log.warning("verdict    one transport is configured and the app still stopped "
                    "posting; look past the manifest")
        return 1
    log.info("verdict    clean           exactly one transport is configured")
    return 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-event-transport.mjs",
"js": '''/**
 * Decide whether Slack has anywhere to deliver this app's events.
 *
 * Read only. apps.manifest.export, auth.test and conversations.history are
 * reads. Nothing here writes a manifest, opens a socket, or sends anything to a
 * Request URL - there is no Request URL to send to, which is the finding.
 *
 * Delivery needs exactly one transport: Socket Mode on and a WebSocket held, or
 * an HTTPS Request URL configured and verified. There is no fallback between
 * them, and Slack drops what it cannot deliver.
 */

import { readFileSync } from 'node:fs';

const API = 'https://slack.com/api/';

export const DAY = 86400.0;

// How much quiet, measured in the app's own average gap, counts as the series
// having ended rather than merely being slow.
export const QUIET_MULTIPLE = 6.0;
export const QUIET_FLOOR = 3600.0;

// The one disconnect reason that means the setting moved rather than the
// network wobbling.
export const DISCONNECT_REASONS = {
  link_disabled: ['confirmed',
    'Socket Mode was switched off for this app while a client was connected. '
    + 'Reconnecting will never succeed'],
  refresh_requested: ['unrelated',
    'a routine scheduled refresh, which every long-lived connection gets. Not this '
    + 'note'],
  too_many_websockets: ['unrelated',
    'the ten connection cap, which is a different note. Socket Mode is on in that '
    + 'case, not off'],
  warning: ['unrelated',
    'the ten second notice before a scheduled refresh. Not a failure'],
};

/**
 * How many transports can deliver an event to this app? Pure.
 * Returns [state, detail, facts]; states none, socket, http, both, unknown.
 */
export function transportState(manifest) {
  if (manifest === null || manifest === undefined) {
    return ['unknown', 'no manifest was read, so the transports cannot be counted; an '
      + 'app configuration token is what reads them', {}];
  }
  const settings = manifest.settings ?? {};
  const socket = Boolean(settings.socket_mode_enabled);
  const events = settings.event_subscriptions ?? {};
  const url = String(events.request_url ?? '').trim();
  const facts = { socket_mode: socket, request_url: url };
  if (socket && url) {
    return ['both', 'Socket Mode is on and a Request URL is still stored underneath '
      + 'it; that is two delivery paths, not none', facts];
  }
  if (socket) {
    return ['socket', 'Socket Mode carries every event, interaction and command',
      facts];
  }
  if (url) return ['http', 'events are delivered to the stored Request URL', facts];
  return ['none', 'neither transport is configured, so Slack has no destination for '
    + "this app's events and drops them", facts];
}

/**
 * Which inbound surfaces still have a route, and which do not? Pure.
 * Returns [[surface, state, detail], ...] with state dark, routed or absent.
 */
export function darkSurfaces(manifest) {
  if (manifest === null || manifest === undefined) return [];
  const settings = manifest.settings ?? {};
  const features = manifest.features ?? {};
  const socket = Boolean(settings.socket_mode_enabled);
  const out = [];

  const events = settings.event_subscriptions ?? {};
  const declared = [...(events.bot_events ?? []), ...(events.user_events ?? [])];
  const eventsUrl = String(events.request_url ?? '').trim();
  if (!declared.length) out.push(['event subscriptions', 'absent', 'nothing is subscribed']);
  else if (socket) out.push(['event subscriptions', 'routed', 'the socket carries them']);
  else if (eventsUrl) out.push(['event subscriptions', 'routed', 'a Request URL of its own']);
  else {
    out.push(['event subscriptions', 'dark',
      `${declared.length} subscription(s) and no route of its own`]);
  }

  const inter = settings.interactivity ?? {};
  const interUrl = String(inter.request_url ?? '').trim();
  if (!inter.is_enabled) out.push(['interactivity', 'absent', 'the switch is off']);
  else if (socket) out.push(['interactivity', 'routed', 'the socket carries clicks too']);
  else if (interUrl) out.push(['interactivity', 'routed', 'carries its own URL']);
  else out.push(['interactivity', 'dark', 'enabled with an empty request_url']);

  for (const cmd of features.slash_commands ?? []) {
    const name = String((cmd ?? {}).command ?? '?');
    const cmdUrl = String((cmd ?? {}).url ?? '').trim();
    if (socket) out.push([name, 'routed', 'the socket carries commands too']);
    else if (cmdUrl) out.push([name, 'routed', 'carries its own URL, so it still answers']);
    else out.push([name, 'dark', 'no URL of its own and no socket']);
  }
  return out;
}

/**
 * What has the app asked for that it cannot receive? Pure.
 * Returns [count, names].
 */
export function undeliverableDeclarations(manifest, state) {
  if (manifest === null || manifest === undefined || state !== 'none') return [0, []];
  const events = (manifest.settings ?? {}).event_subscriptions ?? {};
  const names = [...new Set([...(events.bot_events ?? []), ...(events.user_events ?? [])]
    .map(String))].sort();
  return [names.length, names];
}

/**
 * Did the app's own message series end, and when? Pure.
 * Returns [state, detail, facts]; states cliff, steady, never-posted, sparse.
 */
export function postingCliff(appTimestamps, newestTs, minMessages = 4) {
  const stamps = [...(appTimestamps ?? [])].map(Number).sort((a, b) => a - b);
  const now = Number(newestTs ?? 0);
  const facts = { messages: stamps.length };
  if (!stamps.length) {
    return ['never-posted', 'the app has posted nothing in the messages read, so there '
      + 'is no series to have ended', facts];
  }
  if (stamps.length < Math.max(2, minMessages)) {
    return ['sparse', `${stamps.length} message(s) from the app is too few to measure `
      + 'a rate against', facts];
  }
  const span = stamps[stamps.length - 1] - stamps[0];
  if (span <= 0) {
    return ['sparse', 'every message from the app carries the same timestamp', facts];
  }
  const meanGap = span / (stamps.length - 1);
  const quiet = Math.max(0, now - stamps[stamps.length - 1]);
  const rate = stamps.length / (span / DAY);
  facts.per_day = Math.round(rate * 100) / 100;
  facts.quiet_days = Math.round((quiet / DAY) * 100) / 100;
  facts.last_ts = stamps[stamps.length - 1];
  if (quiet > Math.max(QUIET_FLOOR, QUIET_MULTIPLE * meanGap)) {
    return ['cliff', `${rate.toFixed(1)} message(s) a day for ${(span / DAY).toFixed(0)} `
      + `days, then nothing for ${(quiet / DAY).toFixed(1)} days; the series ends at `
      + `${stamps[stamps.length - 1].toFixed(6)}`, facts];
  }
  return ['steady', `${rate.toFixed(1)} message(s) a day and still posting near the end `
    + 'of the window', facts];
}

/**
 * Read a Socket Mode disconnect reason your client already logged. Pure.
 * Returns [grade, detail]. No connection is opened to produce one.
 */
export function disconnectMeaning(reason) {
  const text = String(reason ?? '').trim();
  if (!text) {
    return ['not-supplied', 'no disconnect reason was given; the manifest read stands '
      + 'on its own'];
  }
  if (Object.prototype.hasOwnProperty.call(DISCONNECT_REASONS, text)) {
    const [grade, detail] = DISCONNECT_REASONS[text];
    return [grade, `${text}: ${detail}`];
  }
  return ['unrecognised', `${text} is not a documented disconnect reason`];
}

function arg(args, name, fallback = null) {
  const i = args.indexOf(name);
  return i === -1 ? fallback : args[i + 1];
}

async function loadManifest(args) {
  const path = arg(args, '--manifest', '');
  if (path) return JSON.parse(readFileSync(path, 'utf8'));
  const tokenEnv = arg(args, '--config-token-env', 'SLACK_CONFIG_TOKEN');
  const appId = arg(args, '--app-id', '');
  const token = process.env[tokenEnv];
  if (!token || !appId) {
    console.warn(`manifest   unavailable     set ${tokenEnv} and --app-id, or pass `
      + '--manifest');
    return null;
  }
  const params = new URLSearchParams({ app_id: appId });
  const body = await (await fetch(`${API}apps.manifest.export?${params}`,
    { headers: { Authorization: `Bearer ${token}` } })).json();
  if (body.ok !== true) {
    console.error(`manifest   unavailable     ${body.error}`);
    return null;
  }
  return body.manifest ?? {};
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
      console.error(`history    unavailable     ${body.error}`);
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
  const manifest = await loadManifest(args);
  const [state, detail, facts] = transportState(manifest);
  if (Object.keys(facts).length) {
    console.log(`manifest   socket mode ${facts.socket_mode ? 'on' : 'off'}, event `
      + `Request URL: ${facts.request_url || 'not set'}`);
  }
  const line = `transport  ${state.padEnd(15)} ${detail}`;
  if (state === 'none' || state === 'both') console.warn(line); else console.log(line);

  const [count, names] = undeliverableDeclarations(manifest, state);
  if (count) {
    console.warn(`declared   ${count} subscription(s) that cannot arrive: `
      + names.slice(0, 6).join(', ') + (count > 6 ? ', ...' : ''));
  }
  for (const [surface, surfaceState, surfaceDetail] of darkSurfaces(manifest)) {
    const row = `surface    ${surface.padEnd(20)} ${surfaceState.padEnd(7)} ${surfaceDetail}`;
    if (surfaceState === 'dark') console.warn(row); else console.log(row);
  }

  const [grade, gradeDetail] = disconnectMeaning(arg(args, '--disconnect-reason', ''));
  if (grade !== 'not-supplied') {
    const row = `disconnect ${grade.padEnd(15)} ${gradeDetail}`;
    if (grade === 'confirmed') console.warn(row); else console.log(row);
  }

  let cliff = 'unmeasured';
  const channel = arg(args, '--channel', '');
  if (channel) {
    const tokenEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
    const token = process.env[tokenEnv];
    if (!token) console.warn(`history    set ${tokenEnv} to date the silence`);
    else {
      const headers = { Authorization: `Bearer ${token}` };
      const who = await (await fetch(`${API}auth.test`, { headers })).json();
      if (who.ok !== true) {
        console.error(`auth.test  unavailable     ${who.error}`);
        process.exitCode = 2;
        return;
      }
      console.log(`identity   ${who.user_id} (${who.user}) in ${who.team}`);
      const messages = await pageHistory(headers, channel,
        Number(arg(args, '--limit', '200')), Number(arg(args, '--max-pages', '4')));
      console.log(`history    ${messages.length} message(s) from ${channel}`);
      const mine = messages.filter((m) => m.bot_id || m.user === who.user_id)
        .map((m) => m.ts);
      const newest = Math.max(0, ...messages.map((m) => Number(m.ts ?? 0)));
      const [cliffState, cliffDetail, cliffFacts] = postingCliff(mine, newest);
      cliff = cliffState;
      const row = `cliff      ${cliffState.padEnd(15)} ${cliffDetail}`;
      if (cliffState === 'cliff') console.warn(row); else console.log(row);
      console.log(`cliff      facts           ${JSON.stringify(cliffFacts)}`);
    }
  }

  if (state === 'none') {
    console.warn(`verdict    the app declares ${count} event(s) and has nowhere to `
      + 'receive them');
    console.warn('  repair: switch Socket Mode back on, or configure and verify an '
      + 'HTTPS Request URL under Event Subscriptions');
    console.warn('  repair: set the Interactivity Request URL too if clicks are '
      + 'expected; it is a separate field on a separate screen');
    console.warn('  repair: assert the transport count at startup and refuse to boot '
      + 'on zero, so this fails at deploy time rather than in a week');
    process.exitCode = 1;
    return;
  }
  if (state === 'both') {
    console.warn('verdict    two transports, not none; read the note on both delivery '
      + 'paths being live at once');
    process.exitCode = 1;
    return;
  }
  if (cliff === 'cliff') {
    console.warn('verdict    one transport is configured and the app still stopped '
      + 'posting; look past the manifest');
    process.exitCode = 1;
    return;
  }
  console.log('verdict    clean           exactly one transport is configured');
}

// Only run when invoked directly, so importing this module in the tests does
// not execute main().
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The assertions that matter are the ones about the four transport states, because the whole note turns on <code>none</code> being a different finding from <code>both</code> and from either healthy value. After that, the tests are about restraint: <code>dark_surfaces</code> is checked for the slash command that keeps working, which is the fact that misdirects the investigation; <code>posting_cliff</code> is checked for the app that is still posting and for the app that posted twice, because declaring a cliff on two data points would send somebody to the configuration screen for no reason.",
"test_py_file": "test_slack_event_transport.py",
"test_py": '''from slack_event_transport import (
    dark_surfaces, disconnect_meaning, posting_cliff, transport_state,
    undeliverable_declarations,
)

DAY = 86400.0


def manifest(socket=False, url="", events=("app_mention",), inter=None, commands=()):
    return {
        "settings": {
            "socket_mode_enabled": socket,
            "event_subscriptions": {"request_url": url, "bot_events": list(events)},
            "interactivity": inter or {},
        },
        "features": {"slash_commands": list(commands)},
    }


def test_neither_transport_is_its_own_state_and_not_a_boolean():
    state, detail, facts = transport_state(manifest())
    assert state == "none"
    assert facts == {"socket_mode": False, "request_url": ""}
    assert "no destination" in detail


def test_socket_only_and_url_only_are_both_healthy():
    assert transport_state(manifest(socket=True))[0] == "socket"
    assert transport_state(manifest(url="https://ops.example.com/slack"))[0] == "http"


def test_both_at_once_is_the_other_note_rather_than_this_one():
    state, detail, _facts = transport_state(
        manifest(socket=True, url="https://ops.example.com/slack"))
    assert state == "both"
    assert "not none" in detail


def test_a_whitespace_url_is_not_a_transport():
    assert transport_state(manifest(url="   "))[0] == "none"


def test_no_manifest_is_unknown_rather_than_a_finding():
    assert transport_state(None)[0] == "unknown"


def test_the_events_surface_goes_dark_because_it_has_no_url_of_its_own():
    rows = dict((r[0], r[1]) for r in dark_surfaces(manifest()))
    assert rows["event subscriptions"] == "dark"


def test_a_slash_command_keeps_answering_and_that_is_the_misdirection():
    rows = dark_surfaces(manifest(commands=[{"command": "/deploy",
                                             "url": "https://ops.example.com/cmd"}]))
    assert ("/deploy", "routed", "carries its own URL, so it still answers") in rows


def test_a_command_with_no_url_of_its_own_goes_dark_too():
    rows = dict((r[0], r[1]) for r in dark_surfaces(manifest(commands=[
        {"command": "/rollback", "url": ""}])))
    assert rows["/rollback"] == "dark"


def test_the_socket_routes_every_surface_at_once():
    rows = dark_surfaces(manifest(socket=True, inter={"is_enabled": True},
                                  commands=[{"command": "/deploy", "url": ""}]))
    assert {r[1] for r in rows} == {"routed"}


def test_interactivity_enabled_with_an_empty_url_is_dark():
    rows = dict((r[0], r[1]) for r in dark_surfaces(manifest(inter={"is_enabled": True})))
    assert rows["interactivity"] == "dark"


def test_interactivity_switched_off_is_absent_rather_than_dark():
    rows = dict((r[0], r[1]) for r in dark_surfaces(manifest(inter={"is_enabled": False})))
    assert rows["interactivity"] == "absent"


def test_nothing_subscribed_is_absent_which_is_a_different_note():
    rows = dict((r[0], r[1]) for r in dark_surfaces(manifest(events=())))
    assert rows["event subscriptions"] == "absent"


def test_the_declarations_are_counted_only_when_there_is_no_transport():
    count, names = undeliverable_declarations(
        manifest(events=("app_mention", "team_join")), "none")
    assert count == 2
    assert names == ["app_mention", "team_join"]
    assert undeliverable_declarations(manifest(socket=True), "socket") == (0, [])


def test_user_events_count_too_and_duplicates_do_not():
    m = manifest(events=("app_mention",))
    m["settings"]["event_subscriptions"]["user_events"] = ["app_mention", "file_shared"]
    assert undeliverable_declarations(m, "none")[0] == 2


def test_a_series_that_ends_is_a_cliff_with_a_date_on_it():
    stamps = [1000.0 + i * DAY for i in range(30)]
    state, detail, facts = posting_cliff(stamps, stamps[-1] + 9 * DAY)
    assert state == "cliff"
    assert facts["quiet_days"] == 9.0
    assert "series ends at" in detail


def test_an_app_still_posting_near_the_end_is_not_a_cliff():
    stamps = [1000.0 + i * DAY for i in range(30)]
    assert posting_cliff(stamps, stamps[-1] + 600.0)[0] == "steady"


def test_two_messages_are_too_few_to_declare_anything():
    assert posting_cliff([1000.0, 2000.0], 900000.0)[0] == "sparse"


def test_an_app_that_never_posted_is_not_a_cliff():
    state, detail, _facts = posting_cliff([], 5000.0)
    assert state == "never-posted"
    assert "no series" in detail


def test_a_chatty_app_that_paused_for_an_hour_is_still_steady():
    stamps = [1000.0 + i * 60.0 for i in range(40)]
    assert posting_cliff(stamps, stamps[-1] + 1800.0)[0] == "steady"


def test_link_disabled_is_the_reason_that_confirms_this_note():
    grade, detail = disconnect_meaning("link_disabled")
    assert grade == "confirmed"
    assert "switched off" in detail


def test_the_other_documented_reasons_belong_to_other_notes():
    for reason in ("refresh_requested", "too_many_websockets", "warning"):
        assert disconnect_meaning(reason)[0] == "unrelated"


def test_no_reason_supplied_is_not_a_finding():
    assert disconnect_meaning("")[0] == "not-supplied"
    assert disconnect_meaning(None)[0] == "not-supplied"
''',
"test_js_file": "slack-event-transport.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  DAY, darkSurfaces, disconnectMeaning, postingCliff, transportState,
  undeliverableDeclarations,
} from './slack-event-transport.mjs';

function manifest({
  socket = false, url = '', events = ['app_mention'], inter = {}, commands = [],
} = {}) {
  return {
    settings: {
      socket_mode_enabled: socket,
      event_subscriptions: { request_url: url, bot_events: [...events] },
      interactivity: inter,
    },
    features: { slash_commands: [...commands] },
  };
}

test('neither transport is its own state and not a boolean', () => {
  const [state, detail, facts] = transportState(manifest());
  assert.equal(state, 'none');
  assert.deepEqual(facts, { socket_mode: false, request_url: '' });
  assert.match(detail, /no destination/);
});

test('socket only and url only are both healthy', () => {
  assert.equal(transportState(manifest({ socket: true }))[0], 'socket');
  assert.equal(transportState(manifest({ url: 'https://ops.example.com/slack' }))[0],
    'http');
});

test('both at once is the other note rather than this one', () => {
  const [state, detail] = transportState(
    manifest({ socket: true, url: 'https://ops.example.com/slack' }));
  assert.equal(state, 'both');
  assert.match(detail, /not none/);
});

test('a whitespace url is not a transport', () => {
  assert.equal(transportState(manifest({ url: '   ' }))[0], 'none');
});

test('no manifest is unknown rather than a finding', () => {
  assert.equal(transportState(null)[0], 'unknown');
});

test('the events surface goes dark because it has no url of its own', () => {
  const rows = Object.fromEntries(darkSurfaces(manifest()).map((r) => [r[0], r[1]]));
  assert.equal(rows['event subscriptions'], 'dark');
});

test('a slash command keeps answering and that is the misdirection', () => {
  const rows = darkSurfaces(manifest({
    commands: [{ command: '/deploy', url: 'https://ops.example.com/cmd' }],
  }));
  assert.deepEqual(rows.find((r) => r[0] === '/deploy'),
    ['/deploy', 'routed', 'carries its own URL, so it still answers']);
});

test('a command with no url of its own goes dark too', () => {
  const rows = Object.fromEntries(darkSurfaces(manifest({
    commands: [{ command: '/rollback', url: '' }],
  })).map((r) => [r[0], r[1]]));
  assert.equal(rows['/rollback'], 'dark');
});

test('the socket routes every surface at once', () => {
  const rows = darkSurfaces(manifest({
    socket: true, inter: { is_enabled: true }, commands: [{ command: '/deploy', url: '' }],
  }));
  assert.deepEqual([...new Set(rows.map((r) => r[1]))], ['routed']);
});

test('interactivity enabled with an empty url is dark', () => {
  const rows = Object.fromEntries(darkSurfaces(manifest({ inter: { is_enabled: true } }))
    .map((r) => [r[0], r[1]]));
  assert.equal(rows.interactivity, 'dark');
});

test('interactivity switched off is absent rather than dark', () => {
  const rows = Object.fromEntries(darkSurfaces(manifest({ inter: { is_enabled: false } }))
    .map((r) => [r[0], r[1]]));
  assert.equal(rows.interactivity, 'absent');
});

test('nothing subscribed is absent which is a different note', () => {
  const rows = Object.fromEntries(darkSurfaces(manifest({ events: [] }))
    .map((r) => [r[0], r[1]]));
  assert.equal(rows['event subscriptions'], 'absent');
});

test('the declarations are counted only when there is no transport', () => {
  const [count, names] = undeliverableDeclarations(
    manifest({ events: ['app_mention', 'team_join'] }), 'none');
  assert.equal(count, 2);
  assert.deepEqual(names, ['app_mention', 'team_join']);
  assert.deepEqual(undeliverableDeclarations(manifest({ socket: true }), 'socket'),
    [0, []]);
});

test('user events count too and duplicates do not', () => {
  const m = manifest({ events: ['app_mention'] });
  m.settings.event_subscriptions.user_events = ['app_mention', 'file_shared'];
  assert.equal(undeliverableDeclarations(m, 'none')[0], 2);
});

test('a series that ends is a cliff with a date on it', () => {
  const stamps = Array.from({ length: 30 }, (_v, i) => 1000 + i * DAY);
  const [state, detail, facts] = postingCliff(stamps, stamps[29] + 9 * DAY);
  assert.equal(state, 'cliff');
  assert.equal(facts.quiet_days, 9);
  assert.match(detail, /series ends at/);
});

test('an app still posting near the end is not a cliff', () => {
  const stamps = Array.from({ length: 30 }, (_v, i) => 1000 + i * DAY);
  assert.equal(postingCliff(stamps, stamps[29] + 600)[0], 'steady');
});

test('two messages are too few to declare anything', () => {
  assert.equal(postingCliff([1000, 2000], 900000)[0], 'sparse');
});

test('an app that never posted is not a cliff', () => {
  const [state, detail] = postingCliff([], 5000);
  assert.equal(state, 'never-posted');
  assert.match(detail, /no series/);
});

test('a chatty app that paused for an hour is still steady', () => {
  const stamps = Array.from({ length: 40 }, (_v, i) => 1000 + i * 60);
  assert.equal(postingCliff(stamps, stamps[39] + 1800)[0], 'steady');
});

test('link_disabled is the reason that confirms this note', () => {
  const [grade, detail] = disconnectMeaning('link_disabled');
  assert.equal(grade, 'confirmed');
  assert.match(detail, /switched off/);
});

test('the other documented reasons belong to other notes', () => {
  for (const reason of ['refresh_requested', 'too_many_websockets', 'warning']) {
    assert.equal(disconnectMeaning(reason)[0], 'unrelated');
  }
});

test('no reason supplied is not a finding', () => {
  assert.equal(disconnectMeaning('')[0], 'not-supplied');
  assert.equal(disconnectMeaning(null)[0], 'not-supplied');
});
''',
"faq": [
 ("If Socket Mode is off, doesn't Slack just use the Request URL again?",
  "Only if there is one. Socket Mode and the Request URL are two independent settings, not two positions of one switch, and turning one off does not turn the other on. An app that was built on Socket Mode from the beginning has never had a Request URL configured, so switching the socket off leaves the events subscription with no destination at all. Slack does not queue those events for later and does not report them anywhere: it has nowhere to put them, so it drops them."),
 ("Our slash commands still work, so delivery is clearly fine. Isn't it?",
  "Slash commands each store their own URL in the app configuration, which is why they survive. So does interactivity, if its URL was ever filled in. The events subscription is the one surface with no URL of its own, and it is the one that goes dark. That is exactly why this failure lasts so long: the surfaces people poke at to check whether the app is up are the surfaces that kept a route, and the surface that carries mentions, joins and reactions is the one that did not."),
 ("There is a Request URL configured, it just never verified. Is that this note?",
  "No, and the distinction is worth keeping because the repairs are different. A URL that exists and failed the challenge is a handshake problem: your endpoint returned the wrong thing, or middleware stood in front of it, and the fix is in your code. A URL that exists and points at a tunnel that closed is a hostname problem, and the fix is in the configuration. This note is the case where the string is simply not there, and no amount of debugging your endpoint will help because Slack is not calling it."),
 ("Why does reading the manifest need a different token from the one the app runs on?",
  "Because app configuration is a different surface from workspace data. A bot token reads channels, messages and users; it cannot read your app's own settings. The manifest is read with an app configuration token, which is minted on the app management page, lives twelve hours, and rotates through tooling.tokens.rotate rather than the OAuth endpoints. If that token is dead, this script reports the manifest as unavailable rather than reporting a clean transport count, because a check that could not run is not a check that passed."),
 ("Can this happen without anyone touching the switch?",
  "Yes, in two ways. Copying a manifest between apps drops whatever fields the source did not have, so an app created from a manifest that never carried a Request URL starts life with zero transports the moment Socket Mode is not also copied. And an app created through the API from a partial manifest has the same shape. Both cases look like a brand new app that has never worked rather than an app that stopped, which is why the script reports never-posted as a distinct state from cliff."),
],
"related": [
 ("/slack/socket-mode-and-request-url-both-on/", "the mirror image: two transports rather than none"),
 ("/slack/no-event-subscriptions/", "a transport that works with nothing subscribed to it"),
 ("/slack/config-token-expired/", "the credential that reads the manifest, and its twelve hours"),
],
"citations": [CITE_SOCKET_MODE, CITE_EVENTS_API, CITE_MANIFEST_EXPORT, CITE_MANIFESTS],
})
GUIDES.append({
"slug": "interactivity-not-enabled",
"title": "Buttons render, clicks vanish: interactivity is switched off",
"description": "Posting a button needs chat:write. Receiving the click needs a second switch on a second screen. Read the route, then measure one surface against the other.",
"h1": "Buttons render, clicks vanish: interactivity is switched off",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack button click does nothing",
             "slack interactivity request url not set",
             "slack block_actions never received",
             "slack dispatch_failed button",
             "slack modal submit no payload"],
"deps": "Python 3.9+ with requests, or Node.js 18+; an app configuration token with app_configurations:read for the manifest, and a bot token with channels:history to read the app's own posted blocks",
"lead": "The approval flow demoed beautifully. A deploy request arrives in <code>#releases</code> as a tidy message with two buttons, Approve and Reject, rendered exactly as they were designed, in the right colours, with the right text. Everyone agreed it looked finished.</p><p>In production nobody can approve anything. The button depresses, the client shows a brief spinner, and then nothing &mdash; sometimes a small red toast, more often no feedback at all. The handler has a log line on its first statement and that line has never printed. The bot answers <code>@deploybot status</code> in the same channel, instantly, every time. Events work. Clicks are not arriving, and they are not arriving because the payload a click produces is delivered to a URL on a screen nobody opened.",
"short_answer": """<p>Posting an interactive message and receiving the interaction are <strong>two different permissions on two different screens</strong>. Anything with <code>chat:write</code> can post a Block Kit message full of buttons, and Slack will render them perfectly. The payload a click produces is delivered to the <strong>Interactivity Request URL</strong>, which is configured under <em>Interactivity &amp; Shortcuts</em> &mdash; a separate toggle, with a separate URL field, from the Events Request URL. With the toggle off, clicks produce nothing at all.</p>
<p>The read is <code>settings.interactivity.is_enabled</code> and <code>settings.interactivity.request_url</code> from <code>apps.manifest.export</code>, held against <code>settings.socket_mode_enabled</code>, because Socket Mode carries interactions as well as events and makes both fields moot. Three ways to be wrong: the toggle is off, the toggle is on with an empty URL, or the toggle is on with a URL that is not the one your app serves.</p>
<p>The workspace confirms it with an <strong>asymmetry</strong>, and the asymmetry is what makes this note different from a dead transport. Read the channel: the app answers mentions within seconds, and the app has posted forty messages carrying <code>type: "actions"</code> blocks without ever posting a single follow-up after one. <strong>One surface alive, the other silent.</strong> If both surfaces are silent you have a transport problem and a different note; if both are alive the switch is fine and the bug is in your handler.</p>
<p>One extra field catches a subtler version: an external select menu makes Slack call back for its options at <code>message_menu_options_url</code>, which is a <em>third</em> URL. Enabled interactivity with external selects and no options URL is a menu that opens empty forever.</p>""",
"problem": """<p>Every part of the visible evidence points away from the answer. The message rendered, so Block Kit is valid. The bot is in the channel, so membership is fine. The token posts successfully, so the scopes are fine. Mentions get answered within a second, so the app is up, the endpoint is reachable, the certificate is good and the deploy is healthy. Every check an on-call engineer runs comes back green, because every check is aimed at the surface that works.</p>
<p>The error, when there is one, is unhelpful in a specific way. A click on an app that cannot receive interactions surfaces as <code>dispatch_failed</code> or as a generic &ldquo;something went wrong&rdquo; toast in the Slack client, with no correlation id and nothing at all in your logs, because nothing reached your logs. The failure is entirely on Slack's side of the boundary: it produced a payload, looked up where to send it, found no destination, and stopped.</p>
<p>The configuration screens encourage it. Event Subscriptions and Interactivity &amp; Shortcuts are two separate pages, each with its own verified-URL box, and there is no cross-reference between them. A team that stood up an events endpoint, pasted the URL, watched it go green and moved on has completed a perfectly coherent task. Nothing on that page mentions that clicks go somewhere else. Bolt makes it worse in a friendly way: it serves both on <code>/slack/events</code> by default, so the URL you need is a URL you already have, and the only missing step is telling Slack about it in the second place.</p>
<p>Then there is the Socket Mode variant, which is how this reaches production after working locally for a month. A developer runs the app on Socket Mode, where one connection carries events <em>and</em> interactions and neither URL field is consulted, so buttons work end to end on a laptop. The production app is the same code with Socket Mode off and an events URL configured. Interactivity was never enabled there because it was never needed anywhere it was tested.</p>""",
"why": """<p><strong>The asymmetry is the finding, not the silence.</strong> Any number of failures make an app stop answering. Exactly one class of failure makes an app answer mentions promptly while ignoring every click, and that is a route that exists for one surface and not the other. So the script measures both surfaces separately and reports the pair. <code>interactions-dead</code> with <code>events-alive</code> is this note. Both dead is a <a href="/slack/socket-mode-off-but-no-request-url/">transport with nowhere to deliver</a>, and the script says so rather than blaming the switch it happens to be looking at.</p>
<p><strong>What counts as an interactive message has to be read out of the blocks, not guessed.</strong> A button is not the only thing that produces a <code>block_actions</code> payload: static and external selects, multi-selects, overflow menus, date and time pickers, checkboxes and radio buttons all do, and they appear both inside an <code>actions</code> block and as a section <code>accessory</code>. The script walks the blocks of the app's own posted messages and inventories them, so &ldquo;this app has posted forty things that can be clicked&rdquo; is a counted fact rather than an impression.</p>
<p><strong>Socket Mode has to be checked first or the whole reading inverts.</strong> With Socket Mode on, interactions arrive over the WebSocket and both interactivity URL fields are ignored entirely. An empty <code>request_url</code> beside <code>socket_mode_enabled: true</code> is completely healthy, and a check that reported it as a fault would be wrong on every correctly configured Socket Mode app in the workspace.</p>
<p><strong>The options URL is a third destination and it fails on its own.</strong> An external select asks Slack to fetch its choices at request time from <code>message_menu_options_url</code>. Interactivity can be enabled, its main URL correct, clicks handled fine &mdash; and every external menu still open empty, because that one field was never filled in. The script only raises it when the app has actually posted an external select, so it stays quiet for the apps it does not apply to.</p>
<p><strong>The behavioural half is honest about what it cannot see.</strong> A click that opens a modal and nothing else leaves no trace in <code>conversations.history</code>, so the absence of a follow-up message is evidence and not proof. The script reports <code>no-evidence</code> when the app has posted nothing clickable, and it reports counts alongside every state so you can see the sample size it reached its conclusion from. A confident answer from four messages would be worse than no answer.</p>
<p><strong>Nothing here clicks anything.</strong> There is no read-only way to make Slack produce an interaction payload, and the write that would &mdash; posting a message with a button and pressing it &mdash; is a message in somebody's channel. The configuration read plus the two surface counts settle it without the audit appearing in the workspace at all.</p>""",
"steps": [
 {"h": "Find out where a click would go, if one happened",
  "body": """<p><code>interaction_route</code> reads <code>socket_mode_enabled</code>, <code>interactivity.is_enabled</code> and <code>interactivity.request_url</code> in that order of precedence and returns <code>socket</code>, <code>url</code>, <code>enabled-no-url</code> or <code>disabled</code>. Socket Mode is checked first because it makes the URL fields irrelevant, and reporting an empty field as a fault on a Socket Mode app would be a false positive on every one of them.</p>"""},
 {"h": "Inventory what the app has actually posted that can be clicked",
  "body": """<p><code>interactive_elements</code> walks a message's blocks and returns every element that can produce a <code>block_actions</code> payload, with its kind and <code>action_id</code>. It looks inside <code>actions</code> blocks, at section <code>accessory</code> elements, and at <code>input</code> blocks that set <code>dispatch_action</code>. Without this the note is an opinion; with it, the count is a fact.</p>"""},
 {"h": "Check whether any of them need the third URL",
  "body": """<p><code>needs_options_url</code> looks for external selects among those elements and <code>options_route</code> holds that against <code>message_menu_options_url</code>. This is the failure where interactivity is configured correctly and menus still open empty, and it is silent for every app that does not use external data sources.</p>"""},
 {"h": "Measure the two surfaces against each other",
  "body": """<p><code>surface_split</code> counts mentions that got a reply within the window and interactive messages that got a plain app follow-up within the window, and returns <code>interactions-dead</code>, <code>all-dead</code>, <code>events-dead</code>, <code>healthy</code> or <code>no-evidence</code>. One surface alive and one silent is the shape this note owns; both silent belongs to the transport note.</p>"""},
 {"h": "Combine the configuration and the evidence into one verdict",
  "body": """<p><code>verdict</code> puts the route and the split together, because either alone is weak. A disabled switch on an app that has never posted a button is not an incident. A disabled switch on an app that has posted forty of them and never followed one up is the answer, and it should be stated with the counts attached.</p>"""},
 {"h": "Point interactivity at the endpoint you already run",
  "body": """<p>The printed repair is usually one paste: enable Interactivity &amp; Shortcuts and set its Request URL to the same route that already serves events, since Bolt and most frameworks handle both there. Then remember the interactivity endpoint carries the same three-second acknowledgement budget as events, and that a modal has its own separate timing constraint on the trigger it was opened with.</p>"""},
],
"verify": """<p>Enable the switch, paste the URL, and run it again against the same channel. The line that should change is <code>split</code>: <code>interactions-dead</code> becomes <code>healthy</code> once one click has been handled and left a trace.</p>
<pre><code class="language-bash">python3 slack_interactivity_route.py --app-id A05DEPB0T --channel C05REL9QT
# manifest   socket mode off
# route      disabled        Interactivity is switched off, so a click produces no
#                            payload at all and nothing is delivered anywhere
# blocks     41 app message(s) read, 38 carrying something clickable
# element    actions[0]      button           approve_deploy
# element    actions[0]      button           reject_deploy
# element    section[2]      overflow         deploy_overflow
# options    not-needed      no external select has been posted by this app
# identity   U07DEP9QD (deploybot) in Northwind
# history    512 message(s) from C05REL9QT
# split      interactions-dead  62 of 66 mention(s) answered within 120s, and 0 of 38
#                            interactive message(s) followed by anything
# verdict    switch-off      the app posts buttons it has no way of hearing about
#   repair: enable Interactivity & Shortcuts and set its Request URL to the route that
#           already serves events; Bolt serves both on /slack/events
#   repair: budget the same three seconds to acknowledge an interaction as an event</code></pre>""",
"code_intro": "Two halves that are only worth anything together. <code>interaction_route</code> is the configuration read and it is four lines, with Socket Mode checked first so a correctly configured socket app is never reported as broken. <code>surface_split</code> is the evidence, and it is written to return a <em>pair</em> of surface states rather than one silence count, because the entire distinction between this note and a dead transport is whether the other surface is still alive. <code>interactive_elements</code> is what makes the counts real: it walks the blocks the app itself posted and names every element a person could click.",
"py_file": "slack_interactivity_route.py",
"py": '''"""Find out where a click on this app's buttons goes, and whether it goes.

Read only. apps.manifest.export, auth.test and conversations.history are reads.
Nothing here posts a message, presses a button, or sends anything to an
interactivity endpoint - there is no read-only way to make Slack produce an
interaction payload, and manufacturing one would mean writing into somebody's
channel.

Posting an interactive message and receiving the interaction are two different
things. chat:write posts the button and Slack renders it; the payload a click
produces goes to the Interactivity Request URL, which is a separate switch with
a separate field on a separate screen, or to the Socket Mode connection when
that is on.
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_interactivity_route")

API = "https://slack.com/api/"

# Every element type that produces a block_actions payload when a person uses
# it. Buttons are the ones everybody thinks of and the menus are the ones that
# quietly stop working with exactly the same cause.
ELEMENT_KINDS = {
    "button", "workflow_button", "overflow", "datepicker", "timepicker",
    "datetimepicker", "checkboxes", "radio_buttons",
    "static_select", "external_select", "users_select", "conversations_select",
    "channels_select", "multi_static_select", "multi_external_select",
    "multi_users_select", "multi_conversations_select", "multi_channels_select",
    "rich_text_input", "plain_text_input", "number_input", "email_text_input",
    "url_text_input", "file_input",
}

# The two that make Slack call back for their choices at a third URL, which is
# configured separately from the interactivity URL and fails on its own.
EXTERNAL_KINDS = {"external_select", "multi_external_select"}

# How long after a trigger an app response still counts as a response to it.
# Generous, because counting a slow handler as a dead one would point at the
# configuration screen when the problem is a queue.
WINDOW = 120.0


def interaction_route(manifest):
    """Where does a click on this app's buttons go? Pure.

    Returns (state, detail, facts). States:

      socket         Socket Mode is on and carries interactions as well as
                     events. Both URL fields are ignored, so an empty one is
                     not a fault - checking this first is what stops the whole
                     reading inverting on a correctly configured socket app.
      url            interactivity is enabled and has a URL.
      enabled-no-url the switch is on and the field is empty.
      disabled       the switch is off. No payload is produced at all.
      unknown        no manifest was available.
    """
    if manifest is None:
        return ("unknown", "no manifest was read, so the interactivity route cannot be "
                           "established; an app configuration token is what reads it",
                {})
    settings = manifest.get("settings") or {}
    socket = bool(settings.get("socket_mode_enabled"))
    inter = settings.get("interactivity") or {}
    enabled = bool(inter.get("is_enabled"))
    url = str(inter.get("request_url") or "").strip()
    options_url = str(inter.get("message_menu_options_url") or "").strip()
    facts = {"socket_mode": socket, "is_enabled": enabled, "request_url": url,
             "message_menu_options_url": options_url}
    if socket:
        return ("socket", "Socket Mode carries interactions as well as events, so "
                          "neither interactivity URL field is consulted", facts)
    if not enabled:
        return ("disabled", "Interactivity is switched off, so a click produces no "
                            "payload at all and nothing is delivered anywhere", facts)
    if not url:
        return ("enabled-no-url", "Interactivity is enabled with an empty request_url, "
                                  "so the payload is produced and has no destination",
                facts)
    return ("url", "interactions are delivered to %s" % url, facts)


def interactive_elements(message):
    """Everything in this posted message that a person can act on. Pure.

    Returns [(location, kind, action_id), ...]. Three places produce a
    block_actions payload and only the first is obvious: elements inside an
    actions block, an accessory hanging off a section, and an input block that
    sets dispatch_action. A count built from buttons alone misses the menus,
    which fail for exactly the same reason and are harder to notice.
    """
    out = []
    for index, block in enumerate(((message or {}).get("blocks") or [])):
        block = block or {}
        kind = str(block.get("type") or "")
        if kind == "actions":
            for element in block.get("elements") or []:
                element = element or {}
                if str(element.get("type") or "") in ELEMENT_KINDS:
                    out.append(("actions[%d]" % index, str(element.get("type")),
                                str(element.get("action_id") or "")))
        accessory = block.get("accessory") or {}
        if str(accessory.get("type") or "") in ELEMENT_KINDS:
            out.append(("%s[%d]" % (kind or "block", index),
                        str(accessory.get("type")),
                        str(accessory.get("action_id") or "")))
        if kind == "input" and block.get("dispatch_action"):
            element = block.get("element") or {}
            if str(element.get("type") or "") in ELEMENT_KINDS:
                out.append(("input[%d]" % index, str(element.get("type")),
                            str(element.get("action_id") or "")))
    return out


def needs_options_url(elements):
    """Do any of these elements make Slack call back for their choices? Pure.

    Returns (needed, kinds). External selects are fetched at request time from
    a third URL, so an app can have interactivity working perfectly and still
    open every menu empty.
    """
    kinds = sorted({kind for _where, kind, _action in (elements or [])
                    if kind in EXTERNAL_KINDS})
    return (bool(kinds), kinds)


def options_route(facts, needed):
    """Is the options URL there, and does this app need it? Pure.

    Returns (state, detail). States: not-needed, socket, missing, configured.
    """
    if facts.get("socket_mode"):
        return ("socket", "external select options arrive over the socket like "
                          "everything else")
    if not needed:
        return ("not-needed", "no external select has been posted by this app")
    if not facts.get("message_menu_options_url"):
        return ("missing", "an external select has been posted and "
                           "message_menu_options_url is empty, so the menu opens empty")
    return ("configured", "options are fetched from %s"
            % facts.get("message_menu_options_url"))


def surface_split(messages, bot_user_id, window=WINDOW):
    """Is one surface of this app alive while the other is silent? Pure.

    Returns (state, detail, counts). States:

      interactions-dead  mentions are answered and no interactive message the
                         app posted was ever followed by anything. This note.
      all-dead           neither surface responds. That is a transport with
                         nowhere to deliver, and a different note.
      events-dead        clicks are handled and mentions are not, which is the
                         mirror case and belongs to the events subscription.
      healthy            both surfaces respond.
      no-evidence        the app has posted nothing clickable, so there is
                         nothing to conclude and this says so.

    The pair is the point. A single silence count cannot tell a missing
    interactivity route from a missing transport, and those have different
    repairs on different screens.
    """
    rows = []
    marker = "<@%s>" % bot_user_id if bot_user_id else None
    for m in messages or []:
        ts = (m or {}).get("ts")
        if ts is None:
            continue
        mine = bool((m or {}).get("bot_id")) or (
            bot_user_id and (m or {}).get("user") == bot_user_id)
        rows.append((float(ts), bool(mine), m or {}))
    rows.sort(key=lambda r: r[0])
    own_ts = [ts for ts, mine, _m in rows if mine]
    # A reply that is itself another prompt is not evidence that a click was
    # handled, so only the app's plain messages count as a follow-up.
    own_plain = [ts for ts, mine, m in rows if mine and not interactive_elements(m)]

    mentions = [ts for ts, mine, m in rows
                if not mine and marker and marker in str(m.get("text") or "")]
    answered = sum(1 for ts in mentions
                   if any(ts < o <= ts + window for o in own_ts))

    interactive = [ts for ts, mine, m in rows if mine and interactive_elements(m)]
    followed = sum(1 for ts in interactive
                   if any(ts < o <= ts + window for o in own_plain))

    counts = {"mentions": len(mentions), "answered_mentions": answered,
              "interactive_messages": len(interactive),
              "followed_interactive": followed}
    if not interactive:
        return ("no-evidence", "the app has posted nothing clickable in the messages "
                               "read, so its interactivity cannot be judged from here",
                counts)
    events_alive = answered > 0
    clicks_alive = followed > 0
    if clicks_alive and events_alive:
        return ("healthy", "both surfaces show responses", counts)
    if clicks_alive:
        return ("events-dead", "clicks are handled and %d mention(s) are not, which is "
                               "the other surface" % len(mentions), counts)
    if events_alive:
        return ("interactions-dead",
                "%d of %d mention(s) answered within %.0fs, and 0 of %d interactive "
                "message(s) followed by a plain reply"
                % (answered, len(mentions), window, len(interactive)), counts)
    return ("all-dead", "neither surface responds, which is a transport problem rather "
                        "than an interactivity switch", counts)


def verdict(route, split):
    """Put the configuration and the evidence together. Pure.

    Returns (state, detail). Either half alone is weak: a switch that is off on
    an app which has never posted a button is not an incident, and an app that
    ignores clicks with the switch on has a different problem.
    """
    if route == "unknown":
        return ("unproven", "the manifest could not be read, so the route is unknown "
                            "and no finding is claimed")
    if split == "all-dead":
        return ("transport", "no surface responds; read the note on an app with no "
                             "transport configured before blaming interactivity")
    if route == "disabled":
        if split in ("interactions-dead", "no-evidence"):
            return ("switch-off", "the app posts buttons it has no way of hearing "
                                  "about")
        return ("contradiction", "interactivity reads as disabled and clicks appear to "
                                 "be handled; the manifest may be stale")
    if route == "enabled-no-url":
        return ("no-url", "the switch is on and the field is empty, so payloads are "
                          "produced and dropped")
    if split == "interactions-dead":
        return ("route-set-still-dead", "a route is configured and clicks still produce "
                                        "nothing; the endpoint or the handler is next, "
                                        "not the switch")
    if split == "events-dead":
        return ("events", "interactions work and events do not; that is the other "
                          "surface and the other screen")
    if split == "healthy":
        return ("clean", "both surfaces respond")
    return ("unproven", "the route is configured and the workspace shows nothing to "
                        "judge it by")


def load_manifest(args):
    """Read the live manifest. A read: export returns it and changes nothing."""
    if args.manifest:
        return json.loads(open(args.manifest, encoding="utf-8").read())
    token = os.environ.get(args.config_token_env)
    if not token or not args.app_id:
        log.warning("manifest   unavailable     set %s and --app-id, or pass "
                    "--manifest", args.config_token_env)
        return None
    body = requests.get(API + "apps.manifest.export",
                        headers={"Authorization": "Bearer " + token},
                        params={"app_id": args.app_id}, timeout=30).json()
    if body.get("ok") is not True:
        log.error("manifest   unavailable     %s", body.get("error"))
        return None
    return body.get("manifest") or {}


def page_history(session, channel, limit, max_pages):
    """Page conversations.history. A read."""
    out, cursor, pages = [], "", 0
    while pages < max_pages:
        params = {"channel": channel, "limit": str(limit)}
        if cursor:
            params["cursor"] = cursor
        body = session.get(API + "conversations.history", params=params,
                           timeout=30).json()
        if body.get("ok") is not True:
            log.error("history    unavailable     %s", body.get("error"))
            return out
        out.extend(body.get("messages") or [])
        cursor = ((body.get("response_metadata") or {}).get("next_cursor") or "")
        pages += 1
        if not cursor:
            break
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", default="", help="path to an exported manifest")
    ap.add_argument("--config-token-env", default="SLACK_CONFIG_TOKEN",
                    help="environment variable holding an app configuration token")
    ap.add_argument("--app-id", default="", help="app id, for the manifest read")
    ap.add_argument("--channel", default="",
                    help="a channel the app posts interactive messages into")
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN",
                    help="environment variable holding a bot token, for the history")
    ap.add_argument("--window", type=float, default=WINDOW,
                    help="seconds after a trigger in which a response still counts")
    ap.add_argument("--limit", type=int, default=200)
    ap.add_argument("--max-pages", type=int, default=4)
    args = ap.parse_args()

    manifest = load_manifest(args)
    route, detail, facts = interaction_route(manifest)
    if facts:
        log.info("manifest   socket mode %s", "on" if facts.get("socket_mode") else "off")
    (log.warning if route in ("disabled", "enabled-no-url") else log.info)(
        "route      %-15s %s", route, detail)

    split, split_detail, counts = ("no-evidence", "no channel was read", {})
    elements = []
    if args.channel:
        token = os.environ.get(args.token_env)
        if not token:
            log.warning("history    set %s to read the app's own blocks", args.token_env)
        else:
            s = requests.Session()
            s.headers.update({"Authorization": "Bearer " + token})
            who = s.get(API + "auth.test", timeout=30).json()
            if who.get("ok") is not True:
                log.error("auth.test  unavailable     %s", who.get("error"))
                return 2
            messages = page_history(s, args.channel, args.limit, args.max_pages)
            mine = [m for m in messages
                    if m.get("bot_id") or m.get("user") == who.get("user_id")]
            clickable = [m for m in mine if interactive_elements(m)]
            log.info("blocks     %d app message(s) read, %d carrying something "
                     "clickable", len(mine), len(clickable))
            for m in clickable[:1]:
                elements = interactive_elements(m)
                for where, kind, action in elements:
                    log.info("element    %-15s %-16s %s", where, kind, action or "-")
            log.info("identity   %s (%s) in %s", who.get("user_id"), who.get("user"),
                     who.get("team"))
            log.info("history    %d message(s) from %s", len(messages), args.channel)
            split, split_detail, counts = surface_split(messages, who.get("user_id"),
                                                        args.window)
            (log.warning if split in ("interactions-dead", "all-dead") else log.info)(
                "split      %-15s %s", split, split_detail)
            log.info("split      counts          %s", counts)

    needed, kinds = needs_options_url(elements)
    options, options_detail = options_route(facts, needed)
    (log.warning if options == "missing" else log.info)(
        "options    %-15s %s", options, options_detail)
    if kinds:
        log.info("options    kinds           %s", ", ".join(kinds))

    state, why = verdict(route, split)
    findings = ("switch-off", "no-url", "route-set-still-dead", "transport",
                "contradiction")
    (log.warning if state in findings else log.info)("verdict    %-15s %s", state, why)
    if state in ("switch-off", "no-url"):
        log.warning("  repair: enable Interactivity & Shortcuts and set its Request URL "
                    "to the route that already serves events")
        log.warning("  repair: budget the same three seconds to acknowledge an "
                    "interaction as an event; the deadline is identical")
        if options == "missing":
            log.warning("  repair: set message_menu_options_url as well, or the "
                        "external menus will open empty after the switch is on")
        return 1
    return 1 if state in findings else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-interactivity-route.mjs",
"js": '''/**
 * Find out where a click on this app's buttons goes, and whether it goes.
 *
 * Read only. apps.manifest.export, auth.test and conversations.history are
 * reads. Nothing here posts a message, presses a button, or sends anything to
 * an interactivity endpoint.
 *
 * Posting an interactive message and receiving the interaction are two
 * different things: chat:write posts the button, and the payload a click
 * produces goes to the Interactivity Request URL, a separate switch with a
 * separate field on a separate screen.
 */

import { readFileSync } from 'node:fs';

const API = 'https://slack.com/api/';

// Every element type that produces a block_actions payload when a person uses
// it. Buttons are the obvious ones; the menus fail identically and quietly.
export const ELEMENT_KINDS = new Set([
  'button', 'workflow_button', 'overflow', 'datepicker', 'timepicker',
  'datetimepicker', 'checkboxes', 'radio_buttons',
  'static_select', 'external_select', 'users_select', 'conversations_select',
  'channels_select', 'multi_static_select', 'multi_external_select',
  'multi_users_select', 'multi_conversations_select', 'multi_channels_select',
  'rich_text_input', 'plain_text_input', 'number_input', 'email_text_input',
  'url_text_input', 'file_input',
]);

// The two that make Slack call back for their choices at a third URL.
export const EXTERNAL_KINDS = new Set(['external_select', 'multi_external_select']);

export const WINDOW = 120.0;

/**
 * Where does a click on this app's buttons go? Pure.
 * Returns [state, detail, facts]; socket, url, enabled-no-url, disabled, unknown.
 */
export function interactionRoute(manifest) {
  if (manifest === null || manifest === undefined) {
    return ['unknown', 'no manifest was read, so the interactivity route cannot be '
      + 'established; an app configuration token is what reads it', {}];
  }
  const settings = manifest.settings ?? {};
  const socket = Boolean(settings.socket_mode_enabled);
  const inter = settings.interactivity ?? {};
  const enabled = Boolean(inter.is_enabled);
  const url = String(inter.request_url ?? '').trim();
  const optionsUrl = String(inter.message_menu_options_url ?? '').trim();
  const facts = {
    socket_mode: socket,
    is_enabled: enabled,
    request_url: url,
    message_menu_options_url: optionsUrl,
  };
  if (socket) {
    return ['socket', 'Socket Mode carries interactions as well as events, so neither '
      + 'interactivity URL field is consulted', facts];
  }
  if (!enabled) {
    return ['disabled', 'Interactivity is switched off, so a click produces no payload '
      + 'at all and nothing is delivered anywhere', facts];
  }
  if (!url) {
    return ['enabled-no-url', 'Interactivity is enabled with an empty request_url, so '
      + 'the payload is produced and has no destination', facts];
  }
  return ['url', `interactions are delivered to ${url}`, facts];
}

/**
 * Everything in this posted message that a person can act on. Pure.
 * Returns [[location, kind, actionId], ...].
 */
export function interactiveElements(message) {
  const out = [];
  const blocks = (message ?? {}).blocks ?? [];
  blocks.forEach((rawBlock, index) => {
    const block = rawBlock ?? {};
    const kind = String(block.type ?? '');
    if (kind === 'actions') {
      for (const rawElement of block.elements ?? []) {
        const element = rawElement ?? {};
        if (ELEMENT_KINDS.has(String(element.type ?? ''))) {
          out.push([`actions[${index}]`, String(element.type),
            String(element.action_id ?? '')]);
        }
      }
    }
    const accessory = block.accessory ?? {};
    if (ELEMENT_KINDS.has(String(accessory.type ?? ''))) {
      out.push([`${kind || 'block'}[${index}]`, String(accessory.type),
        String(accessory.action_id ?? '')]);
    }
    if (kind === 'input' && block.dispatch_action) {
      const element = block.element ?? {};
      if (ELEMENT_KINDS.has(String(element.type ?? ''))) {
        out.push([`input[${index}]`, String(element.type),
          String(element.action_id ?? '')]);
      }
    }
  });
  return out;
}

/**
 * Do any of these elements make Slack call back for their choices? Pure.
 * Returns [needed, kinds].
 */
export function needsOptionsUrl(elements) {
  const kinds = [...new Set((elements ?? [])
    .map(([, kind]) => kind)
    .filter((kind) => EXTERNAL_KINDS.has(kind)))].sort();
  return [kinds.length > 0, kinds];
}

/**
 * Is the options URL there, and does this app need it? Pure.
 * Returns [state, detail]; not-needed, socket, missing, configured.
 */
export function optionsRoute(facts, needed) {
  if ((facts ?? {}).socket_mode) {
    return ['socket', 'external select options arrive over the socket like everything '
      + 'else'];
  }
  if (!needed) return ['not-needed', 'no external select has been posted by this app'];
  if (!(facts ?? {}).message_menu_options_url) {
    return ['missing', 'an external select has been posted and '
      + 'message_menu_options_url is empty, so the menu opens empty'];
  }
  return ['configured',
    `options are fetched from ${(facts ?? {}).message_menu_options_url}`];
}

/**
 * Is one surface of this app alive while the other is silent? Pure.
 * Returns [state, detail, counts]; interactions-dead, all-dead, events-dead,
 * healthy, no-evidence. The pair is the point.
 */
export function surfaceSplit(messages, botUserId, window = WINDOW) {
  const marker = botUserId ? `<@${botUserId}>` : null;
  const rows = [];
  for (const m of messages ?? []) {
    const ts = (m ?? {}).ts;
    if (ts === null || ts === undefined) continue;
    const mine = Boolean((m ?? {}).bot_id)
      || Boolean(botUserId && (m ?? {}).user === botUserId);
    rows.push([Number(ts), mine, m ?? {}]);
  }
  rows.sort((a, b) => a[0] - b[0]);
  const ownTs = rows.filter(([, mine]) => mine).map(([ts]) => ts);
  // A reply that is itself another prompt is not evidence that a click was
  // handled, so only the app plain messages count as a follow-up.
  const ownPlain = rows.filter(([, mine, m]) => mine && !interactiveElements(m).length)
    .map(([ts]) => ts);

  const mentions = rows
    .filter(([, mine, m]) => !mine && marker && String(m.text ?? '').includes(marker))
    .map(([ts]) => ts);
  const answered = mentions
    .filter((ts) => ownTs.some((o) => o > ts && o <= ts + window)).length;

  const interactive = rows
    .filter(([, mine, m]) => mine && interactiveElements(m).length)
    .map(([ts]) => ts);
  const followed = interactive
    .filter((ts) => ownPlain.some((o) => o > ts && o <= ts + window)).length;

  const counts = {
    mentions: mentions.length,
    answered_mentions: answered,
    interactive_messages: interactive.length,
    followed_interactive: followed,
  };
  if (!interactive.length) {
    return ['no-evidence', 'the app has posted nothing clickable in the messages read, '
      + 'so its interactivity cannot be judged from here', counts];
  }
  const eventsAlive = answered > 0;
  const clicksAlive = followed > 0;
  if (clicksAlive && eventsAlive) return ['healthy', 'both surfaces show responses', counts];
  if (clicksAlive) {
    return ['events-dead', `clicks are handled and ${mentions.length} mention(s) are `
      + 'not, which is the other surface', counts];
  }
  if (eventsAlive) {
    return ['interactions-dead',
      `${answered} of ${mentions.length} mention(s) answered within `
      + `${window.toFixed(0)}s, and 0 of ${interactive.length} interactive message(s) `
      + 'followed by a plain reply', counts];
  }
  return ['all-dead', 'neither surface responds, which is a transport problem rather '
    + 'than an interactivity switch', counts];
}

/**
 * Put the configuration and the evidence together. Pure.
 * Returns [state, detail].
 */
export function verdict(route, split) {
  if (route === 'unknown') {
    return ['unproven', 'the manifest could not be read, so the route is unknown and no '
      + 'finding is claimed'];
  }
  if (split === 'all-dead') {
    return ['transport', 'no surface responds; read the note on an app with no '
      + 'transport configured before blaming interactivity'];
  }
  if (route === 'disabled') {
    if (split === 'interactions-dead' || split === 'no-evidence') {
      return ['switch-off', 'the app posts buttons it has no way of hearing about'];
    }
    return ['contradiction', 'interactivity reads as disabled and clicks appear to be '
      + 'handled; the manifest may be stale'];
  }
  if (route === 'enabled-no-url') {
    return ['no-url', 'the switch is on and the field is empty, so payloads are '
      + 'produced and dropped'];
  }
  if (split === 'interactions-dead') {
    return ['route-set-still-dead', 'a route is configured and clicks still produce '
      + 'nothing; the endpoint or the handler is next, not the switch'];
  }
  if (split === 'events-dead') {
    return ['events', 'interactions work and events do not; that is the other surface '
      + 'and the other screen'];
  }
  if (split === 'healthy') return ['clean', 'both surfaces respond'];
  return ['unproven', 'the route is configured and the workspace shows nothing to judge '
    + 'it by'];
}

function arg(args, name, fallback = null) {
  const i = args.indexOf(name);
  return i === -1 ? fallback : args[i + 1];
}

async function loadManifest(args) {
  const path = arg(args, '--manifest', '');
  if (path) return JSON.parse(readFileSync(path, 'utf8'));
  const tokenEnv = arg(args, '--config-token-env', 'SLACK_CONFIG_TOKEN');
  const appId = arg(args, '--app-id', '');
  const token = process.env[tokenEnv];
  if (!token || !appId) {
    console.warn(`manifest   unavailable     set ${tokenEnv} and --app-id, or pass `
      + '--manifest');
    return null;
  }
  const params = new URLSearchParams({ app_id: appId });
  const body = await (await fetch(`${API}apps.manifest.export?${params}`,
    { headers: { Authorization: `Bearer ${token}` } })).json();
  if (body.ok !== true) {
    console.error(`manifest   unavailable     ${body.error}`);
    return null;
  }
  return body.manifest ?? {};
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
      console.error(`history    unavailable     ${body.error}`);
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
  const manifest = await loadManifest(args);
  const [route, detail, facts] = interactionRoute(manifest);
  if (Object.keys(facts).length) {
    console.log(`manifest   socket mode ${facts.socket_mode ? 'on' : 'off'}`);
  }
  const routeLine = `route      ${route.padEnd(15)} ${detail}`;
  if (route === 'disabled' || route === 'enabled-no-url') console.warn(routeLine);
  else console.log(routeLine);

  let split = 'no-evidence';
  let elements = [];
  const channel = arg(args, '--channel', '');
  if (channel) {
    const tokenEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
    const token = process.env[tokenEnv];
    if (!token) console.warn(`history    set ${tokenEnv} to read the app blocks`);
    else {
      const headers = { Authorization: `Bearer ${token}` };
      const who = await (await fetch(`${API}auth.test`, { headers })).json();
      if (who.ok !== true) {
        console.error(`auth.test  unavailable     ${who.error}`);
        process.exitCode = 2;
        return;
      }
      const messages = await pageHistory(headers, channel,
        Number(arg(args, '--limit', '200')), Number(arg(args, '--max-pages', '4')));
      const mine = messages.filter((m) => m.bot_id || m.user === who.user_id);
      const clickable = mine.filter((m) => interactiveElements(m).length);
      console.log(`blocks     ${mine.length} app message(s) read, ${clickable.length} `
        + 'carrying something clickable');
      if (clickable.length) {
        elements = interactiveElements(clickable[0]);
        for (const [where, kind, action] of elements) {
          console.log(`element    ${where.padEnd(15)} ${kind.padEnd(16)} ${action || '-'}`);
        }
      }
      console.log(`identity   ${who.user_id} (${who.user}) in ${who.team}`);
      console.log(`history    ${messages.length} message(s) from ${channel}`);
      const window = Number(arg(args, '--window', String(WINDOW)));
      const [splitState, splitDetail, counts] = surfaceSplit(messages, who.user_id,
        window);
      split = splitState;
      const row = `split      ${splitState.padEnd(15)} ${splitDetail}`;
      if (splitState === 'interactions-dead' || splitState === 'all-dead') console.warn(row);
      else console.log(row);
      console.log(`split      counts          ${JSON.stringify(counts)}`);
    }
  }

  const [needed, kinds] = needsOptionsUrl(elements);
  const [options, optionsDetail] = optionsRoute(facts, needed);
  const optionsLine = `options    ${options.padEnd(15)} ${optionsDetail}`;
  if (options === 'missing') console.warn(optionsLine); else console.log(optionsLine);
  if (kinds.length) console.log(`options    kinds           ${kinds.join(', ')}`);

  const [state, why] = verdict(route, split);
  const findings = ['switch-off', 'no-url', 'route-set-still-dead', 'transport',
    'contradiction'];
  const verdictLine = `verdict    ${state.padEnd(15)} ${why}`;
  if (findings.includes(state)) console.warn(verdictLine); else console.log(verdictLine);
  if (state === 'switch-off' || state === 'no-url') {
    console.warn('  repair: enable Interactivity & Shortcuts and set its Request URL to '
      + 'the route that already serves events');
    console.warn('  repair: budget the same three seconds to acknowledge an interaction '
      + 'as an event; the deadline is identical');
    if (options === 'missing') {
      console.warn('  repair: set message_menu_options_url as well, or the external '
        + 'menus will open empty after the switch is on');
    }
  }
  if (findings.includes(state)) process.exitCode = 1;
}

// Only run when invoked directly, so importing this module in the tests does
// not execute main().
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The tests that earn their place are the ones that stop this note taking credit for other people's failures. <code>interaction_route</code> is asserted to return <code>socket</code> before it looks at either URL field, because an empty interactivity URL on a Socket Mode app is correct and flagging it would be a false positive on every one of them. <code>surface_split</code> is asserted to return <code>all-dead</code> when neither surface answers, which is the transport note rather than this one. And <code>interactive_elements</code> is checked against an accessory and a dispatching input as well as a plain button, because a count built from buttons alone misses the menus.",
"test_py_file": "test_slack_interactivity_route.py",
"test_py": '''from slack_interactivity_route import (
    interaction_route, interactive_elements, needs_options_url, options_route,
    surface_split, verdict,
)


def manifest(socket=False, enabled=False, url="", options_url=""):
    return {"settings": {
        "socket_mode_enabled": socket,
        "interactivity": {"is_enabled": enabled, "request_url": url,
                          "message_menu_options_url": options_url},
    }}


BUTTONS = {"blocks": [
    {"type": "section", "text": {"type": "mrkdwn", "text": "deploy 4.2?"}},
    {"type": "actions", "elements": [
        {"type": "button", "action_id": "approve_deploy"},
        {"type": "button", "action_id": "reject_deploy"}]},
]}


def test_the_switch_being_off_is_the_route_this_note_owns():
    state, detail, facts = interaction_route(manifest())
    assert state == "disabled"
    assert facts["is_enabled"] is False
    assert "no payload at all" in detail


def test_socket_mode_is_checked_before_either_url_field():
    state, _detail, _facts = interaction_route(manifest(socket=True, enabled=False))
    assert state == "socket"


def test_an_empty_url_on_a_socket_app_is_not_a_fault():
    assert interaction_route(manifest(socket=True, enabled=True, url=""))[0] == "socket"


def test_enabled_with_an_empty_url_is_its_own_state():
    assert interaction_route(manifest(enabled=True))[0] == "enabled-no-url"
    assert interaction_route(manifest(enabled=True, url="  "))[0] == "enabled-no-url"


def test_enabled_with_a_url_reports_where_clicks_go():
    state, detail, _facts = interaction_route(
        manifest(enabled=True, url="https://ops.example.com/slack/events"))
    assert state == "url"
    assert "ops.example.com" in detail


def test_no_manifest_is_unknown_rather_than_disabled():
    assert interaction_route(None)[0] == "unknown"


def test_buttons_in_an_actions_block_are_found_with_their_action_ids():
    found = interactive_elements(BUTTONS)
    assert [f[1] for f in found] == ["button", "button"]
    assert [f[2] for f in found] == ["approve_deploy", "reject_deploy"]


def test_a_section_accessory_counts_even_though_it_is_not_in_an_actions_block():
    msg = {"blocks": [{"type": "section", "accessory": {"type": "overflow",
                                                        "action_id": "more"}}]}
    assert interactive_elements(msg) == [("section[0]", "overflow", "more")]


def test_an_input_block_only_counts_when_it_dispatches():
    quiet = {"blocks": [{"type": "input", "element": {"type": "plain_text_input",
                                                      "action_id": "note"}}]}
    loud = {"blocks": [{"type": "input", "dispatch_action": True,
                        "element": {"type": "plain_text_input", "action_id": "note"}}]}
    assert interactive_elements(quiet) == []
    assert interactive_elements(loud) == [("input[0]", "plain_text_input", "note")]


def test_a_message_of_plain_text_has_nothing_to_click():
    assert interactive_elements({"text": "deploy finished"}) == []
    assert interactive_elements({}) == []


def test_an_unknown_element_type_is_not_counted():
    msg = {"blocks": [{"type": "actions", "elements": [{"type": "image"}]}]}
    assert interactive_elements(msg) == []


def test_external_selects_are_the_ones_that_need_the_third_url():
    elements = [("actions[0]", "external_select", "pick")]
    assert needs_options_url(elements) == (True, ["external_select"])
    assert needs_options_url([("actions[0]", "button", "go")]) == (False, [])


def test_the_options_url_is_only_a_finding_when_something_needs_it():
    _state, _detail, facts = interaction_route(manifest(enabled=True, url="https://x/y"))
    assert options_route(facts, False)[0] == "not-needed"
    assert options_route(facts, True)[0] == "missing"


def test_the_socket_carries_options_too():
    _state, _detail, facts = interaction_route(manifest(socket=True))
    assert options_route(facts, True)[0] == "socket"


def test_answered_mentions_beside_ignored_buttons_is_this_note():
    msgs = [{"ts": "100", "user": "U1", "text": "<@UBOT> status"},
            {"ts": "105", "user": "UBOT", "text": "all green"},
            {"ts": "200", "user": "UBOT", **BUTTONS},
            {"ts": "300", "user": "UBOT", **BUTTONS}]
    state, _detail, counts = surface_split(msgs, "UBOT")
    assert state == "interactions-dead"
    assert counts == {"mentions": 1, "answered_mentions": 1,
                      "interactive_messages": 2, "followed_interactive": 0}


def test_both_surfaces_silent_is_the_transport_note_and_not_this_one():
    msgs = [{"ts": "50", "user": "UBOT", **BUTTONS},
            {"ts": "100", "user": "U1", "text": "<@UBOT> status"}]
    assert surface_split(msgs, "UBOT")[0] == "all-dead"


def test_a_follow_up_after_a_button_message_means_clicks_are_arriving():
    msgs = [{"ts": "100", "user": "U1", "text": "<@UBOT> status"},
            {"ts": "105", "user": "UBOT", "text": "all green"},
            {"ts": "200", "user": "UBOT", **BUTTONS},
            {"ts": "210", "user": "UBOT", "text": "approved by <@U1>"}]
    assert surface_split(msgs, "UBOT")[0] == "healthy"


def test_a_follow_up_outside_the_window_does_not_count():
    msgs = [{"ts": "100", "user": "U1", "text": "<@UBOT> status"},
            {"ts": "105", "user": "UBOT", "text": "all green"},
            {"ts": "200", "user": "UBOT", **BUTTONS},
            {"ts": "9000", "user": "UBOT", "text": "unrelated"}]
    assert surface_split(msgs, "UBOT", window=60.0)[0] == "interactions-dead"


def test_an_app_that_posts_nothing_clickable_proves_nothing():
    msgs = [{"ts": "100", "user": "U1", "text": "<@UBOT> status"},
            {"ts": "105", "user": "UBOT", "text": "all green"}]
    assert surface_split(msgs, "UBOT")[0] == "no-evidence"


def test_the_switch_and_the_evidence_are_only_a_verdict_together():
    assert verdict("disabled", "interactions-dead")[0] == "switch-off"
    assert verdict("disabled", "no-evidence")[0] == "switch-off"
    assert verdict("url", "interactions-dead")[0] == "route-set-still-dead"
    assert verdict("socket", "healthy")[0] == "clean"


def test_a_dead_transport_is_handed_over_rather_than_claimed():
    state, detail = verdict("disabled", "all-dead")
    assert state == "transport"
    assert "no transport configured" in detail


def test_an_unreadable_manifest_claims_nothing():
    assert verdict("unknown", "interactions-dead")[0] == "unproven"
''',
"test_js_file": "slack-interactivity-route.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  interactionRoute, interactiveElements, needsOptionsUrl, optionsRoute, surfaceSplit,
  verdict,
} from './slack-interactivity-route.mjs';

function manifest({
  socket = false, enabled = false, url = '', optionsUrl = '',
} = {}) {
  return {
    settings: {
      socket_mode_enabled: socket,
      interactivity: {
        is_enabled: enabled,
        request_url: url,
        message_menu_options_url: optionsUrl,
      },
    },
  };
}

const BUTTONS = {
  blocks: [
    { type: 'section', text: { type: 'mrkdwn', text: 'deploy 4.2?' } },
    {
      type: 'actions',
      elements: [
        { type: 'button', action_id: 'approve_deploy' },
        { type: 'button', action_id: 'reject_deploy' },
      ],
    },
  ],
};

test('the switch being off is the route this note owns', () => {
  const [state, detail, facts] = interactionRoute(manifest());
  assert.equal(state, 'disabled');
  assert.equal(facts.is_enabled, false);
  assert.match(detail, /no payload at all/);
});

test('socket mode is checked before either url field', () => {
  assert.equal(interactionRoute(manifest({ socket: true }))[0], 'socket');
});

test('an empty url on a socket app is not a fault', () => {
  assert.equal(interactionRoute(manifest({ socket: true, enabled: true }))[0], 'socket');
});

test('enabled with an empty url is its own state', () => {
  assert.equal(interactionRoute(manifest({ enabled: true }))[0], 'enabled-no-url');
  assert.equal(interactionRoute(manifest({ enabled: true, url: '  ' }))[0],
    'enabled-no-url');
});

test('enabled with a url reports where clicks go', () => {
  const [state, detail] = interactionRoute(
    manifest({ enabled: true, url: 'https://ops.example.com/slack/events' }));
  assert.equal(state, 'url');
  assert.match(detail, /ops.example.com/);
});

test('no manifest is unknown rather than disabled', () => {
  assert.equal(interactionRoute(null)[0], 'unknown');
});

test('buttons in an actions block are found with their action ids', () => {
  const found = interactiveElements(BUTTONS);
  assert.deepEqual(found.map((f) => f[1]), ['button', 'button']);
  assert.deepEqual(found.map((f) => f[2]), ['approve_deploy', 'reject_deploy']);
});

test('a section accessory counts even though it is not in an actions block', () => {
  const msg = {
    blocks: [{ type: 'section', accessory: { type: 'overflow', action_id: 'more' } }],
  };
  assert.deepEqual(interactiveElements(msg), [['section[0]', 'overflow', 'more']]);
});

test('an input block only counts when it dispatches', () => {
  const quiet = {
    blocks: [{ type: 'input', element: { type: 'plain_text_input', action_id: 'note' } }],
  };
  const loud = {
    blocks: [{
      type: 'input',
      dispatch_action: true,
      element: { type: 'plain_text_input', action_id: 'note' },
    }],
  };
  assert.deepEqual(interactiveElements(quiet), []);
  assert.deepEqual(interactiveElements(loud),
    [['input[0]', 'plain_text_input', 'note']]);
});

test('a message of plain text has nothing to click', () => {
  assert.deepEqual(interactiveElements({ text: 'deploy finished' }), []);
  assert.deepEqual(interactiveElements({}), []);
});

test('an unknown element type is not counted', () => {
  const msg = { blocks: [{ type: 'actions', elements: [{ type: 'image' }] }] };
  assert.deepEqual(interactiveElements(msg), []);
});

test('external selects are the ones that need the third url', () => {
  assert.deepEqual(needsOptionsUrl([['actions[0]', 'external_select', 'pick']]),
    [true, ['external_select']]);
  assert.deepEqual(needsOptionsUrl([['actions[0]', 'button', 'go']]), [false, []]);
});

test('the options url is only a finding when something needs it', () => {
  const [, , facts] = interactionRoute(
    manifest({ enabled: true, url: 'https://ops.example.com/slack' }));
  assert.equal(optionsRoute(facts, false)[0], 'not-needed');
  assert.equal(optionsRoute(facts, true)[0], 'missing');
});

test('the socket carries options too', () => {
  const [, , facts] = interactionRoute(manifest({ socket: true }));
  assert.equal(optionsRoute(facts, true)[0], 'socket');
});

test('answered mentions beside ignored buttons is this note', () => {
  const msgs = [{ ts: '100', user: 'U1', text: '<@UBOT> status' },
    { ts: '105', user: 'UBOT', text: 'all green' },
    { ts: '200', user: 'UBOT', ...BUTTONS },
    { ts: '300', user: 'UBOT', ...BUTTONS }];
  const [state, , counts] = surfaceSplit(msgs, 'UBOT');
  assert.equal(state, 'interactions-dead');
  assert.deepEqual(counts, {
    mentions: 1, answered_mentions: 1, interactive_messages: 2, followed_interactive: 0,
  });
});

test('both surfaces silent is the transport note and not this one', () => {
  const msgs = [{ ts: '50', user: 'UBOT', ...BUTTONS },
    { ts: '100', user: 'U1', text: '<@UBOT> status' }];
  assert.equal(surfaceSplit(msgs, 'UBOT')[0], 'all-dead');
});

test('a follow up after a button message means clicks are arriving', () => {
  const msgs = [{ ts: '100', user: 'U1', text: '<@UBOT> status' },
    { ts: '105', user: 'UBOT', text: 'all green' },
    { ts: '200', user: 'UBOT', ...BUTTONS },
    { ts: '210', user: 'UBOT', text: 'approved by <@U1>' }];
  assert.equal(surfaceSplit(msgs, 'UBOT')[0], 'healthy');
});

test('a follow up outside the window does not count', () => {
  const msgs = [{ ts: '100', user: 'U1', text: '<@UBOT> status' },
    { ts: '105', user: 'UBOT', text: 'all green' },
    { ts: '200', user: 'UBOT', ...BUTTONS },
    { ts: '9000', user: 'UBOT', text: 'unrelated' }];
  assert.equal(surfaceSplit(msgs, 'UBOT', 60)[0], 'interactions-dead');
});

test('an app that posts nothing clickable proves nothing', () => {
  const msgs = [{ ts: '100', user: 'U1', text: '<@UBOT> status' },
    { ts: '105', user: 'UBOT', text: 'all green' }];
  assert.equal(surfaceSplit(msgs, 'UBOT')[0], 'no-evidence');
});

test('the switch and the evidence are only a verdict together', () => {
  assert.equal(verdict('disabled', 'interactions-dead')[0], 'switch-off');
  assert.equal(verdict('disabled', 'no-evidence')[0], 'switch-off');
  assert.equal(verdict('url', 'interactions-dead')[0], 'route-set-still-dead');
  assert.equal(verdict('socket', 'healthy')[0], 'clean');
});

test('a dead transport is handed over rather than claimed', () => {
  const [state, detail] = verdict('disabled', 'all-dead');
  assert.equal(state, 'transport');
  assert.match(detail, /no transport configured/);
});

test('an unreadable manifest claims nothing', () => {
  assert.equal(verdict('unknown', 'interactions-dead')[0], 'unproven');
});
''',
"faq": [
 ("The buttons render perfectly. Doesn't that prove the app is configured?",
  "It proves the app can post, which needs chat:write and nothing else. Rendering happens in the Slack client from the blocks in your message; Slack does not consult your app's configuration to draw a button, and it will happily render one on an app that has no way to receive the click. The two capabilities are independent, and the visible one is the one that does not need the switch."),
 ("Why is there a separate URL for interactivity at all?",
  "Historically because interactions arrived long after events and were designed as their own product surface, with their own screen, their own payload shape and their own verification. Practically it means an app can serve one and not the other, which is occasionally useful and mostly a trap. Most frameworks collapse the distinction again at the receiving end: Bolt serves events, interactions, commands and options on one route, so the fix is usually pasting the URL you already have into a second box."),
 ("It works on my machine over Socket Mode. What changes in production?",
  "Socket Mode carries everything down one connection, so neither interactivity URL field is consulted and interactivity works whether or not the switch has ever been touched. Production has the switch off and events over HTTPS, which is why buttons that worked all through development fail on the first day. The script checks Socket Mode first for exactly this reason, and reports a socket app as routed rather than as broken."),
 ("Our menus open completely empty, but our buttons work. Same problem?",
  "The same screen, a different field. An external select does not carry its choices in the message: Slack fetches them at the moment the menu opens, from message_menu_options_url, which is configured separately from the interactivity request URL. Interactivity can be enabled and working and every external menu still open empty because that third field was never filled in. The script raises it only when the app has actually posted an external select."),
 ("Could the clicks be arriving and the handler dropping them silently?",
  "Yes, and the script is built to tell you that rather than guess. If the manifest shows a configured route and the workspace still shows no follow-up after any interactive message, the verdict is route-set-still-dead, which points at the endpoint and the handler rather than at the configuration screen. The behavioural half is also honest about its blind spot: a click that opens a modal and does nothing else leaves no trace in the channel, so with a small sample it reports no-evidence instead of a conclusion."),
],
"related": [
 ("/slack/trigger-id-expired/", "the other three seconds, on the interaction you did receive"),
 ("/slack/invalid-blocks/", "when the message with the buttons never posts at all"),
 ("/slack/three-second-timeout/", "the acknowledgement budget an interaction shares with an event"),
],
"citations": [CITE_INTERACTIVITY, CITE_MANIFEST_EXPORT, CITE_JAVA_1189,
              CITE_SO_INTERACTIVITY],
})
GUIDES.append({
"slug": "manifest-drift",
"title": "The repo manifest, the live manifest and the granted scopes",
"description": "Slack app config is editable in two places that never reconcile. Export the live manifest, diff it against the repo, then add the third list nobody checks.",
"h1": "The repo manifest, the live manifest and the granted scopes",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack manifest drift repo vs live",
             "apps.manifest.export diff",
             "slack app scopes disappeared after reinstall",
             "slack manifest overwritten by ci",
             "slack app config edited in web ui"],
"deps": "Python 3.9+ with requests, or Node.js 18+; an app configuration token with app_configurations:read, the manifest.json from your repository, and any bot token so the granted scope header can be read",
"lead": "The reinstall was supposed to be routine. A new workspace, the same app, the same install link everyone has used for a year. Twenty minutes later half the app is broken: it cannot read the channel list, it cannot see reactions, and the two event subscriptions that drive the whole product are gone.</p><p>Nobody deployed anything. The repository has not changed in six weeks. What changed is that the reinstall applied the manifest that was <em>live</em>, and the live manifest has been quietly different from the one in the repository since a Sunday in March, when somebody fixed an outage through the web UI at two in the morning and never came back to write it down.",
"short_answer": """<p>Slack app configuration is editable in <strong>two places that do not reconcile</strong>: the web UI and the App Manifest API. A UI edit does not touch your repository, and the next <code>apps.manifest.update</code> from CI does not preserve the UI edit &mdash; it replaces the document. Neither side warns you. The divergence is invisible until something applies one version over the other, which is usually a reinstall, and by then the scopes or the subscriptions have already gone.</p>
<p>So make it visible on a schedule. <code>apps.manifest.export?app_id=A...</code> returns the live manifest as JSON with an app configuration token. <strong>Normalise both documents &mdash; sort the keys, sort the arrays &mdash; and diff them path by path</strong>, so a reordered scope list is not reported as a change and a genuinely missing scope is. Report what moved: which paths exist only in the repo, which exist only on the live app, and which exist in both with different values.</p>
<p>Then add the column that almost nobody checks. The scopes on the <strong>installed token</strong> are a third list, readable from the <code>X-OAuth-Scopes</code> response header on any Web API call, and it can differ from both of the others. A scope added to the live app is not granted until somebody reinstalls; a scope removed from the live app stays in the token until somebody reinstalls. Three lists, drifting independently, and only one of them is what your code is actually allowed to do today.</p>""",
"problem": """<p>The two editors have opposite failure modes and both are silent. The web UI is fast, correct, and available at two in the morning during an incident, which is exactly when it gets used and exactly when nobody is writing anything down. The API is authoritative, repeatable and version controlled, and it clobbers: <code>apps.manifest.update</code> replaces the manifest wholesale, so the emergency scope somebody added in March vanishes the next time CI runs, without CI having any idea it removed anything.</p>
<p>What makes the drift so hard to notice is that <em>nothing applies it</em>. The live manifest is the app's configuration and it is already in effect; the repo manifest is a file. They can disagree for a year with no symptom at all, because the only events that reconcile them are a manifest update from CI and an install or reinstall. Both are rare, both happen under time pressure, and both look like routine operations right up to the moment a scope disappears.</p>
<p>The scope column adds a third timeline that nobody has a mental model for. Adding <code>reactions:read</code> to the live app does not give the running token <code>reactions:read</code> &mdash; the token was minted at install time and carries what it carried then. So a manifest can be correct, a deploy can be green, and the API can still answer <code>missing_scope</code>, because the grant is a fourth thing that only moves when a human clicks Allow. Teams read the manifest, see the scope listed, and go looking for the bug somewhere else entirely.</p>
<p>And then there is ownership. Once the repo and the app disagree, nobody can say which is right, because both are plausible: the repo was reviewed, and the app is what has actually been running for eight months. The resolution is always a judgement call made under pressure with incomplete memory of who changed what in March, and the usual outcome is that somebody picks one and finds out which parts of the other one mattered afterwards.</p>""",
"why": """<p><strong>Normalisation before comparison is what makes this a tool rather than a nuisance.</strong> Slack does not promise key order and does not promise array order, so a naive text diff of two exported manifests reports thirty differences of which zero matter. Sorting keys and sorting arrays first means a difference in the output is a difference in the app. Without that step the check gets ignored inside a fortnight, which is the same as not having it.</p>
<p><strong>Diff by path, not by line.</strong> The output that is useful in an incident is <code>oauth_config.scopes.bot changed: reactions:read removed</code>, not a hunk of JSON with a minus in front of it. So the script flattens both documents into dotted paths first, keeps arrays of scalars whole so a scope list is one finding rather than six, and keys arrays of objects by their own identity &mdash; <code>features.slash_commands[/deploy].url</code> tells you which command moved, where <code>slash_commands[2].url</code> tells you nothing at all if somebody reordered them.</p>
<p><strong>Not every difference deserves the same alarm.</strong> A changed description or a bumped manifest version is noise; a changed scope list, event subscription, interactivity setting or Socket Mode flag is the app behaving differently. The script grades each path and counts them separately, so a build step can fail on the second category without failing every time somebody fixes a typo in the app's blurb.</p>
<p><strong>The third list is the one that explains the errors you are actually seeing.</strong> <code>X-OAuth-Scopes</code> comes back on any Web API response and is the definitive statement of what the installed token may do. Held against the repo and the live manifest it produces seven distinct states, and three of them are actionable in different ways: a scope in the repo and nowhere else was never deployed, a scope in the repo and the app but not the token needs a reinstall, and a scope in the token that no longer appears in the app will be lost the next time anybody reinstalls. That last one is the trap that started this note.</p>
<p><strong>The script reads and refuses to reconcile.</strong> <code>apps.manifest.export</code> is a read. <code>apps.manifest.update</code> is a write, it replaces the whole document, and a tool that offered to &ldquo;just sync it&rdquo; would be capable of deleting the March fix during the incident it was called in to explain. The repair is printed as a decision for a person: pick an authority, backport the difference, then automate the direction you chose.</p>
<p><strong>When the configuration token is dead, the answer is &ldquo;not assessed&rdquo;.</strong> That credential lives twelve hours and rotates through its own endpoint, and every manifest check in this note depends on it. A run that could not read the live manifest reports exactly that, rather than an empty diff that reads like agreement.</p>""",
"steps": [
 {"h": "Normalise both documents before comparing anything",
  "body": """<p><code>normalise</code> walks the manifest recursively, sorts dictionary keys and sorts every array by its canonical serialisation. Slack promises no ordering, so this is the step that stops the check reporting thirty differences that are not differences. Run it on the repo document and the exported document alike.</p>"""},
 {"h": "Flatten to paths so the report names the field",
  "body": """<p><code>flatten</code> turns a manifest into <code>{path: value}</code>. Arrays of scalars stay whole, so a scope list is one row rather than fifteen. Arrays of objects are keyed by the object's own identity &mdash; a slash command by its command, a shortcut by its callback id &mdash; so a reordering is not a finding and <code>features.slash_commands[/deploy].url</code> says which one moved.</p>"""},
 {"h": "Diff the two, path by path",
  "body": """<p><code>diff_manifests</code> returns every path where the two documents disagree, marked <code>only-in-repo</code>, <code>only-in-live</code> or <code>changed</code>, with both values. For the array rows, <code>set_delta</code> reduces a changed scope list to what was added and what was removed, which is the sentence that goes in the incident notes.</p>"""},
 {"h": "Separate what matters from what does not",
  "body": """<p><code>severity</code> grades each path <code>load-bearing</code>, <code>cosmetic</code> or <code>volatile</code>. Scopes, event subscriptions, interactivity, Socket Mode, redirect URLs, commands and shortcuts change what the app can do. Descriptions and manifest metadata do not. A CI gate that fails on the first category is one somebody keeps; one that fails on all three is one somebody deletes.</p>"""},
 {"h": "Add the granted scopes as a third column",
  "body": """<p><code>scope_triangle</code> takes the repo scopes, the live scopes and the <code>X-OAuth-Scopes</code> header from any Web API response, and sorts the union into seven states. The interesting ones are <code>not-yet-granted</code> (deployed, never reinstalled), <code>ui-only</code> (added through the web UI and installed, and the repo has never heard of it) and <code>stale-grant</code> (the token still carries it and nothing declares it any more).</p>"""},
 {"h": "Pick an authority and automate that direction",
  "body": """<p>The printed repair is a decision, not a command: make the repository authoritative, run the update from CI on every change, and add this diff as a build step. Where an emergency UI edit is unavoidable, exporting the manifest back into the repository is part of closing the incident. The script never offers to sync for you, because syncing in the wrong direction is how the March fix disappears.</p>"""},
],
"verify": """<p>Backport the difference, commit the exported manifest, and run it again in CI. The number to watch is the load-bearing count; cosmetic drift can stay non-fatal indefinitely.</p>
<pre><code class="language-bash">python3 slack_manifest_drift.py --repo-manifest manifest.json --app-id A05DEPB0T
# repo       manifest.json    142 path(s)
# live       A05DEPB0T        139 path(s)
# drift      drifted          4 load-bearing, 1 cosmetic, 1 volatile
# path       oauth_config.scopes.bot            changed        load-bearing
#            added: none  removed: reactions:read, groups:read
# path       settings.event_subscriptions.bot_events  changed  load-bearing
#            added: none  removed: reaction_added, member_joined_channel
# path       settings.socket_mode_enabled       changed        load-bearing
#            repo: False  live: True
# path       features.slash_commands[/deploy].url  changed     load-bearing
#            repo: https://ops.example.com/cmd  live: https://a1b2.ngrok-free.app/cmd
# path       display_information.description     changed        cosmetic
# path       _metadata.minor_version             only-in-live   volatile
# scopes     aligned          11
# scopes     not-yet-granted  chat:write.public - in the repo and the app, not the token
# scopes     stale-grant      files:read - the token holds it and nothing declares it
# verdict    the deployed app is not the app in source control
#   repair: decide which document is authoritative before changing either one
#   repair: backport the live differences into the repo, then run apps.manifest.update
#           from CI on every change and fail the build on load-bearing drift</code></pre>""",
"code_intro": "This is a small diff engine and almost all of the value is in the two steps before the comparison. <code>normalise</code> sorts keys and arrays so ordering is never a finding, and <code>flatten</code> reduces both documents to dotted paths with arrays of scalars kept whole and arrays of objects keyed by their own identity. After that <code>diff_manifests</code> is six lines. <code>scope_triangle</code> is the part that turns a configuration diff into an explanation of today's errors, because the token's grant is a third list and it moves on a different clock from either document.",
"py_file": "slack_manifest_drift.py",
"py": '''"""Diff the manifest in your repository against the one Slack is running.

Read only. apps.manifest.export and auth.test are reads; the repository
manifest is read from disk. apps.manifest.update - the method that would
reconcile the two - is a write, it replaces the whole document, and this script
never calls it. Syncing in the wrong direction is how the emergency fix
somebody made through the web UI in March disappears, so the repair is printed
as a decision for a person.

Three lists can disagree and they move on different clocks: the manifest in the
repository, the manifest live on the app, and the scopes the installed token
was actually granted. The last one only changes when a human reinstalls.
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_manifest_drift")

API = "https://slack.com/api/"

# Fields whose own identity is a better key than their position, so a
# reordering is not reported as a change and the path says which item moved.
LIST_KEYS = ("command", "callback_id", "action_id", "name", "type", "domain")

# Paths where a difference changes what the app can do.
LOAD_BEARING = (
    "oauth_config.scopes", "oauth_config.redirect_urls",
    "settings.event_subscriptions", "settings.interactivity",
    "settings.socket_mode_enabled", "settings.org_deploy_enabled",
    "settings.token_rotation_enabled", "settings.allowed_ip_address_ranges",
    "features.slash_commands", "features.shortcuts", "features.bot_user",
    "features.unfurl_domains", "features.app_home", "features.workflow_steps",
)

# Paths that differ for reasons nobody chose, and should never fail a build.
VOLATILE = ("_metadata",)


def _canonical(value):
    """A stable string for any JSON value, for ordering. Pure."""
    return json.dumps(value, sort_keys=True, default=str)


def normalise(doc):
    """Sort every key and every array so two manifests compare by value. Pure.

    Slack promises no key order and no array order, so a naive text diff of two
    exports reports differences that are not differences. Doing this first is
    what makes the output worth reading, and a check nobody trusts is the same
    as no check.
    """
    if isinstance(doc, dict):
        return {k: normalise(doc[k]) for k in sorted(doc)}
    if isinstance(doc, list):
        return sorted((normalise(item) for item in doc), key=_canonical)
    return doc


def _item_key(item, index):
    """Name a list item by its own identity where it has one. Pure."""
    if isinstance(item, dict):
        for key in LIST_KEYS:
            if item.get(key):
                return str(item[key])
    return str(index)


def flatten(doc, prefix=""):
    """Reduce a manifest to {dotted path: value}. Pure.

    Arrays of scalars are kept whole as a tuple, because "the scope list
    changed" is one finding and "scopes[3] changed" is six. Arrays of objects
    are keyed by the item's own identity, so slash_commands[/deploy].url names
    the command that moved rather than a position that means nothing after a
    reorder.
    """
    out = {}
    if isinstance(doc, dict):
        if not doc and prefix:
            out[prefix] = {}
        for key in sorted(doc):
            path = "%s.%s" % (prefix, key) if prefix else str(key)
            out.update(flatten(doc[key], path))
        return out
    if isinstance(doc, list):
        if all(not isinstance(item, (dict, list)) for item in doc):
            out[prefix or "."] = tuple(doc)
            return out
        for index, item in enumerate(doc):
            out.update(flatten(item, "%s[%s]" % (prefix, _item_key(item, index))))
        return out
    out[prefix or "."] = doc
    return out


def diff_manifests(repo, live):
    """What moved between the repository manifest and the live one? Pure.

    Returns [(path, state, repo_value, live_value)] sorted by path, with state
    only-in-repo, only-in-live or changed. Both documents are normalised first,
    so ordering never appears here.
    """
    left = flatten(normalise(repo or {}))
    right = flatten(normalise(live or {}))
    out = []
    for path in sorted(set(left) | set(right)):
        if path not in right:
            out.append((path, "only-in-repo", left[path], None))
        elif path not in left:
            out.append((path, "only-in-live", None, right[path]))
        elif left[path] != right[path]:
            out.append((path, "changed", left[path], right[path]))
    return out


def set_delta(before, after):
    """For an array that changed, what came and what went. Pure.

    Returns (added, removed). This is the line that goes in the incident notes:
    a scope list that "changed" is not actionable, and "reactions:read was
    removed" is.
    """
    left = set(before or ())
    right = set(after or ())
    return (sorted(right - left), sorted(left - right))


def severity(path):
    """How much does a difference at this path matter? Pure.

    Returns load-bearing, cosmetic or volatile. A gate that fails on
    load-bearing drift is one a team keeps; a gate that fails because somebody
    fixed a typo in the app description is one they delete in a fortnight.
    """
    text = str(path or "")
    for prefix in VOLATILE:
        if text == prefix or text.startswith(prefix + ".") or text.startswith(prefix + "["):
            return "volatile"
    for prefix in LOAD_BEARING:
        if text == prefix or text.startswith(prefix + ".") or text.startswith(prefix + "["):
            return "load-bearing"
    return "cosmetic"


def drift_summary(diffs):
    """One state and three counts for the whole comparison. Pure.

    Returns (state, counts) with state aligned, cosmetic-only or drifted.
    """
    counts = {"load-bearing": 0, "cosmetic": 0, "volatile": 0}
    for path, _state, _left, _right in diffs or []:
        counts[severity(path)] += 1
    if not any(counts.values()):
        return ("aligned", counts)
    if counts["load-bearing"]:
        return ("drifted", counts)
    return ("cosmetic-only", counts)


def scope_triangle(repo_scopes, live_scopes, granted_scopes):
    """Three scope lists that drift independently. Pure.

    Returns {state: [scope, ...]} over the union of all three. The states exist
    because each combination has a different repair:

      aligned            in all three. Nothing to do.
      repo-only          declared in the repo and nowhere else: the change was
                         never deployed to the app at all.
      not-yet-granted    in the repo and on the app, not in the token. Somebody
                         has to reinstall before the code can use it.
      ui-only            on the app and in the token, absent from the repo:
                         added through the web UI, and the next update from CI
                         will remove it.
      ui-only-ungranted  on the app only. Added in the UI, never installed, and
                         invisible to both the repo and the running code.
      removed-live       in the repo and the token, gone from the app. The
                         token still works and the next reinstall drops it.
      stale-grant        in the token alone. Nothing declares it any more.
    """
    repo = {str(s) for s in (repo_scopes or [])}
    live = {str(s) for s in (live_scopes or [])}
    granted = {str(s) for s in (granted_scopes or [])}
    states = {"aligned": [], "repo-only": [], "not-yet-granted": [], "ui-only": [],
              "ui-only-ungranted": [], "removed-live": [], "stale-grant": []}
    table = {
        (True, True, True): "aligned",
        (True, False, False): "repo-only",
        (True, True, False): "not-yet-granted",
        (False, True, True): "ui-only",
        (False, True, False): "ui-only-ungranted",
        (True, False, True): "removed-live",
        (False, False, True): "stale-grant",
    }
    for scope in sorted(repo | live | granted):
        key = (scope in repo, scope in live, scope in granted)
        states[table[key]].append(scope)
    return states


def split_scopes(header):
    """Read the X-OAuth-Scopes response header into a list. Pure."""
    return [part.strip() for part in str(header or "").split(",") if part.strip()]


def bot_scopes(manifest):
    """The bot scopes declared by a manifest. Pure."""
    oauth = (manifest or {}).get("oauth_config") or {}
    return list((oauth.get("scopes") or {}).get("bot") or [])


def load_live(args):
    """Read the live manifest. A read: export returns it and changes nothing."""
    if args.live_manifest:
        return json.loads(open(args.live_manifest, encoding="utf-8").read())
    token = os.environ.get(args.config_token_env)
    if not token or not args.app_id:
        log.warning("live       unavailable      set %s and --app-id, or pass "
                    "--live-manifest", args.config_token_env)
        return None
    body = requests.get(API + "apps.manifest.export",
                        headers={"Authorization": "Bearer " + token},
                        params={"app_id": args.app_id}, timeout=30).json()
    if body.get("ok") is not True:
        log.error("live       unavailable      %s; every manifest finding below is not "
                  "assessed rather than clean", body.get("error"))
        return None
    return body.get("manifest") or {}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-manifest", required=True,
                    help="path to the manifest checked into your repository")
    ap.add_argument("--live-manifest", default="",
                    help="path to an already exported manifest, instead of exporting")
    ap.add_argument("--config-token-env", default="SLACK_CONFIG_TOKEN",
                    help="environment variable holding an app configuration token")
    ap.add_argument("--app-id", default="", help="app id, for the manifest read")
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN",
                    help="environment variable holding a bot token, to read the grant")
    ap.add_argument("--granted", default="",
                    help="comma separated granted scopes, instead of reading the header")
    args = ap.parse_args()

    repo = json.loads(open(args.repo_manifest, encoding="utf-8").read())
    live = load_live(args)
    log.info("repo       %-16s %d path(s)", args.repo_manifest,
             len(flatten(normalise(repo))))
    if live is None:
        log.warning("verdict    not assessed     the live manifest could not be read, "
                    "so no comparison was made")
        return 2
    log.info("live       %-16s %d path(s)", args.app_id or args.live_manifest,
             len(flatten(normalise(live))))

    diffs = diff_manifests(repo, live)
    state, counts = drift_summary(diffs)
    (log.warning if state == "drifted" else log.info)(
        "drift      %-16s %d load-bearing, %d cosmetic, %d volatile", state,
        counts["load-bearing"], counts["cosmetic"], counts["volatile"])
    for path, how, left, right in diffs:
        grade = severity(path)
        (log.warning if grade == "load-bearing" else log.info)(
            "path       %-40s %-13s %s", path, how, grade)
        if isinstance(left, tuple) or isinstance(right, tuple):
            added, removed = set_delta(left or (), right or ())
            log.info("           added: %s  removed: %s",
                     ", ".join(added) or "none", ", ".join(removed) or "none")
        else:
            log.info("           repo: %s  live: %s", left, right)

    granted = split_scopes(args.granted)
    if not granted:
        token = os.environ.get(args.token_env)
        if token:
            reply = requests.get(API + "auth.test",
                                 headers={"Authorization": "Bearer " + token},
                                 timeout=30)
            granted = split_scopes(reply.headers.get("x-oauth-scopes"))
        else:
            log.warning("scopes     set %s or pass --granted to read the third column",
                        args.token_env)
    triangle = scope_triangle(bot_scopes(repo), bot_scopes(live), granted)
    for name in ("aligned", "repo-only", "not-yet-granted", "ui-only",
                 "ui-only-ungranted", "removed-live", "stale-grant"):
        items = triangle[name]
        if not items:
            continue
        if name == "aligned":
            log.info("scopes     %-16s %d", name, len(items))
        else:
            log.warning("scopes     %-16s %s", name, ", ".join(items))

    if state == "drifted" or any(triangle[n] for n in
                                 ("repo-only", "ui-only", "removed-live",
                                  "stale-grant")):
        log.warning("verdict    the deployed app is not the app in source control")
        log.warning("  repair: decide which document is authoritative before changing "
                    "either one; this script will not choose for you")
        log.warning("  repair: backport the differences, then run apps.manifest.update "
                    "from CI on every change and fail the build on load-bearing drift")
        log.warning("  repair: reinstall after any scope change, because the grant on "
                    "the installed token moves only when a human clicks Allow")
        return 1
    log.info("verdict    aligned          the repo, the app and the grant agree")
    return 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-manifest-drift.mjs",
"js": '''/**
 * Diff the manifest in your repository against the one Slack is running.
 *
 * Read only. apps.manifest.export and auth.test are reads; the repository
 * manifest is read from disk. apps.manifest.update - the method that would
 * reconcile the two - is a write that replaces the whole document, and this
 * script never calls it.
 *
 * Three lists can disagree and they move on different clocks: the manifest in
 * the repository, the manifest live on the app, and the scopes the installed
 * token was actually granted.
 */

import { readFileSync } from 'node:fs';

const API = 'https://slack.com/api/';

// Fields whose own identity is a better key than their position.
export const LIST_KEYS = ['command', 'callback_id', 'action_id', 'name', 'type',
  'domain'];

// Paths where a difference changes what the app can do.
export const LOAD_BEARING = [
  'oauth_config.scopes', 'oauth_config.redirect_urls',
  'settings.event_subscriptions', 'settings.interactivity',
  'settings.socket_mode_enabled', 'settings.org_deploy_enabled',
  'settings.token_rotation_enabled', 'settings.allowed_ip_address_ranges',
  'features.slash_commands', 'features.shortcuts', 'features.bot_user',
  'features.unfurl_domains', 'features.app_home', 'features.workflow_steps',
];

// Paths that differ for reasons nobody chose.
export const VOLATILE = ['_metadata'];

function canonical(value) {
  if (value === null || typeof value !== 'object') return JSON.stringify(value) ?? 'null';
  if (Array.isArray(value)) return `[${value.map(canonical).join(',')}]`;
  return `{${Object.keys(value).sort().map((k) => `${JSON.stringify(k)}:${canonical(value[k])}`).join(',')}}`;
}

/**
 * Sort every key and every array so two manifests compare by value. Pure.
 * Slack promises no ordering, so this is what makes the diff worth reading.
 */
export function normalise(doc) {
  if (Array.isArray(doc)) {
    return doc.map(normalise).sort((a, b) => (canonical(a) < canonical(b) ? -1 : 1));
  }
  if (doc !== null && typeof doc === 'object') {
    const out = {};
    for (const key of Object.keys(doc).sort()) out[key] = normalise(doc[key]);
    return out;
  }
  return doc;
}

function itemKey(item, index) {
  if (item !== null && typeof item === 'object' && !Array.isArray(item)) {
    for (const key of LIST_KEYS) if (item[key]) return String(item[key]);
  }
  return String(index);
}

/**
 * Reduce a manifest to {dotted path: value}. Pure.
 * Arrays of scalars stay whole; arrays of objects are keyed by identity.
 */
export function flatten(doc, prefix = '') {
  const out = {};
  if (Array.isArray(doc)) {
    if (doc.every((item) => item === null || typeof item !== 'object')) {
      out[prefix || '.'] = [...doc];
      return out;
    }
    doc.forEach((item, index) => {
      Object.assign(out, flatten(item, `${prefix}[${itemKey(item, index)}]`));
    });
    return out;
  }
  if (doc !== null && typeof doc === 'object') {
    const keys = Object.keys(doc).sort();
    if (!keys.length && prefix) out[prefix] = {};
    for (const key of keys) {
      Object.assign(out, flatten(doc[key], prefix ? `${prefix}.${key}` : String(key)));
    }
    return out;
  }
  out[prefix || '.'] = doc;
  return out;
}

/**
 * What moved between the repository manifest and the live one? Pure.
 * Returns [[path, state, repoValue, liveValue], ...] sorted by path.
 */
export function diffManifests(repo, live) {
  const left = flatten(normalise(repo ?? {}));
  const right = flatten(normalise(live ?? {}));
  const paths = [...new Set([...Object.keys(left), ...Object.keys(right)])].sort();
  const out = [];
  for (const path of paths) {
    const inLeft = Object.prototype.hasOwnProperty.call(left, path);
    const inRight = Object.prototype.hasOwnProperty.call(right, path);
    if (!inRight) out.push([path, 'only-in-repo', left[path], null]);
    else if (!inLeft) out.push([path, 'only-in-live', null, right[path]]);
    else if (canonical(left[path]) !== canonical(right[path])) {
      out.push([path, 'changed', left[path], right[path]]);
    }
  }
  return out;
}

/**
 * For an array that changed, what came and what went. Pure.
 * Returns [added, removed].
 */
export function setDelta(before, after) {
  const left = new Set(before ?? []);
  const right = new Set(after ?? []);
  return [
    [...right].filter((v) => !left.has(v)).sort(),
    [...left].filter((v) => !right.has(v)).sort(),
  ];
}

/**
 * How much does a difference at this path matter? Pure.
 * Returns load-bearing, cosmetic or volatile.
 */
export function severity(path) {
  const text = String(path ?? '');
  const under = (prefix) => text === prefix || text.startsWith(`${prefix}.`)
    || text.startsWith(`${prefix}[`);
  if (VOLATILE.some(under)) return 'volatile';
  if (LOAD_BEARING.some(under)) return 'load-bearing';
  return 'cosmetic';
}

/**
 * One state and three counts for the whole comparison. Pure.
 * Returns [state, counts]; aligned, cosmetic-only, drifted.
 */
export function driftSummary(diffs) {
  const counts = { 'load-bearing': 0, cosmetic: 0, volatile: 0 };
  for (const [path] of diffs ?? []) counts[severity(path)] += 1;
  const total = counts['load-bearing'] + counts.cosmetic + counts.volatile;
  if (!total) return ['aligned', counts];
  if (counts['load-bearing']) return ['drifted', counts];
  return ['cosmetic-only', counts];
}

/**
 * Three scope lists that drift independently. Pure.
 * Returns {state: [scope, ...]} over the union of all three.
 */
export function scopeTriangle(repoScopes, liveScopes, grantedScopes) {
  const repo = new Set((repoScopes ?? []).map(String));
  const live = new Set((liveScopes ?? []).map(String));
  const granted = new Set((grantedScopes ?? []).map(String));
  const states = {
    aligned: [],
    'repo-only': [],
    'not-yet-granted': [],
    'ui-only': [],
    'ui-only-ungranted': [],
    'removed-live': [],
    'stale-grant': [],
  };
  const table = {
    'true,true,true': 'aligned',
    'true,false,false': 'repo-only',
    'true,true,false': 'not-yet-granted',
    'false,true,true': 'ui-only',
    'false,true,false': 'ui-only-ungranted',
    'true,false,true': 'removed-live',
    'false,false,true': 'stale-grant',
  };
  const union = [...new Set([...repo, ...live, ...granted])].sort();
  for (const scope of union) {
    const key = `${repo.has(scope)},${live.has(scope)},${granted.has(scope)}`;
    states[table[key]].push(scope);
  }
  return states;
}

/** Read the X-OAuth-Scopes response header into a list. Pure. */
export function splitScopes(header) {
  return String(header ?? '').split(',').map((p) => p.trim()).filter(Boolean);
}

/** The bot scopes declared by a manifest. Pure. */
export function botScopes(manifest) {
  const oauth = (manifest ?? {}).oauth_config ?? {};
  return [...((oauth.scopes ?? {}).bot ?? [])];
}

function arg(args, name, fallback = null) {
  const i = args.indexOf(name);
  return i === -1 ? fallback : args[i + 1];
}

async function loadLive(args) {
  const path = arg(args, '--live-manifest', '');
  if (path) return JSON.parse(readFileSync(path, 'utf8'));
  const tokenEnv = arg(args, '--config-token-env', 'SLACK_CONFIG_TOKEN');
  const appId = arg(args, '--app-id', '');
  const token = process.env[tokenEnv];
  if (!token || !appId) {
    console.warn(`live       unavailable      set ${tokenEnv} and --app-id, or pass `
      + '--live-manifest');
    return null;
  }
  const params = new URLSearchParams({ app_id: appId });
  const body = await (await fetch(`${API}apps.manifest.export?${params}`,
    { headers: { Authorization: `Bearer ${token}` } })).json();
  if (body.ok !== true) {
    console.error(`live       unavailable      ${body.error}; every manifest finding `
      + 'below is not assessed rather than clean');
    return null;
  }
  return body.manifest ?? {};
}

async function main() {
  const args = process.argv.slice(2);
  const repoPath = arg(args, '--repo-manifest', '');
  if (!repoPath) {
    console.error('pass --repo-manifest with the manifest checked into your repository');
    process.exitCode = 2;
    return;
  }
  const repo = JSON.parse(readFileSync(repoPath, 'utf8'));
  const live = await loadLive(args);
  console.log(`repo       ${repoPath.padEnd(16)} `
    + `${Object.keys(flatten(normalise(repo))).length} path(s)`);
  if (live === null) {
    console.warn('verdict    not assessed     the live manifest could not be read, so '
      + 'no comparison was made');
    process.exitCode = 2;
    return;
  }
  console.log(`live       ${String(arg(args, '--app-id', '') || arg(args, '--live-manifest', '')).padEnd(16)} `
    + `${Object.keys(flatten(normalise(live))).length} path(s)`);

  const diffs = diffManifests(repo, live);
  const [state, counts] = driftSummary(diffs);
  const head = `drift      ${state.padEnd(16)} ${counts['load-bearing']} load-bearing, `
    + `${counts.cosmetic} cosmetic, ${counts.volatile} volatile`;
  if (state === 'drifted') console.warn(head); else console.log(head);
  for (const [path, how, left, right] of diffs) {
    const grade = severity(path);
    const row = `path       ${path.padEnd(40)} ${how.padEnd(13)} ${grade}`;
    if (grade === 'load-bearing') console.warn(row); else console.log(row);
    if (Array.isArray(left) || Array.isArray(right)) {
      const [added, removed] = setDelta(left ?? [], right ?? []);
      console.log(`           added: ${added.join(', ') || 'none'}  `
        + `removed: ${removed.join(', ') || 'none'}`);
    } else {
      console.log(`           repo: ${left}  live: ${right}`);
    }
  }

  let granted = splitScopes(arg(args, '--granted', ''));
  if (!granted.length) {
    const tokenEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
    const token = process.env[tokenEnv];
    if (token) {
      const reply = await fetch(`${API}auth.test`,
        { headers: { Authorization: `Bearer ${token}` } });
      granted = splitScopes(reply.headers.get('x-oauth-scopes'));
    } else {
      console.warn(`scopes     set ${tokenEnv} or pass --granted to read the third `
        + 'column');
    }
  }
  const triangle = scopeTriangle(botScopes(repo), botScopes(live), granted);
  for (const name of ['aligned', 'repo-only', 'not-yet-granted', 'ui-only',
    'ui-only-ungranted', 'removed-live', 'stale-grant']) {
    const items = triangle[name];
    if (!items.length) continue;
    if (name === 'aligned') console.log(`scopes     ${name.padEnd(16)} ${items.length}`);
    else console.warn(`scopes     ${name.padEnd(16)} ${items.join(', ')}`);
  }

  const scopeFindings = ['repo-only', 'ui-only', 'removed-live', 'stale-grant']
    .some((name) => triangle[name].length);
  if (state === 'drifted' || scopeFindings) {
    console.warn('verdict    the deployed app is not the app in source control');
    console.warn('  repair: decide which document is authoritative before changing '
      + 'either one; this script will not choose for you');
    console.warn('  repair: backport the differences, then run apps.manifest.update '
      + 'from CI on every change and fail the build on load-bearing drift');
    console.warn('  repair: reinstall after any scope change, because the grant on the '
      + 'installed token moves only when a human clicks Allow');
    process.exitCode = 1;
    return;
  }
  console.log('verdict    aligned          the repo, the app and the grant agree');
}

// Only run when invoked directly, so importing this module in the tests does
// not execute main().
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The first two tests are the ones that decide whether anybody keeps this check: a reordered scope list and a reordered set of slash commands must produce <strong>no</strong> findings at all, because a diff that cries wolf on ordering is deleted within a fortnight. After that the tests pin the identity keying (a command is named by its command, not its index), the array rows staying whole so one changed scope list is one row, and every one of the seven states in the scope triangle &mdash; including <code>stale-grant</code>, the one that explains why a token still works for a scope the app no longer declares.",
"test_py_file": "test_slack_manifest_drift.py",
"test_py": '''from slack_manifest_drift import (
    bot_scopes, diff_manifests, drift_summary, flatten, normalise, scope_triangle,
    set_delta, severity, split_scopes,
)


def app(scopes=("chat:write", "channels:read"), events=("app_mention",),
        socket=False, commands=(), description="the release bot"):
    return {
        "_metadata": {"major_version": 1, "minor_version": 1},
        "display_information": {"name": "releasebot", "description": description},
        "oauth_config": {"scopes": {"bot": list(scopes)}},
        "settings": {
            "socket_mode_enabled": socket,
            "event_subscriptions": {"bot_events": list(events)},
        },
        "features": {"slash_commands": list(commands)},
    }


def test_a_reordered_scope_list_is_not_a_difference():
    left = app(scopes=("chat:write", "channels:read"))
    right = app(scopes=("channels:read", "chat:write"))
    assert diff_manifests(left, right) == []


def test_reordered_slash_commands_are_not_a_difference_either():
    one = {"command": "/deploy", "url": "https://ops.example.com/a"}
    two = {"command": "/rollback", "url": "https://ops.example.com/b"}
    assert diff_manifests(app(commands=(one, two)), app(commands=(two, one))) == []


def test_a_command_is_named_by_its_command_and_not_its_index():
    paths = flatten(normalise(app(commands=(
        {"command": "/deploy", "url": "https://ops.example.com/a"},))))
    assert "features.slash_commands[/deploy].url" in paths


def test_a_missing_scope_is_one_row_and_not_six():
    diffs = diff_manifests(app(), app(scopes=("chat:write",)))
    assert len(diffs) == 1
    path, state, left, right = diffs[0]
    assert path == "oauth_config.scopes.bot"
    assert state == "changed"
    assert set_delta(left, right) == ([], ["channels:read"])


def test_a_path_only_the_live_app_has_is_reported_as_such():
    live = app()
    live["settings"]["interactivity"] = {"is_enabled": True}
    diffs = dict((d[0], d[1]) for d in diff_manifests(app(), live))
    assert diffs["settings.interactivity.is_enabled"] == "only-in-live"


def test_a_path_only_the_repo_has_is_reported_as_such():
    repo = app()
    repo["settings"]["interactivity"] = {"is_enabled": True}
    diffs = dict((d[0], d[1]) for d in diff_manifests(repo, app()))
    assert diffs["settings.interactivity.is_enabled"] == "only-in-repo"


def test_scalar_values_are_compared_by_value():
    diffs = diff_manifests(app(socket=False), app(socket=True))
    assert diffs == [("settings.socket_mode_enabled", "changed", False, True)]


def test_scope_and_event_and_socket_paths_are_load_bearing():
    for path in ("oauth_config.scopes.bot",
                 "settings.event_subscriptions.bot_events",
                 "settings.socket_mode_enabled",
                 "features.slash_commands[/deploy].url",
                 "settings.interactivity.request_url"):
        assert severity(path) == "load-bearing"


def test_descriptions_are_cosmetic_and_metadata_is_volatile():
    assert severity("display_information.description") == "cosmetic"
    assert severity("_metadata.minor_version") == "volatile"


def test_a_prefix_match_does_not_leak_across_names():
    assert severity("settings.socket_mode_enabled_at") == "cosmetic"


def test_the_summary_separates_the_gate_from_the_noise():
    state, counts = drift_summary([("display_information.description", "changed",
                                    "a", "b")])
    assert state == "cosmetic-only"
    assert counts["load-bearing"] == 0
    assert drift_summary([])[0] == "aligned"
    assert drift_summary([("oauth_config.scopes.bot", "changed", (), ())])[0] == "drifted"


def test_the_three_lists_agreeing_is_the_only_quiet_state():
    tri = scope_triangle(["chat:write"], ["chat:write"], ["chat:write"])
    assert tri["aligned"] == ["chat:write"]
    assert all(not tri[k] for k in tri if k != "aligned")


def test_a_scope_only_in_the_repo_was_never_deployed():
    tri = scope_triangle(["reactions:read"], [], [])
    assert tri["repo-only"] == ["reactions:read"]


def test_a_scope_deployed_and_never_reinstalled_needs_a_human():
    tri = scope_triangle(["reactions:read"], ["reactions:read"], [])
    assert tri["not-yet-granted"] == ["reactions:read"]


def test_a_scope_added_through_the_web_ui_is_named_as_such():
    tri = scope_triangle([], ["files:read"], ["files:read"])
    assert tri["ui-only"] == ["files:read"]
    assert scope_triangle([], ["files:read"], [])["ui-only-ungranted"] == ["files:read"]


def test_a_scope_removed_from_the_app_still_works_until_a_reinstall():
    tri = scope_triangle(["groups:read"], [], ["groups:read"])
    assert tri["removed-live"] == ["groups:read"]


def test_a_grant_nothing_declares_any_more_is_a_stale_grant():
    tri = scope_triangle([], [], ["im:read"])
    assert tri["stale-grant"] == ["im:read"]


def test_the_grant_header_is_read_from_a_comma_separated_string():
    assert split_scopes("chat:write, channels:read ,") == ["chat:write", "channels:read"]
    assert split_scopes(None) == []


def test_the_bot_scopes_are_read_out_of_the_manifest_shape():
    assert bot_scopes(app(scopes=("chat:write",))) == ["chat:write"]
    assert bot_scopes({}) == []


def test_normalise_leaves_scalars_alone_and_sorts_everything_else():
    assert normalise({"b": [3, 1, 2], "a": 1}) == {"a": 1, "b": [1, 2, 3]}
''',
"test_js_file": "slack-manifest-drift.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  botScopes, diffManifests, driftSummary, flatten, normalise, scopeTriangle, setDelta,
  severity, splitScopes,
} from './slack-manifest-drift.mjs';

function app({
  scopes = ['chat:write', 'channels:read'], events = ['app_mention'], socket = false,
  commands = [], description = 'the release bot',
} = {}) {
  return {
    _metadata: { major_version: 1, minor_version: 1 },
    display_information: { name: 'releasebot', description },
    oauth_config: { scopes: { bot: [...scopes] } },
    settings: {
      socket_mode_enabled: socket,
      event_subscriptions: { bot_events: [...events] },
    },
    features: { slash_commands: [...commands] },
  };
}

test('a reordered scope list is not a difference', () => {
  const left = app({ scopes: ['chat:write', 'channels:read'] });
  const right = app({ scopes: ['channels:read', 'chat:write'] });
  assert.deepEqual(diffManifests(left, right), []);
});

test('reordered slash commands are not a difference either', () => {
  const one = { command: '/deploy', url: 'https://ops.example.com/a' };
  const two = { command: '/rollback', url: 'https://ops.example.com/b' };
  assert.deepEqual(
    diffManifests(app({ commands: [one, two] }), app({ commands: [two, one] })), []);
});

test('a command is named by its command and not its index', () => {
  const paths = flatten(normalise(app({
    commands: [{ command: '/deploy', url: 'https://ops.example.com/a' }],
  })));
  assert.ok('features.slash_commands[/deploy].url' in paths);
});

test('a missing scope is one row and not six', () => {
  const diffs = diffManifests(app(), app({ scopes: ['chat:write'] }));
  assert.equal(diffs.length, 1);
  const [path, state, left, right] = diffs[0];
  assert.equal(path, 'oauth_config.scopes.bot');
  assert.equal(state, 'changed');
  assert.deepEqual(setDelta(left, right), [[], ['channels:read']]);
});

test('a path only the live app has is reported as such', () => {
  const live = app();
  live.settings.interactivity = { is_enabled: true };
  const diffs = Object.fromEntries(diffManifests(app(), live).map((d) => [d[0], d[1]]));
  assert.equal(diffs['settings.interactivity.is_enabled'], 'only-in-live');
});

test('a path only the repo has is reported as such', () => {
  const repo = app();
  repo.settings.interactivity = { is_enabled: true };
  const diffs = Object.fromEntries(diffManifests(repo, app()).map((d) => [d[0], d[1]]));
  assert.equal(diffs['settings.interactivity.is_enabled'], 'only-in-repo');
});

test('scalar values are compared by value', () => {
  assert.deepEqual(diffManifests(app({ socket: false }), app({ socket: true })),
    [['settings.socket_mode_enabled', 'changed', false, true]]);
});

test('scope and event and socket paths are load bearing', () => {
  for (const path of ['oauth_config.scopes.bot',
    'settings.event_subscriptions.bot_events',
    'settings.socket_mode_enabled',
    'features.slash_commands[/deploy].url',
    'settings.interactivity.request_url']) {
    assert.equal(severity(path), 'load-bearing');
  }
});

test('descriptions are cosmetic and metadata is volatile', () => {
  assert.equal(severity('display_information.description'), 'cosmetic');
  assert.equal(severity('_metadata.minor_version'), 'volatile');
});

test('a prefix match does not leak across names', () => {
  assert.equal(severity('settings.socket_mode_enabled_at'), 'cosmetic');
});

test('the summary separates the gate from the noise', () => {
  const [state, counts] = driftSummary([['display_information.description', 'changed',
    'a', 'b']]);
  assert.equal(state, 'cosmetic-only');
  assert.equal(counts['load-bearing'], 0);
  assert.equal(driftSummary([])[0], 'aligned');
  assert.equal(driftSummary([['oauth_config.scopes.bot', 'changed', [], []]])[0],
    'drifted');
});

test('the three lists agreeing is the only quiet state', () => {
  const tri = scopeTriangle(['chat:write'], ['chat:write'], ['chat:write']);
  assert.deepEqual(tri.aligned, ['chat:write']);
  for (const key of Object.keys(tri)) {
    if (key !== 'aligned') assert.deepEqual(tri[key], []);
  }
});

test('a scope only in the repo was never deployed', () => {
  assert.deepEqual(scopeTriangle(['reactions:read'], [], [])['repo-only'],
    ['reactions:read']);
});

test('a scope deployed and never reinstalled needs a human', () => {
  assert.deepEqual(
    scopeTriangle(['reactions:read'], ['reactions:read'], [])['not-yet-granted'],
    ['reactions:read']);
});

test('a scope added through the web ui is named as such', () => {
  assert.deepEqual(scopeTriangle([], ['files:read'], ['files:read'])['ui-only'],
    ['files:read']);
  assert.deepEqual(scopeTriangle([], ['files:read'], [])['ui-only-ungranted'],
    ['files:read']);
});

test('a scope removed from the app still works until a reinstall', () => {
  assert.deepEqual(scopeTriangle(['groups:read'], [], ['groups:read'])['removed-live'],
    ['groups:read']);
});

test('a grant nothing declares any more is a stale grant', () => {
  assert.deepEqual(scopeTriangle([], [], ['im:read'])['stale-grant'], ['im:read']);
});

test('the grant header is read from a comma separated string', () => {
  assert.deepEqual(splitScopes('chat:write, channels:read ,'),
    ['chat:write', 'channels:read']);
  assert.deepEqual(splitScopes(null), []);
});

test('the bot scopes are read out of the manifest shape', () => {
  assert.deepEqual(botScopes(app({ scopes: ['chat:write'] })), ['chat:write']);
  assert.deepEqual(botScopes({}), []);
});

test('normalise leaves scalars alone and sorts everything else', () => {
  assert.deepEqual(normalise({ b: [3, 1, 2], a: 1 }), { a: 1, b: [1, 2, 3] });
});
''',
"faq": [
 ("Which one is authoritative, the repo or the live app?",
  "Whichever you decide, and the decision has to come before the next change rather than during the next incident. The workable arrangement is repo-authoritative: the manifest is reviewed like code, CI applies it with apps.manifest.update, and this diff runs as a build step so drift fails the build. That only holds if emergency UI edits are followed by exporting the manifest back into the repository as part of closing the incident, because otherwise the next CI run silently deletes the fix that stopped the outage."),
 ("Why does this script refuse to sync the two for me?",
  "Because syncing means calling apps.manifest.update, which is a write and which replaces the entire document rather than merging into it. Run in the wrong direction it removes the change somebody made through the UI at two in the morning, and the moment you are most likely to run it is the moment you understand that change least. This section's scripts read and print; the reconciliation is a decision with consequences, and it belongs to a person who knows which half is the fix."),
 ("Our manifest matches, so why is the API still returning missing_scope?",
  "Because the token's grant is a third list. Scopes take effect at install time: adding one to the app changes what will be requested next time somebody installs, not what the existing token may do. Until a human reinstalls and clicks Allow, the running token carries exactly what it carried before. That state is not-yet-granted in this script's output, and it is the single most common reason a correct-looking manifest coexists with a scope error."),
 ("What is a stale grant, and is it dangerous?",
  "It is a scope the installed token still carries that no longer appears anywhere in the app's configuration, usually because somebody removed it from the manifest without reinstalling. It is not dangerous today and it is a trap tomorrow: the code still works, so nobody notices, and the capability disappears the moment anyone reinstalls the app for any reason. A workspace migration or a routine reauthorisation then looks like it broke the app, when what it actually did was apply a change made months earlier."),
 ("Should this run in CI or on a schedule?",
  "Both, for different reasons. In CI it catches the case where somebody edits the repository manifest and expects that to be enough. On a schedule, daily, it catches the case CI cannot see at all: a UI edit made after the last build, which will sit undetected until the next deploy overwrites it. Note the check needs an app configuration token, which lives twelve hours, so a scheduled run has to rotate its refresh token rather than store an access token."),
],
"related": [
 ("/slack/config-token-expired/", "the twelve-hour credential this whole check depends on"),
 ("/slack/missing-scope-on-read/", "the error a not-yet-granted scope produces at runtime"),
 ("/slack/over-broad-scopes/", "the scopes in the grant that nothing ever calls"),
],
"citations": [CITE_MANIFEST_EXPORT, CITE_MANIFEST_UPDATE, CITE_MANIFESTS, CITE_BOLT_2437],
})
GUIDES.append({
"slug": "app-not-distributed",
"title": "Add to Slack works in one workspace and nowhere else",
"description": "Public distribution is a separate gate with its own checklist. Read the prerequisites out of the manifest before a customer tries to install, not after.",
"h1": "Add to Slack works in one workspace and nowhere else",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack app cannot be installed in another workspace",
             "slack activate public distribution",
             "slack add to slack button error",
             "slack app single workspace only",
             "slack installation store required"],
"deps": "Python 3.9+ with requests, or Node.js 18+; an app configuration token with app_configurations:read for the manifest, and a bot token so the one workspace the app lives in can be named",
"lead": "The pilot customer said yes on a Tuesday and asked for the install link. Somebody pasted the &ldquo;Add to Slack&rdquo; URL from the README, the customer's admin clicked it, and Slack showed an error page instead of a permissions screen.</p><p>Everything about the app is finished. It has an HTTPS Request URL, verified. It has events, interactivity, three slash commands and a home tab. It has been running in the company's own workspace for eight months without a single incident. What it has never had is a redirect URL, an installation store, or a single click on <em>Activate Public Distribution</em> &mdash; and none of those is something you discover by testing the app, because the app works perfectly in the one place it has ever been installed.",
"short_answer": """<p>A new Slack app is installable <strong>only in the workspace it was created in</strong> until public distribution is activated, and activation is a gate with its own checklist rather than a switch you flip at the end. It needs a valid OAuth redirect URL, an install URL with nothing workspace-specific baked into it, and &mdash; for Enterprise Grid customers &mdash; org-wide installation enabled on top of that.</p>
<p>Most of the checklist is readable ahead of time from <code>apps.manifest.export</code>. <strong>An app with an empty <code>oauth_config.redirect_urls[]</code> cannot run a public OAuth flow at all</strong>, because there is nowhere for Slack to send the authorisation code. <code>settings.org_deploy_enabled</code> says whether an org admin can install once for the whole enterprise. Read together, they classify the app's audience: its development workspace only, any workspace, or a whole org.</p>
<p>This is <strong>not</strong> the note about an app that <em>cannot</em> be distributed. A Socket Mode app is barred from the Marketplace by its transport, and no checklist fixes that; the repair there is an architectural change and it has <a href="/slack/socket-mode-blocks-distribution/">its own note</a>. This note is the opposite case and the commoner one: the transport is already public HTTPS, nothing is blocking anything, and the gate was simply never walked through. The script checks the transport first and hands over rather than reporting a checklist that cannot be completed.</p>
<p>One prerequisite lives in your code rather than the manifest, and it is the one that breaks in production rather than at the install screen: a distributed app receives a <strong>different bot token per workspace</strong>, and an app that reads its token from <code>SLACK_BOT_TOKEN</code> has nowhere to put the second one.</p>""",
"problem": """<p>Nothing about single-workspace development feels provisional. You create the app, install it in your own workspace, get a bot token, put it in the environment, and build for months against a completely realistic Slack. Every API call is the real API. Every event is a real event. The only thing that is not real is the assumption underneath all of it, which is that there is exactly one workspace and exactly one token, and that assumption is invisible precisely because it has never been contradicted.</p>
<p>The gate is discovered at the worst moment. Distribution is not something the app fails at gradually &mdash; it fails at the first attempt by an outside party, which is normally a customer, normally after a commitment, and normally in front of somebody. And the error is unhelpfully generic: an install URL with no valid redirect configured produces a Slack error page rather than a message naming the missing prerequisite, so the first hour goes into checking the link for typos.</p>
<p>The deeper problem is the token, and it does not surface at the install screen at all. Public distribution means every workspace that installs the app gets its own bot token, its own bot user id, its own team id. Code that reads one token from an environment variable will serve the second customer with the first customer's credentials, which is not an error you want to find in production: the app will happily post into the wrong company's channels. This is why implementing an installation store belongs <em>before</em> activation and not after &mdash; the gate is the last safe moment to still be single-tenant.</p>
<p>Enterprise Grid adds a third shape underneath. An org admin who wants the app across every workspace in the enterprise needs org-wide installation enabled, which is a separate setting with a separate consent flow and an install record keyed by enterprise rather than by team. An app that activated public distribution and stopped there will install workspace by workspace, which works, and will confuse the first Grid customer who expected one click.</p>""",
"why": """<p><strong>The first thing to establish is whether a checklist is even the right answer.</strong> Socket Mode bars an app from the Marketplace outright, and running a readiness checklist on a Socket Mode app produces a tidy list of items to complete that will not help, because the transport has to change first. So <code>blocking_transport</code> runs first and stops the script. Two notes, one boundary: that one is about an app that <em>cannot</em> be distributed, this one is about an app that <em>was not</em>.</p>
<p><strong>The audience is a fact about the manifest, not an opinion.</strong> Empty <code>redirect_urls[]</code> means no public OAuth flow can complete, which means the app is installable in exactly one workspace regardless of what anybody intended. Present redirect URLs mean any workspace can install. <code>org_deploy_enabled</code> on top of that means an org admin can install once for the enterprise. Three audiences, read directly, before a customer discovers which one you have.</p>
<p><strong>This is a presence check on the redirect URLs and deliberately nothing more.</strong> Whether a particular URL matches the one your code sends is a different failure with a different error &mdash; <code>bad_redirect_uri</code> &mdash; and it belongs to whichever of your environments got the trailing slash wrong. Here the only question is whether the list is empty, because an empty list is the difference between &ldquo;the flow can start&rdquo; and &ldquo;the flow cannot start&rdquo;.</p>
<p><strong>The token storage check is the one that catches a bug rather than a setting.</strong> Everything else in this note is a click somebody has not made yet. The installation store is code that does not exist, and its absence is invisible until the second workspace installs and starts receiving the first workspace's bot. The script asks which environment variables hold tokens and whether a store is implemented, and calls the combination of public distribution with a single environment token exactly what it is.</p>
<p><strong>Nothing here installs anything.</strong> There is no read-only way to test an install flow, and the write that would test it is an install &mdash; a real app in a real workspace with real consent. Every item is read from the manifest and from your own description of your deployment, which is enough to answer the question before the customer's admin clicks the link rather than after.</p>
<p><strong>The checklist reports states rather than a pass or fail count.</strong> An item can pass, fail, be blocked by something upstream, or be genuinely optional for this app &mdash; org-wide install is not a defect in a product with no Grid customers. Flattening those into a percentage would produce a number that is either alarming or reassuring for the wrong reason.</p>""",
"steps": [
 {"h": "Check whether the transport bars distribution before anything else",
  "body": """<p><code>blocking_transport</code> reads <code>settings.socket_mode_enabled</code>. If Socket Mode is on, this note does not apply and the script says so: a Socket Mode app cannot be listed at all, and the repair is a rewrite of the delivery layer rather than a checklist. Everything below assumes a public HTTPS transport already exists.</p>"""},
 {"h": "Establish who can install this app today",
  "body": """<p><code>install_audience</code> combines <code>oauth_config.redirect_urls[]</code> with <code>settings.org_deploy_enabled</code> and returns <code>dev-workspace-only</code>, <code>any-workspace</code> or <code>org-wide</code>. The first of those is the finding, and it is a statement about the configuration rather than about anybody's intentions.</p>"""},
 {"h": "Check the redirect list is not empty, and stop there",
  "body": """<p><code>redirect_presence</code> counts the configured redirect URLs. Zero means the OAuth flow has nowhere to return to and cannot complete for anybody outside your own workspace. Which URL and whether it matches your code is a separate failure with its own error string, and this script deliberately does not go looking for it.</p>"""},
 {"h": "Ask where the second workspace's token would go",
  "body": """<p><code>token_storage_shape</code> takes the names of the environment variables that hold tokens and whether an installation store is implemented. A single environment token is correct for a single-workspace app and a live bug for a distributed one, and it is the only item on this list that is code rather than configuration.</p>"""},
 {"h": "Produce the checklist with real states",
  "body": """<p><code>gate_checklist</code> returns each prerequisite as <code>pass</code>, <code>fail</code>, <code>blocked</code> or <code>optional</code>. Org-wide installation is optional for a product with no Enterprise Grid customers and required the day the first one arrives, and saying <code>optional</code> is more honest than a red cross that everybody learns to ignore.</p>"""},
 {"h": "Activate in the right order",
  "body": """<p>The printed repair puts the installation store first, then the redirect URLs, then activation, because that order is the one where nothing is briefly true and dangerous. Activating distribution on an app that still reads one token from the environment is the arrangement where a second customer's install quietly points your app at the first customer's workspace.</p>"""},
],
"verify": """<p>Add the redirect URLs, ship the installation store, then activate. Run it again and the audience should read <code>any-workspace</code> with nothing left failing.</p>
<pre><code class="language-bash">python3 slack_distribution_readiness.py --app-id A05DEPB0T --token-envs SLACK_BOT_TOKEN
# transport  http             Socket Mode is off, so the transport does not bar
#                             distribution and the checklist below is the right question
# audience   dev-workspace-only  no redirect URL is configured, so a public OAuth flow
#                             cannot start; this app installs in its own workspace only
# redirects  none             0 redirect URL(s) configured
# storage    single-env-token 1 token in an environment variable, which is correct
#                             until the day the app is distributed
# identity   T04NORTHW (Northwind) - the one workspace this app has ever lived in
# gate       public transport                 pass      Socket Mode is off
# gate       redirect URL configured          fail      the OAuth flow cannot return
# gate       scopes requested                 pass      12 bot scope(s) declared
# gate       bot user declared                pass      releasebot
# gate       per-workspace token storage      fail      one token in the environment
# gate       org-wide installation            optional  no Grid customer yet
# verdict    never-activated  the app is finished and has never been let out
#   repair: implement an installationStore first, before activation, so the second
#           workspace has somewhere to put its own token
#   repair: add every environment's redirect URL, then complete Manage Distribution</code></pre>""",
"code_intro": "The order of the functions is the argument. <code>blocking_transport</code> runs first and can end the script, because a checklist for an app that is barred from distribution by its transport is a tidy list of things that will not help. <code>install_audience</code> is then three lines of manifest reading that answer the actual question. <code>token_storage_shape</code> is the odd one out and the important one: it is the only item that describes your code rather than your configuration, and the only one whose failure shows up after a customer has already installed.",
"py_file": "slack_distribution_readiness.py",
"py": '''"""Check whether this app could be installed anywhere but the workspace it was built in.

Read only. apps.manifest.export and auth.test are reads. Nothing here installs
anything, activates anything, or writes a manifest: there is no read-only way to
test an install flow, and the write that would test it is a real installation in
somebody's workspace.

Two neighbouring failures, one boundary. An app on Socket Mode cannot be listed
on the Marketplace at all, whatever its checklist says, and that is a different
note with an architectural repair. This script establishes the transport first
and stops if it is the socket, so what follows is only ever about an app that
could have been distributed and simply never was.
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_distribution_readiness")

API = "https://slack.com/api/"


def blocking_transport(manifest):
    """Does the delivery transport bar distribution outright? Pure.

    Returns (state, detail): socket-mode, http or unknown. Run first, because a
    readiness checklist for a Socket Mode app is a list of items that will not
    help - the Marketplace does not accept one, and the repair is a rewrite of
    the delivery layer rather than a click on a settings page.
    """
    if manifest is None:
        return ("unknown", "no manifest was read, so the transport is unknown; an app "
                           "configuration token is what reads it")
    if bool((manifest.get("settings") or {}).get("socket_mode_enabled")):
        return ("socket-mode", "Socket Mode is on, and a Socket Mode app cannot be "
                               "listed on the Marketplace at all. That is a different "
                               "note with a different repair")
    return ("http", "Socket Mode is off, so the transport does not bar distribution "
                    "and the checklist below is the right question")


def redirect_presence(manifest):
    """Can a public OAuth flow return at all? Pure.

    Returns (state, count, detail): none, one, several or unknown.

    A presence check and nothing more. Whether a particular URL matches the one
    your code sends is bad_redirect_uri, a different failure with its own error
    string; the only question here is whether the list is empty, because an
    empty list means the flow cannot complete for anybody outside your own
    workspace.
    """
    if manifest is None:
        return ("unknown", 0, "no manifest was read")
    oauth = manifest.get("oauth_config") or {}
    urls = [str(u).strip() for u in (oauth.get("redirect_urls") or []) if str(u).strip()]
    if not urls:
        return ("none", 0, "0 redirect URL(s) configured, so the authorisation code "
                           "has nowhere to be delivered")
    if len(urls) == 1:
        return ("one", 1, "1 redirect URL configured: %s" % urls[0])
    return ("several", len(urls), "%d redirect URL(s) configured" % len(urls))


def install_audience(manifest):
    """Who can install this app today? Pure.

    Returns (audience, detail): dev-workspace-only, any-workspace, org-wide or
    unknown. A statement about the configuration rather than about anybody's
    plans: with no redirect URL the app is installable in exactly one workspace
    whatever the roadmap says.
    """
    if manifest is None:
        return ("unknown", "no manifest was read, so the audience cannot be "
                           "established")
    settings = manifest.get("settings") or {}
    state, _count, _detail = redirect_presence(manifest)
    if state == "none":
        return ("dev-workspace-only",
                "no redirect URL is configured, so a public OAuth flow cannot start; "
                "this app installs in the workspace it was created in and nowhere else")
    if bool(settings.get("org_deploy_enabled")):
        return ("org-wide", "org-wide installation is enabled, so a Grid admin can "
                            "install once for every workspace in the enterprise")
    return ("any-workspace", "a public OAuth flow can complete, so any workspace can "
                             "install this app one at a time")


def token_storage_shape(token_env_names, has_store, audience):
    """Where would a second workspace's token go? Pure.

    Returns (state, detail): installation-store, single-env-token,
    env-token-but-public or unknown.

    The only item in this note that is code rather than configuration, and the
    only one whose failure appears after a customer has already installed. A
    distributed app receives a different bot token per workspace; an app that
    reads one token from the environment will serve the second customer with
    the first customer's credentials.
    """
    names = sorted(str(n) for n in (token_env_names or []) if str(n).strip())
    if has_store:
        return ("installation-store", "an installation store is implemented, so each "
                                      "workspace's token has somewhere to live")
    if not names:
        return ("unknown", "no token variables were named and no installation store "
                           "was declared, so the storage shape is unknown")
    if audience in ("any-workspace", "org-wide"):
        return ("env-token-but-public",
                "%d token(s) in environment variables while distribution is on: the "
                "next workspace to install has nowhere to put its own token"
                % len(names))
    return ("single-env-token", "%d token(s) in an environment variable, which is "
                                "correct until the day the app is distributed"
            % len(names))


def gate_checklist(manifest, storage_state):
    """The distribution prerequisites, as far as they are readable. Pure.

    Returns [(item, state, detail)] with state pass, fail, blocked or optional.

    Optional is a real answer rather than a softened failure: org-wide install
    is not a defect in a product with no Enterprise Grid customers, and a red
    cross that every team learns to ignore is worse than no check.
    """
    if manifest is None:
        return [("manifest readable", "blocked", "no manifest was read")]
    settings = manifest.get("settings") or {}
    features = manifest.get("features") or {}
    oauth = manifest.get("oauth_config") or {}
    scopes = oauth.get("scopes") or {}
    socket = bool(settings.get("socket_mode_enabled"))
    redirects, count, _detail = redirect_presence(manifest)
    bot_scopes = list(scopes.get("bot") or [])
    user_scopes = list(scopes.get("user") or [])
    bot_user = ((features.get("bot_user") or {}).get("display_name") or "").strip()

    out = [("public transport", "fail" if socket else "pass",
            "Socket Mode is on" if socket else "Socket Mode is off")]
    out.append(("redirect URL configured", "fail" if redirects == "none" else "pass",
                "the OAuth flow cannot return" if redirects == "none"
                else "%d configured" % count))
    if bot_scopes or user_scopes:
        out.append(("scopes requested", "pass", "%d bot and %d user scope(s) declared"
                    % (len(bot_scopes), len(user_scopes))))
    else:
        out.append(("scopes requested", "fail", "no scopes are declared, so the consent "
                                                "screen has nothing to ask for"))
    if bot_user:
        out.append(("bot user declared", "pass", bot_user))
    elif user_scopes:
        out.append(("bot user declared", "optional", "no bot user, and user scopes are "
                                                     "declared; a user-token app is a "
                                                     "valid shape"))
    else:
        out.append(("bot user declared", "fail", "neither a bot user nor user scopes"))
    if storage_state == "installation-store":
        out.append(("per-workspace token storage", "pass", "an installation store is "
                                                           "implemented"))
    elif storage_state == "unknown":
        out.append(("per-workspace token storage", "blocked", "not described to this "
                                                              "script"))
    else:
        out.append(("per-workspace token storage", "fail",
                    "one token in the environment, which cannot hold a second "
                    "workspace"))
    if bool(settings.get("org_deploy_enabled")):
        out.append(("org-wide installation", "pass", "a Grid admin can install once for "
                                                     "the whole enterprise"))
    else:
        out.append(("org-wide installation", "optional", "not enabled; needed the day "
                                                         "an Enterprise Grid customer "
                                                         "arrives"))
    return out


def distribution_verdict(transport, audience, storage, checklist):
    """One sentence from the transport, the audience and the checklist. Pure.

    Returns (state, detail): unproven, blocked-by-transport, never-activated,
    no-store, incomplete or distributable.
    """
    if transport == "unknown":
        return ("unproven", "the manifest could not be read, so nothing is claimed")
    if transport == "socket-mode":
        return ("blocked-by-transport", "this app cannot be distributed at all while "
                                        "it is on Socket Mode; the checklist below is "
                                        "not the problem to solve first")
    if audience == "dev-workspace-only":
        return ("never-activated", "the app is finished and has never been let out of "
                                   "the workspace it was created in")
    if storage == "env-token-but-public":
        return ("no-store", "distribution is on and there is one token in the "
                            "environment; the next workspace to install will be served "
                            "with another workspace's credentials")
    failed = [item for item, state, _detail in checklist or [] if state == "fail"]
    if failed:
        return ("incomplete", "%d prerequisite(s) still failing: %s"
                % (len(failed), ", ".join(failed)))
    return ("distributable", "every readable prerequisite is met for a %s install"
            % audience)


def load_manifest(args):
    """Read the live manifest. A read: export returns it and changes nothing."""
    if args.manifest:
        return json.loads(open(args.manifest, encoding="utf-8").read())
    token = os.environ.get(args.config_token_env)
    if not token or not args.app_id:
        log.warning("manifest   unavailable      set %s and --app-id, or pass "
                    "--manifest", args.config_token_env)
        return None
    body = requests.get(API + "apps.manifest.export",
                        headers={"Authorization": "Bearer " + token},
                        params={"app_id": args.app_id}, timeout=30).json()
    if body.get("ok") is not True:
        log.error("manifest   unavailable      %s", body.get("error"))
        return None
    return body.get("manifest") or {}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", default="", help="path to an exported manifest")
    ap.add_argument("--config-token-env", default="SLACK_CONFIG_TOKEN",
                    help="environment variable holding an app configuration token")
    ap.add_argument("--app-id", default="", help="app id, for the manifest read")
    ap.add_argument("--token-envs", default="SLACK_BOT_TOKEN",
                    help="comma separated names of variables that hold bot tokens")
    ap.add_argument("--installation-store", action="store_true",
                    help="the app implements a per-workspace installation store")
    args = ap.parse_args()

    manifest = load_manifest(args)
    transport, transport_detail = blocking_transport(manifest)
    (log.warning if transport == "socket-mode" else log.info)(
        "transport  %-16s %s", transport, transport_detail)
    if transport == "socket-mode":
        log.warning("verdict    blocked-by-transport  read the note on Socket Mode and "
                    "the Marketplace; no checklist item below will change this")
        return 1

    audience, audience_detail = install_audience(manifest)
    (log.warning if audience == "dev-workspace-only" else log.info)(
        "audience   %-16s %s", audience, audience_detail)
    redirects, count, redirect_detail = redirect_presence(manifest)
    (log.warning if redirects == "none" else log.info)(
        "redirects  %-16s %s", redirects, redirect_detail)

    # Names only. Whether each variable is set is read from the environment and
    # never printed, and no token value is read, logged or transmitted here.
    names = [n.strip() for n in args.token_envs.split(",") if n.strip()]
    present = [n for n in names if os.environ.get(n)]
    storage, storage_detail = token_storage_shape(present, args.installation_store,
                                                  audience)
    (log.warning if storage == "env-token-but-public" else log.info)(
        "storage    %-16s %s", storage, storage_detail)

    if present:
        reply = requests.get(API + "auth.test",
                             headers={"Authorization": "Bearer "
                                                       + os.environ[present[0]]},
                             timeout=30).json()
        if reply.get("ok") is True:
            log.info("identity   %-16s %s%s", reply.get("team_id"), reply.get("team"),
                     " (enterprise install)" if reply.get("is_enterprise_install")
                     else " - one workspace")
        else:
            log.warning("identity   unavailable      %s", reply.get("error"))

    checklist = gate_checklist(manifest, storage)
    for item, item_state, item_detail in checklist:
        (log.warning if item_state == "fail" else log.info)(
            "gate       %-32s %-9s %s", item, item_state, item_detail)

    state, why = distribution_verdict(transport, audience, storage, checklist)
    findings = ("never-activated", "no-store", "incomplete", "blocked-by-transport")
    (log.warning if state in findings else log.info)("verdict    %-16s %s", state, why)
    if state in ("never-activated", "no-store", "incomplete"):
        log.warning("  repair: implement an installation store first, before "
                    "activation, so each workspace's token has somewhere to live")
        log.warning("  repair: add every environment's OAuth redirect URL, then "
                    "complete the Manage Distribution checklist and activate")
        log.warning("  repair: enable org-wide installation as well if an Enterprise "
                    "Grid customer needs one install for the whole org")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-distribution-readiness.mjs",
"js": '''/**
 * Check whether this app could be installed anywhere but the workspace it was
 * built in.
 *
 * Read only. apps.manifest.export and auth.test are reads. Nothing here
 * installs anything, activates anything, or writes a manifest.
 *
 * Two neighbouring failures, one boundary. An app on Socket Mode cannot be
 * listed on the Marketplace at all, and that is a different note with an
 * architectural repair. This script establishes the transport first and stops
 * if it is the socket, so what follows is only ever about an app that could
 * have been distributed and simply never was.
 */

import { readFileSync } from 'node:fs';

const API = 'https://slack.com/api/';

/**
 * Does the delivery transport bar distribution outright? Pure.
 * Returns [state, detail]; socket-mode, http or unknown. Run first.
 */
export function blockingTransport(manifest) {
  if (manifest === null || manifest === undefined) {
    return ['unknown', 'no manifest was read, so the transport is unknown; an app '
      + 'configuration token is what reads it'];
  }
  if (Boolean((manifest.settings ?? {}).socket_mode_enabled)) {
    return ['socket-mode', 'Socket Mode is on, and a Socket Mode app cannot be listed '
      + 'on the Marketplace at all. That is a different note with a different repair'];
  }
  return ['http', 'Socket Mode is off, so the transport does not bar distribution and '
    + 'the checklist below is the right question'];
}

/**
 * Can a public OAuth flow return at all? Pure.
 * Returns [state, count, detail]; none, one, several or unknown.
 */
export function redirectPresence(manifest) {
  if (manifest === null || manifest === undefined) {
    return ['unknown', 0, 'no manifest was read'];
  }
  const oauth = manifest.oauth_config ?? {};
  const urls = (oauth.redirect_urls ?? []).map((u) => String(u).trim()).filter(Boolean);
  if (!urls.length) {
    return ['none', 0, '0 redirect URL(s) configured, so the authorisation code has '
      + 'nowhere to be delivered'];
  }
  if (urls.length === 1) return ['one', 1, `1 redirect URL configured: ${urls[0]}`];
  return ['several', urls.length, `${urls.length} redirect URL(s) configured`];
}

/**
 * Who can install this app today? Pure.
 * Returns [audience, detail]; dev-workspace-only, any-workspace, org-wide, unknown.
 */
export function installAudience(manifest) {
  if (manifest === null || manifest === undefined) {
    return ['unknown', 'no manifest was read, so the audience cannot be established'];
  }
  const settings = manifest.settings ?? {};
  const [state] = redirectPresence(manifest);
  if (state === 'none') {
    return ['dev-workspace-only', 'no redirect URL is configured, so a public OAuth '
      + 'flow cannot start; this app installs in the workspace it was created in and '
      + 'nowhere else'];
  }
  if (Boolean(settings.org_deploy_enabled)) {
    return ['org-wide', 'org-wide installation is enabled, so a Grid admin can install '
      + 'once for every workspace in the enterprise'];
  }
  return ['any-workspace', 'a public OAuth flow can complete, so any workspace can '
    + 'install this app one at a time'];
}

/**
 * Where would a second workspace's token go? Pure.
 * Returns [state, detail]; installation-store, single-env-token,
 * env-token-but-public or unknown.
 */
export function tokenStorageShape(tokenEnvNames, hasStore, audience) {
  const names = (tokenEnvNames ?? []).map(String).filter((n) => n.trim()).sort();
  if (hasStore) {
    return ['installation-store', 'an installation store is implemented, so each '
      + "workspace's token has somewhere to live"];
  }
  if (!names.length) {
    return ['unknown', 'no token variables were named and no installation store was '
      + 'declared, so the storage shape is unknown'];
  }
  if (audience === 'any-workspace' || audience === 'org-wide') {
    return ['env-token-but-public', `${names.length} token(s) in environment variables `
      + 'while distribution is on: the next workspace to install has nowhere to put its '
      + 'own token'];
  }
  return ['single-env-token', `${names.length} token(s) in an environment variable, `
    + 'which is correct until the day the app is distributed'];
}

/**
 * The distribution prerequisites, as far as they are readable. Pure.
 * Returns [[item, state, detail], ...] with pass, fail, blocked or optional.
 */
export function gateChecklist(manifest, storageState) {
  if (manifest === null || manifest === undefined) {
    return [['manifest readable', 'blocked', 'no manifest was read']];
  }
  const settings = manifest.settings ?? {};
  const features = manifest.features ?? {};
  const scopes = (manifest.oauth_config ?? {}).scopes ?? {};
  const socket = Boolean(settings.socket_mode_enabled);
  const [redirects, count] = redirectPresence(manifest);
  const botScopes = scopes.bot ?? [];
  const userScopes = scopes.user ?? [];
  const botUser = String((features.bot_user ?? {}).display_name ?? '').trim();

  const out = [['public transport', socket ? 'fail' : 'pass',
    socket ? 'Socket Mode is on' : 'Socket Mode is off']];
  out.push(['redirect URL configured', redirects === 'none' ? 'fail' : 'pass',
    redirects === 'none' ? 'the OAuth flow cannot return' : `${count} configured`]);
  if (botScopes.length || userScopes.length) {
    out.push(['scopes requested', 'pass',
      `${botScopes.length} bot and ${userScopes.length} user scope(s) declared`]);
  } else {
    out.push(['scopes requested', 'fail', 'no scopes are declared, so the consent '
      + 'screen has nothing to ask for']);
  }
  if (botUser) out.push(['bot user declared', 'pass', botUser]);
  else if (userScopes.length) {
    out.push(['bot user declared', 'optional', 'no bot user, and user scopes are '
      + 'declared; a user-token app is a valid shape']);
  } else {
    out.push(['bot user declared', 'fail', 'neither a bot user nor user scopes']);
  }
  if (storageState === 'installation-store') {
    out.push(['per-workspace token storage', 'pass', 'an installation store is '
      + 'implemented']);
  } else if (storageState === 'unknown') {
    out.push(['per-workspace token storage', 'blocked', 'not described to this script']);
  } else {
    out.push(['per-workspace token storage', 'fail', 'one token in the environment, '
      + 'which cannot hold a second workspace']);
  }
  if (Boolean(settings.org_deploy_enabled)) {
    out.push(['org-wide installation', 'pass', 'a Grid admin can install once for the '
      + 'whole enterprise']);
  } else {
    out.push(['org-wide installation', 'optional', 'not enabled; needed the day an '
      + 'Enterprise Grid customer arrives']);
  }
  return out;
}

/**
 * One sentence from the transport, the audience and the checklist. Pure.
 * Returns [state, detail].
 */
export function distributionVerdict(transport, audience, storage, checklist) {
  if (transport === 'unknown') {
    return ['unproven', 'the manifest could not be read, so nothing is claimed'];
  }
  if (transport === 'socket-mode') {
    return ['blocked-by-transport', 'this app cannot be distributed at all while it is '
      + 'on Socket Mode; the checklist below is not the problem to solve first'];
  }
  if (audience === 'dev-workspace-only') {
    return ['never-activated', 'the app is finished and has never been let out of the '
      + 'workspace it was created in'];
  }
  if (storage === 'env-token-but-public') {
    return ['no-store', 'distribution is on and there is one token in the environment; '
      + 'the next workspace to install will be served with another workspace credentials'];
  }
  const failed = (checklist ?? []).filter(([, state]) => state === 'fail')
    .map(([item]) => item);
  if (failed.length) {
    return ['incomplete', `${failed.length} prerequisite(s) still failing: `
      + failed.join(', ')];
  }
  return ['distributable',
    `every readable prerequisite is met for a ${audience} install`];
}

function arg(args, name, fallback = null) {
  const i = args.indexOf(name);
  return i === -1 ? fallback : args[i + 1];
}

async function loadManifest(args) {
  const path = arg(args, '--manifest', '');
  if (path) return JSON.parse(readFileSync(path, 'utf8'));
  const tokenEnv = arg(args, '--config-token-env', 'SLACK_CONFIG_TOKEN');
  const appId = arg(args, '--app-id', '');
  const token = process.env[tokenEnv];
  if (!token || !appId) {
    console.warn(`manifest   unavailable      set ${tokenEnv} and --app-id, or pass `
      + '--manifest');
    return null;
  }
  const params = new URLSearchParams({ app_id: appId });
  const body = await (await fetch(`${API}apps.manifest.export?${params}`,
    { headers: { Authorization: `Bearer ${token}` } })).json();
  if (body.ok !== true) {
    console.error(`manifest   unavailable      ${body.error}`);
    return null;
  }
  return body.manifest ?? {};
}

async function main() {
  const args = process.argv.slice(2);
  const manifest = await loadManifest(args);
  const [transport, transportDetail] = blockingTransport(manifest);
  const transportLine = `transport  ${transport.padEnd(16)} ${transportDetail}`;
  if (transport === 'socket-mode') console.warn(transportLine);
  else console.log(transportLine);
  if (transport === 'socket-mode') {
    console.warn('verdict    blocked-by-transport  read the note on Socket Mode and the '
      + 'Marketplace; no checklist item below will change this');
    process.exitCode = 1;
    return;
  }

  const [audience, audienceDetail] = installAudience(manifest);
  const audienceLine = `audience   ${audience.padEnd(16)} ${audienceDetail}`;
  if (audience === 'dev-workspace-only') console.warn(audienceLine);
  else console.log(audienceLine);
  const [redirects, , redirectDetail] = redirectPresence(manifest);
  const redirectLine = `redirects  ${redirects.padEnd(16)} ${redirectDetail}`;
  if (redirects === 'none') console.warn(redirectLine); else console.log(redirectLine);

  // Names only. Whether each variable is set is read from the environment and
  // never printed, and no token value is logged or transmitted here.
  const names = String(arg(args, '--token-envs', 'SLACK_BOT_TOKEN'))
    .split(',').map((n) => n.trim()).filter(Boolean);
  const present = names.filter((n) => process.env[n]);
  const hasStore = args.includes('--installation-store');
  const [storage, storageDetail] = tokenStorageShape(present, hasStore, audience);
  const storageLine = `storage    ${storage.padEnd(16)} ${storageDetail}`;
  if (storage === 'env-token-but-public') console.warn(storageLine);
  else console.log(storageLine);

  if (present.length) {
    const reply = await (await fetch(`${API}auth.test`,
      { headers: { Authorization: `Bearer ${process.env[present[0]]}` } })).json();
    if (reply.ok === true) {
      console.log(`identity   ${String(reply.team_id).padEnd(16)} ${reply.team}`
        + `${reply.is_enterprise_install ? ' (enterprise install)' : ' - one workspace'}`);
    } else {
      console.warn(`identity   unavailable      ${reply.error}`);
    }
  }

  const checklist = gateChecklist(manifest, storage);
  for (const [item, itemState, itemDetail] of checklist) {
    const row = `gate       ${item.padEnd(32)} ${itemState.padEnd(9)} ${itemDetail}`;
    if (itemState === 'fail') console.warn(row); else console.log(row);
  }

  const [state, why] = distributionVerdict(transport, audience, storage, checklist);
  const findings = ['never-activated', 'no-store', 'incomplete', 'blocked-by-transport'];
  const verdictLine = `verdict    ${state.padEnd(16)} ${why}`;
  if (findings.includes(state)) console.warn(verdictLine); else console.log(verdictLine);
  if (state === 'never-activated' || state === 'no-store' || state === 'incomplete') {
    console.warn('  repair: implement an installation store first, before activation, '
      + "so each workspace's token has somewhere to live");
    console.warn('  repair: add every environment OAuth redirect URL, then complete the '
      + 'Manage Distribution checklist and activate');
    console.warn('  repair: enable org-wide installation as well if an Enterprise Grid '
      + 'customer needs one install for the whole org');
    process.exitCode = 1;
  }
}

// Only run when invoked directly, so importing this module in the tests does
// not execute main().
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The first test is the boundary between this note and its neighbour: a Socket Mode app must come back <code>blocked-by-transport</code> and never reach the checklist, because a tidy list of prerequisites for an app that cannot be listed at all is a list of things that will not help. The rest pin the three audiences, the difference between a single environment token that is fine and the same token that is a live bug, and the fact that <code>optional</code> survives as its own state rather than being flattened into a failure.",
"test_py_file": "test_slack_distribution_readiness.py",
"test_py": '''from slack_distribution_readiness import (
    blocking_transport, distribution_verdict, gate_checklist, install_audience,
    redirect_presence, token_storage_shape,
)


def app(socket=False, redirects=(), org=False, bot_scopes=("chat:write",),
        user_scopes=(), bot_user="releasebot"):
    return {
        "oauth_config": {
            "redirect_urls": list(redirects),
            "scopes": {"bot": list(bot_scopes), "user": list(user_scopes)},
        },
        "settings": {"socket_mode_enabled": socket, "org_deploy_enabled": org},
        "features": {"bot_user": {"display_name": bot_user}} if bot_user else {},
    }


def test_socket_mode_is_the_other_note_and_this_script_says_so():
    state, detail = blocking_transport(app(socket=True))
    assert state == "socket-mode"
    assert "different note" in detail


def test_an_http_app_is_the_one_this_checklist_is_for():
    assert blocking_transport(app())[0] == "http"


def test_no_manifest_is_unknown_rather_than_either():
    assert blocking_transport(None)[0] == "unknown"


def test_an_empty_redirect_list_means_the_flow_cannot_return():
    state, count, detail = redirect_presence(app())
    assert (state, count) == ("none", 0)
    assert "nowhere to be delivered" in detail


def test_blank_redirect_entries_do_not_count_as_urls():
    assert redirect_presence(app(redirects=("", "   ")))[0] == "none"


def test_one_and_several_redirect_urls_are_distinguished():
    assert redirect_presence(app(redirects=("https://a.example.com/cb",)))[0] == "one"
    assert redirect_presence(app(redirects=("https://a.example.com/cb",
                                            "https://b.example.com/cb")))[1] == 2


def test_no_redirect_url_pins_the_audience_to_one_workspace():
    audience, detail = install_audience(app())
    assert audience == "dev-workspace-only"
    assert "nowhere else" in detail


def test_a_redirect_url_opens_the_app_to_any_workspace():
    assert install_audience(app(redirects=("https://a.example.com/cb",)))[0] == \\
        "any-workspace"


def test_org_deploy_is_the_third_audience_rather_than_a_flavour_of_the_second():
    assert install_audience(app(redirects=("https://a.example.com/cb",),
                                org=True))[0] == "org-wide"


def test_one_env_token_is_correct_for_one_workspace():
    state, detail = token_storage_shape(["SLACK_BOT_TOKEN"], False, "dev-workspace-only")
    assert state == "single-env-token"
    assert "until the day" in detail


def test_the_same_env_token_is_a_bug_once_the_app_is_public():
    state, detail = token_storage_shape(["SLACK_BOT_TOKEN"], False, "any-workspace")
    assert state == "env-token-but-public"
    assert "nowhere to put its own token" in detail


def test_an_installation_store_passes_whatever_the_audience():
    for audience in ("dev-workspace-only", "any-workspace", "org-wide"):
        assert token_storage_shape(["SLACK_BOT_TOKEN"], True, audience)[0] == \\
            "installation-store"


def test_nothing_described_is_unknown_rather_than_a_failure():
    assert token_storage_shape([], False, "any-workspace")[0] == "unknown"


def test_the_checklist_fails_the_redirect_item_and_the_storage_item():
    rows = dict((r[0], r[1]) for r in gate_checklist(app(), "single-env-token"))
    assert rows["redirect URL configured"] == "fail"
    assert rows["per-workspace token storage"] == "fail"
    assert rows["public transport"] == "pass"


def test_org_wide_install_stays_optional_rather_than_becoming_a_failure():
    rows = dict((r[0], r[1]) for r in gate_checklist(app(), "installation-store"))
    assert rows["org-wide installation"] == "optional"
    rows = dict((r[0], r[1]) for r in gate_checklist(app(org=True),
                                                     "installation-store"))
    assert rows["org-wide installation"] == "pass"


def test_a_user_token_app_with_no_bot_user_is_a_valid_shape():
    rows = dict((r[0], r[1]) for r in gate_checklist(
        app(bot_user="", bot_scopes=(), user_scopes=("search:read",)),
        "installation-store"))
    assert rows["bot user declared"] == "optional"
    assert rows["scopes requested"] == "pass"


def test_an_app_that_declares_no_scopes_at_all_fails():
    rows = dict((r[0], r[1]) for r in gate_checklist(
        app(bot_scopes=(), user_scopes=()), "installation-store"))
    assert rows["scopes requested"] == "fail"


def test_an_unreadable_manifest_blocks_the_checklist_rather_than_failing_it():
    assert gate_checklist(None, "unknown") == [
        ("manifest readable", "blocked", "no manifest was read")]


def test_the_verdict_hands_a_socket_app_straight_over():
    state, detail = distribution_verdict("socket-mode", "dev-workspace-only",
                                         "single-env-token", [])
    assert state == "blocked-by-transport"
    assert "not the problem to solve first" in detail


def test_the_finished_app_that_was_never_let_out_is_this_note():
    checklist = gate_checklist(app(), "single-env-token")
    state, _detail = distribution_verdict("http", "dev-workspace-only",
                                          "single-env-token", checklist)
    assert state == "never-activated"


def test_distribution_on_with_one_env_token_is_named_before_the_checklist():
    state, detail = distribution_verdict("http", "any-workspace",
                                         "env-token-but-public", [])
    assert state == "no-store"
    assert "another workspace" in detail


def test_everything_met_reads_as_distributable():
    manifest = app(redirects=("https://a.example.com/cb",))
    checklist = gate_checklist(manifest, "installation-store")
    assert distribution_verdict("http", "any-workspace", "installation-store",
                                checklist)[0] == "distributable"
''',
"test_js_file": "slack-distribution-readiness.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  blockingTransport, distributionVerdict, gateChecklist, installAudience,
  redirectPresence, tokenStorageShape,
} from './slack-distribution-readiness.mjs';

function app({
  socket = false, redirects = [], org = false, botScopes = ['chat:write'],
  userScopes = [], botUser = 'releasebot',
} = {}) {
  return {
    oauth_config: {
      redirect_urls: [...redirects],
      scopes: { bot: [...botScopes], user: [...userScopes] },
    },
    settings: { socket_mode_enabled: socket, org_deploy_enabled: org },
    features: botUser ? { bot_user: { display_name: botUser } } : {},
  };
}

function rows(checklist) {
  return Object.fromEntries(checklist.map((r) => [r[0], r[1]]));
}

test('socket mode is the other note and this script says so', () => {
  const [state, detail] = blockingTransport(app({ socket: true }));
  assert.equal(state, 'socket-mode');
  assert.match(detail, /different note/);
});

test('an http app is the one this checklist is for', () => {
  assert.equal(blockingTransport(app())[0], 'http');
});

test('no manifest is unknown rather than either', () => {
  assert.equal(blockingTransport(null)[0], 'unknown');
});

test('an empty redirect list means the flow cannot return', () => {
  const [state, count, detail] = redirectPresence(app());
  assert.equal(state, 'none');
  assert.equal(count, 0);
  assert.match(detail, /nowhere to be delivered/);
});

test('blank redirect entries do not count as urls', () => {
  assert.equal(redirectPresence(app({ redirects: ['', '   '] }))[0], 'none');
});

test('one and several redirect urls are distinguished', () => {
  assert.equal(redirectPresence(app({ redirects: ['https://a.example.com/cb'] }))[0],
    'one');
  assert.equal(redirectPresence(app({
    redirects: ['https://a.example.com/cb', 'https://b.example.com/cb'],
  }))[1], 2);
});

test('no redirect url pins the audience to one workspace', () => {
  const [audience, detail] = installAudience(app());
  assert.equal(audience, 'dev-workspace-only');
  assert.match(detail, /nowhere else/);
});

test('a redirect url opens the app to any workspace', () => {
  assert.equal(installAudience(app({ redirects: ['https://a.example.com/cb'] }))[0],
    'any-workspace');
});

test('org deploy is the third audience rather than a flavour of the second', () => {
  assert.equal(installAudience(app({
    redirects: ['https://a.example.com/cb'], org: true,
  }))[0], 'org-wide');
});

test('one env token is correct for one workspace', () => {
  const [state, detail] = tokenStorageShape(['SLACK_BOT_TOKEN'], false,
    'dev-workspace-only');
  assert.equal(state, 'single-env-token');
  assert.match(detail, /until the day/);
});

test('the same env token is a bug once the app is public', () => {
  const [state, detail] = tokenStorageShape(['SLACK_BOT_TOKEN'], false, 'any-workspace');
  assert.equal(state, 'env-token-but-public');
  assert.match(detail, /nowhere to put its own token/);
});

test('an installation store passes whatever the audience', () => {
  for (const audience of ['dev-workspace-only', 'any-workspace', 'org-wide']) {
    assert.equal(tokenStorageShape(['SLACK_BOT_TOKEN'], true, audience)[0],
      'installation-store');
  }
});

test('nothing described is unknown rather than a failure', () => {
  assert.equal(tokenStorageShape([], false, 'any-workspace')[0], 'unknown');
});

test('the checklist fails the redirect item and the storage item', () => {
  const r = rows(gateChecklist(app(), 'single-env-token'));
  assert.equal(r['redirect URL configured'], 'fail');
  assert.equal(r['per-workspace token storage'], 'fail');
  assert.equal(r['public transport'], 'pass');
});

test('org wide install stays optional rather than becoming a failure', () => {
  assert.equal(rows(gateChecklist(app(), 'installation-store'))['org-wide installation'],
    'optional');
  assert.equal(
    rows(gateChecklist(app({ org: true }), 'installation-store'))['org-wide installation'],
    'pass');
});

test('a user token app with no bot user is a valid shape', () => {
  const r = rows(gateChecklist(
    app({ botUser: '', botScopes: [], userScopes: ['search:read'] }),
    'installation-store'));
  assert.equal(r['bot user declared'], 'optional');
  assert.equal(r['scopes requested'], 'pass');
});

test('an app that declares no scopes at all fails', () => {
  const r = rows(gateChecklist(app({ botScopes: [], userScopes: [] }),
    'installation-store'));
  assert.equal(r['scopes requested'], 'fail');
});

test('an unreadable manifest blocks the checklist rather than failing it', () => {
  assert.deepEqual(gateChecklist(null, 'unknown'),
    [['manifest readable', 'blocked', 'no manifest was read']]);
});

test('the verdict hands a socket app straight over', () => {
  const [state, detail] = distributionVerdict('socket-mode', 'dev-workspace-only',
    'single-env-token', []);
  assert.equal(state, 'blocked-by-transport');
  assert.match(detail, /not the problem to solve first/);
});

test('the finished app that was never let out is this note', () => {
  const checklist = gateChecklist(app(), 'single-env-token');
  assert.equal(distributionVerdict('http', 'dev-workspace-only', 'single-env-token',
    checklist)[0], 'never-activated');
});

test('distribution on with one env token is named before the checklist', () => {
  const [state, detail] = distributionVerdict('http', 'any-workspace',
    'env-token-but-public', []);
  assert.equal(state, 'no-store');
  assert.match(detail, /another workspace/);
});

test('everything met reads as distributable', () => {
  const manifest = app({ redirects: ['https://a.example.com/cb'] });
  const checklist = gateChecklist(manifest, 'installation-store');
  assert.equal(distributionVerdict('http', 'any-workspace', 'installation-store',
    checklist)[0], 'distributable');
});
''',
"faq": [
 ("How is this different from the note about Socket Mode blocking distribution?",
  "That note is about an app that cannot be distributed: Socket Mode is not accepted on the Marketplace, and no amount of configuration changes that, so the repair is moving the delivery layer to a public HTTPS endpoint. This note is about an app that could be distributed and never was. Its transport is already public, nothing is blocking it, and the missing pieces are a redirect URL, an installation store and a click on Activate Public Distribution. The script checks the transport first and refuses to print a checklist for an app the checklist cannot help."),
 ("Do I actually need to activate distribution to install in a second workspace?",
  "Yes, for anyone outside your own workspace. Until activation the app is installable only where it was created, and the install link for anyone else produces an error page rather than a consent screen. There is one adjacent case worth knowing: on Enterprise Grid, an app installed in one workspace of an org is still not installed in the others, and installing once for the whole org is a further setting on top of public distribution rather than a consequence of it."),
 ("Why implement the installation store before activating rather than after?",
  "Because the window between the two is where the worst version of this bug lives. Once distribution is on, any workspace can install, and every installation mints its own bot token. An app still reading one token from the environment will keep using whichever token is in that variable, so the second customer's events are handled with the first customer's credentials and the app posts into the wrong company's channels. Nothing errors. Doing the store first means there is never a moment when a successful install produces a wrong-tenant app."),
 ("The manifest looks right and installs still fail with bad_redirect_uri. Same thing?",
  "No, and this script deliberately does not try to diagnose it. bad_redirect_uri means a redirect URL is configured and the one your code sent does not match it, usually over a trailing slash, a scheme, or a staging hostname that was never added. That is a comparison between your code and your configuration. This note only asks whether the list is empty, because an empty list is a different and more fundamental state: not a mismatch, but no possible match at all."),
 ("We only ever want this app in our own workspace. Is any of this a problem?",
  "No, and the script is written so it does not nag you about it. A single-workspace app with no redirect URLs and one bot token in an environment variable is a correct and supported shape, which is why token_storage_shape calls that combination single-env-token and not a failure. The check becomes useful the moment somebody says the word customer, and the useful thing about running it before that conversation is that the answer takes ten seconds instead of a fortnight."),
],
"related": [
 ("/slack/socket-mode-blocks-distribution/", "the app that cannot be distributed rather than the app that was not"),
 ("/slack/enterprise-id-not-stored/", "the installation store, and the key that makes Grid installs collide"),
 ("/slack/non-marketplace-history-clamp/", "the rate limit a listing would lift once you are out there"),
],
"citations": [CITE_OAUTH_INSTALL, CITE_MANIFESTS, CITE_SO_DISTRIBUTION,
              CITE_MANIFEST_EXPORT],
})
