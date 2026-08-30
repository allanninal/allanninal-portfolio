#!/usr/bin/env python3
"""Diagrams for the /llm/ field notes, batch X.

Four server side objects that nobody owns once the upload call returns. That is
the premise, and the hazard is that "a thing accumulated" is one shape which
could be drawn four times with the nouns swapped. So each problem chain here
fails at a different place, and each fix branch grades a different kind of
answer: a total, a set difference, a date, and a probe.

`llmfquota` is the only one whose failure is in the future and lands on the
write path. Nothing in its chain goes wrong at all until the ceiling arrives,
and it arrives on an upload rather than on any read, which is why the fix branch
is the only one in the batch whose outcomes are quantities.

`llmforph` is a subtraction, so it is drawn as two sets rather than as a
sequence of states. The step that breaks is the one where the ownership graph is
removed and the objects it pointed at are not. Its fix branch keeps one whole
outcome for the case where the second set could not be read, because a set
difference against an incomplete set is a confident wrong answer.

`llmfexp` fails last, not in the middle. Every step before the final one
succeeds, including the one that lies: metadata that answers for weeks after the
content behind it stopped existing. The fix branch is the only one here that
grades a clock, and one of its outcomes is a field that is simply not returned.

`llmstored` has no enumeration to draw, which is the note. Its problem chain
ends with a question that has no query behind it, and its fix branch spends an
outcome saying that the coverage is your own records rather than the account.

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

V["llm/files-accumulating-against-storage-quota"] = {
    "flow_intro": (
        "Neither provider will tell you how full the file store is. There is "
        "no endpoint that returns a quota, a remaining figure or a percentage, "
        "so the only way to know is to walk every page of the listing and add "
        "the bytes up yourself. That is the whole script. What makes it worth "
        "running before the ceiling rather than after is that the ceiling "
        "arrives on an upload: reads keep working, the audit keeps passing, "
        "and the first thing that fails is the pipeline writing the next file."
    ),
    "diagram_problem": D.chain(
        "llmfquota-p",
        "How a file store fills up without a single failed read",
        "Every step here succeeded. Uploading is easy, deleting was never "
        "anybody's ticket, and the ceiling is only visible from inside it.",
        [
            ("A file per request", "uploaded, referenced once"),
            ("No expiry set", "the default is forever"),
            ("Ceiling reached", "and never reported before"),
            ("Uploads start to 400", "reads are all still fine"),
            ("Found on the write path", "in production, mid pipeline"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "llmfquota-f",
        "Grading a summed file store against a fixed ceiling and a per file cap",
        "The outcome is a quantity rather than a status. Two ceilings apply at "
        "once, and only one of them is about the total.",
        ("Every page, summed by purpose", "no endpoint reports this"),
        [
            ("Over the warning share", "uploads are what will fail", "bad"),
            ("One purpose dominates", "the class worth sweeping first", "bad"),
            ("A file near the per file cap", "a second ceiling entirely", "bad"),
            ("Nothing carries an expiry", "so the total only grows", "bad"),
            ("Well under, and ageing out", "a store with a lifecycle", "good"),
        ],
    ),
}

V["llm/orphaned-assistants-purpose-files"] = {
    "flow_intro": (
        "This is a subtraction rather than a measurement. One set is every file "
        "carrying a purpose whose owning API no longer exists; the other is "
        "every file id still reachable from a vector store, because stores and "
        "their files survived the shutdown that removed the assistants and "
        "threads pointing at them. What is left over is owned by nothing. The "
        "risk in the arithmetic is the second set: read it partially and the "
        "difference names files that are perfectly well referenced."
    ),
    "diagram_problem": D.chain(
        "llmforph-p",
        "How a shutdown removes the owners of files and leaves the files",
        "The migration guide is about code. Nothing in it walks your storage, "
        "and nothing had to, because storage kept working.",
        [
            ("Files uploaded for assistants", "purpose fixed at upload"),
            ("Attached to threads and stores", "the graph lived server side"),
            ("The API is shut down", "assistants and threads go"),
            ("Vector stores carry over", "so some files keep an owner"),
            ("The rest are billed forever", "referenced by nothing"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "llmforph-f",
        "Sorting one purpose class by whether a surviving vector store still holds it",
        "A set difference is only as good as the set being subtracted, so the "
        "case where that set is incomplete is an outcome and not a footnote.",
        ("Purpose class, minus store members", "two listings, one subtraction"),
        [
            ("In no surviving store", "an orphan, and still billed", "bad"),
            ("Code interpreter output", "nothing has referenced it since", "bad"),
            ("Held by a live store", "keep it, file search reads it", "good"),
            ("Stores unreadable", "the subtraction is not trustworthy", "plain"),
            ("The class is empty", "nothing was left behind", "good"),
        ],
    ),
}

V["llm/expired-files-still-referenced"] = {
    "flow_intro": (
        "An expiry that was set once at upload and cannot be changed afterwards "
        "is a deadline your code inherits without being told. The cruel part is "
        "what happens after it passes: the content stops being retrievable and "
        "the storage is released, but the metadata keeps answering for weeks, "
        "so the obvious existence check returns yes for a file that will fail "
        "every actual use. The script asks about the ids your application "
        "holds, in batches, and reads the date rather than the status code."
    ),
    "diagram_problem": D.chain(
        "llmfexp-p",
        "How a file that still answers a metadata call fails every real use",
        "Only the last step failed. The step before it is the one that did the "
        "damage, by answering a question with a stale yes.",
        [
            ("Expiry set at upload", "and never changeable again"),
            ("Id kept in your own table", "with no copy of the date"),
            ("expires_at passes", "content gone, quota released"),
            ("Metadata still answers", "so the id looks alive"),
            ("The request fails", "before inference, on the id"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "llmfexp-f",
        "Grading the ids an application holds against the expiry date on each one",
        "Every outcome here is a reading of a date, except the one that is "
        "about a date the endpoint declined to return.",
        ("Your own ids, asked in batches", "the date, not the status"),
        [
            ("Expiry already past", "every use of this id will fail", "bad"),
            ("Missing from the response", "gone past metadata as well", "bad"),
            ("Expiring inside the window", "and it cannot be extended", "bad"),
            ("No expiry field returned", "a header hid the whole check", "plain"),
            ("Live, with runway printed", "usable until the date shown", "good"),
        ],
    ),
}

V["llm/stored-responses-accumulating"] = {
    "flow_intro": (
        "Retention here was never chosen. Storing a response is the default, "
        "which means every prompt and every completion is persisted server side "
        "unless something explicitly opted out, and the objects that thread "
        "them together have no expiry at all. The hard part is not the policy, "
        "it is that neither collection can be listed. There is no query that "
        "answers what am I holding, so the script probes the ids you recorded "
        "and says plainly that its coverage is your logs and not your account."
    ),
    "diagram_problem": D.chain(
        "llmstored-p",
        "How server side state accumulates with no way to enumerate it",
        "Nothing here is a mistake anybody made. The default was taken, and "
        "the inventory that would show the result does not exist.",
        [
            ("store defaults on", "nothing had to opt in"),
            ("Prompt and output persisted", "whatever was in them"),
            ("Threads keep their items", "until somebody deletes them"),
            ("Ids leave your logs", "the objects do not"),
            ("Asked what you hold", "and there is no query"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "llmstored-f",
        "Probing recorded response and conversation ids for retention and volume",
        "Coverage is an outcome of its own here, because a probe over ids you "
        "kept can never say anything about the ids you did not.",
        ("Recorded ids, probed one by one", "no listing exists for either"),
        [
            ("Still readable, past policy", "retained longer than your rule", "bad"),
            ("A thread with no end", "items persist until deleted", "bad"),
            ("Growing input on every turn", "the thread is also a cost", "bad"),
            ("Gone, or never stored", "one status, two explanations", "plain"),
            ("Nothing retained", "the setting doing its job", "good"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
