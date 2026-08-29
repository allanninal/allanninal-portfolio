#!/usr/bin/env python3
"""/twilio/ field notes, batch V — the writing.

Four states of the account itself rather than of anything it sends. The account
is suspended or closed; the account never left trial; the trial account has
spent all three of the verified numbers it will ever get; and the credential you
are reading all of that with hits a permission wall that may or may not be a
fault. They share one resource, `GET /2010-04-01/Accounts/{AccountSid}.json`,
and between them they cover the two answers that resource gives you: `status`
and `type`.

Read-only throughout: an API Key with read access, never the account auth token,
and the repair is printed for a human to run. Nothing here could be repaired by
an API call anyway — lifting a suspension and upgrading off trial both happen in
the Console, behind a payment method — which is a good reminder that a script
holding a credential to a live messaging account should only ever be able to
look.
"""

CITE_ACCOUNT = ("Account resource — Twilio Docs",
                "https://www.twilio.com/docs/iam/api/account")
CITE_SUBACCOUNTS = ("Subaccounts — Twilio Docs",
                    "https://www.twilio.com/docs/iam/api/subaccounts")
CITE_KEYS = ("API keys — Twilio Docs", "https://www.twilio.com/docs/iam/api-keys")
CITE_KEY_RESOURCE = ("Key resource (2010-04-01) — Twilio Docs",
                     "https://www.twilio.com/docs/iam/api-keys/key-resource-v2010")
CITE_MESSAGE = ("Message resource — Twilio Docs",
                "https://www.twilio.com/docs/messaging/api/message-resource")
CITE_CALLERIDS = ("OutgoingCallerId resource — Twilio Docs",
                  "https://www.twilio.com/docs/voice/api/outgoing-caller-ids")
CITE_20003 = ("Error 20003: permission denied — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/20003")
CITE_20005 = ("Error 20005: account not active — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/20005")
CITE_30002 = ("Error 30002: account suspended — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/30002")
CITE_21608 = ("Error 21608: unverified number on a trial account — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/21608")
CITE_30044 = ("Error 30044: trial account message length exceeded — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/30044")

GUIDES = [

{
"slug": "account-suspended-or-closed",
"title": "The account itself is suspended, so every send fails 20005",
"description": "Status on the top-level account, not on a subaccount. One GET answers it, and the 30002s on the queued backlog say when it started.",
"h1": "the account itself is suspended, so every send fails with 20005",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio 20005", "twilio account not active", "twilio account suspended",
             "twilio error 30002", "twilio account status closed"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Everything stops at once. Messages, calls, number purchases, Verify starts &mdash; all of them come back <code>403</code> with <code>20005: Account not active</code>, and the queued backlog dies behind them with <code>30002</code>. The Console still loads, your dashboard still draws, and the API still answers questions about the account. It just will not do anything for it any more.",
"short_answer": """<p>Read <code>GET /2010-04-01/Accounts/{AccountSid}.json</code> and look at one field: <code>status</code>. Anything other than <code>active</code> is the whole answer. <code>suspended</code> is recoverable, <code>closed</code> is not.</p>
<p>Then page <code>GET /2010-04-01/Accounts/{AccountSid}/Messages.json?DateSent&gt;=YYYY-MM-DD</code> and count rows whose <code>error_code</code> is <code>30002</code>. That number tells you what the suspension already cost, and it is the only signal left once the status has flipped back to <code>active</code>.</p>""",
"problem": """<p>A suspension is not a degraded mode. It is a hard stop on everything the account can do, applied between one request and the next, and the first thing most teams see is not an alert but a customer saying they never got their code. The error is <code>20005</code> on anything you try to create and <code>30002</code> on anything that was already queued, and neither is a code your application is likely to have a branch for, because neither has ever fired before.</p>
<p>What makes it awkward to diagnose from inside the application is that reads keep working. The credential is valid, the account resource comes back, the message list comes back, the phone numbers are all still there. Every health check that asks "can I reach Twilio" answers yes. The one field that says otherwise is not on any of those responses; it is on the account itself, and nothing fetches the account.</p>
<p>The version of this that hurts most is the one you find late. A balance suspension can clear itself minutes after somebody tops up, so by the time anyone investigates, <code>status</code> reads <code>active</code> again and the only evidence left is a block of <code>30002</code> rows in the message list with a start and an end.</p>""",
"why": """<p><strong>Balance is the usual cause, and it is a threshold, not a warning.</strong> The account spends down, crosses zero, and is suspended. There is no soft landing and no grace period on the way through. Whether you saw it coming depends entirely on whether somebody set a usage trigger, which is <a href="/twilio/no-usage-trigger-configured/">its own note</a>, and on how close to the floor the balance was allowed to sit, which is <a href="/twilio/balance-below-safety-floor/">another</a>.</p>
<p><strong>A policy or ToS review is the cause you cannot fix with a card.</strong> Content review, a spike that looks like pumping, an unresolved compliance item: these disable the project rather than the payment, and the repair is a ticket rather than a top-up. The API reports the same <code>suspended</code> either way, which is why the script tells you to check the balance before you assume you know which one you have.</p>
<p><strong><code>closed</code> is terminal and reads almost the same.</strong> One word apart in the same field, and completely different consequences: a closed account cannot be reopened, so the numbers on it are gone and the work is standing up a new account and porting what can be ported. A report that lumps closed in with suspended is telling you to go and add funds to something that will never take them.</p>
<p><strong>Suspension cascades downward, and this note only looks upward.</strong> A suspended parent takes its subaccounts with it. If the SID you are checking is a child, its own <code>status</code> can read <code>active</code> while the parent's does not, so the script says plainly which of the two you are pointed at. Finding the reverse case &mdash; one suspended tenant under a healthy parent &mdash; is <a href="/twilio/subaccount-suspended-silently/">a different read</a> with different credentials.</p>""",
"steps": [
 {"h": "Fetch the account and read status",
  "body": """<p><code>GET /2010-04-01/Accounts/{AccountSid}.json</code>. The response carries <code>sid</code>, <code>owner_account_sid</code>, <code>friendly_name</code>, <code>status</code> and <code>type</code>. <code>status</code> is the finding. Compare it case-insensitively and treat any value that is not <code>active</code> as a failure, rather than matching only the two you have heard of.</p>"""},
 {"h": "Work out whether you are looking at a parent or a child",
  "body": """<p><code>owner_account_sid</code> on a top-level account is the account's own <code>sid</code>. On a subaccount it is the parent's. This costs nothing to check and it changes the repair completely: a subaccount's suspension may be its own or may be inherited, and reactivating it is done with the parent's credentials.</p>"""},
 {"h": "Count the 30002s to date the outage",
  "body": """<p>Page <code>GET /2010-04-01/Accounts/{AccountSid}/Messages.json?DateSent&gt;=YYYY-MM-DD&amp;PageSize=1000</code>, following <code>next_page_uri</code>. There is no <code>ErrorCode</code> filter on this resource, so read <code>error_code</code> on each row yourself and keep the <code>30002</code>s. The first and last <code>date_sent</code> among them bound the outage.</p>"""},
 {"h": "Separate a balance suspension from a policy one before you act",
  "body": """<p>If the balance is at or below zero, the repair is Console &rarr; Billing &rarr; add funds, and reactivation follows within roughly five to ten minutes rather than instantly. If the balance is healthy and the account is still suspended, adding more money changes nothing and you need a ticket at help.twilio.com. Guessing wrong costs you the time it takes to find out.</p>"""},
 {"h": "Re-run it on a schedule, not just during the incident",
  "body": """<p>This is one GET. Running it every few minutes from somewhere that is not the affected account turns a customer report into an alert, and running it after the fact is how you find the block of <code>30002</code>s that a five-minute suspension left behind three weeks ago.</p>"""},
],
"verify": """<p>Re-run the script. <code>status</code> should read <code>active</code> and the 30002 count over your window should be zero.</p>
<pre><code class="language-bash">python3 twilio_account_status_audit.py --days 7
# active      AC0123  status is active, and no message in the last 7 days failed with 30002.</code></pre>""",
"code_intro": "One GET for the account, and one paginated GET over the message window to date the damage. The classifier is pure and takes the account dict plus the 30002 count, because the interesting decisions &mdash; closed outranks suspended, and an active account with 30002s in the window is still a finding &mdash; are decisions about two values, not about HTTP.",
"py_file": "twilio_account_status_audit.py",
"py": '''"""Report whether the Twilio account behind this credential is still active.

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. Nothing here can lift a suspension anyway;
the repair is printed for a human to run in the Console.
"""
import argparse
import datetime as dt
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_account_status_audit")

HOST = "https://api.twilio.com"
BASE = HOST + "/2010-04-01"

# The error stamped on messages that were queued when the account stopped being
# active. Requests made after the suspension are refused outright with 20005 and
# never become a Message row at all, so this is the only one the list can show.
SUSPENDED_ERROR = 30002


def scope(account):
    """Whether this SID is the top-level account or one of its subaccounts.

    owner_account_sid on a parent account is that account's own sid; on a
    subaccount it is the parent's. The distinction changes the repair, because a
    subaccount is reactivated with the parent's credentials and may have been
    suspended by the parent rather than on its own account.
    """
    sid = str(account.get("sid") or "").strip()
    owner = str(account.get("owner_account_sid") or "").strip()
    if sid and owner and sid != owner:
        return "subaccount"
    return "account"


def verdict(account, failed=0, days=7):
    """Classify one Account resource. Pure, so every state can be exercised
    without a network.

    Returns (state, detail). Order matters: closed is terminal and has to
    outrank suspended, and an account that reads active today is still a finding
    if the window behind it is full of 30002s.
    """
    status = str(account.get("status") or "").strip().lower()

    if not status:
        return ("unknown",
                "the Account resource carried no status field. Do not read that "
                "as healthy: fetch it again before deciding anything.")

    if status == "closed":
        return ("closed",
                "status is closed. This is terminal. The account cannot be "
                "reopened, its numbers are not coming back, and the work is a "
                "new account rather than a payment.")

    if status == "suspended":
        return ("suspended",
                "status is suspended: every send, call and number purchase is "
                "refused with 20005, and anything already queued fails with "
                "%d. Check the balance before assuming it is a billing "
                "suspension." % SUSPENDED_ERROR)

    if status != "active":
        return ("not-active",
                "status is %r, which is not active. Everything the account does "
                "is refused with 20005 until it is." % status)

    if failed:
        return ("recently-suspended",
                "status is active now, but %d message(s) in the last %d days "
                "failed with %d. The account was not active while those were "
                "queued, and nothing recorded when that started or ended except "
                "these rows." % (failed, days, SUSPENDED_ERROR))

    return ("active",
            "status is active, and no message in the last %d days failed with "
            "%d." % (days, SUSPENDED_ERROR))


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access")
    if r.status_code == 403:
        # A 403 on a read is worth reporting rather than swallowing: 20005 here
        # means the account is not active and is refusing on its own behalf,
        # which is the answer this script was run to get.
        raise SystemExit("403 from Twilio at %s. If the body carries 20005 the "
                         "account is not active, which is this finding." % url)
    r.raise_for_status()
    return r.json()


def fetch_account(session, account):
    return get(session, "%s/Accounts/%s.json" % (BASE, account))


def list_messages(session, account, since, limit):
    """Page Messages.json. The resource has no ErrorCode filter, so the date
    window and the page cap are the only levers on how much this reads."""
    url = "%s/Accounts/%s/Messages.json" % (BASE, account)
    params = {"PageSize": 1000, "DateSent>=": since}
    out = []
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get("messages", []))
        nxt = page.get("next_page_uri")
        url, params = (HOST + nxt) if nxt else None, {}
    return out[:limit]


def suspended_rows(messages):
    """Message rows stamped with the account-suspended error, oldest first."""
    rows = [m for m in messages
            if str(m.get("error_code") or "").strip() == str(SUSPENDED_ERROR)]
    return sorted(rows, key=lambda m: str(m.get("date_sent") or ""))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=7,
                    help="how far back to read the Messages list for 30002")
    ap.add_argument("--max-messages", type=int, default=20000,
                    help="stop paging after this many messages")
    ap.add_argument("--skip-messages", action="store_true",
                    help="read the account status only, for a fast health check")
    args = ap.parse_args()

    account = os.environ.get("TWILIO_ACCOUNT_SID")
    key = os.environ.get("TWILIO_API_KEY")
    secret = os.environ.get("TWILIO_API_SECRET")
    if not (account and key and secret):
        log.error("set TWILIO_ACCOUNT_SID, TWILIO_API_KEY and TWILIO_API_SECRET "
                  "(an API Key with read access, not the auth token)")
        return 2

    session = requests.Session()
    session.auth = (key, secret)

    acct = fetch_account(session, account)

    failed = []
    if not args.skip_messages:
        since = (dt.date.today() - dt.timedelta(days=args.days)).isoformat()
        failed = suspended_rows(list_messages(session, account, since,
                                              args.max_messages))

    state, detail = verdict(acct, len(failed), args.days)
    line = "%-18s %s  %s" % (state, acct.get("sid", "?"), detail)
    if state == "active":
        log.info(line)
        return 0

    log.warning(line)
    if scope(acct) == "subaccount":
        log.warning("  this SID is a subaccount of %s. A suspended parent takes "
                    "its children with it, so read the parent's status too.",
                    acct.get("owner_account_sid"))
    if failed:
        log.warning("  first 30002 at %s, last at %s",
                    failed[0].get("date_sent"), failed[-1].get("date_sent"))
    if state == "closed":
        log.warning("  repair: none by API or Console. A closed account is not "
                    "reopened; open a ticket at help.twilio.com to recover what "
                    "can be recovered, and expect to stand up a new account.")
    else:
        log.warning("  repair: Console -> Billing. If the balance is at or below "
                    "zero, add funds and allow five to ten minutes for "
                    "reactivation. If the balance is healthy, this is a policy "
                    "review and only a ticket at help.twilio.com clears it.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-account-status-audit.mjs",
"js": '''/**
 * Report whether the Twilio account behind this credential is still active.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const HOST = 'https://api.twilio.com';
const BASE = `${HOST}/2010-04-01`;

// The error stamped on messages that were queued when the account stopped being
// active. Requests made after the suspension never become a Message row at all.
const SUSPENDED_ERROR = 30002;

/**
 * Whether this SID is the top-level account or one of its subaccounts.
 * owner_account_sid on a parent is the account's own sid; on a child it is the
 * parent's, and the repair differs.
 */
export function scope(account) {
  const sid = String(account.sid ?? '').trim();
  const owner = String(account.owner_account_sid ?? '').trim();
  return sid && owner && sid !== owner ? 'subaccount' : 'account';
}

/**
 * Classify one Account resource. Pure, so every state can be exercised without
 * a network. Returns [state, detail].
 */
export function verdict(account, failed = 0, days = 7) {
  const status = String(account.status ?? '').trim().toLowerCase();

  if (!status) {
    return ['unknown',
      'the Account resource carried no status field. Do not read that as ' +
      'healthy: fetch it again before deciding anything.'];
  }

  if (status === 'closed') {
    return ['closed',
      'status is closed. This is terminal. The account cannot be reopened, its ' +
      'numbers are not coming back, and the work is a new account rather than ' +
      'a payment.'];
  }

  if (status === 'suspended') {
    return ['suspended',
      'status is suspended: every send, call and number purchase is refused ' +
      `with 20005, and anything already queued fails with ${SUSPENDED_ERROR}. ` +
      'Check the balance before assuming it is a billing suspension.'];
  }

  if (status !== 'active') {
    return ['not-active',
      `status is "${status}", which is not active. Everything the account does ` +
      'is refused with 20005 until it is.'];
  }

  if (failed) {
    return ['recently-suspended',
      `status is active now, but ${failed} message(s) in the last ${days} days ` +
      `failed with ${SUSPENDED_ERROR}. The account was not active while those ` +
      'were queued, and nothing recorded when that started or ended except ' +
      'these rows.'];
  }

  return ['active',
    `status is active, and no message in the last ${days} days failed with ` +
    `${SUSPENDED_ERROR}.`];
}

function authHeader(key, secret) {
  return `Basic ${Buffer.from(`${key}:${secret}`).toString('base64')}`;
}

async function get(auth, url, params = {}) {
  const u = new URL(url);
  for (const [k, v] of Object.entries(params)) u.searchParams.set(k, v);
  const res = await fetch(u, { headers: { Authorization: auth } });
  if (res.status === 401) {
    throw new Error('401 from Twilio: check TWILIO_ACCOUNT_SID and that the ' +
                    'API key belongs to that account with read access');
  }
  if (res.status === 403) {
    throw new Error(`403 from Twilio at ${u.pathname}. If the body carries ` +
                    '20005 the account is not active, which is this finding.');
  }
  if (!res.ok) throw new Error(`${res.status} from ${u.pathname}`);
  return res.json();
}

export async function listMessages(auth, account, since, limit = 20000) {
  let url = `${BASE}/Accounts/${account}/Messages.json`;
  let params = { PageSize: 1000, 'DateSent>=': since };
  const out = [];
  while (url && out.length < limit) {
    const page = await get(auth, url, params);
    out.push(...(page.messages ?? []));
    url = page.next_page_uri ? HOST + page.next_page_uri : null;
    params = {};
  }
  return out.slice(0, limit);
}

/** Message rows stamped with the account-suspended error, oldest first. */
export function suspendedRows(messages) {
  return messages
    .filter((m) => String(m.error_code ?? '').trim() === String(SUSPENDED_ERROR))
    .sort((a, b) => String(a.date_sent ?? '').localeCompare(String(b.date_sent ?? '')));
}

async function main() {
  const account = process.env.TWILIO_ACCOUNT_SID;
  const key = process.env.TWILIO_API_KEY;
  const secret = process.env.TWILIO_API_SECRET;
  if (!account || !key || !secret) {
    console.error('set TWILIO_ACCOUNT_SID, TWILIO_API_KEY and TWILIO_API_SECRET ' +
                  '(an API Key with read access, not the auth token)');
    process.exitCode = 2;
    return;
  }
  const auth = authHeader(key, secret);

  const days = Number(process.argv.includes('--days')
    ? process.argv[process.argv.indexOf('--days') + 1] : 7) || 7;

  const acct = await get(auth, `${BASE}/Accounts/${account}.json`);

  let failed = [];
  if (!process.argv.includes('--skip-messages')) {
    const since = new Date(Date.now() - days * 86400000).toISOString().slice(0, 10);
    failed = suspendedRows(await listMessages(auth, account, since));
  }

  const [state, detail] = verdict(acct, failed.length, days);
  const line = `${state.padEnd(18)} ${acct.sid ?? '?'}  ${detail}`;
  if (state === 'active') {
    console.log(line);
    return;
  }

  console.warn(line);
  if (scope(acct) === 'subaccount') {
    console.warn(`  this SID is a subaccount of ${acct.owner_account_sid}. A ` +
                 'suspended parent takes its children with it, so read the ' +
                 "parent's status too.");
  }
  if (failed.length) {
    console.warn(`  first 30002 at ${failed[0].date_sent}, last at ` +
                 `${failed[failed.length - 1].date_sent}`);
  }
  if (state === 'closed') {
    console.warn('  repair: none by API or Console. A closed account is not ' +
                 'reopened; open a ticket at help.twilio.com to recover what can ' +
                 'be recovered, and expect to stand up a new account.');
  } else {
    console.warn('  repair: Console -> Billing. If the balance is at or below ' +
                 'zero, add funds and allow five to ten minutes for ' +
                 'reactivation. If the balance is healthy, this is a policy ' +
                 'review and only a ticket at help.twilio.com clears it.');
  }
  process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The cases that matter are the two that a naive check gets wrong: <code>closed</code> read as just another kind of suspended, and an account reading <code>active</code> while the window behind it is full of <code>30002</code>. The parent/child test is here too, because <code>owner_account_sid</code> equalling <code>sid</code> is the only thing separating a top-level account from a tenant.",
"test_py_file": "test_twilio_account_status_audit.py",
"test_py": '''from twilio_account_status_audit import scope, suspended_rows, verdict


def test_suspended_status_is_the_finding():
    state, detail = verdict({"sid": "AC1", "status": "suspended"})
    assert state == "suspended"
    assert "20005" in detail


def test_closed_outranks_suspended_and_says_it_is_terminal():
    state, detail = verdict({"sid": "AC1", "status": "closed"})
    assert state == "closed"
    assert "terminal" in detail


def test_status_is_compared_case_insensitively():
    assert verdict({"sid": "AC1", "status": "Suspended"})[0] == "suspended"


def test_an_unfamiliar_status_is_not_read_as_healthy():
    state, _ = verdict({"sid": "AC1", "status": "pending-closure"})
    assert state == "not-active"


def test_a_missing_status_field_is_not_read_as_healthy():
    assert verdict({"sid": "AC1"})[0] == "unknown"


def test_active_with_30002_in_the_window_is_still_a_finding():
    state, detail = verdict({"sid": "AC1", "status": "active"}, failed=41, days=7)
    assert state == "recently-suspended"
    assert "41" in detail


def test_active_and_clean_passes():
    assert verdict({"sid": "AC1", "status": "active"}, failed=0)[0] == "active"


def test_owner_account_sid_separates_a_parent_from_a_tenant():
    assert scope({"sid": "AC1", "owner_account_sid": "AC1"}) == "account"
    assert scope({"sid": "AC2", "owner_account_sid": "AC1"}) == "subaccount"


def test_suspended_rows_filters_by_error_code_and_sorts_oldest_first():
    rows = suspended_rows([
        {"error_code": 30002, "date_sent": "2024-05-02"},
        {"error_code": 30007, "date_sent": "2024-05-01"},
        {"error_code": "30002", "date_sent": "2024-05-01"},
        {"error_code": None, "date_sent": "2024-05-03"},
    ])
    assert [r["date_sent"] for r in rows] == ["2024-05-01", "2024-05-02"]
''',
"test_js_file": "twilio-account-status-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { scope, suspendedRows, verdict } from './twilio-account-status-audit.mjs';

test('suspended status is the finding', () => {
  const [state, detail] = verdict({ sid: 'AC1', status: 'suspended' });
  assert.equal(state, 'suspended');
  assert.match(detail, /20005/);
});

test('closed outranks suspended and says it is terminal', () => {
  const [state, detail] = verdict({ sid: 'AC1', status: 'closed' });
  assert.equal(state, 'closed');
  assert.match(detail, /terminal/);
});

test('status is compared case insensitively', () => {
  assert.equal(verdict({ sid: 'AC1', status: 'Suspended' })[0], 'suspended');
});

test('an unfamiliar status is not read as healthy', () => {
  assert.equal(verdict({ sid: 'AC1', status: 'pending-closure' })[0], 'not-active');
});

test('a missing status field is not read as healthy', () => {
  assert.equal(verdict({ sid: 'AC1' })[0], 'unknown');
});

test('active with 30002 in the window is still a finding', () => {
  const [state, detail] = verdict({ sid: 'AC1', status: 'active' }, 41, 7);
  assert.equal(state, 'recently-suspended');
  assert.match(detail, /41/);
});

test('active and clean passes', () => {
  assert.equal(verdict({ sid: 'AC1', status: 'active' }, 0)[0], 'active');
});

test('owner_account_sid separates a parent from a tenant', () => {
  assert.equal(scope({ sid: 'AC1', owner_account_sid: 'AC1' }), 'account');
  assert.equal(scope({ sid: 'AC2', owner_account_sid: 'AC1' }), 'subaccount');
});

test('suspendedRows filters by error code and sorts oldest first', () => {
  const rows = suspendedRows([
    { error_code: 30002, date_sent: '2024-05-02' },
    { error_code: 30007, date_sent: '2024-05-01' },
    { error_code: '30002', date_sent: '2024-05-01' },
    { error_code: null, date_sent: '2024-05-03' },
  ]);
  assert.deepEqual(rows.map((r) => r.date_sent), ['2024-05-01', '2024-05-02']);
});
''',
"faq": [
 ("Why does the API still answer if the account is suspended?",
  "Because reads are not the thing being suspended. The Console loads, the account resource returns, the message list returns. What stops is creating anything: messages, calls, number purchases and Verify starts all come back 403 with 20005. That asymmetry is exactly why a health check that only proves it can reach Twilio will report a suspended account as fine."),
 ("What is the difference between 20005 and 30002 here?",
  "20005 is the request being refused at the door, so no Message row is created and nothing appears in the message list. 30002 is stamped on messages that were already accepted and queued when the account stopped being active. Only the second one leaves a trace you can read afterwards, which is why the script counts those rather than trying to find the requests that were rejected."),
 ("Can the script reactivate the account?",
  "No, and there is no read-only way to do it either. A balance suspension clears when funds are added in the Console and reactivation follows within about five to ten minutes; a policy suspension clears only through a ticket. Both are deliberate human steps, and neither is something a credential in a cron job should be able to do."),
 ("Is closed really unrecoverable?",
  "Yes. A closed account is not reopened, which is why the script gives it a separate state rather than folding it into suspended. The practical consequences are the numbers: they are released rather than held, so the recovery plan is a new account and, where the numbers matter, a conversation with support before anything else is decided."),
 ("My subaccount reads active but nothing works. Why?",
  "Because a suspension on the parent cascades to its children without changing what the child's own status field says. If owner_account_sid on the account you fetched is not equal to its own sid, you are looking at a child, and the next thing to read is the parent's status with the parent's credentials. The reverse case, one suspended child under a healthy parent, is a separate note."),
],
"related": [
 ("/twilio/subaccount-suspended-silently/", "One suspended tenant under a healthy parent"),
 ("/twilio/balance-below-safety-floor/", "A balance one busy hour from a suspension"),
 ("/twilio/no-usage-trigger-configured/", "No spend alarm on an account that can spend"),
],
"citations": [CITE_ACCOUNT, CITE_20005, CITE_30002, CITE_SUBACCOUNTS],
},

{
"slug": "trial-account-still-in-use",
"title": "A production integration is still on a trial account",
"description": "Trial accounts reach three lifetime-verified numbers and prefix every message body. Count how much real traffic is already aimed at one.",
"h1": "a production integration is still running on a trial account",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio trial account", "twilio account type trial", "twilio 21608",
             "sent from your twilio trial account", "twilio upgrade account"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The integration works. It has worked for weeks, on the developer's phone and on the tester's phone, and every message arrived. Then it goes in front of real users and most of them get nothing at all, while the few that do get a message find it starts with the words <em>Sent from your Twilio trial account</em>. Nobody chose this. The account was made for a spike, the spike became the product, and no one step in that sequence was the moment to upgrade.",
"short_answer": """<p>Read <code>GET /2010-04-01/Accounts/{AccountSid}.json</code> and check <code>type</code>. <code>Trial</code> means the account can only message numbers that appear in its verified caller IDs &mdash; at most three, for the lifetime of the account &mdash; and prefixes every outbound body.</p>
<p>Being on trial is not itself a fault; a development account should be. What makes it a finding is traffic. Page <code>GET /2010-04-01/Accounts/{AccountSid}/Messages.json?DateSent&gt;=YYYY-MM-DD</code>, count the distinct <code>to</code> values, and count the rows whose <code>error_code</code> is <code>21608</code>. More than three destinations, or any <code>21608</code> at all, and this is a production integration on a trial account.</p>""",
"problem": """<p>A trial account is not a smaller version of a paid one. It is a different set of rules, and the rules are ones that testing does not exercise. You may only send to numbers you have verified; the verification is by SMS only; you get three verified numbers for the whole life of the account. During development you have one phone, maybe two, and both are verified within the first hour. Every constraint the trial imposes is satisfied by accident, and stays satisfied right up until somebody who is not you is meant to receive a message.</p>
<p>The failure at that point is not subtle, but it is misattributed almost every time. Sends to unverified numbers come back <code>21608</code>, which reads like a problem with the destination rather than with the account, so the investigation starts on the recipient's phone, their carrier, their opt-out status. Meanwhile the messages that do get through carry a Twilio-branded prefix into a customer conversation, which is a different and more expensive kind of wrong.</p>
<p>The reason this survives to launch is that nothing about the trial announces itself in the shape of the code. The same SDK, the same credentials, the same endpoints, the same <code>201</code> responses. One field on one resource says <code>Trial</code>, and nothing reads it.</p>""",
"why": """<p><strong>Nothing forces the upgrade at the right moment.</strong> You upgrade by adding a payment method in the Console, which is a billing decision made by a person who is usually not the person writing the integration. Between the two of them is a gap that a working staging environment fits comfortably inside.</p>
<p><strong>The verified-number rule reads like a rate limit and is not one.</strong> Three is a lifetime cap on the account, not a concurrent one, and deleting a verified caller ID does not return the slot. That specific dead end has <a href="/twilio/trial-verified-caller-ids-exhausted/">its own note</a>, because the way it usually surfaces is one teammate's phone failing while the original developer's still works.</p>
<p><strong>The other trial limits fire at different times.</strong> The message-length cap rejects real templates with <code>30044</code> while short test messages sail through, which is <a href="/twilio/trial-account-segment-limit-30044/">a separate failure</a> with a separate error code. Finding one trial limit does not mean you have found them all; finding <code>type: Trial</code> means you have.</p>
<p><strong>The prefix is a product problem hiding in an infrastructure setting.</strong> Every outbound message on a trial account is prepended with Twilio's trial notice. Nothing in your code did that, nothing in your code can stop it, and it is going out over your brand in front of your customers.</p>
<p><strong>Upgrading does not automatically end every 21608.</strong> The verified-number restriction goes away with the upgrade. If <code>21608</code> continues on an upgraded account, the remaining path is a Primary Compliance Profile under Trust Hub, which is a form rather than a code change and is worth knowing about before you are staring at it during a launch.</p>""",
"steps": [
 {"h": "Read the account type",
  "body": """<p><code>GET /2010-04-01/Accounts/{AccountSid}.json</code> and look at <code>type</code>. This is one field and it is decisive. Do it for every account SID your services use, including the subaccounts, because a parent that has been upgraded says nothing about a child created before the payment method was added.</p>"""},
 {"h": "Measure how much real traffic is pointed at it",
  "body": """<p>Page <code>GET /2010-04-01/Accounts/{AccountSid}/Messages.json?DateSent&gt;=YYYY-MM-DD&amp;PageSize=1000</code>, following <code>next_page_uri</code>, and collect the distinct <code>to</code> values on outbound rows. A trial account cannot ever have more than three verified destinations, so a distinct count above three is proof that the integration is aimed at people it cannot reach.</p>"""},
 {"h": "Count the 21608s rather than assuming them",
  "body": """<p>The list has no <code>ErrorCode</code> filter, so read <code>error_code</code> on each row and keep the <code>21608</code>s. These are the sends that were refused for being unverified. One of them is a tester; a run of them is a launch that is already failing.</p>"""},
 {"h": "Upgrade in the Console, then re-read type",
  "body": """<p>Console &rarr; Billing &rarr; Upgrade, which means adding a payment method. There is no API call for this and there should not be. The confirmation is that <code>type</code> reads <code>Full</code> on the next fetch, and the same run should show new destinations landing without <code>21608</code>.</p>"""},
 {"h": "Keep the check, and point it at every account",
  "body": """<p>The useful version of this runs against the whole list of account SIDs your platform touches, on a schedule. New subaccounts, new environments and new demo accounts arrive as trials, and the one that matters is always the one somebody quietly started sending real traffic through.</p>"""},
],
"verify": """<p>Re-run the script after upgrading. <code>type</code> should read <code>Full</code>, and the run should exit zero regardless of how many destinations it counts.</p>
<pre><code class="language-bash">python3 twilio_trial_account_audit.py --days 7
# upgraded    AC0123  type is Full: no verified-number restriction and no trial prefix.</code></pre>""",
"code_intro": "One GET for the account and one paginated GET over the message window. The classifier is pure and takes the account dict plus the message rows, because the judgement worth testing is the one about traffic: trial with three destinations and nothing failing is a development account doing its job, and trial with forty is an outage that has not been reported yet.",
"py_file": "twilio_trial_account_audit.py",
"py": '''"""Report whether production traffic is running on a Twilio trial account.

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. Upgrading is a Console step behind a payment
method, so the repair is printed for a human to run.
"""
import argparse
import datetime as dt
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_trial_account_audit")

HOST = "https://api.twilio.com"
BASE = HOST + "/2010-04-01"

# A trial account may verify three numbers over its entire lifetime, and may only
# message numbers on that list. More distinct destinations than this is proof the
# integration is aimed at people the account cannot reach.
TRIAL_VERIFIED_CAP = 3

# Sending to a number that is not a verified caller ID on a trial account.
UNVERIFIED_ERROR = 21608


def outbound_profile(messages):
    """Reduce message rows to the two numbers the verdict needs.

    Pure and separate from the verdict so the reduction can be tested on its
    own: which destinations were attempted, and how many sends were refused for
    being unverified.
    """
    destinations = set()
    refused = 0
    for m in messages:
        if str(m.get("direction") or "outbound").startswith("inbound"):
            continue
        to = str(m.get("to") or "").strip()
        if to:
            destinations.add(to)
        if str(m.get("error_code") or "").strip() == str(UNVERIFIED_ERROR):
            refused += 1
    return destinations, refused


def verdict(account, destinations, refused=0, days=7):
    """Classify one account against the traffic aimed at it. Pure, so all four
    states can be exercised without a network.

    Returns (state, detail). Being on trial is not the finding on its own: a
    development account should be on trial. Traffic is the finding.
    """
    kind = str(account.get("type") or "").strip().lower()

    if not kind:
        return ("unknown",
                "the Account resource carried no type field, so whether this is "
                "a trial account is not established. Fetch it again.")

    if kind != "trial":
        return ("upgraded",
                "type is %s: no verified-number restriction and no trial prefix."
                % (account.get("type") or kind))

    if refused:
        return ("trial-blocked",
                "type is Trial and %d send(s) in the last %d days were refused "
                "with %d. Those recipients got nothing, and the ones that did "
                "get through carried Twilio's trial prefix."
                % (refused, days, UNVERIFIED_ERROR))

    if len(destinations) > TRIAL_VERIFIED_CAP:
        return ("trial-in-production",
                "type is Trial with %d distinct destination(s) in the last %d "
                "days. A trial account can verify %d numbers for its entire "
                "lifetime, so most of these can never be delivered to."
                % (len(destinations), days, TRIAL_VERIFIED_CAP))

    return ("trial-idle",
            "type is Trial with %d distinct destination(s) in the last %d days: "
            "consistent with a development account. Upgrade before it sees real "
            "recipients, not after." % (len(destinations), days))


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def list_messages(session, account, since, limit):
    """Page Messages.json. No ErrorCode filter exists on this resource, so the
    21608s are found by reading error_code on every row in the window."""
    url = "%s/Accounts/%s/Messages.json" % (BASE, account)
    params = {"PageSize": 1000, "DateSent>=": since}
    out = []
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get("messages", []))
        nxt = page.get("next_page_uri")
        url, params = (HOST + nxt) if nxt else None, {}
    return out[:limit]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=7,
                    help="how far back to read the Messages list")
    ap.add_argument("--max-messages", type=int, default=20000,
                    help="stop paging after this many messages")
    args = ap.parse_args()

    account = os.environ.get("TWILIO_ACCOUNT_SID")
    key = os.environ.get("TWILIO_API_KEY")
    secret = os.environ.get("TWILIO_API_SECRET")
    if not (account and key and secret):
        log.error("set TWILIO_ACCOUNT_SID, TWILIO_API_KEY and TWILIO_API_SECRET "
                  "(an API Key with read access, not the auth token)")
        return 2

    session = requests.Session()
    session.auth = (key, secret)

    acct = get(session, "%s/Accounts/%s.json" % (BASE, account))
    since = (dt.date.today() - dt.timedelta(days=args.days)).isoformat()
    messages = list_messages(session, account, since, args.max_messages)
    destinations, refused = outbound_profile(messages)

    state, detail = verdict(acct, destinations, refused, args.days)
    line = "%-20s %s  %s" % (state, acct.get("sid", "?"), detail)
    if state == "upgraded":
        log.info(line)
        return 0

    log.warning(line)
    if state == "trial-idle":
        log.warning("  repair: Console -> Billing -> Upgrade before launch. "
                    "There is no API call for this, by design.")
        return 1

    log.warning("  repair: Console -> Billing -> Upgrade (add a payment "
                "method). That removes the verified-number restriction and the "
                "trial prefix on every outbound body.")
    log.warning("  if 21608 continues after upgrading, submit a Primary "
                "Compliance Profile under Console -> Compliance -> Trust Hub.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-trial-account-audit.mjs",
"js": '''/**
 * Report whether production traffic is running on a Twilio trial account.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const HOST = 'https://api.twilio.com';
const BASE = `${HOST}/2010-04-01`;

// A trial account may verify three numbers over its entire lifetime, and may
// only message numbers on that list.
const TRIAL_VERIFIED_CAP = 3;

// Sending to a number that is not a verified caller ID on a trial account.
const UNVERIFIED_ERROR = 21608;

/**
 * Reduce message rows to the two numbers the verdict needs: which destinations
 * were attempted, and how many sends were refused for being unverified.
 */
export function outboundProfile(messages) {
  const destinations = new Set();
  let refused = 0;
  for (const m of messages) {
    if (String(m.direction ?? 'outbound').startsWith('inbound')) continue;
    const to = String(m.to ?? '').trim();
    if (to) destinations.add(to);
    if (String(m.error_code ?? '').trim() === String(UNVERIFIED_ERROR)) refused += 1;
  }
  return { destinations, refused };
}

/**
 * Classify one account against the traffic aimed at it. Pure, so all four
 * states can be exercised without a network. Returns [state, detail].
 */
export function verdict(account, destinations, refused = 0, days = 7) {
  const kind = String(account.type ?? '').trim().toLowerCase();
  const count = destinations instanceof Set ? destinations.size : destinations.length;

  if (!kind) {
    return ['unknown',
      'the Account resource carried no type field, so whether this is a trial ' +
      'account is not established. Fetch it again.'];
  }

  if (kind !== 'trial') {
    return ['upgraded',
      `type is ${account.type ?? kind}: no verified-number restriction and no ` +
      'trial prefix.'];
  }

  if (refused) {
    return ['trial-blocked',
      `type is Trial and ${refused} send(s) in the last ${days} days were ` +
      `refused with ${UNVERIFIED_ERROR}. Those recipients got nothing, and the ` +
      "ones that did get through carried Twilio's trial prefix."];
  }

  if (count > TRIAL_VERIFIED_CAP) {
    return ['trial-in-production',
      `type is Trial with ${count} distinct destination(s) in the last ${days} ` +
      `days. A trial account can verify ${TRIAL_VERIFIED_CAP} numbers for its ` +
      'entire lifetime, so most of these can never be delivered to.'];
  }

  return ['trial-idle',
    `type is Trial with ${count} distinct destination(s) in the last ${days} ` +
    'days: consistent with a development account. Upgrade before it sees real ' +
    'recipients, not after.'];
}

function authHeader(key, secret) {
  return `Basic ${Buffer.from(`${key}:${secret}`).toString('base64')}`;
}

async function get(auth, url, params = {}) {
  const u = new URL(url);
  for (const [k, v] of Object.entries(params)) u.searchParams.set(k, v);
  const res = await fetch(u, { headers: { Authorization: auth } });
  if (res.status === 401 || res.status === 403) {
    throw new Error(`${res.status} from Twilio: check TWILIO_ACCOUNT_SID and ` +
                    'that the API key belongs to that account with read access');
  }
  if (!res.ok) throw new Error(`${res.status} from ${u.pathname}`);
  return res.json();
}

export async function listMessages(auth, account, since, limit = 20000) {
  let url = `${BASE}/Accounts/${account}/Messages.json`;
  let params = { PageSize: 1000, 'DateSent>=': since };
  const out = [];
  while (url && out.length < limit) {
    const page = await get(auth, url, params);
    out.push(...(page.messages ?? []));
    url = page.next_page_uri ? HOST + page.next_page_uri : null;
    params = {};
  }
  return out.slice(0, limit);
}

async function main() {
  const account = process.env.TWILIO_ACCOUNT_SID;
  const key = process.env.TWILIO_API_KEY;
  const secret = process.env.TWILIO_API_SECRET;
  if (!account || !key || !secret) {
    console.error('set TWILIO_ACCOUNT_SID, TWILIO_API_KEY and TWILIO_API_SECRET ' +
                  '(an API Key with read access, not the auth token)');
    process.exitCode = 2;
    return;
  }
  const auth = authHeader(key, secret);

  const days = Number(process.argv.includes('--days')
    ? process.argv[process.argv.indexOf('--days') + 1] : 7) || 7;

  const acct = await get(auth, `${BASE}/Accounts/${account}.json`);
  const since = new Date(Date.now() - days * 86400000).toISOString().slice(0, 10);
  const messages = await listMessages(auth, account, since);
  const { destinations, refused } = outboundProfile(messages);

  const [state, detail] = verdict(acct, destinations, refused, days);
  const line = `${state.padEnd(20)} ${acct.sid ?? '?'}  ${detail}`;
  if (state === 'upgraded') {
    console.log(line);
    return;
  }

  console.warn(line);
  if (state === 'trial-idle') {
    console.warn('  repair: Console -> Billing -> Upgrade before launch. There ' +
                 'is no API call for this, by design.');
  } else {
    console.warn('  repair: Console -> Billing -> Upgrade (add a payment ' +
                 'method). That removes the verified-number restriction and the ' +
                 'trial prefix on every outbound body.');
    console.warn('  if 21608 continues after upgrading, submit a Primary ' +
                 'Compliance Profile under Console -> Compliance -> Trust Hub.');
  }
  process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The distinction being pinned is the one the whole note rests on: trial is not automatically a finding. A trial account with two destinations and no failures is a development account, and reporting it as an incident trains people to ignore the report. The other cases are a single <code>21608</code> outranking a healthy-looking destination count, and inbound rows not inflating that count.",
"test_py_file": "test_twilio_trial_account_audit.py",
"test_py": '''from twilio_trial_account_audit import outbound_profile, verdict

TRIAL = {"sid": "AC1", "type": "Trial"}
FULL = {"sid": "AC1", "type": "Full"}


def test_a_full_account_is_never_a_finding():
    state, detail = verdict(FULL, {"+14155550100"})
    assert state == "upgraded"
    assert "prefix" in detail


def test_trial_with_a_handful_of_testers_is_not_reported_as_an_incident():
    state, _ = verdict(TRIAL, {"+14155550100", "+14155550101"})
    assert state == "trial-idle"


def test_more_destinations_than_the_lifetime_cap_is_production_traffic():
    dests = {"+1415555010%d" % i for i in range(6)}
    state, detail = verdict(TRIAL, dests, days=7)
    assert state == "trial-in-production"
    assert "6 distinct" in detail


def test_one_21608_outranks_a_small_destination_count():
    state, detail = verdict(TRIAL, {"+14155550100"}, refused=1)
    assert state == "trial-blocked"
    assert "21608" in detail


def test_a_missing_type_field_is_not_read_as_upgraded():
    assert verdict({"sid": "AC1"}, set())[0] == "unknown"


def test_type_is_compared_case_insensitively():
    assert verdict({"sid": "AC1", "type": "trial"}, set())[0] == "trial-idle"


def test_inbound_rows_do_not_count_as_destinations():
    dests, refused = outbound_profile([
        {"direction": "inbound", "to": "+14155550100"},
        {"direction": "outbound-api", "to": "+14155550101"},
        {"direction": "outbound-api", "to": "+14155550102", "error_code": 21608},
    ])
    assert dests == {"+14155550101", "+14155550102"}
    assert refused == 1


def test_error_codes_are_compared_as_strings_or_integers():
    _, refused = outbound_profile([
        {"to": "+1", "error_code": "21608"},
        {"to": "+2", "error_code": 21608},
        {"to": "+3", "error_code": 30044},
    ])
    assert refused == 2
''',
"test_js_file": "twilio-trial-account-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { outboundProfile, verdict } from './twilio-trial-account-audit.mjs';

const TRIAL = { sid: 'AC1', type: 'Trial' };
const FULL = { sid: 'AC1', type: 'Full' };

test('a full account is never a finding', () => {
  const [state, detail] = verdict(FULL, new Set(['+14155550100']));
  assert.equal(state, 'upgraded');
  assert.match(detail, /prefix/);
});

test('trial with a handful of testers is not reported as an incident', () => {
  const dests = new Set(['+14155550100', '+14155550101']);
  assert.equal(verdict(TRIAL, dests)[0], 'trial-idle');
});

test('more destinations than the lifetime cap is production traffic', () => {
  const dests = new Set(Array.from({ length: 6 }, (_, i) => `+1415555010${i}`));
  const [state, detail] = verdict(TRIAL, dests, 0, 7);
  assert.equal(state, 'trial-in-production');
  assert.match(detail, /6 distinct/);
});

test('one 21608 outranks a small destination count', () => {
  const [state, detail] = verdict(TRIAL, new Set(['+14155550100']), 1);
  assert.equal(state, 'trial-blocked');
  assert.match(detail, /21608/);
});

test('a missing type field is not read as upgraded', () => {
  assert.equal(verdict({ sid: 'AC1' }, new Set())[0], 'unknown');
});

test('type is compared case insensitively', () => {
  assert.equal(verdict({ sid: 'AC1', type: 'trial' }, new Set())[0], 'trial-idle');
});

test('inbound rows do not count as destinations', () => {
  const { destinations, refused } = outboundProfile([
    { direction: 'inbound', to: '+14155550100' },
    { direction: 'outbound-api', to: '+14155550101' },
    { direction: 'outbound-api', to: '+14155550102', error_code: 21608 },
  ]);
  assert.deepEqual([...destinations].sort(), ['+14155550101', '+14155550102']);
  assert.equal(refused, 1);
});

test('error codes are compared as strings or integers', () => {
  const { refused } = outboundProfile([
    { to: '+1', error_code: '21608' },
    { to: '+2', error_code: 21608 },
    { to: '+3', error_code: 30044 },
  ]);
  assert.equal(refused, 2);
});
''',
"faq": [
 ("Is being on a trial account a problem by itself?",
  "No, and a report that says so is a report people learn to close. A development account should be on trial: it costs nothing and it cannot spend. The finding is trial plus traffic, which is why the script counts distinct destinations and 21608s before it decides how loudly to complain."),
 ("Why does the distinct-destination count matter more than the message count?",
  "Because volume can be one tester hammering a button, and that is fine. A trial account can only ever reach three verified numbers, so more than three distinct destinations means somebody has pointed the integration at a population it cannot serve. That is the shape of a production launch, whatever the total send count says."),
 ("What exactly does the trial prefix do to my messages?",
  "Twilio prepends its trial notice to the body of every outbound message on a trial account. You cannot disable it, it consumes characters from the segment budget, and it goes out in front of your customers under your sender. It is the reason this note is not purely about deliverability."),
 ("We upgraded and we are still getting 21608. What now?",
  "Upgrading removes the trial verified-number restriction, so a continuing 21608 is a different cause on the same code. The next step is a Primary Compliance Profile under Console then Compliance then Trust Hub. It is paperwork rather than a code change, and it takes time, which is why it is worth starting before launch day rather than during it."),
 ("How is this different from the trial message-length note?",
  "That one is a single limit firing: 30044 on a body that exceeds the trial length cap, which is why short test messages send and real templates do not. This one is the account-level state that produces that limit and several others at once. If you find a 30044 on a trial account, fixing the template treats a symptom; reading type tells you how many other symptoms are queued up behind it."),
],
"related": [
 ("/twilio/trial-verified-caller-ids-exhausted/", "The trial account's three verified numbers are spent"),
 ("/twilio/trial-account-segment-limit-30044/", "A trial account rejecting multi-segment messages"),
 ("/twilio/account-suspended-or-closed/", "The account itself is suspended or closed"),
],
"citations": [CITE_ACCOUNT, CITE_21608, CITE_MESSAGE, CITE_30044],
},

{
"slug": "trial-verified-caller-ids-exhausted",
"title": "The trial account's three verified numbers are spent",
"description": "A teammate's phone gets 21608 while the first developer's still works. The trial verification quota is three numbers for the account's lifetime.",
"h1": "the trial account's three verified numbers are spent",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio verified caller id limit", "twilio 21608 trial",
             "twilio outgoingcallerids", "twilio verify number trial",
             "twilio trial three numbers"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "It works on your phone. It has always worked on your phone. A colleague joins the project, adds their number to the test list, and gets nothing at all &mdash; <code>21608</code>, on a number that is switched on, in coverage, and perfectly capable of receiving messages from everyone else. Nothing changed in the code between the two runs. What changed is that the account had already spent the three verifications it was ever going to get.",
"short_answer": """<p>Read <code>GET /2010-04-01/Accounts/{AccountSid}/OutgoingCallerIds.json</code> and count the entries. On an account where <code>GET /2010-04-01/Accounts/{AccountSid}.json</code> reports <code>type</code> as <code>Trial</code>, a count at or near three means the pool is spent: three verifications is the lifetime allowance for the account, not a rolling limit.</p>
<p>Then compare each <code>phone_number</code> against the <code>to</code> values your application actually sends to, from <code>GET /2010-04-01/Accounts/{AccountSid}/Messages.json</code>. Any destination missing from that list is a <code>21608</code> waiting to happen, and comparing the two is the only way to see it before somebody reports it.</p>""",
"problem": """<p>The rule is unusual enough that people do not believe it the first time. A trial account may verify three unique numbers, ever. Not three at a time, not three per month: three, across the whole life of the account, and deleting a verified caller ID does not give the slot back. So the pool is a countdown that only ever goes one way, and it is spent by exactly the ordinary things &mdash; your phone, a second phone for testing inbound, a personal number used once to check something on a Sunday.</p>
<p>By the time the fourth number is needed, the account has been working for weeks. That is what makes the diagnosis go wrong: the failure is new, so it is investigated as though something recently broke. It presents as one person's phone not receiving messages, which points the investigation at that phone, that carrier, that number's opt-out state. The account-level constraint that actually caused it is invisible from anywhere near the failing send.</p>
<p>Worse, verification on a trial account can only be done by SMS. If the number that needs to be added is a landline, a desk phone or a VoIP number that cannot receive SMS, no slot in the world helps, and the answer is the same as it is for the exhausted pool: this account has to be upgraded.</p>""",
"why": """<p><strong>Three is a lifetime cap, and deletion does not refund it.</strong> The tempting fix &mdash; delete the number you no longer test with, free a slot &mdash; does not work. You lose the verification and gain nothing, so the account is left in a worse state than before. It is worth knowing this before you start tidying.</p>
<p><strong>The error names the destination, not the account.</strong> <code>21608</code> is about the <code>To</code> number being unverified, so it reads as a per-recipient problem. Everything about the message that failed looks fine, and the thing that is actually full is a list on the account that nobody has looked at.</p>
<p><strong>The verified list and the destination list are never compared.</strong> Both are one GET away. Nothing joins them for you, and until they are joined the report is either a count with no meaning or a list of numbers with no indication which of them matter. The join is the whole check.</p>
<p><strong>Verification is SMS-only on trial.</strong> A number that cannot receive SMS cannot be verified on a trial account regardless of how many slots remain, which quietly rules out testing against landlines and some VoIP numbers until the account is upgraded.</p>
<p><strong>The real repair is not about slots at all.</strong> Upgrading removes the verified-number restriction entirely, so the correct move on an account that has hit this is to stop managing the pool and go and add a payment method. That the account never left trial is <a href="/twilio/trial-account-still-in-use/">the larger finding</a>; this is the specific wall you hit first.</p>""",
"steps": [
 {"h": "Confirm the restriction applies at all",
  "body": """<p><code>GET /2010-04-01/Accounts/{AccountSid}.json</code> and read <code>type</code>. On a <code>Full</code> account the verified caller ID list still exists &mdash; it is used for outbound voice caller ID &mdash; but it no longer gates who you can message, so counting it proves nothing. Check the account type before you interpret the count.</p>"""},
 {"h": "List the verified numbers",
  "body": """<p><code>GET /2010-04-01/Accounts/{AccountSid}/OutgoingCallerIds.json?PageSize=50</code>, following <code>next_page_uri</code>. Read <code>phone_number</code> and <code>friendly_name</code> on each. The count is the first half of the answer; on a trial account, three is the ceiling.</p>"""},
 {"h": "Collect the destinations the application actually uses",
  "body": """<p>Page <code>GET /2010-04-01/Accounts/{AccountSid}/Messages.json?DateSent&gt;=YYYY-MM-DD&amp;PageSize=1000</code> and collect the distinct <code>to</code> values on outbound rows. This is the other half. Without it you have a number between zero and three and no idea whether it is enough.</p>"""},
 {"h": "Compare them in E.164, not as strings",
  "body": """<p><code>+1 (415) 555-0100</code> and <code>+14155550100</code> are the same phone and different strings. Strip everything that is not a digit or a leading <code>+</code> on both sides before comparing, or the report will confidently tell you a verified number is unverified.</p>"""},
 {"h": "Upgrade rather than manage the pool",
  "body": """<p>Console &rarr; Billing &rarr; Upgrade. Adding a payment method removes the verified-number restriction completely, which is the only repair that scales past the third tester. Do not delete caller IDs hoping to free a slot; the quota does not come back and you will have lost a working verification for nothing.</p>"""},
],
"verify": """<p>Re-run the script. After an upgrade it should report <code>not-trial</code> and exit zero; every destination is reachable and the pool no longer gates anything.</p>
<pre><code class="language-bash">python3 twilio_verified_caller_ids_audit.py --days 30
# not-trial   type is Full: the verified caller ID list no longer gates messaging.</code></pre>""",
"code_intro": "Three GETs: the account, the verified caller IDs, and the message window that says which destinations are actually in use. The two pure pieces are the E.164 normaliser and the verdict, and the normaliser is the one that quietly decides whether the whole report is true, because the two lists arrive formatted differently often enough to matter.",
"py_file": "twilio_verified_caller_ids_audit.py",
"py": '''"""Report whether a Twilio trial account has spent its verified-number quota.

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. The repair is an upgrade in the Console, so
it is printed for a human to run.
"""
import argparse
import datetime as dt
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_verified_caller_ids_audit")

HOST = "https://api.twilio.com"
BASE = HOST + "/2010-04-01"

# Verifications a trial account gets over its entire lifetime. Deleting a
# verified caller ID does not return a slot, so this is a countdown rather than
# a capacity.
TRIAL_VERIFICATION_QUOTA = 3

UNVERIFIED_ERROR = 21608


def e164(value):
    """Reduce a phone number to a comparable form.

    The verified caller ID list and the message list are populated by different
    paths and are not always formatted the same way, so "+1 (415) 555-0100" and
    "+14155550100" both turn up for the same phone. Comparing the raw strings
    reports verified numbers as unverified, which is the one mistake that makes
    this report worse than not running it.
    """
    digits = "".join(c for c in str(value or "") if c.isdigit())
    return ("+" + digits) if digits else ""


def verdict(account, caller_ids, destinations):
    """Classify the verified-number pool against the traffic. Pure, so every
    state can be exercised without a network.

    Returns (state, detail).
    """
    kind = str(account.get("type") or "").strip().lower()
    if kind and kind != "trial":
        return ("not-trial",
                "type is %s: the verified caller ID list no longer gates "
                "messaging." % (account.get("type") or kind))

    verified = {e164(c.get("phone_number")) for c in caller_ids}
    verified.discard("")
    wanted = {e164(d) for d in destinations}
    wanted.discard("")
    missing = sorted(wanted - verified)
    left = TRIAL_VERIFICATION_QUOTA - len(verified)

    if len(verified) >= TRIAL_VERIFICATION_QUOTA:
        return ("spent",
                "%d verified number(s) on a trial account: the lifetime quota of "
                "%d is spent, and deleting one does not return a slot. %d "
                "destination(s) in the window cannot be reached and get %d."
                % (len(verified), TRIAL_VERIFICATION_QUOTA, len(missing),
                   UNVERIFIED_ERROR))

    if missing:
        return ("unverified",
                "%d destination(s) in the window are not verified and get %d. "
                "%d slot(s) left, and they are the last %d this account will "
                "ever have."
                % (len(missing), UNVERIFIED_ERROR, left, left))

    return ("ok",
            "%d verified number(s), every destination in the window covered, %d "
            "slot(s) left for the lifetime of the account."
            % (len(verified), left))


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def paged(session, url, field, params, limit):
    """Walk a 2010-04-01 list resource. next_page_uri is a path, not a URL."""
    out = []
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get(field, []))
        nxt = page.get("next_page_uri")
        url, params = (HOST + nxt) if nxt else None, {}
    return out[:limit]


def destinations_used(messages):
    """Distinct outbound destinations in the window, plus the ones already
    refused for being unverified."""
    used, refused = set(), set()
    for m in messages:
        if str(m.get("direction") or "outbound").startswith("inbound"):
            continue
        to = str(m.get("to") or "").strip()
        if not to:
            continue
        used.add(to)
        if str(m.get("error_code") or "").strip() == str(UNVERIFIED_ERROR):
            refused.add(to)
    return used, refused


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=30,
                    help="how far back to read destinations from the Messages list")
    ap.add_argument("--max-messages", type=int, default=20000,
                    help="stop paging after this many messages")
    args = ap.parse_args()

    account = os.environ.get("TWILIO_ACCOUNT_SID")
    key = os.environ.get("TWILIO_API_KEY")
    secret = os.environ.get("TWILIO_API_SECRET")
    if not (account and key and secret):
        log.error("set TWILIO_ACCOUNT_SID, TWILIO_API_KEY and TWILIO_API_SECRET "
                  "(an API Key with read access, not the auth token)")
        return 2

    session = requests.Session()
    session.auth = (key, secret)

    acct = get(session, "%s/Accounts/%s.json" % (BASE, account))
    caller_ids = paged(session,
                       "%s/Accounts/%s/OutgoingCallerIds.json" % (BASE, account),
                       "outgoing_caller_ids", {"PageSize": 50}, 200)
    since = (dt.date.today() - dt.timedelta(days=args.days)).isoformat()
    messages = paged(session, "%s/Accounts/%s/Messages.json" % (BASE, account),
                     "messages", {"PageSize": 1000, "DateSent>=": since},
                     args.max_messages)
    used, refused = destinations_used(messages)

    state, detail = verdict(acct, caller_ids, used)
    log.info("verified: %s", ", ".join(sorted(
        str(c.get("phone_number")) for c in caller_ids)) or "none")
    line = "%-11s %s" % (state, detail)
    if state in ("not-trial", "ok"):
        log.info(line)
        return 0

    log.warning(line)
    for number in sorted(refused):
        log.warning("  %s already failed with %d in this window",
                    number, UNVERIFIED_ERROR)
    log.warning("  repair: Console -> Billing -> Upgrade. That removes the "
                "verified-number restriction entirely. Do not delete caller IDs "
                "to free slots: the quota is not restored.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-verified-caller-ids-audit.mjs",
"js": '''/**
 * Report whether a Twilio trial account has spent its verified-number quota.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const HOST = 'https://api.twilio.com';
const BASE = `${HOST}/2010-04-01`;

// Verifications a trial account gets over its entire lifetime. Deleting a
// verified caller ID does not return a slot.
const TRIAL_VERIFICATION_QUOTA = 3;

const UNVERIFIED_ERROR = 21608;

/**
 * Reduce a phone number to a comparable form. The two lists this script joins
 * are not always formatted the same way, and comparing raw strings reports
 * verified numbers as unverified.
 */
export function e164(value) {
  const digits = String(value ?? '').replace(/\\D/g, '');
  return digits ? `+${digits}` : '';
}

/**
 * Classify the verified-number pool against the traffic. Pure, so every state
 * can be exercised without a network. Returns [state, detail].
 */
export function verdict(account, callerIds, destinations) {
  const kind = String(account.type ?? '').trim().toLowerCase();
  if (kind && kind !== 'trial') {
    return ['not-trial',
      `type is ${account.type ?? kind}: the verified caller ID list no longer ` +
      'gates messaging.'];
  }

  const verified = new Set(callerIds.map((c) => e164(c.phone_number)).filter(Boolean));
  const wanted = new Set([...destinations].map(e164).filter(Boolean));
  const missing = [...wanted].filter((n) => !verified.has(n)).sort();
  const left = TRIAL_VERIFICATION_QUOTA - verified.size;

  if (verified.size >= TRIAL_VERIFICATION_QUOTA) {
    return ['spent',
      `${verified.size} verified number(s) on a trial account: the lifetime ` +
      `quota of ${TRIAL_VERIFICATION_QUOTA} is spent, and deleting one does ` +
      `not return a slot. ${missing.length} destination(s) in the window ` +
      `cannot be reached and get ${UNVERIFIED_ERROR}.`];
  }

  if (missing.length) {
    return ['unverified',
      `${missing.length} destination(s) in the window are not verified and get ` +
      `${UNVERIFIED_ERROR}. ${left} slot(s) left, and they are the last ` +
      `${left} this account will ever have.`];
  }

  return ['ok',
    `${verified.size} verified number(s), every destination in the window ` +
    `covered, ${left} slot(s) left for the lifetime of the account.`];
}

function authHeader(key, secret) {
  return `Basic ${Buffer.from(`${key}:${secret}`).toString('base64')}`;
}

async function get(auth, url, params = {}) {
  const u = new URL(url);
  for (const [k, v] of Object.entries(params)) u.searchParams.set(k, v);
  const res = await fetch(u, { headers: { Authorization: auth } });
  if (res.status === 401 || res.status === 403) {
    throw new Error(`${res.status} from Twilio: check TWILIO_ACCOUNT_SID and ` +
                    'that the API key belongs to that account with read access');
  }
  if (!res.ok) throw new Error(`${res.status} from ${u.pathname}`);
  return res.json();
}

export async function paged(auth, url, field, params, limit) {
  const out = [];
  let next = url;
  let query = params;
  while (next && out.length < limit) {
    const page = await get(auth, next, query);
    out.push(...(page[field] ?? []));
    next = page.next_page_uri ? HOST + page.next_page_uri : null;
    query = {};
  }
  return out.slice(0, limit);
}

/** Distinct outbound destinations, plus those already refused as unverified. */
export function destinationsUsed(messages) {
  const used = new Set();
  const refused = new Set();
  for (const m of messages) {
    if (String(m.direction ?? 'outbound').startsWith('inbound')) continue;
    const to = String(m.to ?? '').trim();
    if (!to) continue;
    used.add(to);
    if (String(m.error_code ?? '').trim() === String(UNVERIFIED_ERROR)) refused.add(to);
  }
  return { used, refused };
}

async function main() {
  const account = process.env.TWILIO_ACCOUNT_SID;
  const key = process.env.TWILIO_API_KEY;
  const secret = process.env.TWILIO_API_SECRET;
  if (!account || !key || !secret) {
    console.error('set TWILIO_ACCOUNT_SID, TWILIO_API_KEY and TWILIO_API_SECRET ' +
                  '(an API Key with read access, not the auth token)');
    process.exitCode = 2;
    return;
  }
  const auth = authHeader(key, secret);

  const days = Number(process.argv.includes('--days')
    ? process.argv[process.argv.indexOf('--days') + 1] : 30) || 30;

  const acct = await get(auth, `${BASE}/Accounts/${account}.json`);
  const callerIds = await paged(
    auth, `${BASE}/Accounts/${account}/OutgoingCallerIds.json`,
    'outgoing_caller_ids', { PageSize: 50 }, 200);
  const since = new Date(Date.now() - days * 86400000).toISOString().slice(0, 10);
  const messages = await paged(
    auth, `${BASE}/Accounts/${account}/Messages.json`, 'messages',
    { PageSize: 1000, 'DateSent>=': since }, 20000);
  const { used, refused } = destinationsUsed(messages);

  const [state, detail] = verdict(acct, callerIds, used);
  const list = callerIds.map((c) => String(c.phone_number)).sort().join(', ');
  console.log(`verified: ${list || 'none'}`);
  const line = `${state.padEnd(11)} ${detail}`;
  if (state === 'not-trial' || state === 'ok') {
    console.log(line);
    return;
  }

  console.warn(line);
  for (const number of [...refused].sort()) {
    console.warn(`  ${number} already failed with ${UNVERIFIED_ERROR} in this window`);
  }
  console.warn('  repair: Console -> Billing -> Upgrade. That removes the ' +
               'verified-number restriction entirely. Do not delete caller IDs ' +
               'to free slots: the quota is not restored.');
  process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The formatting test is the one that earns its place: the two lists being joined come from different resources and arrive punctuated differently, so a report that compares raw strings will tell you a verified number is unverified and send somebody to burn a slot they do not have. The rest pin the ordering, in particular that a full pool outranks a tidy-looking destination match.",
"test_py_file": "test_twilio_verified_caller_ids_audit.py",
"test_py": '''from twilio_verified_caller_ids_audit import destinations_used, e164, verdict

TRIAL = {"sid": "AC1", "type": "Trial"}
FULL = {"sid": "AC1", "type": "Full"}


def cid(number):
    return {"phone_number": number}


def test_an_upgraded_account_is_not_gated_by_the_list():
    state, detail = verdict(FULL, [cid("+14155550100")], {"+14155550999"})
    assert state == "not-trial"
    assert "no longer gates" in detail


def test_three_verified_numbers_is_the_lifetime_quota():
    state, detail = verdict(
        TRIAL, [cid("+14155550100"), cid("+14155550101"), cid("+14155550102")],
        {"+14155550100", "+14155550999"})
    assert state == "spent"
    assert "does not return a slot" in detail


def test_an_unverified_destination_with_slots_left_says_how_many_remain():
    state, detail = verdict(TRIAL, [cid("+14155550100")], {"+14155550999"})
    assert state == "unverified"
    assert "2 slot(s) left" in detail


def test_formatting_differences_are_not_reported_as_unverified():
    state, _ = verdict(TRIAL, [cid("+1 (415) 555-0100")], {"+14155550100"})
    assert state == "ok"


def test_everything_covered_and_slots_left_passes():
    state, detail = verdict(TRIAL, [cid("+14155550100")], {"+14155550100"})
    assert state == "ok"
    assert "2 slot(s) left" in detail


def test_e164_keeps_only_digits():
    assert e164("+1 (415) 555-0100") == "+14155550100"
    assert e164("") == ""
    assert e164(None) == ""


def test_inbound_rows_are_not_destinations_and_21608s_are_collected():
    used, refused = destinations_used([
        {"direction": "inbound", "to": "+14155550100"},
        {"direction": "outbound-api", "to": "+14155550101"},
        {"direction": "outbound-api", "to": "+14155550999", "error_code": "21608"},
    ])
    assert used == {"+14155550101", "+14155550999"}
    assert refused == {"+14155550999"}
''',
"test_js_file": "twilio-verified-caller-ids-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { destinationsUsed, e164, verdict } from './twilio-verified-caller-ids-audit.mjs';

const TRIAL = { sid: 'AC1', type: 'Trial' };
const FULL = { sid: 'AC1', type: 'Full' };
const cid = (phone_number) => ({ phone_number });

test('an upgraded account is not gated by the list', () => {
  const [state, detail] = verdict(FULL, [cid('+14155550100')], new Set(['+14155550999']));
  assert.equal(state, 'not-trial');
  assert.match(detail, /no longer gates/);
});

test('three verified numbers is the lifetime quota', () => {
  const [state, detail] = verdict(
    TRIAL, [cid('+14155550100'), cid('+14155550101'), cid('+14155550102')],
    new Set(['+14155550100', '+14155550999']));
  assert.equal(state, 'spent');
  assert.match(detail, /does not return a slot/);
});

test('an unverified destination with slots left says how many remain', () => {
  const [state, detail] = verdict(TRIAL, [cid('+14155550100')], new Set(['+14155550999']));
  assert.equal(state, 'unverified');
  assert.match(detail, /2 slot\\(s\\) left/);
});

test('formatting differences are not reported as unverified', () => {
  const [state] = verdict(TRIAL, [cid('+1 (415) 555-0100')], new Set(['+14155550100']));
  assert.equal(state, 'ok');
});

test('everything covered and slots left passes', () => {
  const [state, detail] = verdict(TRIAL, [cid('+14155550100')], new Set(['+14155550100']));
  assert.equal(state, 'ok');
  assert.match(detail, /2 slot\\(s\\) left/);
});

test('e164 keeps only digits', () => {
  assert.equal(e164('+1 (415) 555-0100'), '+14155550100');
  assert.equal(e164(''), '');
  assert.equal(e164(null), '');
});

test('inbound rows are not destinations and 21608s are collected', () => {
  const { used, refused } = destinationsUsed([
    { direction: 'inbound', to: '+14155550100' },
    { direction: 'outbound-api', to: '+14155550101' },
    { direction: 'outbound-api', to: '+14155550999', error_code: '21608' },
  ]);
  assert.deepEqual([...used].sort(), ['+14155550101', '+14155550999']);
  assert.deepEqual([...refused], ['+14155550999']);
});
''',
"faq": [
 ("Can I delete a verified caller ID to free a slot?",
  "No. The quota counts verifications performed over the account's lifetime, not entries currently in the list, so deleting one loses you a working verification and gains you nothing. This is the single most common wrong move on this problem, which is why the script says it in the repair line rather than leaving it implied."),
 ("Why does the error blame the destination number?",
  "Because that is what 21608 describes: the To number is not verified for this account. The wording is accurate and the framing is misleading, since the reason it cannot be verified is an account-level quota rather than anything about the number. That mismatch is why the investigation usually starts on the recipient's handset."),
 ("Does this apply to voice calls too?",
  "Yes. A trial account can only call verified numbers as well as message them, and it is the same list. The list also does a second, unrelated job on paid accounts, where it holds the external numbers you are allowed to present as caller ID, which is why finding entries there on a Full account means nothing about messaging."),
 ("What if the number I need to add cannot receive SMS?",
  "Then it cannot be verified on a trial account at all, because trial verification is SMS-only. A landline or an SMS-incapable VoIP number needs the account upgraded first. It is worth checking this before spending one of the remaining slots on an attempt that cannot succeed."),
 ("Is running out of slots really the problem, or is being on trial the problem?",
  "Being on trial is the problem; this is where it first bites. Managing three slots carefully is effort spent on a constraint that disappears the moment a payment method is added, so treat a spent pool as a prompt to upgrade rather than as a puzzle about which tester matters most."),
],
"related": [
 ("/twilio/trial-account-still-in-use/", "A production integration still on a trial account"),
 ("/twilio/trial-account-segment-limit-30044/", "A trial account rejecting multi-segment messages"),
 ("/twilio/dial-invalid-caller-id-13214/", "An outbound call rejected for an invalid caller ID"),
],
"citations": [CITE_CALLERIDS, CITE_21608, CITE_ACCOUNT, CITE_MESSAGE],
},

{
"slug": "read-credential-permission-denied",
"title": "20003 on a read key: dead credential or a real boundary",
"description": "A read-only key gets 20003 on Keys and Accounts by design. Tell that boundary apart from a wrong SID, a stale key, or a suspended account.",
"h1": "20003 on a read key: dead credential or a real boundary",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio 20003", "twilio authenticate error", "twilio api key permission",
             "twilio 401 authenticate", "twilio main vs standard key"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Every other note in this section opens by telling you to run its script with an API Key that has read access. This is the one you run when that key comes back <code>401</code> with a body whose <code>code</code> is <code>20003</code>, and you have to decide, before changing anything, whether the credential is broken or whether it just met a wall it was always going to meet.",
"short_answer": """<p><code>GET /2010-04-01/Accounts/{AccountSid}.json</code>. If that returns <code>401</code> with <code>code</code> <code>20003</code>, the credential cannot read the account at all and the problem is the credential or the SID beside it. If it returns <code>200</code>, the credential is alive and any <code>20003</code> you saw elsewhere is a scope boundary, not a fault.</p>
<p>Two boundaries account for most of them. <code>GET /2010-04-01/Accounts/{AccountSid}/Keys.json</code> and <code>GET /2010-04-01/Accounts.json</code> require a Main API Key; a Standard key gets <code>20003</code> on both, permanently and by design. Also compare the <code>sid</code> in the response body against the SID you authenticated with: if they differ, you have crossed a parent and a subaccount.</p>""",
"problem": """<p><code>20003</code> is one code covering a set of unrelated causes, and it arrives with no detail that separates them. The credential could be deleted, or from a different region, or belong to a subaccount while the path names the parent. The secret could have picked up a newline on its way through a secrets manager. A proxy in front of your egress could be stripping the <code>Authorization</code> header entirely, which produces exactly the same response as having no credential at all. Or the key could be working perfectly and simply not be allowed to read the specific resource you asked for.</p>
<p>That last case is the one that wastes the most time, because it looks like all the others and it is not a fault. The response is identical: <code>401</code>, <code>20003</code>, <code>Authenticate</code>. So somebody rotates a healthy key, or widens its permissions, or files a support ticket, when the correct action was to stop calling that endpoint from that credential.</p>
<p>There is a second impostor nearby. A suspended account returns <code>403</code> with <code>20005</code>, which reads as a permissions failure to anything that is only checking for an unhappy status code. It is not one; it is <a href="/twilio/account-suspended-or-closed/">an account that has stopped</a>, and no credential change will move it.</p>""",
"why": """<p><strong>Main and Standard keys are not the same key.</strong> A Standard key cannot read <code>Keys.json</code> or the account list at <code>Accounts.json</code>; those need a Main key. This is the boundary a read-only credential most often hits, and it is worth naming precisely, because "my key does not have permission" is usually true and usually fine.</p>
<p><strong>The account SID in the path is half the credential.</strong> Basic auth carries the key SID and secret, but the resource you read is chosen by the SID in the URL. A subaccount's key against the parent's SID authenticates fine and is refused, so the useful check is to compare the <code>sid</code> that comes back against the one you sent.</p>
<p><strong>A stripped header and a wrong password look identical.</strong> Egress proxies, service meshes and some CDN configurations drop or rewrite <code>Authorization</code>. From your side the credential is perfect; from Twilio's side there was no credential. The tell is a <code>401</code> whose body does not carry <code>20003</code> at all, which is why the script reads the body rather than only the status.</p>
<p><strong>Whitespace is a real and invisible cause.</strong> A secret with a trailing newline is a different secret. This is the one failure you can find without making a request at all, so the script checks the shape of what it was given before it spends a round trip proving the obvious.</p>
<p><strong>Nothing on the key tells you what it can do.</strong> <code>Keys.json</code> lists <code>sid</code>, <code>friendly_name</code>, <code>date_created</code> and <code>date_updated</code>. There is no permissions field, no type field and no last-used timestamp, so the only way to know what a key can read is to read something with it. That is a genuine blind spot, and it is the reason this check is a probe rather than a lookup.</p>""",
"steps": [
 {"h": "Check the shape of the credential before spending a request",
  "body": """<p>The username must be an <code>SK</code> key SID and the account SID an <code>AC</code>. A username beginning <code>AC</code> means the password beside it is the account auth token, which is <a href="/twilio/auth-token-used-instead-of-api-key/">a separate finding</a>. Leading or trailing whitespace on either half is enough to produce <code>20003</code> on its own.</p>"""},
 {"h": "Probe the account resource first",
  "body": """<p><code>GET /2010-04-01/Accounts/{AccountSid}.json</code> is the narrowest useful read. A <code>200</code> proves the credential authenticates and is scoped to that account. A <code>401</code> with <code>20003</code> here is conclusive: nothing else you try will work either.</p>"""},
 {"h": "Compare the SID that comes back with the one you sent",
  "body": """<p>The response body carries <code>sid</code> and <code>owner_account_sid</code>. If <code>sid</code> is not the SID you put in the path, you are authenticated against a different account than you meant &mdash; almost always a parent and child crossed over. That is a configuration fix, not a credential fix.</p>"""},
 {"h": "Probe the two Main-key resources deliberately",
  "body": """<p><code>GET /2010-04-01/Accounts/{AccountSid}/Keys.json</code> and <code>GET /2010-04-01/Accounts.json</code>. If the account read succeeded and these two return <code>20003</code>, you are holding a Standard key and this is the documented boundary rather than a fault. Record it and stop calling those endpoints with this credential.</p>"""},
 {"h": "Separate 20005 out before you touch the credential",
  "body": """<p>A <code>403</code> carrying <code>20005</code> is an account that is not active. Rotating keys will not fix it, and treating it as a permissions problem is how an outage gets an extra hour added to it. The script names it explicitly rather than folding it into the failure bucket.</p>"""},
],
"verify": """<p>Re-run the script with the corrected credential. A key that can read everything this section needs reports <code>read-ok</code>; a working read-only key that is Standard reports <code>scoped-key</code>, which is also a pass.</p>
<pre><code class="language-bash">python3 twilio_read_credential_check.py
# read-ok     account, keys and accounts all readable with this credential.</code></pre>""",
"code_intro": "Three GETs, deliberately chosen: the account, then the two resources that need a Main key. Unlike every other script in this section, this one does not raise on a <code>401</code> &mdash; the <code>401</code> is the measurement. Both pure functions are worth testing offline: the shape check that runs before any request, and the classifier that turns three status codes into one of six answers.",
"py_file": "twilio_read_credential_check.py",
"py": '''"""Explain a Twilio 20003: dead credential, crossed SID, or a scope boundary.

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. Unlike the other scripts here it does not
abort on a 401, because the 401 is the thing being measured.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_read_credential_check")

HOST = "https://api.twilio.com"
BASE = HOST + "/2010-04-01"

PERMISSION_DENIED = 20003
ACCOUNT_NOT_ACTIVE = 20005

# Resources a Standard API Key is not allowed to read. A Main key can; a Standard
# key gets 20003 on both, permanently, and that is a documented boundary rather
# than a broken credential. Everything else this section reads is fine on either.
MAIN_KEY_ONLY = ("keys", "accounts")


def credential_shape(account_sid, key_sid, secret):
    """Judge the credential without making a request. Pure.

    Whitespace and a wrong username are the two causes of 20003 that can be
    found for free, and finding them for free matters: a trailing newline on a
    secret is invisible in every log you will look at afterwards.

    Returns (state, detail).
    """
    if not (account_sid and key_sid and secret):
        return ("missing",
                "set TWILIO_ACCOUNT_SID, TWILIO_API_KEY and TWILIO_API_SECRET.")

    for name, value in (("TWILIO_ACCOUNT_SID", account_sid),
                        ("TWILIO_API_KEY", key_sid),
                        ("TWILIO_API_SECRET", secret)):
        if value != value.strip():
            return ("whitespace",
                    "%s has leading or trailing whitespace. A secret with a "
                    "trailing newline is a different secret, and Twilio answers "
                    "%d for it." % (name, PERMISSION_DENIED))

    if key_sid.strip().upper().startswith("AC"):
        return ("auth-token",
                "the username is an account SID, so the password beside it is "
                "the account auth token rather than an API key secret.")

    if not key_sid.strip().upper().startswith("SK"):
        return ("not-a-key",
                "the username is neither an SK API Key SID nor an AC account "
                "SID, so nothing on the Twilio side will match it.")

    if not account_sid.strip().upper().startswith("AC"):
        return ("bad-account-sid",
                "TWILIO_ACCOUNT_SID is not an AC SID. The account in the URL "
                "path is half of what authorises the read.")

    return ("ok", "an SK key SID against an AC account SID.")


def verdict(probes, requested_sid=None, returned_sid=None):
    """Turn the probe results into one answer. Pure, so every outcome can be
    exercised without a network.

    probes: {name: (http_status, twilio_code_or_None)} for "account" and, when
    the account read succeeded, the Main-key-only resources.

    Returns (state, detail).
    """
    account = probes.get("account")
    if account is None:
        return ("unknown", "the account resource was never probed.")

    status, code = account

    if status == 403 and code == ACCOUNT_NOT_ACTIVE:
        return ("account-not-active",
                "403 with %d. This is not a permissions problem: the account is "
                "suspended or closed, and no credential change will move it."
                % ACCOUNT_NOT_ACTIVE)

    if status == 401 and code == PERMISSION_DENIED:
        return ("dead-credential",
                "401 with %d on the account resource itself. The key is "
                "deleted, from another account or another region, or the "
                "secret is wrong. Nothing else will read either."
                % PERMISSION_DENIED)

    if status == 401:
        return ("unauthenticated",
                "401 with no %d in the body. Twilio saw no usable credential at "
                "all, which is what a proxy stripping the Authorization header "
                "looks like from this side." % PERMISSION_DENIED)

    if status != 200:
        return ("http-error",
                "%s from the account resource, which is neither an auth answer "
                "nor a healthy one. Retry before drawing conclusions." % status)

    if requested_sid and returned_sid and requested_sid != returned_sid:
        return ("wrong-account",
                "authenticated, but the account read back is %s rather than the "
                "%s you asked for: a parent and a subaccount have been crossed."
                % (returned_sid, requested_sid))

    denied = [name for name in MAIN_KEY_ONLY
              if probes.get(name) and probes[name][0] == 401
              and probes[name][1] == PERMISSION_DENIED]
    if denied:
        return ("scoped-key",
                "the account reads fine, and %s returned %d. That is a Standard "
                "API Key meeting the Main-key boundary, not a broken "
                "credential. Every check in this section works on this key "
                "except the ones that read keys or list accounts."
                % (" and ".join(denied), PERMISSION_DENIED))

    return ("read-ok", "account, keys and accounts all readable with this "
                       "credential.")


def probe(session, url):
    """One GET, reduced to (status, twilio code). Nothing here raises: a 401 is
    the measurement, not an error."""
    r = session.get(url, timeout=30)
    code = None
    try:
        code = r.json().get("code")
    except ValueError:
        pass
    return (r.status_code, code)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--skip-main-key-probes", action="store_true",
                    help="stop after the account read")
    args = ap.parse_args()

    account_sid = os.environ.get("TWILIO_ACCOUNT_SID", "")
    key_sid = os.environ.get("TWILIO_API_KEY", "")
    secret = os.environ.get("TWILIO_API_SECRET", "")

    shape, detail = credential_shape(account_sid, key_sid, secret)
    if shape != "ok":
        log.error("%-16s %s", shape, detail)
        return 2
    log.info("%-16s %s", "shape", detail)

    session = requests.Session()
    session.auth = (key_sid.strip(), secret.strip())

    account_sid = account_sid.strip()
    url = "%s/Accounts/%s.json" % (BASE, account_sid)
    probes = {"account": probe(session, url)}

    returned = None
    if probes["account"][0] == 200:
        returned = session.get(url, timeout=30).json().get("sid")
        if not args.skip_main_key_probes:
            probes["keys"] = probe(
                session, "%s/Accounts/%s/Keys.json" % (BASE, account_sid))
            probes["accounts"] = probe(session, "%s/Accounts.json" % BASE)

    state, detail = verdict(probes, account_sid, returned)
    line = "%-18s %s" % (state, detail)
    if state in ("read-ok", "scoped-key"):
        log.info(line)
        return 0

    log.warning(line)
    if state == "account-not-active":
        log.warning("  repair: Console -> Billing. Read the account status "
                    "before touching any credential.")
    elif state == "wrong-account":
        log.warning("  repair: use the SID of the account this key belongs to "
                    "in the URL path, or issue a key on the account you meant.")
    elif state == "unauthenticated":
        log.warning("  repair: check whether anything between this process and "
                    "api.twilio.com rewrites or drops the Authorization header.")
    else:
        log.warning("  repair: Console -> Account -> API keys & tokens -> "
                    "create a Main API key, and use the SK SID and its secret "
                    "as the basic-auth pair against this account SID.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-read-credential-check.mjs",
"js": '''/**
 * Explain a Twilio 20003: dead credential, crossed SID, or a scope boundary.
 *
 * Read only. GET requests and nothing else. Unlike the other scripts here it
 * does not throw on a 401, because the 401 is the thing being measured.
 */
const HOST = 'https://api.twilio.com';
const BASE = `${HOST}/2010-04-01`;

const PERMISSION_DENIED = 20003;
const ACCOUNT_NOT_ACTIVE = 20005;

// Resources a Standard API Key is not allowed to read. A Main key can; a
// Standard key gets 20003 on both, permanently and by design.
const MAIN_KEY_ONLY = ['keys', 'accounts'];

/**
 * Judge the credential without making a request. Pure. Whitespace and a wrong
 * username are the two causes of 20003 that can be found for free.
 * Returns [state, detail].
 */
export function credentialShape(accountSid, keySid, secret) {
  if (!accountSid || !keySid || !secret) {
    return ['missing',
      'set TWILIO_ACCOUNT_SID, TWILIO_API_KEY and TWILIO_API_SECRET.'];
  }

  for (const [name, value] of [['TWILIO_ACCOUNT_SID', accountSid],
                               ['TWILIO_API_KEY', keySid],
                               ['TWILIO_API_SECRET', secret]]) {
    if (value !== value.trim()) {
      return ['whitespace',
        `${name} has leading or trailing whitespace. A secret with a trailing ` +
        `newline is a different secret, and Twilio answers ${PERMISSION_DENIED} ` +
        'for it.'];
    }
  }

  if (keySid.trim().toUpperCase().startsWith('AC')) {
    return ['auth-token',
      'the username is an account SID, so the password beside it is the ' +
      'account auth token rather than an API key secret.'];
  }

  if (!keySid.trim().toUpperCase().startsWith('SK')) {
    return ['not-a-key',
      'the username is neither an SK API Key SID nor an AC account SID, so ' +
      'nothing on the Twilio side will match it.'];
  }

  if (!accountSid.trim().toUpperCase().startsWith('AC')) {
    return ['bad-account-sid',
      'TWILIO_ACCOUNT_SID is not an AC SID. The account in the URL path is ' +
      'half of what authorises the read.'];
  }

  return ['ok', 'an SK key SID against an AC account SID.'];
}

/**
 * Turn the probe results into one answer. Pure, so every outcome can be
 * exercised without a network. Returns [state, detail].
 */
export function verdict(probes, requestedSid = null, returnedSid = null) {
  const account = probes.account;
  if (!account) return ['unknown', 'the account resource was never probed.'];

  const [status, code] = account;

  if (status === 403 && code === ACCOUNT_NOT_ACTIVE) {
    return ['account-not-active',
      `403 with ${ACCOUNT_NOT_ACTIVE}. This is not a permissions problem: the ` +
      'account is suspended or closed, and no credential change will move it.'];
  }

  if (status === 401 && code === PERMISSION_DENIED) {
    return ['dead-credential',
      `401 with ${PERMISSION_DENIED} on the account resource itself. The key ` +
      'is deleted, from another account or another region, or the secret is ' +
      'wrong. Nothing else will read either.'];
  }

  if (status === 401) {
    return ['unauthenticated',
      `401 with no ${PERMISSION_DENIED} in the body. Twilio saw no usable ` +
      'credential at all, which is what a proxy stripping the Authorization ' +
      'header looks like from this side.'];
  }

  if (status !== 200) {
    return ['http-error',
      `${status} from the account resource, which is neither an auth answer ` +
      'nor a healthy one. Retry before drawing conclusions.'];
  }

  if (requestedSid && returnedSid && requestedSid !== returnedSid) {
    return ['wrong-account',
      `authenticated, but the account read back is ${returnedSid} rather than ` +
      `the ${requestedSid} you asked for: a parent and a subaccount have been ` +
      'crossed.'];
  }

  const denied = MAIN_KEY_ONLY.filter(
    (name) => probes[name] && probes[name][0] === 401
      && probes[name][1] === PERMISSION_DENIED);
  if (denied.length) {
    return ['scoped-key',
      `the account reads fine, and ${denied.join(' and ')} returned ` +
      `${PERMISSION_DENIED}. That is a Standard API Key meeting the Main-key ` +
      'boundary, not a broken credential. Every check in this section works on ' +
      'this key except the ones that read keys or list accounts.'];
  }

  return ['read-ok', 'account, keys and accounts all readable with this credential.'];
}

function authHeader(key, secret) {
  return `Basic ${Buffer.from(`${key}:${secret}`).toString('base64')}`;
}

/** One GET, reduced to [status, twilio code]. Nothing here throws. */
async function probe(auth, url) {
  const res = await fetch(url, { headers: { Authorization: auth } });
  let code = null;
  try {
    code = (await res.json()).code ?? null;
  } catch {
    code = null;
  }
  return [res.status, code];
}

async function main() {
  const accountSid = process.env.TWILIO_ACCOUNT_SID ?? '';
  const keySid = process.env.TWILIO_API_KEY ?? '';
  const secret = process.env.TWILIO_API_SECRET ?? '';

  const [shape, shapeDetail] = credentialShape(accountSid, keySid, secret);
  if (shape !== 'ok') {
    console.error(`${shape.padEnd(16)} ${shapeDetail}`);
    process.exitCode = 2;
    return;
  }
  console.log(`${'shape'.padEnd(16)} ${shapeDetail}`);

  const auth = authHeader(keySid.trim(), secret.trim());
  const sid = accountSid.trim();
  const url = `${BASE}/Accounts/${sid}.json`;
  const probes = { account: await probe(auth, url) };

  let returned = null;
  if (probes.account[0] === 200) {
    const res = await fetch(url, { headers: { Authorization: auth } });
    returned = (await res.json()).sid ?? null;
    if (!process.argv.includes('--skip-main-key-probes')) {
      probes.keys = await probe(auth, `${BASE}/Accounts/${sid}/Keys.json`);
      probes.accounts = await probe(auth, `${BASE}/Accounts.json`);
    }
  }

  const [state, detail] = verdict(probes, sid, returned);
  const line = `${state.padEnd(18)} ${detail}`;
  if (state === 'read-ok' || state === 'scoped-key') {
    console.log(line);
    return;
  }

  console.warn(line);
  if (state === 'account-not-active') {
    console.warn('  repair: Console -> Billing. Read the account status before ' +
                 'touching any credential.');
  } else if (state === 'wrong-account') {
    console.warn('  repair: use the SID of the account this key belongs to in ' +
                 'the URL path, or issue a key on the account you meant.');
  } else if (state === 'unauthenticated') {
    console.warn('  repair: check whether anything between this process and ' +
                 'api.twilio.com rewrites or drops the Authorization header.');
  } else {
    console.warn('  repair: Console -> Account -> API keys & tokens -> create a ' +
                 'Main API key, and use the SK SID and its secret as the ' +
                 'basic-auth pair against this account SID.');
  }
  process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The whole value of this note is one distinction, so that is the pair of cases to pin: <code>20003</code> on the account read is a dead credential, and <code>20003</code> on <code>Keys.json</code> after a successful account read is a Standard key doing what Standard keys do. The <code>403</code> with <code>20005</code> case is here for the same reason it is in the code, because an unhappy status code is not automatically a permissions problem.",
"test_py_file": "test_twilio_read_credential_check.py",
"test_py": '''from twilio_read_credential_check import credential_shape, verdict


def test_20003_on_the_account_read_is_a_dead_credential():
    state, detail = verdict({"account": (401, 20003)})
    assert state == "dead-credential"
    assert "Nothing else will read" in detail


def test_20003_only_on_the_main_key_resources_is_a_boundary_not_a_fault():
    state, detail = verdict({"account": (200, None), "keys": (401, 20003),
                             "accounts": (401, 20003)})
    assert state == "scoped-key"
    assert "not a broken credential" in detail


def test_a_403_with_20005_is_a_suspended_account_not_a_permission_problem():
    state, detail = verdict({"account": (403, 20005)})
    assert state == "account-not-active"
    assert "suspended" in detail


def test_a_401_without_20003_reads_as_a_stripped_header():
    state, detail = verdict({"account": (401, None)})
    assert state == "unauthenticated"
    assert "Authorization header" in detail


def test_a_different_sid_coming_back_is_a_crossed_parent_and_child():
    state, detail = verdict({"account": (200, None)},
                            requested_sid="AC1", returned_sid="AC2")
    assert state == "wrong-account"
    assert "crossed" in detail


def test_everything_readable_passes():
    state, _ = verdict({"account": (200, None), "keys": (200, None),
                        "accounts": (200, None)}, "AC1", "AC1")
    assert state == "read-ok"


def test_a_non_auth_error_is_not_reported_as_a_credential_problem():
    assert verdict({"account": (503, None)})[0] == "http-error"


def test_trailing_whitespace_is_caught_before_any_request():
    state, detail = credential_shape("AC1", "SK1", "secret\\n")
    assert state == "whitespace"
    assert "TWILIO_API_SECRET" in detail


def test_an_account_sid_as_the_username_means_the_auth_token():
    state, _ = credential_shape("AC1", "AC1", "secret")
    assert state == "auth-token"


def test_a_well_formed_pair_passes_the_shape_check():
    assert credential_shape("AC1", "SK1", "secret")[0] == "ok"
''',
"test_js_file": "twilio-read-credential-check.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { credentialShape, verdict } from './twilio-read-credential-check.mjs';

test('20003 on the account read is a dead credential', () => {
  const [state, detail] = verdict({ account: [401, 20003] });
  assert.equal(state, 'dead-credential');
  assert.match(detail, /Nothing else will read/);
});

test('20003 only on the main key resources is a boundary not a fault', () => {
  const [state, detail] = verdict({
    account: [200, null], keys: [401, 20003], accounts: [401, 20003],
  });
  assert.equal(state, 'scoped-key');
  assert.match(detail, /not a broken credential/);
});

test('a 403 with 20005 is a suspended account not a permission problem', () => {
  const [state, detail] = verdict({ account: [403, 20005] });
  assert.equal(state, 'account-not-active');
  assert.match(detail, /suspended/);
});

test('a 401 without 20003 reads as a stripped header', () => {
  const [state, detail] = verdict({ account: [401, null] });
  assert.equal(state, 'unauthenticated');
  assert.match(detail, /Authorization header/);
});

test('a different sid coming back is a crossed parent and child', () => {
  const [state, detail] = verdict({ account: [200, null] }, 'AC1', 'AC2');
  assert.equal(state, 'wrong-account');
  assert.match(detail, /crossed/);
});

test('everything readable passes', () => {
  const [state] = verdict({
    account: [200, null], keys: [200, null], accounts: [200, null],
  }, 'AC1', 'AC1');
  assert.equal(state, 'read-ok');
});

test('a non auth error is not reported as a credential problem', () => {
  assert.equal(verdict({ account: [503, null] })[0], 'http-error');
});

test('trailing whitespace is caught before any request', () => {
  const [state, detail] = credentialShape('AC1', 'SK1', 'secret\\n');
  assert.equal(state, 'whitespace');
  assert.match(detail, /TWILIO_API_SECRET/);
});

test('an account sid as the username means the auth token', () => {
  assert.equal(credentialShape('AC1', 'AC1', 'secret')[0], 'auth-token');
});

test('a well formed pair passes the shape check', () => {
  assert.equal(credentialShape('AC1', 'SK1', 'secret')[0], 'ok');
});
''',
"faq": [
 ("Which resources can a read-only key legitimately not see?",
  "The two that need a Main API Key: the key list at Accounts/{AccountSid}/Keys.json and the account list at Accounts.json. A Standard key gets 20003 on both, always, and no amount of rotation changes that. Everything else the scripts in this section read - phone numbers, messages, calls, Messaging Services, Verify services, alerts, usage - is readable on a Standard key. A key's own secret is also unreadable after creation, by anyone, including a Main key."),
 ("How do I tell a scope boundary from a broken key without guessing?",
  "By probing in order. Read the account resource first, because it is the narrowest thing the credential could possibly be allowed to read. If that succeeds, the credential is alive and correctly scoped to that account, so any 20003 further out is a boundary. If it fails with 20003, nothing else is worth trying."),
 ("The key works locally and 20003s in production. Same key, same SID.",
  "Then something is changing the request between your process and Twilio, and the usual suspect is an egress proxy or service mesh that drops or rewrites the Authorization header. That produces a 401 whose body has no 20003 in it, because Twilio saw no credential rather than a bad one. The other candidate is the secret arriving with a newline from whatever injected it, which is why the script checks for whitespace before it makes a request."),
 ("Why does the script compare the SID it sent with the SID it got back?",
  "Because a subaccount key against a parent SID, or the reverse, authenticates and then reads the wrong thing or nothing at all. The response body carries sid and owner_account_sid, so the comparison is free, and it catches a class of mistake that otherwise looks exactly like a permissions problem in a multi-tenant setup."),
 ("Is 403 with 20005 the same problem in a different colour?",
  "No, and conflating them costs time during an outage. 20003 is about who you are; 20005 is about whether the account is allowed to do anything at all. A suspended or closed account returns 20005 to a perfectly good credential, and the repair is billing or a support ticket rather than a new key."),
],
"related": [
 ("/twilio/auth-token-used-instead-of-api-key/", "No API keys exist, so the auth token is the credential"),
 ("/twilio/stale-or-orphaned-api-keys/", "Years-old API keys still live with nobody owning them"),
 ("/twilio/account-suspended-or-closed/", "The account itself is suspended or closed"),
],
"citations": [CITE_20003, CITE_KEYS, CITE_KEY_RESOURCE, CITE_ACCOUNT],
},

]
