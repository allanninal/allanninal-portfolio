#!/usr/bin/env python3
"""/llm/ field notes, batch W — the writing.

Five terminal states of an asynchronous job that no exception announces. The
section already publishes four batch notes, so the hazard here is obvious: five
more scripts that all list `/v1/batches` and all conclude "somebody should have
looked". Each of these five reads a different field on a different object and
reaches a conclusion the other four cannot.

`batch-failed-input-validation` owns a job that **never started**. `status` is
`failed`, which on this API means one thing only: the input file did not survive
validation. Nothing reached the model, `request_counts` is all zeros, and
nothing was billed. The finding is `errors.data[]`, where each entry carries a
`code`, a `param` and the `line` number of the row that stopped it. Its second
half is the input file that can never be used at all, because `/v1/batches`
accepts only a file whose `purpose` is exactly `batch` and rejects the rest at
creation, so no batch object is ever made and the evidence lives in the file
list instead. Read it against the published `batch-partial-failure-unnoticed`,
which is arithmetic on `request_counts` for a batch that ran: this one is the
batch that has no counts to do arithmetic on.

`batch-cancelled-partial-results` owns a **cancel clock**. Cancellation is not a
rollback and it is not instantaneous: OpenAI holds the batch in `cancelling` for
up to ten minutes, Anthropic holds it in `canceling` until the in-flight
requests drain, and on both providers the requests that finished before the
cancel landed are billed and written to the output. Anthropic states the other
half outright, that canceled and expired requests are not billed. So a cancelled
batch is a bill plus a partial result set, and the expensive mistake is to
re-run the whole thing. No other note in the section reads `cancelling_at` or
`cancel_initiated_at`.

`background-response-never-polled` is not about batches at all. The Responses
API in background mode returns a 200 the instant the job is accepted and puts
the result nowhere except on the response object, whose `status` enum has six
values of which four are not success. There is no list endpoint for
`/v1/responses`, so the script is bounded by the ids you kept, and it says so.
It also has to separate a genuinely lost job from a 404 that is simply the
platform behaving as documented, because on a zero-data-retention project a
background response is stored for roughly ten minutes and then is gone by
design.

`batch-output-file-never-downloaded` is the mirror of the published
`batch-error-file-never-read`, and the pair has to be told apart in the prose
rather than left to the reader. That note reads `error_file_id`: the list of
rows that failed, whose loss costs you the knowledge of which rows are missing.
This one reads `output_file_id`: the work itself, whose loss costs you the work.
Same ledger join, opposite finding. It also absorbs three slugs that were
separate entries in the research and are states inside one script here: a batch
created and never polled, results never fetched, and a batch that ended and was
never claimed. Those are three verdicts, not three notes.

`batch-queue-limit-reached` is the only one of the five with nothing terminal in
it. Every batch it reads is alive and healthy. The finding is that the org's
`enqueued_batch_requests` ceiling is close, which means the next submission is
refused rather than failed, and the refusal happens somewhere else entirely.
It is also the only note in the batch that needs both an Admin key and a
workspace key, because the ceiling is org-wide and the batch list is
workspace-scoped, and the script is explicit that one workspace's depth is a
lower bound on the org's.

Read only throughout, and more strictly than usual: there is not a single
non-GET request anywhere in this batch. Cancelling a batch, submitting one, and
starting a background response all cost money or destroy work, so none of these
scripts does any of them. Every repair is printed for a human to run.
"""

CITE_OAI_BATCH_REF = ("Batch — OpenAI API reference",
                      "https://developers.openai.com/api/docs/api-reference/batch")
CITE_OAI_BATCH_GUIDE = ("Batch API guide — OpenAI developer docs",
                        "https://developers.openai.com/api/docs/guides/batch")
CITE_OAI_FILES = ("Files — OpenAI API reference",
                  "https://developers.openai.com/api/docs/api-reference/files")
CITE_OAI_ERRORS = ("Error codes — OpenAI platform docs",
                   "https://developers.openai.com/api/docs/guides/error-codes")
CITE_OAI_RESP = ("Responses — OpenAI API reference",
                 "https://developers.openai.com/api/docs/api-reference/responses")
CITE_OAI_BG = ("Background mode — OpenAI developer docs",
               "https://developers.openai.com/api/docs/guides/background")
CITE_OAI_STATE = ("Conversation state and stored response retention",
                  "https://developers.openai.com/api/docs/guides/conversation-state")

CITE_AN_BATCH_GUIDE = ("Batch processing — Claude platform docs",
                       "https://platform.claude.com/docs/en/build-with-claude/batch-processing")
CITE_AN_BATCH_LIST = ("List Message Batches — Claude API reference",
                      "https://platform.claude.com/docs/en/api/messages/batches/list")
CITE_AN_RATE_LIMITS = ("Rate limits, including the Message Batches API limits",
                       "https://platform.claude.com/docs/en/api/rate-limits")
CITE_AN_RL_API = ("Rate Limits API — Claude platform docs",
                  "https://platform.claude.com/docs/en/manage-claude/rate-limits-api")

REL_PARTIAL = ("/llm/batch-partial-failure-unnoticed/",
               "A batch that ran, reads completed, and has failed rows inside it")
REL_ERRFILE = ("/llm/batch-error-file-never-read/",
               "The other half of the same completion handler: the failures, written down and unread")
REL_EXPIRED = ("/llm/batch-expired-past-24h-window/",
               "The clock that closes on a batch before it finishes")
REL_DISCOUNT = ("/llm/batch-discount-left-unused/",
                "Why the work was worth batching in the first place")
REL_CHAIN = ("/llm/previous-response-id-chain-broken/",
             "Another stored response object with a retention clock on it")
REL_TRUNC = ("/llm/structured-output-truncated-by-length/",
             "Reading incomplete_details on a response that came back 200")
REL_LIMITER = ("/llm/rate-limit-429-limiter-unidentified/",
               "Which limiter emptied when the 429 was on the synchronous path")
REL_PROJRL = ("/llm/project-rate-limit-below-org/",
              "The workspace override sitting under the organization ceiling")

REL_VALIDATION = ("/llm/batch-failed-input-validation/",
                  "The batch that never started, and the line number that stopped it")
REL_CANCELLED = ("/llm/batch-cancelled-partial-results/",
                 "Billed rows a cancel left behind, and cancels stuck mid-flight")
REL_OUTPUT = ("/llm/batch-output-file-never-downloaded/",
              "Work you paid for and never collected, on both providers")
REL_QUEUE = ("/llm/batch-queue-limit-reached/",
             "Live queue depth against the ceiling that refuses the next submission")
REL_BACKGROUND = ("/llm/background-response-never-polled/",
                  "The same abandonment on the Responses API instead of a batch")

GUIDES = [
{
"slug": "batch-failed-input-validation",
"title": "The batch failed validation and named the broken line",
"description": "A batch that reads failed never reached the model. errors.data[] carries the code, the param and the line number of the input .jsonl it stopped on.",
"h1": "The batch failed validation and named the broken line",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["openai batch status failed errors data line",
             "openai batch validation error duplicate custom_id",
             "batch input file purpose must be batch",
             "openai batch failed request_counts zero",
             "openai batch invalid_request_error line number"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Reads OPENAI_API_KEY, a project key set to Read Only. Two GET endpoints and nothing else: /v1/batches and /v1/files. Nothing is created, uploaded or re-submitted.",
"lead": "The submitter returned 200 and the run log says the nightly enrichment fired. Sixteen hours later the enrichment table is exactly as long as it was yesterday. There was no exception, no alert and no retry, because from the client's point of view nothing went wrong: the batch was accepted. It failed forty seconds later, in a state your code never looks at, and it has been holding a list of line numbers ever since.",
"short_answer": """<p><code>GET /v1/batches?limit=100</code> with a <strong>project key set to Read Only</strong>, paginate on <code>after</code>, and keep every object where <code>status</code> is <code>failed</code>. On the Batch API that status means one thing: the input file did not survive validation. The batch never reached the model.</p>
<p>The detail is in <code>errors</code>, which is a list object whose <code>data[]</code> entries carry <code>code</code>, <code>message</code>, <code>param</code> and <code>line</code> &mdash; and <code>line</code> is documented as the line number of the input file where the error occurred. That is a pointer straight into the <code>.jsonl</code> you uploaded. Group the entries by <code>code</code> and print the line numbers under each one.</p>
<p>Confirm nothing was billed while you are there. A failed batch has <code>request_counts</code> of <code>{total: 0, completed: 0, failed: 0}</code>, because validation happens before any request is dispatched. That is the reassuring half of the finding and it is worth printing, since the first question anybody asks is whether this cost money.</p>
<p>Then read the file list for the failure that leaves no batch behind. <code>/v1/batches</code> accepts only an input file whose <code>purpose</code> is exactly <code>batch</code>. A <code>.jsonl</code> uploaded under <code>user_data</code>, <code>assistants</code>, <code>fine-tune</code> or <code>vision</code> is refused at creation, so there is no batch object to find and no <code>errors</code> array to read. <code>GET /v1/files</code> shows it sitting there, taking up storage, referenced by nothing.</p>""",
"problem": """<p><code>POST /v1/batches</code> returning 200 means the batch object was created. It does not mean the batch will run, and the two are separated by a validation pass that reads every line of your input file. A malformed JSON line, a missing <code>custom_id</code>, a duplicate <code>custom_id</code>, a per-line <code>url</code> that does not match the batch's <code>endpoint</code>, or a body naming a model this project cannot reach will fail the entire batch. Not the line. The batch.</p>
<p>So the failure arrives after the caller has gone. A submitter that fires and forgets sees a 200, writes a success line to its log and exits. The batch enters <code>validating</code>, leaves it for <code>failed</code> within a minute or two, and stays there. Nothing calls back. There is no webhook in the default flow and no exception to catch, and the batch object will still be sitting in the list a week later holding the exact reason and the exact line.</p>
<p>What makes this expensive is not the failed batch, which cost nothing. It is that the downstream table is simply not updated, and a table that is not updated looks identical to a table that had no new rows. Nightly enrichment that quietly stops enriching is discovered by a person noticing a stale timestamp, and the median time for that is measured in weeks.</p>
<p>The wrong-<code>purpose</code> input file is the same failure one step earlier and it is harder to see, because it never produces a batch at all. The Files API namespaces uploads by purpose, and a shared upload helper with a hard-coded default happily accepts your batch input as <code>user_data</code>. The upload succeeds. The file appears in <code>GET /v1/files</code> with a sensible filename and a byte count. It can never be used as batch input, and it counts against project storage forever.</p>""",
"why": """<p><strong><code>failed</code> on this API is a specific claim, not a general one.</strong> The status enum is <code>validating</code>, <code>failed</code>, <code>in_progress</code>, <code>finalizing</code>, <code>completed</code>, <code>expired</code>, <code>cancelling</code>, <code>cancelled</code>. A batch whose requests failed individually does not land on <code>failed</code>; it lands on <code>completed</code> with a non-zero <code>request_counts.failed</code>, which is a different note. <code>failed</code> means the input file was rejected as a whole. That is why this script does no arithmetic on counts at all: on a failed batch there are none to do.</p>
<p><strong>The <code>line</code> field is the entire value of the reading.</strong> An error object with a <code>code</code> and a <code>message</code> tells you what kind of thing is wrong. <code>line</code> tells you where, in a file that might be two hundred thousand rows long, and it is documented exactly that way: the line number of the input file where the error occurred, if applicable. Grouping by <code>code</code> and listing the lines under each turns a wall of repeated messages into a short repair list.</p>
<p><strong>Nothing was billed, and saying so is part of the output.</strong> Validation runs before any request is dispatched to the model, so a failed batch has an all-zero <code>request_counts</code> and no <code>usage</code> worth reading. A finding that does not answer "did this cost us anything" gets escalated as a cost incident by somebody who does not know, which wastes more time than the bug did.</p>
<p><strong>The batch list cannot be filtered server-side, so the script pages and filters locally.</strong> <code>GET /v1/batches</code> takes exactly two query parameters, <code>limit</code> (1 to 100, default 20) and <code>after</code>. There is no <code>status</code> filter and no date range. A run that reads only the default first page will miss every failure older than the last twenty submissions, which on a nightly pipeline is three weeks.</p>
<p><strong>The wrong-purpose file is invisible from the batch side by construction.</strong> Because the creation call is rejected outright, no batch object exists to carry the error. The only read-only evidence is a file whose purpose is not <code>batch</code>, whose name looks like batch input, and whose id is not the <code>input_file_id</code> of any batch you have. All three conditions are needed: without the last one the check would flag every input file you ever used successfully.</p>""",
"steps": [
 {"h": "Use a project key set to Read Only",
  "body": """<p>Both calls are GETs on project-scoped data, so no admin key is involved. The script never uploads a file, never creates a batch and never re-submits a failed one. Re-submitting spends money on inference, and only you know whether the rows are still wanted.</p>"""},
 {"h": "Page the whole batch list",
  "body": """<p><code>GET /v1/batches?limit=100</code>, then follow <code>after</code> with the last id until <code>has_more</code> is false. There is no server-side status filter, so the filtering happens on your side. Use <code>--max-pages</code> to bound a very long history, and know that bounding it means the answer is bounded too.</p>"""},
 {"h": "Group the errors by code and print the lines",
  "body": """<p>For every <code>failed</code> batch, read <code>errors.data[]</code>. Each entry gives you <code>code</code>, <code>message</code>, <code>param</code> and <code>line</code>. The script prints one row per code with the offending line numbers listed under it, truncated with a count when there are many, because a hundred identical messages is not more informative than one with a hundred line numbers.</p>"""},
 {"h": "Check the input files that never became a batch",
  "body": """<p><code>GET /v1/files</code>, paginate on <code>after</code>, and flag any <code>.jsonl</code> whose <code>purpose</code> is one of <code>user_data</code>, <code>assistants</code>, <code>fine-tune</code> or <code>vision</code> and whose id is not the <code>input_file_id</code> of any batch in the list. That is a file uploaded for a batch that was refused at creation.</p>"""},
 {"h": "Fix the file, then re-create the batch yourself",
  "body": """<p>The repair is printed, never run. Correct the input at the reported lines, re-upload with <code>purpose</code> set to <code>batch</code>, and create the batch again. Then make the pipeline poll: a 200 from creation is a receipt, and the only honest success signal is a batch that has left <code>validating</code>.</p>"""},
],
"verify": """<p>Re-run after the input is fixed and the batch is re-created. The old failed batches do not disappear &mdash; batch objects persist &mdash; so pass <code>--since-days</code> to scope the run to the window you care about, and expect the count of failures inside that window to go to zero. The check worth keeping is the assertion in the submitter, not this script.</p>
<pre><code class="language-bash">python3 openai_batch_validation_audit.py --since-days 30
# batch_68f2a1c9  failed at 2026-08-27T02:14:09Z  nothing billed (0 requests)
#   invalid_json               lines 41207, 41208, 41209 and 6 more
#   duplicate_custom_id        lines 903, 41207
# batch_68e0b7d4  failed at 2026-08-19T02:13:51Z  nothing billed (0 requests)
#   model_not_found            line 1   param body.model
# orphan-input    file_9de2  nightly-enrich.jsonl  purpose=user_data  1.4 MB
# validation-failed    2 batch(es) failed input validation in the last 30 days
#                      and 1 .jsonl was uploaded under a purpose /v1/batches
#                      will not accept
#   measured: status, errors.data[] and request_counts from the batch list,
#             purpose from the file list
#   inferred: that the pipeline never polled, since a failed batch is otherwise
#             indistinguishable from one nobody re-ran on purpose
#   repair: fix the input at the reported lines, then re-upload with
#           purpose=batch and create the batch again. Assert that status has
#           left "validating" before the submitter logs success.
# 3 finding(s)</code></pre>""",
"code_intro": "Two paged GETs and seven pure functions. <code>failed_batches</code>, which is the whole server-side filter the API does not offer; <code>error_rows</code>, which normalises <code>errors.data[]</code> and survives the object being absent, empty or a shape nobody expected; <code>lines_by_code</code>, which groups and sorts so a hundred identical messages become one row with a hundred line numbers; <code>nothing_billed</code>, which reads <code>request_counts</code> and answers the first question anyone asks; <code>batch_input_ids</code>, which collects every <code>input_file_id</code> in the account so a file that <em>was</em> used is never flagged; <code>mispurposed_inputs</code>, which needs all three conditions to fire; and <code>verdict</code>, which keeps the two halves separate because they have different repairs.",
"py_file": "openai_batch_validation_audit.py",
"py": '''"""Report OpenAI batches that failed input validation, and the lines that broke.

Read only. Two GET endpoints, /v1/batches and /v1/files, and nothing else. No
file is uploaded, no batch is created, and no failed batch is re-submitted:
re-running rows spends money on inference and only you know whether the rows
are still wanted.

On the Batch API, status "failed" is a specific claim. It means the input file
did not survive validation, which happens before any request reaches the model.
So request_counts is all zeros and nothing was billed. Individual requests that
failed inside a batch that ran are a different status and a different note.

The second half reads the file list, because an input file uploaded under the
wrong purpose is rejected at creation and never becomes a batch object at all.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("openai_batch_validation_audit")

BATCHES_URL = "https://api.openai.com/v1/batches"
FILES_URL = "https://api.openai.com/v1/files"

# The batch list takes limit (1-100) and after. There is no status filter and no
# date range, so every bit of selection below happens on this side of the wire.
PAGE = 100

# Purposes the Files API namespaces separately from batch input. A .jsonl parked
# under one of these was uploaded for a batch that /v1/batches refused, since it
# accepts an input file only when purpose is exactly "batch".
NOT_BATCH_INPUT = ("user_data", "assistants", "fine-tune", "vision")

# Error codes the docs and the endpoint's own validation produce often enough to
# be worth a specific repair line rather than the generic one.
KNOWN_CODES = {
    "invalid_json": "a line is not valid JSON. Validate the file locally before "
                    "upload: every line must parse on its own.",
    "duplicate_custom_id": "two lines share a custom_id. They must be unique "
                           "within the file, because results come back unordered "
                           "and custom_id is the only join key.",
    "missing_required_parameter": "a line is missing a required field. Each row "
                                  "needs custom_id, method, url and body.",
    "invalid_url": "a line's url does not match the batch endpoint. The two must "
                   "agree for every row in the file.",
    "model_not_found": "the body names a model this project cannot reach. Check "
                       "the id against GET /v1/models with the same key.",
    "empty_file": "the input file has no lines in it. The upload succeeded and "
                  "the content did not.",
}

FINDINGS = ("validation-failed", "orphan-input-files")


def failed_batches(batches):
    """Batches whose input file was rejected. Pure.

    The only status that means "validation refused this file". A batch that ran
    and had rows fail inside it reports completed with a non-zero
    request_counts.failed, which this script deliberately does not look at.
    """
    return [b for b in batches or [] if (b or {}).get("status") == "failed"]


def error_rows(batch):
    """Normalised entries from errors.data[]. Pure. Never raises on a shape.

    errors is optional, its data list is optional, and an entry's line is
    documented as "if applicable", so every field here is allowed to be absent.
    """
    errors = (batch or {}).get("errors") or {}
    data = errors.get("data") if isinstance(errors, dict) else None
    out = []
    for item in data or []:
        if not isinstance(item, dict):
            continue
        line = item.get("line")
        try:
            line = int(line)
        except (TypeError, ValueError):
            line = None
        out.append({"code": str(item.get("code") or "unknown"),
                    "message": str(item.get("message") or ""),
                    "param": item.get("param"),
                    "line": line})
    return out


def lines_by_code(rows):
    """{code: (sorted lines, count, one message, one param)}. Pure.

    A file with 40,000 bad rows produces 40,000 near-identical messages. One row
    per code carrying the line numbers is the same information and is readable.
    """
    grouped = {}
    for row in rows or []:
        slot = grouped.setdefault(row["code"], {"lines": set(), "count": 0,
                                                "message": "", "param": None})
        slot["count"] += 1
        if row.get("line") is not None:
            slot["lines"].add(row["line"])
        if not slot["message"]:
            slot["message"] = row.get("message") or ""
        if slot["param"] is None:
            slot["param"] = row.get("param")
    return {code: (sorted(v["lines"]), v["count"], v["message"], v["param"])
            for code, v in sorted(grouped.items())}


def nothing_billed(batch):
    """True when the batch dispatched no requests at all. Pure.

    Validation runs before dispatch, so a failed batch has an all-zero
    request_counts. An absent counts object is treated as zero, which is what a
    batch that never started actually looks like.
    """
    counts = (batch or {}).get("request_counts") or {}
    try:
        return all(int(counts.get(k) or 0) == 0
                   for k in ("total", "completed", "failed"))
    except (TypeError, ValueError):
        return False


def batch_input_ids(batches):
    """Every input_file_id the account has ever handed to a batch. Pure."""
    return {str(b.get("input_file_id")) for b in batches or []
            if (b or {}).get("input_file_id")}


def mispurposed_inputs(files, used_ids):
    """.jsonl files that can never be batch input and never were. Pure.

    All three conditions matter. Drop the last one and every input file you ever
    used successfully gets flagged, which is how a check gets switched off.
    """
    out = []
    for f in files or []:
        if not isinstance(f, dict):
            continue
        name = str(f.get("filename") or "")
        purpose = str(f.get("purpose") or "")
        if not name.lower().endswith(".jsonl"):
            continue
        if purpose not in NOT_BATCH_INPUT:
            continue
        if str(f.get("id")) in (used_ids or set()):
            continue
        out.append({"id": str(f.get("id")), "filename": name,
                    "purpose": purpose, "bytes": int(f.get("bytes") or 0)})
    return sorted(out, key=lambda r: r["id"])


def within_window(batch, now, days):
    """True when the batch was created inside the window. Pure. days<=0 is all."""
    if not days or days <= 0:
        return True
    try:
        created = int((batch or {}).get("created_at") or 0)
    except (TypeError, ValueError):
        return False
    return created >= now - days * 86400


def verdict(failed, orphans, days):
    """Grade the run. Pure. Returns (state, detail)."""
    failed = list(failed or [])
    orphans = list(orphans or [])
    window = ("in the last %d days" % days) if days and days > 0 else "in the account"
    if failed and orphans:
        return ("validation-failed",
                "%d batch(es) failed input validation %s, and %d .jsonl was "
                "uploaded under a purpose /v1/batches will not accept"
                % (len(failed), window, len(orphans)))
    if failed:
        return ("validation-failed",
                "%d batch(es) failed input validation %s and nothing polled "
                "them to find out" % (len(failed), window))
    if orphans:
        return ("orphan-input-files",
                "%d .jsonl file(s) sit under a purpose /v1/batches will not "
                "accept, referenced by no batch" % len(orphans))
    return ("validation-clean",
            "no batch %s failed validation, and every .jsonl in the file list "
            "either carries purpose=batch or was used by a batch" % window)


def repair_lines(state, codes):
    """The repair for one verdict. Pure. Printed, never performed."""
    if state == "validation-clean":
        return ["nothing to change. Keep the assertion that a submitter only "
                "logs success once status has left \\"validating\\"."]
    lines = []
    for code in sorted(set(codes or [])):
        if code in KNOWN_CODES:
            lines.append("%s: %s" % (code, KNOWN_CODES[code]))
    if state == "validation-failed":
        lines.append("fix the input at the reported lines, then re-upload with "
                     "purpose=batch and create the batch again. Nothing was "
                     "billed, so nothing needs reconciling.")
        lines.append("make the submitter poll. A 200 from batch creation is a "
                     "receipt, not a result: the only honest success signal is "
                     "a batch that has left \\"validating\\".")
    if state == "orphan-input-files":
        lines.append("re-upload each file with purpose=batch and delete the "
                     "mis-purposed copy, which counts against project storage "
                     "until you do.")
        lines.append("assert in the upload helper that the purpose matches the "
                     "endpoint that will consume the file.")
    return lines


def get_json(url, key, params=None, timeout=30):
    """One GET. Returns (payload, error). Read only, always."""
    try:
        r = requests.get(url, headers={"Authorization": "Bearer %s" % key},
                         params=params or {}, timeout=timeout)
    except requests.RequestException as exc:
        return (None, "request failed: %s" % exc)
    if r.status_code != 200:
        detail = ""
        try:
            detail = str((r.json().get("error") or {}).get("message") or "")
        except ValueError:
            detail = (r.text or "")[:160]
        return (None, "HTTP %d %s" % (r.status_code, detail))
    try:
        return (r.json(), None)
    except ValueError:
        return (None, "response was not JSON")


def page_all(url, key, params, max_pages):
    """Follow the after cursor. Returns (rows, error). GETs only."""
    rows = []
    after = None
    for _ in range(max(1, max_pages)):
        query = dict(params or {})
        if after:
            query["after"] = after
        payload, err = get_json(url, key, query)
        if err:
            return (rows, err)
        data = payload.get("data") or []
        rows.extend(data)
        if not payload.get("has_more") or not data:
            break
        after = data[-1].get("id")
        if not after:
            break
    return (rows, None)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--since-days", type=int, default=30,
                    help="only report batches created inside this window (0 = all)")
    ap.add_argument("--max-pages", type=int, default=20,
                    help="cap on pages of 100 for each list; a bounded read "
                         "gives a bounded answer and the output says so")
    args = ap.parse_args()

    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        log.error("set OPENAI_API_KEY to a project key set to Read Only")
        return 2

    now = int(time.time())
    batches, err = page_all(BATCHES_URL, key, {"limit": PAGE}, args.max_pages)
    if err and not batches:
        log.error("could not read the batch list: %s", err)
        return 2
    if err:
        log.warning("batch list stopped early: %s", err)

    scoped = [b for b in batches if within_window(b, now, args.since_days)]
    failed = failed_batches(scoped)
    seen_codes = []
    for b in failed:
        billed = "nothing billed (0 requests)" if nothing_billed(b) \\
            else "request_counts is not all zero, which is unusual for failed"
        stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ",
                              time.gmtime(int(b.get("failed_at")
                                              or b.get("created_at") or 0)))
        log.warning("%-16s failed at %s  %s", b.get("id"), stamp, billed)
        groups = lines_by_code(error_rows(b))
        if not groups:
            log.warning("  (the errors object is empty, so the reason is not "
                        "readable from the API)")
        for code, (lines, count, message, param) in groups.items():
            seen_codes.append(code)
            shown = ", ".join(str(n) for n in lines[:6])
            more = " and %d more" % (len(lines) - 6) if len(lines) > 6 else ""
            where = ("lines %s%s" % (shown, more)) if lines else "no line given"
            extra = "  param %s" % param if param else ""
            log.warning("  %-26s %s%s", code, where, extra)
            if message:
                log.info("  %-26s %s", "", message[:140])

    files, ferr = page_all(FILES_URL, key, {"limit": 10000}, args.max_pages)
    if ferr:
        log.warning("file list stopped early: %s", ferr)
    orphans = mispurposed_inputs(files, batch_input_ids(batches))
    for row in orphans:
        log.warning("orphan-input    %s  %s  purpose=%s  %.1f MB", row["id"],
                    row["filename"], row["purpose"], row["bytes"] / 1048576.0)

    state, detail = verdict(failed, orphans, args.since_days)
    emit = log.warning if state in FINDINGS else log.info
    emit("%-20s %s", state, detail)
    emit("  measured: status, errors.data[] and request_counts from the batch "
         "list, purpose from the file list")
    emit("  inferred: that the pipeline never polled, since a failed batch is "
         "otherwise indistinguishable from one nobody re-ran on purpose")
    for line in repair_lines(state, seen_codes):
        emit("  repair: %s", line)

    total = len(failed) + len(orphans)
    log.info("%d finding(s)", total)
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "openai-batch-validation-audit.mjs",
"js": '''/**
 * Report OpenAI batches that failed input validation, and the lines that broke.
 *
 * Read only. Two GET endpoints, /v1/batches and /v1/files. No upload, no batch
 * creation, no re-submission of a failed batch.
 *
 * Status "failed" on this API means the input file did not survive validation,
 * which happens before any request reaches the model: request_counts is all
 * zeros and nothing was billed. Rows that failed inside a batch that ran are a
 * different status and a different note.
 */
const BATCHES_URL = 'https://api.openai.com/v1/batches';
const FILES_URL = 'https://api.openai.com/v1/files';

const PAGE = 100;

export const NOT_BATCH_INPUT = new Set(['user_data', 'assistants', 'fine-tune', 'vision']);

export const KNOWN_CODES = {
  invalid_json: 'a line is not valid JSON. Validate the file locally before '
    + 'upload: every line must parse on its own.',
  duplicate_custom_id: 'two lines share a custom_id. They must be unique within '
    + 'the file, because results come back unordered and custom_id is the only '
    + 'join key.',
  missing_required_parameter: 'a line is missing a required field. Each row needs '
    + 'custom_id, method, url and body.',
  invalid_url: "a line's url does not match the batch endpoint. The two must "
    + 'agree for every row in the file.',
  model_not_found: 'the body names a model this project cannot reach. Check the '
    + 'id against GET /v1/models with the same key.',
  empty_file: 'the input file has no lines in it. The upload succeeded and the '
    + 'content did not.',
};

const FINDINGS = new Set(['validation-failed', 'orphan-input-files']);

/** Batches whose input file was rejected. Pure. */
export function failedBatches(batches) {
  return (batches ?? []).filter((b) => (b ?? {}).status === 'failed');
}

/** Normalised entries from errors.data[]. Pure. Never throws on a shape. */
export function errorRows(batch) {
  const errors = (batch ?? {}).errors;
  const data = errors && typeof errors === 'object' ? errors.data : null;
  const out = [];
  for (const item of data ?? []) {
    if (!item || typeof item !== 'object') continue;
    const parsed = Number.parseInt(item.line, 10);
    out.push({
      code: String(item.code ?? 'unknown'),
      message: String(item.message ?? ''),
      param: item.param ?? null,
      line: Number.isFinite(parsed) ? parsed : null,
    });
  }
  return out;
}

/** {code: [lines, count, message, param]}. Pure. Sorted by code, then line. */
export function linesByCode(rows) {
  const grouped = new Map();
  for (const row of rows ?? []) {
    if (!grouped.has(row.code)) {
      grouped.set(row.code, { lines: new Set(), count: 0, message: '', param: null });
    }
    const slot = grouped.get(row.code);
    slot.count += 1;
    if (row.line !== null && row.line !== undefined) slot.lines.add(row.line);
    if (!slot.message) slot.message = row.message ?? '';
    if (slot.param === null) slot.param = row.param ?? null;
  }
  const out = {};
  for (const code of [...grouped.keys()].sort()) {
    const slot = grouped.get(code);
    out[code] = [[...slot.lines].sort((a, b) => a - b), slot.count, slot.message,
                 slot.param];
  }
  return out;
}

/** True when the batch dispatched no requests at all. Pure. */
export function nothingBilled(batch) {
  const counts = (batch ?? {}).request_counts ?? {};
  return ['total', 'completed', 'failed']
    .every((k) => (Number(counts[k]) || 0) === 0);
}

/** Every input_file_id the account has handed to a batch. Pure. */
export function batchInputIds(batches) {
  const out = new Set();
  for (const b of batches ?? []) {
    if ((b ?? {}).input_file_id) out.add(String(b.input_file_id));
  }
  return out;
}

/** .jsonl files that can never be batch input and never were. Pure. */
export function mispurposedInputs(files, usedIds) {
  const used = usedIds ?? new Set();
  return (files ?? [])
    .filter((f) => f && typeof f === 'object')
    .filter((f) => String(f.filename ?? '').toLowerCase().endsWith('.jsonl'))
    .filter((f) => NOT_BATCH_INPUT.has(String(f.purpose ?? '')))
    .filter((f) => !used.has(String(f.id)))
    .map((f) => ({ id: String(f.id), filename: String(f.filename ?? ''),
                   purpose: String(f.purpose ?? ''), bytes: Number(f.bytes) || 0 }))
    .sort((a, b) => a.id.localeCompare(b.id));
}

/** True when the batch was created inside the window. Pure. */
export function withinWindow(batch, now, days) {
  if (!days || days <= 0) return true;
  const created = Number((batch ?? {}).created_at) || 0;
  return created >= now - days * 86400;
}

/** Grade the run. Pure. Returns [state, detail]. */
export function verdict(failed, orphans, days) {
  const f = (failed ?? []).length;
  const o = (orphans ?? []).length;
  const window = days && days > 0 ? `in the last ${days} days` : 'in the account';
  if (f && o) {
    return ['validation-failed',
      `${f} batch(es) failed input validation ${window}, and ${o} .jsonl was `
      + 'uploaded under a purpose /v1/batches will not accept'];
  }
  if (f) {
    return ['validation-failed',
      `${f} batch(es) failed input validation ${window} and nothing polled them `
      + 'to find out'];
  }
  if (o) {
    return ['orphan-input-files',
      `${o} .jsonl file(s) sit under a purpose /v1/batches will not accept, `
      + 'referenced by no batch'];
  }
  return ['validation-clean',
    `no batch ${window} failed validation, and every .jsonl in the file list `
    + 'either carries purpose=batch or was used by a batch'];
}

/** The repair for one verdict. Pure. Printed, never performed. */
export function repairLines(state, codes) {
  if (state === 'validation-clean') {
    return ['nothing to change. Keep the assertion that a submitter only logs '
      + 'success once status has left "validating".'];
  }
  const lines = [];
  for (const code of [...new Set(codes ?? [])].sort()) {
    if (KNOWN_CODES[code]) lines.push(`${code}: ${KNOWN_CODES[code]}`);
  }
  if (state === 'validation-failed') {
    lines.push('fix the input at the reported lines, then re-upload with '
      + 'purpose=batch and create the batch again. Nothing was billed, so '
      + 'nothing needs reconciling.');
    lines.push('make the submitter poll. A 200 from batch creation is a receipt, '
      + 'not a result: the only honest success signal is a batch that has left '
      + '"validating".');
  }
  if (state === 'orphan-input-files') {
    lines.push('re-upload each file with purpose=batch and delete the '
      + 'mis-purposed copy, which counts against project storage until you do.');
    lines.push('assert in the upload helper that the purpose matches the '
      + 'endpoint that will consume the file.');
  }
  return lines;
}

async function getJson(url, key, params) {
  const target = new URL(url);
  for (const [k, v] of Object.entries(params ?? {})) {
    target.searchParams.set(k, String(v));
  }
  let res;
  try {
    res = await fetch(target, { headers: { Authorization: `Bearer ${key}` } });
  } catch (err) {
    return [null, `request failed: ${err.message}`];
  }
  if (res.status !== 200) {
    let detail = '';
    try { detail = String((await res.json())?.error?.message ?? ''); } catch { detail = ''; }
    return [null, `HTTP ${res.status} ${detail}`];
  }
  try {
    return [await res.json(), null];
  } catch {
    return [null, 'response was not JSON'];
  }
}

async function pageAll(url, key, params, maxPages) {
  const rows = [];
  let after = null;
  for (let i = 0; i < Math.max(1, maxPages); i += 1) {
    const query = { ...(params ?? {}) };
    if (after) query.after = after;
    const [payload, err] = await getJson(url, key, query);
    if (err) return [rows, err];
    const data = payload.data ?? [];
    rows.push(...data);
    if (!payload.has_more || !data.length) break;
    after = data[data.length - 1]?.id;
    if (!after) break;
  }
  return [rows, null];
}

function args(argv) {
  const out = { sinceDays: 30, maxPages: 20 };
  for (let i = 0; i < argv.length; i += 1) {
    if (argv[i] === '--since-days') out.sinceDays = Number.parseInt(argv[i += 1], 10);
    else if (argv[i] === '--max-pages') out.maxPages = Number.parseInt(argv[i += 1], 10);
  }
  return out;
}

async function main() {
  const opts = args(process.argv.slice(2));
  const key = process.env.OPENAI_API_KEY;
  if (!key) {
    console.error('set OPENAI_API_KEY to a project key set to Read Only');
    process.exitCode = 2;
    return;
  }

  const now = Math.floor(Date.now() / 1000);
  const [batches, err] = await pageAll(BATCHES_URL, key, { limit: PAGE }, opts.maxPages);
  if (err && !batches.length) {
    console.error(`could not read the batch list: ${err}`);
    process.exitCode = 2;
    return;
  }
  if (err) console.log(`batch list stopped early: ${err}`);

  const scoped = batches.filter((b) => withinWindow(b, now, opts.sinceDays));
  const failed = failedBatches(scoped);
  const seenCodes = [];
  for (const b of failed) {
    const billed = nothingBilled(b)
      ? 'nothing billed (0 requests)'
      : 'request_counts is not all zero, which is unusual for failed';
    const stamp = new Date((Number(b.failed_at || b.created_at) || 0) * 1000)
      .toISOString().replace(/\\.\\d+Z$/, 'Z');
    console.log(`${String(b.id).padEnd(16)} failed at ${stamp}  ${billed}`);
    const groups = linesByCode(errorRows(b));
    if (!Object.keys(groups).length) {
      console.log('  (the errors object is empty, so the reason is not readable '
        + 'from the API)');
    }
    for (const [code, [lines, , message, param]] of Object.entries(groups)) {
      seenCodes.push(code);
      const shown = lines.slice(0, 6).join(', ');
      const more = lines.length > 6 ? ` and ${lines.length - 6} more` : '';
      const where = lines.length ? `lines ${shown}${more}` : 'no line given';
      const extra = param ? `  param ${param}` : '';
      console.log(`  ${code.padEnd(26)} ${where}${extra}`);
      if (message) console.log(`  ${''.padEnd(26)} ${message.slice(0, 140)}`);
    }
  }

  const [files, ferr] = await pageAll(FILES_URL, key, { limit: 10000 }, opts.maxPages);
  if (ferr) console.log(`file list stopped early: ${ferr}`);
  const orphans = mispurposedInputs(files, batchInputIds(batches));
  for (const row of orphans) {
    console.log(`orphan-input    ${row.id}  ${row.filename}  purpose=${row.purpose}  `
      + `${(row.bytes / 1048576).toFixed(1)} MB`);
  }

  const [state, detail] = verdict(failed, orphans, opts.sinceDays);
  console.log(`${state.padEnd(20)} ${detail}`);
  console.log('  measured: status, errors.data[] and request_counts from the '
    + 'batch list, purpose from the file list');
  console.log('  inferred: that the pipeline never polled, since a failed batch '
    + 'is otherwise indistinguishable from one nobody re-ran on purpose');
  for (const line of repairLines(state, seenCodes)) console.log(`  repair: ${line}`);

  const total = failed.length + orphans.length;
  console.log(`${total} finding(s)`);
  process.exitCode = total ? 1 : 0;
  void FINDINGS;
}

if (import.meta.url === `file://${process.argv[1]}`) await main();
''',
"test_intro": "The first test is the claim the whole note rests on: a batch whose <code>status</code> is <code>failed</code> is a batch that never ran, so <code>nothing_billed</code> must be true for it and the errors must group by code with their line numbers intact. The second is the shape defence &mdash; <code>errors</code> absent, <code>errors.data</code> null, an entry that is a string rather than an object, and a <code>line</code> of <code>null</code> all have to degrade to no rows instead of an exception, because a script that crashes on the second batch never reports the first. The third is the three-condition filter on mis-purposed files, with a case for each condition removed, since the version that flags every input file you ever used is the version somebody switches off. The fourth checks that a <code>completed</code> batch with failed rows is never picked up here, which is the boundary against the published partial-failure note. Then the window arithmetic, and last the repair text, where a duplicate <code>custom_id</code> gets the documented fix rather than a generic one.",
"test_py_file": "test_openai_batch_validation_audit.py",
"test_py": '''from openai_batch_validation_audit import (batch_input_ids, error_rows,
                                            failed_batches, lines_by_code,
                                            mispurposed_inputs, nothing_billed,
                                            repair_lines, verdict, within_window)

NOW = 1_800_000_000

FAILED = {
    "id": "batch_aa",
    "status": "failed",
    "created_at": NOW - 3600,
    "failed_at": NOW - 3560,
    "input_file_id": "file_in1",
    "request_counts": {"total": 0, "completed": 0, "failed": 0},
    "errors": {"object": "list", "data": [
        {"code": "invalid_json", "message": "not valid JSON", "param": None,
         "line": 41207},
        {"code": "invalid_json", "message": "not valid JSON", "param": None,
         "line": 41208},
        {"code": "duplicate_custom_id", "message": "custom_id repeated",
         "param": "custom_id", "line": 903},
    ]},
}

RAN = {
    "id": "batch_bb",
    "status": "completed",
    "created_at": NOW - 7200,
    "input_file_id": "file_in2",
    "request_counts": {"total": 900, "completed": 880, "failed": 20},
    "output_file_id": "file_out2",
}


def test_a_failed_batch_never_ran_and_names_its_lines():
    assert [b["id"] for b in failed_batches([FAILED, RAN])] == ["batch_aa"]
    # Validation happens before dispatch, so the reassuring half is provable.
    assert nothing_billed(FAILED)
    assert not nothing_billed(RAN)
    groups = lines_by_code(error_rows(FAILED))
    assert groups["invalid_json"][0] == [41207, 41208]
    assert groups["invalid_json"][1] == 2
    assert groups["duplicate_custom_id"][0] == [903]
    assert groups["duplicate_custom_id"][3] == "custom_id"


def test_every_field_in_the_errors_object_is_allowed_to_be_missing():
    assert error_rows({"status": "failed"}) == []
    assert error_rows({"errors": None}) == []
    assert error_rows({"errors": {"data": None}}) == []
    assert error_rows({"errors": {"data": ["not an object"]}}) == []
    rows = error_rows({"errors": {"data": [{"code": None, "line": None}]}})
    assert rows == [{"code": "unknown", "message": "", "param": None,
                     "line": None}]
    # A code with no line still gets a row, worded so nobody hunts for line 0.
    assert lines_by_code(rows)["unknown"][0] == []
    # An absent request_counts is what a batch that never started looks like.
    assert nothing_billed({"status": "failed"})


def test_a_mispurposed_input_needs_all_three_conditions():
    files = [
        {"id": "file_x", "filename": "nightly.jsonl", "purpose": "user_data",
         "bytes": 1400000},
        {"id": "file_ok", "filename": "nightly.jsonl", "purpose": "batch",
         "bytes": 1400000},
        {"id": "file_in2", "filename": "used.jsonl", "purpose": "user_data",
         "bytes": 10},
        {"id": "file_img", "filename": "photo.png", "purpose": "vision",
         "bytes": 900},
        {"id": "file_res", "filename": "out.jsonl", "purpose": "batch_output",
         "bytes": 50},
    ]
    used = batch_input_ids([FAILED, RAN])
    assert used == {"file_in1", "file_in2"}
    found = mispurposed_inputs(files, used)
    assert [r["id"] for r in found] == ["file_x"]
    assert found[0]["purpose"] == "user_data"
    # Outputs are not inputs, and a file that was used is never a finding.
    assert mispurposed_inputs(files, {"file_x"} | used) == []


def test_rows_that_failed_inside_a_batch_that_ran_belong_to_another_note():
    # request_counts.failed > 0 on a completed batch is the published
    # partial-failure note. This script must not claim it.
    assert failed_batches([RAN]) == []
    state, detail = verdict([], [], 30)
    assert state == "validation-clean"
    assert "no batch in the last 30 days" in detail


def test_the_window_is_arithmetic_on_created_at_and_zero_means_everything():
    assert within_window(FAILED, NOW, 30)
    assert not within_window(FAILED, NOW + 40 * 86400, 30)
    assert within_window(FAILED, NOW + 40 * 86400, 0)
    assert not within_window({"created_at": "nonsense"}, NOW, 30)


def test_the_repair_names_the_documented_fix_for_the_code_it_saw():
    state, detail = verdict([FAILED], [{"id": "file_x"}], 30)
    assert state == "validation-failed"
    assert "will not accept" in detail
    lines = repair_lines(state, ["duplicate_custom_id", "invalid_json", "made_up"])
    assert any("custom_id is the only join key" in line for line in lines)
    assert any("every line must parse on its own" in line for line in lines)
    assert not any("made_up" in line for line in lines)
    assert any("receipt, not a result" in line for line in lines)
    assert repair_lines("validation-clean", [])[0].startswith("nothing to change")
    orphan_only = verdict([], [{"id": "file_x"}], 0)
    assert orphan_only[0] == "orphan-input-files"
    assert any("purpose matches the endpoint"
               in line for line in repair_lines(orphan_only[0], []))
''',
"test_js_file": "openai-batch-validation-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { batchInputIds, errorRows, failedBatches, linesByCode, mispurposedInputs,
         nothingBilled, repairLines, verdict,
         withinWindow } from './openai-batch-validation-audit.mjs';

const NOW = 1800000000;

const FAILED = {
  id: 'batch_aa',
  status: 'failed',
  created_at: NOW - 3600,
  failed_at: NOW - 3560,
  input_file_id: 'file_in1',
  request_counts: { total: 0, completed: 0, failed: 0 },
  errors: { object: 'list', data: [
    { code: 'invalid_json', message: 'not valid JSON', param: null, line: 41207 },
    { code: 'invalid_json', message: 'not valid JSON', param: null, line: 41208 },
    { code: 'duplicate_custom_id', message: 'custom_id repeated',
      param: 'custom_id', line: 903 },
  ] },
};

const RAN = {
  id: 'batch_bb',
  status: 'completed',
  created_at: NOW - 7200,
  input_file_id: 'file_in2',
  request_counts: { total: 900, completed: 880, failed: 20 },
  output_file_id: 'file_out2',
};

test('a failed batch never ran and names its lines', () => {
  assert.deepEqual(failedBatches([FAILED, RAN]).map((b) => b.id), ['batch_aa']);
  assert.ok(nothingBilled(FAILED));
  assert.ok(!nothingBilled(RAN));
  const groups = linesByCode(errorRows(FAILED));
  assert.deepEqual(groups.invalid_json[0], [41207, 41208]);
  assert.equal(groups.invalid_json[1], 2);
  assert.deepEqual(groups.duplicate_custom_id[0], [903]);
  assert.equal(groups.duplicate_custom_id[3], 'custom_id');
});

test('every field in the errors object is allowed to be missing', () => {
  assert.deepEqual(errorRows({ status: 'failed' }), []);
  assert.deepEqual(errorRows({ errors: null }), []);
  assert.deepEqual(errorRows({ errors: { data: null } }), []);
  assert.deepEqual(errorRows({ errors: { data: ['not an object'] } }), []);
  const rows = errorRows({ errors: { data: [{ code: null, line: null }] } });
  assert.deepEqual(rows, [{ code: 'unknown', message: '', param: null, line: null }]);
  assert.deepEqual(linesByCode(rows).unknown[0], []);
  assert.ok(nothingBilled({ status: 'failed' }));
});

test('a mispurposed input needs all three conditions', () => {
  const files = [
    { id: 'file_x', filename: 'nightly.jsonl', purpose: 'user_data', bytes: 1400000 },
    { id: 'file_ok', filename: 'nightly.jsonl', purpose: 'batch', bytes: 1400000 },
    { id: 'file_in2', filename: 'used.jsonl', purpose: 'user_data', bytes: 10 },
    { id: 'file_img', filename: 'photo.png', purpose: 'vision', bytes: 900 },
    { id: 'file_res', filename: 'out.jsonl', purpose: 'batch_output', bytes: 50 },
  ];
  const used = batchInputIds([FAILED, RAN]);
  assert.deepEqual([...used].sort(), ['file_in1', 'file_in2']);
  const found = mispurposedInputs(files, used);
  assert.deepEqual(found.map((r) => r.id), ['file_x']);
  assert.equal(found[0].purpose, 'user_data');
  assert.deepEqual(mispurposedInputs(files, new Set([...used, 'file_x'])), []);
});

test('rows that failed inside a batch that ran belong to another note', () => {
  assert.deepEqual(failedBatches([RAN]), []);
  const [state, detail] = verdict([], [], 30);
  assert.equal(state, 'validation-clean');
  assert.ok(detail.includes('no batch in the last 30 days'));
});

test('the window is arithmetic on created_at and zero means everything', () => {
  assert.ok(withinWindow(FAILED, NOW, 30));
  assert.ok(!withinWindow(FAILED, NOW + 40 * 86400, 30));
  assert.ok(withinWindow(FAILED, NOW + 40 * 86400, 0));
  assert.ok(!withinWindow({ created_at: 'nonsense' }, NOW, 30));
});

test('the repair names the documented fix for the code it saw', () => {
  const [state, detail] = verdict([FAILED], [{ id: 'file_x' }], 30);
  assert.equal(state, 'validation-failed');
  assert.ok(detail.includes('will not accept'));
  const lines = repairLines(state, ['duplicate_custom_id', 'invalid_json', 'made_up']);
  assert.ok(lines.some((l) => l.includes('custom_id is the only join key')));
  assert.ok(lines.some((l) => l.includes('every line must parse on its own')));
  assert.ok(!lines.some((l) => l.includes('made_up')));
  assert.ok(lines.some((l) => l.includes('receipt, not a result')));
  assert.ok(repairLines('validation-clean', [])[0].startsWith('nothing to change'));
  const [orphanState] = verdict([], [{ id: 'file_x' }], 0);
  assert.equal(orphanState, 'orphan-input-files');
  assert.ok(repairLines(orphanState, []).some((l) => l.includes('purpose matches the endpoint')));
});
''',
"faq": [
 ("Does a failed batch cost anything?",
  "No. Validation runs while the batch is in the <code>validating</code> state, before any request is dispatched to a model, so a batch that lands on <code>failed</code> has a <code>request_counts</code> of all zeros and no tokens attached to it. The script prints that alongside every failure, because it is the first question anybody asks and getting it wrong in either direction wastes an afternoon. What the failure does cost you is the work that did not happen, which is usually the more expensive half."),
 ("What is the difference between this and a batch that reads completed with failed rows?",
  "Everything, including the repair. <code>failed</code> is a statement about the input file: it was rejected as a whole and nothing ran. A batch that reads <code>completed</code> with a non-zero <code>request_counts.failed</code> did run, was billed for the rows that succeeded, and wrote its failures to an error file. The first is fixed by editing a <code>.jsonl</code> and re-creating the batch; the second is fixed by reading <code>error_file_id</code> and retrying the rows that are worth retrying. Two of the other notes in this section own that second case."),
 ("Why does the script read the file list as well as the batch list?",
  "Because one version of this failure never produces a batch object at all. <code>/v1/batches</code> accepts an input file only when its <code>purpose</code> is exactly <code>batch</code>, and a file uploaded under <code>user_data</code> or <code>assistants</code> is refused at creation. There is no batch to list and no <code>errors</code> array to read: the only evidence anywhere in the API is a <code>.jsonl</code> in the file list that nothing references. That is why the check needs all three conditions &mdash; the extension, the wrong purpose, and no batch pointing at it."),
 ("Can I filter the batch list to failed batches server-side?",
  "No. <code>GET /v1/batches</code> takes <code>limit</code>, which ranges from 1 to 100 and defaults to 20, and <code>after</code> as a cursor. There is no status filter, no date range and no metadata query, so every bit of selection happens on your side of the wire after you have paged the list. The practical consequence is that a run which reads only the default first page sees the last twenty batches, and on a nightly pipeline that is about three weeks of history missed."),
 ("The errors object is empty on one of my failed batches. What then?",
  "Then the reason is not readable from the API and the script says so in those words rather than printing an empty list. <code>errors</code> is an optional field, its <code>data</code> array is optional, and <code>line</code> is documented as present only where applicable. When there is nothing there, the remaining evidence is the input file itself: validate it locally, checking that every line parses, that <code>custom_id</code> values are unique, that each row's <code>url</code> matches the batch endpoint, and that the model in each body is one this project can reach."),
],
"related": [REL_PARTIAL, REL_OUTPUT, REL_EXPIRED],
"citations": [CITE_OAI_BATCH_REF, CITE_OAI_BATCH_GUIDE, CITE_OAI_FILES, CITE_OAI_ERRORS],
},
{
"slug": "batch-cancelled-partial-results",
"title": "Cancelling a batch does not unbill the rows it already ran",
"description": "A cancelled batch holds finished, paid-for output. Read completed vs total on OpenAI and succeeded vs canceled on Anthropic before you re-run the whole thing.",
"h1": "Cancelling a batch does not unbill the rows it already ran",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["openai batch cancelling status stuck 10 minutes",
             "anthropic batch cancel_initiated_at canceling",
             "cancelled batch partial results output file",
             "message batch request_counts canceled succeeded",
             "batch cancelled billed for completed requests"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Reads OPENAI_API_KEY (a project key set to Read Only) and ANTHROPIC_API_KEY (a workspace key). Either one alone is enough; the script reads whichever providers it has keys for. GET requests only, and it never cancels anything.",
"lead": "Somebody hit cancel during the deploy, which was the right call, and then the runbook said re-run it in the morning. So it was re-run in the morning. What nobody checked is that the batch had already processed sixty-one thousand of its ninety thousand rows before the cancel landed, that those rows are sitting in the output file, and that the morning re-run paid for all sixty-one thousand of them a second time. Cancel is not a rollback. It is a stop.",
"short_answer": """<p>Read the cancellation states before you re-run anything. On OpenAI, <code>GET /v1/batches?limit=100</code> and keep <code>status</code> of <code>cancelling</code> or <code>cancelled</code>; the row that matters is <code>request_counts.completed</code> against <code>total</code>, alongside a non-null <code>output_file_id</code>. On Anthropic, <code>GET /v1/messages/batches?limit=1000</code> with a <strong>workspace key</strong> and keep every batch where <code>cancel_initiated_at</code> is not null; the row that matters is <code>request_counts.succeeded</code> against <code>canceled</code>.</p>
<p><strong>Anything with a non-zero completed or succeeded count is finished work you already have.</strong> It is in the output file or at <code>results_url</code>, keyed by <code>custom_id</code>, and re-running those rows spends the money again. The repair is a subtraction, not a re-submission: download what came back, take the <code>custom_id</code>s out of the input file, and submit the remainder.</p>
<p>Anthropic states the billing rule outright, and it is the good news: requests that were <code>canceled</code> or <code>expired</code> before reaching the model are not billed. Only what actually ran costs anything. OpenAI documents the partial results but not the billing split, so for that provider the completed count is a floor on what you paid, and the cost report for the day is the confirmation.</p>
<p><strong>Then check that the cancel actually finished.</strong> OpenAI holds a batch in <code>cancelling</code> for up to ten minutes before it reaches <code>cancelled</code>. Anthropic holds it in <code>canceling</code> until the in-flight requests drain. A batch that has been mid-cancel for an hour has not stopped, and treating it as stopped is how a second batch gets submitted alongside the first.</p>""",
"problem": """<p>The mental model that causes this is that cancel undoes the job. It does not. Both Batch APIs are queues of independent requests, and cancellation stops the ones that have not been dispatched yet; the ones already through the model are done, written down, and paid for. The API is completely honest about it &mdash; OpenAI's cancelled batch carries an <code>output_file_id</code> and Anthropic's carries a <code>results_url</code> &mdash; but the operator who typed the cancel is not reading the batch object afterwards, because in their head the job is gone.</p>
<p>So there are two costs, and the second one is bigger. The first is the output that is thrown away: rows that were generated, billed and never collected. The second is the re-run, which pays for every one of those rows again. On a ninety thousand row batch cancelled two thirds of the way through, that is two thirds of the batch's cost spent twice, and it does not appear as an incident anywhere. It appears as a slightly larger invoice.</p>
<p>The mid-flight state is the other half. Cancellation is asynchronous on both providers: OpenAI's documented window is up to ten minutes in <code>cancelling</code>, and Anthropic's <code>canceling</code> lasts until the requests already in flight finish. During that window the batch is still working, still consuming its share of the enqueued queue, and still producing output. A deploy script that cancels and immediately submits a replacement has, briefly, two batches doing the same work, and a batch stuck in <code>cancelling</code> long past the window is a sign that something is wrong with the job rather than with your patience.</p>
<p>None of this raises. Cancelling is a successful operation, the batch object updates as documented, and the only party who could notice the abandoned output is the code that was going to read it, which was switched off at the same moment as the batch.</p>""",
"why": """<p><strong>The counts are the whole reading, and they are spelled differently on each provider.</strong> OpenAI's <code>request_counts</code> is <code>{total, completed, failed}</code>, so the salvage number is <code>completed</code> and the cancelled remainder is <code>total</code> minus the rest. Anthropic's is <code>{processing, succeeded, errored, canceled, expired}</code>, whose values are documented to sum to the total number of requests in the batch, so the salvage number is <code>succeeded</code> and the cancelled remainder is already its own field. The script normalises both into the same row rather than pretending one shape fits.</p>
<p><strong>Anthropic tells you the billing rule; OpenAI does not, and the script says which is which.</strong> The Claude documentation states that <code>canceled</code> and <code>expired</code> requests are not billed, and that a cancelled batch ends with <code>processing_status: "ended"</code> and may contain partial results. OpenAI's guide documents the ten-minute <code>cancelling</code> window and the partial output, and says nothing about the billing split. Printing a confident claim about OpenAI billing would be inventing it, so the output reports the completed count as a floor and points at the cost report.</p>
<p><strong>A cancel that has not landed is a different finding from a cancel that has.</strong> <code>cancelling_at</code> on OpenAI and <code>cancel_initiated_at</code> on Anthropic are timestamps, and both providers keep a batch in the intermediate state while work drains. Fifteen minutes is a generous read of OpenAI's documented ten, and Anthropic publishes no bound at all, so on that side the threshold is a heuristic and the real ceiling is the batch's own 24-hour <code>expires_at</code>. The script prints the age rather than a verdict dressed up as a fact.</p>
<p><strong>Cancelling before anything completed is a clean outcome and gets said so.</strong> A batch cancelled thirty seconds after submission has <code>completed: 0</code>, no salvage and no double billing, and reporting it in the same breath as one that is two thirds done trains people to skim the output. It gets its own line and no finding.</p>
<p><strong>This note stops at the salvage arithmetic and hands retention to its sibling.</strong> A cancelled batch's output is on the same expiry clock as any other &mdash; thirty days on OpenAI, twenty-nine on Anthropic &mdash; but that clock, and the join against your ingest ledger, belong to the unclaimed-output note. Here the question is only whether there is anything worth collecting before you pay for it twice.</p>""",
"steps": [
 {"h": "Bring whichever keys you have",
  "body": """<p><code>OPENAI_API_KEY</code> as a project key set to Read Only, <code>ANTHROPIC_API_KEY</code> as a workspace key, or both. The script reads what it is given and says which providers it looked at, so a single-provider shop gets a single-provider answer rather than a misleading clean run.</p>"""},
 {"h": "List the batches and keep the cancellations",
  "body": """<p>OpenAI: page <code>/v1/batches</code> on <code>after</code> and keep <code>status</code> in <code>cancelling</code> or <code>cancelled</code>. Anthropic: page <code>/v1/messages/batches</code> on <code>after_id</code> and keep every batch with a non-null <code>cancel_initiated_at</code>, which is set only when cancellation was initiated and stays set afterwards.</p>"""},
 {"h": "Split finished work from cancelled work",
  "body": """<p><code>completed</code> versus <code>total</code> on OpenAI, <code>succeeded</code> versus <code>canceled</code> on Anthropic. A non-zero finished count with an artifact to read &mdash; <code>output_file_id</code> or <code>results_url</code> &mdash; is the finding, and the number printed next to it is how many rows a naive re-run would pay for twice.</p>"""},
 {"h": "Check the cancel actually landed",
  "body": """<p>Anything still in <code>cancelling</code> or <code>canceling</code> gets its age printed from <code>cancelling_at</code> or <code>cancel_initiated_at</code>. Past about fifteen minutes on OpenAI the documented window has gone by; on Anthropic there is no published window, so the number is information rather than a verdict.</p>"""},
 {"h": "Subtract, then re-submit the remainder",
  "body": """<p>The repair is printed. Download the partial output, collect the <code>custom_id</code>s that came back, remove those lines from the input file, and submit what is left. Results are not returned in request order on either provider, so <code>custom_id</code> is the only join key that works.</p>"""},
],
"verify": """<p>Re-run after the remainder batch is submitted. The old cancelled batches stay in the list &mdash; batch objects are not deleted by cancelling them &mdash; so what changes is that the finished counts have been collected and the re-run is smaller than the original by exactly the salvaged number. Keep this in the deploy path rather than in a weekly report: the moment it is worth running is between the cancel and the re-run.</p>
<pre><code class="language-bash">python3 batch_cancellation_audit.py
# openai      batch_68f4b2   cancelled   61,204 of 90,000 done, 28,796 cancelled
#                            output_file_id file_7ac1
# openai      batch_68f51a   cancelling   for 68 min, past the 10 minute window
# anthropic   msgbatch_01Hq  ended        41,880 succeeded, 12,120 canceled
#                            results_url present
# cancel-stuck         1 batch has been mid cancel longer than the documented
#                      window, and 2 cancelled batches hold 103,084 finished
#                      rows nothing has collected
#   measured: request_counts and the cancellation timestamps from both batch
#             lists
#   inferred: that a re-run would repeat the finished rows, since neither API
#             records whether the partial output was ever downloaded
#   repair: download the partial output, drop those custom_ids from the input
#           file, and submit only the remainder.
#   repair: on Anthropic, canceled and expired requests are not billed, so the
#           succeeded count is the whole cost. On OpenAI the completed count is
#           a floor: confirm the day against the cost report.
# 3 finding(s)</code></pre>""",
"code_intro": "Two paged GETs, one per provider, and seven pure functions. <code>parse_time</code>, which takes OpenAI's unix integers and Anthropic's RFC 3339 strings and returns one kind of number; <code>openai_cancel_rows</code> and <code>anthropic_cancel_rows</code>, which normalise two different <code>request_counts</code> shapes into the same row rather than branching everywhere downstream; <code>salvage_rows</code>, which is the subtraction the repair depends on; <code>stuck_rows</code>, which takes both <code>now</code> and the threshold as arguments because a clock in a pure function is a test that fails on a Tuesday; <code>verdict</code>, which puts an unlanded cancel ahead of a salvageable one because billing may not have stopped; and <code>repair_lines</code>, which states the Anthropic billing rule as documented and refuses to state an OpenAI one that is not.",
"py_file": "batch_cancellation_audit.py",
"py": '''"""Find billed, salvageable output left behind by cancelled batches.

Read only, on both providers. Two GET endpoints, /v1/batches on OpenAI and
/v1/messages/batches on Anthropic. This script never cancels a batch, never
submits one, and never downloads a result file.

Cancel is a stop, not a rollback. Requests that reached the model before the
cancel landed are finished and are in the output; re-running the whole batch
pays for them twice. Anthropic documents that canceled and expired requests are
not billed. OpenAI documents the partial output but not the billing split, so
the completed count is reported as a floor rather than as a total.

Retention of that partial output, and the join against your own ingest ledger,
belong to the unclaimed-output note. This one stops at the arithmetic.
"""
import argparse
import calendar
import datetime
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("batch_cancellation_audit")

OPENAI_BATCHES_URL = "https://api.openai.com/v1/batches"
ANTHROPIC_BATCHES_URL = "https://api.anthropic.com/v1/messages/batches"

# OpenAI documents up to ten minutes in "cancelling" before a batch reaches
# "cancelled". Fifteen is a generous read of ten. Anthropic publishes no bound
# for "canceling" at all, so on that side this is a heuristic and the output
# says so rather than dressing a guess up as a rule.
STUCK_SECONDS = 15 * 60

OPENAI_CANCEL_STATES = ("cancelling", "cancelled")

FINDINGS = ("cancel-stuck", "cancel-partial-unclaimed")


def parse_time(value):
    """Epoch seconds from a unix number or an RFC 3339 string. Pure.

    OpenAI stamps integers, Anthropic stamps RFC 3339. Everything downstream
    wants one kind of number, so the difference is absorbed once, here. A
    string with no offset is read as UTC rather than as whatever the machine
    running the audit happens to be set to.
    """
    if value is None or value == "" or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return int(value)
    text = str(value).strip()
    if text[-1:] in ("Z", "z"):
        text = text[:-1] + "+00:00"
    try:
        stamp = datetime.datetime.fromisoformat(text)
    except (ValueError, TypeError):
        return None
    if stamp.tzinfo is None:
        return calendar.timegm(stamp.timetuple())
    return int(stamp.timestamp())


def openai_cancel_rows(batches):
    """Normalised rows for OpenAI batches under cancellation. Pure."""
    out = []
    for b in batches or []:
        status = (b or {}).get("status")
        if status not in OPENAI_CANCEL_STATES:
            continue
        counts = b.get("request_counts") or {}
        total = int(counts.get("total") or 0)
        done = int(counts.get("completed") or 0)
        failed = int(counts.get("failed") or 0)
        out.append({
            "provider": "openai",
            "id": str(b.get("id")),
            "status": status,
            "in_flight": status == "cancelling",
            "done": done,
            "stopped": max(0, total - done - failed),
            "total": total,
            "artifact": b.get("output_file_id"),
            "cancel_started": parse_time(b.get("cancelling_at")),
            "billing_known": False,
        })
    return sorted(out, key=lambda r: r["id"])


def anthropic_cancel_rows(batches):
    """Normalised rows for Claude batches under cancellation. Pure.

    cancel_initiated_at is set only when cancellation was initiated, and stays
    set once the batch has ended, so it is the whole filter.
    """
    out = []
    for b in batches or []:
        started = (b or {}).get("cancel_initiated_at")
        if not started:
            continue
        counts = b.get("request_counts") or {}
        done = int(counts.get("succeeded") or 0)
        stopped = int(counts.get("canceled") or 0)
        status = str(b.get("processing_status") or "")
        out.append({
            "provider": "anthropic",
            "id": str(b.get("id")),
            "status": status or "unknown",
            "in_flight": status == "canceling",
            "done": done,
            "stopped": stopped,
            "total": done + stopped + int(counts.get("errored") or 0)
                     + int(counts.get("expired") or 0)
                     + int(counts.get("processing") or 0),
            "artifact": b.get("results_url"),
            "cancel_started": parse_time(started),
            "billing_known": True,
        })
    return sorted(out, key=lambda r: r["id"])


def salvage_rows(rows):
    """Rows holding finished work a re-run would pay for again. Pure."""
    return [r for r in rows or [] if int(r.get("done") or 0) > 0]


def stuck_rows(rows, now, seconds=STUCK_SECONDS):
    """Rows still mid cancel past the threshold. Pure. now is an argument."""
    out = []
    for r in rows or []:
        if not r.get("in_flight"):
            continue
        started = r.get("cancel_started")
        if started is None or now - started > seconds:
            out.append(r)
    return out


def salvaged_total(rows):
    """Finished rows across everything cancelled. Pure."""
    return sum(int(r.get("done") or 0) for r in salvage_rows(rows))


def verdict(rows, stuck, salvage):
    """Grade the run. Pure. Returns (state, detail)."""
    rows = list(rows or [])
    stuck = list(stuck or [])
    salvage = list(salvage or [])
    if not rows:
        return ("no-cancels",
                "no batch on the providers checked has had a cancellation "
                "initiated")
    if stuck:
        detail = ("%d batch(es) have been mid cancel longer than the documented "
                  "window" % len(stuck))
        if salvage:
            detail += (", and %d cancelled batch(es) hold %d finished rows "
                       "nothing has collected"
                       % (len(salvage), salvaged_total(salvage)))
        return ("cancel-stuck", detail)
    if salvage:
        return ("cancel-partial-unclaimed",
                "%d cancelled batch(es) hold %d finished rows a re-run would "
                "pay for again" % (len(salvage), salvaged_total(salvage)))
    return ("cancel-clean",
            "%d cancellation(s) found, none of which had completed a single "
            "request, so there is nothing to salvage and nothing to double pay"
            % len(rows))


def repair_lines(state, rows):
    """The repair for one verdict. Pure. Printed, never performed."""
    rows = list(rows or [])
    if state == "no-cancels":
        return []
    if state == "cancel-clean":
        return ["nothing to collect. Keep cancelling early: a batch stopped "
                "before its first request completed costs nothing."]
    lines = []
    if state == "cancel-stuck":
        lines.append("a batch still in cancelling or canceling has not stopped. "
                     "Poll it to a terminal state before you submit a "
                     "replacement, or the two will run the same rows at once.")
    if any(int(r.get("done") or 0) > 0 for r in rows):
        lines.append("download the partial output, drop those custom_ids from "
                     "the input file, and submit only the remainder. Results "
                     "are not returned in request order, so custom_id is the "
                     "only join key that works.")
    if any(r.get("provider") == "anthropic" and int(r.get("done") or 0) > 0
           for r in rows):
        lines.append("on Anthropic, canceled and expired requests are not "
                     "billed, so the succeeded count is the whole cost of the "
                     "cancelled batch.")
    if any(r.get("provider") == "openai" and int(r.get("done") or 0) > 0
           for r in rows):
        lines.append("on OpenAI the billing split for a cancelled batch is not "
                     "documented, so treat the completed count as a floor and "
                     "confirm the day against the cost report.")
    return lines


def get_json(url, headers, params=None, timeout=30):
    """One GET. Returns (payload, error). Read only, always."""
    try:
        r = requests.get(url, headers=headers, params=params or {}, timeout=timeout)
    except requests.RequestException as exc:
        return (None, "request failed: %s" % exc)
    if r.status_code != 200:
        return (None, "HTTP %d %s" % (r.status_code, (r.text or "")[:160]))
    try:
        return (r.json(), None)
    except ValueError:
        return (None, "response was not JSON")


def page_openai(key, max_pages):
    """/v1/batches, following the after cursor. GETs only."""
    rows, after = [], None
    headers = {"Authorization": "Bearer %s" % key}
    for _ in range(max(1, max_pages)):
        params = {"limit": 100}
        if after:
            params["after"] = after
        payload, err = get_json(OPENAI_BATCHES_URL, headers, params)
        if err:
            return (rows, err)
        data = payload.get("data") or []
        rows.extend(data)
        if not payload.get("has_more") or not data:
            break
        after = data[-1].get("id")
    return (rows, None)


def page_anthropic(key, max_pages):
    """/v1/messages/batches, following after_id. GETs only."""
    rows, after = [], None
    headers = {"x-api-key": key, "anthropic-version": "2023-06-01"}
    for _ in range(max(1, max_pages)):
        params = {"limit": 1000}
        if after:
            params["after_id"] = after
        payload, err = get_json(ANTHROPIC_BATCHES_URL, headers, params)
        if err:
            return (rows, err)
        data = payload.get("data") or []
        rows.extend(data)
        if not payload.get("has_more") or not data:
            break
        after = payload.get("last_id") or data[-1].get("id")
    return (rows, None)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--stuck-minutes", type=int, default=15,
                    help="age past which a batch still mid cancel is reported")
    ap.add_argument("--max-pages", type=int, default=20)
    args = ap.parse_args()

    openai_key = os.environ.get("OPENAI_API_KEY")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    if not openai_key and not anthropic_key:
        log.error("set OPENAI_API_KEY (project key, Read Only) or "
                  "ANTHROPIC_API_KEY (workspace key), or both")
        return 2

    now = int(time.time())
    rows = []
    checked = []
    if openai_key:
        checked.append("openai")
        batches, err = page_openai(openai_key, args.max_pages)
        if err:
            log.warning("openai batch list stopped early: %s", err)
        rows.extend(openai_cancel_rows(batches))
    if anthropic_key:
        checked.append("anthropic")
        batches, err = page_anthropic(anthropic_key, args.max_pages)
        if err:
            log.warning("anthropic batch list stopped early: %s", err)
        rows.extend(anthropic_cancel_rows(batches))

    stuck = stuck_rows(rows, now, max(1, args.stuck_minutes) * 60)
    salvage = salvage_rows(rows)
    stuck_ids = {r["id"] for r in stuck}

    for r in rows:
        log.info("%-11s %-14s %-11s %s of %s done, %s stopped", r["provider"],
                 r["id"][:14], r["status"], format(r["done"], ","),
                 format(r["total"], ","), format(r["stopped"], ","))
        if r["artifact"]:
            label = "output_file_id" if r["provider"] == "openai" else "results_url"
            log.info("%-11s %-14s   %s present", "", "", label)
        if r["id"] in stuck_ids:
            started = r.get("cancel_started")
            age = "an unknown time" if started is None \\
                else "%d min" % ((now - started) // 60)
            log.warning("%-11s %-14s   mid cancel for %s", r["provider"],
                        r["id"][:14], age)

    state, detail = verdict(rows, stuck, salvage)
    emit = log.warning if state in FINDINGS else log.info
    emit("%-20s %s", state, detail)
    emit("  checked: %s", ", ".join(checked))
    emit("  measured: request_counts and the cancellation timestamps from the "
         "batch lists")
    emit("  inferred: that a re-run would repeat the finished rows, since "
         "neither API records whether the partial output was downloaded")
    for line in repair_lines(state, rows):
        emit("  repair: %s", line)

    total = len(stuck) + len(salvage)
    log.info("%d finding(s)", total)
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "batch-cancellation-audit.mjs",
"js": '''/**
 * Find billed, salvageable output left behind by cancelled batches.
 *
 * Read only, on both providers: /v1/batches on OpenAI and /v1/messages/batches
 * on Anthropic. Nothing is cancelled, submitted or downloaded.
 *
 * Cancel is a stop, not a rollback. Anthropic documents that canceled and
 * expired requests are not billed; OpenAI documents the partial output but not
 * the billing split, so its completed count is reported as a floor.
 */
const OPENAI_BATCHES_URL = 'https://api.openai.com/v1/batches';
const ANTHROPIC_BATCHES_URL = 'https://api.anthropic.com/v1/messages/batches';

export const STUCK_SECONDS = 15 * 60;

const OPENAI_CANCEL_STATES = new Set(['cancelling', 'cancelled']);

const FINDINGS = new Set(['cancel-stuck', 'cancel-partial-unclaimed']);

/** Epoch seconds from a unix number or an RFC 3339 string. Pure. */
export function parseTime(value) {
  if (value === null || value === undefined || value === '' || typeof value === 'boolean') {
    return null;
  }
  if (typeof value === 'number') return Math.trunc(value);
  const ms = Date.parse(String(value));
  return Number.isFinite(ms) ? Math.floor(ms / 1000) : null;
}

/** Normalised rows for OpenAI batches under cancellation. Pure. */
export function openaiCancelRows(batches) {
  return (batches ?? [])
    .filter((b) => OPENAI_CANCEL_STATES.has((b ?? {}).status))
    .map((b) => {
      const counts = b.request_counts ?? {};
      const total = Number(counts.total) || 0;
      const done = Number(counts.completed) || 0;
      const failed = Number(counts.failed) || 0;
      return {
        provider: 'openai',
        id: String(b.id),
        status: b.status,
        inFlight: b.status === 'cancelling',
        done,
        stopped: Math.max(0, total - done - failed),
        total,
        artifact: b.output_file_id ?? null,
        cancelStarted: parseTime(b.cancelling_at),
        billingKnown: false,
      };
    })
    .sort((a, b) => a.id.localeCompare(b.id));
}

/** Normalised rows for Claude batches under cancellation. Pure. */
export function anthropicCancelRows(batches) {
  return (batches ?? [])
    .filter((b) => (b ?? {}).cancel_initiated_at)
    .map((b) => {
      const counts = b.request_counts ?? {};
      const done = Number(counts.succeeded) || 0;
      const stopped = Number(counts.canceled) || 0;
      const status = String(b.processing_status ?? '') || 'unknown';
      return {
        provider: 'anthropic',
        id: String(b.id),
        status,
        inFlight: status === 'canceling',
        done,
        stopped,
        total: done + stopped + (Number(counts.errored) || 0)
               + (Number(counts.expired) || 0) + (Number(counts.processing) || 0),
        artifact: b.results_url ?? null,
        cancelStarted: parseTime(b.cancel_initiated_at),
        billingKnown: true,
      };
    })
    .sort((a, b) => a.id.localeCompare(b.id));
}

/** Rows holding finished work a re-run would pay for again. Pure. */
export function salvageRows(rows) {
  return (rows ?? []).filter((r) => (Number(r?.done) || 0) > 0);
}

/** Rows still mid cancel past the threshold. Pure. now is an argument. */
export function stuckRows(rows, now, seconds = STUCK_SECONDS) {
  return (rows ?? []).filter((r) => {
    if (!r?.inFlight) return false;
    const started = r.cancelStarted;
    return started === null || started === undefined || now - started > seconds;
  });
}

/** Finished rows across everything cancelled. Pure. */
export function salvagedTotal(rows) {
  return salvageRows(rows).reduce((n, r) => n + (Number(r.done) || 0), 0);
}

/** Grade the run. Pure. Returns [state, detail]. */
export function verdict(rows, stuck, salvage) {
  const all = rows ?? [];
  const s = stuck ?? [];
  const v = salvage ?? [];
  if (!all.length) {
    return ['no-cancels',
      'no batch on the providers checked has had a cancellation initiated'];
  }
  if (s.length) {
    let detail = `${s.length} batch(es) have been mid cancel longer than the `
      + 'documented window';
    if (v.length) {
      detail += `, and ${v.length} cancelled batch(es) hold ${salvagedTotal(v)} `
        + 'finished rows nothing has collected';
    }
    return ['cancel-stuck', detail];
  }
  if (v.length) {
    return ['cancel-partial-unclaimed',
      `${v.length} cancelled batch(es) hold ${salvagedTotal(v)} finished rows a `
      + 're-run would pay for again'];
  }
  return ['cancel-clean',
    `${all.length} cancellation(s) found, none of which had completed a single `
    + 'request, so there is nothing to salvage and nothing to double pay'];
}

/** The repair for one verdict. Pure. Printed, never performed. */
export function repairLines(state, rows) {
  const all = rows ?? [];
  if (state === 'no-cancels') return [];
  if (state === 'cancel-clean') {
    return ['nothing to collect. Keep cancelling early: a batch stopped before '
      + 'its first request completed costs nothing.'];
  }
  const lines = [];
  if (state === 'cancel-stuck') {
    lines.push('a batch still in cancelling or canceling has not stopped. Poll '
      + 'it to a terminal state before you submit a replacement, or the two '
      + 'will run the same rows at once.');
  }
  if (all.some((r) => (Number(r?.done) || 0) > 0)) {
    lines.push('download the partial output, drop those custom_ids from the '
      + 'input file, and submit only the remainder. Results are not returned in '
      + 'request order, so custom_id is the only join key that works.');
  }
  if (all.some((r) => r?.provider === 'anthropic' && (Number(r.done) || 0) > 0)) {
    lines.push('on Anthropic, canceled and expired requests are not billed, so '
      + 'the succeeded count is the whole cost of the cancelled batch.');
  }
  if (all.some((r) => r?.provider === 'openai' && (Number(r.done) || 0) > 0)) {
    lines.push('on OpenAI the billing split for a cancelled batch is not '
      + 'documented, so treat the completed count as a floor and confirm the '
      + 'day against the cost report.');
  }
  return lines;
}

async function getJson(url, headers, params) {
  const target = new URL(url);
  for (const [k, v] of Object.entries(params ?? {})) target.searchParams.set(k, String(v));
  let res;
  try {
    res = await fetch(target, { headers });
  } catch (err) {
    return [null, `request failed: ${err.message}`];
  }
  if (res.status !== 200) return [null, `HTTP ${res.status}`];
  try {
    return [await res.json(), null];
  } catch {
    return [null, 'response was not JSON'];
  }
}

async function pageOpenai(key, maxPages) {
  const rows = [];
  let after = null;
  for (let i = 0; i < Math.max(1, maxPages); i += 1) {
    const params = { limit: 100 };
    if (after) params.after = after;
    const [payload, err] = await getJson(OPENAI_BATCHES_URL,
      { Authorization: `Bearer ${key}` }, params);
    if (err) return [rows, err];
    const data = payload.data ?? [];
    rows.push(...data);
    if (!payload.has_more || !data.length) break;
    after = data[data.length - 1]?.id;
  }
  return [rows, null];
}

async function pageAnthropic(key, maxPages) {
  const rows = [];
  let after = null;
  for (let i = 0; i < Math.max(1, maxPages); i += 1) {
    const params = { limit: 1000 };
    if (after) params.after_id = after;
    const [payload, err] = await getJson(ANTHROPIC_BATCHES_URL,
      { 'x-api-key': key, 'anthropic-version': '2023-06-01' }, params);
    if (err) return [rows, err];
    const data = payload.data ?? [];
    rows.push(...data);
    if (!payload.has_more || !data.length) break;
    after = payload.last_id ?? data[data.length - 1]?.id;
  }
  return [rows, null];
}

function args(argv) {
  const out = { stuckMinutes: 15, maxPages: 20 };
  for (let i = 0; i < argv.length; i += 1) {
    if (argv[i] === '--stuck-minutes') out.stuckMinutes = Number.parseInt(argv[i += 1], 10);
    else if (argv[i] === '--max-pages') out.maxPages = Number.parseInt(argv[i += 1], 10);
  }
  return out;
}

async function main() {
  const opts = args(process.argv.slice(2));
  const openaiKey = process.env.OPENAI_API_KEY;
  const anthropicKey = process.env.ANTHROPIC_API_KEY;
  if (!openaiKey && !anthropicKey) {
    console.error('set OPENAI_API_KEY (project key, Read Only) or '
      + 'ANTHROPIC_API_KEY (workspace key), or both');
    process.exitCode = 2;
    return;
  }

  const now = Math.floor(Date.now() / 1000);
  const rows = [];
  const checked = [];
  if (openaiKey) {
    checked.push('openai');
    const [batches, err] = await pageOpenai(openaiKey, opts.maxPages);
    if (err) console.log(`openai batch list stopped early: ${err}`);
    rows.push(...openaiCancelRows(batches));
  }
  if (anthropicKey) {
    checked.push('anthropic');
    const [batches, err] = await pageAnthropic(anthropicKey, opts.maxPages);
    if (err) console.log(`anthropic batch list stopped early: ${err}`);
    rows.push(...anthropicCancelRows(batches));
  }

  const stuck = stuckRows(rows, now, Math.max(1, opts.stuckMinutes) * 60);
  const salvage = salvageRows(rows);
  const stuckIds = new Set(stuck.map((r) => r.id));

  for (const r of rows) {
    console.log(`${r.provider.padEnd(11)} ${r.id.slice(0, 14).padEnd(14)} `
      + `${r.status.padEnd(11)} ${r.done} of ${r.total} done, ${r.stopped} stopped`);
    if (r.artifact) {
      const label = r.provider === 'openai' ? 'output_file_id' : 'results_url';
      console.log(`${''.padEnd(27)} ${label} present`);
    }
    if (stuckIds.has(r.id)) {
      const age = r.cancelStarted === null || r.cancelStarted === undefined
        ? 'an unknown time'
        : `${Math.floor((now - r.cancelStarted) / 60)} min`;
      console.log(`${r.provider.padEnd(11)} ${r.id.slice(0, 14).padEnd(14)}   `
        + `mid cancel for ${age}`);
    }
  }

  const [state, detail] = verdict(rows, stuck, salvage);
  console.log(`${state.padEnd(20)} ${detail}`);
  console.log(`  checked: ${checked.join(', ')}`);
  console.log('  measured: request_counts and the cancellation timestamps from '
    + 'the batch lists');
  console.log('  inferred: that a re-run would repeat the finished rows, since '
    + 'neither API records whether the partial output was downloaded');
  for (const line of repairLines(state, rows)) console.log(`  repair: ${line}`);

  const total = stuck.length + salvage.length;
  console.log(`${total} finding(s)`);
  process.exitCode = total ? 1 : 0;
  void FINDINGS;
}

if (import.meta.url === `file://${process.argv[1]}`) await main();
''',
"test_intro": "The first test is the arithmetic the repair rests on, run twice because the two providers spell it differently: OpenAI's <code>{total, completed, failed}</code> and Anthropic's <code>{processing, succeeded, errored, canceled, expired}</code> have to normalise to the same row, with the same finished count and the same stopped count. The second is the timestamp parser, which is handed a unix integer, an RFC 3339 string with a fractional second, one with an offset, and several kinds of rubbish, because a cancel age computed from a misparsed string is worse than no age at all. The third pins the stuck threshold to an argument rather than a clock, and includes the case where the timestamp is missing entirely &mdash; which has to count as stuck rather than as fine. The fourth is the ordering of verdicts: an unlanded cancel outranks a salvageable one, because billing may not have stopped. Then the clean cancel that produces no finding. And last the repair text, which must state the Anthropic billing rule and must not state an OpenAI one, since that one is not documented.",
"test_py_file": "test_batch_cancellation_audit.py",
"test_py": '''from batch_cancellation_audit import (anthropic_cancel_rows, openai_cancel_rows,
                                      parse_time, repair_lines, salvage_rows,
                                      salvaged_total, stuck_rows, verdict)

NOW = 1_800_000_000

OPENAI = [
    {"id": "batch_c1", "status": "cancelled",
     "request_counts": {"total": 90000, "completed": 61204, "failed": 0},
     "output_file_id": "file_7ac1", "cancelling_at": NOW - 7200,
     "cancelled_at": NOW - 6900},
    {"id": "batch_c2", "status": "cancelling",
     "request_counts": {"total": 400, "completed": 0, "failed": 0},
     "cancelling_at": NOW - 68 * 60},
    {"id": "batch_ok", "status": "completed",
     "request_counts": {"total": 10, "completed": 10, "failed": 0}},
]

ANTHROPIC = [
    {"id": "msgbatch_01Hq", "processing_status": "ended",
     "cancel_initiated_at": "2026-08-20T18:37:24.100435Z",
     "request_counts": {"processing": 0, "succeeded": 41880, "errored": 0,
                        "canceled": 12120, "expired": 0},
     "results_url": "https://api.anthropic.com/v1/messages/batches/x/results"},
    {"id": "msgbatch_02Zz", "processing_status": "in_progress",
     "cancel_initiated_at": None,
     "request_counts": {"processing": 500, "succeeded": 0, "errored": 0,
                        "canceled": 0, "expired": 0}},
]


def test_two_providers_normalise_to_one_row_shape():
    rows = openai_cancel_rows(OPENAI) + anthropic_cancel_rows(ANTHROPIC)
    assert [r["id"] for r in rows] == ["batch_c1", "batch_c2", "msgbatch_01Hq"]
    first = rows[0]
    assert first["done"] == 61204 and first["stopped"] == 28796
    assert first["total"] == 90000 and first["artifact"] == "file_7ac1"
    last = rows[2]
    # succeeded/canceled on Anthropic, and the counts sum to the total.
    assert last["done"] == 41880 and last["stopped"] == 12120
    assert last["total"] == 54000
    assert salvaged_total(rows) == 61204 + 41880
    # A batch with no cancellation initiated is never a row here.
    assert all(r["id"] != "msgbatch_02Zz" for r in rows)


def test_the_timestamp_parser_takes_both_providers_and_refuses_rubbish():
    assert parse_time(NOW) == NOW
    assert parse_time("2026-08-20T18:37:24Z") == 1787251044
    assert parse_time("2026-08-20T18:37:24.100435Z") == 1787251044
    assert parse_time("2026-08-20T18:37:24+00:00") == 1787251044
    for junk in (None, "", "yesterday", True, {}):
        assert parse_time(junk) is None


def test_a_stuck_cancel_is_measured_against_an_argument_not_a_clock():
    rows = openai_cancel_rows(OPENAI)
    stuck = stuck_rows(rows, NOW, 15 * 60)
    assert [r["id"] for r in stuck] == ["batch_c2"]
    # Generous threshold: the same batch is not stuck against a two hour one.
    assert stuck_rows(rows, NOW, 3 * 3600) == []
    # A missing cancelling_at on an in-flight cancel counts as stuck, because
    # "we cannot tell how long" is not the same as "it is fine".
    unknown = [{"id": "batch_x", "in_flight": True, "cancel_started": None,
                "done": 0}]
    assert stuck_rows(unknown, NOW, 15 * 60) == unknown
    # A terminal cancellation is never stuck however old it is.
    assert stuck_rows([rows[0]], NOW, 1) == []


def test_an_unlanded_cancel_outranks_a_salvageable_one():
    rows = openai_cancel_rows(OPENAI) + anthropic_cancel_rows(ANTHROPIC)
    stuck = stuck_rows(rows, NOW, 15 * 60)
    salvage = salvage_rows(rows)
    state, detail = verdict(rows, stuck, salvage)
    assert state == "cancel-stuck"
    assert "mid cancel" in detail and "103084 finished rows" in detail
    # Without the stuck one it drops to the salvage verdict.
    state2, detail2 = verdict(rows, [], salvage)
    assert state2 == "cancel-partial-unclaimed"
    assert "pay for again" in detail2


def test_a_cancel_that_landed_before_anything_ran_is_not_a_finding():
    early = [{"id": "batch_z", "provider": "openai", "status": "cancelled",
              "in_flight": False, "done": 0, "stopped": 400, "total": 400,
              "artifact": None, "cancel_started": NOW - 86400}]
    assert salvage_rows(early) == []
    state, detail = verdict(early, [], [])
    assert state == "cancel-clean"
    assert "nothing to salvage" in detail
    assert repair_lines(state, early)[0].startswith("nothing to collect")
    assert verdict([], [], []) == ("no-cancels",
                                  "no batch on the providers checked has had a "
                                  "cancellation initiated")
    assert repair_lines("no-cancels", []) == []


def test_the_repair_states_the_documented_billing_rule_and_only_that():
    rows = openai_cancel_rows(OPENAI) + anthropic_cancel_rows(ANTHROPIC)
    lines = repair_lines("cancel-partial-unclaimed", rows)
    assert any("custom_id is the only join key" in line for line in lines)
    assert any("canceled and expired requests are not billed" in line
               for line in lines)
    assert any("not documented" in line and "floor" in line for line in lines)
    # Anthropic only: no claim is made about OpenAI billing.
    only_anthropic = anthropic_cancel_rows(ANTHROPIC)
    lines2 = repair_lines("cancel-partial-unclaimed", only_anthropic)
    assert not any("floor" in line for line in lines2)
    assert any("cancelling or canceling has not stopped" in line
               for line in repair_lines("cancel-stuck", rows))
''',
"test_js_file": "batch-cancellation-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { anthropicCancelRows, openaiCancelRows, parseTime, repairLines,
         salvageRows, salvagedTotal, stuckRows,
         verdict } from './batch-cancellation-audit.mjs';

const NOW = 1800000000;

const OPENAI = [
  { id: 'batch_c1', status: 'cancelled',
    request_counts: { total: 90000, completed: 61204, failed: 0 },
    output_file_id: 'file_7ac1', cancelling_at: NOW - 7200, cancelled_at: NOW - 6900 },
  { id: 'batch_c2', status: 'cancelling',
    request_counts: { total: 400, completed: 0, failed: 0 },
    cancelling_at: NOW - 68 * 60 },
  { id: 'batch_ok', status: 'completed',
    request_counts: { total: 10, completed: 10, failed: 0 } },
];

const ANTHROPIC = [
  { id: 'msgbatch_01Hq', processing_status: 'ended',
    cancel_initiated_at: '2026-08-20T18:37:24.100435Z',
    request_counts: { processing: 0, succeeded: 41880, errored: 0, canceled: 12120,
                      expired: 0 },
    results_url: 'https://api.anthropic.com/v1/messages/batches/x/results' },
  { id: 'msgbatch_02Zz', processing_status: 'in_progress', cancel_initiated_at: null,
    request_counts: { processing: 500, succeeded: 0, errored: 0, canceled: 0,
                      expired: 0 } },
];

test('two providers normalise to one row shape', () => {
  const rows = [...openaiCancelRows(OPENAI), ...anthropicCancelRows(ANTHROPIC)];
  assert.deepEqual(rows.map((r) => r.id), ['batch_c1', 'batch_c2', 'msgbatch_01Hq']);
  assert.equal(rows[0].done, 61204);
  assert.equal(rows[0].stopped, 28796);
  assert.equal(rows[0].total, 90000);
  assert.equal(rows[0].artifact, 'file_7ac1');
  assert.equal(rows[2].done, 41880);
  assert.equal(rows[2].stopped, 12120);
  assert.equal(rows[2].total, 54000);
  assert.equal(salvagedTotal(rows), 61204 + 41880);
  assert.ok(rows.every((r) => r.id !== 'msgbatch_02Zz'));
});

test('the timestamp parser takes both providers and refuses rubbish', () => {
  assert.equal(parseTime(NOW), NOW);
  assert.equal(parseTime('2026-08-20T18:37:24Z'), 1787251044);
  assert.equal(parseTime('2026-08-20T18:37:24.100435Z'), 1787251044);
  assert.equal(parseTime('2026-08-20T18:37:24+00:00'), 1787251044);
  for (const junk of [null, undefined, '', 'yesterday', true, {}]) {
    assert.equal(parseTime(junk), null);
  }
});

test('a stuck cancel is measured against an argument not a clock', () => {
  const rows = openaiCancelRows(OPENAI);
  assert.deepEqual(stuckRows(rows, NOW, 15 * 60).map((r) => r.id), ['batch_c2']);
  assert.deepEqual(stuckRows(rows, NOW, 3 * 3600), []);
  const unknown = [{ id: 'batch_x', inFlight: true, cancelStarted: null, done: 0 }];
  assert.deepEqual(stuckRows(unknown, NOW, 15 * 60), unknown);
  assert.deepEqual(stuckRows([rows[0]], NOW, 1), []);
});

test('an unlanded cancel outranks a salvageable one', () => {
  const rows = [...openaiCancelRows(OPENAI), ...anthropicCancelRows(ANTHROPIC)];
  const stuck = stuckRows(rows, NOW, 15 * 60);
  const salvage = salvageRows(rows);
  const [state, detail] = verdict(rows, stuck, salvage);
  assert.equal(state, 'cancel-stuck');
  assert.ok(detail.includes('mid cancel') && detail.includes('103084 finished rows'));
  const [state2, detail2] = verdict(rows, [], salvage);
  assert.equal(state2, 'cancel-partial-unclaimed');
  assert.ok(detail2.includes('pay for again'));
});

test('a cancel that landed before anything ran is not a finding', () => {
  const early = [{ id: 'batch_z', provider: 'openai', status: 'cancelled',
                   inFlight: false, done: 0, stopped: 400, total: 400,
                   artifact: null, cancelStarted: NOW - 86400 }];
  assert.deepEqual(salvageRows(early), []);
  const [state, detail] = verdict(early, [], []);
  assert.equal(state, 'cancel-clean');
  assert.ok(detail.includes('nothing to salvage'));
  assert.ok(repairLines(state, early)[0].startsWith('nothing to collect'));
  assert.deepEqual(verdict([], [], []),
    ['no-cancels', 'no batch on the providers checked has had a cancellation initiated']);
  assert.deepEqual(repairLines('no-cancels', []), []);
});

test('the repair states the documented billing rule and only that', () => {
  const rows = [...openaiCancelRows(OPENAI), ...anthropicCancelRows(ANTHROPIC)];
  const lines = repairLines('cancel-partial-unclaimed', rows);
  assert.ok(lines.some((l) => l.includes('custom_id is the only join key')));
  assert.ok(lines.some((l) => l.includes('canceled and expired requests are not billed')));
  assert.ok(lines.some((l) => l.includes('not documented') && l.includes('floor')));
  const lines2 = repairLines('cancel-partial-unclaimed', anthropicCancelRows(ANTHROPIC));
  assert.ok(!lines2.some((l) => l.includes('floor')));
  assert.ok(repairLines('cancel-stuck', rows)
    .some((l) => l.includes('cancelling or canceling has not stopped')));
});
''',
"faq": [
 ("If I cancel a batch, am I charged for it?",
  "For the requests that had already been processed, yes. Anthropic documents the rule precisely: requests that end up <code>canceled</code> or <code>expired</code> were never sent to the model and are not billed, while the ones that succeeded were, and their results are in the batch's output. OpenAI documents that a cancelled batch keeps the partial results it produced but does not publish a billing split, so this script treats the <code>completed</code> count as a floor on what you paid there and tells you to confirm the day against the cost report rather than guessing."),
 ("Why is my batch stuck in cancelling?",
  "Because cancellation is asynchronous. OpenAI's documentation gives the window explicitly: the batch moves to <code>cancelling</code> and may stay there for up to ten minutes before it reaches <code>cancelled</code>. Anthropic's <code>canceling</code> state lasts until the requests already in flight finish and publishes no bound, so the only hard ceiling on that side is the batch's own <code>expires_at</code>, which is 24 hours after creation. Past the window, poll it to a terminal state before you assume the work has stopped."),
 ("Can I re-run only the rows that did not complete?",
  "Yes, and that is the whole repair. Download the partial output, collect the <code>custom_id</code> of every result that came back, remove those lines from the original input file, and submit the remainder. Results are explicitly not guaranteed to come back in request order on either provider, so <code>custom_id</code> is the only join key that works &mdash; which is also why a batch with duplicate or missing <code>custom_id</code> values cannot be reconciled at all and fails validation on OpenAI in the first place."),
 ("Does this script cancel or clean anything up?",
  "No. It issues GET requests to the two batch list endpoints and nothing else. It does not cancel a batch, does not download a result file, does not delete anything and does not re-submit the remainder, because every one of those either costs money or destroys evidence. What it produces is a list of ids with counts next to them and a printed repair you run yourself, after you have decided the rows are still wanted."),
 ("The batch shows cancelled but request_counts is all zeros. Is that a problem?",
  "No, that is the good outcome and the script reports it as <code>cancel-clean</code> with no finding. A cancellation that landed before any request completed leaves nothing to salvage, nothing that was billed, and nothing a re-run would pay for twice. It is worth distinguishing loudly from the two-thirds-finished case, because if both print the same way people stop reading the output, and then the case that matters gets skimmed past too."),
],
"related": [REL_PARTIAL, REL_OUTPUT, REL_DISCOUNT],
"citations": [CITE_OAI_BATCH_REF, CITE_OAI_BATCH_GUIDE, CITE_AN_BATCH_GUIDE, CITE_AN_BATCH_LIST],
},
{
"slug": "background-response-never-polled",
"title": "The background response is queued and nothing is polling",
"description": "background: true returns 200 immediately and puts the result only on the response object. Four of the six status values are not success. Poll your ids.",
"h1": "The background response is queued and nothing is polling",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["openai responses background true status queued",
             "responses api in_progress never completes",
             "GET /v1/responses/{id} 404 not found",
             "background response cancel abandoned job",
             "responses api incomplete_details reason"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Reads OPENAI_API_KEY, a project key set to Read Only, and a file of response ids from your own job table, because /v1/responses has no list endpoint. GET requests only.",
"lead": "The queue worker takes a job, starts a background response, writes the id somewhere, and returns. It is a good design: the request is accepted in a few hundred milliseconds and the model can take twenty minutes without holding a socket open. Then the worker is redeployed mid-shift, or the process that was going to poll gets an unhandled exception on a different code path, and the ids stop being read. The jobs keep running. They keep billing. And the only place their results exist is on an object nobody is asking about.",
"short_answer": """<p>Poll every id you hold. <code>GET /v1/responses/{response_id}</code> with a <strong>project key set to Read Only</strong>, one call per id, and bucket the answers by <code>status</code>. There is no list endpoint for <code>/v1/responses</code>, so the ids have to come from your own job table &mdash; which is the first thing the script checks, because if you cannot produce a list of ids then the jobs are already unreachable.</p>
<p><strong>The status enum has six values and four of them are not success.</strong> A background response moves through <code>queued</code> and <code>in_progress</code> and lands on one of <code>completed</code>, <code>incomplete</code>, <code>failed</code> or <code>cancelled</code>. The documentation's own instruction is to keep polling while it is <code>queued</code> or <code>in_progress</code>, because leaving those two states is the definition of terminal.</p>
<p>Read the reason, not just the status. <code>failed</code> carries an <code>error</code> object whose <code>code</code> separates the retryable from the escalatable: <code>server_error</code> and <code>rate_limit_exceeded</code> want a retry, <code>invalid_prompt</code> wants a person. <code>incomplete</code> carries <code>incomplete_details.reason</code>, which is <code>max_output_tokens</code> or <code>content_filter</code>.</p>
<p><strong>A 404 is two different things and the script makes you say which.</strong> On an ordinary project, an id that does not resolve is a lost job. On a zero-data-retention project, background responses run with <code>store</code> false and are kept on disk only for roughly ten minutes to make polling possible at all, so a 404 on an old id is the platform behaving exactly as documented. Pass <code>--zdr</code> and the script reports those separately instead of alarming on them.</p>""",
"problem": """<p>Background mode moves the failure surface from your process to a stored object. Without it, a request that takes twenty minutes fails as a timeout somewhere in your stack, loudly and in a place with a stack trace. With it, the request is accepted in milliseconds, the 200 says only that the job was queued, and everything that happens afterwards happens on a response object that has no way to tell you about it. There is no callback in the basic flow. Nothing pushes.</p>
<p>So the abandoned job is invisible from both ends. Your side has a row in a table with no terminal status and no error, which looks the same as a job that is simply still running. The platform's side has a response that reached <code>failed</code> two hours ago and has been sitting there ever since. Neither half raises anything, and the two halves never meet unless somebody writes the reconciler.</p>
<p>The costs stack up in three ways. Work that completed is billed and thrown away, because the output existed only on the object nobody read. Work that is genuinely still queued holds capacity you are not using. And work that failed on something retryable &mdash; a <code>server_error</code>, a <code>rate_limit_exceeded</code> &mdash; is not retried, so a transient blip becomes a permanently missing result.</p>
<p>The awkward part is that the API cannot help you find them. <code>/v1/responses</code> has no list endpoint. You cannot ask for every response your project created, cannot filter by status, and cannot enumerate what you have forgotten. The reconciliation is bounded by the ids you wrote down, which makes the durability of that write the actual failure point: if the id is persisted after the job starts rather than transactionally with it, a crash in between produces a job that is running, billing, and unreferenced anywhere.</p>""",
"why": """<p><strong>Four of the six statuses are not success, and the two that look temporary are the dangerous ones.</strong> <code>queued</code> and <code>in_progress</code> are perfectly normal for a job that started forty seconds ago and are a finding for one that started yesterday. That means the check needs a service level to compare against rather than a fixed number, so the threshold is an argument, and the same id is graded differently depending on what your queue promises.</p>
<p><strong>The error object is the difference between a retry and a page.</strong> The Responses error <code>code</code> is an enumeration, and it separates infrastructure from input: <code>server_error</code> and <code>rate_limit_exceeded</code> are things that will probably work on the next attempt, while <code>invalid_prompt</code> will fail identically forever. A reconciler that retries everything hammers a broken request, and one that retries nothing loses recoverable work, so the script prints the code and sorts the two apart.</p>
<p><strong>There is no list endpoint, and pretending otherwise would produce a clean run on an empty audit.</strong> <code>/v1/responses</code> is reachable only by an id you already hold. So the script takes a file of ids, reports how many it was given, and treats an empty file as a finding in its own right &mdash; the absence of a job table is a worse problem than anything in it.</p>
<p><strong>A 404 needs context the API will not give you.</strong> Retrieving a response that was never stored, or whose retention has elapsed, returns a not-found. Whether that is a lost job or documented behaviour depends on the project's data-retention posture: on a zero-data-retention project a background response runs with <code>store</code> false and is retained for roughly ten minutes purely to make polling work. The script therefore takes <code>--zdr</code> as a declaration from you and grades the same HTTP status differently, rather than guessing and being confidently wrong half the time.</p>
<p><strong>Only background responses can be cancelled, which is why abandonment is worth finding.</strong> The cancel endpoint is documented as applying to responses created with <code>background</code> set to true and to no others. So the stranded jobs this script finds are exactly the population you can actually do something about, and the repair for a queued job that nobody wants any more is a real action rather than waiting for it to finish and paying for it.</p>""",
"steps": [
 {"h": "Produce the id list first",
  "body": """<p>One response id per line, optionally followed by a comma and the unix timestamp your table recorded at creation. There is no list endpoint, so this file is the audit's entire universe. If you cannot produce it, stop here: that is the finding, and the repair is to persist the id transactionally with the job row rather than after the call returns.</p>"""},
 {"h": "Use a project key set to Read Only",
  "body": """<p>One <code>GET /v1/responses/{response_id}</code> per id. The script does not cancel anything, does not re-run anything and does not create a response. Cancelling an abandoned job is often the right repair, but it is destructive, and it is printed for you rather than performed.</p>"""},
 {"h": "Declare your service level",
  "body": """<p><code>--sla-minutes</code> is the age past which <code>queued</code> or <code>in_progress</code> stops being normal. A minute-scale interactive queue and an overnight document pipeline are both correct and want very different numbers, so this is an argument rather than a constant. The value used is printed with the result.</p>"""},
 {"h": "Say whether the project is zero-data-retention",
  "body": """<p><code>--zdr</code> changes how a 404 is graded. On a ZDR project, background responses run unstored and are kept for roughly ten minutes to allow polling at all, so an old id that does not resolve is documented behaviour rather than a lost job. Without the flag, the same 404 is reported as a job whose result is gone.</p>"""},
 {"h": "Read the reasons and split the retries from the escalations",
  "body": """<p>The output groups by bucket and prints the <code>error.code</code> or <code>incomplete_details.reason</code> next to each id. The repair is printed: retry <code>server_error</code> and <code>rate_limit_exceeded</code>, escalate <code>invalid_prompt</code>, raise <code>max_output_tokens</code> or accept the truncation, and cancel the queued jobs nobody wants.</p>"""},
],
"verify": """<p>Re-run after the reconciler exists. What should change is not this script's verdict but the size of its input: a job table that is being driven to terminal states has few open ids in it, and the ones it has are younger than the service level. Run it on a schedule against the open rows only, and treat a <code>stranded</code> count above zero as the alarm rather than as a report.</p>
<pre><code class="language-bash">python3 openai_background_response_audit.py --ids open_jobs.txt --sla-minutes 30
# resp_68f1a2c4   stranded     in_progress for 19 h
# resp_68f1a2d9   stranded     queued for 19 h
# resp_68e94411   failed       error.code server_error
# resp_68e944a7   failed       error.code invalid_prompt
# resp_68e94500   incomplete   incomplete_details.reason max_output_tokens
# resp_68d21a03   gone         HTTP 404, no longer retrievable
# resp_68f9bb10   running      queued for 4 min, inside the 30 min service level
# resp_68f9bb2a   completed
# background-stranded  2 of 8 ids have been queued or in_progress past the 30
#                      minute service level, 2 failed and 1 is no longer
#                      retrievable
#   measured: status, error.code and incomplete_details.reason from one GET per id
#   inferred: nothing about ids not in the file, because /v1/responses has no
#             list endpoint and cannot be enumerated
#   repair: retry server_error and rate_limit_exceeded; escalate invalid_prompt,
#           which will fail identically on every attempt.
#   repair: cancel the stranded jobs you no longer want. Only responses created
#           with background true can be cancelled, so these ones can be.
# 5 finding(s)</code></pre>""",
"code_intro": "One GET per id and six pure functions. <code>read_ids</code>, which takes a plain id or an id with the creation timestamp your table recorded, and de-duplicates while keeping order so the output reads like your job table; <code>age_of</code>, which prefers the response's own <code>created_at</code> and falls back to your hint, because a 404 has no object to read an age from; <code>reason_for</code>, which reaches for <code>error.code</code> and then <code>incomplete_details.reason</code> and returns an empty string rather than a null that gets printed; <code>classify</code>, which is the whole grading and takes <code>now</code>, the service level and the ZDR declaration as arguments; <code>summarise</code>, which counts the buckets in a fixed order so the output does not reshuffle between runs; and <code>verdict</code>, which puts a stranded job ahead of a failed one because it is still spending money.",
"py_file": "openai_background_response_audit.py",
"py": '''"""Drive every background response id you hold to a terminal status.

Read only. One GET /v1/responses/{response_id} per id and nothing else. This
script does not create a response, does not cancel one and does not retry
anything: cancelling is destructive and retrying costs money, so both are
printed for a human to run.

/v1/responses has no list endpoint. The ids come from your own job table, which
means the audit is bounded by what you wrote down, and the script says so with
every result rather than implying it enumerated anything.

A 404 is graded differently on a zero-data-retention project, where background
responses run unstored and are retained for roughly ten minutes purely so that
polling works at all. Pass --zdr and those stop being reported as lost jobs.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("openai_background_response_audit")

RESPONSES_URL = "https://api.openai.com/v1/responses"

# The documented status enum. Four of the six are not success, and the two that
# look temporary are the ones worth an alarm when they stop being temporary.
OPEN_STATES = ("queued", "in_progress")
TERMINAL_STATES = ("completed", "incomplete", "failed", "cancelled")

# Roughly how long a ZDR project keeps a background response on disk so that it
# can be polled at all. Past this, a 404 there is documented behaviour.
ZDR_WINDOW = 600

BUCKET_ORDER = ("stranded", "failed", "incomplete", "gone", "cancelled",
                "running", "completed", "aged-out", "unreadable")

RETRYABLE = ("server_error", "rate_limit_exceeded")

FINDINGS = ("background-stranded", "background-failed", "background-gone",
            "background-no-ids")


def read_ids(text):
    """[(id, created_hint)] from a file body. Pure. Order kept, ids deduped.

    A line is either an id or "id,<unix timestamp>". The timestamp is what your
    own table recorded at creation, and it is the only way to age a 404, which
    has no object behind it to read a created_at from.
    """
    out, seen = [], set()
    for raw in (text or "").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        ident, _, stamp = line.partition(",")
        ident = ident.strip()
        if not ident or ident in seen:
            continue
        seen.add(ident)
        try:
            hint = int(float(stamp.strip())) if stamp.strip() else None
        except ValueError:
            hint = None
        out.append((ident, hint))
    return out


def age_of(response, hint, now):
    """Seconds since creation. Pure. None when neither source has a time."""
    created = (response or {}).get("created_at")
    try:
        created = int(created)
    except (TypeError, ValueError):
        created = None
    if created is None:
        created = hint
    if created is None:
        return None
    return max(0, int(now) - int(created))


def reason_for(response):
    """The failure reason, or "". Pure. Never returns None to be printed."""
    response = response or {}
    error = response.get("error") or {}
    if isinstance(error, dict) and error.get("code"):
        return "error.code %s" % error["code"]
    details = response.get("incomplete_details") or {}
    if isinstance(details, dict) and details.get("reason"):
        return "incomplete_details.reason %s" % details["reason"]
    return ""


def error_code(response):
    """Just the error code, or "". Pure. Used to sort retry from escalate."""
    error = (response or {}).get("error") or {}
    return str(error.get("code") or "") if isinstance(error, dict) else ""


def classify(record, now, sla_seconds, zdr=False):
    """(bucket, detail) for one id. Pure. now and the SLA are arguments.

    The same HTTP 404 is a lost job on an ordinary project and documented
    behaviour on a ZDR one, so the declaration is taken from the caller rather
    than guessed from a field that does not exist.
    """
    http = (record or {}).get("http")
    response = (record or {}).get("response") or {}
    hint = (record or {}).get("created_hint")
    age = age_of(response, hint, now)
    if http == 404:
        if zdr and (age is None or age > ZDR_WINDOW):
            return ("aged-out",
                    "HTTP 404, and on a ZDR project a background response is "
                    "kept only about ten minutes")
        return ("gone", "HTTP 404, no longer retrievable")
    if http != 200:
        return ("unreadable", "HTTP %s" % http)
    status = str(response.get("status") or "")
    if status in OPEN_STATES:
        shown = "%d min" % (age // 60) if age is not None else "an unknown time"
        if age is not None and age > sla_seconds:
            return ("stranded", "%s for %s" % (status, shown))
        return ("running", "%s for %s, inside the service level" % (status, shown))
    if status == "failed":
        return ("failed", reason_for(response) or "failed with no error object")
    if status == "incomplete":
        return ("incomplete", reason_for(response) or "incomplete with no reason")
    if status == "cancelled":
        return ("cancelled", "cancelled")
    if status == "completed":
        return ("completed", "")
    return ("unreadable", "status %r is not one of the six documented values"
            % status)


def summarise(rows):
    """{bucket: count} in a fixed order. Pure. Empty buckets are omitted."""
    counts = {}
    for row in rows or []:
        counts[row.get("bucket")] = counts.get(row.get("bucket"), 0) + 1
    return {b: counts[b] for b in BUCKET_ORDER if b in counts}


def verdict(rows, sla_seconds):
    """Grade the run. Pure. Returns (state, detail)."""
    rows = list(rows or [])
    if not rows:
        return ("background-no-ids",
                "no response ids were supplied. /v1/responses has no list "
                "endpoint, so an empty id file means those jobs are already "
                "unreachable")
    counts = summarise(rows)
    minutes = max(1, int(sla_seconds // 60))
    stranded = counts.get("stranded", 0)
    failed = counts.get("failed", 0)
    gone = counts.get("gone", 0)
    tail = ""
    if failed or gone:
        parts = []
        if failed:
            parts.append("%d failed" % failed)
        if gone:
            parts.append("%d is no longer retrievable" % gone)
        tail = ", " + " and ".join(parts)
    if stranded:
        return ("background-stranded",
                "%d of %d ids have been queued or in_progress past the %d "
                "minute service level%s" % (stranded, len(rows), minutes, tail))
    if failed:
        return ("background-failed",
                "%d of %d ids reached failed and nothing read the error code%s"
                % (failed, len(rows), ", %d is no longer retrievable" % gone
                   if gone else ""))
    if gone:
        return ("background-gone",
                "%d of %d ids no longer resolve, so whatever they produced is "
                "gone" % (gone, len(rows)))
    return ("background-drained",
            "all %d ids are terminal or inside the %d minute service level"
            % (len(rows), minutes))


def repair_lines(state, rows):
    """The repair for one verdict. Pure. Printed, never performed."""
    rows = list(rows or [])
    if state == "background-no-ids":
        return ["persist the response id transactionally with the job row, not "
                "after the call returns. A crash in between leaves a job that "
                "runs, bills, and is referenced nowhere.",
                "there is no list endpoint for /v1/responses, so an id you did "
                "not write down cannot be recovered by any read call."]
    if state == "background-drained":
        return ["nothing stranded. Keep the reconciler running: the failure "
                "mode here is a poller that stops, not one that is wrong."]
    lines = []
    codes = {row.get("code") for row in rows if row.get("code")}
    if codes & set(RETRYABLE):
        lines.append("retry the transient codes (%s), which will usually "
                     "succeed on a second attempt."
                     % ", ".join(sorted(codes & set(RETRYABLE))))
    if codes - set(RETRYABLE):
        lines.append("escalate %s. These fail identically on every attempt, so "
                     "a retry loop only spends money."
                     % ", ".join(sorted(codes - set(RETRYABLE))))
    if any(row.get("bucket") == "stranded" for row in rows):
        lines.append("cancel the stranded jobs you no longer want, at "
                     "/v1/responses/{response_id}/cancel. Only responses "
                     "created with background true can be cancelled, so these "
                     "ones can be.")
    if any(row.get("bucket") == "incomplete" for row in rows):
        lines.append("an incomplete response was cut rather than refused. Read "
                     "incomplete_details.reason: max_output_tokens wants a "
                     "bigger cap, content_filter wants a person.")
    if any(row.get("bucket") == "gone" for row in rows):
        lines.append("an id that no longer resolves cannot be recovered by any "
                     "read call. Archive the output at the moment a response "
                     "reaches completed, not on the next run of a nightly job.")
    return lines


def fetch(response_id, key, timeout=30):
    """One GET. Returns (http_status, payload). Read only, always."""
    try:
        r = requests.get("%s/%s" % (RESPONSES_URL, response_id),
                         headers={"Authorization": "Bearer %s" % key},
                         timeout=timeout)
    except requests.RequestException:
        return (None, {})
    try:
        return (r.status_code, r.json())
    except ValueError:
        return (r.status_code, {})


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ids", help="file of response ids, one per line, "
                                  "optionally id,<unix created_at>")
    ap.add_argument("--sla-minutes", type=int, default=30,
                    help="age past which queued or in_progress is a finding")
    ap.add_argument("--zdr", action="store_true",
                    help="this project is zero data retention, so a 404 on an "
                         "old background response is documented behaviour")
    args = ap.parse_args()

    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        log.error("set OPENAI_API_KEY to a project key set to Read Only")
        return 2

    raw = ""
    if args.ids:
        try:
            with open(args.ids, "r", encoding="utf-8") as fh:
                raw = fh.read()
        except OSError as exc:
            log.error("could not read %s: %s", args.ids, exc)
            return 2
    else:
        raw = os.environ.get("OPENAI_RESPONSE_IDS", "").replace(",", "\\n")

    pairs = read_ids(raw)
    now = int(time.time())
    sla = max(1, args.sla_minutes) * 60
    rows = []
    for ident, hint in pairs:
        http, payload = fetch(ident, key)
        bucket, detail = classify({"http": http, "response": payload,
                                   "created_hint": hint}, now, sla, args.zdr)
        rows.append({"id": ident, "bucket": bucket, "detail": detail,
                     "code": error_code(payload)})
        emit = log.warning if bucket in ("stranded", "failed", "gone") else log.info
        emit("%-16s %-12s %s", ident[:16], bucket, detail)

    state, detail = verdict(rows, sla)
    emit = log.warning if state in FINDINGS else log.info
    emit("%-20s %s", state, detail)
    counts = summarise(rows)
    if counts:
        emit("  buckets: %s", ", ".join("%s %d" % (k, v) for k, v in counts.items()))
    emit("  measured: status, error.code and incomplete_details.reason from one "
         "GET per id")
    emit("  inferred: nothing about ids not in the file, because /v1/responses "
         "has no list endpoint and cannot be enumerated")
    for line in repair_lines(state, rows):
        emit("  repair: %s", line)

    findings = sum(counts.get(b, 0) for b in ("stranded", "failed", "gone"))
    if state == "background-no-ids":
        findings = 1
    log.info("%d finding(s)", findings)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "openai-background-response-audit.mjs",
"js": '''/**
 * Drive every background response id you hold to a terminal status.
 *
 * Read only. One GET /v1/responses/{response_id} per id. Nothing is created,
 * cancelled or retried.
 *
 * /v1/responses has no list endpoint, so the ids come from your own job table
 * and the audit is bounded by what you wrote down.
 *
 * A 404 is graded differently on a zero-data-retention project, where a
 * background response is kept for roughly ten minutes so polling can work.
 */
import { readFile } from 'node:fs/promises';

const RESPONSES_URL = 'https://api.openai.com/v1/responses';

export const OPEN_STATES = new Set(['queued', 'in_progress']);
export const TERMINAL_STATES = new Set(['completed', 'incomplete', 'failed', 'cancelled']);

export const ZDR_WINDOW = 600;

export const BUCKET_ORDER = ['stranded', 'failed', 'incomplete', 'gone', 'cancelled',
  'running', 'completed', 'aged-out', 'unreadable'];

export const RETRYABLE = ['server_error', 'rate_limit_exceeded'];

const FINDINGS = new Set(['background-stranded', 'background-failed',
  'background-gone', 'background-no-ids']);

/** [[id, createdHint]] from a file body. Pure. Order kept, ids deduped. */
export function readIds(text) {
  const out = [];
  const seen = new Set();
  for (const raw of String(text ?? '').split('\\n')) {
    const line = raw.trim();
    if (!line || line.startsWith('#')) continue;
    const at = line.indexOf(',');
    const ident = (at < 0 ? line : line.slice(0, at)).trim();
    const stamp = at < 0 ? '' : line.slice(at + 1).trim();
    if (!ident || seen.has(ident)) continue;
    seen.add(ident);
    const parsed = Number.parseFloat(stamp);
    out.push([ident, Number.isFinite(parsed) ? Math.trunc(parsed) : null]);
  }
  return out;
}

/** Seconds since creation. Pure. Null when neither source has a time. */
export function ageOf(response, hint, now) {
  const raw = Number((response ?? {}).created_at);
  const created = Number.isFinite(raw) ? Math.trunc(raw)
    : (Number.isFinite(Number(hint)) && hint !== null ? Math.trunc(Number(hint)) : null);
  if (created === null) return null;
  return Math.max(0, Math.trunc(now) - created);
}

/** The failure reason, or ''. Pure. Never returns null to be printed. */
export function reasonFor(response) {
  const r = response ?? {};
  const error = r.error;
  if (error && typeof error === 'object' && error.code) return `error.code ${error.code}`;
  const details = r.incomplete_details;
  if (details && typeof details === 'object' && details.reason) {
    return `incomplete_details.reason ${details.reason}`;
  }
  return '';
}

/** Just the error code, or ''. Pure. */
export function errorCode(response) {
  const error = (response ?? {}).error;
  return error && typeof error === 'object' ? String(error.code ?? '') : '';
}

/** [bucket, detail] for one id. Pure. now, the SLA and ZDR are arguments. */
export function classify(record, now, slaSeconds, zdr = false) {
  const http = (record ?? {}).http;
  const response = (record ?? {}).response ?? {};
  const age = ageOf(response, (record ?? {}).created_hint, now);
  if (http === 404) {
    if (zdr && (age === null || age > ZDR_WINDOW)) {
      return ['aged-out', 'HTTP 404, and on a ZDR project a background response '
        + 'is kept only about ten minutes'];
    }
    return ['gone', 'HTTP 404, no longer retrievable'];
  }
  if (http !== 200) return ['unreadable', `HTTP ${http}`];
  const status = String(response.status ?? '');
  if (OPEN_STATES.has(status)) {
    const shown = age === null ? 'an unknown time' : `${Math.floor(age / 60)} min`;
    if (age !== null && age > slaSeconds) return ['stranded', `${status} for ${shown}`];
    return ['running', `${status} for ${shown}, inside the service level`];
  }
  if (status === 'failed') {
    return ['failed', reasonFor(response) || 'failed with no error object'];
  }
  if (status === 'incomplete') {
    return ['incomplete', reasonFor(response) || 'incomplete with no reason'];
  }
  if (status === 'cancelled') return ['cancelled', 'cancelled'];
  if (status === 'completed') return ['completed', ''];
  return ['unreadable',
    `status ${JSON.stringify(status)} is not one of the six documented values`];
}

/** {bucket: count} in a fixed order. Pure. Empty buckets are omitted. */
export function summarise(rows) {
  const counts = new Map();
  for (const row of rows ?? []) {
    counts.set(row?.bucket, (counts.get(row?.bucket) ?? 0) + 1);
  }
  const out = {};
  for (const b of BUCKET_ORDER) if (counts.has(b)) out[b] = counts.get(b);
  return out;
}

/** Grade the run. Pure. Returns [state, detail]. */
export function verdict(rows, slaSeconds) {
  const list = rows ?? [];
  if (!list.length) {
    return ['background-no-ids',
      'no response ids were supplied. /v1/responses has no list endpoint, so an '
      + 'empty id file means those jobs are already unreachable'];
  }
  const counts = summarise(list);
  const minutes = Math.max(1, Math.trunc(slaSeconds / 60));
  const stranded = counts.stranded ?? 0;
  const failed = counts.failed ?? 0;
  const gone = counts.gone ?? 0;
  let tail = '';
  if (failed || gone) {
    const parts = [];
    if (failed) parts.push(`${failed} failed`);
    if (gone) parts.push(`${gone} is no longer retrievable`);
    tail = `, ${parts.join(' and ')}`;
  }
  if (stranded) {
    return ['background-stranded',
      `${stranded} of ${list.length} ids have been queued or in_progress past `
      + `the ${minutes} minute service level${tail}`];
  }
  if (failed) {
    return ['background-failed',
      `${failed} of ${list.length} ids reached failed and nothing read the error `
      + `code${gone ? `, ${gone} is no longer retrievable` : ''}`];
  }
  if (gone) {
    return ['background-gone',
      `${gone} of ${list.length} ids no longer resolve, so whatever they `
      + 'produced is gone'];
  }
  return ['background-drained',
    `all ${list.length} ids are terminal or inside the ${minutes} minute service level`];
}

/** The repair for one verdict. Pure. Printed, never performed. */
export function repairLines(state, rows) {
  const list = rows ?? [];
  if (state === 'background-no-ids') {
    return ['persist the response id transactionally with the job row, not after '
      + 'the call returns. A crash in between leaves a job that runs, bills, and '
      + 'is referenced nowhere.',
    'there is no list endpoint for /v1/responses, so an id you did not write '
      + 'down cannot be recovered by any read call.'];
  }
  if (state === 'background-drained') {
    return ['nothing stranded. Keep the reconciler running: the failure mode '
      + 'here is a poller that stops, not one that is wrong.'];
  }
  const lines = [];
  const codes = new Set(list.map((r) => r?.code).filter(Boolean));
  const retry = [...codes].filter((c) => RETRYABLE.includes(c)).sort();
  const escalate = [...codes].filter((c) => !RETRYABLE.includes(c)).sort();
  if (retry.length) {
    lines.push(`retry the transient codes (${retry.join(', ')}), which will `
      + 'usually succeed on a second attempt.');
  }
  if (escalate.length) {
    lines.push(`escalate ${escalate.join(', ')}. These fail identically on every `
      + 'attempt, so a retry loop only spends money.');
  }
  if (list.some((r) => r?.bucket === 'stranded')) {
    lines.push('cancel the stranded jobs you no longer want, at '
      + '/v1/responses/{response_id}/cancel. Only responses created with '
      + 'background true can be cancelled, so these ones can be.');
  }
  if (list.some((r) => r?.bucket === 'incomplete')) {
    lines.push('an incomplete response was cut rather than refused. Read '
      + 'incomplete_details.reason: max_output_tokens wants a bigger cap, '
      + 'content_filter wants a person.');
  }
  if (list.some((r) => r?.bucket === 'gone')) {
    lines.push('an id that no longer resolves cannot be recovered by any read '
      + 'call. Archive the output at the moment a response reaches completed, '
      + 'not on the next run of a nightly job.');
  }
  return lines;
}

async function fetchOne(id, key) {
  let res;
  try {
    res = await fetch(`${RESPONSES_URL}/${id}`, {
      headers: { Authorization: `Bearer ${key}` },
    });
  } catch {
    return [null, {}];
  }
  try {
    return [res.status, await res.json()];
  } catch {
    return [res.status, {}];
  }
}

function args(argv) {
  const out = { slaMinutes: 30, zdr: false };
  for (let i = 0; i < argv.length; i += 1) {
    if (argv[i] === '--ids') out.ids = argv[i += 1];
    else if (argv[i] === '--sla-minutes') out.slaMinutes = Number.parseInt(argv[i += 1], 10);
    else if (argv[i] === '--zdr') out.zdr = true;
  }
  return out;
}

async function main() {
  const opts = args(process.argv.slice(2));
  const key = process.env.OPENAI_API_KEY;
  if (!key) {
    console.error('set OPENAI_API_KEY to a project key set to Read Only');
    process.exitCode = 2;
    return;
  }

  let raw = '';
  if (opts.ids) {
    try {
      raw = await readFile(opts.ids, 'utf8');
    } catch (err) {
      console.error(`could not read ${opts.ids}: ${err.message}`);
      process.exitCode = 2;
      return;
    }
  } else {
    raw = (process.env.OPENAI_RESPONSE_IDS ?? '').split(',').join('\\n');
  }

  const pairs = readIds(raw);
  const now = Math.floor(Date.now() / 1000);
  const sla = Math.max(1, opts.slaMinutes) * 60;
  const rows = [];
  for (const [ident, hint] of pairs) {
    const [http, payload] = await fetchOne(ident, key);
    const [bucket, detail] = classify({ http, response: payload, created_hint: hint },
      now, sla, opts.zdr);
    rows.push({ id: ident, bucket, detail, code: errorCode(payload) });
    console.log(`${ident.slice(0, 16).padEnd(16)} ${bucket.padEnd(12)} ${detail}`);
  }

  const [state, detail] = verdict(rows, sla);
  console.log(`${state.padEnd(20)} ${detail}`);
  const counts = summarise(rows);
  if (Object.keys(counts).length) {
    console.log(`  buckets: ${Object.entries(counts).map(([k, v]) => `${k} ${v}`).join(', ')}`);
  }
  console.log('  measured: status, error.code and incomplete_details.reason from '
    + 'one GET per id');
  console.log('  inferred: nothing about ids not in the file, because '
    + '/v1/responses has no list endpoint and cannot be enumerated');
  for (const line of repairLines(state, rows)) console.log(`  repair: ${line}`);

  let findings = ['stranded', 'failed', 'gone'].reduce((n, b) => n + (counts[b] ?? 0), 0);
  if (state === 'background-no-ids') findings = 1;
  console.log(`${findings} finding(s)`);
  process.exitCode = findings ? 1 : 0;
  void FINDINGS;
  void TERMINAL_STATES;
}

if (import.meta.url === `file://${process.argv[1]}`) await main();
''',
"test_intro": "The first test walks one id through each of the six documented statuses and asserts a distinct bucket for each, because collapsing <code>incomplete</code> into <code>failed</code> or <code>cancelled</code> into <code>completed</code> would hide exactly the cases that need a different repair. The second is the service level: the same <code>in_progress</code> response is <code>running</code> against a thirty minute promise and <code>stranded</code> against a three minute one, with <code>now</code> and the threshold passed in so the assertion does not depend on when it runs. The third is the 404, graded twice &mdash; a lost job on an ordinary project and documented behaviour on a ZDR one &mdash; and it also covers the case where no timestamp is available at all. The fourth is the id file parser, given blank lines, comments, duplicates, a bare id and an id with a timestamp. The fifth is that an empty id list is a finding rather than a clean run, which is the single most important behaviour in the script. And the last checks the retry split, where <code>server_error</code> and <code>invalid_prompt</code> must not end up in the same repair line.",
"test_py_file": "test_openai_background_response_audit.py",
"test_py": '''from openai_background_response_audit import (age_of, classify, error_code,
                                              read_ids, reason_for,
                                              repair_lines, summarise, verdict)

NOW = 1_800_000_000
SLA = 30 * 60


def record(status, created=None, http=200, **extra):
    body = {"id": "resp_x", "status": status}
    if created is not None:
        body["created_at"] = created
    body.update(extra)
    return {"http": http, "response": body, "created_hint": None}


def test_each_documented_status_gets_its_own_bucket():
    assert classify(record("completed", NOW - 60), NOW, SLA)[0] == "completed"
    assert classify(record("cancelled", NOW - 60), NOW, SLA)[0] == "cancelled"
    incomplete = record("incomplete", NOW - 60,
                        incomplete_details={"reason": "max_output_tokens"})
    bucket, detail = classify(incomplete, NOW, SLA)
    assert bucket == "incomplete" and "max_output_tokens" in detail
    failed = record("failed", NOW - 60,
                    error={"code": "server_error", "message": "boom"})
    bucket, detail = classify(failed, NOW, SLA)
    assert bucket == "failed" and "error.code server_error" in detail
    assert error_code(failed["response"]) == "server_error"
    # A status outside the enum is not silently treated as success.
    assert classify(record("weird", NOW), NOW, SLA)[0] == "unreadable"
    assert reason_for({}) == ""


def test_queued_is_normal_until_the_service_level_says_it_is_not():
    running = record("in_progress", NOW - 4 * 60)
    bucket, detail = classify(running, NOW, SLA)
    assert bucket == "running" and "inside the service level" in detail
    bucket, detail = classify(running, NOW, 3 * 60)
    assert bucket == "stranded" and detail.startswith("in_progress for 4 min")
    queued = record("queued", NOW - 19 * 3600)
    assert classify(queued, NOW, SLA)[0] == "stranded"
    # The hint from your own table stands in when the object has no created_at.
    no_stamp = {"http": 200, "response": {"status": "queued"},
                "created_hint": NOW - 7200}
    assert classify(no_stamp, NOW, SLA)[0] == "stranded"
    assert age_of({}, None, NOW) is None
    assert classify({"http": 200, "response": {"status": "queued"},
                     "created_hint": None}, NOW, SLA)[0] == "running"


def test_a_404_means_two_different_things_and_zdr_decides_which():
    lost = {"http": 404, "response": {}, "created_hint": NOW - 86400}
    assert classify(lost, NOW, SLA)[0] == "gone"
    bucket, detail = classify(lost, NOW, SLA, zdr=True)
    assert bucket == "aged-out" and "ten minutes" in detail
    # Inside the ZDR window a 404 is still a real miss.
    fresh = {"http": 404, "response": {}, "created_hint": NOW - 60}
    assert classify(fresh, NOW, SLA, zdr=True)[0] == "gone"
    assert classify({"http": 500, "response": {}}, NOW, SLA)[0] == "unreadable"


def test_the_id_file_takes_bare_ids_timestamps_comments_and_duplicates():
    text = "\\n".join(["# open jobs", "", "resp_a", "resp_b,1799990000",
                      "resp_a", "  resp_c , not-a-number  "])
    assert read_ids(text) == [("resp_a", None), ("resp_b", 1799990000),
                              ("resp_c", None)]
    assert read_ids("") == []
    assert read_ids(None) == []


def test_an_empty_id_list_is_a_finding_and_not_a_clean_run():
    state, detail = verdict([], SLA)
    assert state == "background-no-ids"
    assert "no list endpoint" in detail
    lines = repair_lines(state, [])
    assert any("transactionally" in line for line in lines)
    drained = [{"id": "a", "bucket": "completed", "code": ""}]
    assert verdict(drained, SLA)[0] == "background-drained"
    assert summarise(drained) == {"completed": 1}


def test_transient_and_permanent_error_codes_get_different_repairs():
    rows = [
        {"id": "a", "bucket": "stranded", "code": ""},
        {"id": "b", "bucket": "failed", "code": "server_error"},
        {"id": "c", "bucket": "failed", "code": "invalid_prompt"},
        {"id": "d", "bucket": "gone", "code": ""},
        {"id": "e", "bucket": "incomplete", "code": ""},
    ]
    state, detail = verdict(rows, SLA)
    assert state == "background-stranded"
    assert "2 failed" in detail and "no longer retrievable" in detail
    lines = repair_lines(state, rows)
    retry = [line for line in lines if line.startswith("retry")]
    escalate = [line for line in lines if line.startswith("escalate")]
    assert retry and "server_error" in retry[0] and "invalid_prompt" not in retry[0]
    assert escalate and "invalid_prompt" in escalate[0]
    assert any("background true can be cancelled" in line for line in lines)
    assert any("incomplete_details.reason" in line for line in lines)
    assert summarise(rows)["stranded"] == 1
''',
"test_js_file": "openai-background-response-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { ageOf, classify, errorCode, readIds, reasonFor, repairLines, summarise,
         verdict } from './openai-background-response-audit.mjs';

const NOW = 1800000000;
const SLA = 30 * 60;

function record(status, created = null, http = 200, extra = {}) {
  const body = { id: 'resp_x', status, ...extra };
  if (created !== null) body.created_at = created;
  return { http, response: body, created_hint: null };
}

test('each documented status gets its own bucket', () => {
  assert.equal(classify(record('completed', NOW - 60), NOW, SLA)[0], 'completed');
  assert.equal(classify(record('cancelled', NOW - 60), NOW, SLA)[0], 'cancelled');
  const incomplete = record('incomplete', NOW - 60, 200,
    { incomplete_details: { reason: 'max_output_tokens' } });
  const [b1, d1] = classify(incomplete, NOW, SLA);
  assert.equal(b1, 'incomplete');
  assert.ok(d1.includes('max_output_tokens'));
  const failed = record('failed', NOW - 60, 200,
    { error: { code: 'server_error', message: 'boom' } });
  const [b2, d2] = classify(failed, NOW, SLA);
  assert.equal(b2, 'failed');
  assert.ok(d2.includes('error.code server_error'));
  assert.equal(errorCode(failed.response), 'server_error');
  assert.equal(classify(record('weird', NOW), NOW, SLA)[0], 'unreadable');
  assert.equal(reasonFor({}), '');
});

test('queued is normal until the service level says it is not', () => {
  const running = record('in_progress', NOW - 4 * 60);
  const [b1, d1] = classify(running, NOW, SLA);
  assert.equal(b1, 'running');
  assert.ok(d1.includes('inside the service level'));
  const [b2, d2] = classify(running, NOW, 3 * 60);
  assert.equal(b2, 'stranded');
  assert.ok(d2.startsWith('in_progress for 4 min'));
  assert.equal(classify(record('queued', NOW - 19 * 3600), NOW, SLA)[0], 'stranded');
  const noStamp = { http: 200, response: { status: 'queued' }, created_hint: NOW - 7200 };
  assert.equal(classify(noStamp, NOW, SLA)[0], 'stranded');
  assert.equal(ageOf({}, null, NOW), null);
  assert.equal(classify({ http: 200, response: { status: 'queued' }, created_hint: null },
    NOW, SLA)[0], 'running');
});

test('a 404 means two different things and zdr decides which', () => {
  const lost = { http: 404, response: {}, created_hint: NOW - 86400 };
  assert.equal(classify(lost, NOW, SLA)[0], 'gone');
  const [b, d] = classify(lost, NOW, SLA, true);
  assert.equal(b, 'aged-out');
  assert.ok(d.includes('ten minutes'));
  const fresh = { http: 404, response: {}, created_hint: NOW - 60 };
  assert.equal(classify(fresh, NOW, SLA, true)[0], 'gone');
  assert.equal(classify({ http: 500, response: {} }, NOW, SLA)[0], 'unreadable');
});

test('the id file takes bare ids timestamps comments and duplicates', () => {
  const text = ['# open jobs', '', 'resp_a', 'resp_b,1799990000', 'resp_a',
    '  resp_c , not-a-number  '].join('\\n');
  assert.deepEqual(readIds(text),
    [['resp_a', null], ['resp_b', 1799990000], ['resp_c', null]]);
  assert.deepEqual(readIds(''), []);
  assert.deepEqual(readIds(null), []);
});

test('an empty id list is a finding and not a clean run', () => {
  const [state, detail] = verdict([], SLA);
  assert.equal(state, 'background-no-ids');
  assert.ok(detail.includes('no list endpoint'));
  assert.ok(repairLines(state, []).some((l) => l.includes('transactionally')));
  const drained = [{ id: 'a', bucket: 'completed', code: '' }];
  assert.equal(verdict(drained, SLA)[0], 'background-drained');
  assert.deepEqual(summarise(drained), { completed: 1 });
});

test('transient and permanent error codes get different repairs', () => {
  const rows = [
    { id: 'a', bucket: 'stranded', code: '' },
    { id: 'b', bucket: 'failed', code: 'server_error' },
    { id: 'c', bucket: 'failed', code: 'invalid_prompt' },
    { id: 'd', bucket: 'gone', code: '' },
    { id: 'e', bucket: 'incomplete', code: '' },
  ];
  const [state, detail] = verdict(rows, SLA);
  assert.equal(state, 'background-stranded');
  assert.ok(detail.includes('2 failed') && detail.includes('no longer retrievable'));
  const lines = repairLines(state, rows);
  const retry = lines.filter((l) => l.startsWith('retry'));
  const escalate = lines.filter((l) => l.startsWith('escalate'));
  assert.ok(retry.length && retry[0].includes('server_error')
    && !retry[0].includes('invalid_prompt'));
  assert.ok(escalate.length && escalate[0].includes('invalid_prompt'));
  assert.ok(lines.some((l) => l.includes('background true can be cancelled')));
  assert.ok(lines.some((l) => l.includes('incomplete_details.reason')));
  assert.equal(summarise(rows).stranded, 1);
});
''',
"faq": [
 ("Can I list all my background responses?",
  "No, and this is the constraint the whole note is built around. <code>/v1/responses</code> has no list endpoint: a stored response is reachable only by an id you already hold. There is no way to ask the API which responses your project created, no status filter and no way to enumerate the ones you have forgotten about. That makes the durability of the write that records the id the real failure point, which is why the repair for an empty id file is to persist it transactionally with the job row rather than after the call returns."),
 ("What are all the statuses a background response can have?",
  "Six: <code>queued</code>, <code>in_progress</code>, <code>completed</code>, <code>incomplete</code>, <code>failed</code> and <code>cancelled</code>. The documented polling rule is to keep going while it is <code>queued</code> or <code>in_progress</code>, because leaving those two states is what terminal means. Of the four terminal values only <code>completed</code> is success, so a reconciler that treats \\u201cnot queued any more\\u201d as done will silently accept a refusal, a truncation and a cancellation as finished work."),
 ("Why does my background response 404 when I know it existed?",
  "Most often because the project is zero data retention. Background requests there run with <code>store</code> set to false, and the response is held on disk only for roughly ten minutes so that polling can work at all; after that the id resolves to nothing, by design. On an ordinary project a 404 means the response was never stored or its retention elapsed, and that is a genuinely lost result. The script cannot tell the two apart from the API, so it takes <code>--zdr</code> from you and grades accordingly."),
 ("Should I cancel the stranded jobs?",
  "That is the usual repair, and it is one of the few actions available: the cancel endpoint is documented as applying only to responses created with <code>background</code> set to true, so this population is exactly the cancellable one. The script prints it rather than doing it, because cancelling destroys work that might still be wanted and only you know whether the job's result still has a consumer. Cancellation is also idempotent, so a later call simply returns the final response object."),
 ("Is this the same problem as a batch nobody polled?",
  "The shape is the same and the surface is not. A batch is a queue of thousands of requests with a 24 hour window, a results file and a retention clock, and its abandonment is found by listing batches. A background response is a single job with no list endpoint, a six value status and an <code>error</code> object, and its abandonment is found by walking ids you kept. The repairs differ too: a batch wants a reconciler over the list, a background response wants the id persisted transactionally in the first place."),
],
"related": [REL_CHAIN, REL_TRUNC, REL_OUTPUT],
"citations": [CITE_OAI_BG, CITE_OAI_RESP, CITE_OAI_STATE, CITE_OAI_ERRORS],
},
{
"slug": "batch-output-file-never-downloaded",
"title": "The batch finished and nobody ever collected the output",
"description": "Join output_file_id and results_url against your ingest ledger. Results expire 30 days after an OpenAI batch completes, 29 after a Claude batch is created.",
"h1": "The batch finished and nobody ever collected the output",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["openai batch output_file_id missing expired",
             "anthropic batch archived_at results no longer available",
             "batch results never downloaded 29 days",
             "batch created and never polled reconciler",
             "batch output file deleted 30 days after completion"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Reads OPENAI_API_KEY (a project key set to Read Only) and ANTHROPIC_API_KEY (a workspace key); either alone is enough. Also takes your own ledger of batch ids that have been consumed, because neither API records whether a result was read.",
"lead": "The batch ran, the model answered ninety thousand times, the invoice includes every one of those answers, and the file holding them was deleted a month later without ever being opened. There is no incident for this. The batch object still sits in the list saying <code>completed</code>, which is true, and pointing at an id that no longer resolves, which is also true. The only party that ever knew the results were wanted was a process that stopped running in March.",
"short_answer": """<p>Join the batch list against your own record of what was consumed. On OpenAI, <code>GET /v1/batches?limit=100</code> for every <code>completed</code> batch's <code>output_file_id</code>, then <code>GET /v1/files?purpose=batch_output</code> to see which of those ids still exist. On Anthropic, <code>GET /v1/messages/batches?limit=1000</code> with a <strong>workspace key</strong> and read <code>ended_at</code>, <code>results_url</code> and <code>archived_at</code>.</p>
<p><strong>Neither API records whether you downloaded anything.</strong> There is no read receipt on a file object and no flag on a batch. So the second half of the join has to come from your side: a list of batch ids your consumer has actually processed. If you cannot produce that list, that absence is the finding, and it is a bigger one than anything in the output.</p>
<p>Both clocks are short and they are anchored differently. An OpenAI batch output file is deleted <strong>thirty days after the batch is complete</strong>. Claude batch results are available for <strong>twenty-nine days after the batch was created</strong> &mdash; created, not ended &mdash; after which you can still see the batch but <code>archived_at</code> is set and the results cannot be downloaded by anyone.</p>
<p>Three states people usually name as separate problems are verdicts inside this one reading. A batch <strong>created and never polled</strong> is a non-terminal object older than its own 24 hour window. A batch whose <strong>results were never fetched</strong> is a terminal one with an artifact and no ledger entry. A batch that <strong>ended and was never claimed</strong> is the same thing said a third way. One script, four verdicts, one repair.</p>""",
"problem": """<p>The Batch API is fire and poll. Creation returns an object, processing happens somewhere else, and the results appear as a file id on the batch when it is done. Nothing pushes. In the default flow there is no callback and no notification, so the entire mechanism by which results reach your database is a loop somebody wrote, running in a process somebody deployed, which is exactly the kind of thing that gets switched off during an incident and not switched back on.</p>
<p>When that loop stops, everything keeps working. Batches are still submitted, because submission is usually a different job. They still run and are still billed. The output files are still written. The only thing that stops is collection, and collection is the only step with no error path, because not reading a file is not an event.</p>
<p>Then the retention clock runs out and the loss becomes permanent. Up to that point this is a morning's work: list the batches, download what you missed, insert the rows. After it, the only way to get those answers back is to submit the same rows again and pay for them again, which on a bulk enrichment job is the difference between an inconvenience and a line item.</p>
<p>The variant that catches people who are otherwise careful is the batch that never reached a terminal state at all. A batch that has been <code>validating</code> or <code>in_progress</code> for three days is not slow; both providers cap processing at 24 hours, so an object still open past that window is a stale record rather than a running job. It is the same failure &mdash; nothing polled &mdash; wearing a different status.</p>""",
"why": """<p><strong>This note and the error-file note read the same batch, join the same ledger, and mean opposite things.</strong> Say plainly which is which. <code>error_file_id</code> is the <em>list of rows that failed</em>: reading it tells you which requests to retry and why, and losing it costs you the knowledge of what is missing, not the work. <code>output_file_id</code> is <em>the work itself</em>: reading it is the reason the batch was run at all, and losing it costs you every token you paid for. If your downstream table is short and <code>error_file_id</code> is null, this note owns it. If <code>error_file_id</code> is non-null and unread, the other one does. Both live in the same completion handler and the handler needs both assertions, so run the two scripts together and fix them in one change.</p>
<p><strong>The retention anchors differ and getting them wrong sorts the queue backwards.</strong> OpenAI's guide is explicit that the output file is deleted thirty days after the batch is <em>complete</em>, so the countdown starts at <code>completed_at</code>; where the file object carries its own <code>expires_at</code>, that value is authoritative and the script prefers it. Anthropic's clock is twenty-nine days from <code>created_at</code>, and the documentation says so twice, including a note that it is creation and not the end of processing. A batch that took twenty hours to run has twenty hours less runway than you would guess.</p>
<p><strong>An <code>output_file_id</code> that is absent from the file list is already lost, and that is a different finding from one that is expiring.</strong> The batch object outlives the file, so a completed batch pointing at an id that no longer appears under <code>purpose=batch_output</code> is a permanent hole: no read call recovers it and the repair is to re-run and re-pay. Something with four days left is a task for this afternoon. Printing them in one list, sorted by urgency, is the only presentation that leads to the right order of work.</p>
<p><strong>There is no read receipt anywhere in either API, so the ledger is an input rather than a derivation.</strong> File objects have no <code>last_accessed_at</code>, batches have no consumed flag, and Anthropic's <code>archived_at</code> tells you the results are gone rather than that they were taken. A script that guessed which batches had been consumed would be wrong in the direction that produces false calm, so this one takes the list from you and treats an empty one as its own verdict.</p>
<p><strong>A non-terminal batch older than 24 hours is a stale object, not a slow one.</strong> Anthropic publishes <code>expires_at</code> as exactly 24 hours after creation, and OpenAI's completion window can only be set to <code>24h</code>. So a batch still open past that plus a little slack has not been polled since the process that made it went away, and it is counted here rather than in a note of its own, because the repair is the same reconciler.</p>""",
"steps": [
 {"h": "Write down what your consumer has actually processed",
  "body": """<p>One batch id per line, from your own ingest table. This is the half of the join the API cannot supply, and producing it is often the moment the problem becomes obvious. No ledger at all is a valid input and produces its own verdict: everything terminal is reported as unclaimed, which is the honest reading when nothing records consumption.</p>"""},
 {"h": "List the batches on whichever providers you use",
  "body": """<p>OpenAI: page <code>/v1/batches</code> on <code>after</code>. Anthropic: page <code>/v1/messages/batches</code> on <code>after_id</code>, up to 1000 per page. The script takes either key or both and names the providers it looked at, so a one-provider run is never mistaken for a clean two-provider one.</p>"""},
 {"h": "Resolve the OpenAI output files",
  "body": """<p><code>GET /v1/files?purpose=batch_output</code> and index by id. An <code>output_file_id</code> missing from that index is a file that has already been deleted. A present one carries <code>bytes</code>, <code>created_at</code> and, where the platform sets it, <code>expires_at</code>, which the script prefers over its own arithmetic.</p>"""},
 {"h": "Sort by the clock, not by size",
  "body": """<p>Thirty days from completion on OpenAI, twenty-nine days from creation on Anthropic. The output leads with what is expiring soonest, because a small batch with two days left outranks a large one with three weeks. <code>--warn-days</code> sets the threshold; the default is five.</p>"""},
 {"h": "Download, then make the assertion",
  "body": """<p>The repair is printed. Sweep the unclaimed batches, persist their output into your own store keyed by batch id, and then add the assertion that closes this for good: a batch is not done until its output has been archived. On future OpenAI submissions, <code>output_expires_after</code> lets you set a shorter retention deliberately rather than discovering the default one.</p>"""},
],
"verify": """<p>Re-run with the ledger regenerated. Everything terminal should be either claimed or newly downloaded, and the count of unclaimed batches should be zero rather than small. Then run it weekly: the value is not the first run, which finds the backlog, but the second and third, which catch the reconciler stopping again.</p>
<pre><code class="language-bash">python3 batch_output_unclaimed_audit.py --ledger ingested_batches.txt --warn-days 5
# anthropic  msgbatch_01Rf  expiring     41,880 succeeded, 2 days left
# openai     batch_68d114   expiring     88,300 completed, 4 days left
# openai     batch_68a002   lost         output_file_id file_2b7c no longer exists
# anthropic  msgbatch_01Kb  lost         archived_at set, 12,400 succeeded, gone
# openai     batch_68e551   unclaimed    90,000 completed, 21 days left
# openai     batch_68f9c1   stalled      in_progress for 62 h, past the 24 h window
# batch-output-expiring  2 batch(es) hold results that expire within 5 days,
#                        2 are already unrecoverable, 1 was never claimed and
#                        1 never reached a terminal state
#   measured: status, the result artifact and the retention clock from the batch
#             lists, and file existence from GET /v1/files?purpose=batch_output
#   inferred: that an id absent from your ledger was never consumed, since
#             neither API records whether a result was downloaded
#   repair: download the expiring outputs today and persist them keyed by batch
#           id. After the clock runs out no read call recovers them.
#   repair: the lost ones must be re-run and re-paid. Nothing in either API can
#           return results after archival.
# 6 finding(s)</code></pre>""",
"code_intro": "Three paged GETs and eight pure functions. <code>read_ledger</code>, which turns your ingest record into a set and tolerates comments and duplicates; <code>parse_time</code>, which absorbs OpenAI's unix integers and Anthropic's RFC 3339 strings once; <code>file_index</code>, which makes the output-file lookup an index rather than a call per batch; <code>openai_deadline</code>, which prefers the file object's own <code>expires_at</code> over thirty days from <code>completed_at</code> and says which it used; <code>openai_rows</code> and <code>anthropic_rows</code>, which turn two very different object shapes into one row with a state and a number of days on it; <code>verdict</code>, which ranks the categories by whether you can still act on them rather than by count; and <code>repair_lines</code>, which separates the batches you can still save from the ones that have to be paid for twice.",
"py_file": "batch_output_unclaimed_audit.py",
"py": '''"""Find batch results that were paid for and never collected, on both providers.

Read only. Three GET endpoints: /v1/batches and /v1/files on OpenAI,
/v1/messages/batches on Anthropic. Nothing is downloaded, deleted or re-run.

Neither API records whether you read a result. File objects have no
last_accessed_at, batches have no consumed flag, and Anthropic's archived_at
means the results are gone rather than that they were taken. So the ledger of
what your consumer has processed is an input, and an empty one is a verdict.

The clocks are anchored differently and it matters. An OpenAI batch output file
is deleted 30 days after the batch is complete; where the file object carries
its own expires_at, that is authoritative and is used instead. Claude batch
results are available for 29 days after the batch was created, not after it
ended.

This is the mirror of the error-file note. That one reads error_file_id, the
list of rows that failed. This one reads output_file_id and results_url, which
are the work itself.
"""
import argparse
import calendar
import datetime
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("batch_output_unclaimed_audit")

OPENAI_BATCHES_URL = "https://api.openai.com/v1/batches"
OPENAI_FILES_URL = "https://api.openai.com/v1/files"
ANTHROPIC_BATCHES_URL = "https://api.anthropic.com/v1/messages/batches"

# 30 days from completion on OpenAI, 29 days from creation on Anthropic. The
# anchors are different and sorting by the wrong one puts the queue backwards.
OPENAI_RETENTION = 30 * 86400
ANTHROPIC_RETENTION = 29 * 86400

# Both providers cap batch processing at 24 hours. Past that plus a little
# slack, a non-terminal batch is a stale object rather than a slow job.
OPEN_WINDOW = 24 * 3600
GRACE = 2 * 3600

OPENAI_TERMINAL = ("completed", "failed", "expired", "cancelled")

FINDINGS = ("batch-output-expiring", "batch-output-lost",
            "batch-output-unclaimed", "batch-never-polled")


def read_ledger(text):
    """Set of batch ids your consumer has processed. Pure. Comments dropped."""
    out = set()
    for raw in (text or "").replace(",", "\\n").splitlines():
        line = raw.strip()
        if line and not line.startswith("#"):
            out.add(line)
    return out


def parse_time(value):
    """Epoch seconds from a unix number or an RFC 3339 string. Pure.

    A string with no offset is read as UTC rather than as whatever the machine
    running the audit happens to be set to.
    """
    if value is None or value == "" or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return int(value)
    text = str(value).strip()
    if text[-1:] in ("Z", "z"):
        text = text[:-1] + "+00:00"
    try:
        stamp = datetime.datetime.fromisoformat(text)
    except (ValueError, TypeError):
        return None
    if stamp.tzinfo is None:
        return calendar.timegm(stamp.timetuple())
    return int(stamp.timestamp())


def file_index(files):
    """{file_id: file object}. Pure. One index instead of a call per batch."""
    out = {}
    for f in files or []:
        if isinstance(f, dict) and f.get("id"):
            out[str(f["id"])] = f
    return out


def openai_deadline(batch, file_obj):
    """(epoch, source) for when this output disappears. Pure.

    The file's own expires_at is the platform speaking. Everything else is
    arithmetic on the documented 30 days from completion, and the source is
    reported so nobody argues with a number whose provenance is invisible.
    """
    stamp = parse_time((file_obj or {}).get("expires_at"))
    if stamp:
        return (stamp, "expires_at")
    completed = parse_time((batch or {}).get("completed_at"))
    if completed:
        return (completed + OPENAI_RETENTION, "completed_at + 30d")
    created = parse_time((batch or {}).get("created_at"))
    if created:
        return (created + OPENAI_RETENTION, "created_at + 30d")
    return (None, "unknown")


def days_left(deadline, now):
    """Whole days until the deadline. Pure. None when there is no deadline."""
    if deadline is None:
        return None
    return int((deadline - now) // 86400)


def openai_rows(batches, index, ledger, now, warn_days):
    """One row per OpenAI batch worth reporting. Pure."""
    rows = []
    for b in batches or []:
        status = str((b or {}).get("status") or "")
        ident = str(b.get("id"))
        created = parse_time(b.get("created_at"))
        if status not in OPENAI_TERMINAL:
            if created is not None and now - created > OPEN_WINDOW + GRACE:
                rows.append({"provider": "openai", "id": ident, "state": "stalled",
                             "done": 0, "days": None,
                             "detail": "%s for %d h, past the 24 h window"
                                       % (status, (now - created) // 3600)})
            continue
        if status != "completed":
            continue
        counts = b.get("request_counts") or {}
        done = int(counts.get("completed") or 0)
        artifact = b.get("output_file_id")
        if not artifact:
            continue
        if str(artifact) not in (index or {}):
            rows.append({"provider": "openai", "id": ident, "state": "lost",
                         "done": done, "days": None,
                         "detail": "output_file_id %s no longer exists" % artifact})
            continue
        deadline, source = openai_deadline(b, index[str(artifact)])
        left = days_left(deadline, now)
        if left is not None and left <= warn_days:
            state = "expiring"
            detail = "%d completed, %d days left (%s)" % (done, max(0, left), source)
        elif ident in (ledger or set()):
            state = "claimed"
            detail = "%d completed, in the ingest ledger" % done
        else:
            state = "unclaimed"
            detail = "%d completed, %s days left" % (
                done, "unknown" if left is None else max(0, left))
        rows.append({"provider": "openai", "id": ident, "state": state,
                     "done": done, "days": left, "detail": detail})
    return rows


def anthropic_rows(batches, ledger, now, warn_days):
    """One row per Claude batch worth reporting. Pure."""
    rows = []
    for b in batches or []:
        ident = str((b or {}).get("id"))
        status = str(b.get("processing_status") or "")
        created = parse_time(b.get("created_at"))
        counts = b.get("request_counts") or {}
        done = int(counts.get("succeeded") or 0)
        if status != "ended":
            if created is not None and now - created > OPEN_WINDOW + GRACE:
                rows.append({"provider": "anthropic", "id": ident,
                             "state": "stalled", "done": done, "days": None,
                             "detail": "%s for %d h, past the 24 h window"
                                       % (status or "unknown",
                                          (now - created) // 3600)})
            continue
        if done <= 0:
            continue
        if b.get("archived_at"):
            rows.append({"provider": "anthropic", "id": ident, "state": "lost",
                         "done": done, "days": None,
                         "detail": "archived_at set, %d succeeded, gone" % done})
            continue
        left = days_left(created + ANTHROPIC_RETENTION, now) \\
            if created is not None else None
        if left is not None and left <= warn_days:
            state = "expiring"
            detail = "%d succeeded, %d days left (created_at + 29d)" % (
                done, max(0, left))
        elif ident in (ledger or set()):
            state = "claimed"
            detail = "%d succeeded, in the ingest ledger" % done
        else:
            state = "unclaimed"
            detail = "%d succeeded, %s days left" % (
                done, "unknown" if left is None else max(0, left))
        rows.append({"provider": "anthropic", "id": ident, "state": state,
                     "done": done, "days": left, "detail": detail})
    return rows


def by_urgency(rows):
    """Rows ordered by what you can still act on. Pure. Stable within a state."""
    rank = {"expiring": 0, "lost": 1, "unclaimed": 2, "stalled": 3, "claimed": 4}
    return sorted(rows or [], key=lambda r: (rank.get(r.get("state"), 9),
                                             99999 if r.get("days") is None
                                             else r["days"], r.get("id") or ""))


def counts_by_state(rows):
    """{state: n}. Pure."""
    out = {}
    for row in rows or []:
        out[row.get("state")] = out.get(row.get("state"), 0) + 1
    return out


def verdict(rows, ledger, warn_days):
    """Grade the run. Pure. Returns (state, detail).

    Ranked by whether you can still do something about it. An expiring result
    is the only category with a deadline you can beat, so it wins even when the
    unclaimed pile is larger.
    """
    rows = list(rows or [])
    if not rows:
        return ("batch-output-clean",
                "every batch on the providers checked is either open inside its "
                "window or terminal with its output accounted for")
    c = counts_by_state(rows)
    parts = []
    if c.get("lost"):
        parts.append("%d are already unrecoverable" % c["lost"])
    if c.get("unclaimed"):
        parts.append("%d were never claimed" % c["unclaimed"])
    if c.get("stalled"):
        parts.append("%d never reached a terminal state" % c["stalled"])
    tail = (", " + ", ".join(parts)) if parts else ""
    if c.get("expiring"):
        return ("batch-output-expiring",
                "%d batch(es) hold results that expire within %d days%s"
                % (c["expiring"], warn_days, tail))
    if c.get("lost"):
        return ("batch-output-lost",
                "%d batch(es) hold results that are already gone and can only "
                "be recovered by re-running them%s"
                % (c["lost"], (", " + ", ".join(parts[1:])) if parts[1:] else ""))
    if c.get("unclaimed"):
        detail = ("%d batch(es) ended with results nothing has collected"
                  % c["unclaimed"])
        if not ledger:
            detail += (", and no ingest ledger was supplied, so every terminal "
                       "batch counts as unclaimed")
        return ("batch-output-unclaimed", detail)
    if c.get("stalled"):
        return ("batch-never-polled",
                "%d batch(es) have been open longer than the 24 hour window, "
                "which means nothing has polled them" % c["stalled"])
    return ("batch-output-clean",
            "all %d terminal batch(es) are in the ingest ledger with runway "
            "left on the clock" % len(rows))


def repair_lines(state, rows, ledger):
    """The repair for one verdict. Pure. Printed, never performed."""
    rows = list(rows or [])
    c = counts_by_state(rows)
    if state == "batch-output-clean":
        return ["nothing outstanding. Keep the assertion that a batch is not "
                "done until its output has been archived into your own store."]
    lines = []
    if c.get("expiring"):
        lines.append("download the expiring outputs today and persist them "
                     "keyed by batch id. After the clock runs out no read call "
                     "recovers them.")
    if c.get("lost"):
        lines.append("the lost ones must be re-run and re-paid. Nothing in "
                     "either API can return results after the retention window "
                     "closes.")
    if c.get("unclaimed"):
        lines.append("sweep the unclaimed batches: list, diff against your "
                     "ledger, download, and key the rows by custom_id, which "
                     "is the only join available since results are not "
                     "returned in request order.")
    if c.get("stalled"):
        lines.append("a batch open past 24 hours is a stale object rather than "
                     "a slow job. Poll every id you create to a terminal state, "
                     "and record the id at creation time so orphans are "
                     "identifiable.")
    if not ledger:
        lines.append("no ingest ledger was supplied, so nothing could be "
                     "confirmed as consumed. Record every batch id your "
                     "consumer processes: neither API offers a read receipt.")
    lines.append("run the error-file audit alongside this one. That note reads "
                 "error_file_id, the list of rows that failed; this one reads "
                 "the work itself. Both assertions belong in the same batch "
                 "completion handler.")
    return lines


def get_json(url, headers, params=None, timeout=30):
    """One GET. Returns (payload, error). Read only, always."""
    try:
        r = requests.get(url, headers=headers, params=params or {}, timeout=timeout)
    except requests.RequestException as exc:
        return (None, "request failed: %s" % exc)
    if r.status_code != 200:
        return (None, "HTTP %d %s" % (r.status_code, (r.text or "")[:160]))
    try:
        return (r.json(), None)
    except ValueError:
        return (None, "response was not JSON")


def page(url, headers, params, max_pages, cursor="after"):
    """Follow a cursor. Returns (rows, error). GETs only."""
    rows, token = [], None
    for _ in range(max(1, max_pages)):
        query = dict(params or {})
        if token:
            query[cursor] = token
        payload, err = get_json(url, headers, query)
        if err:
            return (rows, err)
        data = payload.get("data") or []
        rows.extend(data)
        if not payload.get("has_more") or not data:
            break
        token = payload.get("last_id") or data[-1].get("id")
        if not token:
            break
    return (rows, None)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ledger", help="file of batch ids your consumer processed")
    ap.add_argument("--warn-days", type=int, default=5,
                    help="days of runway below which a result counts as expiring")
    ap.add_argument("--max-pages", type=int, default=20)
    args = ap.parse_args()

    openai_key = os.environ.get("OPENAI_API_KEY")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    if not openai_key and not anthropic_key:
        log.error("set OPENAI_API_KEY (project key, Read Only) or "
                  "ANTHROPIC_API_KEY (workspace key), or both")
        return 2

    raw = os.environ.get("BATCH_INGEST_LEDGER", "")
    if args.ledger:
        try:
            with open(args.ledger, "r", encoding="utf-8") as fh:
                raw = fh.read()
        except OSError as exc:
            log.error("could not read %s: %s", args.ledger, exc)
            return 2
    ledger = read_ledger(raw)

    now = int(time.time())
    rows, checked = [], []
    if openai_key:
        checked.append("openai")
        headers = {"Authorization": "Bearer %s" % openai_key}
        batches, err = page(OPENAI_BATCHES_URL, headers, {"limit": 100},
                            args.max_pages)
        if err:
            log.warning("openai batch list stopped early: %s", err)
        files, ferr = page(OPENAI_FILES_URL, headers,
                           {"limit": 10000, "purpose": "batch_output"},
                           args.max_pages)
        if ferr:
            log.warning("openai file list stopped early: %s", ferr)
        rows.extend(openai_rows(batches, file_index(files), ledger, now,
                                args.warn_days))
    if anthropic_key:
        checked.append("anthropic")
        headers = {"x-api-key": anthropic_key, "anthropic-version": "2023-06-01"}
        batches, err = page(ANTHROPIC_BATCHES_URL, headers, {"limit": 1000},
                            args.max_pages, cursor="after_id")
        if err:
            log.warning("anthropic batch list stopped early: %s", err)
        rows.extend(anthropic_rows(batches, ledger, now, args.warn_days))

    reportable = [r for r in rows if r["state"] != "claimed"]
    for row in by_urgency(reportable):
        log.warning("%-10s %-14s %-12s %s", row["provider"], row["id"][:14],
                    row["state"], row["detail"])

    state, detail = verdict(reportable, ledger, args.warn_days)
    emit = log.warning if state in FINDINGS else log.info
    emit("%-22s %s", state, detail)
    emit("  checked: %s, %d batch id(s) in the ledger",
         ", ".join(checked) or "nothing", len(ledger))
    emit("  measured: status, the result artifact and the retention clock from "
         "the batch lists, and file existence from the file list")
    emit("  inferred: that an id absent from your ledger was never consumed, "
         "since neither API records whether a result was downloaded")
    for line in repair_lines(state, reportable, ledger):
        emit("  repair: %s", line)

    log.info("%d finding(s)", len(reportable))
    return 1 if reportable else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "batch-output-unclaimed-audit.mjs",
"js": '''/**
 * Find batch results that were paid for and never collected, on both providers.
 *
 * Read only: /v1/batches and /v1/files on OpenAI, /v1/messages/batches on
 * Anthropic. Nothing is downloaded, deleted or re-run.
 *
 * Neither API records whether you read a result, so the ledger of what your
 * consumer processed is an input and an empty one is a verdict.
 *
 * An OpenAI batch output file is deleted 30 days after the batch is complete;
 * the file object's own expires_at wins where it is set. Claude batch results
 * are available 29 days after the batch was created, not after it ended.
 */
import { readFile } from 'node:fs/promises';

const OPENAI_BATCHES_URL = 'https://api.openai.com/v1/batches';
const OPENAI_FILES_URL = 'https://api.openai.com/v1/files';
const ANTHROPIC_BATCHES_URL = 'https://api.anthropic.com/v1/messages/batches';

export const OPENAI_RETENTION = 30 * 86400;
export const ANTHROPIC_RETENTION = 29 * 86400;
export const OPEN_WINDOW = 24 * 3600;
export const GRACE = 2 * 3600;

const OPENAI_TERMINAL = new Set(['completed', 'failed', 'expired', 'cancelled']);

const FINDINGS = new Set(['batch-output-expiring', 'batch-output-lost',
  'batch-output-unclaimed', 'batch-never-polled']);

/** Set of batch ids your consumer has processed. Pure. */
export function readLedger(text) {
  const out = new Set();
  for (const raw of String(text ?? '').split(',').join('\\n').split('\\n')) {
    const line = raw.trim();
    if (line && !line.startsWith('#')) out.add(line);
  }
  return out;
}

/** Epoch seconds from a unix number or an RFC 3339 string. Pure. */
export function parseTime(value) {
  if (value === null || value === undefined || value === '' || typeof value === 'boolean') {
    return null;
  }
  if (typeof value === 'number') return Math.trunc(value);
  const ms = Date.parse(String(value));
  return Number.isFinite(ms) ? Math.floor(ms / 1000) : null;
}

/** {file_id: file object}. Pure. */
export function fileIndex(files) {
  const out = {};
  for (const f of files ?? []) {
    if (f && typeof f === 'object' && f.id) out[String(f.id)] = f;
  }
  return out;
}

/** [epoch, source] for when this output disappears. Pure. */
export function openaiDeadline(batch, fileObj) {
  const stamp = parseTime((fileObj ?? {}).expires_at);
  if (stamp) return [stamp, 'expires_at'];
  const completed = parseTime((batch ?? {}).completed_at);
  if (completed) return [completed + OPENAI_RETENTION, 'completed_at + 30d'];
  const created = parseTime((batch ?? {}).created_at);
  if (created) return [created + OPENAI_RETENTION, 'created_at + 30d'];
  return [null, 'unknown'];
}

/** Whole days until the deadline. Pure. Null when there is no deadline. */
export function daysLeft(deadline, now) {
  if (deadline === null || deadline === undefined) return null;
  return Math.floor((deadline - now) / 86400);
}

/** One row per OpenAI batch worth reporting. Pure. */
export function openaiRows(batches, index, ledger, now, warnDays) {
  const rows = [];
  for (const b of batches ?? []) {
    const status = String((b ?? {}).status ?? '');
    const id = String(b.id);
    const created = parseTime(b.created_at);
    if (!OPENAI_TERMINAL.has(status)) {
      if (created !== null && now - created > OPEN_WINDOW + GRACE) {
        rows.push({ provider: 'openai', id, state: 'stalled', done: 0, days: null,
          detail: `${status} for ${Math.floor((now - created) / 3600)} h, past the 24 h window` });
      }
      continue;
    }
    if (status !== 'completed') continue;
    const done = Number((b.request_counts ?? {}).completed) || 0;
    const artifact = b.output_file_id;
    if (!artifact) continue;
    if (!(String(artifact) in (index ?? {}))) {
      rows.push({ provider: 'openai', id, state: 'lost', done, days: null,
        detail: `output_file_id ${artifact} no longer exists` });
      continue;
    }
    const [deadline, source] = openaiDeadline(b, index[String(artifact)]);
    const left = daysLeft(deadline, now);
    let state;
    let detail;
    if (left !== null && left <= warnDays) {
      state = 'expiring';
      detail = `${done} completed, ${Math.max(0, left)} days left (${source})`;
    } else if ((ledger ?? new Set()).has(id)) {
      state = 'claimed';
      detail = `${done} completed, in the ingest ledger`;
    } else {
      state = 'unclaimed';
      detail = `${done} completed, ${left === null ? 'unknown' : Math.max(0, left)} days left`;
    }
    rows.push({ provider: 'openai', id, state, done, days: left, detail });
  }
  return rows;
}

/** One row per Claude batch worth reporting. Pure. */
export function anthropicRows(batches, ledger, now, warnDays) {
  const rows = [];
  for (const b of batches ?? []) {
    const id = String((b ?? {}).id);
    const status = String(b.processing_status ?? '');
    const created = parseTime(b.created_at);
    const done = Number((b.request_counts ?? {}).succeeded) || 0;
    if (status !== 'ended') {
      if (created !== null && now - created > OPEN_WINDOW + GRACE) {
        rows.push({ provider: 'anthropic', id, state: 'stalled', done, days: null,
          detail: `${status || 'unknown'} for ${Math.floor((now - created) / 3600)} h, `
            + 'past the 24 h window' });
      }
      continue;
    }
    if (done <= 0) continue;
    if (b.archived_at) {
      rows.push({ provider: 'anthropic', id, state: 'lost', done, days: null,
        detail: `archived_at set, ${done} succeeded, gone` });
      continue;
    }
    const left = created === null ? null : daysLeft(created + ANTHROPIC_RETENTION, now);
    let state;
    let detail;
    if (left !== null && left <= warnDays) {
      state = 'expiring';
      detail = `${done} succeeded, ${Math.max(0, left)} days left (created_at + 29d)`;
    } else if ((ledger ?? new Set()).has(id)) {
      state = 'claimed';
      detail = `${done} succeeded, in the ingest ledger`;
    } else {
      state = 'unclaimed';
      detail = `${done} succeeded, ${left === null ? 'unknown' : Math.max(0, left)} days left`;
    }
    rows.push({ provider: 'anthropic', id, state, done, days: left, detail });
  }
  return rows;
}

/** Rows ordered by what you can still act on. Pure. */
export function byUrgency(rows) {
  const rank = { expiring: 0, lost: 1, unclaimed: 2, stalled: 3, claimed: 4 };
  return [...(rows ?? [])].sort((a, b) => {
    const ra = rank[a.state] ?? 9;
    const rb = rank[b.state] ?? 9;
    if (ra !== rb) return ra - rb;
    const da = a.days === null || a.days === undefined ? 99999 : a.days;
    const db = b.days === null || b.days === undefined ? 99999 : b.days;
    if (da !== db) return da - db;
    return String(a.id ?? '').localeCompare(String(b.id ?? ''));
  });
}

/** {state: n}. Pure. */
export function countsByState(rows) {
  const out = {};
  for (const row of rows ?? []) out[row.state] = (out[row.state] ?? 0) + 1;
  return out;
}

/** Grade the run. Pure. Returns [state, detail]. */
export function verdict(rows, ledger, warnDays) {
  const list = rows ?? [];
  if (!list.length) {
    return ['batch-output-clean',
      'every batch on the providers checked is either open inside its window or '
      + 'terminal with its output accounted for'];
  }
  const c = countsByState(list);
  const parts = [];
  if (c.lost) parts.push(`${c.lost} are already unrecoverable`);
  if (c.unclaimed) parts.push(`${c.unclaimed} were never claimed`);
  if (c.stalled) parts.push(`${c.stalled} never reached a terminal state`);
  const tail = parts.length ? `, ${parts.join(', ')}` : '';
  if (c.expiring) {
    return ['batch-output-expiring',
      `${c.expiring} batch(es) hold results that expire within ${warnDays} days${tail}`];
  }
  if (c.lost) {
    const rest = parts.slice(1);
    return ['batch-output-lost',
      `${c.lost} batch(es) hold results that are already gone and can only be `
      + `recovered by re-running them${rest.length ? `, ${rest.join(', ')}` : ''}`];
  }
  if (c.unclaimed) {
    let detail = `${c.unclaimed} batch(es) ended with results nothing has collected`;
    if (!ledger || !ledger.size) {
      detail += ', and no ingest ledger was supplied, so every terminal batch '
        + 'counts as unclaimed';
    }
    return ['batch-output-unclaimed', detail];
  }
  if (c.stalled) {
    return ['batch-never-polled',
      `${c.stalled} batch(es) have been open longer than the 24 hour window, `
      + 'which means nothing has polled them'];
  }
  return ['batch-output-clean',
    `all ${list.length} terminal batch(es) are in the ingest ledger with runway `
    + 'left on the clock'];
}

/** The repair for one verdict. Pure. Printed, never performed. */
export function repairLines(state, rows, ledger) {
  const c = countsByState(rows ?? []);
  if (state === 'batch-output-clean') {
    return ['nothing outstanding. Keep the assertion that a batch is not done '
      + 'until its output has been archived into your own store.'];
  }
  const lines = [];
  if (c.expiring) {
    lines.push('download the expiring outputs today and persist them keyed by '
      + 'batch id. After the clock runs out no read call recovers them.');
  }
  if (c.lost) {
    lines.push('the lost ones must be re-run and re-paid. Nothing in either API '
      + 'can return results after the retention window closes.');
  }
  if (c.unclaimed) {
    lines.push('sweep the unclaimed batches: list, diff against your ledger, '
      + 'download, and key the rows by custom_id, which is the only join '
      + 'available since results are not returned in request order.');
  }
  if (c.stalled) {
    lines.push('a batch open past 24 hours is a stale object rather than a slow '
      + 'job. Poll every id you create to a terminal state, and record the id at '
      + 'creation time so orphans are identifiable.');
  }
  if (!ledger || !ledger.size) {
    lines.push('no ingest ledger was supplied, so nothing could be confirmed as '
      + 'consumed. Record every batch id your consumer processes: neither API '
      + 'offers a read receipt.');
  }
  lines.push('run the error-file audit alongside this one. That note reads '
    + 'error_file_id, the list of rows that failed; this one reads the work '
    + 'itself. Both assertions belong in the same batch completion handler.');
  return lines;
}

async function getJson(url, headers, params) {
  const target = new URL(url);
  for (const [k, v] of Object.entries(params ?? {})) target.searchParams.set(k, String(v));
  let res;
  try {
    res = await fetch(target, { headers });
  } catch (err) {
    return [null, `request failed: ${err.message}`];
  }
  if (res.status !== 200) return [null, `HTTP ${res.status}`];
  try {
    return [await res.json(), null];
  } catch {
    return [null, 'response was not JSON'];
  }
}

async function page(url, headers, params, maxPages, cursor = 'after') {
  const rows = [];
  let token = null;
  for (let i = 0; i < Math.max(1, maxPages); i += 1) {
    const query = { ...(params ?? {}) };
    if (token) query[cursor] = token;
    const [payload, err] = await getJson(url, headers, query);
    if (err) return [rows, err];
    const data = payload.data ?? [];
    rows.push(...data);
    if (!payload.has_more || !data.length) break;
    token = payload.last_id ?? data[data.length - 1]?.id;
    if (!token) break;
  }
  return [rows, null];
}

function args(argv) {
  const out = { warnDays: 5, maxPages: 20 };
  for (let i = 0; i < argv.length; i += 1) {
    if (argv[i] === '--ledger') out.ledger = argv[i += 1];
    else if (argv[i] === '--warn-days') out.warnDays = Number.parseInt(argv[i += 1], 10);
    else if (argv[i] === '--max-pages') out.maxPages = Number.parseInt(argv[i += 1], 10);
  }
  return out;
}

async function main() {
  const opts = args(process.argv.slice(2));
  const openaiKey = process.env.OPENAI_API_KEY;
  const anthropicKey = process.env.ANTHROPIC_API_KEY;
  if (!openaiKey && !anthropicKey) {
    console.error('set OPENAI_API_KEY (project key, Read Only) or '
      + 'ANTHROPIC_API_KEY (workspace key), or both');
    process.exitCode = 2;
    return;
  }

  let raw = process.env.BATCH_INGEST_LEDGER ?? '';
  if (opts.ledger) {
    try {
      raw = await readFile(opts.ledger, 'utf8');
    } catch (err) {
      console.error(`could not read ${opts.ledger}: ${err.message}`);
      process.exitCode = 2;
      return;
    }
  }
  const ledger = readLedger(raw);

  const now = Math.floor(Date.now() / 1000);
  const rows = [];
  const checked = [];
  if (openaiKey) {
    checked.push('openai');
    const headers = { Authorization: `Bearer ${openaiKey}` };
    const [batches, err] = await page(OPENAI_BATCHES_URL, headers, { limit: 100 },
      opts.maxPages);
    if (err) console.log(`openai batch list stopped early: ${err}`);
    const [files, ferr] = await page(OPENAI_FILES_URL, headers,
      { limit: 10000, purpose: 'batch_output' }, opts.maxPages);
    if (ferr) console.log(`openai file list stopped early: ${ferr}`);
    rows.push(...openaiRows(batches, fileIndex(files), ledger, now, opts.warnDays));
  }
  if (anthropicKey) {
    checked.push('anthropic');
    const headers = { 'x-api-key': anthropicKey, 'anthropic-version': '2023-06-01' };
    const [batches, err] = await page(ANTHROPIC_BATCHES_URL, headers, { limit: 1000 },
      opts.maxPages, 'after_id');
    if (err) console.log(`anthropic batch list stopped early: ${err}`);
    rows.push(...anthropicRows(batches, ledger, now, opts.warnDays));
  }

  const reportable = rows.filter((r) => r.state !== 'claimed');
  for (const row of byUrgency(reportable)) {
    console.log(`${row.provider.padEnd(10)} ${row.id.slice(0, 14).padEnd(14)} `
      + `${row.state.padEnd(12)} ${row.detail}`);
  }

  const [state, detail] = verdict(reportable, ledger, opts.warnDays);
  console.log(`${state.padEnd(22)} ${detail}`);
  console.log(`  checked: ${checked.join(', ') || 'nothing'}, ${ledger.size} `
    + 'batch id(s) in the ledger');
  console.log('  measured: status, the result artifact and the retention clock '
    + 'from the batch lists, and file existence from the file list');
  console.log('  inferred: that an id absent from your ledger was never consumed, '
    + 'since neither API records whether a result was downloaded');
  for (const line of repairLines(state, reportable, ledger)) {
    console.log(`  repair: ${line}`);
  }

  console.log(`${reportable.length} finding(s)`);
  process.exitCode = reportable.length ? 1 : 0;
  void FINDINGS;
}

if (import.meta.url === `file://${process.argv[1]}`) await main();
''',
"test_intro": "The first test is the retention arithmetic, and it is the one most likely to be wrong in a way nobody notices: OpenAI counts thirty days from <code>completed_at</code>, Anthropic counts twenty-nine from <code>created_at</code>, and the file object's own <code>expires_at</code> beats both when the platform sets it. Get the anchor wrong and the queue sorts backwards. The second asserts that a missing output file is <code>lost</code> rather than <code>unclaimed</code>, because the two have different repairs &mdash; one is a download and one is a re-run &mdash; and that Anthropic's <code>archived_at</code> means the same thing. The third covers the three states the backlog wanted as separate notes, proving they come out of one pass: a stalled non-terminal batch past 24 hours, an ended batch with no ledger entry, and an ended batch that is in the ledger and therefore silent. The fourth is the verdict ordering, where an expiring result outranks a larger unclaimed pile because it is the only one with a deadline you can still beat. The fifth is the empty ledger, which must produce its own sentence rather than a clean run. And the last checks that the repair text names the error-file note, since the pair is the whole point of the boundary.",
"test_py_file": "test_batch_output_unclaimed_audit.py",
"test_py": '''from batch_output_unclaimed_audit import (anthropic_rows, by_urgency,
                                          counts_by_state, days_left,
                                          file_index, openai_deadline,
                                          openai_rows, parse_time, read_ledger,
                                          repair_lines, verdict)

NOW = 1_800_000_000
DAY = 86400

OPENAI_BATCHES = [
    {"id": "batch_fresh", "status": "completed", "created_at": NOW - 26 * DAY,
     "completed_at": NOW - 26 * DAY, "output_file_id": "file_soon",
     "request_counts": {"total": 88300, "completed": 88300, "failed": 0}},
    {"id": "batch_gone", "status": "completed", "created_at": NOW - 60 * DAY,
     "completed_at": NOW - 60 * DAY, "output_file_id": "file_2b7c",
     "request_counts": {"total": 40000, "completed": 40000, "failed": 0}},
    {"id": "batch_open", "status": "completed", "created_at": NOW - 3 * DAY,
     "completed_at": NOW - 3 * DAY, "output_file_id": "file_room",
     "request_counts": {"total": 90000, "completed": 90000, "failed": 0}},
    {"id": "batch_stuck", "status": "in_progress", "created_at": NOW - 62 * 3600},
]

OPENAI_FILES = [
    {"id": "file_soon", "purpose": "batch_output", "bytes": 10,
     "created_at": NOW - 26 * DAY},
    {"id": "file_room", "purpose": "batch_output", "bytes": 10,
     "created_at": NOW - 3 * DAY},
]

ANTHROPIC_BATCHES = [
    {"id": "msgbatch_arch", "processing_status": "ended",
     "created_at": "2026-01-02T00:00:00Z", "ended_at": "2026-01-02T04:00:00Z",
     "archived_at": "2026-01-31T00:00:00Z", "results_url": None,
     "request_counts": {"processing": 0, "succeeded": 12400, "errored": 0,
                        "canceled": 0, "expired": 0}},
    {"id": "msgbatch_open", "processing_status": "in_progress",
     "created_at": "2026-01-02T00:00:00Z",
     "request_counts": {"processing": 500, "succeeded": 0, "errored": 0,
                        "canceled": 0, "expired": 0}},
]


def test_the_retention_anchors_are_different_on_each_provider():
    index = file_index(OPENAI_FILES)
    # No expires_at on the file, so 30 days from completion.
    deadline, source = openai_deadline(OPENAI_BATCHES[0], index["file_soon"])
    assert source == "completed_at + 30d"
    assert days_left(deadline, NOW) == 4
    # The platform's own expires_at wins whenever it is set.
    stamped = dict(index["file_soon"], expires_at=NOW + 2 * DAY)
    deadline, source = openai_deadline(OPENAI_BATCHES[0], stamped)
    assert source == "expires_at" and days_left(deadline, NOW) == 2
    assert openai_deadline({}, {}) == (None, "unknown")
    assert days_left(None, NOW) is None
    # Anthropic counts 29 days from created_at, not from ended_at.
    created = parse_time("2026-01-02T00:00:00Z")
    rows = anthropic_rows([dict(ANTHROPIC_BATCHES[0], archived_at=None)], set(),
                          created + 27 * DAY, 5)
    assert rows[0]["state"] == "expiring"
    assert "created_at + 29d" in rows[0]["detail"]


def test_a_missing_output_file_is_lost_and_not_merely_unclaimed():
    rows = openai_rows(OPENAI_BATCHES, file_index(OPENAI_FILES), set(), NOW, 5)
    states = {r["id"]: r["state"] for r in rows}
    assert states["batch_gone"] == "lost"
    assert states["batch_fresh"] == "expiring"
    assert states["batch_open"] == "unclaimed"
    lost = [r for r in rows if r["state"] == "lost"][0]
    assert "no longer exists" in lost["detail"]
    # Anthropic says the same thing with archived_at.
    arch = anthropic_rows(ANTHROPIC_BATCHES, set(), NOW, 5)
    assert [r["state"] for r in arch if r["id"] == "msgbatch_arch"] == ["lost"]


def test_never_polled_never_fetched_and_never_claimed_are_one_pass():
    rows = (openai_rows(OPENAI_BATCHES, file_index(OPENAI_FILES), set(), NOW, 5)
            + anthropic_rows(ANTHROPIC_BATCHES, set(), NOW, 5))
    counts = counts_by_state(rows)
    # Created and never polled.
    assert counts["stalled"] == 2
    stalled = [r for r in rows if r["state"] == "stalled"]
    assert any("past the 24 h window" in r["detail"] for r in stalled)
    # Ended and never claimed.
    assert counts["unclaimed"] == 1
    # A batch in the ledger goes quiet, which is the whole point of the join.
    claimed = openai_rows([OPENAI_BATCHES[2]], file_index(OPENAI_FILES),
                          {"batch_open"}, NOW, 5)
    assert claimed[0]["state"] == "claimed"
    assert "in the ingest ledger" in claimed[0]["detail"]


def test_the_verdict_leads_with_what_you_can_still_act_on():
    rows = (openai_rows(OPENAI_BATCHES, file_index(OPENAI_FILES), set(), NOW, 5)
            + anthropic_rows(ANTHROPIC_BATCHES, set(), NOW, 5))
    state, detail = verdict(rows, {"x"}, 5)
    assert state == "batch-output-expiring"
    assert "expire within 5 days" in detail
    assert "already unrecoverable" in detail and "never claimed" in detail
    # Order on the page follows the same rule, soonest deadline first.
    ordered = [r["state"] for r in by_urgency(rows)]
    assert ordered[0] == "expiring"
    assert ordered.index("lost") < ordered.index("unclaimed")
    assert ordered.index("unclaimed") < ordered.index("stalled")
    # Without anything expiring, the lost pile leads.
    no_expiring = [r for r in rows if r["state"] != "expiring"]
    assert verdict(no_expiring, {"x"}, 5)[0] == "batch-output-lost"
    assert verdict([], set(), 5)[0] == "batch-output-clean"


def test_an_absent_ledger_is_reported_rather_than_assumed_away():
    rows = openai_rows([OPENAI_BATCHES[2]], file_index(OPENAI_FILES), set(), NOW, 5)
    state, detail = verdict(rows, set(), 5)
    assert state == "batch-output-unclaimed"
    assert "no ingest ledger was supplied" in detail
    lines = repair_lines(state, rows, set())
    assert any("neither API offers a read receipt" in line for line in lines)
    assert read_ledger("# note\\nbatch_a\\nbatch_b,batch_a\\n") == {"batch_a",
                                                                  "batch_b"}
    assert read_ledger("") == set()


def test_the_repair_hands_the_other_half_to_the_error_file_note():
    rows = (openai_rows(OPENAI_BATCHES, file_index(OPENAI_FILES), set(), NOW, 5)
            + anthropic_rows(ANTHROPIC_BATCHES, set(), NOW, 5))
    lines = repair_lines("batch-output-expiring", rows, {"x"})
    assert any("error_file_id, the list of rows that failed" in line
               for line in lines)
    assert any("download the expiring outputs today" in line for line in lines)
    assert any("re-run and re-paid" in line for line in lines)
    assert any("stale object rather than" in line for line in lines)
    clean = repair_lines("batch-output-clean", [], {"x"})
    assert clean[0].startswith("nothing outstanding")
''',
"test_js_file": "batch-output-unclaimed-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { anthropicRows, byUrgency, countsByState, daysLeft, fileIndex,
         openaiDeadline, openaiRows, parseTime, readLedger, repairLines,
         verdict } from './batch-output-unclaimed-audit.mjs';

const NOW = 1800000000;
const DAY = 86400;

const OPENAI_BATCHES = [
  { id: 'batch_fresh', status: 'completed', created_at: NOW - 26 * DAY,
    completed_at: NOW - 26 * DAY, output_file_id: 'file_soon',
    request_counts: { total: 88300, completed: 88300, failed: 0 } },
  { id: 'batch_gone', status: 'completed', created_at: NOW - 60 * DAY,
    completed_at: NOW - 60 * DAY, output_file_id: 'file_2b7c',
    request_counts: { total: 40000, completed: 40000, failed: 0 } },
  { id: 'batch_open', status: 'completed', created_at: NOW - 3 * DAY,
    completed_at: NOW - 3 * DAY, output_file_id: 'file_room',
    request_counts: { total: 90000, completed: 90000, failed: 0 } },
  { id: 'batch_stuck', status: 'in_progress', created_at: NOW - 62 * 3600 },
];

const OPENAI_FILES = [
  { id: 'file_soon', purpose: 'batch_output', bytes: 10, created_at: NOW - 26 * DAY },
  { id: 'file_room', purpose: 'batch_output', bytes: 10, created_at: NOW - 3 * DAY },
];

const ANTHROPIC_BATCHES = [
  { id: 'msgbatch_arch', processing_status: 'ended',
    created_at: '2026-01-02T00:00:00Z', ended_at: '2026-01-02T04:00:00Z',
    archived_at: '2026-01-31T00:00:00Z', results_url: null,
    request_counts: { processing: 0, succeeded: 12400, errored: 0, canceled: 0,
                      expired: 0 } },
  { id: 'msgbatch_open', processing_status: 'in_progress',
    created_at: '2026-01-02T00:00:00Z',
    request_counts: { processing: 500, succeeded: 0, errored: 0, canceled: 0,
                      expired: 0 } },
];

test('the retention anchors are different on each provider', () => {
  const index = fileIndex(OPENAI_FILES);
  const [deadline, source] = openaiDeadline(OPENAI_BATCHES[0], index.file_soon);
  assert.equal(source, 'completed_at + 30d');
  assert.equal(daysLeft(deadline, NOW), 4);
  const stamped = { ...index.file_soon, expires_at: NOW + 2 * DAY };
  const [d2, s2] = openaiDeadline(OPENAI_BATCHES[0], stamped);
  assert.equal(s2, 'expires_at');
  assert.equal(daysLeft(d2, NOW), 2);
  assert.deepEqual(openaiDeadline({}, {}), [null, 'unknown']);
  assert.equal(daysLeft(null, NOW), null);
  const created = parseTime('2026-01-02T00:00:00Z');
  const rows = anthropicRows([{ ...ANTHROPIC_BATCHES[0], archived_at: null }],
    new Set(), created + 27 * DAY, 5);
  assert.equal(rows[0].state, 'expiring');
  assert.ok(rows[0].detail.includes('created_at + 29d'));
});

test('a missing output file is lost and not merely unclaimed', () => {
  const rows = openaiRows(OPENAI_BATCHES, fileIndex(OPENAI_FILES), new Set(), NOW, 5);
  const states = Object.fromEntries(rows.map((r) => [r.id, r.state]));
  assert.equal(states.batch_gone, 'lost');
  assert.equal(states.batch_fresh, 'expiring');
  assert.equal(states.batch_open, 'unclaimed');
  assert.ok(rows.find((r) => r.state === 'lost').detail.includes('no longer exists'));
  const arch = anthropicRows(ANTHROPIC_BATCHES, new Set(), NOW, 5);
  assert.deepEqual(arch.filter((r) => r.id === 'msgbatch_arch').map((r) => r.state),
    ['lost']);
});

test('never polled never fetched and never claimed are one pass', () => {
  const rows = [...openaiRows(OPENAI_BATCHES, fileIndex(OPENAI_FILES), new Set(), NOW, 5),
    ...anthropicRows(ANTHROPIC_BATCHES, new Set(), NOW, 5)];
  const counts = countsByState(rows);
  assert.equal(counts.stalled, 2);
  assert.ok(rows.filter((r) => r.state === 'stalled')
    .some((r) => r.detail.includes('past the 24 h window')));
  assert.equal(counts.unclaimed, 1);
  const claimed = openaiRows([OPENAI_BATCHES[2]], fileIndex(OPENAI_FILES),
    new Set(['batch_open']), NOW, 5);
  assert.equal(claimed[0].state, 'claimed');
  assert.ok(claimed[0].detail.includes('in the ingest ledger'));
});

test('the verdict leads with what you can still act on', () => {
  const rows = [...openaiRows(OPENAI_BATCHES, fileIndex(OPENAI_FILES), new Set(), NOW, 5),
    ...anthropicRows(ANTHROPIC_BATCHES, new Set(), NOW, 5)];
  const [state, detail] = verdict(rows, new Set(['x']), 5);
  assert.equal(state, 'batch-output-expiring');
  assert.ok(detail.includes('expire within 5 days'));
  assert.ok(detail.includes('already unrecoverable') && detail.includes('never claimed'));
  const ordered = byUrgency(rows).map((r) => r.state);
  assert.equal(ordered[0], 'expiring');
  assert.ok(ordered.indexOf('lost') < ordered.indexOf('unclaimed'));
  assert.ok(ordered.indexOf('unclaimed') < ordered.indexOf('stalled'));
  const noExpiring = rows.filter((r) => r.state !== 'expiring');
  assert.equal(verdict(noExpiring, new Set(['x']), 5)[0], 'batch-output-lost');
  assert.equal(verdict([], new Set(), 5)[0], 'batch-output-clean');
});

test('an absent ledger is reported rather than assumed away', () => {
  const rows = openaiRows([OPENAI_BATCHES[2]], fileIndex(OPENAI_FILES), new Set(), NOW, 5);
  const [state, detail] = verdict(rows, new Set(), 5);
  assert.equal(state, 'batch-output-unclaimed');
  assert.ok(detail.includes('no ingest ledger was supplied'));
  assert.ok(repairLines(state, rows, new Set())
    .some((l) => l.includes('neither API offers a read receipt')));
  assert.deepEqual([...readLedger('# note\\nbatch_a\\nbatch_b,batch_a\\n')].sort(),
    ['batch_a', 'batch_b']);
  assert.equal(readLedger('').size, 0);
});

test('the repair hands the other half to the error file note', () => {
  const rows = [...openaiRows(OPENAI_BATCHES, fileIndex(OPENAI_FILES), new Set(), NOW, 5),
    ...anthropicRows(ANTHROPIC_BATCHES, new Set(), NOW, 5)];
  const lines = repairLines('batch-output-expiring', rows, new Set(['x']));
  assert.ok(lines.some((l) => l.includes('error_file_id, the list of rows that failed')));
  assert.ok(lines.some((l) => l.includes('download the expiring outputs today')));
  assert.ok(lines.some((l) => l.includes('re-run and re-paid')));
  assert.ok(lines.some((l) => l.includes('stale object rather than')));
  assert.ok(repairLines('batch-output-clean', [], new Set(['x']))[0]
    .startsWith('nothing outstanding'));
});
''',
"faq": [
 ("How is this different from the error-file note?",
  "By which file id it reads, and therefore by what a finding costs you. <code>error_file_id</code> points at the rows that failed: reading it tells you what to retry, and losing it costs you the knowledge of what is missing rather than the work. <code>output_file_id</code> and <code>results_url</code> point at the work itself: losing those means paying for every one of those answers again. The join is identical &mdash; batch list against your own ingest ledger &mdash; and the repairs land in the same completion handler, so run both scripts and fix them together. If your table is short and <code>error_file_id</code> is null, this note owns it."),
 ("How long do batch results actually last?",
  "OpenAI's batch guide is explicit that the output file is automatically deleted thirty days after the batch is complete, so the clock starts at completion; where the file object carries its own <code>expires_at</code>, that value is what the platform will act on and the script uses it in preference. Anthropic's clock is twenty-nine days from <code>created_at</code>, and the documentation stresses that it is creation and not the end of processing. A Claude batch that took twenty hours to run therefore has twenty hours less runway than a naive count from <code>ended_at</code> would suggest."),
 ("Can I tell from the API whether a result was downloaded?",
  "No, and this is the reason the script asks you for a ledger. File objects carry <code>bytes</code>, <code>created_at</code>, <code>filename</code>, <code>purpose</code> and sometimes <code>expires_at</code>, but nothing resembling a last-accessed timestamp, and there is no access log to query. Anthropic's <code>archived_at</code> is not a read receipt either &mdash; it records that the results became unavailable, whether or not anybody took them first. So the only honest test is a diff against your own record of consumption."),
 ("What about batches that never reached a terminal state?",
  "They are counted here as <code>stalled</code>, and they are the same failure wearing a different status. Both providers cap batch processing at 24 hours: Anthropic publishes <code>expires_at</code> as exactly 24 hours after creation, and OpenAI's <code>completion_window</code> can only be set to <code>24h</code>. So a batch still showing <code>validating</code>, <code>in_progress</code> or <code>finalizing</code> three days later is a stale object rather than a slow job, and the repair is the same reconciler that would have collected the output."),
 ("Should I set output_expires_after when I create a batch?",
  "It is worth knowing about. OpenAI's batch create endpoint accepts an <code>output_expires_after</code> object with an <code>anchor</code> of <code>created_at</code> and a <code>seconds</code> value between 3,600 and 2,592,000, which lets you choose a shorter retention deliberately instead of inheriting the default. That is a storage-hygiene decision rather than a fix for this problem: it makes unread output disappear sooner. The actual fix is the assertion that a batch is not done until its output is in your own store."),
],
"related": [REL_ERRFILE, REL_EXPIRED, REL_PARTIAL],
"citations": [CITE_OAI_BATCH_GUIDE, CITE_OAI_BATCH_REF, CITE_AN_BATCH_GUIDE, CITE_AN_BATCH_LIST],
},
{
"slug": "batch-queue-limit-reached",
"title": "The batch queue is full, so the next submission is refused",
"description": "Sum request_counts.processing across live batches and compare it with the org's enqueued_batch_requests ceiling. A full queue refuses new submissions.",
"h1": "The batch queue is full, so the next submission is refused",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Admin read key", "Python and Node.js", "Tests included"],
"keywords": ["anthropic enqueued_batch_requests limit reached",
             "message batches api rate limit 429 processing queue",
             "batch requests in processing queue maximum",
             "claude rate limits api group_type batch",
             "batch submission rejected while messages api is idle"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Needs ANTHROPIC_ADMIN_KEY for GET /v1/organizations/rate_limits and ANTHROPIC_API_KEY, a workspace key, for GET /v1/messages/batches. Extra workspace keys can be supplied so the depth covers more of the organization. GET requests only.",
"lead": "Nothing has failed. Every batch in the account is healthy, every one of them is inside its window, and the Messages API limits are not being touched. The only symptom is that the submitter has started getting 429s, and it is getting them for a reason that has nothing to do with the requests it is sending: an unrelated job, in an unrelated workspace, has parked four hundred thousand requests in a queue that the whole organization shares.",
"short_answer": """<p>Read the ceiling, then measure the depth. The ceiling comes from the Admin API: <code>GET /v1/organizations/rate_limits?group_type=batch</code> returns a group whose <code>models</code> is <code>null</code> and whose <code>limits</code> array holds a single entry, <code>{\\"type\\": \\"enqueued_batch_requests\\", \\"value\\": N}</code>. That is the number of batch requests your organization may have waiting at once, and it is shared across every model.</p>
<p>The depth comes from the data plane: <code>GET /v1/messages/batches?limit=1000</code> with a <strong>workspace key</strong>, and the sum of <code>request_counts.processing</code> over every batch whose <code>processing_status</code> is <code>in_progress</code> or <code>canceling</code>. The documentation defines the queue precisely &mdash; a batch request is part of the processing queue when it has yet to be successfully processed by the model &mdash; and <code>processing</code> is that count.</p>
<p><strong>Depth against ceiling is the whole reading, and it needs two different credentials.</strong> Admin keys cannot reach the Messages Batches endpoints and workspace keys are rejected by every Admin endpoint, so a run with only one of them gets half the answer. The script says which half it is missing rather than reporting a ratio it could not compute.</p>
<p>One honest caveat is printed with every result. The ceiling is organization wide; the batch list is workspace scoped. A single workspace key therefore measures that workspace's contribution, which is a <strong>lower bound</strong> on the number that matters. Pass more workspace keys and the bound tightens.</p>""",
"problem": """<p>The Message Batches API has its own rate limits, and they are not the ones anybody watches. There is a requests-per-minute limit on the batch endpoints, a cap on how many batch requests may sit in the processing queue at once, and a cap on the size of a single batch. All of them are shared across every model, which is the part that surprises people: moving a job to a different model does not move it to a different queue.</p>
<p>The queue cap is the one that bites, because it is a property of the organization rather than of the job being submitted. Enqueued batch requests run 200,000 on Start, 300,000 on Build and 500,000 on Scale. One nightly backfill that submits four hundred thousand rows at once can hold most of that for hours, and every other team's submission is refused for the duration &mdash; a 429 on <code>/v1/messages/batches</code> with the Messages API sitting idle.</p>
<p>What makes it hard to diagnose is that the refusal and the cause are in different places. The team that gets the 429 is not the team holding the queue, the error names a limit rather than a batch, and there is no view anywhere that says who is using the capacity. Meanwhile the ordinary rate-limit dashboards look fine, because they are about tokens per minute on the Messages API and this has nothing to do with either.</p>
<p>The second-order effect is worse than the refusal. A queue held at the ceiling slows everything behind it, and the documentation notes plainly that when processing is slowed by demand and request volume, you may see more requests expiring after 24 hours. So a full queue does not only reject new work, it puts existing work at risk of running out of window &mdash; which is a different note, and a different symptom, produced by this cause.</p>""",
"why": """<p><strong>The ceiling is readable, which is unusual and worth the extra credential.</strong> Most limits in this section have to be inferred from response headers on a live call. This one is a stored configuration you can GET: the Rate Limits API returns your organization's configured groups, and the <code>batch</code> group carries <code>enqueued_batch_requests</code> as a plain number. That turns a guess into arithmetic, and it is the reason this note reads an Admin endpoint at all.</p>
<p><strong>The queue is defined by a field, not by a status.</strong> It would be natural to count requests in every unfinished batch, but the documented definition is narrower: a batch request is in the processing queue when it has yet to be successfully processed by the model. <code>request_counts.processing</code> is exactly that number, and it is documented as starting at the full request count and moving to the other buckets only once processing of the whole batch ends. So the sum of <code>processing</code> over live batches is the measurement, and adding the succeeded or errored counts would overstate it.</p>
<p><strong>Two credentials, two scopes, and the script refuses to paper over the gap.</strong> Anthropic's Admin API rejects workspace-scoped keys outright, and the Messages Batches endpoints are unreachable from an Admin key. The consequence is structural: the ceiling you can read is organization wide and the depth you can read is per workspace. A single-workspace measurement is a lower bound, the output labels it as one, and passing additional workspace keys is how you tighten it rather than a nicety.</p>
<p><strong>Occupancy is not expiry, and the two notes stay apart.</strong> A batch drifting toward its 24 hour <code>expires_at</code> with work still unprocessed is the published expiry note; this one never looks at <code>expires_at</code> and never grades a batch as late. The reading here is a single number about the organization, taken at a moment, and its finding is about submissions that will be refused rather than about rows that will be lost.</p>
<p><strong>On OpenAI the equivalent ceiling is not readable at all, and the note says so instead of guessing.</strong> OpenAI's Batch API also has a per-model cap on prompt tokens queued for batch processing, plus a limit of 2,000 batch creations per hour and 50,000 requests per batch. None of those is exposed by any endpoint: the token cap lives on the platform limits page and the only signal a script gets is the error text on a submission it is not allowed to make. So this script is Anthropic only, deliberately, rather than half-implemented on both.</p>""",
"steps": [
 {"h": "Provision the two keys",
  "body": """<p><code>ANTHROPIC_ADMIN_KEY</code> for <code>GET /v1/organizations/rate_limits</code>, which needs an Admin key or a personal or service-account key that is not scoped to a workspace. <code>ANTHROPIC_API_KEY</code> as a workspace key for <code>GET /v1/messages/batches</code>. Neither endpoint accepts the other's credential, so both are needed for a complete answer.</p>"""},
 {"h": "Read the ceiling",
  "body": """<p><code>?group_type=batch</code> narrows the response to one group. Its <code>models</code> is <code>null</code>, because batch limits are shared across every model rather than attached to one, and its <code>limits</code> array holds <code>enqueued_batch_requests</code>. Follow <code>next_page</code> if it is ever non-null; today the response is a single page.</p>"""},
 {"h": "Sum the live queue",
  "body": """<p>Page <code>/v1/messages/batches</code> on <code>after_id</code> at up to 1000 per page, keep <code>processing_status</code> of <code>in_progress</code> or <code>canceling</code>, and add up <code>request_counts.processing</code>. Batches that have <code>ended</code> hold nothing in the queue, whatever their other counts say.</p>"""},
 {"h": "Add the other workspaces",
  "body": """<p><code>ANTHROPIC_EXTRA_WORKSPACE_KEYS</code>, comma separated, adds more workspace keys to the same sum. Every key you leave out makes the measurement a looser lower bound against an organization-wide ceiling, and the output prints how many workspaces the number covers so nobody reads it as complete when it is not.</p>"""},
 {"h": "Name the biggest holder and drain before enqueuing",
  "body": """<p>The output ranks the live batches by <code>processing</code> so the conversation has a subject. The repair is printed and it is a scheduling change, not a cancellation: hold at most a few batches in flight, wait for one to end before submitting the next, and split a single enormous submission rather than parking it whole.</p>"""},
],
"verify": """<p>Re-run during the window when submissions were being refused, not afterwards. This is a live measurement of a queue that drains, so a clean result at ten in the morning says nothing about two o'clock. The useful form is a scheduled run every few minutes through the batch window, alarming when occupancy crosses the threshold rather than when a submission has already been rejected.</p>
<pre><code class="language-bash">python3 anthropic_batch_queue_depth.py --threshold 80
# ceiling      enqueued_batch_requests 300,000 (organization wide)
# msgbatch_01Rf  in_progress   214,900 processing
# msgbatch_01Qa  in_progress    58,400 processing
# msgbatch_01Zc  canceling       9,600 processing
# queue-near-limit     282,900 of 300,000 enqueued batch requests are in the
#                      processing queue, which is 94% of the ceiling
#   measured: enqueued_batch_requests from the Rate Limits API, and the sum of
#             request_counts.processing over 3 live batches in 1 workspace
#   inferred: nothing about other workspaces. The ceiling is organization wide
#             and this depth is a lower bound on it
#   repair: hold at most a few batches in flight and wait for one to end before
#           submitting the next. A batch request leaves the queue only when the
#           model has processed it.
#   repair: msgbatch_01Rf alone holds 214,900 of the 300,000. Split submissions
#           of that size: the per batch cap is 100,000 requests or 256 MB,
#           whichever comes first.
# 1 finding(s)</code></pre>""",
"code_intro": "Two GETs against two different credentials, and seven pure functions. <code>enqueued_limit</code>, which digs the one number out of a nested group-and-limits structure and returns <code>None</code> rather than a zero when it is absent, because zero would read as a ceiling of nothing; <code>queue_rows</code>, which keeps only the two non-terminal statuses and takes <code>processing</code> rather than any other count, since that is the field the documented definition of the queue points at; <code>queue_depth</code>, which is the sum; <code>headroom</code>, which returns the remaining requests and the occupancy ratio and refuses to divide by a missing limit; <code>top_holders</code>, which gives the finding a subject; <code>workspace_keys</code>, which de-duplicates the credentials so the same workspace is never counted twice; and <code>verdict</code>, which treats an unreadable ceiling as a finding in its own right.",
"py_file": "anthropic_batch_queue_depth.py",
"py": '''"""Measure live batch queue depth against the organization's enqueued ceiling.

Read only. Two GET endpoints on two different credentials:
GET /v1/organizations/rate_limits?group_type=batch with an Admin key for the
ceiling, and GET /v1/messages/batches with a workspace key for the depth.
Nothing is submitted and nothing is cancelled.

The Message Batches API has its own limits, shared across all models. The one
this measures is the number of batch requests allowed in the processing queue
at once. A batch request is part of that queue when it has yet to be
successfully processed by the model, which is exactly request_counts.processing.

Scope caveat, printed with every result: the ceiling is organization wide and
the batch list is workspace scoped, so a single workspace key produces a lower
bound. Extra workspace keys tighten it.

This is Anthropic only on purpose. OpenAI's equivalent enqueued-token cap is
not returned by any endpoint, so a read-only script cannot compute the ratio
there at all.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("anthropic_batch_queue_depth")

RATE_LIMITS_URL = "https://api.anthropic.com/v1/organizations/rate_limits"
BATCHES_URL = "https://api.anthropic.com/v1/messages/batches"

# The two non-terminal processing_status values. A batch that has ended holds
# nothing in the queue whatever its other counts say.
LIVE_STATES = ("in_progress", "canceling")

# Documented at every tier, and the same at every tier, which is why it is safe
# to print as context rather than looked up per organization.
PER_BATCH_REQUESTS = 100000
PER_BATCH_MB = 256

FINDINGS = ("queue-exhausted", "queue-near-limit", "queue-limit-unknown")


def enqueued_limit(payload):
    """The enqueued_batch_requests value, or None. Pure.

    None rather than zero when it is missing. Zero would read as a ceiling of
    nothing and turn every run into a false alarm at infinite occupancy.
    """
    for group in (payload or {}).get("data") or []:
        if not isinstance(group, dict):
            continue
        if group.get("group_type") != "batch":
            continue
        for limit in group.get("limits") or []:
            if isinstance(limit, dict) and limit.get("type") == "enqueued_batch_requests":
                try:
                    return int(limit.get("value"))
                except (TypeError, ValueError):
                    return None
    return None


def queue_rows(batches, workspace=""):
    """Live batches and what each holds in the queue. Pure.

    processing, and only processing. Adding succeeded or errored would count
    requests the model has already finished with, which are not in the queue.
    """
    out = []
    for b in batches or []:
        status = str((b or {}).get("processing_status") or "")
        if status not in LIVE_STATES:
            continue
        counts = b.get("request_counts") or {}
        try:
            processing = int(counts.get("processing") or 0)
        except (TypeError, ValueError):
            processing = 0
        out.append({"id": str(b.get("id")), "status": status,
                    "processing": processing, "workspace": workspace})
    return sorted(out, key=lambda r: (-r["processing"], r["id"]))


def queue_depth(rows):
    """Total requests waiting on the model. Pure."""
    return sum(int(r.get("processing") or 0) for r in rows or [])


def headroom(depth, limit):
    """(remaining, occupancy) or (None, None) when the ceiling is unknown. Pure."""
    if limit is None or limit <= 0:
        return (None, None)
    return (max(0, limit - depth), depth / float(limit))


def top_holders(rows, n=3):
    """The n biggest contributors. Pure. Gives the finding a subject."""
    return [r for r in (rows or [])[:max(0, n)] if int(r.get("processing") or 0) > 0]


def workspace_keys(primary, extra):
    """Deduplicated workspace credentials. Pure. Order kept.

    The same key passed twice would double the measured depth, which is the one
    error in this script that would look like a real finding.
    """
    out, seen = [], set()
    for candidate in [primary] + str(extra or "").split(","):
        key = (candidate or "").strip()
        if key and key not in seen:
            seen.add(key)
            out.append(key)
    return out


def verdict(depth, limit, rows, workspaces, threshold):
    """Grade the run. Pure. Returns (state, detail)."""
    remaining, occupancy = headroom(depth, limit)
    if limit is None:
        return ("queue-limit-unknown",
                "%d batch requests are in the processing queue across %d "
                "workspace(s), but the enqueued_batch_requests ceiling could "
                "not be read, so there is no headroom to report"
                % (depth, workspaces))
    percent = int(round(occupancy * 100))
    if depth >= limit:
        return ("queue-exhausted",
                "%d of %d enqueued batch requests are in the processing queue, "
                "which is the whole ceiling. New submissions are being refused"
                % (depth, limit))
    if percent >= threshold:
        return ("queue-near-limit",
                "%d of %d enqueued batch requests are in the processing queue, "
                "which is %d%% of the ceiling" % (depth, limit, percent))
    return ("queue-clear",
            "%d of %d enqueued batch requests are in the processing queue, "
            "leaving %d requests of headroom across %d live batch(es)"
            % (depth, limit, remaining, len(rows or [])))


def repair_lines(state, rows, limit):
    """The repair for one verdict. Pure. Printed, never performed."""
    if state == "queue-clear":
        return ["nothing to change. Keep the check running through the batch "
                "window rather than once a day: this is a queue that drains."]
    if state == "queue-limit-unknown":
        return ["read the ceiling with an Admin key: GET "
                "/v1/organizations/rate_limits?group_type=batch returns "
                "enqueued_batch_requests for the organization. Workspace keys "
                "are rejected by every Admin endpoint.",
                "without the ceiling this run is a raw count. It cannot tell "
                "you whether the next submission will be accepted."]
    lines = ["hold at most a few batches in flight and wait for one to end "
             "before submitting the next. A batch request leaves the queue "
             "only when the model has processed it."]
    biggest = top_holders(rows, 1)
    if biggest and limit:
        lines.append("%s alone holds %d of the %d. Split submissions of that "
                     "size: the per batch cap is %d requests or %d MB, "
                     "whichever comes first."
                     % (biggest[0]["id"], biggest[0]["processing"], limit,
                        PER_BATCH_REQUESTS, PER_BATCH_MB))
    lines.append("a queue held at the ceiling also slows what is already in it, "
                 "and slowed batches are the ones that run out of their 24 hour "
                 "window. Draining is the fix for both.")
    return lines


def get_json(url, headers, params=None, timeout=30):
    """One GET. Returns (payload, error). Read only, always."""
    try:
        r = requests.get(url, headers=headers, params=params or {}, timeout=timeout)
    except requests.RequestException as exc:
        return (None, "request failed: %s" % exc)
    if r.status_code != 200:
        return (None, "HTTP %d %s" % (r.status_code, (r.text or "")[:160]))
    try:
        return (r.json(), None)
    except ValueError:
        return (None, "response was not JSON")


def read_ceiling(admin_key, max_pages=5):
    """The organization's enqueued_batch_requests. Returns (limit, error)."""
    headers = {"x-api-key": admin_key, "anthropic-version": "2023-06-01"}
    params = {"group_type": "batch"}
    for _ in range(max(1, max_pages)):
        payload, err = get_json(RATE_LIMITS_URL, headers, params)
        if err:
            return (None, err)
        found = enqueued_limit(payload)
        if found is not None:
            return (found, None)
        nxt = payload.get("next_page")
        if not nxt:
            return (None, "no batch group in the rate limits response")
        params = {"group_type": "batch", "page": nxt}
    return (None, "the rate limits response never carried a batch group")


def read_batches(key, max_pages=20):
    """One workspace's batches. Returns (rows, error). GETs only."""
    headers = {"x-api-key": key, "anthropic-version": "2023-06-01"}
    rows, after = [], None
    for _ in range(max(1, max_pages)):
        params = {"limit": 1000}
        if after:
            params["after_id"] = after
        payload, err = get_json(BATCHES_URL, headers, params)
        if err:
            return (rows, err)
        data = payload.get("data") or []
        rows.extend(data)
        if not payload.get("has_more") or not data:
            break
        after = payload.get("last_id") or data[-1].get("id")
        if not after:
            break
    return (rows, None)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--threshold", type=int, default=80,
                    help="percent occupancy at which the queue is a finding")
    ap.add_argument("--max-pages", type=int, default=20)
    args = ap.parse_args()

    admin_key = os.environ.get("ANTHROPIC_ADMIN_KEY")
    keys = workspace_keys(os.environ.get("ANTHROPIC_API_KEY"),
                          os.environ.get("ANTHROPIC_EXTRA_WORKSPACE_KEYS"))
    if not keys:
        log.error("set ANTHROPIC_API_KEY to a workspace key. Add "
                  "ANTHROPIC_EXTRA_WORKSPACE_KEYS as a comma separated list to "
                  "cover more of the organization")
        return 2

    limit = None
    if admin_key:
        limit, err = read_ceiling(admin_key)
        if err:
            log.warning("could not read the ceiling: %s", err)
    else:
        log.warning("no ANTHROPIC_ADMIN_KEY, so the enqueued_batch_requests "
                    "ceiling cannot be read and only the raw depth is available")
    if limit is not None:
        log.info("%-12s enqueued_batch_requests %s (organization wide)",
                 "ceiling", format(limit, ","))

    rows = []
    for index, key in enumerate(keys):
        batches, err = read_batches(key, args.max_pages)
        if err:
            log.warning("workspace %d batch list stopped early: %s", index + 1, err)
        rows.extend(queue_rows(batches, workspace="ws%d" % (index + 1)))
    rows.sort(key=lambda r: (-r["processing"], r["id"]))

    for row in rows:
        log.info("%-16s %-13s %s processing", row["id"][:16], row["status"],
                 format(row["processing"], ","))

    depth = queue_depth(rows)
    state, detail = verdict(depth, limit, rows, len(keys), args.threshold)
    emit = log.warning if state in FINDINGS else log.info
    emit("%-20s %s", state, detail)
    emit("  measured: enqueued_batch_requests from the Rate Limits API, and the "
         "sum of request_counts.processing over %d live batch(es) in %d "
         "workspace(s)", len(rows), len(keys))
    emit("  inferred: nothing about workspaces whose keys were not supplied. "
         "The ceiling is organization wide and this depth is a lower bound on it")
    for line in repair_lines(state, rows, limit):
        emit("  repair: %s", line)

    log.info("%d finding(s)", 1 if state in FINDINGS else 0)
    return 1 if state in FINDINGS else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "anthropic-batch-queue-depth.mjs",
"js": '''/**
 * Measure live batch queue depth against the organization's enqueued ceiling.
 *
 * Read only. GET /v1/organizations/rate_limits?group_type=batch with an Admin
 * key for the ceiling, GET /v1/messages/batches with a workspace key for the
 * depth. Nothing is submitted and nothing is cancelled.
 *
 * A batch request is part of the processing queue when it has yet to be
 * successfully processed by the model, which is request_counts.processing.
 *
 * The ceiling is organization wide and the batch list is workspace scoped, so
 * a single workspace key produces a lower bound. Extra keys tighten it.
 */
const RATE_LIMITS_URL = 'https://api.anthropic.com/v1/organizations/rate_limits';
const BATCHES_URL = 'https://api.anthropic.com/v1/messages/batches';

export const LIVE_STATES = new Set(['in_progress', 'canceling']);

export const PER_BATCH_REQUESTS = 100000;
export const PER_BATCH_MB = 256;

const FINDINGS = new Set(['queue-exhausted', 'queue-near-limit', 'queue-limit-unknown']);

/** The enqueued_batch_requests value, or null. Pure. */
export function enqueuedLimit(payload) {
  for (const group of (payload ?? {}).data ?? []) {
    if (!group || typeof group !== 'object') continue;
    if (group.group_type !== 'batch') continue;
    for (const limit of group.limits ?? []) {
      if (limit && typeof limit === 'object' && limit.type === 'enqueued_batch_requests') {
        const value = Number(limit.value);
        return Number.isFinite(value) ? Math.trunc(value) : null;
      }
    }
  }
  return null;
}

/** Live batches and what each holds in the queue. Pure. */
export function queueRows(batches, workspace = '') {
  return (batches ?? [])
    .filter((b) => LIVE_STATES.has(String((b ?? {}).processing_status ?? '')))
    .map((b) => ({
      id: String(b.id),
      status: String(b.processing_status),
      processing: Number((b.request_counts ?? {}).processing) || 0,
      workspace,
    }))
    .sort((a, b) => (b.processing - a.processing) || a.id.localeCompare(b.id));
}

/** Total requests waiting on the model. Pure. */
export function queueDepth(rows) {
  return (rows ?? []).reduce((n, r) => n + (Number(r?.processing) || 0), 0);
}

/** [remaining, occupancy] or [null, null] when the ceiling is unknown. Pure. */
export function headroom(depth, limit) {
  if (limit === null || limit === undefined || limit <= 0) return [null, null];
  return [Math.max(0, limit - depth), depth / limit];
}

/** The n biggest contributors. Pure. */
export function topHolders(rows, n = 3) {
  return (rows ?? []).slice(0, Math.max(0, n)).filter((r) => (Number(r.processing) || 0) > 0);
}

/** Deduplicated workspace credentials. Pure. Order kept. */
export function workspaceKeys(primary, extra) {
  const out = [];
  const seen = new Set();
  for (const candidate of [primary, ...String(extra ?? '').split(',')]) {
    const key = (candidate ?? '').trim();
    if (key && !seen.has(key)) {
      seen.add(key);
      out.push(key);
    }
  }
  return out;
}

/** Grade the run. Pure. Returns [state, detail]. */
export function verdict(depth, limit, rows, workspaces, threshold) {
  const [remaining, occupancy] = headroom(depth, limit);
  if (limit === null || limit === undefined) {
    return ['queue-limit-unknown',
      `${depth} batch requests are in the processing queue across ${workspaces} `
      + 'workspace(s), but the enqueued_batch_requests ceiling could not be read, '
      + 'so there is no headroom to report'];
  }
  const percent = Math.round(occupancy * 100);
  if (depth >= limit) {
    return ['queue-exhausted',
      `${depth} of ${limit} enqueued batch requests are in the processing queue, `
      + 'which is the whole ceiling. New submissions are being refused'];
  }
  if (percent >= threshold) {
    return ['queue-near-limit',
      `${depth} of ${limit} enqueued batch requests are in the processing queue, `
      + `which is ${percent}% of the ceiling`];
  }
  return ['queue-clear',
    `${depth} of ${limit} enqueued batch requests are in the processing queue, `
    + `leaving ${remaining} requests of headroom across ${(rows ?? []).length} `
    + 'live batch(es)'];
}

/** The repair for one verdict. Pure. Printed, never performed. */
export function repairLines(state, rows, limit) {
  if (state === 'queue-clear') {
    return ['nothing to change. Keep the check running through the batch window '
      + 'rather than once a day: this is a queue that drains.'];
  }
  if (state === 'queue-limit-unknown') {
    return ['read the ceiling with an Admin key: GET '
      + '/v1/organizations/rate_limits?group_type=batch returns '
      + 'enqueued_batch_requests for the organization. Workspace keys are '
      + 'rejected by every Admin endpoint.',
    'without the ceiling this run is a raw count. It cannot tell you whether '
      + 'the next submission will be accepted.'];
  }
  const lines = ['hold at most a few batches in flight and wait for one to end '
    + 'before submitting the next. A batch request leaves the queue only when '
    + 'the model has processed it.'];
  const biggest = topHolders(rows, 1);
  if (biggest.length && limit) {
    lines.push(`${biggest[0].id} alone holds ${biggest[0].processing} of the `
      + `${limit}. Split submissions of that size: the per batch cap is `
      + `${PER_BATCH_REQUESTS} requests or ${PER_BATCH_MB} MB, whichever comes first.`);
  }
  lines.push('a queue held at the ceiling also slows what is already in it, and '
    + 'slowed batches are the ones that run out of their 24 hour window. '
    + 'Draining is the fix for both.');
  return lines;
}

async function getJson(url, headers, params) {
  const target = new URL(url);
  for (const [k, v] of Object.entries(params ?? {})) target.searchParams.set(k, String(v));
  let res;
  try {
    res = await fetch(target, { headers });
  } catch (err) {
    return [null, `request failed: ${err.message}`];
  }
  if (res.status !== 200) return [null, `HTTP ${res.status}`];
  try {
    return [await res.json(), null];
  } catch {
    return [null, 'response was not JSON'];
  }
}

async function readCeiling(adminKey, maxPages = 5) {
  const headers = { 'x-api-key': adminKey, 'anthropic-version': '2023-06-01' };
  let params = { group_type: 'batch' };
  for (let i = 0; i < Math.max(1, maxPages); i += 1) {
    const [payload, err] = await getJson(RATE_LIMITS_URL, headers, params);
    if (err) return [null, err];
    const found = enqueuedLimit(payload);
    if (found !== null) return [found, null];
    if (!payload.next_page) return [null, 'no batch group in the rate limits response'];
    params = { group_type: 'batch', page: payload.next_page };
  }
  return [null, 'the rate limits response never carried a batch group'];
}

async function readBatches(key, maxPages = 20) {
  const headers = { 'x-api-key': key, 'anthropic-version': '2023-06-01' };
  const rows = [];
  let after = null;
  for (let i = 0; i < Math.max(1, maxPages); i += 1) {
    const params = { limit: 1000 };
    if (after) params.after_id = after;
    const [payload, err] = await getJson(BATCHES_URL, headers, params);
    if (err) return [rows, err];
    const data = payload.data ?? [];
    rows.push(...data);
    if (!payload.has_more || !data.length) break;
    after = payload.last_id ?? data[data.length - 1]?.id;
    if (!after) break;
  }
  return [rows, null];
}

function args(argv) {
  const out = { threshold: 80, maxPages: 20 };
  for (let i = 0; i < argv.length; i += 1) {
    if (argv[i] === '--threshold') out.threshold = Number.parseInt(argv[i += 1], 10);
    else if (argv[i] === '--max-pages') out.maxPages = Number.parseInt(argv[i += 1], 10);
  }
  return out;
}

async function main() {
  const opts = args(process.argv.slice(2));
  const adminKey = process.env.ANTHROPIC_ADMIN_KEY;
  const keys = workspaceKeys(process.env.ANTHROPIC_API_KEY,
    process.env.ANTHROPIC_EXTRA_WORKSPACE_KEYS);
  if (!keys.length) {
    console.error('set ANTHROPIC_API_KEY to a workspace key. Add '
      + 'ANTHROPIC_EXTRA_WORKSPACE_KEYS as a comma separated list to cover more '
      + 'of the organization');
    process.exitCode = 2;
    return;
  }

  let limit = null;
  if (adminKey) {
    const [found, err] = await readCeiling(adminKey);
    if (err) console.log(`could not read the ceiling: ${err}`);
    limit = found;
  } else {
    console.log('no ANTHROPIC_ADMIN_KEY, so the enqueued_batch_requests ceiling '
      + 'cannot be read and only the raw depth is available');
  }
  if (limit !== null) {
    console.log(`ceiling      enqueued_batch_requests ${limit} (organization wide)`);
  }

  const rows = [];
  for (const [index, key] of keys.entries()) {
    const [batches, err] = await readBatches(key, opts.maxPages);
    if (err) console.log(`workspace ${index + 1} batch list stopped early: ${err}`);
    rows.push(...queueRows(batches, `ws${index + 1}`));
  }
  rows.sort((a, b) => (b.processing - a.processing) || a.id.localeCompare(b.id));

  for (const row of rows) {
    console.log(`${row.id.slice(0, 16).padEnd(16)} ${row.status.padEnd(13)} `
      + `${row.processing} processing`);
  }

  const depth = queueDepth(rows);
  const [state, detail] = verdict(depth, limit, rows, keys.length, opts.threshold);
  console.log(`${state.padEnd(20)} ${detail}`);
  console.log('  measured: enqueued_batch_requests from the Rate Limits API, and '
    + `the sum of request_counts.processing over ${rows.length} live batch(es) `
    + `in ${keys.length} workspace(s)`);
  console.log('  inferred: nothing about workspaces whose keys were not '
    + 'supplied. The ceiling is organization wide and this depth is a lower '
    + 'bound on it');
  for (const line of repairLines(state, rows, limit)) console.log(`  repair: ${line}`);

  console.log(`${FINDINGS.has(state) ? 1 : 0} finding(s)`);
  process.exitCode = FINDINGS.has(state) ? 1 : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) await main();
''',
"test_intro": "The first test digs the ceiling out of the real response shape, where the batch group sits alongside several model groups, carries a <code>models</code> of <code>null</code>, and holds its single limit inside a nested array. It also pins the decision that a missing ceiling comes back as <code>None</code> rather than zero, because a zero ceiling reads as infinite occupancy and turns every run into a false alarm. The second is the definition of the queue: only <code>in_progress</code> and <code>canceling</code> count, and only the <code>processing</code> field, so a batch that has ended with fifty thousand successes contributes nothing. The third is the occupancy arithmetic against the threshold, including the exhausted case at exactly the ceiling. The fourth is the unreadable ceiling, which has to be a finding with its own repair rather than a clean run. The fifth checks that the same workspace key passed twice does not double the depth, which is the one mistake here that would look exactly like a real alarm. And the last checks the repair names the biggest holder and the per-batch cap.",
"test_py_file": "test_anthropic_batch_queue_depth.py",
"test_py": '''from anthropic_batch_queue_depth import (enqueued_limit, headroom, queue_depth,
                                        queue_rows, repair_lines, top_holders,
                                        verdict, workspace_keys)

RATE_LIMITS = {
    "data": [
        {"type": "rate_limit", "group_type": "model_group",
         "models": ["claude-opus-5"],
         "limits": [{"type": "requests_per_minute", "value": 4000},
                    {"type": "input_tokens_per_minute", "value": 10000000}]},
        {"type": "rate_limit", "group_type": "batch", "models": None,
         "limits": [{"type": "enqueued_batch_requests", "value": 300000}]},
    ],
    "next_page": None,
}

BATCHES = [
    {"id": "msgbatch_01Rf", "processing_status": "in_progress",
     "request_counts": {"processing": 214900, "succeeded": 0, "errored": 0,
                        "canceled": 0, "expired": 0}},
    {"id": "msgbatch_01Qa", "processing_status": "in_progress",
     "request_counts": {"processing": 58400, "succeeded": 0, "errored": 0,
                        "canceled": 0, "expired": 0}},
    {"id": "msgbatch_01Zc", "processing_status": "canceling",
     "request_counts": {"processing": 9600, "succeeded": 200, "errored": 0,
                        "canceled": 0, "expired": 0}},
    {"id": "msgbatch_01Done", "processing_status": "ended",
     "request_counts": {"processing": 0, "succeeded": 50000, "errored": 0,
                        "canceled": 0, "expired": 0}},
]


def test_the_ceiling_comes_out_of_the_batch_group_and_nowhere_else():
    assert enqueued_limit(RATE_LIMITS) == 300000
    # Absent means unknown, never zero: a zero ceiling reads as infinite
    # occupancy and alarms on an empty queue.
    assert enqueued_limit({"data": [RATE_LIMITS["data"][0]]}) is None
    assert enqueued_limit({}) is None
    assert enqueued_limit({"data": [{"group_type": "batch",
                                     "limits": [{"type": "other", "value": 1}]}]}) is None
    assert enqueued_limit({"data": [{"group_type": "batch",
                                     "limits": [{"type": "enqueued_batch_requests",
                                                 "value": "lots"}]}]}) is None


def test_only_live_batches_and_only_the_processing_count_are_the_queue():
    rows = queue_rows(BATCHES, "ws1")
    assert [r["id"] for r in rows] == ["msgbatch_01Rf", "msgbatch_01Qa",
                                       "msgbatch_01Zc"]
    # An ended batch holds nothing in the queue however many it succeeded on.
    assert all(r["id"] != "msgbatch_01Done" for r in rows)
    # canceling is still live, because those requests have not been processed.
    assert rows[2]["status"] == "canceling"
    assert queue_depth(rows) == 282900
    assert queue_depth([]) == 0


def test_occupancy_is_measured_against_the_threshold_that_was_passed_in():
    rows = queue_rows(BATCHES)
    depth = queue_depth(rows)
    remaining, occupancy = headroom(depth, 300000)
    assert remaining == 17100 and round(occupancy, 3) == 0.943
    state, detail = verdict(depth, 300000, rows, 1, 80)
    assert state == "queue-near-limit" and "94% of the ceiling" in detail
    assert verdict(depth, 300000, rows, 1, 95)[0] == "queue-clear"
    # At or over the ceiling, submissions are refused rather than slowed.
    state, detail = verdict(300000, 300000, rows, 1, 80)
    assert state == "queue-exhausted" and "being refused" in detail
    assert headroom(10, None) == (None, None)
    assert headroom(10, 0) == (None, None)


def test_an_unreadable_ceiling_is_a_finding_with_its_own_repair():
    rows = queue_rows(BATCHES)
    state, detail = verdict(queue_depth(rows), None, rows, 1, 80)
    assert state == "queue-limit-unknown"
    assert "could not be read" in detail and "282900" in detail
    lines = repair_lines(state, rows, None)
    assert any("Workspace keys are rejected by every Admin endpoint" in line
               for line in lines)
    assert any("raw count" in line for line in lines)


def test_the_same_workspace_key_twice_does_not_double_the_depth():
    assert workspace_keys("k1", "k2,k3") == ["k1", "k2", "k3"]
    assert workspace_keys("k1", "k1, k1 ,") == ["k1"]
    assert workspace_keys("", None) == []
    assert workspace_keys(None, "k9") == ["k9"]


def test_the_repair_names_the_biggest_holder_and_the_per_batch_cap():
    rows = queue_rows(BATCHES)
    lines = repair_lines("queue-near-limit", rows, 300000)
    assert any("msgbatch_01Rf alone holds 214900 of the 300000" in line
               for line in lines)
    assert any("100000 requests or 256 MB" in line for line in lines)
    assert any("24 hour window" in line for line in lines)
    assert top_holders(rows, 1)[0]["id"] == "msgbatch_01Rf"
    assert top_holders([], 3) == []
    assert repair_lines("queue-clear", rows, 300000)[0].startswith("nothing to change")
''',
"test_js_file": "anthropic-batch-queue-depth.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { enqueuedLimit, headroom, queueDepth, queueRows, repairLines, topHolders,
         verdict, workspaceKeys } from './anthropic-batch-queue-depth.mjs';

const RATE_LIMITS = {
  data: [
    { type: 'rate_limit', group_type: 'model_group', models: ['claude-opus-5'],
      limits: [{ type: 'requests_per_minute', value: 4000 },
               { type: 'input_tokens_per_minute', value: 10000000 }] },
    { type: 'rate_limit', group_type: 'batch', models: null,
      limits: [{ type: 'enqueued_batch_requests', value: 300000 }] },
  ],
  next_page: null,
};

const BATCHES = [
  { id: 'msgbatch_01Rf', processing_status: 'in_progress',
    request_counts: { processing: 214900, succeeded: 0, errored: 0, canceled: 0,
                      expired: 0 } },
  { id: 'msgbatch_01Qa', processing_status: 'in_progress',
    request_counts: { processing: 58400, succeeded: 0, errored: 0, canceled: 0,
                      expired: 0 } },
  { id: 'msgbatch_01Zc', processing_status: 'canceling',
    request_counts: { processing: 9600, succeeded: 200, errored: 0, canceled: 0,
                      expired: 0 } },
  { id: 'msgbatch_01Done', processing_status: 'ended',
    request_counts: { processing: 0, succeeded: 50000, errored: 0, canceled: 0,
                      expired: 0 } },
];

test('the ceiling comes out of the batch group and nowhere else', () => {
  assert.equal(enqueuedLimit(RATE_LIMITS), 300000);
  assert.equal(enqueuedLimit({ data: [RATE_LIMITS.data[0]] }), null);
  assert.equal(enqueuedLimit({}), null);
  assert.equal(enqueuedLimit({ data: [{ group_type: 'batch',
    limits: [{ type: 'other', value: 1 }] }] }), null);
  assert.equal(enqueuedLimit({ data: [{ group_type: 'batch',
    limits: [{ type: 'enqueued_batch_requests', value: 'lots' }] }] }), null);
});

test('only live batches and only the processing count are the queue', () => {
  const rows = queueRows(BATCHES, 'ws1');
  assert.deepEqual(rows.map((r) => r.id),
    ['msgbatch_01Rf', 'msgbatch_01Qa', 'msgbatch_01Zc']);
  assert.ok(rows.every((r) => r.id !== 'msgbatch_01Done'));
  assert.equal(rows[2].status, 'canceling');
  assert.equal(queueDepth(rows), 282900);
  assert.equal(queueDepth([]), 0);
});

test('occupancy is measured against the threshold that was passed in', () => {
  const rows = queueRows(BATCHES);
  const depth = queueDepth(rows);
  const [remaining, occupancy] = headroom(depth, 300000);
  assert.equal(remaining, 17100);
  assert.equal(Number(occupancy.toFixed(3)), 0.943);
  const [state, detail] = verdict(depth, 300000, rows, 1, 80);
  assert.equal(state, 'queue-near-limit');
  assert.ok(detail.includes('94% of the ceiling'));
  assert.equal(verdict(depth, 300000, rows, 1, 95)[0], 'queue-clear');
  const [state2, detail2] = verdict(300000, 300000, rows, 1, 80);
  assert.equal(state2, 'queue-exhausted');
  assert.ok(detail2.includes('being refused'));
  assert.deepEqual(headroom(10, null), [null, null]);
  assert.deepEqual(headroom(10, 0), [null, null]);
});

test('an unreadable ceiling is a finding with its own repair', () => {
  const rows = queueRows(BATCHES);
  const [state, detail] = verdict(queueDepth(rows), null, rows, 1, 80);
  assert.equal(state, 'queue-limit-unknown');
  assert.ok(detail.includes('could not be read') && detail.includes('282900'));
  const lines = repairLines(state, rows, null);
  assert.ok(lines.some((l) => l.includes('Workspace keys are rejected by every Admin endpoint')));
  assert.ok(lines.some((l) => l.includes('raw count')));
});

test('the same workspace key twice does not double the depth', () => {
  assert.deepEqual(workspaceKeys('k1', 'k2,k3'), ['k1', 'k2', 'k3']);
  assert.deepEqual(workspaceKeys('k1', 'k1, k1 ,'), ['k1']);
  assert.deepEqual(workspaceKeys('', null), []);
  assert.deepEqual(workspaceKeys(null, 'k9'), ['k9']);
});

test('the repair names the biggest holder and the per batch cap', () => {
  const rows = queueRows(BATCHES);
  const lines = repairLines('queue-near-limit', rows, 300000);
  assert.ok(lines.some((l) => l.includes('msgbatch_01Rf alone holds 214900 of the 300000')));
  assert.ok(lines.some((l) => l.includes('100000 requests or 256 MB')));
  assert.ok(lines.some((l) => l.includes('24 hour window')));
  assert.equal(topHolders(rows, 1)[0].id, 'msgbatch_01Rf');
  assert.deepEqual(topHolders([], 3), []);
  assert.ok(repairLines('queue-clear', rows, 300000)[0].startsWith('nothing to change'));
});
''',
"faq": [
 ("What exactly counts as a batch request in the processing queue?",
  "The documentation defines it as a batch request that has yet to be successfully processed by the model, and that is precisely <code>request_counts.processing</code> on the batch object. Those counts start with everything in <code>processing</code> and move to <code>succeeded</code>, <code>errored</code>, <code>canceled</code> or <code>expired</code> only once processing of the whole batch ends, with the five values always summing to the batch's total. So the queue is the sum of <code>processing</code> over batches that are <code>in_progress</code> or <code>canceling</code>, and an <code>ended</code> batch contributes nothing however large it was."),
 ("What are the actual numbers?",
  "The enqueued batch requests limit is 200,000 on Start, 300,000 on Build and 500,000 on Scale, and it is shared across every model rather than allocated per model. A single batch is capped at 100,000 requests or 256 MB, whichever is reached first, at every tier. The batch endpoints also carry their own requests-per-minute limit of 1,000, 2,000 or 4,000 by tier. Rather than hardcode any of that, the script reads your organization's actual configured value from the Rate Limits API, because the tables move and your organization may not be on a standard tier."),
 ("Why does this need two different API keys?",
  "Because Anthropic's two APIs do not share credentials in either direction. The Rate Limits endpoints are part of the Admin API and reject workspace-scoped keys outright; the Messages Batches endpoints are data plane and cannot be reached with an Admin key. There is no single credential that can read both the ceiling and the depth, so a complete answer needs both. With only the workspace key you get a raw count and the script says so; with only the Admin key you get a limit and nothing to compare it against."),
 ("Does this measure the whole organization?",
  "Not unless you give it every workspace's key, and the output says which it is. <code>GET /v1/messages/batches</code> lists batches within the workspace that the key resolves to, while <code>enqueued_batch_requests</code> is an organization-wide ceiling. So a one-key run produces a lower bound on the depth: real occupancy is at least what you measured and possibly much more. <code>ANTHROPIC_EXTRA_WORKSPACE_KEYS</code> takes a comma-separated list, and the script de-duplicates them so passing the same key twice cannot invent a queue that is not there."),
 ("Does OpenAI have the same limit, and can this find it?",
  "It has an equivalent and no, this cannot read it. OpenAI's Batch API caps the prompt tokens that may be queued for batch processing per model, allows up to 2,000 batch creations per hour, and limits a single batch to 50,000 requests. None of those values is returned by any endpoint: the token cap is published on the platform limits page, and the only programmatic signal is the error body on a submission a read-only script is not permitted to make. Rather than half-implement the check there, this note is Anthropic only and says why."),
],
"related": [REL_LIMITER, REL_PROJRL, REL_EXPIRED],
"citations": [CITE_AN_RATE_LIMITS, CITE_AN_RL_API, CITE_AN_BATCH_GUIDE, CITE_AN_BATCH_LIST],
},
]
