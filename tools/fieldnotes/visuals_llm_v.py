#!/usr/bin/env python3
"""Diagrams for the /llm/ field notes, batch V.

Four assumptions that stop holding the day the model, or the stored object
underneath, changes. Drawn carefully, because "a migration broke it" is a shape
that could be reused four times without anyone noticing. Each chain here fails
at a different place for a different reason.

`llmtkdlt` fails at the point where nothing goes wrong. Its problem chain has no
error in it at all: the migration succeeds, the numbers move, and the damage
arrives three weeks later in a finance channel. The fix branch is the only one in
the batch whose outcomes are about a ratio rather than about a status.

`llmfingr` is the note that had to be rebuilt around what a read-only script can
reach, and the diagram says so: the source box is stored completions rather than
a probe, because the obvious canary is a request this section will not send. Its
fix branch spends one whole outcome on a signal that is simply absent, which is
the honest half of the note and the one most likely to be dropped.

`llmchain` is drawn as a linked list with a clock on it. The failing arrow is not
the newest link, which always works; it is the hop into a parent recorded a month
ago. That is the entire reading, so the chain is drawn backwards, from the turn
being served to the oldest thing it depends on.

`llmftfail` has a deploy in the middle of its problem chain and no failure
anywhere near the call that started it. The 200 comes back on the left, the
terminal status arrives on the right, and the gap between them is where nobody
was looking.

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

V["llm/token-counts-reused-across-tokenizers"] = {
    "flow_intro": (
        "There is no error anywhere in this failure, which is why it takes "
        "three weeks and three different people to assemble. A token count is "
        "a property of a string and a tokenizer, and the second half of that "
        "sentence was free to ignore until the tokenizer moved. The reading is "
        "two integers: the same body counted under the model you are leaving "
        "and the model you are moving to, with the ratio between them applied "
        "to every constant that was measured under the old one."
    ),
    "diagram_problem": D.chain(
        "llmtkdlt-p",
        "How a clean migration makes every token constant wrong at once",
        "Nothing failed. The evaluations were better and the rollout was "
        "boring. The number that broke was written down two years ago.",
        [
            ("Counts measured once", "on the model of the day"),
            ("Constants written down", "chunks, trims, capacity"),
            ("Migration ships", "evals better, no errors"),
            ("Same text counts more", "billing follows the count"),
            ("Spend and quality drift", "in three separate rooms"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "llmtkdlt-f",
        "Grading two token counts of one identical body under two model ids",
        "The outcome is a ratio rather than a pass. Both calls are free, and "
        "the only permitted difference between them is the model field.",
        ("One body, counted twice", "free, and creates nothing"),
        [
            ("Target counts more", "re-baseline every constant", "bad"),
            ("Bodies were not identical", "measures the harness, not the model", "bad"),
            ("Counts within two percent", "same tokenizer, nothing to do", "good"),
            ("413 on the count", "a byte ceiling, and another note", "plain"),
            ("One body sampled", "a reading, not a workload rate", "plain"),
        ],
    ),
}

V["llm/seed-determinism-unreliable"] = {
    "flow_intro": (
        "The obvious check here is a canary completion whose fingerprint you "
        "diff against a stored baseline, and this section does not send "
        "completions. What replaced it is stronger anyway: chat completions "
        "stored with store true can be listed, unlike stored responses, so the "
        "fingerprints are already sitting on the traffic that actually "
        "mattered. Group them by model, put them in order, and read the day "
        "the value changed."
    ),
    "diagram_problem": D.chain(
        "llmfingr-p",
        "How a backend change invalidates every baseline recorded before it",
        "The commit that broke the suite is not in your repository, and there "
        "is no release note to correlate it against.",
        [
            ("Baselines recorded", "seed pinned, temperature zero"),
            ("Suite green for months", "so the method looks sound"),
            ("Backend configuration moves", "fingerprint changes"),
            ("Same seed, new output", "diffs of one adjective"),
            ("Team re-records fixtures", "and learns to ignore it"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "llmfingr-f",
        "Sorting one model by the fingerprints on completions you already stored",
        "Nothing is sent. Absence of the field is an outcome of its own, "
        "because a signal you cannot read is not a signal.",
        ("Stored completions, in order", "grouped by model id"),
        [
            ("Two values, one switch", "baselines before it are void", "bad"),
            ("Values interleave", "two configurations at once", "bad"),
            ("No fingerprint at all", "undetectable, even in principle", "bad"),
            ("Nothing stored", "no evidence either way", "bad"),
            ("One value, whole window", "best effort holding, not a promise", "good"),
        ],
    ),
}

V["llm/previous-response-id-chain-broken"] = {
    "flow_intro": (
        "Server side conversation state looks like memory and behaves like a "
        "cache with a retention policy. Response objects are saved for 30 days "
        "by default, so a thread is exactly as durable as its oldest surviving "
        "link, and that is never the link you would think to test. The script "
        "walks each recorded chain upward, from the turn being served to the "
        "parent nobody has touched in a month."
    ),
    "diagram_problem": D.chain(
        "llmchain-p",
        "How a month old thread breaks on the turn after the gap",
        "The newest id resolves perfectly. The request fails on a parent that "
        "quietly aged out weeks ago.",
        [
            ("Thread starts in March", "one id chained forward"),
            ("Turns added for weeks", "each one works"),
            ("Parent passes 30 days", "retention, not deletion"),
            ("Next turn 404s", "on previous_response_id"),
            ("Assistant forgets user", "the most engaged one first"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "llmchain-f",
        "Grading a walked chain by its oldest link rather than its newest",
        "The leaf always passes, so it is never the reading. Every outcome "
        "here is a statement about the far end of the chain.",
        ("Chain walked to a root", "or to the first gap"),
        [
            ("A parent does not resolve", "the next turn will 404", "bad"),
            ("Oldest link near 30 days", "days of runway, not weeks", "bad"),
            ("Stopped at the hop limit", "the oldest link was never seen", "plain"),
            ("Every link on a conversation", "items persisted with no TTL", "good"),
            ("Root reached with runway", "durable for now, by the clock", "good"),
        ],
    ),
}

V["llm/fine-tune-job-failed-with-error-code"] = {
    "flow_intro": (
        "Creating a fine-tuning job is asynchronous, so the 200 that comes "
        "back is a receipt rather than a result. Validation and training "
        "failures surface on the job object and nowhere else: no exception, no "
        "email, and no change in a deploy that keeps working because it is "
        "still pointing at the old model. The job has been holding the error "
        "code, the offending parameter and an events feed the whole time."
    ),
    "diagram_problem": D.chain(
        "llmftfail-p",
        "How a job that failed on Thursday is discovered three weeks later",
        "Every step succeeded on its own terms. The upload was accepted, the "
        "job was accepted, and the deploy did exactly nothing.",
        [
            ("File uploaded", "bytes accepted, not parsed"),
            ("Job created, 200 back", "id pasted into a channel"),
            ("Validation fails later", "status failed, error set"),
            ("Deploy still on old model", "so nothing looks broken"),
            ("Asked about it in a meeting", "three weeks on"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "llmftfail-f",
        "Sorting fine-tuning jobs by terminal status and then by error code",
        "Two GETs. The job list gives the status and the code; the events feed "
        "gives the line that validation actually stopped on.",
        ("Every job, by status", "list plus events feed"),
        [
            ("Failed with a known code", "the documented fix, printed", "bad"),
            ("Failed with a new code", "printed verbatim, not guessed", "bad"),
            ("Hours in validating_files", "not progress, and unwatched", "bad"),
            ("Failed with no error object", "the events feed is all there is", "bad"),
            ("Succeeded", "a different note entirely", "good"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
