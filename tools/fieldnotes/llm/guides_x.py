#!/usr/bin/env python3
"""/llm/ field notes, batch X — the writing.

Four server-side objects that nobody owns once the upload or the completion
call returns. That is the premise, and the hazard is that "stuff accumulated"
is a single shape which could be told four times with the nouns swapped. So
each of these four grades a different *kind* of answer, and the scripts were
written to reach that answer rather than to re-read one listing with four
thresholds.

`files-accumulating-against-storage-quota` owns a **total against a ceiling**.
It sums `bytes` (OpenAI) and `size_bytes` (Anthropic) across every page of the
file store and compares the sum to a documented storage limit. Two things make
it its own note rather than a variant of the published
`vector-store-storage-cost-creeping`: the object is different, and so is the
failure. That note reads `usage_bytes` on vector stores, trends it across
ninety days against retrieval volume, and prices the slope from a
`gibibyte_hours` line item — a cost curve, on a meter, with money at the end of
it. This one reads the file store, where Anthropic states outright that Files
API operations are free, and the thing at the end of it is not an invoice line
but a hard failure on the next upload. A slope tells you what you are spending.
A share of a ceiling tells you how many uploads you have left. And the ceiling
is the part no endpoint will give you on either provider: no quota, no consumed
figure, no percentage. The limit is a documented constant, only the total is
measured, and the script prints those in separate columns for exactly that
reason.

`orphaned-assistants-purpose-files` owns a **set difference**. Not a total, not
a date: one whole purpose class whose owning API no longer exists, minus the
file ids a surviving vector store still holds. It sits next to the just-shipped
`assistants-api-already-shut-down` and it is not the same reading. That note
probes whether `/v1/assistants` still answers for your organization and its
finding is a status code. This one starts where that one ends: the assistants,
threads and runs are gone, the files are not, and only a subtraction separates
the ones that still have an owner from the ones that do not. One correction
made while writing, and it changed the note. The migration guide says nothing
whatsoever about storage — it covers assistants, threads and runs and never
uses the words file, vector store or purpose. So "files carry over" is an
inference, not a quotation, and the script says so. What *is* documented is
narrower and enough: `assistants` and `assistants_output` are still valid
values of `purpose` on the File object, vector stores are a live non-beta
resource, and deleting a file removes it from every vector store it is in. The
weakness of a subtraction is the set you subtract, which is why a store whose
file listing could not be read downgrades every orphan verdict in the run
rather than being skipped.

`expired-files-still-referenced` owns a **date on an id you already hold**. It
is Anthropic-only and it is the only note in the batch whose finding is that an
object which answers is nonetheless useless. `expires_in_seconds` is set once at
upload and cannot be changed; after the moment it names, the content stops being
retrievable and the storage is released, but the metadata remains readable for
up to thirty days and the file keeps appearing in list responses. So the obvious
existence check returns a stale yes. The script asks about the ids your
application holds, up to a hundred per request, and grades the date rather than
the status code — including the case where the date is not returned at all,
because one beta header removes `expires_at` from the response and takes the
whole check with it.

`stored-responses-accumulating` owns **retention and volume on state you never
chose to keep**, and it is built around a limitation rather than around an
endpoint. Storing a response is the default, conversations are retained until
deleted, and neither `/v1/responses` nor `/v1/conversations` has a list
endpoint — so there is no query that answers "what am I holding". The script
probes ids the caller supplies and says on every run that its coverage is your
records and not your account. Read it against the published
`previous-response-id-chain-broken`, which uses one of the same GETs and means
something else entirely: that note walks `previous_response_id` upward and
grades whether a thread will still resolve tomorrow, so for it thirty days is a
deadline after which things vanish. Here it is a **floor**: the data-retention
page says stored response data is kept *for at least* thirty days, which is the
opposite reading and the one a privacy question needs. This note never follows
a parent, and there is a test that fails if `previous_response_id` ever appears
in the row it builds.

Read only, and stricter than the section baseline: every request in all four
scripts is a GET. Nothing is deleted to reclaim quota — the deletions are
printed for a human, because a file deleted by an audit script cannot be
recovered by anyone. And no script here ever fetches file *content*: the
findings are made of sizes, purposes, dates and ids, all of which are metadata,
and a script that downloads a customer's uploaded PDF in order to report that
it is old has misunderstood the assignment.
"""

CITE_OAI_FILES = ("Files — OpenAI API reference",
                  "https://developers.openai.com/api/docs/api-reference/files")
CITE_OAI_DATA = ("Your data, including the retention table",
                 "https://developers.openai.com/api/docs/guides/your-data")
CITE_OAI_MIGRATE = ("Assistants API migration guide — OpenAI platform docs",
                    "https://developers.openai.com/api/docs/assistants/migration")
CITE_OAI_DEPRECATIONS = ("Deprecations — OpenAI platform docs",
                         "https://developers.openai.com/api/docs/deprecations")
CITE_OAI_VS_FILES = ("Vector store files — OpenAI API reference",
                     "https://developers.openai.com/api/docs/api-reference/vector-stores")
CITE_OAI_STATE = ("Conversation state — OpenAI platform docs",
                  "https://developers.openai.com/api/docs/guides/conversation-state")
CITE_OAI_RESP = ("Responses — OpenAI API reference",
                 "https://developers.openai.com/api/docs/api-reference/responses")
CITE_OAI_CONV = ("Conversations — OpenAI API reference",
                 "https://developers.openai.com/api/docs/api-reference/conversations")

CITE_ANT_FILES = ("Files API — Claude platform docs",
                  "https://platform.claude.com/docs/en/build-with-claude/files")
CITE_ANT_LIST = ("List Files — Claude API reference",
                 "https://platform.claude.com/docs/en/api/files/list")
CITE_ANT_UPLOAD = ("Upload a File, including expires_in_seconds",
                   "https://platform.claude.com/docs/en/api/files/upload")
CITE_ANT_DELETE = ("Delete a File — Claude API reference",
                   "https://platform.claude.com/docs/en/api/files/delete")

REL_QUOTA = ("/llm/files-accumulating-against-storage-quota/",
             "The same store read as one number against a ceiling")
REL_ORPHAN = ("/llm/orphaned-assistants-purpose-files/",
              "One purpose class inside that total, owned by nothing at all")
REL_EXPFILE = ("/llm/expired-files-still-referenced/",
               "The files inside that total that are already unusable")
REL_STORED = ("/llm/stored-responses-accumulating/",
              "The other server-side store nobody sweeps, and cannot list")
REL_VSBYTES = ("/llm/vector-store-storage-cost-creeping/",
               "The other retained bytes, on a different object and a real meter")
REL_VSEXPIRY = ("/llm/vector-store-expired-or-expiring/",
                "The same clock set on a whole index instead of on one file")
REL_ASSTSHUT = ("/llm/assistants-api-already-shut-down/",
                "Whether the endpoint that owned these files still answers you")
REL_VSATTACH = ("/llm/vector-store-file-attach-failed/",
                "A file that is in a store and still missing from every search")
REL_BETAHDR = ("/llm/invalid-beta-header-value/",
               "The other reading a beta header quietly changes underneath you")
REL_CHAIN = ("/llm/previous-response-id-chain-broken/",
             "The same GET read for whether a thread still resolves tomorrow")
REL_ZDR = ("/llm/zero-data-retention-not-configured/",
           "The retention posture that was configured, versus what is held")

GUIDES = [
{
"slug": "files-accumulating-against-storage-quota",
"title": "Files pile up against a storage ceiling nothing reports",
"description": "No endpoint returns your file quota. Sum bytes across every page of /v1/files, group by purpose, and grade the total against the documented limit.",
"h1": "Files pile up against a storage ceiling nothing reports",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["openai 2.5 tb project file storage limit",
             "anthropic files api 1 tb storage limit exceeded",
             "sum openai file bytes across pages quota",
             "openai files expires_after anchor created_at",
             "how much file storage am i using openai"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Needs OPENAI_API_KEY, a project key set to Read Only, and/or ANTHROPIC_API_KEY, a key with access to the workspace whose files you want to sum. Every request is a GET of the file listing, and no file content is ever fetched.",
"lead": "The batch pipeline has run every night for two years and tonight it stops on the first step, uploading the input file, with an error nobody has seen before. Nothing was deployed. The key works, because the same key just listed a thousand files without complaint. Reads are fine. Retrieval is fine. Inference is fine. The only thing that is broken is writing, and it is broken because a number you have never once looked at reached a ceiling you have never once been shown.",
"short_answer": """<p>Add it up yourself, because nothing will add it up for you. There is <strong>no endpoint on either provider that reports a storage quota, a consumed figure or a remaining one</strong>. The listing is the only surface that knows anything about your files, so the script pages through all of it and sums the size field: <code>bytes</code> on OpenAI's file object, <code>size_bytes</code> on Anthropic's.</p>
<p>The ceilings are different numbers on different containers and that matters. OpenAI documents <strong>2.5 TB per project</strong>, 512 MB per file, and says in as many words that there is <em>no organization-wide storage limit</em>. Anthropic documents <strong>1 TB per organization</strong> and 500 MB per file, and returns HTTP 400 with a storage-limit message when you cross it. So on one provider you audit per project and on the other per organization, and a number that looks safe under one rule can be over the line under the other.</p>
<p>Then grade four things, because a file store fills up in four ways. The <strong>total</strong>, as a share of the documented ceiling. The <strong>concentration</strong>, from grouping OpenAI's files by <code>purpose</code>, because one class is almost always most of the bytes and that is the class to sweep. The <strong>outliers</strong>, individual files near the per-file cap, which is a second and entirely separate ceiling. And the <strong>expiry coverage</strong>: files with no <code>expires_at</code> older than your retention window, which is the population that can only ever grow.</p>
<p>Keep the measured half and the documented half apart on every line. The total is measured. The ceiling is a number out of a docs page that no request can confirm, and it can be renegotiated for one account or republished for everyone without anything the script reads changing at all. Printing a percentage without saying which half was measured is how an audit becomes a rumour.</p>
<p>The repair is a deletion and the script never performs one. Deleted files cannot be recovered, the metadata gives you no way to tell a dead file from a load-bearing one, and on OpenAI deleting a file also removes it from every vector store it is attached to.</p>""",
"problem": """<p>Uploading a file is the easy half of a two-part transaction whose second half nobody wrote. Batch input files, batch output and error files, fine-tuning corpora, fine-tune result files, images for vision, documents for retrieval: every one of them is created by a pipeline that had a reason to create it, and none of them is deleted by anything, because at the moment the pipeline finishes nobody has decided the file is finished. It might be needed for a re-run. It might be needed for an audit. It costs nothing visible to keep.</p>
<p>So the store grows monotonically, and it grows in a place with no gauge on it. There is no dashboard number, no header, no field on any response that says how full it is. OpenAI's listing endpoint defaults to returning ten thousand objects per page and never once suggests that this is a lot. The first feedback the platform gives you is a hard failure, and it arrives on the write path, which means it arrives inside a production pipeline rather than inside an audit.</p>
<p>That asymmetry is the whole reason this is worth a scheduled script. Everything that reads keeps working perfectly at 100% of quota. Retrieval works, inference works, listing works, your monitoring is green. Only the next upload fails, and it fails at whatever hour your batch job happens to run.</p>
<p>The second ceiling makes it worse by being invisible in the total. A per-file size cap applies independently of the store-wide limit, so a single oversized upload fails on a store that is 3% full, and the error looks close enough to the quota error that the first hour of the investigation goes into the wrong number. An audit that only reports a total will confidently tell you there is plenty of room while the actual failure is one file that is too big on its own.</p>""",
"why": """<p><strong>The ceiling is not readable and the script has to be honest about that.</strong> The total is measured: it is the sum of a field, over every page, and it is exactly as right as the pagination. The limit is a documented constant that came out of a docs page and cannot be confirmed by any request. Those are different kinds of fact, they age differently, and a percentage computed from one of each inherits the weaker one. So the output labels them, the limit is a command-line argument with a documented default rather than a hardcoded truth, and a run against a changed platform reports a wrong percentage loudly instead of a right-looking one quietly.</p>
<p><strong>The two providers put the ceiling on different containers.</strong> OpenAI's 2.5 TB is per project and the docs state there is no organization-wide limit at all, so ten projects are ten separate ceilings and a project key sees exactly one of them. Anthropic's 1 TB is per organization, and the Files API is workspace-scoped, so summing one workspace tells you a fraction of the number that actually governs you. The script prints which container it just measured, and names the stores it did not look at, because an unaudited project is not an empty one.</p>
<p><strong>Pagination is the finding, not a detail of it.</strong> An audit that reads the first page and reports a total is not wrong by a little. On a store big enough to matter it is wrong by an order of magnitude and it is wrong in the reassuring direction. So the script pages to the end on both providers, using each one's own cursor &mdash; <code>after</code> on OpenAI, <code>next_page</code> handed back as <code>page</code> on Anthropic &mdash; and prints how many pages it read. If it stops on a page limit it says the number is a floor and not a total, because a floor is still useful and a total that is secretly a floor is not.</p>
<p><strong>Grouping by <code>purpose</code> is what turns a number into an action.</strong> "You are at 71% of quota" is not something anybody can act on. "You are at 71%, and 64 points of that is <code>batch_output</code> from jobs that finished more than 90 days ago" is a sweep somebody can write this afternoon. The classes are not equally deletable, either, and one of them already deletes itself: OpenAI documents that files with <code>purpose=batch</code> expire after 30 days by default while everything else persists until manually deleted. A store dominated by <code>batch</code> will drain on its own. A store dominated by <code>batch_output</code> will not.</p>
<p><strong>Two ceilings, and only one of them is a total.</strong> The per-file cap is not a fraction of the quota, it is its own limit, and a file approaching it fails an upload the store-level number says is fine. The script grades them separately and reports both, because the two errors look similar enough in production that the wrong one gets investigated first.</p>
<p><strong>This is a ceiling, not a cost curve, and the difference is which note you are reading.</strong> There is a published note about vector store bytes: a stock billed by the hour, trended over ninety days against retrieval volume, priced from a <code>gibibyte_hours</code> line item. Its finding is money and its shape is a slope. This one reads a different object &mdash; Anthropic states that Files API operations are free &mdash; and its finding is not on the invoice at all. It is how many uploads you have left before a pipeline stops. Both are about bytes nobody deleted, and that is the whole of the resemblance.</p>""",
"steps": [
 {"h": "Give it whichever credentials you have, and know what each one sees",
  "body": """<p><code>OPENAI_API_KEY</code>, a project key set to Read Only, reads <code>GET /v1/files</code> for <em>one project</em>, which is the container the 2.5 TB applies to. <code>ANTHROPIC_API_KEY</code> reads the Anthropic listing for one workspace, which is a slice of the organization the 1 TB applies to. Set either, or both. The script audits what it was given and says which stores it did not look at.</p>"""},
 {"h": "Page to the end and count the pages",
  "body": """<p>OpenAI pages on <code>after</code>, carrying the last id of each page forward, and its list response marks <code>has_more</code> as a required field. Anthropic pages by handing the response's <code>next_page</code> back as the <code>page</code> parameter until it comes back null. <code>--max-pages</code> stops a runaway, and stopping there changes the wording of the result from a total to a floor.</p>"""},
 {"h": "Declare the ceiling you are actually working against",
  "body": """<p><code>--quota-bytes</code> overrides the documented default. Use it when your account has a negotiated limit &mdash; OpenAI's docs invite you to ask for one &mdash; and use it when the platform republishes the number. The default is printed on every run with the word documented next to it so nobody mistakes it for something the API said.</p>"""},
 {"h": "Read the concentration before the total",
  "body": """<p>The per-<code>purpose</code> table is the actionable half. It names the class holding the bytes, and those classes behave differently: <code>batch</code> inputs already expire after 30 days by default, while <code>batch_output</code>, <code>fine-tune-results</code> and <code>assistants</code> persist until somebody deletes them. Anthropic's file object has no purpose concept at all, so that table is one row there and the script says so rather than fabricating a breakdown.</p>"""},
 {"h": "Take the printed repair and run it yourself",
  "body": """<p>Two lines come out: the deletion command for each candidate, and the preventive fix, which is an expiry set at upload time so the population stops being unbounded. Neither is executed. A deleted file is not recoverable, nothing in the metadata can tell an audit which files matter, and on OpenAI the deletion also detaches the file from every vector store holding it.</p>"""},
],
"verify": """<p>Set an expiry on the next thing your pipeline uploads and re-run in a week. The total will not have moved much, and that is fine &mdash; the number that should move is the share of files carrying no expiry, because that one describes the trajectory rather than the position. Then delete one purpose class you have confirmed is dead and re-run again: the total steps down, the concentration table reorders, and the percentage against the ceiling becomes a number somebody is willing to look at monthly.</p>
<pre><code class="language-bash">python3 file_store_quota_audit.py --provider openai --stale-days 90
# openai    4 page(s) read, 8,412 file(s), 1.5 TiB
#   measured: the sum of bytes over every page of GET /v1/files
#   documented: a ceiling of 2.5 TB per project, which no endpoint reports
# quota-warning        66.9% of the documented ceiling is in use, with about
#                      771.0 GiB of headroom before uploads start to fail
#   repair: sweep the purpose class named below, then set an expiry at upload
#           so the next two thirds take longer to arrive than the last did.
# purpose-dominates    batch_output is 64.1% of the store, 5,904 file(s)
#   repair: delete the ones whose job is finished and read, one at a time,
#           with DELETE /v1/files/{file_id}. Nothing here does that for you,
#           a deleted file cannot be recovered, and on OpenAI the deletion
#           also removes the file from every vector store holding it.
# file-near-cap        2 file(s) above 80% of the per-file cap
#                      file-9f1  464.6 MiB  fine-tune
#                      file-c07  441.2 MiB  fine-tune
#   repair: a second ceiling, unrelated to the total. Split these at source
#           rather than making room for them.
# no-expiry-policy     8,398 of 8,412 file(s) have no expires_at, and 6,110 of
#                      those are older than 90 day(s)
#   repair: upload with an expiry so this population stops being unbounded:
#           expires_after with an anchor of created_at on OpenAI (3600 to
#           2592000 seconds), expires_in_seconds on Anthropic.
# not-audited          ANTHROPIC_API_KEY not set, so that store was not
#                      audited. An unaudited store is not an empty one
# 1 store(s) audited, 4 finding(s)</code></pre>""",
"code_intro": "One paged GET per provider and nine pure functions. <code>epoch</code>, which turns OpenAI's integer timestamps and Anthropic's RFC 3339 strings into one clock so the age readings work on both; <code>file_row</code>, which normalises <code>bytes</code> and <code>size_bytes</code> into one shape and refuses to invent a <code>purpose</code> for a provider that has none; <code>totals</code> and <code>by_purpose</code>, the two folds; <code>human</code>, binary units in one place rather than at every call site; <code>grade_total</code>, which takes the ceiling as an argument because it is documented rather than measured; <code>grade_concentration</code>, which finds the class worth sweeping; <code>grade_outliers</code>, which grades the second and separate per-file ceiling; and <code>grade_expiry</code>, the only one of the four that describes the future.",
"py_file": "file_store_quota_audit.py",
"py": '''"""Sum every page of the file store and grade it against a documented ceiling.

Read only. GET /v1/files and nothing else, on either provider. Nothing is
uploaded, nothing is deleted, and no file content is ever fetched: every
finding here is made of sizes, purposes, dates and ids.

Neither provider exposes the quota. There is no endpoint that returns a limit,
a consumed figure or a remaining one, so the ceiling below is a documented
constant that no request can confirm while the total is measured by summing a
field over every page. Those are different kinds of fact and the output keeps
them in different columns.

The ceilings also sit on different containers. OpenAI documents 2.5 TB per
project and no organization-wide limit at all; Anthropic documents 1 TB per
organization while its Files API is workspace scoped. So a single run measures
one project or one workspace, and says which.
"""
import argparse
import calendar
import logging
import os
import re
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("file_store_quota_audit")

ENDPOINTS = {"openai": "https://api.openai.com/v1/files",
             "anthropic": "https://api.anthropic.com/v1/files"}

# Documented ceilings, not readable ones. Overridable with --quota-bytes,
# because a negotiated limit and a republished docs page look identical here.
DOC_QUOTA_BYTES = {"openai": 2_500_000_000_000, "anthropic": 1_000_000_000_000}
DOC_QUOTA_LABEL = {"openai": "2.5 TB per project",
                   "anthropic": "1 TB per organization"}
DOC_FILE_CAP_BYTES = {"openai": 512_000_000, "anthropic": 500_000_000}
SIZE_FIELD = {"openai": "bytes", "anthropic": "size_bytes"}
KEY_ENV = {"openai": "OPENAI_API_KEY", "anthropic": "ANTHROPIC_API_KEY"}

FINDINGS = ("quota-critical", "quota-warning", "purpose-dominates",
            "file-near-cap", "no-expiry-policy")

_RFC3339 = re.compile(r"^(\\d{4})-(\\d{2})-(\\d{2})[Tt ](\\d{2}):(\\d{2}):(\\d{2})"
                      r"(?:\\.\\d+)?(Z|z|[+-]\\d{2}:?\\d{2})?$")


def epoch(value):
    """Seconds since the epoch from either provider's shape. Pure.

    OpenAI returns integer Unix seconds. Anthropic returns RFC 3339 strings.
    Returns 0 for anything unparseable, and 0 means unknown everywhere it is
    read rather than meaning 1970.
    """
    if value is None or value == "" or isinstance(value, bool):
        return 0
    if isinstance(value, (int, float)):
        try:
            return max(0, int(value))
        except (TypeError, ValueError, OverflowError):
            return 0
    m = _RFC3339.match(str(value).strip())
    if not m:
        return 0
    try:
        base = calendar.timegm(tuple(int(g) for g in m.groups()[:6]) + (0, 0, 0))
    except (TypeError, ValueError):
        return 0
    off = m.group(7)
    if off and off not in ("Z", "z"):
        digits = off[1:].replace(":", "")
        shift = int(digits[:2]) * 3600 + int(digits[2:4]) * 60
        base -= shift if off[0] == "+" else -shift
    return max(0, base)


def file_row(body, provider):
    """One file object, normalised. Pure. Two providers, one shape.

    OpenAI calls the size `bytes` and carries a `purpose`; Anthropic calls it
    `size_bytes` and has no purpose concept at all, so this refuses to invent
    one. `expires_at` is optional rather than nullable on OpenAI, meaning the
    key is simply absent on a file with no expiry, and on Anthropic it is
    absent whenever the files-api-2025-04-14 beta header was sent.
    """
    body = body if isinstance(body, dict) else {}
    try:
        size = int(body.get(SIZE_FIELD.get(provider, "bytes")))
    except (TypeError, ValueError):
        size = 0
    return {"id": str(body.get("id") or ""),
            "filename": str(body.get("filename") or ""),
            "size": max(0, size),
            "purpose": str(body.get("purpose") or "unclassified"),
            "created_at": epoch(body.get("created_at")),
            "expires_at": epoch(body.get("expires_at")) or None,
            "expiry_reported": "expires_at" in body}


def human(size):
    """Binary units, one decimal. Pure. Used everywhere rather than inlined."""
    try:
        n = float(size)
    except (TypeError, ValueError):
        return "0 B"
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if abs(n) < 1024 or unit == "TiB":
            return "%d B" % int(n) if unit == "B" else "%.1f %s" % (n, unit)
        n /= 1024.0
    return "%.1f TiB" % n


def totals(rows):
    """Count and summed bytes. Pure."""
    rows = rows or []
    return {"count": len(rows), "bytes": sum(int(r.get("size") or 0) for r in rows)}


def by_purpose(rows):
    """Per-purpose count and bytes, largest first. Pure."""
    acc = {}
    for row in rows or []:
        key = str(row.get("purpose") or "unclassified")
        cur = acc.setdefault(key, {"count": 0, "bytes": 0})
        cur["count"] += 1
        cur["bytes"] += int(row.get("size") or 0)
    return sorted(([k, v["count"], v["bytes"]] for k, v in acc.items()),
                  key=lambda item: (-item[2], item[0]))


def grade_total(total_bytes, quota_bytes, warn_share=0.60, critical_share=0.85):
    """Share of a documented ceiling. Pure. The ceiling is an argument.

    An argument rather than a constant because the number came out of a docs
    page: it can be renegotiated for one account and republished for everyone,
    and neither event is visible from any GET.
    """
    try:
        quota, used = int(quota_bytes), int(total_bytes)
    except (TypeError, ValueError):
        quota, used = 0, 0
    if quota <= 0:
        return ("quota-unknown", "no usable ceiling was supplied, so the total "
                                 "is a number without a denominator")
    share = used / float(quota)
    detail = ("%.1f%% of the documented ceiling is in use, with about %s of "
              "headroom before uploads start to fail"
              % (share * 100, human(max(0, quota - used))))
    if share >= critical_share:
        return ("quota-critical", detail)
    if share >= warn_share:
        return ("quota-warning", detail)
    return ("quota-headroom",
            "%.1f%% of the documented ceiling is in use, %s of headroom"
            % (share * 100, human(max(0, quota - used))))


def grade_concentration(purposes, total_bytes, share=0.40):
    """The purpose class worth sweeping first. Pure."""
    try:
        total = int(total_bytes)
    except (TypeError, ValueError):
        total = 0
    if not purposes or total <= 0:
        return ("purpose-even", "nothing to concentrate: the store is empty or "
                                "carries no size information")
    name, count, size = purposes[0]
    got = size / float(total)
    if got < share:
        return ("purpose-even",
                "no single purpose holds more than %.0f%% of the store; the "
                "largest is %s at %.1f%%" % (share * 100, name, got * 100))
    return ("purpose-dominates",
            "%s is %.1f%% of the store, %d file(s)" % (name, got * 100, count))


def grade_outliers(rows, cap_bytes, warn_share=0.80):
    """The second ceiling, per file and not a fraction of the first. Pure."""
    try:
        cap = int(cap_bytes)
    except (TypeError, ValueError):
        cap = 0
    if cap <= 0:
        return ("cap-unknown", "no per-file cap was supplied", [])
    floor = cap * warn_share
    big = sorted((r for r in rows or [] if int(r.get("size") or 0) >= floor),
                 key=lambda r: -int(r.get("size") or 0))
    if not big:
        return ("file-sizes-fine",
                "no file is within %.0f%% of the per-file cap"
                % (warn_share * 100), [])
    return ("file-near-cap",
            "%d file(s) above %.0f%% of the per-file cap"
            % (len(big), warn_share * 100), big)


def grade_expiry(rows, now, stale_days):
    """The only reading here that describes the future. Pure."""
    rows = rows or []
    if not rows:
        return ("expiry-none", "the store is empty")
    unexpiring = [r for r in rows if not r.get("expires_at")]
    if not unexpiring:
        return ("expiry-covered",
                "every file carries an expires_at, so this store has a "
                "lifecycle rather than a trajectory")
    cutoff = int(now) - int(stale_days) * 86400
    stale = [r for r in unexpiring
             if r.get("created_at") and int(r["created_at"]) < cutoff]
    return ("no-expiry-policy",
            "%d of %d file(s) have no expires_at, and %d of those are older "
            "than %d day(s)"
            % (len(unexpiring), len(rows), len(stale), int(stale_days)))


def repair_lines(state):
    """The repair for one verdict. Pure. Printed, never performed."""
    if state in ("quota-critical", "quota-warning"):
        return ["sweep the purpose class named below, then set an expiry at "
                "upload so the next two thirds take longer to arrive than the "
                "last did."]
    if state == "purpose-dominates":
        return ["delete the ones whose job is finished and read, one at a "
                "time, with DELETE /v1/files/{file_id}. Nothing here does that "
                "for you, a deleted file cannot be recovered, and on OpenAI "
                "the deletion also removes the file from every vector store "
                "holding it."]
    if state == "file-near-cap":
        return ["a second ceiling, unrelated to the total. Split these at "
                "source rather than making room for them."]
    if state == "no-expiry-policy":
        return ["upload with an expiry so this population stops being "
                "unbounded: expires_after with an anchor of created_at on "
                "OpenAI (3600 to 2592000 seconds), expires_in_seconds on "
                "Anthropic (3600 to 7776000).",
                "for what is already there, confirm by hand and then delete. "
                "Nothing in the metadata can tell an audit which files matter."]
    if state == "quota-unknown":
        return ["pass --quota-bytes. Without a denominator this run is an "
                "inventory rather than an audit."]
    return []


def fetch_openai(key, max_pages, timeout=30):
    """Page GET /v1/files on `after`. Returns (rows, pages, complete)."""
    rows, cursor, pages = [], None, 0
    while pages < max_pages:
        params = {"limit": 10000, "order": "asc"}
        if cursor:
            params["after"] = cursor
        try:
            r = requests.get(ENDPOINTS["openai"], params=params,
                             headers={"Authorization": "Bearer " + key},
                             timeout=timeout)
        except requests.RequestException as exc:
            log.error("openai listing failed: %s", exc)
            return (rows, pages, False)
        if r.status_code != 200:
            log.error("openai listing returned HTTP %s", r.status_code)
            return (rows, pages, False)
        body = r.json() if r.content else {}
        data = body.get("data") or []
        pages += 1
        rows.extend(file_row(item, "openai") for item in data)
        # has_more is a required field on this response, so it is authoritative
        # where it appears. The short-page fallback is only for a response that
        # does not honour its own schema, which is worth surviving rather than
        # trusting blindly.
        if body.get("has_more") is False or not data:
            return (rows, pages, True)
        if "has_more" not in body and len(data) < params["limit"]:
            return (rows, pages, True)
        cursor = data[-1].get("id")
        if not cursor:
            return (rows, pages, True)
    return (rows, pages, False)


def fetch_anthropic(key, max_pages, timeout=30):
    """Page GET /v1/files on `page`/`next_page`. Returns (rows, pages, complete).

    Sent without the files-api-2025-04-14 beta header on purpose: with it the
    response reverts to the older cursor shape and expires_at is not returned
    at all, which would silently remove a field this audit reads.
    """
    rows, page, pages = [], None, 0
    headers = {"x-api-key": key, "anthropic-version": "2023-06-01"}
    while pages < max_pages:
        params = {"limit": 1000}
        if page:
            params["page"] = page
        try:
            r = requests.get(ENDPOINTS["anthropic"], params=params,
                             headers=headers, timeout=timeout)
        except requests.RequestException as exc:
            log.error("anthropic listing failed: %s", exc)
            return (rows, pages, False)
        if r.status_code != 200:
            log.error("anthropic listing returned HTTP %s", r.status_code)
            return (rows, pages, False)
        body = r.json() if r.content else {}
        data = body.get("data") or []
        pages += 1
        rows.extend(file_row(item, "anthropic") for item in data)
        page = body.get("next_page")
        if not page:
            return (rows, pages, True)
    return (rows, pages, False)


def report(provider, rows, pages, complete, args, now):
    """Print one store's verdicts. Returns the number of findings."""
    quota = args.quota_bytes or DOC_QUOTA_BYTES[provider]
    cap = args.file_cap_bytes or DOC_FILE_CAP_BYTES[provider]
    tot = totals(rows)
    log.info("%-9s %d page(s) read, %d file(s), %s",
             provider, pages, tot["count"], human(tot["bytes"]))
    log.info("  measured: the sum of %s over every page of GET /v1/files",
             SIZE_FIELD[provider])
    log.info("  documented: a ceiling of %s, which no endpoint reports",
             DOC_QUOTA_LABEL[provider])
    if not complete:
        log.warning("  incomplete: paging stopped early, so %s is a floor and "
                    "not a total", human(tot["bytes"]))

    outlier_state, outlier_detail, big = grade_outliers(rows, cap)
    grades = [grade_total(tot["bytes"], quota),
              grade_concentration(by_purpose(rows), tot["bytes"]),
              (outlier_state, outlier_detail),
              grade_expiry(rows, now, args.stale_days)]

    findings = 0
    for state, detail in grades:
        emit = log.warning if state in FINDINGS else log.info
        emit("%-20s %s", state, detail)
        if state == "file-near-cap":
            for row in big[:5]:
                emit("%-20s %s  %s  %s", "", row["id"], human(row["size"]),
                     row["purpose"])
        for line in repair_lines(state):
            emit("  repair: %s", line)
        if state in FINDINGS:
            findings += 1
    return findings


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--provider", choices=("openai", "anthropic", "both"),
                    default="both", help="which file store to audit")
    ap.add_argument("--quota-bytes", type=int, default=0,
                    help="override the documented ceiling for your account")
    ap.add_argument("--file-cap-bytes", type=int, default=0,
                    help="override the documented per-file cap")
    ap.add_argument("--stale-days", type=int, default=90,
                    help="age at which a file with no expiry is worth listing")
    ap.add_argument("--max-pages", type=int, default=50,
                    help="stop after this many pages and report a floor")
    args = ap.parse_args()

    now = int(time.time())
    wanted = ("openai", "anthropic") if args.provider == "both" else (args.provider,)
    ran = findings = 0
    for provider in wanted:
        key = os.environ.get(KEY_ENV[provider])
        if not key:
            log.info("%-20s %s not set, so that store was not audited. An "
                     "unaudited store is not an empty one",
                     "not-audited", KEY_ENV[provider])
            continue
        fetch = fetch_openai if provider == "openai" else fetch_anthropic
        rows, pages, complete = fetch(key, args.max_pages)
        findings += report(provider, rows, pages, complete, args, now)
        ran += 1

    if not ran:
        log.error("set OPENAI_API_KEY (a project read key) or ANTHROPIC_API_KEY "
                  "(a key with access to the workspace). Every call is a GET of "
                  "/v1/files")
        return 2
    log.info("%d store(s) audited, %d finding(s)", ran, findings)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "file-store-quota-audit.mjs",
"js": '''/**
 * Sum every page of the file store and grade it against a documented ceiling.
 *
 * Read only. GET /v1/files and nothing else, on either provider. Nothing is
 * uploaded, nothing is deleted, and no file content is ever fetched.
 *
 * Neither provider exposes the quota, so the ceiling is a documented constant
 * that no request can confirm while the total is measured by summing a field
 * over every page. The output keeps those two in different columns.
 */
const ENDPOINTS = {
  openai: 'https://api.openai.com/v1/files',
  anthropic: 'https://api.anthropic.com/v1/files',
};

export const DOC_QUOTA_BYTES = { openai: 2_500_000_000_000, anthropic: 1_000_000_000_000 };
export const DOC_QUOTA_LABEL = { openai: '2.5 TB per project',
                                 anthropic: '1 TB per organization' };
export const DOC_FILE_CAP_BYTES = { openai: 512_000_000, anthropic: 500_000_000 };
const SIZE_FIELD = { openai: 'bytes', anthropic: 'size_bytes' };
const KEY_ENV = { openai: 'OPENAI_API_KEY', anthropic: 'ANTHROPIC_API_KEY' };

const FINDINGS = new Set(['quota-critical', 'quota-warning', 'purpose-dominates',
  'file-near-cap', 'no-expiry-policy']);

/** Seconds since the epoch from either provider's shape. Pure. */
export function epoch(value) {
  if (value === null || value === undefined || value === '' || typeof value === 'boolean') {
    return 0;
  }
  if (typeof value === 'number') {
    return Number.isFinite(value) ? Math.max(0, Math.trunc(value)) : 0;
  }
  const ms = Date.parse(String(value).trim());
  return Number.isFinite(ms) ? Math.max(0, Math.trunc(ms / 1000)) : 0;
}

/** One file object, normalised. Pure. Two providers, one shape. */
export function fileRow(body, provider) {
  const row = (body && typeof body === 'object') ? body : {};
  const size = Number(row[SIZE_FIELD[provider] ?? 'bytes']);
  const expires = epoch(row.expires_at);
  return {
    id: String(row.id ?? ''),
    filename: String(row.filename ?? ''),
    size: Number.isFinite(size) ? Math.max(0, Math.trunc(size)) : 0,
    purpose: String(row.purpose ?? 'unclassified'),
    created_at: epoch(row.created_at),
    expires_at: expires || null,
    expiry_reported: Object.prototype.hasOwnProperty.call(row, 'expires_at'),
  };
}

/** Binary units, one decimal. Pure. */
export function human(size) {
  let n = Number(size);
  if (!Number.isFinite(n)) return '0 B';
  for (const unit of ['B', 'KiB', 'MiB', 'GiB', 'TiB']) {
    if (Math.abs(n) < 1024 || unit === 'TiB') {
      return unit === 'B' ? `${Math.trunc(n)} B` : `${n.toFixed(1)} ${unit}`;
    }
    n /= 1024;
  }
  return `${n.toFixed(1)} TiB`;
}

/** Count and summed bytes. Pure. */
export function totals(rows) {
  const list = rows ?? [];
  return { count: list.length,
           bytes: list.reduce((a, r) => a + Number(r?.size ?? 0), 0) };
}

/** Per-purpose count and bytes, largest first. Pure. */
export function byPurpose(rows) {
  const acc = new Map();
  for (const row of rows ?? []) {
    const key = String(row?.purpose ?? 'unclassified');
    const cur = acc.get(key) ?? { count: 0, bytes: 0 };
    cur.count += 1;
    cur.bytes += Number(row?.size ?? 0);
    acc.set(key, cur);
  }
  return [...acc.entries()]
    .map(([k, v]) => [k, v.count, v.bytes])
    .sort((a, b) => (b[2] - a[2]) || String(a[0]).localeCompare(String(b[0])));
}

/** Share of a documented ceiling. Pure. The ceiling is an argument. */
export function gradeTotal(totalBytes, quotaBytes, warnShare = 0.60, criticalShare = 0.85) {
  const quota = Number(quotaBytes);
  const used = Number(totalBytes);
  if (!Number.isFinite(quota) || !Number.isFinite(used) || quota <= 0) {
    return ['quota-unknown',
      'no usable ceiling was supplied, so the total is a number without a denominator'];
  }
  const share = used / quota;
  const headroom = human(Math.max(0, quota - used));
  const detail = `${(share * 100).toFixed(1)}% of the documented ceiling is in use, `
    + `with about ${headroom} of headroom before uploads start to fail`;
  if (share >= criticalShare) return ['quota-critical', detail];
  if (share >= warnShare) return ['quota-warning', detail];
  return ['quota-headroom',
    `${(share * 100).toFixed(1)}% of the documented ceiling is in use, ${headroom} of headroom`];
}

/** The purpose class worth sweeping first. Pure. */
export function gradeConcentration(purposes, totalBytes, share = 0.40) {
  const total = Number(totalBytes) || 0;
  if (!(purposes ?? []).length || total <= 0) {
    return ['purpose-even',
      'nothing to concentrate: the store is empty or carries no size information'];
  }
  const [name, count, size] = purposes[0];
  const got = size / total;
  if (got < share) {
    return ['purpose-even',
      `no single purpose holds more than ${(share * 100).toFixed(0)}% of the store; `
      + `the largest is ${name} at ${(got * 100).toFixed(1)}%`];
  }
  return ['purpose-dominates',
    `${name} is ${(got * 100).toFixed(1)}% of the store, ${count} file(s)`];
}

/** The second ceiling, per file and not a fraction of the first. Pure. */
export function gradeOutliers(rows, capBytes, warnShare = 0.80) {
  const cap = Number(capBytes);
  if (!Number.isFinite(cap) || cap <= 0) {
    return ['cap-unknown', 'no per-file cap was supplied', []];
  }
  const floor = cap * warnShare;
  const big = (rows ?? []).filter((r) => Number(r?.size ?? 0) >= floor)
    .sort((a, b) => Number(b.size) - Number(a.size));
  if (!big.length) {
    return ['file-sizes-fine',
      `no file is within ${(warnShare * 100).toFixed(0)}% of the per-file cap`, []];
  }
  return ['file-near-cap',
    `${big.length} file(s) above ${(warnShare * 100).toFixed(0)}% of the per-file cap`,
    big];
}

/** The only reading here that describes the future. Pure. */
export function gradeExpiry(rows, now, staleDays) {
  const list = rows ?? [];
  if (!list.length) return ['expiry-none', 'the store is empty'];
  const unexpiring = list.filter((r) => !r?.expires_at);
  if (!unexpiring.length) {
    return ['expiry-covered',
      'every file carries an expires_at, so this store has a lifecycle rather '
      + 'than a trajectory'];
  }
  const cutoff = Number(now) - Number(staleDays) * 86400;
  const stale = unexpiring.filter((r) => Number(r?.created_at ?? 0) > 0
    && Number(r.created_at) < cutoff);
  return ['no-expiry-policy',
    `${unexpiring.length} of ${list.length} file(s) have no expires_at, and `
    + `${stale.length} of those are older than ${Number(staleDays)} day(s)`];
}

/** The repair for one verdict. Pure. Printed, never performed. */
export function repairLines(state) {
  if (state === 'quota-critical' || state === 'quota-warning') {
    return ['sweep the purpose class named below, then set an expiry at upload so '
      + 'the next two thirds take longer to arrive than the last did.'];
  }
  if (state === 'purpose-dominates') {
    return ['delete the ones whose job is finished and read, one at a time, with '
      + 'DELETE /v1/files/{file_id}. Nothing here does that for you, a deleted '
      + 'file cannot be recovered, and on OpenAI the deletion also removes the '
      + 'file from every vector store holding it.'];
  }
  if (state === 'file-near-cap') {
    return ['a second ceiling, unrelated to the total. Split these at source '
      + 'rather than making room for them.'];
  }
  if (state === 'no-expiry-policy') {
    return ['upload with an expiry so this population stops being unbounded: '
      + 'expires_after with an anchor of created_at on OpenAI (3600 to 2592000 '
      + 'seconds), expires_in_seconds on Anthropic (3600 to 7776000).',
    'for what is already there, confirm by hand and then delete. Nothing in the '
      + 'metadata can tell an audit which files matter.'];
  }
  if (state === 'quota-unknown') {
    return ['pass --quota-bytes. Without a denominator this run is an inventory '
      + 'rather than an audit.'];
  }
  return [];
}

async function fetchOpenai(key, maxPages) {
  const rows = [];
  let cursor = null;
  let pages = 0;
  while (pages < maxPages) {
    const url = new URL(ENDPOINTS.openai);
    url.searchParams.set('limit', '10000');
    url.searchParams.set('order', 'asc');
    if (cursor) url.searchParams.set('after', cursor);
    let res;
    try {
      res = await fetch(url, { headers: { Authorization: `Bearer ${key}` } });
    } catch (err) {
      console.error(`openai listing failed: ${err.message}`);
      return [rows, pages, false];
    }
    if (res.status !== 200) {
      console.error(`openai listing returned HTTP ${res.status}`);
      return [rows, pages, false];
    }
    const body = await res.json().catch(() => ({}));
    const data = body.data ?? [];
    pages += 1;
    for (const item of data) rows.push(fileRow(item, 'openai'));
    if (body.has_more === false || !data.length) return [rows, pages, true];
    if (!('has_more' in body) && data.length < 10000) return [rows, pages, true];
    cursor = data[data.length - 1]?.id;
    if (!cursor) return [rows, pages, true];
  }
  return [rows, pages, false];
}

async function fetchAnthropic(key, maxPages) {
  const rows = [];
  let page = null;
  let pages = 0;
  const headers = { 'x-api-key': key, 'anthropic-version': '2023-06-01' };
  while (pages < maxPages) {
    const url = new URL(ENDPOINTS.anthropic);
    url.searchParams.set('limit', '1000');
    if (page) url.searchParams.set('page', page);
    let res;
    try {
      res = await fetch(url, { headers });
    } catch (err) {
      console.error(`anthropic listing failed: ${err.message}`);
      return [rows, pages, false];
    }
    if (res.status !== 200) {
      console.error(`anthropic listing returned HTTP ${res.status}`);
      return [rows, pages, false];
    }
    const body = await res.json().catch(() => ({}));
    const data = body.data ?? [];
    pages += 1;
    for (const item of data) rows.push(fileRow(item, 'anthropic'));
    page = body.next_page;
    if (!page) return [rows, pages, true];
  }
  return [rows, pages, false];
}

function report(provider, rows, pages, complete, opts, now) {
  const quota = opts.quotaBytes || DOC_QUOTA_BYTES[provider];
  const cap = opts.fileCapBytes || DOC_FILE_CAP_BYTES[provider];
  const tot = totals(rows);
  console.log(`${provider.padEnd(9)} ${pages} page(s) read, ${tot.count} file(s), `
    + `${human(tot.bytes)}`);
  console.log(`  measured: the sum of ${SIZE_FIELD[provider]} over every page of `
    + 'GET /v1/files');
  console.log(`  documented: a ceiling of ${DOC_QUOTA_LABEL[provider]}, which no `
    + 'endpoint reports');
  if (!complete) {
    console.log(`  incomplete: paging stopped early, so ${human(tot.bytes)} is a `
      + 'floor and not a total');
  }

  const [outlierState, outlierDetail, big] = gradeOutliers(rows, cap);
  const grades = [gradeTotal(tot.bytes, quota),
                  gradeConcentration(byPurpose(rows), tot.bytes),
                  [outlierState, outlierDetail],
                  gradeExpiry(rows, now, opts.staleDays)];
  let findings = 0;
  for (const [state, detail] of grades) {
    console.log(`${state.padEnd(20)} ${detail}`);
    if (state === 'file-near-cap') {
      for (const row of big.slice(0, 5)) {
        console.log(`${''.padEnd(20)} ${row.id}  ${human(row.size)}  ${row.purpose}`);
      }
    }
    for (const line of repairLines(state)) console.log(`  repair: ${line}`);
    if (FINDINGS.has(state)) findings += 1;
  }
  return findings;
}

function args(argv) {
  const out = { provider: 'both', quotaBytes: 0, fileCapBytes: 0, staleDays: 90,
                maxPages: 50 };
  for (let i = 0; i < argv.length; i += 1) {
    if (argv[i] === '--provider') out.provider = argv[i += 1];
    else if (argv[i] === '--quota-bytes') out.quotaBytes = Number(argv[i += 1]);
    else if (argv[i] === '--file-cap-bytes') out.fileCapBytes = Number(argv[i += 1]);
    else if (argv[i] === '--stale-days') out.staleDays = Number(argv[i += 1]);
    else if (argv[i] === '--max-pages') out.maxPages = Number(argv[i += 1]);
  }
  return out;
}

async function main() {
  const opts = args(process.argv.slice(2));
  const now = Math.trunc(Date.now() / 1000);
  const wanted = opts.provider === 'both' ? ['openai', 'anthropic'] : [opts.provider];
  let ran = 0;
  let findings = 0;
  for (const provider of wanted) {
    const key = process.env[KEY_ENV[provider]];
    if (!key) {
      console.log(`${'not-audited'.padEnd(20)} ${KEY_ENV[provider]} not set, so that `
        + 'store was not audited. An unaudited store is not an empty one');
      continue;
    }
    const [rows, pages, complete] = provider === 'openai'
      ? await fetchOpenai(key, opts.maxPages)
      : await fetchAnthropic(key, opts.maxPages);
    findings += report(provider, rows, pages, complete, opts, now);
    ran += 1;
  }
  if (!ran) {
    console.error('set OPENAI_API_KEY (a project read key) or ANTHROPIC_API_KEY '
      + '(a key with access to the workspace). Every call is a GET of /v1/files');
    process.exitCode = 2;
    return;
  }
  console.log(`${ran} store(s) audited, ${findings} finding(s)`);
  process.exitCode = findings ? 1 : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) await main();
''',
"test_intro": "The first test is the one that keeps the note honest: the ceiling is an argument, so the same measured total grades differently against a different documented limit, and a run with no usable ceiling reports an inventory rather than a percentage. The second is the normaliser, which turns OpenAI's <code>bytes</code> and Anthropic's <code>size_bytes</code> into one shape, parses both an integer timestamp and an RFC 3339 string through one clock, and must not invent a <code>purpose</code> for a provider that has no such concept. Then concentration, which only fires when one class really dominates, because a report that always fires is a report nobody reads. Then the per-file cap, asserted independent of the total: a store at 3% of quota with one enormous file is still a finding. Then expiry, the only grader here about the future, including the store where everything expires and there is nothing to say. And last the repair lines, checked to name a deletion and never to perform one.",
"test_py_file": "test_file_store_quota_audit.py",
"test_py": '''from file_store_quota_audit import (by_purpose, epoch, file_row,
                                    grade_concentration, grade_expiry,
                                    grade_outliers, grade_total, human,
                                    repair_lines, totals)

NOW = 1_800_000_000
DAY = 86400
GIB = 1024 ** 3


def oai(fid, size, purpose="batch", days_old=1, expires=None):
    return file_row({"id": fid, "bytes": size, "purpose": purpose,
                     "filename": fid + ".jsonl",
                     "created_at": NOW - int(days_old * DAY),
                     "expires_at": expires}, "openai")


def test_the_ceiling_is_an_argument_because_no_endpoint_reports_it():
    used = 90 * GIB
    tight, detail = grade_total(used, 100 * GIB)
    assert tight == "quota-critical"
    assert "90.0%" in detail and "headroom" in detail
    # Same measured total, different documented ceiling, different verdict.
    assert grade_total(used, 1000 * GIB)[0] == "quota-headroom"
    assert grade_total(used, 140 * GIB)[0] == "quota-warning"
    # No denominator at all is an inventory, not a percentage.
    state, detail = grade_total(used, 0)
    assert state == "quota-unknown"
    assert "without a denominator" in detail
    assert any("--quota-bytes" in line for line in repair_lines(state))


def test_two_providers_normalise_to_one_shape_and_one_clock():
    a = file_row({"id": "file-a1", "bytes": 2048, "purpose": "batch_output",
                  "created_at": 1_700_000_000, "expires_at": None}, "openai")
    b = file_row({"id": "file_b2", "size_bytes": 2048, "filename": "doc.pdf",
                  "created_at": "2023-11-14T22:13:20Z",
                  "expires_at": None}, "anthropic")
    assert a["size"] == b["size"] == 2048
    assert a["purpose"] == "batch_output"
    # Anthropic has no purpose concept, so the row says so rather than guessing.
    assert b["purpose"] == "unclassified"
    # One clock: an integer and an RFC 3339 string land on the same second.
    assert a["created_at"] == b["created_at"] == 1_700_000_000
    assert epoch("2023-11-14T22:13:20+00:00") == 1_700_000_000
    assert epoch("2023-11-14T23:13:20+01:00") == 1_700_000_000
    assert epoch(None) == 0 and epoch("") == 0 and epoch("last tuesday") == 0
    assert a["expires_at"] is None and a["expiry_reported"] is True
    # A row with no expires_at key at all: OpenAI omits it rather than nulling.
    assert file_row({"id": "file-c3", "bytes": 1}, "openai")["expiry_reported"] is False
    assert file_row(None, "openai")["size"] == 0
    assert file_row({"bytes": "nonsense"}, "openai")["size"] == 0
    assert human(2048) == "2.0 KiB" and human(0) == "0 B" and human(None) == "0 B"


def test_concentration_only_fires_when_one_class_really_dominates():
    lopsided = [oai("file-1", 90 * GIB, "batch_output"),
                oai("file-2", 5 * GIB, "fine-tune"),
                oai("file-3", 5 * GIB, "user_data")]
    tot = totals(lopsided)
    assert tot == {"count": 3, "bytes": 100 * GIB}
    ranked = by_purpose(lopsided)
    assert ranked[0][0] == "batch_output" and ranked[0][1] == 1
    state, detail = grade_concentration(ranked, tot["bytes"])
    assert state == "purpose-dominates"
    assert "batch_output is 90.0%" in detail
    assert any("DELETE /v1/files/{file_id}" in line for line in repair_lines(state))
    # An evenly spread store has nothing to sweep first.
    even = [oai("file-4", 10 * GIB, "batch"), oai("file-5", 10 * GIB, "fine-tune"),
            oai("file-6", 10 * GIB, "user_data")]
    flat, flat_detail = grade_concentration(by_purpose(even), totals(even)["bytes"])
    assert flat == "purpose-even"
    assert "largest is" in flat_detail
    assert grade_concentration([], 0)[0] == "purpose-even"


def test_the_per_file_cap_is_a_second_ceiling_and_not_a_share_of_the_first():
    rows = [oai("file-9f1", 487_000_000, "fine-tune"), oai("file-a2", 1024)]
    # A fraction of a percent of a huge quota, and still a finding.
    assert grade_total(totals(rows)["bytes"], 16 * 1024 * GIB)[0] == "quota-headroom"
    state, detail, big = grade_outliers(rows, 512_000_000)
    assert state == "file-near-cap"
    assert "1 file(s)" in detail and "80%" in detail
    assert [row["id"] for row in big] == ["file-9f1"]
    assert any("second ceiling" in line for line in repair_lines(state))
    assert grade_outliers(rows, 16 * GIB)[0] == "file-sizes-fine"
    assert grade_outliers(rows, 0)[0] == "cap-unknown"


def test_expiry_is_the_only_grader_that_describes_the_future():
    stale = [oai("file-1", GIB, days_old=200), oai("file-2", GIB, days_old=200),
             oai("file-3", GIB, days_old=2)]
    state, detail = grade_expiry(stale, NOW, 90)
    assert state == "no-expiry-policy"
    assert "3 of 3 file(s) have no expires_at" in detail
    assert "2 of those are older than 90 day(s)" in detail
    assert any("expires_in_seconds" in line for line in repair_lines(state))
    # A store where everything expires has a lifecycle and is not this note.
    covered = [oai("file-4", GIB, expires=NOW + 10 * DAY)]
    clean, clean_detail = grade_expiry(covered, NOW, 90)
    assert clean == "expiry-covered"
    assert "lifecycle" in clean_detail
    assert repair_lines(clean) == []
    assert grade_expiry([], NOW, 90)[0] == "expiry-none"


def test_every_repair_is_printed_and_none_of_them_reclaims_anything():
    for state in ("quota-critical", "quota-warning", "purpose-dominates",
                  "file-near-cap", "no-expiry-policy", "quota-unknown"):
        lines = repair_lines(state)
        assert lines, state
        assert all(isinstance(line, str) and line for line in lines)
    assert any("cannot be recovered" in line
               for line in repair_lines("purpose-dominates"))
    assert repair_lines("quota-headroom") == []
    assert repair_lines("expiry-covered") == []
''',
"test_js_file": "file-store-quota-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { byPurpose, epoch, fileRow, gradeConcentration, gradeExpiry, gradeOutliers,
         gradeTotal, human, repairLines, totals } from './file-store-quota-audit.mjs';

const NOW = 1_800_000_000;
const DAY = 86400;
const GIB = 1024 ** 3;

const oai = (id, size, purpose = 'batch', daysOld = 1, expires = null) => fileRow({
  id, bytes: size, purpose, filename: `${id}.jsonl`,
  created_at: NOW - Math.trunc(daysOld * DAY), expires_at: expires,
}, 'openai');

test('the ceiling is an argument because no endpoint reports it', () => {
  const used = 90 * GIB;
  const [tight, detail] = gradeTotal(used, 100 * GIB);
  assert.equal(tight, 'quota-critical');
  assert.ok(detail.includes('90.0%') && detail.includes('headroom'));
  assert.equal(gradeTotal(used, 1000 * GIB)[0], 'quota-headroom');
  assert.equal(gradeTotal(used, 140 * GIB)[0], 'quota-warning');
  const [state, why] = gradeTotal(used, 0);
  assert.equal(state, 'quota-unknown');
  assert.ok(why.includes('without a denominator'));
  assert.ok(repairLines(state).some((l) => l.includes('--quota-bytes')));
});

test('two providers normalise to one shape and one clock', () => {
  const a = fileRow({ id: 'file-a1', bytes: 2048, purpose: 'batch_output',
                      created_at: 1700000000, expires_at: null }, 'openai');
  const b = fileRow({ id: 'file_b2', size_bytes: 2048, filename: 'doc.pdf',
                      created_at: '2023-11-14T22:13:20Z', expires_at: null },
                    'anthropic');
  assert.equal(a.size, 2048);
  assert.equal(b.size, 2048);
  assert.equal(a.purpose, 'batch_output');
  assert.equal(b.purpose, 'unclassified');
  assert.equal(a.created_at, 1700000000);
  assert.equal(b.created_at, 1700000000);
  assert.equal(epoch('2023-11-14T22:13:20+00:00'), 1700000000);
  assert.equal(epoch('2023-11-14T23:13:20+01:00'), 1700000000);
  assert.equal(epoch(null), 0);
  assert.equal(epoch(''), 0);
  assert.equal(epoch('last tuesday'), 0);
  assert.equal(a.expires_at, null);
  assert.equal(a.expiry_reported, true);
  assert.equal(fileRow({ id: 'file-c3', bytes: 1 }, 'openai').expiry_reported, false);
  assert.equal(fileRow(null, 'openai').size, 0);
  assert.equal(fileRow({ bytes: 'nonsense' }, 'openai').size, 0);
  assert.equal(human(2048), '2.0 KiB');
  assert.equal(human(0), '0 B');
  assert.equal(human(null), '0 B');
});

test('concentration only fires when one class really dominates', () => {
  const lopsided = [oai('file-1', 90 * GIB, 'batch_output'),
                    oai('file-2', 5 * GIB, 'fine-tune'),
                    oai('file-3', 5 * GIB, 'user_data')];
  const tot = totals(lopsided);
  assert.deepEqual(tot, { count: 3, bytes: 100 * GIB });
  const ranked = byPurpose(lopsided);
  assert.equal(ranked[0][0], 'batch_output');
  assert.equal(ranked[0][1], 1);
  const [state, detail] = gradeConcentration(ranked, tot.bytes);
  assert.equal(state, 'purpose-dominates');
  assert.ok(detail.includes('batch_output is 90.0%'));
  assert.ok(repairLines(state).some((l) => l.includes('DELETE /v1/files/{file_id}')));
  const even = [oai('file-4', 10 * GIB, 'batch'), oai('file-5', 10 * GIB, 'fine-tune'),
                oai('file-6', 10 * GIB, 'user_data')];
  const [flat, flatDetail] = gradeConcentration(byPurpose(even), totals(even).bytes);
  assert.equal(flat, 'purpose-even');
  assert.ok(flatDetail.includes('largest is'));
  assert.equal(gradeConcentration([], 0)[0], 'purpose-even');
});

test('the per file cap is a second ceiling and not a share of the first', () => {
  const rows = [oai('file-9f1', 487000000, 'fine-tune'), oai('file-a2', 1024)];
  assert.equal(gradeTotal(totals(rows).bytes, 16 * 1024 * GIB)[0], 'quota-headroom');
  const [state, detail, big] = gradeOutliers(rows, 512000000);
  assert.equal(state, 'file-near-cap');
  assert.ok(detail.includes('1 file(s)') && detail.includes('80%'));
  assert.deepEqual(big.map((r) => r.id), ['file-9f1']);
  assert.ok(repairLines(state).some((l) => l.includes('second ceiling')));
  assert.equal(gradeOutliers(rows, 16 * GIB)[0], 'file-sizes-fine');
  assert.equal(gradeOutliers(rows, 0)[0], 'cap-unknown');
});

test('expiry is the only grader that describes the future', () => {
  const stale = [oai('file-1', GIB, 'batch', 200), oai('file-2', GIB, 'batch', 200),
                 oai('file-3', GIB, 'batch', 2)];
  const [state, detail] = gradeExpiry(stale, NOW, 90);
  assert.equal(state, 'no-expiry-policy');
  assert.ok(detail.includes('3 of 3 file(s) have no expires_at'));
  assert.ok(detail.includes('2 of those are older than 90 day(s)'));
  assert.ok(repairLines(state).some((l) => l.includes('expires_in_seconds')));
  const covered = [oai('file-4', GIB, 'batch', 1, NOW + 10 * DAY)];
  const [clean, cleanDetail] = gradeExpiry(covered, NOW, 90);
  assert.equal(clean, 'expiry-covered');
  assert.ok(cleanDetail.includes('lifecycle'));
  assert.deepEqual(repairLines(clean), []);
  assert.equal(gradeExpiry([], NOW, 90)[0], 'expiry-none');
});

test('every repair is printed and none of them reclaims anything', () => {
  for (const state of ['quota-critical', 'quota-warning', 'purpose-dominates',
                       'file-near-cap', 'no-expiry-policy', 'quota-unknown']) {
    const lines = repairLines(state);
    assert.ok(lines.length, state);
    assert.ok(lines.every((l) => typeof l === 'string' && l.length));
  }
  assert.ok(repairLines('purpose-dominates').some((l) => l.includes('cannot be recovered')));
  assert.deepEqual(repairLines('quota-headroom'), []);
  assert.deepEqual(repairLines('expiry-covered'), []);
});
''',
"faq": [
 ("Is there really no endpoint that tells me how much storage I am using?",
  "There is not, on either provider, and that is why this is a paging script rather than a single GET. Nothing returns a quota, a consumed figure, a remaining figure or a percentage. The listing is the only surface that knows anything about your files, so the total has to be assembled from it by summing a size field over every page. That is also why the ceiling in the output is labelled documented rather than reported: it came from a docs page, no request confirms it, and OpenAI's own files documentation invites you to ask for a higher limit, which means some accounts are working against a number the default would get wrong."),
 ("Which container does the limit actually apply to?",
  "Different ones, which is the trap. OpenAI documents 2.5 TB per project and states there is no organization-wide storage limit at all, so ten projects are ten independent ceilings and a project key can only see one of them. Anthropic documents 1 TB per organization while its Files API is workspace-scoped, so one workspace is a slice of the number that governs you and a clean run there proves less than it looks. The script prints which container it just measured and names the stores it did not look at."),
 ("Why not just delete the old files while the script is already looking at them?",
  "Because a deleted file cannot be recovered, nothing in the metadata can tell an audit which files matter, and on OpenAI the documented behaviour of the delete call is to remove the file from every vector store it is attached to as well. A 400-day-old file with no expiry might be the corpus behind a fine-tuned model serving production traffic, and it looks exactly like a batch input from a job that finished last quarter. The script prints one deletion command per candidate and stops there."),
 ("The store is nowhere near the ceiling but uploads are still failing. What now?",
  "Look at the per-file cap, which is the third finding the script prints and a completely separate limit: 512 MB on OpenAI, 500 MB on Anthropic, applied to one upload rather than to the store. A single oversized file is rejected while the store is 3% full, and the error reads similarly enough to a quota error that it eats the first hour of the investigation. The script grades the two independently and lists the largest files so you can see whether one of them is the actual problem."),
 ("How is this different from the note about vector store storage cost?",
  "Different object, different failure, different repair. That note reads usage_bytes on vector stores, trends it across ninety days against retrieval volume, and prices the slope from a gibibyte_hours line item: its finding is money and its shape is a curve. This one reads the file store, where Anthropic states outright that Files API operations are free, and compares one number to a hard ceiling: the finding is not on the invoice at all, it is how many uploads you have left. A file can be in both populations at once, which is fine, because you would fix that in two different places."),
],
"related": [REL_ORPHAN, REL_EXPFILE, REL_VSBYTES],
"citations": [CITE_OAI_FILES, CITE_OAI_DATA, CITE_ANT_FILES, CITE_ANT_LIST],
},
{
"slug": "orphaned-assistants-purpose-files",
"title": "purpose=assistants files outlived the API that owned them",
"description": "The Assistants API is gone and its files are not. List both assistants purposes, subtract every id a surviving vector store holds, grade the remainder.",
"h1": "purpose=assistants files outlived the API that owned them",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["openai purpose assistants files after shutdown",
             "assistants_output files orphaned 2026",
             "which files are still in a vector store openai",
             "delete orphaned openai files purpose assistants",
             "assistants api sunset what happens to my files"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Needs OPENAI_API_KEY, a project key set to Read Only. Every call is a GET: two file listings, the vector store listing, and one file listing per store. Vector stores are project-scoped, so run it with the key of the project that owns them.",
"lead": "The Assistants API reached its shutdown date on 26 August 2026 and the migration was done months ago. Runs became responses, threads became conversations, the beta header came out of the client, and the whole thing has been working ever since. What nobody did, because nothing asked and nothing broke, was go and look at the files. They are still there. Every document ever uploaded for an assistant, every code-interpreter output from a run that no longer exists, sitting in a store whose owner was deleted, counting against a ceiling and answering every listing call as though the last two years never happened.",
"short_answer": """<p>This is a subtraction, not a measurement. One set is every file carrying a purpose whose owning API is gone: <code>GET /v1/files?purpose=assistants</code> and <code>GET /v1/files?purpose=assistants_output</code>, both paged on <code>after</code> with a <strong>project read key</strong>. Both values are still enumerated on the File object, so those listings still work and still return things.</p>
<p>The other set is every file id a live vector store still holds. Walk <code>GET /v1/vector_stores</code> (<code>limit</code> caps at 100 there, not the 10,000 the files endpoint allows) and then <code>GET /v1/vector_stores/{vector_store_id}/files</code> for each one. The vector-store file object's <code>id</code> <em>is</em> the underlying Files-API id, which is what makes the subtraction possible at all.</p>
<p>What is left over is owned by nothing. It is not attached to a vector store, and the assistant, thread and run that used to point at it no longer exist as objects you can query. Those files are still enumerable, still counted against the project's storage ceiling, and referenced by nothing.</p>
<p>Be careful about what is documented here, because the script is. OpenAI's migration guide covers assistants, threads and runs and <strong>never mentions files, vector stores or purposes at all</strong>. So "files carry over" is an inference. What the platform does state is narrower and sufficient: those two purpose values are still valid on the File object, vector stores are a live non-beta resource with their own reference page, and <code>DELETE /v1/files/{file_id}</code> is documented to remove the file from every vector store it is in. The output labels the measured half and the inferred half separately.</p>
<p>The whole verdict rests on the set you subtract, so a store whose file listing failed poisons the arithmetic. When that happens the script downgrades <em>every</em> orphan in the run rather than skipping one store, because a set difference against an incomplete set names files that are perfectly well referenced.</p>""",
"problem": """<p>An ownership graph is not storage, and only one of them was decommissioned. Assistants, threads, messages and runs were objects on OpenAI's side; the files they referenced were separate objects with their own lifecycle. When the endpoint family reached its shutdown date, the graph went. The files did not, because nothing about deleting an API deletes the blobs it happened to point at, and nobody would want it to.</p>
<p>What makes this a note rather than an obvious consequence is that the migration is written entirely in terms of code. The guide is about turning a run into a response and a thread into a conversation; it does not have a storage chapter, because the storage kept working perfectly throughout. Nothing in the migration path takes you past your own files, so the last time anybody looked at them was before the year of notice started.</p>
<p>And the leftover class is unusually large in a way that is easy to underestimate. <code>purpose=assistants</code> was the upload path for every document anyone ever attached to an assistant, including the ones attached during the prototype, the demo and the abandoned second product. <code>purpose=assistants_output</code> is worse: it is every artefact the code interpreter ever wrote, one per run, generated automatically by traffic rather than deliberately by a person. Nobody uploads those and nobody has a list of them.</p>
<p>The consequence is entirely quiet. They do not fail. They do not error. They cost storage against a project ceiling nothing reports, and they sit in an account as a body of documents nobody has an inventory of and nobody has reviewed, which is a different problem from a cost problem and lands on a different desk.</p>""",
"why": """<p><strong>A subtraction is only as good as the set you subtract, so an unreadable store voids the run.</strong> This is the single most important design decision in the script. If one vector store's file listing 403s or times out, the ids inside it are missing from the referenced set, and every one of those files then looks like an orphan. Printing them anyway would be worse than printing nothing, because the output of this script is a list of deletion commands. So a partial referenced set downgrades every verdict in the run to <code>subtraction-incomplete</code>, names the stores it could not read, and produces no deletion lines at all.</p>
<p><strong>The two purposes are one class and two different problems.</strong> <code>assistants</code> files were uploaded by a person who chose to upload them, so some of them are documents somebody still wants and the repair is an archive followed by a deletion. <code>assistants_output</code> files were generated by the platform, one per code-interpreter run, and were only ever meaningful inside a run object that no longer exists. The script grades them as separate states for that reason, and the second one is a much easier conversation.</p>
<p><strong>The vector store's file id is the file id, and that is what makes this cheap.</strong> There is no join table and no lookup: the object returned by <code>GET /v1/vector_stores/{id}/files</code> carries the underlying Files-API id directly, so the referenced set is built by reading one field. It also means a single set membership test answers the whole question for a file, rather than a per-file query against every store.</p>
<p><strong>The pagination limits are not the same on the two endpoints and copying one to the other silently truncates.</strong> The files listing accepts a <code>limit</code> of up to 10,000 and defaults to it. The vector store listing and the vector-store-files listing both cap at 100 and default to 20. A script that reuses the first number on the second endpoint gets a page of 100 and a referenced set that is missing everything after it, which turns into a confident list of orphans that are not orphans.</p>
<p><strong>Deleting a file detaches it from every vector store, which is why the order matters.</strong> The delete call is documented as removing the file from all vector stores as well. So a mistaken deletion is not just an unrecoverable file, it is a hole in a live retrieval index that will show up later as an answer with fewer citations and no error. That is the failure mode of the note next door about a store that silently lost a document, and it is why nothing here executes anything.</p>
<p><strong>This is not the shutdown probe, and the two answer different questions.</strong> The published note on the Assistants shutdown asks whether <code>/v1/assistants</code> still answers for your organization and grades a status code against a control path. That is a question about access. This is a question about inventory, it assumes the endpoint is gone, and it would produce exactly the same findings on an organization that migrated cleanly two years ago.</p>""",
"steps": [
 {"h": "Use the project key that owns the vector stores",
  "body": """<p>Vector stores are project-scoped, so a key from the wrong project returns a clean, empty store list and every file in the class then looks unreferenced. The script reports how many stores it found, and a run that found zero says so loudly rather than reporting a project full of orphans.</p>"""},
 {"h": "List both purposes, paged to the end",
  "body": """<p><code>GET /v1/files?purpose=assistants</code> and <code>GET /v1/files?purpose=assistants_output</code>. Both values are still enumerated on the File object even though the API that produced them is gone, so these listings return real results. Page on <code>after</code> until <code>has_more</code> is false.</p>"""},
 {"h": "Build the referenced set from the stores, at their own page size",
  "body": """<p><code>GET /v1/vector_stores?limit=100</code>, then <code>GET /v1/vector_stores/{vector_store_id}/files?limit=100</code> for each. Both cap at 100 rather than the files endpoint's 10,000. Each vector-store file object's <code>id</code> is the Files-API id, so the set is one field per row.</p>"""},
 {"h": "Refuse to subtract from an incomplete set",
  "body": """<p>If any store's listing failed, the run is graded <code>subtraction-incomplete</code> in full. The script names the stores it could not read and prints no deletion commands, because the alternative is a deletion list containing files that are in a store the script could not see.</p>"""},
 {"h": "Archive first, then delete, one command at a time",
  "body": """<p>The printed repair is <code>DELETE /v1/files/{file_id}</code> per confirmed orphan, and it is printed rather than run. Deleted files cannot be recovered, and the delete also removes the file from every vector store holding it, so a wrong id costs you a document and a hole in an index.</p>"""},
],
"verify": """<p>Re-run after a sweep and the class should shrink to the files you decided to keep, all of which should come back as <code>still-referenced</code> or as a purpose class you have consciously chosen not to empty. The reading that matters more on the second run is the store count: it should be the same. A run whose store count dropped is not evidence that you cleaned up, it is evidence that the key or the project changed, and the script prints that number first for exactly that reason.</p>
<pre><code class="language-bash">python3 openai_orphaned_assistant_files.py
# 6 vector store(s) read, 1,204 referenced file id(s)
# 318 file(s) in the class: 241 assistants, 77 assistants_output, 12.4 GiB
#   measured: two purpose listings, minus the ids held by every store read
#   inferred: that a file in no surviving store has no owner. The migration
#             guide documents nothing at all about files or vector stores
# class-populated      318 file(s) carry a purpose whose owning API no longer
#                      exists
# orphan               file-3ab: no surviving vector store holds this id,
#                      41.2 MiB, uploaded 511 day(s) ago
# orphan               file-77c: no surviving vector store holds this id,
#                      2.9 MiB, uploaded 447 day(s) ago
# orphan-output        file-b19: code interpreter output from a run that no
#                      longer exists, 118.0 KiB, created 502 day(s) ago
# still-referenced     file-c04: held by a live vector store, so file search
#                      under the Responses API still reads it
#   repair: 289 confirmed orphan(s), 11.8 GiB. Archive anything you still want,
#           then DELETE /v1/files/{file_id} one at a time. The delete also
#           removes the file from every vector store holding it.
#   repair: re-upload future file search sources with purpose user_data and an
#           expires_after policy, so the next class ages out on its own.
# 289 finding(s)</code></pre>""",
"code_intro": "Four kinds of paged GET and seven pure functions. <code>file_row</code> and <code>referenced_ids</code>, the two sides of the subtraction, the second of which reads the vector-store file object's own <code>id</code> because that id <em>is</em> the Files-API id; <code>human</code> and <code>age_days</code>, the formatting the output needs; <code>class_state</code>, which grades the purpose class as a whole and has an outcome for the class being empty; <code>classify_file</code>, which puts the completeness of the referenced set ahead of every other test so that an unreadable store cannot produce a deletion command; <code>summarise</code>, which folds the graded rows into the counts the repair line quotes; and <code>repair_lines</code>, which names the vector-store side effect of a delete in the same breath as the delete.",
"py_file": "openai_orphaned_assistant_files.py",
"py": '''"""Subtract the ids surviving vector stores hold from one dead purpose class.

Read only. Four kinds of GET: two file listings, the vector store listing, and
one file listing per store. Nothing is created and nothing is deleted.

The Assistants API reached its shutdown date on 2026-08-26. Its objects went;
the files they referenced did not, because deleting an API does not delete
storage. `assistants` and `assistants_output` are still valid values of
`purpose` on the File object, so those files still enumerate and still count
against the project's storage ceiling.

One honesty note carried into the output. OpenAI's migration guide covers
assistants, threads and runs and says nothing whatsoever about files, vector
stores or purposes, so "a file in no surviving store has no owner" is an
inference from what is readable rather than a documented fact. What is
documented is that the two purposes remain valid, that vector stores are a
live resource, and that deleting a file removes it from every vector store.

The subtraction is only as good as the set being subtracted, so a store whose
file listing could not be read downgrades every verdict in the run.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("openai_orphaned_assistant_files")

FILES_URL = "https://api.openai.com/v1/files"
STORES_URL = "https://api.openai.com/v1/vector_stores"

PURPOSES = ("assistants", "assistants_output")
FINDINGS = ("orphan", "orphan-output", "subtraction-incomplete")

# The files listing accepts up to 10,000 per page; both vector store listings
# cap at 100. Copying the first number onto the second endpoint is how a
# referenced set silently loses everything after row 100.
FILE_PAGE = 10000
STORE_PAGE = 100


def file_row(body):
    """One file object, reduced. Pure."""
    body = body if isinstance(body, dict) else {}
    try:
        size = int(body.get("bytes"))
    except (TypeError, ValueError):
        size = 0
    try:
        created = int(body.get("created_at") or 0)
    except (TypeError, ValueError):
        created = 0
    return {"id": str(body.get("id") or ""),
            "filename": str(body.get("filename") or ""),
            "size": max(0, size),
            "purpose": str(body.get("purpose") or ""),
            "created_at": max(0, created)}


def referenced_ids(store_files):
    """The set to subtract. Pure.

    A vector_store.file object's own `id` is the underlying Files API id, so
    membership is one field rather than a join.
    """
    out = set()
    for item in store_files or []:
        if isinstance(item, dict):
            fid = str(item.get("id") or "")
            if fid:
                out.add(fid)
    return out


def human(size):
    """Binary units, one decimal. Pure."""
    try:
        n = float(size)
    except (TypeError, ValueError):
        return "0 B"
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if abs(n) < 1024 or unit == "TiB":
            return "%d B" % int(n) if unit == "B" else "%.1f %s" % (n, unit)
        n /= 1024.0
    return "%.1f TiB" % n


def age_days(created_at, now):
    """Age in days. Pure. The clock is an argument. None when undatable."""
    try:
        created, at = int(created_at), int(now)
    except (TypeError, ValueError):
        return None
    return (at - created) / 86400.0 if created > 0 else None


def class_state(rows, complete):
    """Grade the purpose class as a whole. Pure. Returns (state, detail)."""
    if not complete:
        return ("subtraction-unsafe",
                "the referenced set is incomplete, so no file in this class "
                "can be called an orphan")
    if not rows:
        return ("class-empty",
                "no file carries purpose assistants or assistants_output, so "
                "nothing was left behind here")
    return ("class-populated",
            "%d file(s) carry a purpose whose owning API no longer exists"
            % len(rows))


def classify_file(row, referenced, complete, now):
    """Grade one file. Pure. Completeness is tested before anything else.

    Deliberately first: when the referenced set is partial, a file that is in
    a store the script could not read is indistinguishable from an orphan, and
    the output of this script is a list of deletion commands.
    """
    row = row if isinstance(row, dict) else {}
    fid = str(row.get("id") or "")
    if not complete:
        return ("subtraction-incomplete",
                "%s: at least one vector store could not be listed, so this "
                "file cannot be called an orphan" % fid)
    if fid in (referenced or set()):
        return ("still-referenced",
                "%s: held by a live vector store, so file search under the "
                "Responses API still reads it" % fid)
    age = age_days(row.get("created_at"), now)
    when = ("created %.0f day(s) ago" % age) if age is not None else "undated"
    if row.get("purpose") == "assistants_output":
        return ("orphan-output",
                "%s: code interpreter output from a run that no longer exists, "
                "%s, %s" % (fid, human(row.get("size")), when))
    return ("orphan",
            "%s: no surviving vector store holds this id, %s, %s"
            % (fid, human(row.get("size")), when))


def summarise(graded):
    """Fold graded rows into per-state counts and bytes. Pure."""
    acc = {}
    for state, row in graded or []:
        cur = acc.setdefault(state, {"count": 0, "bytes": 0})
        cur["count"] += 1
        cur["bytes"] += int((row or {}).get("size") or 0)
    return acc


def repair_lines(state, orphan_count=0, orphan_bytes=0, unreadable=()):
    """The repair for one verdict. Pure. Printed, never performed."""
    if state in ("orphan", "orphan-output"):
        return ["%d confirmed orphan(s), %s. Archive anything you still want, "
                "then DELETE /v1/files/{file_id} one at a time. The delete "
                "also removes the file from every vector store holding it."
                % (orphan_count, human(orphan_bytes)),
                "re-upload future file search sources with purpose user_data "
                "and an expires_after policy, so the next class ages out on "
                "its own."]
    if state in ("subtraction-incomplete", "subtraction-unsafe"):
        return ["%d vector store(s) could not be listed: %s. Re-run with a key "
                "that can read them. A set difference against an incomplete "
                "set names files that are perfectly well referenced."
                % (len(unreadable), ", ".join(sorted(unreadable)) or "unknown")]
    if state == "class-empty":
        return []
    return []


def get_page(url, params, key, timeout=30):
    """One GET. Returns (body, ok). A non-200 is a fact, not an exception."""
    try:
        r = requests.get(url, params=params,
                         headers={"Authorization": "Bearer " + key},
                         timeout=timeout)
    except requests.RequestException as exc:
        log.debug("GET %s failed: %s", url, exc)
        return (None, False)
    if r.status_code != 200:
        log.debug("GET %s returned HTTP %s", url, r.status_code)
        return (None, False)
    try:
        return (r.json(), True)
    except ValueError:
        return (None, False)


def walk(url, key, params, page_size, max_pages):
    """Page any of these listings on `after`. Returns (items, ok)."""
    items, cursor, pages = [], None, 0
    while pages < max_pages:
        query = dict(params or {})
        query["limit"] = page_size
        if cursor:
            query["after"] = cursor
        body, ok = get_page(url, query, key)
        if not ok:
            return (items, False)
        data = (body or {}).get("data") or []
        pages += 1
        items.extend(data)
        if not data or (body or {}).get("has_more") is False:
            return (items, True)
        if "has_more" not in (body or {}) and len(data) < page_size:
            return (items, True)
        cursor = data[-1].get("id")
        if not cursor:
            return (items, True)
    return (items, False)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-pages", type=int, default=50,
                    help="page cap applied to every listing")
    ap.add_argument("--show", type=int, default=25,
                    help="how many individual files to print")
    args = ap.parse_args()

    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        log.error("set OPENAI_API_KEY to a project key set to Read Only. Every "
                  "call is a GET of /v1/files or /v1/vector_stores")
        return 2

    now = int(time.time())
    rows = []
    for purpose in PURPOSES:
        items, ok = walk(FILES_URL, key, {"purpose": purpose, "order": "asc"},
                         FILE_PAGE, args.max_pages)
        if not ok:
            log.error("the %s listing could not be read in full; nothing can "
                      "be concluded from a partial class", purpose)
            return 2
        rows.extend(file_row(item) for item in items)

    stores, stores_ok = walk(STORES_URL, key, {}, STORE_PAGE, args.max_pages)
    referenced, unreadable = set(), []
    for store in stores:
        sid = str((store or {}).get("id") or "")
        if not sid:
            continue
        items, ok = walk("%s/%s/files" % (STORES_URL, sid), key, {},
                         STORE_PAGE, args.max_pages)
        referenced |= referenced_ids(items)
        if not ok:
            unreadable.append(sid)
    complete = stores_ok and not unreadable

    log.info("%d vector store(s) read, %d referenced file id(s)",
             len(stores), len(referenced))
    counts = {p: sum(1 for r in rows if r["purpose"] == p) for p in PURPOSES}
    log.info("%d file(s) in the class: %d assistants, %d assistants_output, %s",
             len(rows), counts["assistants"], counts["assistants_output"],
             human(sum(r["size"] for r in rows)))
    log.info("  measured: two purpose listings, minus the ids held by every "
             "store read")
    log.info("  inferred: that a file in no surviving store has no owner. The "
             "migration guide documents nothing at all about files or vector "
             "stores")
    if not stores_ok:
        log.warning("  the vector store listing itself was truncated or failed")

    state, detail = class_state(rows, complete)
    (log.warning if state == "subtraction-unsafe" else log.info)(
        "%-20s %s", state, detail)

    graded = [(classify_file(row, referenced, complete, now)[0], row)
              for row in rows]
    shown = 0
    for row in rows:
        verdict, line = classify_file(row, referenced, complete, now)
        if shown < args.show:
            (log.warning if verdict in FINDINGS else log.info)(
                "%-20s %s", verdict, line)
            shown += 1

    totals = summarise(graded)
    orphans = totals.get("orphan", {"count": 0, "bytes": 0})
    outputs = totals.get("orphan-output", {"count": 0, "bytes": 0})
    findings = sum(totals.get(s, {}).get("count", 0) for s in FINDINGS)
    if orphans["count"] or outputs["count"]:
        for line in repair_lines("orphan",
                                 orphans["count"] + outputs["count"],
                                 orphans["bytes"] + outputs["bytes"]):
            log.warning("  repair: %s", line)
    if not complete:
        for line in repair_lines("subtraction-incomplete",
                                 unreadable=unreadable):
            log.warning("  repair: %s", line)

    log.info("%d finding(s)", findings)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "openai-orphaned-assistant-files.mjs",
"js": '''/**
 * Subtract the ids surviving vector stores hold from one dead purpose class.
 *
 * Read only. Four kinds of GET: two file listings, the vector store listing,
 * and one file listing per store. Nothing is created and nothing is deleted.
 *
 * The Assistants API reached its shutdown date on 2026-08-26. Its objects
 * went; the files they referenced did not. `assistants` and
 * `assistants_output` are still valid values of `purpose` on the File object.
 *
 * The subtraction is only as good as the set being subtracted, so a store
 * whose file listing could not be read downgrades every verdict in the run.
 */
const FILES_URL = 'https://api.openai.com/v1/files';
const STORES_URL = 'https://api.openai.com/v1/vector_stores';

export const PURPOSES = ['assistants', 'assistants_output'];
const FINDINGS = new Set(['orphan', 'orphan-output', 'subtraction-incomplete']);

// The files listing accepts up to 10,000 per page; both vector store listings
// cap at 100. Copying the first onto the second silently truncates the set.
const FILE_PAGE = 10000;
const STORE_PAGE = 100;

/** One file object, reduced. Pure. */
export function fileRow(body) {
  const row = (body && typeof body === 'object') ? body : {};
  const size = Number(row.bytes);
  const created = Number(row.created_at ?? 0);
  return {
    id: String(row.id ?? ''),
    filename: String(row.filename ?? ''),
    size: Number.isFinite(size) ? Math.max(0, Math.trunc(size)) : 0,
    purpose: String(row.purpose ?? ''),
    created_at: Number.isFinite(created) ? Math.max(0, Math.trunc(created)) : 0,
  };
}

/** The set to subtract. Pure. A store file's own id is the Files API id. */
export function referencedIds(storeFiles) {
  const out = new Set();
  for (const item of storeFiles ?? []) {
    if (item && typeof item === 'object') {
      const id = String(item.id ?? '');
      if (id) out.add(id);
    }
  }
  return out;
}

/** Binary units, one decimal. Pure. */
export function human(size) {
  let n = Number(size);
  if (!Number.isFinite(n)) return '0 B';
  for (const unit of ['B', 'KiB', 'MiB', 'GiB', 'TiB']) {
    if (Math.abs(n) < 1024 || unit === 'TiB') {
      return unit === 'B' ? `${Math.trunc(n)} B` : `${n.toFixed(1)} ${unit}`;
    }
    n /= 1024;
  }
  return `${n.toFixed(1)} TiB`;
}

/** Age in days. Pure. The clock is an argument. Null when undatable. */
export function ageDays(createdAt, now) {
  const created = Number(createdAt);
  const at = Number(now);
  if (!Number.isFinite(created) || !Number.isFinite(at) || created <= 0) return null;
  return (at - created) / 86400;
}

/** Grade the purpose class as a whole. Pure. */
export function classState(rows, complete) {
  if (!complete) {
    return ['subtraction-unsafe',
      'the referenced set is incomplete, so no file in this class can be called '
      + 'an orphan'];
  }
  if (!(rows ?? []).length) {
    return ['class-empty',
      'no file carries purpose assistants or assistants_output, so nothing was '
      + 'left behind here'];
  }
  return ['class-populated',
    `${rows.length} file(s) carry a purpose whose owning API no longer exists`];
}

/** Grade one file. Pure. Completeness is tested before anything else. */
export function classifyFile(row, referenced, complete, now) {
  const file = (row && typeof row === 'object') ? row : {};
  const id = String(file.id ?? '');
  if (!complete) {
    return ['subtraction-incomplete',
      `${id}: at least one vector store could not be listed, so this file cannot `
      + 'be called an orphan'];
  }
  if ((referenced ?? new Set()).has(id)) {
    return ['still-referenced',
      `${id}: held by a live vector store, so file search under the Responses API `
      + 'still reads it'];
  }
  const age = ageDays(file.created_at, now);
  const when = age === null ? 'undated' : `created ${age.toFixed(0)} day(s) ago`;
  if (file.purpose === 'assistants_output') {
    return ['orphan-output',
      `${id}: code interpreter output from a run that no longer exists, `
      + `${human(file.size)}, ${when}`];
  }
  return ['orphan',
    `${id}: no surviving vector store holds this id, ${human(file.size)}, ${when}`];
}

/** Fold graded rows into per-state counts and bytes. Pure. */
export function summarise(graded) {
  const acc = {};
  for (const [state, row] of graded ?? []) {
    const cur = acc[state] ?? { count: 0, bytes: 0 };
    cur.count += 1;
    cur.bytes += Number(row?.size ?? 0);
    acc[state] = cur;
  }
  return acc;
}

/** The repair for one verdict. Pure. Printed, never performed. */
export function repairLines(state, orphanCount = 0, orphanBytes = 0, unreadable = []) {
  if (state === 'orphan' || state === 'orphan-output') {
    return [`${orphanCount} confirmed orphan(s), ${human(orphanBytes)}. Archive `
      + 'anything you still want, then DELETE /v1/files/{file_id} one at a time. '
      + 'The delete also removes the file from every vector store holding it.',
    're-upload future file search sources with purpose user_data and an '
      + 'expires_after policy, so the next class ages out on its own.'];
  }
  if (state === 'subtraction-incomplete' || state === 'subtraction-unsafe') {
    return [`${(unreadable ?? []).length} vector store(s) could not be listed: `
      + `${[...(unreadable ?? [])].sort().join(', ') || 'unknown'}. Re-run with a `
      + 'key that can read them. A set difference against an incomplete set '
      + 'names files that are perfectly well referenced.'];
  }
  return [];
}

async function getPage(url, params, key) {
  const target = new URL(url);
  for (const [k, v] of Object.entries(params ?? {})) {
    target.searchParams.set(k, String(v));
  }
  try {
    const res = await fetch(target, { headers: { Authorization: `Bearer ${key}` } });
    if (res.status !== 200) return [null, false];
    return [await res.json().catch(() => null), true];
  } catch {
    return [null, false];
  }
}

async function walk(url, key, params, pageSize, maxPages) {
  const items = [];
  let cursor = null;
  let pages = 0;
  while (pages < maxPages) {
    const query = { ...(params ?? {}), limit: pageSize };
    if (cursor) query.after = cursor;
    const [body, ok] = await getPage(url, query, key);
    if (!ok) return [items, false];
    const data = (body ?? {}).data ?? [];
    pages += 1;
    items.push(...data);
    if (!data.length || (body ?? {}).has_more === false) return [items, true];
    if (!('has_more' in (body ?? {})) && data.length < pageSize) return [items, true];
    cursor = data[data.length - 1]?.id;
    if (!cursor) return [items, true];
  }
  return [items, false];
}

function args(argv) {
  const out = { maxPages: 50, show: 25 };
  for (let i = 0; i < argv.length; i += 1) {
    if (argv[i] === '--max-pages') out.maxPages = Number.parseInt(argv[i += 1], 10);
    else if (argv[i] === '--show') out.show = Number.parseInt(argv[i += 1], 10);
  }
  return out;
}

async function main() {
  const opts = args(process.argv.slice(2));
  const key = process.env.OPENAI_API_KEY;
  if (!key) {
    console.error('set OPENAI_API_KEY to a project key set to Read Only. Every '
      + 'call is a GET of /v1/files or /v1/vector_stores');
    process.exitCode = 2;
    return;
  }

  const now = Math.trunc(Date.now() / 1000);
  const rows = [];
  for (const purpose of PURPOSES) {
    const [items, ok] = await walk(FILES_URL, key, { purpose, order: 'asc' },
                                   FILE_PAGE, opts.maxPages);
    if (!ok) {
      console.error(`the ${purpose} listing could not be read in full; nothing `
        + 'can be concluded from a partial class');
      process.exitCode = 2;
      return;
    }
    for (const item of items) rows.push(fileRow(item));
  }

  const [stores, storesOk] = await walk(STORES_URL, key, {}, STORE_PAGE, opts.maxPages);
  const referenced = new Set();
  const unreadable = [];
  for (const store of stores) {
    const id = String(store?.id ?? '');
    if (!id) continue;
    const [items, ok] = await walk(`${STORES_URL}/${id}/files`, key, {},
                                   STORE_PAGE, opts.maxPages);
    for (const fid of referencedIds(items)) referenced.add(fid);
    if (!ok) unreadable.push(id);
  }
  const complete = storesOk && !unreadable.length;

  console.log(`${stores.length} vector store(s) read, ${referenced.size} `
    + 'referenced file id(s)');
  const counts = Object.fromEntries(PURPOSES.map((p) =>
    [p, rows.filter((r) => r.purpose === p).length]));
  console.log(`${rows.length} file(s) in the class: ${counts.assistants} assistants, `
    + `${counts.assistants_output} assistants_output, `
    + `${human(rows.reduce((a, r) => a + r.size, 0))}`);
  console.log('  measured: two purpose listings, minus the ids held by every store read');
  console.log('  inferred: that a file in no surviving store has no owner. The '
    + 'migration guide documents nothing at all about files or vector stores');
  if (!storesOk) console.log('  the vector store listing itself was truncated or failed');

  const [state, detail] = classState(rows, complete);
  console.log(`${state.padEnd(20)} ${detail}`);

  const graded = rows.map((row) => [classifyFile(row, referenced, complete, now)[0], row]);
  let shown = 0;
  for (const row of rows) {
    const [verdict, line] = classifyFile(row, referenced, complete, now);
    if (shown < opts.show) {
      console.log(`${verdict.padEnd(20)} ${line}`);
      shown += 1;
    }
  }

  const tot = summarise(graded);
  const orphans = tot.orphan ?? { count: 0, bytes: 0 };
  const outputs = tot['orphan-output'] ?? { count: 0, bytes: 0 };
  let findings = 0;
  for (const s of FINDINGS) findings += tot[s]?.count ?? 0;
  if (orphans.count || outputs.count) {
    for (const line of repairLines('orphan', orphans.count + outputs.count,
                                   orphans.bytes + outputs.bytes)) {
      console.log(`  repair: ${line}`);
    }
  }
  if (!complete) {
    for (const line of repairLines('subtraction-incomplete', 0, 0, unreadable)) {
      console.log(`  repair: ${line}`);
    }
  }
  console.log(`${findings} finding(s)`);
  process.exitCode = findings ? 1 : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) await main();
''',
"test_intro": "The third test is the one the whole script is built around, so read that one first: a single unreadable vector store has to turn every orphan in the run into <code>subtraction-incomplete</code>, and the same file that would otherwise be a deletion candidate must come back as one that cannot be called an orphan. Before it, the two ordinary outcomes: a file no store holds, graded separately depending on whether a person uploaded it or the code interpreter emitted it, and a file a live store still holds, which is not a finding and gets no repair. Then <code>referenced_ids</code>, asserted to read the vector-store file's own id and to survive a listing full of junk. Then the empty purpose class, which is a real answer rather than a blank. And last the repair lines, which have to name the vector-store side effect of a delete in the same sentence as the delete.",
"test_py_file": "test_openai_orphaned_assistant_files.py",
"test_py": '''from openai_orphaned_assistant_files import (age_days, class_state,
                                            classify_file, file_row, human,
                                            referenced_ids, repair_lines,
                                            summarise)

NOW = 1_800_000_000
DAY = 86400


def f(fid, size=1024, purpose="assistants", days_old=500):
    return file_row({"id": fid, "bytes": size, "purpose": purpose,
                     "filename": fid + ".pdf",
                     "created_at": NOW - int(days_old * DAY)})


def test_a_file_no_surviving_store_holds_is_the_finding():
    row = f("file-3ab", 43_200_512, days_old=511)
    state, detail = classify_file(row, set(), True, NOW)
    assert state == "orphan"
    assert "no surviving vector store holds this id" in detail
    assert "41.2 MiB" in detail and "511 day(s) ago" in detail
    lines = repair_lines(state, 1, 43_200_512)
    assert any("DELETE /v1/files/{file_id}" in line for line in lines)
    assert any("every vector store holding it" in line for line in lines)


def test_platform_generated_output_is_its_own_state():
    row = f("file-b19", 120_832, purpose="assistants_output", days_old=502)
    state, detail = classify_file(row, set(), True, NOW)
    assert state == "orphan-output"
    assert "code interpreter output" in detail
    assert "no longer exists" in detail
    # A file a live store still holds is not a finding at all.
    held, held_detail = classify_file(f("file-c04"), {"file-c04"}, True, NOW)
    assert held == "still-referenced"
    assert "still reads it" in held_detail
    assert repair_lines(held) == []


def test_one_unreadable_store_downgrades_every_verdict_in_the_run():
    row = f("file-3ab")
    # With a complete set this is a deletion candidate.
    assert classify_file(row, set(), True, NOW)[0] == "orphan"
    # With an incomplete one it is not, and the reason is stated.
    state, detail = classify_file(row, set(), False, NOW)
    assert state == "subtraction-incomplete"
    assert "could not be listed" in detail
    assert "cannot be called an orphan" in detail
    # Not even a file that really is referenced escapes the downgrade, because
    # the script cannot tell the two apart once the set is partial.
    assert classify_file(f("file-c04"), {"file-c04"}, False, NOW)[0] \\
        == "subtraction-incomplete"
    assert class_state([row], False)[0] == "subtraction-unsafe"
    lines = repair_lines("subtraction-incomplete", unreadable=["vs_b2", "vs_a1"])
    assert "vs_a1, vs_b2" in lines[0]
    assert "perfectly well referenced" in lines[0]


def test_referenced_ids_reads_the_store_files_own_id():
    ids = referenced_ids([{"id": "file-c04", "object": "vector_store.file",
                           "vector_store_id": "vs_a1", "status": "completed"},
                          {"id": "file-d15", "status": "failed"},
                          {"id": ""}, None, "not-an-object", {}])
    assert ids == {"file-c04", "file-d15"}
    assert referenced_ids(None) == set()
    # A failed attach still holds the id, so the file is still referenced.
    assert classify_file(f("file-d15"), ids, True, NOW)[0] == "still-referenced"


def test_an_empty_purpose_class_is_an_answer_and_not_a_blank():
    state, detail = class_state([], True)
    assert state == "class-empty"
    assert "nothing was left behind" in detail
    assert repair_lines(state) == []
    full, full_detail = class_state([f("file-1"), f("file-2")], True)
    assert full == "class-populated"
    assert "2 file(s)" in full_detail
    assert "no longer exists" in full_detail


def test_the_folds_and_the_formatting_survive_junk():
    graded = [("orphan", f("file-1", 1024)),
              ("orphan", f("file-2", 2048)),
              ("still-referenced", f("file-3", 4096))]
    assert summarise(graded)["orphan"] == {"count": 2, "bytes": 3072}
    assert summarise([])== {}
    assert file_row(None)["id"] == ""
    assert file_row({"bytes": "nope", "created_at": "nope"})["size"] == 0
    assert age_days(0, NOW) is None and age_days("x", NOW) is None
    assert human(1024) == "1.0 KiB" and human(None) == "0 B"
''',
"test_js_file": "openai-orphaned-assistant-files.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { ageDays, classState, classifyFile, fileRow, human, referencedIds,
         repairLines, summarise } from './openai-orphaned-assistant-files.mjs';

const NOW = 1_800_000_000;
const DAY = 86400;

const f = (id, size = 1024, purpose = 'assistants', daysOld = 500) => fileRow({
  id, bytes: size, purpose, filename: `${id}.pdf`,
  created_at: NOW - Math.trunc(daysOld * DAY),
});

test('a file no surviving store holds is the finding', () => {
  const row = f('file-3ab', 43200512, 'assistants', 511);
  const [state, detail] = classifyFile(row, new Set(), true, NOW);
  assert.equal(state, 'orphan');
  assert.ok(detail.includes('no surviving vector store holds this id'));
  assert.ok(detail.includes('41.2 MiB') && detail.includes('511 day(s) ago'));
  const lines = repairLines(state, 1, 43200512);
  assert.ok(lines.some((l) => l.includes('DELETE /v1/files/{file_id}')));
  assert.ok(lines.some((l) => l.includes('every vector store holding it')));
});

test('platform generated output is its own state', () => {
  const row = f('file-b19', 120832, 'assistants_output', 502);
  const [state, detail] = classifyFile(row, new Set(), true, NOW);
  assert.equal(state, 'orphan-output');
  assert.ok(detail.includes('code interpreter output'));
  assert.ok(detail.includes('no longer exists'));
  const [held, heldDetail] = classifyFile(f('file-c04'), new Set(['file-c04']), true, NOW);
  assert.equal(held, 'still-referenced');
  assert.ok(heldDetail.includes('still reads it'));
  assert.deepEqual(repairLines(held), []);
});

test('one unreadable store downgrades every verdict in the run', () => {
  const row = f('file-3ab');
  assert.equal(classifyFile(row, new Set(), true, NOW)[0], 'orphan');
  const [state, detail] = classifyFile(row, new Set(), false, NOW);
  assert.equal(state, 'subtraction-incomplete');
  assert.ok(detail.includes('could not be listed'));
  assert.ok(detail.includes('cannot be called an orphan'));
  assert.equal(classifyFile(f('file-c04'), new Set(['file-c04']), false, NOW)[0],
               'subtraction-incomplete');
  assert.equal(classState([row], false)[0], 'subtraction-unsafe');
  const lines = repairLines('subtraction-incomplete', 0, 0, ['vs_b2', 'vs_a1']);
  assert.ok(lines[0].includes('vs_a1, vs_b2'));
  assert.ok(lines[0].includes('perfectly well referenced'));
});

test('referencedIds reads the store files own id', () => {
  const ids = referencedIds([{ id: 'file-c04', object: 'vector_store.file',
                               vector_store_id: 'vs_a1', status: 'completed' },
                             { id: 'file-d15', status: 'failed' },
                             { id: '' }, null, 'not-an-object', {}]);
  assert.deepEqual([...ids].sort(), ['file-c04', 'file-d15']);
  assert.equal(referencedIds(null).size, 0);
  assert.equal(classifyFile(f('file-d15'), ids, true, NOW)[0], 'still-referenced');
});

test('an empty purpose class is an answer and not a blank', () => {
  const [state, detail] = classState([], true);
  assert.equal(state, 'class-empty');
  assert.ok(detail.includes('nothing was left behind'));
  assert.deepEqual(repairLines(state), []);
  const [full, fullDetail] = classState([f('file-1'), f('file-2')], true);
  assert.equal(full, 'class-populated');
  assert.ok(fullDetail.includes('2 file(s)'));
  assert.ok(fullDetail.includes('no longer exists'));
});

test('the folds and the formatting survive junk', () => {
  const graded = [['orphan', f('file-1', 1024)],
                  ['orphan', f('file-2', 2048)],
                  ['still-referenced', f('file-3', 4096)]];
  assert.deepEqual(summarise(graded).orphan, { count: 2, bytes: 3072 });
  assert.deepEqual(summarise([]), {});
  assert.equal(fileRow(null).id, '');
  assert.equal(fileRow({ bytes: 'nope', created_at: 'nope' }).size, 0);
  assert.equal(ageDays(0, NOW), null);
  assert.equal(ageDays('x', NOW), null);
  assert.equal(human(1024), '1.0 KiB');
  assert.equal(human(null), '0 B');
});
''',
"faq": [
 ("Does OpenAI actually document that files survive the Assistants shutdown?",
  "No, and this is the one place the note deliberately stops short of the research it started from. The migration guide covers assistants, threads and runs; it does not contain the words file, vector store or purpose anywhere. So the survival of these files is something you observe rather than something you can cite. What is documented is enough to build the check: assistants and assistants_output are still enumerated as valid purposes on the File object, vector stores are a live non-beta resource with their own reference, and the delete call is documented to remove a file from all vector stores. The script prints its inference on its own labelled line so the two never get confused."),
 ("What is the difference between this and the note on the Assistants shutdown?",
  "That one asks whether GET /v1/assistants still answers for your organization, grades the status code against a control path on the same key, and its finding is that you still have grace access to an API that is over. It is a question about access, and its answer changes from week to week. This one assumes the endpoint is gone and asks what it left behind. It would produce the same findings on an organization that migrated cleanly two years ago, because storage does not care when you migrated."),
 ("Why does one unreadable vector store invalidate the whole run?",
  "Because the output of this script is a list of files to delete, and a file that lives in a store the script could not read is indistinguishable from a file that lives in no store at all. Skipping the unreadable store would quietly move its contents into the orphan column. So the completeness test runs before every other test in the classifier, the whole run is graded subtraction-incomplete, and no deletion command is printed. There is a test that fails if that ordering is ever changed."),
 ("Some of these files are attached to a store but the attach failed. Are they orphans?",
  "No, and the script counts them as referenced on purpose. A vector_store.file object with status failed still carries the file id, so the file is still owned by a store, still deletable through that store, and still visible to whoever is fixing the ingest. Deleting it as an orphan would remove the evidence somebody needs. The failed attach is its own problem and there is a separate note for it."),
 ("What should we upload these as in future?",
  "purpose user_data, with an expires_after policy set at upload time. The assistants purpose was tied to an API that no longer exists, so anything still using it is writing into a class with no owner from the first second. user_data is the general-purpose value, and an expiry means the next accumulation ages out on its own rather than waiting for somebody to write a script like this one in two years."),
],
"related": [REL_ASSTSHUT, REL_QUOTA, REL_VSATTACH],
"citations": [CITE_OAI_MIGRATE, CITE_OAI_DEPRECATIONS, CITE_OAI_FILES, CITE_OAI_VS_FILES],
},
{
"slug": "expired-files-still-referenced",
"title": "An expired file still answers metadata and fails every use",
"description": "Content stops being retrievable at expires_at while metadata answers for 30 more days. Check the ids your app holds, up to 100 per request, and read the date.",
"h1": "An expired file still answers metadata and fails every use",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["anthropic file 404 not_found_error content expired",
             "claude files api expires_at in the past",
             "expires_in_seconds cannot be changed after upload",
             "anthropic files ids[] lookup up to 100",
             "files-api-2025-04-14 expires_at not returned"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Needs ANTHROPIC_API_KEY, a key with access to the workspace that owns the files, and a file of the file ids your application still references. Every call is a GET of /v1/files with an ids[] filter, and no file content is ever downloaded.",
"lead": "The document pipeline has been fine for months and this morning a batch of requests started failing on a handful of customers. Not all of them, and not consistently. The error is a 404, which sends everybody looking for a typo, and the id is right &mdash; you can paste it into a metadata call and get a filename, a size and a created date back. The file exists. It answers. And every request that tries to actually use it fails before inference, because what came back was the label and the thing behind it went away eleven days ago.",
"short_answer": """<p>Read the date, not the status code. Anthropic's <code>expires_in_seconds</code> is set once at upload &mdash; between 3,600 and 7,776,000 seconds, one hour to ninety days &mdash; and <strong>cannot be changed afterwards</strong>. After the moment it names, the content stops being retrievable, the bytes are released from your storage quota, and <strong>the metadata remains readable for up to thirty days</strong> while the file keeps appearing in list responses. So an existence check against the listing or the metadata endpoint returns a confident yes for a file that will fail every real use.</p>
<p>Ask about the ids you actually hold. <code>GET /v1/files</code> accepts up to <strong>100 <code>ids[]</code> values</strong> in one request, after de-duplication, and that form is <em>mutually exclusive with <code>page</code> and <code>limit</code></em> and always returns a single page. Ids that do not resolve to a visible file &mdash; including deleted ones &mdash; are <strong>silently omitted from <code>data</code></strong>, so comparing what came back against what you asked for is itself a finding rather than an error path.</p>
<p>Then grade each returned object on <code>expires_at</code>, which is an RFC 3339 string or null. In the past is a dead reference. Inside your warning window is a deadline you cannot move, because there is nothing to extend. Null means the file is permanent, which is fine here and is somebody else's problem in the note about the storage total.</p>
<p>One header decides whether any of this works. Send <code>anthropic-beta: files-api-2025-04-14</code> and the response reverts to the older shape, in which <strong><code>expires_at</code> is not returned at all</strong>. The script sends no beta header and, if a response comes back without the field, it reports that the check could not run rather than reporting that nothing is expiring.</p>
<p>The repair for an expired file is not a repair. The content is gone. What the script prints is the reference to remove, and the deletion that clears the metadata immediately instead of waiting out the thirty-day window.</p>""",
"problem": """<p>Expiry on this API is a decision made once, at upload, by whichever piece of code happened to do the upload. It is an integer in a request body. There is no policy object to inspect later, no way to extend it, and nothing that reminds anybody it was set &mdash; and if the uploading service and the consuming service are different teams, the consuming side may not know an expiry exists at all.</p>
<p>What turns that into an outage is the gap between two lifetimes. The content and the metadata do not expire together. At <code>expires_at</code> the bytes stop being retrievable and leave your storage quota; the metadata carries on answering for up to thirty days after that, and the file carries on appearing in list responses for the same window. Every cheap way of asking "does this file still exist" therefore says yes during precisely the period when the answer that matters is no.</p>
<p>The failure lands in the worst place, too. It is not a download that fails &mdash; it is the inference request. A Messages call referencing an expired file fails before the model sees anything, so what a user experiences is not a missing attachment but a request that did not happen. And because expiry is per file and set per upload, the failures arrive spread out and uncorrelated, one customer at a time, which reads as flakiness rather than as a clock.</p>
<p>The quiet accomplice is a beta header. The Files API left beta, and requests still sending <code>files-api-2025-04-14</code> get the older response shape, which does not include <code>expires_at</code> at all. Code written against that shape cannot see the field it would need to prevent any of this, and it does not error &mdash; it simply never has the date. SDK versions dropped the header independently of each other, so which shape you are on can change under a routine dependency bump.</p>""",
"why": """<p><strong>Existence is the wrong question and the API will answer it wrongly on purpose.</strong> Metadata outliving content is a deliberate, documented design: it gives you a window in which you can still find out what a file <em>was</em>. But it means a truthiness check on the metadata endpoint is actively misleading for up to thirty days per file. The only reliable test is the date, which is why every state this script emits is a statement about <code>expires_at</code> and none of them is a statement about whether the object came back.</p>
<p><strong>The ids you hold are the whole input, and the ids form has its own rules.</strong> Up to 100 per request after de-duplication, mutually exclusive with <code>page</code> and <code>limit</code>, always a single page. A script that sends 140 ids, or sends a <code>limit</code> alongside them, is not making a slightly worse request &mdash; it is making a request with different semantics. So the chunking is a pure function with a test on it, and the fetch sends nothing but the ids.</p>
<p><strong>Silent omission is a finding, not an error.</strong> An id that has passed even the metadata window, or that was deleted, is simply absent from <code>data</code> with no error and no marker. That absence is the strongest signal in the whole run: the file is gone past recovery and your record of it is stale. Reading it requires the script to keep the request list and diff it against the response, which is a line of code and the difference between a report and a shrug.</p>
<p><strong>There is nothing to extend, so the repair cannot be the obvious one.</strong> Expiry is fixed at upload and immutable, which rules out the fix everybody reaches for first. What is left is re-upload and swap the id, or upload without an expiry and accept that the file then stays on the storage total forever. The script prints both, and it never suggests changing a value that cannot be changed.</p>
<p><strong>A missing field has to be its own outcome, because otherwise the run looks clean.</strong> If a beta header is in play the objects come back with no <code>expires_at</code> at all, and a naive script reads that as "nothing is expiring" and prints a clean bill of health on an account full of dying references. So a response with no such field produces <code>expiry-not-reported</code>, which is a finding, and the repair names the header. There is also a third shape to know about: with <code>managed-agents-2026-04-01</code> and no files beta header, the old cursors and the new ones coexist.</p>
<p><strong>This is one file's clock, and the note next door is a whole index's.</strong> The published vector store expiry note reads a store's <code>expires_after</code> policy and warns that the store will delete every file inside it. Same idea, different scale, different platform, and a different repair: there you clear a policy on an object that still exists, here there is no policy object and no clearing.</p>""",
"steps": [
 {"h": "Export the file ids your application still references",
  "body": """<p>One per line, out of the table or the object store where you record them. This is the input the note is built on: the question is not what is in your workspace, it is which of the ids you are still handing to the Messages API are already dead. Blanks and <code>#</code> comments are ignored so an export from a query works unedited.</p>"""},
 {"h": "Use a key with access to that workspace, and send no beta header",
  "body": """<p>The Files API is workspace-scoped: any key with access to the workspace can read its files. Send no <code>anthropic-beta</code> value. With <code>files-api-2025-04-14</code> the response omits <code>expires_at</code> entirely and the whole check silently stops working.</p>"""},
 {"h": "Ask in batches of 100 ids and nothing else",
  "body": """<p><code>GET /v1/files?ids[]=…</code>, at most 100 per request after de-duplication. Do not add <code>limit</code> or <code>page</code>: they are mutually exclusive with <code>ids</code>, and the ids form always returns one page.</p>"""},
 {"h": "Diff what came back against what you asked for",
  "body": """<p>Unresolvable ids are silently omitted rather than reported. The set difference between the batch you sent and the ids in <code>data</code> is the list of files that are gone past even the metadata window, or deleted.</p>"""},
 {"h": "Grade the date and take a repair that is not an extension",
  "body": """<p>Past is dead, near is a deadline you cannot move, null is permanent. For anything expired, the printed repair removes the reference and offers <code>DELETE /v1/files/{file_id}</code>, which clears the metadata immediately instead of leaving it to answer for another month.</p>"""},
],
"verify": """<p>Fix one expired reference by re-uploading the source and swapping the id, then re-run with the same file. That row should move from <code>expired</code> to <code>live</code> with a printed number of days on it, and the count of ids missing from the response should not change, because those were already unrecoverable before you started. Put it on a schedule at roughly a third of your shortest expiry window: with ninety-day uploads that is monthly, and with one-day uploads a scheduled audit is the wrong tool and a check at the call site is the right one.</p>
<pre><code class="language-bash">python3 anthropic_expired_file_refs.py --ids referenced-files.txt --warn-days 7
# 214 id(s) asked in 3 batch(es) of at most 100, 209 returned
# expired              file_011a: expired 11.3 day(s) ago; the metadata still
#                      answers and every actual use of this id fails
#   repair: the content is gone and cannot be restored. Remove the reference,
#           re-upload the source if you still need it, and DELETE
#           /v1/files/{file_id} to clear the metadata immediately rather than
#           waiting out the 30 day window.
# expiring             file_02b7: expires in 4.1 day(s), and the expiry cannot
#                      be extended
#   repair: expires_in_seconds is set once at upload and cannot be changed, so
#           there is nothing to extend. Re-upload before the date and swap the
#           id, or upload with no expiry and accept that it stays on the quota.
# gone                 file_03c9: not returned by the ids lookup, so it is past
#                      even the metadata window or was deleted
# no-expiry            file_04d2: no expiry was set, so this one is permanent
# live                 file_05e4: live, expires in 61.8 day(s)
# 5 id(s) missing from the response, 7 finding(s)</code></pre>""",
"code_intro": "One GET per batch of a hundred ids, and seven pure functions. <code>parse_ids</code>, which reads an export nobody tidied; <code>chunks</code>, which de-duplicates and caps at the documented hundred because the <code>ids</code> form has different semantics from the paged one; <code>epoch</code>, which turns the RFC 3339 <code>expires_at</code> into seconds and returns zero rather than a guess for anything it cannot parse; <code>file_row</code>, which records separately whether the field was <em>absent</em> as opposed to null, because those mean two completely different things here; <code>missing_ids</code>, the diff that reads the API's silent omission as a result; <code>classify_id</code>, which grades a date and treats a missing field as a broken check rather than as good news; and <code>repair_lines</code>, which never proposes extending an expiry that cannot be extended.",
"py_file": "anthropic_expired_file_refs.py",
"py": '''"""Check the file ids an application holds against the expiry on each one.

Read only. GET /v1/files with an ids[] filter and nothing else. No file content
is ever downloaded, nothing is uploaded and nothing is deleted.

expires_in_seconds is set once at upload, between 3600 and 7776000 seconds, and
cannot be changed afterwards. After expires_at the content stops being
retrievable and the bytes leave the storage quota, but the metadata remains
readable for up to 30 days and the file keeps appearing in list responses. So
an existence check answers yes for a file that fails every real use.

The ids form accepts at most 100 values after de-duplication, is mutually
exclusive with page and limit, and always returns a single page. Ids that do
not resolve are silently omitted from data, which is read here as a result
rather than as an error.

No anthropic-beta header is sent. With files-api-2025-04-14 the response omits
expires_at entirely, and a run that cannot see the field says so instead of
reporting that nothing is expiring.
"""
import argparse
import calendar
import logging
import os
import re
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("anthropic_expired_file_refs")

BASE_URL = "https://api.anthropic.com/v1/files"

# Documented: at most 100 ids per request, after de-duplication.
ID_BATCH = 100
# Documented: metadata stays readable for up to 30 days past expires_at.
METADATA_WINDOW_DAYS = 30

FINDINGS = ("expired", "expiring", "gone", "expiry-not-reported")

_RFC3339 = re.compile(r"^(\\d{4})-(\\d{2})-(\\d{2})[Tt ](\\d{2}):(\\d{2}):(\\d{2})"
                      r"(?:\\.\\d+)?(Z|z|[+-]\\d{2}:?\\d{2})?$")


def parse_ids(text):
    """File ids from an export nobody tidied. Pure. Blanks and repeats dropped."""
    seen = []
    for line in str(text or "").splitlines():
        item = line.split("#", 1)[0].strip()
        if item and item not in seen:
            seen.append(item)
    return seen


def chunks(ids, size=ID_BATCH):
    """Batches of at most `size` unique ids. Pure.

    The cap is not a performance choice. The ids form is documented at 100
    values after de-duplication and is mutually exclusive with page and limit,
    so a longer list is a different request rather than a slower one.
    """
    try:
        size = max(1, min(int(size), ID_BATCH))
    except (TypeError, ValueError):
        size = ID_BATCH
    unique, out = [], []
    for item in ids or []:
        item = str(item or "").strip()
        if item and item not in unique:
            unique.append(item)
    for i in range(0, len(unique), size):
        out.append(unique[i:i + size])
    return out


def epoch(value):
    """RFC 3339 to seconds. Pure. Zero for anything unparseable, never a guess."""
    if value is None or value == "" or isinstance(value, bool):
        return 0
    if isinstance(value, (int, float)):
        try:
            return max(0, int(value))
        except (TypeError, ValueError, OverflowError):
            return 0
    m = _RFC3339.match(str(value).strip())
    if not m:
        return 0
    try:
        base = calendar.timegm(tuple(int(g) for g in m.groups()[:6]) + (0, 0, 0))
    except (TypeError, ValueError):
        return 0
    off = m.group(7)
    if off and off not in ("Z", "z"):
        digits = off[1:].replace(":", "")
        shift = int(digits[:2]) * 3600 + int(digits[2:4]) * 60
        base -= shift if off[0] == "+" else -shift
    return max(0, base)


def file_row(body):
    """One file object, reduced. Pure.

    `expiry_reported` records whether the key was present at all, which is a
    different fact from the key being null. Absent means the response shape
    does not carry expiry and this check cannot run; null means the file was
    uploaded without one and is permanent.
    """
    body = body if isinstance(body, dict) else {}
    try:
        size = int(body.get("size_bytes"))
    except (TypeError, ValueError):
        size = 0
    return {"id": str(body.get("id") or ""),
            "filename": str(body.get("filename") or ""),
            "size": max(0, size),
            "created_at": epoch(body.get("created_at")),
            "expires_at": epoch(body.get("expires_at")) or None,
            "expiry_reported": "expires_at" in body,
            "downloadable": bool(body.get("downloadable"))}


def missing_ids(requested, returned):
    """Ids asked for and not answered. Pure. Order preserved.

    Unresolvable ids are silently omitted from data with no error and no
    marker, so this diff is the only way the omission becomes a result.
    """
    have = {str(r or "") for r in returned or []}
    return [str(r) for r in requested or [] if str(r) not in have]


def human(size):
    """Binary units, one decimal. Pure."""
    try:
        n = float(size)
    except (TypeError, ValueError):
        return "0 B"
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if abs(n) < 1024 or unit == "TiB":
            return "%d B" % int(n) if unit == "B" else "%.1f %s" % (n, unit)
        n /= 1024.0
    return "%.1f TiB" % n


def classify_id(row, now, warn_days):
    """Grade one referenced id. Pure. Returns (state, detail).

    `row` is None for an id the API declined to return at all.
    """
    if row is None:
        return ("gone", "not returned by the ids lookup, so it is past even "
                        "the %d day metadata window or was deleted"
                        % METADATA_WINDOW_DAYS)
    if not row.get("expiry_reported"):
        return ("expiry-not-reported",
                "the object came back with no expires_at field, so this check "
                "could not run")
    expires = row.get("expires_at")
    if not expires:
        return ("no-expiry", "no expiry was set, so this one is permanent")
    left = (int(expires) - int(now)) / 86400.0
    if left <= 0:
        return ("expired",
                "expired %.1f day(s) ago; the metadata still answers and every "
                "actual use of this id fails" % abs(left))
    if left <= float(warn_days):
        return ("expiring",
                "expires in %.1f day(s), and the expiry cannot be extended" % left)
    return ("live", "live, expires in %.1f day(s)" % left)


def repair_lines(state):
    """The repair for one verdict. Pure. Printed, never performed."""
    if state == "expired":
        return ["the content is gone and cannot be restored. Remove the "
                "reference, re-upload the source if you still need it, and "
                "DELETE /v1/files/{file_id} to clear the metadata immediately "
                "rather than waiting out the %d day window."
                % METADATA_WINDOW_DAYS]
    if state == "expiring":
        return ["expires_in_seconds is set once at upload and cannot be "
                "changed, so there is nothing to extend. Re-upload before the "
                "date and swap the id, or upload with no expiry and accept "
                "that it stays on the storage quota."]
    if state == "gone":
        return ["this id resolves to nothing at all. Treat the record as stale "
                "and stop passing it, because no read will recover the file."]
    if state == "expiry-not-reported":
        return ["drop the anthropic-beta: files-api-2025-04-14 header. With it "
                "the response omits expires_at entirely and reverts to "
                "before_id and after_id paging, so this check cannot run."]
    if state == "no-expiry":
        return ["nothing to do here, but note that a file with no expiry never "
                "leaves the storage total either."]
    return []


def fetch_batch(batch, key, timeout=30):
    """One GET with an ids[] filter. Returns (rows, ok).

    No limit and no page: both are mutually exclusive with ids, and the ids
    form always returns a single page. No beta header either, because with one
    the response would not carry expires_at at all.
    """
    params = [("ids[]", fid) for fid in batch]
    headers = {"x-api-key": key, "anthropic-version": "2023-06-01"}
    try:
        r = requests.get(BASE_URL, params=params, headers=headers, timeout=timeout)
    except requests.RequestException as exc:
        log.error("ids lookup failed: %s", exc)
        return ([], False)
    if r.status_code != 200:
        log.error("ids lookup returned HTTP %s", r.status_code)
        return ([], False)
    try:
        body = r.json()
    except ValueError:
        return ([], False)
    return ([file_row(item) for item in (body.get("data") or [])], True)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ids", required=True,
                    help="file of file ids your application references")
    ap.add_argument("--warn-days", type=float, default=7.0,
                    help="days of remaining life that count as a finding")
    args = ap.parse_args()

    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        log.error("set ANTHROPIC_API_KEY to a key with access to the workspace "
                  "that owns these files. Every call is a GET of /v1/files")
        return 2
    try:
        with open(args.ids, "r", encoding="utf-8") as fh:
            wanted = parse_ids(fh.read())
    except OSError as exc:
        log.error("could not read %s: %s", args.ids, exc)
        return 2
    if not wanted:
        log.error("no file ids in %s. This note is about the ids your "
                  "application holds, not about the workspace listing", args.ids)
        return 2

    now = int(time.time())
    batches = chunks(wanted)
    rows, missing = [], []
    for batch in batches:
        got, ok = fetch_batch(batch, key)
        if not ok:
            log.error("a batch could not be read, so nothing is concluded")
            return 2
        rows.extend(got)
        missing.extend(missing_ids(batch, [r["id"] for r in got]))

    log.info("%d id(s) asked in %d batch(es) of at most %d, %d returned",
             len(wanted), len(batches), ID_BATCH, len(rows))

    findings = 0
    for row in rows:
        state, detail = classify_id(row, now, args.warn_days)
        emit = log.warning if state in FINDINGS else log.info
        emit("%-20s %s: %s", state, row["id"], detail)
        for line in repair_lines(state):
            emit("  repair: %s", line)
        if state in FINDINGS:
            findings += 1
    for fid in missing:
        state, detail = classify_id(None, now, args.warn_days)
        log.warning("%-20s %s: %s", state, fid, detail)
        for line in repair_lines(state):
            log.warning("  repair: %s", line)
        findings += 1

    log.info("%d id(s) missing from the response, %d finding(s)",
             len(missing), findings)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "anthropic-expired-file-refs.mjs",
"js": '''/**
 * Check the file ids an application holds against the expiry on each one.
 *
 * Read only. GET /v1/files with an ids[] filter and nothing else. No file
 * content is ever downloaded, nothing is uploaded and nothing is deleted.
 *
 * expires_in_seconds is set once at upload and cannot be changed. After
 * expires_at the content stops being retrievable and the bytes leave the
 * storage quota, while the metadata remains readable for up to 30 days.
 *
 * The ids form accepts at most 100 values after de-duplication, is mutually
 * exclusive with page and limit, and silently omits ids that do not resolve.
 *
 * No anthropic-beta header is sent: with files-api-2025-04-14 the response
 * omits expires_at entirely and this check cannot run.
 */
import { readFile } from 'node:fs/promises';

const BASE_URL = 'https://api.anthropic.com/v1/files';

export const ID_BATCH = 100;
export const METADATA_WINDOW_DAYS = 30;

const FINDINGS = new Set(['expired', 'expiring', 'gone', 'expiry-not-reported']);

/** File ids from an export nobody tidied. Pure. */
export function parseIds(text) {
  const seen = [];
  for (const line of String(text ?? '').split('\\n')) {
    const item = line.split('#')[0].trim();
    if (item && !seen.includes(item)) seen.push(item);
  }
  return seen;
}

/** Batches of at most `size` unique ids, capped at the documented 100. Pure. */
export function chunks(ids, size = ID_BATCH) {
  let step = Number.parseInt(size, 10);
  if (!Number.isFinite(step)) step = ID_BATCH;
  step = Math.max(1, Math.min(step, ID_BATCH));
  const unique = [];
  for (const raw of ids ?? []) {
    const item = String(raw ?? '').trim();
    if (item && !unique.includes(item)) unique.push(item);
  }
  const out = [];
  for (let i = 0; i < unique.length; i += step) out.push(unique.slice(i, i + step));
  return out;
}

/** RFC 3339 to seconds. Pure. Zero for anything unparseable, never a guess. */
export function epoch(value) {
  if (value === null || value === undefined || value === '' || typeof value === 'boolean') {
    return 0;
  }
  if (typeof value === 'number') {
    return Number.isFinite(value) ? Math.max(0, Math.trunc(value)) : 0;
  }
  const ms = Date.parse(String(value).trim());
  return Number.isFinite(ms) ? Math.max(0, Math.trunc(ms / 1000)) : 0;
}

/** One file object, reduced. Pure. Absent expires_at is not null expires_at. */
export function fileRow(body) {
  const row = (body && typeof body === 'object') ? body : {};
  const size = Number(row.size_bytes);
  const expires = epoch(row.expires_at);
  return {
    id: String(row.id ?? ''),
    filename: String(row.filename ?? ''),
    size: Number.isFinite(size) ? Math.max(0, Math.trunc(size)) : 0,
    created_at: epoch(row.created_at),
    expires_at: expires || null,
    expiry_reported: Object.prototype.hasOwnProperty.call(row, 'expires_at'),
    downloadable: Boolean(row.downloadable),
  };
}

/** Ids asked for and not answered. Pure. Order preserved. */
export function missingIds(requested, returned) {
  const have = new Set((returned ?? []).map((r) => String(r ?? '')));
  return (requested ?? []).map(String).filter((r) => !have.has(r));
}

/** Binary units, one decimal. Pure. */
export function human(size) {
  let n = Number(size);
  if (!Number.isFinite(n)) return '0 B';
  for (const unit of ['B', 'KiB', 'MiB', 'GiB', 'TiB']) {
    if (Math.abs(n) < 1024 || unit === 'TiB') {
      return unit === 'B' ? `${Math.trunc(n)} B` : `${n.toFixed(1)} ${unit}`;
    }
    n /= 1024;
  }
  return `${n.toFixed(1)} TiB`;
}

/** Grade one referenced id. Pure. `row` is null for an id never returned. */
export function classifyId(row, now, warnDays) {
  if (row === null || row === undefined) {
    return ['gone', `not returned by the ids lookup, so it is past even the `
      + `${METADATA_WINDOW_DAYS} day metadata window or was deleted`];
  }
  if (!row.expiry_reported) {
    return ['expiry-not-reported',
      'the object came back with no expires_at field, so this check could not run'];
  }
  if (!row.expires_at) return ['no-expiry', 'no expiry was set, so this one is permanent'];
  const left = (Number(row.expires_at) - Number(now)) / 86400;
  if (left <= 0) {
    return ['expired', `expired ${Math.abs(left).toFixed(1)} day(s) ago; the `
      + 'metadata still answers and every actual use of this id fails'];
  }
  if (left <= Number(warnDays)) {
    return ['expiring',
      `expires in ${left.toFixed(1)} day(s), and the expiry cannot be extended`];
  }
  return ['live', `live, expires in ${left.toFixed(1)} day(s)`];
}

/** The repair for one verdict. Pure. Printed, never performed. */
export function repairLines(state) {
  if (state === 'expired') {
    return ['the content is gone and cannot be restored. Remove the reference, '
      + 're-upload the source if you still need it, and DELETE /v1/files/{file_id} '
      + `to clear the metadata immediately rather than waiting out the `
      + `${METADATA_WINDOW_DAYS} day window.`];
  }
  if (state === 'expiring') {
    return ['expires_in_seconds is set once at upload and cannot be changed, so '
      + 'there is nothing to extend. Re-upload before the date and swap the id, '
      + 'or upload with no expiry and accept that it stays on the storage quota.'];
  }
  if (state === 'gone') {
    return ['this id resolves to nothing at all. Treat the record as stale and '
      + 'stop passing it, because no read will recover the file.'];
  }
  if (state === 'expiry-not-reported') {
    return ['drop the anthropic-beta: files-api-2025-04-14 header. With it the '
      + 'response omits expires_at entirely and reverts to before_id and after_id '
      + 'paging, so this check cannot run.'];
  }
  if (state === 'no-expiry') {
    return ['nothing to do here, but note that a file with no expiry never leaves '
      + 'the storage total either.'];
  }
  return [];
}

async function fetchBatch(batch, key) {
  const url = new URL(BASE_URL);
  for (const id of batch) url.searchParams.append('ids[]', id);
  const headers = { 'x-api-key': key, 'anthropic-version': '2023-06-01' };
  try {
    const res = await fetch(url, { headers });
    if (res.status !== 200) {
      console.error(`ids lookup returned HTTP ${res.status}`);
      return [[], false];
    }
    const body = await res.json().catch(() => null);
    if (!body) return [[], false];
    return [(body.data ?? []).map(fileRow), true];
  } catch (err) {
    console.error(`ids lookup failed: ${err.message}`);
    return [[], false];
  }
}

function args(argv) {
  const out = { warnDays: 7 };
  for (let i = 0; i < argv.length; i += 1) {
    if (argv[i] === '--ids') out.ids = argv[i += 1];
    else if (argv[i] === '--warn-days') out.warnDays = Number(argv[i += 1]);
  }
  return out;
}

async function main() {
  const opts = args(process.argv.slice(2));
  const key = process.env.ANTHROPIC_API_KEY;
  if (!key) {
    console.error('set ANTHROPIC_API_KEY to a key with access to the workspace '
      + 'that owns these files. Every call is a GET of /v1/files');
    process.exitCode = 2;
    return;
  }
  if (!opts.ids) {
    console.error('usage: --ids <file> [--warn-days 7]');
    process.exitCode = 2;
    return;
  }
  let wanted;
  try {
    wanted = parseIds(await readFile(opts.ids, 'utf8'));
  } catch (err) {
    console.error(`could not read ${opts.ids}: ${err.message}`);
    process.exitCode = 2;
    return;
  }
  if (!wanted.length) {
    console.error(`no file ids in ${opts.ids}. This note is about the ids your `
      + 'application holds, not about the workspace listing');
    process.exitCode = 2;
    return;
  }

  const now = Math.trunc(Date.now() / 1000);
  const batches = chunks(wanted);
  const rows = [];
  const missing = [];
  for (const batch of batches) {
    const [got, ok] = await fetchBatch(batch, key);
    if (!ok) {
      console.error('a batch could not be read, so nothing is concluded');
      process.exitCode = 2;
      return;
    }
    rows.push(...got);
    missing.push(...missingIds(batch, got.map((r) => r.id)));
  }

  console.log(`${wanted.length} id(s) asked in ${batches.length} batch(es) of at `
    + `most ${ID_BATCH}, ${rows.length} returned`);

  let findings = 0;
  for (const row of rows) {
    const [state, detail] = classifyId(row, now, opts.warnDays);
    console.log(`${state.padEnd(20)} ${row.id}: ${detail}`);
    for (const line of repairLines(state)) console.log(`  repair: ${line}`);
    if (FINDINGS.has(state)) findings += 1;
  }
  for (const id of missing) {
    const [state, detail] = classifyId(null, now, opts.warnDays);
    console.log(`${state.padEnd(20)} ${id}: ${detail}`);
    for (const line of repairLines(state)) console.log(`  repair: ${line}`);
    findings += 1;
  }

  console.log(`${missing.length} id(s) missing from the response, ${findings} finding(s)`);
  process.exitCode = findings ? 1 : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) await main();
''',
"test_intro": "The first test is the note's whole thesis in four assertions: a file whose date has passed is graded <code>expired</code>, the detail says every actual use fails rather than that a request failed, and the repair offers a deletion that clears the metadata rather than an extension. The second holds the script to the fact that there is nothing to extend, which is the fix everyone reaches for first. The third is the silent omission &mdash; an id the API declines to return is <code>gone</code>, and <code>missing_ids</code> has to produce it from the diff because no error is raised. The fourth is the one that stops a clean bill of health: an object with no <code>expires_at</code> key at all must not be graded permanent. Then the batching, which is a contract and not a performance tuning. And last the parsing, where a null expiry and an unparseable one must not collapse into the same answer.",
"test_py_file": "test_anthropic_expired_file_refs.py",
"test_py": '''from anthropic_expired_file_refs import (ID_BATCH, chunks, classify_id, epoch,
                                        file_row, human, missing_ids, parse_ids,
                                        repair_lines)

NOW = 1_800_000_000
DAY = 86400


def row(fid, expires_in_days=None, has_field=True, size=2048):
    body = {"id": fid, "type": "file", "filename": fid + ".pdf",
            "size_bytes": size, "created_at": "2026-01-01T00:00:00Z",
            "downloadable": False}
    if has_field:
        body["expires_at"] = (None if expires_in_days is None else
                              _stamp(NOW + int(expires_in_days * DAY)))
    return file_row(body)


def _stamp(when):
    import time as _t
    return _t.strftime("%Y-%m-%dT%H:%M:%SZ", _t.gmtime(when))


def test_an_expired_file_still_answers_and_fails_every_use():
    state, detail = classify_id(row("file_011a", -11.3), NOW, 7.0)
    assert state == "expired"
    assert "expired 11.3 day(s) ago" in detail
    assert "the metadata still answers" in detail
    assert "every actual use of this id fails" in detail
    lines = repair_lines(state)
    assert any("cannot be restored" in line for line in lines)
    assert any("DELETE /v1/files/{file_id}" in line for line in lines)
    assert any("30 day window" in line for line in lines)


def test_an_expiry_cannot_be_extended_so_the_repair_never_suggests_it():
    state, detail = classify_id(row("file_02b7", 4.1), NOW, 7.0)
    assert state == "expiring"
    assert "expires in 4.1 day(s)" in detail
    assert "cannot be extended" in detail
    lines = repair_lines(state)
    assert any("set once at upload" in line for line in lines)
    assert any("Re-upload before the date" in line for line in lines)
    assert not any("extend the" in line for line in lines)
    # Outside the window it is simply live, with the runway printed.
    live, live_detail = classify_id(row("file_05e4", 61.8), NOW, 7.0)
    assert live == "live" and "61.8 day(s)" in live_detail
    assert repair_lines(live) == []


def test_an_id_the_api_declines_to_return_is_the_strongest_signal():
    state, detail = classify_id(None, NOW, 7.0)
    assert state == "gone"
    assert "not returned by the ids lookup" in detail
    assert "30 day metadata window" in detail
    assert any("no read will recover" in line for line in repair_lines(state))
    # Nothing is raised for an unresolvable id, so the diff is the only signal.
    asked = ["file_01", "file_02", "file_03"]
    assert missing_ids(asked, ["file_02"]) == ["file_01", "file_03"]
    assert missing_ids(asked, asked) == []
    assert missing_ids([], ["file_09"]) == []


def test_a_missing_expiry_field_disables_the_check_rather_than_passing_it():
    blind = row("file_06f1", has_field=False)
    assert blind["expiry_reported"] is False
    state, detail = classify_id(blind, NOW, 7.0)
    assert state == "expiry-not-reported"
    assert "could not run" in detail
    assert any("files-api-2025-04-14" in line for line in repair_lines(state))
    # A null expiry is a different fact and must not be confused with it.
    perm = row("file_04d2", None)
    assert perm["expiry_reported"] is True and perm["expires_at"] is None
    assert classify_id(perm, NOW, 7.0)[0] == "no-expiry"
    assert any("never leaves the storage total" in line
               for line in repair_lines("no-expiry"))


def test_batching_is_a_contract_and_not_a_performance_setting():
    ids = ["file_%03d" % n for n in range(250)]
    batched = chunks(ids)
    assert [len(b) for b in batched] == [100, 100, 50]
    assert all(len(b) <= ID_BATCH for b in batched)
    # Asking for a bigger batch does not get one: 100 is documented, not tuned.
    assert [len(b) for b in chunks(ids, 500)] == [100, 100, 50]
    # De-duplication happens before the split, as the documentation specifies.
    assert chunks(["a", "a", " a ", "b", ""]) == [["a", "b"]]
    assert chunks([]) == [] and chunks(None) == []


def test_the_dates_and_the_export_survive_what_is_really_in_them():
    ids = parse_ids("file_01\\n\\n# exported 2026-08-31\\nfile_02  # oldest\\n"
                    "file_01\\n   \\nfile_03\\n")
    assert ids == ["file_01", "file_02", "file_03"]
    assert parse_ids("") == [] and parse_ids(None) == []
    assert epoch("2023-11-14T22:13:20Z") == 1_700_000_000
    assert epoch("2023-11-14T22:13:20.512Z") == 1_700_000_000
    assert epoch("2023-11-14T23:13:20+01:00") == 1_700_000_000
    assert epoch(None) == 0 and epoch("soon") == 0 and epoch(True) == 0
    junk = file_row({"id": "file_07", "size_bytes": "big", "expires_at": "soon"})
    assert junk["size"] == 0
    # Unparseable is not permanent, but it does read as no usable date, so the
    # verdict is no-expiry rather than a fabricated one.
    assert junk["expires_at"] is None and junk["expiry_reported"] is True
    assert file_row(None)["id"] == "" and human(2048) == "2.0 KiB"
''',
"test_js_file": "anthropic-expired-file-refs.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { ID_BATCH, chunks, classifyId, epoch, fileRow, human, missingIds,
         parseIds, repairLines } from './anthropic-expired-file-refs.mjs';

const NOW = 1_800_000_000;
const DAY = 86400;

const stamp = (when) => new Date(when * 1000).toISOString().replace(/\\.\\d+Z$/, 'Z');

const row = (id, expiresInDays = null, hasField = true, size = 2048) => {
  const body = { id, type: 'file', filename: `${id}.pdf`, size_bytes: size,
                 created_at: '2026-01-01T00:00:00Z', downloadable: false };
  if (hasField) {
    body.expires_at = expiresInDays === null ? null
      : stamp(NOW + Math.trunc(expiresInDays * DAY));
  }
  return fileRow(body);
};

test('an expired file still answers and fails every use', () => {
  const [state, detail] = classifyId(row('file_011a', -11.3), NOW, 7);
  assert.equal(state, 'expired');
  assert.ok(detail.includes('expired 11.3 day(s) ago'));
  assert.ok(detail.includes('the metadata still answers'));
  assert.ok(detail.includes('every actual use of this id fails'));
  const lines = repairLines(state);
  assert.ok(lines.some((l) => l.includes('cannot be restored')));
  assert.ok(lines.some((l) => l.includes('DELETE /v1/files/{file_id}')));
  assert.ok(lines.some((l) => l.includes('30 day window')));
});

test('an expiry cannot be extended so the repair never suggests it', () => {
  const [state, detail] = classifyId(row('file_02b7', 4.1), NOW, 7);
  assert.equal(state, 'expiring');
  assert.ok(detail.includes('expires in 4.1 day(s)'));
  assert.ok(detail.includes('cannot be extended'));
  const lines = repairLines(state);
  assert.ok(lines.some((l) => l.includes('set once at upload')));
  assert.ok(lines.some((l) => l.includes('Re-upload before the date')));
  assert.ok(!lines.some((l) => l.includes('extend the')));
  const [live, liveDetail] = classifyId(row('file_05e4', 61.8), NOW, 7);
  assert.equal(live, 'live');
  assert.ok(liveDetail.includes('61.8 day(s)'));
  assert.deepEqual(repairLines(live), []);
});

test('an id the api declines to return is the strongest signal', () => {
  const [state, detail] = classifyId(null, NOW, 7);
  assert.equal(state, 'gone');
  assert.ok(detail.includes('not returned by the ids lookup'));
  assert.ok(detail.includes('30 day metadata window'));
  assert.ok(repairLines(state).some((l) => l.includes('no read will recover')));
  const asked = ['file_01', 'file_02', 'file_03'];
  assert.deepEqual(missingIds(asked, ['file_02']), ['file_01', 'file_03']);
  assert.deepEqual(missingIds(asked, asked), []);
  assert.deepEqual(missingIds([], ['file_09']), []);
});

test('a missing expiry field disables the check rather than passing it', () => {
  const blind = row('file_06f1', null, false);
  assert.equal(blind.expiry_reported, false);
  const [state, detail] = classifyId(blind, NOW, 7);
  assert.equal(state, 'expiry-not-reported');
  assert.ok(detail.includes('could not run'));
  assert.ok(repairLines(state).some((l) => l.includes('files-api-2025-04-14')));
  const perm = row('file_04d2', null);
  assert.equal(perm.expiry_reported, true);
  assert.equal(perm.expires_at, null);
  assert.equal(classifyId(perm, NOW, 7)[0], 'no-expiry');
  assert.ok(repairLines('no-expiry')
    .some((l) => l.includes('never leaves the storage total')));
});

test('batching is a contract and not a performance setting', () => {
  const ids = Array.from({ length: 250 }, (_, n) => `file_${String(n).padStart(3, '0')}`);
  const batched = chunks(ids);
  assert.deepEqual(batched.map((b) => b.length), [100, 100, 50]);
  assert.ok(batched.every((b) => b.length <= ID_BATCH));
  assert.deepEqual(chunks(ids, 500).map((b) => b.length), [100, 100, 50]);
  assert.deepEqual(chunks(['a', 'a', ' a ', 'b', '']), [['a', 'b']]);
  assert.deepEqual(chunks([]), []);
  assert.deepEqual(chunks(null), []);
});

test('the dates and the export survive what is really in them', () => {
  const ids = parseIds('file_01\\n\\n# exported 2026-08-31\\nfile_02  # oldest\\n'
    + 'file_01\\n   \\nfile_03\\n');
  assert.deepEqual(ids, ['file_01', 'file_02', 'file_03']);
  assert.deepEqual(parseIds(''), []);
  assert.deepEqual(parseIds(null), []);
  assert.equal(epoch('2023-11-14T22:13:20Z'), 1700000000);
  assert.equal(epoch('2023-11-14T22:13:20.512Z'), 1700000000);
  assert.equal(epoch('2023-11-14T23:13:20+01:00'), 1700000000);
  assert.equal(epoch(null), 0);
  assert.equal(epoch('soon'), 0);
  assert.equal(epoch(true), 0);
  const junk = fileRow({ id: 'file_07', size_bytes: 'big', expires_at: 'soon' });
  assert.equal(junk.size, 0);
  assert.equal(junk.expires_at, null);
  assert.equal(junk.expiry_reported, true);
  assert.equal(fileRow(null).id, '');
  assert.equal(human(2048), '2.0 KiB');
});
''',
"faq": [
 ("The metadata call works. Why does the Messages request still fail?",
  "Because they are two different lifetimes on the same object. At expires_at the content stops being retrievable and the bytes are released from your storage quota; the metadata remains readable for up to thirty days after that and the file keeps appearing in list responses. A metadata call proves the label exists, not the file. That is the entire failure this note is about, and it is why every state the script prints is a statement about the date rather than about whether the object came back."),
 ("Can we extend the expiry on a file we still need?",
  "No. expires_in_seconds is set once, at upload, somewhere between 3,600 and 7,776,000 seconds, and it cannot be changed afterwards. There is no update call and no policy object. The options are to re-upload the source and swap the id in your records before the date, or to upload without an expiry at all and accept that the file then stays on the storage total until somebody deletes it. The script prints both and never suggests the third thing, because the third thing does not exist."),
 ("Some ids do not come back at all and there is no error. Is that a bug?",
  "It is documented behaviour and it is the most useful signal in the run. Ids that do not resolve to a visible file, including deleted ones, are silently omitted from data. So an id you sent and did not get back is past even the metadata window, or was deleted outright, and either way no read will recover it. The script keeps the request list and diffs it against the response, which is the only way that omission becomes a result rather than a shrug."),
 ("Our run says the check could not run. What does that mean?",
  "It means the objects came back with no expires_at key at all, which happens when the request carries anthropic-beta: files-api-2025-04-14. That header keeps the old response shape, in which the field is not returned and pagination uses before_id and after_id. Drop it. It matters more than it sounds: without that state a script would read the missing field as no expiry and print a clean bill of health across an account of dying references. There is also a hybrid case worth knowing about, where managed-agents-2026-04-01 without the files header returns both the old cursors and the new one."),
 ("How often should this run?",
  "About a third of your shortest expiry window. Ninety-day uploads make it a monthly job. One-hour uploads make it the wrong tool entirely: at that cadence the right check is at the call site, verifying the date before you pass the id rather than discovering it in a scheduled report. What a schedule is genuinely good for is the slow half of the population, the files uploaded once with a long expiry and referenced from a record nobody revisits."),
],
"related": [REL_QUOTA, REL_BETAHDR, REL_VSEXPIRY],
"citations": [CITE_ANT_FILES, CITE_ANT_LIST, CITE_ANT_UPLOAD, CITE_ANT_DELETE],
},
{
"slug": "stored-responses-accumulating",
"title": "Every response is stored and no endpoint will list them",
"description": "store defaults to true and retention is at least 30 days, a floor not a deadline. Neither collection can be listed, so probe the ids you recorded.",
"h1": "Every response is stored and no endpoint will list them",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["openai responses api store true default retention",
             "how to list stored responses openai",
             "delete stored responses openai retention 30 days",
             "conversations retained until deleted openai",
             "openai conversation items not deleted with conversation"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Needs OPENAI_API_KEY, a project key set to Read Only, and a file of the response and conversation ids your application recorded. There is no list endpoint for either resource, so the ids have to come from your own records.",
"lead": "The question arrives from legal, not from engineering, and it is one sentence long: what customer data are we currently holding on the model provider's side. Everybody assumes somebody knows. Nobody does. The application logs what it sent and what came back, the provider stores the same thing independently, and when you go looking for the endpoint that lists what is stored there so you can answer the sentence, there is not one. Not for responses, not for conversations. There is no query. There is only whatever ids you happened to write down.",
"short_answer": """<p>Start by accepting the limitation, because it shapes everything else. <strong>Neither <code>/v1/responses</code> nor <code>/v1/conversations</code> has a list endpoint.</strong> Both resources are reachable only by an id you already hold. So this is a probe over your own records rather than an audit of your account, and the script says so on every run instead of implying coverage it does not have.</p>
<p>Then read the retention wording carefully, because it runs the opposite way to how it is usually quoted. The conversation-state guide says response objects are saved for 30 days by default; the data-retention page says stored response data will be kept <strong>for at least 30 days</strong>. For a thread that has to keep resolving, thirty days is a deadline. For a question about what you are holding, it is a <strong>floor</strong>. A response you have not deleted is a response you are still holding, and the API will not tell you for how much longer.</p>
<p>With a <strong>project read key</strong>, call <code>GET /v1/responses/{response_id}</code> for each recorded id. A 200 is the only evidence a response was stored, because the Response object <strong>does not echo <code>store</code> back</strong> &mdash; that parameter exists on the create request and nowhere in the retrieved object. Read <code>created_at</code>, <code>status</code> and <code>conversation</code>, and grade the age against your own retention rule rather than against the platform's.</p>
<p>Conversations are the other half and they are worse. Their documented retention is <em>until deleted</em>, they are excluded from the zero-data-retention column of the same table, and every turn appends items indefinitely, so a long thread is both a data-holding problem and a rising input bill on every subsequent turn. <code>GET /v1/conversations/{conversation_id}/items</code> counts them, 100 per page.</p>
<p>Two repairs, and the second one is a trap. <code>DELETE /v1/responses/{response_id}</code> removes a response. <code>DELETE /v1/conversations/{conversation_id}</code> removes a conversation and <strong>its items are not deleted with it</strong>, so a sweep that only deletes conversations leaves the transcripts behind. The script prints both, in that order, and executes neither.</p>""",
"problem": """<p>Nobody chose this. <code>store</code> defaults to true, because that is what makes <code>previous_response_id</code> threading and background mode work, and defaults do not appear in code review. So every prompt and every completion your application has ever produced is persisted on the provider's side, including the ones that carried a support ticket, a pasted credential, a medical detail or a retrieved internal document, and there was never a moment where somebody decided that.</p>
<p>The absence of a list endpoint is what turns a policy question into an impossible one. You cannot ask what is stored. You can only ask about an id, and you can only ask about the ids you recorded, and the ids you recorded are a subset of the ids you created because logging is best-effort and log retention is shorter than data retention. The gap between those two sets is invisible by construction: the objects in it are still there, still readable by anyone with the key, and permanently unenumerable.</p>
<p>Conversations make the same problem worse along a second axis. They have no expiry at all &mdash; the retention table says until deleted &mdash; and they grow monotonically, one item per turn, forever. A thread that has been going for six months is a transcript nobody has read, held indefinitely, and it is also the reason that thread's input tokens have been climbing every week. The data-holding problem and the cost problem are the same object.</p>
<p>And there is a sting in the deletion path that catches the obvious cleanup script. Deleting a conversation does not delete the items inside it. A sweep written by somebody reasonable, that walks a list of conversation ids and deletes each one, leaves every message body in place and produces a report saying the cleanup succeeded.</p>""",
"why": """<p><strong>The limitation is the note, so the script is built around it rather than apologising for it.</strong> There is no list endpoint for either resource. That is not an inconvenience to route around, it is the fact that determines what an honest answer looks like: a coverage statement printed on every run, ids counted next to findings, and a first repair that is not a deletion at all but a column. If you are not recording response and conversation ids with a created-at, no script can ever answer the legal question, and that is the finding.</p>
<p><strong>"At least 30 days" is a floor, and reading it as a deadline inverts the conclusion.</strong> The two OpenAI pages phrase it differently and the weaker one is the one a retention question needs. A thread note treats thirty days as the moment something disappears and computes runway from it. This note treats it as the minimum time something persists, so an object older than your own policy is a finding regardless of what the platform intends to do next, and the output says which of the two readings it is using.</p>
<p><strong>A 200 is the only evidence of storage, because <code>store</code> is write-only.</strong> The parameter appears in the create request and is absent from the retrieved Response object; there is no flag to read back. So the script never reports a <code>store</code> value, and a 404 gets a sentence naming both of its causes &mdash; created with <code>store: false</code>, or already aged out &mdash; rather than being resolved into whichever one is more convenient.</p>
<p><strong>Deleting a conversation does not delete its items, and that is documented.</strong> This is the single most expensive detail in the note, because the natural cleanup is exactly wrong: a script that iterates conversation ids and deletes them reports success and removes nothing of substance. The repair is printed in the order it has to be done &mdash; items first, conversation second &mdash; and there is a test that fails if the wording ever stops saying so.</p>
<p><strong>A long thread is two findings that happen to share an object.</strong> Item count past a cap is a data-holding problem and a per-turn cost problem at once: every future turn on that conversation carries the accumulated items as input. The script grades the count separately from the idleness, because a busy thread with four thousand items and a dead thread with forty are fixed by different things &mdash; a summarise-and-restart in the first case, a sweep in the second.</p>
<p><strong>This is not the chain note and the code proves it.</strong> The published <code>previous-response-id-chain-broken</code> walks parents upward and asks whether the next turn will resolve. This one never follows a parent: the row it builds from a retrieved response deliberately has no <code>previous_response_id</code> key in it, and a test asserts that. Same GET, opposite question, and the retention number even means the opposite thing in each.</p>""",
"steps": [
 {"h": "Export the ids you have, and notice which ones you do not",
  "body": """<p>One id per line, mixed. Anything beginning <code>resp_</code> is probed as a response, anything beginning <code>conv_</code> as a conversation, and anything else is reported as unroutable rather than guessed at. If this file is short because your logs roll over faster than the provider's retention, that gap is the first thing the run tells you.</p>"""},
 {"h": "Use a project read key",
  "body": """<p>Stored responses and conversations are project data, so an admin key is the wrong credential. Every call is a GET: the response, the conversation, and the conversation's items. Nothing is created, nothing is deleted, and no completion is generated.</p>"""},
 {"h": "Grade responses against your policy, not the platform's",
  "body": """<p><code>--policy-days</code> is your retention rule, defaulting to 30. A response still readable past it is a finding whatever the platform intends, because the documented guarantee is <em>at least</em> 30 days and therefore says nothing about when the object goes away.</p>"""},
 {"h": "Count conversation items, 100 at a time",
  "body": """<p><code>GET /v1/conversations/{conversation_id}/items?limit=100</code>, paged on <code>after</code>. The count answers the retention question and the cost question at once, and <code>--max-items</code> sets where a thread stops being long and starts being a problem.</p>"""},
 {"h": "Take the repair in the order it is printed",
  "body": """<p>Responses: <code>DELETE /v1/responses/{response_id}</code>, and <code>store: false</code> on calls carrying regulated data. Conversations: delete the <em>items</em> first, because deleting the conversation does not delete them, then the conversation. None of it is executed here.</p>"""},
],
"verify": """<p>Delete one conversation properly &mdash; items first, then the conversation &mdash; and re-run. That id should move to <code>not-retained</code>, and the total item count in the run should fall by the number of items you removed rather than by zero, which is the check that tells you the sweep did what you think. The number to keep an eye on across runs is not the findings count but the coverage line: as your own id ledger improves, the number of ids probed should rise, and a run that probes more and finds proportionally fewer problems is the only shape that means progress.</p>
<pre><code class="language-bash">python3 openai_stored_state_probe.py --records stored-ids.txt --policy-days 30
# 412 id(s) supplied: 388 response(s), 22 conversation(s), 2 unroutable
# coverage: neither /v1/responses nor /v1/conversations has a list endpoint,
#           so this is your records and not your account
# retained-past-policy resp_a19: still readable 94.2 day(s) after creation,
#                      past your 30 day policy. Retention is documented as at
#                      least 30 days, so that is a floor and not a deadline
#   repair: DELETE /v1/responses/{response_id} for what you no longer need,
#           and pass store false on calls carrying regulated data.
# items-outlive-response resp_b40: 4.1 day(s) old and inside your policy, but
#                      its items were added to conversation conv_x1, which is
#                      retained until deleted
# not-retained         resp_c02: nothing is stored under this id. It was
#                      created with store false, or it has already aged out
# thread-unbounded     conv_x1: 4,182 item(s) and no TTL, so every turn on
#                      this thread carries them as input
#   repair: start a fresh conversation seeded with a summary once a thread
#           gets long, so input tokens stop compounding.
#   repair: delete the items first with DELETE /v1/conversations/
#           {conversation_id}/items/{item_id}. Deleting the conversation does
#           not delete its items.
# thread-idle          conv_y7: last item 211.4 day(s) ago, past your 30 day
#                      policy, and conversations are retained until deleted
# unrecognised-id      legacy-7742: neither a resp_ nor a conv_ id, so it was
#                      not probed
# 412 supplied, 410 probed, 3 finding(s)</code></pre>""",
"code_intro": "Three kinds of GET and seven pure functions. <code>parse_records</code>, which routes ids by prefix and keeps what it could not route rather than dropping it; <code>response_row</code>, which reduces a retrieved response to five fields and <strong>deliberately has no <code>previous_response_id</code> in it</strong>, because following a parent is the other note's job; <code>item_totals</code>, which folds a conversation's items into a count and two timestamps; <code>age_days</code>, taking the clock as an argument so retention is testable without one; <code>grade_response</code> and <code>grade_conversation</code>, which grade against <em>your</em> policy rather than the platform's and treat a 404 as one fact with two named causes; and <code>repair_lines</code>, which prints the conversation cleanup in the only order that works.",
"py_file": "openai_stored_state_probe.py",
"py": '''"""Probe recorded response and conversation ids for retention and volume.

Read only. GET /v1/responses/{id}, GET /v1/conversations/{id} and
GET /v1/conversations/{id}/items. Nothing is created and nothing is deleted.

Neither /v1/responses nor /v1/conversations has a list endpoint, so there is no
way to enumerate what is stored. This probes the ids you recorded and prints a
coverage statement every run rather than implying it audited an account.

Two retention facts, both documented, both easy to quote the wrong way round.
Stored response data is kept for AT LEAST 30 days, which is a floor rather than
a deadline: an object you have not deleted is one you are still holding.
Conversations are retained UNTIL DELETED and their items are not deleted when
the conversation is.

The Response object does not echo `store` back, so a 200 is the only evidence
that a response was stored and a 404 has two causes, both of which are named.

This never follows previous_response_id. Walking a chain to see whether the
next turn resolves is a different question and a different script.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("openai_stored_state_probe")

RESPONSES_URL = "https://api.openai.com/v1/responses"
CONVERSATIONS_URL = "https://api.openai.com/v1/conversations"

# Documented as "at least 30 days" for stored response data, and "until
# deleted" for conversations. Only the first is a number, and it is a floor.
RESPONSE_RETENTION_FLOOR_DAYS = 30
ITEM_PAGE = 100

FINDINGS = ("retained-past-policy", "items-outlive-response", "thread-unbounded",
            "thread-idle", "probe-unreadable")


def parse_records(text):
    """Route recorded ids by prefix. Pure. What cannot be routed is kept.

    Dropping an unroutable id would quietly shrink the denominator in a note
    whose whole subject is how little of the account it can see.
    """
    out = {"responses": [], "conversations": [], "unrecognised": []}
    seen = set()
    for line in str(text or "").splitlines():
        item = line.split("#", 1)[0].strip()
        if not item or item in seen:
            continue
        seen.add(item)
        if item.startswith("resp_"):
            out["responses"].append(item)
        elif item.startswith("conv_"):
            out["conversations"].append(item)
        else:
            out["unrecognised"].append(item)
    return out


def response_row(body):
    """One retrieved response, reduced. Pure. Five fields and no chain.

    There is deliberately no previous_response_id here. Walking upward from a
    response to its parent answers whether a thread still resolves, which is a
    different note; this one asks how old the object is and what it is attached
    to. There is no `store` field either, because the object does not carry one.
    """
    body = body if isinstance(body, dict) else {}
    conversation = body.get("conversation")
    if isinstance(conversation, dict):
        conversation = conversation.get("id")
    try:
        created = int(body.get("created_at") or 0)
    except (TypeError, ValueError):
        created = 0
    metadata = body.get("metadata")
    return {"id": str(body.get("id") or ""),
            "created_at": max(0, created),
            "status": str(body.get("status") or ""),
            "conversation": str(conversation or ""),
            "metadata_keys": len(metadata) if isinstance(metadata, dict) else 0}


def item_totals(items):
    """Count and the two timestamps that bound a thread. Pure."""
    stamps = []
    for item in items or []:
        if not isinstance(item, dict):
            continue
        try:
            at = int(item.get("created_at") or 0)
        except (TypeError, ValueError):
            at = 0
        if at > 0:
            stamps.append(at)
    return {"count": len(items or []),
            "oldest": min(stamps) if stamps else 0,
            "newest": max(stamps) if stamps else 0}


def age_days(when, now):
    """Age in days. Pure. The clock is an argument. None when undatable."""
    try:
        at, ref = int(when), int(now)
    except (TypeError, ValueError):
        return None
    return (ref - at) / 86400.0 if at > 0 else None


def grade_response(row, status, now, policy_days):
    """Grade one stored response against YOUR policy. Pure."""
    if status == 404:
        return ("not-retained",
                "nothing is stored under this id. It was created with store "
                "false, or it has already aged out")
    if status != 200:
        return ("probe-unreadable",
                "HTTP %s, so nothing about this id was established" % status)
    age = age_days((row or {}).get("created_at"), now)
    if age is None:
        return ("undatable",
                "stored, but it carried no usable created_at, so its age "
                "cannot be graded")
    conversation = str((row or {}).get("conversation") or "")
    if age > float(policy_days):
        tail = ("" if not conversation else
                ", and its items were added to conversation %s, which is "
                "retained until deleted" % conversation)
        return ("retained-past-policy",
                "still readable %.1f day(s) after creation, past your %d day "
                "policy. Retention is documented as at least %d days, so that "
                "is a floor and not a deadline%s"
                % (age, int(policy_days), RESPONSE_RETENTION_FLOOR_DAYS, tail))
    if conversation:
        return ("items-outlive-response",
                "%.1f day(s) old and inside your policy, but its items were "
                "added to conversation %s, which is retained until deleted"
                % (age, conversation))
    return ("within-policy",
            "stored, %.1f day(s) old, inside your %d day policy"
            % (age, int(policy_days)))


def grade_conversation(row, totals, status, now, policy_days, max_items):
    """Grade one conversation on volume first, then on idleness. Pure."""
    if status == 404:
        return ("not-retained",
                "no conversation under this id, so it has already been deleted")
    if status != 200:
        return ("probe-unreadable",
                "HTTP %s, so nothing about this id was established" % status)
    totals = totals or {"count": 0, "oldest": 0, "newest": 0}
    if int(totals.get("count") or 0) > int(max_items):
        return ("thread-unbounded",
                "%d item(s) and no TTL, so every turn on this thread carries "
                "them as input" % int(totals["count"]))
    idle = age_days(totals.get("newest"), now)
    if idle is not None and idle > float(policy_days):
        return ("thread-idle",
                "last item %.1f day(s) ago, past your %d day policy, and "
                "conversations are retained until deleted"
                % (idle, int(policy_days)))
    if idle is None:
        return ("thread-undatable",
                "%d item(s), none of which carried a usable created_at"
                % int(totals.get("count") or 0))
    return ("thread-within-policy",
            "%d item(s), last active %.1f day(s) ago"
            % (int(totals.get("count") or 0), idle))


def coverage_note(records):
    """The sentence that has to appear on every run. Pure."""
    records = records or {}
    return ("%d id(s) supplied: %d response(s), %d conversation(s), %d "
            "unroutable. Neither /v1/responses nor /v1/conversations has a "
            "list endpoint, so this is your records and not your account"
            % (sum(len(records.get(k) or []) for k in
                   ("responses", "conversations", "unrecognised")),
               len(records.get("responses") or []),
               len(records.get("conversations") or []),
               len(records.get("unrecognised") or [])))


def repair_lines(state):
    """The repair for one verdict. Pure. Printed, never performed."""
    items_first = ("delete the items first with DELETE /v1/conversations/"
                   "{conversation_id}/items/{item_id}, then the conversation. "
                   "Deleting the conversation does not delete its items.")
    if state == "retained-past-policy":
        return ["DELETE /v1/responses/{response_id} for what you no longer "
                "need, and pass store false on calls carrying regulated data.",
                "keep an id ledger with a created_at. It is the only inventory "
                "that can exist, because neither collection can be listed."]
    if state == "items-outlive-response":
        return ["deleting the response is not enough here. " + items_first]
    if state == "thread-unbounded":
        return ["start a fresh conversation seeded with a summary once a "
                "thread gets long, so input tokens stop compounding.",
                items_first]
    if state == "thread-idle":
        return [items_first]
    if state == "probe-unreadable":
        return ["the key could not read this id. Check that it belongs to the "
                "project that created the object before concluding anything "
                "about retention."]
    if state == "unrecognised-id":
        return ["route it by hand, or drop it. An id this script cannot "
                "classify is a hole in a coverage figure that is already "
                "bounded by your own records."]
    return []


def get_json(url, key, params=None, timeout=30):
    """One GET. Returns (status, body). A 404 is the answer, not an error."""
    try:
        r = requests.get(url, params=params or {},
                         headers={"Authorization": "Bearer " + key},
                         timeout=timeout)
    except requests.RequestException as exc:
        log.debug("GET %s failed: %s", url, exc)
        return (None, None)
    try:
        return (r.status_code, r.json())
    except ValueError:
        return (r.status_code, None)


def walk_items(conversation_id, key, max_pages):
    """Page a conversation's items on `after`. Returns (items, complete)."""
    url = "%s/%s/items" % (CONVERSATIONS_URL, conversation_id)
    items, cursor, pages = [], None, 0
    while pages < max_pages:
        params = {"limit": ITEM_PAGE, "order": "asc"}
        if cursor:
            params["after"] = cursor
        status, body = get_json(url, key, params)
        if status != 200 or not isinstance(body, dict):
            return (items, False)
        data = body.get("data") or []
        pages += 1
        items.extend(data)
        if not data or body.get("has_more") is False:
            return (items, True)
        cursor = data[-1].get("id")
        if not cursor:
            return (items, True)
    return (items, False)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--records", required=True,
                    help="file of recorded resp_ and conv_ ids, one per line")
    ap.add_argument("--policy-days", type=int, default=30,
                    help="your own retention rule, not the platform's")
    ap.add_argument("--max-items", type=int, default=500,
                    help="item count at which a thread stops being long")
    ap.add_argument("--max-item-pages", type=int, default=50,
                    help="page cap when counting one conversation's items")
    args = ap.parse_args()

    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        log.error("set OPENAI_API_KEY to a project key set to Read Only. Every "
                  "call is a GET of a response, a conversation or its items")
        return 2
    try:
        with open(args.records, "r", encoding="utf-8") as fh:
            records = parse_records(fh.read())
    except OSError as exc:
        log.error("could not read %s: %s", args.records, exc)
        return 2
    probed = len(records["responses"]) + len(records["conversations"])
    if not probed:
        log.error("no resp_ or conv_ ids in %s. Neither collection can be "
                  "listed, so the ids have to come from your own records",
                  args.records)
        return 2

    now = int(time.time())
    log.info("%s", coverage_note(records))
    findings = 0

    for rid in records["responses"]:
        status, body = get_json("%s/%s" % (RESPONSES_URL, rid), key)
        row = response_row(body)
        state, detail = grade_response(row, status, now, args.policy_days)
        emit = log.warning if state in FINDINGS else log.info
        emit("%-22s %s: %s", state, rid, detail)
        for line in repair_lines(state):
            emit("  repair: %s", line)
        if state in FINDINGS:
            findings += 1

    for cid in records["conversations"]:
        status, body = get_json("%s/%s" % (CONVERSATIONS_URL, cid), key)
        totals = None
        if status == 200:
            items, complete = walk_items(cid, key, args.max_item_pages)
            totals = item_totals(items)
            if not complete:
                log.warning("%-22s %s: the item listing stopped early, so %d "
                            "is a floor", "items-incomplete", cid,
                            totals["count"])
        state, detail = grade_conversation(body, totals, status, now,
                                           args.policy_days, args.max_items)
        emit = log.warning if state in FINDINGS else log.info
        emit("%-22s %s: %s", state, cid, detail)
        for line in repair_lines(state):
            emit("  repair: %s", line)
        if state in FINDINGS:
            findings += 1

    for other in records["unrecognised"]:
        log.info("%-22s %s: neither a resp_ nor a conv_ id, so it was not "
                 "probed", "unrecognised-id", other)

    log.info("%d supplied, %d probed, %d finding(s)",
             probed + len(records["unrecognised"]), probed, findings)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "openai-stored-state-probe.mjs",
"js": '''/**
 * Probe recorded response and conversation ids for retention and volume.
 *
 * Read only. GET /v1/responses/{id}, GET /v1/conversations/{id} and
 * GET /v1/conversations/{id}/items. Nothing is created or deleted.
 *
 * Neither collection has a list endpoint, so this probes the ids you recorded
 * and prints a coverage statement every run.
 *
 * Stored response data is kept for AT LEAST 30 days, which is a floor rather
 * than a deadline. Conversations are retained UNTIL DELETED, and their items
 * are not deleted when the conversation is.
 *
 * This never follows previous_response_id: whether a thread still resolves is
 * a different question and a different script.
 */
import { readFile } from 'node:fs/promises';

const RESPONSES_URL = 'https://api.openai.com/v1/responses';
const CONVERSATIONS_URL = 'https://api.openai.com/v1/conversations';

export const RESPONSE_RETENTION_FLOOR_DAYS = 30;
const ITEM_PAGE = 100;

const FINDINGS = new Set(['retained-past-policy', 'items-outlive-response',
  'thread-unbounded', 'thread-idle', 'probe-unreadable']);

/** Route recorded ids by prefix. Pure. What cannot be routed is kept. */
export function parseRecords(text) {
  const out = { responses: [], conversations: [], unrecognised: [] };
  const seen = new Set();
  for (const line of String(text ?? '').split('\\n')) {
    const item = line.split('#')[0].trim();
    if (!item || seen.has(item)) continue;
    seen.add(item);
    if (item.startsWith('resp_')) out.responses.push(item);
    else if (item.startsWith('conv_')) out.conversations.push(item);
    else out.unrecognised.push(item);
  }
  return out;
}

/** One retrieved response, reduced. Pure. Five fields and no chain. */
export function responseRow(body) {
  const row = (body && typeof body === 'object') ? body : {};
  const conversation = (row.conversation && typeof row.conversation === 'object')
    ? row.conversation.id : row.conversation;
  const created = Number(row.created_at ?? 0);
  const metadata = row.metadata;
  return {
    id: String(row.id ?? ''),
    created_at: Number.isFinite(created) ? Math.max(0, Math.trunc(created)) : 0,
    status: String(row.status ?? ''),
    conversation: String(conversation ?? ''),
    metadata_keys: (metadata && typeof metadata === 'object')
      ? Object.keys(metadata).length : 0,
  };
}

/** Count and the two timestamps that bound a thread. Pure. */
export function itemTotals(items) {
  const stamps = [];
  for (const item of items ?? []) {
    if (!item || typeof item !== 'object') continue;
    const at = Number(item.created_at ?? 0);
    if (Number.isFinite(at) && at > 0) stamps.push(Math.trunc(at));
  }
  return {
    count: (items ?? []).length,
    oldest: stamps.length ? Math.min(...stamps) : 0,
    newest: stamps.length ? Math.max(...stamps) : 0,
  };
}

/** Age in days. Pure. The clock is an argument. Null when undatable. */
export function ageDays(when, now) {
  const at = Number(when);
  const ref = Number(now);
  if (!Number.isFinite(at) || !Number.isFinite(ref) || at <= 0) return null;
  return (ref - at) / 86400;
}

/** Grade one stored response against YOUR policy. Pure. */
export function gradeResponse(row, status, now, policyDays) {
  if (status === 404) {
    return ['not-retained',
      'nothing is stored under this id. It was created with store false, or it '
      + 'has already aged out'];
  }
  if (status !== 200) {
    return ['probe-unreadable',
      `HTTP ${status}, so nothing about this id was established`];
  }
  const age = ageDays((row ?? {}).created_at, now);
  if (age === null) {
    return ['undatable',
      'stored, but it carried no usable created_at, so its age cannot be graded'];
  }
  const conversation = String((row ?? {}).conversation ?? '');
  if (age > Number(policyDays)) {
    const tail = conversation
      ? `, and its items were added to conversation ${conversation}, which is `
        + 'retained until deleted'
      : '';
    return ['retained-past-policy',
      `still readable ${age.toFixed(1)} day(s) after creation, past your `
      + `${Math.trunc(policyDays)} day policy. Retention is documented as at least `
      + `${RESPONSE_RETENTION_FLOOR_DAYS} days, so that is a floor and not a `
      + `deadline${tail}`];
  }
  if (conversation) {
    return ['items-outlive-response',
      `${age.toFixed(1)} day(s) old and inside your policy, but its items were `
      + `added to conversation ${conversation}, which is retained until deleted`];
  }
  return ['within-policy',
    `stored, ${age.toFixed(1)} day(s) old, inside your ${Math.trunc(policyDays)} `
    + 'day policy'];
}

/** Grade one conversation on volume first, then on idleness. Pure. */
export function gradeConversation(row, totals, status, now, policyDays, maxItems) {
  if (status === 404) {
    return ['not-retained',
      'no conversation under this id, so it has already been deleted'];
  }
  if (status !== 200) {
    return ['probe-unreadable',
      `HTTP ${status}, so nothing about this id was established`];
  }
  const tot = totals ?? { count: 0, oldest: 0, newest: 0 };
  if (Number(tot.count ?? 0) > Number(maxItems)) {
    return ['thread-unbounded',
      `${Number(tot.count)} item(s) and no TTL, so every turn on this thread `
      + 'carries them as input'];
  }
  const idle = ageDays(tot.newest, now);
  if (idle !== null && idle > Number(policyDays)) {
    return ['thread-idle',
      `last item ${idle.toFixed(1)} day(s) ago, past your ${Math.trunc(policyDays)} `
      + 'day policy, and conversations are retained until deleted'];
  }
  if (idle === null) {
    return ['thread-undatable',
      `${Number(tot.count ?? 0)} item(s), none of which carried a usable created_at`];
  }
  return ['thread-within-policy',
    `${Number(tot.count ?? 0)} item(s), last active ${idle.toFixed(1)} day(s) ago`];
}

/** The sentence that has to appear on every run. Pure. */
export function coverageNote(records) {
  const r = records ?? {};
  const responses = (r.responses ?? []).length;
  const conversations = (r.conversations ?? []).length;
  const unrecognised = (r.unrecognised ?? []).length;
  return `${responses + conversations + unrecognised} id(s) supplied: `
    + `${responses} response(s), ${conversations} conversation(s), `
    + `${unrecognised} unroutable. Neither /v1/responses nor /v1/conversations `
    + 'has a list endpoint, so this is your records and not your account';
}

/** The repair for one verdict. Pure. Printed, never performed. */
export function repairLines(state) {
  const itemsFirst = 'delete the items first with DELETE /v1/conversations/'
    + '{conversation_id}/items/{item_id}, then the conversation. Deleting the '
    + 'conversation does not delete its items.';
  if (state === 'retained-past-policy') {
    return ['DELETE /v1/responses/{response_id} for what you no longer need, and '
      + 'pass store false on calls carrying regulated data.',
    'keep an id ledger with a created_at. It is the only inventory that can '
      + 'exist, because neither collection can be listed.'];
  }
  if (state === 'items-outlive-response') {
    return [`deleting the response is not enough here. ${itemsFirst}`];
  }
  if (state === 'thread-unbounded') {
    return ['start a fresh conversation seeded with a summary once a thread gets '
      + 'long, so input tokens stop compounding.', itemsFirst];
  }
  if (state === 'thread-idle') return [itemsFirst];
  if (state === 'probe-unreadable') {
    return ['the key could not read this id. Check that it belongs to the project '
      + 'that created the object before concluding anything about retention.'];
  }
  if (state === 'unrecognised-id') {
    return ['route it by hand, or drop it. An id this script cannot classify is a '
      + 'hole in a coverage figure that is already bounded by your own records.'];
  }
  return [];
}

async function getJson(url, key, params) {
  const target = new URL(url);
  for (const [k, v] of Object.entries(params ?? {})) {
    target.searchParams.set(k, String(v));
  }
  try {
    const res = await fetch(target, { headers: { Authorization: `Bearer ${key}` } });
    const body = await res.json().catch(() => null);
    return [res.status, body];
  } catch {
    return [null, null];
  }
}

async function walkItems(conversationId, key, maxPages) {
  const url = `${CONVERSATIONS_URL}/${conversationId}/items`;
  const items = [];
  let cursor = null;
  let pages = 0;
  while (pages < maxPages) {
    const params = { limit: ITEM_PAGE, order: 'asc' };
    if (cursor) params.after = cursor;
    const [status, body] = await getJson(url, key, params);
    if (status !== 200 || !body || typeof body !== 'object') return [items, false];
    const data = body.data ?? [];
    pages += 1;
    items.push(...data);
    if (!data.length || body.has_more === false) return [items, true];
    cursor = data[data.length - 1]?.id;
    if (!cursor) return [items, true];
  }
  return [items, false];
}

function args(argv) {
  const out = { policyDays: 30, maxItems: 500, maxItemPages: 50 };
  for (let i = 0; i < argv.length; i += 1) {
    if (argv[i] === '--records') out.records = argv[i += 1];
    else if (argv[i] === '--policy-days') out.policyDays = Number(argv[i += 1]);
    else if (argv[i] === '--max-items') out.maxItems = Number(argv[i += 1]);
    else if (argv[i] === '--max-item-pages') out.maxItemPages = Number(argv[i += 1]);
  }
  return out;
}

async function main() {
  const opts = args(process.argv.slice(2));
  const key = process.env.OPENAI_API_KEY;
  if (!key) {
    console.error('set OPENAI_API_KEY to a project key set to Read Only. Every '
      + 'call is a GET of a response, a conversation or its items');
    process.exitCode = 2;
    return;
  }
  if (!opts.records) {
    console.error('usage: --records <file> [--policy-days 30] [--max-items 500]');
    process.exitCode = 2;
    return;
  }
  let records;
  try {
    records = parseRecords(await readFile(opts.records, 'utf8'));
  } catch (err) {
    console.error(`could not read ${opts.records}: ${err.message}`);
    process.exitCode = 2;
    return;
  }
  const probed = records.responses.length + records.conversations.length;
  if (!probed) {
    console.error(`no resp_ or conv_ ids in ${opts.records}. Neither collection `
      + 'can be listed, so the ids have to come from your own records');
    process.exitCode = 2;
    return;
  }

  const now = Math.trunc(Date.now() / 1000);
  console.log(coverageNote(records));
  let findings = 0;

  for (const id of records.responses) {
    const [status, body] = await getJson(`${RESPONSES_URL}/${id}`, key);
    const [state, detail] = gradeResponse(responseRow(body), status, now,
                                          opts.policyDays);
    console.log(`${state.padEnd(22)} ${id}: ${detail}`);
    for (const line of repairLines(state)) console.log(`  repair: ${line}`);
    if (FINDINGS.has(state)) findings += 1;
  }

  for (const id of records.conversations) {
    const [status, body] = await getJson(`${CONVERSATIONS_URL}/${id}`, key);
    let totals = null;
    if (status === 200) {
      const [items, complete] = await walkItems(id, key, opts.maxItemPages);
      totals = itemTotals(items);
      if (!complete) {
        console.log(`${'items-incomplete'.padEnd(22)} ${id}: the item listing `
          + `stopped early, so ${totals.count} is a floor`);
      }
    }
    const [state, detail] = gradeConversation(body, totals, status, now,
                                              opts.policyDays, opts.maxItems);
    console.log(`${state.padEnd(22)} ${id}: ${detail}`);
    for (const line of repairLines(state)) console.log(`  repair: ${line}`);
    if (FINDINGS.has(state)) findings += 1;
  }

  for (const other of records.unrecognised) {
    console.log(`${'unrecognised-id'.padEnd(22)} ${other}: neither a resp_ nor a `
      + 'conv_ id, so it was not probed');
  }

  console.log(`${probed + records.unrecognised.length} supplied, ${probed} probed, `
    + `${findings} finding(s)`);
  process.exitCode = findings ? 1 : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) await main();
''',
"test_intro": "The second test is the one that keeps this note off the chain note's ground, so it is worth reading first: the row built from a retrieved response must contain no <code>previous_response_id</code> and no <code>store</code> field, the first because following a parent is a different question and the second because the object does not carry one. Around it, the retention reading in both directions &mdash; an object past your own policy is a finding and the wording says floor rather than deadline, while a 404 gets both of its causes named instead of one. Then the conversation trap, which is the most expensive detail here: deleting a conversation does not delete its items, and the repair has to say so in the order the work has to be done. Then volume and idleness graded as two separate states on one object. And last the coverage sentence, asserted to appear whatever the run found, because a probe over your own records can never speak for the account.",
"test_py_file": "test_openai_stored_state_probe.py",
"test_py": '''from openai_stored_state_probe import (RESPONSE_RETENTION_FLOOR_DAYS, age_days,
                                       coverage_note, grade_conversation,
                                       grade_response, item_totals,
                                       parse_records, repair_lines,
                                       response_row)

NOW = 1_800_000_000
DAY = 86400


def resp(rid, days_old, conversation=None):
    return response_row({"id": rid, "object": "response", "status": "completed",
                         "created_at": NOW - int(days_old * DAY),
                         "conversation": ({"id": conversation} if conversation
                                          else None),
                         "metadata": {"tenant": "acme"}})


def items(n, newest_days_old=1.0):
    return [{"id": "msg_%d" % i, "type": "message",
             "created_at": NOW - int((newest_days_old + n - i - 1) * DAY)}
            for i in range(n)]


def test_retention_is_read_as_a_floor_and_a_404_keeps_both_its_causes():
    state, detail = grade_response(resp("resp_a19", 94.2), 200, NOW, 30)
    assert state == "retained-past-policy"
    assert "still readable 94.2 day(s)" in detail
    assert "past your 30 day policy" in detail
    assert "at least %d days" % RESPONSE_RETENTION_FLOOR_DAYS in detail
    assert "a floor and not a deadline" in detail
    lines = repair_lines(state)
    assert any("DELETE /v1/responses/{response_id}" in line for line in lines)
    assert any("id ledger" in line for line in lines)
    # A 404 is one fact with two causes and the script names both.
    gone, gone_detail = grade_response(None, 404, NOW, 30)
    assert gone == "not-retained"
    assert "store false" in gone_detail and "aged out" in gone_detail
    assert repair_lines(gone) == []
    assert grade_response(resp("resp_z1", 1.0), 403, NOW, 30)[0] == "probe-unreadable"


def test_the_row_has_no_chain_in_it_and_no_store_flag():
    row = response_row({"id": "resp_b40", "created_at": 1_700_000_000,
                        "previous_response_id": "resp_a01", "status": "completed",
                        "conversation": {"id": "conv_x1"},
                        "metadata": {"tenant": "acme", "env": "prod"}})
    assert row == {"id": "resp_b40", "created_at": 1_700_000_000,
                   "status": "completed", "conversation": "conv_x1",
                   "metadata_keys": 2}
    # Following a parent is the other note. Reading store back is impossible.
    assert "previous_response_id" not in row
    assert "store" not in row and "stored" not in row
    assert response_row(None)["id"] == ""
    assert response_row({"created_at": "nonsense"})["created_at"] == 0
    assert response_row({"metadata": "nope"})["metadata_keys"] == 0


def test_deleting_the_conversation_does_not_delete_its_items():
    state, detail = grade_response(resp("resp_b40", 4.1, "conv_x1"), 200, NOW, 30)
    assert state == "items-outlive-response"
    assert "inside your policy" in detail
    assert "conv_x1" in detail and "retained until deleted" in detail
    lines = repair_lines(state)
    assert any("not enough here" in line for line in lines)
    assert any("items/{item_id}" in line for line in lines)
    assert any("does not delete its items" in line for line in lines)
    # And the same warning rides along when the response is also over policy.
    over = grade_response(resp("resp_c11", 91.0, "conv_x1"), 200, NOW, 30)
    assert over[0] == "retained-past-policy"
    assert "retained until deleted" in over[1]


def test_volume_and_idleness_are_two_findings_on_one_object():
    busy = item_totals(items(4182, newest_days_old=0.5))
    assert busy["count"] == 4182 and busy["newest"] > busy["oldest"]
    state, detail = grade_conversation({"id": "conv_x1"}, busy, 200, NOW, 30, 500)
    assert state == "thread-unbounded"
    assert "4182 item(s) and no TTL" in detail
    assert any("seeded with a summary" in line for line in repair_lines(state))
    # A small thread nobody has touched is the other finding entirely.
    idle = item_totals(items(12, newest_days_old=211.4))
    state, detail = grade_conversation({"id": "conv_y7"}, idle, 200, NOW, 30, 500)
    assert state == "thread-idle"
    assert "211.4 day(s) ago" in detail
    assert "retained until deleted" in detail
    # Busy and recent is neither.
    fine = item_totals(items(12, newest_days_old=1.0))
    assert grade_conversation({}, fine, 200, NOW, 30, 500)[0] == "thread-within-policy"
    assert grade_conversation(None, None, 404, NOW, 30, 500)[0] == "not-retained"


def test_ids_are_routed_by_prefix_and_what_cannot_be_routed_is_kept():
    records = parse_records("resp_a19\\n\\n# exported 2026-08-31\\nconv_x1\\n"
                            "resp_a19\\nlegacy-7742  # old schema\\n   \\nconv_y7\\n")
    assert records["responses"] == ["resp_a19"]
    assert records["conversations"] == ["conv_x1", "conv_y7"]
    assert records["unrecognised"] == ["legacy-7742"]
    assert parse_records("") == {"responses": [], "conversations": [],
                                 "unrecognised": []}
    assert any("hole in a coverage figure" in line
               for line in repair_lines("unrecognised-id"))


def test_the_coverage_sentence_is_printed_whatever_the_run_found():
    note = coverage_note({"responses": ["resp_a19"] * 388,
                          "conversations": ["conv_x1"] * 22,
                          "unrecognised": ["x", "y"]})
    assert "412 id(s) supplied" in note
    assert "388 response(s), 22 conversation(s), 2 unroutable" in note
    assert "has a list endpoint" in note
    assert "your records and not your account" in note
    # Even an empty run says it, because the limitation is not a result.
    assert "has a list endpoint" in coverage_note({})
    assert "0 id(s) supplied" in coverage_note(None)
    assert age_days(0, NOW) is None and age_days("x", NOW) is None
    assert item_totals(None) == {"count": 0, "oldest": 0, "newest": 0}
''',
"test_js_file": "openai-stored-state-probe.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { RESPONSE_RETENTION_FLOOR_DAYS, ageDays, coverageNote, gradeConversation,
         gradeResponse, itemTotals, parseRecords, repairLines,
         responseRow } from './openai-stored-state-probe.mjs';

const NOW = 1_800_000_000;
const DAY = 86400;

const resp = (id, daysOld, conversation = null) => responseRow({
  id, object: 'response', status: 'completed',
  created_at: NOW - Math.trunc(daysOld * DAY),
  conversation: conversation ? { id: conversation } : null,
  metadata: { tenant: 'acme' },
});

const items = (n, newestDaysOld = 1) => Array.from({ length: n }, (_, i) => ({
  id: `msg_${i}`, type: 'message',
  created_at: NOW - Math.trunc((newestDaysOld + n - i - 1) * DAY),
}));

test('retention is read as a floor and a 404 keeps both its causes', () => {
  const [state, detail] = gradeResponse(resp('resp_a19', 94.2), 200, NOW, 30);
  assert.equal(state, 'retained-past-policy');
  assert.ok(detail.includes('still readable 94.2 day(s)'));
  assert.ok(detail.includes('past your 30 day policy'));
  assert.ok(detail.includes(`at least ${RESPONSE_RETENTION_FLOOR_DAYS} days`));
  assert.ok(detail.includes('a floor and not a deadline'));
  const lines = repairLines(state);
  assert.ok(lines.some((l) => l.includes('DELETE /v1/responses/{response_id}')));
  assert.ok(lines.some((l) => l.includes('id ledger')));
  const [gone, goneDetail] = gradeResponse(null, 404, NOW, 30);
  assert.equal(gone, 'not-retained');
  assert.ok(goneDetail.includes('store false') && goneDetail.includes('aged out'));
  assert.deepEqual(repairLines(gone), []);
  assert.equal(gradeResponse(resp('resp_z1', 1), 403, NOW, 30)[0], 'probe-unreadable');
});

test('the row has no chain in it and no store flag', () => {
  const row = responseRow({ id: 'resp_b40', created_at: 1700000000,
                            previous_response_id: 'resp_a01', status: 'completed',
                            conversation: { id: 'conv_x1' },
                            metadata: { tenant: 'acme', env: 'prod' } });
  assert.deepEqual(row, { id: 'resp_b40', created_at: 1700000000,
                          status: 'completed', conversation: 'conv_x1',
                          metadata_keys: 2 });
  assert.ok(!('previous_response_id' in row));
  assert.ok(!('store' in row) && !('stored' in row));
  assert.equal(responseRow(null).id, '');
  assert.equal(responseRow({ created_at: 'nonsense' }).created_at, 0);
  assert.equal(responseRow({ metadata: 'nope' }).metadata_keys, 0);
});

test('deleting the conversation does not delete its items', () => {
  const [state, detail] = gradeResponse(resp('resp_b40', 4.1, 'conv_x1'), 200, NOW, 30);
  assert.equal(state, 'items-outlive-response');
  assert.ok(detail.includes('inside your policy'));
  assert.ok(detail.includes('conv_x1') && detail.includes('retained until deleted'));
  const lines = repairLines(state);
  assert.ok(lines.some((l) => l.includes('not enough here')));
  assert.ok(lines.some((l) => l.includes('items/{item_id}')));
  assert.ok(lines.some((l) => l.includes('does not delete its items')));
  const over = gradeResponse(resp('resp_c11', 91, 'conv_x1'), 200, NOW, 30);
  assert.equal(over[0], 'retained-past-policy');
  assert.ok(over[1].includes('retained until deleted'));
});

test('volume and idleness are two findings on one object', () => {
  const busy = itemTotals(items(4182, 0.5));
  assert.equal(busy.count, 4182);
  assert.ok(busy.newest > busy.oldest);
  const [state, detail] = gradeConversation({ id: 'conv_x1' }, busy, 200, NOW, 30, 500);
  assert.equal(state, 'thread-unbounded');
  assert.ok(detail.includes('4182 item(s) and no TTL'));
  assert.ok(repairLines(state).some((l) => l.includes('seeded with a summary')));
  const idle = itemTotals(items(12, 211.4));
  const [idleState, idleDetail] = gradeConversation({ id: 'conv_y7' }, idle, 200,
                                                    NOW, 30, 500);
  assert.equal(idleState, 'thread-idle');
  assert.ok(idleDetail.includes('211.4 day(s) ago'));
  assert.ok(idleDetail.includes('retained until deleted'));
  const fine = itemTotals(items(12, 1));
  assert.equal(gradeConversation({}, fine, 200, NOW, 30, 500)[0], 'thread-within-policy');
  assert.equal(gradeConversation(null, null, 404, NOW, 30, 500)[0], 'not-retained');
});

test('ids are routed by prefix and what cannot be routed is kept', () => {
  const records = parseRecords('resp_a19\\n\\n# exported 2026-08-31\\nconv_x1\\n'
    + 'resp_a19\\nlegacy-7742  # old schema\\n   \\nconv_y7\\n');
  assert.deepEqual(records.responses, ['resp_a19']);
  assert.deepEqual(records.conversations, ['conv_x1', 'conv_y7']);
  assert.deepEqual(records.unrecognised, ['legacy-7742']);
  assert.deepEqual(parseRecords(''), { responses: [], conversations: [], unrecognised: [] });
  assert.ok(repairLines('unrecognised-id').some((l) => l.includes('hole in a coverage figure')));
});

test('the coverage sentence is printed whatever the run found', () => {
  const note = coverageNote({ responses: Array(388).fill('resp_a19'),
                              conversations: Array(22).fill('conv_x1'),
                              unrecognised: ['x', 'y'] });
  assert.ok(note.includes('412 id(s) supplied'));
  assert.ok(note.includes('388 response(s), 22 conversation(s), 2 unroutable'));
  assert.ok(note.includes('has a list endpoint'));
  assert.ok(note.includes('your records and not your account'));
  assert.ok(coverageNote({}).includes('has a list endpoint'));
  assert.ok(coverageNote(null).includes('0 id(s) supplied'));
  assert.equal(ageDays(0, NOW), null);
  assert.equal(ageDays('x', NOW), null);
  assert.deepEqual(itemTotals(null), { count: 0, oldest: 0, newest: 0 });
});
''',
"faq": [
 ("Can I get a list of everything we have stored?",
  "No, and that is the fact this note is built on rather than a gap in the script. Neither /v1/responses nor /v1/conversations has a list endpoint; both are reachable only by an id you already hold. So the honest answer to a retention question is bounded by your own records, the script prints that sentence on every run next to the number of ids it probed, and the first repair for an application that keeps no ids is to start keeping them with a created-at. That column is the only inventory that can exist."),
 ("Is retention 30 days or not?",
  "It depends which page you read, and the difference matters here. The conversation-state guide says response objects are saved for 30 days by default. The data-retention page says stored response data will be kept for at least 30 days. For a note about whether a thread will still resolve next week, the first reading is the useful one and 30 days is a deadline. For a note about what you are holding, the second is the operative one and 30 days is a floor: an object you have not deleted is one you are still holding, and nothing tells you for how much longer. Conversations are simpler and worse: the retention table says until deleted."),
 ("Why not just read the store field back off the response?",
  "Because there is not one. store appears in the create request and does not appear anywhere in the retrieved Response object, so there is nothing to read back. That is why a 200 is treated as the only evidence that a response was stored, and why a 404 comes back with both of its causes named (created with store false, or already aged out) instead of being resolved into whichever is more convenient. The script never prints a store value it did not receive."),
 ("We deleted all our old conversations. Are we clean?",
  "Probably not, and this is the most expensive detail in the note. Deleting a conversation does not delete the items inside it, and that behaviour is documented on the delete call itself. So a sweep that walks conversation ids and deletes each one removes the container and leaves every message body in place, while reporting complete success. The repair here is printed in the order the work has to happen: delete the items first, then the conversation."),
 ("How is this different from the note about previous_response_id?",
  "Same GET, opposite question, and the retention number even means the opposite thing in each. That note walks a chain of parents upward and asks whether the next turn on a thread will still resolve, so for it thirty days is a deadline after which a link vanishes and the finding is a broken conversation. This one never follows a parent at all (the row it builds has no previous_response_id in it, and there is a test that fails if one appears) and it asks how old the objects are, how many items a thread has accumulated, and whether either is past a rule you wrote down."),
],
"related": [REL_CHAIN, REL_ZDR, REL_QUOTA],
"citations": [CITE_OAI_DATA, CITE_OAI_STATE, CITE_OAI_RESP, CITE_OAI_CONV],
},
]
