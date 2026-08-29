#!/usr/bin/env python3
"""Diagrams for the /twilio/ field notes, batch C.

The registration notes. Same two shapes as the rest of the site: the problem is
a chain that breaks at one step, the fix is a branch, because every script in
this section sorts what it finds rather than guessing. Drawn in Twilio red.

No em dashes inside SVG text. One mis-sniffed encoding turns a single character
into three mojibake ones inside an image, where nothing will catch it.
"""
import diagrams as D

# Set before the diagrams below are built, restored at the bottom of the module.
# Every diagram here is constructed at import time, so the theme has to be active
# across exactly this file and no further: visuals.py imports several of these
# modules in one process, and a theme left set would silently retint whichever
# section happened to be imported next.
BRAND = "#F22F46"
D.set_theme(BRAND)

V = {}

V["twilio/a2p-campaign-vetting-failed"] = {
    "flow_intro": (
        "The script reads every entry in errors[] rather than the first one, and "
        "sorts the codes by what clears them, because an edit, a brand problem and "
        "a content rejection all arrive as the same word: FAILED."
    ),
    "diagram_problem": D.chain(
        "tacf-p",
        "A campaign resubmitted twice with the same copy that was rejected the first time",
        "The reason was in the response both times. Reading campaign_status and "
        "stopping there throws away the only diagnosis the API gives you.",
        [
            ("Campaign submitted", "vetting runs at TCR"),
            ("Status reads FAILED", "one word, no detail"),
            ("errors[] never read", "code and fields ignored"),
            ("Same copy resubmitted", "three more weeks"),
            ("Rejected again", "US sends still 30034"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "tacf-f",
        "Sorting a failed campaign by which errors[] codes it actually carries",
        "Editing the description clears 30886 and does nothing at all for 30884. "
        "One bucket for all three costs weeks on the wrong work.",
        ("GET Compliance/Usa2p", "campaign_status plus errors[]"),
        [
            ("Status VERIFIED", "registered, sending", "good"),
            ("30886, 30893, 30909", "edit the named field", "plain"),
            ("30898 on the campaign", "the brand is the problem", "bad"),
            ("30883, 30884, 30885", "no edit clears this", "bad"),
        ],
    ),
}

V["twilio/a2p-brand-registration-failed"] = {
    "flow_intro": (
        "The script takes the reason from errors[] and only falls back to "
        "failure_reason and brand_feedback with a label, because both are deprecated "
        "and code written against them reports a fully explained brand as silent."
    ),
    "diagram_problem": D.chain(
        "tabr-p",
        "A fortnight spent on campaign paperwork for a brand that was already rejected",
        "The failure is one level above where it shows. Every 10DLC send collapses "
        "into 30034, which names none of the three things that can cause it.",
        [
            ("Brand submitted", "built from a Trust Hub profile"),
            ("Brand goes FAILED", "errors[] says why"),
            ("Campaign cannot attach", "nothing to attach to"),
            ("Numbers unregistered", "no sender is registered"),
            ("Every US send 30034", "team debugs the campaign"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "tabr-f",
        "Sorting brand registrations by status and by where the explanation came from",
        "Three free resubmissions, then 21724. Each one spent on a guess is one "
        "you do not have once you know the answer.",
        ("GET a2p/BrandRegistrations", "status, tcr_id and errors[]"),
        [
            ("APPROVED with a tcr_id", "campaigns can attach", "good"),
            ("PENDING or IN_REVIEW", "not failed, not usable", "plain"),
            ("FAILED with errors[]", "fix the named fields", "bad"),
            ("FAILED, errors[] empty", "only deprecated prose left", "bad"),
        ],
    ),
}

V["twilio/a2p-campaign-stuck-in-progress"] = {
    "flow_intro": (
        "The age is an argument to the classifier rather than a clock read inside "
        "it, so the SLA boundary, the escalation point and the two states where the "
        "fields disagree are all ordinary tests."
    ),
    "diagram_problem": D.chain(
        "tacw-p",
        "A launch shipped on the assumption that a quiet console meant an approved campaign",
        "Nothing here fails. There is no rejection, no code and no callback saying "
        "stop, which is exactly why monitoring never mentions it.",
        [
            ("Campaign submitted", "review is asynchronous"),
            ("Status IN_PROGRESS", "campaign_id still null"),
            ("Nobody polls again", "callback fired once"),
            ("Rollout gated on time", "not on VERIFIED"),
            ("Launch day 30034", "every US message"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "tacw-f",
        "Sorting campaigns still in review by age and by whether the fields agree",
        "A populated errors[] under an IN_PROGRESS status means the answer has "
        "already arrived and the status is behind it.",
        ("GET Compliance/Usa2p", "status, campaign_id, date_created"),
        [
            ("VERIFIED with an id", "safe to enable US sends", "good"),
            ("Waiting, inside the SLA", "not live yet, keep the gate", "plain"),
            ("Waiting past the SLA", "or past three weeks, escalate", "bad"),
            ("errors[] already filled", "reviewed, status lagging", "bad"),
        ],
    ),
}

V["twilio/tollfree-number-not-verified"] = {
    "flow_intro": (
        "The script joins two APIs on tollfree_phone_number_sid, then picks one "
        "record per number deliberately, because a number can carry an old rejection "
        "and a newer approval and set membership reports whichever came back first."
    ),
    "diagram_problem": D.chain(
        "ttfv-p",
        "A toll-free number bought to skip 10DLC and blocked at launch instead",
        "Since 31 January 2024 unverified toll-free traffic is blocked rather than "
        "throttled, and the blocked attempts are still billed.",
        [
            ("Toll-free bought", "no brand, no campaign"),
            ("No verification filed", "the paperwork moved, not vanished"),
            ("Launch sends to US", "and to Canada"),
            ("Every message 30032", "blocked, not slowed"),
            ("Retry loop bills", "full speed, zero delivery"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "ttfv-f",
        "Sorting toll-free numbers by the verification record that actually governs them",
        "Filing is not passing. A number in review sends exactly like one that "
        "was never filed, so both belong in the same report.",
        ("Numbers joined to verifications", "on tollfree_phone_number_sid"),
        [
            ("TWILIO_APPROVED", "clear to send", "good"),
            ("Voice only number", "nothing to verify", "plain"),
            ("PENDING or IN_REVIEW", "blocked while it waits", "bad"),
            ("No record at all", "every US and CA send 30032", "bad"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
