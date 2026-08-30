#!/usr/bin/env python3
"""Diagrams for the /llm/ field notes, batch R.

Four states of a retrieval index, and the thing they share is the reason they
need four diagrams rather than one: every chain here ends in a 200. The file
search tool does not raise on a store whose files never indexed, on a store
with nothing in it, on a store that deleted itself last Tuesday, or on a store
that has been billing bytes nobody queried since March. The failure arrives as
a worse answer, which is the one output nobody is monitoring.

The two closest chains are the first two, and they are drawn to be told apart.
`llmvsfail` has files in it: the attach call was accepted, the parse failed
afterwards, and the store carries a `failed` count it never surfaces. `llmvsnil`
has nothing in it at all, which is a different fault with a different repair,
and its fix branch spends one of its five outcomes handing the reading back to
the first note when the store turns out to have attached files that simply never
completed. A branch outcome whose job is to say "not mine" is worth its slot.

The last one is the only chain here that is not about correctness. Bytes are a
stock rather than a flow, so its shape is a line that never comes back down,
and its fix branch grades a slope against a query count rather than a state
against an enum.

Drawn in teal, matching the rest of the section. No em dashes inside SVG text:
one mis-sniffed encoding turns a single character into three mojibake ones
inside an image, where nothing will catch it.
"""
import diagrams as D

# Set before the diagrams below are built, restored at the bottom of the module.
# Every diagram here is constructed at import time, so the theme has to be
# active across exactly this file and no further: visuals.py imports several of
# these modules in one process, and a theme left set would silently retint
# whichever section happened to be imported next.
BRAND = "#0D9488"
D.set_theme(BRAND)

V = {}

V["llm/vector-store-file-attach-failed"] = {
    "flow_intro": (
        "The attach call is the last thing in this chain that anybody watches, "
        "and it succeeds. Parsing, chunking and embedding happen afterwards on "
        "the server, and the only record that any of it went wrong is a "
        "per-file field on a listing nobody requests. The store's own summary "
        "does not help: its status turns to completed once no file is still "
        "in progress, which is true whether the files succeeded or failed."
    ),
    "diagram_problem": D.chain(
        "llmvsfail-p",
        "How a file that never indexed leaves the store looking healthy",
        "Every step returns success. The document is missing from retrieval "
        "from the moment the ingest job declares itself finished.",
        [
            ("Attach returns 200", "status in_progress"),
            ("Parse runs server side", "minutes later, elsewhere"),
            ("Scanned PDF, no text", "last_error is set"),
            ("Store status completed", "means nothing is pending"),
            ("Retrieval misses it", "quietly, on every query"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "llmvsfail-f",
        "Sorting one store by its per file errors and its own counts",
        "The per file listing and the store's summary are read together, "
        "because a disagreement between them is itself a finding.",
        ("Files in one store", "last_error against file_counts"),
        [
            ("unsupported_file", "convert or OCR at source", "bad"),
            ("invalid_file", "empty, corrupt or encrypted", "bad"),
            ("server_error", "transient, re attach it", "bad"),
            ("Still in progress for hours", "pinned, not slow", "plain"),
            ("No files attached at all", "the empty store note", "plain"),
        ],
    ),
}

V["llm/empty-vector-store-still-referenced"] = {
    "flow_intro": (
        "This one is only visible from the application side, because an empty "
        "store is a perfectly ordinary object until you know that something "
        "still names it. So the script takes the ids your code configures as "
        "input and reads the platform for the answer, which is the reverse of "
        "every other note in the batch. An id that does not resolve at all is "
        "the same failure one step further along."
    ),
    "diagram_problem": D.chain(
        "llmvsnil-p",
        "How an index with nothing in it keeps answering questions",
        "The tool call succeeds, the model answers, and the answer is drawn "
        "from training data rather than from your documents.",
        [
            ("Store created first", "id copied into config"),
            ("Ingest never finished", "or expired since"),
            ("Config still names it", "nothing revalidates ids"),
            ("file_search returns 200", "with zero citations"),
            ("Model answers anyway", "confident, ungrounded"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "llmvsnil-f",
        "Grading only the store ids the application actually configures",
        "Emptiness alone is not a finding. An abandoned empty store costs "
        "nothing and grounds nothing, because nothing points at it.",
        ("Configured store ids", "read back from the API"),
        [
            ("Zero files ever attached", "ingestion never ran", "bad"),
            ("Id does not resolve", "wrong project, or deleted", "bad"),
            ("Files attached, none done", "the attach failure note", "plain"),
            ("Empty and unreferenced", "litter, not an outage", "plain"),
            ("Completed files present", "grounded, nothing to do", "good"),
        ],
    ),
}

V["llm/vector-store-expired-or-expiring"] = {
    "flow_intro": (
        "The only note in the batch whose finding is in the future. An "
        "expiration policy is a countdown anchored to the last time the store "
        "was active, so it runs fastest exactly when nobody is looking at the "
        "store, and it takes the contained file objects with it when it "
        "fires. Read the expiry the API reports rather than recomputing it: "
        "which operations count as activity is not something the API states."
    ),
    "diagram_problem": D.chain(
        "llmvsexp-p",
        "How an idle store runs its own countdown to deletion",
        "Nothing warns anybody. The store is fine, then it is expired, and "
        "the files it held are not recoverable from it.",
        [
            ("Policy set at creation", "seven days, idle anchored"),
            ("Feature ships, traffic dips", "the clock keeps running"),
            ("Idle window passes", "no notice either way"),
            ("Status turns expired", "contained files deleted"),
            ("Search returns nothing", "and still returns 200"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "llmvsexp-f",
        "Sorting stores by the clock the API itself reports",
        "expires_at as returned is the countdown. A recomputed one is a "
        "guess about what counts as activity.",
        ("Every store with a policy", "expires_at against now"),
        [
            ("Already expired", "re ingest, files are gone", "bad"),
            ("Expires inside the window", "clear the policy first", "bad"),
            ("Policy on a permanent store", "nobody chose this", "bad"),
            ("Reported expiry drifts", "trust the API, not the sum", "plain"),
            ("No policy at all", "permanent, and billed", "good"),
        ],
    ),
}

V["llm/vector-store-storage-cost-creeping"] = {
    "flow_intro": (
        "Every other line on the bill is a flow: it falls to zero when the "
        "traffic stops. Storage is a stock, so it keeps billing whether "
        "anyone queries it or not, and the shape that gives it is a line that "
        "only ever goes up. The reading needs two series rather than one, and "
        "they do not have the same granularity: bytes come back per project, "
        "while file search calls can be grouped per store."
    ),
    "diagram_problem": D.chain(
        "llmvsbyte-p",
        "How retained bytes outlive every project that created them",
        "No step is a mistake. The cost of the whole chain is small enough "
        "each month to stay under the threshold that would prompt a question.",
        [
            ("Corpus indexed for a demo", "a good afternoon's work"),
            ("Demo becomes a feature", "or quietly does not"),
            ("Nobody owns deletion", "it was never a ticket"),
            ("Billed on bytes retained", "in gibibyte hours"),
            ("Line grows every month", "queries do not follow"),
        ],
        fail_at=4,
    ),
    "diagram_fix": D.branch(
        "llmvsbyte-f",
        "Grading ninety days of retained bytes against retrieval volume",
        "A slope on its own is not a finding. Bytes rising alongside queries "
        "is a corpus doing its job and gets graded as such.",
        ("Bytes over ninety days", "against file search calls"),
        [
            ("Bytes climb, queries flat", "paying to retain, not to use", "bad"),
            ("Stores with zero searches", "pure retained waste", "bad"),
            ("Bytes and queries both rise", "growth, priced correctly", "plain"),
            ("No storage line item yet", "under the billed floor", "plain"),
            ("Flat bytes, live queries", "a corpus doing its job", "good"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
