#!/usr/bin/env python3
"""/llm/ field notes, batch R — the writing.

Four states of a retrieval index, all of which answer a `file_search` call with
a 200. That is the premise and it is also the hazard: these four notes read the
same two object types, and written carelessly they collapse into one note about
vector stores told four times. So each one was given a different question to
answer and the scripts were written to reach it rather than to re-read the same
listing with a different threshold.

`vector-store-file-attach-failed` reads the **children**. A `vector_store.file`
carries `last_error.code`, one of exactly three values, and the parent store
carries a `failed` count that its own `status` field does not reflect: `status`
turns `completed` when nothing is still in progress, which is true whether the
files succeeded or failed. The script reconciles the two, because they can
disagree, and separately catches children pinned `in_progress` long after the
ingest ended.

`empty-vector-store-still-referenced` is the closest neighbour and reads the
**parent only**, for the ids your application actually configures. That input is
what makes it a different note: emptiness is not a fault until something names
the store. The two are told apart by one field. `file_counts.total == 0` means
nothing was ever attached and this note owns it; `total > 0` with
`completed == 0` means files were attached and did not index, and the attach
note owns that. The script prints which, rather than leaving the reader to work
it out, and names expiry as the cause when the store's `status` is `expired`.

`vector-store-expired-or-expiring` is the only finding in the batch that is in
the future. It reads the clock fields and nothing else. One correction made
while writing: `expires_after.anchor` has exactly one supported value,
`last_active_at`, so "check the anchor is the one you wanted" is advice about a
choice that does not exist. What the script does instead is compare the
`expires_at` the API reports against `last_active_at + days`, report the drift,
and trust the API's own number — because which operations count as activity is
not something either the object or the documentation states.

`vector-store-storage-cost-creeping` is a cost note rather than a correctness
one and is the only script here that reads the organization usage API. Bytes are
a stock, not a flow: they keep billing when traffic stops. The reading is a
90-day slope in `usage_bytes` against `num_requests` from the file search calls
report, priced off the cost report's `gibibyte_hours` unit. It deliberately does
not reconcile line items against a dashboard, which is a published note, and it
is not a per-token reading, which is another.

All four are OpenAI. Anthropic has no managed vector store object at all, so
there is nothing on that side to read; the FAQ on the first note says so rather
than implying parity.

Read only, and stricter than the section baseline: every request in this batch
is a GET, no script constructs a request body, and in particular no script ever
runs a `file_search` query to test a store. A retrieval query is a generation,
it is billed, and a note about a broken index has no business creating traffic
against it.
"""

CITE_VS = ("Vector stores — OpenAI API reference",
           "https://platform.openai.com/docs/api-reference/vector-stores")
CITE_VS_FILES = ("Vector store files — OpenAI API reference",
                 "https://platform.openai.com/docs/api-reference/vector-stores-files")
CITE_RETRIEVAL = ("File search — OpenAI platform docs",
                  "https://platform.openai.com/docs/guides/retrieval")
CITE_TOOLS_FS = ("File search tool — OpenAI platform docs",
                 "https://platform.openai.com/docs/guides/tools-file-search")
CITE_USAGE = ("Usage and costs — OpenAI API reference",
              "https://platform.openai.com/docs/api-reference/usage")
CITE_PRICING = ("Pricing — OpenAI platform docs",
                "https://platform.openai.com/docs/pricing")
CITE_OPENAPI = ("openai-openapi — the published OpenAPI specification",
                "https://github.com/openai/openai-openapi")
CITE_SDK = ("openai-python API surface",
            "https://github.com/openai/openai-python/blob/main/api.md")
CITE_FILES = ("Files — OpenAI API reference",
              "https://platform.openai.com/docs/api-reference/files")

REL_ATTACH = ("/llm/vector-store-file-attach-failed/",
              "The store that has files in it and never indexed some of them")
REL_EMPTY = ("/llm/empty-vector-store-still-referenced/",
             "The store that has nothing in it and is still named in your config")
REL_EXPIRY = ("/llm/vector-store-expired-or-expiring/",
              "The index that deletes itself on a schedule nobody diaried")
REL_BYTES = ("/llm/vector-store-storage-cost-creeping/",
             "What those retained bytes cost while nobody queries them")
REL_BATCH_ERR = ("/llm/batch-error-file-never-read/",
                 "The other file id nobody fetched, on a completely different object")
REL_TOOL_DEAD = ("/llm/tool-defined-but-never-called/",
                 "A tool wired into every request that never fires")
REL_BATCH_EXP = ("/llm/batch-expired-past-24h-window/",
                 "The other object on this platform that expires on a clock")
REL_MODALITY = ("/llm/audio-and-image-line-items-unnoticed/",
                "The line items a token dashboard never renders at all")
REL_OUTPUT = ("/llm/output-tokens-dominate-cost/",
              "The per-token reading, which storage is not")

GUIDES = [
{
"slug": "vector-store-file-attach-failed",
"title": "Files failed to index and file_search quietly returns less",
"description": "A vector_store.file carries last_error.code when parsing fails. The store's status still reads completed, because completed only means nothing is pending.",
"h1": "Files failed to index and file_search quietly returns less",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["openai vector store file failed last_error",
             "vector_store.file unsupported_file invalid_file",
             "openai file_counts failed not zero",
             "vector store stuck in_progress after ingest",
             "openai file search missing documents no error"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Needs OPENAI_API_KEY, a project key with read access to the project that owns the stores. No admin key, and no organization endpoint is touched.",
"lead": "Somebody in support says the assistant does not know about the September pricing change, and you know for a fact that the September pricing memo was in the ingest. You check, and it was: the upload succeeded, the attach call returned 200, the ingest job logged <em>812 files indexed</em> and exited zero. The store's <code>status</code> says <code>completed</code>. Every one of those things is true, and the memo is a scanned PDF with no text layer, so it is not in the index and never was.",
"short_answer": """<p>Two GETs per store with a <strong>project key</strong>. <code>GET /v1/vector_stores?limit=100</code> for the stores, then for each one <code>GET /v1/vector_stores/{vector_store_id}/files?filter=failed&amp;limit=100</code>, paged on <code>after</code>. Every returned child carries <code>last_error</code>, which is <code>null</code> on a healthy file and otherwise <code>{"code": ..., "message": ...}</code> where <code>code</code> is exactly one of <code>server_error</code>, <code>unsupported_file</code> or <code>invalid_file</code>.</p>
<p>The reason nobody sees this is the parent object. A vector store's <code>status</code> becomes <code>completed</code> when no file is still <code>in_progress</code>, which is true whether the files succeeded or failed, and the only aggregate signal is <code>file_counts.failed</code> sitting next to a large and reassuring <code>completed</code>. An ingest job that polls for <code>status == "completed"</code> and then declares the corpus ready is polling the wrong field.</p>
<p>Reconcile the two rather than trusting either. The script compares <code>file_counts.failed</code> against the number of children the filtered listing actually returns and reports a disagreement as its own finding, because a summary that counts failures the listing no longer contains means the failed children were detached and the repair was never finished.</p>
<p>Then the same listing with <code>filter=in_progress</code>, checking each child's <code>created_at</code> against the clock. A file still processing an hour after the ingest ended is pinned, not slow, and it keeps the parent's <code>status</code> at <code>in_progress</code> forever.</p>
<p>If a store has <code>file_counts.total == 0</code>, this is not the note. Nothing was ever attached, which is <a href="/llm/empty-vector-store-still-referenced/">a different fault with a different repair</a>, and the script says so rather than reporting a zero per cent failure rate.</p>""",
"problem": """<p>Attaching a file to a vector store is asynchronous and the acknowledgement is not the outcome. The request is accepted, a <code>vector_store.file</code> comes back in <code>in_progress</code>, and parsing, chunking and embedding happen afterwards on the server. Whatever happens then is recorded on the child object and nowhere else you are looking.</p>
<p>The things that fail are boring and common: a scanned PDF with no text layer, a password-protected document, an empty file, an extension the parser does not handle, something corrupt at the source. Each ends as <code>status: "failed"</code> with <code>last_error</code> populated. Nothing raises. No webhook fires. The next retrieval call succeeds and returns fewer results, and the only downstream symptom is that the model does not know something it should.</p>
<p>What makes it survive is that every summary you would naturally check looks fine. The ingest exit code is fine. The store's <code>status</code> is fine. The <code>completed</code> count is large. The one number that is not fine is <code>file_counts.failed</code>, which is four digits to the right of a number that is doing an excellent job of reassuring you.</p>
<p>The stalled case is the same shape with the clock instead of an error. A very large file, or an ingest that pushed past the platform's attachment rate, can leave individual children pinned in <code>in_progress</code> indefinitely. The parent stays <code>in_progress</code> as long as any child is, which at least looks unfinished &mdash; but only if somebody reads it, and the retrieval path does not.</p>""",
"why": """<p><strong>The finding lives on the child object, and every reflex points at the parent.</strong> <code>GET /v1/vector_stores/{id}</code> is the call people make, and it returns a status word and five integers. The three error codes, the human-readable message that says which page of the PDF broke, and the file id you need in order to fix anything are all on <code>vector_store.file</code>, which you only see by listing the store's files. A note that read only the parent could tell you 37 files failed and could not tell you what to do about any of them.</p>
<p><strong>The three codes have three different repairs, so bucketing by code is the output.</strong> <code>unsupported_file</code> is a format problem and the fix is a conversion at the source: OCR the scan, export to text or markdown. <code>invalid_file</code> usually means empty, corrupt or encrypted, and the fix is upstream of the API entirely. <code>server_error</code> is transient and the fix is to attach it again. A report that says "37 failures" sends somebody to look at 37 files; a report bucketed by code sends them to three decisions.</p>
<p><strong>A failed file with no <code>last_error</code> is a real state and must not be dropped.</strong> The field is nullable on every child, including failed ones. A reader that keys a dictionary on <code>last_error["code"]</code> either raises or silently discards those rows, and discarding them is worse: the failures with no stated reason are exactly the ones nobody has looked at. They get their own bucket here.</p>
<p><strong>The summary and the listing can disagree, and the disagreement is information.</strong> <code>file_counts.failed</code> is a stored aggregate; the filtered listing is paged and enumerates live children. When the count is non-zero and the listing returns nothing, somebody detached the failed files and stopped there, which is a half-finished repair rather than a healthy store. The script grades that separately instead of averaging the two numbers into a single confident wrong one.</p>
<p><strong>An empty store is not a zero per cent failure rate.</strong> Dividing <code>failed</code> by <code>total</code> when <code>total</code> is zero gives either an exception or a clean bill of health, and both are wrong. A store with nothing in it is a different fault, and the script routes it to the other note by name rather than grading it here.</p>""",
"steps": [
 {"h": "Use a project key for the project that owns the stores",
  "body": """<p><code>/v1/vector_stores</code> is a project-scoped path, so an organization admin key is the wrong credential here and a project key from the wrong project simply will not see the store. The official client still sends <code>OpenAI-Beta: assistants=v2</code> on every vector store call, so these scripts send it too rather than betting on where the listing is in its graduation out of that beta.</p>"""},
 {"h": "List the stores and read file_counts, not status",
  "body": """<p><code>GET /v1/vector_stores?limit=100</code>, paged on <code>after</code> with <code>has_more</code> and <code>last_id</code>. Read the five integers in <code>file_counts</code>. <code>status: "completed"</code> means no child is pending; it is not a statement that any child succeeded.</p>"""},
 {"h": "List the failed children and bucket them by last_error.code",
  "body": """<p><code>GET /v1/vector_stores/{vector_store_id}/files?filter=failed&amp;limit=100</code>, paged on <code>after</code>. <code>filter</code> accepts <code>in_progress</code>, <code>completed</code>, <code>failed</code> and <code>cancelled</code>. Bucket on <code>last_error.code</code> and keep a bucket for children whose <code>last_error</code> is null.</p>"""},
 {"h": "Reconcile the bucket total against file_counts.failed",
  "body": """<p>Equal numbers mean the summary and the children agree and the failure list is complete. A non-zero count with an empty listing means the failed children were removed and never re-attached, which the script reports as its own state rather than as zero failures.</p>"""},
 {"h": "Sweep for children pinned in_progress, and print the repair",
  "body": """<p><code>filter=in_progress</code> on the same path, comparing each child's <code>created_at</code> against the clock. Anything older than an hour is pinned rather than slow. The repair is printed per bucket &mdash; convert, fix at source, or re-attach &mdash; along with the durable one: make <code>file_counts.failed == 0</code> the completion gate in the ingest job, not <code>status == "completed"</code>.</p>"""},
],
"verify": """<p>Fix one bucket and re-run. The failure count should fall by exactly the size of that bucket, and the state should move to <code>complete</code> only when both the summary and the listing agree on zero. A store that moves from <code>attach-failed</code> to <code>counts-disagree</code> has had its failed files detached rather than repaired, which is the state this script exists to stop you shipping.</p>
<pre><code class="language-bash">python3 openai_vector_store_attach_failures.py
# 3 store(s) visible to this key
# attach-failed        vs_a1 handbook-corpus: 37 of 849 file(s) failed (4.4%)
#   unsupported_file   19 file(s)  file-9k2, file-9k4, file-9m1 ...
#   invalid_file       14 file(s)  file-7b1, file-7b8, file-8c2 ...
#   server_error        4 file(s)  file-2d9, file-3a0, file-3a7, file-4b1
#   repair: unsupported_file is a format the parser cannot read. OCR the scanned
#           PDFs and export the rest to .md or .txt, then attach again.
#   repair: invalid_file is usually empty, corrupt or password protected. Fix it
#           at the source; re-attaching the same bytes fails the same way.
#   repair: server_error is transient. Attach those 4 again and re-check.
#   repair: gate the ingest job on file_counts.failed == 0, not on
#           status == "completed", which only means nothing is pending.
# ingestion-stalled    vs_b2 policies: 2 file(s) in_progress for over 1h
# no-files             vs_c3 scratch: nothing has ever been attached, so this is
#                      the empty vector store note rather than this one.
# 2 finding(s)</code></pre>""",
"code_intro": "Two paged GETs per store and six pure functions. <code>counts</code>, which coerces the five <code>file_counts</code> integers so a missing key cannot become a string; <code>bucket_errors</code>, which groups the failed children by <code>last_error.code</code> and keeps a bucket for the ones with no error at all; <code>stalled</code>, which measures each <code>in_progress</code> child's age against the clock; <code>failure_rate</code>, which returns zero rather than raising on an empty store; <code>reconcile</code>, which reports the summary count and the listed count as two numbers instead of averaging them; and <code>verdict</code>, which routes an empty store to the other note by name before it grades anything.",
"py_file": "openai_vector_store_attach_failures.py",
"py": '''"""Find files that never indexed in an OpenAI vector store.

Read only. Every request is a GET: /v1/vector_stores for the parents, then
/v1/vector_stores/{id}/files with filter=failed and filter=in_progress for the
children. No request body is ever constructed, and in particular no file_search
query is ever run. A retrieval query is a generation, it is billed, and a script
about a broken index has no business creating traffic against it.

The subject is the child object. A vector_store.file carries last_error.code
with one of exactly three values; the parent carries a failed count that its own
status field does not reflect, because status becomes "completed" when nothing
is still in progress whether or not anything succeeded.

A store with no files at all is not this note, and is reported as such.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("openai_vector_store_attach_failures")

API = "https://api.openai.com/v1"

# The official client still sends this on every vector store call, so this
# script does too rather than betting on where the listing has got to in its
# graduation out of the Assistants beta. It is a GET either way.
BETA = {"OpenAI-Beta": "assistants=v2"}

# The complete set. last_error.code is documented as exactly these three, and a
# fourth arriving is worth reporting rather than bucketing into "other".
ERROR_CODES = ("server_error", "unsupported_file", "invalid_file")

# A failed child whose last_error is null. The field is nullable on every child
# including the failed ones, and a reader that keys on last_error["code"] either
# raises or drops these rows. Dropping them is worse: a failure with no stated
# reason is the one nobody has looked at.
UNREPORTED = "unreported"

REPAIRS = {
    "unsupported_file":
        "unsupported_file is a format the parser cannot read: a scan with no "
        "text layer, or an extension it does not handle. OCR the scans and "
        "export the rest to .md or .txt, then attach again.",
    "invalid_file":
        "invalid_file is usually empty, corrupt or password protected. Fix it "
        "at the source; re-attaching the same bytes fails the same way.",
    "server_error":
        "server_error is transient. Attach those files again and re-check "
        "before treating them as a content problem.",
    UNREPORTED:
        "these failed with no last_error at all. Fetch each one with GET "
        "/v1/vector_stores/{vector_store_id}/files/{file_id} before deciding, "
        "because a failure with no stated reason has not been looked at.",
}

FINDINGS = ("attach-failed", "ingestion-stalled", "counts-disagree")


def counts(store):
    """The five file_counts integers, coerced. Pure.

    A missing key becomes 0 rather than None, so every caller can do arithmetic
    without guarding, and a string that arrives where an integer was promised
    does not propagate into a division.
    """
    raw = (store or {}).get("file_counts") or {}
    out = {}
    for key in ("in_progress", "completed", "failed", "cancelled", "total"):
        try:
            out[key] = int(raw.get(key) or 0)
        except (TypeError, ValueError):
            out[key] = 0
    return out


def bucket_errors(files):
    """{last_error.code: [file_id, ...]} over the failed children. Pure.

    Only children whose status is actually "failed" are counted, because the
    filtered listing is a request parameter rather than a guarantee, and a
    caller that forgets the filter would otherwise bucket the whole store.
    """
    out = {}
    for entry in files or []:
        row = entry or {}
        if str(row.get("status") or "").strip().lower() != "failed":
            continue
        err = row.get("last_error") or {}
        code = str(err.get("code") or "").strip().lower() or UNREPORTED
        out.setdefault(code, []).append(str(row.get("id") or "?"))
    for ids in out.values():
        ids.sort()
    return out


def stalled(files, now, max_age=3600):
    """[(file_id, age_seconds)] for children pinned in_progress. Pure.

    Sorted oldest first. A child with no usable created_at is skipped rather
    than treated as infinitely old, which would report every store as stalled
    the first time the field shape changes.
    """
    out = []
    for entry in files or []:
        row = entry or {}
        if str(row.get("status") or "").strip().lower() != "in_progress":
            continue
        try:
            created = int(row.get("created_at") or 0)
        except (TypeError, ValueError):
            continue
        if created > 0 and (now - created) > max_age:
            out.append((str(row.get("id") or "?"), int(now - created)))
    out.sort(key=lambda r: (-r[1], r[0]))
    return out


def failure_rate(c):
    """failed / total. Pure. Zero on an empty store rather than an exception."""
    total = (c or {}).get("total") or 0
    if total <= 0:
        return 0.0
    return float((c or {}).get("failed") or 0) / float(total)


def reconcile(c, buckets):
    """(claimed, listed) failure counts. Pure.

    Two numbers, never one. file_counts.failed is a stored aggregate and the
    filtered listing enumerates live children, so they can legitimately differ,
    and averaging them into a single confident number destroys the only signal
    that says a repair was started and abandoned.
    """
    listed = sum(len(v) for v in (buckets or {}).values())
    try:
        claimed = int((c or {}).get("failed") or 0)
    except (TypeError, ValueError):
        claimed = 0
    return (claimed, listed)


def verdict(c, buckets, stalled_rows):
    """Classify one store. Pure. Returns (state, detail).

    The empty case is answered first and handed to the other note by name. A
    store with nothing in it has a zero per cent failure rate, which is true and
    useless, and its repair is re-running an ingest rather than fixing a format.
    """
    c = c or {}
    total = int(c.get("total") or 0)
    claimed, listed = reconcile(c, buckets)
    stalled_rows = list(stalled_rows or [])

    if total <= 0:
        return ("no-files",
                "nothing has ever been attached, so this is the empty vector "
                "store note rather than this one")
    if listed > 0:
        detail = ("%d of %d file(s) failed (%.1f%%)"
                  % (listed, total, failure_rate(c) * 100))
        if claimed != listed:
            detail += (" -- file_counts.failed says %d and the listing returns "
                       "%d, so read the listing" % (claimed, listed))
        return ("attach-failed", detail)
    if claimed > 0:
        return ("counts-disagree",
                "file_counts.failed is %d and the filtered listing returns "
                "none, which is what a half-finished repair looks like: the "
                "failed files were detached and never attached again"
                % claimed)
    if stalled_rows:
        oldest = stalled_rows[0][1] // 3600
        return ("ingestion-stalled",
                "%d file(s) still in_progress, the oldest for over %dh. The "
                "parent stays in_progress while any child is."
                % (len(stalled_rows), max(oldest, 1)))
    if int(c.get("in_progress") or 0) > 0:
        return ("still-ingesting",
                "%d file(s) in_progress and none of them old enough to call "
                "pinned. Re-run after the ingest settles."
                % int(c.get("in_progress") or 0))
    return ("complete",
            "%d file(s), all completed, and the summary agrees with the listing"
            % total)


def repair_lines(state, buckets=None, stalled_rows=()):
    """The repair for one verdict. Pure. Printed, never performed."""
    buckets = buckets or {}
    if state == "attach-failed":
        lines = [REPAIRS[code] for code in
                 sorted(buckets, key=lambda k: (-len(buckets[k]), k))
                 if code in REPAIRS]
        unknown = sorted(set(buckets) - set(REPAIRS))
        if unknown:
            lines.append("last_error.code came back as %s, which is not one of "
                         "the three documented values. Read the message field "
                         "before acting on it." % ", ".join(unknown))
        lines.append("gate the ingest job on file_counts.failed == 0, not on "
                     "status == \\"completed\\", which only means nothing is "
                     "pending.")
        return lines
    if state == "counts-disagree":
        return [
            "list the store's files without a filter and compare the ids "
            "against your ingest manifest. The failures are gone from the "
            "store and are still missing from retrieval.",
            "re-attach the manifest entries that no longer appear, then assert "
            "file_counts.failed == 0 and file_counts.completed == "
            "file_counts.total before declaring the store ready.",
        ]
    if state == "ingestion-stalled":
        oldest = list(stalled_rows or [])[:5]
        lines = ["detach and attach those files again rather than waiting. A "
                 "child pinned for hours is not going to finish on its own."]
        if oldest:
            lines.append("oldest pinned: " + ", ".join(
                "%s (%dh)" % (fid, age // 3600) for fid, age in oldest))
        lines.append("stagger large ingests, and poll file_counts.in_progress "
                     "down to zero with a timeout rather than assuming that "
                     "attach means indexed.")
        return lines
    if state == "no-files":
        return ["an empty store fails differently and is repaired differently. "
                "Re-run the ingest, or stop naming the store in "
                "vector_store_ids."]
    return []


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=90)
    if r.status_code in (401, 403):
        raise SystemExit("%d from OpenAI: /v1/vector_stores needs a project "
                         "key for the project that owns the stores"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def paged(session, path, max_pages=200, **params):
    """Walk an after/last_id cursor listing."""
    params = dict(params)
    for _ in range(max_pages):
        page = get(session, path, **params)
        data = page.get("data") or []
        for item in data:
            yield item
        if not page.get("has_more") or not data:
            return
        params["after"] = page.get("last_id") or (data[-1] or {}).get("id")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--store-id", action="append", default=[],
                    help="restrict to these store ids (repeatable)")
    ap.add_argument("--stalled-hours", type=float, default=1.0,
                    help="age at which an in_progress file is called pinned")
    args = ap.parse_args()

    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        log.error("set OPENAI_API_KEY to a project key for the project that "
                  "owns the vector stores")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key, **BETA})

    stores = list(paged(s, "/vector_stores", limit=100))
    wanted = set(args.store_id or [])
    if wanted:
        stores = [st for st in stores if (st or {}).get("id") in wanted]
    log.info("%d store(s) visible to this key", len(stores))

    now = int(time.time())
    max_age = int(args.stalled_hours * 3600)
    findings = 0

    for store in stores:
        sid = (store or {}).get("id") or "?"
        name = (store or {}).get("name") or "(unnamed)"
        c = counts(store)

        failed = []
        pending = []
        if c["total"] > 0:
            failed = list(paged(s, "/vector_stores/%s/files" % sid,
                                limit=100, filter="failed"))
            if c["in_progress"] > 0:
                pending = list(paged(s, "/vector_stores/%s/files" % sid,
                                     limit=100, filter="in_progress"))

        buckets = bucket_errors(failed)
        stalled_rows = stalled(pending, now, max_age)
        state, detail = verdict(c, buckets, stalled_rows)

        emit = log.warning if state in FINDINGS else log.info
        emit("%-20s %s %s: %s", state, sid, name, detail)
        if state == "attach-failed":
            for code in sorted(buckets, key=lambda k: (-len(buckets[k]), k)):
                ids = buckets[code]
                shown = ", ".join(ids[:3]) + (" ..." if len(ids) > 3 else "")
                emit("  %-18s %d file(s)  %s", code, len(ids), shown)
        for line in repair_lines(state, buckets, stalled_rows):
            emit("  repair: %s", line)
        if state in FINDINGS:
            findings += 1

    log.info("%d finding(s)", findings)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "openai-vector-store-attach-failures.mjs",
"js": '''/**
 * Find files that never indexed in an OpenAI vector store.
 *
 * Read only. Every request is a GET. No request body is constructed and no
 * file_search query is ever run, because a retrieval query is a generation and
 * a script about a broken index should not create traffic against it.
 *
 * The subject is the child object: a vector_store.file carries last_error.code
 * with one of exactly three values, while the parent's status becomes
 * "completed" when nothing is pending whether or not anything succeeded.
 */
const API = 'https://api.openai.com/v1';

// The official client still sends this on every vector store call.
const BETA = { 'OpenAI-Beta': 'assistants=v2' };

export const ERROR_CODES = ['server_error', 'unsupported_file', 'invalid_file'];

// A failed child whose last_error is null. Nullable on every child, and a
// reader that keys on last_error.code drops exactly the rows nobody has read.
export const UNREPORTED = 'unreported';

const REPAIRS = {
  unsupported_file:
    'unsupported_file is a format the parser cannot read: a scan with no text '
    + 'layer, or an extension it does not handle. OCR the scans and export the '
    + 'rest to .md or .txt, then attach again.',
  invalid_file:
    'invalid_file is usually empty, corrupt or password protected. Fix it at '
    + 'the source; re-attaching the same bytes fails the same way.',
  server_error:
    'server_error is transient. Attach those files again and re-check before '
    + 'treating them as a content problem.',
  [UNREPORTED]:
    'these failed with no last_error at all. Fetch each one with GET '
    + '/v1/vector_stores/{vector_store_id}/files/{file_id} before deciding, '
    + 'because a failure with no stated reason has not been looked at.',
};

const FINDINGS = new Set(['attach-failed', 'ingestion-stalled', 'counts-disagree']);

/** The five file_counts integers, coerced. Pure. */
export function counts(store) {
  const raw = store?.file_counts ?? {};
  const out = {};
  for (const key of ['in_progress', 'completed', 'failed', 'cancelled', 'total']) {
    const n = Number(raw[key] ?? 0);
    out[key] = Number.isFinite(n) ? Math.trunc(n) : 0;
  }
  return out;
}

/** {code: [fileId]} over the failed children. Pure. */
export function bucketErrors(files) {
  const out = {};
  for (const entry of files ?? []) {
    const row = entry ?? {};
    if (String(row.status ?? '').trim().toLowerCase() !== 'failed') continue;
    const code = String(row.last_error?.code ?? '').trim().toLowerCase() || UNREPORTED;
    (out[code] ??= []).push(String(row.id ?? '?'));
  }
  for (const ids of Object.values(out)) ids.sort();
  return out;
}

/** [[fileId, ageSeconds]] for children pinned in_progress. Pure. Oldest first. */
export function stalled(files, now, maxAge = 3600) {
  const out = [];
  for (const entry of files ?? []) {
    const row = entry ?? {};
    if (String(row.status ?? '').trim().toLowerCase() !== 'in_progress') continue;
    const created = Number(row.created_at ?? 0);
    if (!Number.isFinite(created) || created <= 0) continue;
    if (now - created > maxAge) out.push([String(row.id ?? '?'), Math.trunc(now - created)]);
  }
  out.sort((a, b) => (b[1] - a[1]) || a[0].localeCompare(b[0]));
  return out;
}

/** failed / total. Pure. Zero on an empty store rather than a division by zero. */
export function failureRate(c) {
  const total = Number(c?.total ?? 0);
  if (!(total > 0)) return 0;
  return Number(c?.failed ?? 0) / total;
}

/** [claimed, listed] failure counts. Pure. Two numbers, never one. */
export function reconcile(c, buckets) {
  const listed = Object.values(buckets ?? {}).reduce((a, v) => a + v.length, 0);
  const claimed = Number(c?.failed ?? 0);
  return [Number.isFinite(claimed) ? Math.trunc(claimed) : 0, listed];
}

/** Classify one store. Pure. Returns [state, detail]. */
export function verdict(c, buckets, stalledRows) {
  const cc = c ?? {};
  const total = Math.trunc(Number(cc.total ?? 0));
  const [claimed, listed] = reconcile(cc, buckets);
  const rows = [...(stalledRows ?? [])];

  if (total <= 0) {
    return ['no-files',
            'nothing has ever been attached, so this is the empty vector store '
            + 'note rather than this one'];
  }
  if (listed > 0) {
    let detail = `${listed} of ${total} file(s) failed `
      + `(${(failureRate(cc) * 100).toFixed(1)}%)`;
    if (claimed !== listed) {
      detail += ` -- file_counts.failed says ${claimed} and the listing returns `
        + `${listed}, so read the listing`;
    }
    return ['attach-failed', detail];
  }
  if (claimed > 0) {
    return ['counts-disagree',
            `file_counts.failed is ${claimed} and the filtered listing returns `
            + 'none, which is what a half-finished repair looks like: the failed '
            + 'files were detached and never attached again'];
  }
  if (rows.length) {
    const oldest = Math.max(Math.trunc(rows[0][1] / 3600), 1);
    return ['ingestion-stalled',
            `${rows.length} file(s) still in_progress, the oldest for over `
            + `${oldest}h. The parent stays in_progress while any child is.`];
  }
  if (Math.trunc(Number(cc.in_progress ?? 0)) > 0) {
    return ['still-ingesting',
            `${Math.trunc(Number(cc.in_progress))} file(s) in_progress and none of `
            + 'them old enough to call pinned. Re-run after the ingest settles.'];
  }
  return ['complete',
          `${total} file(s), all completed, and the summary agrees with the listing`];
}

/** The repair for one verdict. Pure. Printed, never performed. */
export function repairLines(state, buckets = {}, stalledRows = []) {
  const b = buckets ?? {};
  if (state === 'attach-failed') {
    const ordered = Object.keys(b).sort(
      (x, y) => (b[y].length - b[x].length) || x.localeCompare(y));
    const lines = ordered.filter((code) => REPAIRS[code]).map((code) => REPAIRS[code]);
    const unknown = ordered.filter((code) => !REPAIRS[code]);
    if (unknown.length) {
      lines.push(`last_error.code came back as ${unknown.join(', ')}, which is not `
        + 'one of the three documented values. Read the message field before '
        + 'acting on it.');
    }
    lines.push('gate the ingest job on file_counts.failed == 0, not on '
      + 'status == "completed", which only means nothing is pending.');
    return lines;
  }
  if (state === 'counts-disagree') {
    return [
      "list the store's files without a filter and compare the ids against your "
      + 'ingest manifest. The failures are gone from the store and are still '
      + 'missing from retrieval.',
      're-attach the manifest entries that no longer appear, then assert '
      + 'file_counts.failed == 0 and file_counts.completed == file_counts.total '
      + 'before declaring the store ready.',
    ];
  }
  if (state === 'ingestion-stalled') {
    const oldest = [...(stalledRows ?? [])].slice(0, 5);
    const lines = ['detach and attach those files again rather than waiting. A '
      + 'child pinned for hours is not going to finish on its own.'];
    if (oldest.length) {
      lines.push('oldest pinned: ' + oldest
        .map(([id, age]) => `${id} (${Math.trunc(age / 3600)}h)`).join(', '));
    }
    lines.push('stagger large ingests, and poll file_counts.in_progress down to '
      + 'zero with a timeout rather than assuming that attach means indexed.');
    return lines;
  }
  if (state === 'no-files') {
    return ['an empty store fails differently and is repaired differently. '
      + 'Re-run the ingest, or stop naming the store in vector_store_ids.'];
  }
  return [];
}

async function read(key, path, params) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, String(v));
  const r = await fetch(url, { headers: { Authorization: `Bearer ${key}`, ...BETA } });
  if (r.status === 401 || r.status === 403) {
    throw new Error(`${r.status} from OpenAI: /v1/vector_stores needs a project key `
                    + 'for the project that owns the stores');
  }
  if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
  return r.json();
}

async function* paged(key, path, params, maxPages = 200) {
  const q = { ...params };
  for (let i = 0; i < maxPages; i += 1) {
    const page = await read(key, path, q);
    const data = page.data ?? [];
    for (const item of data) yield item;
    if (!page.has_more || data.length === 0) return;
    q.after = page.last_id ?? data[data.length - 1]?.id;
  }
}

async function collect(key, path, params) {
  const out = [];
  for await (const item of paged(key, path, params)) out.push(item);
  return out;
}

async function main() {
  const key = process.env.OPENAI_API_KEY;
  if (!key) {
    console.error('set OPENAI_API_KEY to a project key for the project that owns '
                  + 'the vector stores');
    process.exitCode = 2;
    return;
  }
  const maxAge = Math.trunc(Number(process.env.STALLED_HOURS ?? 1) * 3600);
  const wanted = new Set((process.env.VECTOR_STORE_IDS ?? '')
    .split(/[,\\s]+/).filter(Boolean));

  let stores = await collect(key, '/vector_stores', { limit: 100 });
  if (wanted.size) stores = stores.filter((st) => wanted.has(st?.id));
  console.log(`${stores.length} store(s) visible to this key`);

  const now = Math.floor(Date.now() / 1000);
  let findings = 0;

  for (const store of stores) {
    const sid = store?.id ?? '?';
    const name = store?.name ?? '(unnamed)';
    const c = counts(store);

    let failed = [];
    let pending = [];
    if (c.total > 0) {
      failed = await collect(key, `/vector_stores/${sid}/files`,
                             { limit: 100, filter: 'failed' });
      if (c.in_progress > 0) {
        pending = await collect(key, `/vector_stores/${sid}/files`,
                                { limit: 100, filter: 'in_progress' });
      }
    }

    const buckets = bucketErrors(failed);
    const stalledRows = stalled(pending, now, maxAge);
    const [state, detail] = verdict(c, buckets, stalledRows);

    console.log(`${state.padEnd(20)} ${sid} ${name}: ${detail}`);
    if (state === 'attach-failed') {
      const ordered = Object.keys(buckets).sort(
        (x, y) => (buckets[y].length - buckets[x].length) || x.localeCompare(y));
      for (const code of ordered) {
        const ids = buckets[code];
        const shown = ids.slice(0, 3).join(', ') + (ids.length > 3 ? ' ...' : '');
        console.log(`  ${code.padEnd(18)} ${ids.length} file(s)  ${shown}`);
      }
    }
    for (const line of repairLines(state, buckets, stalledRows)) {
      console.log(`  repair: ${line}`);
    }
    if (FINDINGS.has(state)) findings += 1;
  }

  console.log(`${findings} finding(s)`);
  process.exitCode = findings ? 1 : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) await main();
''',
"test_intro": "The first test is the note: a store whose <code>status</code> is <code>completed</code> and whose <code>file_counts.failed</code> is 37 has to come back as a finding, and the failures have to arrive bucketed by code rather than as a number. Next to it, the case that keeps this note out of its neighbour's territory &mdash; a store with <code>total == 0</code> must be <code>no-files</code>, must not be a finding here, and must say which note owns it. Then the failed child with a null <code>last_error</code>, which a naive fold drops; the summary and the listing disagreeing, which is a half-finished repair rather than a healthy store; the pinned children measured against the clock; and <code>failure_rate</code> on an empty store, which must be zero and not an exception.",
"test_py_file": "test_openai_vector_store_attach_failures.py",
"test_py": '''from openai_vector_store_attach_failures import (UNREPORTED, bucket_errors,
                                                  counts, failure_rate,
                                                  reconcile, repair_lines,
                                                  stalled, verdict)


def store(total=0, completed=0, failed=0, in_progress=0, cancelled=0,
          status="completed"):
    return {"id": "vs_a1", "name": "handbook", "status": status,
            "file_counts": {"total": total, "completed": completed,
                            "failed": failed, "in_progress": in_progress,
                            "cancelled": cancelled}}


def child(fid, status, code=None, created_at=1_700_000_000):
    row = {"id": fid, "object": "vector_store.file", "status": status,
           "created_at": created_at, "vector_store_id": "vs_a1"}
    row["last_error"] = {"code": code, "message": "..."} if code else None
    return row


def test_a_completed_store_with_failed_children_is_the_finding():
    # The whole note. status is "completed" because nothing is pending, which
    # is exactly what an ingest job polls for before declaring the corpus ready.
    c = counts(store(total=849, completed=812, failed=37))
    buckets = bucket_errors(
        [child("file-9k%d" % i, "failed", "unsupported_file") for i in range(19)]
        + [child("file-7b%d" % i, "failed", "invalid_file") for i in range(14)]
        + [child("file-2d%d" % i, "failed", "server_error") for i in range(4)])
    state, detail = verdict(c, buckets, [])
    assert state == "attach-failed"
    assert "37 of 849" in detail
    assert sorted(buckets) == ["invalid_file", "server_error", "unsupported_file"]
    repairs = repair_lines(state, buckets)
    assert any("OCR" in line for line in repairs)
    assert any("file_counts.failed == 0" in line for line in repairs)


def test_an_empty_store_is_handed_to_the_other_note_by_name():
    # The boundary between this note and its closest neighbour, asserted rather
    # than described. total == 0 means nothing was ever attached; that is not a
    # zero per cent failure rate and it is not repaired the same way.
    c = counts(store(total=0))
    state, detail = verdict(c, {}, [])
    assert state == "no-files"
    assert "empty vector store note" in detail
    assert failure_rate(c) == 0.0
    assert any("vector_store_ids" in line for line in repair_lines(state))


def test_a_failed_child_with_no_last_error_keeps_its_own_bucket():
    buckets = bucket_errors([child("file-1", "failed", "invalid_file"),
                             child("file-2", "failed", None),
                             child("file-3", "completed", None)])
    assert buckets[UNREPORTED] == ["file-2"]
    assert buckets["invalid_file"] == ["file-1"]
    assert "completed" not in buckets
    assert any("has not been looked at" in line
               for line in repair_lines("attach-failed", buckets))


def test_the_summary_and_the_listing_can_disagree():
    # file_counts still counts 37 failures and the filtered listing returns
    # none: somebody detached the failed files and stopped there.
    state, detail = verdict(counts(store(total=812, completed=812, failed=37)),
                            {}, [])
    assert state == "counts-disagree"
    assert "half-finished repair" in detail
    assert any("ingest manifest" in line for line in repair_lines(state))
    assert reconcile({"failed": 37}, {}) == (37, 0)
    assert reconcile({"failed": 2}, {"server_error": ["a", "b"]}) == (2, 2)


def test_children_pinned_in_progress_are_measured_against_the_clock():
    now = 1_700_050_000
    rows = stalled([child("file-slow", "in_progress", created_at=now - 40_000),
                    child("file-newer", "in_progress", created_at=now - 20_000),
                    child("file-fresh", "in_progress", created_at=now - 60),
                    child("file-bad", "in_progress", created_at=None),
                    child("file-done", "completed", created_at=now - 90_000)],
                   now)
    assert [r[0] for r in rows] == ["file-slow", "file-newer"]
    state, detail = verdict(counts(store(total=5, completed=3, in_progress=2)),
                            {}, rows)
    assert state == "ingestion-stalled"
    assert "parent stays in_progress" in detail
    assert any("file-slow (11h)" in line
               for line in repair_lines(state, {}, rows))


def test_a_healthy_store_and_a_still_settling_one_are_not_findings():
    assert verdict(counts(store(total=40, completed=40)), {}, [])[0] == "complete"
    state, _ = verdict(counts(store(total=40, completed=38, in_progress=2)),
                       {}, [])
    assert state == "still-ingesting"
    assert repair_lines("complete") == []
    assert bucket_errors(None) == {} and stalled(None, 0) == []
    assert counts(None)["total"] == 0
    assert counts({"file_counts": {"total": "not-a-number"}})["total"] == 0


def test_an_unknown_error_code_is_reported_rather_than_bucketed_away():
    buckets = bucket_errors([child("file-x", "failed", "quota_exceeded")])
    lines = repair_lines("attach-failed", buckets)
    assert any("quota_exceeded" in line for line in lines)
    assert any("three documented values" in line for line in lines)
''',
"test_js_file": "openai-vector-store-attach-failures.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { UNREPORTED, bucketErrors, counts, failureRate, reconcile, repairLines,
         stalled, verdict } from './openai-vector-store-attach-failures.mjs';

const store = ({ total = 0, completed = 0, failed = 0, in_progress = 0,
                 cancelled = 0, status = 'completed' } = {}) =>
  ({ id: 'vs_a1', name: 'handbook', status,
     file_counts: { total, completed, failed, in_progress, cancelled } });

const child = (id, status, code = null, createdAt = 1700000000) =>
  ({ id, object: 'vector_store.file', status, created_at: createdAt,
     vector_store_id: 'vs_a1',
     last_error: code ? { code, message: '...' } : null });

test('a completed store with failed children is the finding', () => {
  const c = counts(store({ total: 849, completed: 812, failed: 37 }));
  const children = [];
  for (let i = 0; i < 19; i += 1) children.push(child(`file-9k${i}`, 'failed', 'unsupported_file'));
  for (let i = 0; i < 14; i += 1) children.push(child(`file-7b${i}`, 'failed', 'invalid_file'));
  for (let i = 0; i < 4; i += 1) children.push(child(`file-2d${i}`, 'failed', 'server_error'));
  const buckets = bucketErrors(children);
  const [state, detail] = verdict(c, buckets, []);
  assert.equal(state, 'attach-failed');
  assert.match(detail, /37 of 849/);
  assert.deepEqual(Object.keys(buckets).sort(),
                   ['invalid_file', 'server_error', 'unsupported_file']);
  const repairs = repairLines(state, buckets);
  assert.ok(repairs.some((l) => l.includes('OCR')));
  assert.ok(repairs.some((l) => l.includes('file_counts.failed == 0')));
});

test('an empty store is handed to the other note by name', () => {
  const c = counts(store({ total: 0 }));
  const [state, detail] = verdict(c, {}, []);
  assert.equal(state, 'no-files');
  assert.match(detail, /empty vector store note/);
  assert.equal(failureRate(c), 0);
  assert.ok(repairLines(state).some((l) => l.includes('vector_store_ids')));
});

test('a failed child with no last_error keeps its own bucket', () => {
  const buckets = bucketErrors([child('file-1', 'failed', 'invalid_file'),
                                child('file-2', 'failed', null),
                                child('file-3', 'completed', null)]);
  assert.deepEqual(buckets[UNREPORTED], ['file-2']);
  assert.deepEqual(buckets.invalid_file, ['file-1']);
  assert.equal(buckets.completed, undefined);
  assert.ok(repairLines('attach-failed', buckets)
    .some((l) => l.includes('has not been looked at')));
});

test('the summary and the listing can disagree', () => {
  const [state, detail] = verdict(
    counts(store({ total: 812, completed: 812, failed: 37 })), {}, []);
  assert.equal(state, 'counts-disagree');
  assert.match(detail, /half-finished repair/);
  assert.ok(repairLines(state).some((l) => l.includes('ingest manifest')));
  assert.deepEqual(reconcile({ failed: 37 }, {}), [37, 0]);
  assert.deepEqual(reconcile({ failed: 2 }, { server_error: ['a', 'b'] }), [2, 2]);
});

test('children pinned in_progress are measured against the clock', () => {
  const now = 1700050000;
  const rows = stalled([child('file-slow', 'in_progress', null, now - 40000),
                        child('file-newer', 'in_progress', null, now - 20000),
                        child('file-fresh', 'in_progress', null, now - 60),
                        child('file-bad', 'in_progress', null, null),
                        child('file-done', 'completed', null, now - 90000)], now);
  assert.deepEqual(rows.map((r) => r[0]), ['file-slow', 'file-newer']);
  const [state, detail] = verdict(
    counts(store({ total: 5, completed: 3, in_progress: 2 })), {}, rows);
  assert.equal(state, 'ingestion-stalled');
  assert.match(detail, /parent stays in_progress/);
  assert.ok(repairLines(state, {}, rows).some((l) => l.includes('file-slow (11h)')));
});

test('a healthy store and a still settling one are not findings', () => {
  assert.equal(verdict(counts(store({ total: 40, completed: 40 })), {}, [])[0],
               'complete');
  assert.equal(verdict(counts(store({ total: 40, completed: 38, in_progress: 2 })),
                       {}, [])[0], 'still-ingesting');
  assert.deepEqual(repairLines('complete'), []);
  assert.deepEqual(bucketErrors(null), {});
  assert.deepEqual(stalled(null, 0), []);
  assert.equal(counts(null).total, 0);
  assert.equal(counts({ file_counts: { total: 'not-a-number' } }).total, 0);
});

test('an unknown error code is reported rather than bucketed away', () => {
  const buckets = bucketErrors([child('file-x', 'failed', 'quota_exceeded')]);
  const lines = repairLines('attach-failed', buckets);
  assert.ok(lines.some((l) => l.includes('quota_exceeded')));
  assert.ok(lines.some((l) => l.includes('three documented values')));
});
''',
"faq": [
 ("How do I tell this apart from an empty vector store? They both retrieve nothing.",
  "One field. file_counts.total is zero on an empty store and non-zero here. If files were attached and some of them failed, this is the note and the repair is per error code: convert the format, fix the source file, or re-attach the transient failures. If nothing was ever attached, the store is empty, retrieval was never grounded at all, and the repair is to run the ingest or stop naming the store. The overlap case is a store that is empty because every attach failed, and the script separates that too: total greater than zero with completed at zero says the ingest ran and produced nothing, which is this note wearing the other note's symptoms."),
 ("Why not just check the store's status field?",
  "Because status does not mean what it looks like it means. A vector store's status becomes completed when no file is still in_progress. That is a statement about pendingness, not about success, and it is true of a store where every single file failed. The only aggregate that carries the failure is file_counts.failed, which sits next to a large completed count and gets read as noise. This is why the repair the script prints is to gate the ingest job on file_counts.failed == 0 rather than on the status word."),
 ("Is this the same as the batch error file nobody reads?",
  "No, and they are not even the same resource. That note is about a Batch object's error_file_id, a file id the platform hands you when a batch job produces per-line failures and which nothing forces you to fetch. This one reads vector_store.file objects, which are children of a vector store, carry a three-valued last_error.code, and have no downloadable error file at all. The only thing the two share is the shape of the mistake: a failure recorded on an object nobody lists."),
 ("Does the script ever run a search to check the store really works?",
  "No, deliberately. A file_search query is a generation: it is billed, it goes through a model, and it is a write in every sense that matters to this section. Everything here is a GET against the vector store and its children. That is also why the script cannot tell you whether retrieval quality is good, only whether the documents you attached are in the index at all, which is the question this note is about."),
 ("Anthropic has file search too. Why is this OpenAI only?",
  "Because Anthropic has no managed vector store object. There is a Files API, and there are search tools, but there is nothing on that side that corresponds to a persistent server-side index with an id, a file_counts summary and per-file ingestion errors you can list. Every note in this batch is OpenAI for that reason, and the honest version of the sentence is that there is no equivalent to read rather than that nobody has written it yet."),
],
"related": [REL_EMPTY, REL_EXPIRY, REL_BATCH_ERR],
"citations": [CITE_VS_FILES, CITE_VS, CITE_RETRIEVAL, CITE_OPENAPI],
},
{
"slug": "empty-vector-store-still-referenced",
"title": "An empty vector store is still named in vector_store_ids",
"description": "file_search returns 200 with zero citations and the model answers anyway. Read back the store ids your app configures and refuse to boot on an empty one.",
"h1": "An empty vector store is still named in vector_store_ids",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["openai vector store empty file_counts total 0",
             "file_search returns no citations",
             "vector_store_ids empty store still configured",
             "openai file search answers without documents",
             "validate vector store id at startup"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Needs OPENAI_API_KEY, a project key, and the store ids your application configures, passed as VECTOR_STORE_IDS or repeated --store-id. Without those ids the script has nothing to grade.",
"lead": "The retrieval feature is live and nobody has complained, which is the part that should worry you. Every request carries a <code>file_search</code> tool with a <code>vector_store_ids</code> array copied out of the config months ago; every response comes back 200 with no citations attached; and the model, asked what the refund window is, says thirty days in a confident and well-structured paragraph. It is thirty days in the training data. Your policy changed to fourteen in March, it is in the document you indexed, and the store that was supposed to hold that document has nothing in it.",
"short_answer": """<p>One GET per configured id with a <strong>project key</strong>, and the configured ids are the input: <code>GET /v1/vector_stores/{vector_store_id}</code> for each id your application actually passes in <code>vector_store_ids</code>, plus <code>GET /v1/vector_stores?limit=100</code> for the wider picture. Flag <code>file_counts.total == 0</code>, <code>file_counts.completed == 0</code>, or <code>usage_bytes == 0</code>.</p>
<p>Emptiness on its own is not a fault. A store nobody references is litter: it grounds nothing because nothing points at it, and it costs nothing because it holds no bytes. The finding only exists when an empty store is named in the tool configuration, which is why this script takes the ids from you rather than grading everything it can see.</p>
<p>The fourth case is an id that does not resolve at all &mdash; a 404 from a store deleted, expired out of existence, or created under a different project than the key you deployed with. That is the same failure one step further along, and <code>file_search</code> handles it about as loudly.</p>
<p>Then say why the store is empty, because that decides who fixes it. <code>file_counts.total == 0</code> means nothing was ever attached and the ingest is the repair. <code>total &gt; 0</code> with <code>completed == 0</code> means files were attached and none of them indexed, which is <a href="/llm/vector-store-file-attach-failed/">the attach-failure note</a> and is repaired per error code. And <code>status == "expired"</code> means the store emptied itself on a schedule, which is <a href="/llm/vector-store-expired-or-expiring/">the expiry note</a> and will happen again.</p>
<p>The durable fix is a startup assertion. For every id in <code>vector_store_ids</code>, read the store back and refuse to boot when <code>file_counts.completed == 0</code>. A retrieval feature that cannot retrieve should fail at deploy, not in an answer.</p>""",
"problem": """<p>The file search tool does not error on an empty index. It searches, finds nothing, and returns nothing, and that is a successful tool call. The model then does what a model does with a tool that returned no context: it answers from what it already knows. The output is fluent, plausible and ungrounded, and it looks exactly like the output you were hoping for, minus the citations that nobody is checking.</p>
<p>Stores get into this state by several ordinary routes and they all look the same afterwards. A create-then-attach sequence broke between the two calls, so the store exists with an id worth copying and nothing in it. An ingest ran against the wrong project. Every attach failed. Or the store hit its expiration policy, and expiry deletes the contained file objects, which turns a working index into an empty one without touching the id.</p>
<p>What keeps it alive is that the id is real. Everything downstream validates: the config parses, the tool schema is well formed, the API accepts the array, the request succeeds. Nothing in the chain has an opinion about whether the id points at anything, and the one component that could tell you &mdash; the store object, with five integers on it &mdash; is not on the request path at all.</p>
<p>And an id can stop resolving entirely. Stores are deletable, expiry eventually removes them, and a project key deployed to the wrong project will not see stores that exist perfectly well elsewhere. All three arrive as an id that does not answer, which your application discovers at request time if it discovers it at all.</p>""",
"why": """<p><strong>The configured ids are the input, and that is what makes this a different note from the rest of the batch.</strong> Every other script here reads the platform and grades what it finds. This one starts from what your application claims and checks it against the platform, which is the only order that can produce this finding: an empty store is a completely ordinary object right up until something names it. Pass the ids you deploy with, from the same source your application reads them from, or the script is grading a list you made up.</p>
<p><strong>An empty store that nobody references is not a finding and must not be reported as one.</strong> It holds no bytes so it bills nothing, it grounds nothing because no request mentions it, and every prototype leaves a few behind. Reporting them at the same severity as a referenced one trains people to skim the output, and the one line that mattered goes past with the nine that did not.</p>
<p><strong>Three fields say three different things about why the store is empty, and only one of them is repaired here.</strong> <code>total == 0</code> is "the ingest never ran", which this note owns. <code>total &gt; 0, completed == 0</code> is "the ingest ran and everything failed", which belongs to the attach-failure note and is fixed per error code. <code>status == "expired"</code> is "the store deleted its own contents", which belongs to the expiry note and will recur on the same schedule unless the policy changes. The script prints the cause with the finding, because otherwise all three land on the same engineer with the same useless instruction to look at the store.</p>
<p><strong><code>usage_bytes == 0</code> alongside completed files is an anomaly rather than a synonym.</strong> The three emptiness tests are usually redundant and occasionally are not, and the case where they disagree &mdash; completed files reported with no bytes retained &mdash; is worth its own state rather than being folded into the same word. It is graded, named, and left to a human, because guessing what it means would be worse than saying it is odd.</p>
<p><strong>An unresolvable id is a project problem far more often than a deletion.</strong> Vector stores are project-scoped, so a key issued in the wrong project sees a clean 404 for a store that is alive and well next door. The repair line says so first, because "your store was deleted" sends somebody to re-ingest a corpus that already exists.</p>""",
"steps": [
 {"h": "Get the ids from the same place your application gets them",
  "body": """<p><code>VECTOR_STORE_IDS</code> as a comma-separated list, or repeated <code>--store-id</code>. Read them out of the deployed configuration rather than from memory: an audit of the ids you believe are configured proves nothing about the ids that ship.</p>"""},
 {"h": "Read each configured store back with a project key",
  "body": """<p><code>GET /v1/vector_stores/{vector_store_id}</code>. A 404 is a finding rather than an error &mdash; usually the wrong project for the key, sometimes a store that expired or was deleted. Everything else returns the object with <code>file_counts</code>, <code>usage_bytes</code> and <code>status</code>.</p>"""},
 {"h": "Apply the three emptiness tests in order",
  "body": """<p><code>file_counts.total == 0</code> first, then <code>file_counts.completed == 0</code>, then <code>usage_bytes == 0</code>. The order is the point: the first says nothing was attached, the second says the attach failed, and running them the other way around reports every failed ingest as an empty store.</p>"""},
 {"h": "Name the cause from status and the counts",
  "body": """<p><code>status == "expired"</code> means the store deleted its own files. A non-zero <code>failed</code> count means the attaches failed. A non-zero <code>in_progress</code> count means it is still working and you are early. Anything else means the ingest never ran at all.</p>"""},
 {"h": "Sweep the rest of the listing, and print the assertion",
  "body": """<p><code>GET /v1/vector_stores?limit=100</code>, paged on <code>after</code>, for the empty stores nothing references. Report them quietly as litter. The repair for the real finding is a startup assertion over <code>vector_store_ids</code> that refuses to boot when <code>file_counts.completed == 0</code>.</p>"""},
],
"verify": """<p>Re-run after the ingest, with the same id list. Every configured store should read <code>grounded</code>, and the abandoned ones should still be listed and still not be findings. The most useful re-run is the one you do from a deploy environment rather than a laptop, because a key from the wrong project turns every configured id into <code>referenced-missing</code> and that is exactly the failure this catches.</p>
<pre><code class="language-bash">VECTOR_STORE_IDS=vs_a1,vs_b2,vs_c3,vs_d4 \\
  python3 openai_empty_vector_store_audit.py
# 4 configured id(s), 9 store(s) visible to this key
# referenced-empty          vs_a1 handbook: 0 file(s) attached, 0 bytes
#   cause: the ingest never ran against this store
#   repair: run the ingest, then re-read the store before shipping the id
#   repair: assert file_counts.completed > 0 for every id in vector_store_ids at
#           startup and refuse to boot. A retrieval feature that cannot retrieve
#           should fail at deploy, not in an answer.
# referenced-nothing-indexed vs_b2 policies: 40 attached, 0 completed, 40 failed
#   cause: files were attached and none of them indexed
#   repair: this is the attach failure note. Bucket the children by
#           last_error.code and repair per bucket, not per store.
# referenced-missing        vs_c3: no such store for this key
#   repair: check the project first. Vector stores are project scoped, so a key
#           from the wrong project 404s on a store that is alive next door.
# grounded                  vs_d4 pricing: 812 file(s) completed, 41.2 MiB
# abandoned-empty           2 empty store(s) nothing references, which is litter
# 3 finding(s)</code></pre>""",
"code_intro": "One GET per configured id, one paged listing, and five pure functions. <code>configured_ids</code>, which splits on commas or whitespace and de-duplicates while keeping order, so a trailing comma in an environment variable cannot become an empty id that 404s; <code>counts</code>, the same coercion of the five integers as its sibling note; <code>emptiness</code>, which runs the three tests in the order that keeps them meaning different things; <code>cause</code>, which reads <code>status</code> and the counts to say which note owns the repair; and <code>classify</code>, which grades a store only against whether something references it.",
"py_file": "openai_empty_vector_store_audit.py",
"py": '''"""Check that the vector store ids your application configures index anything.

Read only. One GET per configured id against /v1/vector_stores/{id}, plus a
paged GET of /v1/vector_stores for the wider picture. No request body is
constructed and no file_search query is ever run, because a retrieval query is
a generation and this script exists to say whether the index is empty, not to
find out what it would answer.

The configured ids are the input, and that is the whole design. An empty vector
store is an ordinary object; it only becomes a fault when something still names
it in vector_store_ids. So this reads your configuration first and the platform
second, which is the reverse of every other note in this batch.
"""
import argparse
import logging
import os
import re
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("openai_empty_vector_store_audit")

API = "https://api.openai.com/v1"

# The official client still sends this on every vector store call, so this
# script does too. It is a GET either way.
BETA = {"OpenAI-Beta": "assistants=v2"}

FINDINGS = ("referenced-empty", "referenced-nothing-indexed",
            "referenced-zero-bytes", "referenced-missing")

CAUSES = {
    "expired": "the store passed its expiration policy and deleted its own "
               "files. That is the expiry note, and it will happen again on "
               "the same schedule.",
    "attach-failed": "files were attached and none of them indexed. That is "
                     "the attach failure note: bucket the children by "
                     "last_error.code and repair per bucket, not per store.",
    "still-ingesting": "files are still processing. You are early rather than "
                       "broken; re-read once file_counts.in_progress is zero.",
    "never-ingested": "the ingest never ran against this store. Nothing was "
                      "ever attached to it.",
}


def configured_ids(*raw):
    """The store ids the application claims to use. Pure.

    Split on commas or whitespace, blanks dropped, order preserved, duplicates
    removed. A trailing comma in an environment variable is the common way an
    empty string becomes an id that 404s and gets reported as a missing store.
    """
    out, seen = [], set()
    for chunk in raw:
        if not chunk:
            continue
        items = chunk if isinstance(chunk, (list, tuple)) else [chunk]
        for item in items:
            for token in re.split(r"[,\\s]+", str(item or "").strip()):
                token = token.strip()
                if token and token not in seen:
                    seen.add(token)
                    out.append(token)
    return out


def counts(store):
    """The five file_counts integers, coerced. Pure."""
    raw = (store or {}).get("file_counts") or {}
    out = {}
    for key in ("in_progress", "completed", "failed", "cancelled", "total"):
        try:
            out[key] = int(raw.get(key) or 0)
        except (TypeError, ValueError):
            out[key] = 0
    return out


def usage_bytes(store):
    """usage_bytes as an integer. Pure. Missing or unparseable reads as 0."""
    try:
        return int((store or {}).get("usage_bytes") or 0)
    except (TypeError, ValueError):
        return 0


def emptiness(store):
    """How empty one store is. Pure. One of four words, tested in order.

    The order carries the meaning. total == 0 says nothing was ever attached;
    completed == 0 with files present says the attach failed. Running the tests
    the other way round reports every failed ingest as an empty store and sends
    the repair to the wrong place.
    """
    c = counts(store)
    if c["total"] <= 0:
        return "no-files"
    if c["completed"] <= 0:
        return "nothing-completed"
    if usage_bytes(store) <= 0:
        return "zero-bytes"
    return "indexed"


def cause(store):
    """Why the store is empty, as far as the object can say. Pure.

    Returns a key into CAUSES. status is read first because expiry is the one
    cause that recurs: an expired store deletes its contained files, so the
    counts afterwards look exactly like an ingest that never ran.
    """
    if str((store or {}).get("status") or "").strip().lower() == "expired":
        return "expired"
    c = counts(store)
    if c["failed"] > 0:
        return "attach-failed"
    if c["in_progress"] > 0:
        return "still-ingesting"
    return "never-ingested"


def classify(store, referenced):
    """Grade one store. Pure. Returns (state, detail).

    A store is only graded against whether something references it. Emptiness
    on its own bills nothing and grounds nothing, and reporting it at finding
    severity is how a report teaches people to skim it.
    """
    if store is None:
        if referenced:
            return ("referenced-missing",
                    "no such store for this key. Vector stores are project "
                    "scoped, so the usual cause is a key from the wrong "
                    "project rather than a deleted store.")
        return ("not-found", "no such store")

    c = counts(store)
    kind = emptiness(store)
    size = usage_bytes(store)

    if not referenced:
        if kind == "indexed":
            return ("unreferenced",
                    "%d file(s) completed, and nothing you passed names it"
                    % c["completed"])
        return ("abandoned-empty",
                "empty and unreferenced, which is litter rather than an outage")

    if kind == "no-files":
        return ("referenced-empty",
                "0 file(s) attached, 0 bytes")
    if kind == "nothing-completed":
        return ("referenced-nothing-indexed",
                "%d attached, 0 completed, %d failed, %d in progress"
                % (c["total"], c["failed"], c["in_progress"]))
    if kind == "zero-bytes":
        return ("referenced-zero-bytes",
                "%d file(s) report completed and usage_bytes is 0, which the "
                "three emptiness tests disagree about. Read it before acting."
                % c["completed"])
    return ("grounded",
            "%d file(s) completed, %.1f MiB" % (c["completed"], size / 1048576.0))


def repair_lines(state, why=None):
    """The repair for one verdict. Pure. Printed, never performed."""
    assertion = ("assert file_counts.completed > 0 for every id in "
                 "vector_store_ids at startup and refuse to boot. A retrieval "
                 "feature that cannot retrieve should fail at deploy, not in "
                 "an answer.")
    if state == "referenced-empty":
        lines = []
        if why == "expired":
            lines.append(CAUSES["expired"])
        lines.append("run the ingest, then re-read the store before shipping "
                     "the id.")
        lines.append(assertion)
        return lines
    if state == "referenced-nothing-indexed":
        return [CAUSES.get(why or "attach-failed", CAUSES["attach-failed"]),
                assertion]
    if state == "referenced-zero-bytes":
        return ["do not delete this one on the strength of a byte count. Read "
                "the store and one of its files before deciding what it is.",
                assertion]
    if state == "referenced-missing":
        return ["check the project first. A project key cannot see a store "
                "that lives in another project, and that 404 is identical to "
                "the one a deleted store returns.",
                "if the store really is gone, re-ingest and update the "
                "configured id in the same change.",
                assertion]
    if state == "abandoned-empty":
        return ["nothing references it and it holds no bytes, so it is not "
                "costing you anything. Delete it when convenient with "
                "DELETE /v1/vector_stores/{vector_store_id}."]
    return []


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=90)
    if r.status_code in (401, 403):
        raise SystemExit("%d from OpenAI: /v1/vector_stores needs a project key"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def get_optional(session, path):
    """One store, or None when it does not resolve for this key."""
    r = session.get(API + path, timeout=90)
    if r.status_code == 404:
        return None
    if r.status_code in (401, 403):
        raise SystemExit("%d from OpenAI: /v1/vector_stores needs a project key"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def paged(session, path, max_pages=200, **params):
    """Walk an after/last_id cursor listing."""
    params = dict(params)
    for _ in range(max_pages):
        page = get(session, path, **params)
        data = page.get("data") or []
        for item in data:
            yield item
        if not page.get("has_more") or not data:
            return
        params["after"] = page.get("last_id") or (data[-1] or {}).get("id")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--store-id", action="append", default=[],
                    help="a store id your application configures (repeatable)")
    args = ap.parse_args()

    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        log.error("set OPENAI_API_KEY to a project key for the project that "
                  "owns the vector stores")
        return 2

    wanted = configured_ids(os.environ.get("VECTOR_STORE_IDS"), args.store_id)
    if not wanted:
        log.error("pass the store ids your application configures, as "
                  "VECTOR_STORE_IDS or repeated --store-id. Without them this "
                  "script has nothing to grade: an empty store is only a "
                  "finding when something still names it.")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key, **BETA})

    stores = list(paged(s, "/vector_stores", limit=100))
    by_id = {(st or {}).get("id"): st for st in stores}
    log.info("%d configured id(s), %d store(s) visible to this key",
             len(wanted), len(stores))

    findings = 0
    for sid in wanted:
        store = by_id.get(sid)
        if store is None:
            store = get_optional(s, "/vector_stores/%s" % sid)
        state, detail = classify(store, referenced=True)
        why = cause(store) if store is not None else None
        name = (store or {}).get("name") or ""
        emit = log.warning if state in FINDINGS else log.info
        emit("%-26s %s %s: %s", state, sid, name, detail)
        if state in FINDINGS and store is not None:
            emit("  cause: %s", CAUSES[why])
        for line in repair_lines(state, why):
            emit("  repair: %s", line)
        if state in FINDINGS:
            findings += 1

    litter = [st for st in stores
              if (st or {}).get("id") not in set(wanted)
              and emptiness(st) != "indexed"]
    if litter:
        log.info("%-26s %d empty store(s) nothing references, which is litter",
                 "abandoned-empty", len(litter))
        for line in repair_lines("abandoned-empty"):
            log.info("  note: %s", line)

    log.info("%d finding(s)", findings)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "openai-empty-vector-store-audit.mjs",
"js": '''/**
 * Check that the vector store ids your application configures index anything.
 *
 * Read only. One GET per configured id plus a paged listing. No request body,
 * and no file_search query is ever run: a retrieval query is a generation, and
 * the question here is whether the index is empty rather than what it answers.
 *
 * The configured ids are the input. An empty vector store is an ordinary
 * object; it becomes a fault only when something still names it.
 */
const API = 'https://api.openai.com/v1';
const BETA = { 'OpenAI-Beta': 'assistants=v2' };

const FINDINGS = new Set(['referenced-empty', 'referenced-nothing-indexed',
                          'referenced-zero-bytes', 'referenced-missing']);

export const CAUSES = {
  expired:
    'the store passed its expiration policy and deleted its own files. That is '
    + 'the expiry note, and it will happen again on the same schedule.',
  'attach-failed':
    'files were attached and none of them indexed. That is the attach failure '
    + 'note: bucket the children by last_error.code and repair per bucket, not '
    + 'per store.',
  'still-ingesting':
    'files are still processing. You are early rather than broken; re-read once '
    + 'file_counts.in_progress is zero.',
  'never-ingested':
    'the ingest never ran against this store. Nothing was ever attached to it.',
};

/** The store ids the application claims to use. Pure. Order kept, dupes dropped. */
export function configuredIds(...raw) {
  const out = [];
  const seen = new Set();
  for (const chunk of raw) {
    if (!chunk) continue;
    const items = Array.isArray(chunk) ? chunk : [chunk];
    for (const item of items) {
      for (const token of String(item ?? '').trim().split(/[,\\s]+/)) {
        if (token && !seen.has(token)) { seen.add(token); out.push(token); }
      }
    }
  }
  return out;
}

/** The five file_counts integers, coerced. Pure. */
export function counts(store) {
  const raw = store?.file_counts ?? {};
  const out = {};
  for (const key of ['in_progress', 'completed', 'failed', 'cancelled', 'total']) {
    const n = Number(raw[key] ?? 0);
    out[key] = Number.isFinite(n) ? Math.trunc(n) : 0;
  }
  return out;
}

/** usage_bytes as an integer. Pure. Missing or unparseable reads as 0. */
export function usageBytes(store) {
  const n = Number(store?.usage_bytes ?? 0);
  return Number.isFinite(n) ? Math.trunc(n) : 0;
}

/** How empty one store is. Pure. Four words, tested in a load-bearing order. */
export function emptiness(store) {
  const c = counts(store);
  if (c.total <= 0) return 'no-files';
  if (c.completed <= 0) return 'nothing-completed';
  if (usageBytes(store) <= 0) return 'zero-bytes';
  return 'indexed';
}

/** Why the store is empty, as far as the object can say. Pure. */
export function cause(store) {
  if (String(store?.status ?? '').trim().toLowerCase() === 'expired') return 'expired';
  const c = counts(store);
  if (c.failed > 0) return 'attach-failed';
  if (c.in_progress > 0) return 'still-ingesting';
  return 'never-ingested';
}

/** Grade one store. Pure. Returns [state, detail]. */
export function classify(store, referenced) {
  if (store === null || store === undefined) {
    if (referenced) {
      return ['referenced-missing',
              'no such store for this key. Vector stores are project scoped, so '
              + 'the usual cause is a key from the wrong project rather than a '
              + 'deleted store.'];
    }
    return ['not-found', 'no such store'];
  }

  const c = counts(store);
  const kind = emptiness(store);
  const size = usageBytes(store);

  if (!referenced) {
    if (kind === 'indexed') {
      return ['unreferenced',
              `${c.completed} file(s) completed, and nothing you passed names it`];
    }
    return ['abandoned-empty',
            'empty and unreferenced, which is litter rather than an outage'];
  }

  if (kind === 'no-files') return ['referenced-empty', '0 file(s) attached, 0 bytes'];
  if (kind === 'nothing-completed') {
    return ['referenced-nothing-indexed',
            `${c.total} attached, 0 completed, ${c.failed} failed, `
            + `${c.in_progress} in progress`];
  }
  if (kind === 'zero-bytes') {
    return ['referenced-zero-bytes',
            `${c.completed} file(s) report completed and usage_bytes is 0, which `
            + 'the three emptiness tests disagree about. Read it before acting.'];
  }
  return ['grounded',
          `${c.completed} file(s) completed, ${(size / 1048576).toFixed(1)} MiB`];
}

/** The repair for one verdict. Pure. Printed, never performed. */
export function repairLines(state, why = null) {
  const assertion = 'assert file_counts.completed > 0 for every id in '
    + 'vector_store_ids at startup and refuse to boot. A retrieval feature that '
    + 'cannot retrieve should fail at deploy, not in an answer.';
  if (state === 'referenced-empty') {
    const lines = [];
    if (why === 'expired') lines.push(CAUSES.expired);
    lines.push('run the ingest, then re-read the store before shipping the id.');
    lines.push(assertion);
    return lines;
  }
  if (state === 'referenced-nothing-indexed') {
    return [CAUSES[why] ?? CAUSES['attach-failed'], assertion];
  }
  if (state === 'referenced-zero-bytes') {
    return ['do not delete this one on the strength of a byte count. Read the '
            + 'store and one of its files before deciding what it is.', assertion];
  }
  if (state === 'referenced-missing') {
    return ['check the project first. A project key cannot see a store that '
            + 'lives in another project, and that 404 is identical to the one a '
            + 'deleted store returns.',
            'if the store really is gone, re-ingest and update the configured id '
            + 'in the same change.',
            assertion];
  }
  if (state === 'abandoned-empty') {
    return ['nothing references it and it holds no bytes, so it is not costing '
            + 'you anything. Delete it when convenient with '
            + 'DELETE /v1/vector_stores/{vector_store_id}.'];
  }
  return [];
}

async function read(key, path, params = {}) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, String(v));
  const r = await fetch(url, { headers: { Authorization: `Bearer ${key}`, ...BETA } });
  if (r.status === 401 || r.status === 403) {
    throw new Error(`${r.status} from OpenAI: /v1/vector_stores needs a project key`);
  }
  if (r.status === 404) return null;
  if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
  return r.json();
}

async function* paged(key, path, params, maxPages = 200) {
  const q = { ...params };
  for (let i = 0; i < maxPages; i += 1) {
    const page = await read(key, path, q);
    const data = page?.data ?? [];
    for (const item of data) yield item;
    if (!page?.has_more || data.length === 0) return;
    q.after = page.last_id ?? data[data.length - 1]?.id;
  }
}

async function main() {
  const key = process.env.OPENAI_API_KEY;
  if (!key) {
    console.error('set OPENAI_API_KEY to a project key for the project that owns '
                  + 'the vector stores');
    process.exitCode = 2;
    return;
  }
  const wanted = configuredIds(process.env.VECTOR_STORE_IDS);
  if (!wanted.length) {
    console.error('pass the store ids your application configures as '
                  + 'VECTOR_STORE_IDS. Without them this script has nothing to '
                  + 'grade: an empty store is only a finding when something '
                  + 'still names it.');
    process.exitCode = 2;
    return;
  }

  const stores = [];
  for await (const st of paged(key, '/vector_stores', { limit: 100 })) stores.push(st);
  const byId = new Map(stores.map((st) => [st?.id, st]));
  console.log(`${wanted.length} configured id(s), ${stores.length} store(s) `
              + 'visible to this key');

  let findings = 0;
  for (const sid of wanted) {
    const store = byId.get(sid) ?? await read(key, `/vector_stores/${sid}`);
    const [state, detail] = classify(store, true);
    const why = store ? cause(store) : null;
    console.log(`${state.padEnd(26)} ${sid} ${store?.name ?? ''}: ${detail}`);
    if (FINDINGS.has(state) && store) console.log(`  cause: ${CAUSES[why]}`);
    for (const line of repairLines(state, why)) console.log(`  repair: ${line}`);
    if (FINDINGS.has(state)) findings += 1;
  }

  const configured = new Set(wanted);
  const litter = stores.filter((st) => !configured.has(st?.id)
                                       && emptiness(st) !== 'indexed');
  if (litter.length) {
    console.log(`${'abandoned-empty'.padEnd(26)} ${litter.length} empty store(s) `
                + 'nothing references, which is litter');
    for (const line of repairLines('abandoned-empty')) console.log(`  note: ${line}`);
  }

  console.log(`${findings} finding(s)`);
  process.exitCode = findings ? 1 : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) await main();
''',
"test_intro": "The first two tests are the boundary this note shares with its neighbour, written as assertions rather than as prose: a store with <code>total == 0</code> is <code>referenced-empty</code> and its cause is that the ingest never ran, while a store with forty files attached and none completed is <code>referenced-nothing-indexed</code> and its repair line names the attach-failure note. The third is the same empty store whose <code>status</code> is <code>expired</code>, which has to attribute the emptiness to the schedule rather than to a missing ingest. Then the unreferenced empty store, which must not be a finding; the unresolvable id, whose repair has to mention the project before it mentions deletion; and <code>configured_ids</code> against the trailing comma that turns an environment variable into an empty id.",
"test_py_file": "test_openai_empty_vector_store_audit.py",
"test_py": '''from openai_empty_vector_store_audit import (cause, classify, configured_ids,
                                             counts, emptiness, repair_lines,
                                             usage_bytes)


def store(total=0, completed=0, failed=0, in_progress=0, bytes_=0,
          status="completed", sid="vs_a1", name="handbook"):
    return {"id": sid, "name": name, "status": status, "usage_bytes": bytes_,
            "file_counts": {"total": total, "completed": completed,
                            "failed": failed, "in_progress": in_progress,
                            "cancelled": 0}}


def test_a_configured_store_with_nothing_in_it_is_the_finding():
    empty = store(total=0)
    assert emptiness(empty) == "no-files"
    state, detail = classify(empty, referenced=True)
    assert state == "referenced-empty"
    assert "0 file(s) attached" in detail
    assert cause(empty) == "never-ingested"
    assert any("refuse to boot" in line
               for line in repair_lines(state, cause(empty)))


def test_attached_but_never_indexed_is_the_other_note():
    # The boundary. Forty files went in and none came out, which is an attach
    # failure wearing an empty store's symptoms, and it is repaired per
    # last_error.code rather than by re-running the ingest.
    broken = store(total=40, completed=0, failed=40)
    assert emptiness(broken) == "nothing-completed"
    state, detail = classify(broken, referenced=True)
    assert state == "referenced-nothing-indexed"
    assert "40 attached, 0 completed" in detail
    assert cause(broken) == "attach-failed"
    assert any("last_error.code" in line
               for line in repair_lines(state, cause(broken)))


def test_an_expired_store_is_empty_for_a_reason_that_will_recur():
    gone = store(total=0, status="expired")
    assert cause(gone) == "expired"
    lines = repair_lines("referenced-empty", cause(gone))
    assert any("same schedule" in line for line in lines)
    # And the counts alone cannot tell you: they are identical either way.
    assert counts(gone) == counts(store(total=0))


def test_an_empty_store_nobody_references_is_not_a_finding():
    state, detail = classify(store(total=0), referenced=False)
    assert state == "abandoned-empty"
    assert "litter" in detail
    assert classify(store(total=9, completed=9, bytes_=1024),
                    referenced=False)[0] == "unreferenced"


def test_an_id_that_does_not_resolve_blames_the_project_first():
    state, detail = classify(None, referenced=True)
    assert state == "referenced-missing"
    assert "project scoped" in detail
    lines = repair_lines(state)
    assert "project" in lines[0]
    assert classify(None, referenced=False)[0] == "not-found"


def test_completed_files_with_no_bytes_is_named_rather_than_guessed():
    odd = store(total=9, completed=9, bytes_=0)
    assert emptiness(odd) == "zero-bytes"
    state, detail = classify(odd, referenced=True)
    assert state == "referenced-zero-bytes"
    assert "disagree" in detail
    assert any("before deciding" in line for line in repair_lines(state))


def test_configured_ids_survives_the_trailing_comma():
    assert configured_ids("vs_a1,vs_b2,") == ["vs_a1", "vs_b2"]
    assert configured_ids("vs_a1 vs_b2\\nvs_a1") == ["vs_a1", "vs_b2"]
    assert configured_ids(None, ["vs_c3"], "vs_c3") == ["vs_c3"]
    assert configured_ids("") == [] and configured_ids() == []


def test_a_grounded_store_reports_its_size():
    good = store(total=812, completed=812, bytes_=43_200_512)
    state, detail = classify(good, referenced=True)
    assert state == "grounded"
    assert "41.2 MiB" in detail
    assert repair_lines(state) == []
    assert usage_bytes({"usage_bytes": "nope"}) == 0
    assert emptiness(None) == "no-files"
''',
"test_js_file": "openai-empty-vector-store-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { cause, classify, configuredIds, counts, emptiness, repairLines,
         usageBytes } from './openai-empty-vector-store-audit.mjs';

const store = ({ total = 0, completed = 0, failed = 0, in_progress = 0,
                 bytes = 0, status = 'completed', id = 'vs_a1',
                 name = 'handbook' } = {}) =>
  ({ id, name, status, usage_bytes: bytes,
     file_counts: { total, completed, failed, in_progress, cancelled: 0 } });

test('a configured store with nothing in it is the finding', () => {
  const empty = store({ total: 0 });
  assert.equal(emptiness(empty), 'no-files');
  const [state, detail] = classify(empty, true);
  assert.equal(state, 'referenced-empty');
  assert.match(detail, /0 file\\(s\\) attached/);
  assert.equal(cause(empty), 'never-ingested');
  assert.ok(repairLines(state, cause(empty)).some((l) => l.includes('refuse to boot')));
});

test('attached but never indexed is the other note', () => {
  const broken = store({ total: 40, completed: 0, failed: 40 });
  assert.equal(emptiness(broken), 'nothing-completed');
  const [state, detail] = classify(broken, true);
  assert.equal(state, 'referenced-nothing-indexed');
  assert.match(detail, /40 attached, 0 completed/);
  assert.equal(cause(broken), 'attach-failed');
  assert.ok(repairLines(state, cause(broken)).some((l) => l.includes('last_error.code')));
});

test('an expired store is empty for a reason that will recur', () => {
  const gone = store({ total: 0, status: 'expired' });
  assert.equal(cause(gone), 'expired');
  assert.ok(repairLines('referenced-empty', cause(gone))
    .some((l) => l.includes('same schedule')));
  assert.deepEqual(counts(gone), counts(store({ total: 0 })));
});

test('an empty store nobody references is not a finding', () => {
  const [state, detail] = classify(store({ total: 0 }), false);
  assert.equal(state, 'abandoned-empty');
  assert.match(detail, /litter/);
  assert.equal(classify(store({ total: 9, completed: 9, bytes: 1024 }), false)[0],
               'unreferenced');
});

test('an id that does not resolve blames the project first', () => {
  const [state, detail] = classify(null, true);
  assert.equal(state, 'referenced-missing');
  assert.match(detail, /project scoped/);
  assert.match(repairLines(state)[0], /project/);
  assert.equal(classify(undefined, false)[0], 'not-found');
});

test('completed files with no bytes is named rather than guessed', () => {
  const odd = store({ total: 9, completed: 9, bytes: 0 });
  assert.equal(emptiness(odd), 'zero-bytes');
  const [state, detail] = classify(odd, true);
  assert.equal(state, 'referenced-zero-bytes');
  assert.match(detail, /disagree/);
  assert.ok(repairLines(state).some((l) => l.includes('before deciding')));
});

test('configuredIds survives the trailing comma', () => {
  assert.deepEqual(configuredIds('vs_a1,vs_b2,'), ['vs_a1', 'vs_b2']);
  assert.deepEqual(configuredIds('vs_a1 vs_b2\\nvs_a1'), ['vs_a1', 'vs_b2']);
  assert.deepEqual(configuredIds(null, ['vs_c3'], 'vs_c3'), ['vs_c3']);
  assert.deepEqual(configuredIds(''), []);
  assert.deepEqual(configuredIds(), []);
});

test('a grounded store reports its size', () => {
  const good = store({ total: 812, completed: 812, bytes: 43200512 });
  const [state, detail] = classify(good, true);
  assert.equal(state, 'grounded');
  assert.match(detail, /41\\.2 MiB/);
  assert.deepEqual(repairLines(state), []);
  assert.equal(usageBytes({ usage_bytes: 'nope' }), 0);
  assert.equal(emptiness(null), 'no-files');
});
''',
"faq": [
 ("A store can be empty because every attach failed. Which note owns that?",
  "The attach-failure note, and the field that decides is file_counts.total. Zero means nothing was ever attached to this store, so there is no per-file error to look up and the repair is to run the ingest. Greater than zero with completed at zero means the ingest did run, produced nothing, and left a last_error.code on every child, so the repair is per error code and lives in the other note. This script prints the distinction as a cause line next to the finding rather than making you go and derive it, because the two states look identical from the retrieval side and are fixed by different people."),
 ("Why does the script need me to tell it which store ids I use?",
  "Because emptiness on its own is not a fault. An empty store nobody references holds no bytes, bills nothing and grounds nothing; every team that has prototyped retrieval has a few and they are harmless. The finding is the intersection of empty and referenced, and the platform cannot see the second half: nothing in the API records which store ids your code passes in vector_store_ids. Pass them from the deployed configuration rather than from memory, because the point is to check what ships."),
 ("The store id 404s but I can see it in the dashboard. What is going on?",
  "Almost always the project. Vector stores are project-scoped resources, so a project key issued in one project gets a clean 404 for a store that is alive and correct in another, and that 404 is byte-identical to the one a deleted store returns. Check which project the key belongs to before you re-ingest anything. The other two causes are a store that was deleted and a store that passed its expiration policy, and the expiry note covers the second."),
 ("Should the script just run a test query to see whether retrieval works?",
  "No. A file_search query is a generation: it costs money, it goes through a model, and every script in this section is read-only in the strict sense that it only makes GET requests. It would also answer a different question. A query tells you what the index returned for that one query; file_counts.completed tells you whether the index contains anything at all, which is the failure this note is about and the one a test query would most easily mask."),
 ("What does the startup assertion actually look like?",
  "For each id in your vector_store_ids configuration, GET /v1/vector_stores/{id} once during boot and refuse to start when the call 404s or when file_counts.completed is zero. It is one request per store per process start, it runs against the same key and the same project the application will use in production, and it converts a silent quality regression into a deploy that does not go out. That last property is the whole value: an ungrounded answer is invisible, and a failed boot is not."),
],
"related": [REL_ATTACH, REL_EXPIRY, REL_TOOL_DEAD],
"citations": [CITE_VS, CITE_TOOLS_FS, CITE_RETRIEVAL, CITE_SDK],
},
{
"slug": "vector-store-expired-or-expiring",
"title": "A vector store with expires_after deletes itself on a clock",
"description": "expires_after counts down from last_active_at, so an idle index evaporates and takes its file objects with it. Read expires_at, not your own arithmetic.",
"h1": "A vector store with expires_after deletes itself on a clock",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["openai vector store expires_after last_active_at",
             "vector store status expired files deleted",
             "openai vector store expiration policy remove",
             "vector store expires_at countdown idle",
             "file search index disappeared after a week"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Needs OPENAI_API_KEY, a project key. Optionally PERMANENT_VECTOR_STORE_IDS, the ids your team treats as permanent, which raises a scheduled expiry from a note to a finding.",
"lead": "The retrieval demo was built in one good afternoon in March, shown twice, and then left alone while the team shipped something else. In May somebody asks to show it again, it comes up, and it answers every question out of the model's own head. The store id is unchanged and still in the config. The store still exists. Its <code>status</code> is <code>expired</code>, its <code>file_counts</code> are all zero, and the file objects it held were deleted on a schedule that was set at creation by a tool nobody remembers configuring.",
"short_answer": """<p>One paged GET with a <strong>project key</strong>: <code>GET /v1/vector_stores?limit=100</code>. Every object carries <code>status</code>, <code>expires_after</code>, <code>expires_at</code> and <code>last_active_at</code>, and that is the whole reading. Flag three things: <code>status == "expired"</code>, an <code>expires_at</code> inside your notice window, and any policy at all on a store the team treats as permanent.</p>
<p><code>expires_after</code> is <code>{"anchor": "last_active_at", "days": N}</code>, and the anchor is not a choice: <code>last_active_at</code> is the only supported value. So the clock is an idle timer, which means it runs fastest during exactly the periods when nobody is watching the store &mdash; a holiday, a quarter spent on something else, the gap between a prototype and the decision to ship it.</p>
<p>When it fires, the store's <code>status</code> becomes <code>expired</code> and <strong>the contained <code>vector_store.file</code> objects are deleted</strong>. That is not recoverable from the store. Re-ingesting is the only repair, which is why the useful version of this check runs before the date rather than after it.</p>
<p>Read the <code>expires_at</code> the API returns rather than computing <code>last_active_at + days</code> yourself. The two can disagree, because which operations count as activity is not something the object or the reference states, and the script reports that disagreement as a number instead of resolving it. The API's own field is the countdown; your arithmetic is a guess about a definition you do not have.</p>""",
"problem": """<p>An expiration policy is a reasonable feature aimed at a real problem &mdash; retained bytes bill forever &mdash; and it fails because it is set once, at creation, by whoever wrote the create call, and is then invisible to everybody who uses the store afterwards. Nothing on the retrieval path mentions it. The tool configuration holds an id and no metadata. The store keeps working, right up until it does not.</p>
<p>The anchor makes it worse in a specific way. A countdown from creation would at least be predictable: seven days is seven days. A countdown from last activity resets whenever the store is used, which sounds safer and behaves in the opposite direction: the store survives as long as it is busy and dies during the quiet stretch, which is precisely the stretch in which nobody will notice that it did.</p>
<p>The consequence is asymmetric with almost everything else in this section. Most findings here are a number that is wrong or a control that is missing, and the repair is to change a setting. This one deletes data. The <code>vector_store.file</code> objects that the store contained are gone when it expires, and the only way back is to attach the source files again &mdash; assuming the source files still exist, which for a corpus assembled by hand during a prototype is not a safe assumption.</p>
<p>The reverse case is quieter and belongs on the other side of the ledger. A store with no policy at all never expires, retains its bytes indefinitely and is billed for them by the hour. That is not a fault; it is a bill, and it is <a href="/llm/vector-store-storage-cost-creeping/">the cost note</a> rather than this one.</p>""",
"why": """<p><strong>The anchor is not a setting, so advice about choosing it is advice about a choice that does not exist.</strong> <code>expires_after.anchor</code> has exactly one supported value, <code>last_active_at</code>. Every expiration policy on the platform is an idle timer, and a report that suggests reviewing whether the anchor is the one you wanted will send somebody to look for a dropdown that is not there. What the script reports instead is the anchor arriving as anything other than <code>last_active_at</code>, which would be a change to the platform rather than a fault in your configuration, and is worth reading about before acting.</p>
<p><strong>Trust the reported <code>expires_at</code> over a recomputed one, and report the difference rather than picking a winner.</strong> The obvious check is <code>last_active_at + days * 86400</code>, and it is the wrong one to act on, because what counts as activity is not stated anywhere you can read. Attaching a file plausibly counts; a metadata read plausibly does not; a retrieval query almost certainly does. The script computes both, uses the API's number for every decision, and prints the drift as a separate line so that a large gap is visible without ever being interpreted.</p>
<p><strong>A short window is not the finding. A short window on a store you thought was permanent is.</strong> Genuinely temporary stores &mdash; per-session uploads, one-off evaluations, anything built to be thrown away &mdash; should have a policy, and grading them as failures buries the one store that matters. That is why the ids you consider permanent are an input: passing them turns a scheduled expiry into a finding, and passing nothing leaves the script reporting the schedule without claiming it is wrong.</p>
<p><strong>The already-expired case has no repair and must not be printed as though it does.</strong> When <code>status</code> is <code>expired</code>, the contained file objects are already deleted and nothing on the API brings them back. Clearing the policy on a store in that state is a change that accomplishes nothing. The output says the files are gone, says re-ingesting is the only path, and puts the policy change on the new store rather than the dead one.</p>
<p><strong>A store that never expires is a cost line, not a clean bill of health.</strong> The absence of a policy is reported as its own state, because the same listing that answers this question also answers the opposite one, and a reader who sees only "no findings" will conclude the storage is free. It is billed by the hour on bytes retained, and that reading belongs to a different note.</p>""",
"steps": [
 {"h": "List the stores with a project key",
  "body": """<p><code>GET /v1/vector_stores?limit=100</code>, paged on <code>after</code> with <code>has_more</code> and <code>last_id</code>. One call answers this note entirely; there is no need to read a single child object.</p>"""},
 {"h": "Read status before anything else",
  "body": """<p><code>status == "expired"</code> is the past tense of this note. The contained <code>vector_store.file</code> objects are gone and the counts will all be zero, which is why an expired store and a never-ingested one look identical from the counts alone.</p>"""},
 {"h": "Read expires_after, and treat the anchor as fixed",
  "body": """<p><code>{"anchor": "last_active_at", "days": N}</code>. <code>last_active_at</code> is the only supported anchor, so every policy is an idle timer. An anchor with any other value is a platform change worth reading about, not a misconfiguration to correct.</p>"""},
 {"h": "Compare the API's expires_at against now, and against your own arithmetic",
  "body": """<p>Use the returned <code>expires_at</code> for the decision. Compute <code>last_active_at + days * 86400</code> as well and print the difference, because which operations reset the anchor is not documented and a large drift is worth seeing without being acted on.</p>"""},
 {"h": "Pass the ids you consider permanent, and print the repair",
  "body": """<p><code>PERMANENT_VECTOR_STORE_IDS</code> raises a scheduled expiry on those stores from a note to a finding. The repair for a live store is to clear the policy by updating it to null; for an expired one it is to re-ingest, because the files are not recoverable.</p>"""},
],
"verify": """<p>Clear the policy on the store that should not have had one, then re-run. It should move to <code>permanent</code>, with <code>expires_at</code> absent rather than far away. Re-run again a week later: the value of this check is that it fires before the date, and the only way to know it will is to have it running on a schedule shorter than the shortest <code>days</code> value it reports.</p>
<pre><code class="language-bash">PERMANENT_VECTOR_STORE_IDS=vs_a1,vs_d4 \\
  python3 openai_vector_store_expiry_audit.py --notice-days 7
# 6 store(s) visible to this key, 4 with an expiration policy
# expired              vs_c3 march-demo: expired 84 day(s) ago. The contained
#                      file objects were deleted and are not recoverable.
#   repair: re-ingest into a new store. Clearing the policy on this one changes
#           nothing, because the files it held are already gone.
# policy-on-permanent  vs_a1 handbook: 7 day idle timer on a store you listed as
#                      permanent, 2.1 day(s) left
#   repair: clear it by updating expires_after to null on the store.
#   drift: reported expires_at is 3h ahead of last_active_at + 7d
# expiring-soon        vs_b2 policies: 4.8 day(s) left, idle for 25.2 day(s)
# scheduled            vs_e5 session-uploads: 1 day idle timer, 0.6 day(s) left
# permanent            vs_d4 pricing: no policy, 41.2 MiB retained and billed
# 2 finding(s)</code></pre>""",
"code_intro": "One paged GET and six pure functions. <code>policy</code>, which normalises <code>expires_after</code> into an anchor and an integer day count or <code>None</code>; <code>expiry_at</code>, which coerces the timestamp; <code>idle_seconds</code>, which measures the store against the clock; <code>drift_seconds</code>, which computes the difference between the API's countdown and your own arithmetic and is never used to override the former; <code>anchor_note</code>, which fires only if the anchor is ever anything but <code>last_active_at</code>; and <code>expiry_state</code>, which reads <code>status</code> first, because an expired store has no repair that a live one has.",
"py_file": "openai_vector_store_expiry_audit.py",
"py": '''"""Find OpenAI vector stores that will delete themselves, and ones that have.

Read only. One paged GET against /v1/vector_stores. No request body is
constructed and no file_search query is ever run.

expires_after is {"anchor": "last_active_at", "days": N} and the anchor is not
a choice: last_active_at is the only supported value, so every expiration
policy on the platform is an idle timer. When it fires the store's status
becomes "expired" and the vector_store.file objects it contained are deleted,
which no read call can undo.

Decisions are made on the expires_at the API returns. The obvious alternative,
last_active_at + days, is computed too and reported as a drift, because which
operations reset the anchor is not something the object or the reference
states. Printing the difference is honest; resolving it would be a guess.
"""
import argparse
import logging
import os
import re
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("openai_vector_store_expiry_audit")

API = "https://api.openai.com/v1"
BETA = {"OpenAI-Beta": "assistants=v2"}
DAY = 86400

# The only anchor the API supports. Anything else is a platform change worth
# reading about rather than a misconfiguration worth correcting.
ANCHOR = "last_active_at"

FINDINGS = ("expired", "policy-on-permanent", "expiring-soon")


def id_set(*raw):
    """The store ids the team treats as permanent. Pure. Order irrelevant."""
    out = set()
    for chunk in raw:
        if not chunk:
            continue
        items = chunk if isinstance(chunk, (list, tuple)) else [chunk]
        for item in items:
            for token in re.split(r"[,\\s]+", str(item or "").strip()):
                if token.strip():
                    out.add(token.strip())
    return out


def policy(store):
    """(anchor, days) from expires_after, or None. Pure.

    A policy with a missing or unparseable day count reads as no policy rather
    than as a zero-day one, because a zero would grade every such store as
    already expiring and the object never actually says that.
    """
    raw = (store or {}).get("expires_after")
    if not isinstance(raw, dict):
        return None
    try:
        days = int(raw.get("days"))
    except (TypeError, ValueError):
        return None
    if days <= 0:
        return None
    anchor = str(raw.get("anchor") or "").strip().lower() or ANCHOR
    return (anchor, days)


def expiry_at(store):
    """expires_at as an integer, or None. Pure."""
    try:
        value = int((store or {}).get("expires_at") or 0)
    except (TypeError, ValueError):
        return None
    return value or None


def idle_seconds(store, now):
    """Seconds since last_active_at, or None when the field is absent. Pure."""
    try:
        last = int((store or {}).get("last_active_at") or 0)
    except (TypeError, ValueError):
        return None
    return (now - last) if last > 0 else None


def drift_seconds(store):
    """reported expires_at minus last_active_at + days. Pure. None if unknown.

    Never used to override the reported value. It exists so that a large gap is
    visible, because the definition of activity that would explain it is not
    published anywhere a script can read.
    """
    pol = policy(store)
    reported = expiry_at(store)
    if not pol or reported is None:
        return None
    try:
        last = int((store or {}).get("last_active_at") or 0)
    except (TypeError, ValueError):
        return None
    if last <= 0:
        return None
    return reported - (last + pol[1] * DAY)


def anchor_note(store):
    """A line about an unexpected anchor, or None. Pure."""
    pol = policy(store)
    if pol and pol[0] != ANCHOR:
        return ("expires_after.anchor is %r and the only documented value is "
                "%r. Read the reference before treating this as a "
                "misconfiguration." % (pol[0], ANCHOR))
    return None


def expiry_state(store, now, permanent=(), notice_days=7):
    """Classify one store's clock. Pure. Returns (state, detail).

    status is read before anything else. An expired store has already lost the
    files it held, so it does not share a repair with a store that is merely
    close to the same fate.
    """
    store = store or {}
    sid = str(store.get("id") or "")
    pol = policy(store)
    reported = expiry_at(store)
    idle = idle_seconds(store, now)

    if str(store.get("status") or "").strip().lower() == "expired":
        ago = ""
        if reported:
            ago = " %.0f day(s) ago" % max((now - reported) / DAY, 0)
        return ("expired",
                "expired%s. The contained file objects were deleted and are "
                "not recoverable." % ago)

    if not pol:
        try:
            size = int(store.get("usage_bytes") or 0)
        except (TypeError, ValueError):
            size = 0
        return ("permanent",
                "no policy, %.1f MiB retained and billed" % (size / 1048576.0))

    left = ((reported - now) / DAY) if reported else None
    left_text = ("%.1f day(s) left" % left) if left is not None else \\
        "no expires_at reported"

    if sid in set(permanent or ()):
        return ("policy-on-permanent",
                "%d day idle timer on a store you listed as permanent, %s"
                % (pol[1], left_text))
    if left is not None and left <= notice_days:
        idle_text = (", idle for %.1f day(s)" % (idle / DAY)) if idle else ""
        return ("expiring-soon", "%s%s" % (left_text, idle_text))
    return ("scheduled", "%d day idle timer, %s" % (pol[1], left_text))


def repair_lines(state, store=None):
    """The repair for one verdict. Pure. Printed, never performed."""
    if state == "expired":
        return ["re-ingest into a new store. Clearing the policy on this one "
                "changes nothing, because the files it held are already gone.",
                "set the policy you actually want on the new store at creation, "
                "and put whatever produced the corpus into source control so "
                "the next re-ingest is a command rather than an afternoon."]
    if state == "policy-on-permanent":
        return ["clear it by updating expires_after to null on the store. The "
                "listing is a read; the clear is a write and is yours to run.",
                "the anchor is last_active_at and cannot be changed, so a "
                "permanent store cannot be expressed as a long policy. It has "
                "to be no policy at all."]
    if state == "expiring-soon":
        return ["decide which this store is before the date. Temporary is "
                "fine and needs no change; permanent means clearing the policy "
                "now rather than after the files are deleted.",
                "run this check on a schedule shorter than the smallest days "
                "value it reports, or it will tell you about the deletion "
                "afterwards."]
    if state == "permanent":
        return ["nothing expires here, which also means nothing is reclaimed. "
                "Retained bytes are billed by the hour whether or not anything "
                "queries them."]
    return []


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=90)
    if r.status_code in (401, 403):
        raise SystemExit("%d from OpenAI: /v1/vector_stores needs a project key"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def paged(session, path, max_pages=200, **params):
    """Walk an after/last_id cursor listing."""
    params = dict(params)
    for _ in range(max_pages):
        page = get(session, path, **params)
        data = page.get("data") or []
        for item in data:
            yield item
        if not page.get("has_more") or not data:
            return
        params["after"] = page.get("last_id") or (data[-1] or {}).get("id")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--notice-days", type=float, default=7.0,
                    help="how far ahead an expiry counts as soon")
    ap.add_argument("--permanent", action="append", default=[],
                    help="a store id your team treats as permanent (repeatable)")
    args = ap.parse_args()

    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        log.error("set OPENAI_API_KEY to a project key for the project that "
                  "owns the vector stores")
        return 2

    permanent = id_set(os.environ.get("PERMANENT_VECTOR_STORE_IDS"),
                       args.permanent)

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key, **BETA})

    stores = list(paged(s, "/vector_stores", limit=100))
    with_policy = [st for st in stores if policy(st)]
    log.info("%d store(s) visible to this key, %d with an expiration policy",
             len(stores), len(with_policy))

    now = int(time.time())
    findings = 0
    for store in stores:
        sid = (store or {}).get("id") or "?"
        name = (store or {}).get("name") or "(unnamed)"
        state, detail = expiry_state(store, now, permanent, args.notice_days)
        emit = log.warning if state in FINDINGS else log.info
        emit("%-20s %s %s: %s", state, sid, name, detail)
        for line in repair_lines(state, store):
            emit("  repair: %s", line)
        note = anchor_note(store)
        if note:
            emit("  anchor: %s", note)
        drift = drift_seconds(store)
        if drift is not None and abs(drift) > 3600:
            emit("  drift: reported expires_at is %.1fh %s last_active_at plus "
                 "the policy window", abs(drift) / 3600.0,
                 "ahead of" if drift > 0 else "behind")
        if state in FINDINGS:
            findings += 1

    log.info("%d finding(s)", findings)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "openai-vector-store-expiry-audit.mjs",
"js": '''/**
 * Find OpenAI vector stores that will delete themselves, and ones that have.
 *
 * Read only. One paged GET against /v1/vector_stores. No request body, and no
 * file_search query is ever run.
 *
 * expires_after is {anchor: "last_active_at", days: N} and the anchor is not a
 * choice, so every policy is an idle timer. Decisions are made on the reported
 * expires_at; last_active_at + days is computed only to be printed as a drift,
 * because which operations reset the anchor is not documented.
 */
const API = 'https://api.openai.com/v1';
const BETA = { 'OpenAI-Beta': 'assistants=v2' };
const DAY = 86400;

/** The only anchor the API supports. */
export const ANCHOR = 'last_active_at';

const FINDINGS = new Set(['expired', 'policy-on-permanent', 'expiring-soon']);

/** The store ids the team treats as permanent. Pure. */
export function idSet(...raw) {
  const out = new Set();
  for (const chunk of raw) {
    if (!chunk) continue;
    const items = Array.isArray(chunk) ? chunk : [chunk];
    for (const item of items) {
      for (const token of String(item ?? '').trim().split(/[,\\s]+/)) {
        if (token) out.add(token);
      }
    }
  }
  return out;
}

/** [anchor, days] from expires_after, or null. Pure. */
export function policy(store) {
  const raw = store?.expires_after;
  if (!raw || typeof raw !== 'object') return null;
  const days = Number(raw.days);
  if (!Number.isFinite(days) || Math.trunc(days) <= 0) return null;
  const anchor = String(raw.anchor ?? '').trim().toLowerCase() || ANCHOR;
  return [anchor, Math.trunc(days)];
}

/** expires_at as an integer, or null. Pure. */
export function expiryAt(store) {
  const n = Number(store?.expires_at ?? 0);
  return Number.isFinite(n) && n > 0 ? Math.trunc(n) : null;
}

/** Seconds since last_active_at, or null. Pure. */
export function idleSeconds(store, now) {
  const last = Number(store?.last_active_at ?? 0);
  if (!Number.isFinite(last) || last <= 0) return null;
  return now - Math.trunc(last);
}

/** reported expires_at minus last_active_at + days. Pure. Never overrides. */
export function driftSeconds(store) {
  const pol = policy(store);
  const reported = expiryAt(store);
  if (!pol || reported === null) return null;
  const last = Number(store?.last_active_at ?? 0);
  if (!Number.isFinite(last) || last <= 0) return null;
  return reported - (Math.trunc(last) + pol[1] * DAY);
}

/** A line about an unexpected anchor, or null. Pure. */
export function anchorNote(store) {
  const pol = policy(store);
  if (pol && pol[0] !== ANCHOR) {
    return `expires_after.anchor is '${pol[0]}' and the only documented value is `
      + `'${ANCHOR}'. Read the reference before treating this as a misconfiguration.`;
  }
  return null;
}

/** Classify one store's clock. Pure. Returns [state, detail]. */
export function expiryState(store, now, permanent = new Set(), noticeDays = 7) {
  const st = store ?? {};
  const sid = String(st.id ?? '');
  const pol = policy(st);
  const reported = expiryAt(st);
  const idle = idleSeconds(st, now);
  const perm = permanent instanceof Set ? permanent : new Set(permanent ?? []);

  if (String(st.status ?? '').trim().toLowerCase() === 'expired') {
    const ago = reported ? ` ${Math.max((now - reported) / DAY, 0).toFixed(0)} day(s) ago` : '';
    return ['expired',
            `expired${ago}. The contained file objects were deleted and are not `
            + 'recoverable.'];
  }

  if (!pol) {
    const size = Number(st.usage_bytes ?? 0);
    return ['permanent',
            `no policy, ${(Number.isFinite(size) ? size / 1048576 : 0).toFixed(1)} `
            + 'MiB retained and billed'];
  }

  const left = reported !== null ? (reported - now) / DAY : null;
  const leftText = left !== null ? `${left.toFixed(1)} day(s) left`
                                 : 'no expires_at reported';

  if (perm.has(sid)) {
    return ['policy-on-permanent',
            `${pol[1]} day idle timer on a store you listed as permanent, ${leftText}`];
  }
  if (left !== null && left <= noticeDays) {
    const idleText = idle ? `, idle for ${(idle / DAY).toFixed(1)} day(s)` : '';
    return ['expiring-soon', `${leftText}${idleText}`];
  }
  return ['scheduled', `${pol[1]} day idle timer, ${leftText}`];
}

/** The repair for one verdict. Pure. Printed, never performed. */
export function repairLines(state) {
  if (state === 'expired') {
    return ['re-ingest into a new store. Clearing the policy on this one changes '
            + 'nothing, because the files it held are already gone.',
            'set the policy you actually want on the new store at creation, and '
            + 'put whatever produced the corpus into source control so the next '
            + 're-ingest is a command rather than an afternoon.'];
  }
  if (state === 'policy-on-permanent') {
    return ['clear it by updating expires_after to null on the store. The listing '
            + 'is a read; the clear is a write and is yours to run.',
            'the anchor is last_active_at and cannot be changed, so a permanent '
            + 'store cannot be expressed as a long policy. It has to be no policy '
            + 'at all.'];
  }
  if (state === 'expiring-soon') {
    return ['decide which this store is before the date. Temporary is fine and '
            + 'needs no change; permanent means clearing the policy now rather '
            + 'than after the files are deleted.',
            'run this check on a schedule shorter than the smallest days value it '
            + 'reports, or it will tell you about the deletion afterwards.'];
  }
  if (state === 'permanent') {
    return ['nothing expires here, which also means nothing is reclaimed. '
            + 'Retained bytes are billed by the hour whether or not anything '
            + 'queries them.'];
  }
  return [];
}

async function read(key, path, params) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, String(v));
  const r = await fetch(url, { headers: { Authorization: `Bearer ${key}`, ...BETA } });
  if (r.status === 401 || r.status === 403) {
    throw new Error(`${r.status} from OpenAI: /v1/vector_stores needs a project key`);
  }
  if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
  return r.json();
}

async function* paged(key, path, params, maxPages = 200) {
  const q = { ...params };
  for (let i = 0; i < maxPages; i += 1) {
    const page = await read(key, path, q);
    const data = page.data ?? [];
    for (const item of data) yield item;
    if (!page.has_more || data.length === 0) return;
    q.after = page.last_id ?? data[data.length - 1]?.id;
  }
}

async function main() {
  const key = process.env.OPENAI_API_KEY;
  if (!key) {
    console.error('set OPENAI_API_KEY to a project key for the project that owns '
                  + 'the vector stores');
    process.exitCode = 2;
    return;
  }
  const permanent = idSet(process.env.PERMANENT_VECTOR_STORE_IDS);
  const noticeDays = Number(process.env.NOTICE_DAYS ?? 7);

  const stores = [];
  for await (const st of paged(key, '/vector_stores', { limit: 100 })) stores.push(st);
  const withPolicy = stores.filter((st) => policy(st));
  console.log(`${stores.length} store(s) visible to this key, ${withPolicy.length} `
              + 'with an expiration policy');

  const now = Math.floor(Date.now() / 1000);
  let findings = 0;
  for (const store of stores) {
    const sid = store?.id ?? '?';
    const name = store?.name ?? '(unnamed)';
    const [state, detail] = expiryState(store, now, permanent, noticeDays);
    console.log(`${state.padEnd(20)} ${sid} ${name}: ${detail}`);
    for (const line of repairLines(state)) console.log(`  repair: ${line}`);
    const note = anchorNote(store);
    if (note) console.log(`  anchor: ${note}`);
    const drift = driftSeconds(store);
    if (drift !== null && Math.abs(drift) > 3600) {
      console.log(`  drift: reported expires_at is ${(Math.abs(drift) / 3600).toFixed(1)}h `
                  + `${drift > 0 ? 'ahead of' : 'behind'} last_active_at plus the `
                  + 'policy window');
    }
    if (FINDINGS.has(state)) findings += 1;
  }

  console.log(`${findings} finding(s)`);
  process.exitCode = findings ? 1 : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) await main();
''',
"test_intro": "The first test is the state that has no repair: an expired store, whose output has to say the files are gone and has to refuse to suggest clearing a policy that no longer matters. The second is the one that does have a repair and only exists because you supplied a list &mdash; a seven-day timer on a store the team calls permanent, which must be a finding while the identical timer on a session-upload store is not. Then the drift, asserted to be reported and never applied; the anchor check, which must stay silent on the only value the API actually returns; and <code>policy</code> against an <code>expires_after</code> with no usable day count, which has to read as no policy rather than as a zero-day one.",
"test_py_file": "test_openai_vector_store_expiry_audit.py",
"test_py": '''from openai_vector_store_expiry_audit import (anchor_note, drift_seconds,
                                               expiry_at, expiry_state, id_set,
                                               idle_seconds, policy,
                                               repair_lines)

NOW = 1_800_000_000
DAY = 86400


def store(sid="vs_a1", name="handbook", status="completed", days=None,
          anchor="last_active_at", expires_at=None, last_active_at=None,
          usage_bytes=41_000_000):
    row = {"id": sid, "name": name, "status": status, "usage_bytes": usage_bytes,
           "last_active_at": last_active_at, "expires_at": expires_at,
           "file_counts": {"total": 9, "completed": 9, "failed": 0,
                           "in_progress": 0, "cancelled": 0}}
    if days is not None:
        row["expires_after"] = {"anchor": anchor, "days": days}
    return row


def test_an_expired_store_has_no_repair_that_touches_the_policy():
    # The one state in this note where nothing can be recovered. Saying "clear
    # the policy" here would be a change that accomplishes nothing at all.
    dead = store(status="expired", days=7, expires_at=NOW - 84 * DAY)
    state, detail = expiry_state(dead, NOW)
    assert state == "expired"
    assert "84 day(s) ago" in detail
    assert "not recoverable" in detail
    lines = repair_lines(state)
    assert any("re-ingest into a new store" in line for line in lines)
    assert not any("clear it by updating" in line for line in lines)


def test_the_same_timer_is_a_finding_only_on_a_store_you_called_permanent():
    live = store(sid="vs_a1", days=7, expires_at=NOW + 2 * DAY,
                 last_active_at=NOW - 5 * DAY)
    temp = store(sid="vs_e5", name="session-uploads", days=7,
                 expires_at=NOW + 2 * DAY, last_active_at=NOW - 5 * DAY)
    assert expiry_state(live, NOW, {"vs_a1"})[0] == "policy-on-permanent"
    assert expiry_state(temp, NOW, {"vs_a1"})[0] == "expiring-soon"
    assert any("has to be no policy at all" in line
               for line in repair_lines("policy-on-permanent"))


def test_the_reported_expiry_wins_and_the_drift_is_only_printed():
    # last_active_at + 7d would put this three hours earlier than the API says.
    # The decision uses the API's number; the gap is reported, never resolved.
    drifting = store(days=7, last_active_at=NOW - 5 * DAY,
                     expires_at=NOW + 2 * DAY + 3 * 3600)
    assert drift_seconds(drifting) == 3 * 3600
    left = (expiry_at(drifting) - NOW) / DAY
    assert 2.1 < left < 2.2
    assert expiry_state(drifting, NOW, set(), notice_days=7)[0] == "expiring-soon"
    assert drift_seconds(store(days=7)) is None
    assert drift_seconds(store(expires_at=NOW)) is None


def test_the_anchor_is_only_mentioned_when_it_is_not_the_documented_one():
    assert anchor_note(store(days=7)) is None
    assert anchor_note(store(days=7, anchor="last_active_at")) is None
    assert anchor_note(store()) is None
    note = anchor_note(store(days=7, anchor="created_at"))
    assert "created_at" in note and "last_active_at" in note


def test_a_policy_with_no_usable_day_count_reads_as_no_policy():
    assert policy(store(days=7)) == ("last_active_at", 7)
    assert policy(store()) is None
    assert policy({"expires_after": {"anchor": "last_active_at"}}) is None
    assert policy({"expires_after": {"anchor": "last_active_at", "days": 0}}) is None
    assert policy({"expires_after": "7 days"}) is None
    assert policy(None) is None


def test_a_store_with_no_policy_is_reported_as_a_bill_not_a_pass():
    state, detail = expiry_state(store(usage_bytes=43_200_512), NOW)
    assert state == "permanent"
    assert "41.2 MiB retained and billed" in detail
    assert any("billed by the hour" in line for line in repair_lines(state))


def test_the_clock_helpers_tolerate_a_missing_field():
    assert idle_seconds(store(last_active_at=NOW - 3 * DAY), NOW) == 3 * DAY
    assert idle_seconds(store(), NOW) is None
    assert expiry_at(store()) is None
    assert expiry_at({"expires_at": "soon"}) is None
    assert id_set("vs_a1, vs_b2", ["vs_a1"]) == {"vs_a1", "vs_b2"}
    assert id_set(None) == set()
    far = store(days=90, expires_at=NOW + 60 * DAY, last_active_at=NOW - 30 * DAY)
    assert expiry_state(far, NOW)[0] == "scheduled"
''',
"test_js_file": "openai-vector-store-expiry-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { anchorNote, driftSeconds, expiryAt, expiryState, idSet, idleSeconds,
         policy, repairLines } from './openai-vector-store-expiry-audit.mjs';

const NOW = 1800000000;
const DAY = 86400;

const store = ({ id = 'vs_a1', name = 'handbook', status = 'completed',
                 days = null, anchor = 'last_active_at', expiresAt = null,
                 lastActiveAt = null, usageBytes = 41000000 } = {}) => {
  const row = { id, name, status, usage_bytes: usageBytes,
                last_active_at: lastActiveAt, expires_at: expiresAt,
                file_counts: { total: 9, completed: 9, failed: 0,
                               in_progress: 0, cancelled: 0 } };
  if (days !== null) row.expires_after = { anchor, days };
  return row;
};

test('an expired store has no repair that touches the policy', () => {
  const dead = store({ status: 'expired', days: 7, expiresAt: NOW - 84 * DAY });
  const [state, detail] = expiryState(dead, NOW);
  assert.equal(state, 'expired');
  assert.match(detail, /84 day\\(s\\) ago/);
  assert.match(detail, /not recoverable/);
  const lines = repairLines(state);
  assert.ok(lines.some((l) => l.includes('re-ingest into a new store')));
  assert.ok(!lines.some((l) => l.includes('clear it by updating')));
});

test('the same timer is a finding only on a store you called permanent', () => {
  const live = store({ id: 'vs_a1', days: 7, expiresAt: NOW + 2 * DAY,
                       lastActiveAt: NOW - 5 * DAY });
  const temp = store({ id: 'vs_e5', name: 'session-uploads', days: 7,
                       expiresAt: NOW + 2 * DAY, lastActiveAt: NOW - 5 * DAY });
  assert.equal(expiryState(live, NOW, new Set(['vs_a1']))[0], 'policy-on-permanent');
  assert.equal(expiryState(temp, NOW, new Set(['vs_a1']))[0], 'expiring-soon');
  assert.ok(repairLines('policy-on-permanent')
    .some((l) => l.includes('has to be no policy at all')));
});

test('the reported expiry wins and the drift is only printed', () => {
  const drifting = store({ days: 7, lastActiveAt: NOW - 5 * DAY,
                           expiresAt: NOW + 2 * DAY + 3 * 3600 });
  assert.equal(driftSeconds(drifting), 3 * 3600);
  const left = (expiryAt(drifting) - NOW) / DAY;
  assert.ok(left > 2.1 && left < 2.2);
  assert.equal(expiryState(drifting, NOW, new Set(), 7)[0], 'expiring-soon');
  assert.equal(driftSeconds(store({ days: 7 })), null);
  assert.equal(driftSeconds(store({ expiresAt: NOW })), null);
});

test('the anchor is only mentioned when it is not the documented one', () => {
  assert.equal(anchorNote(store({ days: 7 })), null);
  assert.equal(anchorNote(store()), null);
  const note = anchorNote(store({ days: 7, anchor: 'created_at' }));
  assert.match(note, /created_at/);
  assert.match(note, /last_active_at/);
});

test('a policy with no usable day count reads as no policy', () => {
  assert.deepEqual(policy(store({ days: 7 })), ['last_active_at', 7]);
  assert.equal(policy(store()), null);
  assert.equal(policy({ expires_after: { anchor: 'last_active_at' } }), null);
  assert.equal(policy({ expires_after: { anchor: 'last_active_at', days: 0 } }), null);
  assert.equal(policy({ expires_after: '7 days' }), null);
  assert.equal(policy(null), null);
});

test('a store with no policy is reported as a bill not a pass', () => {
  const [state, detail] = expiryState(store({ usageBytes: 43200512 }), NOW);
  assert.equal(state, 'permanent');
  assert.match(detail, /41\\.2 MiB retained and billed/);
  assert.ok(repairLines(state).some((l) => l.includes('billed by the hour')));
});

test('the clock helpers tolerate a missing field', () => {
  assert.equal(idleSeconds(store({ lastActiveAt: NOW - 3 * DAY }), NOW), 3 * DAY);
  assert.equal(idleSeconds(store(), NOW), null);
  assert.equal(expiryAt(store()), null);
  assert.equal(expiryAt({ expires_at: 'soon' }), null);
  assert.deepEqual([...idSet('vs_a1, vs_b2', ['vs_a1'])].sort(), ['vs_a1', 'vs_b2']);
  assert.equal(idSet(null).size, 0);
  const far = store({ days: 90, expiresAt: NOW + 60 * DAY,
                      lastActiveAt: NOW - 30 * DAY });
  assert.equal(expiryState(far, NOW)[0], 'scheduled');
});
''',
"faq": [
 ("Can I change the anchor so the countdown runs from creation instead?",
  "No. expires_after.anchor has exactly one supported value, last_active_at, so every expiration policy on the platform is an idle timer and there is no creation-anchored variant to switch to. This matters for the repair: a store you want to keep cannot be expressed as a very long policy that you top up, it has to have no policy at all. The script reports an anchor with any other value not as something for you to correct but as a change to the platform worth reading about before acting on."),
 ("Why not just compute the expiry from last_active_at plus the day count?",
  "Because you do not know what activity means. The object gives you last_active_at and the reference does not enumerate which operations update it. A retrieval query almost certainly counts, attaching a file plausibly counts, reading the store's metadata plausibly does not, and betting on any of that puts a deletion date in your monitoring that the platform does not agree with. The script uses the expires_at the API returns for every decision and prints the difference between that and the naive sum as a drift line, so a large gap is visible without being interpreted."),
 ("The store's status is expired. Can I get the files back by clearing the policy?",
  "No. When a store expires, the vector_store.file objects it contained are deleted, and that is not reversible through the API. Clearing the policy on an expired store leaves you with an empty store and no countdown, which is worse than it sounds because it looks fixed. The only repair is to attach the sources again, into a new store or the same one, and the thing worth fixing at the same time is whatever made the corpus hard to rebuild: an ingest you can re-run from source control turns this from an incident into a command."),
 ("Is an expired store the same thing as an empty one?",
  "From the counts, yes, which is exactly the trap. An expired store reports zeroes across file_counts just like a store nothing was ever attached to, and only status tells them apart. The difference matters because the causes are different and one of them recurs: a never-ingested store needs an ingest, and an expired store needs an ingest plus a policy change, or it will be empty again on the same schedule. The empty-store note reads status for that reason and names expiry as the cause when it finds it."),
 ("Should every store have a policy then?",
  "Every store you would be happy to lose, yes, and that is more of them than most teams assume: per-session uploads, evaluation corpora, anything a prototype produced. Retained bytes are billed by the hour whether or not anything queries them, so a store with no policy is a standing cost rather than a free safety margin. The script reports policy-free stores with their retained size for that reason, as a bill rather than a pass, and the cost note is where that reading is developed properly."),
],
"related": [REL_EMPTY, REL_BYTES, REL_BATCH_EXP],
"citations": [CITE_VS, CITE_RETRIEVAL, CITE_OPENAPI, CITE_FILES],
},
{
"slug": "vector-store-storage-cost-creeping",
"title": "Vector store bytes grow while nobody queries the index",
"description": "Storage is a stock, not a flow: it bills by the hour whether or not anything searches it. Trend usage_bytes over 90 days against file search calls.",
"h1": "Vector store bytes grow while nobody queries the index",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Admin read key", "Python and Node.js", "Tests included"],
"keywords": ["openai vector store storage cost gibibyte hours",
             "organization usage vector_stores usage_bytes",
             "file_search_calls num_requests by vector_store_id",
             "openai retrieval storage bill growing",
             "vector store never queried delete"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Needs OPENAI_ADMIN_KEY, an organization admin key provisioned read-only, for the usage and cost reports. OPENAI_API_KEY, a project key, is optional and adds the per-store snapshot.",
"lead": "Somebody finally asks about the small line. It has been on the invoice for fourteen months, it has never been more than a couple of hundred dollars, and it is the only line that has gone up every single month regardless of what shipped. It is vector store storage. It is billed on bytes retained per hour rather than on anything anybody did, and a good deal of it is a corpus indexed for a demo in the spring of last year that has not been searched since the demo.",
"short_answer": """<p>Three GETs with an <strong>organization admin key</strong>, and the reading is a slope rather than a share. <code>GET /v1/organization/usage/vector_stores?start_time={now-90d}&amp;bucket_width=1d&amp;limit=31&amp;group_by=project_id</code>, paged on <code>next_page</code>, gives a daily <code>usage_bytes</code> series per project. Fit a trend across it.</p>
<p>Then the denominator that makes the slope mean something: <code>GET /v1/organization/usage/file_search_calls?start_time={now-90d}&amp;bucket_width=1d&amp;limit=31&amp;group_by=project_id&amp;group_by=vector_store_id</code>, whose results carry <code>num_requests</code> and <code>vector_store_id</code>. Bytes climbing while queries stay flat is the finding. Bytes climbing alongside queries is a corpus doing its job and is graded as such.</p>
<p>Price it off <code>GET /v1/organization/costs?start_time={now-90d}&amp;bucket_width=1d&amp;limit=31&amp;group_by=line_item</code>, selecting on <code>quantity_unit == "gibibyte_hours"</code> rather than on the line item's name. The unit is the thing that identifies storage, it is the thing that will not be renamed, and gibibyte-hours is the billing model stated out loud: you are paying for bytes multiplied by time.</p>
<p>One asymmetry decides the shape of the script. The bytes endpoint groups by <code>project_id</code> and nothing else, so there is <strong>no per-store byte series in the usage API at all</strong>. Queries can be grouped per store. To name the store rather than the project you need the current snapshot from <code>GET /v1/vector_stores</code> with a project key, joined against the per-store query counts &mdash; a store holding real bytes with zero <code>num_requests</code> across ninety days is retained waste, and that join is the only way to see it.</p>""",
"problem": """<p>Every other line on an LLM invoice is a flow. Tokens, tool calls, audio seconds, image counts: they are all driven by requests, so they fall to zero when the traffic does, and they are all things somebody chose to do. Storage is a stock. It is charged on how many bytes you are holding and for how long, so the bill continues at exactly the same rate through a quiet quarter, a code freeze and a product being retired.</p>
<p>The behaviour that produces it is not careless, which is why it persists. Indexing a corpus is a normal part of building retrieval and it is meant to be easy. Deleting it afterwards was never a ticket, because at the moment the work stops nobody has decided the work is over. The prototype might come back. The evaluation corpus might get re-run. And the monthly cost of keeping it is small enough that it never crosses the threshold at which anybody would ask.</p>
<p>So it compounds, and it compounds invisibly, because the number that would reveal it is a slope rather than a level. Any single month's storage line looks negligible. The same line plotted across ninety days against a flat query count is the whole argument, and nothing in the console or the invoice draws that comparison for you.</p>
<p>The reverse case matters just as much and is easy to trample. A corpus that is growing because the product is growing is supposed to cost more, and reporting it as waste is how a cost report gets ignored. The finding is not growth; it is growth without use.</p>""",
"why": """<p><strong>Bytes and queries do not come back at the same granularity, and the script is shaped around that.</strong> <code>/v1/organization/usage/vector_stores</code> supports exactly one grouping, <code>project_id</code>, so the usage API has no per-store byte series and never will produce one by asking harder. <code>/v1/organization/usage/file_search_calls</code> does support <code>vector_store_id</code>. So the trend is a per-project reading, and naming the individual store requires joining the per-store query counts against the current snapshot from <code>GET /v1/vector_stores</code>, which needs a project key rather than the admin key everything else here uses. Run it with only the admin key and you get a correct trend and no culprit, which the output says rather than implying the store list was empty.</p>
<p><strong>Selecting the storage cost by <code>quantity_unit</code> rather than by line-item name is what makes this survive a rename.</strong> <code>quantity_unit</code> is an enumerated field, and <code>gibibyte_hours</code> appears on exactly the storage lines. Matching a name string means the reconciliation quietly returns zero the first time the platform relabels something, and returning zero from a cost check is the failure mode that never gets noticed. This also keeps the note away from <a href="/llm/audio-and-image-line-items-unnoticed/">the line-item reconciliation note</a>, which is about a dashboard's coverage of the whole bill; this one reads one unit and one slope.</p>
<p><strong>Ninety days of daily buckets does not fit in one response.</strong> The usage endpoints cap <code>limit</code> at 31 buckets when <code>bucket_width</code> is <code>1d</code>, so the window has to be walked with the <code>page</code> parameter against <code>next_page</code>. A script that asks for ninety and reads what comes back gets a month, computes a slope over it, and reports a trend that is genuinely a third of the one you asked for.</p>
<p><strong>A slope needs a floor under it or it reports rounding.</strong> A project holding forty megabytes can double its storage in a week and the finding is worth nothing at all. The script requires an absolute size before it grades a growth rate, and reports the money next to the percentage every time, because a percentage with no dollars attached is how cost reports get argued with rather than acted on.</p>
<p><strong>This is not a per-token reading and does not belong next to one.</strong> <a href="/llm/output-tokens-dominate-cost/">The output-token note</a> is about the price of generating; this is about the price of holding. They move independently, they are fixed by different changes, and the only thing storage has in common with the rest of the bill is that it appears on it.</p>""",
"steps": [
 {"h": "Use an organization admin key, provisioned read-only",
  "body": """<p>Every <code>/v1/organization/*</code> path rejects a project key. Add a project key as well if you want the per-store snapshot, because <code>GET /v1/vector_stores</code> is project-scoped and the admin key cannot reach it.</p>"""},
 {"h": "Walk ninety days of daily byte buckets, one page at a time",
  "body": """<p><code>GET /v1/organization/usage/vector_stores?start_time={now-90d}&amp;bucket_width=1d&amp;limit=31&amp;group_by=project_id</code>. <code>limit</code> caps at 31 for daily buckets, so page on <code>next_page</code> until it is null. Each result carries <code>usage_bytes</code> and <code>project_id</code>.</p>"""},
 {"h": "Pull the query volume over the same window, grouped two ways",
  "body": """<p><code>GET /v1/organization/usage/file_search_calls</code> with <code>group_by=project_id&amp;group_by=vector_store_id</code>. Results carry <code>num_requests</code>, and both grouping fields are null on rows the API could not attribute, which are summed separately rather than folded into a store.</p>"""},
 {"h": "Price the storage by its unit, not by its name",
  "body": """<p><code>GET /v1/organization/costs?start_time={now-90d}&amp;bucket_width=1d&amp;limit=31&amp;group_by=line_item</code>, keeping only results whose <code>quantity_unit</code> is <code>gibibyte_hours</code>. That unit is the billing model written down: bytes multiplied by time.</p>"""},
 {"h": "Join the snapshot to name the stores, and print the repair",
  "body": """<p><code>GET /v1/vector_stores?limit=100</code> with a project key for each store's current <code>usage_bytes</code>, <code>last_active_at</code> and <code>name</code>. A store above the size floor with zero <code>num_requests</code> across the window is retained waste. The repair is a deletion for the dead ones and an expiration policy at creation for the rest, printed rather than run.</p>"""},
],
"verify": """<p>Delete one dead store and re-run a week later. The project's byte series should step down and stay down, and the <code>gibibyte_hours</code> quantity should fall in proportion. The reading that tells you the fix is durable is a second run a month after that: a project whose slope is flat while its query count is not has stopped accumulating, which is the actual goal rather than a one-off deletion.</p>
<pre><code class="language-bash">python3 openai_vector_store_storage_trend.py --days 90
# 90 day(s) of daily buckets across 3 project(s), 4 store(s) in the snapshot
# storage cost in the window: $412.88 over 41,288.0 gibibyte_hours
# bytes-growing-queries-flat  proj_research: 8.1 GiB -> 31.4 GiB (+288%), 0
#                             file search call(s) in 90 day(s)
#   repair: no query has touched this project's stores in the window. The bytes
#           are being retained, not used.
#   repair: idle stores holding real bytes:
#           vs_c3 march-demo        12.4 GiB, last active 148 day(s) ago
#           vs_e5 eval-corpus-v1     9.8 GiB, last active  96 day(s) ago
#   repair: delete the dead ones with DELETE /v1/vector_stores/{vector_store_id}
#           after archiving anything you still need.
#   repair: set an expiration policy at creation on stores that are meant to be
#           temporary, so the next prototype ages out on its own.
# bytes-and-queries-growing   proj_prod: 44.0 GiB -> 61.2 GiB (+39%), 1,204,551
#                             file search call(s). Growth, priced correctly.
# below-threshold             proj_ci: 0.1 GiB, under the 1.0 GiB floor
# 1 finding(s)</code></pre>""",
"code_intro": "Three paged GETs, one optional fourth, and seven pure functions. <code>byte_series</code> and <code>query_series</code>, which fold the usage buckets into per-project daily series and keep the unattributed rows under an explicit sentinel; <code>slope</code>, a least-squares fit in bytes per day that returns zero rather than raising on a single point; <code>growth</code>, which returns first, last, delta and percentage together so no caller has to recompute one from another; <code>searches_by_store</code>, the per-store query totals that the byte series cannot provide; <code>storage_lines</code>, which selects cost results on <code>quantity_unit</code> being <code>gibibyte_hours</code> rather than on a name; <code>idle_stores</code>, the join; and <code>verdict</code>, which puts an absolute size floor under every growth rate.",
"py_file": "openai_vector_store_storage_trend.py",
"py": '''"""Trend retained vector store bytes against the queries that justify them.

Read only. Three paged GETs against /v1/organization/* with an admin key, plus
one optional GET of /v1/vector_stores with a project key for the per-store
snapshot. No request body is constructed and no file_search query is ever run.

Storage is a stock rather than a flow: it bills on bytes retained per unit of
time, so it does not fall when traffic does. The finding is therefore a slope
rather than a share, and it is only a finding when the slope is not matched by
query volume. Bytes growing alongside searches is a corpus doing its job.

One asymmetry shapes everything below. The vector stores usage endpoint groups
by project_id and nothing else, so there is no per-store byte series to ask
for; file search calls can be grouped by vector_store_id. Naming an individual
store therefore requires the current snapshot, which needs a project key.
"""
import argparse
import datetime as dt
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("openai_vector_store_storage_trend")

API = "https://api.openai.com/v1"
BETA = {"OpenAI-Beta": "assistants=v2"}

# Rows the report could not attribute to a project or a store. Kept under an
# explicit name and never folded into a real id, because a null that becomes a
# key is how one enormous fictional project gets reported.
UNGROUPED = "ungrouped"

# The unit that identifies storage on the cost report. Selecting on this rather
# than on a line item's display name is the difference between a check that
# survives a relabel and one that silently starts returning zero.
STORAGE_UNIT = "gibibyte_hours"

GIB = 1073741824.0
DAY = 86400

FINDINGS = ("bytes-growing-queries-flat", "bytes-growing-never-queried")


def byte_series(buckets):
    """{project_id: [(start_time, usage_bytes)]} sorted by time. Pure."""
    rows = {}
    for bucket in buckets or []:
        start = (bucket or {}).get("start_time")
        for result in (bucket or {}).get("results") or []:
            row = result or {}
            key = str(row.get("project_id") or UNGROUPED)
            try:
                value = int(row.get("usage_bytes") or 0)
            except (TypeError, ValueError):
                continue
            rows.setdefault(key, []).append((int(start or 0), value))
    for points in rows.values():
        points.sort()
    return rows


def query_series(buckets):
    """{project_id: [(start_time, num_requests)]} sorted by time. Pure."""
    rows = {}
    for bucket in buckets or []:
        start = (bucket or {}).get("start_time")
        for result in (bucket or {}).get("results") or []:
            row = result or {}
            key = str(row.get("project_id") or UNGROUPED)
            try:
                value = int(row.get("num_requests") or 0)
            except (TypeError, ValueError):
                continue
            rows.setdefault(key, []).append((int(start or 0), value))
    for points in rows.values():
        points.sort()
    return rows


def searches_by_store(buckets):
    """{vector_store_id: total num_requests}. Pure.

    The one per-store number available anywhere in the usage API. There is no
    matching per-store byte series: the vector stores endpoint groups by
    project_id only.
    """
    rows = {}
    for bucket in buckets or []:
        for result in (bucket or {}).get("results") or []:
            row = result or {}
            key = str(row.get("vector_store_id") or UNGROUPED)
            try:
                value = int(row.get("num_requests") or 0)
            except (TypeError, ValueError):
                continue
            rows[key] = rows.get(key, 0) + value
    return rows


def slope(points):
    """Least-squares trend in units per day. Pure. Zero on fewer than 2 points."""
    rows = sorted(points or [])
    if len(rows) < 2:
        return 0.0
    base = rows[0][0]
    xs = [(t - base) / float(DAY) for t, _ in rows]
    ys = [float(v) for _, v in rows]
    n = float(len(rows))
    mx = sum(xs) / n
    my = sum(ys) / n
    denom = sum((x - mx) ** 2 for x in xs)
    if denom <= 0:
        return 0.0
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / denom


def growth(points):
    """(first, last, delta, fraction) over a series. Pure.

    The fraction is delta over first, and is 0.0 rather than infinity when the
    series starts at zero, because "grew infinitely from nothing" is a division
    artefact rather than a reading anybody can act on.
    """
    rows = sorted(points or [])
    if not rows:
        return (0, 0, 0, 0.0)
    first = rows[0][1]
    last = rows[-1][1]
    delta = last - first
    fraction = (float(delta) / float(first)) if first > 0 else 0.0
    return (first, last, delta, fraction)


def storage_lines(buckets):
    """{line_item: {"dollars": x, "gibibyte_hours": q}} for storage only. Pure.

    Selected on quantity_unit, never on the line item's name.
    """
    rows = {}
    for bucket in buckets or []:
        for result in (bucket or {}).get("results") or []:
            row = result or {}
            if str(row.get("quantity_unit") or "") != STORAGE_UNIT:
                continue
            name = str(row.get("line_item") or "unlabelled")
            try:
                dollars = float((row.get("amount") or {}).get("value") or 0.0)
            except (TypeError, ValueError):
                dollars = 0.0
            try:
                quantity = float(row.get("quantity") or 0.0)
            except (TypeError, ValueError):
                quantity = 0.0
            entry = rows.setdefault(name, {"dollars": 0.0, STORAGE_UNIT: 0.0})
            entry["dollars"] += dollars
            entry[STORAGE_UNIT] += quantity
    return rows


def idle_stores(stores, searches, now, min_bytes=1073741824):
    """[(id, name, bytes, idle_days)] for stores nothing searched. Pure.

    The join the usage API cannot do for you: per-store query counts against a
    current snapshot. A store under the size floor is skipped, because a
    finding about 40 MiB is a finding about nothing.
    """
    out = []
    for store in stores or []:
        row = store or {}
        sid = str(row.get("id") or "")
        try:
            size = int(row.get("usage_bytes") or 0)
        except (TypeError, ValueError):
            continue
        if not sid or size < min_bytes:
            continue
        if int((searches or {}).get(sid, 0)) > 0:
            continue
        try:
            last = int(row.get("last_active_at") or 0)
        except (TypeError, ValueError):
            last = 0
        idle = int((now - last) / DAY) if last > 0 else -1
        out.append((sid, str(row.get("name") or "(unnamed)"), size, idle))
    out.sort(key=lambda r: (-r[2], r[0]))
    return out


def verdict(bytes_points, query_points, days, min_gib=1.0, min_growth=0.25):
    """Classify one project. Pure. Returns (state, detail).

    The absolute size floor comes before the growth rate, always. A project
    holding forty megabytes can triple its storage in a week and the reading is
    worth nothing.
    """
    first, last, _delta, fraction = growth(bytes_points)
    queries = sum(v for _, v in (query_points or []))

    if last < min_gib * GIB:
        return ("below-threshold",
                "%.1f GiB, under the %.1f GiB floor" % (last / GIB, min_gib))
    if fraction < min_growth:
        return ("flat",
                "%.1f GiB, %+.0f%% over %d day(s), %s file search call(s)"
                % (last / GIB, fraction * 100, days, format(queries, ",")))

    shape = ("%.1f GiB -> %.1f GiB (%+.0f%%)"
             % (first / GIB, last / GIB, fraction * 100))
    if queries <= 0:
        return ("bytes-growing-never-queried",
                "%s, 0 file search call(s) in %d day(s)" % (shape, days))
    if slope(query_points) <= 0:
        return ("bytes-growing-queries-flat",
                "%s while file search calls are flat or falling across the same "
                "window" % shape)
    return ("bytes-and-queries-growing",
            "%s, %s file search call(s). Growth, priced correctly."
            % (shape, format(queries, ",")))


def repair_lines(state, idle=()):
    """The repair for one verdict. Pure. Printed, never performed."""
    idle = list(idle or [])
    if state in FINDINGS:
        lines = []
        if state == "bytes-growing-never-queried":
            lines.append("no query has touched this project's stores in the "
                         "window. The bytes are being retained, not used.")
        else:
            lines.append("the corpus is growing and the query volume is not, "
                         "so you are paying more each month for the same "
                         "amount of retrieval.")
        if idle:
            lines.append("idle stores holding real bytes: " + "; ".join(
                "%s %s %.1f GiB%s" % (sid, name, size / GIB,
                                      "" if days < 0 else
                                      ", last active %d day(s) ago" % days)
                for sid, name, size, days in idle[:8]))
        else:
            lines.append("no per-store snapshot was read, so the project is "
                         "named and the store is not. Add a project key to "
                         "join the query counts against GET /v1/vector_stores.")
        lines.append("delete the dead ones with "
                     "DELETE /v1/vector_stores/{vector_store_id} after "
                     "archiving anything you still need.")
        lines.append("set an expiration policy at creation on stores that are "
                     "meant to be temporary, so the next prototype ages out on "
                     "its own rather than being somebody's future ticket.")
        return lines
    if state == "bytes-and-queries-growing":
        return ["nothing to do. This is a corpus that is being used more, and "
                "the storage line is supposed to follow it."]
    return []


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=90)
    if r.status_code in (401, 403):
        raise SystemExit("%d from OpenAI: /v1/organization/* needs an "
                         "organization admin key, not a project key"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def usage_buckets(session, path, params, max_pages=40):
    """Walk a usage report. limit caps at 31 daily buckets, so this pages."""
    params = dict(params)
    for _ in range(max_pages):
        page = get(session, path, **params)
        for bucket in page.get("data") or []:
            yield bucket
        if not page.get("has_more") or not page.get("next_page"):
            return
        params["page"] = page["next_page"]


def paged(session, path, max_pages=200, **params):
    """Walk an after/last_id cursor listing."""
    params = dict(params)
    for _ in range(max_pages):
        page = get(session, path, **params)
        data = page.get("data") or []
        for item in data:
            yield item
        if not page.get("has_more") or not data:
            return
        params["after"] = page.get("last_id") or (data[-1] or {}).get("id")


def window_start(days, now=None):
    """Unix seconds at midnight UTC, `days` ago."""
    now = now or dt.datetime.now(dt.timezone.utc)
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return int((midnight - dt.timedelta(days=days)).timestamp())


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=90,
                    help="days of daily buckets to trend (default 90)")
    ap.add_argument("--min-gib", type=float, default=1.0,
                    help="size floor below which growth is not graded")
    ap.add_argument("--min-growth", type=float, default=0.25,
                    help="fractional growth above which a slope is a finding")
    args = ap.parse_args()

    admin = os.environ.get("OPENAI_ADMIN_KEY")
    if not admin:
        log.error("set OPENAI_ADMIN_KEY to an organization admin key; a "
                  "project key cannot read /v1/organization/*")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + admin})

    start = window_start(args.days)
    common = {"start_time": start, "bucket_width": "1d", "limit": 31}

    bytes_buckets = list(usage_buckets(
        s, "/organization/usage/vector_stores",
        dict(common, group_by="project_id")))
    search_buckets = list(usage_buckets(
        s, "/organization/usage/file_search_calls",
        dict(common, group_by=["project_id", "vector_store_id"])))
    cost_buckets = list(usage_buckets(
        s, "/organization/costs", dict(common, group_by="line_item")))

    by_project = byte_series(bytes_buckets)
    queries = query_series(search_buckets)
    per_store = searches_by_store(search_buckets)

    stores = []
    project_key = os.environ.get("OPENAI_API_KEY")
    if project_key:
        p = requests.Session()
        p.headers.update({"Authorization": "Bearer " + project_key, **BETA})
        stores = list(paged(p, "/vector_stores", limit=100))

    log.info("%d day(s) of daily buckets across %d project(s), %d store(s) in "
             "the snapshot", args.days, len(by_project), len(stores))

    lines = storage_lines(cost_buckets)
    dollars = sum(v["dollars"] for v in lines.values())
    hours = sum(v[STORAGE_UNIT] for v in lines.values())
    if lines:
        log.info("storage cost in the window: $%s over %s %s",
                 format(round(dollars, 2), ",.2f"), format(round(hours, 1), ","),
                 STORAGE_UNIT)
    else:
        log.info("no cost result carried quantity_unit %r in the window, so "
                 "nothing is being billed for storage yet", STORAGE_UNIT)

    now = int(dt.datetime.now(dt.timezone.utc).timestamp())
    idle = idle_stores(stores, per_store, now,
                       min_bytes=int(args.min_gib * GIB))

    findings = 0
    for project in sorted(by_project):
        state, detail = verdict(by_project[project], queries.get(project, []),
                                args.days, args.min_gib, args.min_growth)
        emit = log.warning if state in FINDINGS else log.info
        emit("%-27s %s: %s", state, project, detail)
        for line in repair_lines(state, idle if state in FINDINGS else ()):
            emit("  repair: %s", line)
        if state in FINDINGS:
            findings += 1

    if per_store.get(UNGROUPED):
        log.info("%s file search call(s) came back with no vector_store_id and "
                 "are not attributed to a store",
                 format(per_store[UNGROUPED], ","))

    log.info("%d finding(s)", findings)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "openai-vector-store-storage-trend.mjs",
"js": '''/**
 * Trend retained vector store bytes against the queries that justify them.
 *
 * Read only. Three paged GETs against /v1/organization/* with an admin key,
 * plus one optional GET of /v1/vector_stores with a project key. No request
 * body is constructed and no file_search query is ever run.
 *
 * Storage is a stock rather than a flow, so the finding is a slope rather than
 * a share, and only when the slope is not matched by query volume.
 *
 * The vector stores usage endpoint groups by project_id and nothing else, so
 * naming an individual store needs the snapshot joined to per-store query
 * counts from the file search calls report.
 */
const API = 'https://api.openai.com/v1';
const BETA = { 'OpenAI-Beta': 'assistants=v2' };

/** Rows the report could not attribute. Never folded into a real id. */
export const UNGROUPED = 'ungrouped';

/** The unit that identifies storage on the cost report. Not a name match. */
export const STORAGE_UNIT = 'gibibyte_hours';

const GIB = 1073741824;
const DAY = 86400;

const FINDINGS = new Set(['bytes-growing-queries-flat',
                          'bytes-growing-never-queried']);

const num = (n) => Number(n).toLocaleString('en-US');

/** {projectId: [[startTime, usageBytes]]} sorted by time. Pure. */
export function byteSeries(buckets) {
  const rows = {};
  for (const bucket of buckets ?? []) {
    const start = Math.trunc(Number(bucket?.start_time ?? 0));
    for (const result of bucket?.results ?? []) {
      const key = String(result?.project_id ?? UNGROUPED);
      const value = Number(result?.usage_bytes ?? 0);
      if (!Number.isFinite(value)) continue;
      (rows[key] ??= []).push([start, Math.trunc(value)]);
    }
  }
  for (const points of Object.values(rows)) points.sort((a, b) => a[0] - b[0]);
  return rows;
}

/** {projectId: [[startTime, numRequests]]} sorted by time. Pure. */
export function querySeries(buckets) {
  const rows = {};
  for (const bucket of buckets ?? []) {
    const start = Math.trunc(Number(bucket?.start_time ?? 0));
    for (const result of bucket?.results ?? []) {
      const key = String(result?.project_id ?? UNGROUPED);
      const value = Number(result?.num_requests ?? 0);
      if (!Number.isFinite(value)) continue;
      (rows[key] ??= []).push([start, Math.trunc(value)]);
    }
  }
  for (const points of Object.values(rows)) points.sort((a, b) => a[0] - b[0]);
  return rows;
}

/** {vectorStoreId: total numRequests}. Pure. The only per-store number there is. */
export function searchesByStore(buckets) {
  const rows = {};
  for (const bucket of buckets ?? []) {
    for (const result of bucket?.results ?? []) {
      const key = String(result?.vector_store_id ?? UNGROUPED);
      const value = Number(result?.num_requests ?? 0);
      if (!Number.isFinite(value)) continue;
      rows[key] = (rows[key] ?? 0) + Math.trunc(value);
    }
  }
  return rows;
}

/** Least-squares trend in units per day. Pure. Zero on fewer than 2 points. */
export function slope(points) {
  const rows = [...(points ?? [])].sort((a, b) => a[0] - b[0]);
  if (rows.length < 2) return 0;
  const base = rows[0][0];
  const xs = rows.map(([t]) => (t - base) / DAY);
  const ys = rows.map(([, v]) => Number(v));
  const n = rows.length;
  const mx = xs.reduce((a, x) => a + x, 0) / n;
  const my = ys.reduce((a, y) => a + y, 0) / n;
  const denom = xs.reduce((a, x) => a + (x - mx) ** 2, 0);
  if (denom <= 0) return 0;
  let cov = 0;
  for (let i = 0; i < n; i += 1) cov += (xs[i] - mx) * (ys[i] - my);
  return cov / denom;
}

/** [first, last, delta, fraction] over a series. Pure. */
export function growth(points) {
  const rows = [...(points ?? [])].sort((a, b) => a[0] - b[0]);
  if (!rows.length) return [0, 0, 0, 0];
  const first = rows[0][1];
  const last = rows[rows.length - 1][1];
  const delta = last - first;
  return [first, last, delta, first > 0 ? delta / first : 0];
}

/** {lineItem: {dollars, gibibyte_hours}} for storage only. Pure. */
export function storageLines(buckets) {
  const rows = {};
  for (const bucket of buckets ?? []) {
    for (const result of bucket?.results ?? []) {
      if (String(result?.quantity_unit ?? '') !== STORAGE_UNIT) continue;
      const name = String(result?.line_item ?? 'unlabelled');
      const dollars = Number(result?.amount?.value ?? 0);
      const quantity = Number(result?.quantity ?? 0);
      const entry = (rows[name] ??= { dollars: 0, [STORAGE_UNIT]: 0 });
      if (Number.isFinite(dollars)) entry.dollars += dollars;
      if (Number.isFinite(quantity)) entry[STORAGE_UNIT] += quantity;
    }
  }
  return rows;
}

/** [[id, name, bytes, idleDays]] for stores nothing searched. Pure. */
export function idleStores(stores, searches, now, minBytes = GIB) {
  const out = [];
  for (const store of stores ?? []) {
    const sid = String(store?.id ?? '');
    const size = Number(store?.usage_bytes ?? 0);
    if (!sid || !Number.isFinite(size) || size < minBytes) continue;
    if (Number((searches ?? {})[sid] ?? 0) > 0) continue;
    const last = Number(store?.last_active_at ?? 0);
    const idle = Number.isFinite(last) && last > 0
      ? Math.trunc((now - last) / DAY) : -1;
    out.push([sid, String(store?.name ?? '(unnamed)'), Math.trunc(size), idle]);
  }
  out.sort((a, b) => (b[2] - a[2]) || a[0].localeCompare(b[0]));
  return out;
}

/** Classify one project. Pure. Returns [state, detail]. */
export function verdict(bytesPoints, queryPoints, days, minGib = 1.0,
                        minGrowth = 0.25) {
  const [first, last, , fraction] = growth(bytesPoints);
  const queries = (queryPoints ?? []).reduce((a, [, v]) => a + v, 0);

  if (last < minGib * GIB) {
    return ['below-threshold',
            `${(last / GIB).toFixed(1)} GiB, under the ${minGib.toFixed(1)} GiB floor`];
  }
  if (fraction < minGrowth) {
    return ['flat',
            `${(last / GIB).toFixed(1)} GiB, ${fraction >= 0 ? '+' : ''}`
            + `${(fraction * 100).toFixed(0)}% over ${days} day(s), `
            + `${num(queries)} file search call(s)`];
  }

  const shape = `${(first / GIB).toFixed(1)} GiB -> ${(last / GIB).toFixed(1)} GiB `
    + `(${fraction >= 0 ? '+' : ''}${(fraction * 100).toFixed(0)}%)`;
  if (queries <= 0) {
    return ['bytes-growing-never-queried',
            `${shape}, 0 file search call(s) in ${days} day(s)`];
  }
  if (slope(queryPoints) <= 0) {
    return ['bytes-growing-queries-flat',
            `${shape} while file search calls are flat or falling across the same window`];
  }
  return ['bytes-and-queries-growing',
          `${shape}, ${num(queries)} file search call(s). Growth, priced correctly.`];
}

/** The repair for one verdict. Pure. Printed, never performed. */
export function repairLines(state, idle = []) {
  const rows = [...(idle ?? [])];
  if (FINDINGS.has(state)) {
    const lines = [];
    if (state === 'bytes-growing-never-queried') {
      lines.push("no query has touched this project's stores in the window. The "
        + 'bytes are being retained, not used.');
    } else {
      lines.push('the corpus is growing and the query volume is not, so you are '
        + 'paying more each month for the same amount of retrieval.');
    }
    if (rows.length) {
      lines.push('idle stores holding real bytes: ' + rows.slice(0, 8)
        .map(([sid, name, size, days]) => `${sid} ${name} ${(size / GIB).toFixed(1)} GiB`
          + (days < 0 ? '' : `, last active ${days} day(s) ago`)).join('; '));
    } else {
      lines.push('no per-store snapshot was read, so the project is named and the '
        + 'store is not. Add a project key to join the query counts against '
        + 'GET /v1/vector_stores.');
    }
    lines.push('delete the dead ones with DELETE /v1/vector_stores/{vector_store_id} '
      + 'after archiving anything you still need.');
    lines.push('set an expiration policy at creation on stores that are meant to be '
      + 'temporary, so the next prototype ages out on its own rather than being '
      + "somebody's future ticket.");
    return lines;
  }
  if (state === 'bytes-and-queries-growing') {
    return ['nothing to do. This is a corpus that is being used more, and the '
      + 'storage line is supposed to follow it.'];
  }
  return [];
}

/** Unix seconds at midnight UTC, `days` ago. Pure given `now`. */
export function windowStart(days, now = new Date()) {
  const midnight = Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate());
  return Math.floor(midnight / 1000) - days * DAY;
}

async function read(key, path, params, extra = {}) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) {
    if (Array.isArray(v)) for (const one of v) url.searchParams.append(k, String(one));
    else url.searchParams.set(k, String(v));
  }
  const r = await fetch(url, { headers: { Authorization: `Bearer ${key}`, ...extra } });
  if (r.status === 401 || r.status === 403) {
    throw new Error(`${r.status} from OpenAI: /v1/organization/* needs an `
                    + 'organization admin key, not a project key');
  }
  if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
  return r.json();
}

async function* usageBuckets(key, path, params, maxPages = 40) {
  const q = { ...params };
  for (let i = 0; i < maxPages; i += 1) {
    const page = await read(key, path, q);
    for (const bucket of page.data ?? []) yield bucket;
    if (!page.has_more || !page.next_page) return;
    q.page = page.next_page;
  }
}

async function* paged(key, path, params, maxPages = 200) {
  const q = { ...params };
  for (let i = 0; i < maxPages; i += 1) {
    const page = await read(key, path, q, BETA);
    const data = page.data ?? [];
    for (const item of data) yield item;
    if (!page.has_more || data.length === 0) return;
    q.after = page.last_id ?? data[data.length - 1]?.id;
  }
}

async function main() {
  const admin = process.env.OPENAI_ADMIN_KEY;
  if (!admin) {
    console.error('set OPENAI_ADMIN_KEY to an organization admin key; a project '
                  + 'key cannot read /v1/organization/*');
    process.exitCode = 2;
    return;
  }
  const days = Number(process.env.DAYS ?? 90);
  const minGib = Number(process.env.MIN_GIB ?? 1);
  const minGrowth = Number(process.env.MIN_GROWTH ?? 0.25);
  const common = { start_time: windowStart(days), bucket_width: '1d', limit: 31 };

  const collect = async (path, params) => {
    const out = [];
    for await (const b of usageBuckets(admin, path, params)) out.push(b);
    return out;
  };

  const bytesBuckets = await collect('/organization/usage/vector_stores',
                                     { ...common, group_by: 'project_id' });
  const searchBuckets = await collect('/organization/usage/file_search_calls',
    { ...common, group_by: ['project_id', 'vector_store_id'] });
  const costBuckets = await collect('/organization/costs',
                                    { ...common, group_by: 'line_item' });

  const byProject = byteSeries(bytesBuckets);
  const queries = querySeries(searchBuckets);
  const perStore = searchesByStore(searchBuckets);

  const stores = [];
  if (process.env.OPENAI_API_KEY) {
    for await (const st of paged(process.env.OPENAI_API_KEY, '/vector_stores',
                                 { limit: 100 })) stores.push(st);
  }

  console.log(`${days} day(s) of daily buckets across `
              + `${Object.keys(byProject).length} project(s), ${stores.length} `
              + 'store(s) in the snapshot');

  const lines = storageLines(costBuckets);
  const dollars = Object.values(lines).reduce((a, v) => a + v.dollars, 0);
  const hours = Object.values(lines).reduce((a, v) => a + v[STORAGE_UNIT], 0);
  if (Object.keys(lines).length) {
    console.log(`storage cost in the window: $${dollars.toFixed(2)} over `
                + `${hours.toFixed(1)} ${STORAGE_UNIT}`);
  } else {
    console.log(`no cost result carried quantity_unit '${STORAGE_UNIT}' in the `
                + 'window, so nothing is being billed for storage yet');
  }

  const now = Math.floor(Date.now() / 1000);
  const idle = idleStores(stores, perStore, now, Math.trunc(minGib * GIB));

  let findings = 0;
  for (const project of Object.keys(byProject).sort()) {
    const [state, detail] = verdict(byProject[project], queries[project] ?? [],
                                    days, minGib, minGrowth);
    console.log(`${state.padEnd(27)} ${project}: ${detail}`);
    for (const line of repairLines(state, FINDINGS.has(state) ? idle : [])) {
      console.log(`  repair: ${line}`);
    }
    if (FINDINGS.has(state)) findings += 1;
  }

  if (perStore[UNGROUPED]) {
    console.log(`${num(perStore[UNGROUPED])} file search call(s) came back with no `
                + 'vector_store_id and are not attributed to a store');
  }

  console.log(`${findings} finding(s)`);
  process.exitCode = findings ? 1 : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) await main();
''',
"test_intro": "The first test is the note: bytes tripling across ninety days with not one file search call has to be a finding, and the repair has to name the store rather than the project, which only works because the snapshot was joined in. The second is the case the finding must not swallow &mdash; identical byte growth alongside rising query volume, which is a corpus doing its job and is graded as such. Then the size floor, which keeps a project holding a hundred megabytes out of the report however fast it grew; the cost selection, which has to pick storage by <code>quantity_unit</code> and ignore a token line whatever it is called; the null <code>vector_store_id</code>, which must not become a store; and the slope, checked on a flat series and on a single point.",
"test_py_file": "test_openai_vector_store_storage_trend.py",
"test_py": '''from openai_vector_store_storage_trend import (GIB, UNGROUPED, byte_series,
                                                growth, idle_stores,
                                                query_series, repair_lines,
                                                searches_by_store, slope,
                                                storage_lines, verdict,
                                                window_start)

DAY = 86400
T0 = 1_800_000_000


def series(first, last, points=90, key="usage_bytes", project="proj_research"):
    """A straight line from first to last, as usage buckets."""
    out = []
    for i in range(points):
        value = first + (last - first) * i // max(points - 1, 1)
        out.append({"start_time": T0 + i * DAY,
                    "results": [{"object": "organization.usage.vector_stores.result",
                                 key: value, "project_id": project}]})
    return out


def test_bytes_tripling_with_no_queries_at_all_is_the_finding():
    # The note. Nothing is wrong with the index; the money is being spent on
    # holding it rather than on using it.
    points = byte_series(series(int(8.1 * GIB), int(31.4 * GIB)))["proj_research"]
    state, detail = verdict(points, [], 90)
    assert state == "bytes-growing-never-queried"
    assert "8.1 GiB -> 31.4 GiB" in detail and "+288%" in detail
    idle = idle_stores(
        [{"id": "vs_c3", "name": "march-demo", "usage_bytes": int(12.4 * GIB),
          "last_active_at": T0 - 148 * DAY}],
        {"vs_c3": 0}, T0)
    lines = repair_lines(state, idle)
    assert any("march-demo" in line and "12.4 GiB" in line for line in lines)
    assert any("expiration policy at creation" in line for line in lines)


def test_the_same_growth_with_rising_queries_is_not_a_finding():
    # The reading this note must not trample. A corpus that is growing because
    # it is being used more is supposed to cost more.
    points = byte_series(series(int(44 * GIB), int(61 * GIB)))["proj_research"]
    queries = query_series(series(400, 14_000, key="num_requests"))["proj_research"]
    state, detail = verdict(points, queries, 90)
    assert state == "bytes-and-queries-growing"
    assert "Growth, priced correctly" in detail
    assert repair_lines(state)[0].startswith("nothing to do")


def test_the_size_floor_comes_before_the_growth_rate():
    tiny = byte_series(series(int(0.02 * GIB), int(0.12 * GIB)))["proj_research"]
    state, detail = verdict(tiny, [], 90)
    assert state == "below-threshold"
    assert "0.1 GiB" in detail
    assert repair_lines(state) == []


def test_storage_is_selected_by_unit_and_never_by_name():
    buckets = [{"results": [
        {"line_item": "Vector store storage", "quantity_unit": "gibibyte_hours",
         "quantity": 41_288.0, "amount": {"value": 412.88, "currency": "usd"}},
        {"line_item": "gpt-5, input", "quantity_unit": "tokens",
         "quantity": 9_000_000, "amount": {"value": 18_402.11, "currency": "usd"}},
        {"line_item": "Storage, renamed next quarter",
         "quantity_unit": "gibibyte_hours", "quantity": 10.0,
         "amount": {"value": 0.1, "currency": "usd"}}]}]
    lines = storage_lines(buckets)
    assert set(lines) == {"Vector store storage", "Storage, renamed next quarter"}
    assert round(sum(v["dollars"] for v in lines.values()), 2) == 412.98
    assert storage_lines([]) == {}


def test_an_unattributed_row_never_becomes_a_store():
    buckets = [{"results": [
        {"num_requests": 12, "vector_store_id": "vs_a1", "project_id": "proj_a"},
        {"num_requests": 3, "vector_store_id": None, "project_id": None}]}]
    per_store = searches_by_store(buckets)
    assert per_store == {"vs_a1": 12, UNGROUPED: 3}
    assert byte_series([{"start_time": T0, "results": [
        {"usage_bytes": 5, "project_id": None}]}]) == {UNGROUPED: [(T0, 5)]}


def test_idle_stores_need_real_bytes_and_zero_searches():
    stores = [
        {"id": "vs_big", "name": "corpus", "usage_bytes": int(9 * GIB),
         "last_active_at": T0 - 96 * DAY},
        {"id": "vs_busy", "name": "live", "usage_bytes": int(9 * GIB),
         "last_active_at": T0},
        {"id": "vs_small", "name": "scratch", "usage_bytes": 40 * 1024 * 1024,
         "last_active_at": T0 - 400 * DAY},
        {"id": "vs_never", "name": "no-timestamp", "usage_bytes": int(2 * GIB),
         "last_active_at": None}]
    rows = idle_stores(stores, {"vs_busy": 900}, T0)
    assert [r[0] for r in rows] == ["vs_big", "vs_never"]
    assert rows[0][3] == 96
    assert rows[1][3] == -1
    assert idle_stores(None, None, T0) == []


def test_the_slope_is_zero_on_a_flat_series_and_on_one_point():
    flat = [(T0 + i * DAY, 1000) for i in range(30)]
    assert slope(flat) == 0.0
    assert slope([(T0, 5)]) == 0.0
    assert slope([]) == 0.0
    rising = [(T0 + i * DAY, 100 * i) for i in range(10)]
    assert round(slope(rising), 3) == 100.0
    assert growth([]) == (0, 0, 0, 0.0)
    assert growth([(T0, 0), (T0 + DAY, 50)])[3] == 0.0


def test_the_window_starts_at_midnight_utc():
    import datetime as dt
    now = dt.datetime(2026, 8, 31, 17, 45, 12, tzinfo=dt.timezone.utc)
    assert window_start(90, now) == int(
        dt.datetime(2026, 6, 2, tzinfo=dt.timezone.utc).timestamp())
''',
"test_js_file": "openai-vector-store-storage-trend.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { UNGROUPED, byteSeries, growth, idleStores, querySeries, repairLines,
         searchesByStore, slope, storageLines, verdict, windowStart }
  from './openai-vector-store-storage-trend.mjs';

const GIB = 1073741824;
const DAY = 86400;
const T0 = 1800000000;

const series = (first, last, points = 90, key = 'usage_bytes',
                project = 'proj_research') => {
  const out = [];
  for (let i = 0; i < points; i += 1) {
    const value = first + Math.trunc((last - first) * i / Math.max(points - 1, 1));
    out.push({ start_time: T0 + i * DAY,
               results: [{ [key]: value, project_id: project }] });
  }
  return out;
};

test('bytes tripling with no queries at all is the finding', () => {
  const points = byteSeries(series(Math.trunc(8.1 * GIB),
                                   Math.trunc(31.4 * GIB))).proj_research;
  const [state, detail] = verdict(points, [], 90);
  assert.equal(state, 'bytes-growing-never-queried');
  assert.match(detail, /8\\.1 GiB -> 31\\.4 GiB/);
  assert.match(detail, /\\+288%/);
  const idle = idleStores(
    [{ id: 'vs_c3', name: 'march-demo', usage_bytes: Math.trunc(12.4 * GIB),
       last_active_at: T0 - 148 * DAY }], { vs_c3: 0 }, T0);
  const lines = repairLines(state, idle);
  assert.ok(lines.some((l) => l.includes('march-demo') && l.includes('12.4 GiB')));
  assert.ok(lines.some((l) => l.includes('expiration policy at creation')));
});

test('the same growth with rising queries is not a finding', () => {
  const points = byteSeries(series(44 * GIB, 61 * GIB)).proj_research;
  const queries = querySeries(series(400, 14000, 90, 'num_requests')).proj_research;
  const [state, detail] = verdict(points, queries, 90);
  assert.equal(state, 'bytes-and-queries-growing');
  assert.match(detail, /Growth, priced correctly/);
  assert.ok(repairLines(state)[0].startsWith('nothing to do'));
});

test('the size floor comes before the growth rate', () => {
  const tiny = byteSeries(series(Math.trunc(0.02 * GIB),
                                 Math.trunc(0.12 * GIB))).proj_research;
  const [state, detail] = verdict(tiny, [], 90);
  assert.equal(state, 'below-threshold');
  assert.match(detail, /0\\.1 GiB/);
  assert.deepEqual(repairLines(state), []);
});

test('storage is selected by unit and never by name', () => {
  const buckets = [{ results: [
    { line_item: 'Vector store storage', quantity_unit: 'gibibyte_hours',
      quantity: 41288, amount: { value: 412.88, currency: 'usd' } },
    { line_item: 'gpt-5, input', quantity_unit: 'tokens', quantity: 9000000,
      amount: { value: 18402.11, currency: 'usd' } },
    { line_item: 'Storage, renamed next quarter', quantity_unit: 'gibibyte_hours',
      quantity: 10, amount: { value: 0.1, currency: 'usd' } }] }];
  const lines = storageLines(buckets);
  assert.deepEqual(Object.keys(lines).sort(),
                   ['Storage, renamed next quarter', 'Vector store storage']);
  const total = Object.values(lines).reduce((a, v) => a + v.dollars, 0);
  assert.equal(Math.round(total * 100) / 100, 412.98);
  assert.deepEqual(storageLines([]), {});
});

test('an unattributed row never becomes a store', () => {
  const buckets = [{ results: [
    { num_requests: 12, vector_store_id: 'vs_a1', project_id: 'proj_a' },
    { num_requests: 3, vector_store_id: null, project_id: null }] }];
  assert.deepEqual(searchesByStore(buckets), { vs_a1: 12, [UNGROUPED]: 3 });
  assert.deepEqual(byteSeries([{ start_time: T0,
                                 results: [{ usage_bytes: 5, project_id: null }] }]),
                   { [UNGROUPED]: [[T0, 5]] });
});

test('idle stores need real bytes and zero searches', () => {
  const stores = [
    { id: 'vs_big', name: 'corpus', usage_bytes: 9 * GIB,
      last_active_at: T0 - 96 * DAY },
    { id: 'vs_busy', name: 'live', usage_bytes: 9 * GIB, last_active_at: T0 },
    { id: 'vs_small', name: 'scratch', usage_bytes: 40 * 1024 * 1024,
      last_active_at: T0 - 400 * DAY },
    { id: 'vs_never', name: 'no-timestamp', usage_bytes: 2 * GIB,
      last_active_at: null }];
  const rows = idleStores(stores, { vs_busy: 900 }, T0);
  assert.deepEqual(rows.map((r) => r[0]), ['vs_big', 'vs_never']);
  assert.equal(rows[0][3], 96);
  assert.equal(rows[1][3], -1);
  assert.deepEqual(idleStores(null, null, T0), []);
});

test('the slope is zero on a flat series and on one point', () => {
  const flat = [];
  for (let i = 0; i < 30; i += 1) flat.push([T0 + i * DAY, 1000]);
  assert.equal(slope(flat), 0);
  assert.equal(slope([[T0, 5]]), 0);
  assert.equal(slope([]), 0);
  const rising = [];
  for (let i = 0; i < 10; i += 1) rising.push([T0 + i * DAY, 100 * i]);
  assert.equal(Math.round(slope(rising) * 1000) / 1000, 100);
  assert.deepEqual(growth([]), [0, 0, 0, 0]);
  assert.equal(growth([[T0, 0], [T0 + DAY, 50]])[3], 0);
});

test('the window starts at midnight utc', () => {
  assert.equal(windowStart(90, new Date('2026-08-31T17:45:12Z')),
               Date.UTC(2026, 5, 2) / 1000);
});
''',
"faq": [
 ("Can I get a byte trend for one vector store rather than a whole project?",
  "Not from the usage API. The vector stores usage endpoint accepts exactly one grouping, project_id, so there is no per-store byte series and asking harder will not produce one. What you can group per store is the query volume: the file search calls endpoint accepts vector_store_id and returns num_requests against it. So the trend is a project-level reading and the culprit is identified by joining those per-store query counts against the current snapshot from GET /v1/vector_stores, which needs a project key. The script says out loud when it ran without one, rather than reporting an empty store list as though there were no idle stores."),
 ("Why match on quantity_unit instead of the line item name?",
  "Because names get relabelled and units do not. quantity_unit is an enumerated field on the cost result and gibibyte_hours appears on the storage lines specifically. A check written against a display string keeps working right up until somebody in the billing team renames a product, at which point it starts reporting zero dollars of storage cost, which looks exactly like good news. Matching the unit also states the billing model in the output: gibibyte-hours is bytes multiplied by time, which is the whole reason this line behaves differently from every other one."),
 ("How is this different from reconciling the line items on the bill?",
  "Different question and different shape. The line-item note asks whether your cost dashboard renders the whole invoice, and it answers by subtracting what you cover from what you were charged in one window. This one takes a single unit and asks whether it is trending, over ninety days, against the thing that is supposed to justify it. A storage line can be fully covered by a dashboard, perfectly reconciled, and still be the wrong number, because nothing about the reconciliation asks whether anybody searched the bytes."),
 ("The bytes are growing. Is that not just what a growing product does?",
  "Frequently, and the script grades that separately for exactly that reason. Bytes climbing alongside a climbing query count is a corpus being used more, the storage line is supposed to follow it, and reporting it as waste is how a cost report gets ignored. The finding is growth without use: bytes rising while file search calls are flat, falling, or zero. Two of the five states this script emits exist purely to keep normal growth out of the finding column."),
 ("Why ninety days, and why does the script page the usage endpoints?",
  "Ninety days because a slope needs enough points to be a slope rather than a coincidence, and a monthly billing cycle means anything shorter than two of them cannot show you a trend that survives a month boundary. The paging is not optional: the usage endpoints cap limit at 31 buckets when bucket_width is 1d, so a request for ninety days returns thirty-one of them and a next_page cursor. A script that reads the first response and stops computes a real slope over a third of the window and reports it as though it covered all of it."),
],
"related": [REL_EXPIRY, REL_MODALITY, REL_OUTPUT],
"citations": [CITE_USAGE, CITE_VS, CITE_OPENAPI, CITE_PRICING],
},
]
