#!/usr/bin/env python3
"""Diagrams for the /stripe/ field notes, batch N.

Same two shapes as the rest of the site: the problem is a chain that breaks at
one step, the fix is a branch, because every script in this section classifies
what it finds rather than guessing. Drawn in Stripe indigo.

No em dashes inside SVG text. One mis-sniffed encoding turns a single character
into three mojibake ones inside an image, where nothing will catch it.
"""
import diagrams as D

# Set before the diagrams below are built, restored at the bottom of the module.
# Every diagram here is constructed at import time, so the theme has to be active
# across exactly this file and no further: visuals.py imports several of these
# modules in one process, and a theme left set would silently retint whichever
# section happened to be imported next.
BRAND = "#635BFF"
D.set_theme(BRAND)

V = {}

V["stripe/radar-reviews-open-stale"] = {
    "flow_intro": (
        "The script ages every open review against the two deadlines that matter, "
        "then reads the charge behind it, because a review on an uncaptured "
        "authorization stops being actionable at seven days."
    ),
    "diagram_problem": D.chain(
        "srros-p",
        "A Radar review queue nobody works while an authorization lapses",
        "A review does not hold an automatically captured payment back. On separate "
        "authorization and capture it holds everything, and then the hold expires.",
        [
            ("Review rule added", "broad predicate"),
            ("Queue fills", "opened_reason rule"),
            ("Nobody visits", "no alert attached"),
            ("Day 7 passes", "hold released"),
            ("Nothing to capture", "goods already shipped"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "srros-f",
        "Sorting open Radar reviews by age and by whether the charge was captured",
        "The age says whether the queue is being worked. The captured flag says "
        "whether working it can still recover anything.",
        ("GET /v1/reviews", "plus captured on each charge"),
        [
            ("Open under 3 days", "inside the window", "good"),
            ("Over 3 days, captured", "backlog, refund decisions", "bad"),
            ("Over 3 days, uncaptured", "hold expires soon", "bad"),
            ("Over 7 days, uncaptured", "lapsed, nothing to capture", "bad"),
        ],
    ),
}

V["stripe/highest-risk-charges-succeeded"] = {
    "flow_intro": (
        "The script reads outcome.risk_level and outcome.rule together, because a "
        "highest risk charge that captured tells you an allow rule won, and an empty "
        "rule tells you the default block is simply off."
    ),
    "diagram_problem": D.chain(
        "shrcs-p",
        "An allow rule overriding the built in highest risk block rule",
        "Allow rules override Stripe's own defaults, so the block rule stays "
        "enabled on the page while letting the worst traffic straight through.",
        [
            ("Partner blocked", "support ticket"),
            ("Allow rule added", "ip_country predicate"),
            ("Allow wins", "beats every other rule"),
            ("Highest risk captured", "block never applies"),
            ("Fraud warnings", "weeks later"),
        ],
        fail_at=1,
        loop=(4, 1, "the rule looks enabled the whole time"),
    ),
    "diagram_fix": D.branch(
        "shrcs-f",
        "Sorting highest risk charges by what let them through",
        "Four outcomes that look identical in a charge list have four different "
        "repairs, and only outcome.rule separates them.",
        ("GET /v1/charges", "outcome.risk_level and outcome.rule"),
        [
            ("Not succeeded", "the block held", "good"),
            ("Not scored", "no Radar session collected", "bad"),
            ("Captured, allow rule", "guard the predicate", "bad"),
            ("Captured, no rule", "default block is off", "bad"),
        ],
    ),
}

V["stripe/avs-cvc-fail-captured"] = {
    "flow_intro": (
        "The script reads the account's decline_on settings first, then every card "
        "charge's checks object, because a null check and a failed check sit in the "
        "same field and need opposite repairs."
    ),
    "diagram_problem": D.chain(
        "savcf-p",
        "A charge captured after the postal code and security code failed",
        "The issuer can approve a payment that fails verification. Stripe records "
        "the failure and, with decline_on unset, captures anyway.",
        [
            ("Details mismatch", "postal code and CVC"),
            ("Issuer approves", "weighs other signals"),
            ("decline_on false", "the default"),
            ("Charge captured", "goods shipped"),
            ("Disputed as fraud", "no evidence to file"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "savcf-f",
        "Sorting card charges by their AVS and CVC verification result",
        "A failed check is a Radar rule you never enabled. A null check is a "
        "checkout form that never asked, and no rule will help.",
        ("GET /v1/account", "then checks on each charge"),
        [
            ("All checks passed", "verified", "good"),
            ("No checks at all", "collect the billing details", "bad"),
            ("Failed, not captured", "still your decision", "plain"),
            ("Failed and captured", "enable the risk scored rules", "bad"),
        ],
    ),
}

V["stripe/missing-statement-descriptor"] = {
    "flow_intro": (
        "The script compares the configured prefix with the descriptors actually "
        "sent, because the expensive failure is not an empty setting but two payment "
        "flows disagreeing about what your business is called."
    ),
    "diagram_problem": D.chain(
        "smstd-p",
        "A statement descriptor customers cannot recognise producing disputes",
        "Nobody in your team ever sees the descriptor. The only people who read it "
        "are the customers about to dispute the charge.",
        [
            ("Prefix left empty", "format rules rejected it"),
            ("Generic default sent", "not your brand"),
            ("Statement arrives", "line means nothing"),
            ("Dispute filed", "reason unrecognized"),
            ("Ratio fragmented", "Visa sees two merchants"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "smstd-f",
        "Sorting an account by the descriptors its charges actually carried",
        "One value is the goal. Several is fragmentation, which splits your dispute "
        "ratio across accounts the networks think are separate.",
        ("GET /v1/account", "plus calculated_statement_descriptor"),
        [
            ("One clear value", "consistent", "good"),
            ("No prefix set", "set it in Dashboard settings", "bad"),
            ("Several distinct values", "one prefix everywhere", "bad"),
            ("Too short or unreadable", "fails Stripe's own rules", "bad"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
