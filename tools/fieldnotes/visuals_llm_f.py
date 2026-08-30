#!/usr/bin/env python3
"""Diagrams for the /llm/ field notes, batch F.

Four notes that all land on an invoice and are not four pictures of an invoice.
The problem chains have to say what is actually different about each: a ratio
nobody computed, a reporting dimension that means something other than what it
is read as, a bill denominated in five units where the dashboard speaks one, and
an asset that was paid for once and then forgotten. The fixes are all branches,
because every script here sorts what it finds into named states rather than
returning a yes or a no. Drawn in teal, matching the rest of the section.

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

V["llm/frontier-model-on-trivial-workload"] = {
    "flow_intro": (
        "The usage endpoint already returns both numbers. Requests is one column "
        "and output tokens is another, and nobody divides them, so the shape of "
        "the work stays invisible behind its volume. The fix reads the quotient "
        "and then refuses to give the same answer to three different shapes."
    ),
    "diagram_problem": D.chain(
        "llmfront-p",
        "A model chosen on the first afternoon and never asked about again",
        "Nothing in this chain errors and no dashboard row looks odd. The "
        "expensive model is the busy model, which is exactly what you expect.",
        [
            ("Prototype picks a model", "pasted from the quickstart"),
            ("It works", "correctness, not cost"),
            ("Config is inherited", "copied into four services"),
            ("400k calls a month", "each answer one word"),
            ("Frontier price per label", "no signal anywhere"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "llmfront-f",
        "Sorting models by the mean length of what they actually said",
        "Short answers over huge prompts wear this problem's signature and want "
        "the caching note instead. Saying so is the difference between a useful "
        "report and a pile of false positives.",
        ("Output tokens divided", "by request count"),
        [
            ("Premium, tiny answers", "the wrong size for the work", "bad"),
            ("Premium, long answers", "doing what it was chosen for", "good"),
            ("Tiny answers, huge prompts", "the bill is input, not tier", "plain"),
            ("Already the mini sibling", "nothing cheaper to move to", "good"),
        ],
    ),
}

V["llm/per-tenant-cost-attribution-impossible"] = {
    "flow_intro": (
        "This one is not arithmetic. The script resolves every principal the "
        "usage endpoint returned against the org directory, and the finding is "
        "that they all resolve: engineers and service accounts, never customers. "
        "Key cardinality is then the whole ceiling on how finely anything can be "
        "sliced, which is why the tenant count has to come from your database."
    ),
    "diagram_problem": D.chain(
        "llmtenant-p",
        "A grouping dimension read as a report on a request field it has nothing to do with",
        "Two years of sending a customer id on every call, in good faith, and "
        "none of it was ever stored anywhere that can be read back.",
        [
            ("user sent per request", "for abuse and cache"),
            ("group_by user_id", "looks like the report"),
            ("Chain is key to owner", "your staff, not theirs"),
            ("Eleven rows come back", "nine engineers, two bots"),
            ("Question has no answer", "and cannot be backfilled"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "llmtenant-f",
        "Sorting an organization by how many buckets the platform can offer it",
        "The platform can attribute to a key and to a project. Nothing else. So "
        "the finest slice available is exactly as fine as the keys you minted.",
        ("Distinct api_key_id", "against your tenant count"),
        [
            ("One key for everyone", "a single bucket, permanently", "bad"),
            ("Fewer keys than tenants", "impossible by construction", "bad"),
            ("A key per tenant or tier", "the platform can slice it", "good"),
            ("A principal nobody knows", "answer this one first", "plain"),
        ],
    ),
}

V["llm/audio-and-image-line-items-unnoticed"] = {
    "flow_intro": (
        "One endpoint is denominated in money and eight are denominated in "
        "characters, seconds, images, sessions and calls. The reconciliation runs "
        "in that direction on purpose: costs grouped by line item is the total, "
        "and the per modality endpoints are only there to explain what moved."
    ),
    "diagram_problem": D.chain(
        "llmmodal-p",
        "A spend dashboard built on the one endpoint that only speaks tokens",
        "A gap of three percent has four plausible innocent explanations, and "
        "all four are wrong. Then a voice feature ships.",
        [
            ("Dashboard reads completions", "tokens in, tokens out"),
            ("Speech bills characters", "different endpoint"),
            ("Search bills per call", "no tokens at all"),
            ("Totals drift a few percent", "filed under rounding"),
            ("Invoice arrives", "how long has this been here"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "llmmodal-f",
        "Sorting the bill by whether the dashboard can render the line at all",
        "A line item the script cannot classify is reported loudly. The platform "
        "ships new billable surfaces, and a quiet other bucket swallows the next one.",
        ("Costs by line item", "minus what you cover"),
        [
            ("Audio, image, tool spend", "invisible in a token graph", "bad"),
            ("Line items nobody can name", "read the strings first", "bad"),
            ("Gap under the tolerance", "rounding and report lag", "good"),
            ("Audio tokens inside chat", "priced apart from text", "plain"),
        ],
    ),
}

V["llm/fine-tuned-model-never-used"] = {
    "flow_intro": (
        "An inventory join with a deadline on it. Succeeded jobs on one side, "
        "thirty days of requests per model on the other, and the two lists come "
        "from two different credentials. The base model check is what turns an "
        "idle asset into one with a published date attached."
    ),
    "diagram_problem": D.chain(
        "llmftune-p",
        "A custom model that succeeded, was invoiced, and was never wired up",
        "There is no error to trigger a cleanup and no expiry to force a "
        "decision. The natural end state of an experiment is a model still listed.",
        [
            ("Four jobs in three weeks", "each better than the last"),
            ("Training billed", "trained_tokens, once"),
            ("Deploy is your config", "nothing routes traffic"),
            ("Priority moves on", "the id is never pasted"),
            ("Zero requests, still listed", "plus result files"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "llmftune-f",
        "Sorting custom models by whether anything calls them and whether the base survives",
        "A fine-tune dies with its base model. That makes a model still serving "
        "traffic on a vanished base more urgent than one nobody calls at all.",
        ("Succeeded jobs joined", "to requests per model"),
        [
            ("In service, base vanished", "serving now, stopping soon", "bad"),
            ("Zero calls, base vanished", "nothing to migrate", "bad"),
            ("Zero calls in the window", "route to it or retire it", "bad"),
            ("Requests against it", "the model earned its training", "good"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
