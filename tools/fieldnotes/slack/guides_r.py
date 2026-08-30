#!/usr/bin/env python3
"""/slack/ field notes, batch R - the writing.

Four notes about work that Slack has already accepted, or will never start,
written so that no two of them are the same note and none of them is a note
this section has already published.

The first is a queue that outlived the code that filled it. Slack holds a
scheduled message for up to 120 days and delivers it whatever happens to your
application in between, so the interesting reading is the pending queue held
beside your own records: the entries nothing in your app knows about any more.
It is deliberately not about post_at arithmetic, which is a different note.

The second is silence. Link unfurling has four separate preconditions and a
missing one produces nothing at all - no error, no event, no log line - so the
interesting reading is the app's own manifest beside the messages already in a
channel, and the finding is which of the four is absent.

The third is a token with a life measured in seconds. A trigger_id is single
use and expires almost immediately, which is a different deadline from the
three second ack this section already covers, and the interesting reading is
your own interaction ledger: how long the handler waited, and whether the same
trigger was spent twice.

The fourth is a sequence that stopped halfway. Uploading a file is three
network operations and only the first and last are Slack calls, so a break
between them leaves a file id that names nothing. The interesting reading is
your upload ledger held against files.info, one id at a time.

Read only throughout. Nothing here schedules, cancels, unfurls, opens a view or
uploads anything. Listing the scheduled queue is a read and cancelling from it
is not, so cancellations are printed. Minting an upload URL is a write and does
not appear at all: this script reads the ids you already have.
"""

CITE_SCHEDULED_LIST = ("chat.scheduledMessages.list method reference - Slack Docs",
                       "https://docs.slack.dev/reference/methods/chat.scheduledMessages.list")
CITE_DELETE_SCHEDULED = ("chat.deleteScheduledMessage method reference - Slack Docs",
                         "https://docs.slack.dev/reference/methods/chat.deleteScheduledMessage")
CITE_SCHEDULE = ("chat.scheduleMessage method reference - Slack Docs",
                 "https://docs.slack.dev/reference/methods/chat.scheduleMessage")
CITE_CONV_INFO = ("conversations.info method reference - Slack Docs",
                  "https://docs.slack.dev/reference/methods/conversations.info")
CITE_CONV_HISTORY = ("conversations.history method reference - Slack Docs",
                     "https://docs.slack.dev/reference/methods/conversations.history")
CITE_LINK_SHARED = ("link_shared event reference - Slack Docs",
                    "https://docs.slack.dev/reference/events/link_shared")
CITE_CHAT_UNFURL = ("chat.unfurl method reference - Slack Docs",
                    "https://docs.slack.dev/reference/methods/chat.unfurl")
CITE_UNFURLING = ("Unfurling links in messages - Slack Docs",
                  "https://docs.slack.dev/messaging/unfurling-links-in-messages")
CITE_MANIFEST = ("App manifest reference - Slack Docs",
                 "https://docs.slack.dev/reference/app-manifest")
CITE_VIEWS_OPEN = ("views.open method reference - Slack Docs",
                   "https://docs.slack.dev/reference/methods/views.open")
CITE_VIEWS_PUSH = ("views.push method reference - Slack Docs",
                   "https://docs.slack.dev/reference/methods/views.push")
CITE_INTERACTIVITY = ("Handling user interaction - Slack Docs",
                      "https://docs.slack.dev/interactivity/handling-user-interaction")
CITE_MODALS = ("Modals - Slack Docs", "https://docs.slack.dev/surfaces/modals")
CITE_GET_UPLOAD_URL = ("files.getUploadURLExternal method reference - Slack Docs",
                       "https://docs.slack.dev/reference/methods/files.getUploadURLExternal")
CITE_COMPLETE_UPLOAD = ("files.completeUploadExternal method reference - Slack Docs",
                        "https://docs.slack.dev/reference/methods/files.completeUploadExternal")
CITE_FILES_INFO = ("files.info method reference - Slack Docs",
                   "https://docs.slack.dev/reference/methods/files.info")
CITE_FILES_LIST = ("files.list method reference - Slack Docs",
                   "https://docs.slack.dev/reference/methods/files.list")

GUIDES = []

GUIDES.append({
"slug": "scheduled-messages-orphaned",
"title": "Scheduled messages outlive the app that queued them",
"description": "chat.scheduleMessage hands the send to Slack for up to 120 days. Diff the pending queue against your own records to find the sends nothing will stop.",
"h1": "Scheduled messages outlive the app that queued them",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack scheduled message not cancelled",
             "chat.scheduledMessages.list orphaned",
             "slack chat.deleteScheduledMessage",
             "slack scheduled message after redeploy",
             "slack scheduled message queue audit"],
"deps": "Python 3.9+ with requests, or Node.js 18+; a bot token that can list its own scheduled messages, plus channels:read to check where they are aimed",
"lead": "The reminder bot is redeployed on Tuesday with a rewritten scheduler. On Wednesday morning people start getting two nudges for every task: one from the new code, and one from the old code, for a ticket that was closed nine days ago.</p><p>Nobody deployed the old code. Nobody can find it running. The old code is not running &mdash; it stopped existing on Tuesday. What is still running is Slack, working through a queue of sends the old scheduler handed it weeks ago and which nothing has ever told it to forget.",
"short_answer": """<p><code>chat.scheduleMessage</code> is not a timer inside your app. It is a handover. Slack takes the message, keeps it for up to 120 days, and delivers it at <code>post_at</code> regardless of what happens to you in the meantime. Deleting the database row does not cancel it. Redeploying does not cancel it. <strong>Uninstalling and reinstalling the app does not cancel it.</strong> Only <code>chat.deleteScheduledMessage</code>, with the <code>scheduled_message_id</code> that the original call returned, cancels it.</p>
<p>So the queue is a resource with a lifecycle, and almost nobody gives it one. Every scheduling change that ships without draining the queue leaves a tail behind it, and the tail is invisible until it fires.</p>
<p><code>chat.scheduledMessages.list</code> reads the queue, and reading it is the whole diagnosis. Hold each entry's <code>id</code> against your own records: an entry you cannot account for is an orphan, and an entry you can account for but whose reason has closed is worse, because you will find it and decide it is fine. Then check where each one is aimed, because a channel archived last month is a send that is already doomed. Run it twice a week apart and the count itself is the finding: a queue that grows run over run is a queue nobody drains.</p>""",
"problem": """<p>The reason this is expensive is that the symptom arrives with an alibi. Users report messages from a version of the app that no longer exists, and every instinct says <em>look at what is deployed</em>. What is deployed is fine. The sender is Slack, on your behalf, from an instruction you gave it in the past and can no longer see from inside your own process.</p>
<p>There are four ways a queued message becomes wrong, and they want different repairs. <strong>The reason closed.</strong> A reminder was scheduled for a task, the task was completed, the row was deleted, and the send was never cancelled because deleting a row is not an API call. <strong>The scheduler was replaced.</strong> A deploy changed the cadence, the text, or the channel, and the previous version's queue was left to fire alongside the new one, which is the duplicate-reminder shape. <strong>The target moved.</strong> The channel was archived, made private, or the bot was removed from it in a spring clean, and the send will fail on arrival with <code>is_archived</code> or <code>not_in_channel</code> weeks after anybody could connect the two. <strong>The install was replaced.</strong> The app was uninstalled and reinstalled, the token is new, and the queue from the old install is still there under the same app.</p>
<p>What all four share is that nothing in your application is in a position to notice. There is no callback when a scheduled message fires, no event, and no error surface for a send that fails at delivery time. The only place the state lives is in Slack's queue, and the only way to see it is to ask.</p>
<p>The queue is also silently capped. A workspace holds a limited number of pending scheduled messages per channel and per app, and an app that schedules without cancelling eventually starts getting rejections on new sends while the old ones sit there. By that point the failure is a scheduling failure, several layers away from the leak that caused it, and it gets fixed by raising a retry count.</p>
<p>And the horizon is long enough to hide the problem across an entire project. 120 days is a third of a year. A message scheduled in March fires in July, into a channel that has been renamed twice, from an app that has been rewritten once, for a person who left in May.</p>""",
"why": """<p><strong>The queue is state you own and cannot see from your own process.</strong> Every other piece of scheduling state is in your database, where a migration or a delete reaches it. This one is not. It sits in Slack, it is only reachable by an API call, and the only reason it is ever wrong is that nobody made that call.</p>
<p><strong>An id you cannot account for is the finding, not a count.</strong> "There are 340 pending messages" changes nothing. "There are 340 pending messages and 291 of them have ids that appear nowhere in your records" is a decision. The script exists to do that join, because it is the only comparison that separates a healthy backlog from a leak.</p>
<p><strong>A tracked entry whose reason has closed is worse than an untracked one.</strong> The orphan is at least obviously wrong. The entry you can still look up is the one you will glance at, confirm exists in your table, and move on from &mdash; without noticing the row says the task was completed on the fourth. The script reads the state on your own record rather than only its presence.</p>
<p><strong>Where it is aimed matters as much as whether you meant it.</strong> A send you still want, into a channel that was archived, is a failure already scheduled. It is worth knowing now rather than in six weeks, and <code>conversations.info</code> answers it with a read.</p>
<p><strong>Two runs beat one run.</strong> A single snapshot cannot tell a queue that is being drained properly from one that is filling up, because both look like a number. The difference between two snapshots does: the ids that fired, the ids that appeared, and the ids that have been sitting there through both.</p>
<p><strong>Cancelling is a write, so this script prints it.</strong> The repair for an orphan is <code>chat.deleteScheduledMessage</code> per id, and a script that ran that itself would be one bad ledger away from silently cancelling every reminder in the workspace. It prints the lines. You decide.</p>""",
"steps": [
 {"h": "Read the queue before you read anything else",
  "body": """<p><code>chat.scheduledMessages.list</code> with <code>limit=100</code> and cursor pagination returns every pending send: <code>id</code>, <code>channel_id</code>, <code>post_at</code> and <code>date_created</code>. This is a read. Run it first and print the raw count, because the count alone is often the moment somebody says <em>it should not be anywhere near that</em>.</p>"""},
 {"h": "Join each entry against your own records by scheduled_message_id",
  "body": """<p><code>ledger_verdict</code> takes one queue entry and your records and returns <code>tracked</code>, <code>superseded</code>, or <code>unknown-to-you</code>. If you are not storing the <code>id</code> that <code>chat.scheduleMessage</code> returned, every entry comes back <code>unknown-to-you</code> and that is itself the finding: you have no way to cancel any of them.</p>"""},
 {"h": "Separate superseded from unknown rather than counting both as orphans",
  "body": """<p><code>superseded</code> means your own record says this send should not happen &mdash; the task is done, the reminder was cancelled, the row is tombstoned &mdash; and the send is still queued anyway. That is a missing cancel call in a specific code path, which is a bug with an address. <code>unknown-to-you</code> is a whole scheduler that never stored its ids, which is a design change.</p>"""},
 {"h": "Check where every pending send is aimed",
  "body": """<p><code>target_verdict</code> reads <code>conversations.info</code> for each distinct channel in the queue and returns <code>target-archived</code>, <code>target-left</code>, <code>target-unreadable</code>, or <code>deliverable</code>. These are sends that will fail on arrival with nobody watching, and they are worth cancelling even when you still want the message, because the message is not going to happen.</p>"""},
 {"h": "Look at the distribution, not just the total",
  "body": """<p><code>bucket</code> sorts each entry into <code>within-the-hour</code>, <code>today</code>, <code>this-week</code>, <code>months-out</code> and <code>beyond-horizon</code>. A healthy reminder queue is front-loaded. A queue with a long flat tail months out is a queue that has been accumulating, and the tail is where the orphans concentrate because nobody has been around long enough to remember them.</p>"""},
 {"h": "Run it again a week later and diff the ids",
  "body": """<p>Save the id list, pass it back as <code>--previous</code>, and <code>queue_drift</code> reports what fired, what was added and what has been held through both runs. <code>growing</code> means more is being scheduled than is being cancelled or delivered, which is the leak stated as a rate rather than as a number. The held set is your orphan list, confirmed twice.</p>"""},
],
"verify": """<p>Run it against the workspace and your own scheduling table. The finding is a set of ids and a reason, and the repair is a list of lines you run yourself.</p>
<pre><code class="language-bash">python3 slack_scheduled_orphans.py --ledger reminders.json --previous last-week.json
# identity   U024BE7LH in Acme
# queue      312 pending scheduled message(s) across 9 channel(s)
# buckets    within-the-hour 2   today 14   this-week 51   months-out 245
# ledger     unknown-to-you Q1298ABCD C024BE91L post_at=2026-11-04T09:00Z
#                           no record of this id; nothing in your app can cancel it
# ledger     superseded     Q1298XYZW C024BE91L post_at=2026-09-02T09:00Z
#                           your record says state=completed on 2026-08-20
# target     target-archived              C07J4K2QT  14 pending send(s) aimed at a
#                           channel archived on 2026-06-11; every one will fail
# drift      growing        fired 26   added 61   held 251
# verdict    291 of 312 pending send(s) have no owner
#   repair: chat.deleteScheduledMessage channel=C024BE91L scheduled_message_id=Q1298ABCD
#   repair: store the scheduled_message_id chat.scheduleMessage returns, beside the
#           row that justifies the send, and cancel it when that row closes</code></pre>""",
"code_intro": "Five pure functions and two reads. <code>ledger_verdict</code> is the join that makes the whole note, and it separates <em>you never knew about this</em> from <em>you knew and changed your mind</em> because those are different bugs. <code>target_verdict</code> asks whether the destination still accepts messages. <code>bucket</code> turns the queue into a shape. <code>queue_drift</code> is the only function here that needs two runs, and it is the one that answers whether this is a backlog or a leak. <code>cancel_line</code> writes the repair out as text and never runs it.",
"py_file": "slack_scheduled_orphans.py",
"py": '''"""Find the scheduled messages Slack still intends to send on your behalf.

Read only. chat.scheduledMessages.list is a read and is the only thing this
touches in the queue; chat.deleteScheduledMessage is a write, so cancellations
are printed as lines for you to run and are never executed here.

The question is not whether post_at was computed correctly. It is whether the
send still has a reason to exist. Your app was redeployed, the task closed, the
channel was archived, and Slack knows about none of that: it took the message
and it will deliver it up to 120 days later exactly as instructed.
"""
import argparse
import json
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_scheduled_orphans")

API = "https://slack.com/api/"
HOUR = 3600
DAY = 86400
HORIZON_DAYS = 120

# States on your own record that mean the send should not happen. Anything else
# is treated as live, because guessing that an unknown state means cancelled is
# the one error that would make this script recommend cancelling a real send.
CLOSED_STATES = ("cancelled", "canceled", "completed", "done", "superseded",
                 "deleted", "tombstoned", "obsolete")


def ledger_verdict(entry, ledger):
    """Does your application still stand behind this queued send? Pure.

    Returns (verdict, detail). tracked is the only one that needs no action.
    superseded and unknown-to-you are both orphans, and they are kept apart
    because they are different bugs: superseded is one missing cancel call in a
    code path you can name, unknown-to-you is a scheduler that never stored the
    ids it was given and therefore cannot cancel anything at all.
    """
    entry = entry or {}
    sid = str(entry.get("id") or "")
    if not sid:
        return ("unidentified", "the queue entry has no id, so there is nothing to "
                                "join against and nothing to cancel it with")
    row = (ledger or {}).get(sid)
    if row is None:
        return ("unknown-to-you", "no record of %s. Nothing in your application can "
                                  "cancel this send, because cancelling needs exactly "
                                  "this id and you did not keep it" % sid)
    if not isinstance(row, dict):
        return ("tracked", "%s appears in your records" % sid)
    state = str(row.get("state") or row.get("status") or "live").strip().lower()
    if state in CLOSED_STATES:
        return ("superseded", "your record says state=%s%s, and the send is still "
                              "queued. The row was closed and the cancel call was "
                              "never made" % (state, (" on " + str(row["closed_at"]))
                                              if row.get("closed_at") else ""))
    return ("tracked", "%s appears in your records as state=%s" % (sid, state))


def target_verdict(entry, channels):
    """Will the channel this is aimed at still take a message? Pure.

    channels maps a channel id to the conversations.info payload, or to None
    when the read failed. deliverable does not promise the send is wanted, only
    that it is possible; everything else is a send that is already going to
    fail, weeks from now, with nobody watching.
    """
    entry = entry or {}
    cid = str(entry.get("channel_id") or entry.get("channel") or "")
    if not cid:
        return ("target-missing", "the entry names no channel")
    if cid not in (channels or {}):
        return ("target-unchecked", "%s was not read; pass channels:read to check "
                                    "where the queue is aimed" % cid)
    info = (channels or {}).get(cid)
    if not info:
        return ("target-unreadable", "%s could not be read. A private channel the "
                                     "bot has been removed from looks exactly like a "
                                     "channel that does not exist" % cid)
    if info.get("is_archived") is True:
        return ("target-archived", "%s was archived. Archiving is permanent until "
                                   "somebody undoes it by hand, and an archived "
                                   "channel refuses every message" % cid)
    if info.get("is_member") is False:
        return ("target-left", "the bot is no longer in %s, so this send will fail "
                               "with not_in_channel when it fires" % cid)
    return ("deliverable", "%s still accepts messages from this bot" % cid)


def bucket(entry, now=None):
    """How far into the future is this send, in words? Pure.

    A healthy reminder queue is front loaded. A long flat tail months out is
    where orphans collect, because by the time those fire nobody remembers
    scheduling them.
    """
    now = time.time() if now is None else now
    try:
        post_at = float((entry or {}).get("post_at") or 0)
    except (TypeError, ValueError):
        return ("unparseable", "post_at is not a number")
    if not post_at:
        return ("unparseable", "post_at is missing")
    delta = post_at - now
    if delta < 0:
        return ("overdue", "post_at is %.0f second(s) in the past and it is still "
                           "listed as pending" % -delta)
    if delta < HOUR:
        return ("within-the-hour", "%.0f minute(s) away" % (delta / 60))
    if delta < DAY:
        return ("today", "%.1f hour(s) away" % (delta / HOUR))
    if delta < 7 * DAY:
        return ("this-week", "%.1f day(s) away" % (delta / DAY))
    if delta <= HORIZON_DAYS * DAY:
        return ("months-out", "%.0f day(s) away" % (delta / DAY))
    return ("beyond-horizon", "%.0f day(s) away, past the %d day limit the API "
                              "accepts" % (delta / DAY, HORIZON_DAYS))


def queue_drift(before, after):
    """What happened to the queue between two runs? Pure.

    Returns (verdict, detail, counts). One snapshot is a number and a number
    cannot tell a backlog from a leak. Two snapshots can: if more ids appear
    than leave, the queue is filling faster than it drains, and the ids present
    in both runs are the orphan list confirmed twice.
    """
    a = {str(x) for x in (before or [])}
    b = {str(x) for x in (after or [])}
    counts = {"fired": len(a - b), "added": len(b - a), "held": len(a & b)}
    if not a:
        return ("first-run", "no previous snapshot, so there is nothing to compare. "
                             "Keep this id list and pass it back next time",
                counts)
    if counts["added"] > counts["fired"]:
        return ("growing", "%d id(s) appeared and %d left. The queue is being filled "
                           "faster than it is drained, which is the leak stated as a "
                           "rate" % (counts["added"], counts["fired"]), counts)
    if counts["fired"] > counts["added"]:
        return ("draining", "%d id(s) left and %d appeared"
                % (counts["fired"], counts["added"]), counts)
    return ("flat", "%d id(s) in and %d out; %d have been held through both runs"
            % (counts["added"], counts["fired"], counts["held"]), counts)


def cancel_line(entry):
    """The repair for one orphan, as text. Printed, never executed. Pure.

    Cancelling is a write and this script does not make writes. It is also the
    one operation here that a wrong ledger would turn into deleting every
    reminder in the workspace, which is a decision for a person.
    """
    entry = entry or {}
    return ("chat.deleteScheduledMessage channel=%s scheduled_message_id=%s"
            % (entry.get("channel_id") or entry.get("channel") or "?",
               entry.get("id") or "?"))


def load_ledger(path):
    """Read your own scheduling records. Deliberately forgiving of shape."""
    if not path:
        return {}
    raw = json.loads(open(path, encoding="utf-8").read())
    if isinstance(raw, dict) and not any(isinstance(v, dict) for v in raw.values()):
        return {str(k): {"state": str(v)} for k, v in raw.items()}
    if isinstance(raw, dict):
        rows = raw.get("scheduled") or raw.get("records") or raw
        if isinstance(rows, dict):
            return {str(k): v for k, v in rows.items()}
        raw = rows
    out = {}
    for row in raw or []:
        if not isinstance(row, dict):
            out[str(row)] = {}
            continue
        sid = (row.get("scheduled_message_id") or row.get("id")
               or row.get("slack_id") or "")
        if sid:
            out[str(sid)] = row
    return out


def read_queue(session, channel=""):
    """Follow the cursor to the end. Listing is a read; cancelling is not."""
    entries, cursor = [], ""
    while True:
        params = {"limit": "100"}
        if channel:
            params["channel"] = channel
        if cursor:
            params["cursor"] = cursor
        body = session.get(API + "chat.scheduledMessages.list", timeout=30,
                           params=params).json()
        if body.get("ok") is not True:
            log.error("queue      unavailable    %s", body.get("error"))
            return entries, False
        entries.extend(body.get("scheduled_messages") or [])
        cursor = ((body.get("response_metadata") or {}).get("next_cursor") or "")
        if not cursor:
            return entries, True


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ledger", default="",
                    help="a JSON file of your own scheduling records, keyed by or "
                         "carrying the scheduled_message_id Slack returned")
    ap.add_argument("--previous", default="",
                    help="a JSON array of ids emitted by an earlier run")
    ap.add_argument("--channel", default="", help="limit the queue read to one channel")
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN",
                    help="environment variable holding the bot token")
    ap.add_argument("--emit", action="store_true",
                    help="print the current id list as JSON on stdout, to save and "
                         "pass back as --previous next time")
    ap.add_argument("--skip-targets", action="store_true",
                    help="do not read conversations.info for the queued channels")
    args = ap.parse_args()

    token = os.environ.get(args.token_env)
    if not token:
        log.error("set %s to a bot token that can list its own scheduled messages",
                  args.token_env)
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + token})
    who = s.get(API + "auth.test", timeout=30).json()
    if who.get("ok") is not True:
        log.error("auth.test  unavailable    %s", who.get("error"))
        return 2
    log.info("identity   %s in %s", who.get("user_id"), who.get("team"))

    entries, complete = read_queue(s, args.channel)
    if not complete:
        return 2
    channels = sorted({str(e.get("channel_id") or "") for e in entries} - {""})
    log.info("queue      %d pending scheduled message(s) across %d channel(s)",
             len(entries), len(channels))

    shape = {}
    for entry in entries:
        verdict, _ = bucket(entry)
        shape[verdict] = shape.get(verdict, 0) + 1
    log.info("buckets    %s", "   ".join("%s %d" % kv for kv in sorted(shape.items())))

    info = {}
    if not args.skip_targets:
        for cid in channels:
            body = s.get(API + "conversations.info", timeout=30,
                         params={"channel": cid}).json()
            info[cid] = body.get("channel") if body.get("ok") is True else None

    ledger = load_ledger(args.ledger)
    if args.ledger:
        log.info("ledger     %d record(s) read from %s", len(ledger), args.ledger)

    orphans, doomed = [], {}
    for entry in entries:
        verdict, detail = ledger_verdict(entry, ledger)
        if verdict != "tracked":
            orphans.append(entry)
            log.warning("ledger     %-14s %s %s post_at=%s", verdict,
                        entry.get("id"), entry.get("channel_id"), entry.get("post_at"))
            log.warning("                          %s", detail)
        tverdict, tdetail = target_verdict(entry, info)
        if tverdict not in ("deliverable", "target-unchecked"):
            doomed.setdefault((entry.get("channel_id"), tverdict, tdetail), 0)
            doomed[(entry.get("channel_id"), tverdict, tdetail)] += 1

    for (cid, tverdict, tdetail), count in sorted(doomed.items(), key=str):
        log.warning("target     %-16s %s  %d pending send(s); %s",
                    tverdict, cid, count, tdetail)

    ids = [str(e.get("id") or "") for e in entries if e.get("id")]
    if args.previous:
        before = json.loads(open(args.previous, encoding="utf-8").read())
        dverdict, ddetail, counts = queue_drift(before, ids)
        line = "drift      %-14s fired %d   added %d   held %d" % (
            dverdict, counts["fired"], counts["added"], counts["held"])
        (log.warning if dverdict == "growing" else log.info)(line)
        log.info("                          %s", ddetail)

    if args.emit:
        print(json.dumps(ids))

    if orphans or doomed:
        log.warning("verdict    %d of %d pending send(s) have no owner",
                    len(orphans), len(entries))
        for entry in orphans[:10]:
            log.warning("  repair: %s", cancel_line(entry))
        if len(orphans) > 10:
            log.warning("  repair: and %d more, listed the same way",
                        len(orphans) - 10)
        log.warning("  repair: store the scheduled_message_id chat.scheduleMessage "
                    "returns beside the row that justifies the send, and cancel it "
                    "when that row closes")
        log.warning("  repair: drain the queue as a migration step on any deploy that "
                    "changes scheduling semantics, rather than leaving it to fire")
        return 1
    log.info("verdict    clean          every pending send is accounted for")
    return 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-scheduled-orphans.mjs",
"js": '''/**
 * Find the scheduled messages Slack still intends to send on your behalf.
 *
 * Read only. chat.scheduledMessages.list is a read and is the only thing this
 * touches in the queue; chat.deleteScheduledMessage is a write, so
 * cancellations are printed as lines for you to run and are never executed.
 *
 * The question is not whether post_at was computed correctly. It is whether
 * the send still has a reason to exist. Your app was redeployed, the task
 * closed, the channel was archived, and Slack knows about none of that.
 */

import { readFile } from 'node:fs/promises';

const API = 'https://slack.com/api/';
const HOUR = 3600;
const DAY = 86400;
const HORIZON_DAYS = 120;

// States on your own record that mean the send should not happen. Anything
// else is treated as live: guessing that an unknown state means cancelled is
// the one error that would make this recommend cancelling a real send.
const CLOSED_STATES = ['cancelled', 'canceled', 'completed', 'done', 'superseded',
  'deleted', 'tombstoned', 'obsolete'];

/**
 * Does your application still stand behind this queued send? Pure.
 * Returns [verdict, detail]; tracked is the only one that needs no action.
 */
export function ledgerVerdict(entry, ledger) {
  const e = entry ?? {};
  const sid = String(e.id ?? '');
  if (!sid) {
    return ['unidentified', 'the queue entry has no id, so there is nothing to join '
      + 'against and nothing to cancel it with'];
  }
  const row = (ledger ?? {})[sid];
  if (row === undefined || row === null) {
    return ['unknown-to-you', `no record of ${sid}. Nothing in your application can `
      + 'cancel this send, because cancelling needs exactly this id and you did not '
      + 'keep it'];
  }
  if (typeof row !== 'object') return ['tracked', `${sid} appears in your records`];
  const state = String(row.state ?? row.status ?? 'live').trim().toLowerCase();
  if (CLOSED_STATES.includes(state)) {
    return ['superseded', `your record says state=${state}`
      + `${row.closed_at ? ` on ${row.closed_at}` : ''}, and the send is still queued. `
      + 'The row was closed and the cancel call was never made'];
  }
  return ['tracked', `${sid} appears in your records as state=${state}`];
}

/**
 * Will the channel this is aimed at still take a message? Pure.
 * channels maps a channel id to the conversations.info payload, or to null.
 */
export function targetVerdict(entry, channels) {
  const e = entry ?? {};
  const cid = String(e.channel_id ?? e.channel ?? '');
  if (!cid) return ['target-missing', 'the entry names no channel'];
  if (!Object.prototype.hasOwnProperty.call(channels ?? {}, cid)) {
    return ['target-unchecked', `${cid} was not read; pass channels:read to check `
      + 'where the queue is aimed'];
  }
  const info = (channels ?? {})[cid];
  if (!info) {
    return ['target-unreadable', `${cid} could not be read. A private channel the bot `
      + 'has been removed from looks exactly like a channel that does not exist'];
  }
  if (info.is_archived === true) {
    return ['target-archived', `${cid} was archived. Archiving is permanent until `
      + 'somebody undoes it by hand, and an archived channel refuses every message'];
  }
  if (info.is_member === false) {
    return ['target-left', `the bot is no longer in ${cid}, so this send will fail `
      + 'with not_in_channel when it fires'];
  }
  return ['deliverable', `${cid} still accepts messages from this bot`];
}

/** How far into the future is this send, in words? Pure. */
export function bucket(entry, now = Date.now() / 1000) {
  const raw = (entry ?? {}).post_at;
  const postAt = Number(raw);
  if (raw === undefined || raw === null || raw === '' || !Number.isFinite(postAt)) {
    return ['unparseable', 'post_at is missing or is not a number'];
  }
  if (!postAt) return ['unparseable', 'post_at is missing'];
  const delta = postAt - now;
  if (delta < 0) {
    return ['overdue', `post_at is ${(-delta).toFixed(0)} second(s) in the past and it `
      + 'is still listed as pending'];
  }
  if (delta < HOUR) return ['within-the-hour', `${(delta / 60).toFixed(0)} minute(s) away`];
  if (delta < DAY) return ['today', `${(delta / HOUR).toFixed(1)} hour(s) away`];
  if (delta < 7 * DAY) return ['this-week', `${(delta / DAY).toFixed(1)} day(s) away`];
  if (delta <= HORIZON_DAYS * DAY) {
    return ['months-out', `${(delta / DAY).toFixed(0)} day(s) away`];
  }
  return ['beyond-horizon', `${(delta / DAY).toFixed(0)} day(s) away, past the `
    + `${HORIZON_DAYS} day limit the API accepts`];
}

/**
 * What happened to the queue between two runs? Pure.
 * Returns [verdict, detail, counts].
 */
export function queueDrift(before, after) {
  const a = new Set((before ?? []).map(String));
  const b = new Set((after ?? []).map(String));
  const counts = {
    fired: [...a].filter((x) => !b.has(x)).length,
    added: [...b].filter((x) => !a.has(x)).length,
    held: [...a].filter((x) => b.has(x)).length,
  };
  if (!a.size) {
    return ['first-run', 'no previous snapshot, so there is nothing to compare. Keep '
      + 'this id list and pass it back next time', counts];
  }
  if (counts.added > counts.fired) {
    return ['growing', `${counts.added} id(s) appeared and ${counts.fired} left. The `
      + 'queue is being filled faster than it is drained, which is the leak stated as '
      + 'a rate', counts];
  }
  if (counts.fired > counts.added) {
    return ['draining', `${counts.fired} id(s) left and ${counts.added} appeared`,
      counts];
  }
  return ['flat', `${counts.added} id(s) in and ${counts.fired} out; ${counts.held} `
    + 'have been held through both runs', counts];
}

/** The repair for one orphan, as text. Printed, never executed. Pure. */
export function cancelLine(entry) {
  const e = entry ?? {};
  return `chat.deleteScheduledMessage channel=${e.channel_id ?? e.channel ?? '?'} `
    + `scheduled_message_id=${e.id ?? '?'}`;
}

function loadLedger(raw) {
  if (!raw) return {};
  if (!Array.isArray(raw) && typeof raw === 'object') {
    const values = Object.values(raw);
    if (values.length && !values.some((v) => v && typeof v === 'object')) {
      return Object.fromEntries(Object.entries(raw).map(([k, v]) => [k, { state: String(v) }]));
    }
    const rows = raw.scheduled ?? raw.records ?? raw;
    if (!Array.isArray(rows)) return rows;
    return loadLedger(rows);
  }
  const out = {};
  for (const row of raw ?? []) {
    if (!row || typeof row !== 'object') { out[String(row)] = {}; continue; }
    const sid = row.scheduled_message_id ?? row.id ?? row.slack_id ?? '';
    if (sid) out[String(sid)] = row;
  }
  return out;
}

function arg(args, name, fallback = null) {
  const i = args.indexOf(name);
  return i === -1 ? fallback : args[i + 1];
}

async function main() {
  const args = process.argv.slice(2);
  const tokenEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
  const token = process.env[tokenEnv];
  if (!token) {
    console.error(`set ${tokenEnv} to a bot token that can list its own scheduled `
      + 'messages');
    process.exitCode = 2;
    return;
  }
  const headers = { Authorization: `Bearer ${token}` };
  const read = async (method, params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return (await fetch(`${API}${method}${qs ? `?${qs}` : ''}`, { headers })).json();
  };

  const who = await read('auth.test');
  if (who.ok !== true) {
    console.error(`auth.test  unavailable    ${who.error}`);
    process.exitCode = 2;
    return;
  }
  console.log(`identity   ${who.user_id} in ${who.team}`);

  const channel = arg(args, '--channel', '');
  const entries = [];
  let cursor = '';
  for (;;) {
    const params = { limit: '100' };
    if (channel) params.channel = channel;
    if (cursor) params.cursor = cursor;
    // eslint-disable-next-line no-await-in-loop
    const body = await read('chat.scheduledMessages.list', params);
    if (body.ok !== true) {
      console.error(`queue      unavailable    ${body.error}`);
      process.exitCode = 2;
      return;
    }
    entries.push(...(body.scheduled_messages ?? []));
    cursor = body.response_metadata?.next_cursor ?? '';
    if (!cursor) break;
  }
  const channels = [...new Set(entries.map((e) => String(e.channel_id ?? '')))]
    .filter(Boolean).sort();
  console.log(`queue      ${entries.length} pending scheduled message(s) across `
    + `${channels.length} channel(s)`);

  const shape = {};
  for (const entry of entries) {
    const [verdict] = bucket(entry);
    shape[verdict] = (shape[verdict] ?? 0) + 1;
  }
  console.log(`buckets    ${Object.entries(shape).sort()
    .map(([k, v]) => `${k} ${v}`).join('   ')}`);

  const info = {};
  if (!args.includes('--skip-targets')) {
    for (const cid of channels) {
      // eslint-disable-next-line no-await-in-loop
      const body = await read('conversations.info', { channel: cid });
      info[cid] = body.ok === true ? body.channel : null;
    }
  }

  const ledgerFile = arg(args, '--ledger', '');
  const ledger = ledgerFile
    ? loadLedger(JSON.parse(await readFile(ledgerFile, 'utf8')))
    : {};
  if (ledgerFile) {
    console.log(`ledger     ${Object.keys(ledger).length} record(s) read from ${ledgerFile}`);
  }

  const orphans = [];
  const doomed = new Map();
  for (const entry of entries) {
    const [verdict, detail] = ledgerVerdict(entry, ledger);
    if (verdict !== 'tracked') {
      orphans.push(entry);
      console.warn(`ledger     ${verdict.padEnd(14)} ${entry.id} ${entry.channel_id} `
        + `post_at=${entry.post_at}`);
      console.warn(`                          ${detail}`);
    }
    const [tv, td] = targetVerdict(entry, info);
    if (tv !== 'deliverable' && tv !== 'target-unchecked') {
      const key = `${entry.channel_id}\\u0000${tv}\\u0000${td}`;
      doomed.set(key, (doomed.get(key) ?? 0) + 1);
    }
  }
  for (const [key, count] of [...doomed.entries()].sort()) {
    const [cid, tv, td] = key.split('\\u0000');
    console.warn(`target     ${tv.padEnd(16)} ${cid}  ${count} pending send(s); ${td}`);
  }

  const ids = entries.map((e) => String(e.id ?? '')).filter(Boolean);
  const previous = arg(args, '--previous', '');
  if (previous) {
    const before = JSON.parse(await readFile(previous, 'utf8'));
    const [dv, dd, counts] = queueDrift(before, ids);
    const line = `drift      ${dv.padEnd(14)} fired ${counts.fired}   `
      + `added ${counts.added}   held ${counts.held}`;
    if (dv === 'growing') console.warn(line); else console.log(line);
    console.log(`                          ${dd}`);
  }

  if (args.includes('--emit')) console.log(JSON.stringify(ids));

  if (orphans.length || doomed.size) {
    console.warn(`verdict    ${orphans.length} of ${entries.length} pending send(s) `
      + 'have no owner');
    for (const entry of orphans.slice(0, 10)) console.warn(`  repair: ${cancelLine(entry)}`);
    if (orphans.length > 10) {
      console.warn(`  repair: and ${orphans.length - 10} more, listed the same way`);
    }
    console.warn('  repair: store the scheduled_message_id chat.scheduleMessage returns '
      + 'beside the row that justifies the send, and cancel it when that row closes');
    console.warn('  repair: drain the queue as a migration step on any deploy that '
      + 'changes scheduling semantics, rather than leaving it to fire');
    process.exitCode = 1;
  } else {
    console.log('verdict    clean          every pending send is accounted for');
  }
}

// Only run when invoked directly, so importing this module in the tests does
// not execute main() and fail the file on a missing token.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The assertions worth having are the ones that keep two orphans apart and keep one non-orphan out. <code>ledger_verdict</code> has to call a closed record <code>superseded</code> rather than folding it in with the ids you never stored, because those two findings send you to different code. It also has to treat an unrecognised state as live, since the cost of a false <code>superseded</code> is a cancelled reminder somebody needed. And <code>queue_drift</code> has to distinguish a first run from a flat one, because zero movement and no comparison are not the same answer.",
"test_py_file": "test_slack_scheduled_orphans.py",
"test_py": '''from slack_scheduled_orphans import (bucket, cancel_line, ledger_verdict, queue_drift,
                                     target_verdict)

NOW = 1_800_000_000.0


def entry(**kw):
    row = {"id": "Q1298ABCD", "channel_id": "C024BE91L", "post_at": NOW + 3600,
           "date_created": NOW}
    row.update(kw)
    return row


def test_an_id_you_stored_is_tracked():
    verdict, detail = ledger_verdict(entry(), {"Q1298ABCD": {"state": "live"}})
    assert verdict == "tracked"
    assert "Q1298ABCD" in detail


def test_an_id_you_never_stored_is_the_orphan_you_cannot_cancel():
    verdict, detail = ledger_verdict(entry(), {})
    assert verdict == "unknown-to-you"
    assert "can cancel this send" in detail


def test_a_closed_record_with_a_live_send_is_its_own_verdict():
    verdict, detail = ledger_verdict(
        entry(), {"Q1298ABCD": {"state": "completed", "closed_at": "2026-08-20"}})
    assert verdict == "superseded"
    assert "2026-08-20" in detail


def test_superseded_and_unknown_are_never_collapsed():
    assert ledger_verdict(entry(), {})[0] != ledger_verdict(
        entry(), {"Q1298ABCD": {"state": "cancelled"}})[0]


def test_an_unrecognised_state_is_treated_as_live():
    for state in ("live", "pending", "queued", "wat", ""):
        assert ledger_verdict(entry(), {"Q1298ABCD": {"state": state}})[0] == "tracked"


def test_an_entry_with_no_id_cannot_be_joined_or_cancelled():
    verdict, detail = ledger_verdict(entry(id=""), {"Q1298ABCD": {}})
    assert verdict == "unidentified"
    assert "nothing to cancel" in detail


def test_a_plain_string_record_still_counts_as_tracked():
    assert ledger_verdict(entry(), {"Q1298ABCD": "live"})[0] == "tracked"


def test_a_channel_that_still_takes_messages_is_deliverable():
    verdict, _ = target_verdict(entry(), {"C024BE91L": {"is_archived": False,
                                                        "is_member": True}})
    assert verdict == "deliverable"


def test_an_archived_target_is_a_send_that_is_already_doomed():
    verdict, detail = target_verdict(entry(), {"C024BE91L": {"is_archived": True}})
    assert verdict == "target-archived"
    assert "refuses every message" in detail


def test_a_channel_the_bot_left_names_the_error_it_will_fail_with():
    verdict, detail = target_verdict(entry(), {"C024BE91L": {"is_archived": False,
                                                             "is_member": False}})
    assert verdict == "target-left"
    assert "not_in_channel" in detail


def test_an_unreadable_channel_is_not_reported_as_gone():
    verdict, detail = target_verdict(entry(), {"C024BE91L": None})
    assert verdict == "target-unreadable"
    assert "looks exactly like" in detail


def test_a_channel_that_was_never_read_is_unchecked_rather_than_fine():
    assert target_verdict(entry(), {})[0] == "target-unchecked"


def test_the_buckets_sort_by_distance_into_the_future():
    assert bucket(entry(post_at=NOW + 600), NOW)[0] == "within-the-hour"
    assert bucket(entry(post_at=NOW + 5 * 3600), NOW)[0] == "today"
    assert bucket(entry(post_at=NOW + 3 * 86400), NOW)[0] == "this-week"
    assert bucket(entry(post_at=NOW + 60 * 86400), NOW)[0] == "months-out"


def test_a_send_past_the_horizon_is_named_as_past_it():
    verdict, detail = bucket(entry(post_at=NOW + 200 * 86400), NOW)
    assert verdict == "beyond-horizon"
    assert "120 day limit" in detail


def test_a_pending_entry_behind_the_clock_is_overdue():
    assert bucket(entry(post_at=NOW - 90), NOW)[0] == "overdue"


def test_a_missing_post_at_is_unparseable_rather_than_zero():
    assert bucket(entry(post_at=None), NOW)[0] == "unparseable"
    assert bucket(entry(post_at="soon"), NOW)[0] == "unparseable"


def test_more_arriving_than_leaving_is_a_leak_stated_as_a_rate():
    verdict, detail, counts = queue_drift(["a", "b"], ["b", "c", "d"])
    assert verdict == "growing"
    assert counts == {"fired": 1, "added": 2, "held": 1}
    assert "faster than it is drained" in detail


def test_more_leaving_than_arriving_is_draining():
    verdict, _, counts = queue_drift(["a", "b", "c"], ["c"])
    assert verdict == "draining"
    assert counts["fired"] == 2


def test_no_previous_snapshot_is_not_the_same_answer_as_no_movement():
    assert queue_drift([], ["a"])[0] == "first-run"
    assert queue_drift(["a"], ["a"])[0] == "flat"


def test_the_held_set_is_the_orphan_list_confirmed_twice():
    _, _, counts = queue_drift(["a", "b", "c"], ["b", "c", "d"])
    assert counts["held"] == 2


def test_the_cancel_line_is_text_and_carries_both_arguments():
    line = cancel_line(entry())
    assert "chat.deleteScheduledMessage" in line
    assert "channel=C024BE91L" in line
    assert "scheduled_message_id=Q1298ABCD" in line
''',
"test_js_file": "slack-scheduled-orphans.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  bucket, cancelLine, ledgerVerdict, queueDrift, targetVerdict,
} from './slack-scheduled-orphans.mjs';

const NOW = 1800000000;

const entry = (over = {}) => ({
  id: 'Q1298ABCD', channel_id: 'C024BE91L', post_at: NOW + 3600, date_created: NOW,
  ...over,
});

test('an id you stored is tracked', () => {
  const [verdict, detail] = ledgerVerdict(entry(), { Q1298ABCD: { state: 'live' } });
  assert.equal(verdict, 'tracked');
  assert.match(detail, /Q1298ABCD/);
});

test('an id you never stored is the orphan you cannot cancel', () => {
  const [verdict, detail] = ledgerVerdict(entry(), {});
  assert.equal(verdict, 'unknown-to-you');
  assert.match(detail, /can cancel this send/);
});

test('a closed record with a live send is its own verdict', () => {
  const [verdict, detail] = ledgerVerdict(entry(),
    { Q1298ABCD: { state: 'completed', closed_at: '2026-08-20' } });
  assert.equal(verdict, 'superseded');
  assert.match(detail, /2026-08-20/);
});

test('superseded and unknown are never collapsed', () => {
  assert.notEqual(ledgerVerdict(entry(), {})[0],
    ledgerVerdict(entry(), { Q1298ABCD: { state: 'cancelled' } })[0]);
});

test('an unrecognised state is treated as live', () => {
  for (const state of ['live', 'pending', 'queued', 'wat', '']) {
    assert.equal(ledgerVerdict(entry(), { Q1298ABCD: { state } })[0], 'tracked');
  }
});

test('an entry with no id cannot be joined or cancelled', () => {
  const [verdict, detail] = ledgerVerdict(entry({ id: '' }), { Q1298ABCD: {} });
  assert.equal(verdict, 'unidentified');
  assert.match(detail, /nothing to cancel/);
});

test('a plain string record still counts as tracked', () => {
  assert.equal(ledgerVerdict(entry(), { Q1298ABCD: 'live' })[0], 'tracked');
});

test('a channel that still takes messages is deliverable', () => {
  assert.equal(targetVerdict(entry(),
    { C024BE91L: { is_archived: false, is_member: true } })[0], 'deliverable');
});

test('an archived target is a send that is already doomed', () => {
  const [verdict, detail] = targetVerdict(entry(), { C024BE91L: { is_archived: true } });
  assert.equal(verdict, 'target-archived');
  assert.match(detail, /refuses every message/);
});

test('a channel the bot left names the error it will fail with', () => {
  const [verdict, detail] = targetVerdict(entry(),
    { C024BE91L: { is_archived: false, is_member: false } });
  assert.equal(verdict, 'target-left');
  assert.match(detail, /not_in_channel/);
});

test('an unreadable channel is not reported as gone', () => {
  const [verdict, detail] = targetVerdict(entry(), { C024BE91L: null });
  assert.equal(verdict, 'target-unreadable');
  assert.match(detail, /looks exactly like/);
});

test('a channel that was never read is unchecked rather than fine', () => {
  assert.equal(targetVerdict(entry(), {})[0], 'target-unchecked');
});

test('the buckets sort by distance into the future', () => {
  assert.equal(bucket(entry({ post_at: NOW + 600 }), NOW)[0], 'within-the-hour');
  assert.equal(bucket(entry({ post_at: NOW + 5 * 3600 }), NOW)[0], 'today');
  assert.equal(bucket(entry({ post_at: NOW + 3 * 86400 }), NOW)[0], 'this-week');
  assert.equal(bucket(entry({ post_at: NOW + 60 * 86400 }), NOW)[0], 'months-out');
});

test('a send past the horizon is named as past it', () => {
  const [verdict, detail] = bucket(entry({ post_at: NOW + 200 * 86400 }), NOW);
  assert.equal(verdict, 'beyond-horizon');
  assert.match(detail, /120 day limit/);
});

test('a pending entry behind the clock is overdue', () => {
  assert.equal(bucket(entry({ post_at: NOW - 90 }), NOW)[0], 'overdue');
});

test('a missing post_at is unparseable rather than zero', () => {
  assert.equal(bucket(entry({ post_at: null }), NOW)[0], 'unparseable');
  assert.equal(bucket(entry({ post_at: 'soon' }), NOW)[0], 'unparseable');
});

test('more arriving than leaving is a leak stated as a rate', () => {
  const [verdict, detail, counts] = queueDrift(['a', 'b'], ['b', 'c', 'd']);
  assert.equal(verdict, 'growing');
  assert.deepEqual(counts, { fired: 1, added: 2, held: 1 });
  assert.match(detail, /faster than it is drained/);
});

test('more leaving than arriving is draining', () => {
  const [verdict, , counts] = queueDrift(['a', 'b', 'c'], ['c']);
  assert.equal(verdict, 'draining');
  assert.equal(counts.fired, 2);
});

test('no previous snapshot is not the same answer as no movement', () => {
  assert.equal(queueDrift([], ['a'])[0], 'first-run');
  assert.equal(queueDrift(['a'], ['a'])[0], 'flat');
});

test('the held set is the orphan list confirmed twice', () => {
  const [, , counts] = queueDrift(['a', 'b', 'c'], ['b', 'c', 'd']);
  assert.equal(counts.held, 2);
});

test('the cancel line is text and carries both arguments', () => {
  const line = cancelLine(entry());
  assert.match(line, /chat\\.deleteScheduledMessage/);
  assert.match(line, /channel=C024BE91L/);
  assert.match(line, /scheduled_message_id=Q1298ABCD/);
});
''',
"faq": [
 ("Does uninstalling the app cancel its scheduled messages?",
  "No. Neither does reinstalling it, rotating the token, deleting the database, or deleting the code. The scheduled message lives in Slack, keyed by an id Slack gave you, and the only thing that removes it is chat.deleteScheduledMessage with that id. This surprises people because every other kind of pending work in an integration dies with the process that created it."),
 ("How is this different from a scheduled message that fails with time_in_past?",
  "That failure happens at scheduling time and is arithmetic: post_at was computed in milliseconds, or in local time, or too close to now. This one happens at delivery time and is bookkeeping: post_at was perfect, Slack accepted it, and then the world changed underneath it. The first never enters the queue. The second is already in it."),
 ("We do not store the scheduled_message_id at all. Where does that leave us?",
  "With a queue you can read and cannot cancel, which is exactly what the script will tell you: every entry comes back unknown-to-you. Reading gives you back the ids, so a one-off drain is still possible by hand, matching entries to channels and post_at values. The lasting fix is to store the id the scheduling call returns beside the row that justifies the send."),
 ("Is there an event when a scheduled message fires or fails?",
  "No. The delivery is invisible from your side. If the channel was archived in the meantime the send simply fails, at a moment when nothing of yours is running and nothing is watching, which is why an audit that checks where the queue is aimed is worth more here than logging would be."),
 ("Why does the script print the cancel commands instead of running them?",
  "Because everything in this section reads, and because this is the one repair where a mistake is expensive in the other direction. If your ledger is incomplete for a boring reason, a script with a write path would quietly cancel real reminders that people are relying on. Printed lines let you look at the list first."),
],
"related": [
 ("/slack/scheduled-message-in-past/", "the other scheduling failure, at the other end of the call"),
 ("/slack/archived-channel-target/", "where a queued send lands when the channel closed"),
 ("/slack/token-revoked/", "why a reinstall does not clear anything the old install left"),
],
"citations": [CITE_SCHEDULED_LIST, CITE_DELETE_SCHEDULED, CITE_SCHEDULE, CITE_CONV_INFO],
})

GUIDES.append({
"slug": "unfurl-domain-not-configured",
"title": "link_shared never fires: no domain was ever registered",
"description": "Unfurling has four separate preconditions and a missing one is silent. Find whether the domain, the subscription, links:read or links:write is the absent one.",
"h1": "link_shared never fires: no domain was ever registered",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack link_shared not firing",
             "slack unfurl domain not configured",
             "slack app unfurl domains",
             "slack chat.unfurl links:write",
             "slack links never unfurl no preview"],
"deps": "Python 3.9+ with requests, or Node.js 18+; a bot token with channels:history, and optionally a manifest exported from the app configuration page",
"lead": "The handler is written, deployed and covered by tests. Somebody pastes a link to your product into <code>#support</code> and it posts as a bare blue URL with no preview at all. Nothing appears in the logs, because nothing arrived. The handler was never called.</p><p>There is no error to search for. Slack did not reject anything, your endpoint did not time out, and the app is in the channel with a valid token. Unfurling is gated by four separate switches and only one of them lives anywhere near your code, so the app sits there behaving perfectly and receiving nothing.",
"short_answer": """<p>Slack sends <code>link_shared</code> <strong>only</strong> for domains the app has explicitly registered under <em>Event Subscriptions &rarr; App unfurl domains</em>. Not for every link. Not for links in channels the bot is in. Only for registered domains, and only to an app that also holds <code>links:read</code>, and only if the <code>link_shared</code> event is subscribed. Answering then needs <code>chat.unfurl</code>, which needs <code>links:write</code>.</p>
<p>Four preconditions, and every one of them fails silently. There is no <code>ok: false</code>, no rejected event, no warning on install. The app simply never hears about the link, and from inside the handler that is indistinguishable from nobody having posted one.</p>
<p>Two more rules make this harder to test than it should be. <strong>Slack suppresses <code>link_shared</code> for links the app posts itself</strong>, so the obvious way to check &mdash; have the bot post its own link &mdash; proves nothing. And unfurls honour per-user preferences, so a link that unfurls for you may not for a colleague who turned previews off.</p>
<p>Which precondition is missing is decidable without guessing. The domain list and the event subscription come from the app manifest, the scopes come from the <code>X-OAuth-Scopes</code> header on any response, and the evidence that it is not working comes from <code>conversations.history</code>: your links, sitting in a channel, with no unfurl attached.</p>""",
"problem": """<p>The reason this eats a day is that everything you can check looks correct. The bot is installed. The bot is in the channel. The Request URL is verified, and other events arrive through it, so the endpoint is definitely reachable. The code has a branch for <code>link_shared</code>. Every hypothesis you can form from inside the application is already disproved, and the actual answer is a text box on a web page nobody opened.</p>
<p>The domain registration is the switch that catches almost everyone, because it does not resemble anything else in the Slack app model. Scopes are a list, events are a list, and both are visible in the manifest next to code that mentions them. The unfurl domain list is a third list, in a different place, with its own rules: Slack matches a registered domain <em>and its subdomains</em>, so registering the apex is what you want &mdash; and registering <code>www.example.com</code> instead means every link without the <code>www</code> is invisible, because <code>example.com</code> is not a subdomain of <code>www.example.com</code>. Pasting in a full URL with a scheme or a path fails the same quiet way.</p>
<p>The scope pair is the second trap, and the two scopes fail at opposite ends. Without <code>links:read</code> the event never arrives, so you see nothing. With <code>links:read</code> but without <code>links:write</code> the event arrives, your handler runs happily, and <code>chat.unfurl</code> comes back <code>{"ok": false, "error": "missing_scope"}</code> &mdash; which is at least a visible failure, and is a completely different debugging session from the silent one.</p>
<p>Then there is the self-post rule. The natural test is to have the bot post a link to your own product and watch. Slack does not fire <code>link_shared</code> for links posted by the app itself, so that test returns a negative result no matter how correct the configuration is, and people conclude the configuration is wrong when it may be fine.</p>
<p>Finally, adding the domain and the scopes changes the token grant, which means a reinstall. Apps get all four things right, skip the reinstall, and stay broken with a configuration page that says everything is set.</p>""",
"why": """<p><strong>Silence is not evidence of anything, so the script goes looking for the evidence.</strong> A handler that never runs writes no logs, so the only proof that unfurling is not happening lives in the workspace: messages your users already posted, carrying links on your domain, with no unfurl attached to them. That is a read, and it turns "it does not seem to work" into a count.</p>
<p><strong>The four preconditions have an order, and reporting them out of order wastes the fix.</strong> If no domain is registered, the scopes do not matter yet. If the event is not subscribed, <code>links:write</code> does not matter yet. The script names the first missing one rather than listing all four and leaving you to work out which to do first.</p>
<p><strong>A registered domain is matched literally, and the ways to write it wrong all look fine.</strong> A scheme, a path, a port, a leading <code>www.</code>, a wildcard someone added because wildcards feel right: each one is a string that reads as a domain and matches nothing. The script checks the shape of what is registered before it checks whether anything matched.</p>
<p><strong>Links the app posted itself are excluded from the evidence, not counted against it.</strong> Slack suppresses the event for those. Counting them as failures inflates the finding and, worse, sends people to re-check a handler that was never going to be called for that message.</p>
<p><strong>A link on an unregistered domain is a different row from a link on a registered one.</strong> The first will never fire whatever you do to the code. The second should have fired and did not, which is the row that means the remaining preconditions are worth checking. Merging them produces a number that cannot be acted on.</p>
<p><strong>The two scopes fail at opposite ends and want to be named separately.</strong> Missing <code>links:read</code> is silence. Missing <code>links:write</code> is a loud <code>missing_scope</code> after your handler already did its work. Same feature, same page, entirely different symptom.</p>""",
"steps": [
 {"h": "Read the domain list and the subscription out of the manifest",
  "body": """<p>Export the manifest from the app configuration page and pass it with <code>--manifest</code>. <code>features.unfurl_domains</code> is the registered list and <code>settings.event_subscriptions.bot_events</code> is where <code>link_shared</code> has to appear. A bot token cannot read either of these; this is app configuration, not workspace state.</p>"""},
 {"h": "Check the shape of every registered domain before you check anything else",
  "body": """<p><code>registration_fault</code> returns <code>scheme-included</code>, <code>path-included</code>, <code>port-included</code>, <code>wildcard</code>, <code>www-prefixed</code> or <code>usable</code>. Each of the failing ones is a string that reads perfectly as a domain and matches no link at all, and finding one here ends the investigation before any workspace read.</p>"""},
 {"h": "Take the granted scopes from the response header, not from the manifest",
  "body": """<p><code>X-OAuth-Scopes</code> on any Web API response lists what the token actually holds, which is what matters. The manifest lists what the app asks for. An app whose manifest requests <code>links:read</code> and whose token was granted before that line was added has a manifest that says yes and a token that says no.</p>"""},
 {"h": "Name the first missing precondition rather than all of them",
  "body": """<p><code>precondition_gap</code> returns <code>no-domains</code>, <code>not-subscribed</code>, <code>no-links-read</code>, <code>no-links-write</code> or <code>ready</code>, in that order. The order is the fix order. Anything after the first missing one is unknowable until that one is done, because the failures mask each other.</p>"""},
 {"h": "Prove it from the channel, using links other people posted",
  "body": """<p><code>conversations.history</code> returns what is already there. <code>link_urls</code> pulls the URLs out of Slack's <code>&lt;url|label&gt;</code> markup, <code>domain_match</code> decides which registered domain covers each one, and <code>unfurl_state</code> sorts each message into <code>unfurled</code>, <code>not-unfurled</code>, <code>off-domain</code>, <code>self-posted</code> or <code>no-links</code>.</p>"""},
 {"h": "Discard the app's own links from the evidence",
  "body": """<p><code>self-posted</code> exists because Slack does not fire <code>link_shared</code> for links the app posted itself. Those messages tell you nothing about whether unfurling works, so they are excluded from the count rather than reported as failures. If every link in your test channel was posted by the bot, the run has no evidence in it and says so.</p>"""},
],
"verify": """<p>Run it against a channel where people paste your links. The finding is one missing precondition and a count of links that went unadorned.</p>
<pre><code class="language-bash">python3 slack_unfurl_silence.py --manifest app-manifest.json --channel C024BE91L
# identity   U024BE7LH in Acme
# scopes     chat:write,channels:history,channels:read,links:read
# manifest   1 unfurl domain(s), link_shared subscribed
# domain     www-prefixed   www.acme.dev  Slack matches this domain and its
#                           subdomains, and acme.dev is not a subdomain of it
# gap        no-links-write links:read is granted so the event can arrive, but
#                           chat.unfurl needs links:write to answer it
# history    182 message(s) read from C024BE91L
# links      not-unfurled   31 link(s) on a registered domain, none with an unfurl
# links      off-domain     12 link(s) on acme.dev, which matches nothing registered
# links      self-posted    4 link(s) posted by this app; Slack suppresses the event
#                           for those, so they are not evidence either way
# verdict    unfurling cannot work as configured
#   repair: register the apex acme.dev under Event Subscriptions, App unfurl domains
#   repair: add links:write to the bot scopes and reinstall the app</code></pre>""",
"code_intro": "Five pure functions and one read. <code>registration_fault</code> is the cheapest useful thing here and catches the majority of real cases without touching the network. <code>domain_match</code> implements the matching rule literally, apex plus subdomains, because implementing it generously would hide the exact mistake the note is about. <code>link_urls</code> unpacks Slack's link markup. <code>unfurl_state</code> classifies one posted message, and <code>precondition_gap</code> answers the only question that decides what you do next: which switch to flip first.",
"py_file": "slack_unfurl_silence.py",
"py": '''"""Find out why your links never unfurl, when nothing anywhere reports an error.

Read only. This reads the app manifest you exported, the scopes on the token,
and messages that are already in a channel. It never posts a link, never calls
chat.unfurl, and never changes the app configuration.

Unfurling has four preconditions: the domain is registered under App unfurl
domains, link_shared is subscribed, the token holds links:read to receive the
event and links:write to answer it. Every one of them fails silently, so the
useful output is which one is missing first.
"""
import argparse
import json
import logging
import os
import re
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_unfurl_silence")

API = "https://slack.com/api/"

# Slack rewrites links in message text as <url> or <url|label>. Anything left
# after those are removed is a bare URL somebody typed.
LINK_MARKUP = re.compile(r"<(https?://[^>|\\s]+)(?:\\|[^>]*)?>")
BARE_URL = re.compile(r"https?://[^\\s<>|]+")


def link_urls(text):
    """Every URL in a message's text, unwrapped from Slack's markup. Pure."""
    body = str(text or "")
    found = list(LINK_MARKUP.findall(body))
    found.extend(BARE_URL.findall(LINK_MARKUP.sub(" ", body)))
    out = []
    for url in found:
        cleaned = url.rstrip(".,;:)]>")
        if cleaned and cleaned not in out:
            out.append(cleaned)
    return out


def host_of(url):
    """The host part of a URL, lowercased and stripped of everything else. Pure."""
    text = str(url or "").strip()
    if "://" in text:
        text = text.split("://", 1)[1]
    for sep in ("/", "?", "#"):
        text = text.split(sep, 1)[0]
    if "@" in text:
        text = text.split("@", 1)[1]
    text = text.split(":", 1)[0]
    return text.strip().lower().rstrip(".")


def registration_fault(value):
    """Is this registered entry a domain Slack can match? Pure.

    Returns (verdict, detail). Every failing verdict is a string that reads
    perfectly well as a domain to a human and matches nothing at all in Slack,
    which is why this runs before any network call.
    """
    raw = str(value or "").strip()
    if not raw:
        return ("empty", "an empty entry in the unfurl domain list")
    if "://" in raw:
        return ("scheme-included", "%s carries a scheme. The field takes a domain, so "
                                   "the scheme becomes part of the string being "
                                   "matched and nothing matches it" % raw)
    if "/" in raw:
        return ("path-included", "%s carries a path. Slack matches on the domain; a "
                                 "path here matches no link" % raw)
    if raw.startswith("*."):
        return ("wildcard", "%s is a wildcard. Slack already matches the registered "
                            "domain and every subdomain of it, so the literal *. is "
                            "just a domain that does not exist" % raw)
    if ":" in raw:
        return ("port-included", "%s carries a port, which is not part of the domain "
                                 "Slack compares against" % raw)
    low = raw.lower()
    if "." not in low or low.startswith(".") or low.endswith("."):
        return ("not-a-domain", "%s is not shaped like a domain" % raw)
    if low.startswith("www."):
        return ("www-prefixed", "%s matches this domain and its subdomains, and %s is "
                                "not a subdomain of it. Every link without the www "
                                "prefix is invisible to the app" % (low, low[4:]))
    return ("usable", "%s is registered and will match itself and its subdomains" % low)


def domain_match(url, registered):
    """Which registered domain, if any, covers this URL? Pure.

    Implemented literally: a registered domain matches itself and anything
    ending in a dot plus itself. Being generous here would hide the exact
    mistake this note exists for, so it is not.
    """
    host = host_of(url)
    if not host:
        return ""
    best = ""
    for entry in registered or []:
        domain = str(entry or "").strip().lower().rstrip(".")
        if not domain:
            continue
        if host == domain or host.endswith("." + domain):
            if len(domain) > len(best):
                best = domain
    return best


def unfurl_state(message, own_ids, registered):
    """What does this posted message tell you about unfurling? Pure.

    Returns (verdict, detail, urls). self-posted is excluded from the evidence
    rather than counted as a failure, because Slack does not fire link_shared
    for links the app posted itself and the message could never have unfurled
    however correct the configuration is.
    """
    msg = message or {}
    urls = link_urls(msg.get("text"))
    if not urls:
        return ("no-links", "nothing to unfurl in this message", [])
    author = {str(msg.get("user") or ""), str(msg.get("bot_id") or ""),
              str(msg.get("app_id") or "")} - {""}
    if author & {str(x) for x in (own_ids or set()) if x}:
        return ("self-posted", "this app posted the link. Slack suppresses "
                               "link_shared for an app's own links, so this message "
                               "is not evidence either way", urls)
    matched = [u for u in urls if domain_match(u, registered)]
    if not matched:
        return ("off-domain", "no URL here falls under a registered domain, so no "
                              "link_shared would ever fire for this message", urls)
    attached = []
    for att in (msg.get("attachments") or []):
        attached.append(str((att or {}).get("app_unfurl_url")
                            or (att or {}).get("from_url") or ""))
    for url in matched:
        if url in attached:
            return ("unfurled", "%s came back with an unfurl attached" % url, matched)
    if msg.get("attachments"):
        return ("not-unfurled", "%d attachment(s) on this message and none of them is "
                                "an unfurl of %s" % (len(msg["attachments"]),
                                                     matched[0]), matched)
    return ("not-unfurled", "%s is on a registered domain and posted with no unfurl "
                            "at all" % matched[0], matched)


def precondition_gap(domains, events, scopes):
    """Which of the four preconditions is missing, in fix order? Pure.

    The order is the point. A missing domain makes the scopes unknowable, and a
    missing links:read makes links:write academic, so reporting all four at once
    produces a list nobody can start on.
    """
    usable = [d for d in (domains or [])
              if registration_fault(d)[0] == "usable"]
    if not usable:
        return ("no-domains", "no usable domain is registered under App unfurl "
                              "domains, so link_shared cannot fire for any link at "
                              "all. This is the first thing to fix and nothing after "
                              "it can be tested until it is done")
    if events is not None and "link_shared" not in set(events or []):
        return ("not-subscribed", "%d domain(s) are registered and link_shared is not "
                                  "in the subscribed bot events. Registering the "
                                  "domain does not subscribe the event"
                % len(usable))
    if scopes is None:
        return ("scopes-unread", "the domain and the subscription are in place; the "
                                 "granted scopes were not read, so links:read and "
                                 "links:write are unverified")
    held = {s.strip() for s in scopes}
    if "links:read" not in held:
        return ("no-links-read", "links:read is not granted, so the event will not be "
                                 "delivered however the domain is registered. This is "
                                 "the silent one: no error appears anywhere")
    if "links:write" not in held:
        return ("no-links-write", "links:read is granted so the event can arrive, but "
                                  "chat.unfurl needs links:write to answer it. This "
                                  "one fails loudly, after your handler has already "
                                  "done its work")
    return ("ready", "all four preconditions are in place: a registered domain, the "
                     "link_shared subscription, links:read and links:write")


def manifest_facts(manifest):
    """Pull the unfurl domains and subscribed bot events out of a manifest."""
    doc = manifest or {}
    doc = doc.get("manifest", doc)
    features = doc.get("features") or {}
    settings = doc.get("settings") or {}
    events = ((settings.get("event_subscriptions") or {}).get("bot_events"))
    return list(features.get("unfurl_domains") or []), events


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", default="",
                    help="path to a manifest exported from the app configuration page")
    ap.add_argument("--domain", action="append", default=[],
                    help="a registered unfurl domain, if you have no manifest to hand")
    ap.add_argument("--channel", action="append", default=[],
                    help="a channel to read for evidence; repeatable")
    ap.add_argument("--limit", type=int, default=200,
                    help="messages to read per channel")
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN",
                    help="environment variable holding the bot token")
    args = ap.parse_args()

    domains, events = list(args.domain), None
    if args.manifest:
        domains_from_file, events = manifest_facts(
            json.loads(open(args.manifest, encoding="utf-8").read()))
        domains.extend(domains_from_file)

    token = os.environ.get(args.token_env)
    if not token:
        log.error("set %s; the scopes and the channel evidence both need one",
                  args.token_env)
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + token})
    r = s.get(API + "auth.test", timeout=30)
    who = r.json()
    if who.get("ok") is not True:
        log.error("auth.test  unavailable    %s", who.get("error"))
        return 2
    scopes = None
    header = r.headers.get("X-OAuth-Scopes")
    if header:
        scopes = [p.strip() for p in header.split(",") if p.strip()]
    log.info("identity   %s in %s", who.get("user_id"), who.get("team"))
    log.info("scopes     %s", ",".join(scopes) if scopes else "not reported")
    log.info("manifest   %d unfurl domain(s), link_shared %s", len(domains),
             "subscribed" if events and "link_shared" in events
             else "not subscribed" if events is not None else "unknown")

    broken = 0
    for entry in domains:
        verdict, detail = registration_fault(entry)
        if verdict != "usable":
            broken += 1
            log.warning("domain     %-14s %s", verdict, detail)

    gap, detail = precondition_gap(domains, events, scopes)
    (log.info if gap == "ready" else log.warning)("gap        %-14s %s", gap, detail)

    own = {who.get("user_id"), who.get("bot_id"), who.get("app_id")}
    tally = {}
    for channel in args.channel:
        body = s.get(API + "conversations.history", timeout=30,
                     params={"channel": channel, "limit": str(args.limit)}).json()
        if body.get("ok") is not True:
            log.warning("history    unavailable    %s: %s", channel, body.get("error"))
            continue
        messages = body.get("messages") or []
        log.info("history    %d message(s) read from %s", len(messages), channel)
        for msg in messages:
            verdict, _, urls = unfurl_state(msg, own, domains)
            if verdict == "no-links":
                continue
            tally[verdict] = tally.get(verdict, 0) + len(urls)

    for verdict in ("not-unfurled", "off-domain", "self-posted", "unfurled"):
        if verdict in tally:
            (log.info if verdict == "unfurled" else log.warning)(
                "links      %-14s %d link(s)", verdict, tally[verdict])

    if gap != "ready" or broken or tally.get("not-unfurled"):
        log.warning("verdict    unfurling cannot work as configured")
        if broken or gap == "no-domains":
            log.warning("  repair: register the apex domain under Event Subscriptions, "
                        "App unfurl domains. Slack matches it and every subdomain")
        if gap == "not-subscribed":
            log.warning("  repair: subscribe to link_shared under Subscribe to bot "
                        "events; registering the domain does not do it for you")
        if gap in ("no-links-read", "no-links-write"):
            log.warning("  repair: add links:read and links:write to the bot scopes "
                        "and reinstall the app; a scope change needs a fresh grant")
        if not tally:
            log.warning("  note: no evidence was read. Pass --channel with a channel "
                        "where people paste your links, and note that links the app "
                        "posts itself never fire the event")
        return 1
    log.info("verdict    clean          the configuration allows unfurling")
    return 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-unfurl-silence.mjs",
"js": '''/**
 * Find out why your links never unfurl, when nothing reports an error anywhere.
 *
 * Read only. This reads the app manifest you exported, the scopes on the
 * token, and messages already in a channel. It never posts a link, never calls
 * chat.unfurl, and never changes the app configuration.
 *
 * Unfurling has four preconditions: the domain is registered under App unfurl
 * domains, link_shared is subscribed, the token holds links:read to receive
 * the event and links:write to answer it. Every one fails silently.
 */

import { readFile } from 'node:fs/promises';

const API = 'https://slack.com/api/';

// Slack rewrites links in message text as <url> or <url|label>. Anything left
// after those are removed is a bare URL somebody typed.
const LINK_MARKUP = /<(https?:\\/\\/[^>|\\s]+)(?:\\|[^>]*)?>/g;
const BARE_URL = /https?:\\/\\/[^\\s<>|]+/g;

/** Every URL in a message's text, unwrapped from Slack's markup. Pure. */
export function linkUrls(text) {
  const body = String(text ?? '');
  const found = [...body.matchAll(LINK_MARKUP)].map((m) => m[1]);
  found.push(...(body.replace(LINK_MARKUP, ' ').match(BARE_URL) ?? []));
  const out = [];
  for (const url of found) {
    const cleaned = url.replace(/[.,;:)\\]>]+$/, '');
    if (cleaned && !out.includes(cleaned)) out.push(cleaned);
  }
  return out;
}

/** The host part of a URL, lowercased and stripped of everything else. Pure. */
export function hostOf(url) {
  let text = String(url ?? '').trim();
  if (text.includes('://')) [, text] = text.split('://');
  for (const sep of ['/', '?', '#']) [text] = text.split(sep);
  if (text.includes('@')) text = text.slice(text.indexOf('@') + 1);
  [text] = text.split(':');
  return text.trim().toLowerCase().replace(/\\.+$/, '');
}

/**
 * Is this registered entry a domain Slack can match? Pure.
 * Returns [verdict, detail]; every failing verdict reads fine to a human.
 */
export function registrationFault(value) {
  const raw = String(value ?? '').trim();
  if (!raw) return ['empty', 'an empty entry in the unfurl domain list'];
  if (raw.includes('://')) {
    return ['scheme-included', `${raw} carries a scheme. The field takes a domain, so `
      + 'the scheme becomes part of the string being matched and nothing matches it'];
  }
  if (raw.includes('/')) {
    return ['path-included', `${raw} carries a path. Slack matches on the domain; a `
      + 'path here matches no link'];
  }
  if (raw.startsWith('*.')) {
    return ['wildcard', `${raw} is a wildcard. Slack already matches the registered `
      + 'domain and every subdomain of it, so the literal *. is just a domain that '
      + 'does not exist'];
  }
  if (raw.includes(':')) {
    return ['port-included', `${raw} carries a port, which is not part of the domain `
      + 'Slack compares against'];
  }
  const low = raw.toLowerCase();
  if (!low.includes('.') || low.startsWith('.') || low.endsWith('.')) {
    return ['not-a-domain', `${raw} is not shaped like a domain`];
  }
  if (low.startsWith('www.')) {
    return ['www-prefixed', `${low} matches this domain and its subdomains, and `
      + `${low.slice(4)} is not a subdomain of it. Every link without the www prefix `
      + 'is invisible to the app'];
  }
  return ['usable', `${low} is registered and will match itself and its subdomains`];
}

/** Which registered domain, if any, covers this URL? Pure. */
export function domainMatch(url, registered) {
  const host = hostOf(url);
  if (!host) return '';
  let best = '';
  for (const entry of registered ?? []) {
    const domain = String(entry ?? '').trim().toLowerCase().replace(/\\.+$/, '');
    if (!domain) continue;
    if ((host === domain || host.endsWith(`.${domain}`)) && domain.length > best.length) {
      best = domain;
    }
  }
  return best;
}

/**
 * What does this posted message tell you about unfurling? Pure.
 * Returns [verdict, detail, urls].
 */
export function unfurlState(message, ownIds, registered) {
  const msg = message ?? {};
  const urls = linkUrls(msg.text);
  if (!urls.length) return ['no-links', 'nothing to unfurl in this message', []];
  const author = new Set([String(msg.user ?? ''), String(msg.bot_id ?? ''),
    String(msg.app_id ?? '')].filter(Boolean));
  const mine = [...(ownIds ?? [])].filter(Boolean).map(String);
  if (mine.some((id) => author.has(id))) {
    return ['self-posted', 'this app posted the link. Slack suppresses link_shared for '
      + 'an app\\u2019s own links, so this message is not evidence either way', urls];
  }
  const matched = urls.filter((u) => domainMatch(u, registered));
  if (!matched.length) {
    return ['off-domain', 'no URL here falls under a registered domain, so no '
      + 'link_shared would ever fire for this message', urls];
  }
  const attached = (msg.attachments ?? []).map(
    (a) => String((a ?? {}).app_unfurl_url ?? (a ?? {}).from_url ?? ''));
  for (const url of matched) {
    if (attached.includes(url)) {
      return ['unfurled', `${url} came back with an unfurl attached`, matched];
    }
  }
  if ((msg.attachments ?? []).length) {
    return ['not-unfurled', `${msg.attachments.length} attachment(s) on this message `
      + `and none of them is an unfurl of ${matched[0]}`, matched];
  }
  return ['not-unfurled', `${matched[0]} is on a registered domain and posted with no `
    + 'unfurl at all', matched];
}

/** Which of the four preconditions is missing, in fix order? Pure. */
export function preconditionGap(domains, events, scopes) {
  const usable = (domains ?? []).filter((d) => registrationFault(d)[0] === 'usable');
  if (!usable.length) {
    return ['no-domains', 'no usable domain is registered under App unfurl domains, so '
      + 'link_shared cannot fire for any link at all. This is the first thing to fix '
      + 'and nothing after it can be tested until it is done'];
  }
  if (events !== null && events !== undefined && !new Set(events).has('link_shared')) {
    return ['not-subscribed', `${usable.length} domain(s) are registered and `
      + 'link_shared is not in the subscribed bot events. Registering the domain does '
      + 'not subscribe the event'];
  }
  if (scopes === null || scopes === undefined) {
    return ['scopes-unread', 'the domain and the subscription are in place; the granted '
      + 'scopes were not read, so links:read and links:write are unverified'];
  }
  const held = new Set(scopes.map((s) => String(s).trim()));
  if (!held.has('links:read')) {
    return ['no-links-read', 'links:read is not granted, so the event will not be '
      + 'delivered however the domain is registered. This is the silent one: no error '
      + 'appears anywhere'];
  }
  if (!held.has('links:write')) {
    return ['no-links-write', 'links:read is granted so the event can arrive, but '
      + 'chat.unfurl needs links:write to answer it. This one fails loudly, after your '
      + 'handler has already done its work'];
  }
  return ['ready', 'all four preconditions are in place: a registered domain, the '
    + 'link_shared subscription, links:read and links:write'];
}

/** Pull the unfurl domains and subscribed bot events out of a manifest. */
export function manifestFacts(manifest) {
  const doc = (manifest ?? {}).manifest ?? manifest ?? {};
  const events = ((doc.settings ?? {}).event_subscriptions ?? {}).bot_events;
  return [[...((doc.features ?? {}).unfurl_domains ?? [])], events];
}

function arg(args, name, fallback = null) {
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
  const domains = argAll(args, '--domain');
  let events = null;
  const manifestFile = arg(args, '--manifest', '');
  if (manifestFile) {
    const [fromFile, subscribed] = manifestFacts(
      JSON.parse(await readFile(manifestFile, 'utf8')));
    domains.push(...fromFile);
    events = subscribed ?? null;
  }

  const tokenEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
  const token = process.env[tokenEnv];
  if (!token) {
    console.error(`set ${tokenEnv}; the scopes and the channel evidence both need one`);
    process.exitCode = 2;
    return;
  }
  const headers = { Authorization: `Bearer ${token}` };
  const r = await fetch(`${API}auth.test`, { headers });
  const who = await r.json();
  if (who.ok !== true) {
    console.error(`auth.test  unavailable    ${who.error}`);
    process.exitCode = 2;
    return;
  }
  const header = r.headers.get('x-oauth-scopes');
  const scopes = header ? header.split(',').map((p) => p.trim()).filter(Boolean) : null;
  console.log(`identity   ${who.user_id} in ${who.team}`);
  console.log(`scopes     ${scopes ? scopes.join(',') : 'not reported'}`);
  console.log(`manifest   ${domains.length} unfurl domain(s), link_shared `
    + `${events === null ? 'unknown' : (new Set(events).has('link_shared')
      ? 'subscribed' : 'not subscribed')}`);

  let broken = 0;
  for (const entry of domains) {
    const [verdict, detail] = registrationFault(entry);
    if (verdict !== 'usable') {
      broken += 1;
      console.warn(`domain     ${verdict.padEnd(14)} ${detail}`);
    }
  }

  const [gap, gapDetail] = preconditionGap(domains, events, scopes);
  const gapLine = `gap        ${gap.padEnd(14)} ${gapDetail}`;
  if (gap === 'ready') console.log(gapLine); else console.warn(gapLine);

  const own = new Set([who.user_id, who.bot_id, who.app_id]);
  const tally = {};
  const limit = arg(args, '--limit', '200');
  for (const channel of argAll(args, '--channel')) {
    const qs = new URLSearchParams({ channel, limit: String(limit) }).toString();
    // eslint-disable-next-line no-await-in-loop
    const body = await (await fetch(`${API}conversations.history?${qs}`, { headers })).json();
    if (body.ok !== true) {
      console.warn(`history    unavailable    ${channel}: ${body.error}`);
      continue;
    }
    const messages = body.messages ?? [];
    console.log(`history    ${messages.length} message(s) read from ${channel}`);
    for (const msg of messages) {
      const [verdict, , urls] = unfurlState(msg, own, domains);
      if (verdict === 'no-links') continue;
      tally[verdict] = (tally[verdict] ?? 0) + urls.length;
    }
  }

  for (const verdict of ['not-unfurled', 'off-domain', 'self-posted', 'unfurled']) {
    if (verdict in tally) {
      const line = `links      ${verdict.padEnd(14)} ${tally[verdict]} link(s)`;
      if (verdict === 'unfurled') console.log(line); else console.warn(line);
    }
  }

  if (gap !== 'ready' || broken || tally['not-unfurled']) {
    console.warn('verdict    unfurling cannot work as configured');
    if (broken || gap === 'no-domains') {
      console.warn('  repair: register the apex domain under Event Subscriptions, App '
        + 'unfurl domains. Slack matches it and every subdomain');
    }
    if (gap === 'not-subscribed') {
      console.warn('  repair: subscribe to link_shared under Subscribe to bot events; '
        + 'registering the domain does not do it for you');
    }
    if (gap === 'no-links-read' || gap === 'no-links-write') {
      console.warn('  repair: add links:read and links:write to the bot scopes and '
        + 'reinstall the app; a scope change needs a fresh grant');
    }
    if (!Object.keys(tally).length) {
      console.warn('  note: no evidence was read. Pass --channel with a channel where '
        + 'people paste your links, and note that links the app posts itself never '
        + 'fire the event');
    }
    process.exitCode = 1;
  } else {
    console.log('verdict    clean          the configuration allows unfurling');
  }
}

// Only run when invoked directly, so importing this module in the tests does
// not execute main() and fail the file on a missing token.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The tests that matter are the ones that keep the matching rule honest. <code>domain_match</code> has to match a subdomain of a registered apex and refuse the reverse, because that asymmetry is the entire <code>www.</code> mistake. <code>precondition_gap</code> has to return the <em>first</em> missing switch rather than a list, and has to keep <code>no-links-read</code> and <code>no-links-write</code> apart, since one is silence and the other is a loud error at the far end of the handler. And <code>unfurl_state</code> has to call the app's own links <code>self-posted</code> rather than counting them as failures, which is the assertion that stops the script from lying about its evidence.",
"test_py_file": "test_slack_unfurl_silence.py",
"test_py": '''from slack_unfurl_silence import (domain_match, host_of, link_urls, manifest_facts,
                                  precondition_gap, registration_fault, unfurl_state)

OWN = {"U024BE7LH", "B024BE7LH", "A024BE7LH"}
REG = ["acme.dev"]


def msg(text, **kw):
    row = {"text": text, "user": "U07J4K2QT"}
    row.update(kw)
    return row


def test_slack_link_markup_is_unwrapped():
    assert link_urls("see <https://acme.dev/docs|the docs>") == ["https://acme.dev/docs"]
    assert link_urls("see <https://acme.dev/docs>") == ["https://acme.dev/docs"]


def test_a_bare_url_is_found_too_and_duplicates_collapse():
    assert link_urls("https://acme.dev/a and https://acme.dev/a") == \\
        ["https://acme.dev/a"]


def test_trailing_punctuation_is_not_part_of_the_url():
    assert link_urls("try https://acme.dev/x.") == ["https://acme.dev/x"]


def test_a_message_with_no_link_yields_nothing():
    assert link_urls("no links here") == []
    assert link_urls(None) == []


def test_the_host_is_stripped_of_everything_that_is_not_the_host():
    assert host_of("https://Acme.dev:8443/docs?a=1#b") == "acme.dev"
    assert host_of("http://user@acme.dev/") == "acme.dev"
    assert host_of("acme.dev.") == "acme.dev"


def test_an_apex_matches_itself_and_its_subdomains():
    assert domain_match("https://acme.dev/x", REG) == "acme.dev"
    assert domain_match("https://docs.acme.dev/x", REG) == "acme.dev"
    assert domain_match("https://a.b.acme.dev/x", REG) == "acme.dev"


def test_a_subdomain_registration_does_not_match_the_apex():
    assert domain_match("https://acme.dev/x", ["www.acme.dev"]) == ""
    assert domain_match("https://www.acme.dev/x", ["www.acme.dev"]) == "www.acme.dev"


def test_a_lookalike_domain_does_not_match():
    assert domain_match("https://notacme.dev/x", REG) == ""
    assert domain_match("https://acme.dev.evil.example/x", REG) == ""


def test_the_most_specific_registered_domain_wins():
    assert domain_match("https://docs.acme.dev/x",
                        ["acme.dev", "docs.acme.dev"]) == "docs.acme.dev"


def test_a_plain_apex_is_the_only_usable_registration():
    assert registration_fault("acme.dev")[0] == "usable"
    assert registration_fault("ACME.dev")[0] == "usable"


def test_every_way_of_writing_a_domain_wrong_gets_its_own_verdict():
    assert registration_fault("https://acme.dev")[0] == "scheme-included"
    assert registration_fault("acme.dev/docs")[0] == "path-included"
    assert registration_fault("*.acme.dev")[0] == "wildcard"
    assert registration_fault("acme.dev:443")[0] == "port-included"
    assert registration_fault("localhost")[0] == "not-a-domain"
    assert registration_fault("")[0] == "empty"


def test_a_www_registration_is_named_as_the_trap_it_is():
    verdict, detail = registration_fault("www.acme.dev")
    assert verdict == "www-prefixed"
    assert "acme.dev is not a subdomain" in detail


def test_no_registered_domain_is_the_first_thing_reported():
    verdict, detail = precondition_gap([], ["link_shared"],
                                       ["links:read", "links:write"])
    assert verdict == "no-domains"
    assert "nothing after it can be tested" in detail


def test_an_unusable_domain_counts_as_no_domain_at_all():
    assert precondition_gap(["https://acme.dev"], ["link_shared"], ["links:read"])[0] \\
        == "no-domains"


def test_a_registered_domain_with_no_subscription_names_the_subscription():
    verdict, detail = precondition_gap(REG, ["app_mention"], ["links:read"])
    assert verdict == "not-subscribed"
    assert "does not subscribe the event" in detail


def test_the_two_link_scopes_fail_at_opposite_ends():
    silent, detail = precondition_gap(REG, ["link_shared"], ["chat:write"])
    assert silent == "no-links-read"
    assert "no error appears anywhere" in detail
    loud, detail = precondition_gap(REG, ["link_shared"], ["links:read"])
    assert loud == "no-links-write"
    assert "fails loudly" in detail


def test_unread_scopes_are_not_reported_as_granted():
    assert precondition_gap(REG, ["link_shared"], None)[0] == "scopes-unread"


def test_all_four_in_place_is_ready():
    assert precondition_gap(REG, ["link_shared"],
                            ["links:read", "links:write"])[0] == "ready"


def test_a_registered_link_with_no_attachment_is_the_finding():
    verdict, detail, urls = unfurl_state(msg("look at https://acme.dev/x"), OWN, REG)
    assert verdict == "not-unfurled"
    assert urls == ["https://acme.dev/x"]
    assert "no unfurl at all" in detail


def test_an_unfurled_link_is_recognised_by_its_attachment():
    message = msg("look at https://acme.dev/x",
                  attachments=[{"app_unfurl_url": "https://acme.dev/x"}])
    assert unfurl_state(message, OWN, REG)[0] == "unfurled"


def test_an_unrelated_attachment_does_not_count_as_an_unfurl():
    message = msg("look at https://acme.dev/x",
                  attachments=[{"from_url": "https://example.com/other"}])
    verdict, detail, _ = unfurl_state(message, OWN, REG)
    assert verdict == "not-unfurled"
    assert "none of them is an unfurl" in detail


def test_the_apps_own_link_is_excluded_from_the_evidence():
    message = msg("here is https://acme.dev/x", user="U024BE7LH")
    verdict, detail, _ = unfurl_state(message, OWN, REG)
    assert verdict == "self-posted"
    assert "not evidence either way" in detail


def test_a_link_on_an_unregistered_domain_is_its_own_row():
    verdict, detail, _ = unfurl_state(msg("see https://example.com/x"), OWN, REG)
    assert verdict == "off-domain"
    assert "would ever fire" in detail


def test_off_domain_and_not_unfurled_are_never_collapsed():
    assert unfurl_state(msg("https://example.com/x"), OWN, REG)[0] \\
        != unfurl_state(msg("https://acme.dev/x"), OWN, REG)[0]


def test_the_manifest_gives_up_both_lists_through_either_wrapper():
    doc = {"features": {"unfurl_domains": ["acme.dev"]},
           "settings": {"event_subscriptions": {"bot_events": ["link_shared"]}}}
    assert manifest_facts(doc) == (["acme.dev"], ["link_shared"])
    assert manifest_facts({"manifest": doc}) == (["acme.dev"], ["link_shared"])
    assert manifest_facts({}) == ([], None)
''',
"test_js_file": "slack-unfurl-silence.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  domainMatch, hostOf, linkUrls, manifestFacts, preconditionGap, registrationFault,
  unfurlState,
} from './slack-unfurl-silence.mjs';

const OWN = new Set(['U024BE7LH', 'B024BE7LH', 'A024BE7LH']);
const REG = ['acme.dev'];

const msg = (text, over = {}) => ({ text, user: 'U07J4K2QT', ...over });

test('Slack link markup is unwrapped', () => {
  assert.deepEqual(linkUrls('see <https://acme.dev/docs|the docs>'),
    ['https://acme.dev/docs']);
  assert.deepEqual(linkUrls('see <https://acme.dev/docs>'), ['https://acme.dev/docs']);
});

test('a bare url is found too and duplicates collapse', () => {
  assert.deepEqual(linkUrls('https://acme.dev/a and https://acme.dev/a'),
    ['https://acme.dev/a']);
});

test('trailing punctuation is not part of the url', () => {
  assert.deepEqual(linkUrls('try https://acme.dev/x.'), ['https://acme.dev/x']);
});

test('a message with no link yields nothing', () => {
  assert.deepEqual(linkUrls('no links here'), []);
  assert.deepEqual(linkUrls(null), []);
});

test('the host is stripped of everything that is not the host', () => {
  assert.equal(hostOf('https://Acme.dev:8443/docs?a=1#b'), 'acme.dev');
  assert.equal(hostOf('http://user@acme.dev/'), 'acme.dev');
  assert.equal(hostOf('acme.dev.'), 'acme.dev');
});

test('an apex matches itself and its subdomains', () => {
  assert.equal(domainMatch('https://acme.dev/x', REG), 'acme.dev');
  assert.equal(domainMatch('https://docs.acme.dev/x', REG), 'acme.dev');
  assert.equal(domainMatch('https://a.b.acme.dev/x', REG), 'acme.dev');
});

test('a subdomain registration does not match the apex', () => {
  assert.equal(domainMatch('https://acme.dev/x', ['www.acme.dev']), '');
  assert.equal(domainMatch('https://www.acme.dev/x', ['www.acme.dev']), 'www.acme.dev');
});

test('a lookalike domain does not match', () => {
  assert.equal(domainMatch('https://notacme.dev/x', REG), '');
  assert.equal(domainMatch('https://acme.dev.evil.example/x', REG), '');
});

test('the most specific registered domain wins', () => {
  assert.equal(domainMatch('https://docs.acme.dev/x', ['acme.dev', 'docs.acme.dev']),
    'docs.acme.dev');
});

test('a plain apex is the only usable registration', () => {
  assert.equal(registrationFault('acme.dev')[0], 'usable');
  assert.equal(registrationFault('ACME.dev')[0], 'usable');
});

test('every way of writing a domain wrong gets its own verdict', () => {
  assert.equal(registrationFault('https://acme.dev')[0], 'scheme-included');
  assert.equal(registrationFault('acme.dev/docs')[0], 'path-included');
  assert.equal(registrationFault('*.acme.dev')[0], 'wildcard');
  assert.equal(registrationFault('acme.dev:443')[0], 'port-included');
  assert.equal(registrationFault('localhost')[0], 'not-a-domain');
  assert.equal(registrationFault('')[0], 'empty');
});

test('a www registration is named as the trap it is', () => {
  const [verdict, detail] = registrationFault('www.acme.dev');
  assert.equal(verdict, 'www-prefixed');
  assert.match(detail, /acme\\.dev is not a subdomain/);
});

test('no registered domain is the first thing reported', () => {
  const [verdict, detail] = preconditionGap([], ['link_shared'],
    ['links:read', 'links:write']);
  assert.equal(verdict, 'no-domains');
  assert.match(detail, /nothing after it can be tested/);
});

test('an unusable domain counts as no domain at all', () => {
  assert.equal(preconditionGap(['https://acme.dev'], ['link_shared'],
    ['links:read'])[0], 'no-domains');
});

test('a registered domain with no subscription names the subscription', () => {
  const [verdict, detail] = preconditionGap(REG, ['app_mention'], ['links:read']);
  assert.equal(verdict, 'not-subscribed');
  assert.match(detail, /does not subscribe the event/);
});

test('the two link scopes fail at opposite ends', () => {
  const [silent, silentDetail] = preconditionGap(REG, ['link_shared'], ['chat:write']);
  assert.equal(silent, 'no-links-read');
  assert.match(silentDetail, /no error appears anywhere/);
  const [loud, loudDetail] = preconditionGap(REG, ['link_shared'], ['links:read']);
  assert.equal(loud, 'no-links-write');
  assert.match(loudDetail, /fails loudly/);
});

test('unread scopes are not reported as granted', () => {
  assert.equal(preconditionGap(REG, ['link_shared'], null)[0], 'scopes-unread');
});

test('all four in place is ready', () => {
  assert.equal(preconditionGap(REG, ['link_shared'], ['links:read', 'links:write'])[0],
    'ready');
});

test('a registered link with no attachment is the finding', () => {
  const [verdict, detail, urls] = unfurlState(msg('look at https://acme.dev/x'),
    OWN, REG);
  assert.equal(verdict, 'not-unfurled');
  assert.deepEqual(urls, ['https://acme.dev/x']);
  assert.match(detail, /no unfurl at all/);
});

test('an unfurled link is recognised by its attachment', () => {
  const message = msg('look at https://acme.dev/x',
    { attachments: [{ app_unfurl_url: 'https://acme.dev/x' }] });
  assert.equal(unfurlState(message, OWN, REG)[0], 'unfurled');
});

test('an unrelated attachment does not count as an unfurl', () => {
  const message = msg('look at https://acme.dev/x',
    { attachments: [{ from_url: 'https://example.com/other' }] });
  const [verdict, detail] = unfurlState(message, OWN, REG);
  assert.equal(verdict, 'not-unfurled');
  assert.match(detail, /none of them is an unfurl/);
});

test('the app\\u2019s own link is excluded from the evidence', () => {
  const [verdict, detail] = unfurlState(
    msg('here is https://acme.dev/x', { user: 'U024BE7LH' }), OWN, REG);
  assert.equal(verdict, 'self-posted');
  assert.match(detail, /not evidence either way/);
});

test('a link on an unregistered domain is its own row', () => {
  const [verdict, detail] = unfurlState(msg('see https://example.com/x'), OWN, REG);
  assert.equal(verdict, 'off-domain');
  assert.match(detail, /would ever fire/);
});

test('off-domain and not-unfurled are never collapsed', () => {
  assert.notEqual(unfurlState(msg('https://example.com/x'), OWN, REG)[0],
    unfurlState(msg('https://acme.dev/x'), OWN, REG)[0]);
});

test('the manifest gives up both lists through either wrapper', () => {
  const doc = {
    features: { unfurl_domains: ['acme.dev'] },
    settings: { event_subscriptions: { bot_events: ['link_shared'] } },
  };
  assert.deepEqual(manifestFacts(doc), [['acme.dev'], ['link_shared']]);
  assert.deepEqual(manifestFacts({ manifest: doc }), [['acme.dev'], ['link_shared']]);
  assert.deepEqual(manifestFacts({}), [[], undefined]);
});
''',
"faq": [
 ("Why is there no error anywhere when the domain is not registered?",
  "Because nothing failed. Slack decides which apps to notify about a shared link, your app is not on the list for that domain, and so no event is created. There is no request to reject and no response to carry an error. This is the same reason a missing event subscription is silent: the failure is an absence, and absences do not have error codes."),
 ("Do I register the apex domain or every subdomain?",
  "The apex. Slack matches a registered domain and its subdomains, so registering acme.dev covers docs.acme.dev and app.acme.dev. The mistake worth avoiding is the reverse: registering www.acme.dev covers only that host and its subdomains, and acme.dev is not one of them, so every link without the www prefix stays silent."),
 ("The bot posts its own links and they never unfurl. Is that the same bug?",
  "No, and it is why testing this is awkward. Slack deliberately suppresses link_shared for links an app posts itself, so a link the bot posted would not unfurl even with everything configured correctly. Test with a link a human posts, which is why the script separates the app's own links out of its evidence rather than counting them."),
 ("We have links:read. Is that enough?",
  "It is enough to receive the event and not enough to answer it. chat.unfurl needs links:write, and without it your handler runs, does its work, and fails on the last line with missing_scope. The two scopes produce completely different symptoms, so it is worth knowing which one you are missing before you start reading handler code."),
 ("We added the domain and the scopes and it still does nothing. What is left?",
  "A reinstall. Adding a scope changes the token grant, and the grant your app is running with was issued before the change. Also check that the event is actually subscribed rather than only available: registering the domain and holding the scope makes link_shared subscribable, and subscribing to it is a separate click."),
],
"related": [
 ("/slack/no-event-subscriptions/", "the same silence, one switch further back"),
 ("/slack/event-scope-mismatch/", "an event that is subscribed and still never arrives"),
 ("/slack/missing-scope-on-read/", "how to read what the token was actually granted"),
],
"citations": [CITE_LINK_SHARED, CITE_CHAT_UNFURL, CITE_UNFURLING, CITE_MANIFEST],
})

GUIDES.append({
"slug": "trigger-id-expired",
"title": "expired_trigger_id: the modal opened a moment too late",
"description": "A trigger_id is single use and lives seconds, not minutes. Measure the wait before views.open and tell expired, exchanged and invalid triggers apart.",
"h1": "expired_trigger_id: the modal opened a moment too late",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack expired_trigger_id",
             "slack exchanged_trigger_id views.push",
             "slack invalid_trigger_id",
             "slack trigger_id expires",
             "slack views.open modal not opening"],
"deps": "Python 3.9+ with requests, or Node.js 18+; a bot token with channels:history, plus a JSON ledger of your own interaction timings",
"lead": "Clicking the button opens the modal about four times out of five. The fifth time the user gets <em>We had some trouble connecting. Try again?</em>, clicks again, and it works. Nobody can reproduce it on a laptop, and it happens constantly in production on Monday mornings.</p><p>The logs show <code>views.open</code> returning <code>{\"ok\": false, \"error\": \"expired_trigger_id\"}</code> after 400 milliseconds. Four hundred milliseconds, against a limit everyone remembers as three seconds. The number in the documentation is the ceiling, and what you actually have is whatever is left of it once the click has crossed the internet twice.",
"short_answer": """<p>A <code>trigger_id</code> is not a session, a token or a handle. It is <strong>a single-use permission to interrupt one person with one view, and it expires almost immediately</strong> &mdash; nominally three seconds from the interaction, in practice often much less, because the clock starts when the user clicks and not when your handler wakes up.</p>
<p>Three errors come out of this and they mean three different things. <code>expired_trigger_id</code>: you were too slow, and everything you did before <code>views.open</code> is why. <code>exchanged_trigger_id</code>: this trigger was already spent, and a trigger opens exactly one view. <code>invalid_trigger_id</code>: the value is not a trigger at all &mdash; truncated, from a different payload, or logged and copied by hand.</p>
<p>The repair is one sentence with no exceptions in it: <strong>call <code>views.open</code> as the first thing the handler does</strong>, before the database read, before the API call, before anything. Open a modal that says Loading, get back a <code>view.id</code>, and fill it in with <code>views.update</code> when the data arrives. <code>views.update</code> takes a <code>view_id</code> and has no deadline at all.</p>
<p>None of this is visible to a read-only token, which is the honest limit here: Slack does not expose trigger state. What is visible is your own timing ledger, which decides it, and the workspace, which shows the side effects that never landed because the modal never opened.</p>""",
"problem": """<p>The reason this is hard to see is that the budget is spent before your code is involved. Three seconds is measured from the interaction, and by the time the payload reaches your handler it has crossed the internet, been queued by your load balancer, and possibly started a cold container. Reports of expiry inside 500 milliseconds of handler time are common, which means the visible margin can be a fraction of what the documentation implies. You are not spending three seconds. You are spending what is left.</p>
<p>So the ordinary things a handler does become the bug. A lookup in the installation store. A permissions check against your own database. Fetching the options for a select menu so the modal can be rendered fully populated &mdash; which is the most reasonable-looking mistake in the whole category, because it produces a better modal and it is exactly the thing that must not happen first.</p>
<p><strong>Single use is the second half.</strong> A trigger opens one view. A handler that opens a modal and then pushes a second one onto the stack with the same <code>trigger_id</code> gets <code>exchanged_trigger_id</code>, and every retry of that handler does the same. Slack does hand you a fresh <code>trigger_id</code> on the <code>view_submission</code> payload precisely so you can open a follow-up view after a submit &mdash; and code that reaches for the trigger it captured at the start of the flow will use a value that was spent two views ago.</p>
<p>Retries make both worse. When a handler is slow enough to miss the ack, Slack retries the delivery, and the retry arrives carrying a trigger that is now even older. The user clicks again out of frustration, which generates a genuinely fresh trigger, and that one works &mdash; which is why the bug presents as intermittent and unreproducible rather than as a deadline.</p>
<p>And a failed <code>views.open</code> is quiet in the wrong way. The user gets a generic connection message, your handler logs one line, and the work the modal was meant to collect simply never happens. There is no half-finished record to find later. The absence is the only evidence.</p>""",
"why": """<p><strong>This deadline is not the ack deadline, and confusing them sends you to the wrong repair.</strong> The three-second ack is about returning 2xx and can be satisfied by acknowledging and then working in the background. The trigger deadline cannot: <code>views.open</code> is the work, and moving it into a background queue guarantees expiry. One is fixed by deferring, the other by refusing to defer.</p>
<p><strong>The three errors are three different bugs wearing similar names.</strong> Slow, spent and malformed want different fixes, and a handler that retries on all three will loop forever on two of them. The script maps each error to its own cause so the retry policy can too.</p>
<p><strong>The measurement that matters is the handler's own, and only you have it.</strong> Slack reports nothing about trigger state, so the ledger is the instrument: when the payload arrived, when <code>views.open</code> was called, what happened in between. Anything under about 150 milliseconds means the call really is first; anything above a second is living on margin that Monday morning will take away.</p>
<p><strong>A trigger used twice is a structural bug, not a slow one.</strong> Making the handler faster does nothing for <code>exchanged_trigger_id</code>, and the reflex fix &mdash; adding a retry &mdash; makes it worse. Counting how often each trigger appears in the ledger separates the two before anyone starts optimising the wrong thing.</p>
<p><strong>Passing a trigger to a call that does not want one is worth naming.</strong> <code>views.update</code> identifies a view by <code>view_id</code>. Code that carries a trigger into it has usually misunderstood the model, and that misunderstanding is what produces the reuse in the first place.</p>
<p><strong>The workspace holds the consequence, even though it cannot hold the cause.</strong> A modal that never opened is a record that never appeared. If the ledger says the flow started and the channel has nothing to show for it, the missing side effect confirms that these failures are costing real work rather than only producing log lines.</p>""",
"steps": [
 {"h": "Record two timestamps per interaction and nothing else",
  "body": """<p>The ledger needs the moment the payload arrived and the moment <code>views.open</code> was called. Everything else in this note is derived from that pair. If your handler does not record them, adding two lines is the first change, because no amount of reading Slack will recover them afterwards.</p>"""},
 {"h": "Check the shape before you interpret the timing",
  "body": """<p><code>trigger_shape</code> returns <code>usable</code>, <code>not-three-parts</code>, <code>non-numeric-head</code>, <code>not-a-string</code> or <code>missing</code>. A trigger is three dot-separated parts and the first two are numeric. A value that fails this was never going to work at any speed, and it usually means the payload was parsed wrongly or the value was copied out of a log by hand.</p>"""},
 {"h": "Turn each pair of timestamps into a budget verdict",
  "body": """<p><code>budget</code> returns <code>first-thing</code> under 150 milliseconds, <code>tight</code> under a second, <code>at-risk</code> under three, and <code>expired</code> beyond. The thresholds are deliberately stricter than the documented limit, because the documented limit is measured from the click and you only ever see part of it.</p>"""},
 {"h": "Map every observed error to its own cause",
  "body": """<p><code>classify</code> separates <code>too-slow</code>, <code>already-spent</code> and <code>malformed</code>. This is the step that decides your retry policy: retrying is defensible for the first, pointless for the second and harmful for the third, and a single catch-all retry treats them identically.</p>"""},
 {"h": "Count how many times each trigger was used",
  "body": """<p><code>reuse_report</code> finds every <code>trigger_id</code> appearing more than once in the ledger. Each one is an <code>exchanged_trigger_id</code> waiting to happen, and speed will not help. The usual source is a chained modal reusing the trigger it captured at the start rather than the fresh one on the current payload.</p>"""},
 {"h": "Look for the work that never landed",
  "body": """<p>For entries that failed, <code>landed</code> reads <code>conversations.history</code> and asks whether the record the modal was meant to produce ever appeared. That is the read-only half of this note: Slack will not tell you about a trigger, but it will show you the absence of everything that trigger was supposed to lead to.</p>"""},
],
"verify": """<p>Run it against your own interaction ledger and the channel your modals write into.</p>
<pre><code class="language-bash">python3 slack_trigger_budget.py --ledger interactions.json --channel C024BE91L
# identity   U024BE7LH in Acme
# ledger     412 interaction(s) read from interactions.json
# shape      usable         412 of 412
# budget     first-thing    97   tight 148   at-risk 141   expired 26
# budget     at-risk        i-3312 1180ms before views.open; the documented three
#                           seconds is measured from the click, not from your handler
# error      too-slow       26 x expired_trigger_id
#                           the options query runs before views.open in this handler
# error      already-spent  9 x exchanged_trigger_id
# reuse      reused         9 trigger(s) used twice; a trigger opens exactly one view
# source     stale-payload  9 entries reused the trigger from the opening payload
#                           instead of the fresh one on view_submission
# landed     missing        35 flow(s) started and produced no record in C024BE91L
# verdict    35 of 412 interactions lost the modal
#   repair: call views.open as the first statement, with a Loading view, then fill it
#           in with views.update using the returned view.id
#   repair: for a chained view use views.push with the trigger_id on the current
#           payload; view_submission carries a new one for exactly this</code></pre>""",
"code_intro": "Six pure functions and one read, because the cause of this failure is not in Slack. <code>trigger_shape</code> and <code>budget</code> decide almost everything from your own two timestamps. <code>classify</code> keeps the three errors apart, which is what stops a retry policy from looping. <code>reuse_report</code> and <code>source_fault</code> cover the half of this that speed cannot fix. <code>landed</code> is the only one that touches the network, and it asks the workspace what the failures cost.",
"py_file": "slack_trigger_budget.py",
"py": '''"""Measure how long your handlers wait before opening a modal, and why they fail.

Read only. Nothing here opens a view, pushes one, or acknowledges anything: a
trigger_id is single use, so a script that exercised one would consume it. The
timings come from a ledger your own handler writes, and the one Slack call made
here is conversations.history, to ask what the failed flows never produced.

Slack exposes no trigger state at all, which is the honest limit of this note.
What it exposes is the consequence: a modal that never opened is a record that
never appeared.
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_trigger_budget")

API = "https://slack.com/api/"

# Deliberately stricter than the documented three seconds. That three seconds
# is measured from the moment the user clicked, and the handler only ever sees
# what is left after the round trip, the queue and any cold start.
FAST_MS = 150
TIGHT_MS = 1000
LIMIT_MS = 3000

# The two calls that spend a trigger. views.update takes a view_id and has no
# deadline, which is the whole basis of the repair.
NEEDS_TRIGGER = ("views.open", "views.push")


def trigger_shape(value):
    """Is this value shaped like a trigger_id at all? Pure.

    Three dot-separated parts, the first two numeric. A value that fails this
    was never going to work at any speed, and the usual cause is a payload
    parsed wrongly or a value copied out of a log by hand.
    """
    if value is None or (isinstance(value, str) and not value.strip()):
        return ("missing", "no trigger_id on this entry. Interactions carry one and "
                           "view_submission carries a fresh one; a handler that has "
                           "none is reading the wrong field")
    if not isinstance(value, str):
        return ("not-a-string", "a %s. A trigger_id is an opaque string and any "
                                "numeric handling of it destroys it"
                % type(value).__name__)
    parts = value.strip().split(".")
    if len(parts) != 3:
        return ("not-three-parts", "%s has %d dot separated part(s) and a trigger_id "
                                   "has three" % (value[:40], len(parts)))
    if not (parts[0].isdigit() and parts[1].isdigit()):
        return ("non-numeric-head", "%s does not start with two numeric parts"
                % value[:40])
    return ("usable", "shaped like a trigger_id")


def budget(received_ms, opened_ms):
    """How much of the trigger's life did the handler spend? Pure.

    Returns (verdict, detail, elapsed_ms). first-thing is the only verdict that
    means the handler is written the way this note asks for; everything else is
    running on margin that a cold start will take away.
    """
    try:
        elapsed = float(opened_ms) - float(received_ms)
    except (TypeError, ValueError):
        return ("unmeasured", "the entry does not carry both timestamps, so the "
                              "handler cannot be judged. Record the arrival and the "
                              "views.open call", None)
    if elapsed < 0:
        return ("impossible", "views.open is recorded %.0fms before the payload "
                              "arrived, which is a clock or a field mix up rather "
                              "than a fast handler" % -elapsed, elapsed)
    if elapsed < FAST_MS:
        return ("first-thing", "%.0fms; views.open really is the first thing this "
                               "handler does" % elapsed, elapsed)
    if elapsed < TIGHT_MS:
        return ("tight", "%.0fms before views.open. It works today and it is the "
                         "first thing to break on a cold start" % elapsed, elapsed)
    if elapsed < LIMIT_MS:
        return ("at-risk", "%.0fms before views.open; the documented three seconds is "
                           "measured from the click, not from your handler, so the "
                           "real margin is smaller than this looks" % elapsed, elapsed)
    return ("expired", "%.0fms before views.open, past the three second ceiling even "
                       "before the round trip is counted" % elapsed, elapsed)


def classify(error):
    """Which of the three trigger failures is this? Pure.

    They want three different repairs, and a handler that retries all of them
    identically will loop forever on two.
    """
    err = str(error or "").strip()
    if not err:
        return ("no-error", "this interaction opened its view")
    if err == "expired_trigger_id":
        return ("too-slow", "the trigger had already expired when views.open ran. "
                            "Everything the handler did first is the cause; retrying "
                            "with the same trigger cannot succeed")
    if err == "exchanged_trigger_id":
        return ("already-spent", "this trigger had already opened a view. A trigger "
                                 "opens exactly one, and speed has nothing to do with "
                                 "it. Use the trigger on the current payload")
    if err == "invalid_trigger_id":
        return ("malformed", "Slack did not recognise the value as a trigger. It was "
                             "truncated, taken from the wrong field, or belongs to "
                             "another workspace")
    if err in ("not_authed", "invalid_auth", "missing_scope", "channel_not_found"):
        return ("unrelated", "%s is a token or target problem and has nothing to do "
                             "with the trigger" % err)
    return ("unrecognised", "%s is not one of the trigger errors" % err)


def source_fault(entry):
    """Was the trigger taken from the payload in hand? Pure.

    The reuse bug almost always looks like this: a flow captures the trigger it
    was opened with and reaches for that one again three views later, when
    every payload since has carried a fresh one.
    """
    entry = entry or {}
    used = str(entry.get("used_for") or "").strip()
    origin = str(entry.get("trigger_from") or "").strip().lower()
    if not used:
        return ("unknown", "the entry does not say which call the trigger was used for")
    if used not in NEEDS_TRIGGER:
        return ("unnecessary", "%s does not take a trigger_id. views.update "
                               "identifies a view by view_id and has no deadline at "
                               "all, which is the call the slow work belongs behind"
                % used)
    if origin in ("earlier-payload", "original", "first", "captured"):
        return ("stale-payload", "the trigger came from an earlier payload. Every "
                                 "interaction carries its own, and view_submission "
                                 "carries a fresh one for exactly this case")
    if origin in ("this-payload", "current", "fresh"):
        return ("fresh", "the trigger came from the payload being handled")
    return ("unknown", "the entry does not say which payload the trigger came from")


def reuse_report(ledger):
    """Which triggers were spent more than once? Pure.

    Returns (verdict, detail, repeats). This is the half of the note that speed
    cannot fix, so it is counted separately from the timings.
    """
    counts = {}
    for entry in ledger or []:
        tid = str((entry or {}).get("trigger_id") or "")
        if tid:
            counts[tid] = counts.get(tid, 0) + 1
    repeats = {k: v for k, v in counts.items() if v > 1}
    if not repeats:
        return ("single-use", "every trigger in the ledger was used once", {})
    return ("reused", "%d trigger(s) were used more than once. A trigger opens exactly "
                      "one view, so the second use fails with exchanged_trigger_id "
                      "however fast the handler is" % len(repeats), repeats)


def landed(marker, messages):
    """Did the work this flow was meant to produce ever appear? Pure.

    A failed views.open leaves nothing behind: no half written record, no
    partial message. The absence is the only evidence there is.
    """
    needle = str(marker or "").strip()
    if not needle:
        return ("unmarked", "the entry carries no marker, so nothing can be looked for")
    for msg in messages or []:
        if needle in str((msg or {}).get("text") or ""):
            return ("landed", "%s appears in the channel" % needle)
    return ("missing", "%s never appeared. The flow started and produced nothing"
            % needle)


def load_ledger(path):
    raw = json.loads(open(path, encoding="utf-8").read())
    if isinstance(raw, dict):
        raw = raw.get("interactions") or raw.get("entries") or []
    return [r for r in raw or [] if isinstance(r, dict)]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ledger", required=True,
                    help="a JSON file of interactions, each with trigger_id, "
                         "received_ms, opened_ms, used_for, trigger_from and error")
    ap.add_argument("--channel", action="append", default=[],
                    help="a channel your modals write into; repeatable")
    ap.add_argument("--limit", type=int, default=200,
                    help="messages to read per channel when checking side effects")
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN",
                    help="environment variable holding the bot token")
    ap.add_argument("--offline", action="store_true",
                    help="judge the ledger and make no API call at all")
    args = ap.parse_args()

    ledger = load_ledger(args.ledger)
    log.info("ledger     %d interaction(s) read from %s", len(ledger), args.ledger)

    shapes, budgets, errors, sources = {}, {}, {}, {}
    for entry in ledger:
        sverdict, sdetail = trigger_shape(entry.get("trigger_id"))
        shapes[sverdict] = shapes.get(sverdict, 0) + 1
        if sverdict != "usable":
            log.warning("shape      %-16s %s  %s", sverdict, entry.get("id") or "?",
                        sdetail)
        bverdict, bdetail, _ = budget(entry.get("received_ms"), entry.get("opened_ms"))
        budgets[bverdict] = budgets.get(bverdict, 0) + 1
        if bverdict in ("at-risk", "expired", "impossible"):
            log.warning("budget     %-16s %s  %s", bverdict, entry.get("id") or "?",
                        bdetail)
        cause, cdetail = classify(entry.get("error"))
        if cause != "no-error":
            errors.setdefault(cause, [0, cdetail])
            errors[cause][0] += 1
        fverdict, fdetail = source_fault(entry)
        if fverdict not in ("fresh", "unknown"):
            sources.setdefault(fverdict, [0, fdetail])
            sources[fverdict][0] += 1

    log.info("shape      %s", "   ".join("%s %d" % kv for kv in sorted(shapes.items())))
    log.info("budget     %s", "   ".join("%s %d" % kv for kv in sorted(budgets.items())))
    for cause, (count, detail) in sorted(errors.items()):
        log.warning("error      %-16s %d entry(s); %s", cause, count, detail)
    for verdict, (count, detail) in sorted(sources.items()):
        log.warning("source     %-16s %d entry(s); %s", verdict, count, detail)

    rverdict, rdetail, repeats = reuse_report(ledger)
    (log.warning if rverdict == "reused" else log.info)("reuse      %-16s %s",
                                                        rverdict, rdetail)

    lost = 0
    if args.channel and not args.offline:
        token = os.environ.get(args.token_env)
        if not token:
            log.error("set %s, or pass --offline to judge the ledger alone",
                      args.token_env)
            return 2
        s = requests.Session()
        s.headers.update({"Authorization": "Bearer " + token})
        who = s.get(API + "auth.test", timeout=30).json()
        if who.get("ok") is not True:
            log.error("auth.test  unavailable    %s", who.get("error"))
            return 2
        log.info("identity   %s in %s", who.get("user_id"), who.get("team"))
        for channel in args.channel:
            body = s.get(API + "conversations.history", timeout=30,
                         params={"channel": channel,
                                 "limit": str(args.limit)}).json()
            if body.get("ok") is not True:
                log.warning("history    unavailable    %s: %s", channel,
                            body.get("error"))
                continue
            messages = body.get("messages") or []
            for entry in ledger:
                if not entry.get("error"):
                    continue
                verdict, detail = landed(entry.get("marker"), messages)
                if verdict == "missing":
                    lost += 1
        if lost:
            log.warning("landed     missing          %d flow(s) started and produced "
                        "no record", lost)

    failed = sum(count for cause, (count, _) in errors.items()
                 if cause in ("too-slow", "already-spent", "malformed"))
    if failed or repeats or budgets.get("expired") or budgets.get("at-risk"):
        log.warning("verdict    %d interaction(s) lost the modal", failed or lost)
        log.warning("  repair: call views.open as the first statement in the handler, "
                    "with a Loading view, then fill it in with views.update using the "
                    "view.id it returns")
        log.warning("  repair: for a chained view use views.push with the trigger_id "
                    "on the current payload; view_submission carries a new one for "
                    "exactly this")
        log.warning("  repair: retry expired_trigger_id never, since the trigger is "
                    "gone; fix the handler order instead")
        return 1
    log.info("verdict    clean          every interaction opened its view in time")
    return 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-trigger-budget.mjs",
"js": '''/**
 * Measure how long your handlers wait before opening a modal, and why they fail.
 *
 * Read only. Nothing here opens a view, pushes one, or acknowledges anything: a
 * trigger_id is single use, so a script that exercised one would consume it.
 * The timings come from a ledger your own handler writes, and the one Slack
 * call made here is conversations.history.
 *
 * Slack exposes no trigger state at all, which is the honest limit of this
 * note. What it exposes is the consequence: a modal that never opened is a
 * record that never appeared.
 */

import { readFile } from 'node:fs/promises';

const API = 'https://slack.com/api/';

// Deliberately stricter than the documented three seconds, which is measured
// from the moment the user clicked. The handler only ever sees what is left.
const FAST_MS = 150;
const TIGHT_MS = 1000;
const LIMIT_MS = 3000;

// The two calls that spend a trigger. views.update takes a view_id and has no
// deadline, which is the whole basis of the repair.
const NEEDS_TRIGGER = ['views.open', 'views.push'];

/** Is this value shaped like a trigger_id at all? Pure. */
export function triggerShape(value) {
  if (value === null || value === undefined
      || (typeof value === 'string' && !value.trim())) {
    return ['missing', 'no trigger_id on this entry. Interactions carry one and '
      + 'view_submission carries a fresh one; a handler that has none is reading the '
      + 'wrong field'];
  }
  if (typeof value !== 'string') {
    return ['not-a-string', `a ${typeof value}. A trigger_id is an opaque string and `
      + 'any numeric handling of it destroys it'];
  }
  const parts = value.trim().split('.');
  if (parts.length !== 3) {
    return ['not-three-parts', `${value.slice(0, 40)} has ${parts.length} dot `
      + 'separated part(s) and a trigger_id has three'];
  }
  if (!/^\\d+$/.test(parts[0]) || !/^\\d+$/.test(parts[1])) {
    return ['non-numeric-head', `${value.slice(0, 40)} does not start with two `
      + 'numeric parts'];
  }
  return ['usable', 'shaped like a trigger_id'];
}

/**
 * How much of the trigger's life did the handler spend? Pure.
 * Returns [verdict, detail, elapsedMs].
 */
export function budget(receivedMs, openedMs) {
  const a = Number(receivedMs);
  const b = Number(openedMs);
  if (receivedMs === null || receivedMs === undefined || openedMs === null
      || openedMs === undefined || !Number.isFinite(a) || !Number.isFinite(b)) {
    return ['unmeasured', 'the entry does not carry both timestamps, so the handler '
      + 'cannot be judged. Record the arrival and the views.open call', null];
  }
  const elapsed = b - a;
  if (elapsed < 0) {
    return ['impossible', `views.open is recorded ${(-elapsed).toFixed(0)}ms before `
      + 'the payload arrived, which is a clock or a field mix up rather than a fast '
      + 'handler', elapsed];
  }
  if (elapsed < FAST_MS) {
    return ['first-thing', `${elapsed.toFixed(0)}ms; views.open really is the first `
      + 'thing this handler does', elapsed];
  }
  if (elapsed < TIGHT_MS) {
    return ['tight', `${elapsed.toFixed(0)}ms before views.open. It works today and it `
      + 'is the first thing to break on a cold start', elapsed];
  }
  if (elapsed < LIMIT_MS) {
    return ['at-risk', `${elapsed.toFixed(0)}ms before views.open; the documented `
      + 'three seconds is measured from the click, not from your handler, so the real '
      + 'margin is smaller than this looks', elapsed];
  }
  return ['expired', `${elapsed.toFixed(0)}ms before views.open, past the three second `
    + 'ceiling even before the round trip is counted', elapsed];
}

/** Which of the three trigger failures is this? Pure. */
export function classify(error) {
  const err = String(error ?? '').trim();
  if (!err) return ['no-error', 'this interaction opened its view'];
  if (err === 'expired_trigger_id') {
    return ['too-slow', 'the trigger had already expired when views.open ran. '
      + 'Everything the handler did first is the cause; retrying with the same trigger '
      + 'cannot succeed'];
  }
  if (err === 'exchanged_trigger_id') {
    return ['already-spent', 'this trigger had already opened a view. A trigger opens '
      + 'exactly one, and speed has nothing to do with it. Use the trigger on the '
      + 'current payload'];
  }
  if (err === 'invalid_trigger_id') {
    return ['malformed', 'Slack did not recognise the value as a trigger. It was '
      + 'truncated, taken from the wrong field, or belongs to another workspace'];
  }
  if (['not_authed', 'invalid_auth', 'missing_scope', 'channel_not_found'].includes(err)) {
    return ['unrelated', `${err} is a token or target problem and has nothing to do `
      + 'with the trigger'];
  }
  return ['unrecognised', `${err} is not one of the trigger errors`];
}

/** Was the trigger taken from the payload in hand? Pure. */
export function sourceFault(entry) {
  const e = entry ?? {};
  const used = String(e.used_for ?? '').trim();
  const origin = String(e.trigger_from ?? '').trim().toLowerCase();
  if (!used) {
    return ['unknown', 'the entry does not say which call the trigger was used for'];
  }
  if (!NEEDS_TRIGGER.includes(used)) {
    return ['unnecessary', `${used} does not take a trigger_id. views.update `
      + 'identifies a view by view_id and has no deadline at all, which is the call '
      + 'the slow work belongs behind'];
  }
  if (['earlier-payload', 'original', 'first', 'captured'].includes(origin)) {
    return ['stale-payload', 'the trigger came from an earlier payload. Every '
      + 'interaction carries its own, and view_submission carries a fresh one for '
      + 'exactly this case'];
  }
  if (['this-payload', 'current', 'fresh'].includes(origin)) {
    return ['fresh', 'the trigger came from the payload being handled'];
  }
  return ['unknown', 'the entry does not say which payload the trigger came from'];
}

/**
 * Which triggers were spent more than once? Pure.
 * Returns [verdict, detail, repeats].
 */
export function reuseReport(ledger) {
  const counts = new Map();
  for (const entry of ledger ?? []) {
    const tid = String((entry ?? {}).trigger_id ?? '');
    if (tid) counts.set(tid, (counts.get(tid) ?? 0) + 1);
  }
  const repeats = Object.fromEntries([...counts.entries()].filter(([, v]) => v > 1));
  if (!Object.keys(repeats).length) {
    return ['single-use', 'every trigger in the ledger was used once', {}];
  }
  return ['reused', `${Object.keys(repeats).length} trigger(s) were used more than `
    + 'once. A trigger opens exactly one view, so the second use fails with '
    + 'exchanged_trigger_id however fast the handler is', repeats];
}

/** Did the work this flow was meant to produce ever appear? Pure. */
export function landed(marker, messages) {
  const needle = String(marker ?? '').trim();
  if (!needle) {
    return ['unmarked', 'the entry carries no marker, so nothing can be looked for'];
  }
  for (const msg of messages ?? []) {
    if (String((msg ?? {}).text ?? '').includes(needle)) {
      return ['landed', `${needle} appears in the channel`];
    }
  }
  return ['missing', `${needle} never appeared. The flow started and produced nothing`];
}

function arg(args, name, fallback = null) {
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
  const ledgerFile = arg(args, '--ledger', '');
  if (!ledgerFile) {
    console.error('pass --ledger FILE with your recorded interaction timings');
    process.exitCode = 2;
    return;
  }
  let ledger = JSON.parse(await readFile(ledgerFile, 'utf8'));
  if (!Array.isArray(ledger)) ledger = ledger.interactions ?? ledger.entries ?? [];
  ledger = ledger.filter((r) => r && typeof r === 'object');
  console.log(`ledger     ${ledger.length} interaction(s) read from ${ledgerFile}`);

  const shapes = {};
  const budgets = {};
  const errors = new Map();
  const sources = new Map();
  for (const entry of ledger) {
    const [sv, sd] = triggerShape(entry.trigger_id);
    shapes[sv] = (shapes[sv] ?? 0) + 1;
    if (sv !== 'usable') {
      console.warn(`shape      ${sv.padEnd(16)} ${entry.id ?? '?'}  ${sd}`);
    }
    const [bv, bd] = budget(entry.received_ms, entry.opened_ms);
    budgets[bv] = (budgets[bv] ?? 0) + 1;
    if (['at-risk', 'expired', 'impossible'].includes(bv)) {
      console.warn(`budget     ${bv.padEnd(16)} ${entry.id ?? '?'}  ${bd}`);
    }
    const [cause, cd] = classify(entry.error);
    if (cause !== 'no-error') {
      const row = errors.get(cause) ?? [0, cd];
      errors.set(cause, [row[0] + 1, cd]);
    }
    const [fv, fd] = sourceFault(entry);
    if (fv !== 'fresh' && fv !== 'unknown') {
      const row = sources.get(fv) ?? [0, fd];
      sources.set(fv, [row[0] + 1, fd]);
    }
  }

  console.log(`shape      ${Object.entries(shapes).sort()
    .map(([k, v]) => `${k} ${v}`).join('   ')}`);
  console.log(`budget     ${Object.entries(budgets).sort()
    .map(([k, v]) => `${k} ${v}`).join('   ')}`);
  for (const [cause, [count, detail]] of [...errors.entries()].sort()) {
    console.warn(`error      ${cause.padEnd(16)} ${count} entry(s); ${detail}`);
  }
  for (const [verdict, [count, detail]] of [...sources.entries()].sort()) {
    console.warn(`source     ${verdict.padEnd(16)} ${count} entry(s); ${detail}`);
  }

  const [rv, rd, repeats] = reuseReport(ledger);
  const reuseLine = `reuse      ${rv.padEnd(16)} ${rd}`;
  if (rv === 'reused') console.warn(reuseLine); else console.log(reuseLine);

  let lost = 0;
  const channels = argAll(args, '--channel');
  if (channels.length && !args.includes('--offline')) {
    const tokenEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
    const token = process.env[tokenEnv];
    if (!token) {
      console.error(`set ${tokenEnv}, or pass --offline to judge the ledger alone`);
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
    console.log(`identity   ${who.user_id} in ${who.team}`);
    const limit = arg(args, '--limit', '200');
    for (const channel of channels) {
      const qs = new URLSearchParams({ channel, limit: String(limit) }).toString();
      // eslint-disable-next-line no-await-in-loop
      const body = await (await fetch(`${API}conversations.history?${qs}`, { headers })).json();
      if (body.ok !== true) {
        console.warn(`history    unavailable    ${channel}: ${body.error}`);
        continue;
      }
      for (const entry of ledger) {
        if (!entry.error) continue;
        if (landed(entry.marker, body.messages ?? [])[0] === 'missing') lost += 1;
      }
    }
    if (lost) {
      console.warn(`landed     missing          ${lost} flow(s) started and produced `
        + 'no record');
    }
  }

  const failed = [...errors.entries()]
    .filter(([cause]) => ['too-slow', 'already-spent', 'malformed'].includes(cause))
    .reduce((sum, [, [count]]) => sum + count, 0);
  if (failed || Object.keys(repeats).length || budgets.expired || budgets['at-risk']) {
    console.warn(`verdict    ${failed || lost} interaction(s) lost the modal`);
    console.warn('  repair: call views.open as the first statement in the handler, with '
      + 'a Loading view, then fill it in with views.update using the view.id it returns');
    console.warn('  repair: for a chained view use views.push with the trigger_id on the '
      + 'current payload; view_submission carries a new one for exactly this');
    console.warn('  repair: retry expired_trigger_id never, since the trigger is gone; '
      + 'fix the handler order instead');
    process.exitCode = 1;
  } else {
    console.log('verdict    clean          every interaction opened its view in time');
  }
}

// Only run when invoked directly, so importing this module in the tests does
// not execute main() and fail the file on a missing ledger.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The thresholds are the argument, so they are the tests. <code>budget</code> has to call 140 milliseconds <code>first-thing</code> and 1200 <code>at-risk</code>, because the whole note is that a limit you comfortably meet on a warm afternoon is not margin. <code>classify</code> has to keep <code>too-slow</code> and <code>already-spent</code> apart, since one of them is worth retrying and the other will fail identically forever. And <code>reuse_report</code> has to find a trigger used twice even when both uses are fast, because that failure has nothing to do with time.",
"test_py_file": "test_slack_trigger_budget.py",
"test_py": '''from slack_trigger_budget import (budget, classify, landed, reuse_report,
                                  source_fault, trigger_shape)

GOOD = "13245.67890.abcdef"


def entry(**kw):
    row = {"id": "i-1", "trigger_id": GOOD, "received_ms": 1000, "opened_ms": 1050,
           "used_for": "views.open", "trigger_from": "this-payload", "error": ""}
    row.update(kw)
    return row


def test_three_dotted_parts_with_numeric_heads_is_usable():
    assert trigger_shape(GOOD)[0] == "usable"


def test_a_trigger_with_the_wrong_number_of_parts_is_named():
    verdict, detail = trigger_shape("13245.67890")
    assert verdict == "not-three-parts"
    assert "has three" in detail


def test_a_non_numeric_head_is_its_own_verdict():
    assert trigger_shape("abc.def.ghi")[0] == "non-numeric-head"


def test_a_number_is_refused_rather_than_stringified():
    verdict, detail = trigger_shape(13245.6789)
    assert verdict == "not-a-string"
    assert "opaque string" in detail


def test_a_missing_trigger_points_at_the_field_being_read():
    for value in (None, "", "   "):
        verdict, detail = trigger_shape(value)
        assert verdict == "missing"
        assert "wrong field" in detail


def test_opening_immediately_is_the_only_good_verdict():
    verdict, detail, elapsed = budget(1000, 1140)
    assert verdict == "first-thing"
    assert elapsed == 140
    assert "first thing" in detail


def test_a_few_hundred_milliseconds_is_already_tight():
    assert budget(1000, 1600)[0] == "tight"


def test_over_a_second_is_at_risk_and_says_why_the_margin_is_smaller():
    verdict, detail, _ = budget(1000, 2200)
    assert verdict == "at-risk"
    assert "measured from the click" in detail


def test_past_three_seconds_is_expired():
    assert budget(1000, 4500)[0] == "expired"
    assert budget(1000, 4000)[0] == "expired"


def test_a_negative_elapsed_is_a_clock_problem_not_a_fast_handler():
    verdict, detail, _ = budget(2000, 1000)
    assert verdict == "impossible"
    assert "clock" in detail


def test_missing_timestamps_are_unmeasured_rather_than_zero():
    assert budget(None, 1000)[0] == "unmeasured"
    assert budget(1000, None)[0] == "unmeasured"
    assert budget("soon", 1000)[0] == "unmeasured"


def test_the_three_trigger_errors_get_three_causes():
    assert classify("expired_trigger_id")[0] == "too-slow"
    assert classify("exchanged_trigger_id")[0] == "already-spent"
    assert classify("invalid_trigger_id")[0] == "malformed"


def test_too_slow_and_already_spent_are_never_collapsed():
    assert classify("expired_trigger_id")[0] != classify("exchanged_trigger_id")[0]
    assert "cannot succeed" in classify("expired_trigger_id")[1]
    assert "speed has nothing to do with it" in classify("exchanged_trigger_id")[1]


def test_an_empty_error_means_the_view_opened():
    assert classify("")[0] == "no-error"
    assert classify(None)[0] == "no-error"


def test_a_token_error_is_not_dressed_up_as_a_trigger_error():
    verdict, detail = classify("missing_scope")
    assert verdict == "unrelated"
    assert "nothing to do with the trigger" in detail


def test_an_unknown_error_is_not_guessed_at():
    assert classify("ratelimited")[0] == "unrecognised"


def test_a_trigger_from_the_current_payload_is_fresh():
    assert source_fault(entry())[0] == "fresh"


def test_a_trigger_carried_from_an_earlier_payload_is_the_reuse_bug():
    verdict, detail = source_fault(entry(trigger_from="earlier-payload"))
    assert verdict == "stale-payload"
    assert "view_submission carries a fresh one" in detail


def test_a_trigger_handed_to_views_update_is_unnecessary():
    verdict, detail = source_fault(entry(used_for="views.update"))
    assert verdict == "unnecessary"
    assert "no deadline" in detail


def test_an_entry_that_does_not_say_is_unknown_rather_than_fine():
    assert source_fault(entry(trigger_from=""))[0] == "unknown"
    assert source_fault(entry(used_for=""))[0] == "unknown"


def test_a_trigger_used_twice_is_found_even_when_both_uses_are_fast():
    ledger = [entry(id="i-1", opened_ms=1010), entry(id="i-2", opened_ms=1010)]
    verdict, detail, repeats = reuse_report(ledger)
    assert verdict == "reused"
    assert repeats == {GOOD: 2}
    assert "however fast the handler is" in detail


def test_distinct_triggers_are_single_use():
    ledger = [entry(trigger_id="1.2.aa"), entry(trigger_id="1.3.bb")]
    assert reuse_report(ledger)[0] == "single-use"
    assert reuse_report([])[0] == "single-use"


def test_a_marker_in_the_channel_means_the_flow_finished():
    verdict, _ = landed("REQ-4127", [{"text": "opened REQ-4127 for review"}])
    assert verdict == "landed"


def test_an_absent_marker_is_the_only_evidence_there_is():
    verdict, detail = landed("REQ-4127", [{"text": "something else"}])
    assert verdict == "missing"
    assert "produced nothing" in detail


def test_no_marker_is_not_reported_as_a_missing_record():
    assert landed("", [{"text": "anything"}])[0] == "unmarked"
''',
"test_js_file": "slack-trigger-budget.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  budget, classify, landed, reuseReport, sourceFault, triggerShape,
} from './slack-trigger-budget.mjs';

const GOOD = '13245.67890.abcdef';

const entry = (over = {}) => ({
  id: 'i-1', trigger_id: GOOD, received_ms: 1000, opened_ms: 1050,
  used_for: 'views.open', trigger_from: 'this-payload', error: '', ...over,
});

test('three dotted parts with numeric heads is usable', () => {
  assert.equal(triggerShape(GOOD)[0], 'usable');
});

test('a trigger with the wrong number of parts is named', () => {
  const [verdict, detail] = triggerShape('13245.67890');
  assert.equal(verdict, 'not-three-parts');
  assert.match(detail, /has three/);
});

test('a non numeric head is its own verdict', () => {
  assert.equal(triggerShape('abc.def.ghi')[0], 'non-numeric-head');
});

test('a number is refused rather than stringified', () => {
  const [verdict, detail] = triggerShape(13245.6789);
  assert.equal(verdict, 'not-a-string');
  assert.match(detail, /opaque string/);
});

test('a missing trigger points at the field being read', () => {
  for (const value of [null, undefined, '', '   ']) {
    const [verdict, detail] = triggerShape(value);
    assert.equal(verdict, 'missing');
    assert.match(detail, /wrong field/);
  }
});

test('opening immediately is the only good verdict', () => {
  const [verdict, detail, elapsed] = budget(1000, 1140);
  assert.equal(verdict, 'first-thing');
  assert.equal(elapsed, 140);
  assert.match(detail, /first thing/);
});

test('a few hundred milliseconds is already tight', () => {
  assert.equal(budget(1000, 1600)[0], 'tight');
});

test('over a second is at risk and says why the margin is smaller', () => {
  const [verdict, detail] = budget(1000, 2200);
  assert.equal(verdict, 'at-risk');
  assert.match(detail, /measured from the click/);
});

test('past three seconds is expired', () => {
  assert.equal(budget(1000, 4500)[0], 'expired');
  assert.equal(budget(1000, 4000)[0], 'expired');
});

test('a negative elapsed is a clock problem not a fast handler', () => {
  const [verdict, detail] = budget(2000, 1000);
  assert.equal(verdict, 'impossible');
  assert.match(detail, /clock/);
});

test('missing timestamps are unmeasured rather than zero', () => {
  assert.equal(budget(null, 1000)[0], 'unmeasured');
  assert.equal(budget(1000, undefined)[0], 'unmeasured');
  assert.equal(budget('soon', 1000)[0], 'unmeasured');
});

test('the three trigger errors get three causes', () => {
  assert.equal(classify('expired_trigger_id')[0], 'too-slow');
  assert.equal(classify('exchanged_trigger_id')[0], 'already-spent');
  assert.equal(classify('invalid_trigger_id')[0], 'malformed');
});

test('too slow and already spent are never collapsed', () => {
  assert.notEqual(classify('expired_trigger_id')[0], classify('exchanged_trigger_id')[0]);
  assert.match(classify('expired_trigger_id')[1], /cannot succeed/);
  assert.match(classify('exchanged_trigger_id')[1], /speed has nothing to do with it/);
});

test('an empty error means the view opened', () => {
  assert.equal(classify('')[0], 'no-error');
  assert.equal(classify(null)[0], 'no-error');
});

test('a token error is not dressed up as a trigger error', () => {
  const [verdict, detail] = classify('missing_scope');
  assert.equal(verdict, 'unrelated');
  assert.match(detail, /nothing to do with the trigger/);
});

test('an unknown error is not guessed at', () => {
  assert.equal(classify('ratelimited')[0], 'unrecognised');
});

test('a trigger from the current payload is fresh', () => {
  assert.equal(sourceFault(entry())[0], 'fresh');
});

test('a trigger carried from an earlier payload is the reuse bug', () => {
  const [verdict, detail] = sourceFault(entry({ trigger_from: 'earlier-payload' }));
  assert.equal(verdict, 'stale-payload');
  assert.match(detail, /view_submission carries a fresh one/);
});

test('a trigger handed to views.update is unnecessary', () => {
  const [verdict, detail] = sourceFault(entry({ used_for: 'views.update' }));
  assert.equal(verdict, 'unnecessary');
  assert.match(detail, /no deadline/);
});

test('an entry that does not say is unknown rather than fine', () => {
  assert.equal(sourceFault(entry({ trigger_from: '' }))[0], 'unknown');
  assert.equal(sourceFault(entry({ used_for: '' }))[0], 'unknown');
});

test('a trigger used twice is found even when both uses are fast', () => {
  const ledger = [entry({ id: 'i-1', opened_ms: 1010 }),
    entry({ id: 'i-2', opened_ms: 1010 })];
  const [verdict, detail, repeats] = reuseReport(ledger);
  assert.equal(verdict, 'reused');
  assert.deepEqual(repeats, { [GOOD]: 2 });
  assert.match(detail, /however fast the handler is/);
});

test('distinct triggers are single use', () => {
  assert.equal(reuseReport([entry({ trigger_id: '1.2.aa' }),
    entry({ trigger_id: '1.3.bb' })])[0], 'single-use');
  assert.equal(reuseReport([])[0], 'single-use');
});

test('a marker in the channel means the flow finished', () => {
  assert.equal(landed('REQ-4127', [{ text: 'opened REQ-4127 for review' }])[0], 'landed');
});

test('an absent marker is the only evidence there is', () => {
  const [verdict, detail] = landed('REQ-4127', [{ text: 'something else' }]);
  assert.equal(verdict, 'missing');
  assert.match(detail, /produced nothing/);
});

test('no marker is not reported as a missing record', () => {
  assert.equal(landed('', [{ text: 'anything' }])[0], 'unmarked');
});
''',
"faq": [
 ("Is this the same three seconds as the acknowledgement deadline?",
  "It is the same number and a different deadline, and the fixes point in opposite directions. The ack deadline is about returning a 2xx, and the standard repair is to acknowledge immediately and do the work in the background. The trigger deadline cannot be satisfied that way, because opening the view is the work: pushed into a background queue it is guaranteed to expire. Ack fast and open fast, in that order, both in the first few lines."),
 ("Why does it expire in under a second when the documentation says three?",
  "Because the clock starts when the user clicks, not when your process wakes up. The payload crosses the internet, waits in whatever sits in front of your handler, and may start a cold container on the way. All of that is spent before your first line runs, and reports of expiry inside a few hundred milliseconds of handler time are common. Treat three seconds as a ceiling you never actually get."),
 ("How do I open a modal that needs data I have to fetch first?",
  "Open it empty. Call views.open immediately with a small view that says Loading, keep the view.id it returns, fetch the data, then replace the content with views.update. views.update takes a view_id rather than a trigger and has no deadline, so all the slow work lives safely behind it."),
 ("I get exchanged_trigger_id on the second modal in a flow. Why?",
  "Because a trigger opens exactly one view. Pushing a second view needs the trigger_id from the payload you are handling right now, not the one that opened the first view. This is also why view_submission payloads carry their own trigger_id: it exists so you can open something new after a submit, and reaching past it for the original value is the most common way this fails."),
 ("Can a read-only script detect this by asking Slack?",
  "No, and it is worth being clear about that. Slack exposes no trigger state, so there is nothing to query. What a read can do is show the consequence: read the channel your modal-driven flow writes into and look for the records that were supposed to appear. A flow that started and left nothing behind is the failure with a cost attached to it."),
],
"related": [
 ("/slack/three-second-timeout/", "the other three second deadline, and the opposite repair"),
 ("/slack/invalid-blocks/", "when the view opens in time and Slack rejects the payload"),
 ("/slack/http-200-ok-false/", "why the refusal came back looking like a success"),
],
"citations": [CITE_VIEWS_OPEN, CITE_VIEWS_PUSH, CITE_INTERACTIVITY, CITE_MODALS],
})

GUIDES.append({
"slug": "incomplete-external-upload",
"title": "Half finished uploads leave a file id that names nothing",
"description": "getUploadURLExternal hands back a file id before any bytes exist. Reconcile your upload ledger against files.info to find the sequences that stopped halfway.",
"h1": "Half finished uploads leave a file id that names nothing",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack files.completeUploadExternal failed",
             "slack getUploadURLExternal file_not_found",
             "slack filesUploadV2 file missing",
             "slack upload succeeded file never appeared",
             "slack orphaned file id upload"],
"deps": "Python 3.9+ with requests, or Node.js 18+; a bot token with files:read, plus a JSON ledger of the file ids your uploader recorded",
"lead": "The report generator says it uploaded the PDF. The log line is there, no exception was raised, and the message announcing it went out on time. The message links to a file that does not exist.</p><p>Uploading to Slack is three network operations and only the first and last are Slack API calls. The middle one goes to a URL Slack handed you, so it is invisible to every Slack-shaped piece of monitoring you have. A break anywhere along the way leaves a <code>file_id</code> that was issued before any bytes existed and never became anything, and the SDK helper that wraps the sequence reports the whole thing as one failure with no indication of which third of it broke.",
"short_answer": """<p>The modern upload is: <code>files.getUploadURLExternal</code> returns an <code>upload_url</code> and a <code>file_id</code>; you send the bytes to that URL; <code>files.completeUploadExternal</code> registers the file and shares it. <strong>The <code>file_id</code> exists from the first call, before a single byte has been transferred.</strong> That is what makes the failure so quiet: you have an id, you write it down, you put it in a message, and nothing about it says whether it ever became a file.</p>
<p>Break the sequence at step two and the id names nothing. Break it at step three and the bytes are in Slack's storage attached to a file that was never registered. Either way <code>files.info</code> on your recorded id comes back <code>{"ok": false, "error": "file_not_found"}</code> &mdash; and that answer, against an id your own logs say you own, is the proof.</p>
<p>The most common cause is a scope. <code>files:write</code> is needed for the completion call and not for the byte transfer, so an app missing it gets all the way through the expensive part and fails at the end. The SDK reports it as an upload error, which sends people to look at the file, the size, the mime type: everything except the grant.</p>
<p>Fix the retry direction too. A sequence that failed at step three should repeat step three. Restarting from step one instead mints a second <code>file_id</code>, uploads the bytes again, and leaves the first orphan exactly where it was.</p>""",
"problem": """<p>The thing that makes this expensive is that the sequence is not atomic and nothing in it says so. Three operations, two systems, no transaction, and an id issued at the start that looks equally valid whether the story finished or not. Every other resource in the Slack API is either there or not there. This one has a middle state that your code holds a handle to.</p>
<p>The middle operation is invisible in an unusual way. It does not go to <code>slack.com/api</code>, it is not a Web API method, and it does not answer with <code>ok</code>. If your instrumentation wraps the Slack client, it does not see this call at all: no metric, no trace span, no retry policy, no timeout you set on purpose. A proxy that rewrites large request bodies, a network that drops the connection halfway through fifty megabytes, a hop that truncates the stream &mdash; all of that happens outside everything you have instrumented, and the next thing your code does is confidently call step three.</p>
<p>Then there is the length. <code>files.getUploadURLExternal</code> takes a <code>length</code>, and the value you declare has to be the number of bytes that actually arrive. Compute it from a string length rather than the encoded byte count, or from the file size before compression, and you have declared one thing and sent another. The failure surfaces later and elsewhere.</p>
<p>The scope trap is the one that catches whole teams at once. <code>files:write</code> is required for the completion step. An app installed with <code>files:read</code> alone will happily mint upload URLs and transfer bytes, and then die on the last call. Everything before the failure worked, which is exactly why nobody looks at the token: the natural reading of a failure at the end of an upload is that something is wrong with the file.</p>
<p>And the SDK helpers hide the seam. <code>filesUploadV2</code> and <code>files_upload_v2</code> exist because hand-rolling three steps is worse, but they turn three failure modes into one exception, and there have been versions that dropped a per-call token override between steps and produced <code>not_authed</code> in the middle of a sequence whose first call had authenticated perfectly.</p>""",
"why": """<p><strong>An id issued before the resource exists is the whole problem, so the audit is keyed on the id.</strong> Your ledger holds ids your uploader was given. <code>files.info</code> says whether each one became a file. That one join separates a real upload from a receipt for an upload that never happened, and nothing else in the API will tell you.</p>
<p><strong>file_not_found on your own id is not ambiguous, and that is rare here.</strong> Most Slack errors could mean several things. This one, against an id your logs say you were handed, means the sequence did not finish. It is one of the few places in this section where a single error string is conclusive.</p>
<p><strong>Which step broke decides which step to repeat, and getting it backwards doubles the mess.</strong> A failure at completion should be retried at completion, using the id you already have. Restarting from the beginning mints a new id, sends the bytes again, and leaves the first orphan behind. A retry policy that always starts over converts one stalled upload into a growing pile.</p>
<p><strong>The scope has to be checked before the sequence, not after it fails.</strong> <code>files:write</code> is a precondition of a step that runs last. Checking it up front costs one header read; discovering it at the end costs the bytes, the time, and a half-created file.</p>
<p><strong>Zero bytes is a distinct verdict from no file.</strong> A file registered with a size of zero means the completion call succeeded and the transfer did not, which is the opposite diagnosis from an id that names nothing, and it points at the middle operation nobody is watching.</p>
<p><strong>The reverse direction finds what a ledger cannot.</strong> Listing the files this bot owns turns up ids your records have never heard of &mdash; uploads from a code path that does not write to the ledger at all. A one-directional audit will always report those as clean.</p>""",
"steps": [
 {"h": "Check files:write before you look at a single file",
  "body": """<p><code>precondition</code> reads the <code>X-OAuth-Scopes</code> header and reports <code>no-files-write</code> first, because that scope is a requirement of the last step in the sequence. An app without it can mint URLs and transfer bytes all day and will fail every completion, after the expensive part is done.</p>"""},
 {"h": "Say how far each recorded upload got",
  "body": """<p><code>step_reached</code> reads one ledger row and returns <code>nothing</code>, <code>url-minted</code>, <code>bytes-sent</code> or <code>completed</code>. This is your side of the story, and it is worth stating before Slack's side, because the two disagreeing is the finding.</p>"""},
 {"h": "Ask files.info about every id you recorded",
  "body": """<p><code>reconcile</code> takes your step and Slack's answer and returns <code>never-registered</code>, <code>empty-file</code>, <code>registered-unshared</code>, <code>deleted</code>, <code>unseeable</code> or <code>complete</code>. <code>file_not_found</code> against an id from your own logs is the conclusive one: the sequence stopped before the file was created.</p>"""},
 {"h": "Read zero bytes as a different failure from no file",
  "body": """<p><code>empty-file</code> means completion succeeded and the transfer did not. That is the middle operation failing, the one that never goes through your Slack client and is therefore not in your traces. It is also where a wrong <code>length</code> shows up, which is what <code>length_fault</code> is for.</p>"""},
 {"h": "Take the retry the finding implies, not the one the wrapper implies",
  "body": """<p><code>retry_plan</code> names the single step to repeat. A completion that failed wants completion retried with the id you already hold. Starting the sequence over mints a second id, sends the bytes again, and leaves the first orphan untouched, which is how a stalled upload becomes a pile of them.</p>"""},
 {"h": "Look in the other direction as well",
  "body": """<p><code>files.list</code> filtered to the bot's own user id returns what Slack thinks this app owns. Ids in that list which are absent from your ledger came from a code path that does not record anything, and no amount of auditing your records will ever surface them.</p>"""},
],
"verify": """<p>Run it against the ids your uploader wrote down. The finding is a specific id, a specific step, and one line saying which step to repeat.</p>
<pre><code class="language-bash">python3 slack_upload_gaps.py --ledger uploads.json
# identity   U024BE7LH in Acme
# scopes     files:read,chat:write,channels:history
# scope      no-files-write the completion step needs files:write. Without it the
#                           sequence always fails after the bytes are already up
# ledger     146 recorded upload(s)
# gap        never-registered F07ABCD1234  step reached: bytes-sent
#                           the bytes went up and files.completeUploadExternal was
#                           never answered, so the id names nothing
#   retry: repeat the completion for F07ABCD1234; do not mint a second upload URL
# gap        empty-file     F07ABCD5678  registered with 0 bytes; completion
#                           succeeded and the transfer did not
# gap        length         F07ABCD9999  declared 41821 bytes and sent 41 bytes;
#                           a character count was used where a byte count belongs
# inverse    17 file(s) owned by this bot are absent from your ledger
# verdict    31 of 146 recorded upload(s) never became a file
#   repair: grant files:write before the first call, so the sequence cannot fail
#           at the one step that needs it
#   repair: record the file_id at step one and the outcome at step three, and
#           retry the step that failed rather than the whole sequence</code></pre>""",
"code_intro": "Five pure functions and two reads. <code>step_reached</code> states your side, <code>reconcile</code> states Slack's, and the interesting rows are where they disagree. <code>length_fault</code> catches the declared byte count that was really a character count, which is the quiet way the middle operation goes wrong. <code>precondition</code> checks the scope that a step at the end of the sequence needs at the beginning. <code>retry_plan</code> exists because getting the retry direction wrong is what turns one stalled upload into a hundred.",
"py_file": "slack_upload_gaps.py",
"py": '''"""Find the uploads that stopped between the three calls that make one.

Read only. This never mints an upload URL, never sends bytes anywhere, and
never completes an upload: those are writes. It reads the ids your uploader
already recorded and asks files.info whether each one ever became a file.

The modern upload is three network operations and only the first and last are
Slack API calls. The file_id is handed out by the first one, before any bytes
exist, so an id on its own proves nothing at all.
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_upload_gaps")

API = "https://slack.com/api/"


def precondition(scopes):
    """Can this app finish an upload, and can this script audit one? Pure.

    files:write is a requirement of the last of the three steps, which is why
    it is checked first here. An app without it mints URLs and sends bytes
    perfectly well and then fails at the end, once the expensive part is done.
    """
    if scopes is None:
        return ("scopes-unread", "the granted scopes were not read, so the one "
                                 "precondition that matters is unverified")
    held = {str(s).strip() for s in scopes}
    if "files:write" not in held:
        return ("no-files-write", "the completion step needs files:write. Without it "
                                  "the sequence always fails after the bytes are "
                                  "already up, which is the state that leaves orphans")
    if "files:read" not in held:
        return ("no-files-read", "files:write is granted so uploads can complete, but "
                                 "this audit needs files:read to ask about any of them")
    return ("ready", "files:write and files:read are both granted")


def step_reached(record):
    """How far did your own uploader get with this file? Pure.

    This is your side of the story and it is stated before Slack's, because the
    two disagreeing is the entire finding.
    """
    row = record or {}
    if row.get("completed_at") or row.get("completed") is True:
        return ("completed", "your record says the completion call was answered")
    if row.get("bytes_sent") or row.get("uploaded_at"):
        return ("bytes-sent", "the bytes went up and the completion call is not "
                              "recorded as having been answered")
    if row.get("file_id") or row.get("upload_url"):
        return ("url-minted", "an upload URL and a file id were issued and nothing "
                              "after that is recorded")
    return ("nothing", "the row records no file id at all, so there is nothing to ask "
                       "Slack about")


def length_fault(declared, actual):
    """Did you send the number of bytes you said you would? Pure.

    The declared length is the one number in the sequence that has to agree
    with a fact about the file, and the usual mistake is a character count
    where a byte count belongs, which only diverges once the text is not
    plain ASCII.
    """
    try:
        want = int(declared)
        got = int(actual)
    except (TypeError, ValueError):
        return ("unknown", "the row does not carry both a declared length and a sent "
                           "byte count")
    if want <= 0:
        return ("zero", "a declared length of %d. The call takes the byte count of the "
                        "file, and zero is never right" % want)
    if got == want:
        return ("match", "%d byte(s) declared and sent" % want)
    if got < want:
        return ("short", "declared %d byte(s) and sent %d. A truncated transfer, or a "
                         "length taken before compression" % (want, got))
    return ("over", "declared %d byte(s) and sent %d. A character count was very "
                    "likely used where a byte count belongs" % (want, got))


def reconcile(step, info):
    """What does Slack say about the id your ledger recorded? Pure.

    file_not_found against an id your own logs say you were handed is the
    conclusive answer in this note: the sequence stopped before the file was
    ever created. Most Slack errors are ambiguous. This one is not.
    """
    body = info or {}
    if body.get("ok") is False:
        error = str(body.get("error") or "")
        if error == "file_not_found":
            return ("never-registered", "Slack has no file under this id. It was "
                                        "issued by the first call before any bytes "
                                        "existed, and nothing ever completed it")
        if error == "not_visible":
            return ("unseeable", "the file exists and this token cannot see it, which "
                                 "is a membership question rather than a broken "
                                 "sequence")
        if error == "file_deleted":
            return ("deleted", "the file was created and later deleted, so the "
                               "sequence did finish")
        return ("unreadable", "files.info answered %s, which decides nothing either "
                              "way" % (error or "with no error string"))
    row = body.get("file") if isinstance(body.get("file"), dict) else body
    if not row:
        return ("unreadable", "no file object came back")
    try:
        size = int(row.get("size") or 0)
    except (TypeError, ValueError):
        size = 0
    if size <= 0:
        return ("empty-file", "registered with %d byte(s). The completion call "
                              "succeeded and the transfer did not, which is the "
                              "middle operation failing" % size)
    shares = row.get("shares") or {}
    targets = (list(row.get("channels") or []) + list(row.get("groups") or [])
               + list(row.get("ims") or []) + list(shares.get("public") or [])
               + list(shares.get("private") or []))
    if not targets:
        return ("registered-unshared", "the file exists with %d byte(s) and is shared "
                                       "nowhere. The sequence finished; the channel "
                                       "argument is a separate question" % size)
    if step == "completed":
        return ("complete", "%d byte(s), shared in %d place(s)" % (size, len(targets)))
    return ("complete-unrecorded", "the file exists and your ledger stopped at %s, so "
                                   "your records are behind Slack rather than ahead of "
                                   "it" % step)


def retry_plan(step, verdict):
    """Which single step should be repeated? Pure. Printed, never run.

    Getting this backwards is what turns one stalled upload into a pile of
    them: restarting from the first call mints a second id, sends the bytes a
    second time, and leaves the first orphan exactly where it was.
    """
    if verdict == "never-registered" and step in ("bytes-sent", "completed"):
        return ("repeat the completion for this file id and nothing else. The bytes "
                "are already up; minting a second upload URL would create a second "
                "orphan beside this one")
    if verdict == "never-registered":
        return ("start this upload again and discard the recorded id. Nothing was "
                "ever transferred under it")
    if verdict == "empty-file":
        return ("start this upload again. The upload URL is single use and spent, and "
                "the step that failed was the byte transfer")
    if verdict == "registered-unshared":
        return ("nothing in the sequence needs repeating. Share the file that exists "
                "rather than uploading it again")
    if verdict in ("unseeable", "deleted"):
        return "nothing to repeat; the sequence finished"
    if verdict == "complete-unrecorded":
        return ("nothing to repeat. Record the outcome so the next audit does not "
                "raise this file again")
    return "nothing to repeat"


def load_ledger(path):
    raw = json.loads(open(path, encoding="utf-8").read())
    if isinstance(raw, dict):
        raw = raw.get("uploads") or raw.get("files") or []
    return [r for r in raw or [] if isinstance(r, dict)]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ledger", required=True,
                    help="a JSON file of upload records, each with file_id and "
                         "whatever of upload_url, bytes_sent and completed_at you keep")
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN",
                    help="environment variable holding the bot token")
    ap.add_argument("--inverse", action="store_true",
                    help="also list files this bot owns that your ledger has never "
                         "heard of")
    ap.add_argument("--count", type=int, default=100,
                    help="files to read in the inverse pass")
    args = ap.parse_args()

    token = os.environ.get(args.token_env)
    if not token:
        log.error("set %s to a bot token holding files:read", args.token_env)
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + token})
    r = s.get(API + "auth.test", timeout=30)
    who = r.json()
    if who.get("ok") is not True:
        log.error("auth.test  unavailable    %s", who.get("error"))
        return 2
    header = r.headers.get("X-OAuth-Scopes")
    scopes = [p.strip() for p in header.split(",") if p.strip()] if header else None
    log.info("identity   %s in %s", who.get("user_id"), who.get("team"))
    log.info("scopes     %s", ",".join(scopes) if scopes else "not reported")

    sverdict, sdetail = precondition(scopes)
    (log.info if sverdict == "ready" else log.warning)("scope      %-16s %s",
                                                       sverdict, sdetail)

    ledger = load_ledger(args.ledger)
    log.info("ledger     %d recorded upload(s)", len(ledger))

    broken = 0
    seen = set()
    for row in ledger:
        step, _ = step_reached(row)
        file_id = str(row.get("file_id") or "")
        if not file_id:
            log.warning("gap        no-file-id       a row with no id; step reached: %s",
                        step)
            broken += 1
            continue
        seen.add(file_id)
        lverdict, ldetail = length_fault(row.get("length"), row.get("bytes_sent"))
        if lverdict in ("short", "over", "zero"):
            log.warning("gap        length           %s  %s", file_id, ldetail)
        body = s.get(API + "files.info", timeout=30,
                     params={"file": file_id}).json()
        verdict, detail = reconcile(step, body)
        if verdict in ("complete", "complete-unrecorded", "deleted"):
            continue
        broken += 1
        log.warning("gap        %-16s %s  step reached: %s", verdict, file_id, step)
        log.warning("                            %s", detail)
        log.warning("  retry: %s", retry_plan(step, verdict))

    if args.inverse:
        body = s.get(API + "files.list", timeout=30,
                     params={"user": who.get("user_id") or "",
                             "count": str(args.count),
                             "types": "all"}).json()
        if body.get("ok") is True:
            owned = {str(f.get("id") or "") for f in body.get("files") or []} - {""}
            unknown = owned - seen
            if unknown:
                log.warning("inverse    %d file(s) owned by this bot are absent from "
                            "your ledger", len(unknown))
                log.warning("                            %s",
                            ", ".join(sorted(unknown)[:8]))
        else:
            log.warning("files.list unavailable      %s", body.get("error"))

    if broken or sverdict not in ("ready", "no-files-read"):
        log.warning("verdict    %d of %d recorded upload(s) never became a file",
                    broken, len(ledger))
        log.warning("  repair: grant files:write before the first call, so the "
                    "sequence cannot fail at the one step that needs it")
        log.warning("  repair: record the file_id at step one and the outcome at step "
                    "three, and retry the step that failed rather than the whole "
                    "sequence")
        log.warning("  repair: pass the channel as an id in channel_id on the "
                    "completion call; a channel name is rejected there")
        return 1
    log.info("verdict    clean          every recorded upload became a real file")
    return 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-upload-gaps.mjs",
"js": '''/**
 * Find the uploads that stopped between the three calls that make one.
 *
 * Read only. This never mints an upload URL, never sends bytes anywhere, and
 * never completes an upload: those are writes. It reads the ids your uploader
 * already recorded and asks files.info whether each one became a file.
 *
 * The modern upload is three network operations and only the first and last
 * are Slack API calls. The file_id comes from the first one, before any bytes
 * exist, so an id on its own proves nothing at all.
 */

import { readFile } from 'node:fs/promises';

const API = 'https://slack.com/api/';

/** Can this app finish an upload, and can this script audit one? Pure. */
export function precondition(scopes) {
  if (scopes === null || scopes === undefined) {
    return ['scopes-unread', 'the granted scopes were not read, so the one '
      + 'precondition that matters is unverified'];
  }
  const held = new Set(scopes.map((s) => String(s).trim()));
  if (!held.has('files:write')) {
    return ['no-files-write', 'the completion step needs files:write. Without it the '
      + 'sequence always fails after the bytes are already up, which is the state that '
      + 'leaves orphans'];
  }
  if (!held.has('files:read')) {
    return ['no-files-read', 'files:write is granted so uploads can complete, but this '
      + 'audit needs files:read to ask about any of them'];
  }
  return ['ready', 'files:write and files:read are both granted'];
}

/** How far did your own uploader get with this file? Pure. */
export function stepReached(record) {
  const row = record ?? {};
  if (row.completed_at || row.completed === true) {
    return ['completed', 'your record says the completion call was answered'];
  }
  if (row.bytes_sent || row.uploaded_at) {
    return ['bytes-sent', 'the bytes went up and the completion call is not recorded '
      + 'as having been answered'];
  }
  if (row.file_id || row.upload_url) {
    return ['url-minted', 'an upload URL and a file id were issued and nothing after '
      + 'that is recorded'];
  }
  return ['nothing', 'the row records no file id at all, so there is nothing to ask '
    + 'Slack about'];
}

/** Did you send the number of bytes you said you would? Pure. */
export function lengthFault(declared, actual) {
  const want = Number(declared);
  const got = Number(actual);
  if (declared === null || declared === undefined || actual === null
      || actual === undefined || !Number.isFinite(want) || !Number.isFinite(got)) {
    return ['unknown', 'the row does not carry both a declared length and a sent byte '
      + 'count'];
  }
  if (want <= 0) {
    return ['zero', `a declared length of ${want}. The call takes the byte count of `
      + 'the file, and zero is never right'];
  }
  if (got === want) return ['match', `${want} byte(s) declared and sent`];
  if (got < want) {
    return ['short', `declared ${want} byte(s) and sent ${got}. A truncated transfer, `
      + 'or a length taken before compression'];
  }
  return ['over', `declared ${want} byte(s) and sent ${got}. A character count was `
    + 'very likely used where a byte count belongs'];
}

/** What does Slack say about the id your ledger recorded? Pure. */
export function reconcile(step, info) {
  const body = info ?? {};
  if (body.ok === false) {
    const error = String(body.error ?? '');
    if (error === 'file_not_found') {
      return ['never-registered', 'Slack has no file under this id. It was issued by '
        + 'the first call before any bytes existed, and nothing ever completed it'];
    }
    if (error === 'not_visible') {
      return ['unseeable', 'the file exists and this token cannot see it, which is a '
        + 'membership question rather than a broken sequence'];
    }
    if (error === 'file_deleted') {
      return ['deleted', 'the file was created and later deleted, so the sequence did '
        + 'finish'];
    }
    return ['unreadable', `files.info answered ${error || 'with no error string'}, `
      + 'which decides nothing either way'];
  }
  const row = (body.file && typeof body.file === 'object') ? body.file : body;
  if (!row || !Object.keys(row).length) {
    return ['unreadable', 'no file object came back'];
  }
  const size = Number(row.size ?? 0) || 0;
  if (size <= 0) {
    return ['empty-file', `registered with ${size} byte(s). The completion call `
      + 'succeeded and the transfer did not, which is the middle operation failing'];
  }
  const shares = row.shares ?? {};
  const targets = [...(row.channels ?? []), ...(row.groups ?? []), ...(row.ims ?? []),
    ...Object.keys(shares.public ?? {}), ...Object.keys(shares.private ?? {})];
  if (!targets.length) {
    return ['registered-unshared', `the file exists with ${size} byte(s) and is shared `
      + 'nowhere. The sequence finished; the channel argument is a separate question'];
  }
  if (step === 'completed') {
    return ['complete', `${size} byte(s), shared in ${targets.length} place(s)`];
  }
  return ['complete-unrecorded', `the file exists and your ledger stopped at ${step}, `
    + 'so your records are behind Slack rather than ahead of it'];
}

/** Which single step should be repeated? Pure. Printed, never run. */
export function retryPlan(step, verdict) {
  if (verdict === 'never-registered' && ['bytes-sent', 'completed'].includes(step)) {
    return 'repeat the completion for this file id and nothing else. The bytes are '
      + 'already up; minting a second upload URL would create a second orphan beside '
      + 'this one';
  }
  if (verdict === 'never-registered') {
    return 'start this upload again and discard the recorded id. Nothing was ever '
      + 'transferred under it';
  }
  if (verdict === 'empty-file') {
    return 'start this upload again. The upload URL is single use and spent, and the '
      + 'step that failed was the byte transfer';
  }
  if (verdict === 'registered-unshared') {
    return 'nothing in the sequence needs repeating. Share the file that exists rather '
      + 'than uploading it again';
  }
  if (['unseeable', 'deleted'].includes(verdict)) {
    return 'nothing to repeat; the sequence finished';
  }
  if (verdict === 'complete-unrecorded') {
    return 'nothing to repeat. Record the outcome so the next audit does not raise '
      + 'this file again';
  }
  return 'nothing to repeat';
}

function arg(args, name, fallback = null) {
  const i = args.indexOf(name);
  return i === -1 ? fallback : args[i + 1];
}

async function main() {
  const args = process.argv.slice(2);
  const ledgerFile = arg(args, '--ledger', '');
  if (!ledgerFile) {
    console.error('pass --ledger FILE with the file ids your uploader recorded');
    process.exitCode = 2;
    return;
  }
  const tokenEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
  const token = process.env[tokenEnv];
  if (!token) {
    console.error(`set ${tokenEnv} to a bot token holding files:read`);
    process.exitCode = 2;
    return;
  }
  const headers = { Authorization: `Bearer ${token}` };
  const read = async (method, params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return fetch(`${API}${method}${qs ? `?${qs}` : ''}`, { headers });
  };

  const r = await read('auth.test');
  const who = await r.json();
  if (who.ok !== true) {
    console.error(`auth.test  unavailable    ${who.error}`);
    process.exitCode = 2;
    return;
  }
  const header = r.headers.get('x-oauth-scopes');
  const scopes = header ? header.split(',').map((p) => p.trim()).filter(Boolean) : null;
  console.log(`identity   ${who.user_id} in ${who.team}`);
  console.log(`scopes     ${scopes ? scopes.join(',') : 'not reported'}`);

  const [sv, sd] = precondition(scopes);
  const scopeLine = `scope      ${sv.padEnd(16)} ${sd}`;
  if (sv === 'ready') console.log(scopeLine); else console.warn(scopeLine);

  let ledger = JSON.parse(await readFile(ledgerFile, 'utf8'));
  if (!Array.isArray(ledger)) ledger = ledger.uploads ?? ledger.files ?? [];
  ledger = ledger.filter((row) => row && typeof row === 'object');
  console.log(`ledger     ${ledger.length} recorded upload(s)`);

  let broken = 0;
  const seen = new Set();
  for (const row of ledger) {
    const [step] = stepReached(row);
    const fileId = String(row.file_id ?? '');
    if (!fileId) {
      console.warn(`gap        no-file-id       a row with no id; step reached: ${step}`);
      broken += 1;
      continue;
    }
    seen.add(fileId);
    const [lv, ld] = lengthFault(row.length, row.bytes_sent);
    if (['short', 'over', 'zero'].includes(lv)) {
      console.warn(`gap        length           ${fileId}  ${ld}`);
    }
    // eslint-disable-next-line no-await-in-loop
    const body = await (await read('files.info', { file: fileId })).json();
    const [verdict, detail] = reconcile(step, body);
    if (['complete', 'complete-unrecorded', 'deleted'].includes(verdict)) continue;
    broken += 1;
    console.warn(`gap        ${verdict.padEnd(16)} ${fileId}  step reached: ${step}`);
    console.warn(`                            ${detail}`);
    console.warn(`  retry: ${retryPlan(step, verdict)}`);
  }

  if (args.includes('--inverse')) {
    const body = await (await read('files.list', {
      user: who.user_id ?? '', count: String(arg(args, '--count', '100')), types: 'all',
    })).json();
    if (body.ok === true) {
      const owned = new Set((body.files ?? []).map((f) => String(f.id ?? ''))
        .filter(Boolean));
      const unknown = [...owned].filter((id) => !seen.has(id));
      if (unknown.length) {
        console.warn(`inverse    ${unknown.length} file(s) owned by this bot are `
          + 'absent from your ledger');
        console.warn(`                            ${unknown.sort().slice(0, 8).join(', ')}`);
      }
    } else {
      console.warn(`files.list unavailable      ${body.error}`);
    }
  }

  if (broken || (sv !== 'ready' && sv !== 'no-files-read')) {
    console.warn(`verdict    ${broken} of ${ledger.length} recorded upload(s) never `
      + 'became a file');
    console.warn('  repair: grant files:write before the first call, so the sequence '
      + 'cannot fail at the one step that needs it');
    console.warn('  repair: record the file_id at step one and the outcome at step '
      + 'three, and retry the step that failed rather than the whole sequence');
    console.warn('  repair: pass the channel as an id in channel_id on the completion '
      + 'call; a channel name is rejected there');
    process.exitCode = 1;
  } else {
    console.log('verdict    clean          every recorded upload became a real file');
  }
}

// Only run when invoked directly, so importing this module in the tests does
// not execute main() and fail the file on a missing ledger.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The assertions that matter are the ones that stop a retry going the wrong way. <code>retry_plan</code> has to say <em>repeat the completion</em> when the bytes are already up and <em>start again</em> when they are not, because those two look identical from inside an SDK wrapper and one of them doubles the orphans. <code>reconcile</code> has to keep <code>never-registered</code> and <code>empty-file</code> apart, since the first means nothing was created and the second means the middle operation failed. And <code>precondition</code> has to name <code>files:write</code> before <code>files:read</code>, because one of them breaks uploads and the other only breaks this script.",
"test_py_file": "test_slack_upload_gaps.py",
"test_py": '''from slack_upload_gaps import (length_fault, precondition, reconcile, retry_plan,
                               step_reached)


def ok_file(**kw):
    row = {"id": "F07ABCD1234", "size": 41821, "channels": ["C024BE91L"],
           "shares": {}}
    row.update(kw)
    return {"ok": True, "file": row}


def test_files_write_is_the_precondition_that_is_reported_first():
    verdict, detail = precondition(["files:read", "chat:write"])
    assert verdict == "no-files-write"
    assert "after the bytes are already up" in detail


def test_a_missing_read_scope_only_breaks_the_audit():
    verdict, detail = precondition(["files:write"])
    assert verdict == "no-files-read"
    assert "this audit" in detail


def test_both_scopes_present_is_ready():
    assert precondition(["files:write", "files:read"])[0] == "ready"


def test_unread_scopes_are_not_reported_as_granted():
    assert precondition(None)[0] == "scopes-unread"


def test_each_recorded_stage_is_named():
    assert step_reached({"completed_at": "2026-08-20"})[0] == "completed"
    assert step_reached({"file_id": "F1", "bytes_sent": 12})[0] == "bytes-sent"
    assert step_reached({"file_id": "F1"})[0] == "url-minted"
    assert step_reached({})[0] == "nothing"


def test_a_row_with_only_an_upload_url_got_no_further_than_step_one():
    verdict, detail = step_reached({"upload_url": "https://files.slack.com/upload/v1/x"})
    assert verdict == "url-minted"
    assert "nothing after that is recorded" in detail


def test_matching_byte_counts_are_a_match():
    assert length_fault(41821, 41821)[0] == "match"


def test_sending_fewer_bytes_than_declared_is_short():
    verdict, detail = length_fault(41821, 41)
    assert verdict == "short"
    assert "truncated" in detail


def test_sending_more_than_declared_names_the_character_count_mistake():
    verdict, detail = length_fault(41, 41821)
    assert verdict == "over"
    assert "character count" in detail


def test_a_declared_length_of_zero_is_never_right():
    assert length_fault(0, 0)[0] == "zero"


def test_a_row_without_both_numbers_is_unknown_rather_than_a_match():
    assert length_fault(None, 100)[0] == "unknown"
    assert length_fault(100, None)[0] == "unknown"


def test_file_not_found_on_your_own_id_is_the_conclusive_answer():
    verdict, detail = reconcile("bytes-sent",
                                {"ok": False, "error": "file_not_found"})
    assert verdict == "never-registered"
    assert "before any bytes existed" in detail


def test_a_zero_byte_file_is_the_middle_operation_failing():
    verdict, detail = reconcile("completed", ok_file(size=0))
    assert verdict == "empty-file"
    assert "middle operation" in detail


def test_never_registered_and_empty_file_are_never_collapsed():
    assert reconcile("bytes-sent", {"ok": False, "error": "file_not_found"})[0] \\
        != reconcile("completed", ok_file(size=0))[0]


def test_a_file_shared_nowhere_is_reported_as_a_separate_question():
    verdict, detail = reconcile("completed", ok_file(channels=[]))
    assert verdict == "registered-unshared"
    assert "separate question" in detail


def test_a_finished_upload_is_complete():
    assert reconcile("completed", ok_file())[0] == "complete"


def test_a_file_slack_has_and_your_ledger_stopped_short_of_is_its_own_verdict():
    verdict, detail = reconcile("bytes-sent", ok_file())
    assert verdict == "complete-unrecorded"
    assert "behind Slack" in detail


def test_not_visible_is_a_membership_answer_not_a_broken_sequence():
    verdict, detail = reconcile("completed", {"ok": False, "error": "not_visible"})
    assert verdict == "unseeable"
    assert "membership question" in detail


def test_a_deleted_file_did_finish_the_sequence():
    assert reconcile("completed", {"ok": False, "error": "file_deleted"})[0] == "deleted"


def test_an_unrecognised_error_decides_nothing():
    assert reconcile("completed", {"ok": False, "error": "ratelimited"})[0] == "unreadable"


def test_bytes_already_up_means_repeat_the_completion_only():
    plan = retry_plan("bytes-sent", "never-registered")
    assert "repeat the completion" in plan
    assert "second orphan" in plan


def test_nothing_transferred_means_start_again():
    plan = retry_plan("url-minted", "never-registered")
    assert "start this upload again" in plan
    assert "discard the recorded id" in plan


def test_the_two_retry_directions_are_never_the_same_line():
    assert retry_plan("bytes-sent", "never-registered") \\
        != retry_plan("url-minted", "never-registered")


def test_an_empty_file_is_restarted_because_the_url_is_spent():
    assert "single use and spent" in retry_plan("completed", "empty-file")


def test_an_unshared_file_is_not_uploaded_again():
    assert "rather than uploading it again" in retry_plan("completed",
                                                          "registered-unshared")
''',
"test_js_file": "slack-upload-gaps.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  lengthFault, precondition, reconcile, retryPlan, stepReached,
} from './slack-upload-gaps.mjs';

const okFile = (over = {}) => ({
  ok: true,
  file: {
    id: 'F07ABCD1234', size: 41821, channels: ['C024BE91L'], shares: {}, ...over,
  },
});

test('files:write is the precondition that is reported first', () => {
  const [verdict, detail] = precondition(['files:read', 'chat:write']);
  assert.equal(verdict, 'no-files-write');
  assert.match(detail, /after the bytes are already up/);
});

test('a missing read scope only breaks the audit', () => {
  const [verdict, detail] = precondition(['files:write']);
  assert.equal(verdict, 'no-files-read');
  assert.match(detail, /this audit/);
});

test('both scopes present is ready', () => {
  assert.equal(precondition(['files:write', 'files:read'])[0], 'ready');
});

test('unread scopes are not reported as granted', () => {
  assert.equal(precondition(null)[0], 'scopes-unread');
});

test('each recorded stage is named', () => {
  assert.equal(stepReached({ completed_at: '2026-08-20' })[0], 'completed');
  assert.equal(stepReached({ file_id: 'F1', bytes_sent: 12 })[0], 'bytes-sent');
  assert.equal(stepReached({ file_id: 'F1' })[0], 'url-minted');
  assert.equal(stepReached({})[0], 'nothing');
});

test('a row with only an upload url got no further than step one', () => {
  const [verdict, detail] = stepReached(
    { upload_url: 'https://files.slack.com/upload/v1/x' });
  assert.equal(verdict, 'url-minted');
  assert.match(detail, /nothing after that is recorded/);
});

test('matching byte counts are a match', () => {
  assert.equal(lengthFault(41821, 41821)[0], 'match');
});

test('sending fewer bytes than declared is short', () => {
  const [verdict, detail] = lengthFault(41821, 41);
  assert.equal(verdict, 'short');
  assert.match(detail, /truncated/);
});

test('sending more than declared names the character count mistake', () => {
  const [verdict, detail] = lengthFault(41, 41821);
  assert.equal(verdict, 'over');
  assert.match(detail, /character count/);
});

test('a declared length of zero is never right', () => {
  assert.equal(lengthFault(0, 0)[0], 'zero');
});

test('a row without both numbers is unknown rather than a match', () => {
  assert.equal(lengthFault(null, 100)[0], 'unknown');
  assert.equal(lengthFault(100, undefined)[0], 'unknown');
});

test('file_not_found on your own id is the conclusive answer', () => {
  const [verdict, detail] = reconcile('bytes-sent',
    { ok: false, error: 'file_not_found' });
  assert.equal(verdict, 'never-registered');
  assert.match(detail, /before any bytes existed/);
});

test('a zero byte file is the middle operation failing', () => {
  const [verdict, detail] = reconcile('completed', okFile({ size: 0 }));
  assert.equal(verdict, 'empty-file');
  assert.match(detail, /middle operation/);
});

test('never-registered and empty-file are never collapsed', () => {
  assert.notEqual(reconcile('bytes-sent', { ok: false, error: 'file_not_found' })[0],
    reconcile('completed', okFile({ size: 0 }))[0]);
});

test('a file shared nowhere is reported as a separate question', () => {
  const [verdict, detail] = reconcile('completed', okFile({ channels: [] }));
  assert.equal(verdict, 'registered-unshared');
  assert.match(detail, /separate question/);
});

test('a finished upload is complete', () => {
  assert.equal(reconcile('completed', okFile())[0], 'complete');
});

test('a file Slack has and your ledger stopped short of is its own verdict', () => {
  const [verdict, detail] = reconcile('bytes-sent', okFile());
  assert.equal(verdict, 'complete-unrecorded');
  assert.match(detail, /behind Slack/);
});

test('not_visible is a membership answer not a broken sequence', () => {
  const [verdict, detail] = reconcile('completed', { ok: false, error: 'not_visible' });
  assert.equal(verdict, 'unseeable');
  assert.match(detail, /membership question/);
});

test('a deleted file did finish the sequence', () => {
  assert.equal(reconcile('completed', { ok: false, error: 'file_deleted' })[0],
    'deleted');
});

test('an unrecognised error decides nothing', () => {
  assert.equal(reconcile('completed', { ok: false, error: 'ratelimited' })[0],
    'unreadable');
});

test('bytes already up means repeat the completion only', () => {
  const plan = retryPlan('bytes-sent', 'never-registered');
  assert.match(plan, /repeat the completion/);
  assert.match(plan, /second orphan/);
});

test('nothing transferred means start again', () => {
  const plan = retryPlan('url-minted', 'never-registered');
  assert.match(plan, /start this upload again/);
  assert.match(plan, /discard the recorded id/);
});

test('the two retry directions are never the same line', () => {
  assert.notEqual(retryPlan('bytes-sent', 'never-registered'),
    retryPlan('url-minted', 'never-registered'));
});

test('an empty file is restarted because the url is spent', () => {
  assert.match(retryPlan('completed', 'empty-file'), /single use and spent/);
});

test('an unshared file is not uploaded again', () => {
  assert.match(retryPlan('completed', 'registered-unshared'),
    /rather than uploading it again/);
});
''',
"faq": [
 ("The upload raised no exception. How can the file not exist?",
  "Because the id you were given came from the first call, and the first call only reserves a slot. It hands back an upload URL and a file id before any bytes have moved. If the transfer or the completion fails, the id you already wrote down stays exactly as valid-looking as it was. files.info on that id is the only thing that distinguishes a real file from a receipt for one that never happened."),
 ("Why does the failure so often turn out to be a scope?",
  "Because files:write is needed by the last step and by nothing before it. An app without it mints the URL fine, transfers the bytes fine, and fails at completion after all the work is done. The SDK reports that as an upload error, which naturally sends people to look at the file rather than at the token. Checking the scope up front costs one header read."),
 ("Should I retry the whole upload when it fails?",
  "Only if it failed before the bytes went up. If the transfer succeeded and completion did not, retry completion with the id you already hold. Starting over mints a second id and sends the bytes again, leaving the first orphan in place, which is how a single stalled upload turns into a steadily growing pile of them."),
 ("The file exists but nobody can find it. Is that this problem?",
  "No, that one is about sharing rather than about the sequence. If files.info returns a real file with real bytes, all three steps finished and what is missing is a channel to share it into. This script reports that case and hands it on, because the fix is a different argument on a call that already worked rather than a broken sequence."),
 ("Can I detect this without keeping a ledger of file ids?",
  "Only partly. Without recorded ids there is nothing to ask files.info about, so the forward audit is unavailable. Listing the files this bot owns still shows what Slack has, which is worth running on its own, but it cannot show you the uploads that produced no file at all. Those exist only as ids in your logs, which is the argument for recording them."),
],
"related": [
 ("/slack/files-upload-retired/", "why the upload became three calls in the first place"),
 ("/slack/public-file-links-exposed/", "the other way a file ends up somewhere you did not intend"),
 ("/slack/missing-scope-on-read/", "reading what the token was actually granted"),
],
"citations": [CITE_GET_UPLOAD_URL, CITE_COMPLETE_UPLOAD, CITE_FILES_INFO, CITE_FILES_LIST],
})
