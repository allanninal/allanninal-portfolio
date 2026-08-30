#!/usr/bin/env python3
"""/llm/ field notes, batch A — the writing.

Four ways a model id goes wrong, and they are four different problems rather than
four readings of one. A date that has passed. The same date still ahead of you. An
id that is not on the list at all, with no date anywhere. And an id that is not
retiring in any sense but will not keep pointing at the same weights.

Read-only throughout: a project key set to Read Only on the OpenAI side, a
workspace key on the Anthropic side, GET requests only, and the repair printed for
a human to run. These scripts hold a credential that can spend money on inference,
so none of them writes.
"""

CITE_OA_DEPRECATIONS = ("Deprecations — OpenAI API docs",
                        "https://developers.openai.com/api/docs/deprecations")
CITE_OA_MODELS = ("Models — OpenAI API reference",
                  "https://developers.openai.com/api/docs/api-reference/models")
CITE_AN_DEPRECATIONS = ("Model deprecations — Claude Docs",
                        "https://platform.claude.com/docs/en/about-claude/model-deprecations")
CITE_AN_MODELS = ("Models API — Claude Docs",
                  "https://platform.claude.com/docs/en/api/models")
CITE_AN_OVERVIEW = ("Models overview — Claude Docs",
                    "https://platform.claude.com/docs/en/models/overview")
CITE_AN_ERRORS = ("Errors — Claude Docs",
                  "https://platform.claude.com/docs/en/api/errors")

REL_PAST = ("/llm/model-past-shutdown-date/",
            "A model id past its published shutdown date")
REL_SOON = ("/llm/model-retiring-within-90-days/",
            "A model still in production retiring in under 90 days")
REL_GONE = ("/llm/retired-model-id-still-in-code/",
            "A retired model id still sitting in the code")
REL_ALIAS = ("/llm/floating-alias-instead-of-pinned-snapshot/",
             "A floating alias where a pinned snapshot belongs")

GUIDES = [

{
"slug": "model-past-shutdown-date",
"title": "A model id in use is past its published shutdown date",
"description": "GET /v1/models carries a shutdown_date per model. Once it passes, the id fails exactly like a typo: 404 model_not_found, with no retired error code.",
"h1": "a model id in use is past its published shutdown date",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["openai model_not_found", "openai model shutdown date",
             "openai model retired 404", "gpt model deprecated error",
             "openai deprecations check"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Reads OPENAI_API_KEY, a project key set to Read Only.",
"lead": "Nothing was deployed. The key did not rotate. One model id started returning <code>404</code> on the same morning for every request, and the message reads exactly like a typo: <em>The model does not exist or you do not have access to it.</em> It existed yesterday. There is no distinct error code for a retired model, no deprecation warning on the successful calls that came before it, and nothing in the response that tells the difference between a model that was shut down and a model name somebody misspelled.",
"short_answer": """<p><code>GET /v1/models</code> returns a <code>shutdown_date</code> on each entry in <code>data[]</code>. Any id whose <code>shutdown_date</code> is non-null and earlier than today is already dead, and every call naming it is already failing.</p>
<p>That one field is the whole check. It needs a project key set to Read Only, it is a single request, and it answers the question the 404 refuses to: this id was retired on a published date, it was not mistyped.</p>""",
"problem": """<p>The damage is not that the model went away &mdash; that was announced months earlier. The damage is that the failure is <em>ambiguous</em>. A 404 with <code>model_not_found</code> is the same response you get for a genuine typo, for a model your organization has never been granted, and for a model that exists only on a partner platform. So the first hour goes into checking the spelling, then the key, then the project, then whether somebody changed an environment variable. The one explanation nobody reaches for is that the string is correct and the model is gone.</p>
<p>It also arrives all at once. Retirement is not a ramp: the id routes normally until the shutdown date and then stops, so every code path naming it breaks in the same minute. A fallback branch that names the same retired snapshot fails with it, which is how a graceful degradation path turns into a second outage.</p>""",
"why": """<p><strong>The retirement is a date, not an event.</strong> OpenAI publishes shutdown dates on the deprecations page, usually three to six months ahead. Nothing in the API pushes that at you: successful inference responses carry no deprecation header and no <code>warnings</code> array, so a service can run for months against an id with a shutdown date already published and get no runtime hint at all.</p>
<p><strong>The 404 is shared with three other causes.</strong> <code>model_not_found</code> means "not routable for you", which covers retired, misspelled, never-granted and wrong-endpoint. The error body cannot distinguish them because it does not know which one applies. Only the models list can, and only if you read it.</p>
<p><strong>Pinning a snapshot does not exempt you.</strong> Pinning is the correct thing to do and it is exactly what gets bitten here: a dated snapshot has a fixed lifetime by construction. Teams that took the advice and pinned are the ones holding an id with a real shutdown date, while teams on a floating alias were quietly migrated for them &mdash; and got a <a href="/llm/floating-alias-instead-of-pinned-snapshot/">different problem</a> in exchange.</p>
<p><strong>The list entry outlives the model, and then it does not.</strong> Immediately after a shutdown the entry can still appear in <code>data[]</code> with the date in the past, which is what makes this check possible. Once the entry is dropped from the list entirely there is no date left to read, and the only evidence is <a href="/llm/retired-model-id-still-in-code/">absence</a>. Catching it while the date is still readable is much cheaper than reconstructing it afterwards.</p>""",
"steps": [
 {"h": "Read the models list once",
  "body": """<p><code>GET https://api.openai.com/v1/models</code> with a project key set to Read Only. The response is a single page of <code>data[]</code> entries; the field that matters is <code>shutdown_date</code>, and on most entries it is null.</p>"""},
 {"h": "Compare each date against today, not against a hardcoded year",
  "body": """<p>A date in the past means the id is dead now. A date of today means it dies during today, which is an outage in progress rather than a warning. Everything else is future work and belongs in the <a href="/llm/model-retiring-within-90-days/">90-day check</a> instead, or the report is too noisy to read.</p>"""},
 {"h": "Restrict the output to ids you actually name",
  "body": """<p>The list carries every model the key can see, including families you have never called. Pass the ids that appear in your configuration with <code>--model</code> so the report is about your code rather than about OpenAI's catalogue. With an admin-read key you can get that list from usage instead: <code>GET /v1/organization/usage/completions?bucket_width=1d&amp;group_by[]=model</code> and read <code>data[].results[].model</code>.</p>"""},
 {"h": "Find every place the string is written, including the fallbacks",
  "body": """<p>Grep the whole tree, not just the main call path. The id hides in default arguments, in a retry branch that picks a cheaper model, in a batch request body, in an infrastructure variable and in a test fixture. A migration that misses the fallback branch converts one outage into two.</p>"""},
 {"h": "Replace with a pinned successor, then diary the new date",
  "body": """<p>Take the replacement from the deprecations page and pin it. Then read <code>shutdown_date</code> on the id you just pinned and put it in a calendar, because the successor has one too. A migration that lands on a floating alias to avoid this has traded a dated failure for an undated one.</p>"""},
],
"verify": """<p>Re-run the script. Nothing should be reported as retired, and every id you passed should come back with either a future date or none.</p>
<pre><code class="language-bash">python3 openai_model_shutdown_audit.py --model gpt-5.6-sol --model gpt-5.6-terra
# 2 model id(s) checked, 0 past their shutdown date</code></pre>""",
"code_intro": "One GET and no writes: a project key set to Read Only is enough, and is what this should hold. The classifier is pure and takes the date to compare against as an argument, because a rule about whether a day has passed is only testable if the day can be fixed &mdash; and because the interesting case, a shutdown date that lands on today, exists for exactly 24 hours a year and will never show up in a test that uses the real clock.",
"py_file": "openai_model_shutdown_audit.py",
"py": '''"""Report OpenAI model ids whose published shutdown date has already passed.

Read only. One GET request, no writes: give this a project key set to Read Only.
The repair is printed, never performed, because this script holds a credential
that can spend real money on inference.
"""
import argparse
import datetime as dt
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("openai_model_shutdown_audit")

API = "https://api.openai.com/v1"

# Printed beside a dead id so the reader is not sent back to the deprecations
# page for the obvious part. Matched longest prefix first, and deliberately
# family-level: this says where a line went, not that any one snapshot is a
# drop-in replacement for another.
SUCCESSORS = (
    ("gpt-image-1", "gpt-image-2"),
    ("chatgpt-image", "gpt-image-2"),
    ("dall-e", "gpt-image-2"),
    ("gpt-5-nano", "gpt-5.6-luna"),
    ("gpt-5-mini", "gpt-5.6-terra"),
    ("gpt-5-pro", "gpt-5.6-sol"),
    ("gpt-5", "gpt-5.6-sol"),
    ("o4-mini", "gpt-5.6-terra"),
    ("o3-pro", "gpt-5.6-sol"),
    ("o3", "gpt-5.6-sol"),
    ("o1", "gpt-5.6-sol"),
    ("gpt-4", "gpt-5.6-sol"),
)

FAILING = ("retired", "retiring-today")


def successor(model_id):
    """The family a retired id was folded into, or None if this script has no
    opinion. An unknown id is left without a suggestion rather than pointed at
    a guess."""
    for prefix, replacement in SUCCESSORS:
        if model_id.startswith(prefix):
            return replacement
    return None


def parse_day(value):
    """Read a shutdown_date into a date, or None when it cannot be read.

    The field is a plain YYYY-MM-DD string. A full timestamp is tolerated by
    taking the date part. Anything else returns None rather than a guess,
    because a guess here either invents an outage or hides one.
    """
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        return dt.date.fromisoformat(raw.split("T")[0])
    except ValueError:
        return None


def verdict(model, today):
    """Classify one entry from GET /v1/models against a date you pass in.

    Pure, so the boundary cases can be tested at a fixed date instead of at
    whatever day the suite happens to run. Returns (state, detail).
    """
    model_id = str(model.get("id") or "").strip()
    if not model_id:
        return ("unreadable", "entry has no id field")

    raw = model.get("shutdown_date")
    if raw is None or str(raw).strip() == "":
        return ("open",
                "no shutdown date published. That is the current state of the "
                "field, not a guarantee: re-read it on a schedule.")

    day = parse_day(raw)
    if day is None:
        return ("unreadable-date",
                "shutdown_date is %r, which is not a date this script will "
                "guess at. Check it by hand." % (raw,))

    days = (day - today).days
    if days < 0:
        return ("retired",
                "shut down on %s, %d day(s) ago. Calls naming this id return "
                "404 model_not_found, which is the same error a misspelled "
                "model name returns." % (day.isoformat(), -days))
    if days == 0:
        return ("retiring-today",
                "shuts down today (%s). Requests may already be failing; treat "
                "this as an outage in progress, not a warning."
                % (day.isoformat(),))
    return ("scheduled",
            "shuts down on %s, %d day(s) from now. Still routable today."
            % (day.isoformat(), days))


def get(session, path):
    r = session.get(API + path, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from OpenAI: the key is wrong, revoked, or belongs "
                         "to another organization")
    r.raise_for_status()
    return r.json()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", action="append", default=[],
                    help="only report this id; repeatable. Pass the ids your "
                         "code actually names to keep the report about you")
    ap.add_argument("--show-all", action="store_true",
                    help="also print ids that are fine")
    args = ap.parse_args()

    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        log.error("set OPENAI_API_KEY (a project key set to Read Only)")
        return 2

    session = requests.Session()
    session.headers.update({"Authorization": "Bearer " + key})

    models = get(session, "/models").get("data", [])
    if not models:
        log.info("the models list came back empty for this key")
        return 0

    wanted = set(args.model)
    if wanted:
        listed = {str(m.get("id") or "") for m in models}
        for missing in sorted(wanted - listed):
            log.warning("%-15s %s  not in the models list at all, so there is no "
                        "shutdown_date left to read. An id that has been dropped "
                        "from the list is already gone.", "absent", missing)
        models = [m for m in models if str(m.get("id") or "") in wanted]

    today = dt.date.today()
    bad = 0
    for model in sorted(models, key=lambda m: str(m.get("id") or "")):
        state, detail = verdict(model, today)
        model_id = str(model.get("id") or "?")
        line = "%-15s %s  %s" % (state, model_id, detail)
        if state in FAILING:
            bad += 1
            log.warning(line)
            replacement = successor(model_id)
            if replacement:
                log.warning("  repair: change model=%r to model=%r at every call "
                            "site, then read shutdown_date on the new id",
                            model_id, replacement)
            else:
                log.warning("  repair: take the replacement from the "
                            "deprecations page and pin it")
        elif state in ("unreadable", "unreadable-date"):
            log.warning(line)
        elif args.show_all or state == "scheduled":
            log.info(line)

    log.info("%d model id(s) checked, %d past their shutdown date",
             len(models), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "openai-model-shutdown-audit.mjs",
"js": '''/**
 * Report OpenAI model ids whose published shutdown date has already passed.
 *
 * Read only. One GET request, no writes: give this a project key set to Read
 * Only. The repair is printed, never performed.
 */
const API = 'https://api.openai.com/v1';

// Matched longest prefix first, and deliberately family-level: this says where a
// line went, not that any one snapshot is a drop-in replacement for another.
const SUCCESSORS = [
  ['gpt-image-1', 'gpt-image-2'],
  ['chatgpt-image', 'gpt-image-2'],
  ['dall-e', 'gpt-image-2'],
  ['gpt-5-nano', 'gpt-5.6-luna'],
  ['gpt-5-mini', 'gpt-5.6-terra'],
  ['gpt-5-pro', 'gpt-5.6-sol'],
  ['gpt-5', 'gpt-5.6-sol'],
  ['o4-mini', 'gpt-5.6-terra'],
  ['o3-pro', 'gpt-5.6-sol'],
  ['o3', 'gpt-5.6-sol'],
  ['o1', 'gpt-5.6-sol'],
  ['gpt-4', 'gpt-5.6-sol'],
];

const FAILING = ['retired', 'retiring-today'];

/** The family a retired id was folded into, or null if this script has no opinion. */
export function successor(modelId) {
  for (const [prefix, replacement] of SUCCESSORS) {
    if (modelId.startsWith(prefix)) return replacement;
  }
  return null;
}

/**
 * Read a shutdown_date into a UTC date, or null when it cannot be read. The
 * field is a plain YYYY-MM-DD string; a full timestamp is tolerated by taking
 * the date part. Anything else returns null rather than a guess, because a
 * guess here either invents an outage or hides one.
 */
export function parseDay(value) {
  const raw = String(value ?? '').trim().split('T')[0];
  if (!/^\\d{4}-\\d{2}-\\d{2}$/.test(raw)) return null;
  const ms = Date.parse(`${raw}T00:00:00Z`);
  return Number.isNaN(ms) ? null : new Date(ms);
}

const DAY = 86400000;

/**
 * Classify one entry from GET /v1/models against a date you pass in. Pure, so
 * the boundary cases can be tested at a fixed date instead of at whatever day
 * the suite happens to run. Returns [state, detail].
 */
export function verdict(model, today) {
  const modelId = String(model.id ?? '').trim();
  if (!modelId) return ['unreadable', 'entry has no id field'];

  const raw = model.shutdown_date;
  if (raw === null || raw === undefined || String(raw).trim() === '') {
    return ['open',
      'no shutdown date published. That is the current state of the field, ' +
      'not a guarantee: re-read it on a schedule.'];
  }

  const day = parseDay(raw);
  if (day === null) {
    return ['unreadable-date',
      `shutdown_date is ${JSON.stringify(raw)}, which is not a date this ` +
      'script will guess at. Check it by hand.'];
  }

  const iso = day.toISOString().slice(0, 10);
  const days = Math.round((day.getTime() - today.getTime()) / DAY);
  if (days < 0) {
    return ['retired',
      `shut down on ${iso}, ${-days} day(s) ago. Calls naming this id return ` +
      '404 model_not_found, which is the same error a misspelled model name returns.'];
  }
  if (days === 0) {
    return ['retiring-today',
      `shuts down today (${iso}). Requests may already be failing; treat this ` +
      'as an outage in progress, not a warning.'];
  }
  return ['scheduled',
    `shuts down on ${iso}, ${days} day(s) from now. Still routable today.`];
}

async function get(key, path) {
  const res = await fetch(API + path, {
    headers: { Authorization: `Bearer ${key}` },
  });
  if (res.status === 401) {
    throw new Error('401 from OpenAI: the key is wrong, revoked, or belongs to ' +
                    'another organization');
  }
  if (!res.ok) throw new Error(`${res.status} from ${path}`);
  return res.json();
}

async function main() {
  const key = process.env.OPENAI_API_KEY;
  if (!key) {
    console.error('set OPENAI_API_KEY (a project key set to Read Only)');
    process.exitCode = 2;
    return;
  }

  const wanted = new Set(process.argv.reduce((acc, arg, i) => (
    arg === '--model' && process.argv[i + 1] ? [...acc, process.argv[i + 1]] : acc
  ), []));
  const showAll = process.argv.includes('--show-all');

  const { data = [] } = await get(key, '/models');
  if (data.length === 0) {
    console.log('the models list came back empty for this key');
    return;
  }

  let models = data;
  if (wanted.size > 0) {
    const listed = new Set(data.map((m) => String(m.id ?? '')));
    for (const missing of [...wanted].filter((m) => !listed.has(m)).sort()) {
      console.warn(`${'absent'.padEnd(15)} ${missing}  not in the models list at ` +
        'all, so there is no shutdown_date left to read. An id that has been ' +
        'dropped from the list is already gone.');
    }
    models = data.filter((m) => wanted.has(String(m.id ?? '')));
  }

  const today = new Date(`${new Date().toISOString().slice(0, 10)}T00:00:00Z`);
  let bad = 0;
  for (const model of [...models].sort((a, b) =>
    String(a.id ?? '').localeCompare(String(b.id ?? '')))) {
    const [state, detail] = verdict(model, today);
    const modelId = String(model.id ?? '?');
    const line = `${state.padEnd(15)} ${modelId}  ${detail}`;
    if (FAILING.includes(state)) {
      bad += 1;
      console.warn(line);
      const replacement = successor(modelId);
      console.warn(replacement
        ? `  repair: change model="${modelId}" to model="${replacement}" at ` +
          'every call site, then read shutdown_date on the new id'
        : '  repair: take the replacement from the deprecations page and pin it');
    } else if (state === 'unreadable' || state === 'unreadable-date') {
      console.warn(line);
    } else if (showAll || state === 'scheduled') {
      console.log(line);
    }
  }

  console.log(`${models.length} model id(s) checked, ${bad} past their shutdown date`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Every test runs against a fixed date. The two that earn their place are the boundaries: a shutdown date of <em>today</em> is an outage happening now rather than a warning, and a null <code>shutdown_date</code> is the absence of a published date rather than a promise &mdash; collapsing either into its neighbour is how a check like this gets ignored or, worse, believed.",
"test_py_file": "test_openai_model_shutdown_audit.py",
"test_py": '''import datetime as dt

from openai_model_shutdown_audit import parse_day, successor, verdict

TODAY = dt.date(2026, 8, 30)


def test_shutdown_date_is_read_as_a_plain_day():
    assert parse_day("2026-12-11") == dt.date(2026, 12, 11)
    assert parse_day("2026-12-11T00:00:00Z") == dt.date(2026, 12, 11)
    assert parse_day("") is None
    assert parse_day(None) is None
    assert parse_day("December 2026") is None


def test_a_date_already_passed_is_retired():
    state, detail = verdict({"id": "gpt-4-turbo", "shutdown_date": "2026-06-15"},
                            TODAY)
    assert state == "retired"
    assert "76 day(s) ago" in detail
    assert "misspelled" in detail


def test_a_shutdown_date_of_today_is_its_own_state():
    # The whole point of the note: this is happening now, not soon.
    state, detail = verdict({"id": "gpt-5-2025-08-07", "shutdown_date": "2026-08-30"},
                            TODAY)
    assert state == "retiring-today"
    assert "outage in progress" in detail


def test_a_future_date_belongs_to_the_other_note():
    state, detail = verdict({"id": "gpt-5-2025-08-07", "shutdown_date": "2026-12-11"},
                            TODAY)
    assert state == "scheduled"
    assert "103 day(s)" in detail


def test_no_shutdown_date_is_not_a_promise():
    state, detail = verdict({"id": "gpt-5.6-sol", "shutdown_date": None}, TODAY)
    assert state == "open"
    assert "not a guarantee" in detail
    assert verdict({"id": "gpt-5.6-sol"}, TODAY)[0] == "open"


def test_an_unreadable_date_is_not_silently_healthy():
    assert verdict({"id": "x", "shutdown_date": "soon"}, TODAY)[0] == "unreadable-date"
    assert verdict({"shutdown_date": "2026-01-01"}, TODAY)[0] == "unreadable"


def test_the_successor_is_family_level_and_admits_ignorance():
    assert successor("gpt-5-mini-2025-08-07") == "gpt-5.6-terra"
    assert successor("gpt-5-2025-08-07") == "gpt-5.6-sol"
    assert successor("dall-e-3") == "gpt-image-2"
    assert successor("some-vendor-model") is None
''',
"test_js_file": "openai-model-shutdown-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { parseDay, successor, verdict } from './openai-model-shutdown-audit.mjs';

const TODAY = new Date('2026-08-30T00:00:00Z');

test('shutdown_date is read as a plain day', () => {
  assert.equal(parseDay('2026-12-11').toISOString().slice(0, 10), '2026-12-11');
  assert.equal(parseDay('2026-12-11T00:00:00Z').toISOString().slice(0, 10),
               '2026-12-11');
  assert.equal(parseDay(''), null);
  assert.equal(parseDay(null), null);
  assert.equal(parseDay('December 2026'), null);
});

test('a date already passed is retired', () => {
  const [state, detail] = verdict(
    { id: 'gpt-4-turbo', shutdown_date: '2026-06-15' }, TODAY);
  assert.equal(state, 'retired');
  assert.match(detail, /76 day\\(s\\) ago/);
  assert.match(detail, /misspelled/);
});

test('a shutdown date of today is its own state', () => {
  const [state, detail] = verdict(
    { id: 'gpt-5-2025-08-07', shutdown_date: '2026-08-30' }, TODAY);
  assert.equal(state, 'retiring-today');
  assert.match(detail, /outage in progress/);
});

test('a future date belongs to the other note', () => {
  const [state, detail] = verdict(
    { id: 'gpt-5-2025-08-07', shutdown_date: '2026-12-11' }, TODAY);
  assert.equal(state, 'scheduled');
  assert.match(detail, /103 day\\(s\\)/);
});

test('no shutdown date is not a promise', () => {
  const [state, detail] = verdict({ id: 'gpt-5.6-sol', shutdown_date: null }, TODAY);
  assert.equal(state, 'open');
  assert.match(detail, /not a guarantee/);
  assert.equal(verdict({ id: 'gpt-5.6-sol' }, TODAY)[0], 'open');
});

test('an unreadable date is not silently healthy', () => {
  assert.equal(verdict({ id: 'x', shutdown_date: 'soon' }, TODAY)[0],
               'unreadable-date');
  assert.equal(verdict({ shutdown_date: '2026-01-01' }, TODAY)[0], 'unreadable');
});

test('the successor is family level and admits ignorance', () => {
  assert.equal(successor('gpt-5-mini-2025-08-07'), 'gpt-5.6-terra');
  assert.equal(successor('gpt-5-2025-08-07'), 'gpt-5.6-sol');
  assert.equal(successor('dall-e-3'), 'gpt-image-2');
  assert.equal(successor('some-vendor-model'), null);
});
''',
"faq": [
 ("How do I tell a retired model from a typo, when both return the same 404?",
  "By reading GET /v1/models. The error body cannot tell them apart because it does not know which applies, but the list can: an entry with a shutdown_date in the past was retired on a published date, while a string that never appears in the list at any point was never a model this key could call."),
 ("Does OpenAI warn me before the shutdown date on a successful call?",
  "No. Successful inference responses carry no deprecation header and no warnings array. The notice is published on the deprecations page, and the machine-readable form of it is the shutdown_date field on the models list. If nothing reads that field, nothing warns you."),
 ("A model has no shutdown_date at all. Is it safe?",
  "It is unscheduled, which is not the same as permanent. OpenAI typically publishes three to six months of notice, so a null today can be a date tomorrow. The value of the check is that it is one request, so running it weekly costs nothing and turns the announcement into something your pipeline sees."),
 ("Should I switch to an unpinned alias so this never happens again?",
  "That trades a dated failure for an undated one. An alias is repointed at new weights without notice, so the model changes underneath you with no deploy and no error; the symptoms are drifting evals and token counts rather than a 404. Pinning plus a scheduled read of shutdown_date is the combination that gives you both stability and warning."),
 ("Does Anthropic have the same field?",
  "No. Anthropic's model object carries created_at, max_input_tokens and max_output_tokens but no retirement date, so on that side the date has to come from the published deprecation table and the API can only tell you whether the id is still callable at all. That is why the Anthropic check in this section is built on the id disappearing from the list rather than on a date."),
],
"related": [REL_SOON, REL_GONE, REL_ALIAS],
"citations": [CITE_OA_MODELS, CITE_OA_DEPRECATIONS, CITE_AN_DEPRECATIONS],
},

{
"slug": "model-retiring-within-90-days",
"title": "A model you still call retires in under 90 days",
"description": "The shutdown_date is real but still ahead of you. One GET turns that field into a migration schedule, ordered by days left and by the traffic each id carries.",
"h1": "a model you still call retires in under 90 days",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["openai model retirement schedule", "openai shutdown_date upcoming",
             "plan llm model migration", "model deprecation 90 days",
             "openai usage by model"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Reads OPENAI_API_KEY, and optionally OPENAI_ADMIN_KEY to weight the report by traffic.",
"lead": "Every call is returning <code>200</code>. Latency is normal, cost is normal, the evals are green. The only thing wrong is a field nobody is reading: <code>shutdown_date</code> on the model you route most of your traffic to is a real date, and it is close. Nothing will change until that morning, and then everything will, all at once, in every code path that names the id.",
"short_answer": """<p><code>GET /v1/models</code>, read <code>shutdown_date</code> on each entry, and flag the ones that are non-null and less than 90 days out. That is the window where you can still do this on a Tuesday afternoon instead of during an incident.</p>
<p>With an admin-read key, join it against <code>GET /v1/organization/usage/completions?bucket_width=1d&amp;group_by[]=model</code> so the list is ordered by how much traffic each id actually carries. A model with a date in six weeks and four million requests is a different piece of work from one with the same date and zero.</p>""",
"problem": """<p>The hard part of a model migration is never the string. It is finding out about it early enough that the swap can be tested, evaluated and rolled out normally, rather than pasted in at 07:00 by whoever answered the page. Nothing in the request path tells you it is coming, so the deadline arrives through email, chat, or a colleague who happened to read a changelog &mdash; three channels that all fail quietly.</p>
<p>The other half is that "we should migrate" is not actionable until it has a size. Which ids? How much traffic on each? Which are load-bearing and which are strings left in a config file from an experiment two quarters ago? Without that, the work gets deferred at every planning meeting because nobody can say how big it is, and the deferral holds right up to the day it cannot.</p>""",
"why": """<p><strong>The field is there, but only if something reads it.</strong> <code>shutdown_date</code> is on every entry in the models list, which means the deadline is machine-readable and free to check. It is also entirely passive: no header, no warning on a successful response, nothing in an SDK exception, because there is no exception. A check that never runs is indistinguishable from a field that does not exist.</p>
<p><strong>Days remaining is only half of the priority.</strong> Two ids with the same date can be a week of work and five minutes of work. The traffic split lives on the Admin usage endpoints, not on the models list, and it needs a different credential &mdash; an organization admin key, because usage belongs to the organization rather than to a project. The script treats that key as optional and says so when it is missing, rather than pretending the ordering is complete.</p>
<p><strong>Zero traffic on a dated id is a finding, not a pass.</strong> An id with a shutdown date and no requests in the last 30 days is usually a string in a config file, a fallback branch, or a batch job that runs monthly. The first two want deleting, the third is a landmine with a fuse a month long. What none of them wants is to be filtered out of the report as "unused".</p>
<p><strong>The other provider does not give you this field at all.</strong> Anthropic publishes retirement dates on its deprecations page and exposes none of them through the API: the model object has <code>created_at</code>, <code>max_input_tokens</code> and <code>max_output_tokens</code>, and no date. So the same check on that side is a join against a table you maintain by hand, and the API's only contribution is <a href="/llm/retired-model-id-still-in-code/">whether the id is still callable</a>.</p>""",
"steps": [
 {"h": "Read the models list and keep the non-null dates",
  "body": """<p><code>GET https://api.openai.com/v1/models</code> with a Read Only project key. Most entries have <code>shutdown_date</code> null; the ones that do not are your calendar.</p>"""},
 {"h": "Set a window that matches how long a migration takes you",
  "body": """<p>Ninety days is a reasonable default because it is roughly the notice period, but the number that matters is your own: evaluation, canary and rollout for a model change. Make it an argument. A team that needs six weeks and a team that needs one should not be reading the same report.</p>"""},
 {"h": "Join the dates against traffic",
  "body": """<p>With an organization admin key: <code>GET /v1/organization/usage/completions?start_time=&lt;30d ago&gt;&amp;bucket_width=1d&amp;group_by[]=model</code>, then sum <code>data[].results[].num_model_requests</code> per <code>results[].model</code>. Sort the flagged ids by that number so the biggest migration is on the first line.</p>"""},
 {"h": "Treat an urgent date differently from a due one",
  "body": """<p>Under a month left is not the same status as under three. The first is scheduling work now; the second is putting it in the next cycle. Two states, printed differently, or the report reads as one undifferentiated wall and gets skimmed.</p>"""},
 {"h": "Pin the successor and re-run the check on it",
  "body": """<p>The replacement has a shutdown date too, or will have. The migration is finished when the new id is pinned <em>and</em> the check has been run against it, so the next deadline is already visible rather than waiting to be discovered the same way.</p>"""},
],
"verify": """<p>Re-run after the migration. The window should be empty, and the ids you moved to should report a date well outside it, or none.</p>
<pre><code class="language-bash">python3 openai_model_retirement_window.py --window 90
# 41 dated model(s), 0 inside a 90 day window</code></pre>""",
"code_intro": "Two GETs and no writes. The models list needs only a Read Only project key; the traffic join needs an organization admin key and is skipped, loudly, when there is not one. The classifier takes both the date to measure from and the window, so the thresholds are arguments rather than constants &mdash; which is the only honest way to write a rule whose right answer depends on how long your own rollout takes.",
"py_file": "openai_model_retirement_window.py",
"py": '''"""Turn OpenAI shutdown dates into a migration schedule, ordered by urgency.

Read only. GET requests and nothing else: the models list needs a project key
set to Read Only, and the optional traffic join needs an organization admin key
because usage belongs to the organization rather than to a project. The repair
is printed, never performed.
"""
import argparse
import datetime as dt
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("openai_model_retirement_window")

API = "https://api.openai.com/v1"

FLAGGED = ("urgent", "due", "expired", "unreadable-date")


def parse_day(value):
    """Read a shutdown_date into a date, or None when it cannot be read."""
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        return dt.date.fromisoformat(raw.split("T")[0])
    except ValueError:
        return None


def traffic_note(requests_30d):
    """How the traffic column is described, including when there is none.

    None means the admin key was not supplied, which is different from zero and
    has to read differently, or an unmeasured id looks like an unused one.
    """
    if requests_30d is None:
        return ("traffic unknown: no admin key, so this is ordered by date "
                "alone")
    if requests_30d == 0:
        return ("no requests in the last 30 days, so this is probably a string "
                "in a config file or a monthly job rather than live traffic")
    return "%d request(s) in the last 30 days" % (requests_30d,)


def plan(model, today, window_days=90, urgent_within=30, requests_30d=None):
    """Classify one models-list entry into a place in the migration schedule.

    Pure, and both thresholds are arguments: the right window is however long a
    model change takes to evaluate and roll out where you work, and that is not
    a constant this script gets to choose. Returns (state, detail).
    """
    raw = model.get("shutdown_date")
    if raw is None or str(raw).strip() == "":
        return ("unscheduled",
                "no shutdown date published today. Re-read the field rather "
                "than trusting this answer for a quarter.")

    day = parse_day(raw)
    if day is None:
        return ("unreadable-date",
                "shutdown_date is %r, which this script will not guess at."
                % (raw,))

    days = (day - today).days
    note = traffic_note(requests_30d)
    if days < 0:
        return ("expired",
                "shut down %d day(s) ago on %s. This is past planning; calls "
                "naming it are already failing. %s"
                % (-days, day.isoformat(), note))
    if days <= urgent_within:
        return ("urgent",
                "%d day(s) left, shutting down %s. Under %d days is scheduling "
                "work now, not next cycle. %s"
                % (days, day.isoformat(), urgent_within, note))
    if days <= window_days:
        return ("due",
                "%d day(s) left, shutting down %s. Inside the %d day window. %s"
                % (days, day.isoformat(), window_days, note))
    return ("later",
            "%d day(s) left, shutting down %s. Outside the window; nothing to "
            "do yet. %s" % (days, day.isoformat(), note))


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=60)
    if r.status_code in (401, 403):
        raise SystemExit("%d from OpenAI on %s: check the key, and that an "
                         "organization admin key is used for /organization/*"
                         % (r.status_code, path))
    r.raise_for_status()
    return r.json()


def usage_by_model(admin_key, days):
    """Sum num_model_requests per model over the window.

    Needs an organization admin key: the usage endpoints reject project keys
    outright. Returns {} when no key was given, which the caller reports as
    unknown rather than as zero.
    """
    if not admin_key:
        return {}
    session = requests.Session()
    session.headers.update({"Authorization": "Bearer " + admin_key})
    start = int((dt.datetime.now(dt.timezone.utc)
                 - dt.timedelta(days=days)).timestamp())
    totals = {}
    params = {"start_time": start, "bucket_width": "1d",
              "group_by[]": "model", "limit": 31}
    while True:
        page = get(session, "/organization/usage/completions", **params)
        for bucket in page.get("data", []):
            for row in bucket.get("results", []):
                name = row.get("model")
                if name:
                    totals[name] = totals.get(name, 0) + int(
                        row.get("num_model_requests") or 0)
        if not page.get("has_more"):
            break
        params["page"] = page.get("next_page")
        if not params["page"]:
            break
    return totals


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--window", type=int, default=90,
                    help="days ahead to treat as inside the migration window")
    ap.add_argument("--urgent-within", type=int, default=30,
                    help="days ahead that count as urgent rather than due")
    ap.add_argument("--usage-days", type=int, default=30,
                    help="days of usage to sum when an admin key is available")
    args = ap.parse_args()

    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        log.error("set OPENAI_API_KEY (a project key set to Read Only)")
        return 2
    admin = os.environ.get("OPENAI_ADMIN_KEY")
    if not admin:
        log.warning("OPENAI_ADMIN_KEY is not set: the report will be ordered by "
                    "date alone, with no idea which ids carry traffic")

    session = requests.Session()
    session.headers.update({"Authorization": "Bearer " + key})
    models = get(session, "/models").get("data", [])
    dated = [m for m in models if str(m.get("shutdown_date") or "").strip()]

    totals = usage_by_model(admin, args.usage_days)

    rows = []
    today = dt.date.today()
    for model in dated:
        model_id = str(model.get("id") or "?")
        seen = totals.get(model_id) if admin else None
        if admin and seen is None:
            seen = 0
        state, detail = plan(model, today, args.window, args.urgent_within, seen)
        rows.append((parse_day(model.get("shutdown_date")) or dt.date.max,
                     -(seen or 0), state, model_id, detail))

    flagged = 0
    for _day, _neg, state, model_id, detail in sorted(rows):
        line = "%-14s %s  %s" % (state, model_id, detail)
        if state in FLAGGED:
            flagged += 1
            log.warning(line)
            log.warning("  repair: pin the successor from the deprecations page, "
                        "then re-run this against the new id so its own date is "
                        "on the calendar before it is a surprise")
        else:
            log.info(line)

    log.info("%d dated model(s), %d inside a %d day window",
             len(dated), flagged, args.window)
    return 1 if flagged else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "openai-model-retirement-window.mjs",
"js": '''/**
 * Turn OpenAI shutdown dates into a migration schedule, ordered by urgency.
 *
 * Read only. GET requests and nothing else: the models list needs a project key
 * set to Read Only, and the optional traffic join needs an organization admin
 * key. The repair is printed, never performed.
 */
const API = 'https://api.openai.com/v1';
const DAY = 86400000;
const FLAGGED = ['urgent', 'due', 'expired', 'unreadable-date'];

/** Read a shutdown_date into a UTC date, or null when it cannot be read. */
export function parseDay(value) {
  const raw = String(value ?? '').trim().split('T')[0];
  if (!/^\\d{4}-\\d{2}-\\d{2}$/.test(raw)) return null;
  const ms = Date.parse(`${raw}T00:00:00Z`);
  return Number.isNaN(ms) ? null : new Date(ms);
}

/**
 * How the traffic column is described, including when there is none. null means
 * the admin key was not supplied, which is different from zero and has to read
 * differently, or an unmeasured id looks like an unused one.
 */
export function trafficNote(requests30d) {
  if (requests30d === null || requests30d === undefined) {
    return 'traffic unknown: no admin key, so this is ordered by date alone';
  }
  if (requests30d === 0) {
    return 'no requests in the last 30 days, so this is probably a string in a ' +
           'config file or a monthly job rather than live traffic';
  }
  return `${requests30d} request(s) in the last 30 days`;
}

/**
 * Classify one models-list entry into a place in the migration schedule. Pure,
 * and both thresholds are arguments: the right window is however long a model
 * change takes to evaluate and roll out where you work. Returns [state, detail].
 */
export function plan(model, today, windowDays = 90, urgentWithin = 30,
                     requests30d = null) {
  const raw = model.shutdown_date;
  if (raw === null || raw === undefined || String(raw).trim() === '') {
    return ['unscheduled',
      'no shutdown date published today. Re-read the field rather than ' +
      'trusting this answer for a quarter.'];
  }

  const day = parseDay(raw);
  if (day === null) {
    return ['unreadable-date',
      `shutdown_date is ${JSON.stringify(raw)}, which this script will not guess at.`];
  }

  const iso = day.toISOString().slice(0, 10);
  const days = Math.round((day.getTime() - today.getTime()) / DAY);
  const note = trafficNote(requests30d);
  if (days < 0) {
    return ['expired',
      `shut down ${-days} day(s) ago on ${iso}. This is past planning; calls ` +
      `naming it are already failing. ${note}`];
  }
  if (days <= urgentWithin) {
    return ['urgent',
      `${days} day(s) left, shutting down ${iso}. Under ${urgentWithin} days is ` +
      `scheduling work now, not next cycle. ${note}`];
  }
  if (days <= windowDays) {
    return ['due',
      `${days} day(s) left, shutting down ${iso}. Inside the ${windowDays} day ` +
      `window. ${note}`];
  }
  return ['later',
    `${days} day(s) left, shutting down ${iso}. Outside the window; nothing to ` +
    `do yet. ${note}`];
}

async function get(key, path, params = {}) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v);
  const res = await fetch(url, { headers: { Authorization: `Bearer ${key}` } });
  if (res.status === 401 || res.status === 403) {
    throw new Error(`${res.status} from OpenAI on ${path}: check the key, and ` +
      'that an organization admin key is used for /organization/*');
  }
  if (!res.ok) throw new Error(`${res.status} from ${path}`);
  return res.json();
}

export async function usageByModel(adminKey, days) {
  if (!adminKey) return new Map();
  const start = Math.floor((Date.now() - days * DAY) / 1000);
  const totals = new Map();
  const params = { start_time: start, bucket_width: '1d',
                   'group_by[]': 'model', limit: 31 };
  for (;;) {
    const page = await get(adminKey, '/organization/usage/completions', params);
    for (const bucket of page.data ?? []) {
      for (const row of bucket.results ?? []) {
        if (!row.model) continue;
        totals.set(row.model,
          (totals.get(row.model) ?? 0) + Number(row.num_model_requests ?? 0));
      }
    }
    if (!page.has_more || !page.next_page) break;
    params.page = page.next_page;
  }
  return totals;
}

async function main() {
  const key = process.env.OPENAI_API_KEY;
  if (!key) {
    console.error('set OPENAI_API_KEY (a project key set to Read Only)');
    process.exitCode = 2;
    return;
  }
  const admin = process.env.OPENAI_ADMIN_KEY;
  if (!admin) {
    console.warn('OPENAI_ADMIN_KEY is not set: the report will be ordered by ' +
                 'date alone, with no idea which ids carry traffic');
  }

  const arg = (name, fallback) => Number(process.argv.includes(name)
    ? process.argv[process.argv.indexOf(name) + 1] : fallback) || fallback;
  const windowDays = arg('--window', 90);
  const urgentWithin = arg('--urgent-within', 30);
  const usageDays = arg('--usage-days', 30);

  const { data = [] } = await get(key, '/models');
  const dated = data.filter((m) => String(m.shutdown_date ?? '').trim() !== '');
  const totals = await usageByModel(admin, usageDays);

  const today = new Date(`${new Date().toISOString().slice(0, 10)}T00:00:00Z`);
  const rows = dated.map((model) => {
    const modelId = String(model.id ?? '?');
    const seen = admin ? (totals.get(modelId) ?? 0) : null;
    const [state, detail] = plan(model, today, windowDays, urgentWithin, seen);
    const day = parseDay(model.shutdown_date);
    return { sort: day ? day.getTime() : Infinity, seen: seen ?? 0,
             state, modelId, detail };
  }).sort((a, b) => a.sort - b.sort || b.seen - a.seen);

  let flagged = 0;
  for (const row of rows) {
    const line = `${row.state.padEnd(14)} ${row.modelId}  ${row.detail}`;
    if (FLAGGED.includes(row.state)) {
      flagged += 1;
      console.warn(line);
      console.warn('  repair: pin the successor from the deprecations page, then ' +
        're-run this against the new id so its own date is on the calendar ' +
        'before it is a surprise');
    } else {
      console.log(line);
    }
  }

  console.log(`${dated.length} dated model(s), ${flagged} inside a ${windowDays} day window`);
  process.exitCode = flagged ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The tests fix the date and then move the thresholds, because both are arguments and the whole value of the note is in where the lines fall. The one to read is the traffic case: an id with no admin key behind it and an id with genuinely zero requests must not produce the same sentence, or a model nobody measured gets filed as a model nobody uses.",
"test_py_file": "test_openai_model_retirement_window.py",
"test_py": '''import datetime as dt

from openai_model_retirement_window import plan, traffic_note

TODAY = dt.date(2026, 8, 30)


def dated(day, model_id="gpt-5-2025-08-07"):
    return {"id": model_id, "shutdown_date": day}


def test_a_date_inside_the_window_is_due():
    state, detail = plan(dated("2026-11-15"), TODAY)
    assert state == "due"
    assert "77 day(s) left" in detail


def test_a_date_under_a_month_out_is_urgent_not_merely_due():
    state, detail = plan(dated("2026-09-20"), TODAY)
    assert state == "urgent"
    assert "not next cycle" in detail


def test_a_date_beyond_the_window_is_left_alone():
    assert plan(dated("2027-06-01"), TODAY)[0] == "later"


def test_the_window_and_the_urgency_line_are_both_arguments():
    model = dated("2026-11-15")
    assert plan(model, TODAY)[0] == "due"
    assert plan(model, TODAY, window_days=30)[0] == "later"
    assert plan(model, TODAY, window_days=90, urgent_within=120)[0] == "urgent"


def test_a_date_already_passed_is_out_of_scope_for_planning():
    state, detail = plan(dated("2026-07-01"), TODAY)
    assert state == "expired"
    assert "already failing" in detail


def test_no_date_is_unscheduled_rather_than_safe():
    state, detail = plan({"id": "gpt-5.6-sol"}, TODAY)
    assert state == "unscheduled"
    assert "Re-read" in detail
    assert plan({"id": "x", "shutdown_date": "Q4"}, TODAY)[0] == "unreadable-date"


def test_unmeasured_traffic_and_zero_traffic_do_not_read_the_same():
    assert "no admin key" in traffic_note(None)
    assert "config file" in traffic_note(0)
    assert "4000000 request(s)" in traffic_note(4000000)
    assert "config file" in plan(dated("2026-09-20"), TODAY, requests_30d=0)[1]
    assert "no admin key" in plan(dated("2026-09-20"), TODAY)[1]
''',
"test_js_file": "openai-model-retirement-window.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { plan, trafficNote } from './openai-model-retirement-window.mjs';

const TODAY = new Date('2026-08-30T00:00:00Z');
const dated = (day, id = 'gpt-5-2025-08-07') => ({ id, shutdown_date: day });

test('a date inside the window is due', () => {
  const [state, detail] = plan(dated('2026-11-15'), TODAY);
  assert.equal(state, 'due');
  assert.match(detail, /77 day\\(s\\) left/);
});

test('a date under a month out is urgent, not merely due', () => {
  const [state, detail] = plan(dated('2026-09-20'), TODAY);
  assert.equal(state, 'urgent');
  assert.match(detail, /not next cycle/);
});

test('a date beyond the window is left alone', () => {
  assert.equal(plan(dated('2027-06-01'), TODAY)[0], 'later');
});

test('the window and the urgency line are both arguments', () => {
  const model = dated('2026-11-15');
  assert.equal(plan(model, TODAY)[0], 'due');
  assert.equal(plan(model, TODAY, 30)[0], 'later');
  assert.equal(plan(model, TODAY, 90, 120)[0], 'urgent');
});

test('a date already passed is out of scope for planning', () => {
  const [state, detail] = plan(dated('2026-07-01'), TODAY);
  assert.equal(state, 'expired');
  assert.match(detail, /already failing/);
});

test('no date is unscheduled rather than safe', () => {
  const [state, detail] = plan({ id: 'gpt-5.6-sol' }, TODAY);
  assert.equal(state, 'unscheduled');
  assert.match(detail, /Re-read/);
  assert.equal(plan({ id: 'x', shutdown_date: 'Q4' }, TODAY)[0], 'unreadable-date');
});

test('unmeasured traffic and zero traffic do not read the same', () => {
  assert.match(trafficNote(null), /no admin key/);
  assert.match(trafficNote(0), /config file/);
  assert.match(trafficNote(4000000), /4000000 request\\(s\\)/);
  assert.match(plan(dated('2026-09-20'), TODAY, 90, 30, 0)[1], /config file/);
  assert.match(plan(dated('2026-09-20'), TODAY)[1], /no admin key/);
});
''',
"faq": [
 ("Why 90 days rather than 30 or 180?",
  "Because it is roughly the notice period, so it is the longest window in which the field is reliably populated. It is still the wrong number for most teams, which is why it is an argument: pick the time a model change actually takes you to evaluate, canary and roll out, and set the window to that."),
 ("Why does the traffic join need a different key?",
  "Usage and cost live on the organization, not on a project, so the /v1/organization/* endpoints reject project keys outright and want an organization admin key. The models list does not. The script keeps them separate and runs without the admin key, reporting the traffic column as unknown rather than pretending it is zero."),
 ("A flagged model has no traffic at all. Can I ignore it?",
  "No, but the work is different. Zero requests in 30 days usually means the id survives in a config default, a fallback branch or a job that runs monthly. The first two should be deleted rather than migrated; the third will fail on its next run, after the date, with nobody watching."),
 ("Does Anthropic expose a retirement date I can check the same way?",
  "No. The Claude models API returns created_at, display_name and the token limits, and no retirement date, so dates on that side come from the published deprecation table. The API contribution there is negative evidence: an id that has stopped appearing in GET /v1/models is already retired."),
 ("What stops the replacement from becoming the same problem in six months?",
  "Nothing, which is the point of the last step. Pin the successor and then run this same check against the new id, so its date is on the calendar the day you adopt it rather than the day it expires."),
],
"related": [REL_PAST, REL_GONE, REL_ALIAS],
"citations": [CITE_OA_MODELS, CITE_OA_DEPRECATIONS, CITE_AN_DEPRECATIONS, CITE_AN_MODELS],
},

{
"slug": "retired-model-id-still-in-code",
"title": "Retired model id in code fails every call with 404",
"description": "Anthropic drops a retired id from the models list entirely, with no date left to read. You find it by diffing your config strings against GET /v1/models.",
"h1": "a retired model id still sitting in the code",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["anthropic not_found_error", "claude model retired 404",
             "claude model deprecations", "anthropic list models",
             "claude-3-5-sonnet retired"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Reads ANTHROPIC_API_KEY, a workspace key, and sends only GET requests.",
"lead": "A batch job that runs on the first of the month failed on every request with <code>404</code> and <code>\"type\": \"not_found_error\"</code>, message <em>The requested resource could not be found.</em> The endpoint is right, the key works, the same key runs the rest of the application all day. The model id in that job's <code>params</code> block was retired months ago, and nothing else in the codebase names it, so nothing else broke and nobody knew.",
"short_answer": """<p>Collect every model string in your tree &mdash; configs, defaults, fallback branches, batch bodies, fixtures &mdash; and diff them against <code>GET /v1/models?limit=1000</code>. Anything not in <code>data[].id</code> is not callable. Confirm one at a time with <code>GET /v1/models/{id}</code>: a live id returns a model object, a retired one returns <code>404 not_found_error</code>.</p>
<p>There is no date to read here. Anthropic's model object carries no retirement field, so the only thing the API can tell you is presence or absence, and the date has to come from the published deprecation table.</p>""",
"problem": """<p>This is the failure that survives a migration. Somebody moves the main call path to the new model, tests it, ships it, and closes the ticket &mdash; and the old string stays alive in the three places nobody greps: the <code>model</code> default in a helper function's signature, the cheaper fallback used when the primary times out, and the <code>params</code> block of a batch that runs monthly. Each of them is exercised rarely enough to look fine for a quarter.</p>
<p>Then it fails on the worst possible schedule. The fallback breaks precisely when the primary is already struggling, so a partial degradation becomes a total one. The batch breaks on its next run, days after the retirement, with the error in a log nobody tails. And the 404 body says nothing about retirement: <em>the requested resource could not be found</em> is the same sentence you would get for a mistyped id.</p>""",
"why": """<p><strong>Retirement removes the id, it does not mark it.</strong> The models list is a list of what is callable now. A retired id is simply absent from it, and <code>GET /v1/models/{id}</code> returns the generic 404. There is no tombstone entry, no <code>status: "retired"</code>, no date field on the model object &mdash; so unlike the <a href="/llm/model-past-shutdown-date/">OpenAI side</a>, you cannot read the deadline from the API either before or after it passes.</p>
<p><strong>Absence is only detectable if you know what to look for.</strong> A diff needs both sides, and the API only gives you one. The other side is your own source tree, which is why this check takes the model strings as input rather than discovering them: nothing in the API knows what your config file says.</p>
<p><strong>Usage confirms the id is dead, never that it is alive.</strong> The Admin usage report grouped by model shows an id's traffic stopping dead on its retirement date, because the calls started failing, and a retired id never reappears. That makes it good confirming evidence and useless as a warning: by the time the shape is visible, the outage has already happened.</p>
<p><strong>Alive elsewhere is not alive here.</strong> Bedrock and Vertex run their own retirement schedules, generally later than the first-party API. An id that a colleague insists is still working may well be working, on a platform this key does not talk to. That is why an id which is neither in the live list nor on the deprecation table is reported as unknown rather than as retired.</p>""",
"steps": [
 {"h": "Collect the model strings, all of them",
  "body": """<p>Grep for the vendor prefix across the whole repository and the infrastructure that configures it: <code>grep -rn "claude-" --include='*.py' --include='*.ts' --include='*.yaml' .</code>, plus environment variables and secret stores. Default arguments and fallback branches are the two that get missed, and they are the two that fail worst.</p>"""},
 {"h": "List what is actually callable",
  "body": """<p><code>GET https://api.anthropic.com/v1/models?limit=1000</code> with <code>x-api-key</code> and <code>anthropic-version: 2023-06-01</code>, following <code>has_more</code> and <code>last_id</code>. This is the authority on what exists for this workspace right now.</p>"""},
 {"h": "Diff, then confirm one by one",
  "body": """<p>Anything in your strings but not in <code>data[].id</code> is the finding. Confirm each with <code>GET /v1/models/{id}</code> so a paging mistake does not turn into a false alarm; a retired id returns <code>404</code> with <code>not_found_error</code>, and the SDKs raise the typed 404 class rather than a generic error.</p>"""},
 {"h": "Separate retired from never-existed",
  "body": """<p>Join the missing ids against the deprecation table. One that matches is retired and has a documented replacement. One that matches nothing is a typo, a partner-platform id, or a model this workspace has not been granted &mdash; three different repairs, and calling all of them "retired" sends people to the wrong page.</p>"""},
 {"h": "Replace the string everywhere it appears, then re-run",
  "body": """<p>The replacement lines are documented: the Opus 4 and 4.1 line rolls forward to <code>claude-opus-4-8</code>, the Sonnet line to <code>claude-sonnet-4-6</code>, the Haiku and Instant line to <code>claude-haiku-4-5-20251001</code>. Re-run the script with the same input list afterwards; a clean run is the only proof that the fallback branch got the change too.</p>"""},
],
"verify": """<p>Feed the script the same list of strings after the change. Every one should come back as live.</p>
<pre><code class="language-bash">python3 anthropic_model_ids_audit.py --from-file models-in-use.txt
# 6 id(s) checked against 14 live model(s), 0 retired, 0 unknown</code></pre>""",
"code_intro": "GET requests only, with a workspace key. The classifier is pure and takes the live id set and the date as arguments, so the whole thing is testable without a network: what is callable comes from the API, what is retired comes from a table copied off the deprecations page, and the interesting conflict &mdash; the table saying retired while the API still lists the id &mdash; gets its own state rather than being resolved in favour of whichever check ran first.",
"py_file": "anthropic_model_ids_audit.py",
"py": '''"""Find retired Claude model ids still named in your configuration.

Read only. GET requests and nothing else: give this a workspace API key. The
repair is printed, never performed, because this script holds a credential that
can spend real money on inference.
"""
import argparse
import datetime as dt
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("anthropic_model_ids_audit")

API = "https://api.anthropic.com/v1"
VERSION = "2023-06-01"

# Copied from the published deprecations page, because the API has no retirement
# field at all: the model object carries created_at and the token limits and
# nothing about the end of life. A hardcoded table goes stale, so the live list
# from the API always wins over this one; see verdict().
RETIRED = {
    "claude-opus-4-1-20250805": "2026-08-05",
    "claude-opus-4-20250514": "2026-06-15",
    "claude-sonnet-4-20250514": "2026-06-15",
    "claude-3-haiku-20240307": "2026-04-20",
    "claude-3-7-sonnet-20250219": "2026-02-19",
    "claude-3-5-haiku-20241022": "2026-02-19",
    "claude-3-opus-20240229": "2026-01-05",
    "claude-3-5-sonnet-20240620": "2025-10-28",
    "claude-3-5-sonnet-20241022": "2025-10-28",
    "claude-3-sonnet-20240229": "2025-07-21",
    "claude-2.0": "2025-07-21",
    "claude-2.1": "2025-07-21",
    "claude-1.0": "2024-11-06",
    "claude-1.1": "2024-11-06",
    "claude-1.2": "2024-11-06",
    "claude-1.3": "2024-11-06",
    "claude-instant-1.0": "2024-11-06",
    "claude-instant-1.1": "2024-11-06",
    "claude-instant-1.2": "2024-11-06",
}

BAD = ("retired", "unknown", "table-stale", "unreadable")


def replacement(model_id):
    """Where a retired line rolls forward to, by family.

    Family level on purpose. This says the Opus line continues as Opus, not that
    any two snapshots behave the same: a model swap still needs evaluating.
    """
    if "opus" in model_id:
        return "claude-opus-4-8"
    if "haiku" in model_id or "instant" in model_id:
        return "claude-haiku-4-5-20251001"
    if "sonnet" in model_id or model_id.startswith(("claude-1", "claude-2")):
        return "claude-sonnet-4-6"
    return None


def days_since(day_str, today):
    """Whole days from a YYYY-MM-DD string to `today`, or None if unreadable."""
    try:
        return (today - dt.date.fromisoformat(str(day_str))).days
    except (TypeError, ValueError):
        return None


def verdict(model_id, live_ids, today):
    """Classify one model string against the live list and the retirement table.

    Pure: both the live set and the date come in as arguments, so this is
    testable with no network and no clock. Returns (state, detail).

    The live list wins over the table. If the API still lists an id the table
    calls retired, the table is out of date, not the API, and saying so is more
    useful than reporting an outage that is not happening.
    """
    model_id = str(model_id or "").strip()
    if not model_id:
        return ("unreadable", "empty model string")

    retired_on = RETIRED.get(model_id)

    if model_id in live_ids:
        if retired_on:
            return ("table-stale",
                    "still in the live models list, though the local table says "
                    "it retired on %s. Trust the API and correct the table."
                    % (retired_on,))
        return ("live", "in the live models list for this workspace")

    if retired_on:
        ago = days_since(retired_on, today)
        when = ("%s, %d day(s) ago" % (retired_on, ago) if ago is not None
                else retired_on)
        moved_to = replacement(model_id)
        return ("retired",
                "retired on %s. Every request naming it returns 404 "
                "not_found_error, the same body a mistyped id returns.%s"
                % (when, " Line continues as %s." % moved_to if moved_to else ""))

    return ("unknown",
            "not in the live list and not on the deprecation table. That is a "
            "typo, an id that only exists on Bedrock or Vertex (which run later "
            "retirement schedules), or a model this workspace has not been "
            "granted. Three different repairs, so check before assuming.")


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Anthropic: check ANTHROPIC_API_KEY; an Admin "
                         "key cannot read the models list" % r.status_code)
    r.raise_for_status()
    return r.json()


def live_model_ids(session):
    """Every id callable by this workspace key, following the cursor."""
    ids, params = set(), {"limit": 1000}
    while True:
        page = get(session, "/models", **params)
        data = page.get("data", [])
        ids.update(str(m.get("id")) for m in data if m.get("id"))
        if not page.get("has_more") or not page.get("last_id"):
            break
        params["after_id"] = page["last_id"]
    return ids


def read_ids(args):
    """Model strings from the command line and, optionally, a file of them."""
    ids = list(args.model)
    if args.from_file:
        with open(args.from_file, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.split("#", 1)[0].strip()
                if line:
                    ids.append(line)
    seen, unique = set(), []
    for model_id in ids:
        if model_id not in seen:
            seen.add(model_id)
            unique.append(model_id)
    return unique


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", action="append", default=[],
                    help="a model string found in your code; repeatable")
    ap.add_argument("--from-file",
                    help="file of model strings, one per line, # for comments")
    args = ap.parse_args()

    wanted = read_ids(args)
    if not wanted:
        log.error("give at least one --model, or a --from-file list. Collect "
                  "them with: grep -rn 'claude-' .")
        return 2

    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        log.error("set ANTHROPIC_API_KEY (a workspace key; this script only "
                  "sends GET requests)")
        return 2

    session = requests.Session()
    session.headers.update({"x-api-key": key, "anthropic-version": VERSION})

    live = live_model_ids(session)
    today = dt.date.today()

    counts, bad = {}, 0
    for model_id in wanted:
        state, detail = verdict(model_id, live, today)
        counts[state] = counts.get(state, 0) + 1
        line = "%-12s %s  %s" % (state, model_id or "<empty>", detail)
        if state not in BAD:
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        if state == "retired":
            moved_to = replacement(model_id)
            log.warning("  repair: replace the string %r with %r everywhere it "
                        "appears, including default arguments, fallback "
                        "branches and batch request bodies",
                        model_id, moved_to or "the documented replacement")

    log.info("%d id(s) checked against %d live model(s), %d retired, %d unknown",
             len(wanted), len(live), counts.get("retired", 0),
             counts.get("unknown", 0))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "anthropic-model-ids-audit.mjs",
"js": '''/**
 * Find retired Claude model ids still named in your configuration.
 *
 * Read only. GET requests and nothing else: give this a workspace API key. The
 * repair is printed, never performed.
 */
import { readFileSync } from 'node:fs';

const API = 'https://api.anthropic.com/v1';
const VERSION = '2023-06-01';

// Copied from the published deprecations page, because the API has no
// retirement field at all. A hardcoded table goes stale, so the live list from
// the API always wins over this one; see verdict().
export const RETIRED = {
  'claude-opus-4-1-20250805': '2026-08-05',
  'claude-opus-4-20250514': '2026-06-15',
  'claude-sonnet-4-20250514': '2026-06-15',
  'claude-3-haiku-20240307': '2026-04-20',
  'claude-3-7-sonnet-20250219': '2026-02-19',
  'claude-3-5-haiku-20241022': '2026-02-19',
  'claude-3-opus-20240229': '2026-01-05',
  'claude-3-5-sonnet-20240620': '2025-10-28',
  'claude-3-5-sonnet-20241022': '2025-10-28',
  'claude-3-sonnet-20240229': '2025-07-21',
  'claude-2.0': '2025-07-21',
  'claude-2.1': '2025-07-21',
  'claude-1.0': '2024-11-06',
  'claude-1.1': '2024-11-06',
  'claude-1.2': '2024-11-06',
  'claude-1.3': '2024-11-06',
  'claude-instant-1.0': '2024-11-06',
  'claude-instant-1.1': '2024-11-06',
  'claude-instant-1.2': '2024-11-06',
};

const BAD = ['retired', 'unknown', 'table-stale', 'unreadable'];
const DAY = 86400000;

/**
 * Where a retired line rolls forward to, by family. Family level on purpose:
 * this says the Opus line continues as Opus, not that any two snapshots behave
 * the same.
 */
export function replacement(modelId) {
  if (modelId.includes('opus')) return 'claude-opus-4-8';
  if (modelId.includes('haiku') || modelId.includes('instant')) {
    return 'claude-haiku-4-5-20251001';
  }
  if (modelId.includes('sonnet') || /^claude-[12]/.test(modelId)) {
    return 'claude-sonnet-4-6';
  }
  return null;
}

/** Whole days from a YYYY-MM-DD string to `today`, or null if unreadable. */
export function daysSince(dayStr, today) {
  if (!/^\\d{4}-\\d{2}-\\d{2}$/.test(String(dayStr))) return null;
  const ms = Date.parse(`${dayStr}T00:00:00Z`);
  if (Number.isNaN(ms)) return null;
  return Math.round((today.getTime() - ms) / DAY);
}

/**
 * Classify one model string against the live list and the retirement table.
 * Pure: both the live set and the date come in as arguments. Returns
 * [state, detail].
 *
 * The live list wins over the table. If the API still lists an id the table
 * calls retired, the table is out of date, not the API.
 */
export function verdict(modelId, liveIds, today) {
  const id = String(modelId ?? '').trim();
  if (!id) return ['unreadable', 'empty model string'];

  const retiredOn = RETIRED[id];

  if (liveIds.has(id)) {
    if (retiredOn) {
      return ['table-stale',
        `still in the live models list, though the local table says it retired ` +
        `on ${retiredOn}. Trust the API and correct the table.`];
    }
    return ['live', 'in the live models list for this workspace'];
  }

  if (retiredOn) {
    const ago = daysSince(retiredOn, today);
    const when = ago === null ? retiredOn : `${retiredOn}, ${ago} day(s) ago`;
    const movedTo = replacement(id);
    return ['retired',
      `retired on ${when}. Every request naming it returns 404 not_found_error, ` +
      `the same body a mistyped id returns.` +
      (movedTo ? ` Line continues as ${movedTo}.` : '')];
  }

  return ['unknown',
    'not in the live list and not on the deprecation table. That is a typo, an ' +
    'id that only exists on Bedrock or Vertex (which run later retirement ' +
    'schedules), or a model this workspace has not been granted. Three ' +
    'different repairs, so check before assuming.'];
}

async function get(key, path, params = {}) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v);
  const res = await fetch(url, {
    headers: { 'x-api-key': key, 'anthropic-version': VERSION },
  });
  if (res.status === 401 || res.status === 403) {
    throw new Error(`${res.status} from Anthropic: check ANTHROPIC_API_KEY; an ` +
                    'Admin key cannot read the models list');
  }
  if (!res.ok) throw new Error(`${res.status} from ${path}`);
  return res.json();
}

export async function liveModelIds(key) {
  const ids = new Set();
  const params = { limit: 1000 };
  for (;;) {
    const page = await get(key, '/models', params);
    for (const m of page.data ?? []) if (m.id) ids.add(String(m.id));
    if (!page.has_more || !page.last_id) break;
    params.after_id = page.last_id;
  }
  return ids;
}

function readIds(argv) {
  const ids = [];
  argv.forEach((arg, i) => {
    if (arg === '--model' && argv[i + 1]) ids.push(argv[i + 1]);
    if (arg === '--from-file' && argv[i + 1]) {
      for (const line of readFileSync(argv[i + 1], 'utf8').split('\\n')) {
        const trimmed = line.split('#')[0].trim();
        if (trimmed) ids.push(trimmed);
      }
    }
  });
  return [...new Set(ids)];
}

async function main() {
  const wanted = readIds(process.argv);
  if (wanted.length === 0) {
    console.error("give at least one --model, or a --from-file list. Collect " +
                  "them with: grep -rn 'claude-' .");
    process.exitCode = 2;
    return;
  }

  const key = process.env.ANTHROPIC_API_KEY;
  if (!key) {
    console.error('set ANTHROPIC_API_KEY (a workspace key; this script only ' +
                  'sends GET requests)');
    process.exitCode = 2;
    return;
  }

  const live = await liveModelIds(key);
  const today = new Date(`${new Date().toISOString().slice(0, 10)}T00:00:00Z`);

  const counts = new Map();
  let bad = 0;
  for (const modelId of wanted) {
    const [state, detail] = verdict(modelId, live, today);
    counts.set(state, (counts.get(state) ?? 0) + 1);
    const line = `${state.padEnd(12)} ${modelId || '<empty>'}  ${detail}`;
    if (!BAD.includes(state)) { console.log(line); continue; }
    bad += 1;
    console.warn(line);
    if (state === 'retired') {
      const movedTo = replacement(modelId) ?? 'the documented replacement';
      console.warn(`  repair: replace the string "${modelId}" with "${movedTo}" ` +
        'everywhere it appears, including default arguments, fallback branches ' +
        'and batch request bodies');
    }
  }

  console.log(`${wanted.length} id(s) checked against ${live.size} live ` +
    `model(s), ${counts.get('retired') ?? 0} retired, ` +
    `${counts.get('unknown') ?? 0} unknown`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The live set and the date are both handed in, so every case runs offline. The two worth pinning are the ones that keep the script honest about what it does not know: an id missing from the live list but absent from the deprecation table is <code>unknown</code> rather than retired, and an id the table calls retired while the API still lists it means the table is stale &mdash; not that a working model should be reported as an outage.",
"test_py_file": "test_anthropic_model_ids_audit.py",
"test_py": '''import datetime as dt

from anthropic_model_ids_audit import days_since, replacement, verdict

TODAY = dt.date(2026, 8, 30)
LIVE = {"claude-opus-4-8", "claude-sonnet-4-6", "claude-haiku-4-5-20251001",
        "claude-opus-4-1-20250805"}


def test_an_id_in_the_live_list_is_callable():
    state, detail = verdict("claude-sonnet-4-6", LIVE, TODAY)
    assert state == "live"
    assert "live models list" in detail


def test_an_id_missing_from_the_list_and_on_the_table_is_retired():
    state, detail = verdict("claude-3-5-sonnet-20241022", LIVE - {"x"}, TODAY)
    assert state == "retired"
    assert "2025-10-28" in detail
    assert "not_found_error" in detail
    assert "claude-sonnet-4-6" in detail


def test_the_days_since_retirement_are_counted_from_the_date_passed_in():
    assert days_since("2026-06-15", TODAY) == 76
    assert days_since("not a date", TODAY) is None
    assert "76 day(s) ago" in verdict("claude-opus-4-20250514", set(), TODAY)[1]


def test_missing_from_the_list_but_not_on_the_table_is_unknown():
    state, detail = verdict("claude-sonnet-4-6-20260101", set(), TODAY)
    assert state == "unknown"
    assert "Bedrock" in detail


def test_the_api_wins_over_the_hardcoded_table():
    # The table is a copy of a web page and this one has gone stale. Reporting
    # an outage on a model the API is still serving would be worse than useless.
    state, detail = verdict("claude-opus-4-1-20250805", LIVE, TODAY)
    assert state == "table-stale"
    assert "Trust the API" in detail


def test_an_empty_string_is_not_silently_live():
    assert verdict("", LIVE, TODAY)[0] == "unreadable"
    assert verdict(None, LIVE, TODAY)[0] == "unreadable"


def test_the_replacement_is_family_level_and_admits_ignorance():
    assert replacement("claude-3-opus-20240229") == "claude-opus-4-8"
    assert replacement("claude-3-5-haiku-20241022") == "claude-haiku-4-5-20251001"
    assert replacement("claude-instant-1.2") == "claude-haiku-4-5-20251001"
    assert replacement("claude-2.1") == "claude-sonnet-4-6"
    assert replacement("some-other-vendor-model") is None
''',
"test_js_file": "anthropic-model-ids-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { daysSince, replacement, verdict } from './anthropic-model-ids-audit.mjs';

const TODAY = new Date('2026-08-30T00:00:00Z');
const LIVE = new Set(['claude-opus-4-8', 'claude-sonnet-4-6',
                      'claude-haiku-4-5-20251001', 'claude-opus-4-1-20250805']);

test('an id in the live list is callable', () => {
  const [state, detail] = verdict('claude-sonnet-4-6', LIVE, TODAY);
  assert.equal(state, 'live');
  assert.match(detail, /live models list/);
});

test('an id missing from the list and on the table is retired', () => {
  const [state, detail] = verdict('claude-3-5-sonnet-20241022', new Set(), TODAY);
  assert.equal(state, 'retired');
  assert.match(detail, /2025-10-28/);
  assert.match(detail, /not_found_error/);
  assert.match(detail, /claude-sonnet-4-6/);
});

test('the days since retirement are counted from the date passed in', () => {
  assert.equal(daysSince('2026-06-15', TODAY), 76);
  assert.equal(daysSince('not a date', TODAY), null);
  assert.match(verdict('claude-opus-4-20250514', new Set(), TODAY)[1],
               /76 day\\(s\\) ago/);
});

test('missing from the list but not on the table is unknown', () => {
  const [state, detail] = verdict('claude-sonnet-4-6-20260101', new Set(), TODAY);
  assert.equal(state, 'unknown');
  assert.match(detail, /Bedrock/);
});

test('the api wins over the hardcoded table', () => {
  const [state, detail] = verdict('claude-opus-4-1-20250805', LIVE, TODAY);
  assert.equal(state, 'table-stale');
  assert.match(detail, /Trust the API/);
});

test('an empty string is not silently live', () => {
  assert.equal(verdict('', LIVE, TODAY)[0], 'unreadable');
  assert.equal(verdict(null, LIVE, TODAY)[0], 'unreadable');
});

test('the replacement is family level and admits ignorance', () => {
  assert.equal(replacement('claude-3-opus-20240229'), 'claude-opus-4-8');
  assert.equal(replacement('claude-3-5-haiku-20241022'), 'claude-haiku-4-5-20251001');
  assert.equal(replacement('claude-instant-1.2'), 'claude-haiku-4-5-20251001');
  assert.equal(replacement('claude-2.1'), 'claude-sonnet-4-6');
  assert.equal(replacement('some-other-vendor-model'), null);
});
''',
"faq": [
 ("Why does the 404 not say the model was retired?",
  "Because not_found_error means the resource is not addressable, and the API no longer holds anything at that id to describe. A retired model, a mistyped model and a model your workspace was never granted all produce the same body. The models list is what distinguishes them, and only while you still know which strings your code uses."),
 ("Can I get the retirement date out of the API?",
  "No. The Claude model object returns id, display_name, created_at and the token limits. There is no retirement field before the date and no tombstone after it, so the date comes from the published deprecations page. The API tells you callable or not, which is the whole of its contribution here."),
 ("The usage report shows the id, so is it still working?",
  "Check when it last appeared. A retired id stops accruing usage on its retirement date because the calls fail, and it never comes back. Traffic that stops dead on a published date is the fingerprint of this problem, not evidence against it."),
 ("A teammate says the id still works for them. Who is right?",
  "Possibly both of you. Amazon Bedrock and Google Cloud set their own retirement dates, generally later than the first-party API, so a model can be dead on api.anthropic.com and alive on Bedrock. The script reports an id it cannot place as unknown rather than retired for exactly this reason."),
 ("Is running this in CI safe with a key that can send messages?",
  "A workspace key is all-or-nothing on the data plane: the same credential that reads GET /v1/models could send a message. This script only ever issues GET requests, which is a property you can verify by reading it, but the safer control is to give CI a key scoped to a workspace with no budget rather than one that fronts production."),
],
"related": [REL_PAST, REL_SOON, REL_ALIAS],
"citations": [CITE_AN_DEPRECATIONS, CITE_AN_MODELS, CITE_AN_ERRORS],
},

{
"slug": "floating-alias-instead-of-pinned-snapshot",
"title": "A floating model alias silently changes model under you",
"description": "An alias is not retiring, it moves. GET /v1/models/{alias} returns the snapshot it resolves to today, which is the id that should have been in the config.",
"h1": "a floating model alias silently changes model under you",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["claude model alias", "pin model snapshot", "resolve model alias",
             "claude-sonnet-4-5 alias snapshot", "anthropic model id date suffix"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Reads ANTHROPIC_API_KEY, a workspace key, and sends only GET requests.",
"lead": "No error, no deploy, no incident. The evals were 91% on Thursday and 87% on Monday, the mean output length moved, the prompt cache hit rate dropped a few points and the bill went up slightly. Everyone looks at the prompt, which did not change, and at the retrieval corpus, which did not change either. The model changed: the config names an alias, and an alias is a pointer, not a model.",
"short_answer": """<p><code>GET /v1/models/{id}</code> for every model string in your config and compare the <code>id</code> that comes back with the one you sent. If they differ, the string is an alias and the returned value is the snapshot it resolves to <em>today</em> &mdash; pin that instead.</p>
<p>Two things this check is not. It is not a retirement check: nothing here has an end date, and an alias that moves is <a href="/llm/retired-model-id-still-in-code/">the opposite failure</a> to an id that disappears. And from the 4.6 generation onward the dateless id <em>is</em> the snapshot, so appending a date to it is a 404 rather than a tightening.</p>""",
"problem": """<p>Alias drift is the only failure in this group that produces no error at any point. There is no status code, no missing field, no log line. The application keeps working; it just starts doing slightly different work, and every measurement that would show it &mdash; eval scores, output length, cache hit rate, cost per request &mdash; moves by an amount small enough to be attributed to noise.</p>
<p>What makes it expensive is where the investigation goes. Nothing in your repository changed, so the search starts in the places that did: data, traffic mix, a dependency bump, a customer's new usage pattern. Days go into that before anybody asks the one question that resolves it, which is what the model string actually resolves to. And because the answer is a moving target, reproducing the old behaviour later requires knowing which snapshot you <em>were</em> on, which nobody recorded.</p>""",
"why": """<p><strong>An alias is a convenience, and its convenience is the problem.</strong> For models released before the 4.6 generation the undated string is a pointer: <code>claude-sonnet-4-5</code> resolves to <code>claude-sonnet-4-5-20250929</code>, <code>claude-haiku-4-5</code> to <code>claude-haiku-4-5-20251001</code>, <code>claude-opus-4-5</code> to <code>claude-opus-4-5-20251101</code>. The string is stable; what serves it is not.</p>
<p><strong>The naming convention changed, so the rule you learned is now half wrong.</strong> From 4.6 on, the dateless id is itself the pinned snapshot. So <code>claude-opus-4-6</code>, <code>claude-sonnet-4-6</code>, <code>claude-opus-4-8</code> and their siblings need no date, and adding one produces a 404 for an id that never existed. "Always pin by appending the date" is now a way to break production, which is why this check reads the resolution rather than pattern-matching the string.</p>
<p><strong>The resolution is only knowable by asking.</strong> The Models API resolves an alias to a model id, and the returned <code>id</code> is the one that will appear in <code>response.model</code> and in the Admin usage report. Nothing warns you when the pointer moves; the only way to notice is to have recorded what it pointed at before.</p>
<p><strong>Pinning is not the end of the work.</strong> A pinned snapshot has a retirement date, which is what the <a href="/llm/model-retiring-within-90-days/">other half of this cluster</a> is about. Pinning trades an invisible failure for a scheduled one, which is a good trade only if something is reading the schedule.</p>""",
"steps": [
 {"h": "List the model strings your code actually sends",
  "body": """<p>Same collection as any model audit: configs, environment variables, default arguments, fallback branches, batch bodies. An alias in a rarely-exercised path drifts just as much, and is even harder to attribute afterwards.</p>"""},
 {"h": "Ask the API what each one resolves to",
  "body": """<p><code>GET https://api.anthropic.com/v1/models/{id}</code> with <code>x-api-key</code> and <code>anthropic-version: 2023-06-01</code>. Compare the returned <code>id</code> with the string you sent. Different means alias; identical means the string is already a snapshot.</p>"""},
 {"h": "Read the identical case correctly",
  "body": """<p>A string that resolves to itself and carries no date suffix is a 4.6-or-later id, which is a pinned snapshot in its own right. Do not "fix" it by appending a date. That is a distinct outcome in the report for a reason: the obvious remediation is the one that breaks it.</p>"""},
 {"h": "Record the resolution, not just the finding",
  "body": """<p>Store today's mapping from alias to snapshot alongside your eval results. Without it, a future regression cannot be attributed to a model change, and the previous snapshot cannot be re-pinned to confirm the theory.</p>"""},
 {"h": "Pin, then put the new id on the retirement check",
  "body": """<p>Write the resolved snapshot into the config. Then run the retirement check against it, because a pinned id is one with a date attached, and the whole point of pinning is to know when the change is coming rather than to avoid it forever.</p>"""},
],
"verify": """<p>Re-run after pinning. Every string should resolve to itself, and the only remaining states should be pinned ones.</p>
<pre><code class="language-bash">python3 anthropic_alias_pinning_audit.py --model claude-sonnet-4-6 --model claude-haiku-4-5-20251001
# 2 id(s) checked, 0 unpinned alias(es)</code></pre>""",
"code_intro": "One GET per model string, with a workspace key, and no writes. The classifier compares what you asked for with what came back and takes the current date only to say how old the resolved snapshot is &mdash; a snapshot created last week behind an alias you have been calling for a year is the drift, stated as plainly as this check can state it.",
"py_file": "anthropic_alias_pinning_audit.py",
"py": '''"""Report Claude model strings that are aliases rather than pinned snapshots.

Read only. One GET per model string and nothing else: give this a workspace API
key. The repair is printed, never performed, because this script holds a
credential that can spend real money on inference.
"""
import argparse
import datetime as dt
import logging
import os
import re
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("anthropic_alias_pinning_audit")

API = "https://api.anthropic.com/v1"
VERSION = "2023-06-01"

# A trailing -YYYYMMDD. Used only to describe an id, never to decide whether it
# is pinned: that answer comes from the API, because from the 4.6 generation on
# a dateless id is itself a snapshot and pattern-matching gets it backwards.
DATED = re.compile(r"-\\d{8}$")

BAD = ("alias", "not-found", "unreadable")


def parse_created(value):
    """Read created_at into a date, or None.

    The field is RFC 3339 with a trailing Z, which date.fromisoformat will not
    accept before Python 3.11, so the timestamp is cut at the T rather than
    parsed whole.
    """
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        return dt.date.fromisoformat(raw.split("T")[0])
    except ValueError:
        return None


def verdict(requested, model, today):
    """Compare a model string with what GET /v1/models/{id} resolved it to.

    `model` is the returned object, or None for a 404. Pure, and `today` is
    passed in so the age of the resolved snapshot is testable at a fixed date.
    Returns (state, detail).
    """
    requested = str(requested or "").strip()
    if not requested:
        return ("unreadable", "empty model string")

    if model is None:
        return ("not-found",
                "404 not_found_error: nothing resolves this id. If a date "
                "suffix was appended to a 4.6-or-later id, remove it: those "
                "ids are already snapshots and the dated form never existed.")

    resolved = str(model.get("id") or "").strip()
    if not resolved:
        return ("unreadable", "the model object came back with no id")

    created = parse_created(model.get("created_at"))
    age = ("" if created is None else
           " The snapshot behind it was created %s, %d day(s) ago."
           % (created.isoformat(), (today - created).days))

    if resolved != requested:
        return ("alias",
                "an alias: it resolves to %s today, and the pointer moves "
                "without a deploy or an error.%s Pin %s."
                % (resolved, age, resolved))

    if DATED.search(requested):
        return ("pinned", "a dated snapshot; it resolves to itself.%s" % (age,))

    return ("pinned-dateless",
            "already a pinned snapshot even though it carries no date: from the "
            "4.6 generation on, the dateless id is the snapshot. Do not append "
            "a date to it, that id does not exist.%s" % (age,))


def get_model(session, model_id):
    """The model object for one id, or None when the API returns 404."""
    r = session.get("%s/models/%s" % (API, model_id), timeout=30)
    if r.status_code == 404:
        return None
    if r.status_code in (401, 403):
        raise SystemExit("%d from Anthropic: check ANTHROPIC_API_KEY; an Admin "
                         "key cannot read the models list" % r.status_code)
    r.raise_for_status()
    return r.json()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", action="append", default=[],
                    help="a model string found in your code; repeatable")
    ap.add_argument("--from-file",
                    help="file of model strings, one per line, # for comments")
    args = ap.parse_args()

    wanted = list(args.model)
    if args.from_file:
        with open(args.from_file, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.split("#", 1)[0].strip()
                if line:
                    wanted.append(line)
    wanted = list(dict.fromkeys(wanted))
    if not wanted:
        log.error("give at least one --model, or a --from-file list")
        return 2

    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        log.error("set ANTHROPIC_API_KEY (a workspace key; this script only "
                  "sends GET requests)")
        return 2

    session = requests.Session()
    session.headers.update({"x-api-key": key, "anthropic-version": VERSION})

    today = dt.date.today()
    unpinned = 0
    for model_id in wanted:
        state, detail = verdict(model_id, get_model(session, model_id), today)
        line = "%-15s %s  %s" % (state, model_id, detail)
        if state not in BAD:
            log.info(line)
            continue
        if state == "alias":
            unpinned += 1
        log.warning(line)
        if state == "alias":
            log.warning("  repair: write the resolved snapshot into the config "
                        "in place of the alias, record today's mapping beside "
                        "your eval results, then check the new id's retirement "
                        "date")

    log.info("%d id(s) checked, %d unpinned alias(es)", len(wanted), unpinned)
    return 1 if unpinned else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "anthropic-alias-pinning-audit.mjs",
"js": '''/**
 * Report Claude model strings that are aliases rather than pinned snapshots.
 *
 * Read only. One GET per model string and nothing else: give this a workspace
 * API key. The repair is printed, never performed.
 */
import { readFileSync } from 'node:fs';

const API = 'https://api.anthropic.com/v1';
const VERSION = '2023-06-01';
const DAY = 86400000;

// A trailing -YYYYMMDD. Used only to describe an id, never to decide whether it
// is pinned: that answer comes from the API, because from the 4.6 generation on
// a dateless id is itself a snapshot and pattern-matching gets it backwards.
const DATED = /-\\d{8}$/;

const BAD = ['alias', 'not-found', 'unreadable'];

/**
 * Read created_at into a UTC date, or null. The field is RFC 3339, and only the
 * date part is used.
 */
export function parseCreated(value) {
  const raw = String(value ?? '').trim().split('T')[0];
  if (!/^\\d{4}-\\d{2}-\\d{2}$/.test(raw)) return null;
  const ms = Date.parse(`${raw}T00:00:00Z`);
  return Number.isNaN(ms) ? null : new Date(ms);
}

/**
 * Compare a model string with what GET /v1/models/{id} resolved it to. `model`
 * is the returned object, or null for a 404. Pure, and `today` is passed in so
 * the age of the resolved snapshot is testable at a fixed date. Returns
 * [state, detail].
 */
export function verdict(requested, model, today) {
  const asked = String(requested ?? '').trim();
  if (!asked) return ['unreadable', 'empty model string'];

  if (model === null || model === undefined) {
    return ['not-found',
      '404 not_found_error: nothing resolves this id. If a date suffix was ' +
      'appended to a 4.6-or-later id, remove it: those ids are already ' +
      'snapshots and the dated form never existed.'];
  }

  const resolved = String(model.id ?? '').trim();
  if (!resolved) return ['unreadable', 'the model object came back with no id'];

  const created = parseCreated(model.created_at);
  const age = created === null ? ''
    : ` The snapshot behind it was created ${created.toISOString().slice(0, 10)}, ` +
      `${Math.round((today.getTime() - created.getTime()) / DAY)} day(s) ago.`;

  if (resolved !== asked) {
    return ['alias',
      `an alias: it resolves to ${resolved} today, and the pointer moves ` +
      `without a deploy or an error.${age} Pin ${resolved}.`];
  }

  if (DATED.test(asked)) {
    return ['pinned', `a dated snapshot; it resolves to itself.${age}`];
  }

  return ['pinned-dateless',
    'already a pinned snapshot even though it carries no date: from the 4.6 ' +
    'generation on, the dateless id is the snapshot. Do not append a date to ' +
    `it, that id does not exist.${age}`];
}

/** The model object for one id, or null when the API returns 404. */
export async function getModel(key, modelId) {
  const res = await fetch(`${API}/models/${modelId}`, {
    headers: { 'x-api-key': key, 'anthropic-version': VERSION },
  });
  if (res.status === 404) return null;
  if (res.status === 401 || res.status === 403) {
    throw new Error(`${res.status} from Anthropic: check ANTHROPIC_API_KEY; an ` +
                    'Admin key cannot read the models list');
  }
  if (!res.ok) throw new Error(`${res.status} from /models/${modelId}`);
  return res.json();
}

function readIds(argv) {
  const ids = [];
  argv.forEach((arg, i) => {
    if (arg === '--model' && argv[i + 1]) ids.push(argv[i + 1]);
    if (arg === '--from-file' && argv[i + 1]) {
      for (const line of readFileSync(argv[i + 1], 'utf8').split('\\n')) {
        const trimmed = line.split('#')[0].trim();
        if (trimmed) ids.push(trimmed);
      }
    }
  });
  return [...new Set(ids)];
}

async function main() {
  const wanted = readIds(process.argv);
  if (wanted.length === 0) {
    console.error('give at least one --model, or a --from-file list');
    process.exitCode = 2;
    return;
  }

  const key = process.env.ANTHROPIC_API_KEY;
  if (!key) {
    console.error('set ANTHROPIC_API_KEY (a workspace key; this script only ' +
                  'sends GET requests)');
    process.exitCode = 2;
    return;
  }

  const today = new Date(`${new Date().toISOString().slice(0, 10)}T00:00:00Z`);
  let unpinned = 0;
  for (const modelId of wanted) {
    const [state, detail] = verdict(modelId, await getModel(key, modelId), today);
    const line = `${state.padEnd(15)} ${modelId}  ${detail}`;
    if (!BAD.includes(state)) { console.log(line); continue; }
    if (state === 'alias') unpinned += 1;
    console.warn(line);
    if (state === 'alias') {
      console.warn('  repair: write the resolved snapshot into the config in ' +
        "place of the alias, record today's mapping beside your eval results, " +
        "then check the new id's retirement date");
    }
  }

  console.log(`${wanted.length} id(s) checked, ${unpinned} unpinned alias(es)`);
  process.exitCode = unpinned ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The resolution is handed to the classifier, so every case runs offline. The test that matters most is the dateless one: a 4.6-or-later id resolves to itself and is already pinned, and a script that decides pinning by looking for a date suffix would tell you to append one and hand you a 404 in exchange for a working config.",
"test_py_file": "test_anthropic_alias_pinning_audit.py",
"test_py": '''import datetime as dt

from anthropic_alias_pinning_audit import parse_created, verdict

TODAY = dt.date(2026, 8, 30)


def model(model_id, created="2025-09-29T00:00:00Z"):
    return {"id": model_id, "created_at": created, "type": "model"}


def test_a_string_that_resolves_to_something_else_is_an_alias():
    state, detail = verdict("claude-sonnet-4-5",
                            model("claude-sonnet-4-5-20250929"), TODAY)
    assert state == "alias"
    assert "resolves to claude-sonnet-4-5-20250929" in detail
    assert "Pin claude-sonnet-4-5-20250929" in detail


def test_a_dated_id_that_resolves_to_itself_is_pinned():
    state, detail = verdict("claude-haiku-4-5-20251001",
                            model("claude-haiku-4-5-20251001"), TODAY)
    assert state == "pinned"
    assert "resolves to itself" in detail


def test_a_dateless_id_that_resolves_to_itself_is_also_pinned():
    # The trap: appending a date to a 4.6-or-later id gives a 404, so the check
    # has to read the resolution rather than look for a date suffix.
    state, detail = verdict("claude-opus-4-8", model("claude-opus-4-8"), TODAY)
    assert state == "pinned-dateless"
    assert "Do not append a date" in detail


def test_a_404_says_what_probably_caused_it():
    state, detail = verdict("claude-opus-4-8-20260601", None, TODAY)
    assert state == "not-found"
    assert "remove it" in detail


def test_the_age_of_the_resolved_snapshot_is_measured_from_the_date_passed_in():
    assert parse_created("2025-09-29T00:00:00Z") == dt.date(2025, 9, 29)
    assert parse_created("") is None
    assert parse_created("last autumn") is None
    detail = verdict("claude-sonnet-4-5", model("claude-sonnet-4-5-20250929"),
                     TODAY)[1]
    assert "335 day(s) ago" in detail


def test_a_missing_created_at_drops_the_age_rather_than_inventing_one():
    state, detail = verdict("claude-sonnet-4-5",
                            {"id": "claude-sonnet-4-5-20250929"}, TODAY)
    assert state == "alias"
    assert "day(s) ago" not in detail


def test_an_empty_string_or_a_headless_object_is_unreadable():
    assert verdict("", model("x"), TODAY)[0] == "unreadable"
    assert verdict("claude-opus-4-8", {"created_at": "x"}, TODAY)[0] == "unreadable"
''',
"test_js_file": "anthropic-alias-pinning-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { parseCreated, verdict } from './anthropic-alias-pinning-audit.mjs';

const TODAY = new Date('2026-08-30T00:00:00Z');
const model = (id, created = '2025-09-29T00:00:00Z') =>
  ({ id, created_at: created, type: 'model' });

test('a string that resolves to something else is an alias', () => {
  const [state, detail] = verdict('claude-sonnet-4-5',
                                  model('claude-sonnet-4-5-20250929'), TODAY);
  assert.equal(state, 'alias');
  assert.match(detail, /resolves to claude-sonnet-4-5-20250929/);
  assert.match(detail, /Pin claude-sonnet-4-5-20250929/);
});

test('a dated id that resolves to itself is pinned', () => {
  const [state, detail] = verdict('claude-haiku-4-5-20251001',
                                  model('claude-haiku-4-5-20251001'), TODAY);
  assert.equal(state, 'pinned');
  assert.match(detail, /resolves to itself/);
});

test('a dateless id that resolves to itself is also pinned', () => {
  const [state, detail] = verdict('claude-opus-4-8', model('claude-opus-4-8'), TODAY);
  assert.equal(state, 'pinned-dateless');
  assert.match(detail, /Do not append a date/);
});

test('a 404 says what probably caused it', () => {
  const [state, detail] = verdict('claude-opus-4-8-20260601', null, TODAY);
  assert.equal(state, 'not-found');
  assert.match(detail, /remove it/);
});

test('the age of the resolved snapshot is measured from the date passed in', () => {
  assert.equal(parseCreated('2025-09-29T00:00:00Z').toISOString().slice(0, 10),
               '2025-09-29');
  assert.equal(parseCreated(''), null);
  assert.equal(parseCreated('last autumn'), null);
  const [, detail] = verdict('claude-sonnet-4-5',
                             model('claude-sonnet-4-5-20250929'), TODAY);
  assert.match(detail, /335 day\\(s\\) ago/);
});

test('a missing created_at drops the age rather than inventing one', () => {
  const [state, detail] = verdict('claude-sonnet-4-5',
                                  { id: 'claude-sonnet-4-5-20250929' }, TODAY);
  assert.equal(state, 'alias');
  assert.ok(!/day\\(s\\) ago/.test(detail));
});

test('an empty string or a headless object is unreadable', () => {
  assert.equal(verdict('', model('x'), TODAY)[0], 'unreadable');
  assert.equal(verdict('claude-opus-4-8', { created_at: 'x' }, TODAY)[0],
               'unreadable');
});
''',
"faq": [
 ("How do I know whether a model string is an alias?",
  "Ask. GET /v1/models/{id} returns the model it resolves to, and if that id differs from the string you sent, the string is an alias. Guessing from the shape of the name does not work any more: before the 4.6 generation a dateless id was an alias, and from 4.6 on it is the snapshot itself."),
 ("Should I append a date to claude-opus-4-6 to pin it?",
  "No. That id is already a pinned snapshot, and the dated form does not exist, so appending a date returns a 404. This is the most common way the pinning advice gets misapplied, which is why the script gives the dateless-but-pinned case a state of its own instead of quietly calling it fine."),
 ("What does an alias moving actually look like in production?",
  "Nothing, at first. There is no error and no deploy. Output length and token counts shift, prompt cache hit rates drop as the cached prefix stops matching, eval scores move a few points, and cost per request changes slightly. Every one of those is individually dismissible as noise, which is why it is usually found weeks later."),
 ("If I pin, do I stop having to think about model changes?",
  "You change which problem you have. A pinned snapshot cannot drift, but it does have a retirement date, so it will eventually stop working on a day somebody can look up in advance. That is the trade: an invisible failure exchanged for a scheduled one, and it is only a good trade if the schedule is being read."),
 ("Which credential does this need?",
  "A workspace API key, because the Models API lives on the data plane and an Admin key cannot reach it. The script issues GET requests only, and the Admin API is the wrong tool here even though it is the read-only one, which is the sort of inversion worth knowing before you go looking for a safer key."),
],
"related": [REL_PAST, REL_SOON, REL_GONE],
"citations": [CITE_AN_MODELS, CITE_AN_OVERVIEW, CITE_AN_DEPRECATIONS],
},

]
