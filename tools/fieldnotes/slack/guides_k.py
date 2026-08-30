#!/usr/bin/env python3
"""/slack/ field notes, batch K - the writing.

Four notes about quantity rather than permission. One is a bot that is allowed
in every channel it is in, several thousand of them, where nothing has failed
and the inventory has quietly become unreadable. Two are about the two
arguments that drive a paginated read and that fail in opposite directions: the
page size, which is a constant in your code and is either rejected outright or
silently made smaller, and the cursor, which is a short-lived token bound to
the query that produced it and which a resumable job persists as if it were an
offset. And one is a ceiling that belongs to the whole workspace rather than to
your app, where the sender that exhausted it is frequently somebody else's
integration.

Read only throughout. Counting how much a workspace sends is the one question
here it would be tempting to answer by sending, and none of these do: every
number below is read out of history, out of a membership list, or out of a
checkpoint file the application already wrote.
"""

CITE_PAGINATION = ("Pagination in the Web API - Slack Docs",
                   "https://docs.slack.dev/apis/web-api/pagination")
CITE_RATE_LIMITS = ("Rate limits - Slack Docs",
                    "https://docs.slack.dev/apis/web-api/rate-limits")
CITE_CONV_LIST = ("conversations.list method reference - Slack Docs",
                  "https://docs.slack.dev/reference/methods/conversations.list")
CITE_CONV_HISTORY = ("conversations.history method reference - Slack Docs",
                     "https://docs.slack.dev/reference/methods/conversations.history")
CITE_CONV_MEMBERS = ("conversations.members method reference - Slack Docs",
                     "https://docs.slack.dev/reference/methods/conversations.members")
CITE_USERS_LIST = ("users.list method reference - Slack Docs",
                   "https://docs.slack.dev/reference/methods/users.list")
CITE_USERS_CONVERSATIONS = ("users.conversations method reference - Slack Docs",
                            "https://docs.slack.dev/reference/methods/users.conversations")
CITE_POSTMESSAGE = ("chat.postMessage method reference - Slack Docs",
                    "https://docs.slack.dev/reference/methods/chat.postMessage")
CITE_EVENTS = ("Events API - Slack Docs", "https://docs.slack.dev/apis/events-api/")
CITE_AUTH_TEST = ("auth.test method reference - Slack Docs",
                  "https://docs.slack.dev/reference/methods/auth.test")
CITE_RETRIEVING = ("Retrieving messages - Slack Docs",
                   "https://docs.slack.dev/messaging/retrieving-messages")

GUIDES = []

GUIDES.append({
"slug": "bot-in-too-many-channels",
"title": "The bot joined 4,000 channels and the nightly sweep dies",
"description": "Nothing failed: the bot is a member everywhere it was invited. Count the footprint, price one inventory against Tier 2, and cut the event volume.",
"h1": "The bot joined 4,000 channels and the nightly sweep dies",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack bot too many channels", "users.conversations slow",
             "slack bot channel count", "slack tier 2 rate limit sweep",
             "slack message.channels event volume"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The job that enumerates the bot's channels used to take four seconds. It now takes eleven minutes, and last Tuesday it stopped taking any time at all because it died on <code>ratelimited</code> before it finished. Nothing in the code changed. Nothing is misconfigured. The bot is a member of every channel it is a member of, legitimately, because an onboarding automation has been inviting it to every new channel for two years.</p><p>This is the note in the section where nothing has gone wrong and something has to change anyway.",
"short_answer": """<p><code>users.conversations</code> and <code>conversations.list</code> are cursor-paginated with a maximum <code>limit</code> of 1000 and both sit on <strong>Tier 2</strong>, which is roughly twenty requests a minute. Four thousand memberships is four pages, and four pages is nothing. Four pages taken once per incoming message, or once per queue item, is a request rate that exhausts a Tier 2 bucket inside a minute and stays exhausted.</p>
<p>So the number to compute is not the membership count on its own. It is <em>pages multiplied by how often you take the inventory</em>, held against the tier's budget of 1200 requests an hour. The script below counts the footprint with one timed sweep, gets the workspace denominator from a bounded <code>conversations.list</code>, and prints that arithmetic. Then it does the second half, which people forget: membership is also the multiplier on event delivery, because <code>message.channels</code> pays out once for every message in every channel the app is in.</p>""",
"problem": """<p>Nobody decides to put a bot in four thousand channels. It accumulates. Somebody writes a workflow that invites the standard set of apps to each new project channel, which is a thoroughly good idea at forty channels. Two years later the workspace has four thousand channels, the app is in most of them, and every piece of code that says "list the channels I am in" has quietly become a multi-page paginated walk on a Tier 2 method.</p>
<p>The failure mode is not a permission error, which is what makes it hard to file. The sweep works. It works slower each month. Then one day it works slower than the interval it runs on, two runs overlap, they share the same per-method bucket, and both of them start seeing <code>ratelimited</code>. The stack trace names a rate limit, so the ticket says "rate limiting", and the repair everybody reaches for is backoff, which makes the job take longer and fixes nothing, because the job is not being throttled by bad luck. It is asking for more than the tier allows, every run, by design.</p>
<p>Underneath that is a second cost that no sweep will show you. An app in four thousand channels subscribed to <code>message.channels</code> receives an event for every message posted in any of them. Slack expects an acknowledgement within three seconds, and an app that is spending its time acknowledging traffic from channels it will never act on has a much smaller margin than its author believes. The membership count is the multiplier on both problems at once, which is why the honest finding is the count and its consequences rather than an error string.</p>""",
"why": """<p><strong>Membership is not a failure, so no error handler will ever mention it.</strong> Every one of those channels returned <code>ok: true</code> when the bot was invited. There is no error to catch and no flag to check. The only way this becomes visible is if something asserts a number, which means somebody has to decide what number is too many before it is.</p>
<p><strong>The tier, not the count, is the constraint.</strong> Tier 2 is about twenty requests a minute per method per workspace per app. One inventory of four thousand channels is four requests. That is affordable once an hour and ruinous once a minute, and the difference between those two is a scheduling decision buried somewhere in the application, not a property of Slack.</p>
<p><strong>The maximum page size is 1000, and it is a ceiling rather than a promise.</strong> Asking for more is rejected outright, so there is no way to make the sweep cheaper by asking for a bigger page. The only lever is asking less often.</p>
<p><strong>Membership multiplies event delivery, and that budget is measured in seconds.</strong> A subscription to <code>message.channels</code> scales with the footprint. A subscription to <code>app_mention</code> scales with how often somebody wants something. Narrowing the subscription is usually a much larger win than optimising the sweep, and it is the one repair that shrinks with usage rather than growing with it.</p>
<p><strong>A read-only audit that gets throttled has already answered the question.</strong> If a script whose entire job is to count things cannot count them without hitting the tier, then the application, which does this plus its actual work, is over the line too. That is worth recording as a finding rather than as an inconvenience the script retries around.</p>""",
"steps": [
 {"h": "Time the sweep rather than estimating it",
  "body": """<p>The script starts a clock, follows every cursor on <code>users.conversations</code> at <code>limit=1000</code>, and reports pages and wall time. An estimate derived from the count would be tidier and would miss the thing you want to know, which is whether this workspace's sweep is already slow enough to overlap the interval it runs on.</p>"""},
 {"h": "Get a denominator before you judge the numerator",
  "body": """<p>Two thousand channels means one thing in a workspace of two thousand one hundred and something else in a workspace of forty thousand. A bounded <code>conversations.list</code> gives the total, and the share is what tells you whether the bot was invited selectively or by a rule.</p>"""},
 {"h": "Price one inventory against Tier 2, then against how often you take it",
  "body": """<p>Pages times runs per hour, against a budget of twenty a minute. This is the arithmetic that turns "the bot is in a lot of channels" into "this job asks for 1,440 requests an hour out of 1,200", which is a sentence somebody can act on this afternoon.</p>"""},
 {"h": "Sort the event subscriptions into the ones that scale with membership",
  "body": """<p><code>message.channels</code>, <code>message.groups</code>, <code>member_joined_channel</code> and <code>reaction_added</code> all pay out per channel. <code>app_mention</code> and <code>message.im</code> pay out per request from a human. The script labels each subscription you name and says which side of that line it is on.</p>"""},
 {"h": "Cache the inventory instead of retaking it",
  "body": """<p>The printed repair is a TTL and an event-driven refresh: keep the channel list, refresh it from <code>channel_created</code>, <code>channel_deleted</code> and <code>member_joined_channel</code> rather than by re-enumerating. A cache with a one-hour TTL turns 2,400 requests an hour into four.</p>"""},
 {"h": "Stop the automation that is still adding to the count",
  "body": """<p>Every repair above is undone by the workflow that invites the bot to each new channel. The script prints the footprint growth as a share of the workspace precisely so that the conversation includes the thing generating it, rather than only the job that suffers from it.</p>"""},
],
"verify": """<p>Re-run after the cache is in place with the real run frequency. The footprint will not have moved, and the request arithmetic should be the part that changed.</p>
<pre><code class="language-bash">python3 slack_channel_footprint.py --runs-per-hour 1
# identity   U0APPBOT11 in acme
# footprint  broad          3,914 of 4,102 channel(s), 95.4% of the workspace
# sweep      4 page(s) in 1.9s, no cursor left unfollowed
# cost       affordable     4 request(s)/hour against a Tier 2 budget of 1200
# events     membership     message.channels scales with the footprint
# events     demand         app_mention scales with how often somebody asks</code></pre>""",
"code_intro": "Three pure functions and two paginated GETs. <code>sweep_cost</code> is the whole note in nine lines: pages, multiplied by how often you take the inventory, against the tier's hourly budget. <code>footprint_verdict</code> holds the count against the workspace so the number has a denominator. <code>event_load</code> is the half that has nothing to do with the Web API at all, sorting the subscriptions that scale with membership away from the ones that scale with demand.",
"py_file": "slack_channel_footprint.py",
"py": '''"""Measure the bot's channel footprint and price the sweep that reads it.

Read only. One paginated users.conversations counts the memberships and times
itself, one bounded conversations.list supplies the workspace denominator.
Nothing joins, leaves or invites: this reports how large the footprint is, what
one inventory costs against the method's tier, and which event subscriptions
grow with membership rather than with demand.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_channel_footprint")

API = "https://slack.com/api/"

# users.conversations and conversations.list are cursor paginated with a
# maximum limit of 1000, and both sit on Tier 2: roughly 20 requests a minute
# per method, per workspace, per app. Those two numbers are the entire
# arithmetic of this script.
PAGE_MAX = 1000
TIER2_PER_MINUTE = 20

# Which subscriptions pay out once per channel the app belongs to, and which
# pay out once per person who wanted something. The first group is what turns a
# large footprint into an event volume problem; the second is what a narrowed
# app should be left holding.
EVENT_SCALING = {
    "message.channels": ("membership",
                         "one delivery per message in every public channel the app is in"),
    "message.groups": ("membership", "the same, for private channels"),
    "message.mpim": ("membership", "the same, for group DMs"),
    "member_joined_channel": ("membership",
                              "one delivery per join across the whole footprint"),
    "member_left_channel": ("membership", "one delivery per leave, likewise"),
    "reaction_added": ("membership",
                       "one delivery per reaction across the whole footprint"),
    "channel_created": ("workspace",
                        "one per new channel, whether or not the app is in it"),
    "channel_deleted": ("workspace", "one per deletion, likewise"),
    "app_mention": ("demand", "one delivery when somebody asks for the app by name"),
    "message.im": ("demand", "one delivery per direct message to the app"),
    "app_home_opened": ("demand", "one delivery when somebody opens the app"),
}


def sweep_cost(count, runs_per_hour=1, page_size=PAGE_MAX,
               per_minute=TIER2_PER_MINUTE):
    """Price one inventory, and then the habit of taking it. Pure.

    The membership count on its own is not a finding. Four pages is nothing
    once an hour and is over the tier once a minute, so the number that
    matters is pages multiplied by frequency, held against the budget.
    """
    size = max(int(page_size or 0), 1)
    n = max(int(count or 0), 0)
    pages = max(1, (n + size - 1) // size)
    budget = max(int(per_minute or 0), 1) * 60
    per_hour = pages * max(int(runs_per_hour or 0), 0)
    share = round(per_hour * 100.0 / budget, 1)
    if per_hour > budget:
        verdict = "over-budget"
    elif share >= 50.0:
        verdict = "tight"
    else:
        verdict = "affordable"
    return {"pages": pages, "requests_per_hour": per_hour,
            "budget_per_hour": budget, "share_percent": share,
            "verdict": verdict}


def footprint_verdict(member_of, workspace_total=None, budget=200):
    """Hold the membership count against the size of the workspace. Pure.

    Returns (verdict, detail). A count without a denominator is a number
    somebody will argue with; a share is a number somebody will act on.
    """
    if member_of is None or int(member_of) < 0:
        return ("unmeasured",
                "the sweep did not complete, so there is no footprint to judge. "
                "That failure is itself worth reading: a read-only count that "
                "cannot finish describes an application that asks for more.")

    n = int(member_of)
    if not workspace_total:
        share_text = "no workspace total available"
        share = None
    else:
        share = round(n * 100.0 / int(workspace_total), 1)
        share_text = "%s%% of the %d channel(s) this token can enumerate" % (
            share, int(workspace_total))

    if share is not None and share >= 90.0:
        return ("near-total",
                "%d channel(s), %s. A footprint that tracks the workspace is a "
                "rule inviting the app rather than people choosing it." % (n, share_text))
    if n > int(budget):
        return ("broad",
                "%d channel(s), over the budget of %d, %s. Every paginated read "
                "of this list is multi-page and every membership scaled "
                "subscription is multiplied by it." % (n, int(budget), share_text))
    return ("narrow", "%d channel(s), %s" % (n, share_text))


def event_load(member_of, subscriptions):
    """Sort subscriptions by what their delivery volume is a function of. Pure.

    Membership scaled events are the ones a large footprint multiplies. Demand
    scaled events are the ones that stay the same size when the app is invited
    to another thousand channels, which is why narrowing to them is the repair
    that does not need revisiting.
    """
    n = max(int(member_of or 0), 0)
    order = {"membership": 0, "workspace": 1, "demand": 2, "unknown": 3}
    out = []
    for name in subscriptions or []:
        key = str(name or "").strip()
        if not key:
            continue
        scaling, detail = EVENT_SCALING.get(
            key, ("unknown", "not a subscription this script knows how to place"))
        if scaling == "membership":
            detail = "%s, so %d channel(s) of it" % (detail, n)
        out.append((key, scaling, detail))
    out.sort(key=lambda row: (order.get(row[1], 3), row[0]))
    return out


def paged_count(session, method, params, key, max_pages):
    """Count everything the method returns, following every cursor. GET only.

    Returns (count, pages, seconds, note). The sweep times itself rather than
    estimating from the count, because whether this workspace's inventory
    already takes longer than the interval it runs on is the finding.
    """
    total, pages, cursor, note = 0, 0, "", ""
    started = time.monotonic()
    while pages < max_pages:
        page = dict(params, limit=str(PAGE_MAX))
        if cursor:
            page["cursor"] = cursor
        r = session.get(API + method, params=page, timeout=30)
        body = r.json()
        pages += 1
        if body.get("ok") is not True:
            err = body.get("error")
            note = "stopped on %s after %d page(s)" % (err, pages)
            if err == "ratelimited":
                note += ("; Retry-After was %s, and a read-only count that gets "
                         "throttled has already proved the point"
                         % r.headers.get("Retry-After", "absent"))
            return (-1, pages, time.monotonic() - started, note)
        total += len(body.get(key) or [])
        cursor = (body.get("response_metadata") or {}).get("next_cursor") or ""
        if not cursor:
            return (total, pages, time.monotonic() - started,
                    "no cursor left unfollowed")
    return (total, pages, time.monotonic() - started,
            "stopped at the %d page cap, so the real count is higher" % max_pages)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN",
                    help="environment variable holding the bot token")
    ap.add_argument("--user", default="",
                    help="bot user ID; auth.test supplies it when omitted")
    ap.add_argument("--budget", type=int, default=200,
                    help="channel count above which the footprint is called broad")
    ap.add_argument("--runs-per-hour", type=int, default=1,
                    help="how often the application takes this inventory")
    ap.add_argument("--subscription", action="append", default=[],
                    help="an event your app subscribes to; repeatable")
    ap.add_argument("--max-pages", type=int, default=40,
                    help="cap on both sweeps, so an audit cannot become the problem")
    args = ap.parse_args()

    token = os.environ.get(args.token_env)
    if not token:
        log.error("set %s (channels:read, groups:read and users:read are enough)",
                  args.token_env)
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + token})

    who = s.get(API + "auth.test", timeout=30).json()
    if who.get("ok") is not True:
        log.error("auth.test answered 200 with ok: false, error=%s", who.get("error"))
        return 2
    user = args.user or who.get("user_id") or ""
    log.info("identity   %s in %s", user, who.get("team"))

    mine, pages, seconds, note = paged_count(
        s, "users.conversations",
        {"user": user, "types": "public_channel,private_channel"},
        "channels", args.max_pages)
    total, _, _, _ = paged_count(
        s, "conversations.list",
        {"types": "public_channel,private_channel", "exclude_archived": "true"},
        "channels", args.max_pages)

    verdict, detail = footprint_verdict(None if mine < 0 else mine, total, args.budget)
    log.info("sweep      %d page(s) in %.1fs, %s", pages, seconds, note)
    (log.info if verdict == "narrow" else log.warning)(
        "footprint  %-14s %s", verdict, detail)

    cost = sweep_cost(max(mine, 0), args.runs_per_hour)
    (log.info if cost["verdict"] == "affordable" else log.warning)(
        "cost       %-14s %d request(s)/hour against a Tier 2 budget of %d (%.1f%%)",
        cost["verdict"], cost["requests_per_hour"], cost["budget_per_hour"],
        cost["share_percent"])

    for name, scaling, why in event_load(max(mine, 0), args.subscription):
        (log.warning if scaling == "membership" else log.info)(
            "events     %-14s %s: %s", scaling, name, why)

    if verdict in ("broad", "near-total") or cost["verdict"] != "affordable":
        log.warning("  repair: cache the channel inventory with a TTL and refresh "
                    "it from channel_created, channel_deleted and "
                    "member_joined_channel rather than re-enumerating per run")
        log.warning("  repair: narrow membership scaled subscriptions to "
                    "app_mention and message.im, so event volume tracks demand "
                    "instead of the footprint")
        log.warning("  repair: stop the automation that invites this app to every "
                    "new channel; every other repair is undone by it")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-channel-footprint.mjs",
"js": '''/**
 * Measure the bot's channel footprint and price the sweep that reads it.
 *
 * Read only. One paginated users.conversations counts the memberships and
 * times itself, one bounded conversations.list supplies the workspace
 * denominator. Nothing joins, leaves or invites: this reports how large the
 * footprint is, what one inventory costs against the method's tier, and which
 * event subscriptions grow with membership rather than with demand.
 */

const API = 'https://slack.com/api/';

// Cursor paginated with a maximum limit of 1000, and Tier 2: roughly 20
// requests a minute per method, per workspace, per app.
const PAGE_MAX = 1000;
const TIER2_PER_MINUTE = 20;

// Which subscriptions pay out once per channel the app belongs to, and which
// pay out once per person who wanted something.
const EVENT_SCALING = new Map([
  ['message.channels', ['membership',
    'one delivery per message in every public channel the app is in']],
  ['message.groups', ['membership', 'the same, for private channels']],
  ['message.mpim', ['membership', 'the same, for group DMs']],
  ['member_joined_channel', ['membership',
    'one delivery per join across the whole footprint']],
  ['member_left_channel', ['membership', 'one delivery per leave, likewise']],
  ['reaction_added', ['membership',
    'one delivery per reaction across the whole footprint']],
  ['channel_created', ['workspace',
    'one per new channel, whether or not the app is in it']],
  ['channel_deleted', ['workspace', 'one per deletion, likewise']],
  ['app_mention', ['demand', 'one delivery when somebody asks for the app by name']],
  ['message.im', ['demand', 'one delivery per direct message to the app']],
  ['app_home_opened', ['demand', 'one delivery when somebody opens the app']],
]);

/**
 * Price one inventory, and then the habit of taking it. Pure.
 * Four pages is nothing once an hour and over the tier once a minute, so the
 * number that matters is pages multiplied by frequency.
 */
export function sweepCost(count, runsPerHour = 1, pageSize = PAGE_MAX,
  perMinute = TIER2_PER_MINUTE) {
  const size = Math.max(Number(pageSize) || 0, 1);
  const n = Math.max(Number(count) || 0, 0);
  const pages = Math.max(1, Math.ceil(n / size));
  const budget = Math.max(Number(perMinute) || 0, 1) * 60;
  const perHour = pages * Math.max(Number(runsPerHour) || 0, 0);
  const share = Math.round((perHour * 1000.0) / budget) / 10;
  let verdict = 'affordable';
  if (perHour > budget) verdict = 'over-budget';
  else if (share >= 50.0) verdict = 'tight';
  return {
    pages, requestsPerHour: perHour, budgetPerHour: budget,
    sharePercent: share, verdict,
  };
}

/**
 * Hold the membership count against the size of the workspace. Pure.
 * A count without a denominator is a number somebody will argue with.
 */
export function footprintVerdict(memberOf, workspaceTotal = null, budget = 200) {
  if (memberOf === null || memberOf === undefined || Number(memberOf) < 0) {
    return ['unmeasured',
      'the sweep did not complete, so there is no footprint to judge. That ' +
      'failure is itself worth reading: a read-only count that cannot finish ' +
      'describes an application that asks for more.'];
  }

  const n = Number(memberOf);
  let share = null;
  let shareText = 'no workspace total available';
  if (workspaceTotal) {
    share = Math.round((n * 1000.0) / Number(workspaceTotal)) / 10;
    shareText = `${share}% of the ${Number(workspaceTotal)} channel(s) this token can enumerate`;
  }

  if (share !== null && share >= 90.0) {
    return ['near-total',
      `${n} channel(s), ${shareText}. A footprint that tracks the workspace is ` +
      'a rule inviting the app rather than people choosing it.'];
  }
  if (n > Number(budget)) {
    return ['broad',
      `${n} channel(s), over the budget of ${Number(budget)}, ${shareText}. ` +
      'Every paginated read of this list is multi-page and every membership ' +
      'scaled subscription is multiplied by it.'];
  }
  return ['narrow', `${n} channel(s), ${shareText}`];
}

/**
 * Sort subscriptions by what their delivery volume is a function of. Pure.
 * Demand scaled events stay the same size when the app is invited to another
 * thousand channels, which is why narrowing to them is the durable repair.
 */
export function eventLoad(memberOf, subscriptions) {
  const n = Math.max(Number(memberOf) || 0, 0);
  const order = { membership: 0, workspace: 1, demand: 2, unknown: 3 };
  const out = [];
  for (const name of subscriptions ?? []) {
    const key = String(name ?? '').trim();
    if (!key) continue;
    const [scaling, base] = EVENT_SCALING.get(key)
      ?? ['unknown', 'not a subscription this script knows how to place'];
    const detail = scaling === 'membership'
      ? `${base}, so ${n} channel(s) of it` : base;
    out.push([key, scaling, detail]);
  }
  out.sort((a, b) => (order[a[1]] ?? 3) - (order[b[1]] ?? 3)
    || a[0].localeCompare(b[0]));
  return out;
}

async function pagedCount(token, method, params, key, maxPages) {
  let total = 0;
  let pages = 0;
  let cursor = '';
  const started = Date.now();
  while (pages < maxPages) {
    const page = new URLSearchParams({ ...params, limit: String(PAGE_MAX) });
    if (cursor) page.set('cursor', cursor);
    const res = await fetch(`${API}${method}?${page}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const body = await res.json();
    pages += 1;
    if (body.ok !== true) {
      let note = `stopped on ${body.error} after ${pages} page(s)`;
      if (body.error === 'ratelimited') {
        note += `; Retry-After was ${res.headers.get('retry-after') ?? 'absent'}, ` +
          'and a read-only count that gets throttled has already proved the point';
      }
      return [-1, pages, (Date.now() - started) / 1000, note];
    }
    total += (body.channels ?? []).length;
    cursor = body.response_metadata?.next_cursor ?? '';
    if (!cursor) {
      return [total, pages, (Date.now() - started) / 1000, 'no cursor left unfollowed'];
    }
  }
  return [total, pages, (Date.now() - started) / 1000,
    `stopped at the ${maxPages} page cap, so the real count is higher`];
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
  const tokenEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
  const token = process.env[tokenEnv];
  if (!token) {
    console.error(`set ${tokenEnv} (channels:read, groups:read and users:read are enough)`);
    process.exitCode = 2;
    return;
  }
  const budget = Number(arg(args, '--budget', 200));
  const runsPerHour = Number(arg(args, '--runs-per-hour', 1));
  const maxPages = Number(arg(args, '--max-pages', 40));

  const whoRes = await fetch(`${API}auth.test`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const who = await whoRes.json();
  if (who.ok !== true) {
    console.error(`auth.test answered 200 with ok: false, error=${who.error}`);
    process.exitCode = 2;
    return;
  }
  const user = arg(args, '--user', '') || who.user_id || '';
  console.log(`identity   ${user} in ${who.team}`);

  const [mine, pages, seconds, note] = await pagedCount(token, 'users.conversations',
    { user, types: 'public_channel,private_channel' }, 'channels', maxPages);
  const [total] = await pagedCount(token, 'conversations.list',
    { types: 'public_channel,private_channel', exclude_archived: 'true' },
    'channels', maxPages);

  const [verdict, detail] = footprintVerdict(mine < 0 ? null : mine, total, budget);
  console.log(`sweep      ${pages} page(s) in ${seconds.toFixed(1)}s, ${note}`);
  (verdict === 'narrow' ? console.log : console.warn)(
    `footprint  ${verdict.padEnd(14)} ${detail}`);

  const cost = sweepCost(Math.max(mine, 0), runsPerHour);
  (cost.verdict === 'affordable' ? console.log : console.warn)(
    `cost       ${cost.verdict.padEnd(14)} ${cost.requestsPerHour} request(s)/hour ` +
    `against a Tier 2 budget of ${cost.budgetPerHour} (${cost.sharePercent}%)`);

  for (const [name, scaling, why] of eventLoad(Math.max(mine, 0),
    argAll(args, '--subscription'))) {
    (scaling === 'membership' ? console.warn : console.log)(
      `events     ${scaling.padEnd(14)} ${name}: ${why}`);
  }

  if (verdict === 'broad' || verdict === 'near-total' || cost.verdict !== 'affordable') {
    console.warn('  repair: cache the channel inventory with a TTL and refresh it ' +
      'from channel_created, channel_deleted and member_joined_channel rather ' +
      'than re-enumerating per run');
    console.warn('  repair: narrow membership scaled subscriptions to app_mention ' +
      'and message.im, so event volume tracks demand instead of the footprint');
    console.warn('  repair: stop the automation that invites this app to every new ' +
      'channel; every other repair is undone by it');
    process.exitCode = 1;
  }
}

// Only run when invoked directly, so importing this module in the tests does
// not execute main() and fail the file on a missing token.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The tests pin the arithmetic rather than the wording, because the arithmetic is the argument. Four thousand memberships is four pages, four pages once an hour is affordable and four pages a hundred times an hour is over a Tier 2 budget, and the same footprint produces all three verdicts depending only on how often somebody takes the inventory. A sweep that did not finish is asserted to return <code>unmeasured</code> rather than a small number, which is the one place this script could lie confidently.",
"test_py_file": "test_slack_channel_footprint.py",
"test_py": '''from slack_channel_footprint import event_load, footprint_verdict, sweep_cost


def test_one_inventory_of_four_thousand_channels_is_four_pages():
    assert sweep_cost(4000)["pages"] == 4
    assert sweep_cost(1)["pages"] == 1
    assert sweep_cost(0)["pages"] == 1


def test_the_same_footprint_is_cheap_hourly_and_ruinous_per_minute():
    assert sweep_cost(4000, runs_per_hour=1)["verdict"] == "affordable"
    assert sweep_cost(4000, runs_per_hour=360)["verdict"] == "over-budget"


def test_the_tier_2_budget_is_twelve_hundred_an_hour():
    cost = sweep_cost(4000, runs_per_hour=1)
    assert cost["budget_per_hour"] == 1200
    assert cost["requests_per_hour"] == 4


def test_the_halfway_mark_is_reported_as_tight_rather_than_fine():
    cost = sweep_cost(4000, runs_per_hour=150)
    assert cost["requests_per_hour"] == 600
    assert cost["verdict"] == "tight"


def test_a_footprint_that_tracks_the_workspace_is_its_own_verdict():
    verdict, detail = footprint_verdict(3914, 4102)
    assert verdict == "near-total"
    assert "95.4%" in detail


def test_a_large_footprint_in_a_much_larger_workspace_is_merely_broad():
    verdict, detail = footprint_verdict(3914, 40000)
    assert verdict == "broad"
    assert "3914" in detail


def test_a_small_footprint_is_left_alone():
    assert footprint_verdict(12, 4102)[0] == "narrow"
    assert footprint_verdict(200, 4102)[0] == "narrow"
    assert footprint_verdict(201, 4102)[0] == "broad"


def test_a_sweep_that_did_not_finish_is_never_reported_as_a_count():
    verdict, detail = footprint_verdict(None, 4102)
    assert verdict == "unmeasured"
    assert "did not complete" in detail
    assert footprint_verdict(-1, 4102)[0] == "unmeasured"


def test_a_missing_denominator_is_said_out_loud():
    assert "no workspace total" in footprint_verdict(12, None)[1]


def test_membership_scaled_events_sort_first_and_carry_the_multiplier():
    rows = event_load(3914, ["app_mention", "message.channels", "channel_created"])
    assert [r[0] for r in rows] == ["message.channels", "channel_created", "app_mention"]
    assert rows[0][1] == "membership"
    assert "3914" in rows[0][2]


def test_demand_scaled_events_are_not_multiplied_by_the_footprint():
    rows = event_load(3914, ["app_mention"])
    assert rows[0][1] == "demand"
    assert "3914" not in rows[0][2]


def test_an_unrecognised_subscription_is_placed_last_and_not_guessed_at():
    rows = event_load(10, ["app_mention", "team_join_or_something"])
    assert rows[-1][1] == "unknown"
    assert event_load(10, ["", None]) == []
''',
"test_js_file": "slack-channel-footprint.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { eventLoad, footprintVerdict, sweepCost } from './slack-channel-footprint.mjs';

test('one inventory of four thousand channels is four pages', () => {
  assert.equal(sweepCost(4000).pages, 4);
  assert.equal(sweepCost(1).pages, 1);
  assert.equal(sweepCost(0).pages, 1);
});

test('the same footprint is cheap hourly and ruinous per minute', () => {
  assert.equal(sweepCost(4000, 1).verdict, 'affordable');
  assert.equal(sweepCost(4000, 360).verdict, 'over-budget');
});

test('the tier 2 budget is twelve hundred an hour', () => {
  const cost = sweepCost(4000, 1);
  assert.equal(cost.budgetPerHour, 1200);
  assert.equal(cost.requestsPerHour, 4);
});

test('the halfway mark is reported as tight rather than fine', () => {
  const cost = sweepCost(4000, 150);
  assert.equal(cost.requestsPerHour, 600);
  assert.equal(cost.verdict, 'tight');
});

test('a footprint that tracks the workspace is its own verdict', () => {
  const [verdict, detail] = footprintVerdict(3914, 4102);
  assert.equal(verdict, 'near-total');
  assert.match(detail, /95\\.4%/);
});

test('a large footprint in a much larger workspace is merely broad', () => {
  const [verdict, detail] = footprintVerdict(3914, 40000);
  assert.equal(verdict, 'broad');
  assert.match(detail, /3914/);
});

test('a small footprint is left alone', () => {
  assert.equal(footprintVerdict(12, 4102)[0], 'narrow');
  assert.equal(footprintVerdict(200, 4102)[0], 'narrow');
  assert.equal(footprintVerdict(201, 4102)[0], 'broad');
});

test('a sweep that did not finish is never reported as a count', () => {
  const [verdict, detail] = footprintVerdict(null, 4102);
  assert.equal(verdict, 'unmeasured');
  assert.match(detail, /did not complete/);
  assert.equal(footprintVerdict(-1, 4102)[0], 'unmeasured');
});

test('a missing denominator is said out loud', () => {
  assert.match(footprintVerdict(12, null)[1], /no workspace total/);
});

test('membership scaled events sort first and carry the multiplier', () => {
  const rows = eventLoad(3914, ['app_mention', 'message.channels', 'channel_created']);
  assert.deepEqual(rows.map((r) => r[0]),
    ['message.channels', 'channel_created', 'app_mention']);
  assert.equal(rows[0][1], 'membership');
  assert.match(rows[0][2], /3914/);
});

test('demand scaled events are not multiplied by the footprint', () => {
  const rows = eventLoad(3914, ['app_mention']);
  assert.equal(rows[0][1], 'demand');
  assert.doesNotMatch(rows[0][2], /3914/);
});

test('an unrecognised subscription is placed last and not guessed at', () => {
  const rows = eventLoad(10, ['app_mention', 'team_join_or_something']);
  assert.equal(rows[rows.length - 1][1], 'unknown');
  assert.deepEqual(eventLoad(10, ['', null]), []);
});
''',
"faq": [
 ("How many channels is too many for a bot?",
  "There is no number in the documentation, because the ceiling is not on membership. It is on what membership costs you: pages per inventory against a Tier 2 budget of about twenty requests a minute, and event deliveries per minute against a three second acknowledgement window. The script defaults to flagging above two hundred, which is a prompt to do the arithmetic rather than a limit Slack enforces."),
 ("Can I make the sweep cheaper by asking for a bigger page?",
  "No. The maximum limit on these methods is 1000 and asking for more is rejected outright with invalid_limit rather than clamped, so the page count is fixed by the membership count. The only lever left is frequency, which is why the repair is a cache with a TTL and an event-driven refresh rather than a tuning parameter."),
 ("The bot needs to be in all those channels. What then?",
  "Then keep the membership and change what it costs. Narrowing event subscriptions from message.channels to app_mention is the largest single win available, because it converts a bill that scales with the footprint into one that scales with how often somebody actually wants the app to do something. Membership stops being a multiplier the moment nothing subscribes per channel."),
 ("Why does the script count the workspace as well as the bot?",
  "Because the same count means different things in different workspaces. Three thousand channels out of four thousand is a rule inviting the app automatically, and the conversation is with whoever wrote that rule. Three thousand out of forty thousand is a large but deliberate footprint, and the conversation is about caching. One number cannot tell those apart."),
 ("The audit itself got rate limited. Is that a bug in the script?",
  "It is the finding. The script does the cheapest possible version of what your application does, once, with two paginated reads and a page cap so it cannot become the problem it is describing. If that gets throttled, the application, which does this plus its real work on a shared per-method bucket, is over the line by a wider margin than the audit is."),
],
"related": [
 ("/slack/pagination-not-followed/", "the sweep this note prices, done wrong"),
 ("/slack/bot-not-in-channel/", "the opposite problem, one channel at a time"),
 ("/slack/membership-lost-silently/", "when the footprint shrinks without telling you"),
],
"citations": [CITE_USERS_CONVERSATIONS, CITE_RATE_LIMITS, CITE_CONV_LIST, CITE_EVENTS],
})

GUIDES.append({
"slug": "invalid-limit",
"title": "invalid_limit: asking for more than a page can hold",
"description": "limit=5000 is rejected outright and limit=1000 is often quietly cut down. Audit the page size your code asks for against what each method returns.",
"h1": "invalid_limit: asking for more than a page can hold",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack invalid_limit", "slack conversations.list limit",
             "slack users.list limit 1000", "slack api page size",
             "slack limit parameter maximum"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Somebody read the pagination documentation, decided that following cursors was a lot of code for a workspace with three hundred channels, and wrote <code>limit=5000</code>. It is an entirely rational thing to try, and Slack answers it with <code>HTTP 200</code> carrying <code>ok: false</code> and <code>error: invalid_limit</code>.</p><p>The interesting version is the one that does not error. Ask for a thousand and you may get fifteen, with <code>ok: true</code>, no warning, and a cursor waiting that nobody reads.",
"short_answer": """<p><code>limit</code> is capped. Cursor-paginated Slack methods take at most 1000 items per page and reject anything larger outright, so <code>limit=5000</code> is a hard failure rather than a clamp. That much is easy to find, because it is an error.</p>
<p>The failure worth auditing is the other direction. Several methods return fewer items than you asked for while still answering <code>ok: true</code>: a non-Marketplace app gets fifteen messages from <code>conversations.history</code> however many it requested, and <code>users.list</code> is documented up to 1000 but is unreliable and slow near the top of that range on a large workspace. A page smaller than the one you asked for, with a non-empty cursor, is Slack telling you your constant is fiction. The script below sends each method's configured page size once, compares what came back against what was asked, and sorts the result into rejected, cut down, honoured, or genuinely the end of the data.</p>""",
"problem": """<p>The page size is a constant somewhere in the code, and it was chosen once. Usually it was chosen to avoid pagination: if the workspace has three hundred channels and the limit can be a thousand, then one call is the whole answer and the cursor loop never has to be written. That reasoning is correct on the day it is written and it decays in two different ways.</p>
<p>The loud decay is <code>invalid_limit</code>. Somebody raises the constant past 1000, either to cover a workspace that grew or because a different API they used last week allowed it, and every call to that method starts failing. The error arrives as <code>HTTP 200</code> with <code>ok: false</code> like everything else in Slack, so a client that checks status codes reports success and the application sees an empty list rather than an error. An empty channel list is much harder to attribute than a 400 would have been.</p>
<p>The quiet decay is worse. Slack does not always reject an over-large limit; sometimes it simply returns less. The most common case in 2026 is <code>conversations.history</code> for an app that is not on the Slack Marketplace, which returns a maximum of fifteen objects no matter what you ask for. Code that requested a thousand, received fifteen, and stops because it assumed a short page meant the end of the data has now silently truncated the history to fifteen messages with a perfectly healthy <code>ok: true</code>. The constant is not the problem there. The belief that the constant was honoured is.</p>""",
"why": """<p><strong>The ceiling is per method, and it is not documented in one place.</strong> Each method's reference page states its own maximum. There is no global constant to import and no header that reports it, so the only reliable way to know what a method will give you is to ask for a page and measure what arrives.</p>
<p><strong>Rejection and clamping are different bugs with different repairs.</strong> <code>invalid_limit</code> is loud, immediate and fixed by lowering a number. A clamp is silent, is not fixed by lowering the number, and is fixed by not assuming a short page is the last page. A detector that only looks for the error string finds the easy half.</p>
<p><strong>A short page with a cursor is the signature.</strong> Fewer items than requested plus a non-empty <code>next_cursor</code> means Slack decided your page size for you. Fewer items than requested with no cursor means the data ran out, which is fine. Those two look identical to code that only counts the array.</p>
<p><strong>Bigger pages are not faster past a point.</strong> Slack's own guidance recommends 200 for <code>users.list</code> on large workspaces, because a request for a thousand users spends longer being assembled and is more likely to time out than five requests for two hundred. The page size that avoids pagination is frequently the page size that makes the call fail.</p>
<p><strong>This is one call per method, deliberately.</strong> The audit does not walk the pages. Walking is a different question, answered by a different script, and a page size audit that paginates would be spending the tier budget of the method it is trying to describe.</p>""",
"steps": [
 {"h": "Write down the page size the application actually sends",
  "body": """<p>Not the one in the documentation and not the one in the constants file if they have drifted. The script takes it as an argument, per method if you need to, because the whole point is to compare a real request against a real response.</p>"""},
 {"h": "Check it offline against the documented ceiling first",
  "body": """<p><code>limit_verdict</code> needs no token. It knows each method's maximum and its recommended value, and it will tell you that 5000 is going to be rejected and that 1000 on <code>users.list</code> is legal and unwise before a single request is sent.</p>"""},
 {"h": "Send exactly one request per method",
  "body": """<p>One call, with your limit, no cursor. That is enough to learn everything: the error if there is one, the number of items, and whether a cursor came back. Anything more is spending the method's own rate budget to measure the method.</p>"""},
 {"h": "Compare what arrived against what was asked",
  "body": """<p>Four outcomes, and they are not variations on each other. <code>rejected</code> is an error string. <code>cut-down</code> is a smaller page with a cursor. <code>short-final</code> is a smaller page with no cursor, which is correct behaviour. <code>honoured</code> is the full page you asked for.</p>"""},
 {"h": "Treat a cut-down page as a pagination bug, not a limit bug",
  "body": """<p>Lowering the constant does not fix a clamp; it only makes the request honest. What fixes it is code that never infers "no more data" from "fewer items than I asked for", and reads the cursor instead. The script prints that repair separately, because it is a different line of code in a different function.</p>"""},
 {"h": "Set the recommended value and stop tuning it",
  "body": """<p>200 for <code>users.list</code>, 200 for the rest unless you have a measured reason. The printed repair names the value per method. A correct cursor loop over small pages beats a large page every time, and it stops being a thing anybody has to think about again.</p>"""},
],
"verify": """<p>Re-run with the repaired constants. Every method should come back <code>honoured</code> or <code>short-final</code>, and nothing should be reported as cut down.</p>
<pre><code class="language-bash">python3 slack_page_size_audit.py --limit 200
# conversations.list     configured  within-limits   200 is at the recommended page size
# conversations.list     response    honoured        asked 200, got 200, cursor set
# users.list             configured  within-limits   200 is at the recommended page size
# users.list             response    short-final     asked 200, got 141, no cursor: the data ran out
# conversations.history  response    cut-down        asked 200, got 15, cursor set
# 1 method(s) not answering at the size they were asked</code></pre>""",
"code_intro": "Three pure functions and one GET per method. <code>limit_verdict</code> is the offline half: a table of per-method ceilings and recommendations, no token required, which will tell you that a constant is doomed before you spend a request finding out. <code>page_verdict</code> is the live half, and it exists to keep four genuinely different outcomes apart. <code>repair_for</code> prints the value to set, per method, so the finding ends in a number rather than in advice.",
"py_file": "slack_page_size_audit.py",
"py": '''"""Compare the page size your code asks Slack for against what Slack returns.

Read only, and one GET per method: no cursor is ever followed, because
following cursors is a different question and would spend the rate budget of
the method being measured. Reports whether the configured limit is rejected,
quietly cut down, honoured, or simply larger than the data, and prints the
value to set instead.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_page_size_audit")

API = "https://slack.com/api/"

# Per method: the documented hard ceiling, the value worth sending, the key the
# items arrive under, and any extra parameters the call needs. The ceiling is
# what produces invalid_limit. The recommendation is what avoids the timeouts
# that a legal but very large page produces on a big workspace.
METHODS = {
    "conversations.list": {
        "ceiling": 1000, "recommended": 200, "items": "channels",
        "params": {"types": "public_channel,private_channel"}},
    "users.list": {
        "ceiling": 1000, "recommended": 200, "items": "members", "params": {},
        "note": "documented to 1000 and unreliable near it on a large workspace; "
                "Slack's own guidance is 200"},
    "users.conversations": {
        "ceiling": 1000, "recommended": 200, "items": "channels",
        "params": {"types": "public_channel,private_channel"}},
    "conversations.members": {
        "ceiling": 1000, "recommended": 200, "items": "members", "params": {},
        "needs_channel": True},
    "conversations.history": {
        "ceiling": 1000, "recommended": 200, "items": "messages", "params": {},
        "needs_channel": True,
        "note": "an app that is not on the Slack Marketplace is held to 15 objects "
                "per call whatever it asks for, which arrives as a cut down page "
                "rather than as an error"},
    "files.list": {
        "ceiling": 1000, "recommended": 200, "items": "files", "params": {}},
}


def limit_verdict(method, limit, table=None):
    """Judge a configured page size offline. Pure, and needs no token.

    Returns (verdict, detail). Knowing that 5000 will be refused before
    spending a request to find out is the cheapest finding in this script.
    """
    spec = (table or METHODS).get(str(method or ""))
    if spec is None:
        return ("unknown-method",
                "%s is not in this table, so nothing can be said about its page "
                "size ceiling. Its own reference page states it." % method)

    if limit is None or str(limit).strip() == "":
        return ("defaulted",
                "no limit is being sent, so Slack uses its default of 100 items. "
                "That is a legitimate choice and it is rarely a deliberate one.")

    try:
        n = int(limit)
    except (TypeError, ValueError):
        return ("not-a-number",
                "%r is not an integer. Whatever the client does with it, Slack "
                "will not read the number you meant." % limit)

    if n <= 0:
        return ("not-a-number",
                "a limit of %d is not a page size. Anything at or below zero is a "
                "bug upstream of this call." % n)
    if n > spec["ceiling"]:
        return ("over-ceiling",
                "%d is above the %d maximum for this method, so every call "
                "returns HTTP 200 with ok: false and error invalid_limit. Nothing "
                "downstream sees an exception; it sees an empty list."
                % (n, spec["ceiling"]))
    if n > spec["recommended"]:
        return ("over-recommended",
                "%d is legal, at or below the %d ceiling, and above the %d worth "
                "sending. %s" % (n, spec["ceiling"], spec["recommended"],
                                 spec.get("note", "Large pages take longer to "
                                          "assemble and time out sooner than the "
                                          "extra round trips they save.")))
    return ("within-limits", "%d is at or under the recommended page size of %d"
                             % (n, spec["recommended"]))


def page_verdict(asked, returned, cursor, error=None):
    """Classify one response against the request that produced it. Pure.

    Four outcomes that are not variations on each other: an error, a page Slack
    made smaller, a page the data made smaller, and the page you asked for.
    """
    err = str(error or "").strip()
    if err == "invalid_limit":
        return ("rejected",
                "invalid_limit: %s is above this method's ceiling and the call "
                "returns nothing at all. Lower the constant." % asked)
    if err:
        return ("unreadable",
                "the call answered ok: false with error %s, so the page size was "
                "never exercised. Fix that first." % err)

    got = int(returned or 0)
    want = int(asked or 0)
    has_cursor = bool(str(cursor or "").strip())

    if got >= want:
        return ("honoured",
                "asked %d, got %d, cursor %s" % (want, got,
                                                 "set" if has_cursor else "empty"))
    if has_cursor:
        return ("cut-down",
                "asked %d, got %d, and a cursor is waiting. Slack chose the page "
                "size, not your constant. Code that reads a short page as the end "
                "of the data is truncating here with ok: true." % (want, got))
    return ("short-final",
            "asked %d, got %d, no cursor: the data ran out. This is the method "
            "behaving correctly." % (want, got))


def repair_for(method, verdict, table=None):
    """The value to set, per method, so a finding ends in a number. Pure."""
    spec = (table or METHODS).get(str(method or ""))
    rec = spec["recommended"] if spec else 200
    if verdict in ("over-ceiling", "rejected"):
        return ("set limit=%d for %s; the ceiling is %d and asking past it "
                "returns nothing" % (rec, method, spec["ceiling"] if spec else 1000))
    if verdict == "over-recommended":
        return ("lower limit to %d for %s; the extra round trips cost less than "
                "the timeouts" % (rec, method))
    if verdict == "cut-down":
        return ("a smaller limit will not change this: the repair is in the "
                "pagination, which must follow response_metadata.next_cursor "
                "rather than stopping on a short page. Send limit=%d and loop"
                % rec)
    if verdict == "defaulted":
        return "send limit=%d explicitly for %s rather than inheriting 100" % (rec, method)
    return "nothing to change for %s" % method


def probe(session, method, spec, limit, channel):
    """One GET, with the configured limit and no cursor. Returns the body."""
    params = dict(spec["params"], limit=str(limit))
    if spec.get("needs_channel"):
        params["channel"] = channel
    return session.get(API + method, params=params, timeout=30).json()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN",
                    help="environment variable holding the bot token")
    ap.add_argument("--limit", default="1000",
                    help="the page size your application sends (default 1000)")
    ap.add_argument("--channel", default="",
                    help="a channel ID for the methods that need one")
    ap.add_argument("--offline", action="store_true",
                    help="check the configured limit against the table and stop")
    args = ap.parse_args()

    bad = 0
    for method, spec in METHODS.items():
        verdict, detail = limit_verdict(method, args.limit)
        line = "%-22s %-11s %-15s %s" % (method, "configured", verdict, detail)
        if verdict in ("within-limits",):
            log.info(line)
        else:
            log.warning(line)
            log.warning("  repair: %s", repair_for(method, verdict))
            bad += 1

    if args.offline:
        log.info("%d configured page size(s) worth changing", bad)
        return 1 if bad else 0

    token = os.environ.get(args.token_env)
    if not token:
        log.error("set %s, or pass --offline to check the constants only",
                  args.token_env)
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + token})

    live = 0
    for method, spec in METHODS.items():
        if spec.get("needs_channel") and not args.channel:
            log.info("%-22s %-11s %-15s pass --channel to exercise this one",
                     method, "response", "skipped")
            continue
        body = probe(s, method, spec, args.limit, args.channel)
        cursor = (body.get("response_metadata") or {}).get("next_cursor") or ""
        verdict, detail = page_verdict(
            args.limit, len(body.get(spec["items"]) or []), cursor,
            None if body.get("ok") is True else body.get("error"))
        line = "%-22s %-11s %-15s %s" % (method, "response", verdict, detail)
        if verdict in ("honoured", "short-final"):
            log.info(line)
            continue
        log.warning(line)
        log.warning("  repair: %s", repair_for(method, verdict))
        if spec.get("note"):
            log.warning("  context: %s", spec["note"])
        live += 1

    log.info("%d method(s) not answering at the size they were asked", live)
    return 1 if (live or bad) else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-page-size-audit.mjs",
"js": '''/**
 * Compare the page size your code asks Slack for against what Slack returns.
 *
 * Read only, and one GET per method: no cursor is ever followed, because
 * following cursors is a different question and would spend the rate budget of
 * the method being measured. Reports whether the configured limit is rejected,
 * quietly cut down, honoured, or simply larger than the data.
 */

const API = 'https://slack.com/api/';

// Per method: the documented hard ceiling, the value worth sending, the key the
// items arrive under, and any extra parameters the call needs.
const METHODS = new Map([
  ['conversations.list', {
    ceiling: 1000, recommended: 200, items: 'channels',
    params: { types: 'public_channel,private_channel' },
  }],
  ['users.list', {
    ceiling: 1000, recommended: 200, items: 'members', params: {},
    note: 'documented to 1000 and unreliable near it on a large workspace; ' +
      "Slack's own guidance is 200",
  }],
  ['users.conversations', {
    ceiling: 1000, recommended: 200, items: 'channels',
    params: { types: 'public_channel,private_channel' },
  }],
  ['conversations.members', {
    ceiling: 1000, recommended: 200, items: 'members', params: {},
    needsChannel: true,
  }],
  ['conversations.history', {
    ceiling: 1000, recommended: 200, items: 'messages', params: {},
    needsChannel: true,
    note: 'an app that is not on the Slack Marketplace is held to 15 objects per ' +
      'call whatever it asks for, which arrives as a cut down page rather than ' +
      'as an error',
  }],
  ['files.list', { ceiling: 1000, recommended: 200, items: 'files', params: {} }],
]);

/**
 * Judge a configured page size offline. Pure, and needs no token.
 * Knowing that 5000 will be refused before spending a request to find out is
 * the cheapest finding in this script.
 */
export function limitVerdict(method, limit, table = METHODS) {
  const spec = table.get(String(method ?? ''));
  if (spec === undefined) {
    return ['unknown-method',
      `${method} is not in this table, so nothing can be said about its page ` +
      'size ceiling. Its own reference page states it.'];
  }

  if (limit === null || limit === undefined || String(limit).trim() === '') {
    return ['defaulted',
      'no limit is being sent, so Slack uses its default of 100 items. That is a ' +
      'legitimate choice and it is rarely a deliberate one.'];
  }

  const n = Number(limit);
  if (!Number.isInteger(n)) {
    return ['not-a-number',
      `${limit} is not an integer. Whatever the client does with it, Slack will ` +
      'not read the number you meant.'];
  }
  if (n <= 0) {
    return ['not-a-number',
      `a limit of ${n} is not a page size. Anything at or below zero is a bug ` +
      'upstream of this call.'];
  }
  if (n > spec.ceiling) {
    return ['over-ceiling',
      `${n} is above the ${spec.ceiling} maximum for this method, so every call ` +
      'returns HTTP 200 with ok: false and error invalid_limit. Nothing ' +
      'downstream sees an exception; it sees an empty list.'];
  }
  if (n > spec.recommended) {
    return ['over-recommended',
      `${n} is legal, at or below the ${spec.ceiling} ceiling, and above the ` +
      `${spec.recommended} worth sending. ` + (spec.note ?? 'Large pages take ' +
      'longer to assemble and time out sooner than the extra round trips they save.')];
  }
  return ['within-limits',
    `${n} is at or under the recommended page size of ${spec.recommended}`];
}

/**
 * Classify one response against the request that produced it. Pure.
 * Four outcomes that are not variations on each other.
 */
export function pageVerdict(asked, returned, cursor, error = null) {
  const err = String(error ?? '').trim();
  if (err === 'invalid_limit') {
    return ['rejected',
      `invalid_limit: ${asked} is above this method's ceiling and the call ` +
      'returns nothing at all. Lower the constant.'];
  }
  if (err) {
    return ['unreadable',
      `the call answered ok: false with error ${err}, so the page size was never ` +
      'exercised. Fix that first.'];
  }

  const got = Number(returned) || 0;
  const want = Number(asked) || 0;
  const hasCursor = Boolean(String(cursor ?? '').trim());

  if (got >= want) {
    return ['honoured',
      `asked ${want}, got ${got}, cursor ${hasCursor ? 'set' : 'empty'}`];
  }
  if (hasCursor) {
    return ['cut-down',
      `asked ${want}, got ${got}, and a cursor is waiting. Slack chose the page ` +
      'size, not your constant. Code that reads a short page as the end of the ' +
      'data is truncating here with ok: true.'];
  }
  return ['short-final',
    `asked ${want}, got ${got}, no cursor: the data ran out. This is the method ` +
    'behaving correctly.'];
}

/** The value to set, per method, so a finding ends in a number. Pure. */
export function repairFor(method, verdict, table = METHODS) {
  const spec = table.get(String(method ?? ''));
  const rec = spec ? spec.recommended : 200;
  if (verdict === 'over-ceiling' || verdict === 'rejected') {
    return `set limit=${rec} for ${method}; the ceiling is ${spec ? spec.ceiling : 1000} ` +
      'and asking past it returns nothing';
  }
  if (verdict === 'over-recommended') {
    return `lower limit to ${rec} for ${method}; the extra round trips cost less ` +
      'than the timeouts';
  }
  if (verdict === 'cut-down') {
    return 'a smaller limit will not change this: the repair is in the pagination, ' +
      'which must follow response_metadata.next_cursor rather than stopping on a ' +
      `short page. Send limit=${rec} and loop`;
  }
  if (verdict === 'defaulted') {
    return `send limit=${rec} explicitly for ${method} rather than inheriting 100`;
  }
  return `nothing to change for ${method}`;
}

async function probe(token, method, spec, limit, channel) {
  const params = new URLSearchParams({ ...spec.params, limit: String(limit) });
  if (spec.needsChannel) params.set('channel', channel);
  const res = await fetch(`${API}${method}?${params}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return res.json();
}

function arg(args, name, fallback = null) {
  const i = args.indexOf(name);
  return i === -1 ? fallback : args[i + 1];
}

async function main() {
  const args = process.argv.slice(2);
  const limit = arg(args, '--limit', '1000');
  const channel = arg(args, '--channel', '');

  let bad = 0;
  for (const [method] of METHODS) {
    const [verdict, detail] = limitVerdict(method, limit);
    const line = `${method.padEnd(22)} ${'configured'.padEnd(11)} ` +
      `${verdict.padEnd(15)} ${detail}`;
    if (verdict === 'within-limits') {
      console.log(line);
    } else {
      console.warn(line);
      console.warn(`  repair: ${repairFor(method, verdict)}`);
      bad += 1;
    }
  }

  if (args.includes('--offline')) {
    console.log(`${bad} configured page size(s) worth changing`);
    process.exitCode = bad ? 1 : 0;
    return;
  }

  const tokenEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
  const token = process.env[tokenEnv];
  if (!token) {
    console.error(`set ${tokenEnv}, or pass --offline to check the constants only`);
    process.exitCode = 2;
    return;
  }

  let live = 0;
  for (const [method, spec] of METHODS) {
    if (spec.needsChannel && !channel) {
      console.log(`${method.padEnd(22)} ${'response'.padEnd(11)} ` +
        `${'skipped'.padEnd(15)} pass --channel to exercise this one`);
      continue;
    }
    const body = await probe(token, method, spec, limit, channel);
    const cursor = body.response_metadata?.next_cursor ?? '';
    const [verdict, detail] = pageVerdict(limit, (body[spec.items] ?? []).length,
      cursor, body.ok === true ? null : body.error);
    const line = `${method.padEnd(22)} ${'response'.padEnd(11)} ` +
      `${verdict.padEnd(15)} ${detail}`;
    if (verdict === 'honoured' || verdict === 'short-final') {
      console.log(line);
      continue;
    }
    console.warn(line);
    console.warn(`  repair: ${repairFor(method, verdict)}`);
    if (spec.note) console.warn(`  context: ${spec.note}`);
    live += 1;
  }

  console.log(`${live} method(s) not answering at the size they were asked`);
  process.exitCode = (live || bad) ? 1 : 0;
}

// Only run when invoked directly, so importing this module in the tests does
// not execute main() and fail the file on a missing token.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The two halves are tested separately because they answer different questions. <code>limit_verdict</code> is exercised with no network at all: 5000 is doomed, 1000 is legal and unwise, 200 is fine, and a method the table has never heard of produces an admission rather than a guess. <code>page_verdict</code> gets the case the whole note is about, which is a request for two hundred answered with fifteen and a cursor, asserted to come back as <code>cut-down</code> and never as the end of the data.",
"test_py_file": "test_slack_page_size_audit.py",
"test_py": '''from slack_page_size_audit import limit_verdict, page_verdict, repair_for


def test_five_thousand_is_rejected_before_a_request_is_spent():
    verdict, detail = limit_verdict("conversations.list", 5000)
    assert verdict == "over-ceiling"
    assert "invalid_limit" in detail


def test_a_thousand_is_legal_and_still_worth_lowering():
    verdict, detail = limit_verdict("users.list", 1000)
    assert verdict == "over-recommended"
    assert "200" in detail


def test_the_recommended_value_passes_cleanly():
    assert limit_verdict("users.list", 200)[0] == "within-limits"
    assert limit_verdict("conversations.list", 100)[0] == "within-limits"


def test_an_unknown_method_is_admitted_rather_than_guessed_at():
    verdict, detail = limit_verdict("chat.scheduledMessages.list", 200)
    assert verdict == "unknown-method"
    assert "reference page" in detail


def test_sending_no_limit_at_all_is_its_own_finding():
    assert limit_verdict("users.list", None)[0] == "defaulted"
    assert limit_verdict("users.list", "")[0] == "defaulted"


def test_a_limit_that_is_not_a_page_size_is_caught_here_not_by_slack():
    assert limit_verdict("users.list", "two hundred")[0] == "not-a-number"
    assert limit_verdict("users.list", 0)[0] == "not-a-number"
    assert limit_verdict("users.list", -5)[0] == "not-a-number"


def test_the_full_page_you_asked_for_is_honoured():
    verdict, detail = page_verdict(200, 200, "dXNlcjpVMDYx")
    assert verdict == "honoured"
    assert "cursor set" in detail


def test_fifteen_messages_with_a_cursor_is_the_clamp_not_the_end():
    verdict, detail = page_verdict(200, 15, "dXNlcjpVMDYx")
    assert verdict == "cut-down"
    assert "Slack chose the page size" in detail


def test_fifteen_messages_with_no_cursor_is_correct_behaviour():
    verdict, detail = page_verdict(200, 15, "")
    assert verdict == "short-final"
    assert "the data ran out" in detail


def test_the_error_string_is_reported_as_a_rejection_not_a_short_page():
    verdict, detail = page_verdict(5000, 0, "", "invalid_limit")
    assert verdict == "rejected"
    assert "5000" in detail


def test_any_other_error_means_the_page_size_was_never_exercised():
    verdict, detail = page_verdict(200, 0, "", "missing_scope")
    assert verdict == "unreadable"
    assert "missing_scope" in detail


def test_a_clamp_is_not_repaired_by_lowering_the_constant():
    assert "next_cursor" in repair_for("conversations.history", "cut-down")
    assert "set limit=200" in repair_for("conversations.list", "over-ceiling")
    assert repair_for("conversations.list", "honoured").startswith("nothing to change")
''',
"test_js_file": "slack-page-size-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { limitVerdict, pageVerdict, repairFor } from './slack-page-size-audit.mjs';

test('five thousand is rejected before a request is spent', () => {
  const [verdict, detail] = limitVerdict('conversations.list', 5000);
  assert.equal(verdict, 'over-ceiling');
  assert.match(detail, /invalid_limit/);
});

test('a thousand is legal and still worth lowering', () => {
  const [verdict, detail] = limitVerdict('users.list', 1000);
  assert.equal(verdict, 'over-recommended');
  assert.match(detail, /200/);
});

test('the recommended value passes cleanly', () => {
  assert.equal(limitVerdict('users.list', 200)[0], 'within-limits');
  assert.equal(limitVerdict('conversations.list', 100)[0], 'within-limits');
});

test('an unknown method is admitted rather than guessed at', () => {
  const [verdict, detail] = limitVerdict('chat.scheduledMessages.list', 200);
  assert.equal(verdict, 'unknown-method');
  assert.match(detail, /reference page/);
});

test('sending no limit at all is its own finding', () => {
  assert.equal(limitVerdict('users.list', null)[0], 'defaulted');
  assert.equal(limitVerdict('users.list', '')[0], 'defaulted');
});

test('a limit that is not a page size is caught here not by slack', () => {
  assert.equal(limitVerdict('users.list', 'two hundred')[0], 'not-a-number');
  assert.equal(limitVerdict('users.list', 0)[0], 'not-a-number');
  assert.equal(limitVerdict('users.list', -5)[0], 'not-a-number');
});

test('the full page you asked for is honoured', () => {
  const [verdict, detail] = pageVerdict(200, 200, 'dXNlcjpVMDYx');
  assert.equal(verdict, 'honoured');
  assert.match(detail, /cursor set/);
});

test('fifteen messages with a cursor is the clamp not the end', () => {
  const [verdict, detail] = pageVerdict(200, 15, 'dXNlcjpVMDYx');
  assert.equal(verdict, 'cut-down');
  assert.match(detail, /Slack chose the page size/);
});

test('fifteen messages with no cursor is correct behaviour', () => {
  const [verdict, detail] = pageVerdict(200, 15, '');
  assert.equal(verdict, 'short-final');
  assert.match(detail, /the data ran out/);
});

test('the error string is reported as a rejection not a short page', () => {
  const [verdict, detail] = pageVerdict(5000, 0, '', 'invalid_limit');
  assert.equal(verdict, 'rejected');
  assert.match(detail, /5000/);
});

test('any other error means the page size was never exercised', () => {
  const [verdict, detail] = pageVerdict(200, 0, '', 'missing_scope');
  assert.equal(verdict, 'unreadable');
  assert.match(detail, /missing_scope/);
});

test('a clamp is not repaired by lowering the constant', () => {
  assert.match(repairFor('conversations.history', 'cut-down'), /next_cursor/);
  assert.match(repairFor('conversations.list', 'over-ceiling'), /set limit=200/);
  assert.match(repairFor('conversations.list', 'honoured'), /^nothing to change/);
});
''',
"faq": [
 ("What is the actual maximum for limit?",
  "1000 on the cursor-paginated methods, and each method's own reference page is the authority. There is no global constant and no response header that reports it, which is why the script keeps a small table for the offline check and then measures the real answer with one request per method rather than trusting the table."),
 ("Why did my call return fewer items without an error?",
  "Because Slack decided the page size instead of refusing your number. The commonest cause in 2026 is the history clamp on apps that are not on the Slack Marketplace, which returns fifteen objects per call regardless of the request. A short page with a non-empty next_cursor always means there is more data, whatever the reason the page was small."),
 ("Is a large limit faster than paginating?",
  "Usually not, and past a point it is slower. A request for a thousand users takes longer to assemble server side and is more likely to time out than five requests for two hundred, which is why Slack's own guidance recommends 200 for users.list on large workspaces. The page size chosen to avoid writing a loop is often the one that makes the call unreliable."),
 ("Should the audit follow the cursor to check the totals?",
  "No, on purpose. One call per method is enough to compare the request against the response, and walking every page would spend the rate budget of the very method being measured, on a Tier 2 or Tier 3 limit, to answer a question one request already answered. Whether your application follows cursors correctly is a separate check."),
 ("The constant is fine now. Will this stay fixed?",
  "The constant will. The clamp will not: Slack has changed per-method page ceilings before, and the change arrives as smaller pages rather than as an error, so nothing in your code will notice. Running this check on a schedule costs six requests and catches a ceiling that moved under you."),
],
"related": [
 ("/slack/pagination-not-followed/", "the loop that has to follow the cursor"),
 ("/slack/non-marketplace-history-clamp/", "why fifteen is the page you got"),
 ("/slack/http-200-ok-false/", "why invalid_limit arrives as a success"),
],
"citations": [CITE_PAGINATION, CITE_CONV_LIST, CITE_USERS_LIST, CITE_CONV_MEMBERS],
})

GUIDES.append({
"slug": "invalid-cursor",
"title": "invalid_cursor: a stored cursor replayed after expiry",
"description": "A cursor is a short-lived token bound to the query that made it, not an offset. Audit the checkpoints a resumable sync persists before the restart fails.",
"h1": "invalid_cursor: a stored cursor replayed after expiry",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack invalid_cursor", "slack next_cursor expired",
             "slack resume pagination", "slack cursor checkpoint",
             "slack pagination cursor lifetime"],
"deps": "Python 3.9+ with requests, or Node.js 18+; a checkpoint file the job already writes",
"lead": "The sync job is careful. It follows every cursor, it handles rate limits, and when it is interrupted it writes <code>next_cursor</code> to the database so the next run can pick up where it left off. That last part was tested by restarting the job immediately, which worked perfectly.</p><p>Six weeks later the job is stopped for a deploy on a Friday and started again on a Monday, and it comes back <code>invalid_cursor</code> on the first call. Nothing was corrupted. The checkpoint is exactly the string Slack handed over. It just is not a checkpoint.",
"short_answer": """<p>Slack's pagination cursors are opaque and short-lived, and they encode the <em>query</em> as well as the position. That makes them safe to use inside one pagination loop and unsafe for anything else. Persisting one to resume across runs fails in two ways that look identical from the outside: the cursor aged out, or the parameters sent with the continuation are not the parameters that produced it. Changing <code>limit</code>, <code>types</code> or <code>exclude_archived</code> between pages is enough.</p>
<p>So the audit is not of your pagination loop, which may be perfect. It is of the checkpoint records your job persists. The script below reads them, dates them, compares the parameters recorded against the parameters that would be sent now, and then replays each cursor once alongside a control call with no cursor at all. The control is the point: it separates "this cursor is dead" from "this method is broken", which the error string alone will not do. What it prints is the stable key to checkpoint on instead, per method.</p>""",
"problem": """<p>A cursor looks exactly like a resumable offset. It is a string, it means "carry on from here", and the obvious thing to do with it when a long job is interrupted is to write it down. Every database has somewhere to put a string. The tests pass, because the tests restart the job within seconds of stopping it.</p>
<p>Then the job is stopped for a weekend, or a queue backs up, or a retry fires a day later, and the resume call returns <code>ok: false</code> with <code>invalid_cursor</code>. The natural reading is that something corrupted the value. It did not. Cursors are time-limited by design, and the lifetime is not a number Slack publishes, so there is no timeout to configure and no header that says when it expires. The only durable statement is the one in the documentation: cursors are for the loop that created them.</p>
<p>The second failure has nothing to do with time and produces the same error, which is what makes this genuinely hard to debug. The cursor encodes the query. A job that pages <code>conversations.list</code> with <code>types=public_channel</code> and then, on resume, sends the same cursor with <code>types=public_channel,private_channel</code> because somebody widened a config value, gets <code>invalid_cursor</code> on a cursor that is minutes old. The parameters and the cursor have to match, and nothing in the stored string will tell you what they were unless you stored them alongside it.</p>""",
"why": """<p><strong>A cursor is a continuation token, not an offset.</strong> It carries the position and the query together, opaquely. There is no stable meaning to extract from it, no expiry to read out of it, and no way to migrate one to a different parameter set. Treating it as data that can be stored is the whole bug.</p>
<p><strong>The lifetime is unspecified, so it cannot be checked against a clock you control.</strong> The honest test is not "is this cursor still valid", which nobody can answer offline. It is "how old is this checkpoint", with a budget you chose. Anything hours old is a finding before it errors, which is the only moment at which this is cheap to fix.</p>
<p><strong>A checkpoint with no timestamp is worse than a stale one.</strong> If the record does not say when the cursor was issued, nothing downstream can decide whether to trust it, and the job will keep replaying a value of unknown age forever. The script reports undated records as their own verdict rather than assuming they are fresh.</p>
<p><strong>Parameter drift is invisible and produces the same error as expiry.</strong> Storing the parameters next to the cursor costs nothing and turns an unattributable failure into a diff. Without it, a config change three commits away looks exactly like an expired token.</p>
<p><strong>The control call is what makes the finding attributable.</strong> Replaying a cursor that fails tells you very little on its own; the method could be broken, the scope could have been removed, the channel could have been archived. One call with the same parameters and no cursor separates those cases in a single request, and it is the difference between "the cursor is dead" and "everything here is dead".</p>""",
"steps": [
 {"h": "Find where the job writes its checkpoints",
  "body": """<p>A table, a Redis key, a JSON file on a volume. The script reads a JSON array of records, so export whatever you have into that shape once; the records need a method, a cursor, ideally the parameters it was issued with, and ideally a timestamp.</p>"""},
 {"h": "Date every record before touching the network",
  "body": """<p><code>staleness_verdict</code> is offline. It sorts records into fresh, aging, expired by age, and undated, against a budget you set. A record from Friday afternoon on a Monday morning is a finding whether or not the replay happens to work.</p>"""},
 {"h": "Diff the parameters against what the job would send now",
  "body": """<p><code>params_drifted</code> returns the keys that changed. A cursor issued under <code>types=public_channel</code> and replayed under a wider set is dead on arrival, and the diff names the config value somebody widened rather than leaving you with an error string.</p>"""},
 {"h": "Take a control reading with no cursor at all",
  "body": """<p>One GET, same method, same parameters, cursor omitted. If that fails too, the cursor was never the problem and the finding is about scopes or the channel. If it succeeds and the replay fails, the cursor is confirmed dead and the attribution is exact.</p>"""},
 {"h": "Replay the stored cursor once and classify it",
  "body": """<p>Once. A cursor that returned <code>invalid_cursor</code> will keep doing so, and retrying it is how a resumable job turns one dead checkpoint into a rate limit. The verdict is <code>cursor-rejected</code>, <code>accepted</code>, or an error that belongs to something else.</p>"""},
 {"h": "Replace the checkpoint with a key that means something",
  "body": """<p>The printed repair is per method: the <code>ts</code> of the newest message you stored, passed as <code>oldest</code> on the next run for the history methods; the last ID you processed for the list methods, restarting pagination from the beginning. Both survive a weekend, a deploy, and a change to <code>types</code>.</p>"""},
],
"verify": """<p>Re-run after the job checkpoints on a stable key. The checkpoint file should hold no cursors at all, which the script reports as nothing to audit.</p>
<pre><code class="language-bash">python3 slack_cursor_checkpoint_audit.py checkpoints.json --max-age 3600
# conversations.list   age      expired-by-age   issued 261,143s ago, over the 3600s budget
# conversations.list   params   drifted          types changed since the cursor was issued
# conversations.list   control  reachable        the same call without a cursor answered ok
# conversations.list   replay   cursor-rejected  invalid_cursor: the stored value is dead
#   repair: checkpoint the last channel ID you processed and restart pagination
# 1 checkpoint(s) that will not resume</code></pre>""",
"code_intro": "Four pure functions and two GETs per record. <code>staleness_verdict</code> and <code>params_drifted</code> run with no token at all, which matters because most of these findings are visible in the checkpoint file alone. <code>replay_verdict</code> keeps a dead cursor apart from a broken call, and <code>checkpoint_repair</code> answers the only question the reader actually has, which is what to store instead.",
"py_file": "slack_cursor_checkpoint_audit.py",
"py": '''"""Audit the pagination cursors a resumable Slack job persisted.

Read only. For each stored checkpoint: date it, diff the parameters it was
issued under against the ones that would be sent now, take one control reading
with no cursor, and replay the cursor exactly once. Nothing is written and no
checkpoint is repaired; the key to store instead is printed per method.

The checkpoint file is a JSON array of records:

  [{"method": "conversations.list",
    "cursor": "dGVhbTpDMDYxRkE1UEI=",
    "issued_at": 1756400000,
    "params": {"types": "public_channel", "limit": "200"}}]
"""
import argparse
import json
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_cursor_checkpoint_audit")

API = "https://slack.com/api/"

# What to checkpoint instead, per method. Every one of these is a value that
# still means the same thing after a weekend, a deploy and a config change,
# which is the whole property a cursor does not have.
STABLE_KEYS = {
    "conversations.history": "the ts of the newest message you stored, sent as "
                             "oldest on the next run",
    "conversations.replies": "the thread ts plus the ts of the last reply you "
                             "stored, sent as oldest",
    "conversations.list": "the last channel ID you processed, restarting "
                          "pagination from the beginning and skipping past it",
    "users.list": "the last user ID you processed, restarting pagination from "
                  "the beginning",
    "users.conversations": "the last channel ID you processed, restarting "
                           "pagination from the beginning",
    "conversations.members": "the last member ID you processed, restarting "
                             "pagination from the beginning",
    "files.list": "the ts_to of the window you finished, used as the next run's "
                  "ts_from",
}

# Parameters that are part of the query a cursor encodes. Changing any of them
# between the call that issued the cursor and the call that replays it
# invalidates the cursor, and produces exactly the error an expired one does.
QUERY_KEYS = ("types", "exclude_archived", "exclude_members", "limit", "channel",
              "user", "oldest", "latest", "inclusive", "team_id")


def staleness_verdict(issued_at, now=None, max_age=3600):
    """Date one checkpoint. Pure, offline, and the cheapest check here.

    Slack does not publish how long a cursor lives, so this cannot answer "is
    it still valid". It answers "how old is this", against a budget you chose,
    which is the question that is actually decidable.
    """
    when = time.time() if now is None else float(now)
    if issued_at in (None, "", 0):
        return ("undated",
                "the record does not say when the cursor was issued, so nothing "
                "downstream can decide whether to trust it. An undated checkpoint "
                "is replayed forever at an unknown age.")
    try:
        age = when - float(issued_at)
    except (TypeError, ValueError):
        return ("undated",
                "the issued_at value %r is not a timestamp, so this record is "
                "effectively undated." % issued_at)

    if age < 0:
        return ("undated",
                "the checkpoint is dated %.0fs in the future, so the clock that "
                "wrote it and the clock reading it disagree. Treat the age as "
                "unknown." % -age)
    budget = float(max_age)
    if age > budget:
        return ("expired-by-age",
                "issued %.0fs ago, over the %.0fs budget. Cursors are scoped to "
                "the loop that created them and this one has outlived any loop."
                % (age, budget))
    if age > budget / 2:
        return ("aging",
                "issued %.0fs ago, over half the %.0fs budget. It may still work "
                "and it is not something to depend on." % (age, budget))
    return ("fresh", "issued %.0fs ago, inside the %.0fs budget" % (age, budget))


def params_drifted(issued_with, sending_now, keys=QUERY_KEYS):
    """The query keys that changed since the cursor was issued. Pure.

    A cursor encodes the query as well as the position, so a widened types
    value invalidates a cursor that is thirty seconds old, with the same error
    an expired one gives. Storing the parameters is what turns that into a diff.
    """
    was = dict(issued_with or {})
    now = dict(sending_now or {})
    out = []
    for key in keys:
        a = was.get(key)
        b = now.get(key)
        if a is None and b is None:
            continue
        if str(a) != str(b):
            out.append(key)
    return sorted(out)


def replay_verdict(ok, error=None, control_ok=True):
    """Classify one replay, with the control reading beside it. Pure.

    The control is the whole reason this can attribute anything. A failed
    replay on its own is ambiguous between a dead cursor, a removed scope and
    an archived channel; the same call without a cursor separates them.
    """
    err = str(error or "").strip()
    if not control_ok:
        return ("call-unreachable",
                "the same call without a cursor also failed%s, so the cursor is "
                "not what is wrong here. Fix the call first."
                % (" with %s" % err if err else ""))
    if ok is True:
        return ("accepted",
                "the stored cursor was still valid at the moment it was replayed. "
                "That is luck rather than a design: nothing about it will be true "
                "tomorrow.")
    if err == "invalid_cursor":
        return ("cursor-rejected",
                "invalid_cursor: the stored value is dead. Age and parameter "
                "drift both produce this and the checks above say which.")
    if err:
        return ("other-error",
                "the replay failed with %s, which is not a cursor problem. The "
                "control call succeeded, so something about this specific "
                "continuation is different." % err)
    return ("inconclusive", "no result and no error was recorded for this replay")


def checkpoint_repair(method):
    """What to store instead of a cursor, for this method. Pure."""
    stable = STABLE_KEYS.get(str(method or ""))
    if stable is None:
        return ("checkpoint on a stable, meaningful key from the items "
                "themselves rather than on the cursor: the last ID or timestamp "
                "you finished with, restarting pagination from the beginning")
    return "checkpoint %s" % stable


def read_checkpoints(path):
    """The stored records. Read only, and the only file this script opens."""
    with open(path, "r", encoding="utf-8") as fh:
        records = json.load(fh)
    if isinstance(records, dict):
        records = [records]
    return [r for r in records if isinstance(r, dict)]


def call(session, method, params):
    """One GET. Returns (ok, error)."""
    body = session.get(API + method, params=params, timeout=30).json()
    return (body.get("ok") is True, body.get("error"))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("checkpoints", help="JSON file of stored cursor records")
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN",
                    help="environment variable holding the bot token")
    ap.add_argument("--max-age", type=float, default=3600,
                    help="seconds a checkpoint may be old before it is a finding")
    ap.add_argument("--offline", action="store_true",
                    help="date and diff the records without replaying anything")
    args = ap.parse_args()

    records = read_checkpoints(args.checkpoints)
    if not records:
        log.info("no cursors stored, which is the state this note is arguing for")
        return 0

    session = None
    if not args.offline:
        token = os.environ.get(args.token_env)
        if not token:
            log.error("set %s, or pass --offline to audit the file alone",
                      args.token_env)
            return 2
        session = requests.Session()
        session.headers.update({"Authorization": "Bearer " + token})

    bad = 0
    for record in records:
        method = str(record.get("method") or "?")
        issued_with = record.get("params") or {}
        sending_now = record.get("params_now") or issued_with
        cursor = str(record.get("cursor") or "")
        failed = False

        verdict, detail = staleness_verdict(record.get("issued_at"), None, args.max_age)
        (log.info if verdict == "fresh" else log.warning)(
            "%-20s %-8s %-16s %s", method, "age", verdict, detail)
        failed = failed or verdict != "fresh"

        drift = params_drifted(issued_with, sending_now)
        if drift:
            log.warning("%-20s %-8s %-16s %s changed since the cursor was issued",
                        method, "params", "drifted", ", ".join(drift))
            failed = True
        else:
            log.info("%-20s %-8s %-16s the query is unchanged",
                     method, "params", "stable")

        if session is not None and cursor:
            control_ok, control_err = call(session, method, dict(sending_now))
            log.info("%-20s %-8s %-16s %s", method, "control",
                     "reachable" if control_ok else "unreachable",
                     "the same call without a cursor answered ok" if control_ok
                     else "the same call without a cursor failed with %s" % control_err)
            ok, err = call(session, method, dict(sending_now, cursor=cursor))
            rv, rd = replay_verdict(ok, err, control_ok)
            (log.info if rv == "accepted" else log.warning)(
                "%-20s %-8s %-16s %s", method, "replay", rv, rd)
            failed = failed or rv != "accepted"

        if failed:
            bad += 1
            log.warning("  repair: %s", checkpoint_repair(method))
            log.warning("  repair: keep cursors in memory for the life of one "
                        "pagination loop and never write one down")

    log.info("%d checkpoint(s) that will not resume, out of %d",
             bad, len(records))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-cursor-checkpoint-audit.mjs",
"js": '''/**
 * Audit the pagination cursors a resumable Slack job persisted.
 *
 * Read only. For each stored checkpoint: date it, diff the parameters it was
 * issued under against the ones that would be sent now, take one control
 * reading with no cursor, and replay the cursor exactly once. Nothing is
 * written and no checkpoint is repaired; the key to store instead is printed.
 */

import { readFile } from 'node:fs/promises';

const API = 'https://slack.com/api/';

// What to checkpoint instead, per method. Every one of these still means the
// same thing after a weekend, a deploy and a config change.
const STABLE_KEYS = new Map([
  ['conversations.history',
    'the ts of the newest message you stored, sent as oldest on the next run'],
  ['conversations.replies',
    'the thread ts plus the ts of the last reply you stored, sent as oldest'],
  ['conversations.list',
    'the last channel ID you processed, restarting pagination from the beginning ' +
    'and skipping past it'],
  ['users.list',
    'the last user ID you processed, restarting pagination from the beginning'],
  ['users.conversations',
    'the last channel ID you processed, restarting pagination from the beginning'],
  ['conversations.members',
    'the last member ID you processed, restarting pagination from the beginning'],
  ['files.list',
    "the ts_to of the window you finished, used as the next run's ts_from"],
]);

// Parameters that are part of the query a cursor encodes. Changing any of them
// invalidates the cursor, with exactly the error an expired one gives.
const QUERY_KEYS = ['types', 'exclude_archived', 'exclude_members', 'limit',
  'channel', 'user', 'oldest', 'latest', 'inclusive', 'team_id'];

/**
 * Date one checkpoint. Pure, offline, and the cheapest check here.
 * Slack does not publish how long a cursor lives, so this answers "how old is
 * this" against a budget you chose, which is the decidable question.
 */
export function stalenessVerdict(issuedAt, now = null, maxAge = 3600) {
  const when = now === null ? Date.now() / 1000 : Number(now);
  if (issuedAt === null || issuedAt === undefined || issuedAt === '' || issuedAt === 0) {
    return ['undated',
      'the record does not say when the cursor was issued, so nothing downstream ' +
      'can decide whether to trust it. An undated checkpoint is replayed forever ' +
      'at an unknown age.'];
  }
  const stamp = Number(issuedAt);
  if (!Number.isFinite(stamp)) {
    return ['undated',
      `the issued_at value ${issuedAt} is not a timestamp, so this record is ` +
      'effectively undated.'];
  }

  const age = when - stamp;
  if (age < 0) {
    return ['undated',
      `the checkpoint is dated ${(-age).toFixed(0)}s in the future, so the clock ` +
      'that wrote it and the clock reading it disagree. Treat the age as unknown.'];
  }
  const budget = Number(maxAge);
  if (age > budget) {
    return ['expired-by-age',
      `issued ${age.toFixed(0)}s ago, over the ${budget.toFixed(0)}s budget. ` +
      'Cursors are scoped to the loop that created them and this one has ' +
      'outlived any loop.'];
  }
  if (age > budget / 2) {
    return ['aging',
      `issued ${age.toFixed(0)}s ago, over half the ${budget.toFixed(0)}s budget. ` +
      'It may still work and it is not something to depend on.'];
  }
  return ['fresh', `issued ${age.toFixed(0)}s ago, inside the ${budget.toFixed(0)}s budget`];
}

/**
 * The query keys that changed since the cursor was issued. Pure.
 * A widened types value invalidates a cursor that is thirty seconds old, with
 * the same error an expired one gives.
 */
export function paramsDrifted(issuedWith, sendingNow, keys = QUERY_KEYS) {
  const was = { ...(issuedWith ?? {}) };
  const now = { ...(sendingNow ?? {}) };
  const out = [];
  for (const key of keys) {
    const a = was[key];
    const b = now[key];
    if ((a === undefined || a === null) && (b === undefined || b === null)) continue;
    if (String(a) !== String(b)) out.push(key);
  }
  return out.sort();
}

/**
 * Classify one replay, with the control reading beside it. Pure.
 * A failed replay on its own is ambiguous between a dead cursor, a removed
 * scope and an archived channel; the control call separates them.
 */
export function replayVerdict(ok, error = null, controlOk = true) {
  const err = String(error ?? '').trim();
  if (!controlOk) {
    return ['call-unreachable',
      'the same call without a cursor also failed' + (err ? ` with ${err}` : '') +
      ', so the cursor is not what is wrong here. Fix the call first.'];
  }
  if (ok === true) {
    return ['accepted',
      'the stored cursor was still valid at the moment it was replayed. That is ' +
      'luck rather than a design: nothing about it will be true tomorrow.'];
  }
  if (err === 'invalid_cursor') {
    return ['cursor-rejected',
      'invalid_cursor: the stored value is dead. Age and parameter drift both ' +
      'produce this and the checks above say which.'];
  }
  if (err) {
    return ['other-error',
      `the replay failed with ${err}, which is not a cursor problem. The control ` +
      'call succeeded, so something about this specific continuation is different.'];
  }
  return ['inconclusive', 'no result and no error was recorded for this replay'];
}

/** What to store instead of a cursor, for this method. Pure. */
export function checkpointRepair(method) {
  const stable = STABLE_KEYS.get(String(method ?? ''));
  if (stable === undefined) {
    return 'checkpoint on a stable, meaningful key from the items themselves ' +
      'rather than on the cursor: the last ID or timestamp you finished with, ' +
      'restarting pagination from the beginning';
  }
  return `checkpoint ${stable}`;
}

async function call(token, method, params) {
  const res = await fetch(`${API}${method}?${new URLSearchParams(params)}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const body = await res.json();
  return [body.ok === true, body.error];
}

function arg(args, name, fallback = null) {
  const i = args.indexOf(name);
  return i === -1 ? fallback : args[i + 1];
}

async function main() {
  const args = process.argv.slice(2);
  const path = args.find((a) => !a.startsWith('--')
    && args[args.indexOf(a) - 1]?.startsWith('--') !== true);
  if (!path) {
    console.error('usage: <checkpoints.json> [--max-age 3600] [--offline]');
    process.exitCode = 2;
    return;
  }
  const maxAge = Number(arg(args, '--max-age', 3600));
  const offline = args.includes('--offline');

  const records = JSON.parse(await readFile(path, 'utf-8'));
  const list = (Array.isArray(records) ? records : [records])
    .filter((r) => r && typeof r === 'object');
  if (list.length === 0) {
    console.log('no cursors stored, which is the state this note is arguing for');
    return;
  }

  let token = null;
  if (!offline) {
    const tokenEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
    token = process.env[tokenEnv];
    if (!token) {
      console.error(`set ${tokenEnv}, or pass --offline to audit the file alone`);
      process.exitCode = 2;
      return;
    }
  }

  let bad = 0;
  for (const record of list) {
    const method = String(record.method ?? '?');
    const issuedWith = record.params ?? {};
    const sendingNow = record.params_now ?? issuedWith;
    const cursor = String(record.cursor ?? '');
    let failed = false;

    const [verdict, detail] = stalenessVerdict(record.issued_at, null, maxAge);
    (verdict === 'fresh' ? console.log : console.warn)(
      `${method.padEnd(20)} ${'age'.padEnd(8)} ${verdict.padEnd(16)} ${detail}`);
    failed = failed || verdict !== 'fresh';

    const drift = paramsDrifted(issuedWith, sendingNow);
    if (drift.length > 0) {
      console.warn(`${method.padEnd(20)} ${'params'.padEnd(8)} ${'drifted'.padEnd(16)} ` +
        `${drift.join(', ')} changed since the cursor was issued`);
      failed = true;
    } else {
      console.log(`${method.padEnd(20)} ${'params'.padEnd(8)} ${'stable'.padEnd(16)} ` +
        'the query is unchanged');
    }

    if (token !== null && cursor) {
      const [controlOk, controlErr] = await call(token, method, { ...sendingNow });
      console.log(`${method.padEnd(20)} ${'control'.padEnd(8)} ` +
        `${(controlOk ? 'reachable' : 'unreachable').padEnd(16)} ` +
        (controlOk ? 'the same call without a cursor answered ok'
          : `the same call without a cursor failed with ${controlErr}`));
      const [ok, err] = await call(token, method, { ...sendingNow, cursor });
      const [rv, rd] = replayVerdict(ok, err, controlOk);
      (rv === 'accepted' ? console.log : console.warn)(
        `${method.padEnd(20)} ${'replay'.padEnd(8)} ${rv.padEnd(16)} ${rd}`);
      failed = failed || rv !== 'accepted';
    }

    if (failed) {
      bad += 1;
      console.warn(`  repair: ${checkpointRepair(method)}`);
      console.warn('  repair: keep cursors in memory for the life of one ' +
        'pagination loop and never write one down');
    }
  }

  console.log(`${bad} checkpoint(s) that will not resume, out of ${list.length}`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly, so importing this module in the tests does
// not execute main() and fail the file on a missing checkpoint path.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Every test passes an explicit <code>now</code>, so the clock is a parameter rather than an ambient fact and a suite that runs at midnight behaves like one that runs at noon. The cases that matter are the two that produce the same error for different reasons: a checkpoint from Friday replayed on Monday, and a cursor thirty seconds old replayed after somebody widened <code>types</code>. The last test is the one that stops the script overclaiming: when the control call fails too, the verdict is that the cursor was never the problem.",
"test_py_file": "test_slack_cursor_checkpoint_audit.py",
"test_py": '''from slack_cursor_checkpoint_audit import (checkpoint_repair, params_drifted,
                                            replay_verdict, staleness_verdict)

NOW = 1756400000.0
ISSUED = {"types": "public_channel", "exclude_archived": "true", "limit": "200"}


def test_a_checkpoint_from_friday_read_on_monday_is_expired():
    verdict, detail = staleness_verdict(NOW - 261143, NOW, 3600)
    assert verdict == "expired-by-age"
    assert "261143s ago" in detail


def test_a_checkpoint_inside_the_budget_is_fresh():
    assert staleness_verdict(NOW - 60, NOW, 3600)[0] == "fresh"


def test_past_half_the_budget_is_flagged_before_it_fails():
    assert staleness_verdict(NOW - 2000, NOW, 3600)[0] == "aging"


def test_a_record_with_no_timestamp_is_its_own_verdict():
    assert staleness_verdict(None, NOW, 3600)[0] == "undated"
    assert staleness_verdict("", NOW, 3600)[0] == "undated"
    assert staleness_verdict("last tuesday", NOW, 3600)[0] == "undated"


def test_a_checkpoint_dated_in_the_future_is_not_called_fresh():
    verdict, detail = staleness_verdict(NOW + 900, NOW, 3600)
    assert verdict == "undated"
    assert "disagree" in detail


def test_an_unchanged_query_drifts_in_no_keys():
    assert params_drifted(ISSUED, dict(ISSUED)) == []


def test_widening_types_is_the_drift_that_kills_a_fresh_cursor():
    now = dict(ISSUED, types="public_channel,private_channel")
    assert params_drifted(ISSUED, now) == ["types"]


def test_every_query_key_that_moved_is_named_and_sorted():
    now = dict(ISSUED, types="private_channel", limit="1000")
    assert params_drifted(ISSUED, now) == ["limit", "types"]


def test_a_key_added_or_removed_counts_as_drift():
    assert params_drifted(ISSUED, dict(ISSUED, oldest="1756300000.0")) == ["oldest"]
    without = {k: v for k, v in ISSUED.items() if k != "limit"}
    assert params_drifted(ISSUED, without) == ["limit"]


def test_the_dead_cursor_is_named_when_the_control_call_worked():
    verdict, detail = replay_verdict(False, "invalid_cursor", control_ok=True)
    assert verdict == "cursor-rejected"
    assert "invalid_cursor" in detail


def test_a_replay_that_still_works_is_called_luck_rather_than_a_design():
    verdict, detail = replay_verdict(True, None, control_ok=True)
    assert verdict == "accepted"
    assert "luck" in detail


def test_when_the_control_call_fails_the_cursor_is_not_blamed():
    verdict, detail = replay_verdict(False, "missing_scope", control_ok=False)
    assert verdict == "call-unreachable"
    assert "not what is wrong here" in detail


def test_an_unrelated_error_is_not_dressed_up_as_a_cursor_problem():
    assert replay_verdict(False, "channel_not_found", True)[0] == "other-error"
    assert replay_verdict(False, None, True)[0] == "inconclusive"


def test_the_repair_is_a_stable_key_and_it_differs_by_method():
    assert "oldest" in checkpoint_repair("conversations.history")
    assert "channel ID" in checkpoint_repair("conversations.list")
    assert "stable, meaningful key" in checkpoint_repair("some.future.method")
''',
"test_js_file": "slack-cursor-checkpoint-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { checkpointRepair, paramsDrifted, replayVerdict, stalenessVerdict }
  from './slack-cursor-checkpoint-audit.mjs';

const NOW = 1756400000.0;
const ISSUED = { types: 'public_channel', exclude_archived: 'true', limit: '200' };

test('a checkpoint from friday read on monday is expired', () => {
  const [verdict, detail] = stalenessVerdict(NOW - 261143, NOW, 3600);
  assert.equal(verdict, 'expired-by-age');
  assert.match(detail, /261143s ago/);
});

test('a checkpoint inside the budget is fresh', () => {
  assert.equal(stalenessVerdict(NOW - 60, NOW, 3600)[0], 'fresh');
});

test('past half the budget is flagged before it fails', () => {
  assert.equal(stalenessVerdict(NOW - 2000, NOW, 3600)[0], 'aging');
});

test('a record with no timestamp is its own verdict', () => {
  assert.equal(stalenessVerdict(null, NOW, 3600)[0], 'undated');
  assert.equal(stalenessVerdict('', NOW, 3600)[0], 'undated');
  assert.equal(stalenessVerdict('last tuesday', NOW, 3600)[0], 'undated');
});

test('a checkpoint dated in the future is not called fresh', () => {
  const [verdict, detail] = stalenessVerdict(NOW + 900, NOW, 3600);
  assert.equal(verdict, 'undated');
  assert.match(detail, /disagree/);
});

test('an unchanged query drifts in no keys', () => {
  assert.deepEqual(paramsDrifted(ISSUED, { ...ISSUED }), []);
});

test('widening types is the drift that kills a fresh cursor', () => {
  assert.deepEqual(paramsDrifted(ISSUED,
    { ...ISSUED, types: 'public_channel,private_channel' }), ['types']);
});

test('every query key that moved is named and sorted', () => {
  assert.deepEqual(paramsDrifted(ISSUED,
    { ...ISSUED, types: 'private_channel', limit: '1000' }), ['limit', 'types']);
});

test('a key added or removed counts as drift', () => {
  assert.deepEqual(paramsDrifted(ISSUED, { ...ISSUED, oldest: '1756300000.0' }),
    ['oldest']);
  const without = { ...ISSUED };
  delete without.limit;
  assert.deepEqual(paramsDrifted(ISSUED, without), ['limit']);
});

test('the dead cursor is named when the control call worked', () => {
  const [verdict, detail] = replayVerdict(false, 'invalid_cursor', true);
  assert.equal(verdict, 'cursor-rejected');
  assert.match(detail, /invalid_cursor/);
});

test('a replay that still works is called luck rather than a design', () => {
  const [verdict, detail] = replayVerdict(true, null, true);
  assert.equal(verdict, 'accepted');
  assert.match(detail, /luck/);
});

test('when the control call fails the cursor is not blamed', () => {
  const [verdict, detail] = replayVerdict(false, 'missing_scope', false);
  assert.equal(verdict, 'call-unreachable');
  assert.match(detail, /not what is wrong here/);
});

test('an unrelated error is not dressed up as a cursor problem', () => {
  assert.equal(replayVerdict(false, 'channel_not_found', true)[0], 'other-error');
  assert.equal(replayVerdict(false, null, true)[0], 'inconclusive');
});

test('the repair is a stable key and it differs by method', () => {
  assert.match(checkpointRepair('conversations.history'), /oldest/);
  assert.match(checkpointRepair('conversations.list'), /channel ID/);
  assert.match(checkpointRepair('some.future.method'), /stable, meaningful key/);
});
''',
"faq": [
 ("How long does a Slack pagination cursor live?",
  "Slack does not publish a number, and that is the answer rather than an omission. The documented contract is that a cursor continues one pagination loop, so any design that depends on a specific lifetime is depending on something nobody has promised. The script dates checkpoints against a budget you set because that is the only version of the question that can be answered."),
 ("Can I store the cursor if I refresh it often enough?",
  "You can, and it will still break on the day the parameters change, because a cursor encodes the query as well as the position. Widening types, switching exclude_archived, or raising limit between the call that issued the cursor and the call that replays it produces invalid_cursor on a cursor that is seconds old. Frequency does not help with that failure at all."),
 ("What should a resumable sync checkpoint instead?",
  "Something that still means what it meant last week. For conversations.history and conversations.replies that is the ts of the newest message you stored, passed as oldest on the next run. For the list methods it is the last ID you processed, restarting pagination from the beginning and skipping past it. Both survive a weekend and a config change."),
 ("Why does the script make a call without the cursor first?",
  "Because a failed replay on its own does not attribute anything. The cursor might be dead, or the scope might have been removed, or the channel might have been archived since the job last ran. One control request with the same parameters and no cursor tells those apart, and it turns invalid_cursor from a symptom into a conclusion."),
 ("The replay succeeded. Is the checkpoint fine?",
  "No, it is fresh. The script says so in those words on purpose: an accepted replay means the cursor had not expired at the instant it was tried, which is a fact about this minute rather than a property of the design. The finding to act on is that a cursor is being persisted at all, and that is true whether or not today's replay worked."),
],
"related": [
 ("/slack/pagination-not-followed/", "the loop that issues the cursor"),
 ("/slack/http-200-ok-false/", "invalid_cursor arrives as a 200"),
 ("/slack/non-marketplace-history-clamp/", "when the pages themselves shrank"),
],
"citations": [CITE_PAGINATION, CITE_CONV_HISTORY, CITE_CONV_LIST, CITE_USERS_LIST],
})

GUIDES.append({
"slug": "message-limit-exceeded",
"title": "message_limit_exceeded: the workspace posting cap",
"description": "Not your app's quota, the whole workspace's. Rank every sender in the busiest channels by messages per minute and find out whether it is even you.",
"h1": "message_limit_exceeded: the workspace posting cap",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack message_limit_exceeded", "slack workspace message limit",
             "members on this team are sending too many messages",
             "slack too many messages error", "slack app message volume audit"],
"deps": "Python 3.9+ with requests, or Node.js 18+; channels:history on the channels you name",
"lead": "Your app posts eleven messages a day. This morning every one of them failed with <code>message_limit_exceeded</code>, and the human-readable half of the error says that members on this team are sending too many messages. Nobody on your team is sending anything. Your retry logic, which is well written and honours <code>Retry-After</code>, does not help, because this is not your quota.</p><p>Somebody else's migration script is running, and it has taken the whole workspace with it.",
"short_answer": """<p><code>message_limit_exceeded</code> is a <strong>workspace-wide</strong> ceiling on message volume, sitting above and apart from the per-method rate limits your app has. When it is exhausted, every app in the workspace starts failing at once, which means the app that reports the error is frequently not the app that caused it. Conflating it with <code>ratelimited</code> sends the investigation to your own backoff code, which is the one place the answer definitely is not.</p>
<p>A read-only token cannot query the workspace's remaining budget, and there is no method that would. What it can do is count. The script below reads recent history from the channels you name, buckets every app-authored message into whole minutes, and ranks the sending apps by their peak minute. Volume is attributed by <code>app_id</code> and <code>bot_id</code>, so the output distinguishes your app from the three others in the workspace, and the loudest sender is usually one line in somebody's loop.</p>""",
"problem": """<p>The error looks like a rate limit and is filed as one. It is not: <code>ratelimited</code> is per method, per workspace, per app, and it is a statement about your traffic. <code>message_limit_exceeded</code> is a statement about the workspace's traffic, all of it, from every integration and every user, and your app can be at the bottom of that list and still be refused. Backoff will not clear it, retrying will not clear it, and a second app token will not clear it either, because the ceiling is not attached to the token.</p>
<p>What makes it genuinely difficult is that the evidence is not in your logs. Your logs contain your sends, which are not the problem. The volume that exhausted the ceiling is in the workspace, posted by something you may not own, and the only place a read-only token can see it is in the channels themselves. Nobody thinks to look there, because the instinct when an error mentions limits is to look at the code that hit the limit.</p>
<p>And the cause is nearly always mundane. A migration script that posts one message per row instead of one message per batch. A monitoring integration that lost its deduplication and is re-announcing the same alert every four seconds. An automation that got wired into a loop with another automation. In every case the shape in the history is unmistakable once somebody counts it: one sender, one channel, several hundred messages in a minute, in a workspace where the normal figure is single digits.</p>""",
"why": """<p><strong>The ceiling belongs to the workspace, so the fix might not belong to you.</strong> This is the rare Slack failure where the correct outcome of an investigation can be a message to another team. Establishing that early saves the day that would otherwise go into tuning your own sender, and the only way to establish it is to attribute the volume by app rather than counting your own.</p>
<p><strong><code>ratelimited</code> and <code>message_limit_exceeded</code> must never be caught by the same branch.</strong> One is answered by honouring <code>Retry-After</code> and slowing your own sends. The other is answered by finding a different app. A handler that treats them alike will retry politely into a wall for as long as the incident lasts.</p>
<p><strong>Whole minutes are the right unit, and seconds are not.</strong> The workspace ceiling is an aggregate over time, so the number that describes it is messages per minute summed across channels and senders. How closely spaced two consecutive messages from one app are in one channel is a different measurement answering a different question, and mixing the two produces a report where a chatty deploy bot outranks the migration script that caused the incident.</p>
<p><strong>Attribution is readable and free.</strong> Messages posted by apps carry <code>app_id</code>, <code>bot_id</code> and often a <code>bot_profile</code> with a name. That is enough to build a leaderboard of senders from history alone, without any admin scope, and to say plainly whether the app at the top of it is yours.</p>
<p><strong>The sample can be too small to divide into minutes, and then the script says nothing.</strong> One page of history from a quiet channel spans hours and produces buckets of one. A ranking built on that is noise dressed as evidence, so the run reports the window it actually got and declines to rank when there is not enough of it.</p>""",
"steps": [
 {"h": "Separate the two errors in the handler before anything else",
  "body": """<p><code>attribute_ceiling</code> is offline and takes ten seconds to wire in. Until <code>message_limit_exceeded</code> and <code>ratelimited</code> land in different branches with different log lines, every future incident of this kind starts by being misfiled.</p>"""},
 {"h": "Pick the channels where the volume would be",
  "body": """<p>Alert channels, deploy channels, whatever the migration is writing to. The script takes them as arguments because a read-only token cannot ask the workspace where its traffic is, and guessing across every channel would cost more requests than the answer is worth.</p>"""},
 {"h": "Read history and keep only what an app posted",
  "body": """<p>Human messages are not what exhausts this ceiling and counting them buries the signal. <code>sender_key</code> keeps messages carrying <code>app_id</code> or <code>bot_id</code> and drops the rest, returning a stable key so the same app is one row across every channel.</p>"""},
 {"h": "Bucket into whole minutes, deliberately",
  "body": """<p>Peak messages per minute, per app, summed across the channels you named. Not gaps between consecutive messages: that measures the cadence of one sender in one channel, which is a real problem and a different note, and it will rank a steady bot above a burst that took the workspace down.</p>"""},
 {"h": "Rank the senders and find yourself in the list",
  "body": """<p><code>auth.test</code> gives your own <code>bot_id</code>, and the ranking marks your rows. Being third with four messages a minute behind something posting six hundred is the finding, and it is the one that ends the argument about whose sender needs work.</p>"""},
 {"h": "Take the number to whoever owns the loop",
  "body": """<p>The printed repair is batching: one message with many blocks rather than N messages, a per-workspace send budget in each app so no single integration can exhaust a shared ceiling, and, where the volume is genuinely legitimate, a conversation with Slack, because this ceiling is not self-service.</p>"""},
],
"verify": """<p>Re-run after the offending sender is batched. The peak minute should fall by an order of magnitude and no sender should be labelled a likely cause.</p>
<pre><code class="language-bash">python3 slack_workspace_send_volume.py C0ALERTS99 C0DEPLOY11
# identity   B0OURAPP11 in acme
# window     412 message(s) across 2 channel(s), 143 from apps, spanning 96 minute(s)
# sender     background     B0OURAPP11 (this app)  peak 4/min, 31 total
# sender     background     A0PAGERDUTY           peak 6/min, 44 total
# sender     background     A0MIGRATION           peak 9/min, 68 total
# 0 sender(s) at a rate that would exhaust a workspace ceiling</code></pre>""",
"code_intro": "Four pure functions and one paginated read per channel. <code>sender_key</code> decides what counts as an app-authored message and gives the same app one identity across channels. <code>per_minute_by_app</code> does the arithmetic in whole minutes, which is the unit this ceiling is measured in. <code>rank_senders</code> turns that into a leaderboard that marks your own app. <code>attribute_ceiling</code> is the ten-second fix: it keeps this error away from your retry code.",
"py_file": "slack_workspace_send_volume.py",
"py": '''"""Rank the apps sending into a workspace, in messages per minute.

Read only. Reads recent history from the channels you name, keeps the messages
an app posted, buckets them into whole minutes and ranks the senders. Nothing
is sent: the workspace message ceiling is an aggregate over everybody's
traffic, and the point of this script is to find out whose.

Whole minutes on purpose. How closely spaced one app's consecutive messages are
in one channel is a different measurement answering a different question.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_workspace_send_volume")

API = "https://slack.com/api/"

# Errors that get caught by the same branch and should not be. The first
# belongs to the workspace, the second to your app, and they have opposite
# repairs: find another team, or slow your own sender down.
CEILINGS = {
    "message_limit_exceeded": (
        "workspace-ceiling",
        "a workspace-wide cap on message volume, not your app's quota. Every app "
        "in the workspace fails at once when it is exhausted, so the app that "
        "reports it is often not the app that caused it. Backoff does not clear "
        "it and a second token does not either."),
    "ratelimited": (
        "app-quota",
        "your app's own per-method window, answered by honouring Retry-After. It "
        "is a statement about your traffic, which the workspace ceiling is not."),
    "rate_limited": (
        "app-quota",
        "the same limit under its older spelling. Still your traffic, still "
        "answered by backoff."),
    "accesslimited": (
        "network-policy",
        "the calling IP is outside an allowed range. Nothing to do with volume."),
    "msg_too_long": (
        "message-shape",
        "one message exceeded the size limit. A single message problem rather "
        "than a rate of them."),
}

# Below this many app messages, or this many distinct minutes, the window is
# too thin to divide into a rate. A ranking built on three messages spread over
# four hours is noise wearing the clothes of evidence.
MIN_APP_MESSAGES = 20
MIN_MINUTES = 3


def sender_key(message):
    """The app that posted this message, or None if a person did. Pure.

    app_id is preferred because it is stable for the app across workspaces and
    across reinstalls; bot_id is the fallback for messages that carry only
    that. Human messages are dropped: they are not what exhausts this ceiling
    and counting them buries the sender that is.
    """
    m = message or {}
    app_id = str(m.get("app_id") or "").strip()
    if app_id:
        return app_id
    bot_id = str(m.get("bot_id") or "").strip()
    if bot_id:
        return bot_id
    if m.get("subtype") == "bot_message":
        return "bot:unattributed"
    return None


def per_minute_by_app(messages):
    """Bucket app-authored messages into whole minutes, per sender. Pure.

    Returns {key: {"total", "minutes", "peak_per_minute", "mean_per_minute"}}.
    Whole minutes because the workspace ceiling is an aggregate over time; the
    gap between two consecutive sends is a cadence question and belongs to the
    per-channel posting rate rather than here.
    """
    buckets = {}
    for message in messages or []:
        key = sender_key(message)
        if key is None:
            continue
        try:
            minute = int(float(message.get("ts"))) // 60
        except (TypeError, ValueError):
            continue
        buckets.setdefault(key, {})
        buckets[key][minute] = buckets[key].get(minute, 0) + 1

    out = {}
    for key, minutes in buckets.items():
        counts = list(minutes.values())
        out[key] = {
            "total": sum(counts),
            "minutes": len(counts),
            "peak_per_minute": max(counts),
            "mean_per_minute": round(sum(counts) / float(len(counts)), 1),
        }
    return out


def rank_senders(volume, own_ids=(), threshold=60):
    """Order senders by their peak minute and label them. Pure.

    Returns [(key, verdict, detail), ...], loudest first. own_ids are the
    identities auth.test gave for this app, so the reader can see at a glance
    whether the app at the top of the list is theirs.
    """
    mine = {str(i) for i in own_ids if i}
    rows = []
    for key, stats in volume.items():
        peak = stats["peak_per_minute"]
        if peak >= threshold:
            verdict = "likely-cause"
        elif peak >= max(threshold // 4, 1):
            verdict = "contributor"
        else:
            verdict = "background"
        label = "%s (this app)" % key if key in mine else key
        rows.append((peak, label, verdict,
                     "peak %d/min, %d total over %d minute(s), mean %s/min"
                     % (peak, stats["total"], stats["minutes"],
                        stats["mean_per_minute"])))
    rows.sort(key=lambda row: (-row[0], row[1]))
    return [(label, verdict, detail) for _, label, verdict, detail in rows]


def attribute_ceiling(error):
    """Keep the workspace ceiling away from your retry code. Pure and offline.

    The ten second fix in this note: two errors that look alike, land in the
    same handler, and want opposite repairs.
    """
    text = str(error or "").strip()
    known = CEILINGS.get(text)
    if known is not None:
        return known
    if not text:
        return ("none-recorded",
                "no error was supplied, so the ranking below stands on its own as "
                "a volume measurement.")
    return ("unattributed",
            "%s is not a volume limit. Whatever refused the message, the workspace "
            "ceiling is not it." % text)


def history(session, channel, limit, pages):
    """Recent messages from one channel. GET only, bounded."""
    out, cursor = [], ""
    for _ in range(max(int(pages), 1)):
        params = {"channel": channel, "limit": str(limit)}
        if cursor:
            params["cursor"] = cursor
        body = session.get(API + "conversations.history", params=params,
                           timeout=30).json()
        if body.get("ok") is not True:
            log.warning("%-10s %-14s %s", channel, "unreadable",
                        "conversations.history answered ok: false, error=%s"
                        % body.get("error"))
            return out
        out.extend(body.get("messages") or [])
        cursor = (body.get("response_metadata") or {}).get("next_cursor") or ""
        if not cursor:
            break
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("channels", nargs="+",
                    help="channel IDs where the volume would be")
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN",
                    help="environment variable holding the bot token")
    ap.add_argument("--limit", type=int, default=200,
                    help="page size for conversations.history")
    ap.add_argument("--pages", type=int, default=2,
                    help="pages per channel, so the audit stays cheap")
    ap.add_argument("--threshold", type=int, default=60,
                    help="peak messages per minute at which a sender is a likely cause")
    ap.add_argument("--observed-error", default="",
                    help="an error your app recorded, attributed offline")
    args = ap.parse_args()

    token = os.environ.get(args.token_env)
    if not token:
        log.error("set %s (channels:history on the named channels is enough)",
                  args.token_env)
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + token})

    who = s.get(API + "auth.test", timeout=30).json()
    if who.get("ok") is not True:
        log.error("auth.test answered 200 with ok: false, error=%s", who.get("error"))
        return 2
    own = [who.get("bot_id"), who.get("user_id")]
    log.info("identity   %s in %s", who.get("bot_id") or who.get("user_id"),
             who.get("team"))

    messages = []
    for channel in args.channels:
        messages.extend(history(s, channel, args.limit, args.pages))

    volume = per_minute_by_app(messages)
    app_messages = sum(v["total"] for v in volume.values())
    minutes = len({int(float(m["ts"])) // 60 for m in messages if m.get("ts")})
    log.info("window     %d message(s) across %d channel(s), %d from apps, "
             "spanning %d minute(s)", len(messages), len(args.channels),
             app_messages, minutes)

    if args.observed_error:
        source, why = attribute_ceiling(args.observed_error)
        (log.warning if source == "workspace-ceiling" else log.info)(
            "recorded   %-14s %s", source, why)

    if app_messages < MIN_APP_MESSAGES or minutes < MIN_MINUTES:
        log.info("ranking    %-14s %d app message(s) over %d minute(s) is not "
                 "enough to divide into a rate. Widen --pages or name a busier "
                 "channel.", "sample-thin", app_messages, minutes)
        return 0

    loud = 0
    for key, verdict, detail in rank_senders(volume, own, args.threshold):
        (log.warning if verdict != "background" else log.info)(
            "sender     %-14s %-24s %s", verdict, key, detail)
        if verdict == "likely-cause":
            loud += 1

    if loud:
        log.warning("  repair: batch. One message with many blocks instead of N "
                    "messages is the single largest reduction available")
        log.warning("  repair: give every app a per-workspace send budget so no "
                    "one integration can exhaust a ceiling all of them share")
        log.warning("  repair: if the volume is legitimate, contact Slack; the "
                    "workspace ceiling is not self-service")
    log.info("%d sender(s) at a rate that would exhaust a workspace ceiling", loud)
    return 1 if loud else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-workspace-send-volume.mjs",
"js": '''/**
 * Rank the apps sending into a workspace, in messages per minute.
 *
 * Read only. Reads recent history from the channels you name, keeps the
 * messages an app posted, buckets them into whole minutes and ranks the
 * senders. Nothing is sent: the workspace message ceiling is an aggregate over
 * everybody's traffic, and the point of this script is to find out whose.
 *
 * Whole minutes on purpose. How closely spaced one app's consecutive messages
 * are in one channel is a different measurement answering a different question.
 */

const API = 'https://slack.com/api/';

// Errors that get caught by the same branch and should not be. The first
// belongs to the workspace, the second to your app, and they have opposite
// repairs.
const CEILINGS = new Map([
  ['message_limit_exceeded', ['workspace-ceiling',
    "a workspace-wide cap on message volume, not your app's quota. Every app in " +
    'the workspace fails at once when it is exhausted, so the app that reports ' +
    'it is often not the app that caused it. Backoff does not clear it and a ' +
    'second token does not either.']],
  ['ratelimited', ['app-quota',
    'your app\\'s own per-method window, answered by honouring Retry-After. It is ' +
    'a statement about your traffic, which the workspace ceiling is not.']],
  ['rate_limited', ['app-quota',
    'the same limit under its older spelling. Still your traffic, still answered ' +
    'by backoff.']],
  ['accesslimited', ['network-policy',
    'the calling IP is outside an allowed range. Nothing to do with volume.']],
  ['msg_too_long', ['message-shape',
    'one message exceeded the size limit. A single message problem rather than a ' +
    'rate of them.']],
]);

// Below this many app messages, or this many distinct minutes, the window is
// too thin to divide into a rate.
const MIN_APP_MESSAGES = 20;
const MIN_MINUTES = 3;

/**
 * The app that posted this message, or null if a person did. Pure.
 * app_id first because it is stable across reinstalls; bot_id is the fallback.
 */
export function senderKey(message) {
  const m = message ?? {};
  const appId = String(m.app_id ?? '').trim();
  if (appId) return appId;
  const botId = String(m.bot_id ?? '').trim();
  if (botId) return botId;
  if (m.subtype === 'bot_message') return 'bot:unattributed';
  return null;
}

/**
 * Bucket app-authored messages into whole minutes, per sender. Pure.
 * Whole minutes because the workspace ceiling is an aggregate over time; the
 * gap between two consecutive sends is a cadence question and belongs
 * elsewhere.
 */
export function perMinuteByApp(messages) {
  const buckets = new Map();
  for (const message of messages ?? []) {
    const key = senderKey(message);
    if (key === null) continue;
    const seconds = Number(message.ts);
    if (!Number.isFinite(seconds)) continue;
    const minute = Math.floor(seconds / 60);
    if (!buckets.has(key)) buckets.set(key, new Map());
    const per = buckets.get(key);
    per.set(minute, (per.get(minute) ?? 0) + 1);
  }

  const out = {};
  for (const [key, minutes] of buckets) {
    const counts = [...minutes.values()];
    const total = counts.reduce((a, b) => a + b, 0);
    out[key] = {
      total,
      minutes: counts.length,
      peak_per_minute: Math.max(...counts),
      mean_per_minute: Math.round((total * 10) / counts.length) / 10,
    };
  }
  return out;
}

/**
 * Order senders by their peak minute and label them. Pure.
 * ownIds are the identities auth.test gave for this app, so the reader can see
 * at a glance whether the app at the top of the list is theirs.
 */
export function rankSenders(volume, ownIds = [], threshold = 60) {
  const mine = new Set([...ownIds].filter(Boolean).map(String));
  const rows = [];
  for (const [key, stats] of Object.entries(volume)) {
    const peak = stats.peak_per_minute;
    let verdict = 'background';
    if (peak >= threshold) verdict = 'likely-cause';
    else if (peak >= Math.max(Math.floor(threshold / 4), 1)) verdict = 'contributor';
    const label = mine.has(key) ? `${key} (this app)` : key;
    rows.push([peak, label, verdict,
      `peak ${peak}/min, ${stats.total} total over ${stats.minutes} minute(s), ` +
      `mean ${stats.mean_per_minute}/min`]);
  }
  rows.sort((a, b) => (b[0] - a[0]) || a[1].localeCompare(b[1]));
  return rows.map(([, label, verdict, detail]) => [label, verdict, detail]);
}

/**
 * Keep the workspace ceiling away from your retry code. Pure and offline.
 * Two errors that look alike, land in the same handler, and want opposite
 * repairs.
 */
export function attributeCeiling(error) {
  const text = String(error ?? '').trim();
  const known = CEILINGS.get(text);
  if (known !== undefined) return known;
  if (!text) {
    return ['none-recorded',
      'no error was supplied, so the ranking below stands on its own as a volume ' +
      'measurement.'];
  }
  return ['unattributed',
    `${text} is not a volume limit. Whatever refused the message, the workspace ` +
    'ceiling is not it.'];
}

async function history(token, channel, limit, pages) {
  const out = [];
  let cursor = '';
  for (let i = 0; i < Math.max(pages, 1); i += 1) {
    const params = new URLSearchParams({ channel, limit: String(limit) });
    if (cursor) params.set('cursor', cursor);
    const res = await fetch(`${API}conversations.history?${params}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const body = await res.json();
    if (body.ok !== true) {
      console.warn(`${channel.padEnd(10)} ${'unreadable'.padEnd(14)} ` +
        `conversations.history answered ok: false, error=${body.error}`);
      return out;
    }
    out.push(...(body.messages ?? []));
    cursor = body.response_metadata?.next_cursor ?? '';
    if (!cursor) break;
  }
  return out;
}

function arg(args, name, fallback = null) {
  const i = args.indexOf(name);
  return i === -1 ? fallback : args[i + 1];
}

function positionals(args) {
  const out = [];
  for (let i = 0; i < args.length; i += 1) {
    if (args[i].startsWith('--')) { i += 1; continue; }
    out.push(args[i]);
  }
  return out;
}

async function main() {
  const args = process.argv.slice(2);
  const channels = positionals(args);
  if (channels.length === 0) {
    console.error('usage: <channel id>... [--pages 2] [--threshold 60] ' +
      '[--observed-error message_limit_exceeded]');
    process.exitCode = 2;
    return;
  }
  const tokenEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
  const token = process.env[tokenEnv];
  if (!token) {
    console.error(`set ${tokenEnv} (channels:history on the named channels is enough)`);
    process.exitCode = 2;
    return;
  }
  const limit = Number(arg(args, '--limit', 200));
  const pages = Number(arg(args, '--pages', 2));
  const threshold = Number(arg(args, '--threshold', 60));

  const whoRes = await fetch(`${API}auth.test`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const who = await whoRes.json();
  if (who.ok !== true) {
    console.error(`auth.test answered 200 with ok: false, error=${who.error}`);
    process.exitCode = 2;
    return;
  }
  const own = [who.bot_id, who.user_id];
  console.log(`identity   ${who.bot_id ?? who.user_id} in ${who.team}`);

  const messages = [];
  for (const channel of channels) {
    messages.push(...await history(token, channel, limit, pages));
  }

  const volume = perMinuteByApp(messages);
  const appMessages = Object.values(volume).reduce((a, v) => a + v.total, 0);
  const minutes = new Set(messages.filter((m) => m.ts)
    .map((m) => Math.floor(Number(m.ts) / 60))).size;
  console.log(`window     ${messages.length} message(s) across ${channels.length} ` +
    `channel(s), ${appMessages} from apps, spanning ${minutes} minute(s)`);

  const observed = arg(args, '--observed-error', '');
  if (observed) {
    const [source, why] = attributeCeiling(observed);
    (source === 'workspace-ceiling' ? console.warn : console.log)(
      `recorded   ${source.padEnd(14)} ${why}`);
  }

  if (appMessages < MIN_APP_MESSAGES || minutes < MIN_MINUTES) {
    console.log(`ranking    ${'sample-thin'.padEnd(14)} ${appMessages} app ` +
      `message(s) over ${minutes} minute(s) is not enough to divide into a rate. ` +
      'Widen --pages or name a busier channel.');
    return;
  }

  let loud = 0;
  for (const [key, verdict, detail] of rankSenders(volume, own, threshold)) {
    (verdict === 'background' ? console.log : console.warn)(
      `sender     ${verdict.padEnd(14)} ${key.padEnd(24)} ${detail}`);
    if (verdict === 'likely-cause') loud += 1;
  }

  if (loud) {
    console.warn('  repair: batch. One message with many blocks instead of N ' +
      'messages is the single largest reduction available');
    console.warn('  repair: give every app a per-workspace send budget so no one ' +
      'integration can exhaust a ceiling all of them share');
    console.warn('  repair: if the volume is legitimate, contact Slack; the ' +
      'workspace ceiling is not self-service');
  }
  console.log(`${loud} sender(s) at a rate that would exhaust a workspace ceiling`);
  process.exitCode = loud ? 1 : 0;
}

// Only run when invoked directly, so importing this module in the tests does
// not execute main() and fail the file on a missing token.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The fixture is one minute of an incident: a migration app posting sixty times inside a single minute while the app running the audit posts twice, in the same channel, over the same window. The tests assert that the migration is ranked first and labelled a likely cause, that this app is found in the list and labelled as its own, and that human messages are excluded entirely. The last two pin the discipline: <code>message_limit_exceeded</code> and <code>ratelimited</code> never come back with the same source.",
"test_py_file": "test_slack_workspace_send_volume.py",
"test_py": '''from slack_workspace_send_volume import (attribute_ceiling, per_minute_by_app,
                                          rank_senders, sender_key)

MINUTE = 1756400000

# One minute of an incident, plus a quiet minute either side. The migration app
# posts sixty times inside a single minute; the app running the audit posts
# twice; a person says something, which is not what exhausts this ceiling.
MESSAGES = (
    [{"ts": "%d.0000%02d" % (MINUTE, i), "app_id": "A0MIGRATION",
      "bot_id": "B0MIGRATION"} for i in range(60)]
    + [{"ts": "%d.000000" % (MINUTE - 60), "app_id": "A0MIGRATION"}]
    + [{"ts": "%d.000000" % (MINUTE + 60), "app_id": "A0MIGRATION"}]
    + [{"ts": "%d.000100" % MINUTE, "bot_id": "B0OURAPP11"},
       {"ts": "%d.000200" % (MINUTE + 60), "bot_id": "B0OURAPP11"}]
    + [{"ts": "%d.000300" % MINUTE, "user": "U0HUMAN111", "text": "what is going on"}]
)


def test_a_human_message_has_no_sender_key():
    assert sender_key({"ts": "1.0", "user": "U0HUMAN111"}) is None
    assert sender_key({}) is None
    assert sender_key(None) is None


def test_app_id_is_preferred_over_bot_id_so_one_app_is_one_row():
    assert sender_key({"app_id": "A0MIGRATION", "bot_id": "B0MIGRATION"}) == "A0MIGRATION"
    assert sender_key({"bot_id": "B0OURAPP11"}) == "B0OURAPP11"
    assert sender_key({"subtype": "bot_message"}) == "bot:unattributed"


def test_the_peak_minute_is_the_number_this_ceiling_is_measured_in():
    volume = per_minute_by_app(MESSAGES)
    assert volume["A0MIGRATION"]["peak_per_minute"] == 60
    assert volume["A0MIGRATION"]["total"] == 62
    assert volume["A0MIGRATION"]["minutes"] == 3


def test_a_steady_sender_never_reaches_a_peak():
    volume = per_minute_by_app(MESSAGES)
    assert volume["B0OURAPP11"]["peak_per_minute"] == 1
    assert volume["B0OURAPP11"]["total"] == 2


def test_humans_are_not_counted_at_all():
    assert set(per_minute_by_app(MESSAGES)) == {"A0MIGRATION", "B0OURAPP11"}


def test_a_message_without_a_usable_timestamp_is_skipped_not_guessed():
    volume = per_minute_by_app([{"app_id": "A0X"}, {"ts": "later", "app_id": "A0X"}])
    assert volume == {}


def test_the_loudest_sender_is_first_and_named_as_the_likely_cause():
    rows = rank_senders(per_minute_by_app(MESSAGES), ["B0OURAPP11"])
    assert rows[0][0] == "A0MIGRATION"
    assert rows[0][1] == "likely-cause"
    assert "peak 60/min" in rows[0][2]


def test_your_own_app_is_marked_so_the_answer_is_unmissable():
    rows = rank_senders(per_minute_by_app(MESSAGES), ["B0OURAPP11"])
    assert rows[1][0] == "B0OURAPP11 (this app)"
    assert rows[1][1] == "background"


def test_the_threshold_is_a_dial_rather_than_a_law():
    volume = per_minute_by_app(MESSAGES)
    assert rank_senders(volume, [], threshold=1000)[0][1] == "background"
    assert rank_senders(volume, [], threshold=200)[0][1] == "contributor"
    assert rank_senders(volume, [], threshold=60)[0][1] == "likely-cause"


def test_the_workspace_ceiling_is_never_confused_with_your_own_quota():
    source, why = attribute_ceiling("message_limit_exceeded")
    assert source == "workspace-ceiling"
    assert "not your app" in why
    assert attribute_ceiling("ratelimited")[0] == "app-quota"
    assert attribute_ceiling("rate_limited")[0] == "app-quota"


def test_an_unrelated_error_is_not_read_as_volume():
    assert attribute_ceiling("msg_too_long")[0] == "message-shape"
    assert attribute_ceiling("channel_not_found")[0] == "unattributed"
    assert attribute_ceiling("")[0] == "none-recorded"
''',
"test_js_file": "slack-workspace-send-volume.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { attributeCeiling, perMinuteByApp, rankSenders, senderKey }
  from './slack-workspace-send-volume.mjs';

const MINUTE = 1756400000;

// One minute of an incident, plus a quiet minute either side.
const MESSAGES = [
  ...Array.from({ length: 60 }, (_, i) => ({
    ts: `${MINUTE}.0000${String(i).padStart(2, '0')}`,
    app_id: 'A0MIGRATION', bot_id: 'B0MIGRATION',
  })),
  { ts: `${MINUTE - 60}.000000`, app_id: 'A0MIGRATION' },
  { ts: `${MINUTE + 60}.000000`, app_id: 'A0MIGRATION' },
  { ts: `${MINUTE}.000100`, bot_id: 'B0OURAPP11' },
  { ts: `${MINUTE + 60}.000200`, bot_id: 'B0OURAPP11' },
  { ts: `${MINUTE}.000300`, user: 'U0HUMAN111', text: 'what is going on' },
];

test('a human message has no sender key', () => {
  assert.equal(senderKey({ ts: '1.0', user: 'U0HUMAN111' }), null);
  assert.equal(senderKey({}), null);
  assert.equal(senderKey(null), null);
});

test('app_id is preferred over bot_id so one app is one row', () => {
  assert.equal(senderKey({ app_id: 'A0MIGRATION', bot_id: 'B0MIGRATION' }),
    'A0MIGRATION');
  assert.equal(senderKey({ bot_id: 'B0OURAPP11' }), 'B0OURAPP11');
  assert.equal(senderKey({ subtype: 'bot_message' }), 'bot:unattributed');
});

test('the peak minute is the number this ceiling is measured in', () => {
  const volume = perMinuteByApp(MESSAGES);
  assert.equal(volume.A0MIGRATION.peak_per_minute, 60);
  assert.equal(volume.A0MIGRATION.total, 62);
  assert.equal(volume.A0MIGRATION.minutes, 3);
});

test('a steady sender never reaches a peak', () => {
  const volume = perMinuteByApp(MESSAGES);
  assert.equal(volume.B0OURAPP11.peak_per_minute, 1);
  assert.equal(volume.B0OURAPP11.total, 2);
});

test('humans are not counted at all', () => {
  assert.deepEqual(Object.keys(perMinuteByApp(MESSAGES)).sort(),
    ['A0MIGRATION', 'B0OURAPP11']);
});

test('a message without a usable timestamp is skipped not guessed', () => {
  assert.deepEqual(perMinuteByApp([{ app_id: 'A0X' }, { ts: 'later', app_id: 'A0X' }]),
    {});
});

test('the loudest sender is first and named as the likely cause', () => {
  const rows = rankSenders(perMinuteByApp(MESSAGES), ['B0OURAPP11']);
  assert.equal(rows[0][0], 'A0MIGRATION');
  assert.equal(rows[0][1], 'likely-cause');
  assert.match(rows[0][2], /peak 60\\/min/);
});

test('your own app is marked so the answer is unmissable', () => {
  const rows = rankSenders(perMinuteByApp(MESSAGES), ['B0OURAPP11']);
  assert.equal(rows[1][0], 'B0OURAPP11 (this app)');
  assert.equal(rows[1][1], 'background');
});

test('the threshold is a dial rather than a law', () => {
  const volume = perMinuteByApp(MESSAGES);
  assert.equal(rankSenders(volume, [], 1000)[0][1], 'background');
  assert.equal(rankSenders(volume, [], 200)[0][1], 'contributor');
  assert.equal(rankSenders(volume, [], 60)[0][1], 'likely-cause');
});

test('the workspace ceiling is never confused with your own quota', () => {
  const [source, why] = attributeCeiling('message_limit_exceeded');
  assert.equal(source, 'workspace-ceiling');
  assert.match(why, /not your app/);
  assert.equal(attributeCeiling('ratelimited')[0], 'app-quota');
  assert.equal(attributeCeiling('rate_limited')[0], 'app-quota');
});

test('an unrelated error is not read as volume', () => {
  assert.equal(attributeCeiling('msg_too_long')[0], 'message-shape');
  assert.equal(attributeCeiling('channel_not_found')[0], 'unattributed');
  assert.equal(attributeCeiling('')[0], 'none-recorded');
});
''',
"faq": [
 ("Is message_limit_exceeded the same as ratelimited?",
  "No, and treating them as the same is the mistake this note exists to prevent. ratelimited is per method, per workspace, per app, and it describes your traffic; message_limit_exceeded is a workspace-wide ceiling on message volume that every app in the workspace shares. One is answered by honouring Retry-After, the other by finding whichever integration is flooding the place."),
 ("Can a read-only token see how much of the ceiling is left?",
  "No. There is no method that reports remaining budget for anything in Slack, and rate limit posture is always inferred from live calls rather than queried. What a read token can do is count what has already been posted, which is why this script measures history rather than asking for a quota that no endpoint returns."),
 ("Why whole minutes rather than the gap between messages?",
  "Because they answer different questions. The workspace ceiling is an aggregate over time, so peak messages per minute summed across senders is the figure that describes it. Sub-second spacing between one app's consecutive posts in one channel describes that app's cadence against the per-channel send rate, and ranking by it would put a chatty deploy bot above the migration that caused the outage."),
 ("The top sender is not our app. What do we actually do?",
  "Send the number to whoever owns it. That is the useful outcome: a named app, a channel, and a peak minute is a message somebody can act on, where a screenshot of your own failures is not. In the meantime the only thing your app can do for itself is post less, so batching is worth doing regardless of who caused this one."),
 ("Our volume is legitimate. Is there a way to raise the ceiling?",
  "Not by yourself. The workspace ceiling is not a setting in the admin console and it is not a plan upgrade, so the route is a conversation with Slack about the workload. Before starting it, batch what can be batched: replacing N messages with one message carrying N blocks usually removes most of the volume and makes the remaining case much easier to argue."),
],
"related": [
 ("/slack/bot-message-echo-loop/", "two apps generating volume out of each other"),
 ("/slack/non-marketplace-history-clamp/", "the other limit that is not your fault"),
 ("/slack/http-200-ok-false/", "why the refusal arrived as a success"),
],
"citations": [CITE_POSTMESSAGE, CITE_RATE_LIMITS, CITE_CONV_HISTORY, CITE_AUTH_TEST],
})
