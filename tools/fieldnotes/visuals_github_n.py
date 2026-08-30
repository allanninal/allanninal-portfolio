#!/usr/bin/env python3
"""Diagrams for the /github/ field notes, batch N.

Four notes about numbers that are not the number anybody assumed. Two of them
are ceilings that turned out to be lower, and two are volumes that turned out
to be higher.

The first is a rate limit that was never going to be the quoted one. An App
installation earns its ceiling from its own size, so a narrow selection inside
a large organization sits at the floor forever. The problem chain is a capacity
plan built on a remembered figure, and the fix branch sorts a measured ceiling
against the one an installation of that shape is entitled to.

The second is an identifier that was treated as a constant. The chain is a
reinstall nobody told you about; the branch has four outcomes because the
dangerous one does not fail, and a check that only asks whether the id still
resolves will pass on it.

The third reads a feed another note already reads and takes a different
column. The chain is a handler that finishes its work after the listener has
gone, and the branch sorts on a percentile rather than a failure count, because
a receiver two seconds from the cutoff has a perfect failure count.

The fourth has no failure anywhere in it. The chain is a subscription made in a
hurry that widens by itself every time GitHub ships an event, and the branch
sorts on the fraction of delivered volume the receiver throws away.

Drawn in GitHub blue. No em dashes inside SVG text: one mis-sniffed encoding
turns a single character into three mojibake ones inside an image, where
nothing downstream will catch it.
"""
import diagrams as D

# Set before the diagrams below are built, restored at the bottom of the module.
# Every diagram here is constructed at import time, so the theme has to be
# active across exactly this file and no further.
BRAND = "#0969DA"
D.set_theme(BRAND)

V = {}

V["github/app-rate-limit-not-scaling"] = {
    "flow_intro": (
        "Two GETs, one of which is free, and then arithmetic that needs no "
        "network at all. The rate-limit endpoint reports the ceiling this "
        "credential was actually given; the installation endpoint reports how "
        "big the installation is, in one item rather than a page of them. "
        "Everything after that is a formula, which is why it can be tested "
        "properly. One half of the formula is not readable from here, so the "
        "entitlement comes out as a floor rather than an estimate, and the "
        "script says which half it could see."
    ),
    "diagram_problem": D.chain(
        "ghceil-p",
        "A capacity plan built on a remembered rate limit rather than a measured one",
        "Every number in the investigation is correct except the one nobody "
        "read. The usage matches the plan exactly, which is what makes it so "
        "hard to look at the other side of the fraction.",
        [
            ("Apps scale, so 12,500", "written into the plan"),
            ("Throttles at 5,000", "the ceiling never moved"),
            ("Usage is audited", "and matches the plan"),
            ("Auth is suspected", "a week in the JWT code"),
            ("Caching bolted on", "which only postpones it"),
        ],
        fail_at=1,
        loop=(4, 2, "and the usage is audited again"),
    ),
    "diagram_fix": D.branch(
        "ghceil-f",
        "Sorting a measured ceiling against the one an installation of that size earns",
        "The middle two rows are both 5,000 and they are opposite findings. "
        "One is a selection to widen, the other is a ceiling to live within.",
        ("Measured ceiling", "against installation size"),
        [
            ("Below entitlement, selected", "the selection is the cap", "bad"),
            ("At 5,000, small install", "real ceiling, spend less", "plain"),
            ("At the 12,500 cap", "nothing left to earn", "plain"),
            ("Matches its size", "the ceiling is honest", "good"),
        ],
    ),
}

V["github/app-installation-id-hardcoded"] = {
    "flow_intro": (
        "One paginated GET builds the authoritative list, and each configured "
        "pair is then looked up twice against it: once by id, to see whether "
        "it still exists, and once by account, to see what that account's id "
        "is today. Running only the first lookup is how the serious finding "
        "survives an audit, because a crossed id exists perfectly well. The "
        "endpoint that mints a token is a write and is never called, so the "
        "script explains the 404 rather than reproducing it."
    ),
    "diagram_problem": D.chain(
        "ghdrift-p",
        "A stored installation id broken by a reinstall nobody reported",
        "The change happened inside a customer's organization, was entirely "
        "legitimate, and left no trace anywhere in your systems except the "
        "failure it caused.",
        [
            ("Id pasted from a URL", "into config, two years ago"),
            ("Customer reinstalls", "a new id is created"),
            ("Token call 404s", "and names no cause"),
            ("Key and JWT checked", "both are perfectly fine"),
            ("Filed as flaky", "until the next reinstall"),
        ],
        fail_at=1,
        loop=(4, 2, "and the id is pasted in again"),
    ),
    "diagram_fix": D.branch(
        "ghdrift-f",
        "Sorting a configured installation id by existence and by the account behind it",
        "The first row is the one worth building the check for. It is the "
        "only outcome here that never produces an error of any kind.",
        ("Each configured id", "looked up by id and by account"),
        [
            ("Exists, wrong account", "silently hits another org", "bad"),
            ("Gone, account still there", "reinstalled under a new id", "bad"),
            ("Gone, account gone too", "uninstalled and not replaced", "plain"),
            ("Matches its account", "and was not recreated since", "good"),
        ],
    ),
}

V["github/webhook-timeout-10s"] = {
    "flow_intro": (
        "The same feed as the failure audit, read for a different column. "
        "Statuses are thrown away except the one marker that says the attempt "
        "was abandoned, and the duration is kept on every record, including "
        "the ones that succeeded. That is what makes the finding arrive "
        "early: a tail at nine seconds is a problem today, and a failure "
        "count calls that same window healthy. Nothing is ever sent to the "
        "receiver, because the clock that decides is not the one this script "
        "would be holding."
    ),
    "diagram_problem": D.chain(
        "ghslow-p",
        "A webhook handler doing its work inline and crossing the ten second cutoff",
        "Both logs are telling the truth about different moments. The handler "
        "did return 200, to a connection that had already been abandoned.",
        [
            ("Work done inline", "clone, call, build, reply"),
            ("Cut off at 10s", "recorded as a failure"),
            ("Our log says 200", "so the log is argued with"),
            ("Called flaky", "it is size, not weather"),
            ("Redelivered", "the same work runs twice"),
        ],
        fail_at=1,
        loop=(4, 2, "and the duplicate is investigated"),
    ),
    "diagram_fix": D.branch(
        "ghslow-f",
        "Sorting a delivery window by its duration tail rather than its failure count",
        "The second row is the reason for the note. Zero failures and two "
        "seconds of headroom is the state a failure audit reports as fine.",
        ("Every delivery duration", "against a 10 second cutoff"),
        [
            ("Abandoned at 10s", "already failing, and replayed", "bad"),
            ("No failures, p95 at 9s", "fails on the next slow week", "bad"),
            ("Tail past 5s", "real work is still inline", "plain"),
            ("Tail in milliseconds", "the handler only enqueues", "good"),
        ],
    ),
}

V["github/webhook-wildcard-events"] = {
    "flow_intro": (
        "Set arithmetic in the direction nobody runs it. The usual check asks "
        "which events the code handles that the hook does not send; this one "
        "asks the opposite, and the answer has no symptom attached to it, so "
        "it has to be gone looking for. The delivery tally turns the objection "
        "into a fraction, and the proposal is built from what the receiver "
        "implements rather than from what happened to arrive, because a "
        "retention window shorter than a release cycle would quietly prune a "
        "handler that is still needed."
    ),
    "diagram_problem": D.chain(
        "ghwild-p",
        "A wildcard webhook subscription widening on its own over two years",
        "Nothing here is an error. Every dashboard stays green while the "
        "volume grows on somebody else's release schedule.",
        [
            ("Set to * in a hurry", "before the events were known"),
            ("Everything arrives", "and most is discarded"),
            ("Receiver runs hot", "verify, parse, throw away"),
            ("Read as slow code", "a bigger instance is bought"),
            ("New events join", "with no deploy at all"),
        ],
        fail_at=1,
        loop=(4, 2, "and the receiver is scaled again"),
    ),
    "diagram_fix": D.branch(
        "ghwild-f",
        "Sorting a hook subscription by the share of delivered volume the receiver discards",
        "The second row is still a finding. A window where everything "
        "happened to be wanted says nothing about the events GitHub adds next.",
        ("Subscribed events", "against the ones handled"),
        [
            ("Wildcard, most discarded", "print the explicit list", "bad"),
            ("Wildcard, all wanted", "open ended is the problem", "bad"),
            ("Explicit, some unhandled", "narrow the array", "plain"),
            ("Explicit and matching", "nothing arrives unwanted", "good"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
