#!/usr/bin/env python3
"""/twilio/ field notes, batch W — the writing.

Four failures in the parts of Twilio that are configured once and then trusted:
a Studio Flow whose definition does not compile, a Conversations webhook that
subscribes to no events, a conversation already holding the five webhooks it is
allowed, and a Sync Service whose callbacks are either rejected or suppressed.
Read-only throughout: an API Key with read access, never the account auth token,
and the repair is printed for a human to run.
"""

CITE_FLOW = ("Studio Flow resource (v2) — Twilio Docs",
             "https://www.twilio.com/docs/studio/rest-api/v2/flow")
CITE_FLOW_VALIDATE = ("Studio Flow Validate resource (v2) — Twilio Docs",
                      "https://www.twilio.com/docs/studio/rest-api/v2/flow-validate")
CITE_EXEC = ("Studio Execution resource (v2) — Twilio Docs",
             "https://www.twilio.com/docs/studio/rest-api/v2/execution")
CITE_STUDIO_FAQ = ("Studio FAQ — Twilio Docs",
                   "https://www.twilio.com/docs/studio/user-guide/studio-faq")
CITE_CONV_CONFIG = ("Conversations webhook configuration resource — Twilio Docs",
                    "https://www.twilio.com/docs/conversations/api/webhook-configuration-resource")
CITE_CONV_HOOKS = ("Conversations webhooks — Twilio Docs",
                   "https://www.twilio.com/docs/conversations/conversations-webhooks")
CITE_CONV_HOOK = ("Conversation-scoped webhook resource — Twilio Docs",
                  "https://www.twilio.com/docs/conversations/api/conversation-scoped-webhook-resource")
CITE_CONV = ("Conversation resource — Twilio Docs",
             "https://www.twilio.com/docs/conversations/api/conversation-resource")
CITE_50361 = ("Error 50361: too many conversation webhooks — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/50361")
CITE_54051 = ("Error 54051: invalid webhook URL — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/54051")
CITE_SYNC = ("Sync Service resource — Twilio Docs",
             "https://www.twilio.com/docs/sync/api/service")
CITE_ALERTS = ("Monitor Alert resource — Twilio Docs",
               "https://www.twilio.com/docs/usage/monitor-alert")
CITE_WEBHOOKS = ("Webhooks (HTTP callbacks) — Twilio Docs",
                 "https://www.twilio.com/docs/usage/webhooks")

GUIDES = [

{
"slug": "studio-flow-invalid-definition",
"title": "A Studio Flow whose definition is invalid, so widgets never run",
"description": "The Console draws the canvas and valid is false. A transition to a deleted widget leaves the definition uncompilable, and executions stop at the break.",
"h1": "a Studio Flow whose definition is invalid, so widgets never run",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio studio flow invalid", "studio flow valid false",
             "twilio studio flow errors array", "studio flow validate",
             "twilio studio widget never runs"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The Flow looks finished. The canvas renders, the widgets are connected, the Console opens it and saves it without complaint. But executions end two widgets in, or skip a branch that is plainly drawn on screen, and <code>valid</code> on the Flow resource is <code>false</code>. The picture is a drawing of a definition, and the drawing does not stop being tidy when the definition stops compiling.",
"short_answer": """<p>Read <code>GET https://studio.twilio.com/v2/Flows/{FlowSid}</code> and look at <code>valid</code>. When it is <code>false</code>, the diagnosis is already in the same response: <code>errors[]</code> holds one entry per fault, each with a <code>message</code> and the <code>path</code> of the widget that caused it.</p>
<p><code>warnings[]</code> is the other array and is not the same finding. A warning does not make a definition invalid; it flags something that will behave oddly rather than something that stops it running. Report the two in separate columns, or one real outage arrives buried in eleven notes about naming.</p>""",
"problem": """<p>An invalid definition fails in the middle of a call. The execution starts, runs the widgets it can, and stops where the definition breaks &mdash; so the caller hears the greeting and then silence, or the SMS branch that should have replied never fires. There is nothing wrong with the number, nothing wrong with the webhook, and nothing wrong with the Flow's <code>status</code>: it can be <code>published</code>, live, and taking traffic while <code>valid</code> is <code>false</code>.</p>
<p>The Console is no help because the canvas keeps drawing. Deleting a widget removes the box; it does not remove the transitions in other widgets that named it, and a transition with no destination simply draws no line. Nothing on screen turns red. The only place the fault is stated in words is <code>errors[]</code> on the Flow resource, and that is a field you have to go and ask for.</p>""",
"why": """<p><strong>The canvas and the definition are not the same object.</strong> Studio renders a picture from the Flow's JSON, and rendering is forgiving: a widget whose transition points at something that no longer exists is drawn as a widget with one fewer arrow. Compiling is not forgiving. The two disagree, and only one of them is what runs.</p>
<p><strong>Deleting a widget does not delete what pointed at it.</strong> This is the most common single cause. Somebody removes a step that is no longer needed, the widgets that transitioned into it keep the reference, and the definition is invalid from that save onwards even though the visible change was a deletion nobody could get wrong.</p>
<p><strong>Liquid is not checked while you type it.</strong> A template referencing a variable from a widget that was renamed, or a filter with the wrong number of arguments, is accepted into the definition and reported later as an error against that widget's <code>path</code>. The person who renamed the widget is not the person who wrote the template.</p>
<p><strong>An invalid draft and an invalid published Flow need opposite advice.</strong> A draft that does not compile cannot be published at all, so telling anyone to press Publish is wrong: the widget has to be fixed first. A published Flow that is invalid is failing executions right now. The same <code>valid: false</code> means both, which is why the script reads <code>status</code> alongside it rather than reporting one line for every case.</p>""",
"steps": [
 {"h": "List the Flows, then fetch each one",
  "body": """<p><code>GET https://studio.twilio.com/v2/Flows?PageSize=50</code>, following <code>meta.next_page_url</code>, gives you the SIDs. The diagnosis comes from <code>GET https://studio.twilio.com/v2/Flows/{FlowSid}</code>: that is the fetch that carries <code>errors[]</code> and <code>warnings[]</code>, and without them all you have is a boolean saying something is wrong somewhere.</p>"""},
 {"h": "Read valid before you read anything else",
  "body": """<p><code>valid</code> is the finding. <code>status</code> only tells you who is affected: <code>published</code> means executions are hitting the fault now, <code>draft</code> means the last published revision is still serving and the publish is blocked until the widget is fixed.</p>"""},
 {"h": "Take the path, not just the message",
  "body": """<p>Each entry in <code>errors[]</code> carries a <code>message</code> and a <code>path</code>. The message is what broke; the path is where. A report that prints only messages sends somebody hunting through a canvas with forty widgets on it for a transition that names a widget that is not there.</p>"""},
 {"h": "Keep warnings in their own column",
  "body": """<p><code>warnings[]</code> can be populated on a Flow whose <code>valid</code> is <code>true</code>. Those are worth reading and they are not this outage. Fold them into the error list and the report grows a long tail that gets skimmed, which is how the one entry that mattered stops being read.</p>"""},
 {"h": "Fix the widget, validate, then publish",
  "body": """<p>Repair the widget named by <code>path</code>, then check the definition against <code>https://studio.twilio.com/v2/Flows/Validate</code> before you publish it &mdash; that endpoint answers the compile question without touching the live Flow. Leave this audit on a schedule: the fault arrives with an ordinary edit, not with a deploy, so nothing in your release process is watching for it.</p>"""},
],
"verify": """<p>Re-run after the fix. Every flow should report <code>valid</code>, and the count of definitions that do not compile should be zero.</p>
<pre><code class="language-bash">python3 twilio_studio_flow_validity_audit.py
# 7 flow(s), 0 with a definition that does not compile</code></pre>""",
"code_intro": "One paginated GET for the Flows and one GET per flow for the detail, on an API Key with read access and nothing else. Two pure functions carry the judgement: one normalises <code>errors[]</code> and <code>warnings[]</code> into deduplicated path-and-message pairs, and one decides which of the five situations a flow is in. Both are worth reading on their own, because the whole note is the difference between an invalid draft and an invalid published Flow.",
"py_file": "twilio_studio_flow_validity_audit.py",
"py": '''"""Report Twilio Studio Flows whose definition does not compile.

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
log = logging.getLogger("twilio_studio_flow_validity_audit")

STUDIO = "https://studio.twilio.com/v2"


def normalise(entries):
    """Reduce errors[] or warnings[] to deduplicated (path, message) pairs. Pure.

    Each entry names the widget in `path` and what broke in `message`. Entries
    that arrive as a bare string are kept with an empty path rather than
    dropped: a finding with no location is still a finding, and silently losing
    it is worse than printing it without one.

    The same fault is reported once per referencing transition, so a single
    deleted widget can produce four identical entries. Deduplicating here keeps
    the report a list of problems rather than a list of mentions.
    """
    out = []
    for e in entries or []:
        if isinstance(e, dict):
            path = str(e.get("path") or "").strip()
            message = str(e.get("message") or "").strip()
        else:
            path, message = "", str(e or "").strip()
        if not (path or message):
            continue
        pair = (path, message)
        if pair not in out:
            out.append(pair)
    return out


def verdict(flow):
    """Classify one Studio Flow by whether its definition compiles. Pure, so the
    five cases sit together instead of being spread through a request loop.

    `status` does not change the finding, only who is affected by it: a
    published Flow is failing executions now, a draft cannot be published until
    the widget is fixed. Returns (state, detail).
    """
    valid = flow.get("valid")
    status = str(flow.get("status") or "").lower()
    errors = normalise(flow.get("errors"))
    warnings = normalise(flow.get("warnings"))

    if valid is None:
        return ("unknown",
                "no valid field on this response: read the single flow at "
                "/v2/Flows/{FlowSid}, which is where errors[] and warnings[] "
                "are carried.")

    if valid is False:
        where = errors[0][0] if errors and errors[0][0] else "an unnamed widget"
        what = errors[0][1] if errors else "no message returned with the error"
        if not errors:
            detail = ("definition does not compile but errors[] came back empty. "
                      "Fetch the flow on its own; the list view is not where the "
                      "detail lives.")
        elif status == "published":
            detail = ("published and does not compile: executions stop at the "
                      "fault. %d error(s), first at %s: %s"
                      % (len(errors), where, what))
        else:
            detail = ("draft and does not compile, so it cannot be published at "
                      "all. %d error(s), first at %s: %s"
                      % (len(errors), where, what))
        return ("invalid-published" if status == "published" else "invalid-draft",
                detail)

    if warnings:
        return ("warnings",
                "compiles, with %d warning(s), first at %s: %s"
                % (len(warnings), warnings[0][0] or "an unnamed widget",
                   warnings[0][1] or "no message"))

    return ("valid", "definition compiles with no errors or warnings")


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def paged(session, url, key, limit, **first):
    """Page a studio.twilio.com list. meta.next_page_url is absolute."""
    params = dict(first)
    params.setdefault("PageSize", 50)
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
                    help="stop after this many flows")
    ap.add_argument("--warnings", action="store_true",
                    help="also report flows that compile but carry warnings")
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

    flows = paged(session, STUDIO + "/Flows", "flows", args.max_flows)
    if not flows:
        log.info("no Studio Flows on this account")
        return 0

    bad = 0
    for listed in flows:
        # The list gives the SIDs; errors[] and warnings[] come from the
        # single-flow fetch, and without them there is nothing to report but a
        # boolean saying something somewhere is wrong.
        flow = get(session, "%s/Flows/%s" % (STUDIO, listed.get("sid")))
        state, detail = verdict(flow)
        line = "%-18s %s  %s" % (state, flow.get("friendly_name") or flow.get("sid"),
                                 detail)

        if state == "valid":
            log.info(line)
            continue
        if state == "warnings" and not args.warnings:
            log.info("%-18s %s  %d warning(s); re-run with --warnings to see them",
                     state, flow.get("friendly_name") or flow.get("sid"),
                     len(normalise(flow.get("warnings"))))
            continue

        bad += 1
        log.warning(line)
        for path, message in normalise(flow.get("errors")):
            log.warning("  error at %s: %s", path or "(no path)", message)
        if state.startswith("invalid"):
            log.warning("  repair: fix the widget at that path in %s, check the "
                        "definition against %s/Flows/Validate, then republish.",
                        flow.get("sid"), STUDIO)

    log.info("%d flow(s), %d with a definition that does not compile",
             len(flows), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-studio-flow-validity-audit.mjs",
"js": '''/**
 * Report Twilio Studio Flows whose definition does not compile.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const STUDIO = 'https://studio.twilio.com/v2';

/**
 * Reduce errors[] or warnings[] to deduplicated [path, message] pairs. Pure.
 *
 * Entries that arrive as a bare string keep an empty path rather than being
 * dropped. The same fault is reported once per referencing transition, so one
 * deleted widget can produce four identical entries; deduplicating here keeps
 * the report a list of problems rather than a list of mentions.
 */
export function normalise(entries) {
  const out = [];
  const seen = new Set();
  for (const e of entries ?? []) {
    let path = '';
    let message = '';
    if (e && typeof e === 'object') {
      path = String(e.path ?? '').trim();
      message = String(e.message ?? '').trim();
    } else {
      message = String(e ?? '').trim();
    }
    if (!path && !message) continue;
    const key = `${path}\\u0000${message}`;
    if (seen.has(key)) continue;
    seen.add(key);
    out.push([path, message]);
  }
  return out;
}

/**
 * Classify one Studio Flow by whether its definition compiles. Pure.
 *
 * `status` does not change the finding, only who is affected by it: a published
 * Flow is failing executions now, a draft cannot be published until the widget
 * is fixed. Returns [state, detail].
 */
export function verdict(flow) {
  const valid = flow.valid;
  const status = String(flow.status ?? '').toLowerCase();
  const errors = normalise(flow.errors);
  const warnings = normalise(flow.warnings);

  if (valid === null || valid === undefined) {
    return ['unknown',
      'no valid field on this response: read the single flow at ' +
      '/v2/Flows/{FlowSid}, which is where errors[] and warnings[] are carried.'];
  }

  if (valid === false) {
    const where = errors.length && errors[0][0] ? errors[0][0] : 'an unnamed widget';
    const what = errors.length ? errors[0][1] : 'no message returned with the error';
    let detail;
    if (!errors.length) {
      detail = 'definition does not compile but errors[] came back empty. Fetch ' +
        'the flow on its own; the list view is not where the detail lives.';
    } else if (status === 'published') {
      detail = `published and does not compile: executions stop at the fault. ` +
        `${errors.length} error(s), first at ${where}: ${what}`;
    } else {
      detail = 'draft and does not compile, so it cannot be published at all. ' +
        `${errors.length} error(s), first at ${where}: ${what}`;
    }
    return [status === 'published' ? 'invalid-published' : 'invalid-draft', detail];
  }

  if (warnings.length) {
    return ['warnings',
      `compiles, with ${warnings.length} warning(s), first at ` +
      `${warnings[0][0] || 'an unnamed widget'}: ${warnings[0][1] || 'no message'}`];
  }

  return ['valid', 'definition compiles with no errors or warnings'];
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

async function paged(auth, url, key, limit, first = {}) {
  let params = { PageSize: 50, ...first };
  const out = [];
  while (url && out.length < limit) {
    const page = await get(auth, url, params);
    out.push(...(page[key] ?? []));
    url = (page.meta ?? {}).next_page_url ?? null;
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
  const showWarnings = process.argv.includes('--warnings');

  const flows = await paged(auth, `${STUDIO}/Flows`, 'flows', 200);
  if (!flows.length) {
    console.log('no Studio Flows on this account');
    return;
  }

  let bad = 0;
  for (const listed of flows) {
    const flow = await get(auth, `${STUDIO}/Flows/${listed.sid}`);
    const [state, detail] = verdict(flow);
    const name = flow.friendly_name || flow.sid;
    const line = `${state.padEnd(18)} ${name}  ${detail}`;

    if (state === 'valid') { console.log(line); continue; }
    if (state === 'warnings' && !showWarnings) {
      console.log(`${state.padEnd(18)} ${name}  ` +
                  `${normalise(flow.warnings).length} warning(s); re-run with ` +
                  '--warnings to see them');
      continue;
    }

    bad += 1;
    console.warn(line);
    for (const [path, message] of normalise(flow.errors)) {
      console.warn(`  error at ${path || '(no path)'}: ${message}`);
    }
    if (state.startsWith('invalid')) {
      console.warn(`  repair: fix the widget at that path in ${flow.sid}, check ` +
                   `the definition against ${STUDIO}/Flows/Validate, then republish.`);
    }
  }

  console.log(`${flows.length} flow(s), ${bad} with a definition that does not compile`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The cases worth pinning are the ones that decide what a human is told to do: an invalid published Flow, which is an outage, against an invalid draft, which must not be told to press Publish. Then the ones that make a report unreadable &mdash; four copies of the same error from four transitions into one deleted widget, and a warning on a Flow that compiles perfectly well.",
"test_py_file": "test_twilio_studio_flow_validity_audit.py",
"test_py": '''from twilio_studio_flow_validity_audit import normalise, verdict


def flow(**kw):
    base = {"sid": "FW1", "friendly_name": "support", "status": "published",
            "valid": True, "errors": [], "warnings": []}
    base.update(kw)
    return base


def test_published_and_invalid_is_an_outage_now():
    state, detail = verdict(flow(valid=False, errors=[
        {"path": "states[3].transitions[0]", "message": "unknown next widget"}]))
    assert state == "invalid-published"
    assert "executions stop" in detail
    assert "states[3].transitions[0]" in detail


def test_draft_and_invalid_is_never_told_to_publish():
    state, detail = verdict(flow(status="draft", valid=False, errors=[
        {"path": "states[1]", "message": "liquid syntax error"}]))
    assert state == "invalid-draft"
    assert "cannot be published" in detail


def test_one_deleted_widget_reported_four_times_is_one_error():
    entry = {"path": "states[2]", "message": "transition to a deleted widget"}
    state, detail = verdict(flow(valid=False, errors=[entry, dict(entry),
                                                      dict(entry), dict(entry)]))
    assert state == "invalid-published"
    assert "1 error(s)" in detail


def test_warnings_do_not_make_a_flow_invalid():
    state, detail = verdict(flow(warnings=[{"path": "states[0]",
                                            "message": "widget name is not unique"}]))
    assert state == "warnings"
    assert "compiles" in detail


def test_a_clean_flow_is_valid():
    assert verdict(flow())[0] == "valid"


def test_invalid_with_an_empty_errors_array_says_where_to_look():
    state, detail = verdict(flow(valid=False, errors=[]))
    assert state == "invalid-published"
    assert "Fetch the flow on its own" in detail


def test_a_response_with_no_valid_field_is_not_assumed_healthy():
    listed = flow()
    del listed["valid"]
    assert verdict(listed)[0] == "unknown"


def test_normalise_keeps_string_entries_and_drops_empty_ones():
    assert normalise(["transition to a deleted widget", {}, None, ""]) == \\
        [("", "transition to a deleted widget")]
''',
"test_js_file": "twilio-studio-flow-validity-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { normalise, verdict } from './twilio-studio-flow-validity-audit.mjs';

const flow = (kw = {}) => ({
  sid: 'FW1', friendly_name: 'support', status: 'published', valid: true,
  errors: [], warnings: [], ...kw,
});

test('published and invalid is an outage now', () => {
  const [state, detail] = verdict(flow({
    valid: false,
    errors: [{ path: 'states[3].transitions[0]', message: 'unknown next widget' }],
  }));
  assert.equal(state, 'invalid-published');
  assert.match(detail, /executions stop/);
  assert.match(detail, /states\\[3\\]/);
});

test('draft and invalid is never told to publish', () => {
  const [state, detail] = verdict(flow({
    status: 'draft', valid: false,
    errors: [{ path: 'states[1]', message: 'liquid syntax error' }],
  }));
  assert.equal(state, 'invalid-draft');
  assert.match(detail, /cannot be published/);
});

test('one deleted widget reported four times is one error', () => {
  const entry = { path: 'states[2]', message: 'transition to a deleted widget' };
  const [state, detail] = verdict(flow({
    valid: false, errors: [entry, { ...entry }, { ...entry }, { ...entry }],
  }));
  assert.equal(state, 'invalid-published');
  assert.match(detail, /1 error\\(s\\)/);
});

test('warnings do not make a flow invalid', () => {
  const [state, detail] = verdict(flow({
    warnings: [{ path: 'states[0]', message: 'widget name is not unique' }],
  }));
  assert.equal(state, 'warnings');
  assert.match(detail, /compiles/);
});

test('a clean flow is valid', () => {
  assert.equal(verdict(flow())[0], 'valid');
});

test('invalid with an empty errors array says where to look', () => {
  const [state, detail] = verdict(flow({ valid: false, errors: [] }));
  assert.equal(state, 'invalid-published');
  assert.match(detail, /Fetch the flow on its own/);
});

test('a response with no valid field is not assumed healthy', () => {
  const listed = flow();
  delete listed.valid;
  assert.equal(verdict(listed)[0], 'unknown');
});

test('normalise keeps string entries and drops empty ones', () => {
  assert.deepEqual(normalise(['transition to a deleted widget', {}, null, '']),
    [['', 'transition to a deleted widget']]);
});
''',
"faq": [
 ("What actually makes a Studio definition invalid?",
  "Structural faults in the JSON behind the canvas: a transition naming a widget that has been deleted, a required field on a widget left empty, or Liquid that does not parse. Each one is reported as an entry in errors[] with the path of the widget it belongs to."),
 ("Why does the Console still render a Flow that does not compile?",
  "Because rendering and compiling are different operations on the same JSON. Drawing a widget whose transition points at nothing produces a widget with one fewer arrow, which looks like a widget that simply has fewer arrows. Nothing turns red, so the canvas is not where you find this."),
 ("Is a warning worth fixing?",
  "Often yes, but not urgently, and not in the same list. warnings[] can be populated on a Flow whose valid is true; those Flows run. Mixing warnings into the error report is how the one line that meant an outage ends up eleventh in a list nobody finishes reading."),
 ("Can I just press Publish and see whether it takes?",
  "Not on an invalid definition, which is why the script separates a draft from a published Flow. The safe way to ask the question is the Validate endpoint: it answers whether a definition compiles without touching what is live."),
 ("Why fetch every flow separately instead of reading the list?",
  "Because the diagnosis is errors[] and warnings[], and those are read from the single-flow fetch at /v2/Flows/{FlowSid}. An account with two hundred Flows costs two hundred and a few GETs, which is a cheap price for a report that names the widget rather than the Flow."),
],
"related": [
 ("/twilio/studio-flow-draft-not-published/", "A Studio Flow left in draft, live nowhere"),
 ("/twilio/studio-flow-not-wired-to-number/", "A published Flow no number points at"),
 ("/twilio/twiml-document-parse-failure-12100/", "TwiML that fails to parse: 12100"),
],
"citations": [CITE_FLOW, CITE_FLOW_VALIDATE, CITE_EXEC, CITE_STUDIO_FAQ],
},


{
"slug": "conversations-webhook-filters-empty",
"title": "Conversations webhooks fire for nothing when filters are empty",
"description": "post_webhook_url is set and correct and nothing ever arrives. Conversations delivers only the events named in filters, and an empty list names none of them.",
"h1": "Conversations webhooks fire for nothing when filters are empty",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio conversations filters empty", "onMessageAdded not firing",
             "post_webhook_url not called", "conversations webhook configuration",
             "twilio conversations no events"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "<code>post_webhook_url</code> is set. It is the right URL, it is HTTPS, and curl gets a <code>200</code> out of it in a second. Messages are being added to conversations all day, and your endpoint has never once been called. There is no error code to look up, because nothing failed: Conversations delivered every event it was asked for, and it was asked for none.",
"short_answer": """<p>Read <code>GET https://conversations.twilio.com/v1/Configuration/Webhooks</code> and look at <code>filters</code> next to <code>post_webhook_url</code> and <code>pre_webhook_url</code>. <code>filters</code> is an allowlist: only the event names in it are ever delivered, and an empty list delivers nothing at all.</p>
<p>The second trap is the tense. Post-action names end in <code>-ed</code> &mdash; <code>onMessageAdded</code>, <code>onConversationStateUpdated</code> &mdash; and go to <code>post_webhook_url</code>; the pre-action name is <code>onMessageAdd</code>, it fires before the action is committed, and it goes to <code>pre_webhook_url</code>. One filter list feeds both, so a list of pre-action names with only a post URL configured is the same silence with a longer configuration.</p>""",
"problem": """<p>This is a subscription with nothing subscribed. The configuration is present, populated and correct on every field a review would look at, and the one field that decides whether anything is sent holds an empty array. Twilio raises nothing, because there is no failure: no delivery was attempted, so no delivery failed. The Debugger stays empty, the conversation transcripts are complete, and the application simply never learns that any of it happened.</p>
<p>It is usually a partial setup. Someone configures the URL first, intending to come back for the filters, and the URL is the part that feels like the work. Or a later update sets one filter to add an event and replaces the whole list in doing so, quietly unsubscribing from the three that were already there. Both leave a configuration that reads as finished.</p>""",
"why": """<p><strong>filters is an allowlist, not a mute list.</strong> An empty list is not "no exclusions", it is "no events". That reading is the entire bug, and it is the opposite of how almost every other filter field in every other product behaves.</p>
<p><strong>The default is deliberately narrow.</strong> Conversations does not subscribe you to everything, because a post-action webhook that fires on every event can drive an integration that writes back into the conversation into a loop. Narrow by default is the right choice and it means the working configuration is always something you built, never something you inherited.</p>
<p><strong>One list serves two webhooks with two naming conventions.</strong> The <code>-ed</code> suffix is the only thing separating an event that fires after the fact from one that fires before it and can reject the action. Put <code>onMessageAdd</code> in the list, set only <code>post_webhook_url</code>, and the configuration is coherent, well-formed, and delivers nothing to the URL you set.</p>
<p><strong>An update replaces the list rather than adding to it.</strong> The configuration is one resource that you overwrite, so the safe change is always "send the full set of filters you want", and the natural change &mdash; sending the one you are adding &mdash; drops the rest without saying so.</p>""",
"steps": [
 {"h": "Read the configuration as one object",
  "body": """<p><code>GET https://conversations.twilio.com/v1/Configuration/Webhooks</code>. It is a singleton, not a list: one response carrying <code>pre_webhook_url</code>, <code>post_webhook_url</code>, <code>method</code> and <code>filters</code>. Every finding in this note is a relationship between those four fields, which is why the check reads them together.</p>"""},
 {"h": "Write down the events your code actually handles",
  "body": """<p>The audit needs a required list or it can only tell you that <code>filters</code> is empty. Take the event names your handler branches on &mdash; usually <code>onMessageAdded</code>, often <code>onConversationStateUpdated</code> and <code>onParticipantAdded</code> &mdash; and pass them in. Anything your code handles that Conversations is not sending is a silent gap.</p>"""},
 {"h": "Check the tense against the URL that is set",
  "body": """<p>Split the filter list on the <code>-ed</code> suffix. Post-action names need <code>post_webhook_url</code>; pre-action names need <code>pre_webhook_url</code>. A list that is entirely one kind while only the other URL is configured is a configuration that cannot deliver, and it looks busier than an empty one.</p>"""},
 {"h": "Treat every update as a replacement",
  "body": """<p>Because the resource is overwritten, the repair is the complete set: <code>Filters=onMessageAdded&amp;Filters=onConversationStateUpdated&amp;Filters=onParticipantAdded</code>, repeating the parameter once per event. Sending only the new one is how a working integration loses the two events it had.</p>"""},
 {"h": "Check the per-service configurations too",
  "body": """<p>An account with more than the default Conversations service carries a webhook configuration per service, and each has its own <code>filters</code>. The script does this under <code>--services</code> rather than by default, because on most accounts the account-level configuration is the whole story and an extra pass is noise.</p>"""},
],
"verify": """<p>Re-run with the events your handler needs. Every configuration should report <code>ok</code>.</p>
<pre><code class="language-bash">python3 twilio_conversations_filter_audit.py --require onMessageAdded,onParticipantAdded
# 1 configuration(s), 0 delivering nothing</code></pre>""",
"code_intro": "One GET for the account-level configuration, and one per service under <code>--services</code>, on an API Key with read access. The pure part is the pair of functions that split a filter list by tense and then judge the configuration against the events you say you need &mdash; the whole note lives in those two, and neither of them should need a Twilio account to test.",
"py_file": "twilio_conversations_filter_audit.py",
"py": '''"""Report Conversations webhook configurations that deliver no events.

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
log = logging.getLogger("twilio_conversations_filter_audit")

CONVERSATIONS = "https://conversations.twilio.com/v1"

DEFAULT_REQUIRED = ("onMessageAdded",)


def split_filters(filters):
    """Split a filter list into (pre_action, post_action) names. Pure.

    Post-action names are past tense: onMessageAdded fires once the message is
    committed and is delivered to post_webhook_url. The pre-action name is
    onMessageAdd, it fires before the action and can reject it, and it goes to
    pre_webhook_url. One list feeds both webhooks and the suffix is the only
    thing separating the two halves.
    """
    pre, post = [], []
    for f in filters or []:
        name = str(f or "").strip()
        if not name:
            continue
        (post if name.endswith("ed") else pre).append(name)
    return pre, post


def verdict(config, required=DEFAULT_REQUIRED):
    """Classify one Conversations webhook configuration. Pure.

    `required` is the set of events the application actually handles. Without it
    the check can only say whether filters is empty, which misses the far more
    common case of a list that is populated and short of the one event the code
    is waiting for. Returns (state, detail).
    """
    post_url = str(config.get("post_webhook_url") or "").strip()
    pre_url = str(config.get("pre_webhook_url") or "").strip()
    pre, post = split_filters(config.get("filters"))
    wanted = [str(r).strip() for r in (required or []) if str(r).strip()]
    total = len(pre) + len(post)

    if not (post_url or pre_url):
        return ("no-webhook",
                "neither pre_webhook_url nor post_webhook_url is set, so the "
                "filter list has nowhere to deliver to.")

    if total == 0:
        return ("no-filters",
                "a webhook URL is set and filters is empty. filters is an "
                "allowlist, so no event is delivered and nothing fails.")

    if post_url and not post:
        return ("post-url-no-post-filters",
                "post_webhook_url is set but every filter is a pre-action name "
                "(%s). Post-action names end in -ed; the post webhook fires for "
                "nothing." % ", ".join(pre))

    if pre_url and not pre:
        return ("pre-url-no-pre-filters",
                "pre_webhook_url is set but every filter is a post-action name, "
                "so nothing is ever sent to it before an action is committed.")

    missing = [w for w in wanted if w not in pre and w not in post]
    if missing:
        return ("missing-events",
                "delivering %d event type(s) but not %s, and an event that is "
                "not in filters is dropped without a trace."
                % (total, ", ".join(missing)))

    return ("ok", "delivering %d event type(s), including everything the "
                  "application asked for" % total)


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


def report(name, config, required):
    """Print one configuration's verdict. Returns 1 when it is a finding."""
    state, detail = verdict(config, required)
    line = "%-24s %s  %s" % (state, name, detail)
    if state == "ok":
        log.info(line)
        return 0
    log.warning(line)
    log.warning("  repair: update the webhook configuration with the complete "
                "filter list, repeating the parameter once per event: "
                "Filters=%s. An update replaces the list rather than adding to it.",
                "&Filters=".join(required))
    return 1


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--require", default=",".join(DEFAULT_REQUIRED),
                    help="comma-separated event names the application handles")
    ap.add_argument("--services", action="store_true",
                    help="also read the per-service webhook configurations")
    args = ap.parse_args()

    account = os.environ.get("TWILIO_ACCOUNT_SID")
    key = os.environ.get("TWILIO_API_KEY")
    secret = os.environ.get("TWILIO_API_SECRET")
    if not (account and key and secret):
        log.error("set TWILIO_ACCOUNT_SID, TWILIO_API_KEY and TWILIO_API_SECRET "
                  "(an API Key with read access, not the auth token)")
        return 2

    required = [r.strip() for r in args.require.split(",") if r.strip()]
    session = requests.Session()
    session.auth = (key, secret)

    checked = 1
    bad = report("account configuration",
                 get(session, CONVERSATIONS + "/Configuration/Webhooks"), required)

    if args.services:
        for svc in paged(session, CONVERSATIONS + "/Services", "services", 200):
            sid = svc.get("sid")
            try:
                config = get(session, "%s/Services/%s/Configuration/Webhooks"
                             % (CONVERSATIONS, sid))
            except requests.HTTPError as exc:
                log.info("%s: no readable webhook configuration (%s)", sid, exc)
                continue
            checked += 1
            bad += report(svc.get("friendly_name") or sid, config, required)

    log.info("%d configuration(s), %d delivering nothing the application needs",
             checked, bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-conversations-filter-audit.mjs",
"js": '''/**
 * Report Conversations webhook configurations that deliver no events.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const CONVERSATIONS = 'https://conversations.twilio.com/v1';

const DEFAULT_REQUIRED = ['onMessageAdded'];

/**
 * Split a filter list into [preAction, postAction] names. Pure.
 *
 * Post-action names are past tense: onMessageAdded fires once the message is
 * committed and is delivered to post_webhook_url. The pre-action name is
 * onMessageAdd, it fires before the action and can reject it, and it goes to
 * pre_webhook_url. One list feeds both webhooks and the suffix is the only
 * thing separating the two halves.
 */
export function splitFilters(filters) {
  const pre = [];
  const post = [];
  for (const f of filters ?? []) {
    const name = String(f ?? '').trim();
    if (!name) continue;
    (name.endsWith('ed') ? post : pre).push(name);
  }
  return [pre, post];
}

/**
 * Classify one Conversations webhook configuration. Pure.
 *
 * `required` is the set of events the application actually handles; without it
 * the check can only say whether filters is empty. Returns [state, detail].
 */
export function verdict(config, required = DEFAULT_REQUIRED) {
  const postUrl = String(config.post_webhook_url ?? '').trim();
  const preUrl = String(config.pre_webhook_url ?? '').trim();
  const [pre, post] = splitFilters(config.filters);
  const wanted = (required ?? []).map((r) => String(r).trim()).filter(Boolean);
  const total = pre.length + post.length;

  if (!postUrl && !preUrl) {
    return ['no-webhook',
      'neither pre_webhook_url nor post_webhook_url is set, so the filter list ' +
      'has nowhere to deliver to.'];
  }

  if (total === 0) {
    return ['no-filters',
      'a webhook URL is set and filters is empty. filters is an allowlist, so ' +
      'no event is delivered and nothing fails.'];
  }

  if (postUrl && post.length === 0) {
    return ['post-url-no-post-filters',
      `post_webhook_url is set but every filter is a pre-action name ` +
      `(${pre.join(', ')}). Post-action names end in -ed; the post webhook ` +
      'fires for nothing.'];
  }

  if (preUrl && pre.length === 0) {
    return ['pre-url-no-pre-filters',
      'pre_webhook_url is set but every filter is a post-action name, so ' +
      'nothing is ever sent to it before an action is committed.'];
  }

  const missing = wanted.filter((w) => !pre.includes(w) && !post.includes(w));
  if (missing.length) {
    return ['missing-events',
      `delivering ${total} event type(s) but not ${missing.join(', ')}, and an ` +
      'event that is not in filters is dropped without a trace.'];
  }

  return ['ok', `delivering ${total} event type(s), including everything the ` +
                'application asked for'];
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

async function paged(auth, url, key, limit, first = {}) {
  let params = { PageSize: 50, ...first };
  const out = [];
  while (url && out.length < limit) {
    const page = await get(auth, url, params);
    out.push(...(page[key] ?? []));
    url = (page.meta ?? {}).next_page_url ?? null;
    params = {};
  }
  return out.slice(0, limit);
}

function report(name, config, required) {
  const [state, detail] = verdict(config, required);
  const line = `${state.padEnd(24)} ${name}  ${detail}`;
  if (state === 'ok') { console.log(line); return 0; }
  console.warn(line);
  console.warn('  repair: update the webhook configuration with the complete ' +
               'filter list, repeating the parameter once per event: ' +
               `Filters=${required.join('&Filters=')}. An update replaces the ` +
               'list rather than adding to it.');
  return 1;
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

  const flag = process.argv.indexOf('--require');
  const required = flag === -1
    ? DEFAULT_REQUIRED
    : String(process.argv[flag + 1] ?? '').split(',').map((r) => r.trim()).filter(Boolean);

  let checked = 1;
  let bad = report('account configuration',
                   await get(auth, `${CONVERSATIONS}/Configuration/Webhooks`), required);

  if (process.argv.includes('--services')) {
    for (const svc of await paged(auth, `${CONVERSATIONS}/Services`, 'services', 200)) {
      let config;
      try {
        config = await get(auth, `${CONVERSATIONS}/Services/${svc.sid}/Configuration/Webhooks`);
      } catch (err) {
        console.log(`${svc.sid}: no readable webhook configuration (${err.message})`);
        continue;
      }
      checked += 1;
      bad += report(svc.friendly_name || svc.sid, config, required);
    }
  }

  console.log(`${checked} configuration(s), ${bad} delivering nothing the ` +
              'application needs');
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Three cases carry this note. An empty <code>filters</code> with a perfectly good URL, which is the headline. A list of pre-action names against a post URL, which is the same silence dressed up as configuration. And a populated list missing exactly one required event, which is the version that runs in production for months because most of the integration works.",
"test_py_file": "test_twilio_conversations_filter_audit.py",
"test_py": '''from twilio_conversations_filter_audit import split_filters, verdict

POST_URL = "https://app.example.com/conversations"


def config(**kw):
    base = {"post_webhook_url": POST_URL, "pre_webhook_url": "",
            "filters": ["onMessageAdded"], "method": "POST"}
    base.update(kw)
    return base


def test_a_good_url_with_no_filters_delivers_nothing():
    state, detail = verdict(config(filters=[]))
    assert state == "no-filters"
    assert "allowlist" in detail


def test_pre_action_names_against_a_post_url_deliver_nothing_either():
    state, detail = verdict(config(filters=["onMessageAdd", "onParticipantAdd"]))
    assert state == "post-url-no-post-filters"
    assert "-ed" in detail


def test_a_populated_list_missing_one_required_event_is_a_finding():
    state, detail = verdict(config(filters=["onParticipantAdded"]),
                            required=["onMessageAdded", "onParticipantAdded"])
    assert state == "missing-events"
    assert "onMessageAdded" in detail


def test_no_url_at_all_is_reported_before_the_filters():
    state, _ = verdict(config(post_webhook_url="", pre_webhook_url="", filters=[]))
    assert state == "no-webhook"


def test_a_pre_webhook_with_only_post_filters_is_its_own_finding():
    state, _ = verdict(config(post_webhook_url="", pre_webhook_url=POST_URL,
                              filters=["onMessageAdded"]))
    assert state == "pre-url-no-pre-filters"


def test_everything_the_application_asked_for_is_ok():
    state, _ = verdict(config(filters=["onMessageAdded", "onConversationStateUpdated"]),
                       required=["onMessageAdded", "onConversationStateUpdated"])
    assert state == "ok"


def test_split_filters_uses_the_tense_and_ignores_blanks():
    pre, post = split_filters(["onMessageAdd", "onMessageAdded", "", None,
                               "onConversationStateUpdated"])
    assert pre == ["onMessageAdd"]
    assert post == ["onMessageAdded", "onConversationStateUpdated"]
''',
"test_js_file": "twilio-conversations-filter-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { splitFilters, verdict } from './twilio-conversations-filter-audit.mjs';

const POST_URL = 'https://app.example.com/conversations';

const config = (kw = {}) => ({
  post_webhook_url: POST_URL, pre_webhook_url: '',
  filters: ['onMessageAdded'], method: 'POST', ...kw,
});

test('a good url with no filters delivers nothing', () => {
  const [state, detail] = verdict(config({ filters: [] }));
  assert.equal(state, 'no-filters');
  assert.match(detail, /allowlist/);
});

test('pre-action names against a post url deliver nothing either', () => {
  const [state, detail] = verdict(config({ filters: ['onMessageAdd', 'onParticipantAdd'] }));
  assert.equal(state, 'post-url-no-post-filters');
  assert.match(detail, /-ed/);
});

test('a populated list missing one required event is a finding', () => {
  const [state, detail] = verdict(config({ filters: ['onParticipantAdded'] }),
    ['onMessageAdded', 'onParticipantAdded']);
  assert.equal(state, 'missing-events');
  assert.match(detail, /onMessageAdded/);
});

test('no url at all is reported before the filters', () => {
  assert.equal(
    verdict(config({ post_webhook_url: '', pre_webhook_url: '', filters: [] }))[0],
    'no-webhook');
});

test('a pre webhook with only post filters is its own finding', () => {
  assert.equal(
    verdict(config({ post_webhook_url: '', pre_webhook_url: POST_URL,
                     filters: ['onMessageAdded'] }))[0],
    'pre-url-no-pre-filters');
});

test('everything the application asked for is ok', () => {
  const [state] = verdict(
    config({ filters: ['onMessageAdded', 'onConversationStateUpdated'] }),
    ['onMessageAdded', 'onConversationStateUpdated']);
  assert.equal(state, 'ok');
});

test('splitFilters uses the tense and ignores blanks', () => {
  const [pre, post] = splitFilters(['onMessageAdd', 'onMessageAdded', '', null,
                                    'onConversationStateUpdated']);
  assert.deepEqual(pre, ['onMessageAdd']);
  assert.deepEqual(post, ['onMessageAdded', 'onConversationStateUpdated']);
});
''',
"faq": [
 ("Does an empty filters list mean everything or nothing?",
  "Nothing. filters is an allowlist of event names, so an empty list subscribes to no events at all. That is the reverse of how most filter fields behave, and it is the whole reason this configuration can look complete and deliver silence."),
 ("Why is there no error code for it?",
  "Because nothing failed. No delivery was attempted, so no delivery could fail, so the Debugger has nothing to log. This is one of the failures that error-based monitoring cannot see at any volume: the account is healthy and the integration is deaf."),
 ("What is the difference between onMessageAdd and onMessageAdded?",
  "Tense, and which webhook receives it. The pre-action event fires before the action is committed and goes to pre_webhook_url, where a handler can reject it. The past-tense event fires afterwards and goes to post_webhook_url. Both live in the same filters list, which is why a list of the wrong tense delivers nothing to the URL you configured."),
 ("Why does the script want a list of required events?",
  "Because an empty filters list is the easy case. The common case is a list with three events in it and not the fourth one your handler branches on, and no check that only asks whether the list is empty will ever find that."),
 ("Will adding one filter keep the ones already there?",
  "No. The configuration is a single resource that is replaced when updated, so the repair has to send the complete set with the Filters parameter repeated once per event. Sending only the new one is how an integration silently unsubscribes from what it already had."),
],
"related": [
 ("/twilio/conversations-webhook-url-missing/", "A conversation webhook with no URL: 50369"),
 ("/twilio/conversations-webhook-limit/", "Five conversation webhooks is the cap"),
 ("/twilio/event-streams-sink-failed/", "An Event Streams sink that stopped delivering"),
],
"citations": [CITE_CONV_CONFIG, CITE_CONV_HOOKS, CITE_CONV_HOOK, CITE_WEBHOOKS],
},


{
"slug": "conversations-webhook-limit",
"title": "Five conversation webhooks is the cap, and the sixth is rejected",
"description": "Error 50361 lands on whichever integration deployed last. The conversation already holds five webhooks, and two of them often point at the same URL.",
"h1": "five conversation webhooks is the cap, and the sixth is rejected",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio error 50361", "too many conversation webhooks",
             "conversation webhook limit", "conversations five webhooks",
             "conversation scoped webhook cap"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The new integration worked all the way through staging and failed on its first real conversation with <code>50361</code>, <em>Too many conversation webhooks</em>. Nothing about the new integration is wrong. It is the sixth thing to ask for a webhook on a conversation that allows five, and the five that got there first were added by code nobody has opened in a year.",
"short_answer": """<p>Read <code>GET https://conversations.twilio.com/v1/Conversations/{ConversationSid}/Webhooks</code> and take <code>meta.total</code>. Conversation-scoped webhooks are capped at five per conversation; at five, the next create is rejected with <code>50361</code>, and the rejection lands on whoever tried last rather than on whoever filled the slots.</p>
<p>Then look at where those five actually deliver. A create that was retried, or one that runs per conversation on startup, produces two webhooks with the same <code>configuration.url</code> &mdash; the ceiling is usually one integration counted twice rather than five integrations that all need to be there.</p>""",
"problem": """<p>A cap is an unusual failure because the thing that breaks is not the thing that is wrong. The five existing webhooks work. The sixth create is refused, so the newest integration is the one that appears broken, and the person debugging it is the person with the least context about the other five. The natural first move &mdash; re-run the create, try a different target, check the credentials &mdash; is wasted, because the request was well formed and the account is healthy.</p>
<p>Underneath, the count usually grew by accident. Webhooks are created per conversation by automation, and automation retries. A create that timed out after Twilio had already accepted it leaves a duplicate, and nothing reconciles it away: the conversation now carries two identical webhooks and has three slots left instead of four. Do that across a couple of integrations and the ceiling arrives on a conversation that only ever needed two.</p>""",
"why": """<p><strong>The limit is per conversation, and conversations are created constantly.</strong> The account is not near any limit; one conversation is. Which means the failure appears on some conversations and not others, at a rate that depends on how much automation has touched them, and reproducing it in staging requires a conversation with the same history rather than the same code.</p>
<p><strong>The victim is not the culprit.</strong> 50361 is raised against the create that could not fit. It names no reason beyond the count, so the error tells you nothing at all about which of the five existing webhooks is the stale one, and the only way to find that out is to read them and look at where they point.</p>
<p><strong>Creating a webhook is not idempotent.</strong> Nothing dedupes on <code>configuration.url</code>. Two creates with identical configuration produce two webhooks with two SIDs, both of which fire, so the duplicate also means your endpoint is being called twice for every event and probably has been for months.</p>
<p><strong>A conversation-scoped webhook is often the wrong tool anyway.</strong> Anything that wants to hear about every conversation belongs on the account or service-level configuration, which is one subscription rather than one per conversation. Integrations reach for the per-conversation resource because it is the one in the tutorial, and each one that does costs a slot out of five forever.</p>""",
"steps": [
 {"h": "List the conversations you care about",
  "body": """<p><code>GET https://conversations.twilio.com/v1/Conversations?PageSize=50</code>, following <code>meta.next_page_url</code>. This is a per-conversation check, so it costs one extra GET per conversation; bound it with a limit and run it over the newest conversations first, because those are the ones carrying the most automation.</p>"""},
 {"h": "Read meta.total, not the length of the page",
  "body": """<p><code>GET .../Conversations/{ConversationSid}/Webhooks</code> returns <code>meta.total</code> alongside the page. Counting the array works today because five fits in one page, and stops working the moment somebody sets a smaller <code>PageSize</code>. Take the total the API gives you and fall back to counting only when it is absent.</p>"""},
 {"h": "Compare where the five deliver",
  "body": """<p>Reduce each webhook to a comparable destination: the <code>target</code> plus its <code>configuration.url</code>, or the <code>flow_sid</code> for a Studio target. Two entries with the same destination are one integration registered twice, which is both a free slot and an explanation for the duplicate deliveries nobody has chased down.</p>"""},
 {"h": "Cross-check against the alerts",
  "body": """<p><code>GET https://monitor.twilio.com/v1/Alerts?LogLevel=error</code> filtered to <code>error_code</code> <code>50361</code> tells you the cap is being hit right now and on which conversations. It is a 30-day window and it only shows conversations something tried to add to, so it confirms the problem rather than bounding it.</p>"""},
 {"h": "Free a slot, or stop using the slot",
  "body": """<p>Two repairs, and the second is usually the right one. Remove the stale or duplicate webhook by SID to unblock today's deploy; move any integration that wants every conversation onto the account or service-level webhook configuration so it stops consuming one of the five on every conversation you will ever create.</p>"""},
],
"verify": """<p>Re-run over the same conversations. Nothing should report <code>at-limit</code>, and the duplicate count should be zero.</p>
<pre><code class="language-bash">python3 twilio_conversation_webhook_limit_audit.py --max-conversations 200
# 200 conversation(s), 0 at the five webhook ceiling</code></pre>""",
"code_intro": "One paginated GET for the conversations and one for each conversation's webhooks, on an API Key with read access. The pure functions are the destination key &mdash; which is what turns five webhooks into three integrations and two duplicates &mdash; and the classifier that reads the total against the cap. Neither needs a network, and the duplicate rule is the part worth arguing with.",
"py_file": "twilio_conversation_webhook_limit_audit.py",
"py": '''"""Report Twilio conversations at the five conversation-webhook ceiling (50361).

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
log = logging.getLogger("twilio_conversation_webhook_limit_audit")

CONVERSATIONS = "https://conversations.twilio.com/v1"

LIMIT = 5


def destination(webhook):
    """A comparable key for where one conversation webhook delivers. Pure.

    Nothing dedupes on the URL when a webhook is created, so a retried create
    leaves two webhooks with two SIDs and one destination. Normalising case and
    the trailing slash is what makes those two compare equal; a Studio target
    has no URL at all and is keyed on its flow_sid instead.
    """
    cfg = webhook.get("configuration") or {}
    target = str(webhook.get("target") or "").strip().lower()
    if target == "studio":
        return "studio %s" % (str(cfg.get("flow_sid") or "").strip() or "(no flow)")
    url = str(cfg.get("url") or "").strip().lower().rstrip("/")
    method = str(cfg.get("method") or "").strip().upper()
    return "%s %s %s" % (target or "(no target)", method or "(no method)",
                         url or "(no url)")


def webhook_total(page):
    """The number of webhooks on a conversation. Pure.

    meta.total is the authority: counting the array is right only while five
    entries fit in one page, which stops being true the moment somebody passes a
    smaller PageSize. Counting is the fallback, not the method.
    """
    meta = page.get("meta") or {}
    raw = meta.get("total")
    try:
        if raw is not None:
            return int(raw)
    except (TypeError, ValueError):
        pass
    return len(page.get("webhooks") or [])


def verdict(total, webhooks):
    """Classify one conversation against the five-webhook cap. Pure.

    Duplicates matter more than the raw count: at the ceiling they are the free
    slot, and below it they mean the endpoint is being called twice for every
    event. Returns (state, detail).
    """
    seen = {}
    for w in webhooks or []:
        seen.setdefault(destination(w), []).append(str(w.get("sid") or "?"))
    dupes = {k: v for k, v in seen.items() if len(v) > 1}
    dupe_note = ""
    if dupes:
        first = sorted(dupes)[0]
        dupe_note = (" %d destination(s) are registered more than once, including "
                     "%s (%s)." % (len(dupes), first, ", ".join(dupes[first])))

    if total >= LIMIT and dupes:
        return ("at-limit-duplicates",
                "%d webhook(s): at the cap of %d, so the next create is rejected "
                "with 50361.%s Removing a duplicate frees a slot without losing "
                "an integration." % (total, LIMIT, dupe_note))

    if total >= LIMIT:
        return ("at-limit",
                "%d webhook(s): at the cap of %d. The next create is rejected "
                "with 50361, and the rejection lands on whichever integration "
                "deploys last." % (total, LIMIT))

    if dupes:
        return ("duplicates",
                "%d webhook(s), below the cap of %d, but%s Your endpoint is "
                "being called twice for every event." % (total, LIMIT, dupe_note))

    if total == LIMIT - 1:
        return ("near-limit",
                "%d webhook(s): one slot left before creates start failing with "
                "50361." % total)

    if total == 0:
        return ("none",
                "no conversation-scoped webhooks. Events reach the account or "
                "service-level configuration only.")

    return ("headroom", "%d webhook(s), %d slot(s) left" % (total, LIMIT - total))


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


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-conversations", type=int, default=200,
                    help="stop after this many conversations; one GET each")
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

    conversations = paged(session, CONVERSATIONS + "/Conversations",
                          "conversations", args.max_conversations)
    if not conversations:
        log.info("no conversations on this account")
        return 0

    bad = 0
    for conv in conversations:
        sid = conv.get("sid")
        page = get(session, "%s/Conversations/%s/Webhooks" % (CONVERSATIONS, sid),
                   PageSize=50)
        webhooks = page.get("webhooks") or []
        state, detail = verdict(webhook_total(page), webhooks)
        line = "%-19s %s  %s" % (state, sid, detail)

        if state in ("headroom", "none"):
            log.info(line)
            continue
        if state == "near-limit":
            log.info(line)
            continue

        bad += 1
        log.warning(line)
        for w in webhooks:
            log.warning("    %s  %s", w.get("sid"), destination(w))
        log.warning("  repair: remove the stale or duplicate webhook by SID at "
                    "%s/Conversations/%s/Webhooks/{WebhookSid}, or move the "
                    "integration onto the account-level webhook configuration so "
                    "it stops taking a slot on every conversation.",
                    CONVERSATIONS, sid)

    log.info("%d conversation(s), %d at the five webhook ceiling or carrying "
             "duplicates", len(conversations), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-conversation-webhook-limit-audit.mjs",
"js": '''/**
 * Report Twilio conversations at the five conversation-webhook ceiling (50361).
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const CONVERSATIONS = 'https://conversations.twilio.com/v1';

const LIMIT = 5;

/**
 * A comparable key for where one conversation webhook delivers. Pure.
 *
 * Nothing dedupes on the URL when a webhook is created, so a retried create
 * leaves two webhooks with two SIDs and one destination. Normalising case and
 * the trailing slash is what makes those two compare equal; a Studio target has
 * no URL at all and is keyed on its flow_sid instead.
 */
export function destination(webhook) {
  const cfg = webhook.configuration ?? {};
  const target = String(webhook.target ?? '').trim().toLowerCase();
  if (target === 'studio') {
    return `studio ${String(cfg.flow_sid ?? '').trim() || '(no flow)'}`;
  }
  const url = String(cfg.url ?? '').trim().toLowerCase().replace(/\\/+$/, '');
  const method = String(cfg.method ?? '').trim().toUpperCase();
  return `${target || '(no target)'} ${method || '(no method)'} ${url || '(no url)'}`;
}

/**
 * The number of webhooks on a conversation. Pure.
 *
 * meta.total is the authority: counting the array is right only while five
 * entries fit in one page. Counting is the fallback, not the method.
 */
export function webhookTotal(page) {
  const raw = (page.meta ?? {}).total;
  const n = Number(raw);
  if (raw !== null && raw !== undefined && raw !== '' && Number.isFinite(n)) {
    return n;
  }
  return (page.webhooks ?? []).length;
}

/**
 * Classify one conversation against the five-webhook cap. Pure.
 *
 * Duplicates matter more than the raw count: at the ceiling they are the free
 * slot, and below it they mean the endpoint is called twice for every event.
 * Returns [state, detail].
 */
export function verdict(total, webhooks) {
  const seen = new Map();
  for (const w of webhooks ?? []) {
    const key = destination(w);
    if (!seen.has(key)) seen.set(key, []);
    seen.get(key).push(String(w.sid ?? '?'));
  }
  const dupes = [...seen.entries()].filter(([, sids]) => sids.length > 1).sort();
  let dupeNote = '';
  if (dupes.length) {
    const [first, sids] = dupes[0];
    dupeNote = ` ${dupes.length} destination(s) are registered more than once, ` +
      `including ${first} (${sids.join(', ')}).`;
  }

  if (total >= LIMIT && dupes.length) {
    return ['at-limit-duplicates',
      `${total} webhook(s): at the cap of ${LIMIT}, so the next create is ` +
      `rejected with 50361.${dupeNote} Removing a duplicate frees a slot ` +
      'without losing an integration.'];
  }

  if (total >= LIMIT) {
    return ['at-limit',
      `${total} webhook(s): at the cap of ${LIMIT}. The next create is rejected ` +
      'with 50361, and the rejection lands on whichever integration deploys last.'];
  }

  if (dupes.length) {
    return ['duplicates',
      `${total} webhook(s), below the cap of ${LIMIT}, but${dupeNote} Your ` +
      'endpoint is being called twice for every event.'];
  }

  if (total === LIMIT - 1) {
    return ['near-limit',
      `${total} webhook(s): one slot left before creates start failing with 50361.`];
  }

  if (total === 0) {
    return ['none',
      'no conversation-scoped webhooks. Events reach the account or ' +
      'service-level configuration only.'];
  }

  return ['headroom', `${total} webhook(s), ${LIMIT - total} slot(s) left`];
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

async function paged(auth, url, key, limit, first = {}) {
  let params = { PageSize: 50, ...first };
  const out = [];
  while (url && out.length < limit) {
    const page = await get(auth, url, params);
    out.push(...(page[key] ?? []));
    url = (page.meta ?? {}).next_page_url ?? null;
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

  const conversations = await paged(auth, `${CONVERSATIONS}/Conversations`,
                                    'conversations', 200);
  if (!conversations.length) {
    console.log('no conversations on this account');
    return;
  }

  let bad = 0;
  for (const conv of conversations) {
    const page = await get(auth, `${CONVERSATIONS}/Conversations/${conv.sid}/Webhooks`,
                           { PageSize: 50 });
    const webhooks = page.webhooks ?? [];
    const [state, detail] = verdict(webhookTotal(page), webhooks);
    const line = `${state.padEnd(19)} ${conv.sid}  ${detail}`;

    if (state === 'headroom' || state === 'none' || state === 'near-limit') {
      console.log(line);
      continue;
    }

    bad += 1;
    console.warn(line);
    for (const w of webhooks) console.warn(`    ${w.sid}  ${destination(w)}`);
    console.warn('  repair: remove the stale or duplicate webhook by SID at ' +
                 `${CONVERSATIONS}/Conversations/${conv.sid}/Webhooks/{WebhookSid}, ` +
                 'or move the integration onto the account-level webhook ' +
                 'configuration so it stops taking a slot on every conversation.');
  }

  console.log(`${conversations.length} conversation(s), ${bad} at the five ` +
              'webhook ceiling or carrying duplicates');
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The cases that matter are the ones that change the advice. Five webhooks with two pointing at the same URL is a slot you can have back for free; five distinct ones is a conversation that needs an integration moved off it. Below the cap, a duplicate is still a finding, because it means every event is being delivered twice.",
"test_py_file": "test_twilio_conversation_webhook_limit_audit.py",
"test_py": '''from twilio_conversation_webhook_limit_audit import (
    destination, verdict, webhook_total)

URL = "https://app.example.com/hook"


def hook(sid, url=URL, target="webhook", method="POST", flow=None):
    cfg = {"url": url, "method": method}
    if flow:
        cfg = {"flow_sid": flow}
    return {"sid": sid, "target": target, "configuration": cfg}


def distinct(n):
    return [hook("WH%d" % i, "%s/%d" % (URL, i)) for i in range(n)]


def test_five_distinct_webhooks_is_the_ceiling():
    state, detail = verdict(5, distinct(5))
    assert state == "at-limit"
    assert "50361" in detail


def test_a_duplicate_at_the_ceiling_is_a_free_slot():
    hooks = distinct(4) + [hook("WH9", "%s/0" % URL)]
    state, detail = verdict(5, hooks)
    assert state == "at-limit-duplicates"
    assert "frees a slot" in detail


def test_a_duplicate_below_the_ceiling_is_still_a_finding():
    state, detail = verdict(2, [hook("WH1"), hook("WH2")])
    assert state == "duplicates"
    assert "twice for every event" in detail


def test_four_distinct_webhooks_is_one_slot_from_failing():
    assert verdict(4, distinct(4))[0] == "near-limit"


def test_an_empty_conversation_is_not_a_finding():
    assert verdict(0, [])[0] == "none"
    assert verdict(2, distinct(2))[0] == "headroom"


def test_destination_ignores_case_and_a_trailing_slash():
    assert destination(hook("WH1", "https://App.Example.com/hook/")) == \\
        destination(hook("WH2", URL))


def test_a_studio_target_is_keyed_on_the_flow():
    assert destination(hook("WH1", target="studio", flow="FW1")) == "studio FW1"
    assert destination(hook("WH1", target="studio", flow="FW1")) != \\
        destination(hook("WH2", target="studio", flow="FW2"))


def test_meta_total_wins_over_the_length_of_the_page():
    # A smaller PageSize returns fewer entries than the conversation holds, and
    # counting the array would report headroom on a conversation at the cap.
    page = {"webhooks": distinct(2), "meta": {"total": 5}}
    assert webhook_total(page) == 5
    assert webhook_total({"webhooks": distinct(2), "meta": {}}) == 2
''',
"test_js_file": "twilio-conversation-webhook-limit-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { destination, verdict, webhookTotal }
  from './twilio-conversation-webhook-limit-audit.mjs';

const URL_ = 'https://app.example.com/hook';

const hook = (sid, { url = URL_, target = 'webhook', method = 'POST', flow = null } = {}) => ({
  sid, target, configuration: flow ? { flow_sid: flow } : { url, method },
});

const distinct = (n) =>
  Array.from({ length: n }, (_, i) => hook(`WH${i}`, { url: `${URL_}/${i}` }));

test('five distinct webhooks is the ceiling', () => {
  const [state, detail] = verdict(5, distinct(5));
  assert.equal(state, 'at-limit');
  assert.match(detail, /50361/);
});

test('a duplicate at the ceiling is a free slot', () => {
  const hooks = [...distinct(4), hook('WH9', { url: `${URL_}/0` })];
  const [state, detail] = verdict(5, hooks);
  assert.equal(state, 'at-limit-duplicates');
  assert.match(detail, /frees a slot/);
});

test('a duplicate below the ceiling is still a finding', () => {
  const [state, detail] = verdict(2, [hook('WH1'), hook('WH2')]);
  assert.equal(state, 'duplicates');
  assert.match(detail, /twice for every event/);
});

test('four distinct webhooks is one slot from failing', () => {
  assert.equal(verdict(4, distinct(4))[0], 'near-limit');
});

test('an empty conversation is not a finding', () => {
  assert.equal(verdict(0, [])[0], 'none');
  assert.equal(verdict(2, distinct(2))[0], 'headroom');
});

test('destination ignores case and a trailing slash', () => {
  assert.equal(destination(hook('WH1', { url: 'https://App.Example.com/hook/' })),
               destination(hook('WH2')));
});

test('a studio target is keyed on the flow', () => {
  assert.equal(destination(hook('WH1', { target: 'studio', flow: 'FW1' })),
               'studio FW1');
  assert.notEqual(destination(hook('WH1', { target: 'studio', flow: 'FW1' })),
                  destination(hook('WH2', { target: 'studio', flow: 'FW2' })));
});

test('meta.total wins over the length of the page', () => {
  assert.equal(webhookTotal({ webhooks: distinct(2), meta: { total: 5 } }), 5);
  assert.equal(webhookTotal({ webhooks: distinct(2), meta: {} }), 2);
});
''',
"faq": [
 ("What is the actual limit?",
  "Five conversation-scoped webhooks per conversation. It is a per-conversation cap, not an account one, so the account can be nowhere near any quota while individual conversations refuse new webhooks."),
 ("Why did it fail in production and not in staging?",
  "Because the limit depends on the conversation's history, not on your code. A staging conversation created by the test that just ran carries one webhook. A production conversation that three integrations have touched over six months carries five, and the sixth create is the one that meets the cap."),
 ("Does 50361 tell me which webhook to remove?",
  "No. It reports that the count is at the cap and nothing about the five that are already there. Reading the webhook list and comparing destinations is the only way to find the duplicate or the integration that was decommissioned but never unhooked."),
 ("Why are duplicates so common?",
  "Because creating a webhook is not idempotent and automation retries. A create that succeeded on Twilio's side and timed out on yours leaves a second webhook with the same URL, and both of them fire. The wasted slot is the smaller half of that problem; the double delivery is the larger."),
 ("What should be a conversation-scoped webhook at all?",
  "Something that genuinely applies to one conversation: a handoff to an agent, a bot attached for the length of one thread. Anything that wants every conversation belongs on the account or service-level configuration, where it is one subscription instead of one slot out of five on every conversation you create."),
],
"related": [
 ("/twilio/conversations-webhook-url-missing/", "A conversation webhook with no URL: 50369"),
 ("/twilio/conversations-webhook-filters-empty/", "Conversations webhooks with an empty filter list"),
 ("/twilio/rest-api-concurrency-exhausted/", "REST API concurrency exhausted"),
],
"citations": [CITE_50361, CITE_CONV_HOOK, CITE_CONV, CITE_ALERTS],
},


{
"slug": "sync-webhook-url-invalid",
"title": "A Sync webhook rejected as invalid, or never called at all",
"description": "Error 54051 is the loud half. The quiet half is webhooks_from_rest_enabled, off by default, so every change your own server makes over REST calls nothing.",
"h1": "a Sync webhook rejected as invalid, or never called at all",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio error 54051", "sync invalid webhook url",
             "webhooks_from_rest_enabled", "twilio sync webhook not firing",
             "sync service webhook_url"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Documents are changing and the backend hears nothing about it. Sometimes there is a <code>54051</code> in the error logs, <em>Invalid webhook URL</em>, and sometimes there is nothing at all &mdash; because the URL can be perfect and still never be called. <code>webhooks_from_rest_enabled</code> is off unless somebody turned it on, and the changes it suppresses are exactly the ones your own server makes.",
"short_answer": """<p>Read <code>GET https://sync.twilio.com/v1/Services</code> and check two fields on every service. <code>webhook_url</code> empty, plain <code>http://</code>, or otherwise not a reachable absolute URL is the <code>54051</code> half: Twilio has a callback configured and cannot use it.</p>
<p><code>webhooks_from_rest_enabled</code> is the other half and raises no error at all. While it is <code>false</code>, changes made through the REST API produce no webhook, so an application that writes its Sync data server-side gets a correctly configured URL that is never called. Cross-check the alerts with <code>GET https://monitor.twilio.com/v1/Alerts</code> filtered to <code>error_code</code> <code>54051</code>.</p>""",
"problem": """<p>Two failures wear the same symptom, and only one of them leaves evidence. The first is a webhook URL Twilio will not accept or cannot reach; that raises 54051 and at least appears somewhere. The second is a service whose URL is impeccable and whose callbacks are switched off for the exact class of change your architecture produces, and it raises nothing at all, ever.</p>
<p>The second is the one that survives. Sync is usually adopted for a client that reads live state, with the server writing that state through the REST API. Under the default, those writes are the changes that do not call the webhook, so the developer sets the URL, tests it by editing a document from a browser SDK or the console, sees it fire, and ships. In production every change comes from the server, and the webhook is silent from the first day without a single failed request to explain it.</p>""",
"why": """<p><strong>The default is off, and the default is defensible.</strong> A service that calls your webhook on changes your own server just made will happily deliver an echo of every write you perform. Turning that off by default prevents a loop; it also means the useful configuration is one somebody had to know to ask for.</p>
<p><strong>The two failures need different reads and produce different evidence.</strong> 54051 is in the alerts, bounded by a 30-day retention window. The suppressed-callback case is nowhere in the alerts and only visible as a boolean on the service, which is why the service list is the primary read and the alert sweep is the corroboration rather than the other way around.</p>
<p><strong>Whether it is a fault depends on your architecture.</strong> A service whose data is only ever changed by client SDKs is fine with <code>webhooks_from_rest_enabled</code> off. A service written to by your backend is not. The script cannot know which you are, so it takes the answer as an argument rather than guessing and reporting a fleet of false positives.</p>
<p><strong>A plain-http URL is two problems.</strong> It is rejected, which is the 54051, and it would have carried whatever your Sync documents hold in the clear if it had not been. Both belong in the report, and the second is the one that outlives the fix if someone repairs it by making the endpoint reachable rather than by making it HTTPS.</p>""",
"steps": [
 {"h": "List the Sync Services",
  "body": """<p><code>GET https://sync.twilio.com/v1/Services?PageSize=50</code>, following <code>meta.next_page_url</code>. Accounts accumulate these: one per environment, one from a prototype, and the default service that Sync creates for you. Every one of them has its own <code>webhook_url</code> and its own flags.</p>"""},
 {"h": "Judge the URL first",
  "body": """<p>Empty means nothing is configured and no change on that service calls anything. <code>http://</code> means it is rejected and would have been insecure anyway. Anything that is not an absolute <code>https://</code> URL belongs in the same bucket: Twilio needs a URL it can resolve and connect to, and a relative path or a hostname with no scheme is neither.</p>"""},
 {"h": "Say out loud where your writes come from",
  "body": """<p>If your backend changes Sync documents, lists or maps through the REST API, then <code>webhooks_from_rest_enabled</code> being <code>false</code> means none of those changes produces a callback. Pass that fact to the script. Without it, the flag is only informational, and a report that flags every service on the account is a report nobody reads twice.</p>"""},
 {"h": "Sweep the alerts for 54051",
  "body": """<p><code>GET https://monitor.twilio.com/v1/Alerts?LogLevel=error&amp;StartDate=YYYY-MM-DD</code>, keeping <code>error_code</code> <code>54051</code>. Coerce the code before comparing: it arrives as a number on the resource and as a string in some exports, and a raw comparison finds nothing on an account full of them. Alerts are retained 30 days, so absence proves nothing.</p>"""},
 {"h": "Fix both halves at once, then re-run",
  "body": """<p>The repair is an update to the service setting <code>WebhookUrl</code> to an HTTPS endpoint and, when your writes come from the server, <code>WebhooksFromRestEnabled</code> to <code>true</code>. Do both in one change: fixing the URL alone on a REST-driven service leaves it just as silent, with the added confidence of a URL that now looks right.</p>"""},
],
"verify": """<p>Re-run with a start date after the change. Every service should report <code>ok</code> and the 54051 count should be zero.</p>
<pre><code class="language-bash">python3 twilio_sync_webhook_audit.py --rest-writes --days 3
# 4 service(s), 0 with a webhook that cannot fire</code></pre>""",
"code_intro": "One paginated GET over the Sync Services and one alert sweep, both read-only. The classifier takes the service, whether your application writes over REST, and how many 54051 alerts named that service &mdash; three inputs, because the same <code>webhooks_from_rest_enabled: false</code> is correct on one account and an outage on the next, and a script that cannot express that difference has to choose between missing it and crying wolf.",
"py_file": "twilio_sync_webhook_audit.py",
"py": '''"""Report Twilio Sync Services whose webhook is invalid or cannot fire (54051).

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
log = logging.getLogger("twilio_sync_webhook_audit")

SYNC = "https://sync.twilio.com/v1"
MONITOR = "https://monitor.twilio.com/v1"

INVALID_WEBHOOK = 54051


def alert_counts(alerts, code=INVALID_WEBHOOK):
    """Count alerts carrying one error code, keyed by resource_sid. Pure.

    error_code arrives as a number on the Alert resource and as a string in some
    exports, so it is coerced rather than compared raw: that comparison is why a
    sweep reports nothing on an account full of findings.

    Keyed rather than totalled because the same code can be attributed to more
    than one resource, and a count against a resource the caller did not ask
    about is still worth printing rather than dropping.
    """
    counts = {}
    for a in alerts or []:
        raw = a.get("error_code")
        try:
            if raw is None or int(raw) != int(code):
                continue
        except (TypeError, ValueError):
            continue
        sid = str(a.get("resource_sid") or "(unattributed)")
        counts[sid] = counts.get(sid, 0) + 1
    return counts


def verdict(service, rest_writes=False, alerts=0):
    """Classify one Sync Service's webhook. Pure, so the one judgement call in
    this note is visible in one place.

    `rest_writes` is the caller saying their application changes Sync data
    through the REST API. It is an input rather than an assumption because
    webhooks_from_rest_enabled being false is correct on a service only ever
    written to by client SDKs, and an outage on one written to by a server.

    `alerts` is how many 54051 alerts named this service in the window.

    Returns (state, detail).
    """
    url = str(service.get("webhook_url") or "").strip()
    from_rest = service.get("webhooks_from_rest_enabled")
    low = url.lower()

    if not url:
        return ("no-url",
                "webhook_url is empty: no change on this service calls anything, "
                "and an attempt to deliver raises 54051.")

    if low.startswith("http://"):
        return ("insecure",
                "webhook_url is plain http, which is rejected as invalid (54051) "
                "and would have carried document contents in the clear.")

    if not low.startswith("https://"):
        return ("not-absolute",
                "webhook_url is %r, which is not an absolute https URL for "
                "Twilio to resolve and connect to." % url)

    if alerts:
        return ("unreachable",
                "%d alert(s) with 54051 named this service while webhook_url is "
                "a well-formed https URL: Twilio could not reach or complete the "
                "request to %s." % (alerts, url))

    if from_rest is False and rest_writes:
        return ("rest-silent",
                "webhooks_from_rest_enabled is false and your application writes "
                "over REST, so none of those changes calls %s. No error is "
                "raised for this." % url)

    if from_rest is False:
        return ("rest-disabled",
                "webhooks_from_rest_enabled is false. Correct if only client SDKs "
                "change this data; silent for every server-side write if not.")

    return ("ok", "https webhook at %s, REST-driven changes included" % url)


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


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rest-writes", action="store_true",
                    help="your application changes Sync data through the REST API")
    ap.add_argument("--days", type=int, default=7,
                    help="how far back to sweep the alerts (30 day retention)")
    ap.add_argument("--max-alerts", type=int, default=10000)
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

    services = paged(session, SYNC + "/Services", "services", 200)
    if not services:
        log.info("no Sync Services on this account")
        return 0

    start = (dt.date.today() - dt.timedelta(days=args.days)).isoformat()
    counts = alert_counts(paged(session, MONITOR + "/Alerts", "alerts",
                                args.max_alerts, LogLevel="error", StartDate=start,
                                PageSize=100))

    bad = 0
    for svc in services:
        sid = svc.get("sid")
        state, detail = verdict(svc, args.rest_writes, counts.pop(sid, 0))
        line = "%-14s %s  %s" % (state, svc.get("friendly_name") or sid, detail)
        if state in ("ok", "rest-disabled"):
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        log.warning("  repair: update %s/Services/%s with "
                    "WebhookUrl=https://your-app.example.com/sync and, when your "
                    "writes come from the server, WebhooksFromRestEnabled=true.",
                    SYNC, sid)

    for sid, n in sorted(counts.items()):
        log.info("%d alert(s) with 54051 attributed to %s, which is not a Sync "
                 "Service on this account", n, sid)

    log.info("%d service(s), %d with a webhook that cannot fire", len(services), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-sync-webhook-audit.mjs",
"js": '''/**
 * Report Twilio Sync Services whose webhook is invalid or cannot fire (54051).
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const SYNC = 'https://sync.twilio.com/v1';
const MONITOR = 'https://monitor.twilio.com/v1';

const INVALID_WEBHOOK = 54051;

/**
 * Count alerts carrying one error code, keyed by resource_sid. Pure.
 *
 * error_code arrives as a number on the Alert resource and as a string in some
 * exports, so it is coerced rather than compared raw. Keyed rather than
 * totalled because a count against a resource the caller did not ask about is
 * still worth printing rather than dropping.
 */
export function alertCounts(alerts, code = INVALID_WEBHOOK) {
  const counts = new Map();
  for (const a of alerts ?? []) {
    const raw = a.error_code;
    if (raw === null || raw === undefined || raw === '') continue;
    const n = Number(raw);
    if (!Number.isFinite(n) || n !== Number(code)) continue;
    const sid = String(a.resource_sid ?? '(unattributed)');
    counts.set(sid, (counts.get(sid) ?? 0) + 1);
  }
  return counts;
}

/**
 * Classify one Sync Service's webhook. Pure.
 *
 * `restWrites` is the caller saying their application changes Sync data through
 * the REST API. It is an input rather than an assumption because
 * webhooks_from_rest_enabled being false is correct on a service only ever
 * written to by client SDKs, and an outage on one written to by a server.
 * `alerts` is how many 54051 alerts named this service. Returns [state, detail].
 */
export function verdict(service, restWrites = false, alerts = 0) {
  const url = String(service.webhook_url ?? '').trim();
  const fromRest = service.webhooks_from_rest_enabled;
  const low = url.toLowerCase();

  if (!url) {
    return ['no-url',
      'webhook_url is empty: no change on this service calls anything, and an ' +
      'attempt to deliver raises 54051.'];
  }

  if (low.startsWith('http://')) {
    return ['insecure',
      'webhook_url is plain http, which is rejected as invalid (54051) and ' +
      'would have carried document contents in the clear.'];
  }

  if (!low.startsWith('https://')) {
    return ['not-absolute',
      `webhook_url is "${url}", which is not an absolute https URL for Twilio ` +
      'to resolve and connect to.'];
  }

  if (alerts) {
    return ['unreachable',
      `${alerts} alert(s) with 54051 named this service while webhook_url is a ` +
      `well-formed https URL: Twilio could not reach or complete the request to ${url}.`];
  }

  if (fromRest === false && restWrites) {
    return ['rest-silent',
      'webhooks_from_rest_enabled is false and your application writes over ' +
      `REST, so none of those changes calls ${url}. No error is raised for this.`];
  }

  if (fromRest === false) {
    return ['rest-disabled',
      'webhooks_from_rest_enabled is false. Correct if only client SDKs change ' +
      'this data; silent for every server-side write if not.'];
  }

  return ['ok', `https webhook at ${url}, REST-driven changes included`];
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

async function paged(auth, url, key, limit, first = {}) {
  let params = { PageSize: 50, ...first };
  const out = [];
  while (url && out.length < limit) {
    const page = await get(auth, url, params);
    out.push(...(page[key] ?? []));
    url = (page.meta ?? {}).next_page_url ?? null;
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
  const restWrites = process.argv.includes('--rest-writes');
  const flag = process.argv.indexOf('--days');
  const days = flag === -1 ? 7 : Number(process.argv[flag + 1] ?? 7);

  const services = await paged(auth, `${SYNC}/Services`, 'services', 200);
  if (!services.length) {
    console.log('no Sync Services on this account');
    return;
  }

  const start = new Date(Date.now() - days * 86400000).toISOString().slice(0, 10);
  const counts = alertCounts(await paged(auth, `${MONITOR}/Alerts`, 'alerts', 10000,
                                         { LogLevel: 'error', StartDate: start,
                                           PageSize: 100 }));

  let bad = 0;
  for (const svc of services) {
    const alerts = counts.get(svc.sid) ?? 0;
    counts.delete(svc.sid);
    const [state, detail] = verdict(svc, restWrites, alerts);
    const line = `${state.padEnd(14)} ${svc.friendly_name || svc.sid}  ${detail}`;
    if (state === 'ok' || state === 'rest-disabled') { console.log(line); continue; }
    bad += 1;
    console.warn(line);
    console.warn(`  repair: update ${SYNC}/Services/${svc.sid} with ` +
                 'WebhookUrl=https://your-app.example.com/sync and, when your ' +
                 'writes come from the server, WebhooksFromRestEnabled=true.');
  }

  for (const [sid, n] of [...counts.entries()].sort()) {
    console.log(`${n} alert(s) with 54051 attributed to ${sid}, which is not a ` +
                'Sync Service on this account');
  }

  console.log(`${services.length} service(s), ${bad} with a webhook that cannot fire`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The test that matters most is the pair: the same service, with <code>webhooks_from_rest_enabled</code> false, classified as fine when only client SDKs write to it and as an outage when the caller says their server does. After that, the ordinary URL faults, and the coercion in the alert count &mdash; because an error code compared as a string against a number is a sweep that finds nothing and reports success.",
"test_py_file": "test_twilio_sync_webhook_audit.py",
"test_py": '''from twilio_sync_webhook_audit import alert_counts, verdict

URL = "https://app.example.com/sync"


def service(**kw):
    base = {"sid": "IS1", "friendly_name": "live", "webhook_url": URL,
            "webhooks_from_rest_enabled": True}
    base.update(kw)
    return base


def test_rest_writes_decide_whether_the_flag_is_a_fault():
    svc = service(webhooks_from_rest_enabled=False)
    assert verdict(svc, rest_writes=False)[0] == "rest-disabled"
    state, detail = verdict(svc, rest_writes=True)
    assert state == "rest-silent"
    assert "No error is raised" in detail


def test_an_empty_webhook_url_is_the_first_thing_reported():
    state, detail = verdict(service(webhook_url="", webhooks_from_rest_enabled=False))
    assert state == "no-url"
    assert "54051" in detail


def test_plain_http_is_rejected_and_insecure():
    state, detail = verdict(service(webhook_url="http://app.example.com/sync"))
    assert state == "insecure"
    assert "in the clear" in detail


def test_a_url_with_no_scheme_is_not_absolute():
    assert verdict(service(webhook_url="app.example.com/sync"))[0] == "not-absolute"


def test_alerts_against_a_well_formed_url_mean_unreachable():
    state, detail = verdict(service(), alerts=12)
    assert state == "unreachable"
    assert "12 alert(s)" in detail


def test_a_healthy_service_is_ok():
    assert verdict(service(), rest_writes=True)[0] == "ok"


def test_alert_counts_coerce_the_code_and_key_on_the_resource():
    alerts = [{"error_code": "54051", "resource_sid": "IS1"},
              {"error_code": 54051, "resource_sid": "IS1"},
              {"error_code": 54051, "resource_sid": "IS2"},
              {"error_code": 11200, "resource_sid": "IS1"},
              {"error_code": None, "resource_sid": "IS1"}]
    assert alert_counts(alerts) == {"IS1": 2, "IS2": 1}


def test_an_alert_with_no_resource_is_still_counted():
    assert alert_counts([{"error_code": 54051}]) == {"(unattributed)": 1}
''',
"test_js_file": "twilio-sync-webhook-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { alertCounts, verdict } from './twilio-sync-webhook-audit.mjs';

const URL_ = 'https://app.example.com/sync';

const service = (kw = {}) => ({
  sid: 'IS1', friendly_name: 'live', webhook_url: URL_,
  webhooks_from_rest_enabled: true, ...kw,
});

test('rest writes decide whether the flag is a fault', () => {
  const svc = service({ webhooks_from_rest_enabled: false });
  assert.equal(verdict(svc, false)[0], 'rest-disabled');
  const [state, detail] = verdict(svc, true);
  assert.equal(state, 'rest-silent');
  assert.match(detail, /No error is raised/);
});

test('an empty webhook url is the first thing reported', () => {
  const [state, detail] = verdict(
    service({ webhook_url: '', webhooks_from_rest_enabled: false }));
  assert.equal(state, 'no-url');
  assert.match(detail, /54051/);
});

test('plain http is rejected and insecure', () => {
  const [state, detail] = verdict(service({ webhook_url: 'http://app.example.com/sync' }));
  assert.equal(state, 'insecure');
  assert.match(detail, /in the clear/);
});

test('a url with no scheme is not absolute', () => {
  assert.equal(verdict(service({ webhook_url: 'app.example.com/sync' }))[0],
               'not-absolute');
});

test('alerts against a well formed url mean unreachable', () => {
  const [state, detail] = verdict(service(), false, 12);
  assert.equal(state, 'unreachable');
  assert.match(detail, /12 alert\\(s\\)/);
});

test('a healthy service is ok', () => {
  assert.equal(verdict(service(), true)[0], 'ok');
});

test('alertCounts coerce the code and key on the resource', () => {
  const alerts = [{ error_code: '54051', resource_sid: 'IS1' },
                  { error_code: 54051, resource_sid: 'IS1' },
                  { error_code: 54051, resource_sid: 'IS2' },
                  { error_code: 11200, resource_sid: 'IS1' },
                  { error_code: null, resource_sid: 'IS1' }];
  assert.deepEqual([...alertCounts(alerts).entries()], [['IS1', 2], ['IS2', 1]]);
});

test('an alert with no resource is still counted', () => {
  assert.deepEqual([...alertCounts([{ error_code: 54051 }]).entries()],
                   [['(unattributed)', 1]]);
});
''',
"faq": [
 ("What does 54051 actually mean?",
  "That Twilio had a webhook URL for the Sync Service and could not use it: empty, not an absolute HTTPS URL, or a URL it could not reach. It is raised at delivery time, so it appears when something changed rather than when the URL was configured."),
 ("Why would a perfectly good URL never be called?",
  "Because webhooks_from_rest_enabled is false by default, and while it is false, changes made through the REST API produce no callback. If your server is what writes to Sync, that covers every change you make, and no error is raised at any point."),
 ("Why is that the default?",
  "To stop a service echoing your own writes back at you. A webhook that fires on REST-driven changes will call your application about changes your application just made, which is a loop unless the handler is written for it. Off by default is the safe choice and the surprising one."),
 ("Should the script flag every service with the flag off?",
  "No, and that is why it takes --rest-writes. A service whose data is only ever changed by client SDKs is correct with the flag off. Reporting those as findings puts a false positive beside every real one, and the report stops being read."),
 ("If the alerts are empty, is the service fine?",
  "Not necessarily. Debugger alerts are retained for 30 days, and the silent failure raises no alert at any point in any window. The alert sweep confirms an active URL problem; the fields on the service are what actually answer the question."),
],
"related": [
 ("/twilio/phone-number-insecure-or-unreachable-webhook-url/", "A webhook URL that is insecure or unreachable"),
 ("/twilio/status-callback-webhook-failing-11200/", "Status callbacks failing with 11200"),
 ("/twilio/event-streams-sink-failed/", "An Event Streams sink that stopped delivering"),
],
"citations": [CITE_54051, CITE_SYNC, CITE_ALERTS, CITE_WEBHOOKS],
},

]
