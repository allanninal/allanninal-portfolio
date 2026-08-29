#!/usr/bin/env python3
"""Diagrams for the /twilio/ field notes, batch U.

Four paperwork failures, drawn the same way as everything else in this section:
the problem is a chain that breaks at one step, the fix is a branch, because each
script classifies what it finds rather than guessing. Drawn in Twilio red.

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

V["twilio/regulatory-bundle-rejected"] = {
    "flow_intro": (
        "The script classifies on status alone, because status is all the Bundle "
        "resource carries. The reason lives with the reviewer and with the objects "
        "the bundle assigns, which is why the item assignments are the second call."
    ),
    "diagram_problem": D.chain(
        "tbrj-p",
        "A number purchase refused by a bundle rejected weeks earlier",
        "Nothing between the rejection and the purchase mentions the bundle. The "
        "account works normally in every other country the whole time.",
        [
            ("Bundle submitted", "documents attached"),
            ("Reviewer refuses", "scan illegible or wrong class"),
            ("No email, no callback", "told to nobody"),
            ("Weeks pass", "other countries unaffected"),
            ("Purchase refused", "found inside a launch"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "tbrj-f",
        "Sorting regulatory bundles by the state their status actually reports",
        "A draft blocks purchases exactly like a rejection and needs the opposite "
        "action: a submission rather than a correction.",
        ("GET RegulatoryCompliance/Bundles", "status per country and number type"),
        [
            ("twilio-approved", "buyable today", "good"),
            ("pending or in review", "queued, hold the purchase", "plain"),
            ("twilio-rejected", "replace the refused object", "bad"),
            ("draft", "never submitted, never reviewed", "bad"),
        ],
    ),
}

V["twilio/bundle-evaluation-noncompliant"] = {
    "flow_intro": (
        "The script walks two levels, not one. results[] names the requirement that "
        "failed; results[].invalid[] names the attribute, and that attribute is the "
        "only thing anybody can act on."
    ),
    "diagram_problem": D.chain(
        "tbev-p",
        "A bundle resubmitted four times without reading the evaluation",
        "The answer existed before the first resubmission. It is one GET away, on "
        "a subresource the bundle status never mentions.",
        [
            ("Bundle filled in", "documents attached"),
            ("Submission bounces", "status stays draft"),
            ("Status says nothing", "no errors array on the bundle"),
            ("Another document added", "guessing at the cause"),
            ("Same result", "one field was wrong all along"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "tbev-f",
        "Reading the latest evaluation of a bundle and what it names",
        "A failed requirement with no invalid entries is the missing-document "
        "case: nothing to name, and the most basic failure there is.",
        ("GET Bundles/{Sid}/Evaluations", "latest run by date_created"),
        [
            ("compliant and current", "ready to submit", "good"),
            ("compliant but older than the edit", "snapshot, not status", "plain"),
            ("noncompliant with invalid[]", "correct that object_field", "bad"),
            ("noncompliant, no field named", "a required document is absent", "bad"),
        ],
    ),
}

V["twilio/trusthub-customer-profile-rejected"] = {
    "flow_intro": (
        "The join is the report. Brands name the profile in "
        "customer_profile_bundle_sid and toll-free verifications name it in "
        "customer_profile_sid, and both hold the same BU sid."
    ),
    "diagram_problem": D.chain(
        "tcpr-p",
        "Two teams debugging two products that share one rejected profile",
        "Neither product says the profile was rejected. Each fails in its own "
        "vocabulary, on its own resource, with its own docs page.",
        [
            ("Profile submitted", "business identity and address"),
            ("Profile rejected", "errors recorded on the profile"),
            ("Brand fails", "code about business identity"),
            ("Toll-free rejected", "reason about business name"),
            ("Two investigations", "neither looks upstream"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "tcpr-f",
        "Sorting Trust Hub customer profiles by what they are blocking",
        "An approved profile past valid_until still reads approved, and everything "
        "built on it has stopped inheriting an approval that no longer exists.",
        ("Profiles joined to brands and TFV", "on the BU sid each one names"),
        [
            ("Approved and in date", "downstream free to submit", "good"),
            ("Pending or in review", "hold the resubmissions", "plain"),
            ("twilio-rejected", "fix here, not downstream", "bad"),
            ("Approved but past valid_until", "approval already gone", "bad"),
        ],
    ),
}

V["twilio/tollfree-verification-rejected"] = {
    "flow_intro": (
        "The code decides, not the prose. A prohibited category cannot be reworded "
        "into an approval, and every attempt spends days of a window that only "
        "matters while it is open."
    ),
    "diagram_problem": D.chain(
        "ttfr-p",
        "A rejected toll-free verification resubmitted into the same answer",
        "Traffic is blocked with 30032 for the whole loop, and the account is "
        "billed for the attempts that never left.",
        [
            ("Verification filed", "business and use case"),
            ("TWILIO_REJECTED", "coded reason on the record"),
            ("Prose read, code ignored", "reads like writing feedback"),
            ("Summary reworded", "category unchanged"),
            ("Rejected again", "edit window spent"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "ttfr-f",
        "Sorting rejected toll-free verifications by code and by edit window",
        "edit_allowed true with an expiration already past is the trap: the field "
        "says yes and the clock says no.",
        ("GET Tollfree/Verifications", "rejection_reasons, edit_allowed, expiry"),
        [
            ("Not a rejection", "nothing to correct", "good"),
            ("Fixable, window open", "correct the named fields", "plain"),
            ("Fixable, window closed", "fresh submission, back of queue", "bad"),
            ("Prohibited category", "no edit ever passes", "bad"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
