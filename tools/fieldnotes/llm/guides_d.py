#!/usr/bin/env python3
"""/llm/ field notes, batch D — the writing.

The Batch API four times, and the four are four problems rather than four
readings of one.

`batch-partial-failure-unnoticed` is a word: the batch says `completed`, which
is a statement about the run and not about the requests inside it, and rows
failed underneath it. `batch-error-file-never-read` is a file: the failures were
written down, to a second file id that the ingest code never opens. Those two
are adjacent and must not be collapsed — the first is arithmetic on
`request_counts` that needs no other call, the second is a file that exists,
holds bytes, and expires after thirty days whether or not anyone read it.
`batch-expired-past-24h-window` is a clock: the fixed 24 hour completion window
closed on work that had not drained, and the rows are gone rather than late.

`batch-discount-left-unused` is not a failure at all. Nothing is broken, nothing
errored, and no row is missing. It is a cost note: latency-insensitive work is
going through the synchronous endpoint at roughly twice the price the same work
would cost asynchronously, and the only evidence is the shape of the traffic in
aggregate.

Read-only throughout: a project key set to Read Only for the three batch-object
notes, an organization admin key provisioned read-only for the cost one, GET
requests only, and every repair printed for a human to run. Re-submitting rows
spends money on inference, so none of these scripts does it.
"""

CITE_BATCH_REF = ("Batch — OpenAI API reference",
                  "https://developers.openai.com/api/docs/api-reference/batch")
CITE_BATCH_GUIDE = ("Batch API guide — OpenAI developer docs",
                    "https://developers.openai.com/api/docs/guides/batch")
CITE_FILES_REF = ("Files — OpenAI API reference",
                  "https://developers.openai.com/api/docs/api-reference/files")
CITE_USAGE_COMPLETIONS = ("Usage: completions — OpenAI API reference",
                          "https://platform.openai.com/docs/api-reference/usage/completions")
CITE_COSTS = ("Costs — OpenAI API reference",
              "https://platform.openai.com/docs/api-reference/usage/costs")
CITE_AN_BATCH = ("Batch processing — Claude Docs",
                 "https://platform.claude.com/docs/en/build-with-claude/batch-processing")

REL_PARTIAL = ("/llm/batch-partial-failure-unnoticed/",
               "A batch that reads completed with failed rows inside it")
REL_ERRFILE = ("/llm/batch-error-file-never-read/",
               "An error file that exists and was never fetched")
REL_EXPIRED = ("/llm/batch-expired-past-24h-window/",
               "A batch the 24 hour window closed on")
REL_DISCOUNT = ("/llm/batch-discount-left-unused/",
                "Batch-eligible work paying synchronous prices")
REL_OUTPUT_COST = ("/llm/output-tokens-dominate-cost/",
                   "Output tokens, not input, are what the bill is made of")

GUIDES = [

{
"slug": "batch-partial-failure-unnoticed",
"title": "A batch reads completed while some of its rows failed",
"description": "GET /v1/batches returns completed while request_counts.failed is non-zero. Completed means the run finished, not that every request inside it succeeded.",
"h1": "a batch reads completed while some of its rows failed",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["openai batch request_counts failed", "openai batch partial failure",
             "batch completed but rows missing", "openai batch output file short",
             "openai batch reconciliation"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Reads OPENAI_API_KEY, a project key set to Read Only.",
"lead": "The nightly job submits fifty thousand rows, sleeps, polls until the status turns to <code>completed</code>, downloads the output file and loads it. It has done that every night for eight months. The table it fills is short &mdash; not empty, not obviously wrong, just a few hundred rows smaller than the input file, by a number that changes every night. No exception was ever raised. The batch object says <code>completed</code> in plain text, and three fields further down it says <code>\"failed\": 869</code>, which nothing has ever read.",
"short_answer": """<p><code>GET /v1/batches?limit=100</code> with a project key set to Read Only, paginating on <code>after</code>. For every object, stop reading <code>status</code> and start reading the arithmetic in <code>request_counts</code>: a batch is clean only when <code>failed == 0</code> <em>and</em> <code>completed == total</code>.</p>
<p><code>completed</code> is a statement about the batch, not about the requests in it. It means the run finished. Individual rows inside a finished run can fail on rate limits, context-length overflow, content filtering or a transient server error, and the batch still lands in <code>completed</code> with no HTTP error anywhere.</p>
<p>Two disagreements are possible and they are not the same thing. <code>failed &gt; 0</code> is rows that ran and failed. <code>completed + failed &lt; total</code> is rows that are neither, which is a hole in the accounting rather than a failure, and it wants a different question asked of it.</p>""",
"problem": """<p>The output file has one line per successful row, keyed by <code>custom_id</code>, and it is shorter than the input file. That is the entire visible symptom. Code that zips the output back onto the input by position rather than by <code>custom_id</code> does something worse than lose rows: it misaligns every row after the first failure, so eight hundred failures at the front of a fifty thousand row file quietly shift the whole result set and every downstream number is wrong rather than missing.</p>
<p>What keeps it alive is that <code>completed</code> is the word everyone was waiting for. The polling loop is written once, early, against a status enum, and <code>status == "completed"</code> becomes the definition of success for the rest of the system's life. The counts sit in the same object the loop already fetched, one field away from the condition it tests, and are never looked at. There is no alert to configure, because nothing failed: the API did exactly what it said, and what it said was narrower than what was heard.</p>""",
"why": """<p><strong>"Completed" describes the batch, not the requests.</strong> The status field tracks the lifecycle of the job object: <code>validating</code>, <code>in_progress</code>, <code>finalizing</code>, <code>completed</code>. A batch reaches <code>completed</code> when it has stopped running, whatever the outcome of the rows. There is no status that means "finished and every row succeeded", so no status check can express it.</p>
<p><strong>Row-level failures are individually ordinary.</strong> A row can hit the model's context limit, trip a content filter, exhaust a rate limit or catch a 500. Each of those is a normal per-request outcome that the Batch API records against the row and moves on from. Aborting a fifty thousand row job because row 12,004 was too long would be worse behaviour, so it does not, and the price of that is that partial success is the API's ordinary state.</p>
<p><strong>The signal is arithmetic, not a flag.</strong> There is no <code>partial</code> boolean and no warning field. <code>request_counts</code> carries <code>total</code>, <code>completed</code> and <code>failed</code>, and the finding is the comparison between them. That is why this check is a function rather than a condition: three numbers can disagree in more than one way.</p>
<p><strong>There is no request log to fall back on.</strong> Neither provider exposes an endpoint that lists individual inference requests with their statuses. If you do not reconcile the counts on the batch object, there is nowhere else to go and ask which rows failed &mdash; only the <a href="/llm/batch-error-file-never-read/">error file</a>, which expires after thirty days.</p>
<p><strong>The other terminal states hide behind the same loop.</strong> A batch that never ran at all lands in <code>failed</code>, one that ran out of time lands in <code>expired</code>, and a polling loop that only tests for <code>completed</code> treats both as "still running" forever. Those are separate notes, and a reconciliation script should say so rather than fold them in here.</p>""",
"steps": [
 {"h": "List the batches, do not just re-fetch the one you remember",
  "body": """<p><code>GET /v1/batches?limit=100</code> and follow <code>after</code> with the last <code>id</code> on the page while <code>has_more</code> is true. The audit has to be over every batch in the retention window, because the whole failure mode is a job that nobody went back to look at.</p>"""},
 {"h": "Read request_counts instead of status",
  "body": """<p>Three fields: <code>total</code>, <code>completed</code>, <code>failed</code>. Assert both halves &mdash; <code>failed == 0</code> and <code>completed == total</code>. Testing only the first misses rows that never ran; testing only the second misses nothing today but says less about what happened.</p>"""},
 {"h": "Separate failed rows from unaccounted rows",
  "body": """<p><code>failed &gt; 0</code> means rows ran and returned an error, and those errors are in the error file. <code>completed + failed &lt; total</code> means rows are in neither column, which on a finished batch is a hole: cross-check it against the <a href="/llm/batch-expired-past-24h-window/">expiry note</a>, because abandoned rows are how a window closing shows up in the counts.</p>"""},
 {"h": "Reconcile line counts, not just the status enum",
  "body": """<p>Before your job marks itself done, count the lines in the downloaded output file and compare against the lines you uploaded. Join on <code>custom_id</code> and never on position: a missing row in a positional join corrupts every row after it instead of dropping one.</p>"""},
 {"h": "Print the repair, then decide whether to re-run it",
  "body": """<p>Read the error file, bucket the lines by <code>error.code</code>, retry the transient ones (<code>rate_limit_exceeded</code>, <code>server_error</code>) in a follow-up batch of just those <code>custom_id</code>s, and fix the rest. Re-submitting spends money on inference, which is why this script prints the command and stops.</p>"""},
],
"verify": """<p>Re-run the script after the follow-up batch has landed. Every completed batch in the window should reconcile.</p>
<pre><code class="language-bash">python3 openai_batch_partial_failure_audit.py
# clean       batch_68f2a1  all 50000 row(s) completed
# 14 completed batch(es) checked, 0 with rows missing</code></pre>""",
"code_intro": "One paginated GET and no writes, so a project key set to Read Only is enough and is what this should hold. The classifier is pure and takes nothing but the batch object, because no clock is involved in this note: the question is whether three integers agree, and the reason it is a function with tests rather than an <code>if</code> is that they can disagree in two different ways and the two want different repairs.",
"py_file": "openai_batch_partial_failure_audit.py",
"py": '''"""Report OpenAI batches that read completed while rows inside them failed.

Read only. GET requests and nothing else: give this a project key set to Read
Only. The repair is printed, never performed, because re-submitting the failed
rows means spending money on inference and that is your decision to make.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("openai_batch_partial_failure_audit")

API = "https://api.openai.com/v1"

# Still moving. None of these is a verdict about the rows, because the counts
# are not final until the batch stops.
IN_FLIGHT = ("validating", "in_progress", "finalizing", "cancelling")

# Terminal, and owned by the sibling notes rather than by this script: a failed
# batch never ran a single row, an expired one ran out of window, a cancelled
# one was stopped on purpose.
OTHER_TERMINAL = ("failed", "expired", "cancelled")

FINDINGS = ("partial", "unaccounted")


def counts_of(batch):
    """Read request_counts into three ints, or None when it cannot be read.

    Pure. Missing members are read as zero because the API omits nothing here,
    but a request_counts that is not an object at all returns None rather than
    three zeros: three zeros would classify as an empty batch, which is a
    completely different and much calmer finding than an unreadable one.
    """
    counts = batch.get("request_counts")
    if not isinstance(counts, dict):
        return None
    try:
        total = int(counts.get("total") or 0)
        done = int(counts.get("completed") or 0)
        failed = int(counts.get("failed") or 0)
    except (TypeError, ValueError):
        return None
    return (total, done, failed)


def verdict(batch):
    """Classify one object from GET /v1/batches. Pure.

    Returns (state, detail). The two findings are kept apart on purpose:
    "partial" is rows that ran and failed, which are in the error file, and
    "unaccounted" is rows that are in neither column, which are not.
    """
    status = str(batch.get("status") or "").strip().lower()

    if status in IN_FLIGHT:
        return ("running",
                "status is %s, so the counts are not final and there is nothing "
                "to reconcile yet" % status)
    if status in OTHER_TERMINAL:
        return ("other-terminal",
                "status is %s. The batch did not finish running, which is a "
                "different problem from finishing with failures inside it."
                % status)
    if status != "completed":
        return ("unreadable",
                "status is %r, which is not a lifecycle state this script "
                "recognises. Read the object by hand." % (status or None,))

    numbers = counts_of(batch)
    if numbers is None:
        return ("unreadable",
                "the batch says completed and carries no readable "
                "request_counts, so nothing here can be reconciled. That is not "
                "the same as a clean batch and is not reported as one.")

    total, done, failed = numbers
    if total <= 0:
        return ("empty",
                "completed with a total of 0 request(s). The input file was "
                "empty or never parsed into rows.")
    if failed > 0:
        return ("partial",
                "%d of %d row(s) failed and the batch still reads completed. "
                "The output file is %d line(s) shorter than the input file."
                % (failed, total, total - done))
    if done < total:
        return ("unaccounted",
                "%d of %d row(s) are neither completed nor failed. Rows in "
                "neither column were abandoned rather than attempted, which is "
                "what a closed completion window looks like in the counts."
                % (total - done, total))
    return ("clean", "all %d row(s) completed" % total)


def get(session, path, params=None):
    r = session.get(API + path, params=params or {}, timeout=60)
    if r.status_code == 401:
        raise SystemExit("401 from OpenAI: the key is wrong, revoked, or belongs "
                         "to another project")
    r.raise_for_status()
    return r.json()


def batches(session, page_size, max_pages):
    """Walk GET /v1/batches, which paginates on the id of the last object."""
    params = {"limit": page_size}
    for _ in range(max_pages):
        page = get(session, "/batches", params)
        data = page.get("data") or []
        for batch in data:
            yield batch
        if not page.get("has_more") or not data:
            return
        params = {"limit": page_size, "after": data[-1].get("id")}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=100,
                    help="page size for GET /v1/batches (default 100)")
    ap.add_argument("--pages", type=int, default=20,
                    help="stop after this many pages (default 20)")
    ap.add_argument("--show-all", action="store_true",
                    help="also print batches that reconcile")
    args = ap.parse_args()

    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        log.error("set OPENAI_API_KEY (a project key set to Read Only)")
        return 2

    session = requests.Session()
    session.headers.update({"Authorization": "Bearer " + key})

    checked = 0
    bad = 0
    for batch in batches(session, args.limit, args.pages):
        state, detail = verdict(batch)
        batch_id = str(batch.get("id") or "?")
        line = "%-15s %s  %s" % (state, batch_id, detail)

        if state in FINDINGS:
            checked += 1
            bad += 1
            log.warning(line)
            error_file = batch.get("error_file_id")
            if error_file:
                log.warning("  repair: read the failures with GET "
                            "/v1/files/%s/content, bucket the lines by "
                            "error.code, and re-submit the failed custom_ids as "
                            "a new batch", error_file)
            else:
                log.warning("  repair: no error_file_id on this batch, so the "
                            "missing rows were never attempted. Re-submit them "
                            "and reconcile output lines against input lines.")
            log.warning("  repair: treat request_counts.failed > 0 as a job "
                        "failure in your orchestrator instead of trusting "
                        "status == completed")
        elif state == "clean":
            checked += 1
            if args.show_all:
                log.info(line)
        elif state in ("unreadable", "empty"):
            checked += 1
            log.warning(line)
        elif args.show_all:
            log.info(line)

    log.info("%d completed batch(es) checked, %d with rows missing", checked, bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "openai-batch-partial-failure-audit.mjs",
"js": '''/**
 * Report OpenAI batches that read completed while rows inside them failed.
 *
 * Read only. GET requests and nothing else: give this a project key set to Read
 * Only. The repair is printed, never performed.
 */
const API = 'https://api.openai.com/v1';

// Still moving. None of these is a verdict about the rows, because the counts
// are not final until the batch stops.
const IN_FLIGHT = ['validating', 'in_progress', 'finalizing', 'cancelling'];

// Terminal, and owned by the sibling notes rather than by this script.
const OTHER_TERMINAL = ['failed', 'expired', 'cancelled'];

const FINDINGS = ['partial', 'unaccounted'];

/**
 * Read request_counts into three numbers, or null when it cannot be read. Pure.
 * A request_counts that is not an object returns null rather than three zeros,
 * because three zeros classify as an empty batch and that is a much calmer
 * finding than an unreadable one.
 */
export function countsOf(batch) {
  const counts = batch.request_counts;
  if (counts === null || typeof counts !== 'object' || Array.isArray(counts)) return null;
  const total = Number(counts.total ?? 0);
  const done = Number(counts.completed ?? 0);
  const failed = Number(counts.failed ?? 0);
  if (!Number.isFinite(total) || !Number.isFinite(done) || !Number.isFinite(failed)) {
    return null;
  }
  return [Math.trunc(total), Math.trunc(done), Math.trunc(failed)];
}

/**
 * Classify one object from GET /v1/batches. Pure. Returns [state, detail].
 * The two findings are kept apart on purpose: "partial" is rows that ran and
 * failed, which are in the error file, and "unaccounted" is rows that are in
 * neither column, which are not.
 */
export function verdict(batch) {
  const status = String(batch.status ?? '').trim().toLowerCase();

  if (IN_FLIGHT.includes(status)) {
    return ['running',
      `status is ${status}, so the counts are not final and there is nothing ` +
      'to reconcile yet'];
  }
  if (OTHER_TERMINAL.includes(status)) {
    return ['other-terminal',
      `status is ${status}. The batch did not finish running, which is a ` +
      'different problem from finishing with failures inside it.'];
  }
  if (status !== 'completed') {
    return ['unreadable',
      `status is ${JSON.stringify(status || null)}, which is not a lifecycle ` +
      'state this script recognises. Read the object by hand.'];
  }

  const numbers = countsOf(batch);
  if (numbers === null) {
    return ['unreadable',
      'the batch says completed and carries no readable request_counts, so ' +
      'nothing here can be reconciled. That is not the same as a clean batch ' +
      'and is not reported as one.'];
  }

  const [total, done, failed] = numbers;
  if (total <= 0) {
    return ['empty',
      'completed with a total of 0 request(s). The input file was empty or ' +
      'never parsed into rows.'];
  }
  if (failed > 0) {
    return ['partial',
      `${failed} of ${total} row(s) failed and the batch still reads ` +
      `completed. The output file is ${total - done} line(s) shorter than the ` +
      'input file.'];
  }
  if (done < total) {
    return ['unaccounted',
      `${total - done} of ${total} row(s) are neither completed nor failed. ` +
      'Rows in neither column were abandoned rather than attempted, which is ' +
      'what a closed completion window looks like in the counts.'];
  }
  return ['clean', `all ${total} row(s) completed`];
}

async function get(key, path, params = {}) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null) url.searchParams.set(k, String(v));
  }
  const res = await fetch(url, { headers: { Authorization: `Bearer ${key}` } });
  if (res.status === 401) {
    throw new Error('401 from OpenAI: the key is wrong, revoked, or belongs to ' +
                    'another project');
  }
  if (!res.ok) throw new Error(`${res.status} from ${path}`);
  return res.json();
}

async function* walk(key, pageSize, maxPages) {
  let params = { limit: pageSize };
  for (let i = 0; i < maxPages; i += 1) {
    const page = await get(key, '/batches', params);
    const data = page.data ?? [];
    for (const batch of data) yield batch;
    if (!page.has_more || data.length === 0) return;
    params = { limit: pageSize, after: data[data.length - 1].id };
  }
}

async function main() {
  const key = process.env.OPENAI_API_KEY;
  if (!key) {
    console.error('set OPENAI_API_KEY (a project key set to Read Only)');
    process.exitCode = 2;
    return;
  }

  const pageSize = Number(process.env.LIMIT ?? 100);
  const maxPages = Number(process.env.PAGES ?? 20);
  const showAll = process.argv.includes('--show-all');

  let checked = 0;
  let bad = 0;
  for await (const batch of walk(key, pageSize, maxPages)) {
    const [state, detail] = verdict(batch);
    const batchId = String(batch.id ?? '?');
    const line = `${state.padEnd(15)} ${batchId}  ${detail}`;

    if (FINDINGS.includes(state)) {
      checked += 1;
      bad += 1;
      console.warn(line);
      console.warn(batch.error_file_id
        ? `  repair: read the failures with GET /v1/files/${batch.error_file_id}` +
          '/content, bucket the lines by error.code, and re-submit the failed ' +
          'custom_ids as a new batch'
        : '  repair: no error_file_id on this batch, so the missing rows were ' +
          'never attempted. Re-submit them and reconcile output lines against ' +
          'input lines.');
      console.warn('  repair: treat request_counts.failed > 0 as a job failure ' +
                   'in your orchestrator instead of trusting status == completed');
    } else if (state === 'clean') {
      checked += 1;
      if (showAll) console.log(line);
    } else if (state === 'unreadable' || state === 'empty') {
      checked += 1;
      console.warn(line);
    } else if (showAll) {
      console.log(line);
    }
  }

  console.log(`${checked} completed batch(es) checked, ${bad} with rows missing`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The test that matters is the first one: a batch whose <code>status</code> is <code>completed</code> and whose <code>failed</code> count is not zero must classify as a finding, because the entire note is that those two facts are compatible. The rest hold the surrounding states apart &mdash; rows that failed against rows that were never attempted, a batch still running against one that reconciles, and a missing <code>request_counts</code> against a clean one, which is the failure mode a lenient parser produces.",
"test_py_file": "test_openai_batch_partial_failure_audit.py",
"test_py": '''from openai_batch_partial_failure_audit import counts_of, verdict


def batch(status="completed", total=100, completed=100, failed=0, **extra):
    """A batch object shaped like GET /v1/batches returns them."""
    body = {"id": "batch_test", "status": status,
            "request_counts": {"total": total, "completed": completed,
                               "failed": failed}}
    body.update(extra)
    return body


def test_completed_does_not_mean_every_row_succeeded():
    # The whole note: these two facts are compatible and the status hides it.
    state, detail = verdict(batch(total=50000, completed=49131, failed=869))
    assert state == "partial"
    assert "869 of 50000" in detail
    assert "869 line(s) shorter" in detail


def test_a_clean_batch_needs_both_halves_of_the_arithmetic():
    assert verdict(batch(total=100, completed=100, failed=0))[0] == "clean"
    assert verdict(batch(total=100, completed=99, failed=1))[0] == "partial"


def test_rows_in_neither_column_are_their_own_finding():
    # Not failures. Abandoned rows: attempted by nobody, absent from the error
    # file, and the shape a closed completion window leaves behind.
    state, detail = verdict(batch(total=100, completed=60, failed=0))
    assert state == "unaccounted"
    assert "40 of 100" in detail
    assert "abandoned" in detail


def test_an_in_flight_batch_is_not_reconciled_yet():
    for status in ("validating", "in_progress", "finalizing", "cancelling"):
        state, detail = verdict(batch(status=status, total=100, completed=3))
        assert state == "running"
        assert "not final" in detail


def test_the_other_terminal_states_belong_to_the_sibling_notes():
    for status in ("failed", "expired", "cancelled"):
        assert verdict(batch(status=status, total=100, completed=4,
                             failed=0))[0] == "other-terminal"


def test_missing_counts_are_never_reported_as_clean():
    assert verdict({"id": "b", "status": "completed"})[0] == "unreadable"
    assert verdict({"id": "b", "status": "completed",
                    "request_counts": []})[0] == "unreadable"
    assert verdict({"id": "b"})[0] == "unreadable"
    assert verdict(batch(total=0, completed=0))[0] == "empty"


def test_counts_are_read_leniently_but_not_invented():
    assert counts_of({"request_counts": {"total": 10}}) == (10, 0, 0)
    assert counts_of({"request_counts": {"total": "10", "completed": "9",
                                         "failed": "1"}}) == (10, 9, 1)
    assert counts_of({"request_counts": {"total": "many"}}) is None
    assert counts_of({}) is None
''',
"test_js_file": "openai-batch-partial-failure-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { countsOf, verdict } from './openai-batch-partial-failure-audit.mjs';

/** A batch object shaped like GET /v1/batches returns them. */
function batch({ status = 'completed', total = 100, completed = 100,
                 failed = 0, ...extra } = {}) {
  return {
    id: 'batch_test',
    status,
    request_counts: { total, completed, failed },
    ...extra,
  };
}

test('completed does not mean every row succeeded', () => {
  const [state, detail] = verdict(batch({ total: 50000, completed: 49131, failed: 869 }));
  assert.equal(state, 'partial');
  assert.match(detail, /869 of 50000/);
  assert.match(detail, /869 line\\(s\\) shorter/);
});

test('a clean batch needs both halves of the arithmetic', () => {
  assert.equal(verdict(batch({ total: 100, completed: 100, failed: 0 }))[0], 'clean');
  assert.equal(verdict(batch({ total: 100, completed: 99, failed: 1 }))[0], 'partial');
});

test('rows in neither column are their own finding', () => {
  const [state, detail] = verdict(batch({ total: 100, completed: 60, failed: 0 }));
  assert.equal(state, 'unaccounted');
  assert.match(detail, /40 of 100/);
  assert.match(detail, /abandoned/);
});

test('an in flight batch is not reconciled yet', () => {
  for (const status of ['validating', 'in_progress', 'finalizing', 'cancelling']) {
    const [state, detail] = verdict(batch({ status, total: 100, completed: 3 }));
    assert.equal(state, 'running');
    assert.match(detail, /not final/);
  }
});

test('the other terminal states belong to the sibling notes', () => {
  for (const status of ['failed', 'expired', 'cancelled']) {
    assert.equal(verdict(batch({ status, total: 100, completed: 4 }))[0],
                 'other-terminal');
  }
});

test('missing counts are never reported as clean', () => {
  assert.equal(verdict({ id: 'b', status: 'completed' })[0], 'unreadable');
  assert.equal(verdict({ id: 'b', status: 'completed', request_counts: [] })[0],
               'unreadable');
  assert.equal(verdict({ id: 'b' })[0], 'unreadable');
  assert.equal(verdict(batch({ total: 0, completed: 0 }))[0], 'empty');
});

test('counts are read leniently but not invented', () => {
  assert.deepEqual(countsOf({ request_counts: { total: 10 } }), [10, 0, 0]);
  assert.deepEqual(countsOf({ request_counts: { total: '10', completed: '9', failed: '1' } }),
                   [10, 9, 1]);
  assert.equal(countsOf({ request_counts: { total: 'many' } }), null);
  assert.equal(countsOf({}), null);
});
''',
"faq": [
 ("If the batch says completed, what does the word actually promise?",
  "That the run reached a terminal state without being cancelled and without failing validation. It says nothing about the outcome of the requests inside it. Rows can fail individually on rate limits, context length, content filtering or transient server errors, and the batch still reads completed, so status is the wrong field to build a success condition on."),
 ("How do I know which rows failed?",
  "The error file. A batch with failures carries a non-null error_file_id, and GET /v1/files/{id}/content returns one JSON line per failed row with its custom_id and an error object. That file expires after thirty days, which is the whole of the sibling note on error files never being fetched."),
 ("What does it mean when completed plus failed is less than total?",
  "Rows that were neither run successfully nor run unsuccessfully. On a batch that reached completed this is unusual; on a batch that expired it is the normal shape, because the completion window closed on rows that had not been processed. Reconciling the two numbers separately is how you tell an abandoned row from a failed one."),
 ("Can I just retry the whole batch?",
  "You can, and on a large job you will pay for every row again including the ones that already succeeded. Rebuilding a .jsonl of only the failed custom_ids is cheaper, and it is also what tells you whether the failures are systematic — five hundred context-length errors are a prompt problem, five hundred rate-limit errors are a scheduling one."),
 ("Does Anthropic's Message Batches API behave the same way?",
  "Structurally yes. A Claude message batch ends with processing_status of ended and carries a request_counts object with succeeded, errored, canceled and expired members, so the same reconciliation applies: the batch ending is not a claim that every request in it succeeded. The result set is a .jsonl of per-request results rather than a split pair of output and error files, and it is retained for twenty-nine days."),
],
"related": [REL_ERRFILE, REL_EXPIRED, REL_DISCOUNT],
"citations": [CITE_BATCH_REF, CITE_BATCH_GUIDE, CITE_FILES_REF, CITE_AN_BATCH],
},

{
"slug": "batch-error-file-never-read",
"title": "The batch left an error_file_id that nothing ever fetched",
"description": "A completed batch carries a non-null error_file_id and no code ever called /content. The failures were written down and the downstream table is short.",
"h1": "the batch left an error_file_id that nothing ever fetched",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["openai batch error_file_id", "openai batch error file content",
             "batch output file missing rows", "openai files retention 30 days",
             "openai batch failures not logged"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Reads OPENAI_API_KEY, a project key set to Read Only.",
"lead": "The Batch API answers in two files. Successes go to <code>output_file_id</code> and failures go to <code>error_file_id</code>, and the ingest code was written against the first one on a day when the test batch had no failures. It has never opened the second. The failures are not lost &mdash; they were written down carefully, one JSON line each, with the <code>custom_id</code> and the reason. They are sitting in a file that has an id, a byte count and an expiry date, and in thirty days they will be gone whether or not anybody looked.",
"short_answer": """<p><code>GET /v1/batches?limit=100</code> and flag every object where <code>error_file_id</code> is not null. Then <code>GET /v1/files/{error_file_id}</code> for each one and read <code>bytes</code>: a non-zero error file is failures written down and waiting.</p>
<p>The API cannot tell you whether you read it &mdash; there is no access log on a file object &mdash; so the second half of the check has to come from your side. Pass the file ids your pipeline has actually fetched and the script reports the difference. Ids your ingest never recorded are the finding.</p>
<p>The clock matters here and nowhere else in this cluster. Batch output and error files expire <strong>thirty days</strong> after creation. An unread error file inside the window is a task; one past the window is a permanent hole, because no read call can recover it.</p>""",
"problem": """<p>The downstream table is short and nothing says so. The batch reported <code>completed</code>, the output file parsed cleanly, every line in it was valid, and the job wrote its success metric. The rows that failed are not in the output file at all, so there is no null to notice, no error to catch and no count to compare against unless somebody wrote the comparison. A pipeline can run in this state for a year, and the shortfall shows up eventually as an analytics number that is slightly wrong in a direction nobody can explain.</p>
<p>The thirty day retention is what turns a tidy problem into an untidy one. While the file exists, this is a morning's work: download, group by error code, re-submit. Once it expires you have lost the list of which rows failed and why, and reconstructing it means re-running the whole batch against the input file and diffing &mdash; paying for every row again to find out which ones you are missing.</p>""",
"why": """<p><strong>The results are deliberately split across two files.</strong> Successes go to <code>output_file_id</code> and failures to <code>error_file_id</code>. Each error line looks like <code>{"custom_id": "...", "response": null, "error": {"code": "...", "message": "..."}}</code>, or carries a <code>response.status_code</code> in the 4xx or 5xx range. Code that reads only the first file gets a silently truncated result set that is internally consistent.</p>
<p><strong>Nothing raises when you ignore a file id.</strong> <code>error_file_id</code> is a string on an object. Not fetching it is not an error condition, not a warning, and not visible to OpenAI. The only party who can notice is the code that was supposed to read it, which is precisely the code that does not exist.</p>
<p><strong>The API has no read receipt.</strong> There is no <code>last_accessed_at</code> on a file object and no access log to query, so a read-only script cannot prove the file was never opened. It can prove the file exists, that it is not empty, and that it is not in the list your pipeline says it has consumed &mdash; which is why the check takes your ingest record as an input rather than pretending to derive it.</p>
<p><strong>Retention is thirty days and it is measured from creation.</strong> That is a hard boundary in the platform, not a policy you can extend from the client, and it applies to the error file as much as the output file. Anything that has already aged out cannot be recovered by any read call, so "no evidence" outside the window is never proof of "no problem".</p>
<p><strong>A zero-byte error file is not the same as no error file.</strong> An <code>error_file_id</code> pointing at an empty file means the id was allocated and nothing was written to it. Reporting that as an unread pile of failures sends somebody after nothing, which is the fastest way to get the whole check ignored.</p>""",
"steps": [
 {"h": "List the batches and keep the ones with an error file",
  "body": """<p><code>GET /v1/batches?limit=100</code>, paginating on <code>after</code>. Keep every object where <code>error_file_id</code> is not null, regardless of <code>status</code> &mdash; a completed batch and an expired one can both carry one.</p>"""},
 {"h": "Confirm the file, and read its size",
  "body": """<p><code>GET /v1/files/{error_file_id}</code> returns the object with <code>bytes</code>, <code>created_at</code>, <code>filename</code> and <code>purpose</code>. Non-zero <code>bytes</code> means there are failures written down. Zero means the id was allocated and never written to, which is not a finding.</p>"""},
 {"h": "Bring your own record of what the pipeline has fetched",
  "body": """<p>The API cannot tell you whether you read the file. Pass the ids your ingest has consumed with <code>--fetched</code> or a newline-delimited file, and the script reports the ones that are not in it. If you have no such record, that absence is itself the finding.</p>"""},
 {"h": "Sort by the retention clock, not by batch size",
  "body": """<p>Files expire thirty days after creation. An error file with two days left is more urgent than a bigger one with three weeks, because after that the list of failed <code>custom_id</code>s cannot be recovered by any read call at all &mdash; only by re-running the batch.</p>"""},
 {"h": "Make the assertion, then keep it",
  "body": """<p>In the batch-completion handler, assert that <code>error_file_id</code> is null before the job marks itself done, and when it is not, download it, group by <code>error.code</code> and act. That single assertion is what stops this recurring; the audit script exists to find the batches that ran before it was there.</p>"""},
],
"verify": """<p>Re-run with the ids your pipeline consumed. Every batch carrying an error file should be accounted for.</p>
<pre><code class="language-bash">python3 openai_batch_error_file_audit.py --fetched-file ingested_error_files.txt
# fetched         batch_68f2a1  error file file_abc is in the ingest record
# 6 batch(es) with an error file, 0 never fetched</code></pre>""",
"code_intro": "Two GETs and no writes: the batch list, then one file object per batch that names an error file. The classifier is pure and takes <code>now</code> as an argument, because the thirty day retention boundary is the one thing here that changes on its own &mdash; a file with a day left and a file that expired yesterday want different words, and neither case will ever occur on the day a test happens to run. It also takes your ingest record as an argument rather than inventing one, because the API has no read receipt to offer.",
"py_file": "openai_batch_error_file_audit.py",
"py": '''"""Report OpenAI batch error files that exist and were never fetched.

Read only. Two GET requests and nothing else: give this a project key set to
Read Only. The repair is printed, never performed.

The API cannot tell you whether you read a file: there is no last_accessed_at
on a file object and no access log to query. So the second half of this check
comes from you, as a list of error file ids your ingest has consumed. Absence
of that list is itself an answer.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("openai_batch_error_file_audit")

API = "https://api.openai.com/v1"
DAY = 86400

# Batch input, output and error files are retained for 30 days from creation.
# After that the content is unrecoverable by any read call.
RETENTION_DAYS = 30

IN_FLIGHT = ("validating", "in_progress", "finalizing", "cancelling")

FINDINGS = ("unread", "expiring", "aged-out")


def days_left(created_at, now, retention_days=RETENTION_DAYS):
    """Whole days of retention left on a file, or None if unreadable. Pure.

    Floors the elapsed time, so a file created 29.9 days ago has 1 day left
    rather than 0.1: this number is printed to a human who will act on it
    tomorrow, and rounding it the other way promises time that is not there.
    """
    try:
        created = int(created_at)
    except (TypeError, ValueError):
        return None
    if created <= 0:
        return None
    return retention_days - int((int(now) - created) // DAY)


def verdict(batch, file_meta, fetched, now, retention_days=RETENTION_DAYS,
            urgent_days=3):
    """Classify one batch against its error file and your ingest record. Pure.

    file_meta is the object from GET /v1/files/{id}, or None when that call
    found nothing. fetched is the set of error file ids your pipeline has
    consumed. now is unix seconds, passed in so the retention boundary can be
    tested at a fixed instant. Returns (state, detail).
    """
    status = str(batch.get("status") or "").strip().lower()
    file_id = str(batch.get("error_file_id") or "").strip()

    if status in IN_FLIGHT:
        return ("running",
                "status is %s; an error file is not final until the batch stops"
                % status)
    if not file_id:
        return ("no-error-file",
                "no error_file_id on this batch, so nothing failed hard enough "
                "to be written to one")
    if file_id in set(fetched or ()):
        return ("fetched",
                "error file %s is in the ingest record, so the failures were "
                "read" % file_id)

    created = None
    if isinstance(file_meta, dict):
        created = file_meta.get("created_at")
    if not created:
        created = batch.get("created_at")
    left = days_left(created, now, retention_days)

    if not isinstance(file_meta, dict):
        if left is not None and left <= 0:
            return ("aged-out",
                    "error file %s is past the %d day retention window and "
                    "GET /v1/files no longer returns it. Which rows failed, and "
                    "why, cannot be recovered by any read call now."
                    % (file_id, retention_days))
        return ("unresolvable",
                "the batch names error file %s but GET /v1/files/%s returned "
                "nothing, and the file is still inside the retention window. "
                "Check that id by hand." % (file_id, file_id))

    try:
        size = int(file_meta.get("bytes") or 0)
    except (TypeError, ValueError):
        size = 0

    if size <= 0:
        return ("empty",
                "error file %s exists and holds 0 byte(s). The id was allocated "
                "and never written to, so there is nothing in it to read."
                % file_id)
    if left is not None and left <= 0:
        return ("aged-out",
                "error file %s holds %d byte(s) that are past the %d day "
                "retention window. The metadata is still listed; the content is "
                "not retrievable." % (file_id, size, retention_days))
    if left is not None and left <= urgent_days:
        return ("expiring",
                "error file %s holds %d byte(s), is not in the ingest record, "
                "and expires in %d day(s). Download it before the window closes."
                % (file_id, size, left))
    return ("unread",
            "error file %s holds %d byte(s) and is not in the ingest record. "
            "Every line in it is a row missing from the downstream table."
            % (file_id, size))


def get(session, path, params=None):
    r = session.get(API + path, params=params or {}, timeout=60)
    if r.status_code == 401:
        raise SystemExit("401 from OpenAI: the key is wrong, revoked, or belongs "
                         "to another project")
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.json()


def batches(session, page_size, max_pages):
    """Walk GET /v1/batches, which paginates on the id of the last object."""
    params = {"limit": page_size}
    for _ in range(max_pages):
        page = get(session, "/batches", params)
        data = (page or {}).get("data") or []
        for batch in data:
            yield batch
        if not (page or {}).get("has_more") or not data:
            return
        params = {"limit": page_size, "after": data[-1].get("id")}


def read_fetched(args):
    """The error file ids your pipeline says it consumed. Local reads only."""
    ids = set(args.fetched)
    if args.fetched_file:
        with open(args.fetched_file, "r", encoding="utf-8") as fh:
            ids.update(line.strip() for line in fh if line.strip())
    return ids


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fetched", action="append", default=[],
                    help="an error file id your pipeline has consumed; repeatable")
    ap.add_argument("--fetched-file",
                    help="a file of error file ids your pipeline has consumed, "
                         "one per line")
    ap.add_argument("--limit", type=int, default=100,
                    help="page size for GET /v1/batches (default 100)")
    ap.add_argument("--pages", type=int, default=20,
                    help="stop after this many pages (default 20)")
    ap.add_argument("--show-all", action="store_true",
                    help="also print batches with nothing to fetch")
    args = ap.parse_args()

    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        log.error("set OPENAI_API_KEY (a project key set to Read Only)")
        return 2

    fetched = read_fetched(args)
    if not fetched:
        log.info("no ingest record passed, so every error file will be reported "
                 "as unread. Pass --fetched or --fetched-file once you have one.")

    session = requests.Session()
    session.headers.update({"Authorization": "Bearer " + key})

    now = int(time.time())
    with_file = 0
    bad = 0
    for batch in batches(session, args.limit, args.pages):
        file_id = str(batch.get("error_file_id") or "").strip()
        file_meta = get(session, "/files/" + file_id) if file_id else None

        state, detail = verdict(batch, file_meta, fetched, now)
        batch_id = str(batch.get("id") or "?")
        line = "%-15s %s  %s" % (state, batch_id, detail)

        if file_id:
            with_file += 1
        if state in FINDINGS:
            bad += 1
            log.warning(line)
            if state == "aged-out":
                log.warning("  repair: the content is gone. Re-run the batch "
                            "from the original input file and diff the output "
                            "custom_ids against it to find the missing rows.")
            else:
                log.warning("  repair: GET /v1/files/%s/content, group the lines "
                            "by error.code, retry the transient ones "
                            "(rate_limit_exceeded, server_error) as a new batch, "
                            "and fix the rest", file_id)
            log.warning("  repair: assert error_file_id is null in the "
                        "batch-completion handler rather than checking it by hand "
                        "once a year")
        elif state == "unresolvable":
            log.warning(line)
        elif args.show_all or state == "empty":
            log.info(line)

    log.info("%d batch(es) with an error file, %d never fetched", with_file, bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "openai-batch-error-file-audit.mjs",
"js": '''/**
 * Report OpenAI batch error files that exist and were never fetched.
 *
 * Read only. Two GET requests and nothing else: give this a project key set to
 * Read Only. The repair is printed, never performed.
 *
 * The API cannot tell you whether you read a file, so the second half of this
 * check comes from you, as a list of error file ids your ingest has consumed.
 */
import { readFileSync } from 'node:fs';

const API = 'https://api.openai.com/v1';
const DAY = 86400;

// Batch input, output and error files are retained for 30 days from creation.
const RETENTION_DAYS = 30;

const IN_FLIGHT = ['validating', 'in_progress', 'finalizing', 'cancelling'];

const FINDINGS = ['unread', 'expiring', 'aged-out'];

/**
 * Whole days of retention left on a file, or null if unreadable. Pure. Floors
 * the elapsed time, so a file created 29.9 days ago has 1 day left rather than
 * 0.1: the number is printed to a human who will act on it tomorrow.
 */
export function daysLeft(createdAt, now, retentionDays = RETENTION_DAYS) {
  const created = Number(createdAt);
  if (!Number.isFinite(created) || created <= 0) return null;
  return retentionDays - Math.floor((Number(now) - created) / DAY);
}

/**
 * Classify one batch against its error file and your ingest record. Pure.
 * fileMeta is the object from GET /v1/files/{id}, or null when that call found
 * nothing. now is unix seconds, passed in so the retention boundary can be
 * tested at a fixed instant. Returns [state, detail].
 */
export function verdict(batch, fileMeta, fetched, now,
                        retentionDays = RETENTION_DAYS, urgentDays = 3) {
  const status = String(batch.status ?? '').trim().toLowerCase();
  const fileId = String(batch.error_file_id ?? '').trim();

  if (IN_FLIGHT.includes(status)) {
    return ['running',
      `status is ${status}; an error file is not final until the batch stops`];
  }
  if (!fileId) {
    return ['no-error-file',
      'no error_file_id on this batch, so nothing failed hard enough to be ' +
      'written to one'];
  }
  const seen = fetched instanceof Set ? fetched : new Set(fetched ?? []);
  if (seen.has(fileId)) {
    return ['fetched',
      `error file ${fileId} is in the ingest record, so the failures were read`];
  }

  const isMeta = fileMeta !== null && typeof fileMeta === 'object';
  const created = (isMeta && fileMeta.created_at) || batch.created_at;
  const left = daysLeft(created, now, retentionDays);

  if (!isMeta) {
    if (left !== null && left <= 0) {
      return ['aged-out',
        `error file ${fileId} is past the ${retentionDays} day retention ` +
        'window and GET /v1/files no longer returns it. Which rows failed, ' +
        'and why, cannot be recovered by any read call now.'];
    }
    return ['unresolvable',
      `the batch names error file ${fileId} but GET /v1/files/${fileId} ` +
      'returned nothing, and the file is still inside the retention window. ' +
      'Check that id by hand.'];
  }

  const raw = Number(fileMeta.bytes ?? 0);
  const size = Number.isFinite(raw) ? Math.trunc(raw) : 0;

  if (size <= 0) {
    return ['empty',
      `error file ${fileId} exists and holds 0 byte(s). The id was allocated ` +
      'and never written to, so there is nothing in it to read.'];
  }
  if (left !== null && left <= 0) {
    return ['aged-out',
      `error file ${fileId} holds ${size} byte(s) that are past the ` +
      `${retentionDays} day retention window. The metadata is still listed; ` +
      'the content is not retrievable.'];
  }
  if (left !== null && left <= urgentDays) {
    return ['expiring',
      `error file ${fileId} holds ${size} byte(s), is not in the ingest ` +
      `record, and expires in ${left} day(s). Download it before the window ` +
      'closes.'];
  }
  return ['unread',
    `error file ${fileId} holds ${size} byte(s) and is not in the ingest ` +
    'record. Every line in it is a row missing from the downstream table.'];
}

async function get(key, path, params = {}) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null) url.searchParams.set(k, String(v));
  }
  const res = await fetch(url, { headers: { Authorization: `Bearer ${key}` } });
  if (res.status === 401) {
    throw new Error('401 from OpenAI: the key is wrong, revoked, or belongs to ' +
                    'another project');
  }
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`${res.status} from ${path}`);
  return res.json();
}

async function* walk(key, pageSize, maxPages) {
  let params = { limit: pageSize };
  for (let i = 0; i < maxPages; i += 1) {
    const page = await get(key, '/batches', params);
    const data = page?.data ?? [];
    for (const batch of data) yield batch;
    if (!page?.has_more || data.length === 0) return;
    params = { limit: pageSize, after: data[data.length - 1].id };
  }
}

function readFetched() {
  const ids = new Set();
  process.argv.forEach((arg, i) => {
    if (arg === '--fetched' && process.argv[i + 1]) ids.add(process.argv[i + 1]);
    if (arg === '--fetched-file' && process.argv[i + 1]) {
      for (const line of readFileSync(process.argv[i + 1], 'utf8').split('\\n')) {
        if (line.trim()) ids.add(line.trim());
      }
    }
  });
  return ids;
}

async function main() {
  const key = process.env.OPENAI_API_KEY;
  if (!key) {
    console.error('set OPENAI_API_KEY (a project key set to Read Only)');
    process.exitCode = 2;
    return;
  }

  const fetched = readFetched();
  if (fetched.size === 0) {
    console.log('no ingest record passed, so every error file will be reported ' +
                'as unread. Pass --fetched or --fetched-file once you have one.');
  }

  const pageSize = Number(process.env.LIMIT ?? 100);
  const maxPages = Number(process.env.PAGES ?? 20);
  const showAll = process.argv.includes('--show-all');
  const now = Math.floor(Date.now() / 1000);

  let withFile = 0;
  let bad = 0;
  for await (const batch of walk(key, pageSize, maxPages)) {
    const fileId = String(batch.error_file_id ?? '').trim();
    const fileMeta = fileId ? await get(key, `/files/${fileId}`) : null;

    const [state, detail] = verdict(batch, fileMeta, fetched, now);
    const line = `${state.padEnd(15)} ${String(batch.id ?? '?')}  ${detail}`;

    if (fileId) withFile += 1;
    if (FINDINGS.includes(state)) {
      bad += 1;
      console.warn(line);
      console.warn(state === 'aged-out'
        ? '  repair: the content is gone. Re-run the batch from the original ' +
          'input file and diff the output custom_ids against it to find the ' +
          'missing rows.'
        : `  repair: GET /v1/files/${fileId}/content, group the lines by ` +
          'error.code, retry the transient ones (rate_limit_exceeded, ' +
          'server_error) as a new batch, and fix the rest');
      console.warn('  repair: assert error_file_id is null in the ' +
                   'batch-completion handler rather than checking it by hand ' +
                   'once a year');
    } else if (state === 'unresolvable') {
      console.warn(line);
    } else if (showAll || state === 'empty') {
      console.log(line);
    }
  }

  console.log(`${withFile} batch(es) with an error file, ${bad} never fetched`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly, so importing this module from the test file
// does not fire main() and fail on the missing key.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Every test runs at a fixed instant, because the interesting boundary is a calendar one: the day an error file crosses out of the thirty day retention window is the day the finding stops being a task and becomes a permanent hole, and it will never land on the day the suite runs. The other tests hold apart the three ways an error file can be uninteresting &mdash; already fetched, empty, or attached to a batch that is still running &mdash; from the one way it is not.",
"test_py_file": "test_openai_batch_error_file_audit.py",
"test_py": '''from openai_batch_error_file_audit import days_left, verdict

# 2026-08-30T00:00:00Z. Fixed, because the retention boundary is the point.
NOW = 1788048000
DAY = 86400


def batch(status="completed", error_file_id="file_err", age_days=10):
    return {"id": "batch_test", "status": status,
            "error_file_id": error_file_id,
            "created_at": NOW - age_days * DAY}


def meta(size=4096, age_days=10):
    return {"id": "file_err", "bytes": size, "purpose": "batch_output",
            "created_at": NOW - age_days * DAY}


def test_an_error_file_nobody_fetched_is_the_finding():
    state, detail = verdict(batch(), meta(size=4096), set(), NOW)
    assert state == "unread"
    assert "4096 byte(s)" in detail
    assert "missing from the downstream table" in detail


def test_the_ingest_record_is_what_clears_it():
    state, _ = verdict(batch(), meta(), {"file_err"}, NOW)
    assert state == "fetched"


def test_retention_turns_a_task_into_a_hole():
    # 29 days old: one day left, and urgent.
    state, detail = verdict(batch(age_days=29), meta(age_days=29), set(), NOW)
    assert state == "expiring"
    assert "1 day(s)" in detail

    # 31 days old: the content is unrecoverable by any read call.
    state, detail = verdict(batch(age_days=31), meta(age_days=31), set(), NOW)
    assert state == "aged-out"
    assert "not retrievable" in detail


def test_a_missing_file_object_reads_differently_inside_and_outside_the_window():
    assert verdict(batch(age_days=40), None, set(), NOW)[0] == "aged-out"
    assert verdict(batch(age_days=2), None, set(), NOW)[0] == "unresolvable"


def test_an_empty_error_file_is_not_a_pile_of_failures():
    state, detail = verdict(batch(), meta(size=0), set(), NOW)
    assert state == "empty"
    assert "never written to" in detail


def test_batches_with_nothing_to_read_are_left_alone():
    assert verdict(batch(error_file_id=None), None, set(), NOW)[0] == "no-error-file"
    assert verdict(batch(error_file_id=""), None, set(), NOW)[0] == "no-error-file"
    assert verdict(batch(status="in_progress"), meta(), set(), NOW)[0] == "running"


def test_days_left_floors_and_admits_ignorance():
    assert days_left(NOW - 10 * DAY, NOW) == 20
    assert days_left(NOW - int(29.9 * DAY), NOW) == 1
    assert days_left(NOW - 30 * DAY, NOW) == 0
    assert days_left(None, NOW) is None
    assert days_left("yesterday", NOW) is None
''',
"test_js_file": "openai-batch-error-file-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { daysLeft, verdict } from './openai-batch-error-file-audit.mjs';

// 2026-08-30T00:00:00Z. Fixed, because the retention boundary is the point.
const NOW = 1788048000;
const DAY = 86400;

function batch({ status = 'completed', errorFileId = 'file_err',
                 ageDays = 10 } = {}) {
  return {
    id: 'batch_test',
    status,
    error_file_id: errorFileId,
    created_at: NOW - ageDays * DAY,
  };
}

function meta({ size = 4096, ageDays = 10 } = {}) {
  return {
    id: 'file_err',
    bytes: size,
    purpose: 'batch_output',
    created_at: NOW - ageDays * DAY,
  };
}

test('an error file nobody fetched is the finding', () => {
  const [state, detail] = verdict(batch(), meta({ size: 4096 }), new Set(), NOW);
  assert.equal(state, 'unread');
  assert.match(detail, /4096 byte\\(s\\)/);
  assert.match(detail, /missing from the downstream table/);
});

test('the ingest record is what clears it', () => {
  assert.equal(verdict(batch(), meta(), new Set(['file_err']), NOW)[0], 'fetched');
});

test('retention turns a task into a hole', () => {
  const [near, nearDetail] = verdict(batch({ ageDays: 29 }),
                                     meta({ ageDays: 29 }), new Set(), NOW);
  assert.equal(near, 'expiring');
  assert.match(nearDetail, /1 day\\(s\\)/);

  const [gone, goneDetail] = verdict(batch({ ageDays: 31 }),
                                     meta({ ageDays: 31 }), new Set(), NOW);
  assert.equal(gone, 'aged-out');
  assert.match(goneDetail, /not retrievable/);
});

test('a missing file object reads differently inside and outside the window', () => {
  assert.equal(verdict(batch({ ageDays: 40 }), null, new Set(), NOW)[0], 'aged-out');
  assert.equal(verdict(batch({ ageDays: 2 }), null, new Set(), NOW)[0],
               'unresolvable');
});

test('an empty error file is not a pile of failures', () => {
  const [state, detail] = verdict(batch(), meta({ size: 0 }), new Set(), NOW);
  assert.equal(state, 'empty');
  assert.match(detail, /never written to/);
});

test('batches with nothing to read are left alone', () => {
  assert.equal(verdict(batch({ errorFileId: null }), null, new Set(), NOW)[0],
               'no-error-file');
  assert.equal(verdict(batch({ errorFileId: '' }), null, new Set(), NOW)[0],
               'no-error-file');
  assert.equal(verdict(batch({ status: 'in_progress' }), meta(), new Set(), NOW)[0],
               'running');
});

test('daysLeft floors and admits ignorance', () => {
  assert.equal(daysLeft(NOW - 10 * DAY, NOW), 20);
  assert.equal(daysLeft(NOW - Math.trunc(29.9 * DAY), NOW), 1);
  assert.equal(daysLeft(NOW - 30 * DAY, NOW), 0);
  assert.equal(daysLeft(null, NOW), null);
  assert.equal(daysLeft('yesterday', NOW), null);
});
''',
"faq": [
 ("Can the API tell me whether I ever downloaded the error file?",
  "No. A file object carries id, bytes, created_at, filename, purpose and status, and nothing resembling last_accessed_at. There is no access log endpoint either. That is why this script takes the list of ids your pipeline has consumed as an input: the half of the question the API can answer is that the file exists and is not empty, and the other half has to come from you."),
 ("What is actually in the error file?",
  "One JSON object per failed row. Each carries the custom_id you supplied, a null response, and an error object with code and message; some rows instead carry a response with a 4xx or 5xx status_code and the body the endpoint returned. Because custom_id is in every line, the file is directly usable as the input to a follow-up batch of only the failed rows."),
 ("The batch says completed and there is still an error_file_id. Is that a contradiction?",
  "No, and it is the normal case. Completed describes the run, not the rows: a batch finishes with successes in the output file and failures in the error file. Reconciling request_counts is the sibling check, and it is the one that tells you how many lines to expect in the file this note is about."),
 ("How long do I have?",
  "Thirty days from the file's creation, for batch input, output and error files alike. After that the content cannot be retrieved by any read call and the only way back to the list of failed rows is to re-run the batch from the original input file and diff the custom_ids, which means paying for every row again."),
 ("Does Anthropic split results the same way?",
  "No, and the difference matters if you run both. A Claude message batch exposes a single results_url streaming one JSON line per request, where each line carries a result object whose type is succeeded, errored, canceled or expired. There is no separate error file to forget, because successes and failures arrive interleaved in the same stream and a parser has to look at the type on every line. Results are retained for twenty-nine days."),
],
"related": [REL_PARTIAL, REL_EXPIRED, REL_DISCOUNT],
"citations": [CITE_FILES_REF, CITE_BATCH_GUIDE, CITE_BATCH_REF, CITE_AN_BATCH],
},

{
"slug": "batch-expired-past-24h-window",
"title": "A batch expired when the 24 hour completion window closed",
"description": "status is expired and request_counts.completed is below total. The fixed 24h window closed on rows that had not run, and no HTTP error was raised.",
"h1": "a batch expired when the 24 hour completion window closed",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["openai batch expired", "batch_expired error code",
             "openai batch 24h completion window", "openai batch expires_at",
             "openai batch never finished"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Reads OPENAI_API_KEY, a project key set to Read Only.",
"lead": "The submission returned <code>200</code> yesterday afternoon. The poller has been asking for the batch ever since, testing the status against <code>completed</code>, and it has never matched, so as far as the job is concerned the work is still running. It is not. Twenty-four hours after the batch started processing, everything OpenAI had not got to was abandoned, the status went to <code>expired</code>, and thirty thousand rows landed in the error file with the code <code>batch_expired</code>. Nothing raised, nothing retried, and the poller is still waiting.",
"short_answer": """<p><code>GET /v1/batches?limit=100</code>, paginating on <code>after</code>. Flag every object with <code>status == \"expired\"</code> and compute the shortfall as <code>request_counts.total - request_counts.completed</code>. Those rows were never processed and never will be.</p>
<p>Then do the more useful half: flag the batches that are <em>about</em> to do this. Anything still in <code>validating</code>, <code>in_progress</code> or <code>finalizing</code> whose <code>expires_at</code> is a few hours away is the same outage, caught while there is still time to split the job.</p>
<p>The window is fixed. <code>completion_window</code> accepts one value, <code>24h</code>, and the clock runs from when the batch starts processing rather than from when you created it. A batch is not late; at the end of that window it is over.</p>""",
"problem": """<p>The damage is shaped by the polling loop. Code that waits for <code>completed</code> and treats everything else as "not yet" will wait forever on an expired batch, because <code>expired</code> is terminal and <code>completed</code> will never arrive. The job does not fail, it hangs; and a hung nightly job usually means the next night's run stacks on top of it, which puts more work into the same queue that could not drain the first batch.</p>
<p>The partial result is the second problem. An expired batch is not empty: the rows that ran are in the output file and are perfectly good. Downstream that looks like a batch that worked, at a size nobody checked. Deleting and re-running is expensive because you pay again for the rows that already succeeded, and re-running only the missing rows means reading the error file to find out which they were &mdash; a file that expires thirty days after it was written.</p>""",
"why": """<p><strong>The window is a hard 24 hours and it is not configurable.</strong> <code>completion_window</code> takes the single value <code>24h</code>. There is no extension, no priority flag and no way to ask for longer. What has not been processed when the window closes is abandoned rather than deferred.</p>
<p><strong>Size and queue depth both eat the window.</strong> A batch can hold up to 50,000 requests or a 200 MB input file, and a batch that large has no obligation to fit in the window. Neither does a small one submitted behind a queue of your own earlier batches, since they all draw on the same per-model capacity.</p>
<p><strong>The create call cannot warn you.</strong> <code>POST /v1/batches</code> returns 200 immediately with a status of <code>validating</code>. Whether the work will drain in time is a fact about the next twenty-four hours, so nothing in the response can carry it. The only forward-looking field is <code>expires_at</code>, and reading it is the entire pre-emptive half of this check.</p>
<p><strong>Expiry is invisible unless you enumerate.</strong> There is no webhook, no email and no push of any kind for a batch reaching <code>expired</code>. It is a field on an object you have to ask for, and the code most likely to have stopped asking is the code that lost track of the batch id.</p>
<p><strong>The clock starts at in_progress_at, not created_at.</strong> Time spent in <code>validating</code> is not the window. That is why this script reads <code>expires_at</code> when the object carries it, falls back to <code>in_progress_at</code> plus 24 hours, and only then falls back to <code>created_at</code> plus 24 hours &mdash; which it labels as an upper bound rather than pretending it is the deadline.</p>""",
"steps": [
 {"h": "Enumerate every batch, not the ones you have ids for",
  "body": """<p><code>GET /v1/batches?limit=100</code> and follow <code>after</code>. A job that lost track of its batch id is exactly the job that expired, so the audit cannot start from the ids your database remembers.</p>"""},
 {"h": "Measure the shortfall on the expired ones",
  "body": """<p><code>request_counts.total - request_counts.completed</code> is the number of rows that never ran. Read <code>expired_at</code> for when the window closed. Every one of those rows is a line in the error file carrying <code>{"code": "batch_expired"}</code>, which is what makes the re-submission list recoverable for thirty days.</p>"""},
 {"h": "Read expires_at on the batches still moving",
  "body": """<p>This is the half worth automating. Anything in <code>validating</code>, <code>in_progress</code> or <code>finalizing</code> with only a few hours of window left is heading for the same outcome, and there is still time to submit the tail as a second batch rather than lose it.</p>"""},
 {"h": "Stop treating anything-but-completed as still running",
  "body": """<p><code>expired</code>, <code>failed</code> and <code>cancelled</code> are terminal. A poller that waits for <code>completed</code> hangs on all three. Test for a terminal set and branch, and give the poll loop a wall-clock ceiling of its own so it cannot outlive the window it is waiting on.</p>"""},
 {"h": "Split the work so it fits, and diary the deadline",
  "body": """<p>Keep a single batch well under the 50,000 request and 200 MB ceilings, hold a small number in flight rather than submitting a loop of them, and store <code>expires_at</code> in your own job table with an alert at the twenty-hour mark. The window you cannot extend is one you have to plan inside.</p>"""},
],
"verify": """<p>Re-run after splitting the job. Nothing should be expired, and nothing in flight should be near its deadline.</p>
<pre><code class="language-bash">python3 openai_batch_expiry_audit.py --warn-hours 4
# in-flight       batch_68f3c2  21.4 hour(s) of window left (from expires_at); 8200 of 20000 row(s) done
# 9 batch(es) checked, 0 expired, 0 close to expiring</code></pre>""",
"code_intro": "One paginated GET, no writes, and a project key set to Read Only. The classifier takes <code>now</code> as an argument for the obvious reason and one less obvious one: the pre-emptive half of this check is entirely a subtraction against the current time, so without an injected clock the only testable case is the one that has already gone wrong. The deadline itself is a second pure function, because the object offers three different timestamps to measure from and they are not equally good.",
"py_file": "openai_batch_expiry_audit.py",
"py": '''"""Report OpenAI batches that expired, and the ones about to.

Read only. GET requests and nothing else: give this a project key set to Read
Only. The repair is printed, never performed, because re-submitting the rows
that never ran means spending money on inference.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("openai_batch_expiry_audit")

API = "https://api.openai.com/v1"

# completion_window accepts one value. This is not a default, it is the value.
WINDOW = 86400

IN_FLIGHT = ("validating", "in_progress", "finalizing", "cancelling")

# Terminal and not this note: a completed batch finished, a failed one never
# started, a cancelled one was stopped on purpose.
SETTLED = ("completed", "failed", "cancelled")

FINDINGS = ("expired", "overdue", "expiring-soon")


def counts_of(batch):
    """Read request_counts into (total, completed), or None. Pure."""
    counts = batch.get("request_counts")
    if not isinstance(counts, dict):
        return None
    try:
        return (int(counts.get("total") or 0), int(counts.get("completed") or 0))
    except (TypeError, ValueError):
        return None


def deadline(batch):
    """When this batch's window closes, and where the number came from. Pure.

    Returns (unix_seconds, source) or (None, reason). Three timestamps can
    answer this and they are not equally good, which is why the source is
    returned alongside the number rather than thrown away:

      expires_at      the API's own answer. Use it whenever it is there.
      in_progress_at  the window runs from when processing started, so this
                      plus 24h is the deadline whenever expires_at is absent.
      created_at      an upper bound only. Time spent in validating is not part
                      of the window, so this over-estimates the time left.
    """
    for field, offset, source in (
            ("expires_at", 0, "expires_at"),
            ("in_progress_at", WINDOW, "in_progress_at plus 24h"),
            ("created_at", WINDOW,
             "created_at plus 24h, an upper bound: the window starts when the "
             "batch starts processing, not when it was created")):
        raw = batch.get(field)
        if raw in (None, ""):
            continue
        try:
            value = int(raw)
        except (TypeError, ValueError):
            continue
        if value > 0:
            return (value + offset, source)
    return (None, "no usable timestamp on this object")


def verdict(batch, now, warn_hours=4):
    """Classify one object from GET /v1/batches against a clock you pass in.

    Pure. warn_hours is the headroom below which an in-flight batch is called
    out: 4 hours left of a 24 hour window is the 20 hour mark. Returns
    (state, detail).
    """
    status = str(batch.get("status") or "").strip().lower()
    numbers = counts_of(batch)
    total, done = numbers if numbers else (0, 0)
    rows = ("%d of %d row(s)" % (done, total)) if total else "an unreadable count of rows"

    if status == "expired":
        missing = max(0, total - done)
        return ("expired",
                "the 24 hour window closed with %d row(s) unfinished (%s done). "
                "Each one is a batch_expired line in the error file, and none of "
                "them will run." % (missing, rows))
    if status in SETTLED:
        return ("settled",
                "status is %s, so no window is running against it" % status)
    if status not in IN_FLIGHT:
        return ("unreadable",
                "status is %r, which is not a lifecycle state this script "
                "recognises" % (status or None,))

    when, source = deadline(batch)
    if when is None:
        return ("unreadable",
                "still %s and there is %s, so the window cannot be measured"
                % (status, source))

    left = when - int(now)
    hours = abs(left) / 3600.0
    if left <= 0:
        return ("overdue",
                "still %s, %.1f hour(s) past the close of its window (from %s). "
                "The rows that have not run are not going to." % (status, hours, source))
    if left <= warn_hours * 3600:
        return ("expiring-soon",
                "%.1f hour(s) of window left (from %s) with %s done. Submit the "
                "tail as a second batch while there is still time."
                % (hours, source, rows))
    return ("in-flight",
            "%.1f hour(s) of window left (from %s); %s done" % (hours, source, rows))


def get(session, path, params=None):
    r = session.get(API + path, params=params or {}, timeout=60)
    if r.status_code == 401:
        raise SystemExit("401 from OpenAI: the key is wrong, revoked, or belongs "
                         "to another project")
    r.raise_for_status()
    return r.json()


def batches(session, page_size, max_pages):
    """Walk GET /v1/batches, which paginates on the id of the last object."""
    params = {"limit": page_size}
    for _ in range(max_pages):
        page = get(session, "/batches", params)
        data = page.get("data") or []
        for batch in data:
            yield batch
        if not page.get("has_more") or not data:
            return
        params = {"limit": page_size, "after": data[-1].get("id")}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--warn-hours", type=float, default=4.0,
                    help="call out in-flight batches with less than this many "
                         "hours of window left (default 4, the 20 hour mark)")
    ap.add_argument("--limit", type=int, default=100,
                    help="page size for GET /v1/batches (default 100)")
    ap.add_argument("--pages", type=int, default=20,
                    help="stop after this many pages (default 20)")
    ap.add_argument("--show-all", action="store_true",
                    help="also print settled batches")
    args = ap.parse_args()

    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        log.error("set OPENAI_API_KEY (a project key set to Read Only)")
        return 2

    session = requests.Session()
    session.headers.update({"Authorization": "Bearer " + key})

    now = int(time.time())
    checked = 0
    expired = 0
    closing = 0
    for batch in batches(session, args.limit, args.pages):
        state, detail = verdict(batch, now, args.warn_hours)
        batch_id = str(batch.get("id") or "?")
        line = "%-15s %s  %s" % (state, batch_id, detail)
        checked += 1

        if state == "expired":
            expired += 1
            log.warning(line)
            error_file = batch.get("error_file_id")
            log.warning("  repair: rebuild a .jsonl of the custom_ids whose "
                        "error.code is batch_expired%s and re-submit them, then "
                        "split future jobs so one batch stays well under 50,000 "
                        "requests",
                        (" from GET /v1/files/%s/content" % error_file)
                        if error_file else "")
        elif state in ("overdue", "expiring-soon"):
            closing += 1
            log.warning(line)
            log.warning("  repair: store expires_at in your own job table and "
                        "alert at the 20 hour mark; a poller that waits for "
                        "status == completed waits forever on an expired batch")
        elif state == "unreadable":
            log.warning(line)
        elif args.show_all or state == "in-flight":
            log.info(line)

    log.info("%d batch(es) checked, %d expired, %d close to expiring",
             checked, expired, closing)
    return 1 if (expired or closing) else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "openai-batch-expiry-audit.mjs",
"js": '''/**
 * Report OpenAI batches that expired, and the ones about to.
 *
 * Read only. GET requests and nothing else: give this a project key set to Read
 * Only. The repair is printed, never performed.
 */
const API = 'https://api.openai.com/v1';

// completion_window accepts one value. This is not a default, it is the value.
const WINDOW = 86400;

const IN_FLIGHT = ['validating', 'in_progress', 'finalizing', 'cancelling'];

// Terminal and not this note.
const SETTLED = ['completed', 'failed', 'cancelled'];

/** Read request_counts into [total, completed], or null. Pure. */
export function countsOf(batch) {
  const counts = batch.request_counts;
  if (counts === null || typeof counts !== 'object' || Array.isArray(counts)) return null;
  const total = Number(counts.total ?? 0);
  const done = Number(counts.completed ?? 0);
  if (!Number.isFinite(total) || !Number.isFinite(done)) return null;
  return [Math.trunc(total), Math.trunc(done)];
}

/**
 * When this batch's window closes, and where the number came from. Pure.
 * Returns [unixSeconds, source] or [null, reason]. Three timestamps can answer
 * this and they are not equally good, which is why the source is returned
 * alongside the number: expires_at is the API's own answer, in_progress_at plus
 * 24h is the deadline when it is absent, and created_at plus 24h is an upper
 * bound only, because time spent validating is not part of the window.
 */
export function deadline(batch) {
  const candidates = [
    ['expires_at', 0, 'expires_at'],
    ['in_progress_at', WINDOW, 'in_progress_at plus 24h'],
    ['created_at', WINDOW,
      'created_at plus 24h, an upper bound: the window starts when the batch ' +
      'starts processing, not when it was created'],
  ];
  for (const [field, offset, source] of candidates) {
    const raw = batch[field];
    if (raw === null || raw === undefined || raw === '') continue;
    const value = Number(raw);
    if (Number.isFinite(value) && value > 0) return [Math.trunc(value) + offset, source];
  }
  return [null, 'no usable timestamp on this object'];
}

/**
 * Classify one object from GET /v1/batches against a clock you pass in. Pure.
 * warnHours is the headroom below which an in-flight batch is called out: 4
 * hours left of a 24 hour window is the 20 hour mark. Returns [state, detail].
 */
export function verdict(batch, now, warnHours = 4) {
  const status = String(batch.status ?? '').trim().toLowerCase();
  const numbers = countsOf(batch);
  const [total, done] = numbers ?? [0, 0];
  const rows = total ? `${done} of ${total} row(s)` : 'an unreadable count of rows';

  if (status === 'expired') {
    const missing = Math.max(0, total - done);
    return ['expired',
      `the 24 hour window closed with ${missing} row(s) unfinished (${rows} ` +
      'done). Each one is a batch_expired line in the error file, and none of ' +
      'them will run.'];
  }
  if (SETTLED.includes(status)) {
    return ['settled', `status is ${status}, so no window is running against it`];
  }
  if (!IN_FLIGHT.includes(status)) {
    return ['unreadable',
      `status is ${JSON.stringify(status || null)}, which is not a lifecycle ` +
      'state this script recognises'];
  }

  const [when, source] = deadline(batch);
  if (when === null) {
    return ['unreadable',
      `still ${status} and there is ${source}, so the window cannot be measured`];
  }

  const left = when - Math.trunc(now);
  const hours = (Math.abs(left) / 3600).toFixed(1);
  if (left <= 0) {
    return ['overdue',
      `still ${status}, ${hours} hour(s) past the close of its window (from ` +
      `${source}). The rows that have not run are not going to.`];
  }
  if (left <= warnHours * 3600) {
    return ['expiring-soon',
      `${hours} hour(s) of window left (from ${source}) with ${rows} done. ` +
      'Submit the tail as a second batch while there is still time.'];
  }
  return ['in-flight',
    `${hours} hour(s) of window left (from ${source}); ${rows} done`];
}

async function get(key, path, params = {}) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null) url.searchParams.set(k, String(v));
  }
  const res = await fetch(url, { headers: { Authorization: `Bearer ${key}` } });
  if (res.status === 401) {
    throw new Error('401 from OpenAI: the key is wrong, revoked, or belongs to ' +
                    'another project');
  }
  if (!res.ok) throw new Error(`${res.status} from ${path}`);
  return res.json();
}

async function* walk(key, pageSize, maxPages) {
  let params = { limit: pageSize };
  for (let i = 0; i < maxPages; i += 1) {
    const page = await get(key, '/batches', params);
    const data = page.data ?? [];
    for (const batch of data) yield batch;
    if (!page.has_more || data.length === 0) return;
    params = { limit: pageSize, after: data[data.length - 1].id };
  }
}

async function main() {
  const key = process.env.OPENAI_API_KEY;
  if (!key) {
    console.error('set OPENAI_API_KEY (a project key set to Read Only)');
    process.exitCode = 2;
    return;
  }

  const warnHours = Number(process.env.WARN_HOURS ?? 4);
  const pageSize = Number(process.env.LIMIT ?? 100);
  const maxPages = Number(process.env.PAGES ?? 20);
  const showAll = process.argv.includes('--show-all');
  const now = Math.floor(Date.now() / 1000);

  let checked = 0;
  let expired = 0;
  let closing = 0;
  for await (const batch of walk(key, pageSize, maxPages)) {
    const [state, detail] = verdict(batch, now, warnHours);
    const line = `${state.padEnd(15)} ${String(batch.id ?? '?')}  ${detail}`;
    checked += 1;

    if (state === 'expired') {
      expired += 1;
      console.warn(line);
      const errorFile = batch.error_file_id;
      console.warn('  repair: rebuild a .jsonl of the custom_ids whose ' +
        'error.code is batch_expired' +
        (errorFile ? ` from GET /v1/files/${errorFile}/content` : '') +
        ' and re-submit them, then split future jobs so one batch stays well ' +
        'under 50,000 requests');
    } else if (state === 'overdue' || state === 'expiring-soon') {
      closing += 1;
      console.warn(line);
      console.warn('  repair: store expires_at in your own job table and alert ' +
        'at the 20 hour mark; a poller that waits for status == completed waits ' +
        'forever on an expired batch');
    } else if (state === 'unreadable') {
      console.warn(line);
    } else if (showAll || state === 'in-flight') {
      console.log(line);
    }
  }

  console.log(`${checked} batch(es) checked, ${expired} expired, ${closing} ` +
              'close to expiring');
  process.exitCode = (expired || closing) ? 1 : 0;
}

// Only run when invoked directly, so importing this module from the test file
// does not fire main() and fail on the missing key.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The clock is an argument, so the two states that only exist for a few hours can be tested at all: a batch with two hours of window left, and one whose window closed while it was still reporting <code>in_progress</code>. The other tests pin down which timestamp the deadline came from, because a fallback to <code>created_at</code> over-states the time remaining and a report that quietly does that is worse than no report.",
"test_py_file": "test_openai_batch_expiry_audit.py",
"test_py": '''from openai_batch_expiry_audit import counts_of, deadline, verdict

# 2026-08-30T00:00:00Z. Fixed, because every state here is a subtraction from it.
NOW = 1788048000
HOUR = 3600


def batch(status="in_progress", total=20000, completed=8000, **extra):
    body = {"id": "batch_test", "status": status,
            "request_counts": {"total": total, "completed": completed,
                               "failed": 0}}
    body.update(extra)
    return body


def test_an_expired_batch_reports_the_rows_that_never_ran():
    state, detail = verdict(
        batch(status="expired", total=50000, completed=20000,
              expired_at=NOW - HOUR), NOW)
    assert state == "expired"
    assert "30000 row(s) unfinished" in detail
    assert "batch_expired" in detail


def test_a_batch_close_to_its_deadline_is_the_useful_finding():
    state, detail = verdict(batch(expires_at=NOW + 2 * HOUR), NOW, warn_hours=4)
    assert state == "expiring-soon"
    assert "2.0 hour(s) of window left" in detail
    assert "second batch" in detail


def test_a_batch_with_room_left_is_left_alone():
    state, detail = verdict(batch(expires_at=NOW + 23 * HOUR), NOW, warn_hours=4)
    assert state == "in-flight"
    assert "23.0 hour(s)" in detail


def test_a_window_that_closed_while_the_status_still_says_running():
    state, detail = verdict(batch(expires_at=NOW - HOUR), NOW)
    assert state == "overdue"
    assert "1.0 hour(s) past" in detail


def test_the_deadline_says_which_timestamp_it_came_from():
    assert deadline({"expires_at": NOW}) == (NOW, "expires_at")
    when, source = deadline({"in_progress_at": NOW - HOUR})
    assert when == NOW - HOUR + 86400
    assert source == "in_progress_at plus 24h"
    when, source = deadline({"created_at": NOW - HOUR})
    assert when == NOW - HOUR + 86400
    assert "upper bound" in source
    assert deadline({"id": "b"})[0] is None


def test_expires_at_wins_over_the_fallbacks():
    # A long validating queue makes created_at plus 24h too generous, so the
    # API's own answer is preferred whenever the object carries it.
    when, source = deadline({"created_at": NOW - 6 * HOUR,
                             "in_progress_at": NOW - HOUR,
                             "expires_at": NOW + 2 * HOUR})
    assert when == NOW + 2 * HOUR
    assert source == "expires_at"


def test_settled_and_unreadable_batches_are_not_findings():
    for status in ("completed", "failed", "cancelled"):
        assert verdict(batch(status=status), NOW)[0] == "settled"
    assert verdict(batch(status="teleporting"), NOW)[0] == "unreadable"
    assert verdict(batch(), NOW)[0] == "unreadable"  # in flight, no timestamps
    assert counts_of({"request_counts": {"total": 5, "completed": 5}}) == (5, 5)
    assert counts_of({}) is None
''',
"test_js_file": "openai-batch-expiry-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { countsOf, deadline, verdict } from './openai-batch-expiry-audit.mjs';

// 2026-08-30T00:00:00Z. Fixed, because every state here is a subtraction from it.
const NOW = 1788048000;
const HOUR = 3600;

function batch({ status = 'in_progress', total = 20000, completed = 8000,
                 ...extra } = {}) {
  return {
    id: 'batch_test',
    status,
    request_counts: { total, completed, failed: 0 },
    ...extra,
  };
}

test('an expired batch reports the rows that never ran', () => {
  const [state, detail] = verdict(
    batch({ status: 'expired', total: 50000, completed: 20000,
            expired_at: NOW - HOUR }), NOW);
  assert.equal(state, 'expired');
  assert.match(detail, /30000 row\\(s\\) unfinished/);
  assert.match(detail, /batch_expired/);
});

test('a batch close to its deadline is the useful finding', () => {
  const [state, detail] = verdict(batch({ expires_at: NOW + 2 * HOUR }), NOW, 4);
  assert.equal(state, 'expiring-soon');
  assert.match(detail, /2\\.0 hour\\(s\\) of window left/);
  assert.match(detail, /second batch/);
});

test('a batch with room left is left alone', () => {
  const [state, detail] = verdict(batch({ expires_at: NOW + 23 * HOUR }), NOW, 4);
  assert.equal(state, 'in-flight');
  assert.match(detail, /23\\.0 hour\\(s\\)/);
});

test('a window that closed while the status still says running', () => {
  const [state, detail] = verdict(batch({ expires_at: NOW - HOUR }), NOW);
  assert.equal(state, 'overdue');
  assert.match(detail, /1\\.0 hour\\(s\\) past/);
});

test('the deadline says which timestamp it came from', () => {
  assert.deepEqual(deadline({ expires_at: NOW }), [NOW, 'expires_at']);
  const [started, startedSource] = deadline({ in_progress_at: NOW - HOUR });
  assert.equal(started, NOW - HOUR + 86400);
  assert.equal(startedSource, 'in_progress_at plus 24h');
  const [created, createdSource] = deadline({ created_at: NOW - HOUR });
  assert.equal(created, NOW - HOUR + 86400);
  assert.match(createdSource, /upper bound/);
  assert.equal(deadline({ id: 'b' })[0], null);
});

test('expires_at wins over the fallbacks', () => {
  const [when, source] = deadline({
    created_at: NOW - 6 * HOUR,
    in_progress_at: NOW - HOUR,
    expires_at: NOW + 2 * HOUR,
  });
  assert.equal(when, NOW + 2 * HOUR);
  assert.equal(source, 'expires_at');
});

test('settled and unreadable batches are not findings', () => {
  for (const status of ['completed', 'failed', 'cancelled']) {
    assert.equal(verdict(batch({ status }), NOW)[0], 'settled');
  }
  assert.equal(verdict(batch({ status: 'teleporting' }), NOW)[0], 'unreadable');
  assert.equal(verdict(batch(), NOW)[0], 'unreadable');
  assert.deepEqual(countsOf({ request_counts: { total: 5, completed: 5 } }), [5, 5]);
  assert.equal(countsOf({}), null);
});
''',
"faq": [
 ("Can I ask for a completion window longer than 24 hours?",
  "No. completion_window takes the single value 24h, there is no priority tier for batch, and there is no extension request. The window is a constraint to plan inside rather than a setting to tune, which is why the repair is to split the job rather than to ask for more time."),
 ("When does the clock actually start?",
  "When the batch starts processing, which the object records as in_progress_at, not when you created it. Time spent in validating is not charged against the window. In practice you should read expires_at, which the API sets for you; the fallbacks matter only when an object does not carry it, and a fallback to created_at over-states the time you have left."),
 ("What happened to the rows that did finish?",
  "They are in the output file and they are good. An expired batch is a partial result, not a failed one, which is why it is dangerous downstream: the output parses cleanly at a size nobody checks. Reconcile the line count against the input file before loading it."),
 ("How do I find out which rows to re-submit?",
  "The error file. Every abandoned row is written there with an error code of batch_expired, so selecting those lines and taking their custom_ids gives you exactly the re-submission set. That file expires thirty days after it was written, and after that the only way to reconstruct the list is to re-run the whole batch and diff it."),
 ("Does Anthropic's Message Batches API expire the same way?",
  "It has the same idea with different numbers and a different vocabulary. A Claude message batch is also expected to complete within 24 hours, requests that do not finish come back with a result type of expired, and the batch itself is cancellable mid-flight. There is no completion_window parameter to set at all, and results are retained for twenty-nine days rather than thirty."),
],
"related": [REL_PARTIAL, REL_ERRFILE, REL_DISCOUNT],
"citations": [CITE_BATCH_REF, CITE_BATCH_GUIDE, CITE_FILES_REF, CITE_AN_BATCH],
},

{
"slug": "batch-discount-left-unused",
"title": "Scheduled jobs pay full price for work the Batch API halves",
"description": "group_by=batch returns one row, batch:false. Nightly enrichment and backfills go through the synchronous endpoint at roughly twice the batch price.",
"h1": "scheduled jobs pay full price for work the Batch API halves",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["openai batch api discount", "openai batch 50 percent cheaper",
             "openai usage group_by batch", "openai reduce inference cost",
             "batch vs synchronous pricing"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Needs OPENAI_ADMIN_KEY, an organization admin key provisioned read-only, because everything under /v1/organization/* rejects a project key.",
"lead": "Nothing here is broken. No request failed, no row is missing, and no alert should have fired. The nightly enrichment job fires forty thousand completions between 02:00 and 02:20, finishes cleanly, and does it again the next night. It has no user waiting on it and no latency requirement of any kind, and it is being billed at the interactive rate because the synchronous endpoint is what the SDK example used. This is not a bug report. It is an invoice roughly twice the size it needs to be.",
"short_answer": """<p>With an <strong>organization admin key</strong>, read <code>GET /v1/organization/usage/completions?start_time={now-7d}&amp;bucket_width=1h&amp;limit=168&amp;group_by=batch&amp;group_by=project_id&amp;group_by=model</code>. Each result carries a <code>batch</code> boolean beside <code>input_tokens</code>, <code>output_tokens</code> and <code>num_model_requests</code>.</p>
<p>If every result has <code>batch: false</code>, the Batch API is unused. That on its own is not a finding &mdash; interactive traffic belongs on the synchronous endpoint. The finding is batch-<em>shaped</em> traffic inside the synchronous half: a project whose requests are concentrated into a handful of hours a day rather than spread across them, which is a scheduled job wearing interactive pricing.</p>
<p>Then price it. <code>GET /v1/organization/costs?start_time=…&amp;group_by=line_item</code> reports batch and non-batch as distinct line items, and batch is priced at half. The saving is half the synchronous spend of the jobs you can actually move.</p>""",
"problem": """<p>The cost is invisible because it is a discount not taken rather than a charge incurred. There is no line on the invoice labelled "paid twice as much as necessary", no error, no degraded response and no metric that moves. The only artefact is a total that is larger than a counterfactual nobody computed. That is a category of problem that survives indefinitely, because every review of it concludes that the system is working.</p>
<p>It is also nobody's decision. Nothing chose the synchronous endpoint over the asynchronous one: the SDK's <code>create()</code> is synchronous, every example in the docs is synchronous, and the first prototype was necessarily synchronous because it was a person typing into a terminal. The nightly job was built by copying the prototype. Latency insensitivity is a property of the workload that the code has no way to declare and the API has no way to infer.</p>""",
"why": """<p><strong>Batch is priced at half, on both input and output.</strong> That is the entire trade, and it is a real one: you give up latency guarantees and accept a completion window of up to 24 hours, and the same tokens cost half as much. For work with nobody waiting, the thing you gave up has no value.</p>
<p><strong>The API cannot tell a scheduled job from user traffic.</strong> Request by request, forty thousand completions from a cron job look exactly like forty thousand completions from people. There is no field that says "this could have waited". The only signal is aggregate shape, which is why this check reads hourly buckets rather than totals.</p>
<p><strong>The shape is the whole detection.</strong> Interactive traffic follows human hours: a broad curve with a floor. Scheduled work is a spike &mdash; most of the week's requests inside a few percent of the hours. Concentration is measurable from <code>num_model_requests</code> per bucket without knowing anything about what the requests contained.</p>
<p><strong>The usage endpoints need an admin key, and only OpenAI counts requests.</strong> Everything under <code>/v1/organization/*</code> rejects a project key outright. And the request count that makes this check possible is an OpenAI field: Anthropic's messages usage report returns token sums per bucket with no request-count member at all, so the same shape analysis on that side has to be done on tokens and is correspondingly blunter.</p>
<p><strong>Not every clustered job can move.</strong> A job with a downstream deadline four hours later cannot accept a 24 hour window, and one that feeds a user-visible dashboard by 09:00 might not either. The script reports what is eligible by shape; whether it can actually move is a fact about your schedule that no endpoint knows.</p>""",
"steps": [
 {"h": "Get an organization admin key, provisioned read-only",
  "body": """<p><code>/v1/organization/usage/*</code> and <code>/v1/organization/costs</code> both reject project keys. Use an <code>sk-admin-</code> key with read scopes. This script only ever issues GETs, so read-only is all it wants.</p>"""},
 {"h": "Pull a week of hourly buckets, grouped by batch",
  "body": """<p><code>bucket_width=1h</code> with <code>limit=168</code> over seven days, grouping by <code>batch</code>, <code>project_id</code> and <code>model</code>. The <code>batch</code> boolean is non-null only because you grouped by it. Follow <code>next_page</code> to the end.</p>"""},
 {"h": "Measure concentration, not just the batch share",
  "body": """<p>For each project and model, take the synchronous <code>num_model_requests</code> per hour and compute what share of the week lands in the busiest ten percent of hours. Above about seventy percent, that is a schedule rather than an audience.</p>"""},
 {"h": "Price it from the cost report, not from a table you typed in",
  "body": """<p><code>GET /v1/organization/costs?start_time=…&amp;bucket_width=1d&amp;group_by=line_item&amp;group_by=project_id</code>. Batch and non-batch appear as distinct <code>line_item</code> strings, so the synchronous spend is a filter rather than an estimate, and the saving is half of it. Hardcoded per-token prices go stale; the cost report does not.</p>"""},
 {"h": "Move one job, then read the same window again",
  "body": """<p>Upload a JSONL of requests to <code>/v1/files</code> with <code>purpose=\"batch\"</code>, create the batch with a 24 hour completion window, and handle the two result files. A week later the same query should show a <code>batch: true</code> population that did not exist before. Then read the <a href="/llm/batch-partial-failure-unnoticed/">reconciliation note</a>, because asynchronous work fails differently.</p>"""},
],
"verify": """<p>Re-run after the first job has moved. The traffic that was batch-shaped should now be reported as already batched.</p>
<pre><code class="language-bash">python3 openai_batch_discount_audit.py --days 7
# already-batched  proj_night / gpt-5.6-terra  94% of requests already go through the Batch API
# 6 workload(s), 0 batch shaped
</code></pre>""",
"code_intro": "Two GETs against the organization endpoints, no writes, and an admin key that should be provisioned read-only. Four pure functions carry the note: the accumulator, which has to keep the hourly buckets aligned per workload or the shape measurement is meaningless; the concentration measure, which is the actual detection; the classifier, which keeps “too little traffic to say” and “already batched” as answers rather than folding them into a pass; and the saving, which is deliberately half of the measured spend rather than a per-token price table that would go stale by the time you read this.",
"py_file": "openai_batch_discount_audit.py",
"py": '''"""Report synchronous OpenAI traffic that is shaped like batch work.

Read only. Two GET requests against the organization endpoints and nothing
else. Those endpoints reject project keys, so this needs an organization admin
key (sk-admin-), which can and should be provisioned read-only.

This is a cost note, not a failure note. Nothing found here is broken: the
finding is latency-insensitive work paying interactive prices, and the repair
is a change to how a job submits its requests, printed for you to run.
"""
import argparse
import logging
import math
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("openai_batch_discount_audit")

API = "https://api.openai.com/v1"

# The Batch API is priced at half the synchronous rate on both input and output
# tokens, in exchange for a completion window of up to 24 hours.
DISCOUNT = 0.50


def accumulate(buckets):
    """Fold usage buckets into one row per project and model. Pure.

    The hourly request counts have to stay aligned across the whole window, so
    each row carries a list as long as the bucket list with zeros where that
    workload was idle. Compacting out the idle hours would make every workload
    look concentrated, which is exactly the thing being measured.
    """
    buckets = list(buckets or [])
    rows = {}
    for index, bucket in enumerate(buckets):
        for result in bucket.get("results") or []:
            project = str(result.get("project_id") or "unknown")
            model = str(result.get("model") or "unknown")
            key = "%s / %s" % (project, model)
            row = rows.get(key)
            if row is None:
                row = {"key": key, "project_id": project, "model": model,
                       "sync_requests": 0, "batch_requests": 0,
                       "sync_input": 0, "sync_output": 0,
                       "hourly": [0] * len(buckets)}
                rows[key] = row
            requests_made = int(result.get("num_model_requests") or 0)
            if result.get("batch") is True:
                row["batch_requests"] += requests_made
            else:
                row["sync_requests"] += requests_made
                row["sync_input"] += int(result.get("input_tokens") or 0)
                row["sync_output"] += int(result.get("output_tokens") or 0)
                row["hourly"][index] += requests_made
    return rows


def concentration(hourly, top_fraction=0.10):
    """Share of requests inside the busiest slice of the window. Pure.

    Returns a float between 0 and 1, or None when there is nothing to measure.
    A scheduled job puts most of its week into a handful of hours; an audience
    does not, however uneven its day looks.
    """
    counts = [int(c or 0) for c in (hourly or [])]
    total = sum(counts)
    if not counts or total <= 0:
        return None
    top = max(1, int(math.ceil(len(counts) * top_fraction)))
    return sum(sorted(counts, reverse=True)[:top]) / float(total)


def verdict(row, min_requests=1000, threshold=0.70, top_fraction=0.10):
    """Classify one workload's week. Pure. Returns (state, detail).

    "interactive" and "already-batched" are answers, not failures to detect
    something: synchronous is the correct endpoint for traffic with a person
    waiting on it, and this script says so rather than staying silent.
    """
    sync = int(row.get("sync_requests") or 0)
    batched = int(row.get("batch_requests") or 0)
    total = sync + batched

    if total < min_requests:
        return ("too-little-traffic",
                "%d request(s) in the window, which is too few to say anything "
                "about the shape" % total)

    share = sync / float(total)
    if share < 0.20:
        return ("already-batched",
                "%.0f%% of %d request(s) already go through the Batch API"
                % (100 * (1 - share), total))

    spike = concentration(row.get("hourly"), top_fraction)
    if spike is None:
        return ("unmeasurable",
                "%d synchronous request(s) and no per bucket counts to spread "
                "them over, so the shape cannot be measured" % sync)

    if spike >= threshold:
        return ("batch-shaped",
                "%.0f%% of %d synchronous request(s) land in the busiest %.0f%% "
                "of hours. That is a schedule, not an audience, and it is paying "
                "interactive prices." % (spike * 100, sync, top_fraction * 100))
    return ("interactive",
            "%d synchronous request(s), %.0f%% of them in the busiest %.0f%% of "
            "hours. Spread out like traffic with someone waiting on it, so the "
            "synchronous endpoint is the right one."
            % (sync, spike * 100, top_fraction * 100))


def sync_cost(buckets, project_id=None):
    """Non-batch dollars in the cost report, optionally for one project. Pure.

    Batch and non-batch appear as distinct line_item strings, so the split is a
    substring test and nothing more clever than that. Reading the money from the
    cost report rather than from a per-token price table is deliberate: the
    table goes stale, the report does not.
    """
    total = 0.0
    for bucket in buckets or []:
        for result in bucket.get("results") or []:
            if project_id and str(result.get("project_id") or "") != project_id:
                continue
            if "batch" in str(result.get("line_item") or "").lower():
                continue
            try:
                total += float((result.get("amount") or {}).get("value") or 0.0)
            except (TypeError, ValueError):
                continue
    return round(total, 2)


def saving(sync_cost_usd, discount=DISCOUNT):
    """What the same spend would have been worth at batch prices. Pure.

    Not a promise: it is the value of the discount on money already spent, and
    it says nothing about whether the job can accept a 24 hour window. That
    part is a fact about your schedule and no endpoint knows it.
    """
    if sync_cost_usd is None:
        return None
    try:
        return round(max(0.0, float(sync_cost_usd)) * discount, 2)
    except (TypeError, ValueError):
        return None


def get(session, path, params):
    r = session.get(API + path, params=params, timeout=90)
    if r.status_code in (401, 403):
        raise SystemExit("%d from OpenAI: /v1/organization/* needs an "
                         "organization admin key (sk-admin-), not a project key"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def pages(session, path, params, max_pages=40):
    """Walk a usage or cost report, which paginates on an opaque page cursor."""
    params = dict(params)
    for _ in range(max_pages):
        page = get(session, path, params)
        for bucket in page.get("data") or []:
            yield bucket
        if not page.get("has_more") or not page.get("next_page"):
            return
        params = dict(params)
        params["page"] = page["next_page"]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=7,
                    help="days of hourly buckets to read (default 7)")
    ap.add_argument("--min-requests", type=int, default=1000,
                    help="ignore workloads below this many requests (default 1000)")
    ap.add_argument("--threshold", type=float, default=0.70,
                    help="share of requests in the busiest hours above which a "
                         "workload is called batch shaped (default 0.70)")
    ap.add_argument("--top-fraction", type=float, default=0.10,
                    help="the busiest share of buckets to measure against "
                         "(default 0.10)")
    ap.add_argument("--show-all", action="store_true",
                    help="also print workloads that are correctly synchronous")
    args = ap.parse_args()

    key = os.environ.get("OPENAI_ADMIN_KEY") or os.environ.get("OPENAI_API_KEY")
    if not key:
        log.error("set OPENAI_ADMIN_KEY (an organization admin key, read-only "
                  "scopes are enough)")
        return 2

    session = requests.Session()
    session.headers.update({"Authorization": "Bearer " + key})

    start = int(time.time()) - args.days * 86400
    usage = list(pages(session, "/organization/usage/completions", {
        "start_time": start,
        "bucket_width": "1h",
        "limit": 168,
        "group_by": ["batch", "project_id", "model"],
    }))
    costs = list(pages(session, "/organization/costs", {
        "start_time": start,
        "bucket_width": "1d",
        "limit": 31,
        "group_by": ["line_item", "project_id"],
    }))

    rows = accumulate(usage)
    if not rows:
        log.info("no completions usage in the last %d day(s) for this "
                 "organization", args.days)
        return 0

    found = 0
    for key_name in sorted(rows):
        row = rows[key_name]
        state, detail = verdict(row, args.min_requests, args.threshold,
                                args.top_fraction)
        line = "%-17s %s  %s" % (state, key_name, detail)
        if state == "batch-shaped":
            found += 1
            log.warning(line)
            spend = sync_cost(costs, row["project_id"])
            worth = saving(spend)
            log.warning("  cost: $%.2f of synchronous spend on project %s over "
                        "%d day(s); about $%.2f of that is the batch discount "
                        "you are not taking", spend, row["project_id"],
                        args.days, worth)
            log.warning("  repair: upload the requests as a .jsonl to /v1/files "
                        "with purpose=batch, create a batch with a 24h "
                        "completion window, and read both result files. The "
                        "trade is half price for no latency guarantee.")
        elif state in ("interactive", "already-batched", "too-little-traffic"):
            if args.show_all:
                log.info(line)
        else:
            log.warning(line)

    log.info("%d workload(s), %d batch shaped", len(rows), found)
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "openai-batch-discount-audit.mjs",
"js": '''/**
 * Report synchronous OpenAI traffic that is shaped like batch work.
 *
 * Read only. Two GET requests against the organization endpoints and nothing
 * else. Those endpoints reject project keys, so this needs an organization
 * admin key (sk-admin-), which can and should be provisioned read-only.
 *
 * This is a cost note, not a failure note. Nothing found here is broken.
 */
const API = 'https://api.openai.com/v1';

// The Batch API is priced at half the synchronous rate on both input and output
// tokens, in exchange for a completion window of up to 24 hours.
const DISCOUNT = 0.50;

/**
 * Fold usage buckets into one row per project and model. Pure. The hourly
 * request counts stay aligned across the whole window, with zeros where a
 * workload was idle: compacting the idle hours out would make every workload
 * look concentrated, which is the thing being measured.
 */
export function accumulate(buckets) {
  const list = buckets ?? [];
  const rows = new Map();
  list.forEach((bucket, index) => {
    for (const result of bucket.results ?? []) {
      const project = String(result.project_id ?? 'unknown');
      const model = String(result.model ?? 'unknown');
      const key = `${project} / ${model}`;
      let row = rows.get(key);
      if (!row) {
        row = {
          key,
          project_id: project,
          model,
          sync_requests: 0,
          batch_requests: 0,
          sync_input: 0,
          sync_output: 0,
          hourly: new Array(list.length).fill(0),
        };
        rows.set(key, row);
      }
      const made = Number(result.num_model_requests ?? 0) || 0;
      if (result.batch === true) {
        row.batch_requests += made;
      } else {
        row.sync_requests += made;
        row.sync_input += Number(result.input_tokens ?? 0) || 0;
        row.sync_output += Number(result.output_tokens ?? 0) || 0;
        row.hourly[index] += made;
      }
    }
  });
  return rows;
}

/**
 * Share of requests inside the busiest slice of the window. Pure. Returns a
 * number between 0 and 1, or null when there is nothing to measure.
 */
export function concentration(hourly, topFraction = 0.10) {
  const counts = (hourly ?? []).map((c) => Number(c) || 0);
  const total = counts.reduce((a, b) => a + b, 0);
  if (counts.length === 0 || total <= 0) return null;
  const top = Math.max(1, Math.ceil(counts.length * topFraction));
  const busiest = [...counts].sort((a, b) => b - a).slice(0, top);
  return busiest.reduce((a, b) => a + b, 0) / total;
}

/**
 * Classify one workload's week. Pure. Returns [state, detail]. "interactive"
 * and "already-batched" are answers rather than failures to detect something:
 * synchronous is correct for traffic with a person waiting on it.
 */
export function verdict(row, minRequests = 1000, threshold = 0.70,
                        topFraction = 0.10) {
  const sync = Number(row.sync_requests ?? 0) || 0;
  const batched = Number(row.batch_requests ?? 0) || 0;
  const total = sync + batched;

  if (total < minRequests) {
    return ['too-little-traffic',
      `${total} request(s) in the window, which is too few to say anything ` +
      'about the shape'];
  }

  const share = sync / total;
  if (share < 0.20) {
    return ['already-batched',
      `${Math.round(100 * (1 - share))}% of ${total} request(s) already go ` +
      'through the Batch API'];
  }

  const spike = concentration(row.hourly, topFraction);
  if (spike === null) {
    return ['unmeasurable',
      `${sync} synchronous request(s) and no per bucket counts to spread them ` +
      'over, so the shape cannot be measured'];
  }

  const pct = Math.round(spike * 100);
  const slice = Math.round(topFraction * 100);
  if (spike >= threshold) {
    return ['batch-shaped',
      `${pct}% of ${sync} synchronous request(s) land in the busiest ` +
      `${slice}% of hours. That is a schedule, not an audience, and it is ` +
      'paying interactive prices.'];
  }
  return ['interactive',
    `${sync} synchronous request(s), ${pct}% of them in the busiest ${slice}% ` +
    'of hours. Spread out like traffic with someone waiting on it, so the ' +
    'synchronous endpoint is the right one.'];
}

/**
 * Non-batch dollars in the cost report, optionally for one project. Pure.
 * Batch and non-batch appear as distinct line_item strings, so the split is a
 * substring test and nothing more clever than that.
 */
export function syncCost(buckets, projectId = null) {
  let total = 0;
  for (const bucket of buckets ?? []) {
    for (const result of bucket.results ?? []) {
      if (projectId && String(result.project_id ?? '') !== projectId) continue;
      if (String(result.line_item ?? '').toLowerCase().includes('batch')) continue;
      total += Number(result.amount?.value ?? 0) || 0;
    }
  }
  return Math.round(total * 100) / 100;
}

/**
 * What the same spend would have been worth at batch prices. Pure. Not a
 * promise: it says nothing about whether the job can accept a 24 hour window.
 */
export function saving(syncCostUsd, discount = DISCOUNT) {
  if (syncCostUsd === null || syncCostUsd === undefined) return null;
  const value = Number(syncCostUsd);
  if (!Number.isFinite(value)) return null;
  return Math.round(Math.max(0, value) * discount * 100) / 100;
}

async function get(key, path, params) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) {
    if (Array.isArray(v)) v.forEach((one) => url.searchParams.append(k, String(one)));
    else if (v !== undefined && v !== null) url.searchParams.set(k, String(v));
  }
  const res = await fetch(url, { headers: { Authorization: `Bearer ${key}` } });
  if (res.status === 401 || res.status === 403) {
    throw new Error(`${res.status} from OpenAI: /v1/organization/* needs an ` +
                    'organization admin key (sk-admin-), not a project key');
  }
  if (!res.ok) throw new Error(`${res.status} from ${path}`);
  return res.json();
}

async function pages(key, path, params, maxPages = 40) {
  const out = [];
  let query = { ...params };
  for (let i = 0; i < maxPages; i += 1) {
    const page = await get(key, path, query);
    out.push(...(page.data ?? []));
    if (!page.has_more || !page.next_page) break;
    query = { ...params, page: page.next_page };
  }
  return out;
}

async function main() {
  const key = process.env.OPENAI_ADMIN_KEY ?? process.env.OPENAI_API_KEY;
  if (!key) {
    console.error('set OPENAI_ADMIN_KEY (an organization admin key, read-only ' +
                  'scopes are enough)');
    process.exitCode = 2;
    return;
  }

  const days = Number(process.env.DAYS ?? 7);
  const minRequests = Number(process.env.MIN_REQUESTS ?? 1000);
  const threshold = Number(process.env.THRESHOLD ?? 0.70);
  const topFraction = Number(process.env.TOP_FRACTION ?? 0.10);
  const showAll = process.argv.includes('--show-all');

  const start = Math.floor(Date.now() / 1000) - days * 86400;
  const usage = await pages(key, '/organization/usage/completions', {
    start_time: start,
    bucket_width: '1h',
    limit: 168,
    group_by: ['batch', 'project_id', 'model'],
  });
  const costs = await pages(key, '/organization/costs', {
    start_time: start,
    bucket_width: '1d',
    limit: 31,
    group_by: ['line_item', 'project_id'],
  });

  const rows = accumulate(usage);
  if (rows.size === 0) {
    console.log(`no completions usage in the last ${days} day(s) for this ` +
                'organization');
    return;
  }

  let found = 0;
  for (const name of [...rows.keys()].sort()) {
    const row = rows.get(name);
    const [state, detail] = verdict(row, minRequests, threshold, topFraction);
    const line = `${state.padEnd(17)} ${name}  ${detail}`;
    if (state === 'batch-shaped') {
      found += 1;
      console.warn(line);
      const spend = syncCost(costs, row.project_id);
      console.warn(`  cost: $${spend.toFixed(2)} of synchronous spend on ` +
        `project ${row.project_id} over ${days} day(s); about ` +
        `$${saving(spend).toFixed(2)} of that is the batch discount you are ` +
        'not taking');
      console.warn('  repair: upload the requests as a .jsonl to /v1/files ' +
        'with purpose=batch, create a batch with a 24h completion window, and ' +
        'read both result files. The trade is half price for no latency ' +
        'guarantee.');
    } else if (['interactive', 'already-batched', 'too-little-traffic'].includes(state)) {
      if (showAll) console.log(line);
    } else {
      console.warn(line);
    }
  }

  console.log(`${rows.size} workload(s), ${found} batch shaped`);
  process.exitCode = found ? 1 : 0;
}

// Only run when invoked directly, so importing this module from the test file
// does not fire main() and fail on the missing key.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "No clock in these tests, because the finding is a shape rather than a moment. What they pin down instead is that idle hours are counted: a workload with one busy hour and nineteen empty ones is only concentrated if the empty ones are in the denominator, and an accumulator that drops them turns every workload into a finding. The rest hold apart the three answers that are not findings &mdash; already batched, genuinely interactive, and too small to judge.",
"test_py_file": "test_openai_batch_discount_audit.py",
"test_py": '''from openai_batch_discount_audit import (accumulate, concentration, saving,
                                           sync_cost, verdict)


def bucket(*results):
    return {"start_time": 0, "end_time": 3600, "results": list(results)}


def result(project="proj_a", model="gpt-5.6-terra", batch=False, made=0,
           input_tokens=0, output_tokens=0):
    return {"project_id": project, "model": model, "batch": batch,
            "num_model_requests": made, "input_tokens": input_tokens,
            "output_tokens": output_tokens}


def test_idle_hours_stay_in_the_denominator():
    # Four buckets, one of them busy. If the empty hours were dropped the
    # workload would look perfectly flat instead of perfectly spiky.
    buckets = [bucket(result(made=0)), bucket(result(made=4000)),
               bucket(), bucket(result(made=0))]
    rows = accumulate(buckets)
    row = rows["proj_a / gpt-5.6-terra"]
    assert row["hourly"] == [0, 4000, 0, 0]
    assert row["sync_requests"] == 4000


def test_batch_and_synchronous_traffic_are_kept_apart():
    rows = accumulate([bucket(result(made=100, input_tokens=50, batch=False),
                              result(made=900, batch=True))])
    row = rows["proj_a / gpt-5.6-terra"]
    assert row["sync_requests"] == 100
    assert row["batch_requests"] == 900
    assert row["sync_input"] == 50
    assert row["hourly"] == [100]


def test_concentration_separates_a_schedule_from_an_audience():
    spiky = [0] * 18 + [4000, 1000]
    assert concentration(spiky, 0.10) == 1.0
    assert concentration([250] * 20, 0.10) == 0.1
    assert concentration([], 0.10) is None
    assert concentration([0, 0, 0], 0.10) is None


def test_a_nightly_job_on_the_synchronous_endpoint_is_the_finding():
    row = {"sync_requests": 5000, "batch_requests": 0,
           "hourly": [0] * 18 + [4000, 1000]}
    state, detail = verdict(row)
    assert state == "batch-shaped"
    assert "100% of 5000 synchronous request(s)" in detail
    assert "paying interactive prices" in detail


def test_spread_out_traffic_is_correctly_synchronous():
    row = {"sync_requests": 5000, "batch_requests": 0, "hourly": [250] * 20}
    state, detail = verdict(row)
    assert state == "interactive"
    assert "right one" in detail


def test_the_three_answers_that_are_not_findings():
    assert verdict({"sync_requests": 10, "batch_requests": 0,
                    "hourly": [10]})[0] == "too-little-traffic"
    assert verdict({"sync_requests": 100, "batch_requests": 9900,
                    "hourly": [100]})[0] == "already-batched"
    assert verdict({"sync_requests": 5000, "batch_requests": 0,
                    "hourly": []})[0] == "unmeasurable"


def test_the_money_comes_from_the_cost_report_not_a_price_table():
    costs = [{"results": [
        {"project_id": "proj_a", "line_item": "gpt-5.6-terra, input",
         "amount": {"value": 300.0, "currency": "usd"}},
        {"project_id": "proj_a", "line_item": "gpt-5.6-terra, batch input",
         "amount": {"value": 40.0, "currency": "usd"}},
        {"project_id": "proj_b", "line_item": "gpt-5.6-terra, input",
         "amount": {"value": 99.0, "currency": "usd"}},
    ]}]
    assert sync_cost(costs, "proj_a") == 300.0
    assert sync_cost(costs) == 399.0
    assert saving(300.0) == 150.0
    assert saving(0) == 0.0
    assert saving(None) is None
''',
"test_js_file": "openai-batch-discount-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { accumulate, concentration, saving, syncCost, verdict }
  from './openai-batch-discount-audit.mjs';

function bucket(...results) {
  return { start_time: 0, end_time: 3600, results };
}

function result({ project = 'proj_a', model = 'gpt-5.6-terra', batch = false,
                  made = 0, inputTokens = 0, outputTokens = 0 } = {}) {
  return {
    project_id: project,
    model,
    batch,
    num_model_requests: made,
    input_tokens: inputTokens,
    output_tokens: outputTokens,
  };
}

test('idle hours stay in the denominator', () => {
  const buckets = [bucket(result({ made: 0 })), bucket(result({ made: 4000 })),
                   bucket(), bucket(result({ made: 0 }))];
  const row = accumulate(buckets).get('proj_a / gpt-5.6-terra');
  assert.deepEqual(row.hourly, [0, 4000, 0, 0]);
  assert.equal(row.sync_requests, 4000);
});

test('batch and synchronous traffic are kept apart', () => {
  const rows = accumulate([bucket(
    result({ made: 100, inputTokens: 50, batch: false }),
    result({ made: 900, batch: true }))]);
  const row = rows.get('proj_a / gpt-5.6-terra');
  assert.equal(row.sync_requests, 100);
  assert.equal(row.batch_requests, 900);
  assert.equal(row.sync_input, 50);
  assert.deepEqual(row.hourly, [100]);
});

test('concentration separates a schedule from an audience', () => {
  const spiky = [...new Array(18).fill(0), 4000, 1000];
  assert.equal(concentration(spiky, 0.10), 1.0);
  assert.equal(concentration(new Array(20).fill(250), 0.10), 0.1);
  assert.equal(concentration([], 0.10), null);
  assert.equal(concentration([0, 0, 0], 0.10), null);
});

test('a nightly job on the synchronous endpoint is the finding', () => {
  const row = { sync_requests: 5000, batch_requests: 0,
                hourly: [...new Array(18).fill(0), 4000, 1000] };
  const [state, detail] = verdict(row);
  assert.equal(state, 'batch-shaped');
  assert.match(detail, /100% of 5000 synchronous request\\(s\\)/);
  assert.match(detail, /paying interactive prices/);
});

test('spread out traffic is correctly synchronous', () => {
  const row = { sync_requests: 5000, batch_requests: 0,
                hourly: new Array(20).fill(250) };
  const [state, detail] = verdict(row);
  assert.equal(state, 'interactive');
  assert.match(detail, /right one/);
});

test('the three answers that are not findings', () => {
  assert.equal(verdict({ sync_requests: 10, batch_requests: 0, hourly: [10] })[0],
               'too-little-traffic');
  assert.equal(verdict({ sync_requests: 100, batch_requests: 9900, hourly: [100] })[0],
               'already-batched');
  assert.equal(verdict({ sync_requests: 5000, batch_requests: 0, hourly: [] })[0],
               'unmeasurable');
});

test('the money comes from the cost report not a price table', () => {
  const costs = [{ results: [
    { project_id: 'proj_a', line_item: 'gpt-5.6-terra, input',
      amount: { value: 300.0, currency: 'usd' } },
    { project_id: 'proj_a', line_item: 'gpt-5.6-terra, batch input',
      amount: { value: 40.0, currency: 'usd' } },
    { project_id: 'proj_b', line_item: 'gpt-5.6-terra, input',
      amount: { value: 99.0, currency: 'usd' } },
  ] }];
  assert.equal(syncCost(costs, 'proj_a'), 300.0);
  assert.equal(syncCost(costs), 399.0);
  assert.equal(saving(300.0), 150.0);
  assert.equal(saving(0), 0);
  assert.equal(saving(null), null);
});
''',
"faq": [
 ("Is this a bug, exactly?",
  "No, and the note is written that way on purpose. Nothing failed, no row is missing and no alert should have fired. It is a cost finding: work with nobody waiting on it is being billed at the price of work with somebody waiting on it. The other three notes in this cluster are failures; this one is an invoice."),
 ("How much cheaper is the Batch API?",
  "Half, on both input and output tokens, in exchange for a completion window of up to 24 hours and no latency guarantee. Prompt caching and batch are separate discounts on different axes, so a job can take both: cache the stable prefix and submit the requests as a batch."),
 ("How do I know a clustered job could actually wait?",
  "You do not, from the API. Concentration proves the traffic is scheduled rather than interactive, which is a necessary condition and not a sufficient one. A backfill can usually wait a day; a job that feeds a dashboard by 09:00 might have four hours, not twenty-four. The script reports what is eligible by shape and leaves the schedule question to you."),
 ("Why hourly buckets rather than the daily ones?",
  "Because the whole detection is the shape within a day. Daily buckets flatten a twenty-minute spike and a twenty-four-hour plateau into the same number. With bucket_width=1h and limit=168 you get a week of hours in one call, which is enough resolution to see a cron job and cheap enough to run weekly."),
 ("Does the same check work on Anthropic?",
  "Only in a blunter form. Claude's Message Batches API carries the same 50% discount, but the messages usage report returns token sums per bucket with no request-count field at all, so you cannot measure request concentration on that side — you would have to infer the shape from input tokens per hour, which mixes traffic volume with prompt size and is a weaker signal."),
],
"related": [REL_PARTIAL, REL_EXPIRED, REL_OUTPUT_COST],
"citations": [CITE_USAGE_COMPLETIONS, CITE_COSTS, CITE_BATCH_REF, CITE_BATCH_GUIDE],
},

]
