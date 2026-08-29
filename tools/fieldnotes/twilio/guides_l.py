#!/usr/bin/env python3
"""/twilio/ field notes, batch L — the writing.

Four failures in the plumbing that carries events around a Twilio account: a
Studio Flow whose edits are live nowhere, a published Flow no number points at,
a conversation-scoped webhook with no URL behind it, and an Event Streams sink
that stopped delivering without a single message or call changing. Read-only
throughout: an API Key with read access, never the account auth token, and the
repair is printed for a human to run.
"""

CITE_FLOW = ("Studio Flow resource (v2) — Twilio Docs",
             "https://www.twilio.com/docs/studio/rest-api/v2/flow")
CITE_EXEC = ("Studio Execution resource (v2) — Twilio Docs",
             "https://www.twilio.com/docs/studio/rest-api/v2/execution")
CITE_STUDIO_FAQ = ("Studio FAQ — Twilio Docs",
                   "https://www.twilio.com/docs/studio/user-guide/studio-faq")
CITE_NUMBER = ("IncomingPhoneNumber resource — Twilio Docs",
               "https://www.twilio.com/docs/phone-numbers/api/incomingphonenumber-resource")
CITE_CONV_HOOK = ("Conversation-scoped webhook resource — Twilio Docs",
                  "https://www.twilio.com/docs/conversations/api/conversation-scoped-webhook-resource")
CITE_50369 = ("Error 50369: conversation webhook URL not provided — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/50369")
CITE_CONV_HOOKS = ("Conversations webhooks — Twilio Docs",
                   "https://www.twilio.com/docs/conversations/conversations-webhooks")
CITE_ALERTS = ("Monitor Alert resource — Twilio Docs",
               "https://www.twilio.com/docs/usage/monitor-alert")
CITE_SINK = ("Event Streams Sink resource — Twilio Docs",
             "https://www.twilio.com/docs/events/event-streams/sink-resource")
CITE_SUB = ("Event Streams Subscription resource — Twilio Docs",
            "https://www.twilio.com/docs/events/event-streams/subscription-resource")
CITE_DELIVERY = ("Event delivery and duplication — Twilio Docs",
                 "https://www.twilio.com/docs/events/event-delivery-and-duplication")

GUIDES = [

{
"slug": "studio-flow-draft-not-published",
"title": "A Studio Flow left in draft, so your edits are live nowhere",
"description": "Studio keeps a published revision and a draft. The Console shows the draft; a number pointed at the Flow runs the published one. Your change is live nowhere.",
"h1": "a Studio Flow left in draft, so your edits are live nowhere",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio studio flow draft", "studio flow not published",
             "twilio studio publish flow", "studio flow revision",
             "twilio studio changes not taking effect"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Someone opened the Flow, moved a widget, changed the greeting, saved, and tested it from their own handset. It worked. Two weeks later a customer quotes the <em>old</em> greeting back at you. Nothing failed, nothing was rolled back, and the Console still shows the new version exactly as it was left &mdash; because the Console shows the draft, and every real caller is running the last revision somebody pressed Publish on.",
"short_answer": """<p>Read <code>GET https://studio.twilio.com/v2/Flows</code> and flag any flow whose <code>status</code> is <code>draft</code>. Then read <code>GET https://studio.twilio.com/v2/Flows/{FlowSid}/Executions</code>: a draft flow that is still taking executions is the bad case, because live traffic is running an older definition than the one on screen.</p>
<p>Publishing is a separate act from saving. Saving raises <code>revision</code>; only Publish moves the definition that inbound calls and messages actually execute, and only phone numbers listed under <strong>TEST USERS</strong> ever see the draft.</p>""",
"problem": """<p>Studio has two definitions per Flow and one canvas to show them in. The canvas shows the draft. The runtime uses the last published revision. There is no banner in the Console that a caller ever sees, no failed request, no alert &mdash; a Flow in draft is not broken, it is simply not the thing running.</p>
<p>The shape this takes in practice is a change that seems to work for exactly one person. Whoever made the edit tested it from a handset that is in the Flow's TEST USERS list, saw the new behaviour, and closed the tab. Everyone else got the old behaviour, and will keep getting it until someone presses Publish. Weeks later the bug report arrives describing a message nobody can find in the code, because it is not in the code: it is in a revision of a Flow that has not moved since March.</p>""",
"why": """<p><strong>Save and Publish are different operations.</strong> The REST equivalent is the <code>Status</code> parameter on the Flow: a flow can be updated with <code>Status=draft</code> any number of times, incrementing <code>revision</code> each time, and none of those revisions is served to anybody. The Console's Save button does the same thing the API does.</p>
<p><strong>The draft is reachable, which is why it fools people.</strong> Numbers added to TEST USERS execute the draft rather than the published revision. That is the feature working as designed, and it is also the reason the person who made the change is the least likely person in the company to notice that it never shipped.</p>
<p><strong>Nothing in the message or call logs changes.</strong> Executions run, widgets fire, the number answers. The Debugger stays quiet because there is no error: the published revision is valid and it does what it always did. There is no error code for this note to give you, which is exactly why it needs a script.</p>
<p><strong>The API will not tell you which revision is live.</strong> <code>revision</code> on the Flow resource counts every saved revision, published or not. A flow reading <code>draft</code> at revision 12 has an earlier published revision serving traffic, and the number of that revision is not a field you can read back. What the script can tell you &mdash; definitively &mdash; is that the definition on screen is not the definition running.</p>""",
"steps": [
 {"h": "List the Flows and read status, not the canvas",
  "body": """<p><code>GET https://studio.twilio.com/v2/Flows?PageSize=50</code>, following <code>meta.next_page_url</code>. The field that matters is <code>status</code>: <code>draft</code> or <code>published</code>. <code>friendly_name</code> and <code>date_updated</code> are for the human reading the report; <code>status</code> is the finding.</p>"""},
 {"h": "Separate never-published from published-then-edited",
  "body": """<p>A draft flow at <code>revision</code> 1 has never been published at all: a number pointed at it has nothing to run. A draft flow at a higher revision has an older published definition still serving traffic, which is the quieter and more common failure. The two need different sentences in a report because they need different reactions.</p>"""},
 {"h": "Ask whether the Flow is carrying live traffic",
  "body": """<p><code>GET https://studio.twilio.com/v2/Flows/{FlowSid}/Executions?PageSize=20</code>. Executions on a draft flow are the proof that this is not a scratch Flow somebody abandoned &mdash; real conversations are running through it, and they are running the definition you cannot see on screen.</p>"""},
 {"h": "Check valid before you blame the publish step",
  "body": """<p><code>valid</code> is <code>false</code> when the definition itself will not compile: a transition to a deleted widget, broken Liquid, a required field left empty. Publishing that flow is not the repair and will not succeed. Read <code>errors[]</code> on <code>GET https://studio.twilio.com/v2/Flows/{FlowSid}</code> first; each entry names the widget <code>path</code>.</p>"""},
 {"h": "Publish deliberately, and keep the check on a schedule",
  "body": """<p>The repair is Console &rarr; Studio &rarr; open the Flow &rarr; Publish, or the REST update with <code>Status=published</code> and a <code>CommitMessage</code> you will thank yourself for later. Then leave this script on a schedule: the failure is not a one-time mistake, it recurs every time someone edits a Flow at the end of a day.</p>"""},
],
"verify": """<p>Re-run after publishing. Every flow that carries traffic should report <code>published</code>, and the only drafts left should be ones nobody has pointed a number at.</p>
<pre><code class="language-bash">python3 twilio_studio_draft_audit.py
# 7 flow(s), 0 running a definition older than the one on screen</code></pre>""",
"code_intro": "Two read-only surfaces &mdash; the Flows list and, for each draft, one page of its Executions &mdash; and an API Key with read access, which is all the script can use. The pure part is the classifier, because the judgement here is entirely about which of four situations a draft flow is in, and that distinction is worth reading in one place rather than inferring from a log line.",
"py_file": "twilio_studio_draft_audit.py",
"py": '''"""Report Twilio Studio Flows whose live definition is not the one on screen.

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. The repair is printed, never performed,
because this script holds a credential to an account that can send messages and
spend money.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_studio_draft_audit")

STUDIO = "https://studio.twilio.com/v2"


def execution_stats(executions):
    """Summarise one Flow's executions. Pure, so the report can be tested.

    Only two things are being asked: is anything running through this Flow at
    all, and how recently. Execution status is `active` or `ended`; an ended
    execution still counts as traffic, because it ran a definition.
    """
    total = 0
    active = 0
    latest = None
    for ex in executions or []:
        total += 1
        if str(ex.get("status") or "").lower() == "active":
            active += 1
        created = str(ex.get("date_created") or "")
        if created and (latest is None or created > latest):
            latest = created
    return {"total": total, "active": active, "latest": latest}


def verdict(flow, stats=None):
    """Classify one Studio Flow. Pure, so the four cases are visible together
    rather than spread across a request loop.

    Returns (state, detail).
    """
    stats = stats or {"total": 0, "active": 0, "latest": None}
    status = str(flow.get("status") or "").lower()
    revision = int(flow.get("revision") or 0)
    total = int(stats.get("total") or 0)

    # An invalid definition cannot be published, so saying "press Publish" is
    # wrong advice: the widget errors have to be fixed first.
    if flow.get("valid") is False:
        return ("invalid",
                "definition does not compile, so publishing it is not possible. "
                "Read errors[] on the single-flow fetch: each entry names the "
                "widget path that broke.")

    if status == "published":
        return ("published",
                "revision %d is published and is what inbound traffic runs." % revision)

    if revision <= 1:
        return ("never-published",
                "revision %d and still a draft: this Flow has never been "
                "published, so a number pointed at it has no definition to run. "
                "Only TEST USERS reach the draft." % revision)

    if total:
        return ("draft-over-traffic",
                "draft at revision %d with %d execution(s) seen (%d active, "
                "latest %s). Live traffic is running an earlier published "
                "revision, not the definition in the Console."
                % (revision, total, int(stats.get("active") or 0),
                   stats.get("latest") or "unknown"))

    return ("draft",
            "draft at revision %d with no executions in the page read. The saved "
            "edits are live nowhere; whoever made them sees them because the "
            "Console shows the draft." % revision)


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def paged(session, url, key, limit):
    params = {"PageSize": 50}
    out = []
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get(key, []))
        url = (page.get("meta") or {}).get("next_page_url")
        params = {}
    return out[:limit]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-flows", type=int, default=200,
                    help="stop paging after this many Studio Flows")
    ap.add_argument("--executions", type=int, default=20,
                    help="how many executions to read per draft flow")
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

    flows = paged(session, "%s/Flows" % STUDIO, "flows", args.max_flows)
    if not flows:
        log.info("no Studio Flows on this account")
        return 0

    bad = 0
    for flow in flows:
        stats = None
        if str(flow.get("status") or "").lower() != "published":
            executions = paged(session, "%s/Flows/%s/Executions"
                               % (STUDIO, flow.get("sid")), "executions",
                               args.executions)
            stats = execution_stats(executions)

        state, detail = verdict(flow, stats)
        line = "%-18s %s (%s)  %s" % (state, flow.get("sid"),
                                      flow.get("friendly_name", "?"), detail)
        if state == "published":
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        if state == "invalid":
            log.warning("  repair: fix the widget at each errors[].path, validate "
                        "the definition, then publish. GET %s/Flows/%s to read "
                        "errors[] and warnings[].", STUDIO, flow.get("sid"))
            continue
        log.warning("  repair: Console -> Studio -> open %s -> Publish, or update "
                    "%s/Flows/%s with Status=published and a CommitMessage. "
                    "Saving is not publishing.",
                    flow.get("friendly_name", flow.get("sid")), STUDIO,
                    flow.get("sid"))

    log.info("%d flow(s), %d running a definition older than the one on screen",
             len(flows), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-studio-draft-audit.mjs",
"js": '''/**
 * Report Twilio Studio Flows whose live definition is not the one on screen.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const STUDIO = 'https://studio.twilio.com/v2';

/**
 * Summarise one Flow's executions. Pure, so the report can be tested. Only two
 * things are being asked: is anything running through this Flow at all, and how
 * recently. An ended execution still counts as traffic, because it ran a
 * definition.
 */
export function executionStats(executions) {
  let total = 0;
  let active = 0;
  let latest = null;
  for (const ex of executions ?? []) {
    total += 1;
    if (String(ex.status ?? '').toLowerCase() === 'active') active += 1;
    const created = String(ex.date_created ?? '');
    if (created && (latest === null || created > latest)) latest = created;
  }
  return { total, active, latest };
}

/**
 * Classify one Studio Flow. Pure, so the four cases are visible together rather
 * than spread across a request loop. Returns [state, detail].
 */
export function verdict(flow, stats = { total: 0, active: 0, latest: null }) {
  const status = String(flow.status ?? '').toLowerCase();
  const revision = Number(flow.revision ?? 0);
  const total = Number(stats.total ?? 0);

  // An invalid definition cannot be published, so saying "press Publish" is
  // wrong advice: the widget errors have to be fixed first.
  if (flow.valid === false) {
    return ['invalid',
      'definition does not compile, so publishing it is not possible. Read ' +
      'errors[] on the single-flow fetch: each entry names the widget path that broke.'];
  }

  if (status === 'published') {
    return ['published',
      `revision ${revision} is published and is what inbound traffic runs.`];
  }

  if (revision <= 1) {
    return ['never-published',
      `revision ${revision} and still a draft: this Flow has never been published, ` +
      'so a number pointed at it has no definition to run. Only TEST USERS reach the draft.'];
  }

  if (total) {
    return ['draft-over-traffic',
      `draft at revision ${revision} with ${total} execution(s) seen ` +
      `(${Number(stats.active ?? 0)} active, latest ${stats.latest ?? 'unknown'}). ` +
      'Live traffic is running an earlier published revision, not the definition ' +
      'in the Console.'];
  }

  return ['draft',
    `draft at revision ${revision} with no executions in the page read. The saved ` +
    'edits are live nowhere; whoever made them sees them because the Console shows ' +
    'the draft.'];
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

export async function paged(auth, url, key, limit = 200) {
  let next = url;
  let params = { PageSize: 50 };
  const out = [];
  while (next && out.length < limit) {
    const page = await get(auth, next, params);
    out.push(...(page[key] ?? []));
    next = page.meta?.next_page_url ?? null;
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

  const flows = await paged(auth, `${STUDIO}/Flows`, 'flows');
  if (flows.length === 0) {
    console.log('no Studio Flows on this account');
    return;
  }

  let bad = 0;
  for (const flow of flows) {
    let stats;
    if (String(flow.status ?? '').toLowerCase() !== 'published') {
      const executions = await paged(auth, `${STUDIO}/Flows/${flow.sid}/Executions`,
                                     'executions', 20);
      stats = executionStats(executions);
    }
    const [state, detail] = verdict(flow, stats);
    const line = `${state.padEnd(18)} ${flow.sid} (${flow.friendly_name ?? '?'})  ${detail}`;
    if (state === 'published') { console.log(line); continue; }
    bad += 1;
    console.warn(line);
    if (state === 'invalid') {
      console.warn('  repair: fix the widget at each errors[].path, validate the ' +
                   `definition, then publish. GET ${STUDIO}/Flows/${flow.sid} to ` +
                   'read errors[] and warnings[].');
      continue;
    }
    console.warn(`  repair: Console -> Studio -> open ${flow.friendly_name ?? flow.sid}` +
                 ` -> Publish, or update ${STUDIO}/Flows/${flow.sid} with ` +
                 'Status=published and a CommitMessage. Saving is not publishing.');
  }

  console.log(`${flows.length} flow(s), ${bad} running a definition older than the ` +
              'one on screen');
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The tests pin down the distinctions that make this report worth reading. A draft with executions is a different sentence from a draft without any, because one of them is an outage and the other is a scratch Flow. Revision 1 in draft has never been published at all. And an invalid definition never gets told to press Publish, because pressing it will not work.",
"test_py_file": "test_twilio_studio_draft_audit.py",
"test_py": '''from twilio_studio_draft_audit import execution_stats, verdict


def flow(status="draft", revision=4, valid=True, sid="FW1"):
    return {"sid": sid, "friendly_name": "Support IVR", "status": status,
            "revision": revision, "valid": valid}


def execution(status="ended", created="2026-08-01T10:00:00Z"):
    return {"sid": "FN1", "status": status, "date_created": created}


def test_execution_stats_counts_traffic_and_keeps_the_latest_date():
    stats = execution_stats([
        execution("ended", "2026-08-01T10:00:00Z"),
        execution("active", "2026-08-03T09:00:00Z"),
        execution("ended", "2026-08-02T11:00:00Z"),
    ])
    assert stats == {"total": 3, "active": 1, "latest": "2026-08-03T09:00:00Z"}


def test_execution_stats_on_nothing_is_zero_not_an_error():
    assert execution_stats([]) == {"total": 0, "active": 0, "latest": None}
    assert execution_stats(None) == {"total": 0, "active": 0, "latest": None}


def test_a_published_flow_is_the_one_that_runs():
    state, detail = verdict(flow(status="published", revision=9))
    assert state == "published"
    assert "revision 9" in detail


def test_a_draft_with_executions_is_the_outage():
    state, detail = verdict(flow(revision=12),
                            {"total": 40, "active": 2, "latest": "2026-08-28T07:00:00Z"})
    assert state == "draft-over-traffic"
    assert "earlier published revision" in detail
    assert "2026-08-28T07:00:00Z" in detail


def test_a_draft_with_no_traffic_is_quieter_but_still_flagged():
    state, detail = verdict(flow(revision=12), {"total": 0, "active": 0, "latest": None})
    assert state == "draft"
    assert "live nowhere" in detail


def test_revision_one_in_draft_has_never_been_published():
    # There is no earlier published definition to fall back to, so a number
    # pointed at this Flow has nothing at all to execute.
    state, detail = verdict(flow(revision=1), {"total": 0, "active": 0, "latest": None})
    assert state == "never-published"
    assert "TEST USERS" in detail


def test_an_invalid_definition_is_not_told_to_press_publish():
    state, detail = verdict(flow(valid=False, revision=6), {"total": 5, "active": 0,
                                                            "latest": None})
    assert state == "invalid"
    assert "errors[]" in detail
    assert "Publish" not in detail


def test_a_missing_stats_argument_still_classifies():
    assert verdict(flow(revision=3))[0] == "draft"
''',
"test_js_file": "twilio-studio-draft-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { executionStats, verdict } from './twilio-studio-draft-audit.mjs';

const flow = ({ status = 'draft', revision = 4, valid = true } = {}) => ({
  sid: 'FW1', friendly_name: 'Support IVR', status, revision, valid,
});

const execution = (status = 'ended', created = '2026-08-01T10:00:00Z') => ({
  sid: 'FN1', status, date_created: created,
});

test('execution stats counts traffic and keeps the latest date', () => {
  const stats = executionStats([
    execution('ended', '2026-08-01T10:00:00Z'),
    execution('active', '2026-08-03T09:00:00Z'),
    execution('ended', '2026-08-02T11:00:00Z'),
  ]);
  assert.deepEqual(stats, { total: 3, active: 1, latest: '2026-08-03T09:00:00Z' });
});

test('execution stats on nothing is zero, not an error', () => {
  assert.deepEqual(executionStats([]), { total: 0, active: 0, latest: null });
  assert.deepEqual(executionStats(null), { total: 0, active: 0, latest: null });
});

test('a published flow is the one that runs', () => {
  const [state, detail] = verdict(flow({ status: 'published', revision: 9 }));
  assert.equal(state, 'published');
  assert.match(detail, /revision 9/);
});

test('a draft with executions is the outage', () => {
  const [state, detail] = verdict(flow({ revision: 12 }),
    { total: 40, active: 2, latest: '2026-08-28T07:00:00Z' });
  assert.equal(state, 'draft-over-traffic');
  assert.match(detail, /earlier published revision/);
  assert.match(detail, /2026-08-28T07:00:00Z/);
});

test('a draft with no traffic is quieter but still flagged', () => {
  const [state, detail] = verdict(flow({ revision: 12 }),
    { total: 0, active: 0, latest: null });
  assert.equal(state, 'draft');
  assert.match(detail, /live nowhere/);
});

test('revision one in draft has never been published', () => {
  const [state, detail] = verdict(flow({ revision: 1 }),
    { total: 0, active: 0, latest: null });
  assert.equal(state, 'never-published');
  assert.match(detail, /TEST USERS/);
});

test('an invalid definition is not told to press Publish', () => {
  const [state, detail] = verdict(flow({ valid: false, revision: 6 }),
    { total: 5, active: 0, latest: null });
  assert.equal(state, 'invalid');
  assert.match(detail, /errors\\[\\]/);
  assert.ok(!/Publish/.test(detail));
});

test('a missing stats argument still classifies', () => {
  assert.equal(verdict(flow({ revision: 3 }))[0], 'draft');
});
''',
"faq": [
 ("Why does the Console show my change if it is not live?",
  "Because the Studio canvas renders the draft, which is the working copy you last saved. The runtime executes the most recent published revision. Both exist at once, the canvas only ever shows one of them, and there is no marker on a call or message that tells you which definition served it."),
 ("Why did it work when I tested it?",
  "Phone numbers listed under TEST USERS on the Flow execute the draft rather than the published revision. The person who made the edit is usually the person on that list, so the change works for exactly one handset in the company and for nobody else."),
 ("Can the script tell me which revision is actually serving traffic?",
  "No, and neither can the API. The Flow resource reports the current revision number and its status; there is no field that names the revision the runtime is executing. What the script establishes is the thing that matters: that the current definition is a draft, so whatever is running is older than what you are looking at."),
 ("Is a draft Flow always a problem?",
  "No. A Flow nobody has wired up and nobody executes is just work in progress, which is why the script reports that case in a quieter state. A draft that is taking executions is the one to act on, because real conversations are running a definition no one on the team has read recently."),
 ("Why not just publish everything the script finds?",
  "Because a draft can be a half-finished edit, and because a Flow whose valid field is false cannot be published at all. The script prints the repair and stops there: it holds a read-only credential on an account that answers real calls, and publishing a Flow changes what those callers hear."),
],
"related": [
 ("/twilio/studio-flow-not-wired-to-number/", "A published Flow no number points at"),
 ("/twilio/phone-number-still-on-demo-twiml/", "A number still on Twilio's demo TwiML"),
 ("/twilio/inbound-webhook-black-hole/", "Inbound SMS into a number with no sms_url"),
],
"citations": [CITE_FLOW, CITE_EXEC, CITE_STUDIO_FAQ, CITE_ALERTS],
},


{
"slug": "studio-flow-not-wired-to-number",
"title": "A published Studio Flow that no phone number points at",
"description": "Publishing a Flow does not attach it to anything. The Flow has zero executions while inbound calls and SMS still hit the old webhook, or Twilio's demo TwiML.",
"h1": "a published Studio Flow that no phone number points at",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio studio flow not triggering", "studio flow zero executions",
             "attach studio flow to phone number", "twilio studio webhook url",
             "studio flow no incoming calls"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The Flow is built, published, and correct. Its Executions tab is empty, and it has been empty since the day it was created. Meanwhile the support line still plays whatever it played last year, because publishing a Flow tells Studio the definition is live &mdash; it does not tell a single phone number to send anything to it.",
"short_answer": """<p>Read <code>GET https://studio.twilio.com/v2/Flows</code>, then <code>GET /2010-04-01/Accounts/{AccountSid}/IncomingPhoneNumbers.json?PageSize=1000</code>, and look for any number whose <code>voice_url</code> or <code>sms_url</code> contains the <code>FlowSid</code>. The Studio webhook takes the form <code>https://webhooks.twilio.com/v1/Accounts/{AccountSid}/Flows/{FlowSid}</code>, so the SID is a plain substring match.</p>
<p>Corroborate with <code>GET https://studio.twilio.com/v2/Flows/{FlowSid}/Executions?PageSize=1</code>. No number pointing at it <em>and</em> no executions is a Flow that has never run; no number but executions present means something else triggers it, and that is a different, healthier answer.</p>""",
"problem": """<p>Publishing is a Studio-side act. Routing is a phone-number-side act. Nothing in the Console forces you to do the second after the first, and the two live in different sections behind different menus, so a Flow can be finished, reviewed, approved and entirely disconnected.</p>
<p>What makes it survive is that both halves look right in isolation. The Flow page shows a published Flow. The number's configuration page shows a URL that resolves and returns TwiML. Nobody compares them, because comparing them means holding a 34-character SID in your head while you switch pages. The customer-facing symptom is the absence of a change: the new IVR simply never appears, and there is no failure anywhere to investigate.</p>""",
"why": """<p><strong>The attachment is a URL on the number, not a reference to the Flow.</strong> A number runs a Studio Flow because its <code>voice_url</code> or <code>sms_url</code> happens to be the Studio webhook for that <code>FlowSid</code>. Change the Flow and the URL still points at it; delete the Flow and the URL points at nothing. There is no foreign key here and nothing enforces the relationship.</p>
<p><strong>Zero executions is ambiguous on its own.</strong> Flows are also started by the REST Executions API, by a Trigger widget in another Flow, and by a Messaging Service whose inbound request URL is the Studio webhook. An empty Executions list plus no number is a dead Flow; executions with no number means the entry point is somewhere the phone number list cannot see.</p>
<p><strong>A number can point at an Application SID instead.</strong> When <code>voice_application_sid</code> is set, the number's own <code>voice_url</code> is ignored and the TwiML App's URL is used, which may itself be the Studio webhook. A scan that only reads the number's URLs will report a wired Flow as an orphan, so the report has to say which fields it looked at.</p>
<p><strong>Nothing errors.</strong> The old webhook keeps answering. Twilio's demo TwiML keeps answering. The Debugger stays empty because a working webhook that returns the wrong greeting is not an error condition, and the only signal available is a Flow with no traffic.</p>""",
"steps": [
 {"h": "List the published Flows",
  "body": """<p><code>GET https://studio.twilio.com/v2/Flows?PageSize=50</code>, following <code>meta.next_page_url</code>. A flow still in <code>draft</code> is a different note: it has no published definition for a number to run, so wiring it up would not help until somebody publishes.</p>"""},
 {"h": "List every incoming number once",
  "body": """<p><code>GET /2010-04-01/Accounts/{AccountSid}/IncomingPhoneNumbers.json?PageSize=1000</code>, following <code>next_page_uri</code>. Read the whole list a single time and match every Flow against it in memory; a per-Flow search of the numbers list is the same answer for many times the requests.</p>"""},
 {"h": "Match on the SID inside the URL",
  "body": """<p>Test whether <code>voice_url</code> or <code>sms_url</code> contains the <code>FlowSid</code>. That is a deliberate substring test rather than an equality test against a constructed webhook URL, because the URL can legitimately carry a query string, and building the expected string by hand is how a scan reports every Flow as unwired.</p>"""},
 {"h": "Ask the Flow whether it has ever run",
  "body": """<p><code>GET https://studio.twilio.com/v2/Flows/{FlowSid}/Executions?PageSize=1</code>. One page is enough: the question is existence, not volume. Executions with no attached number tell you the Flow is triggered by the REST API, another Flow's Trigger widget, or a Messaging Service, and that it is not the orphan it looks like.</p>"""},
 {"h": "Attach the number, then confirm with a real call",
  "body": """<p>The repair is a number update setting <code>SmsUrl</code> or <code>VoiceUrl</code> to <code>https://webhooks.twilio.com/v1/Accounts/{AccountSid}/Flows/{FlowSid}</code> with the method set to POST, or assigning the number to the Flow in the Console. Then dial it. A Flow whose first execution appears in the list is wired; a Flow you believe is wired is not evidence of anything.</p>"""},
],
"verify": """<p>Re-run after attaching the numbers. Every Flow that is meant to answer a line should report <code>wired</code>, and anything left in <code>orphan</code> should be a Flow you no longer need.</p>
<pre><code class="language-bash">python3 twilio_studio_wiring_audit.py
# 6 published flow(s), 0 with no entry point at all</code></pre>""",
"code_intro": "Two lists read once each &mdash; Studio Flows and incoming phone numbers &mdash; plus one page of executions per Flow, on an API Key with read access. Both pure functions matter here: the matcher decides what counts as an attachment, and the classifier keeps apart the Flow that nothing can reach and the Flow that is reached from somewhere this scan cannot see.",
"py_file": "twilio_studio_wiring_audit.py",
"py": '''"""Report published Twilio Studio Flows that no phone number points at.

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. The repair is printed, never performed,
because this script holds a credential to an account that can send messages and
spend money.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_studio_wiring_audit")

HOST = "https://api.twilio.com"
BASE = HOST + "/2010-04-01"
STUDIO = "https://studio.twilio.com/v2"


def attachments(flow_sid, numbers):
    """Find the numbers whose voice or SMS webhook runs this Flow. Pure.

    The attachment is a URL, not a reference: a number runs a Flow because its
    voice_url or sms_url is the Studio webhook for that FlowSid. Matched as a
    substring, because the URL can carry a query string and reconstructing the
    exact expected string is how a scan reports every Flow as unwired.

    Numbers whose voice_application_sid is set are collected separately: their
    voice_url is ignored at runtime, so this scan cannot answer for them.
    """
    out = {"voice": [], "sms": [], "via_application": []}
    if not flow_sid:
        return out
    for n in numbers or []:
        label = n.get("phone_number") or n.get("sid") or "?"
        if flow_sid in str(n.get("voice_url") or ""):
            out["voice"].append(label)
        if flow_sid in str(n.get("sms_url") or ""):
            out["sms"].append(label)
        if str(n.get("voice_application_sid") or "").strip():
            out["via_application"].append(label)
    return out


def verdict(flow, attach=None, executions=0):
    """Classify one published Flow's entry point. Pure, so the difference
    between "nothing can reach it" and "something reaches it from elsewhere"
    is written down rather than inferred.

    Returns (state, detail).
    """
    attach = attach or {"voice": [], "sms": [], "via_application": []}
    status = str(flow.get("status") or "").lower()
    wired = list(attach.get("voice") or []) + list(attach.get("sms") or [])
    executions = int(executions or 0)

    if status != "published":
        return ("unpublished",
                "status is %s, so there is no published definition for a number "
                "to run. Publish first; wiring a draft changes nothing."
                % (status or "unknown"))

    if wired and executions:
        return ("wired", "reached from %s and running: %d execution(s) seen."
                % (", ".join(sorted(set(wired))), executions))

    if wired:
        return ("wired-idle",
                "attached to %s but no executions in the page read. Wired and "
                "untested, or wired to a line nobody calls."
                % ", ".join(sorted(set(wired))))

    if executions:
        return ("triggered-elsewhere",
                "no number points at it, but %d execution(s) exist: started by "
                "the REST Executions API, a Trigger widget in another Flow, or a "
                "Messaging Service inbound request URL." % executions)

    apps = attach.get("via_application") or []
    hint = ("" if not apps else
            " %d number(s) on this account use voice_application_sid, whose URL "
            "this scan does not follow." % len(apps))
    return ("orphan",
            "published, no number's voice_url or sms_url contains this FlowSid, "
            "and no executions. Inbound traffic is still going wherever it went "
            "before.%s" % hint)


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def paged_v2(session, url, key, limit):
    params = {"PageSize": 50}
    out = []
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get(key, []))
        url = (page.get("meta") or {}).get("next_page_url")
        params = {}
    return out[:limit]


def list_numbers(session, account, limit):
    """The 2010-04-01 API pages with next_page_uri rather than meta, so this
    cannot share the v2 pager above."""
    url = "%s/Accounts/%s/IncomingPhoneNumbers.json" % (BASE, account)
    params = {"PageSize": 1000}
    out = []
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get("incoming_phone_numbers", []))
        nxt = page.get("next_page_uri")
        url, params = (HOST + nxt) if nxt else None, {}
    return out[:limit]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-flows", type=int, default=200,
                    help="stop paging after this many Studio Flows")
    ap.add_argument("--max-numbers", type=int, default=5000,
                    help="stop paging after this many phone numbers")
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

    flows = paged_v2(session, "%s/Flows" % STUDIO, "flows", args.max_flows)
    if not flows:
        log.info("no Studio Flows on this account")
        return 0

    numbers = list_numbers(session, account, args.max_numbers)
    log.info("%d flow(s), %d number(s) read", len(flows), len(numbers))

    bad = 0
    for flow in flows:
        sid = flow.get("sid")
        attach = attachments(sid, numbers)
        executions = 0
        if not (attach["voice"] or attach["sms"]):
            executions = len(paged_v2(session, "%s/Flows/%s/Executions"
                                      % (STUDIO, sid), "executions", 1))

        state, detail = verdict(flow, attach, executions)
        line = "%-20s %s (%s)  %s" % (state, sid, flow.get("friendly_name", "?"),
                                      detail)
        if state in ("wired", "triggered-elsewhere"):
            log.info(line)
            continue
        if state == "wired-idle":
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        if state == "unpublished":
            log.warning("  repair: publish the Flow, then attach a number to it.")
            continue
        log.warning("  repair: update %s/Accounts/%s/IncomingPhoneNumbers/{PNSid}"
                    ".json with SmsUrl=https://webhooks.twilio.com/v1/Accounts/%s/"
                    "Flows/%s and SmsMethod=POST (or the VoiceUrl equivalent), or "
                    "assign the number in Console -> Studio -> the Flow.",
                    BASE, account, account, sid)

    log.info("%d published flow(s), %d with no entry point at all",
             sum(1 for f in flows if str(f.get("status") or "") == "published"), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-studio-wiring-audit.mjs",
"js": '''/**
 * Report published Twilio Studio Flows that no phone number points at.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const HOST = 'https://api.twilio.com';
const BASE = `${HOST}/2010-04-01`;
const STUDIO = 'https://studio.twilio.com/v2';

/**
 * Find the numbers whose voice or SMS webhook runs this Flow. Pure.
 *
 * The attachment is a URL, not a reference. Matched as a substring, because the
 * URL can carry a query string and reconstructing the exact expected string is
 * how a scan reports every Flow as unwired. Numbers with voice_application_sid
 * are collected separately: their voice_url is ignored at runtime.
 */
export function attachments(flowSid, numbers) {
  const out = { voice: [], sms: [], via_application: [] };
  if (!flowSid) return out;
  for (const n of numbers ?? []) {
    const label = n.phone_number || n.sid || '?';
    if (String(n.voice_url ?? '').includes(flowSid)) out.voice.push(label);
    if (String(n.sms_url ?? '').includes(flowSid)) out.sms.push(label);
    if (String(n.voice_application_sid ?? '').trim()) out.via_application.push(label);
  }
  return out;
}

/**
 * Classify one published Flow's entry point. Pure, so the difference between
 * "nothing can reach it" and "something reaches it from elsewhere" is written
 * down rather than inferred. Returns [state, detail].
 */
export function verdict(flow, attach = { voice: [], sms: [], via_application: [] },
                        executions = 0) {
  const status = String(flow.status ?? '').toLowerCase();
  const wired = [...(attach.voice ?? []), ...(attach.sms ?? [])];
  const runs = Number(executions ?? 0);

  if (status !== 'published') {
    return ['unpublished',
      `status is ${status || 'unknown'}, so there is no published definition for a ` +
      'number to run. Publish first; wiring a draft changes nothing.'];
  }

  const named = [...new Set(wired)].sort().join(', ');

  if (wired.length && runs) {
    return ['wired', `reached from ${named} and running: ${runs} execution(s) seen.`];
  }

  if (wired.length) {
    return ['wired-idle',
      `attached to ${named} but no executions in the page read. Wired and untested, ` +
      'or wired to a line nobody calls.'];
  }

  if (runs) {
    return ['triggered-elsewhere',
      `no number points at it, but ${runs} execution(s) exist: started by the REST ` +
      'Executions API, a Trigger widget in another Flow, or a Messaging Service ' +
      'inbound request URL.'];
  }

  const apps = attach.via_application ?? [];
  const hint = apps.length
    ? ` ${apps.length} number(s) on this account use voice_application_sid, whose ` +
      'URL this scan does not follow.'
    : '';
  return ['orphan',
    'published, no number\\'s voice_url or sms_url contains this FlowSid, and no ' +
    `executions. Inbound traffic is still going wherever it went before.${hint}`];
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

export async function pagedV2(auth, url, key, limit = 200) {
  let next = url;
  let params = { PageSize: 50 };
  const out = [];
  while (next && out.length < limit) {
    const page = await get(auth, next, params);
    out.push(...(page[key] ?? []));
    next = page.meta?.next_page_url ?? null;
    params = {};
  }
  return out.slice(0, limit);
}

async function listNumbers(auth, account, limit = 5000) {
  let url = `${BASE}/Accounts/${account}/IncomingPhoneNumbers.json`;
  let params = { PageSize: 1000 };
  const out = [];
  while (url && out.length < limit) {
    const page = await get(auth, url, params);
    out.push(...(page.incoming_phone_numbers ?? []));
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

  const flows = await pagedV2(auth, `${STUDIO}/Flows`, 'flows');
  if (flows.length === 0) {
    console.log('no Studio Flows on this account');
    return;
  }

  const numbers = await listNumbers(auth, account);
  console.log(`${flows.length} flow(s), ${numbers.length} number(s) read`);

  let bad = 0;
  for (const flow of flows) {
    const attach = attachments(flow.sid, numbers);
    let executions = 0;
    if (!attach.voice.length && !attach.sms.length) {
      const page = await pagedV2(auth, `${STUDIO}/Flows/${flow.sid}/Executions`,
                                 'executions', 1);
      executions = page.length;
    }
    const [state, detail] = verdict(flow, attach, executions);
    const line = `${state.padEnd(20)} ${flow.sid} (${flow.friendly_name ?? '?'})  ${detail}`;
    if (state === 'wired' || state === 'triggered-elsewhere' || state === 'wired-idle') {
      console.log(line);
      continue;
    }
    bad += 1;
    console.warn(line);
    if (state === 'unpublished') {
      console.warn('  repair: publish the Flow, then attach a number to it.');
      continue;
    }
    console.warn(`  repair: update ${BASE}/Accounts/${account}/IncomingPhoneNumbers/` +
                 '{PNSid}.json with SmsUrl=https://webhooks.twilio.com/v1/Accounts/' +
                 `${account}/Flows/${flow.sid} and SmsMethod=POST (or the VoiceUrl ` +
                 'equivalent), or assign the number in Console -> Studio -> the Flow.');
  }

  const published = flows.filter((f) => String(f.status ?? '') === 'published').length;
  console.log(`${published} published flow(s), ${bad} with no entry point at all`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The matcher is tested against the shape of a real Studio webhook, including a query string, because an equality test against a hand-built URL is the failure mode that makes this whole audit report nothing. The classifier is tested on the case that decides whether a report is trustworthy: a Flow with executions and no number is not an orphan, and calling it one teaches people to ignore the output.",
"test_py_file": "test_twilio_studio_wiring_audit.py",
"test_py": '''from twilio_studio_wiring_audit import attachments, verdict

FLOW = "FW11111111111111111111111111111111"
HOOK = "https://webhooks.twilio.com/v1/Accounts/ACxxx/Flows/" + FLOW


def number(phone="+15550001111", **fields):
    row = {"sid": "PN1", "phone_number": phone, "voice_url": "", "sms_url": "",
           "voice_application_sid": ""}
    row.update(fields)
    return row


def test_a_number_whose_sms_url_is_the_studio_webhook_counts():
    attach = attachments(FLOW, [number(sms_url=HOOK)])
    assert attach["sms"] == ["+15550001111"]
    assert attach["voice"] == []


def test_a_query_string_on_the_webhook_still_matches():
    # Matched as a substring on purpose: an equality test against a rebuilt URL
    # reports every Flow on the account as unwired.
    attach = attachments(FLOW, [number(voice_url=HOOK + "?lang=fr")])
    assert attach["voice"] == ["+15550001111"]


def test_a_different_flow_sid_does_not_match():
    other = "FW22222222222222222222222222222222"
    assert attachments(other, [number(sms_url=HOOK)]) == {
        "voice": [], "sms": [], "via_application": []}


def test_numbers_on_an_application_sid_are_recorded_as_unanswerable():
    attach = attachments(FLOW, [number(voice_application_sid="AP1")])
    assert attach["via_application"] == ["+15550001111"]
    assert attach["voice"] == []


def test_a_wired_flow_with_traffic_is_healthy():
    state, detail = verdict({"status": "published"},
                            {"voice": [], "sms": ["+15550001111"],
                             "via_application": []}, 12)
    assert state == "wired"
    assert "12 execution(s)" in detail


def test_executions_with_no_number_is_not_an_orphan():
    state, detail = verdict({"status": "published"}, None, 40)
    assert state == "triggered-elsewhere"
    assert "REST Executions API" in detail


def test_no_number_and_no_executions_is_the_finding():
    state, detail = verdict({"status": "published"},
                            {"voice": [], "sms": [], "via_application": ["+15550002222"]},
                            0)
    assert state == "orphan"
    assert "voice_application_sid" in detail


def test_a_draft_flow_is_a_different_problem():
    state, detail = verdict({"status": "draft"}, None, 0)
    assert state == "unpublished"
    assert "Publish first" in detail
''',
"test_js_file": "twilio-studio-wiring-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { attachments, verdict } from './twilio-studio-wiring-audit.mjs';

const FLOW = 'FW11111111111111111111111111111111';
const HOOK = `https://webhooks.twilio.com/v1/Accounts/ACxxx/Flows/${FLOW}`;

const number = (fields = {}) => ({
  sid: 'PN1', phone_number: '+15550001111', voice_url: '', sms_url: '',
  voice_application_sid: '', ...fields,
});

test('a number whose sms_url is the Studio webhook counts', () => {
  const attach = attachments(FLOW, [number({ sms_url: HOOK })]);
  assert.deepEqual(attach.sms, ['+15550001111']);
  assert.deepEqual(attach.voice, []);
});

test('a query string on the webhook still matches', () => {
  const attach = attachments(FLOW, [number({ voice_url: `${HOOK}?lang=fr` })]);
  assert.deepEqual(attach.voice, ['+15550001111']);
});

test('a different flow sid does not match', () => {
  const other = 'FW22222222222222222222222222222222';
  assert.deepEqual(attachments(other, [number({ sms_url: HOOK })]),
    { voice: [], sms: [], via_application: [] });
});

test('numbers on an application sid are recorded as unanswerable', () => {
  const attach = attachments(FLOW, [number({ voice_application_sid: 'AP1' })]);
  assert.deepEqual(attach.via_application, ['+15550001111']);
  assert.deepEqual(attach.voice, []);
});

test('a wired flow with traffic is healthy', () => {
  const [state, detail] = verdict({ status: 'published' },
    { voice: [], sms: ['+15550001111'], via_application: [] }, 12);
  assert.equal(state, 'wired');
  assert.match(detail, /12 execution\\(s\\)/);
});

test('executions with no number is not an orphan', () => {
  const [state, detail] = verdict({ status: 'published' }, undefined, 40);
  assert.equal(state, 'triggered-elsewhere');
  assert.match(detail, /REST Executions API/);
});

test('no number and no executions is the finding', () => {
  const [state, detail] = verdict({ status: 'published' },
    { voice: [], sms: [], via_application: ['+15550002222'] }, 0);
  assert.equal(state, 'orphan');
  assert.match(detail, /voice_application_sid/);
});

test('a draft flow is a different problem', () => {
  const [state, detail] = verdict({ status: 'draft' }, undefined, 0);
  assert.equal(state, 'unpublished');
  assert.match(detail, /Publish first/);
});
''',
"faq": [
 ("Doesn't publishing a Flow make it live?",
  "It makes the definition live inside Studio. It does not create an entry point. A Flow runs when something sends a request to its webhook URL, and the usual something is a phone number whose voice_url or sms_url is that URL. Publishing and routing are two separate acts in two separate parts of the Console."),
 ("The Flow has executions but no number points at it. Is that broken?",
  "No. Flows are also started by the REST Executions API, by a Trigger widget inside another Flow, and by a Messaging Service whose inbound request URL is the Studio webhook. The script reports that case as triggered elsewhere rather than as an orphan, because it is a working Flow with an entry point this scan cannot see."),
 ("Why match on the SID inside the URL instead of comparing full URLs?",
  "Because the Studio webhook can carry a query string, and because reconstructing the expected URL by hand means getting the account SID, the path and the version right in every case. A substring test on the FlowSid is both simpler and much harder to get wrong in the direction that hides findings."),
 ("What about numbers that use an Application SID?",
  "When voice_application_sid is set, the number's own voice_url is ignored and the TwiML App's URL is used instead. The script counts those numbers and says so in the report rather than pretending to have checked them, because following the App is a second lookup and a different note."),
 ("Can the script wire the number up for me?",
  "No. Everything in this section reads. Attaching a Flow to a number changes what happens when a customer dials it, which is a decision for a person; the script prints the exact update to make, including the webhook URL with the account SID and FlowSid already filled in."),
],
"related": [
 ("/twilio/studio-flow-draft-not-published/", "A Studio Flow whose edits are live nowhere"),
 ("/twilio/number-conflicting-url-and-application-sid/", "An Application SID overriding a number's URL"),
 ("/twilio/phone-number-still-on-demo-twiml/", "A number still on Twilio's demo TwiML"),
],
"citations": [CITE_STUDIO_FAQ, CITE_FLOW, CITE_NUMBER, CITE_EXEC],
},


{
"slug": "conversations-webhook-url-missing",
"title": "A conversation webhook with no URL fails every event: 50369",
"description": "Error 50369 says the conversation webhook URL was not provided. The webhook exists, it is attached, and configuration.url is empty, so no event ever leaves.",
"h1": "a conversation webhook with no URL fails every event: 50369",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio error 50369", "conversation webhook url not provided",
             "twilio conversations webhook", "conversation scoped webhook",
             "twilio conversations events missing"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The Debugger fills up with <code>50369</code>, <em>Conversation webhook URL not provided</em>. The webhook resource exists. It is attached to the conversation, it has the right target, and it has been there since the integration was built. What it does not have is a URL, so every message added to that conversation raises an error and reaches nothing.",
"short_answer": """<p>Sweep <code>GET https://monitor.twilio.com/v1/Alerts?LogLevel=error</code> for <code>error_code</code> <code>50369</code> and collect the conversation SIDs from <code>resource_sid</code>. Then read <code>GET https://conversations.twilio.com/v1/Conversations/{ConversationSid}/Webhooks</code> and find the entry whose <code>configuration.url</code> is null or empty.</p>
<p>Only a webhook whose <code>target</code> is <code>webhook</code> or <code>trigger</code> needs a URL. A <code>studio</code>-target webhook routes to a <code>flow_sid</code> instead and correctly has none, so a check that flags every empty URL produces a report nobody will read twice.</p>""",
"problem": """<p>A conversation-scoped webhook with no URL is a subscription to nothing. Twilio holds the resource, matches the event, goes to deliver it, finds no destination and raises 50369. The conversation itself keeps working perfectly &mdash; participants send messages, the transcript is complete, nothing a user can see is wrong. The only thing missing is your application finding out any of it happened.</p>
<p>It usually arrives from automation. A service creates a webhook per conversation at the moment the conversation is created, and one path through that code omits the URL: a config value that was empty at boot, a template that rendered to nothing, a later update that cleared the field. Every conversation created after that point gets a webhook that cannot fire, and the count of broken conversations grows for as long as the alerts go unread.</p>""",
"why": """<p><strong>The error is per event, not per configuration.</strong> 50369 is raised when an event tries to fire, so one badly created webhook produces alerts forever rather than once, and volume in the Debugger tells you how chatty the conversation is rather than how many things are broken. The count of distinct conversation SIDs is the number that means something.</p>
<p><strong>The alert list is a 30-day window.</strong> Debugger alerts are retained for 30 days and a single request returns at most 10,000. A webhook created six weeks ago on a conversation that has been quiet since shows up nowhere in the alerts, which is why the alert sweep is the starting point and the webhook list is the confirmation.</p>
<p><strong>Not every webhook needs a URL.</strong> <code>target</code> can be <code>webhook</code>, <code>trigger</code> or <code>studio</code>. The first two deliver to <code>configuration.url</code>; the third hands the conversation to a Studio Flow named by <code>configuration.flow_sid</code>. Treating a Studio webhook's empty URL as a finding is the fastest way to make this audit useless.</p>
<p><strong>Conversation-scoped and service-scoped webhooks are different resources.</strong> A global <code>post_webhook_url</code> under <code>Configuration/Webhooks</code> being correct does not make a per-conversation webhook correct, and the reverse is also true. 50369 is raised by the conversation-scoped one, and that is the resource to read.</p>""",
"steps": [
 {"h": "Sweep the alerts for the code",
  "body": """<p><code>GET https://monitor.twilio.com/v1/Alerts?LogLevel=error&amp;StartDate=YYYY-MM-DD&amp;PageSize=100</code>, following <code>meta.next_page_url</code>. Keep alerts whose <code>error_code</code> is <code>50369</code>. Read the code defensively: it comes back as a number on the resource and as a string in some exports, and comparing the raw value is how a sweep finds nothing on an account full of them.</p>"""},
 {"h": "Pull the conversation SIDs out",
  "body": """<p><code>resource_sid</code> on the alert is the affected resource. When it is not a <code>CH</code> SID, fall back to the first <code>CH</code>-prefixed SID in <code>alert_text</code>. Deduplicate: one broken webhook on a busy conversation produces hundreds of alerts, and the finding is the conversation, not the alert.</p>"""},
 {"h": "Read the webhooks on each conversation",
  "body": """<p><code>GET https://conversations.twilio.com/v1/Conversations/{ConversationSid}/Webhooks</code>. Each entry carries <code>target</code> and a <code>configuration</code> object holding <code>url</code>, <code>method</code>, <code>filters</code>, <code>triggers</code> and <code>flow_sid</code>. This is the resource that proves the diagnosis; the alert only told you where to look.</p>"""},
 {"h": "Judge by target, not by the URL alone",
  "body": """<p>An empty <code>configuration.url</code> is a finding on a <code>webhook</code> or <code>trigger</code> target and correct on a <code>studio</code> target. While you are there, an <code>http://</code> URL is worth reporting separately: it is not 50369, but it is a webhook carrying conversation content in the clear.</p>"""},
 {"h": "Repair the resource, then the code that created it",
  "body": """<p>The webhook update takes <code>Configuration.Url</code> and <code>Configuration.Method</code>. Fixing the resource clears today's alerts; fixing the creation path stops tomorrow's. Then re-run the alert sweep over a window that starts after the change, because the historical alerts stay in the list until they age out and will otherwise look like a repair that did not work.</p>"""},
],
"verify": """<p>Re-run with a start date after the fix. The alert sweep should return no 50369 at all, and every webhook the script reads should classify as <code>ok</code> or <code>studio</code>.</p>
<pre><code class="language-bash">python3 twilio_conversation_webhook_audit.py --days 3
# 0 conversation(s) raising 50369 in the last 3 day(s)</code></pre>""",
"code_intro": "One alert sweep and one webhook list per affected conversation, both GETs, on an API Key with read access. The two pure functions are the SID extraction and the per-webhook verdict, because those are the two places this check can quietly go wrong: a numeric comparison that never matches, and a Studio-target webhook reported as broken because it has no URL and never needed one.",
"py_file": "twilio_conversation_webhook_audit.py",
"py": '''"""Report Twilio conversation webhooks with no URL behind them (error 50369).

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. The repair is printed, never performed,
because this script holds a credential to an account that can send messages and
spend money.
"""
import argparse
import datetime as dt
import logging
import os
import re
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_conversation_webhook_audit")

MONITOR = "https://monitor.twilio.com/v1"
CONVERSATIONS = "https://conversations.twilio.com/v1"

NO_URL = 50369
CH_SID = re.compile(r"CH[0-9a-fA-F]{32}")


def conversation_sids(alerts, code=NO_URL):
    """Distinct conversation SIDs from the alerts carrying one error code. Pure.

    error_code arrives as a number on the Alert resource and as a string in some
    exports, so it is coerced rather than compared raw: that comparison is why a
    sweep reports nothing on an account full of findings. resource_sid is the
    affected resource; alert_text is the fallback when it is not a CH SID.

    Deduplicated, because one broken webhook on a busy conversation raises the
    error on every event and the finding is the conversation, not the alert.
    """
    found = []
    for a in alerts or []:
        raw = a.get("error_code")
        try:
            if raw is None or int(raw) != int(code):
                continue
        except (TypeError, ValueError):
            continue
        sid = str(a.get("resource_sid") or "")
        if not CH_SID.fullmatch(sid):
            match = CH_SID.search(str(a.get("alert_text") or ""))
            sid = match.group(0) if match else ""
        if sid and sid not in found:
            found.append(sid)
    return found


def verdict(webhook):
    """Classify one conversation-scoped webhook. Pure.

    target decides whether a URL is even required: `webhook` and `trigger`
    deliver to configuration.url, while `studio` hands the conversation to the
    Flow named by configuration.flow_sid and correctly has no URL at all.

    Returns (state, detail).
    """
    target = str(webhook.get("target") or "").lower()
    cfg = webhook.get("configuration") or {}
    url = str(cfg.get("url") or "").strip()

    if target == "studio":
        flow = str(cfg.get("flow_sid") or "").strip()
        if flow:
            return ("studio", "routes to Studio Flow %s; no URL is required." % flow)
        return ("studio-no-flow",
                "target is studio but configuration.flow_sid is empty, so there "
                "is no Flow to route to and no URL either.")

    if target not in ("webhook", "trigger"):
        return ("unknown-target",
                "target %r is not one this check understands; read the webhook "
                "resource by hand." % (target or "empty"))

    if not url:
        return ("missing-url",
                "target is %s and configuration.url is empty. Every event on this "
                "conversation raises 50369 and reaches nothing." % target)

    if url.startswith("http://"):
        return ("insecure",
                "delivers conversation content over plain http to %s. Not 50369, "
                "but message bodies in the clear." % url)

    if not url.startswith("https://"):
        return ("invalid-url",
                "configuration.url is %r, which is not an absolute http(s) URL." % url)

    return ("ok", "target %s delivering to %s." % (target, url))


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def paged(session, url, key, limit, **first):
    params = dict(first)
    params.setdefault("PageSize", 100)
    out = []
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get(key, []))
        url = (page.get("meta") or {}).get("next_page_url")
        params = {}
    return out[:limit]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=7,
                    help="how far back to sweep the alerts (30 day retention)")
    ap.add_argument("--max-alerts", type=int, default=10000,
                    help="stop paging after this many alerts")
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

    start = (dt.date.today() - dt.timedelta(days=args.days)).isoformat()
    alerts = paged(session, "%s/Alerts" % MONITOR, "alerts", args.max_alerts,
                   LogLevel="error", StartDate=start)
    sids = conversation_sids(alerts)
    if not sids:
        log.info("0 conversation(s) raising 50369 in the last %d day(s)", args.days)
        return 0

    bad = 0
    for sid in sids:
        webhooks = paged(session, "%s/Conversations/%s/Webhooks"
                         % (CONVERSATIONS, sid), "webhooks", 50)
        if not webhooks:
            log.warning("%-15s %s  50369 in the alerts but the conversation has no "
                        "webhooks now: it was deleted, or the conversation was.",
                        "gone", sid)
            bad += 1
            continue
        for hook in webhooks:
            state, detail = verdict(hook)
            line = "%-15s %s/%s  %s" % (state, sid, hook.get("sid"), detail)
            if state in ("ok", "studio"):
                log.info(line)
                continue
            bad += 1
            log.warning(line)
            log.warning("  repair: update %s/Conversations/%s/Webhooks/%s with "
                        "Configuration.Url=https://... and Configuration.Method="
                        "POST, then fix the code path that created it without one.",
                        CONVERSATIONS, sid, hook.get("sid"))

    log.info("%d conversation(s) raising 50369 in the last %d day(s), %d webhook "
             "finding(s)", len(sids), args.days, bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-conversation-webhook-audit.mjs",
"js": '''/**
 * Report Twilio conversation webhooks with no URL behind them (error 50369).
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const MONITOR = 'https://monitor.twilio.com/v1';
const CONVERSATIONS = 'https://conversations.twilio.com/v1';

const NO_URL = 50369;
const CH_SID = /CH[0-9a-fA-F]{32}/;

/**
 * Distinct conversation SIDs from the alerts carrying one error code. Pure.
 *
 * error_code arrives as a number on the Alert resource and as a string in some
 * exports, so it is coerced rather than compared raw. resource_sid is the
 * affected resource; alert_text is the fallback. Deduplicated, because one
 * broken webhook on a busy conversation raises the error on every event.
 */
export function conversationSids(alerts, code = NO_URL) {
  const found = [];
  for (const a of alerts ?? []) {
    const raw = a.error_code;
    if (raw === null || raw === undefined || raw === '') continue;
    const n = Number(raw);
    if (!Number.isFinite(n) || n !== Number(code)) continue;
    let sid = String(a.resource_sid ?? '');
    if (!/^CH[0-9a-fA-F]{32}$/.test(sid)) {
      const match = CH_SID.exec(String(a.alert_text ?? ''));
      sid = match ? match[0] : '';
    }
    if (sid && !found.includes(sid)) found.push(sid);
  }
  return found;
}

/**
 * Classify one conversation-scoped webhook. Pure.
 *
 * target decides whether a URL is even required: `webhook` and `trigger`
 * deliver to configuration.url, while `studio` hands the conversation to the
 * Flow named by configuration.flow_sid and correctly has no URL at all.
 * Returns [state, detail].
 */
export function verdict(webhook) {
  const target = String(webhook.target ?? '').toLowerCase();
  const cfg = webhook.configuration ?? {};
  const url = String(cfg.url ?? '').trim();

  if (target === 'studio') {
    const flow = String(cfg.flow_sid ?? '').trim();
    if (flow) return ['studio', `routes to Studio Flow ${flow}; no URL is required.`];
    return ['studio-no-flow',
      'target is studio but configuration.flow_sid is empty, so there is no Flow ' +
      'to route to and no URL either.'];
  }

  if (target !== 'webhook' && target !== 'trigger') {
    return ['unknown-target',
      `target "${target || 'empty'}" is not one this check understands; read the ` +
      'webhook resource by hand.'];
  }

  if (!url) {
    return ['missing-url',
      `target is ${target} and configuration.url is empty. Every event on this ` +
      'conversation raises 50369 and reaches nothing.'];
  }

  if (url.startsWith('http://')) {
    return ['insecure',
      `delivers conversation content over plain http to ${url}. Not 50369, but ` +
      'message bodies in the clear.'];
  }

  if (!url.startsWith('https://')) {
    return ['invalid-url',
      `configuration.url is "${url}", which is not an absolute http(s) URL.`];
  }

  return ['ok', `target ${target} delivering to ${url}.`];
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

export async function paged(auth, url, key, limit = 10000, first = {}) {
  let next = url;
  let params = { PageSize: 100, ...first };
  const out = [];
  while (next && out.length < limit) {
    const page = await get(auth, next, params);
    out.push(...(page[key] ?? []));
    next = page.meta?.next_page_url ?? null;
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
  const start = new Date(Date.now() - days * 86400000).toISOString().slice(0, 10);

  const alerts = await paged(auth, `${MONITOR}/Alerts`, 'alerts', 10000,
                             { LogLevel: 'error', StartDate: start });
  const sids = conversationSids(alerts);
  if (sids.length === 0) {
    console.log(`0 conversation(s) raising 50369 in the last ${days} day(s)`);
    return;
  }

  let bad = 0;
  for (const sid of sids) {
    const webhooks = await paged(auth, `${CONVERSATIONS}/Conversations/${sid}/Webhooks`,
                                 'webhooks', 50);
    if (webhooks.length === 0) {
      console.warn(`${'gone'.padEnd(15)} ${sid}  50369 in the alerts but the ` +
                   'conversation has no webhooks now: it was deleted, or the ' +
                   'conversation was.');
      bad += 1;
      continue;
    }
    for (const hook of webhooks) {
      const [state, detail] = verdict(hook);
      const line = `${state.padEnd(15)} ${sid}/${hook.sid}  ${detail}`;
      if (state === 'ok' || state === 'studio') { console.log(line); continue; }
      bad += 1;
      console.warn(line);
      console.warn(`  repair: update ${CONVERSATIONS}/Conversations/${sid}/Webhooks/` +
                   `${hook.sid} with Configuration.Url=https://... and ` +
                   'Configuration.Method=POST, then fix the code path that created ' +
                   'it without one.');
    }
  }

  console.log(`${sids.length} conversation(s) raising 50369 in the last ${days} ` +
              `day(s), ${bad} webhook finding(s)`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Two things decide whether this audit is worth running. An <code>error_code</code> that arrives as the string <code>\"50369\"</code> has to match, and a Studio-target webhook with no URL has to come back clean &mdash; it is supposed to have no URL. The rest of the tests are about not double-counting: hundreds of alerts on one chatty conversation are one finding.",
"test_py_file": "test_twilio_conversation_webhook_audit.py",
"test_py": '''from twilio_conversation_webhook_audit import conversation_sids, verdict

CH = "CH11111111111111111111111111111111"
CH2 = "CH22222222222222222222222222222222"


def alert(code=50369, resource=CH, text=""):
    return {"sid": "NO1", "error_code": code, "resource_sid": resource,
            "alert_text": text, "log_level": "error"}


def hook(target="webhook", **cfg):
    return {"sid": "WH1", "target": target, "configuration": cfg}


def test_error_code_as_a_string_still_matches():
    assert conversation_sids([alert(code="50369")]) == [CH]


def test_other_error_codes_are_ignored():
    assert conversation_sids([alert(code=50361), alert(code=None)]) == []


def test_one_chatty_conversation_is_one_finding():
    assert conversation_sids([alert(), alert(), alert(resource=CH2)]) == [CH, CH2]


def test_the_conversation_sid_is_recovered_from_the_alert_text():
    a = alert(resource="ACxxxxxxxx", text="Conversation webhook URL not provided "
                                          "for %s" % CH2)
    assert conversation_sids([a]) == [CH2]


def test_a_webhook_target_with_no_url_is_the_finding():
    state, detail = verdict(hook("webhook", url=None))
    assert state == "missing-url"
    assert "50369" in detail


def test_a_studio_target_with_no_url_is_correct():
    # This is the false positive that would make the report useless: a studio
    # webhook routes to a Flow and never has a URL.
    state, detail = verdict(hook("studio", flow_sid="FW1"))
    assert state == "studio"
    assert "FW1" in detail


def test_a_studio_target_with_no_flow_is_still_wrong():
    assert verdict(hook("studio"))[0] == "studio-no-flow"


def test_a_trigger_target_needs_a_url_too():
    assert verdict(hook("trigger", url=""))[0] == "missing-url"
    assert verdict(hook("trigger", url="https://app.example.com/hook"))[0] == "ok"


def test_plain_http_is_reported_separately_from_the_missing_url():
    state, detail = verdict(hook("webhook", url="http://app.example.com/hook"))
    assert state == "insecure"
    assert "Not 50369" in detail
''',
"test_js_file": "twilio-conversation-webhook-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { conversationSids, verdict } from './twilio-conversation-webhook-audit.mjs';

const CH = 'CH11111111111111111111111111111111';
const CH2 = 'CH22222222222222222222222222222222';

const alert = ({ code = 50369, resource = CH, text = '' } = {}) => ({
  sid: 'NO1', error_code: code, resource_sid: resource, alert_text: text,
  log_level: 'error',
});

const hook = (target = 'webhook', configuration = {}) => ({
  sid: 'WH1', target, configuration,
});

test('error code as a string still matches', () => {
  assert.deepEqual(conversationSids([alert({ code: '50369' })]), [CH]);
});

test('other error codes are ignored', () => {
  assert.deepEqual(conversationSids([alert({ code: 50361 }), alert({ code: null })]), []);
});

test('one chatty conversation is one finding', () => {
  assert.deepEqual(conversationSids([alert(), alert(), alert({ resource: CH2 })]),
    [CH, CH2]);
});

test('the conversation sid is recovered from the alert text', () => {
  const a = alert({ resource: 'ACxxxxxxxx',
                    text: `Conversation webhook URL not provided for ${CH2}` });
  assert.deepEqual(conversationSids([a]), [CH2]);
});

test('a webhook target with no url is the finding', () => {
  const [state, detail] = verdict(hook('webhook', { url: null }));
  assert.equal(state, 'missing-url');
  assert.match(detail, /50369/);
});

test('a studio target with no url is correct', () => {
  const [state, detail] = verdict(hook('studio', { flow_sid: 'FW1' }));
  assert.equal(state, 'studio');
  assert.match(detail, /FW1/);
});

test('a studio target with no flow is still wrong', () => {
  assert.equal(verdict(hook('studio', {}))[0], 'studio-no-flow');
});

test('a trigger target needs a url too', () => {
  assert.equal(verdict(hook('trigger', { url: '' }))[0], 'missing-url');
  assert.equal(verdict(hook('trigger', { url: 'https://app.example.com/hook' }))[0], 'ok');
});

test('plain http is reported separately from the missing url', () => {
  const [state, detail] = verdict(hook('webhook', { url: 'http://app.example.com/hook' }));
  assert.equal(state, 'insecure');
  assert.match(detail, /Not 50369/);
});
''',
"faq": [
 ("What exactly does 50369 mean?",
  "That an event matched a conversation-scoped webhook whose configuration carried no URL to deliver to. The webhook resource exists and is attached; there is simply nowhere for Twilio to send the request, so it raises the error instead. The conversation itself is unaffected and the participants notice nothing."),
 ("Why do I get hundreds of these for one conversation?",
  "Because the error is raised per event, not per configuration. Every message added, every participant change, every state update tries to fire the webhook and fails again. The number worth reporting is the count of distinct conversation SIDs, which is why the script deduplicates before it looks anything up."),
 ("Can I find every affected conversation from the alerts alone?",
  "No. Debugger alerts are retained for 30 days, and a webhook on a conversation that has been quiet for longer raises nothing to find. The alert sweep tells you which conversations are actively failing; auditing the creation path in your own code is the only way to bound the rest."),
 ("Why does the script not flag a webhook with no URL when the target is studio?",
  "Because a studio-target webhook routes the conversation to the Flow named in configuration.flow_sid and never has a URL. Reporting those would put a false positive next to every real one, and a report with false positives in it stops being read after the second week."),
 ("Is the global Conversations webhook the same thing?",
  "No. The service-level configuration under Configuration/Webhooks holds post_webhook_url, pre_webhook_url and the filters that decide which events fire at all. It is a different resource with a different failure mode; 50369 comes from the conversation-scoped webhook, and that is what this script reads."),
],
"related": [
 ("/twilio/inbound-webhook-black-hole/", "Inbound SMS into a number with no sms_url"),
 ("/twilio/status-callback-webhook-failing-11200/", "Status callbacks failing with 11200"),
 ("/twilio/event-streams-sink-failed/", "An Event Streams sink that stopped delivering"),
],
"citations": [CITE_50369, CITE_CONV_HOOK, CITE_CONV_HOOKS, CITE_ALERTS],
},


{
"slug": "event-streams-sink-failed",
"title": "A failed Event Streams sink drops events and nothing says so",
"description": "A sink whose status is failed has stopped delivering. Messages and calls carry on as before, downstream analytics quietly stop, and no error code is raised.",
"h1": "a failed Event Streams sink drops events and nothing says so",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio event streams sink failed", "twilio sink status",
             "event streams subscription", "twilio sink validation",
             "twilio events not delivered"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The dashboards flatlined a week ago and everyone assumed volume was down. It was not: an Event Streams sink stopped responding inside its timeout, Twilio marked it <code>failed</code>, and delivery stopped. Every message still sent, every call still connected, and nothing in the message or call logs changed &mdash; the only place this exists is a <code>status</code> field nobody polls.",
"short_answer": """<p>Read <code>GET https://events.twilio.com/v1/Sinks</code> and flag any sink whose <code>status</code> is not <code>active</code>: <code>failed</code>, <code>validating</code> or <code>initialized</code>. Pair each one with <code>GET https://events.twilio.com/v1/Subscriptions</code> to see which subscriptions feed it, because a sink with no subscription is untidy and a sink with three is an outage.</p>
<p>Cross-check <code>GET https://monitor.twilio.com/v1/Alerts?LogLevel=error</code> for the sink SID in <code>resource_sid</code>. The failure notice repeats while the sink is down, so its presence dates the outage and its absence does not clear the sink.</p>""",
"problem": """<p>Event Streams is the pipe that carries what happened to somewhere you can query it. When the destination stops answering &mdash; a webhook past its five-second timeout, a Kinesis stream whose credentials expired &mdash; Twilio marks the sink failed and stops delivering to it. Nothing else changes. Messages send, calls connect, the API is healthy, and the pipe is empty.</p>
<p>The reason this runs for weeks is that the loss is invisible from both ends. Twilio's own logs look normal because nothing about messaging or voice failed. Your warehouse looks normal because a table that stops growing looks exactly like a table nobody wrote to, and dashboards built on top of it render a flat line rather than an error. The first real signal is usually someone asking why a chart ends on a Tuesday.</p>""",
"why": """<p><strong>The status field is the whole diagnosis.</strong> A sink is <code>initialized</code> when created, <code>validating</code> while a test event is being confirmed, <code>active</code> once it is, and <code>failed</code> when the destination stopped accepting delivery. Nothing else in the account changes with it, so a check that does not read this field cannot see any of it.</p>
<p><strong>Not-active is not one problem.</strong> A sink stuck at <code>initialized</code> or <code>validating</code> has never delivered a single event: somebody created it and never finished. A <code>failed</code> sink was working and stopped, which means there is a period of missing data with a start date. Those need different sentences, and a report that lumps them together sends people looking in the wrong place.</p>
<p><strong>A sink alone proves nothing.</strong> Sinks and subscriptions are separate resources; a subscription names a <code>sink_sid</code>. An active sink with no subscription pointed at it delivers nothing at all while looking perfectly healthy, and a failed sink with no subscription is only litter. The pairing is what tells you whether events are actually being lost.</p>
<p><strong>Recovery is not automatic.</strong> Fixing the destination does not un-fail the sink. It has to be validated again with a test event and the subscriptions re-attached, so a team that repairs the endpoint and walks away still has an empty pipe and no error to show for it.</p>""",
"steps": [
 {"h": "List the sinks and read status",
  "body": """<p><code>GET https://events.twilio.com/v1/Sinks?PageSize=50</code>, following <code>meta.next_page_url</code>. Keep <code>sid</code>, <code>description</code>, <code>sink_type</code> and <code>status</code>. Anything other than <code>active</code> is a finding of some kind; which kind depends on the next two steps.</p>"""},
 {"h": "List the subscriptions and pair them by sink_sid",
  "body": """<p><code>GET https://events.twilio.com/v1/Subscriptions?PageSize=50</code>. Build a map from <code>sink_sid</code> to the subscriptions that name it. This is the difference between a failed sink that is losing your delivery events and a failed sink somebody abandoned last quarter, and there is no way to tell them apart from the sink resource alone.</p>"""},
 {"h": "Separate never-worked from stopped-working",
  "body": """<p><code>initialized</code> and <code>validating</code> mean the sink has never delivered anything: the validation step was never completed. <code>failed</code> means it delivered until it did not. The second has a gap in your data with a start date; the first has no data and never did.</p>"""},
 {"h": "Date the outage from the alerts",
  "body": """<p><code>GET https://monitor.twilio.com/v1/Alerts?LogLevel=error&amp;StartDate=YYYY-MM-DD</code> and look for the sink SID in <code>resource_sid</code>. The failure notice repeats while the sink is down, so the earliest one bounds the data loss. Alerts are retained 30 days, so an older outage will have no alerts left and still be an outage.</p>"""},
 {"h": "Fix the destination, then validate and re-attach",
  "body": """<p>Repair the endpoint or the credentials first, then validate the sink with a test ID, then re-point the subscription at it. Every one of those is a write, so this script prints them: it holds a read-only credential on an account that spends money. Re-run afterwards, because a sink that is <code>active</code> with no subscription is the failure mode people create while fixing this one.</p>"""},
],
"verify": """<p>Re-run after validating and re-attaching. Every sink carrying real traffic should report <code>active</code>, and any sink left in <code>unused</code> should be one you meant to leave lying around.</p>
<pre><code class="language-bash">python3 twilio_event_sink_audit.py
# 3 sink(s), 0 dropping events</code></pre>""",
"code_intro": "Two lists and an optional alert sweep, all GETs, on an API Key with read access. The pure part is the pairing and the verdict: the pairing because sinks and subscriptions are separate resources and the join is the entire diagnosis, and the verdict because a failed sink with subscriptions and a failed sink without them are the same status field and completely different news.",
"py_file": "twilio_event_sink_audit.py",
"py": '''"""Report Twilio Event Streams sinks that are not delivering events.

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. The repair is printed, never performed,
because this script holds a credential to an account that can send messages and
spend money.
"""
import argparse
import datetime as dt
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_event_sink_audit")

EVENTS = "https://events.twilio.com/v1"
MONITOR = "https://monitor.twilio.com/v1"

HEALTHY = "active"
NEVER_RAN = ("initialized", "validating")


def subscribers(subscriptions):
    """Map every sink SID to the subscriptions feeding it. Pure.

    Sinks and subscriptions are separate resources joined only by sink_sid, and
    that join is the whole diagnosis: a failed sink with three subscriptions is
    an outage, and a failed sink with none is litter.
    """
    out = {}
    for sub in subscriptions or []:
        sink = str(sub.get("sink_sid") or "").strip()
        if not sink:
            continue
        out.setdefault(sink, []).append(str(sub.get("sid") or "?"))
    return out


def verdict(sink, subs=None):
    """Classify one sink. Pure, so the difference between a sink that stopped
    working and one that never worked is written down once.

    Returns (state, detail).
    """
    subs = list(subs or [])
    status = str(sink.get("status") or "").lower()
    kind = str(sink.get("sink_type") or "unknown")
    feeding = ("%d subscription(s): %s" % (len(subs), ", ".join(subs)) if subs
               else "no subscription points at it")

    if status == HEALTHY:
        if subs:
            return ("active", "%s sink, delivering, %s." % (kind, feeding))
        return ("unused",
                "%s sink is active but %s, so it delivers nothing. Healthy in the "
                "list and carrying no events." % (kind, feeding))

    if status == "failed":
        if subs:
            return ("failed",
                    "%s sink is failed and %s. Every event those subscriptions "
                    "carry is being dropped, and nothing in the message or call "
                    "logs changed." % (kind, feeding))
        return ("failed-detached",
                "%s sink is failed and %s. Nothing is being lost through it; it "
                "is a dead resource somebody left behind." % (kind, feeding))

    if status in NEVER_RAN:
        return ("unvalidated",
                "%s sink is %s, which means validation was never completed: it "
                "has never delivered a single event. %s."
                % (kind, status, feeding[0].upper() + feeding[1:]))

    return ("unknown-status",
            "%s sink reports status %r, which this check does not recognise. Read "
            "the sink resource by hand." % (kind, status or "empty"))


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def paged(session, url, key, limit, **first):
    params = dict(first)
    params.setdefault("PageSize", 50)
    out = []
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get(key, []))
        url = (page.get("meta") or {}).get("next_page_url")
        params = {}
    return out[:limit]


def alert_dates(session, days, sids):
    """Earliest error alert per sink SID, to date the outage. Alerts are kept
    for 30 days, so an older failure has nothing here and is still a failure."""
    if not sids:
        return {}
    start = (dt.date.today() - dt.timedelta(days=days)).isoformat()
    alerts = paged(session, "%s/Alerts" % MONITOR, "alerts", 10000,
                   LogLevel="error", StartDate=start)
    out = {}
    for a in alerts:
        sid = str(a.get("resource_sid") or "")
        if sid not in sids:
            continue
        when = str(a.get("date_generated") or a.get("date_created") or "")
        if when and (sid not in out or when < out[sid]):
            out[sid] = when
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=7,
                    help="how far back to sweep alerts to date the outage")
    ap.add_argument("--max-sinks", type=int, default=200,
                    help="stop paging after this many sinks")
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

    sinks = paged(session, "%s/Sinks" % EVENTS, "sinks", args.max_sinks)
    if not sinks:
        log.info("no Event Streams sinks on this account")
        return 0

    feeds = subscribers(paged(session, "%s/Subscriptions" % EVENTS,
                              "subscriptions", 500))

    broken = set(str(s.get("sid")) for s in sinks
                 if str(s.get("status") or "").lower() != HEALTHY)
    dated = alert_dates(session, args.days, broken)

    bad = 0
    for sink in sinks:
        sid = str(sink.get("sid"))
        state, detail = verdict(sink, feeds.get(sid))
        line = "%-16s %s (%s)  %s" % (state, sid, sink.get("description", "?"), detail)
        if state == "active":
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        if sid in dated:
            log.warning("  first error alert in the window: %s", dated[sid])
        if state == "unused":
            log.warning("  repair: point a subscription at this sink, or delete it "
                        "so it stops looking like observability.")
            continue
        log.warning("  repair: fix the destination or its credentials, validate the "
                    "sink at %s/Sinks/%s/Validate with a TestId, then re-attach it "
                    "at %s/Subscriptions/{SubscriptionSid} with SinkSid=%s. Fixing "
                    "the endpoint alone does not restart delivery.",
                    EVENTS, sid, EVENTS, sid)

    log.info("%d sink(s), %d dropping events", len(sinks), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-event-sink-audit.mjs",
"js": '''/**
 * Report Twilio Event Streams sinks that are not delivering events.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const EVENTS = 'https://events.twilio.com/v1';
const MONITOR = 'https://monitor.twilio.com/v1';

const HEALTHY = 'active';
const NEVER_RAN = ['initialized', 'validating'];

/**
 * Map every sink SID to the subscriptions feeding it. Pure.
 *
 * Sinks and subscriptions are separate resources joined only by sink_sid, and
 * that join is the whole diagnosis: a failed sink with three subscriptions is
 * an outage, and a failed sink with none is litter.
 */
export function subscribers(subscriptions) {
  const out = new Map();
  for (const sub of subscriptions ?? []) {
    const sink = String(sub.sink_sid ?? '').trim();
    if (!sink) continue;
    if (!out.has(sink)) out.set(sink, []);
    out.get(sink).push(String(sub.sid ?? '?'));
  }
  return out;
}

/**
 * Classify one sink. Pure, so the difference between a sink that stopped
 * working and one that never worked is written down once.
 * Returns [state, detail].
 */
export function verdict(sink, subs = []) {
  const list = [...(subs ?? [])];
  const status = String(sink.status ?? '').toLowerCase();
  const kind = String(sink.sink_type ?? 'unknown');
  const feeding = list.length
    ? `${list.length} subscription(s): ${list.join(', ')}`
    : 'no subscription points at it';

  if (status === HEALTHY) {
    if (list.length) return ['active', `${kind} sink, delivering, ${feeding}.`];
    return ['unused',
      `${kind} sink is active but ${feeding}, so it delivers nothing. Healthy in ` +
      'the list and carrying no events.'];
  }

  if (status === 'failed') {
    if (list.length) {
      return ['failed',
        `${kind} sink is failed and ${feeding}. Every event those subscriptions ` +
        'carry is being dropped, and nothing in the message or call logs changed.'];
    }
    return ['failed-detached',
      `${kind} sink is failed and ${feeding}. Nothing is being lost through it; it ` +
      'is a dead resource somebody left behind.'];
  }

  if (NEVER_RAN.includes(status)) {
    return ['unvalidated',
      `${kind} sink is ${status}, which means validation was never completed: it ` +
      `has never delivered a single event. ${feeding[0].toUpperCase()}${feeding.slice(1)}.`];
  }

  return ['unknown-status',
    `${kind} sink reports status "${status || 'empty'}", which this check does not ` +
    'recognise. Read the sink resource by hand.'];
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

export async function paged(auth, url, key, limit = 200, first = {}) {
  let next = url;
  let params = { PageSize: 50, ...first };
  const out = [];
  while (next && out.length < limit) {
    const page = await get(auth, next, params);
    out.push(...(page[key] ?? []));
    next = page.meta?.next_page_url ?? null;
    params = {};
  }
  return out.slice(0, limit);
}

async function alertDates(auth, days, sids) {
  if (sids.size === 0) return new Map();
  const start = new Date(Date.now() - days * 86400000).toISOString().slice(0, 10);
  const alerts = await paged(auth, `${MONITOR}/Alerts`, 'alerts', 10000,
                             { LogLevel: 'error', StartDate: start });
  const out = new Map();
  for (const a of alerts) {
    const sid = String(a.resource_sid ?? '');
    if (!sids.has(sid)) continue;
    const when = String(a.date_generated ?? a.date_created ?? '');
    if (when && (!out.has(sid) || when < out.get(sid))) out.set(sid, when);
  }
  return out;
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

  const sinks = await paged(auth, `${EVENTS}/Sinks`, 'sinks');
  if (sinks.length === 0) {
    console.log('no Event Streams sinks on this account');
    return;
  }

  const feeds = subscribers(await paged(auth, `${EVENTS}/Subscriptions`,
                                        'subscriptions', 500));

  const broken = new Set(sinks
    .filter((s) => String(s.status ?? '').toLowerCase() !== HEALTHY)
    .map((s) => String(s.sid)));
  const dated = await alertDates(auth, days, broken);

  let bad = 0;
  for (const sink of sinks) {
    const sid = String(sink.sid);
    const [state, detail] = verdict(sink, feeds.get(sid));
    const line = `${state.padEnd(16)} ${sid} (${sink.description ?? '?'})  ${detail}`;
    if (state === 'active') { console.log(line); continue; }
    bad += 1;
    console.warn(line);
    if (dated.has(sid)) {
      console.warn(`  first error alert in the window: ${dated.get(sid)}`);
    }
    if (state === 'unused') {
      console.warn('  repair: point a subscription at this sink, or delete it so it ' +
                   'stops looking like observability.');
      continue;
    }
    console.warn('  repair: fix the destination or its credentials, validate the sink ' +
                 `at ${EVENTS}/Sinks/${sid}/Validate with a TestId, then re-attach it ` +
                 `at ${EVENTS}/Subscriptions/{SubscriptionSid} with SinkSid=${sid}. ` +
                 'Fixing the endpoint alone does not restart delivery.');
  }

  console.log(`${sinks.length} sink(s), ${bad} dropping events`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The join is the diagnosis, so it is tested first: a subscription with no <code>sink_sid</code> is skipped, and two subscriptions on one sink both count. After that the tests are about how loudly to say things &mdash; a failed sink with subscriptions is an outage, a failed sink with none is litter, and an active sink nothing subscribes to is the trap people create while repairing the first one.",
"test_py_file": "test_twilio_event_sink_audit.py",
"test_py": '''from twilio_event_sink_audit import subscribers, verdict

SINK = "DG11111111111111111111111111111111"


def sink(status="active", kind="webhook", sid=SINK):
    return {"sid": sid, "status": status, "sink_type": kind,
            "description": "warehouse"}


def subscription(sid="DF1", sink_sid=SINK):
    return {"sid": sid, "sink_sid": sink_sid}


def test_subscribers_joins_on_sink_sid():
    feeds = subscribers([subscription("DF1"), subscription("DF2"),
                         subscription("DF3", "DG99")])
    assert feeds[SINK] == ["DF1", "DF2"]
    assert feeds["DG99"] == ["DF3"]


def test_a_subscription_with_no_sink_is_skipped_not_crashed_on():
    assert subscribers([{"sid": "DF1"}, {"sid": "DF2", "sink_sid": ""}]) == {}
    assert subscribers(None) == {}


def test_a_failed_sink_with_subscriptions_is_the_outage():
    state, detail = verdict(sink("failed"), ["DF1", "DF2"])
    assert state == "failed"
    assert "2 subscription(s)" in detail
    assert "being dropped" in detail


def test_a_failed_sink_nothing_feeds_is_litter_not_an_outage():
    state, detail = verdict(sink("failed"), [])
    assert state == "failed-detached"
    assert "left behind" in detail


def test_initialized_and_validating_never_delivered_anything():
    for status in ("initialized", "validating"):
        state, detail = verdict(sink(status), ["DF1"])
        assert state == "unvalidated"
        assert "never delivered a single event" in detail


def test_an_active_sink_with_no_subscription_delivers_nothing():
    # The failure mode people create while fixing the other one: the sink is
    # green in the list and carries no events at all.
    state, detail = verdict(sink("active"), [])
    assert state == "unused"
    assert "delivers nothing" in detail


def test_an_active_sink_with_a_subscription_is_healthy():
    state, detail = verdict(sink("active"), ["DF1"])
    assert state == "active"
    assert "DF1" in detail


def test_an_unrecognised_status_is_reported_rather_than_assumed_healthy():
    assert verdict(sink("paused"), ["DF1"])[0] == "unknown-status"
    assert verdict(sink(""), ["DF1"])[0] == "unknown-status"
''',
"test_js_file": "twilio-event-sink-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { subscribers, verdict } from './twilio-event-sink-audit.mjs';

const SINK = 'DG11111111111111111111111111111111';

const sink = (status = 'active', kind = 'webhook', sid = SINK) => ({
  sid, status, sink_type: kind, description: 'warehouse',
});

const subscription = (sid = 'DF1', sinkSid = SINK) => ({ sid, sink_sid: sinkSid });

test('subscribers joins on sink_sid', () => {
  const feeds = subscribers([subscription('DF1'), subscription('DF2'),
                             subscription('DF3', 'DG99')]);
  assert.deepEqual(feeds.get(SINK), ['DF1', 'DF2']);
  assert.deepEqual(feeds.get('DG99'), ['DF3']);
});

test('a subscription with no sink is skipped, not crashed on', () => {
  assert.equal(subscribers([{ sid: 'DF1' }, { sid: 'DF2', sink_sid: '' }]).size, 0);
  assert.equal(subscribers(null).size, 0);
});

test('a failed sink with subscriptions is the outage', () => {
  const [state, detail] = verdict(sink('failed'), ['DF1', 'DF2']);
  assert.equal(state, 'failed');
  assert.match(detail, /2 subscription\\(s\\)/);
  assert.match(detail, /being dropped/);
});

test('a failed sink nothing feeds is litter, not an outage', () => {
  const [state, detail] = verdict(sink('failed'), []);
  assert.equal(state, 'failed-detached');
  assert.match(detail, /left behind/);
});

test('initialized and validating never delivered anything', () => {
  for (const status of ['initialized', 'validating']) {
    const [state, detail] = verdict(sink(status), ['DF1']);
    assert.equal(state, 'unvalidated');
    assert.match(detail, /never delivered a single event/);
  }
});

test('an active sink with no subscription delivers nothing', () => {
  const [state, detail] = verdict(sink('active'), []);
  assert.equal(state, 'unused');
  assert.match(detail, /delivers nothing/);
});

test('an active sink with a subscription is healthy', () => {
  const [state, detail] = verdict(sink('active'), ['DF1']);
  assert.equal(state, 'active');
  assert.match(detail, /DF1/);
});

test('an unrecognised status is reported rather than assumed healthy', () => {
  assert.equal(verdict(sink('paused'), ['DF1'])[0], 'unknown-status');
  assert.equal(verdict(sink(''), ['DF1'])[0], 'unknown-status');
});
''',
"faq": [
 ("What makes a sink go from active to failed?",
  "The destination stopped accepting delivery: a webhook that did not respond inside its timeout, a Kinesis stream whose credentials expired or whose permissions changed, an endpoint that started returning 5xx. Twilio marks the sink failed and stops delivering rather than queueing indefinitely."),
 ("Will Twilio start delivering again once my endpoint is healthy?",
  "No. A failed sink stays failed. It has to be validated again with a test event and the subscriptions re-attached, which is why a team can fix the endpoint, watch it return 200 to their own curl, and still receive nothing at all."),
 ("Is initialized or validating the same problem as failed?",
  "Not at all, and the script says so separately. Those two mean the sink was created and validation was never completed, so it has never delivered a single event. There is no gap in the data because there was never any data, and the fix is finishing the setup rather than investigating an outage."),
 ("Why check subscriptions as well as sinks?",
  "Because they are separate resources and only the join answers the question. A failed sink with no subscription is dead litter; a failed sink with three subscriptions is losing everything those subscriptions carry. The same status field means both, so reading it alone cannot tell you which."),
 ("Are the Debugger alerts enough to catch this on their own?",
  "They are a good cross-check and a poor monitor. The sink failure notice repeats while the sink is down, so it dates the outage, but alerts are retained for 30 days and an older failure leaves nothing behind. The status field on the sink is true whether or not anybody was reading alerts at the time."),
],
"related": [
 ("/twilio/messaging-service-no-status-callback/", "A Messaging Service with no delivery signal"),
 ("/twilio/conversations-webhook-url-missing/", "A conversation webhook with no URL: 50369"),
 ("/twilio/webhook-connection-timeout-11205/", "Twilio failing to connect to your webhook"),
],
"citations": [CITE_SINK, CITE_SUB, CITE_DELIVERY, CITE_ALERTS],
},

]
