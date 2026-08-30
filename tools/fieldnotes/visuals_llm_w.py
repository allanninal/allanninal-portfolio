#!/usr/bin/env python3
"""Diagrams for the /llm/ field notes, batch W.

Five terminal states of an asynchronous job that no exception announces. The
section already has four batch diagrams, so the risk here is five more pictures
of a list being read, which would say nothing. Each of these five is drawn
around the one thing its script sees that the other four cannot.

`llmbval` is the shortest problem chain in the batch, because the failure
happens two steps in and everything after it is silence. The batch never runs,
so there is no output, no billing and no counts, and the fix branch spends its
first outcome on a line number rather than on a status.

`llmbcanc` has the cancel in the middle of the chain instead of at the end. The
point of the drawing is that the arrow after the cancel still carries work: the
rows that were already through the model are finished, and the failing step is
the re-run, not the cancel. The fix branch is the only one in the batch whose
outcomes are about arithmetic on two counts.

`llmbgres` is not a batch at all, and the diagram keeps it that way. Its chain
starts at a 200 that means "accepted" and ends at a job that is still spending
money, with the worker disappearing in the middle. The fix branch has six
outcomes because the status enum has six values, and four of them are drawn as
failures on purpose.

`llmbout` is a clock drawn twice. Its problem chain has no fault in it anywhere
until the last step, where a deletion that was always scheduled arrives, and the
fix branch is ordered by what can still be saved rather than by what went wrong.
This is the one that has to read differently from the published error file note,
so its source box says which file id it is holding.

`llmbqdep` is the only one with nothing broken in it. Every batch in the picture
is healthy and inside its window; what fails is a submission somewhere else
entirely, which is why the failing arrow points at a box belonging to another
team. The fix branch grades a ratio rather than a state.

Drawn in teal, matching the rest of the section. No em dashes inside SVG text:
one mis-sniffed encoding turns a single character into three mojibake ones
inside an image, where nothing will catch it.
"""
import diagrams as D

# Set before the diagrams below are built, restored at the bottom of the module.
# Every diagram here is constructed at import time, so the theme has to be
# active across exactly this file and no further.
BRAND = "#0D9488"
D.set_theme(BRAND)

V = {}

V["llm/batch-failed-input-validation"] = {
    "flow_intro": (
        "Two hundred is a receipt for a batch object, not a promise that the "
        "batch will run. Between creation and the first request there is a "
        "validation pass over every line of the input file, and a single bad "
        "row fails the whole job rather than the row. Nothing is billed and "
        "nothing is produced, so the only trace is a status and an errors "
        "array holding the line numbers, sitting on an object nobody polled."
    ),
    "diagram_problem": D.chain(
        "llmbval-p",
        "How a batch dies forty seconds after the submitter logs success",
        "Every step here worked on its own terms. The upload was accepted, the "
        "batch was created, and the enrichment table simply stopped growing.",
        [
            ("File uploaded", "bytes accepted, not parsed"),
            ("Batch created, 200 back", "submitter logs success, exits"),
            ("Validation refuses it", "status failed, nothing ran"),
            ("No rows, no error, no bill", "there is nothing to catch"),
            ("Stale table noticed", "by a person, weeks later"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "llmbval-f",
        "Sorting failed batches by error code and then by input line number",
        "Two GETs. The batch list gives the code and the line; the file list "
        "gives the upload that never became a batch at all.",
        ("Batch list, then file list", "no status filter exists"),
        [
            ("Failed, with line numbers", "grouped by code, printed", "bad"),
            ("Failed, errors empty", "validate the file locally", "bad"),
            ("Orphan .jsonl, wrong purpose", "refused before a batch existed", "bad"),
            ("Completed with failed rows", "a different note entirely", "plain"),
            ("Nothing failed in the window", "keep the poll assertion", "good"),
        ],
    ),
}

V["llm/batch-cancelled-partial-results"] = {
    "flow_intro": (
        "Cancel stops the requests that have not been dispatched. It does not "
        "reach back for the ones already through the model, which are "
        "finished, billed and written to the output. The expensive step is the "
        "one after the cancel, where the whole batch is submitted again and "
        "the overlap is paid for twice. Two counts on the batch object are the "
        "entire reading."
    ),
    "diagram_problem": D.chain(
        "llmbcanc-p",
        "How a cancel and a re-run bill the same rows twice",
        "The cancel was the right call. What follows it is the mistake, and "
        "the batch object was holding the evidence the whole time.",
        [
            ("Batch running", "two thirds of the way through"),
            ("Deploy, somebody cancels", "the right call at the time"),
            ("Finished rows are kept", "billed, and in the output"),
            ("Whole batch re-run", "the overlap paid for again"),
            ("Invoice slightly larger", "no incident, no alert"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "llmbcanc-f",
        "Splitting finished work from cancelled work on both providers",
        "One list per provider. The finished count is what a naive re-run "
        "would buy a second time.",
        ("Two batch lists", "cancel timestamps and counts"),
        [
            ("Finished count above zero", "subtract before re-running", "bad"),
            ("Still cancelling after an hour", "it has not stopped yet", "bad"),
            ("Cancelled before anything ran", "nothing to salvage, no cost", "good"),
            ("Claude counts, billing known", "canceled rows are not billed", "plain"),
            ("OpenAI counts, billing a floor", "confirm against the cost report", "plain"),
        ],
    ),
}

V["llm/background-response-never-polled"] = {
    "flow_intro": (
        "Background mode moves the failure out of your process and onto a "
        "stored object. The request is accepted in milliseconds, the model "
        "works for twenty minutes, and the result exists in exactly one place: "
        "a response whose status has six values, four of which are not "
        "success. There is no list endpoint, so the audit can only reach the "
        "ids you wrote down, which makes that write the real failure point."
    ),
    "diagram_problem": D.chain(
        "llmbgres-p",
        "How a redeploy strands a job that keeps running and keeps billing",
        "Nothing in this sequence raises. The job is fine, the platform is "
        "fine, and the only broken part is a loop that stopped.",
        [
            ("Job accepted, 200 back", "queued, id written down"),
            ("Worker redeployed", "the poller never restarts"),
            ("Job runs on regardless", "queued, then in progress"),
            ("Terminal status arrives", "failed, and nobody reads it"),
            ("Result billed, discarded", "table row still says pending"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "llmbgres-f",
        "Bucketing every response id you hold by its documented status",
        "One GET per id, because the collection cannot be listed. Four of the "
        "six statuses need an action, and a 404 needs context you supply.",
        ("Ids from your own table", "the audit's whole universe"),
        [
            ("Queued past your service level", "still running, still billing", "bad"),
            ("Failed, transient code", "retry server_error and 429s", "bad"),
            ("Failed, invalid prompt", "escalate, retries never help", "bad"),
            ("Not found, ordinary project", "the result is gone", "bad"),
            ("Not found, zero retention", "documented, kept ten minutes", "plain"),
            ("Completed or inside the SLA", "the poller is doing its job", "good"),
        ],
    ),
}

V["llm/batch-output-file-never-downloaded"] = {
    "flow_intro": (
        "This is the mirror of the published error file note. That one reads "
        "the id holding the rows that failed; this one reads the id holding "
        "the work itself, which is why losing it costs money rather than "
        "knowledge. Neither API records whether you downloaded anything, so "
        "the second half of the join is your own ingest ledger, and the clock "
        "runs from completion on one provider and creation on the other."
    ),
    "diagram_problem": D.chain(
        "llmbout-p",
        "How finished work is deleted on schedule without anyone deciding to",
        "There is no fault anywhere in this chain. A retention policy that "
        "was always documented simply arrives.",
        [
            ("Batch submitted nightly", "by a job that still works"),
            ("Consumer switched off", "during an incident, in March"),
            ("Results written, unread", "billed in full, collected never"),
            ("Retention window closes", "29 or 30 days, by provider"),
            ("Only repair is re-running", "and paying for it again"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "llmbout-f",
        "Ranking unclaimed batch output by how much runway is left on it",
        "The output file id, not the error file id. Ordered by what you can "
        "still save rather than by what is largest.",
        ("Batch lists plus your ledger", "output_file_id and results_url"),
        [
            ("Days left on the clock", "download today, it is recoverable", "bad"),
            ("File id no longer resolves", "gone, re-run and re-pay", "bad"),
            ("Ended, not in the ledger", "sweep it before the clock runs", "bad"),
            ("Open past 24 hours", "a stale object, not a slow job", "bad"),
            ("No ledger supplied at all", "nothing can be called consumed", "plain"),
            ("In the ledger, runway left", "the reconciler is working", "good"),
        ],
    ),
}

V["llm/batch-queue-limit-reached"] = {
    "flow_intro": (
        "Nothing in this reading is broken. Every batch is healthy and inside "
        "its window, and the failure lands on somebody else: a submission "
        "refused with a 429 while the Messages API sits idle. The ceiling is "
        "one number on an Admin endpoint and the depth is a sum over a "
        "workspace's live batches, which means the two halves need two "
        "credentials that cannot read each other's data."
    ),
    "diagram_problem": D.chain(
        "llmbqdep-p",
        "How one backfill refuses another team's submissions for hours",
        "The team that sees the error is not the team holding the capacity, "
        "and no view anywhere connects the two.",
        [
            ("Backfill enqueues 400k rows", "one submission, one workspace"),
            ("Queue near the org ceiling", "shared across every model"),
            ("Another team submits", "429 on the batch endpoint"),
            ("Messages API looks idle", "so the dashboards say fine"),
            ("Queued work slows too", "and starts running out of window"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "llmbqdep-f",
        "Grading live queue depth against the configured enqueued ceiling",
        "Two credentials, two scopes. The ceiling is organization wide and "
        "the depth is per workspace, so the reading is a lower bound.",
        ("Ceiling and live depth", "Admin key plus workspace key"),
        [
            ("Depth at the ceiling", "submissions refused right now", "bad"),
            ("Depth past your threshold", "the next one may not land", "bad"),
            ("Ceiling could not be read", "a raw count, not a ratio", "bad"),
            ("One workspace measured", "a lower bound, not a total", "plain"),
            ("Headroom, batches draining", "nothing to schedule around", "good"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
