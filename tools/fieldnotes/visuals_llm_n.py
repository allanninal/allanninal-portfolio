#!/usr/bin/env python3
"""Diagrams for the /llm/ field notes, batch N.

Four checks that a capability the organization already pays for is arriving in
production. None of the four problem chains contains an error, which is the
whole reason they are drawn: the request succeeds, the answer is fine, and the
thing that was bought is simply not there.

The first two chains end in an absence. A tier that stopped applying the day a
model id changed, and a context window that exists on the provider's side and
is refused by a constant on yours. Their fix branches both have a state that
hands the reading back rather than claiming it: an organization with no
commitment at all is not a per-model finding, and an enforced ceiling above the
reported window is the opposite fault and fails loudly.

The last two are siblings on one report and had to be drawn so that nobody
mistakes them for one picture. They share an endpoint and nothing else. One
chain is a habit that repurchases the same prefix every turn and ends in a bill;
the other is a diff that was generated, billed, read and dropped, and ends in a
keystroke. That last box is the only one in this section where the thing that
destroys the value is a person deciding, correctly, that they do not want it.

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

V["llm/priority-tier-model-unsupported"] = {
    "flow_intro": (
        "There is no failing request anywhere in this. service_tier auto is "
        "valid, the model is valid, and the fallback to standard is the "
        "documented behaviour rather than a fault. The only place the absence "
        "is visible is the usage report grouped by service_tier, because "
        "Priority costs are excluded from the cost report entirely, which is "
        "also why no dollar figure appears at the end of it."
    ),
    "diagram_problem": D.chain(
        "llmprio-p",
        "A priority commitment that stopped applying the day a model id changed",
        "Nothing in this chain errors. The migration was correct on every "
        "axis anyone measured, and tiers were not one of them.",
        [
            ("Commitment bought", "the 529s stopped"),
            ("Migrated to a newer model", "not on the covered list"),
            ("service_tier auto", "accepted, served standard"),
            ("No error, no line item", "costs are off the report"),
            ("Overload protection gone", "and the 529s return"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "llmprio-f",
        "Sorting each model by whether the usage report ever reports priority",
        "The org-level fact comes first. A zero everywhere is an organization "
        "without a commitment, not a gap on any one model.",
        ("Tokens by model", "and by service_tier"),
        [
            ("Zero, and on the exclusion list", "no coverage: this is not a setting", "bad"),
            ("Zero, and not on the list", "standard_only, or the wrong workspace", "bad"),
            ("A thin priority share", "the commitment is sized too small", "plain"),
            ("Zero on every model", "no commitment in the organization", "plain"),
            ("Priority on most traffic", "the tier is arriving", "good"),
        ],
    ),
}

V["llm/long-context-gated-on-obsolete-beta"] = {
    "flow_intro": (
        "This is what a capability looks like after it graduates. The beta "
        "header, the separate rate limits and the price premium all went away, "
        "and none of those removals produces an error in an application that "
        "is still being careful about them. Careful code keeps working. It "
        "keeps working at two hundred thousand tokens."
    ),
    "diagram_problem": D.chain(
        "llmgate1m-p",
        "A million token window that a constant in your own code refuses to use",
        "The guard was correct when it was written and has never failed, "
        "which is exactly why nobody deletes it.",
        [
            ("Ceiling set at 200k", "with a beta header beside it"),
            ("1M becomes the default", "no header, standard rates"),
            ("Model ids rotate", "the constant does not"),
            ("Documents truncated", "retrieval takes the blame"),
            ("Window paid for", "and never reached"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "llmgate1m-f",
        "Sorting each model id by the window it reports against the one you enforce",
        "One id routinely carries three of these at once, so the audit "
        "returns a list of findings rather than a single verdict.",
        ("max_input_tokens", "against your enforced cap"),
        [
            ("Reports 1M, code allows 200k", "bought, capped, unreachable", "bad"),
            ("Beta sent on a 1M model", "inert: delete the header", "bad"),
            ("Beta sent on a 200k model", "retired, and now a hard 400", "bad"),
            ("A premium branch survives", "there is no premium to charge", "plain"),
            ("Enforced equals reported", "nothing to repair here", "good"),
        ],
    ),
}

V["llm/claude-code-sessions-not-hitting-cache"] = {
    "flow_intro": (
        "This reads a report the other caching notes have never touched. Its "
        "unit is one person on one UTC day, it carries session counts that "
        "exist nowhere else, and it cannot be joined to the messages usage "
        "report by any field. The two workflows below are indistinguishable "
        "from inside the editor and differ by about an order of magnitude on "
        "the input half of the bill."
    ),
    "diagram_problem": D.chain(
        "llmccsess-p",
        "A prefix repurchased at full rate because every question starts a new session",
        "No setting is wrong and no request fails. The difference between "
        "these two habits never surfaces anywhere the developer can see.",
        [
            ("A question, a new session", "it feels tidier"),
            ("Context resent in full", "project file, tools, files read"),
            ("No earlier turn to match", "so nothing is read back"),
            ("Reads sit at zero", "no error, no warning"),
            ("Full rate every turn", "on a very large prefix"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "llmccsess-f",
        "Sorting each actor by sessions against cache reads on the Claude Code report",
        "The session floor comes first. One session has no earlier turn to "
        "read from, so a zero there is arithmetic rather than a finding.",
        ("Sessions per actor", "against cache_read"),
        [
            ("Two or more, no reads or writes", "the prefix is never cached", "bad"),
            ("Writes present, reads at zero", "written, never matched, worse", "bad"),
            ("A thin read share", "long and one shot sessions mixed", "plain"),
            ("One session in the window", "nothing to read back yet", "plain"),
            ("Most input read back", "the prefix is earning its keep", "good"),
        ],
    ),
}

V["llm/claude-code-edit-rejection-rate-high"] = {
    "flow_intro": (
        "The sibling of the note above, on the same endpoint and a different "
        "block of it, and the only measurement in this section whose subject "
        "is billed output that a person deliberately threw away. Rejecting a "
        "bad diff is the review step working. A sustained majority of them is "
        "an output budget going to work that reaches nobody, and there is no "
        "threshold at which anything starts objecting."
    ),
    "diagram_problem": D.chain(
        "llmccrej-p",
        "A diff generated at full output rates and discarded before it is applied",
        "Every step here is correct behaviour, including the last one. The "
        "money is spent by the time anybody gets to decide.",
        [
            ("A broad task, thin context", "the model guesses at scope"),
            ("Forty lines generated", "billed at output rates"),
            ("Shown to the developer", "confidently in the wrong place"),
            ("Rejected in two seconds", "review working as intended"),
            ("Another turn, another diff", "and the budget goes again"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "llmccrej-f",
        "Sorting each actor by accepted over accepted plus rejected, per tool",
        "The proposal floor comes first, because this number sits beside a "
        "person's name and a bad afternoon is not a pattern.",
        ("tool_actions per actor", "accepted against rejected"),
        [
            ("Under half accepted", "project setup, not the tool", "bad"),
            ("Multi edit worst by far", "the task was scoped too wide", "bad"),
            ("Low rate, commits landing", "read it as cost per change", "plain"),
            ("Fewer proposals than the floor", "not enough to say anything", "plain"),
            ("Most proposals kept", "the output is being used", "good"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
