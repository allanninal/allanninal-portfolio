#!/usr/bin/env python3
"""Diagrams for the /llm/ field notes, batch D.

The Batch API four times. Three failures and one invoice, and the diagrams have
to keep them apart: a word that was read too generously, a file nobody opened, a
clock that ran out, and a workload on the wrong endpoint at twice the price. The
problem chains differ because the failures differ, and every fix is a branch,
because each script sorts what it finds rather than guessing at it. Drawn in teal.

No em dashes inside SVG text. One mis-sniffed encoding turns a single character
into three mojibake ones inside an image, where nothing will catch it.
"""
import diagrams as D

# Set before the diagrams below are built, restored at the bottom of the module.
# Every diagram here is constructed at import time, so the theme has to be active
# across exactly this file and no further: visuals.py imports several of these
# modules in one process, and a theme left set would silently retint whichever
# section happened to be imported next.
BRAND = "#0D9488"
D.set_theme(BRAND)

V = {}

V["llm/batch-partial-failure-unnoticed"] = {
    "flow_intro": (
        "The script asks for the batch list and then ignores the field everyone "
        "reads. The finding is arithmetic on three integers, and the reason it "
        "is a function rather than a condition is that they can disagree in two "
        "ways: rows that ran and failed, and rows that never ran at all."
    ),
    "diagram_problem": D.chain(
        "llmbpart-p",
        "A batch that finishes, reports completed, and hands back fewer rows than it took",
        "Nothing in this chain returns an error. The output file is valid, it is "
        "simply shorter than the file that went in.",
        [
            ("50,000 rows submitted", "one jsonl, one call"),
            ("Poller waits", "for status completed"),
            ("Status turns completed", "the word everyone wanted"),
            ("failed: 869", "three fields further down"),
            ("Table loads short", "no null, no exception"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "llmbpart-f",
        "Sorting batches by what request_counts actually adds up to",
        "Rows that failed are in the error file. Rows in neither column are not, "
        "so the two findings cannot print the same sentence.",
        ("request_counts read", "instead of status"),
        [
            ("failed above zero", "ran and failed, in the error file", "bad"),
            ("completed below total", "never attempted, not in any file", "bad"),
            ("Both halves agree", "the only clean batch there is", "good"),
            ("No counts at all", "unreadable, never a pass", "plain"),
        ],
    ),
}

V["llm/batch-error-file-never-read"] = {
    "flow_intro": (
        "Half of this question is answerable from the API and half is not. The "
        "file object proves the failures exist and are not empty; nothing on it "
        "records whether anyone opened it, so the ingest record has to come from "
        "your side and the retention clock decides how long the answer is useful."
    ),
    "diagram_problem": D.chain(
        "llmberr-p",
        "Failures written to a second file that the ingest code was never taught to open",
        "The pipeline was written against a test batch that had no failures, so "
        "the second file id has never once been needed.",
        [
            ("Batch completes", "two files, not one"),
            ("output_file_id read", "parses cleanly"),
            ("error_file_id ignored", "no code path opens it"),
            ("Rows silently absent", "nothing to be null"),
            ("Day 30, file expires", "the list is gone"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "llmberr-f",
        "Sorting error files by whether they hold anything and how long they last",
        "An empty error file sends somebody after nothing, and a file past day 30 "
        "is a different job from one with three weeks left.",
        ("File object plus", "your own ingest record"),
        [
            ("Bytes, not in the record", "failures waiting to be read", "bad"),
            ("Bytes, days from expiry", "read it before the window shuts", "bad"),
            ("Past the 30 day window", "unrecoverable by any read call", "bad"),
            ("Zero bytes, or fetched", "nothing left to do here", "good"),
        ],
    ),
}

V["llm/batch-expired-past-24h-window"] = {
    "flow_intro": (
        "Two questions from one list. The batches that already expired are a "
        "count of rows that will never run, and the batches still moving are the "
        "half worth automating: a subtraction against expires_at, while there is "
        "still time to submit the tail as a second job."
    ),
    "diagram_problem": D.chain(
        "llmbexp-p",
        "A fixed 24 hour window closing on a job that a poller still thinks is running",
        "The create call returned 200 a day earlier. Expired is terminal, so a "
        "loop waiting for completed waits for something that cannot arrive.",
        [
            ("Batch created", "200, status validating"),
            ("Queue does not drain", "50,000 rows, one window"),
            ("24h from in_progress_at", "not configurable"),
            ("Status turns expired", "30,000 rows abandoned"),
            ("Poller still waiting", "the job hangs, it does not fail"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "llmbexp-f",
        "Sorting batches by how much of the completion window is left",
        "expires_at is the API's own answer. Falling back to created_at over "
        "states the time remaining, so the report says which one it used.",
        ("Deadline resolved", "then compared to now"),
        [
            ("Already expired", "count the rows that never ran", "bad"),
            ("Past the deadline, still running", "the tail is not coming", "bad"),
            ("Hours of window left", "split it now, not tomorrow", "bad"),
            ("Room left, or settled", "nothing to do yet", "good"),
        ],
    ),
}

V["llm/batch-discount-left-unused"] = {
    "flow_intro": (
        "Nothing here failed, so there is no error to trace. The evidence is the "
        "shape of the traffic in hourly buckets: a week of requests folded per "
        "workload, and the share of them that lands in the busiest few hours. A "
        "schedule spikes. An audience does not."
    ),
    "diagram_problem": D.chain(
        "llmbdisc-p",
        "A nightly job inheriting interactive pricing because the first prototype was interactive",
        "No request failed and no alert should have fired. The only artefact is "
        "a total larger than a counterfactual nobody computed.",
        [
            ("Prototype is synchronous", "a person at a terminal"),
            ("Job copies the prototype", "same client, same call"),
            ("40,000 calls at 02:00", "nobody waiting on any of them"),
            ("Billed at full rate", "batch would be half"),
            ("Invoice looks normal", "a discount not taken"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "llmbdisc-f",
        "Sorting workloads by whether their request volume is spiky or spread out",
        "Interactive and already batched are answers, not gaps in the detection. "
        "Only clustered synchronous volume is a cost finding.",
        ("Hourly request counts", "per project and model"),
        [
            ("Clustered in a few hours", "a schedule paying interactive prices", "bad"),
            ("Spread across the week", "synchronous is the right endpoint", "good"),
            ("Mostly batch already", "the discount is being taken", "good"),
            ("Below the volume floor", "too small to draw a shape from", "plain"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
