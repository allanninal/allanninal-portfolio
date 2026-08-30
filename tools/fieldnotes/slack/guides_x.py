#!/usr/bin/env python3
"""/slack/ field notes, batch X - the writing.

Three notes about incoming webhooks and one about a surface Slack switched
off. The webhook three are deliberately separated by what is actually broken,
because "the webhook does not work" is four different faults wearing one
sentence.

The first is about the URL outliving the thing that issued it. A webhook URL
is a bearer credential with no expiry printed on it, minted by one install for
one channel, and it dies when that install dies - including when the human who
clicked Allow is deactivated, which leaves the bot token working and the
webhook dead. The reading is an inventory joined to install records and to the
bound channel's history.

The second is about a field that used to work. An app based webhook is bound
to one channel at creation, and the channel override that every blog post from
2015 demonstrates is inert. A routing table collapses into a single room with
no error anywhere. The reading is the destinations the code asks for held
against the one it is bound to, corroborated by several teams' traffic
arriving in one channel.

The third is about bytes, and it stops before Block Kit begins. A body built
by string interpolation stops being JSON the moment the interpolated text
contains a quote or a newline, and the webhook answers a real 400 that a shell
script does not check. The reading is one captured body, decoded, parsed and
sorted, locally, with no network call of any kind.

The fourth is a date. Slack retired Steps from Apps on 26 September 2024: the
workflows stopped, the steps stopped, the events stopped being subscribable,
and none of that produced an error anywhere. The reading is a live manifest
still declaring a feature that no longer runs.

Read only throughout, and one refusal is absolute. An incoming webhook URL
exists to have a message sent to it. There is no status endpoint, no probe, no
"is this alive" call - the only way to ask Slack whether a webhook works is to
deliver a message through it, into a real channel, in front of people who then
have to be told what the message was. Nothing in this batch sends anything to
a webhook URL, and nothing in this batch ever prints one in full.
"""

CITE_WEBHOOKS = ("Sending messages using incoming webhooks - Slack Docs",
                 "https://docs.slack.dev/messaging/"
                 "sending-messages-using-incoming-webhooks")
CITE_AUTH_TEST = ("auth.test method reference - Slack Docs",
                  "https://docs.slack.dev/reference/methods/auth.test")
CITE_USERS_INFO = ("users.info method reference - Slack Docs",
                   "https://docs.slack.dev/reference/methods/users.info")
CITE_HISTORY = ("conversations.history method reference - Slack Docs",
                "https://docs.slack.dev/reference/methods/conversations.history")
CITE_POST_MESSAGE = ("chat.postMessage method reference - Slack Docs",
                     "https://docs.slack.dev/reference/methods/chat.postMessage")
CITE_MANIFEST_EXPORT = ("apps.manifest.export method reference - Slack Docs",
                        "https://docs.slack.dev/reference/methods/apps.manifest.export")
CITE_BLOCK_KIT = ("Block Kit reference - Slack Docs",
                  "https://docs.slack.dev/reference/block-kit")
CITE_SO_NO_SERVICE = ("Stack Overflow: Slack incoming webhook returns no_service",
                      "https://stackoverflow.com/questions/77158147")
CITE_SO_WEBHOOK_CHANNEL = ("Stack Overflow: the Slack webhook ignores the channel "
                           "in the payload",
                           "https://stackoverflow.com/questions/51467215")
CITE_SO_INVALID_PAYLOAD = ("Stack Overflow: Slack webhook answers invalid_payload",
                           "https://stackoverflow.com/questions/39925395")
CITE_SO_CURL_JSON = ("Stack Overflow: sending JSON to a Slack webhook from curl",
                     "https://stackoverflow.com/questions/31905260")
CITE_STEPS_RETIRED = ("Steps from Apps is being retired - Slack changelog",
                      "https://docs.slack.dev/changelog/2024/05/02/apps/")
CITE_STEPS_FAQ = ("Legacy Steps from Apps survival guide - Slack Docs",
                  "https://docs.slack.dev/legacy/legacy-steps-from-apps/"
                  "legacy-steps-from-apps-survival-guide-faq/")
CITE_BOLT_1025 = ("bolt-python #1025: legacy workflow steps after the retirement",
                  "https://github.com/slackapi/bolt-python/issues/1025")

GUIDES = []

GUIDES.append({
"slug": "incoming-webhook-dead",
"title": "no_service: the incoming webhook died with its install",
"description": "A webhook URL keeps its shape forever and stops working in silence. Join your inventory to your install records and read the bound channel, sending nothing.",
"h1": "no_service: the incoming webhook died with its install",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack incoming webhook no_service",
             "slack webhook no_active_hooks 404",
             "slack webhook stopped working after uninstall",
             "slack webhook dies when installer leaves",
             "slack incoming webhook inventory"],
"deps": "Python 3.9+ with requests, or Node.js 18+; a bot token with users:read and channels:history, and a JSON inventory of the webhook URLs your systems hold",
"lead": "The deploy notifications stopped. Nobody noticed for five weeks, because the absence of a message is not a message, and a channel that has gone quiet looks exactly like a channel where nothing has gone wrong. When somebody finally checks, the build server is still calling the same URL it has called for two years, the URL still looks perfectly well formed, and Slack has been answering <code>404</code> with the four words <code>no_service</code> into a <code>curl</code> whose exit status nothing has ever read.</p><p>The webhook did not expire. Somebody left the company, or somebody reinstalled the app, and the URL died at that moment. There is nothing in the URL that records this, and there is nothing in your build server that could have found out.",
"short_answer": """<p>An incoming webhook URL is bound to one app installation, one authorising user and one channel. Uninstall the app, revoke the authorisation, delete the webhook in app configuration, or deactivate the user who clicked <strong>Allow</strong>, and the URL is dead permanently. It answers <code>404</code> with the plain text body <code>no_service</code> or <code>no_active_hooks</code>, or <code>401 invalid_token</code>, and it will answer that forever. Reinstalling the app does not resurrect it: a reinstall mints a <em>new</em> URL.</p>
<p>The detail that catches people is the fourth cause. A webhook dies with the human who authorised it, and a bot token does not. So an app can be perfectly healthy &mdash; <code>auth.test</code> answers <code>ok: true</code>, <code>chat.postMessage</code> works, the bot is in every channel it should be &mdash; while three webhook URLs pasted into three unrelated systems have all been dead since an offboarding nobody connected to Slack.</p>
<p><strong>Do not send anything to the URL to find out.</strong> A webhook URL has exactly one verb and no read side: no status endpoint, no probe, no metadata call. Anything you send is a delivery, and a delivery lands in a real channel in front of real people, who then have to be told what it was. The script below establishes all of this without sending: from the shape of the stored URL, from your install records, from <code>users.info</code> on the authorising user, and from the bound channel's own history showing what the webhook has and has not delivered.</p>""",
"problem": """<p>The reason this note is about an inventory rather than about a URL is that almost nobody has an inventory. A webhook URL is created by clicking through an install, copied out of a browser once, and pasted into whatever needed it: a build server, a monitoring rule, a cron job on a box that predates the current team, a Zapier step, a colleague's shell alias. It is a bearer credential with no name, no owner, no expiry and no listing endpoint, and the moment it leaves the browser Slack has no idea where it went and neither do you.</p>
<p>That is survivable while the URLs work. It stops being survivable at the moment one dies, because the failure has no reader. A webhook that fails answers with a real HTTP status &mdash; genuinely unusual on Slack, where almost everything is <code>200</code> with <code>ok: false</code> in the body &mdash; and the status arrives in the one class of client least likely to check it. <code>curl</code> exits <code>0</code> on a <code>404</code> unless you passed <code>--fail</code>. A shell step in CI goes green. A monitoring rule that alerts through the dead webhook cannot alert you that the webhook is dead.</p>
<p>The four ways to kill one are worth separating, because they have different blast radii and different repairs. Uninstalling the app kills every webhook the app ever issued in that workspace, all at once, which at least fails loudly enough to be noticed. Revoking one authorisation kills the webhooks minted under it. Deleting the webhook from app configuration kills that one URL. And deactivating the authorising user kills the webhooks they authorised, quietly, on a date chosen by HR, while every other part of the app carries on working perfectly.</p>
<p>Then there is the slow version, which is worse. Nothing has died at all: the app is installed, the user is active, the URL is fine, and the system that used to send through it was decommissioned eighteen months ago. The URL is still valid, still a credential, still in a config file in a repository somewhere, and still capable of posting into your workspace as your app if it ever leaks. A dead webhook is an outage. A live orphaned webhook is a standing grant to whoever finds it.</p>""",
"why": """<p><strong>Nothing here sends anything to a webhook URL, and that is not squeamishness.</strong> A webhook has no read side. Every request to it that Slack accepts is a message posted into somebody's channel: an empty payload is refused, a test payload is delivered, and either way somebody now has to explain it. This is the one surface in this section where a diagnostic that "just tries it" is not a write against a database, it is a write in front of an audience. So the script reads the URL's shape, the install records, the authorising user and the bound channel, and reaches the same verdict without an audience.</p>
<p><strong>The shape of the URL is worth reading before anything else, because half of the bad rows are not webhooks.</strong> A stored value that is not <code>hooks.slack.com/services/T&hellip;/B&hellip;/&hellip;</code> is something else: a workflow trigger URL, a Web API URL somebody filed in the wrong column, a truncated paste, a URL that picked up a trailing quote from a YAML file. Those fail identically to a dead webhook and are fixed completely differently, so they are sorted out first.</p>
<p><strong>The team ID is in the URL, and it is a free join key.</strong> The first path segment of a webhook URL is the workspace it was issued for. Holding that against the workspaces you actually hold installs for finds the rows that belong to a workspace you no longer serve &mdash; a customer that churned, a test workspace, a Grid workspace that was split off &mdash; without any call at all.</p>
<p><strong>The authorising user is the join everyone forgets.</strong> <code>users.info</code> on the person who clicked Allow costs one read and answers the question that no amount of staring at the app's health will answer, because the app <em>is</em> healthy. This is also why the verdict for that case says so explicitly rather than just saying <code>dead</code>: the repair is a reinstall by somebody who is not leaving, and ideally a move to a bot token, which has no human attached to it.</p>
<p><strong>The bound channel's history is the only positive evidence available.</strong> Everything else in this check is an absence. <code>conversations.history</code> on the channel the webhook posts into says when an app last delivered anything there, which turns "we think this still works" into a date. A channel where no app has ever posted is a webhook that has delivered nothing in the sample read, which for a deploy notifier is the whole finding.</p>
<p><strong>The inventory gaps are reported as findings in their own right.</strong> A row with no recorded owner cannot be rotated, because a rotation has nowhere to land. A row with no recorded authorising user cannot be watched for the one event that kills it. The same URL under two owners means a single rotation breaks a system nobody remembered. None of these are outages today and all of them are the reason the next one takes five weeks to find.</p>""",
"steps": [
 {"h": "Write down where the URLs are, once",
  "body": """<p>The inventory is a JSON list, one row per place a webhook URL is pasted: the URL, the system using it, the authorising user, the bound channel and the state of the install. If you do not have one, building it is the work &mdash; the script cannot discover a URL sitting in a Jenkins credential store. Everything after this step is mechanical.</p>"""},
 {"h": "Sort the rows that are not webhooks out first",
  "body": """<p><code>parse_webhook_url</code> reads the shape and answers <code>services</code>, <code>workflow-trigger</code>, <code>not-a-webhook</code> or <code>unusable</code>. A trailing quote picked up from YAML, a Web API URL in the wrong column and a workflow trigger URL all fail like a dead webhook and are none of them fixed like one.</p>"""},
 {"h": "Check the workspace in the URL against the workspaces you serve",
  "body": """<p>The first path segment is the team the webhook was issued for. A row whose team is not one you hold an install for is an orphan from a workspace you no longer serve, and it is reported before any network call is made, because the URL already said so.</p>"""},
 {"h": "Read the authorising user, not the app",
  "body": """<p>One <code>users.info</code> per distinct authoriser. <code>deleted: true</code> is the finding that nothing else in your monitoring will produce, because the bot token is fine, the app is installed, and the webhook has been dead since the leaving date.</p>"""},
 {"h": "Date the last delivery from the channel, not from your logs",
  "body": """<p><code>conversations.history</code> on the bound channel, then <code>last_webhook_delivery</code> for the most recent message an app posted. Your own logs record what you sent; the channel records what arrived. When those disagree, the channel is right.</p>"""},
 {"h": "Move the ones that matter off webhooks entirely",
  "body": """<p>The repair the script prints for <code>dead-installer</code> is not "reinstall". A bot token and <code>chat.postMessage</code> survive the installing user leaving, post to any channel the bot is in rather than one fixed room, and answer with a structured error you can read. Webhooks are the right tool for exactly one thing: a message into one known channel from a system that cannot hold a token.</p>"""},
],
"verify": """<p>Fix the rows, run it again, and read the last column. Every row should say <code>live</code>, and the gaps section should be empty.</p>
<pre><code class="language-bash">python3 slack_webhook_inventory.py --inventory webhooks.json --stale-days 14
# anchor     T04AB12CD      auth.test names the workspace this token lives in
# webhook    live           ci/deploy-notify -> hooks.slack.com/services/T04AB/B071P/********
#                           an app delivered into the bound channel 1 day(s) ago
# webhook    dead-installer alerts/pagerduty -> hooks.slack.com/services/T04AB/B05KQ/********
#                           the authorising user is deactivated; a webhook dies with its
#                           authoriser even though the bot token keeps working
# webhook    never-delivered ops/nightly-backup -> hooks.slack.com/services/T04AB/B02WE/********
#                           nothing in the bound channel came from an app in the sample read
# webhook    unusable-url   legacy/status-page -> &lt;not-a-webhook at api.slack.com&gt;
# gap        no-owner       one row records no system, so a rotation has nowhere to land
# verdict    3 finding(s)
#   repair: reinstall to mint a new URL, and move the alerting paths to a bot token
#   note:   nothing was sent to any webhook URL to establish this</code></pre>""",
"code_intro": "Three reads and no sends. <code>parse_webhook_url</code> and <code>redact_webhook_url</code> are pure and never let a secret reach the output; <code>webhook_verdict</code> is a pure decision over one inventory row and the facts the reads established, in a fixed precedence so that a revoked install is never reported as merely silent; <code>last_webhook_delivery</code> turns a page of channel history into a number of days; <code>inventory_gaps</code> and <code>duplicate_owners</code> report the bookkeeping that makes the next outage slow to find. There is no code path in this file that sends anything to <code>hooks.slack.com</code>.",
"py_file": "slack_webhook_inventory.py",
"py": '''"""Hold an inventory of incoming webhook URLs against the installs behind them.

Read only, and one thing is refused outright. An incoming webhook URL exists
for exactly one purpose: to have a message sent to it. There is no status
endpoint, no HEAD, no "is this alive" call. The only way to ask Slack directly
whether a webhook still works is to deliver a message through it, into a real
channel, in front of real people, who then have to be told what the message
was. So nothing in this file sends anything to hooks.slack.com.

Everything is established instead from the shape of the stored URL, from your
own install records, from users.info on the authorising user, and from the
bound channel's history showing what the webhook has and has not delivered.

Three reads: auth.test once, users.info once per distinct authorising user,
conversations.history once per distinct bound channel. No webhook URL is ever
printed in full - a webhook URL is a bearer credential, and anyone holding one
can post into your workspace as your app.
"""
import argparse
import json
import logging
import os
import sys
import time
from urllib.parse import urlsplit

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_webhook_inventory")

API = "https://slack.com/api/"
HOOK_HOST = "hooks.slack.com"

# Install states an inventory row can carry that already mean the webhook is
# gone. Slack does not revoke a webhook on its own: it dies with the
# installation, with the authorisation, or with the human who granted it.
DEAD_INSTALL_STATES = ("revoked", "uninstalled", "token_revoked", "deleted")


def parse_webhook_url(url):
    """Read a webhook URL's shape without contacting anything. Pure.

    Returns (kind, parts, notes). Kinds:

      services          hooks.slack.com/services/T.../B.../secret, the real thing.
      workflow-trigger  a Workflow Builder trigger URL, which is a different
                        surface with a different lifecycle and different repairs.
      not-a-webhook     a URL, but not one Slack delivers webhooks through.
      unusable          not a URL at all, which is what a trailing quote picked
                        up from a YAML file leaves behind.

    parts never contains the secret segment, only its length, so that a caller
    cannot accidentally log one by logging this.
    """
    text = str(url or "").strip()
    if not text:
        return ("unusable", {}, ["empty"])
    try:
        split = urlsplit(text if "://" in text else "https://" + text)
        host = (split.hostname or "").lower()
    except ValueError:
        return ("unusable", {}, ["unparseable"])
    if not host:
        return ("unusable", {}, ["unparseable"])
    notes = []
    if (split.scheme or "https").lower() != "https":
        notes.append("insecure-scheme")
    segments = [s for s in (split.path or "").split("/") if s]
    if host != HOOK_HOST:
        return ("not-a-webhook", {"host": host},
                notes + ["slack-but-not-hooks" if host.endswith("slack.com")
                         else "foreign-host"])
    if segments[:1] == ["services"]:
        if len(segments) != 4:
            return ("unusable", {"host": host}, notes + ["truncated-path"])
        team, hook, secret = segments[1], segments[2], segments[3]
        if not team.startswith(("T", "E")):
            notes.append("odd-team-segment")
        if not hook.startswith("B"):
            notes.append("odd-hook-segment")
        if len(secret) < 20:
            notes.append("short-secret")
        return ("services",
                {"host": host, "team": team, "hook": hook, "secret_len": len(secret)},
                notes)
    if segments[:1] in (["triggers"], ["workflows"]):
        return ("workflow-trigger",
                {"host": host, "team": segments[1] if len(segments) > 1 else ""},
                notes + ["workflow-trigger"])
    return ("not-a-webhook", {"host": host}, notes + ["unknown-path"])


def redact_webhook_url(url):
    """A form of the URL safe to print, log, paste and screenshot. Pure.

    The secret segment never appears, and neither does enough of the other two
    to reconstruct anything. Everything this script prints goes through here.
    """
    kind, parts, _notes = parse_webhook_url(url)
    if kind == "services":
        return "%s/services/%s/%s/%s" % (parts["host"], parts["team"][:5],
                                         parts["hook"][:5], "*" * 8)
    if kind == "unusable":
        return "<unusable value>"
    return "<%s at %s>" % (kind, parts.get("host", "unknown"))


def last_webhook_delivery(messages, now_ts):
    """Days since an app last posted into this channel. Pure.

    Returns None when nothing in the sample came from an app at all, which is
    a stronger statement than "old": it means this channel has no record of the
    webhook ever having delivered within the window that was read.
    """
    best = None
    for m in messages or []:
        if not isinstance(m, dict):
            continue
        if not (m.get("bot_id") or m.get("app_id") or m.get("subtype") == "bot_message"):
            continue
        try:
            ts = float(m.get("ts") or 0)
        except (TypeError, ValueError):
            continue
        if ts and (best is None or ts > best):
            best = ts
    if best is None:
        return None
    return max(0, int((float(now_ts) - best) // 86400))


def webhook_verdict(record, facts):
    """One inventory row, judged against what the reads established. Pure.

    facts: installer_deleted (True, False or None), last_delivery_days (int or
    None), stale_days (int), known_teams (list of team ids you hold installs
    for; empty disables the check).

    The precedence is deliberate and runs from permanent to circumstantial. A
    revoked install reported as merely "silent" would send somebody to look at
    the sending system, which is working perfectly and cannot be fixed.
    """
    kind, parts, _notes = parse_webhook_url(record.get("url"))
    if kind != "services":
        return ("unusable-url",
                "the stored value is not an incoming webhook URL; it reads as %s" % kind)
    state = str(record.get("install_state") or "").strip().lower()
    if state in DEAD_INSTALL_STATES:
        return ("dead-install",
                "the installation behind this webhook is %s, so the URL answers "
                "no_service and a reinstall mints a different one" % state)
    if facts.get("installer_deleted") is True:
        return ("dead-installer",
                "the authorising user is deactivated; a webhook dies with the human "
                "who granted it even though the bot token keeps working")
    known = [str(t) for t in (facts.get("known_teams") or []) if t]
    if known and parts["team"] not in known:
        return ("foreign-workspace",
                "the URL was issued for %s, which is not a workspace this inventory "
                "holds an install for" % parts["team"])
    days = facts.get("last_delivery_days")
    stale = int(facts.get("stale_days") or 30)
    if days is None:
        return ("never-delivered",
                "no app posted into the bound channel anywhere in the sample read, so "
                "this webhook has delivered nothing within that window")
    if int(days) > stale:
        return ("silent",
                "the last app message in the bound channel is %d days old, past the "
                "%d day window" % (int(days), stale))
    return ("live", "an app delivered into the bound channel %d day(s) ago" % int(days))


def inventory_gaps(record):
    """The bookkeeping that makes the next outage slow to find. Pure.

    None of these is an outage today. Every one of them is a reason the outage
    that does happen takes five weeks to attribute to Slack.
    """
    out = []
    if not str(record.get("used_by") or "").strip():
        out.append(("no-owner", "no system is recorded as holding this URL, so a "
                                "rotation has nowhere to land"))
    if not str(record.get("installed_by") or "").strip():
        out.append(("no-installer", "no authorising user is recorded, so the one "
                                    "event that silently kills this URL cannot be "
                                    "watched for"))
    if not str(record.get("channel_id") or "").strip():
        out.append(("no-channel", "no bound channel is recorded, so nothing can be "
                                  "read back to show what was delivered"))
    return out


def duplicate_owners(records):
    """Which URLs are pasted into more than one system? Pure.

    Returns [(redacted, [owner, ...]), ...]. Sharing one URL between systems
    is not wrong in itself, and it is the reason a rotation that looked like a
    one line change took a system down that nobody had connected to it.
    """
    by_url = {}
    order = []
    for r in records or []:
        url = str((r or {}).get("url") or "").strip()
        if not url:
            continue
        owner = str(r.get("used_by") or "").strip() or "unrecorded"
        if url not in by_url:
            by_url[url] = []
            order.append(url)
        if owner not in by_url[url]:
            by_url[url].append(owner)
    return [(redact_webhook_url(u), by_url[u]) for u in order if len(by_url[u]) > 1]


def read(session, method, token, params=None):
    """One GET. Slack answers 200 for failures too, so the body is the answer."""
    r = session.get(API + method, headers={"Authorization": "Bearer " + token},
                    params=params or {}, timeout=30)
    try:
        return r.json()
    except ValueError:
        return {"ok": False, "error": "unparseable_body"}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--inventory", required=True,
                    help="JSON list of rows: url, used_by, installed_by, "
                         "channel_id, install_state")
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN",
                    help="environment variable holding a read scoped bot token")
    ap.add_argument("--stale-days", type=int, default=30,
                    help="how old the last delivery may be before it is a finding")
    ap.add_argument("--limit", type=int, default=200,
                    help="messages of channel history to read per bound channel")
    ap.add_argument("--now", type=float, default=0.0,
                    help="epoch seconds to measure against, for a repeatable run")
    args = ap.parse_args()

    with open(args.inventory, encoding="utf-8") as fh:
        records = json.load(fh)
    now_ts = args.now or time.time()
    findings = 0

    token = os.environ.get(args.token_env)
    session = requests.Session()
    known_teams = []
    if token:
        who = read(session, "auth.test", token)
        if who.get("ok") is True:
            known_teams = [who.get("team_id")]
            log.info("anchor     %-14s auth.test names the workspace this token "
                     "lives in", who.get("team_id"))
        else:
            log.warning("anchor     unavailable    auth.test answered ok: false, "
                        "error=%s", who.get("error"))
    else:
        log.warning("anchor     skipped        set %s to read the authorising users "
                    "and the bound channels", args.token_env)

    installer_state = {}
    channel_days = {}
    if token:
        for uid in sorted({str(r.get("installed_by") or "").strip()
                           for r in records} - {""}):
            body = read(session, "users.info", token, {"user": uid})
            installer_state[uid] = (bool((body.get("user") or {}).get("deleted"))
                                    if body.get("ok") is True else None)
        for cid in sorted({str(r.get("channel_id") or "").strip()
                           for r in records} - {""}):
            body = read(session, "conversations.history", token,
                        {"channel": cid, "limit": args.limit})
            if body.get("ok") is True:
                channel_days[cid] = last_webhook_delivery(body.get("messages"), now_ts)
            else:
                log.warning("channel    %-14s conversations.history answered %s",
                            cid, body.get("error"))

    for record in records:
        facts = {
            "installer_deleted": installer_state.get(
                str(record.get("installed_by") or "").strip()),
            "last_delivery_days": channel_days.get(
                str(record.get("channel_id") or "").strip()),
            "stale_days": args.stale_days,
            "known_teams": known_teams,
        }
        state, detail = webhook_verdict(record, facts)
        owner = str(record.get("used_by") or "unrecorded")
        emit = log.info if state == "live" else log.warning
        emit("webhook    %-14s %s -> %s", state, owner,
             redact_webhook_url(record.get("url")))
        emit("                          %s", detail)
        if state != "live":
            findings += 1
        for code, why in inventory_gaps(record):
            log.warning("gap        %-14s %s: %s", code, owner, why)
            findings += 1

    for redacted, owners in duplicate_owners(records):
        log.warning("shared     %-14s %s is held by %s", "duplicate-url", redacted,
                    ", ".join(owners))
        findings += 1

    if not findings:
        log.info("verdict    clean          every row resolves to a live install and "
                 "a channel that is receiving")
        return 0
    log.warning("verdict    %d finding(s)", findings)
    log.warning("  repair: a dead webhook cannot be revived; reinstall the app to mint "
                "a new URL and update every system holding the old one")
    log.warning("  repair: move anything that matters to a bot token and "
                "chat.postMessage, which survives the authorising user leaving")
    log.warning("  repair: keep the inventory, with an owner per row, because Slack "
                "has no method that lists where your webhook URLs went")
    log.warning("  note:   nothing was sent to any webhook URL to establish this; a "
                "webhook has no read side and every request to one is a message")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-webhook-inventory.mjs",
"js": '''/**
 * Hold an inventory of incoming webhook URLs against the installs behind them.
 *
 * Read only, and one thing is refused outright. An incoming webhook URL exists
 * for exactly one purpose: to have a message sent to it. There is no status
 * endpoint and no "is this alive" call, so the only way to ask Slack directly
 * whether a webhook works is to deliver a message into a real channel in front
 * of real people. Nothing here sends anything to hooks.slack.com.
 *
 * Three reads: auth.test once, users.info once per distinct authorising user,
 * conversations.history once per distinct bound channel. No webhook URL is
 * ever printed in full.
 */
import { readFile } from 'node:fs/promises';

const API = 'https://slack.com/api/';
const HOOK_HOST = 'hooks.slack.com';

// Install states that already mean the webhook is gone. Slack does not revoke
// a webhook on its own: it dies with the install, the authorisation, or the
// human who granted it.
export const DEAD_INSTALL_STATES = ['revoked', 'uninstalled', 'token_revoked',
  'deleted'];

/**
 * Read a webhook URL's shape without contacting anything. Pure.
 * Returns [kind, parts, notes]; services, workflow-trigger, not-a-webhook,
 * unusable. parts never carries the secret segment, only its length.
 */
export function parseWebhookUrl(url) {
  const text = String(url ?? '').trim();
  if (!text) return ['unusable', {}, ['empty']];
  let parsed;
  try {
    parsed = new URL(text.includes('://') ? text : `https://${text}`);
  } catch {
    return ['unusable', {}, ['unparseable']];
  }
  const host = parsed.hostname.toLowerCase();
  if (!host) return ['unusable', {}, ['unparseable']];
  const notes = [];
  if (parsed.protocol.replace(':', '').toLowerCase() !== 'https') {
    notes.push('insecure-scheme');
  }
  const segments = parsed.pathname.split('/').filter(Boolean);
  if (host !== HOOK_HOST) {
    notes.push(host.endsWith('slack.com') ? 'slack-but-not-hooks' : 'foreign-host');
    return ['not-a-webhook', { host }, notes];
  }
  if (segments[0] === 'services') {
    if (segments.length !== 4) {
      notes.push('truncated-path');
      return ['unusable', { host }, notes];
    }
    const [, team, hook, secret] = segments;
    if (!(team.startsWith('T') || team.startsWith('E'))) notes.push('odd-team-segment');
    if (!hook.startsWith('B')) notes.push('odd-hook-segment');
    if (secret.length < 20) notes.push('short-secret');
    return ['services', { host, team, hook, secretLen: secret.length }, notes];
  }
  if (segments[0] === 'triggers' || segments[0] === 'workflows') {
    notes.push('workflow-trigger');
    return ['workflow-trigger', { host, team: segments[1] ?? '' }, notes];
  }
  notes.push('unknown-path');
  return ['not-a-webhook', { host }, notes];
}

/** A form of the URL safe to print, log, paste and screenshot. Pure. */
export function redactWebhookUrl(url) {
  const [kind, parts] = parseWebhookUrl(url);
  if (kind === 'services') {
    return `${parts.host}/services/${parts.team.slice(0, 5)}/`
      + `${parts.hook.slice(0, 5)}/********`;
  }
  if (kind === 'unusable') return '<unusable value>';
  return `<${kind} at ${parts.host ?? 'unknown'}>`;
}

/**
 * Days since an app last posted into this channel. Pure.
 * null means nothing in the sample came from an app at all.
 */
export function lastWebhookDelivery(messages, nowTs) {
  let best = null;
  for (const m of messages ?? []) {
    if (!m || typeof m !== 'object') continue;
    if (!(m.bot_id || m.app_id || m.subtype === 'bot_message')) continue;
    const ts = Number(m.ts ?? 0);
    if (!Number.isFinite(ts) || !ts) continue;
    if (best === null || ts > best) best = ts;
  }
  if (best === null) return null;
  return Math.max(0, Math.floor((Number(nowTs) - best) / 86400));
}

/**
 * One inventory row, judged against what the reads established. Pure.
 * The precedence runs from permanent to circumstantial on purpose.
 */
export function webhookVerdict(record, facts) {
  const [kind, parts] = parseWebhookUrl(record?.url);
  if (kind !== 'services') {
    return ['unusable-url',
      `the stored value is not an incoming webhook URL; it reads as ${kind}`];
  }
  const state = String(record?.install_state ?? '').trim().toLowerCase();
  if (DEAD_INSTALL_STATES.includes(state)) {
    return ['dead-install', `the installation behind this webhook is ${state}, so the `
      + 'URL answers no_service and a reinstall mints a different one'];
  }
  if (facts?.installerDeleted === true) {
    return ['dead-installer', 'the authorising user is deactivated; a webhook dies '
      + 'with the human who granted it even though the bot token keeps working'];
  }
  const known = (facts?.knownTeams ?? []).filter(Boolean).map(String);
  if (known.length && !known.includes(parts.team)) {
    return ['foreign-workspace', `the URL was issued for ${parts.team}, which is not a `
      + 'workspace this inventory holds an install for'];
  }
  const days = facts?.lastDeliveryDays;
  const stale = Number(facts?.staleDays ?? 30);
  if (days === null || days === undefined) {
    return ['never-delivered', 'no app posted into the bound channel anywhere in the '
      + 'sample read, so this webhook has delivered nothing within that window'];
  }
  if (Number(days) > stale) {
    return ['silent', `the last app message in the bound channel is ${Number(days)} `
      + `days old, past the ${stale} day window`];
  }
  return ['live', `an app delivered into the bound channel ${Number(days)} day(s) ago`];
}

/** The bookkeeping that makes the next outage slow to find. Pure. */
export function inventoryGaps(record) {
  const out = [];
  if (!String(record?.used_by ?? '').trim()) {
    out.push(['no-owner', 'no system is recorded as holding this URL, so a rotation '
      + 'has nowhere to land']);
  }
  if (!String(record?.installed_by ?? '').trim()) {
    out.push(['no-installer', 'no authorising user is recorded, so the one event that '
      + 'silently kills this URL cannot be watched for']);
  }
  if (!String(record?.channel_id ?? '').trim()) {
    out.push(['no-channel', 'no bound channel is recorded, so nothing can be read back '
      + 'to show what was delivered']);
  }
  return out;
}

/** Which URLs are pasted into more than one system? Pure. */
export function duplicateOwners(records) {
  const byUrl = new Map();
  for (const r of records ?? []) {
    const url = String(r?.url ?? '').trim();
    if (!url) continue;
    const owner = String(r?.used_by ?? '').trim() || 'unrecorded';
    if (!byUrl.has(url)) byUrl.set(url, []);
    if (!byUrl.get(url).includes(owner)) byUrl.get(url).push(owner);
  }
  return [...byUrl.entries()]
    .filter(([, owners]) => owners.length > 1)
    .map(([url, owners]) => [redactWebhookUrl(url), owners]);
}

function arg(args, name, fallback = '') {
  const i = args.indexOf(name);
  return i === -1 ? fallback : args[i + 1];
}

async function read(method, token, params = {}) {
  const qs = new URLSearchParams(params).toString();
  const r = await fetch(`${API}${method}${qs ? `?${qs}` : ''}`,
    { headers: { Authorization: `Bearer ${token}` } });
  try {
    return await r.json();
  } catch {
    return { ok: false, error: 'unparseable_body' };
  }
}

async function main() {
  const args = process.argv.slice(2);
  const records = JSON.parse(await readFile(arg(args, '--inventory'), 'utf8'));
  const tokenEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
  const staleDays = Number(arg(args, '--stale-days', '30'));
  const limit = arg(args, '--limit', '200');
  const nowTs = Number(arg(args, '--now', '0')) || Date.now() / 1000;
  const token = process.env[tokenEnv];
  let findings = 0;
  let knownTeams = [];

  if (token) {
    const who = await read('auth.test', token);
    if (who.ok === true) {
      knownTeams = [who.team_id];
      console.log(`anchor     ${String(who.team_id).padEnd(14)} auth.test names the `
        + 'workspace this token lives in');
    } else {
      console.warn('anchor     unavailable    auth.test answered ok: false, '
        + `error=${who.error}`);
    }
  } else {
    console.warn(`anchor     skipped        set ${tokenEnv} to read the authorising `
      + 'users and the bound channels');
  }

  const installerState = new Map();
  const channelDays = new Map();
  if (token) {
    const users = [...new Set(records.map((r) => String(r.installed_by ?? '').trim()))]
      .filter(Boolean).sort();
    for (const uid of users) {
      const body = await read('users.info', token, { user: uid });
      installerState.set(uid, body.ok === true ? Boolean(body.user?.deleted) : null);
    }
    const channels = [...new Set(records.map((r) => String(r.channel_id ?? '').trim()))]
      .filter(Boolean).sort();
    for (const cid of channels) {
      const body = await read('conversations.history', token,
        { channel: cid, limit });
      if (body.ok === true) {
        channelDays.set(cid, lastWebhookDelivery(body.messages, nowTs));
      } else {
        console.warn(`channel    ${cid.padEnd(14)} conversations.history answered `
          + `${body.error}`);
      }
    }
  }

  for (const record of records) {
    const uid = String(record.installed_by ?? '').trim();
    const cid = String(record.channel_id ?? '').trim();
    const facts = {
      installerDeleted: installerState.has(uid) ? installerState.get(uid) : undefined,
      lastDeliveryDays: channelDays.has(cid) ? channelDays.get(cid) : undefined,
      staleDays,
      knownTeams,
    };
    const [state, detail] = webhookVerdict(record, facts);
    const owner = String(record.used_by ?? 'unrecorded');
    const emit = state === 'live' ? console.log : console.warn;
    emit(`webhook    ${state.padEnd(14)} ${owner} -> ${redactWebhookUrl(record.url)}`);
    emit(`                          ${detail}`);
    if (state !== 'live') findings += 1;
    for (const [code, why] of inventoryGaps(record)) {
      console.warn(`gap        ${code.padEnd(14)} ${owner}: ${why}`);
      findings += 1;
    }
  }

  for (const [redacted, owners] of duplicateOwners(records)) {
    console.warn(`shared     duplicate-url  ${redacted} is held by ${owners.join(', ')}`);
    findings += 1;
  }

  if (!findings) {
    console.log('verdict    clean          every row resolves to a live install and a '
      + 'channel that is receiving');
    return;
  }
  console.warn(`verdict    ${findings} finding(s)`);
  console.warn('  repair: a dead webhook cannot be revived; reinstall the app to mint a '
    + 'new URL and update every system holding the old one');
  console.warn('  repair: move anything that matters to a bot token and '
    + 'chat.postMessage, which survives the authorising user leaving');
  console.warn('  repair: keep the inventory, with an owner per row, because Slack has '
    + 'no method that lists where your webhook URLs went');
  console.warn('  note:   nothing was sent to any webhook URL to establish this; a '
    + 'webhook has no read side and every request to one is a message');
  process.exitCode = 1;
}

// Only run when invoked directly, so importing this module in the tests does
// not execute main().
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Every URL in these fixtures is obviously fake and the secret segment is deliberately far too short to be a real one, which the shape reader notices and says so. The assertion that matters most is the redaction test: it asserts the secret string does not appear anywhere in the output of the only function this script prints URLs through, because a diagnostic that leaks the credential it is diagnosing is worse than no diagnostic. After that it is the precedence in <code>webhook_verdict</code> &mdash; a revoked install outranks a deactivated authoriser, which outranks a foreign workspace, which outranks silence &mdash; and the <code>dead-installer</code> case, which is the whole reason this note exists.",
"test_py_file": "test_slack_webhook_inventory.py",
"test_py": '''from slack_webhook_inventory import (
    duplicate_owners, inventory_gaps, last_webhook_delivery, parse_webhook_url,
    redact_webhook_url, webhook_verdict,
)

SECRET = "notarealsecret"
HOOK = "https://hooks.slack.com/services/T00FAKE/B00FAKE/" + SECRET
NOW = 1_700_000_000.0
DAY = 86400.0


def row(**kw):
    base = {"url": HOOK, "used_by": "ci/deploy", "installed_by": "U00FAKE",
            "channel_id": "C00FAKE01", "install_state": "active"}
    base.update(kw)
    return base


def facts(**kw):
    base = {"installer_deleted": False, "last_delivery_days": 1, "stale_days": 30,
            "known_teams": ["T00FAKE"]}
    base.update(kw)
    return base


def test_a_real_shaped_webhook_url_is_read_as_services():
    kind, parts, _notes = parse_webhook_url(HOOK)
    assert kind == "services"
    assert parts["team"] == "T00FAKE"
    assert parts["hook"] == "B00FAKE"


def test_the_secret_segment_is_measured_and_never_carried():
    _kind, parts, notes = parse_webhook_url(HOOK)
    assert parts["secret_len"] == len(SECRET)
    assert SECRET not in str(parts)
    assert "short-secret" in notes


def test_redaction_never_reproduces_the_secret():
    redacted = redact_webhook_url(HOOK)
    assert SECRET not in redacted
    assert "hooks.slack.com/services/" in redacted
    assert redacted.endswith("*" * 8)


def test_a_workflow_trigger_url_is_a_different_surface_and_says_so():
    kind, _parts, _notes = parse_webhook_url(
        "https://hooks.slack.com/triggers/T00FAKE/1234/abcd")
    assert kind == "workflow-trigger"


def test_a_web_api_url_filed_in_the_wrong_column_is_not_a_webhook():
    kind, _parts, notes = parse_webhook_url("https://slack.com/api/chat.postMessage")
    assert kind == "not-a-webhook"
    assert "slack-but-not-hooks" in notes


def test_a_truncated_paste_is_unusable_rather_than_dead():
    kind, _parts, notes = parse_webhook_url("https://hooks.slack.com/services/T00FAKE")
    assert kind == "unusable"
    assert "truncated-path" in notes


def test_an_empty_or_unparseable_value_never_reaches_a_verdict():
    assert parse_webhook_url("")[0] == "unusable"
    assert redact_webhook_url("") == "<unusable value>"


def test_the_most_recent_app_message_sets_the_age():
    messages = [{"ts": str(NOW - 3 * DAY), "bot_id": "B00FAKE"},
                {"ts": str(NOW - 9 * DAY), "bot_id": "B00FAKE"}]
    assert last_webhook_delivery(messages, NOW) == 3


def test_messages_from_humans_do_not_count_as_a_delivery():
    messages = [{"ts": str(NOW - DAY), "user": "U00FAKE", "text": "morning"}]
    assert last_webhook_delivery(messages, NOW) is None


def test_an_empty_history_is_none_rather_than_zero():
    assert last_webhook_delivery([], NOW) is None


def test_a_revoked_install_outranks_every_other_explanation():
    state, detail = webhook_verdict(row(install_state="revoked"),
                                    facts(installer_deleted=True,
                                          last_delivery_days=None))
    assert state == "dead-install"
    assert "no_service" in detail


def test_a_deactivated_authoriser_kills_the_url_while_the_bot_token_lives():
    state, detail = webhook_verdict(row(), facts(installer_deleted=True))
    assert state == "dead-installer"
    assert "bot token" in detail


def test_a_url_issued_for_another_workspace_is_named_before_any_silence():
    state, detail = webhook_verdict(row(), facts(known_teams=["T00OTHER"],
                                                 last_delivery_days=None))
    assert state == "foreign-workspace"
    assert "T00FAKE" in detail


def test_a_channel_no_app_has_posted_in_is_never_delivered():
    assert webhook_verdict(row(), facts(last_delivery_days=None))[0] == "never-delivered"


def test_a_delivery_older_than_the_window_is_silent_and_names_the_window():
    state, detail = webhook_verdict(row(), facts(last_delivery_days=45, stale_days=14))
    assert state == "silent"
    assert "14" in detail


def test_a_recent_delivery_into_the_bound_channel_is_live():
    assert webhook_verdict(row(), facts(last_delivery_days=0))[0] == "live"


def test_a_row_holding_something_that_is_not_a_webhook_never_reaches_liveness():
    state, _detail = webhook_verdict(row(url="https://example.com/hook"), facts())
    assert state == "unusable-url"


def test_the_gaps_that_make_the_next_outage_slow_are_each_named():
    codes = [c for c, _w in inventory_gaps({"url": HOOK})]
    assert codes == ["no-owner", "no-installer", "no-channel"]
    assert inventory_gaps(row()) == []


def test_one_url_held_by_two_systems_is_reported_once_and_redacted():
    shared = duplicate_owners([row(used_by="ci/deploy"), row(used_by="ops/cron"),
                               row(url=HOOK + "x", used_by="alerts")])
    assert len(shared) == 1
    redacted, owners = shared[0]
    assert owners == ["ci/deploy", "ops/cron"]
    assert SECRET not in redacted
''',
"test_js_file": "slack-webhook-inventory.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  duplicateOwners, inventoryGaps, lastWebhookDelivery, parseWebhookUrl,
  redactWebhookUrl, webhookVerdict,
} from './slack-webhook-inventory.mjs';

const SECRET = 'notarealsecret';
const HOOK = `https://hooks.slack.com/services/T00FAKE/B00FAKE/${SECRET}`;
const NOW = 1700000000;
const DAY = 86400;

const row = (kw = {}) => ({
  url: HOOK,
  used_by: 'ci/deploy',
  installed_by: 'U00FAKE',
  channel_id: 'C00FAKE01',
  install_state: 'active',
  ...kw,
});

const facts = (kw = {}) => ({
  installerDeleted: false,
  lastDeliveryDays: 1,
  staleDays: 30,
  knownTeams: ['T00FAKE'],
  ...kw,
});

test('a real shaped webhook url is read as services', () => {
  const [kind, parts] = parseWebhookUrl(HOOK);
  assert.equal(kind, 'services');
  assert.equal(parts.team, 'T00FAKE');
  assert.equal(parts.hook, 'B00FAKE');
});

test('the secret segment is measured and never carried', () => {
  const [, parts, notes] = parseWebhookUrl(HOOK);
  assert.equal(parts.secretLen, SECRET.length);
  assert.equal(JSON.stringify(parts).includes(SECRET), false);
  assert.equal(notes.includes('short-secret'), true);
});

test('redaction never reproduces the secret', () => {
  const redacted = redactWebhookUrl(HOOK);
  assert.equal(redacted.includes(SECRET), false);
  assert.equal(redacted.includes('hooks.slack.com/services/'), true);
  assert.equal(redacted.endsWith('********'), true);
});

test('a workflow trigger url is a different surface and says so', () => {
  assert.equal(
    parseWebhookUrl('https://hooks.slack.com/triggers/T00FAKE/1234/abcd')[0],
    'workflow-trigger');
});

test('a web api url filed in the wrong column is not a webhook', () => {
  const [kind, , notes] = parseWebhookUrl('https://slack.com/api/chat.postMessage');
  assert.equal(kind, 'not-a-webhook');
  assert.equal(notes.includes('slack-but-not-hooks'), true);
});

test('a truncated paste is unusable rather than dead', () => {
  const [kind, , notes] = parseWebhookUrl('https://hooks.slack.com/services/T00FAKE');
  assert.equal(kind, 'unusable');
  assert.equal(notes.includes('truncated-path'), true);
});

test('an empty or unparseable value never reaches a verdict', () => {
  assert.equal(parseWebhookUrl('')[0], 'unusable');
  assert.equal(redactWebhookUrl(''), '<unusable value>');
});

test('the most recent app message sets the age', () => {
  const messages = [{ ts: String(NOW - 3 * DAY), bot_id: 'B00FAKE' },
    { ts: String(NOW - 9 * DAY), bot_id: 'B00FAKE' }];
  assert.equal(lastWebhookDelivery(messages, NOW), 3);
});

test('messages from humans do not count as a delivery', () => {
  const messages = [{ ts: String(NOW - DAY), user: 'U00FAKE', text: 'morning' }];
  assert.equal(lastWebhookDelivery(messages, NOW), null);
});

test('an empty history is null rather than zero', () => {
  assert.equal(lastWebhookDelivery([], NOW), null);
});

test('a revoked install outranks every other explanation', () => {
  const [state, detail] = webhookVerdict(row({ install_state: 'revoked' }),
    facts({ installerDeleted: true, lastDeliveryDays: null }));
  assert.equal(state, 'dead-install');
  assert.equal(detail.includes('no_service'), true);
});

test('a deactivated authoriser kills the url while the bot token lives', () => {
  const [state, detail] = webhookVerdict(row(), facts({ installerDeleted: true }));
  assert.equal(state, 'dead-installer');
  assert.equal(detail.includes('bot token'), true);
});

test('a url issued for another workspace is named before any silence', () => {
  const [state, detail] = webhookVerdict(row(),
    facts({ knownTeams: ['T00OTHER'], lastDeliveryDays: null }));
  assert.equal(state, 'foreign-workspace');
  assert.equal(detail.includes('T00FAKE'), true);
});

test('a channel no app has posted in is never delivered', () => {
  assert.equal(webhookVerdict(row(), facts({ lastDeliveryDays: null }))[0],
    'never-delivered');
});

test('a delivery older than the window is silent and names the window', () => {
  const [state, detail] = webhookVerdict(row(),
    facts({ lastDeliveryDays: 45, staleDays: 14 }));
  assert.equal(state, 'silent');
  assert.equal(detail.includes('14'), true);
});

test('a recent delivery into the bound channel is live', () => {
  assert.equal(webhookVerdict(row(), facts({ lastDeliveryDays: 0 }))[0], 'live');
});

test('a row holding something that is not a webhook never reaches liveness', () => {
  assert.equal(webhookVerdict(row({ url: 'https://example.com/hook' }), facts())[0],
    'unusable-url');
});

test('the gaps that make the next outage slow are each named', () => {
  assert.deepEqual(inventoryGaps({ url: HOOK }).map(([c]) => c),
    ['no-owner', 'no-installer', 'no-channel']);
  assert.deepEqual(inventoryGaps(row()), []);
});

test('one url held by two systems is reported once and redacted', () => {
  const shared = duplicateOwners([row({ used_by: 'ci/deploy' }),
    row({ used_by: 'ops/cron' }), row({ url: `${HOOK}x`, used_by: 'alerts' })]);
  assert.equal(shared.length, 1);
  const [redacted, owners] = shared[0];
  assert.deepEqual(owners, ['ci/deploy', 'ops/cron']);
  assert.equal(redacted.includes(SECRET), false);
});
''',
"faq": [
 ("Can I not just send a test message to the URL and see what comes back?",
  "You can, and it is the one thing this note asks you not to do. A webhook URL has no read side at all: no status endpoint, no HEAD, no metadata call. Every request Slack accepts is a message delivered into a real channel, so a probe is a write with an audience, and somebody then has to explain the test message to the people who saw it. Sending an empty body does not help either, because it is refused with no_text and tells you nothing you did not already know. Everything the probe would establish is available from the URL's shape, your install records, users.info on the authorising user, and the bound channel's own history."),
 ("Our app is installed and the bot token works. How can the webhook be dead?",
  "Because they have different lifetimes. A bot token belongs to the installation and survives the person who created it; an incoming webhook belongs to one authorisation by one human. Deactivate that human and the webhook dies while auth.test keeps answering ok: true, chat.postMessage keeps working and every dashboard you have stays green. That is the dead-installer verdict, and it is the reason this check reads users.info on the authoriser rather than reading the health of the app."),
 ("Will reinstalling the app bring the old URL back?",
  "No. A reinstall mints a new webhook URL, and the old one stays dead forever. That is why the repair is not a one line change: every system holding the old URL has to be updated, which is exactly the moment teams discover they do not know how many systems that is. Keeping an inventory with an owner per row is the cheap part of this note and the part that pays for itself."),
 ("What is the difference between no_service, no_active_hooks and invalid_token?",
  "They are three ways of saying the URL will never work again, and the distinction matters less than people hope. no_service and no_active_hooks come back as 404 and mean the webhook behind this URL no longer exists: uninstalled, revoked, deleted or authorised by someone who is gone. invalid_token comes back as 401 and usually means the URL itself is wrong rather than dead, which in practice means truncated by a config file, re-wrapped by an email client, or copied with a trailing character. The first two are fixed by reinstalling; the third is fixed by checking what you stored, which is what the shape reader here does before anything else."),
 ("A webhook nobody uses any more is harmless, surely?",
  "It is the opposite of harmless. A dead webhook is an outage that has already happened. A live webhook that nothing uses is a standing bearer credential sitting in a config file, a wiki page or an old repository, and anyone who finds it can post into your workspace as your app, indefinitely, with no audit trail pointing at them. That is why the no-owner gap is reported as a finding rather than as a note: a URL nobody claims is a URL nobody will revoke."),
],
"related": [
 ("/slack/token-revoked/", "the same death, seen from the bot token's side"),
 ("/slack/account-inactive/", "the offboarding that kills the authorisation"),
 ("/slack/webhook-locked-to-one-channel/", "the webhook that works and posts to one room"),
],
"citations": [CITE_WEBHOOKS, CITE_SO_NO_SERVICE, CITE_USERS_INFO, CITE_HISTORY],
})
GUIDES.append({
"slug": "webhook-locked-to-one-channel",
"title": "The webhook posts to one channel whatever the payload says",
"description": "An app based webhook is bound to one channel at creation. The channel field every old blog post shows is inert, and a routing table collapses into one room.",
"h1": "The webhook posts to one channel whatever the payload says",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack webhook ignores channel field",
             "slack incoming webhook channel override not working",
             "slack webhook posts to wrong channel",
             "slack webhook one channel per url",
             "slack webhook routing chat.postMessage"],
"deps": "Python 3.9+ with requests, or Node.js 18+; a bot token with channels:read and channels:history, the channel the webhook is bound to, and the destinations your sending code asks for",
"lead": "The alert router has four destinations. Database alerts go to <code>#db-oncall</code>, deploy notices to <code>#releases</code>, security events to <code>#sec-ops</code>, and everything else to <code>#alerts</code>. The code sets a <code>channel</code> field on every payload, exactly as the tutorial it was written from does, and every send comes back <code>ok</code>.</p><p>Then somebody in <code>#db-oncall</code> mentions that they have not seen a database alert in a while, and somebody in <code>#alerts</code> mentions that the channel has become unreadable. All four streams have been arriving in one room since the migration off the old custom integration, eighteen months ago, and nothing failed to make that happen.",
"short_answer": """<p>An incoming webhook created through the modern Slack app model is bound to <strong>one channel, chosen at the moment it was created</strong>, and that binding cannot be changed by the payload. The <code>channel</code> field is a leftover from custom integrations: on an app based webhook it does not choose anything. Depending on where the value came from you get silence &mdash; the message lands in the bound channel anyway &mdash; or a refusal.</p>
<p>This is the failure mode with the fewest symptoms in this section. Nothing errors. Slack answers each send with <code>ok</code>, the messages exist, they are readable, they are just all in one place. The people who would notice are the ones in the three channels that receive nothing, and an empty channel produces no signal at all. The people in the fourth channel notice something, but what they notice is noise, which reads as a volume problem rather than a routing problem.</p>
<p>The repair is not a better payload. It is a different mechanism: a bot token and <code>chat.postMessage</code> with an explicit <code>channel</code> per message, which is one credential that can reach any channel the bot is in. If webhooks have to stay, you need one webhook per destination and a routing table on your side, accepting that each URL is a separate secret with a separate lifetime. The script below establishes which of the two situations you are in without sending anything to any webhook URL.</p>""",
"problem": """<p>The <code>channel</code> override was real. Custom integrations &mdash; the pre-app model, configured per workspace rather than per app &mdash; honoured a <code>channel</code> field, and roughly every tutorial, gist and Stack Overflow answer written before 2016 demonstrates it. That documentation did not go anywhere. It is still the top result, still copied into new code, and the code written from it still runs without error, which is the worst possible combination: a wrong instruction that produces no complaint.</p>
<p>Migrating off custom integrations is where this usually lands. The migration is presented as a credential swap: get a new URL, put it in the config, done. The URL works, the messages arrive, the deploy is called a success. What silently changed is that a routing scheme with four outputs now has one, and the evidence for that is spread across three channels that stopped receiving and one that started receiving four times as much.</p>
<p>There is a second shape, and it is the one that produces a symptom. Send a <code>channel</code> value that the webhook's own app cannot resolve, or a channel reference in a form the surface will not take, and instead of quietly ignoring it you get a refusal. That converts an invisible routing collapse into a visible failure, which sounds better and often is not, because the team then fixes the channel reference and restores the silence.</p>
<p>The third shape is the one people build on purpose after discovering the first two: one webhook per destination channel, held in a routing table. This works. It is also four bearer credentials instead of one, four things to rotate, four things to inventory, four things that die independently when someone leaves, and no method anywhere that lists them. It is a legitimate answer when a system genuinely cannot hold a token, and it is a poor answer for anything that can.</p>""",
"why": """<p><strong>The finding is the presence of the field, not the response to it.</strong> If your sending code sets <code>channel</code> on an app based webhook payload at all, that is the whole diagnosis: the field is inert, so either it agrees with the binding and is decoration, or it disagrees and the intent is being lost. This is why the check reads what your code intends rather than what Slack answered. Slack's answer is <code>ok</code> in the interesting case.</p>
<p><strong>Counting distinct destinations is what turns a style note into an outage report.</strong> One inert <code>channel</code> field that happens to name the bound channel is harmless. Four distinct values across a routing table means three destinations are receiving nothing and one is receiving everything, and the script reports that as <code>collapsed</code> with the count, because the number is the argument.</p>
<p><strong>A channel reference has two forms and they do not compare directly.</strong> Your code may hold <code>#db-oncall</code> and your install record holds <code>C07AB12CD</code>. Comparing those as strings says they differ, which is useless. So references are normalised to a kind and a value first, names are folded and stripped of the leading hash, and the comparison happens between comparable things.</p>
<p><strong>The corroboration comes from the channel, not from your logs.</strong> Your logs say what you sent, which is exactly the thing that is not in question. <code>conversations.history</code> on the bound channel says what arrived, and a sample in which several routing keys turn up in a single channel is the evidence that the fan out collapsed. That reading needs <code>channels:history</code> and nothing else, and it works even for sending code you cannot read.</p>
<p><strong>Markers are supplied rather than guessed at, and matched in the order you give them.</strong> A script that tried to infer which team a message was meant for would be inventing the finding. Instead you pass the substrings that identify each stream &mdash; a service name, a prefix, an emoji &mdash; and the first marker that matches wins, deterministically, so two runs over the same history produce the same counts.</p>
<p><strong>Nothing here sends anything to a webhook URL.</strong> The tempting probe is to send one message with a <code>channel</code> field and see where it lands, and that probe posts into a real channel in front of people, twice if you want a control. The two readings this script does &mdash; what the code intends and what the bound channel actually received &mdash; answer the same question with no audience.</p>""",
"steps": [
 {"h": "Find the channel the webhook is actually bound to",
  "body": """<p>It is in the OAuth install response, under <code>incoming_webhook.channel</code> and <code>incoming_webhook.channel_id</code>, and it should be in your install record. If it is not, <code>conversations.info</code> on the channel id names it. This is the one destination that exists, and everything else is compared against it.</p>"""},
 {"h": "Collect the destinations your sending code asks for",
  "body": """<p>One row per send site: a name and the <code>channel</code> value it sets. This comes from the code, not from Slack, because Slack has no record of an intent it ignored. A grep for the payload builder is usually enough.</p>"""},
 {"h": "Say what each override field does, which is nothing",
  "body": """<p><code>payload_overrides</code> flags <code>channel</code> as inert on an app based webhook, and flags <code>username</code>, <code>icon_emoji</code> and <code>icon_url</code> as coming from the same custom integration era and not to be depended on. These are not errors and they are not features either.</p>"""},
 {"h": "Count the destinations against the binding",
  "body": """<p><code>fanout_verdict</code> answers <code>collapsed</code> when more than one destination is asked for, <code>misdirected</code> when exactly one is asked for and it is not the bound channel, <code>aligned</code> when the field is inert but harmless, and <code>no-override</code> when the code does not set the field at all, which is the correct shape.</p>"""},
 {"h": "Read the bound channel and see whose traffic is in it",
  "body": """<p>Pass a marker or two per intended destination, then <code>arrival_mix</code> counts the sample. Several streams present in one channel is the corroboration, and it is the reading that convinces somebody who does not believe the code review.</p>"""},
 {"h": "Move the routing to a bot token, or accept one secret per room",
  "body": """<p><code>chat.postMessage</code> with a bot token takes an explicit channel per message and reaches any channel the bot is in, with one credential and a structured error when something is wrong. One webhook per channel is the fallback for systems that cannot hold a token, and it is a real cost: a separate secret per destination, each with its own way of dying.</p>"""},
],
"verify": """<p>Once the sends carry no <code>channel</code> field, or once you have moved to <code>chat.postMessage</code>, run it again. The fan out row should read <code>no-override</code> and the arrival row should show one stream.</p>
<pre><code class="language-bash">python3 slack_webhook_routing.py --sends sends.json --bound-channel C07AB12CD \\
  --markers '{"#db-oncall": ["pg-primary"], "#releases": ["deployed"], \\
              "#sec-ops": ["cve-"]}'
# bound      C07AB12CD      #alerts, from the install record
# override   channel-override  db-alerts sets channel=#db-oncall, which is inert on an
#                              app based webhook: the destination was fixed at creation
# override   legacy-override   release-notes sets username, from the same era
# fanout     collapsed      4 distinct destinations are asked for and one channel
#                           receives all of them
# arrival    mixed          #db-oncall, #releases, #sec-ops traffic all arrived in
#                           #alerts across 200 messages read
# verdict    3 finding(s)
#   repair: move to chat.postMessage with a bot token and an explicit channel id
#   note:   nothing was sent to any webhook URL to establish this</code></pre>""",
"code_intro": "Two reads and no sends. <code>payload_overrides</code> names the fields that no longer do anything; <code>normalise_channel_reference</code> and <code>same_destination</code> make a <code>#name</code> and a <code>C&hellip;</code> id comparable before anything is compared; <code>fanout_verdict</code> counts the distinct destinations the code asks for against the one it has, and <code>arrival_mix</code> with <code>evidence_verdict</code> turn a page of the bound channel's history into the corroboration. Every one of them is pure, and the only network calls in the file are <code>conversations.info</code> and <code>conversations.history</code>.",
"py_file": "slack_webhook_routing.py",
"py": '''"""Find out whether your webhook routing collapsed into a single channel.

Read only, and nothing is sent to any webhook URL. The obvious probe here is
to send one message with a channel field and see where it lands, which posts
into a real channel in front of real people - twice, if you want a control.
The two readings this script makes answer the same question with no audience:
what the sending code intends, and what the bound channel actually received.

An incoming webhook created through the app model is bound to one channel at
creation. The channel field in the payload is a custom integration leftover
and does not choose anything. So the finding is the presence of the field and
the number of distinct destinations behind it, not Slack's answer, which is ok.

Two reads: conversations.info to name the bound channel, and
conversations.history to see whose traffic is arriving in it.
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_webhook_routing")

API = "https://slack.com/api/"

# Fields that a custom integration webhook honoured and an app based one does
# not. They are not errors, and they are not features either.
LEGACY_OVERRIDE_KEYS = ("username", "icon_emoji", "icon_url")

# Channel ids are upper case and start with one of these. Anything else in a
# channel field is a name, whether or not somebody remembered the hash.
ID_PREFIXES = ("C", "G", "D")


def payload_overrides(payload):
    """Which fields in this webhook payload no longer do anything? Pure.

    Returns [(code, why), ...]. channel is the finding; the other three come
    from the same era and are listed so that nobody rebuilds the routing on
    top of them next.
    """
    if not isinstance(payload, dict):
        return [("not-an-object", "a webhook payload is a JSON object and this is not "
                                  "one, so nothing about its routing can be read")]
    out = []
    if "channel" in payload:
        out.append(("channel-override",
                    "channel=%s is inert on an app based webhook: the destination was "
                    "fixed when the webhook was created" % payload.get("channel")))
    for key in LEGACY_OVERRIDE_KEYS:
        if key in payload:
            out.append(("legacy-override",
                        "%s comes from the same custom integration era as the channel "
                        "override and should not be depended on" % key))
    return out


def normalise_channel_reference(ref):
    """Reduce a channel reference to (kind, value). Pure.

    Kinds are id, name and empty. Names are folded and lose the leading hash,
    because #DB-Oncall and db-oncall are the same room and comparing them as
    written says otherwise. Ids are left exactly as they are, because they are
    case sensitive identifiers rather than words.

    An id is recognised by shape rather than by a lookup: nine characters or
    more, upper case, alphanumeric, beginning with C, G or D, and containing at
    least one digit. The digit is what keeps a shouted channel name out of the
    id branch, where it would be compared against a channel id and never match.
    """
    text = str(ref or "").strip()
    if not text:
        return ("empty", "")
    if (len(text) >= 9 and text[0] in ID_PREFIXES and text.upper() == text
            and text.isalnum() and any(c.isdigit() for c in text)):
        return ("id", text)
    return ("name", text.lstrip("#").lower())


def same_destination(ref, bound_id, bound_name):
    """Does this reference name the channel the webhook is bound to? Pure."""
    kind, value = normalise_channel_reference(ref)
    if kind == "empty":
        return False
    if kind == "id":
        return value == str(bound_id or "").strip()
    return value == str(bound_name or "").strip().lstrip("#").lower()


def fanout_verdict(sends, bound_id, bound_name):
    """How many destinations does the code ask for, and how many exist? Pure.

    sends: [{"name": ..., "channel": ...}, ...] read from your own source.
    Returns (state, detail, destinations).

      no-override  no send sets a channel field. The correct shape.
      aligned      one destination, and it is the bound channel. Inert but harmless.
      misdirected  one destination, and it is not the bound channel. Every message
                   is addressed to one room and lands in another.
      collapsed    more than one destination. This is the routing table that has
                   silently had three of its four outputs removed.
    """
    destinations = []
    for send in sends or []:
        ref = send.get("channel") if isinstance(send, dict) else send
        kind, value = normalise_channel_reference(ref)
        if kind == "empty":
            continue
        key = value if kind == "id" else "#" + value
        if key not in destinations:
            destinations.append(key)
    if not destinations:
        return ("no-override", "no send sets a channel field, which is the only "
                               "correct shape for an app based webhook", destinations)
    if len(destinations) > 1:
        return ("collapsed", "%d distinct destinations are asked for and one channel "
                             "receives all of them" % len(destinations), destinations)
    if same_destination(destinations[0], bound_id, bound_name):
        return ("aligned", "the only destination asked for is the channel the webhook "
                           "is bound to, so the field is inert but harmless",
                destinations)
    return ("misdirected", "every message is addressed to %s and every message lands "
                           "in %s" % (destinations[0], bound_name or bound_id or
                                      "the bound channel"), destinations)


def arrival_mix(messages, markers):
    """Whose traffic is in the bound channel? Pure.

    markers: {destination: [substring, ...]}. Matching is case folded, and the
    first destination whose marker matches wins, in the order given, so two
    runs over the same history produce the same counts.

    Returns (counts, unmatched).
    """
    counts = {d: 0 for d in (markers or {})}
    unmatched = 0
    for m in messages or []:
        text = str((m or {}).get("text") or "").lower()
        hit = None
        for dest, subs in (markers or {}).items():
            if any(str(s).lower() in text for s in subs or []):
                hit = dest
                break
        if hit is None:
            unmatched += 1
        else:
            counts[hit] += 1
    return (counts, unmatched)


def evidence_verdict(counts, unmatched):
    """Turn the arrival counts into the corroboration, or into nothing. Pure.

    mixed is the finding: traffic for several intended destinations sitting in
    one channel. single is what a correctly bound webhook looks like. none
    means the markers did not match, which is a statement about the markers
    rather than about the routing, and it says so.
    """
    present = sorted(d for d, n in (counts or {}).items() if n)
    if len(present) > 1:
        return ("mixed", "%s traffic all arrived in one channel" % ", ".join(present),
                present)
    if len(present) == 1:
        return ("single", "only %s traffic is present, which is what a correctly bound "
                          "webhook looks like" % present[0], present)
    return ("none", "no marker matched any of the %d messages read; widen the sample or "
                    "correct the markers" % int(unmatched), present)


def read(session, method, token, params=None):
    """One GET. Slack answers 200 for failures too, so the body is the answer."""
    r = session.get(API + method, headers={"Authorization": "Bearer " + token},
                    params=params or {}, timeout=30)
    try:
        return r.json()
    except ValueError:
        return {"ok": False, "error": "unparseable_body"}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sends", required=True,
                    help="JSON list of what your code sends: name and channel")
    ap.add_argument("--bound-channel", default="",
                    help="the channel id from incoming_webhook.channel_id")
    ap.add_argument("--bound-name", default="",
                    help="its name, if you have no token to resolve the id")
    ap.add_argument("--markers", default="{}",
                    help="JSON object of destination to substrings that identify it")
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN",
                    help="environment variable holding a read scoped bot token")
    ap.add_argument("--limit", type=int, default=200,
                    help="messages of bound channel history to read")
    args = ap.parse_args()

    with open(args.sends, encoding="utf-8") as fh:
        sends = json.load(fh)
    markers = json.loads(args.markers or "{}")
    findings = 0

    token = os.environ.get(args.token_env)
    session = requests.Session()
    bound_name = args.bound_name
    if token and args.bound_channel and not bound_name:
        info = read(session, "conversations.info", token,
                    {"channel": args.bound_channel})
        if info.get("ok") is True:
            bound_name = "#" + str((info.get("channel") or {}).get("name") or "")
        else:
            log.warning("bound      unavailable    conversations.info answered %s",
                        info.get("error"))
    log.info("bound      %-14s %s, from the install record",
             args.bound_channel or "unknown", bound_name or "name not resolved")

    for send in sends:
        for code, why in payload_overrides(send.get("payload", send)):
            log.warning("override   %-16s %s: %s", code,
                        send.get("name", "unnamed"), why)
            findings += 1

    state, detail, destinations = fanout_verdict(
        [s.get("payload", s) for s in sends], args.bound_channel, bound_name)
    emit = log.info if state in ("no-override", "aligned") else log.warning
    emit("fanout     %-14s %s", state, detail)
    if state in ("collapsed", "misdirected"):
        findings += 1
        log.warning("           destinations   %s", ", ".join(destinations))

    if token and args.bound_channel and markers:
        body = read(session, "conversations.history", token,
                    {"channel": args.bound_channel, "limit": args.limit})
        if body.get("ok") is True:
            counts, unmatched = arrival_mix(body.get("messages"), markers)
            evidence, why, _present = evidence_verdict(counts, unmatched)
            (log.warning if evidence == "mixed" else log.info)(
                "arrival    %-14s %s", evidence, why)
            for dest, n in counts.items():
                log.info("           %-14s %d message(s)", dest, n)
            if evidence == "mixed":
                findings += 1
        else:
            log.warning("arrival    unavailable    conversations.history answered %s",
                        body.get("error"))
    else:
        log.info("arrival    skipped        pass --markers and a token to corroborate "
                 "from the channel itself")

    if not findings:
        log.info("verdict    clean          no send tries to choose a channel a webhook "
                 "cannot choose")
        return 0
    log.warning("verdict    %d finding(s)", findings)
    log.warning("  repair: move to chat.postMessage with a bot token and an explicit "
                "channel id per message, which reaches any channel the bot is in")
    log.warning("  repair: if webhooks must stay, create one per destination and route "
                "on your side, accepting one bearer secret per room")
    log.warning("  repair: delete the channel field from the payloads either way; it "
                "reads as intent and carries none")
    log.warning("  note:   nothing was sent to any webhook URL to establish this")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-webhook-routing.mjs",
"js": '''/**
 * Find out whether your webhook routing collapsed into a single channel.
 *
 * Read only, and nothing is sent to any webhook URL. The obvious probe is to
 * send one message with a channel field and see where it lands, which puts a
 * message into a real channel in front of real people. The two readings here
 * answer the same question with no audience: what the sending code intends,
 * and what the bound channel actually received.
 *
 * Two reads: conversations.info to name the bound channel, and
 * conversations.history to see whose traffic is arriving in it.
 */
import { readFile } from 'node:fs/promises';

const API = 'https://slack.com/api/';

// Fields a custom integration webhook honoured and an app based one does not.
export const LEGACY_OVERRIDE_KEYS = ['username', 'icon_emoji', 'icon_url'];

// Channel ids are upper case and start with one of these.
export const ID_PREFIXES = ['C', 'G', 'D'];

/** Which fields in this webhook payload no longer do anything? Pure. */
export function payloadOverrides(payload) {
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)) {
    return [['not-an-object', 'a webhook payload is a JSON object and this is not one, '
      + 'so nothing about its routing can be read']];
  }
  const out = [];
  if ('channel' in payload) {
    out.push(['channel-override', `channel=${payload.channel} is inert on an app based `
      + 'webhook: the destination was fixed when the webhook was created']);
  }
  for (const key of LEGACY_OVERRIDE_KEYS) {
    if (key in payload) {
      out.push(['legacy-override', `${key} comes from the same custom integration era `
        + 'as the channel override and should not be depended on']);
    }
  }
  return out;
}

/**
 * Reduce a channel reference to [kind, value]. Pure.
 * Kinds are id, name and empty. Names fold case and lose the leading hash.
 * An id is recognised by shape: nine characters or more, upper case,
 * alphanumeric, beginning with C, G or D, and carrying at least one digit.
 * The digit is what keeps a shouted channel name out of the id branch.
 */
export function normaliseChannelReference(ref) {
  const text = String(ref ?? '').trim();
  if (!text) return ['empty', ''];
  const alnum = [...text].every((c) => /[a-z0-9]/i.test(c));
  const hasDigit = [...text].some((c) => c >= '0' && c <= '9');
  if (text.length >= 9 && ID_PREFIXES.includes(text[0]) && text === text.toUpperCase()
    && alnum && hasDigit) {
    return ['id', text];
  }
  return ['name', text.replace(/^#+/, '').toLowerCase()];
}

/** Does this reference name the channel the webhook is bound to? Pure. */
export function sameDestination(ref, boundId, boundName) {
  const [kind, value] = normaliseChannelReference(ref);
  if (kind === 'empty') return false;
  if (kind === 'id') return value === String(boundId ?? '').trim();
  return value === String(boundName ?? '').trim().replace(/^#+/, '').toLowerCase();
}

/**
 * How many destinations does the code ask for, and how many exist? Pure.
 * Returns [state, detail, destinations]; no-override, aligned, misdirected,
 * collapsed.
 */
export function fanoutVerdict(sends, boundId, boundName) {
  const destinations = [];
  for (const send of sends ?? []) {
    const ref = (send && typeof send === 'object') ? send.channel : send;
    const [kind, value] = normaliseChannelReference(ref);
    if (kind === 'empty') continue;
    const key = kind === 'id' ? value : `#${value}`;
    if (!destinations.includes(key)) destinations.push(key);
  }
  if (!destinations.length) {
    return ['no-override', 'no send sets a channel field, which is the only correct '
      + 'shape for an app based webhook', destinations];
  }
  if (destinations.length > 1) {
    return ['collapsed', `${destinations.length} distinct destinations are asked for `
      + 'and one channel receives all of them', destinations];
  }
  if (sameDestination(destinations[0], boundId, boundName)) {
    return ['aligned', 'the only destination asked for is the channel the webhook is '
      + 'bound to, so the field is inert but harmless', destinations];
  }
  return ['misdirected', `every message is addressed to ${destinations[0]} and every `
    + `message lands in ${boundName || boundId || 'the bound channel'}`, destinations];
}

/**
 * Whose traffic is in the bound channel? Pure.
 * The first destination whose marker matches wins, in the order given.
 * Returns [counts, unmatched].
 */
export function arrivalMix(messages, markers) {
  const counts = {};
  for (const dest of Object.keys(markers ?? {})) counts[dest] = 0;
  let unmatched = 0;
  for (const m of messages ?? []) {
    const text = String(m?.text ?? '').toLowerCase();
    let hit = null;
    for (const [dest, subs] of Object.entries(markers ?? {})) {
      if ((subs ?? []).some((s) => text.includes(String(s).toLowerCase()))) {
        hit = dest;
        break;
      }
    }
    if (hit === null) unmatched += 1;
    else counts[hit] += 1;
  }
  return [counts, unmatched];
}

/** Turn the arrival counts into the corroboration, or into nothing. Pure. */
export function evidenceVerdict(counts, unmatched) {
  const present = Object.entries(counts ?? {})
    .filter(([, n]) => n).map(([d]) => d).sort();
  if (present.length > 1) {
    return ['mixed', `${present.join(', ')} traffic all arrived in one channel`,
      present];
  }
  if (present.length === 1) {
    return ['single', `only ${present[0]} traffic is present, which is what a correctly `
      + 'bound webhook looks like', present];
  }
  return ['none', `no marker matched any of the ${Number(unmatched)} messages read; `
    + 'widen the sample or correct the markers', present];
}

function arg(args, name, fallback = '') {
  const i = args.indexOf(name);
  return i === -1 ? fallback : args[i + 1];
}

async function read(method, token, params = {}) {
  const qs = new URLSearchParams(params).toString();
  const r = await fetch(`${API}${method}${qs ? `?${qs}` : ''}`,
    { headers: { Authorization: `Bearer ${token}` } });
  try {
    return await r.json();
  } catch {
    return { ok: false, error: 'unparseable_body' };
  }
}

async function main() {
  const args = process.argv.slice(2);
  const sends = JSON.parse(await readFile(arg(args, '--sends'), 'utf8'));
  const markers = JSON.parse(arg(args, '--markers', '{}'));
  const boundChannel = arg(args, '--bound-channel');
  const tokenEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
  const limit = arg(args, '--limit', '200');
  const token = process.env[tokenEnv];
  let boundName = arg(args, '--bound-name');
  let findings = 0;

  if (token && boundChannel && !boundName) {
    const info = await read('conversations.info', token, { channel: boundChannel });
    if (info.ok === true) boundName = `#${info.channel?.name ?? ''}`;
    else {
      console.warn('bound      unavailable    conversations.info answered '
        + `${info.error}`);
    }
  }
  console.log(`bound      ${(boundChannel || 'unknown').padEnd(14)} `
    + `${boundName || 'name not resolved'}, from the install record`);

  for (const send of sends) {
    for (const [code, why] of payloadOverrides(send.payload ?? send)) {
      console.warn(`override   ${code.padEnd(16)} ${send.name ?? 'unnamed'}: ${why}`);
      findings += 1;
    }
  }

  const [state, detail, destinations] = fanoutVerdict(
    sends.map((s) => s.payload ?? s), boundChannel, boundName);
  const emit = (state === 'no-override' || state === 'aligned')
    ? console.log : console.warn;
  emit(`fanout     ${state.padEnd(14)} ${detail}`);
  if (state === 'collapsed' || state === 'misdirected') {
    findings += 1;
    console.warn(`           destinations   ${destinations.join(', ')}`);
  }

  if (token && boundChannel && Object.keys(markers).length) {
    const body = await read('conversations.history', token,
      { channel: boundChannel, limit });
    if (body.ok === true) {
      const [counts, unmatched] = arrivalMix(body.messages, markers);
      const [evidence, why] = evidenceVerdict(counts, unmatched);
      (evidence === 'mixed' ? console.warn : console.log)(
        `arrival    ${evidence.padEnd(14)} ${why}`);
      for (const [dest, n] of Object.entries(counts)) {
        console.log(`           ${dest.padEnd(14)} ${n} message(s)`);
      }
      if (evidence === 'mixed') findings += 1;
    } else {
      console.warn('arrival    unavailable    conversations.history answered '
        + `${body.error}`);
    }
  } else {
    console.log('arrival    skipped        pass --markers and a token to corroborate '
      + 'from the channel itself');
  }

  if (!findings) {
    console.log('verdict    clean          no send tries to choose a channel a webhook '
      + 'cannot choose');
    return;
  }
  console.warn(`verdict    ${findings} finding(s)`);
  console.warn('  repair: move to chat.postMessage with a bot token and an explicit '
    + 'channel id per message, which reaches any channel the bot is in');
  console.warn('  repair: if webhooks must stay, create one per destination and route '
    + 'on your side, accepting one bearer secret per room');
  console.warn('  repair: delete the channel field from the payloads either way; it '
    + 'reads as intent and carries none');
  console.warn('  note:   nothing was sent to any webhook URL to establish this');
  process.exitCode = 1;
}

// Only run when invoked directly, so importing this module in the tests does
// not execute main().
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "No webhook URL appears in these fixtures at all, which is worth noticing on its own: the whole diagnosis runs on the destinations your code asks for and the history of one channel, and neither of those needs the credential. The assertions that carry the note are the counting ones &mdash; one inert <code>channel</code> field naming the bound channel is <code>aligned</code> and four distinct values are <code>collapsed</code> &mdash; and the pair that make a <code>#name</code> and a <code>C&hellip;</code> id comparable, including the case that catches a shouted channel name being mistaken for an id.",
"test_py_file": "test_slack_webhook_routing.py",
"test_py": '''from slack_webhook_routing import (
    arrival_mix, evidence_verdict, fanout_verdict, normalise_channel_reference,
    payload_overrides, same_destination,
)

BOUND_ID = "C07AB12CD"
BOUND_NAME = "#alerts"

MARKERS = {"#db-oncall": ["pg-primary"], "#releases": ["deployed"],
           "#sec-ops": ["cve-"]}


def msg(text):
    return {"text": text}


def test_a_channel_field_is_named_as_inert_rather_than_as_an_error():
    codes = [c for c, _w in payload_overrides({"text": "hi", "channel": "#db-oncall"})]
    assert codes == ["channel-override"]


def test_the_other_custom_integration_fields_are_listed_beside_it():
    codes = [c for c, _w in payload_overrides(
        {"text": "hi", "username": "deploybot", "icon_emoji": ":rocket:"})]
    assert codes == ["legacy-override", "legacy-override"]


def test_a_payload_with_no_overrides_has_nothing_to_say():
    assert payload_overrides({"text": "hi"}) == []


def test_something_that_is_not_an_object_is_refused_before_it_is_read():
    assert payload_overrides(["text"])[0][0] == "not-an-object"


def test_a_channel_id_is_recognised_by_shape():
    assert normalise_channel_reference(BOUND_ID) == ("id", BOUND_ID)


def test_a_shouted_channel_name_is_not_mistaken_for_an_id():
    kind, value = normalise_channel_reference("DEPLOYMENTS")
    assert kind == "name"
    assert value == "deployments"


def test_a_name_loses_its_hash_and_its_case():
    assert normalise_channel_reference("#DB-Oncall") == ("name", "db-oncall")


def test_an_id_and_a_name_both_resolve_against_the_binding():
    assert same_destination(BOUND_ID, BOUND_ID, BOUND_NAME) is True
    assert same_destination("#Alerts", BOUND_ID, BOUND_NAME) is True
    assert same_destination("#db-oncall", BOUND_ID, BOUND_NAME) is False
    assert same_destination("", BOUND_ID, BOUND_NAME) is False


def test_code_that_sets_no_channel_field_is_the_correct_shape():
    state, _detail, dests = fanout_verdict([{"text": "hi"}], BOUND_ID, BOUND_NAME)
    assert state == "no-override"
    assert dests == []


def test_one_field_naming_the_bound_channel_is_inert_but_harmless():
    state, _detail, _dests = fanout_verdict([{"channel": "#alerts"}],
                                            BOUND_ID, BOUND_NAME)
    assert state == "aligned"


def test_one_field_naming_somewhere_else_is_misdirected_and_names_both():
    state, detail, _dests = fanout_verdict([{"channel": "#db-oncall"}],
                                           BOUND_ID, BOUND_NAME)
    assert state == "misdirected"
    assert "#db-oncall" in detail and "#alerts" in detail


def test_four_destinations_are_reported_as_collapsed_with_the_count():
    sends = [{"channel": "#db-oncall"}, {"channel": "#releases"},
             {"channel": "#sec-ops"}, {"channel": "#alerts"}]
    state, detail, dests = fanout_verdict(sends, BOUND_ID, BOUND_NAME)
    assert state == "collapsed"
    assert "4" in detail
    assert len(dests) == 4


def test_the_same_destination_twice_is_counted_once():
    sends = [{"channel": "#db-oncall"}, {"channel": "#DB-Oncall"}]
    state, _detail, dests = fanout_verdict(sends, BOUND_ID, BOUND_NAME)
    assert dests == ["#db-oncall"]
    assert state == "misdirected"


def test_the_first_matching_marker_wins_so_two_runs_agree():
    counts, unmatched = arrival_mix(
        [msg("pg-primary failover"), msg("deployed v2.1"), msg("cve-2026-1 patched"),
         msg("good morning")], MARKERS)
    assert counts == {"#db-oncall": 1, "#releases": 1, "#sec-ops": 1}
    assert unmatched == 1


def test_matching_folds_case():
    counts, _unmatched = arrival_mix([msg("PG-Primary failover")], MARKERS)
    assert counts["#db-oncall"] == 1


def test_several_streams_in_one_channel_is_the_corroboration():
    counts, _u = arrival_mix([msg("pg-primary down"), msg("deployed v3")], MARKERS)
    state, detail, present = evidence_verdict(counts, 0)
    assert state == "mixed"
    assert present == ["#db-oncall", "#releases"]
    assert "#db-oncall" in detail


def test_one_stream_is_what_a_correctly_bound_webhook_looks_like():
    counts, _u = arrival_mix([msg("deployed v3"), msg("deployed v4")], MARKERS)
    assert evidence_verdict(counts, 0)[0] == "single"


def test_no_marker_matching_is_a_statement_about_the_markers():
    counts, unmatched = arrival_mix([msg("hello"), msg("world")], MARKERS)
    state, detail, _present = evidence_verdict(counts, unmatched)
    assert state == "none"
    assert "2" in detail
''',
"test_js_file": "slack-webhook-routing.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  arrivalMix, evidenceVerdict, fanoutVerdict, normaliseChannelReference,
  payloadOverrides, sameDestination,
} from './slack-webhook-routing.mjs';

const BOUND_ID = 'C07AB12CD';
const BOUND_NAME = '#alerts';

const MARKERS = {
  '#db-oncall': ['pg-primary'],
  '#releases': ['deployed'],
  '#sec-ops': ['cve-'],
};

const msg = (text) => ({ text });
const codes = (payload) => payloadOverrides(payload).map(([c]) => c);

test('a channel field is named as inert rather than as an error', () => {
  assert.deepEqual(codes({ text: 'hi', channel: '#db-oncall' }), ['channel-override']);
});

test('the other custom integration fields are listed beside it', () => {
  assert.deepEqual(codes({ text: 'hi', username: 'deploybot', icon_emoji: ':rocket:' }),
    ['legacy-override', 'legacy-override']);
});

test('a payload with no overrides has nothing to say', () => {
  assert.deepEqual(payloadOverrides({ text: 'hi' }), []);
});

test('something that is not an object is refused before it is read', () => {
  assert.equal(payloadOverrides(['text'])[0][0], 'not-an-object');
});

test('a channel id is recognised by shape', () => {
  assert.deepEqual(normaliseChannelReference(BOUND_ID), ['id', BOUND_ID]);
});

test('a shouted channel name is not mistaken for an id', () => {
  assert.deepEqual(normaliseChannelReference('DEPLOYMENTS'), ['name', 'deployments']);
});

test('a name loses its hash and its case', () => {
  assert.deepEqual(normaliseChannelReference('#DB-Oncall'), ['name', 'db-oncall']);
});

test('an id and a name both resolve against the binding', () => {
  assert.equal(sameDestination(BOUND_ID, BOUND_ID, BOUND_NAME), true);
  assert.equal(sameDestination('#Alerts', BOUND_ID, BOUND_NAME), true);
  assert.equal(sameDestination('#db-oncall', BOUND_ID, BOUND_NAME), false);
  assert.equal(sameDestination('', BOUND_ID, BOUND_NAME), false);
});

test('code that sets no channel field is the correct shape', () => {
  const [state, , dests] = fanoutVerdict([{ text: 'hi' }], BOUND_ID, BOUND_NAME);
  assert.equal(state, 'no-override');
  assert.deepEqual(dests, []);
});

test('one field naming the bound channel is inert but harmless', () => {
  assert.equal(fanoutVerdict([{ channel: '#alerts' }], BOUND_ID, BOUND_NAME)[0],
    'aligned');
});

test('one field naming somewhere else is misdirected and names both', () => {
  const [state, detail] = fanoutVerdict([{ channel: '#db-oncall' }],
    BOUND_ID, BOUND_NAME);
  assert.equal(state, 'misdirected');
  assert.equal(detail.includes('#db-oncall') && detail.includes('#alerts'), true);
});

test('four destinations are reported as collapsed with the count', () => {
  const sends = [{ channel: '#db-oncall' }, { channel: '#releases' },
    { channel: '#sec-ops' }, { channel: '#alerts' }];
  const [state, detail, dests] = fanoutVerdict(sends, BOUND_ID, BOUND_NAME);
  assert.equal(state, 'collapsed');
  assert.equal(detail.includes('4'), true);
  assert.equal(dests.length, 4);
});

test('the same destination twice is counted once', () => {
  const [state, , dests] = fanoutVerdict(
    [{ channel: '#db-oncall' }, { channel: '#DB-Oncall' }], BOUND_ID, BOUND_NAME);
  assert.deepEqual(dests, ['#db-oncall']);
  assert.equal(state, 'misdirected');
});

test('the first matching marker wins so two runs agree', () => {
  const [counts, unmatched] = arrivalMix([msg('pg-primary failover'),
    msg('deployed v2.1'), msg('cve-2026-1 patched'), msg('good morning')], MARKERS);
  assert.deepEqual(counts, { '#db-oncall': 1, '#releases': 1, '#sec-ops': 1 });
  assert.equal(unmatched, 1);
});

test('matching folds case', () => {
  const [counts] = arrivalMix([msg('PG-Primary failover')], MARKERS);
  assert.equal(counts['#db-oncall'], 1);
});

test('several streams in one channel is the corroboration', () => {
  const [counts] = arrivalMix([msg('pg-primary down'), msg('deployed v3')], MARKERS);
  const [state, detail, present] = evidenceVerdict(counts, 0);
  assert.equal(state, 'mixed');
  assert.deepEqual(present, ['#db-oncall', '#releases']);
  assert.equal(detail.includes('#db-oncall'), true);
});

test('one stream is what a correctly bound webhook looks like', () => {
  const [counts] = arrivalMix([msg('deployed v3'), msg('deployed v4')], MARKERS);
  assert.equal(evidenceVerdict(counts, 0)[0], 'single');
});

test('no marker matching is a statement about the markers', () => {
  const [counts, unmatched] = arrivalMix([msg('hello'), msg('world')], MARKERS);
  const [state, detail] = evidenceVerdict(counts, unmatched);
  assert.equal(state, 'none');
  assert.equal(detail.includes('2'), true);
});
''',
"faq": [
 ("The channel override definitely used to work. What changed?",
  "The integration model did. Custom integrations, configured per workspace before the app model existed, honoured a channel field in the webhook body, and that is what every tutorial written before 2016 demonstrates. An incoming webhook created through a Slack app is bound to the single channel chosen when it was created, and the field no longer chooses anything. Nothing about your code changed; the URL underneath it did, usually during a migration presented as a credential swap."),
 ("Can I create one webhook per channel and route on my side?",
  "Yes, and it works. Be clear about what it costs. Each URL is a separate bearer credential that can post into your workspace as your app, with a separate lifetime, and Slack has no method that lists them for you. Each one dies independently when the person who authorised it is deactivated. Four destinations means four secrets to inventory and rotate, and the rotation has to reach every system holding each one. It is the right answer when the sending system genuinely cannot hold a token, and a poor answer for anything that can."),
 ("Why not just send one test message with a channel field and see where it lands?",
  "Because that probe posts into a real channel, and to be conclusive it has to post twice: once addressed elsewhere and once as a control. Somebody then has to explain both messages. The two readings this script makes reach the same conclusion with no audience: the destinations your code asks for come from your code, and where the messages went comes from the bound channel's own history."),
 ("Our sends carry a channel field and everything looks fine. Is that a finding?",
  "It is the aligned verdict, and it is worth fixing anyway. The field reads as intent to every future maintainer, so the first person who needs a second destination will add a second value to it and change nothing. Deleting it costs a line and makes the binding visible in the one place somebody will look."),
 ("Is this the same as posting to a channel the bot is not in?",
  "No, and they are easy to tell apart because one produces an error and this one does not. not_in_channel comes back from chat.postMessage with a bot token and names the problem: the bot has to be invited. A webhook has no membership question at all, because the binding was made at creation and the app was joined to that channel then. If you are getting an error, you are on the bot token path and that is a different note. If you are getting ok and the messages are in the wrong room, you are here."),
],
"related": [
 ("/slack/channel-name-instead-of-id/", "the other way a channel reference goes wrong"),
 ("/slack/incoming-webhook-dead/", "the same webhook, after its install went away"),
 ("/slack/archived-channel-target/", "when the one bound channel gets frozen"),
],
"citations": [CITE_WEBHOOKS, CITE_SO_WEBHOOK_CHANNEL, CITE_POST_MESSAGE, CITE_HISTORY],
})
GUIDES.append({
"slug": "webhook-invalid-payload",
"title": "invalid_payload: the webhook body stopped being JSON",
"description": "Shell interpolation puts a quote in the body and it stops parsing. Sort the captured payload locally, as bytes, without sending anything to a webhook.",
"h1": "invalid_payload: the webhook body stopped being JSON",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack webhook invalid_payload 400",
             "slack incoming webhook curl invalid_payload",
             "slack webhook no_text 400",
             "slack webhook json escaping shell",
             "slack webhook content-type application/json"],
"deps": "Python 3.9+, or Node.js 18+; no token and no network access at all, only the payload bytes your sender produced",
"lead": "The release notification has worked for two years. Then one release goes out with a commit message that reads <code>fix: don't drop the \"retry\" header</code>, and the notification does not arrive. The pipeline is green. The step that sends the message exited zero. Slack answered <code>400</code> with the plain text body <code>invalid_payload</code>, into a <code>curl</code> that was never given <code>--fail</code>, and the body of that response went to <code>/dev/null</code> along with the message.</p><p>The webhook is fine. The channel is fine. The app is fine. What left the machine was not JSON, because a double quote from a commit message was interpolated straight into a JSON string literal and closed it three characters early.",
"short_answer": """<p><code>400 invalid_payload</code> means the bytes you sent did not parse as JSON, and Slack will not tell you where. It is almost always string interpolation: a shell script, a CI YAML step or a template that builds the JSON as text and substitutes a value containing a double quote, a newline, a backslash or a control character. The close sibling is <code>400 no_text</code>, which means the JSON parsed perfectly and carried no message.</p>
<p>This is one of the few places on Slack where the HTTP status is the truth. The Web API answers <code>200 OK</code> for almost every failure and hides it in the body as <code>ok: false</code>; a webhook answers a real <code>400</code>, <code>401</code>, <code>403</code>, <code>404</code> or <code>410</code> with a short plain text reason. Checking the status here actually works, which makes the usual cause of a silent failure not Slack's answer but a client that never reads it.</p>
<p>The check below is deliberately narrow and entirely local. It takes the bytes your sender produced, decodes them, tries to parse them, and if that fails it names which of the interpolation fingerprints is present. If it parses, it reads the top level object against the incoming webhook envelope, which is not the same contract as a Web API call and not the same contract as Block Kit. It makes <strong>no network call of any kind</strong>: nothing to Slack's API and, above all, nothing to the webhook, because sending the payload to find out whether it is valid delivers it into a channel if it happens to be valid.</p>""",
"problem": """<p>Building JSON by hand works until it does not, and the day it stops is decided by somebody else's typing. A commit message, a test failure summary, a stack trace, a customer name, a filename with an apostrophe in it: any of these interpolated into a JSON literal will eventually contain a character that ends the string early. The code that built the payload has no bug in it that a review would catch, because the bug is a value that did not exist when the code was written.</p>
<p>The shell is where this concentrates, for two reasons. The first is that a shell has no JSON type, so the payload is a string with holes in it and there is no layer that could have escaped anything. The second is that <code>curl -d</code> sends <code>application/x-www-form-urlencoded</code> unless you tell it otherwise, so even a perfectly built body can arrive as the wrong kind of thing. Multi-line values make it worse: a raw newline inside a JSON string is not legal JSON, and a log fragment pasted into a payload is a stack of them.</p>
<p>Then there is the failure with a green tick. <code>curl</code> exits <code>0</code> on a <code>400</code> unless you pass <code>--fail</code>, so a CI step that sends a notification succeeds while the notification does not exist. The one class of message most likely to be built this way &mdash; a build alert, a deploy notice, a cron summary &mdash; is also the one nobody misses individually, so the fault is discovered weeks later by somebody asking a question about last month.</p>
<p>And there is the near miss, which is worse than the failure. A payload that ends up truncated at the first quote still parses, and still posts. So the message arrives, it is just wrong: cut off mid sentence, carrying a stray backslash, showing a raw <code>${VERSION}</code> that never got expanded, or holding a fragment of JSON that leaked out of the value it was supposed to be in. Nothing anywhere reports a problem, because as far as every layer is concerned there was none.</p>""",
"why": """<p><strong>This is the only script in this section that makes no network call at all, and that is the design.</strong> The natural way to test a payload is to send it, and for a webhook that means delivering it into a channel if it turns out to be valid, which is the outcome you were trying to avoid finding out about. Validating locally costs nothing, needs no credential, runs in a pre-commit hook, and cannot post anything to anybody.</p>
<p><strong>It reads bytes rather than an object, because by the time you have an object the bug is gone.</strong> A payload built by a serializer is correct by construction and does not need this. The payload that needs it is a string built by a shell, and the only honest way to inspect it is as the bytes that left the machine: with the byte order mark a Windows editor added, the encoding, and the exact newline that ended the string early.</p>
<p><strong>The string scanner is naive in exactly the way a parser is.</strong> An unescaped quote closes a string here as it does in a real parser, which is what makes the leftover text between the string literals a usable signal. Text sitting outside every string literal that is not JSON punctuation is the fingerprint of a quote that got in, and it is a much more direct statement than a parser offset, which points at where the damage was noticed rather than at where it began.</p>
<p><strong>The envelope check is not a Block Kit check, and the line between them is the point of this note.</strong> Whether a <code>section</code> block has a <code>text</code> object with a legal <code>type</code> is Block Kit's contract and it is validated in its own note. What is checked here is the layer above: whether the top level is an object at all, whether it carries a message in <code>text</code>, <code>blocks</code> or <code>attachments</code>, and whether it is carrying keys that belong to a different surface entirely.</p>
<p><strong>Keys from other surfaces are their own finding, because they are silent.</strong> A body carrying <code>token</code>, <code>ts</code> or <code>as_user</code> is a <code>chat.postMessage</code> call that somebody pointed at a webhook; a body carrying <code>response_type</code> or <code>replace_original</code> is a reply meant for a <code>response_url</code>. Both parse. Both post. Both do less than their author thinks, and no error is produced by either.</p>
<p><strong>The status table is here because the statuses are real.</strong> Everywhere else in this section the advice is to stop trusting the HTTP status and read the body. On a webhook the status is meaningful and the body is four plain words, and the whole set fits in one function: what <code>invalid_payload</code>, <code>no_text</code>, <code>invalid_token</code>, <code>no_service</code>, <code>channel_is_archived</code>, <code>action_prohibited</code> and <code>posting_to_general_channel_denied</code> each mean, and which of them are a different note.</p>""",
"steps": [
 {"h": "Capture the bytes, not the object",
  "body": """<p>Have the sender write the exact body it is about to send to a file, before it sends it. In a shell that is a redirect; in CI it is an artefact. The bytes are the evidence, and reconstructing them afterwards from the code loses the one value that caused the problem.</p>"""},
 {"h": "Decode before you parse",
  "body": """<p><code>decode_body</code> reports <code>empty</code>, <code>byte-order-mark</code> and <code>not-utf8</code> before JSON is attempted. A file saved by a Windows editor with a byte order mark fails to parse for a reason that has nothing to do with the content, and a JSON parser's error message will not mention it.</p>"""},
 {"h": "Parse, and if it fails, name the fingerprint",
  "body": """<p><code>parse_probe</code> gives you the line and column. <code>interpolation_fingerprints</code> gives you the cause: a raw newline inside a string, a control character, an unterminated string, a trailing comma, single quotes, Python literals, an unexpanded shell variable, an unrendered template, or text sitting outside every string literal, which is what an unescaped quote leaves behind.</p>"""},
 {"h": "Read the envelope, not the blocks",
  "body": """<p><code>envelope_findings</code> checks the layer this surface owns: is the top level an object, does it carry a message at all, are <code>blocks</code> and <code>attachments</code> the right types, and is it carrying keys from the Web API or from a <code>response_url</code> reply. Block structure is a different contract and a different note.</p>"""},
 {"h": "Check the Content-Type you actually sent",
  "body": """<p><code>curl -d</code> sends <code>application/x-www-form-urlencoded</code>. Pass <code>-H 'Content-Type: application/json'</code> and <code>--data-binary @payload.json</code>, and the last of those matters too: <code>-d</code> strips newlines from a file, which is fine for JSON and confusing when you are comparing what you wrote against what was sent.</p>"""},
 {"h": "Stop interpolating, and start checking the status",
  "body": """<p>Build the body with <code>jq -n --arg text &quot;$MSG&quot; '{text: $text}'</code>, <code>json.dumps</code> or <code>JSON.stringify</code>. Then give <code>curl</code> its <code>--fail</code> so that a <code>400</code> becomes a non zero exit, because on this surface, unlike the rest of Slack, the status code tells the truth.</p>"""},
],
"verify": """<p>Run it over the captured body before your sender is allowed to send it. A clean run says the payload parses and the envelope carries a message.</p>
<pre><code class="language-bash">python3 slack_webhook_payload.py --payload captured.json \\
  --content-type application/x-www-form-urlencoded --status 400 --body invalid_payload
# decode     ok             247 byte(s), utf-8
# parse      invalid-json   line 1 column 34: Expecting ',' delimiter
# fingerprint stray-text-outside-string  14 character(s) sit outside every string
#                           literal, which is what an unescaped quote leaves behind
# fingerprint unexpanded-variable  a $NAME sequence survived into the body
# content    form-encoded   this is curl -d's default; the body is not read as JSON
# status     invalid_payload the body did not parse as JSON, and Slack does not say
#                            where
# verdict    3 finding(s)
#   repair: build the body with a serializer and send it with --data-binary
#   note:   nothing was sent anywhere; this file makes no network call at all</code></pre>""",
"code_intro": "There is no HTTP client in this file, in either language, and that is the feature. <code>decode_body</code> reads the captured bytes and reports a byte order mark or a bad encoding before JSON is attempted; <code>parse_probe</code> tries the parse and returns the position when it fails; <code>interpolation_fingerprints</code> scans for the ten shapes a hand built body takes when it stops being JSON, using a string scanner that closes a string on an unescaped quote exactly as a parser does; <code>envelope_findings</code> reads the top level object against the incoming webhook contract, which is neither the Web API's nor Block Kit's; <code>content_type_finding</code> and <code>explain_status</code> cover the header and the four word answer. Every one of them is pure.",
"py_file": "slack_webhook_payload.py",
"py": '''"""Sort a captured incoming webhook body before anything is sent to a webhook.

This file makes no network call of any kind. That is deliberate and it is the
whole point: the obvious way to find out whether a payload is valid is to send
it to the webhook, and if it turns out to be valid that delivers it into a real
channel in front of real people. There is no dry run mode on a webhook and no
validation endpoint. So the payload is read here, locally, from the bytes your
sender produced.

The scope is narrow on purpose. This covers the layer a webhook owns: whether
the bytes are JSON at all, and whether the top level object is a legal incoming
webhook envelope. It does not validate Block Kit structure, which is a
different contract with its own errors and its own note.
"""
import argparse
import codecs
import json
import logging
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_webhook_payload")

# What may legally appear outside a JSON string literal, once the three bare
# words are taken out. Anything else out there is text that escaped from a
# string, which is what an unescaped quote leaves behind.
JSON_PUNCTUATION = set(" \\t\\r\\n{}[]:,-+.eE0123456789")
BARE_WORDS = ("true", "false", "null")

# The incoming webhook envelope. Four separate vocabularies end up in these
# bodies and only the first one does anything.
ENVELOPE_KEYS = ("text", "blocks", "attachments", "thread_ts", "mrkdwn",
                 "unfurl_links", "unfurl_media")
LEGACY_OVERRIDE_KEYS = ("channel", "username", "icon_emoji", "icon_url")
RESPONSE_URL_KEYS = ("response_type", "replace_original", "delete_original")
WEB_API_KEYS = ("token", "ts", "as_user", "reply_broadcast", "link_names", "parse",
                "metadata")


def decode_body(raw):
    """Turn captured bytes into text, reporting what a parser will not. Pure.

    Returns (text, notes). A byte order mark and a bad encoding both make a
    perfectly sensible looking file fail to parse, and a JSON parser's message
    will mention neither.
    """
    data = raw if isinstance(raw, (bytes, bytearray)) else str(raw or "").encode("utf-8")
    notes = []
    if not data:
        return ("", ["empty"])
    if bytes(data[:3]) == codecs.BOM_UTF8:
        notes.append("byte-order-mark")
        data = data[3:]
    try:
        text = bytes(data).decode("utf-8")
    except UnicodeDecodeError:
        return ("", notes + ["not-utf8"])
    if not text.strip():
        notes.append("blank")
    return (text, notes)


def parse_probe(text):
    """Try the parse. Pure. Returns (state, detail, value).

    States are ok and invalid-json. The detail carries the position, which is
    where the damage was noticed rather than where it began - which is exactly
    why the fingerprints below exist.
    """
    if not str(text or "").strip():
        return ("invalid-json", "the body is empty, which is not a JSON document", None)
    try:
        return ("ok", "the body parses as JSON", json.loads(text))
    except ValueError as exc:
        return ("invalid-json", str(exc), None)


def _string_spans(text):
    """Where the JSON string literals are. Pure. Returns (spans, unterminated).

    Naive in one direction on purpose: an unescaped quote closes a string here
    exactly as it does in a real parser, which is what makes the text left over
    between the spans a usable signal rather than noise.
    """
    spans = []
    inside = False
    escaped = False
    start = 0
    for i, ch in enumerate(text):
        if inside:
            if escaped:
                escaped = False
            elif ch == "\\\\":
                escaped = True
            elif ch == '"':
                inside = False
                spans.append((start, i))
        elif ch == '"':
            inside = True
            start = i + 1
    if inside:
        spans.append((start, len(text)))
    return (spans, inside)


def _outside(text, spans):
    """Everything that is not inside a string literal, quotes excluded. Pure."""
    out = []
    prev = 0
    for a, b in spans:
        out.append(text[prev:max(prev, a - 1)])
        prev = b + 1
    out.append(text[prev:])
    return "".join(out)


def interpolation_fingerprints(text):
    """Name the ways a hand built body stops being JSON. Pure.

    Returns [(code, why), ...] in a fixed order, so two runs over the same body
    produce the same report.
    """
    out = []
    spans, unterminated = _string_spans(text)
    inside = [text[a:b] for a, b in spans]
    if any(chr(10) in s or chr(13) in s for s in inside):
        out.append(("raw-newline-in-string",
                    "a literal newline sits inside a string; JSON has no multi line "
                    "strings, and a log fragment pasted into a payload is a stack of "
                    "them"))
    if any(any(ord(c) < 32 and c not in (chr(10), chr(13)) for c in s) for s in inside):
        out.append(("control-character",
                    "a control character sits inside a string, usually a tab or a "
                    "terminal escape that came in with captured output"))
    if unterminated:
        out.append(("unterminated-string",
                    "the body ends inside a string literal, which is what truncation "
                    "and a missing closing quote both look like"))
    outside = _outside(text, spans)
    if any(word in outside for word in ("True", "False", "None")):
        out.append(("python-literals",
                    "True, False or None appear outside a string; JSON spells those "
                    "true, false and null, and a Python repr is not JSON"))
    if "'" in outside:
        out.append(("single-quoted",
                    "an apostrophe sits outside every string; JSON has no single "
                    "quoted strings or keys"))
    scrub = outside.lower()
    for word in BARE_WORDS:
        scrub = scrub.replace(word, "")
    stray = "".join(ch for ch in scrub if ch not in JSON_PUNCTUATION and ch != "'")
    if stray:
        out.append(("stray-text-outside-string",
                    "%d character(s) sit outside every string literal, which is what "
                    "an unescaped quote leaves behind: the value closed its string "
                    "early and the rest spilled out" % len(stray)))
    j = 0
    while j < len(outside):
        if outside[j] == ",":
            k = j + 1
            while k < len(outside) and outside[k].isspace():
                k += 1
            if k < len(outside) and outside[k] in "}]":
                out.append(("trailing-comma",
                            "a comma is followed by a closing brace or bracket; a "
                            "loop that appends an item and a separator every time "
                            "leaves one behind"))
                break
        j += 1
    for i, ch in enumerate(text):
        if ch == "$" and i + 1 < len(text) and (text[i + 1].isalpha()
                                                or text[i + 1] == "_"):
            out.append(("unexpanded-variable",
                        "a dollar sign followed by a name survived into the body, so "
                        "a shell or template variable was never substituted"))
            break
    if "{{" in text or "${" in text:
        out.append(("unrendered-template",
                    "a template delimiter survived into the body, so the templating "
                    "layer either did not run or did not know about this value"))
    return out


def envelope_findings(value):
    """Read the top level object against the incoming webhook contract. Pure.

    Not a Block Kit check. Whether a section block has a legal text object is a
    different contract with its own error and its own note; what is read here
    is the envelope those blocks travel in.
    """
    if not isinstance(value, dict):
        return [("not-an-object",
                 "the body parses and the top level is a %s; an incoming webhook takes "
                 "a JSON object" % type(value).__name__)]
    keys = list(value.keys())
    out = []
    if keys == ["payload"]:
        out.append(("payload-wrapper",
                    "the body is a single payload key, which is the form encoded shape "
                    "where the JSON is the value of a payload field; sent as JSON it is "
                    "an envelope with no message in it"))
    text = value.get("text")
    if "text" in keys and not isinstance(text, str):
        out.append(("text-not-a-string",
                    "text is a %s; a number or an object here is a serializer that was "
                    "handed the wrong thing" % type(text).__name__))
    if "blocks" in keys and not isinstance(value.get("blocks"), list):
        out.append(("blocks-not-a-list", "blocks has to be an array of blocks"))
    if "attachments" in keys and not isinstance(value.get("attachments"), list):
        out.append(("attachments-not-a-list",
                    "attachments has to be an array of attachments"))
    carries = (bool(str(text or "").strip()) or bool(value.get("blocks"))
               or bool(value.get("attachments")))
    if not carries:
        out.append(("no-text",
                    "nothing in text, blocks or attachments carries a message, which "
                    "is the 400 no_text answer rather than the invalid_payload one"))
    if value.get("blocks") and not str(text or "").strip():
        out.append(("no-fallback-text",
                    "blocks with no top level text leaves the push notification, the "
                    "sidebar preview and the screen reader with nothing to read"))
    for key in LEGACY_OVERRIDE_KEYS:
        if key in keys:
            out.append(("legacy-override",
                        "%s is a custom integration field; on an app based webhook it "
                        "does not choose anything" % key))
    for key in RESPONSE_URL_KEYS:
        if key in keys:
            out.append(("response-url-key",
                        "%s belongs to a reply sent to a response_url, not to an "
                        "incoming webhook, and is ignored here" % key))
    for key in WEB_API_KEYS:
        if key in keys:
            out.append(("web-api-key",
                        "%s is a chat.postMessage argument; a webhook body is not a "
                        "Web API request and this key does nothing" % key))
    known = (set(ENVELOPE_KEYS) | set(LEGACY_OVERRIDE_KEYS) | set(RESPONSE_URL_KEYS)
             | set(WEB_API_KEYS) | {"payload"})
    for key in keys:
        if key not in known:
            out.append(("unknown-key",
                        "%s is not part of the incoming webhook envelope and is "
                        "ignored" % key))
    return out


def content_type_finding(header):
    """What the header you actually sent does to the body. Pure."""
    value = str(header or "").split(";")[0].strip().lower()
    if not value:
        return ("no-content-type",
                "no Content-Type was recorded; curl -d sends "
                "application/x-www-form-urlencoded unless you say otherwise")
    if value == "application/json":
        return ("ok", "application/json is what a JSON body should be sent as")
    if value == "application/x-www-form-urlencoded":
        return ("form-encoded",
                "this is curl -d's default; the body is then looked for in a payload "
                "field rather than read as JSON")
    return ("wrong-type", "%s is not application/json" % value)


def explain_status(status, body):
    """What a webhook's real HTTP answer means. Pure. Returns (code, repair).

    Worth stating plainly because it is the exception in this section: the Web
    API answers 200 with ok false for almost every failure, and a webhook
    answers a real status with a short plain text reason. Checking the status
    works here.
    """
    code = str(status or "").strip()
    reason = str(body or "").strip().lower()
    if code == "200" and reason in ("ok", ""):
        return ("delivered", "the message was accepted and posted into the bound "
                             "channel")
    if reason == "invalid_payload":
        return ("invalid_payload", "the body did not parse as JSON, and Slack does not "
                                   "say where; build it with a serializer and send it "
                                   "with --data-binary")
    if reason in ("no_text", "missing_text_or_fallback_or_attachments"):
        return ("no_text", "the body parsed and carried no message; guard the empty "
                           "case before sending rather than after")
    if reason == "invalid_token":
        return ("invalid_token", "the URL is not one Slack recognises, which usually "
                                 "means it was truncated, re-wrapped or copied with a "
                                 "trailing character")
    if reason in ("no_service", "no_active_hooks"):
        return ("no_service", "the webhook itself is gone: uninstalled, revoked, "
                              "deleted, or authorised by somebody who has left")
    if reason == "channel_is_archived":
        return ("channel_is_archived", "the bound channel was archived, and a webhook "
                                       "cannot be pointed at a different one")
    if reason == "action_prohibited":
        return ("action_prohibited", "an administrator has restricted what this app is "
                                     "allowed to do in that channel")
    if reason == "posting_to_general_channel_denied":
        return ("posting_to_general_channel_denied",
                "the webhook is bound to the workspace default channel, where posting "
                "is restricted")
    if code == "429":
        return ("rate_limited", "one message per second per webhook is the shape to "
                                "aim for; slow down rather than retrying immediately")
    if code.startswith("5"):
        return ("server_error", "a Slack side failure; retry with backoff and check "
                                "the status page before changing anything")
    return ("unrecognised", "no entry for status %s with body %s"
            % (code or "none", body or "none"))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--payload", required=True,
                    help="file holding the exact bytes your sender produced")
    ap.add_argument("--content-type", default="",
                    help="the Content-Type header you actually sent, if you have it")
    ap.add_argument("--status", default="",
                    help="the HTTP status the webhook answered, if you captured it")
    ap.add_argument("--body", default="",
                    help="the plain text response body, if you captured it")
    args = ap.parse_args()

    with open(args.payload, "rb") as fh:
        raw = fh.read()
    findings = 0

    text, notes = decode_body(raw)
    for note in notes:
        log.warning("decode     %-14s %s", note, {
            "empty": "the captured file is empty; the sender wrote nothing",
            "blank": "the body is whitespace only",
            "byte-order-mark": "a byte order mark leads the file, which no JSON parser "
                               "accepts and no parser error mentions",
            "not-utf8": "the bytes are not valid UTF-8, so the body cannot be read as "
                        "JSON at all",
        }.get(note, note))
        findings += 1
    if not notes:
        log.info("decode     ok             %d byte(s), utf-8", len(raw))

    state, detail, value = parse_probe(text)
    if state == "ok":
        log.info("parse      ok             %s", detail)
    else:
        log.warning("parse      invalid-json   %s", detail)
        findings += 1

    for code, why in interpolation_fingerprints(text):
        log.warning("fingerprint %-14s %s", code, why)
        findings += 1

    if state == "ok":
        for code, why in envelope_findings(value):
            log.warning("envelope   %-14s %s", code, why)
            findings += 1

    code, why = content_type_finding(args.content_type)
    (log.info if code == "ok" else log.warning)("content    %-14s %s", code, why)
    if code != "ok":
        findings += 1

    if args.status or args.body:
        code, why = explain_status(args.status, args.body)
        (log.info if code == "delivered" else log.warning)(
            "status     %-14s %s", code, why)

    if not findings:
        log.info("verdict    clean          the body parses and the envelope carries a "
                 "message")
        return 0
    log.warning("verdict    %d finding(s)", findings)
    log.warning("  repair: build the body with a serializer - jq -n --arg, json.dumps "
                "or JSON.stringify - and never by interpolating into a JSON literal")
    log.warning("  repair: send it with --data-binary and an explicit "
                "Content-Type: application/json header")
    log.warning("  repair: give curl --fail so a 400 becomes a non zero exit; on this "
                "surface, unlike the rest of Slack, the status code tells the truth")
    log.warning("  note:   nothing was sent anywhere to establish this; this file "
                "makes no network call at all")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-webhook-payload.mjs",
"js": '''/**
 * Sort a captured incoming webhook body before anything is sent to a webhook.
 *
 * This file makes no network call of any kind, and there is no HTTP client in
 * it. That is deliberate: the obvious way to find out whether a payload is
 * valid is to send it to the webhook, and if it turns out to be valid that
 * delivers it into a real channel in front of real people. There is no dry run
 * mode on a webhook and no validation endpoint.
 *
 * The scope is narrow on purpose. This covers the layer a webhook owns:
 * whether the bytes are JSON at all, and whether the top level object is a
 * legal incoming webhook envelope. Block Kit structure is a different contract
 * with its own errors and its own note.
 */
import { readFile } from 'node:fs/promises';

// What may legally appear outside a JSON string literal, once the three bare
// words are taken out. Anything else out there escaped from a string.
export const JSON_PUNCTUATION = new Set([...' \\t\\r\\n{}[]:,-+.eE0123456789']);
export const BARE_WORDS = ['true', 'false', 'null'];

// The incoming webhook envelope. Four vocabularies end up in these bodies and
// only the first one does anything.
export const ENVELOPE_KEYS = ['text', 'blocks', 'attachments', 'thread_ts', 'mrkdwn',
  'unfurl_links', 'unfurl_media'];
export const LEGACY_OVERRIDE_KEYS = ['channel', 'username', 'icon_emoji', 'icon_url'];
export const RESPONSE_URL_KEYS = ['response_type', 'replace_original',
  'delete_original'];
export const WEB_API_KEYS = ['token', 'ts', 'as_user', 'reply_broadcast', 'link_names',
  'parse', 'metadata'];

/**
 * Turn captured bytes into text, reporting what a parser will not. Pure.
 * Returns [text, notes].
 */
export function decodeBody(raw) {
  const data = (raw instanceof Uint8Array) ? raw
    : new TextEncoder().encode(String(raw ?? ''));
  const notes = [];
  if (!data.length) return ['', ['empty']];
  let body = data;
  if (data[0] === 0xef && data[1] === 0xbb && data[2] === 0xbf) {
    notes.push('byte-order-mark');
    body = data.subarray(3);
  }
  let text;
  try {
    text = new TextDecoder('utf-8', { fatal: true }).decode(body);
  } catch {
    return ['', notes.concat(['not-utf8'])];
  }
  if (!text.trim()) notes.push('blank');
  return [text, notes];
}

/** Try the parse. Pure. Returns [state, detail, value]; ok or invalid-json. */
export function parseProbe(text) {
  if (!String(text ?? '').trim()) {
    return ['invalid-json', 'the body is empty, which is not a JSON document', null];
  }
  try {
    return ['ok', 'the body parses as JSON', JSON.parse(text)];
  } catch (err) {
    return ['invalid-json', err.message, null];
  }
}

/**
 * Where the JSON string literals are. Pure. Returns [spans, unterminated].
 * Naive in one direction on purpose: an unescaped quote closes a string here
 * exactly as it does in a real parser.
 */
function stringSpans(text) {
  const spans = [];
  let inside = false;
  let escaped = false;
  let start = 0;
  for (let i = 0; i < text.length; i += 1) {
    const ch = text[i];
    if (inside) {
      if (escaped) escaped = false;
      else if (ch === '\\\\') escaped = true;
      else if (ch === '"') { inside = false; spans.push([start, i]); }
    } else if (ch === '"') {
      inside = true;
      start = i + 1;
    }
  }
  if (inside) spans.push([start, text.length]);
  return [spans, inside];
}

/** Everything that is not inside a string literal, quotes excluded. Pure. */
function outsideText(text, spans) {
  const out = [];
  let prev = 0;
  for (const [a, b] of spans) {
    out.push(text.slice(prev, Math.max(prev, a - 1)));
    prev = b + 1;
  }
  out.push(text.slice(prev));
  return out.join('');
}

/** Name the ways a hand built body stops being JSON. Pure, in a fixed order. */
export function interpolationFingerprints(text) {
  const out = [];
  const [spans, unterminated] = stringSpans(text);
  const inside = spans.map(([a, b]) => text.slice(a, b));
  const NL = String.fromCharCode(10);
  const CR = String.fromCharCode(13);
  if (inside.some((s) => s.includes(NL) || s.includes(CR))) {
    out.push(['raw-newline-in-string', 'a literal newline sits inside a string; JSON '
      + 'has no multi line strings, and a log fragment pasted into a payload is a '
      + 'stack of them']);
  }
  if (inside.some((s) => [...s].some((c) => c.charCodeAt(0) < 32
    && c !== NL && c !== CR))) {
    out.push(['control-character', 'a control character sits inside a string, usually '
      + 'a tab or a terminal escape that came in with captured output']);
  }
  if (unterminated) {
    out.push(['unterminated-string', 'the body ends inside a string literal, which is '
      + 'what truncation and a missing closing quote both look like']);
  }
  const outside = outsideText(text, spans);
  if (['True', 'False', 'None'].some((w) => outside.includes(w))) {
    out.push(['python-literals', 'True, False or None appear outside a string; JSON '
      + 'spells those true, false and null, and a Python repr is not JSON']);
  }
  if (outside.includes("'")) {
    out.push(['single-quoted', 'an apostrophe sits outside every string; JSON has no '
      + 'single quoted strings or keys']);
  }
  let scrub = outside.toLowerCase();
  for (const word of BARE_WORDS) scrub = scrub.split(word).join('');
  const stray = [...scrub].filter((c) => !JSON_PUNCTUATION.has(c) && c !== "'").length;
  if (stray) {
    out.push(['stray-text-outside-string', `${stray} character(s) sit outside every `
      + 'string literal, which is what an unescaped quote leaves behind: the value '
      + 'closed its string early and the rest spilled out']);
  }
  for (let j = 0; j < outside.length; j += 1) {
    if (outside[j] !== ',') continue;
    let k = j + 1;
    while (k < outside.length && /\\s/.test(outside[k])) k += 1;
    if (k < outside.length && (outside[k] === '}' || outside[k] === ']')) {
      out.push(['trailing-comma', 'a comma is followed by a closing brace or bracket; '
        + 'a loop that appends an item and a separator every time leaves one behind']);
      break;
    }
  }
  for (let i = 0; i < text.length; i += 1) {
    if (text[i] === '$' && i + 1 < text.length && /[A-Za-z_]/.test(text[i + 1])) {
      out.push(['unexpanded-variable', 'a dollar sign followed by a name survived into '
        + 'the body, so a shell or template variable was never substituted']);
      break;
    }
  }
  if (text.includes('{{') || text.includes('${')) {
    out.push(['unrendered-template', 'a template delimiter survived into the body, so '
      + 'the templating layer either did not run or did not know about this value']);
  }
  return out;
}

/**
 * Read the top level object against the incoming webhook contract. Pure.
 * Not a Block Kit check: this is the envelope those blocks travel in.
 */
export function envelopeFindings(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    const kind = Array.isArray(value) ? 'array' : typeof value;
    return [['not-an-object', `the body parses and the top level is a ${kind}; an `
      + 'incoming webhook takes a JSON object']];
  }
  const keys = Object.keys(value);
  const out = [];
  if (keys.length === 1 && keys[0] === 'payload') {
    out.push(['payload-wrapper', 'the body is a single payload key, which is the form '
      + 'encoded shape where the JSON is the value of a payload field; sent as JSON it '
      + 'is an envelope with no message in it']);
  }
  const text = value.text;
  if (keys.includes('text') && typeof text !== 'string') {
    out.push(['text-not-a-string', `text is a ${typeof text}; a number or an object `
      + 'here is a serializer that was handed the wrong thing']);
  }
  if (keys.includes('blocks') && !Array.isArray(value.blocks)) {
    out.push(['blocks-not-a-list', 'blocks has to be an array of blocks']);
  }
  if (keys.includes('attachments') && !Array.isArray(value.attachments)) {
    out.push(['attachments-not-a-list', 'attachments has to be an array of attachments']);
  }
  const carries = Boolean(String(text ?? '').trim())
    || Boolean(value.blocks?.length) || Boolean(value.attachments?.length);
  if (!carries) {
    out.push(['no-text', 'nothing in text, blocks or attachments carries a message, '
      + 'which is the 400 no_text answer rather than the invalid_payload one']);
  }
  if (value.blocks?.length && !String(text ?? '').trim()) {
    out.push(['no-fallback-text', 'blocks with no top level text leaves the push '
      + 'notification, the sidebar preview and the screen reader with nothing to read']);
  }
  for (const key of LEGACY_OVERRIDE_KEYS) {
    if (keys.includes(key)) {
      out.push(['legacy-override', `${key} is a custom integration field; on an app `
        + 'based webhook it does not choose anything']);
    }
  }
  for (const key of RESPONSE_URL_KEYS) {
    if (keys.includes(key)) {
      out.push(['response-url-key', `${key} belongs to a reply sent to a response_url, `
        + 'not to an incoming webhook, and is ignored here']);
    }
  }
  for (const key of WEB_API_KEYS) {
    if (keys.includes(key)) {
      out.push(['web-api-key', `${key} is a chat.postMessage argument; a webhook body `
        + 'is not a Web API request and this key does nothing']);
    }
  }
  const known = new Set([...ENVELOPE_KEYS, ...LEGACY_OVERRIDE_KEYS,
    ...RESPONSE_URL_KEYS, ...WEB_API_KEYS, 'payload']);
  for (const key of keys) {
    if (!known.has(key)) {
      out.push(['unknown-key', `${key} is not part of the incoming webhook envelope `
        + 'and is ignored']);
    }
  }
  return out;
}

/** What the header you actually sent does to the body. Pure. */
export function contentTypeFinding(header) {
  const value = String(header ?? '').split(';')[0].trim().toLowerCase();
  if (!value) {
    return ['no-content-type', 'no Content-Type was recorded; curl -d sends '
      + 'application/x-www-form-urlencoded unless you say otherwise'];
  }
  if (value === 'application/json') {
    return ['ok', 'application/json is what a JSON body should be sent as'];
  }
  if (value === 'application/x-www-form-urlencoded') {
    return ['form-encoded', "this is curl -d's default; the body is then looked for in "
      + 'a payload field rather than read as JSON'];
  }
  return ['wrong-type', `${value} is not application/json`];
}

/**
 * What a webhook's real HTTP answer means. Pure. Returns [code, repair].
 * The exception in this section: here the status code tells the truth.
 */
export function explainStatus(status, body) {
  const code = String(status ?? '').trim();
  const reason = String(body ?? '').trim().toLowerCase();
  if (code === '200' && (reason === 'ok' || reason === '')) {
    return ['delivered', 'the message was accepted and posted into the bound channel'];
  }
  if (reason === 'invalid_payload') {
    return ['invalid_payload', 'the body did not parse as JSON, and Slack does not say '
      + 'where; build it with a serializer and send it with --data-binary'];
  }
  if (reason === 'no_text' || reason === 'missing_text_or_fallback_or_attachments') {
    return ['no_text', 'the body parsed and carried no message; guard the empty case '
      + 'before sending rather than after'];
  }
  if (reason === 'invalid_token') {
    return ['invalid_token', 'the URL is not one Slack recognises, which usually means '
      + 'it was truncated, re-wrapped or copied with a trailing character'];
  }
  if (reason === 'no_service' || reason === 'no_active_hooks') {
    return ['no_service', 'the webhook itself is gone: uninstalled, revoked, deleted, '
      + 'or authorised by somebody who has left'];
  }
  if (reason === 'channel_is_archived') {
    return ['channel_is_archived', 'the bound channel was archived, and a webhook '
      + 'cannot be pointed at a different one'];
  }
  if (reason === 'action_prohibited') {
    return ['action_prohibited', 'an administrator has restricted what this app is '
      + 'allowed to do in that channel'];
  }
  if (reason === 'posting_to_general_channel_denied') {
    return ['posting_to_general_channel_denied', 'the webhook is bound to the '
      + 'workspace default channel, where posting is restricted'];
  }
  if (code === '429') {
    return ['rate_limited', 'one message per second per webhook is the shape to aim '
      + 'for; slow down rather than retrying immediately'];
  }
  if (code.startsWith('5')) {
    return ['server_error', 'a Slack side failure; retry with backoff and check the '
      + 'status page before changing anything'];
  }
  return ['unrecognised', `no entry for status ${code || 'none'} with body `
    + `${body || 'none'}`];
}

const DECODE_WHY = {
  empty: 'the captured file is empty; the sender wrote nothing',
  blank: 'the body is whitespace only',
  'byte-order-mark': 'a byte order mark leads the file, which no JSON parser accepts '
    + 'and no parser error mentions',
  'not-utf8': 'the bytes are not valid UTF-8, so the body cannot be read as JSON at all',
};

function arg(args, name, fallback = '') {
  const i = args.indexOf(name);
  return i === -1 ? fallback : args[i + 1];
}

async function main() {
  const args = process.argv.slice(2);
  const raw = new Uint8Array(await readFile(arg(args, '--payload')));
  let findings = 0;

  const [text, notes] = decodeBody(raw);
  for (const note of notes) {
    console.warn(`decode     ${note.padEnd(14)} ${DECODE_WHY[note] ?? note}`);
    findings += 1;
  }
  if (!notes.length) {
    console.log(`decode     ok             ${raw.length} byte(s), utf-8`);
  }

  const [state, detail, value] = parseProbe(text);
  if (state === 'ok') console.log(`parse      ok             ${detail}`);
  else { console.warn(`parse      invalid-json   ${detail}`); findings += 1; }

  for (const [code, why] of interpolationFingerprints(text)) {
    console.warn(`fingerprint ${code.padEnd(14)} ${why}`);
    findings += 1;
  }

  if (state === 'ok') {
    for (const [code, why] of envelopeFindings(value)) {
      console.warn(`envelope   ${code.padEnd(14)} ${why}`);
      findings += 1;
    }
  }

  const [ctCode, ctWhy] = contentTypeFinding(arg(args, '--content-type'));
  (ctCode === 'ok' ? console.log : console.warn)(
    `content    ${ctCode.padEnd(14)} ${ctWhy}`);
  if (ctCode !== 'ok') findings += 1;

  const status = arg(args, '--status');
  const body = arg(args, '--body');
  if (status || body) {
    const [code, why] = explainStatus(status, body);
    (code === 'delivered' ? console.log : console.warn)(
      `status     ${code.padEnd(14)} ${why}`);
  }

  if (!findings) {
    console.log('verdict    clean          the body parses and the envelope carries a '
      + 'message');
    return;
  }
  console.warn(`verdict    ${findings} finding(s)`);
  console.warn('  repair: build the body with a serializer - jq -n --arg, json.dumps '
    + 'or JSON.stringify - and never by interpolating into a JSON literal');
  console.warn('  repair: send it with --data-binary and an explicit '
    + 'Content-Type: application/json header');
  console.warn('  repair: give curl --fail so a 400 becomes a non zero exit; on this '
    + 'surface, unlike the rest of Slack, the status code tells the truth');
  console.warn('  note:   nothing was sent anywhere to establish this; this file makes '
    + 'no network call at all');
  process.exitCode = 1;
}

// Only run when invoked directly, so importing this module in the tests does
// not execute main().
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The fixtures are built with <code>chr(10)</code> and <code>chr(7)</code> rather than written out, because a raw newline and a control character inside a JSON string are the two faults this check exists for and a source file that contained them literally would not survive being edited. The assertion that carries the note is <code>stray-text-outside-string</code>: an unescaped quote closes the string early, the rest of the value spills into the space between the literals, and counting the characters out there names the cause where a parser offset only names the symptom. The envelope tests pin the line this note will not cross &mdash; <code>blocks</code> has to be an array and nothing here looks inside it.",
"test_py_file": "test_slack_webhook_payload.py",
"test_py": '''import codecs

from slack_webhook_payload import (
    content_type_finding, decode_body, envelope_findings, explain_status,
    interpolation_fingerprints, parse_probe,
)

GOOD = '{"text": "deployed v2.1"}'
UNESCAPED = '{"text": "he said "hi" there"}'
RAW_NEWLINE = '{"text": "line one' + chr(10) + 'line two"}'
CONTROL = '{"text": "a' + chr(7) + 'b"}'


def codes(text):
    return [c for c, _w in interpolation_fingerprints(text)]


def envelope(value):
    return [c for c, _w in envelope_findings(value)]


def test_a_clean_body_decodes_parses_and_says_nothing():
    text, notes = decode_body(GOOD.encode("utf-8"))
    assert notes == []
    assert parse_probe(text)[0] == "ok"
    assert codes(text) == []


def test_a_byte_order_mark_is_named_before_the_parser_is_asked():
    text, notes = decode_body(codecs.BOM_UTF8 + GOOD.encode("utf-8"))
    assert notes == ["byte-order-mark"]
    assert parse_probe(text)[0] == "ok"


def test_bytes_that_are_not_utf8_never_reach_the_parser():
    text, notes = decode_body(bytes([0xff, 0xfe, 0x00]))
    assert notes == ["not-utf8"]
    assert text == ""


def test_an_empty_capture_is_empty_rather_than_invalid():
    assert decode_body(b"")[1] == ["empty"]


def test_an_unescaped_quote_leaves_text_outside_every_string():
    assert parse_probe(UNESCAPED)[0] == "invalid-json"
    assert "stray-text-outside-string" in codes(UNESCAPED)


def test_a_raw_newline_inside_a_string_is_named_as_itself():
    assert parse_probe(RAW_NEWLINE)[0] == "invalid-json"
    assert "raw-newline-in-string" in codes(RAW_NEWLINE)


def test_a_control_character_that_came_in_with_captured_output():
    assert "control-character" in codes(CONTROL)


def test_a_body_that_ends_mid_string_is_reported_as_truncation():
    assert "unterminated-string" in codes('{"text": "truncated')


def test_a_trailing_comma_from_a_loop_that_appends_a_separator():
    assert "trailing-comma" in codes('{"text": "a", }')


def test_single_quotes_are_not_json_and_are_named_before_the_stray_text():
    found = codes("{'text': 'hi'}")
    assert found.index("single-quoted") < found.index("stray-text-outside-string")


def test_a_python_repr_is_recognised_rather_than_called_stray_text():
    assert "python-literals" in codes('{"ok": True}')


def test_a_shell_variable_that_was_never_substituted():
    assert "unexpanded-variable" in codes('{"text": "deploy $VERSION"}')


def test_a_template_delimiter_that_survived_into_the_body():
    found = codes('{"text": "${{ github.sha }}"}')
    assert "unrendered-template" in found
    assert "unexpanded-variable" not in found


def test_an_envelope_carrying_a_message_has_nothing_to_report():
    assert envelope({"text": "deployed"}) == []


def test_a_body_that_parses_and_carries_nothing_is_the_no_text_case():
    assert envelope({}) == ["no-text"]
    assert envelope({"text": "   "}) == ["no-text"]


def test_blocks_with_no_top_level_text_leaves_the_notification_blank():
    assert envelope({"blocks": [{"type": "divider"}]}) == ["no-fallback-text"]


def test_the_block_array_is_type_checked_and_never_looked_inside():
    assert "blocks-not-a-list" in envelope({"text": "hi", "blocks": "divider"})
    assert envelope({"text": "hi", "blocks": [{"type": "nonsense"}]}) == []


def test_text_that_is_not_a_string_is_a_serializer_handed_the_wrong_thing():
    assert envelope({"text": 42}) == ["text-not-a-string"]


def test_a_top_level_array_is_refused_before_anything_else_is_read():
    assert envelope(["text"]) == ["not-an-object"]


def test_the_form_encoded_wrapper_sent_as_json_is_an_empty_envelope():
    assert envelope({"payload": '{"text": "hi"}'}) == ["payload-wrapper", "no-text"]


def test_keys_from_the_other_three_surfaces_are_each_named():
    assert envelope({"text": "hi", "channel": "#ops"}) == ["legacy-override"]
    assert envelope({"text": "hi", "response_type": "in_channel"}) == ["response-url-key"]
    assert envelope({"text": "hi", "token": "not-a-token"}) == ["web-api-key"]
    assert envelope({"text": "hi", "colour": "red"}) == ["unknown-key"]


def test_the_default_curl_content_type_is_the_finding_people_miss():
    assert content_type_finding("application/x-www-form-urlencoded")[0] == "form-encoded"
    assert content_type_finding("application/json; charset=utf-8")[0] == "ok"
    assert content_type_finding("")[0] == "no-content-type"
    assert content_type_finding("text/plain")[0] == "wrong-type"


def test_the_status_table_separates_the_body_from_the_webhook():
    assert explain_status(400, "invalid_payload")[0] == "invalid_payload"
    assert explain_status(400, "no_text")[0] == "no_text"
    assert explain_status(404, "no_active_hooks")[0] == "no_service"
    assert explain_status(410, "channel_is_archived")[0] == "channel_is_archived"
    assert explain_status(401, "invalid_token")[0] == "invalid_token"
    assert explain_status(200, "ok")[0] == "delivered"


def test_an_answer_with_no_entry_says_so_rather_than_guessing():
    assert explain_status(418, "teapot")[0] == "unrecognised"
''',
"test_js_file": "slack-webhook-payload.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  contentTypeFinding, decodeBody, envelopeFindings, explainStatus,
  interpolationFingerprints, parseProbe,
} from './slack-webhook-payload.mjs';

const GOOD = '{"text": "deployed v2.1"}';
const UNESCAPED = '{"text": "he said "hi" there"}';
const RAW_NEWLINE = `{"text": "line one${String.fromCharCode(10)}line two"}`;
const CONTROL = `{"text": "a${String.fromCharCode(7)}b"}`;

const bytes = (s) => new TextEncoder().encode(s);
const codes = (text) => interpolationFingerprints(text).map(([c]) => c);
const envelope = (value) => envelopeFindings(value).map(([c]) => c);

test('a clean body decodes, parses and says nothing', () => {
  const [text, notes] = decodeBody(bytes(GOOD));
  assert.deepEqual(notes, []);
  assert.equal(parseProbe(text)[0], 'ok');
  assert.deepEqual(codes(text), []);
});

test('a byte order mark is named before the parser is asked', () => {
  const withBom = new Uint8Array([0xef, 0xbb, 0xbf, ...bytes(GOOD)]);
  const [text, notes] = decodeBody(withBom);
  assert.deepEqual(notes, ['byte-order-mark']);
  assert.equal(parseProbe(text)[0], 'ok');
});

test('bytes that are not utf8 never reach the parser', () => {
  const [text, notes] = decodeBody(new Uint8Array([0xff, 0xfe, 0x00]));
  assert.deepEqual(notes, ['not-utf8']);
  assert.equal(text, '');
});

test('an empty capture is empty rather than invalid', () => {
  assert.deepEqual(decodeBody(new Uint8Array([]))[1], ['empty']);
});

test('an unescaped quote leaves text outside every string', () => {
  assert.equal(parseProbe(UNESCAPED)[0], 'invalid-json');
  assert.equal(codes(UNESCAPED).includes('stray-text-outside-string'), true);
});

test('a raw newline inside a string is named as itself', () => {
  assert.equal(parseProbe(RAW_NEWLINE)[0], 'invalid-json');
  assert.equal(codes(RAW_NEWLINE).includes('raw-newline-in-string'), true);
});

test('a control character that came in with captured output', () => {
  assert.equal(codes(CONTROL).includes('control-character'), true);
});

test('a body that ends mid string is reported as truncation', () => {
  assert.equal(codes('{"text": "truncated').includes('unterminated-string'), true);
});

test('a trailing comma from a loop that appends a separator', () => {
  assert.equal(codes('{"text": "a", }').includes('trailing-comma'), true);
});

test('single quotes are not json and are named before the stray text', () => {
  const found = codes("{'text': 'hi'}");
  assert.equal(found.indexOf('single-quoted')
    < found.indexOf('stray-text-outside-string'), true);
});

test('a python repr is recognised rather than called stray text', () => {
  assert.equal(codes('{"ok": True}').includes('python-literals'), true);
});

test('a shell variable that was never substituted', () => {
  assert.equal(codes('{"text": "deploy $VERSION"}').includes('unexpanded-variable'),
    true);
});

test('a template delimiter that survived into the body', () => {
  const found = codes('{"text": "${{ github.sha }}"}');
  assert.equal(found.includes('unrendered-template'), true);
  assert.equal(found.includes('unexpanded-variable'), false);
});

test('an envelope carrying a message has nothing to report', () => {
  assert.deepEqual(envelope({ text: 'deployed' }), []);
});

test('a body that parses and carries nothing is the no_text case', () => {
  assert.deepEqual(envelope({}), ['no-text']);
  assert.deepEqual(envelope({ text: '   ' }), ['no-text']);
});

test('blocks with no top level text leaves the notification blank', () => {
  assert.deepEqual(envelope({ blocks: [{ type: 'divider' }] }), ['no-fallback-text']);
});

test('the block array is type checked and never looked inside', () => {
  assert.equal(envelope({ text: 'hi', blocks: 'divider' })
    .includes('blocks-not-a-list'), true);
  assert.deepEqual(envelope({ text: 'hi', blocks: [{ type: 'nonsense' }] }), []);
});

test('text that is not a string is a serializer handed the wrong thing', () => {
  assert.deepEqual(envelope({ text: 42 }), ['text-not-a-string']);
});

test('a top level array is refused before anything else is read', () => {
  assert.deepEqual(envelope(['text']), ['not-an-object']);
});

test('the form encoded wrapper sent as json is an empty envelope', () => {
  assert.deepEqual(envelope({ payload: '{"text": "hi"}' }),
    ['payload-wrapper', 'no-text']);
});

test('keys from the other three surfaces are each named', () => {
  assert.deepEqual(envelope({ text: 'hi', channel: '#ops' }), ['legacy-override']);
  assert.deepEqual(envelope({ text: 'hi', response_type: 'in_channel' }),
    ['response-url-key']);
  assert.deepEqual(envelope({ text: 'hi', token: 'not-a-token' }), ['web-api-key']);
  assert.deepEqual(envelope({ text: 'hi', colour: 'red' }), ['unknown-key']);
});

test('the default curl content type is the finding people miss', () => {
  assert.equal(contentTypeFinding('application/x-www-form-urlencoded')[0],
    'form-encoded');
  assert.equal(contentTypeFinding('application/json; charset=utf-8')[0], 'ok');
  assert.equal(contentTypeFinding('')[0], 'no-content-type');
  assert.equal(contentTypeFinding('text/plain')[0], 'wrong-type');
});

test('the status table separates the body from the webhook', () => {
  assert.equal(explainStatus(400, 'invalid_payload')[0], 'invalid_payload');
  assert.equal(explainStatus(400, 'no_text')[0], 'no_text');
  assert.equal(explainStatus(404, 'no_active_hooks')[0], 'no_service');
  assert.equal(explainStatus(410, 'channel_is_archived')[0], 'channel_is_archived');
  assert.equal(explainStatus(401, 'invalid_token')[0], 'invalid_token');
  assert.equal(explainStatus(200, 'ok')[0], 'delivered');
});

test('an answer with no entry says so rather than guessing', () => {
  assert.equal(explainStatus(418, 'teapot')[0], 'unrecognised');
});
''',
"faq": [
 ("Is this not just the same as validating Block Kit before sending?",
  "No, and the boundary is the reason this note exists separately. Block Kit validation asks whether a section block has a legal text object, whether the array is under fifty, whether a field is over its ceiling. All of that assumes you already have a valid JSON document containing an array. This check is the layer underneath: whether the bytes are JSON at all, and whether the top level object is a legal incoming webhook envelope, which is not the same contract as chat.postMessage and not the same contract as a response_url reply. A payload can fail here while every block in it is perfect, because the failure happened in a shell before any block was parsed."),
 ("Why not send the payload to the webhook and read the error?",
  "Because if the payload turns out to be valid, that sends it. A webhook has no dry run mode and no validation endpoint; the only outcomes of the experiment are a 400 that tells you what this script already told you, or a message delivered into a channel in front of people. Running the check locally costs nothing, needs no credential, and can sit in a pre-commit hook or a CI step before the sender is ever reached."),
 ("Slack says invalid_payload but does not say where. Can you do better?",
  "Slightly, and the fingerprints are the better part. A parser offset points at where the damage was noticed, which for an unescaped quote is several characters after where it began. The fingerprints name the cause instead: a raw newline inside a string, a control character, an unterminated string, a trailing comma, single quotes, a Python repr, a variable that was never substituted, a template delimiter that survived, and text sitting outside every string literal, which is the signature of a quote that got in. The position is still printed, because sometimes it is enough on its own."),
 ("Our message arrives but it is truncated at the first quote. Nothing errored.",
  "That is the near miss, and it is worse than the failure because no layer anywhere reports it. The interpolated value closed its string early, the rest of it happened to land somewhere the parser tolerated, and the message posted. Run this over a body you know was accepted: the stray text and unterminated string fingerprints both fire on payloads that parse, precisely so that the ones which nearly broke are visible before the one that does."),
 ("Should we check the HTTP status? Everywhere else this section says not to.",
  "Here you should, and that is the one place in this section where that advice reverses. The Web API answers 200 with ok: false for almost every failure, so the status is meaningless. Incoming webhooks answer real statuses with a short plain text reason: 400 invalid_payload, 400 no_text, 401 invalid_token, 403 action_prohibited, 404 no_service, 410 channel_is_archived. Give curl its --fail flag and the failure becomes a non zero exit instead of a green build with no message in it."),
],
"related": [
 ("/slack/invalid-blocks/", "the layer above, once the body is valid JSON"),
 ("/slack/no-text-empty-message/", "the message that rendered to nothing"),
 ("/slack/http-200-ok-false/", "why the rest of Slack works the other way round"),
],
"citations": [CITE_SO_INVALID_PAYLOAD, CITE_SO_CURL_JSON, CITE_WEBHOOKS, CITE_BLOCK_KIT],
})
GUIDES.append({
"slug": "legacy-workflow-steps",
"title": "Steps from Apps was retired and the manifest still lists it",
"description": "Slack retired Steps from Apps on 26 September 2024. The workflows stopped, the events stopped, and the dead declarations are still in your live manifest.",
"h1": "Steps from Apps was retired and the manifest still lists it",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack steps from apps retired",
             "slack workflow_step_execute not firing",
             "slack legacy workflow steps migration",
             "slack workflow.steps:execute scope",
             "slack workflow builder custom step app"],
"deps": "Python 3.9+ with requests, or Node.js 18+; an app configuration token with app_configurations:read for the manifest, any bot token so the granted scope header can be read, and read access to the source that registers your handlers",
"lead": "Somebody in operations files a ticket saying the onboarding workflow has stopped creating tickets. You look at the app. It is installed, the token works, the handler is deployed, the tests pass, and the logs contain nothing at all &mdash; not an error, not a request, nothing. The workflow itself, opened in Workflow Builder, is not running either.</p><p>Nothing broke. On 26 September 2024 Slack retired <strong>Steps from Apps</strong>, the legacy way an app contributed a custom step to Workflow Builder. Every workflow containing one stopped running that day, the steps stopped working, and the events that would have told your app about it stopped being deliverable. The only trace left is a set of declarations sitting in your live app manifest describing a feature that no longer exists.",
"short_answer": """<p>Legacy <strong>Steps from Apps</strong> were retired on <strong>26 September 2024</strong>. From that date, workflows containing a legacy step stopped executing, the steps themselves stopped working, and the five associated events &mdash; <code>workflow_step_execute</code>, <code>workflow_published</code>, <code>workflow_unpublished</code>, <code>workflow_deleted</code> and <code>workflow_step_deleted</code> &mdash; could no longer be subscribed to. There is no automated migration for a legacy step or for the workflows that used one. The replacement is a custom function that Workflow Builder can call, and the workflows themselves have to be rebuilt by hand by the people who own them.</p>
<p>What makes this hard to find is that a retirement is not an error. Nothing returns a failure code, because nothing is called. The handler that would have logged something is simply never reached, and an app whose only Workflow Builder integration was a legacy step looks completely healthy from every angle except the one where somebody's workflow used to run.</p>
<p>The evidence that survives is configuration. A live manifest still carrying <code>features.workflow_steps</code>, retired event names still in <code>settings.event_subscriptions.bot_events</code>, and <code>workflow.steps:execute</code> still in the granted scope list are all dead declarations, and all three are readable. There is no API that will tell you which Workflow Builder workflows referenced your steps or how often they ran, so the manifest is what you get.</p>""",
"problem": """<p>The awkward part of a retirement is that it produces the same signals as success. A handler that is never invoked writes nothing, so the logs are clean. The app is installed, so <code>auth.test</code> is fine. The scope is granted, so nothing is refused. Your monitoring, which watches for errors, has nothing to report, and would have nothing to report if the feature had never shipped at all.</p>
<p>The people who feel it are not on your team. A Workflow Builder workflow is built by whoever needed it, often in operations or people ops, out of steps offered by apps somebody else installed. When the step disappears, the workflow stops, and the person affected has no reason to connect that to an app, a retirement or a date. The report arrives weeks later as "the onboarding thing does not work any more", and by then nobody remembers that the onboarding thing had a custom step in it.</p>
<p>Meanwhile the configuration stays exactly as it was. Slack did not strip <code>workflow_steps</code> out of anybody's manifest, and it did not remove the granted scope from installed tokens. So an app can carry a complete, well formed declaration of a feature that has not run since 2024, and that declaration will be faithfully reproduced by every export, copied into every new environment, and reviewed by everyone who reads the manifest as though it described something real.</p>
<p>There is a specific trap in the middle of the migration, too. The modern replacement is a custom function, declared under <code>functions</code>, and it is entirely possible to add one while leaving the legacy declaration in place &mdash; the two do not conflict, and nothing complains. That state looks like progress and is in fact the worst of both: a manifest that claims two capabilities, one of which cannot run, and a set of users who have no way to tell which of your steps in the Workflow Builder picker is the one that works.</p>""",
"why": """<p><strong>This is a configuration read, because there is no traffic read available.</strong> Since the retirement there is no method that enumerates which Workflow Builder workflows call your app's steps, how often they ran, or when they last succeeded. That surface is genuinely closed. So the check goes where the evidence still is: the live manifest, the granted scope header, and your own source.</p>
<p><strong>The retired event names are a fixed list, and a fixed list is checkable.</strong> Five names stopped being subscribable on one date. Their presence in <code>bot_events</code> is not ambiguous and does not need interpretation: it is configuration describing deliveries that will never happen. Listing them individually rather than as a count matters, because a manifest carrying one of them is a different conversation from a manifest carrying all five.</p>
<p><strong>The scope is the one signal that survives on the token rather than in the document.</strong> <code>workflow.steps:execute</code> was only ever granted to apps that implemented legacy steps, so its presence in <code>X-OAuth-Scopes</code> identifies the era of the install regardless of what the manifest currently says. It also survives a manifest edit: clean up the document without reinstalling and the grant stays exactly where it was.</p>
<p><strong>Reading your own source is what separates dead configuration from a dead feature.</strong> A manifest declaration with no handler behind it is leftover paperwork and deleting it costs nothing. A manifest declaration with a maintained handler behind it is a capability somebody still believes in, and the repair is a rebuild rather than a deletion. The two need different conversations, so the check reads both and reports the combination rather than either half.</p>
<p><strong>The half migrated state is called out by name because it is the one that looks finished.</strong> Legacy steps and modern functions can coexist in one manifest with no error, and a team that shipped the replacement without removing the original will read that as done. It is not: the legacy entry is still in the picker's history, still in the document, and still describing something that cannot run.</p>
<p><strong>Everything here is a read, and the write that would fix it is deliberately not made.</strong> <code>apps.manifest.update</code> replaces the whole document, which means a script that "just removes the dead entries" is a script that rewrites your app configuration from a copy it made a moment ago. This one prints what to delete and leaves the deleting to you.</p>""",
"steps": [
 {"h": "Export the live manifest, not the one in the repository",
  "body": """<p><code>apps.manifest.export</code> with an app configuration token returns what Slack is actually running. The repository copy is what you think you shipped, and on this particular feature the two diverge routinely, because the legacy declaration predates whenever the manifest was first checked in.</p>"""},
 {"h": "Look for the legacy feature block",
  "body": """<p><code>features.workflow_steps</code> is the declaration. Each entry has a <code>name</code> and a <code>callback_id</code>, and every one of them is a step that has not been callable since 26 September 2024. The callback ids are worth printing: they are what your handler registrations are keyed on.</p>"""},
 {"h": "List the retired events by name",
  "body": """<p><code>retired_events</code> takes <code>settings.event_subscriptions.bot_events</code> and returns the subset that stopped being subscribable. One of the five is a leftover; all five is an app that was built around this feature.</p>"""},
 {"h": "Read the granted scopes, which the manifest does not cover",
  "body": """<p><code>workflow.steps:execute</code> in <code>X-OAuth-Scopes</code> means the installed token still carries the legacy grant. Cleaning the manifest does not remove it, because a grant only moves when somebody reinstalls, so this is the line that tells you whether the cleanup was finished or only started.</p>"""},
 {"h": "Check whether a handler still exists behind the declaration",
  "body": """<p><code>source_findings</code> looks for the Bolt symbols &mdash; <code>WorkflowStep</code>, <code>workflow_step_execute</code>, a <code>.step(</code> registration &mdash; in the source you point it at. Dead paperwork gets deleted; a maintained handler gets rebuilt, and telling the two apart is the point.</p>"""},
 {"h": "Rebuild as a custom function, and tell the workflow owners",
  "body": """<p>The modern replacement is a custom function that Workflow Builder can call, declared under <code>functions</code> in the manifest. Slack provides no automated migration for either the step or the workflows that used it, so the second half of the repair is not code: it is telling the people whose workflows stopped that they have to rebuild them, which nobody will discover on their own.</p>"""},
],
"verify": """<p>Once the legacy declarations are gone and the app has been reinstalled, run it again. The manifest rows should be empty and the scope row should say the legacy grant is gone.</p>
<pre><code class="language-bash">python3 slack_legacy_workflow_steps.py --app-id A05NW7XQ1 --source ./listeners
# manifest   ok             exported A05NW7XQ1
# manifest   legacy-steps   2 legacy step(s) declared: create_ticket, notify_manager
# manifest   retired-event  workflow_step_execute is subscribed and cannot be delivered
# manifest   retired-event  workflow_step_deleted is subscribed and cannot be delivered
# manifest   no-modern-functions  nothing under functions, so no replacement exists yet
# scopes     legacy-scope   workflow.steps:execute is granted; only legacy step apps
#                           ever held it, and it survives a manifest edit
# source     legacy-handler WorkflowStep appears in ./listeners/onboarding.py
# state      not-started    the legacy feature is declared, granted and still handled
# verdict    6 finding(s)
#   repair: rebuild each step as a custom function Workflow Builder can call
#   repair: tell the workflow owners; Slack provides no automated migration
#   note:   apps.manifest.update would replace the whole document and is not called</code></pre>""",
"code_intro": "Two reads, both GET, and the one method that would fix this is deliberately absent. <code>retired_events</code> holds the five names against your subscription list; <code>manifest_findings</code> reads the legacy feature block, those events and whether a modern replacement exists yet; <code>scope_findings</code> reads the one grant only legacy step apps were ever given, which lives on the token rather than in the document; <code>source_findings</code> looks for the handler symbols in the source you point it at; and <code>migration_state</code> combines the three into the sentence you actually want, which is whether this is leftover paperwork, a half migration, or a feature somebody still maintains.",
"py_file": "slack_legacy_workflow_steps.py",
"py": '''"""Find legacy Steps from Apps configuration left standing after the retirement.

Slack retired legacy Steps from Apps on 26 September 2024. Workflows containing
one stopped running, the steps stopped working, and the five associated events
stopped being subscribable. Nothing about that produced an error, because
nothing was called - which is why the evidence is configuration rather than
traffic. There is no method that enumerates which Workflow Builder workflows
referenced your steps or how often they ran; that surface is closed.

Read only. Two GETs: apps.manifest.export with an app configuration token, and
auth.test with any bot token so the granted scope header can be read. The
method that would fix this, apps.manifest.update, replaces the whole document
from a copy made a moment earlier, and is never called here.
"""
import argparse
import logging
import os
import sys
from pathlib import Path

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_legacy_workflow_steps")

API = "https://slack.com/api/"

RETIREMENT_DATE = "26 September 2024"

# The five events that stopped being subscribable on the retirement date. A
# fixed list, which is what makes this checkable rather than interpretive.
RETIRED_EVENTS = ("workflow_step_execute", "workflow_published",
                  "workflow_unpublished", "workflow_deleted",
                  "workflow_step_deleted")

# Granted only to apps that implemented legacy steps, and it lives on the
# installed token rather than in the manifest, so it survives a document edit.
LEGACY_SCOPE = "workflow.steps:execute"

# Symbols that mean a handler still exists behind the declaration. Deliberately
# few: this is a signal, not a parser, and a false positive costs one look.
LEGACY_SYMBOLS = (
    ("WorkflowStep", "the Bolt legacy step class"),
    ("workflow_step_execute", "a handler for the retired execute event"),
    (".step(", "a Bolt legacy step registration"),
    (LEGACY_SCOPE, "the legacy scope requested in code"),
)


def retired_events(bot_events):
    """Which subscribed events can no longer be delivered? Pure.

    Returned in the order of RETIRED_EVENTS rather than the order of the
    manifest, so two exports of the same app read the same way.
    """
    subscribed = {str(e) for e in (bot_events or [])}
    return [e for e in RETIRED_EVENTS if e in subscribed]


def manifest_findings(manifest):
    """Read a live manifest for configuration the retirement left behind. Pure.

    Returns [(code, why), ...]. Nothing here is an error Slack will ever
    report: it is a document describing a feature that stopped existing.
    """
    doc = (manifest or {}).get("manifest", manifest) or {}
    features = doc.get("features") or {}
    settings = doc.get("settings") or {}
    steps = features.get("workflow_steps") or []
    out = []
    if steps:
        names = [str((s or {}).get("callback_id") or (s or {}).get("name") or "unnamed")
                 for s in steps]
        out.append(("legacy-steps",
                    "%d legacy step(s) declared: %s. None has been callable since %s"
                    % (len(steps), ", ".join(names), RETIREMENT_DATE)))
    bot_events = ((settings.get("event_subscriptions") or {}).get("bot_events")) or []
    for event in retired_events(bot_events):
        out.append(("retired-event",
                    "%s is subscribed and cannot be delivered; it stopped being "
                    "subscribable on %s" % (event, RETIREMENT_DATE)))
    if steps and not (doc.get("functions") or {}):
        out.append(("no-modern-functions",
                    "nothing is declared under functions, so no replacement exists "
                    "yet and the capability is simply gone"))
    return out


def scope_findings(scope_header):
    """Read the granted scope list for the legacy grant. Pure.

    X-OAuth-Scopes is what the installed token actually holds, which is a
    different question from what the manifest asks for. A manifest cleaned up
    without a reinstall leaves this exactly where it was.
    """
    granted = [s.strip() for s in str(scope_header or "").split(",") if s.strip()]
    if LEGACY_SCOPE in granted:
        return [("legacy-scope",
                 "%s is granted on the installed token; only legacy step apps ever "
                 "held it, and it survives a manifest edit because a grant moves only "
                 "when somebody reinstalls" % LEGACY_SCOPE)]
    return []


def source_findings(text, label="source"):
    """Is there still a handler behind the declaration? Pure.

    A declaration with no handler is leftover paperwork and deleting it costs
    nothing. A declaration with a maintained handler is a capability somebody
    still believes in, and the repair is a rebuild. Different conversations,
    so the check reads both halves.
    """
    body = str(text or "")
    return [("legacy-handler", "%s appears in %s" % (symbol, label))
            for symbol, _why in LEGACY_SYMBOLS if symbol in body]


def migration_state(has_legacy_manifest, has_retired_events, has_legacy_scope,
                    has_modern_functions, has_legacy_source):
    """Say in one word where this app actually stands. Pure.

    clean         nothing legacy anywhere.
    migrated      a modern function exists and no legacy trace remains.
    half-migrated the replacement was built and the legacy entry was left in
                  place. This is the state that looks finished and is not.
    source-only   a handler survives with nothing declared. Dead code that no
                  user can reach and no reviewer will question.
    dead-config   declarations and grants with no handler behind them. Delete.
    not-started   declared, granted and still maintained, with no replacement.
    """
    legacy_config = bool(has_legacy_manifest or has_retired_events or has_legacy_scope)
    if not legacy_config and not has_legacy_source:
        return ("migrated" if has_modern_functions else "clean",
                "no legacy Steps from Apps configuration remains")
    if legacy_config and has_modern_functions:
        return ("half-migrated",
                "a modern function is declared and the legacy step was left beside "
                "it; both appear to users and only one can run")
    if not legacy_config and has_legacy_source:
        return ("source-only",
                "a legacy handler survives in source with nothing declared, so it is "
                "dead code no user can reach")
    if legacy_config and not has_legacy_source:
        return ("dead-config",
                "legacy declarations and grants remain with no handler behind them, "
                "which is paperwork rather than a capability")
    return ("not-started",
            "the legacy feature is declared, granted and still handled, and no "
            "replacement exists")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--app-id", default="", help="the app id to export, A...")
    ap.add_argument("--config-token-env", default="SLACK_CONFIG_ACCESS_TOKEN",
                    help="environment variable holding an app configuration token")
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN",
                    help="environment variable holding any bot token, for the scopes")
    ap.add_argument("--granted", default="",
                    help="comma separated granted scopes, if you have no bot token")
    ap.add_argument("--source", default="",
                    help="a directory of source files to read for handler symbols")
    args = ap.parse_args()

    findings = 0
    session = requests.Session()
    manifest = {}
    config_token = os.environ.get(args.config_token_env)
    if args.app_id and config_token:
        r = session.get(API + "apps.manifest.export",
                        headers={"Authorization": "Bearer " + config_token},
                        params={"app_id": args.app_id}, timeout=30)
        try:
            body = r.json()
        except ValueError:
            body = {"ok": False, "error": "unparseable_body"}
        if body.get("ok") is True:
            manifest = body
            log.info("manifest   ok             exported %s", args.app_id)
        else:
            log.warning("manifest   unavailable    apps.manifest.export answered "
                        "ok: false, error=%s", body.get("error"))
    else:
        log.info("manifest   skipped        set %s and pass --app-id to read the live "
                 "manifest", args.config_token_env)

    manifest_hits = manifest_findings(manifest)
    for code, why in manifest_hits:
        log.warning("manifest   %-14s %s", code, why)
        findings += 1

    granted = args.granted
    if not granted:
        token = os.environ.get(args.token_env)
        if token:
            reply = session.get(API + "auth.test",
                                headers={"Authorization": "Bearer " + token},
                                timeout=30)
            granted = reply.headers.get("x-oauth-scopes") or ""
        else:
            log.info("scopes     skipped        set %s or pass --granted to read the "
                     "grant on the installed token", args.token_env)
    scope_hits = scope_findings(granted)
    for code, why in scope_hits:
        log.warning("scopes     %-14s %s", code, why)
        findings += 1

    source_hits = []
    if args.source:
        for path in sorted(Path(args.source).rglob("*")):
            if not path.is_file() or path.suffix not in (".py", ".js", ".mjs", ".ts"):
                continue
            hits = source_findings(path.read_text(encoding="utf-8", errors="replace"),
                                   str(path))
            source_hits.extend(hits)
        for code, why in source_hits:
            log.warning("source     %-14s %s", code, why)
    else:
        log.info("source     skipped        pass --source to tell dead paperwork from "
                 "a capability somebody still maintains")

    doc = (manifest or {}).get("manifest", manifest) or {}
    state, why = migration_state(
        bool(((doc.get("features") or {}).get("workflow_steps"))),
        bool([c for c, _w in manifest_hits if c == "retired-event"]),
        bool(scope_hits),
        bool(doc.get("functions") or {}),
        bool(source_hits))
    (log.info if state in ("clean", "migrated") else log.warning)(
        "state      %-14s %s", state, why)

    if not findings and state in ("clean", "migrated"):
        log.info("verdict    clean          nothing from the retired surface remains")
        return 0
    log.warning("verdict    %d finding(s)", findings)
    log.warning("  repair: rebuild each step as a custom function that Workflow "
                "Builder can call, declared under functions in the manifest")
    log.warning("  repair: remove the workflow_steps block and the retired event "
                "subscriptions, then reinstall so the legacy grant goes with them")
    log.warning("  repair: tell the workflow owners their workflows must be rebuilt; "
                "Slack provides no automated migration for either half")
    log.warning("  note:   apps.manifest.update would replace the whole document from "
                "a copy made a moment ago, and is not called here")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-legacy-workflow-steps.mjs",
"js": '''/**
 * Find legacy Steps from Apps configuration left standing after the retirement.
 *
 * Slack retired legacy Steps from Apps on 26 September 2024. Workflows
 * containing one stopped running, the steps stopped working, and the five
 * associated events stopped being subscribable. None of that produced an
 * error, because nothing was called - which is why the evidence is
 * configuration rather than traffic. There is no method that enumerates which
 * Workflow Builder workflows referenced your steps; that surface is closed.
 *
 * Read only. Two GETs: apps.manifest.export with an app configuration token,
 * and auth.test with any bot token for the granted scope header. The method
 * that would fix this, apps.manifest.update, replaces the whole document and
 * is never called here.
 */
import { readdir, readFile } from 'node:fs/promises';
import { join, extname } from 'node:path';

const API = 'https://slack.com/api/';

export const RETIREMENT_DATE = '26 September 2024';

// The five events that stopped being subscribable on the retirement date.
export const RETIRED_EVENTS = ['workflow_step_execute', 'workflow_published',
  'workflow_unpublished', 'workflow_deleted', 'workflow_step_deleted'];

// Granted only to apps that implemented legacy steps, and it lives on the
// installed token rather than in the manifest.
export const LEGACY_SCOPE = 'workflow.steps:execute';

// Symbols that mean a handler still exists behind the declaration.
export const LEGACY_SYMBOLS = ['WorkflowStep', 'workflow_step_execute', '.step(',
  LEGACY_SCOPE];

/** Which subscribed events can no longer be delivered? Pure. */
export function retiredEvents(botEvents) {
  const subscribed = new Set((botEvents ?? []).map(String));
  return RETIRED_EVENTS.filter((e) => subscribed.has(e));
}

/** Read a live manifest for configuration the retirement left behind. Pure. */
export function manifestFindings(manifest) {
  const doc = manifest?.manifest ?? manifest ?? {};
  const steps = doc.features?.workflow_steps ?? [];
  const out = [];
  if (steps.length) {
    const names = steps.map((s) => String(s?.callback_id ?? s?.name ?? 'unnamed'));
    out.push(['legacy-steps', `${steps.length} legacy step(s) declared: `
      + `${names.join(', ')}. None has been callable since ${RETIREMENT_DATE}`]);
  }
  const botEvents = doc.settings?.event_subscriptions?.bot_events ?? [];
  for (const event of retiredEvents(botEvents)) {
    out.push(['retired-event', `${event} is subscribed and cannot be delivered; it `
      + `stopped being subscribable on ${RETIREMENT_DATE}`]);
  }
  if (steps.length && !Object.keys(doc.functions ?? {}).length) {
    out.push(['no-modern-functions', 'nothing is declared under functions, so no '
      + 'replacement exists yet and the capability is simply gone']);
  }
  return out;
}

/** Read the granted scope list for the legacy grant. Pure. */
export function scopeFindings(scopeHeader) {
  const granted = String(scopeHeader ?? '').split(',')
    .map((s) => s.trim()).filter(Boolean);
  if (granted.includes(LEGACY_SCOPE)) {
    return [['legacy-scope', `${LEGACY_SCOPE} is granted on the installed token; only `
      + 'legacy step apps ever held it, and it survives a manifest edit because a '
      + 'grant moves only when somebody reinstalls']];
  }
  return [];
}

/** Is there still a handler behind the declaration? Pure. */
export function sourceFindings(text, label = 'source') {
  const body = String(text ?? '');
  return LEGACY_SYMBOLS.filter((symbol) => body.includes(symbol))
    .map((symbol) => ['legacy-handler', `${symbol} appears in ${label}`]);
}

/**
 * Say in one word where this app actually stands. Pure.
 * clean, migrated, half-migrated, source-only, dead-config, not-started.
 */
export function migrationState(hasLegacyManifest, hasRetiredEvents, hasLegacyScope,
  hasModernFunctions, hasLegacySource) {
  const legacyConfig = Boolean(hasLegacyManifest || hasRetiredEvents || hasLegacyScope);
  if (!legacyConfig && !hasLegacySource) {
    return [hasModernFunctions ? 'migrated' : 'clean',
      'no legacy Steps from Apps configuration remains'];
  }
  if (legacyConfig && hasModernFunctions) {
    return ['half-migrated', 'a modern function is declared and the legacy step was '
      + 'left beside it; both appear to users and only one can run'];
  }
  if (!legacyConfig && hasLegacySource) {
    return ['source-only', 'a legacy handler survives in source with nothing declared, '
      + 'so it is dead code no user can reach'];
  }
  if (legacyConfig && !hasLegacySource) {
    return ['dead-config', 'legacy declarations and grants remain with no handler '
      + 'behind them, which is paperwork rather than a capability'];
  }
  return ['not-started', 'the legacy feature is declared, granted and still handled, '
    + 'and no replacement exists'];
}

function arg(args, name, fallback = '') {
  const i = args.indexOf(name);
  return i === -1 ? fallback : args[i + 1];
}

async function sourceFiles(dir) {
  const out = [];
  for (const entry of await readdir(dir, { withFileTypes: true })) {
    const full = join(dir, entry.name);
    if (entry.isDirectory()) out.push(...await sourceFiles(full));
    else if (['.py', '.js', '.mjs', '.ts'].includes(extname(entry.name))) out.push(full);
  }
  return out.sort();
}

async function main() {
  const args = process.argv.slice(2);
  const appId = arg(args, '--app-id');
  const configTokenEnv = arg(args, '--config-token-env', 'SLACK_CONFIG_ACCESS_TOKEN');
  const tokenEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
  const source = arg(args, '--source');
  let findings = 0;
  let manifest = {};

  const configToken = process.env[configTokenEnv];
  if (appId && configToken) {
    const r = await fetch(`${API}apps.manifest.export?app_id=${encodeURIComponent(appId)}`,
      { headers: { Authorization: `Bearer ${configToken}` } });
    let body;
    try {
      body = await r.json();
    } catch {
      body = { ok: false, error: 'unparseable_body' };
    }
    if (body.ok === true) {
      manifest = body;
      console.log(`manifest   ok             exported ${appId}`);
    } else {
      console.warn('manifest   unavailable    apps.manifest.export answered ok: false, '
        + `error=${body.error}`);
    }
  } else {
    console.log(`manifest   skipped        set ${configTokenEnv} and pass --app-id to `
      + 'read the live manifest');
  }

  const manifestHits = manifestFindings(manifest);
  for (const [code, why] of manifestHits) {
    console.warn(`manifest   ${code.padEnd(14)} ${why}`);
    findings += 1;
  }

  let granted = arg(args, '--granted');
  if (!granted) {
    const token = process.env[tokenEnv];
    if (token) {
      const reply = await fetch(`${API}auth.test`,
        { headers: { Authorization: `Bearer ${token}` } });
      granted = reply.headers.get('x-oauth-scopes') ?? '';
    } else {
      console.log(`scopes     skipped        set ${tokenEnv} or pass --granted to read `
        + 'the grant on the installed token');
    }
  }
  const scopeHits = scopeFindings(granted);
  for (const [code, why] of scopeHits) {
    console.warn(`scopes     ${code.padEnd(14)} ${why}`);
    findings += 1;
  }

  const sourceHits = [];
  if (source) {
    for (const path of await sourceFiles(source)) {
      sourceHits.push(...sourceFindings(await readFile(path, 'utf8'), path));
    }
    for (const [code, why] of sourceHits) {
      console.warn(`source     ${code.padEnd(14)} ${why}`);
    }
  } else {
    console.log('source     skipped        pass --source to tell dead paperwork from a '
      + 'capability somebody still maintains');
  }

  const doc = manifest?.manifest ?? manifest ?? {};
  const [state, why] = migrationState(
    Boolean(doc.features?.workflow_steps?.length),
    manifestHits.some(([c]) => c === 'retired-event'),
    Boolean(scopeHits.length),
    Boolean(Object.keys(doc.functions ?? {}).length),
    Boolean(sourceHits.length));
  ((state === 'clean' || state === 'migrated') ? console.log : console.warn)(
    `state      ${state.padEnd(14)} ${why}`);

  if (!findings && (state === 'clean' || state === 'migrated')) {
    console.log('verdict    clean          nothing from the retired surface remains');
    return;
  }
  console.warn(`verdict    ${findings} finding(s)`);
  console.warn('  repair: rebuild each step as a custom function that Workflow Builder '
    + 'can call, declared under functions in the manifest');
  console.warn('  repair: remove the workflow_steps block and the retired event '
    + 'subscriptions, then reinstall so the legacy grant goes with them');
  console.warn('  repair: tell the workflow owners their workflows must be rebuilt; '
    + 'Slack provides no automated migration for either half');
  console.warn('  note:   apps.manifest.update would replace the whole document from a '
    + 'copy made a moment ago, and is not called here');
  process.exitCode = 1;
}

// Only run when invoked directly, so importing this module in the tests does
// not execute main().
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "There is no token in these fixtures and no fixture that needs one, because the whole check is a document and a comma separated header. The assertions worth reading are the state machine ones: <code>half-migrated</code> has to win over <code>dead-config</code> when both a legacy step and a modern function are declared, because that is the state a team will otherwise report as finished, and <code>source-only</code> has to be distinguishable from <code>clean</code>, because a handler nobody can reach is dead code rather than a tidy app. The retired event list is asserted in its declared order so that two exports of the same app read the same way.",
"test_py_file": "test_slack_legacy_workflow_steps.py",
"test_py": '''from slack_legacy_workflow_steps import (
    manifest_findings, migration_state, retired_events, scope_findings,
    source_findings,
)

LEGACY = {"manifest": {
    "features": {"workflow_steps": [
        {"name": "Create ticket", "callback_id": "create_ticket"},
        {"name": "Notify manager", "callback_id": "notify_manager"},
    ]},
    "settings": {"event_subscriptions": {
        "bot_events": ["workflow_step_execute", "app_mention", "workflow_step_deleted"],
    }},
}}

MODERN = {"manifest": {
    "features": {},
    "functions": {"create_ticket": {"title": "Create ticket"}},
    "settings": {"event_subscriptions": {"bot_events": ["app_mention"]}},
}}


def codes(hits):
    return [c for c, _w in hits]


def test_only_the_retired_events_are_returned_and_in_a_fixed_order():
    found = retired_events(["workflow_step_deleted", "app_mention",
                            "workflow_step_execute"])
    assert found == ["workflow_step_execute", "workflow_step_deleted"]


def test_an_empty_or_missing_subscription_list_returns_nothing():
    assert retired_events([]) == []
    assert retired_events(None) == []


def test_the_legacy_feature_block_is_reported_with_its_callback_ids():
    hits = manifest_findings(LEGACY)
    legacy = [w for c, w in hits if c == "legacy-steps"][0]
    assert "create_ticket" in legacy and "notify_manager" in legacy
    assert "26 September 2024" in legacy


def test_each_retired_subscription_is_reported_on_its_own_line():
    assert codes(manifest_findings(LEGACY)).count("retired-event") == 2


def test_a_legacy_declaration_with_no_replacement_says_so():
    assert "no-modern-functions" in codes(manifest_findings(LEGACY))


def test_a_modern_manifest_has_nothing_to_report():
    assert manifest_findings(MODERN) == []
    assert manifest_findings({}) == []


def test_a_manifest_returned_unwrapped_is_read_the_same_way():
    assert codes(manifest_findings(LEGACY["manifest"])) == codes(
        manifest_findings(LEGACY))


def test_the_legacy_scope_is_found_in_the_granted_header():
    hits = scope_findings("chat:write,workflow.steps:execute, channels:read")
    assert codes(hits) == ["legacy-scope"]
    assert "reinstall" in hits[0][1]


def test_a_modern_grant_carries_nothing_to_report():
    assert scope_findings("chat:write,channels:read") == []
    assert scope_findings("") == []


def test_the_handler_symbols_are_found_in_source():
    hits = source_findings("from slack_bolt.workflows.step import WorkflowStep",
                           "listeners/onboarding.py")
    assert codes(hits) == ["legacy-handler"]
    assert "listeners/onboarding.py" in hits[0][1]


def test_source_with_no_legacy_symbol_reports_nothing():
    assert source_findings("app.event('app_mention')(handle)") == []


def test_an_app_with_nothing_legacy_anywhere_is_clean():
    assert migration_state(False, False, False, False, False)[0] == "clean"


def test_a_rebuilt_app_with_no_legacy_trace_is_migrated():
    assert migration_state(False, False, False, True, False)[0] == "migrated"


def test_the_replacement_beside_the_original_is_the_state_that_looks_finished():
    state, why = migration_state(True, True, True, True, True)
    assert state == "half-migrated"
    assert "only one can run" in why


def test_declarations_with_no_handler_behind_them_are_paperwork():
    assert migration_state(True, True, True, False, False)[0] == "dead-config"


def test_a_handler_with_nothing_declared_is_dead_code_rather_than_clean():
    state, why = migration_state(False, False, False, False, True)
    assert state == "source-only"
    assert "no user can reach" in why


def test_declared_granted_and_maintained_with_no_replacement_is_not_started():
    assert migration_state(True, True, True, False, True)[0] == "not-started"


def test_the_scope_alone_is_enough_to_count_as_legacy_configuration():
    assert migration_state(False, False, True, False, False)[0] == "dead-config"
''',
"test_js_file": "slack-legacy-workflow-steps.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  manifestFindings, migrationState, retiredEvents, scopeFindings, sourceFindings,
} from './slack-legacy-workflow-steps.mjs';

const LEGACY = {
  manifest: {
    features: {
      workflow_steps: [
        { name: 'Create ticket', callback_id: 'create_ticket' },
        { name: 'Notify manager', callback_id: 'notify_manager' },
      ],
    },
    settings: {
      event_subscriptions: {
        bot_events: ['workflow_step_execute', 'app_mention', 'workflow_step_deleted'],
      },
    },
  },
};

const MODERN = {
  manifest: {
    features: {},
    functions: { create_ticket: { title: 'Create ticket' } },
    settings: { event_subscriptions: { bot_events: ['app_mention'] } },
  },
};

const codes = (hits) => hits.map(([c]) => c);

test('only the retired events are returned and in a fixed order', () => {
  assert.deepEqual(
    retiredEvents(['workflow_step_deleted', 'app_mention', 'workflow_step_execute']),
    ['workflow_step_execute', 'workflow_step_deleted']);
});

test('an empty or missing subscription list returns nothing', () => {
  assert.deepEqual(retiredEvents([]), []);
  assert.deepEqual(retiredEvents(null), []);
});

test('the legacy feature block is reported with its callback ids', () => {
  const legacy = manifestFindings(LEGACY).find(([c]) => c === 'legacy-steps')[1];
  assert.equal(legacy.includes('create_ticket'), true);
  assert.equal(legacy.includes('notify_manager'), true);
  assert.equal(legacy.includes('26 September 2024'), true);
});

test('each retired subscription is reported on its own line', () => {
  assert.equal(codes(manifestFindings(LEGACY))
    .filter((c) => c === 'retired-event').length, 2);
});

test('a legacy declaration with no replacement says so', () => {
  assert.equal(codes(manifestFindings(LEGACY)).includes('no-modern-functions'), true);
});

test('a modern manifest has nothing to report', () => {
  assert.deepEqual(manifestFindings(MODERN), []);
  assert.deepEqual(manifestFindings({}), []);
});

test('a manifest returned unwrapped is read the same way', () => {
  assert.deepEqual(codes(manifestFindings(LEGACY.manifest)),
    codes(manifestFindings(LEGACY)));
});

test('the legacy scope is found in the granted header', () => {
  const hits = scopeFindings('chat:write,workflow.steps:execute, channels:read');
  assert.deepEqual(codes(hits), ['legacy-scope']);
  assert.equal(hits[0][1].includes('reinstall'), true);
});

test('a modern grant carries nothing to report', () => {
  assert.deepEqual(scopeFindings('chat:write,channels:read'), []);
  assert.deepEqual(scopeFindings(''), []);
});

test('the handler symbols are found in source', () => {
  const hits = sourceFindings("import { WorkflowStep } from '@slack/bolt';",
    'listeners/onboarding.js');
  assert.deepEqual(codes(hits), ['legacy-handler']);
  assert.equal(hits[0][1].includes('listeners/onboarding.js'), true);
});

test('source with no legacy symbol reports nothing', () => {
  assert.deepEqual(sourceFindings("app.event('app_mention', handle);"), []);
});

test('an app with nothing legacy anywhere is clean', () => {
  assert.equal(migrationState(false, false, false, false, false)[0], 'clean');
});

test('a rebuilt app with no legacy trace is migrated', () => {
  assert.equal(migrationState(false, false, false, true, false)[0], 'migrated');
});

test('the replacement beside the original is the state that looks finished', () => {
  const [state, why] = migrationState(true, true, true, true, true);
  assert.equal(state, 'half-migrated');
  assert.equal(why.includes('only one can run'), true);
});

test('declarations with no handler behind them are paperwork', () => {
  assert.equal(migrationState(true, true, true, false, false)[0], 'dead-config');
});

test('a handler with nothing declared is dead code rather than clean', () => {
  const [state, why] = migrationState(false, false, false, false, true);
  assert.equal(state, 'source-only');
  assert.equal(why.includes('no user can reach'), true);
});

test('declared, granted and maintained with no replacement is not started', () => {
  assert.equal(migrationState(true, true, true, false, true)[0], 'not-started');
});

test('the scope alone is enough to count as legacy configuration', () => {
  assert.equal(migrationState(false, false, true, false, false)[0], 'dead-config');
});
''',
"faq": [
 ("When exactly did this stop working, and what stopped?",
  "26 September 2024. From that date, Workflow Builder workflows containing a legacy step stopped executing, the steps themselves stopped working, and five events stopped being subscribable: workflow_step_execute, workflow_published, workflow_unpublished, workflow_deleted and workflow_step_deleted. Nothing was deleted from anybody's app configuration, which is why a manifest exported today can still describe the feature in full."),
 ("Is there a migration path from a legacy step to a modern one?",
  "Not an automated one, for either half. The replacement is a custom function that Workflow Builder can call, and you write it. The workflows that used the old step cannot be converted either: they have to be rebuilt by the people who own them, in Workflow Builder, by hand. That second half is the part that gets forgotten, because it is not your work and the people who have to do it will not find out on their own."),
 ("Can I find out which workflows were using my steps?",
  "No, and this is a real blind spot rather than a gap in the script. Since the retirement there is no read API that enumerates Workflow Builder workflows referencing an app's steps, or how often they ran, or when they last succeeded. The manifest tells you what your app declared; nothing tells you who was using it. In practice the list has to be reconstructed by asking, which is another reason to send the notice early."),
 ("We removed the workflow_steps block. Why does the scope still show up?",
  "Because a granted scope lives on the installed token, not in the manifest, and it moves only when somebody reinstalls the app. Editing the document changes what would be requested next time; it changes nothing about what is currently held. That is exactly why the check reads X-OAuth-Scopes separately, and why workflow.steps:execute is the line that tells you whether the cleanup was finished or only started."),
 ("Our manifest has both a legacy step and a new custom function. Is that fine?",
  "It is the half-migrated state, and it is the one worth acting on soonest, because it looks finished. Nothing conflicts and nothing errors, so the manifest quietly claims two capabilities of which one cannot run. Anybody browsing your app's steps has no way to tell which is which, and the legacy entry will keep being copied into every environment created from that document. Delete it, then reinstall so the grant goes with it."),
],
"related": [
 ("/slack/manifest-drift/", "the document this check reads, and how it diverges"),
 ("/slack/rtm-legacy-still-used/", "another retired transport still in the grant"),
 ("/slack/files-upload-retired/", "a method sunset the same way, with a probe"),
],
"citations": [CITE_STEPS_RETIRED, CITE_STEPS_FAQ, CITE_BOLT_1025, CITE_MANIFEST_EXPORT],
})
