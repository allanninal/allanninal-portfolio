#!/usr/bin/env python3
"""Diagrams for the /twilio/ field notes, batch R.

The same two shapes as the rest of the site: the problem is a chain that breaks
at one step, the fix is a branch, because every script in this batch sorts what
it finds rather than guessing at it. Drawn in Twilio red.

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

V["twilio/a2p-campaign-suspended-30033"] = {
    "flow_intro": (
        "The classifier splits the window at the first 30033 and reads the half "
        "after it, because the useful question is not whether the campaign is "
        "suspended but what the code did once it was."
    ),
    "diagram_problem": D.chain(
        "t30033-p",
        "A campaign suspension reaching the send worker and nobody else",
        "The suspension notice goes to the account owner by email. The worker "
        "learns about it as an error code and treats it like any other.",
        [
            ("Carrier suspends", "policy review, no API event"),
            ("Notice emailed", "to an unread alias"),
            ("Worker sends anyway", "30033 on every message"),
            ("Retries multiply it", "one customer, three rows"),
            ("Traffic rerouted", "the escalating move"),
        ],
        fail_at=1,
        loop=(3, 2, "retry"),
    ),
    "diagram_fix": D.branch(
        "t30033-f",
        "Sorting a window of messages by what the producer did after the onset",
        "A window that opens on a 30033 cannot tell a new sender from an old "
        "one, so the reroute check is skipped rather than guessed at.",
        ("First 30033 in the window", "the only onset time there is"),
        [
            ("No 30033 at all", "nothing suspended here", "good"),
            ("Refusals stopped", "sending halted, ticket open", "plain"),
            ("Still pushing", "every send refused and billed", "bad"),
            ("New sender after onset", "undo it before Support", "bad"),
        ],
    ),
}

V["twilio/a2p-throughput-exceeded-30022"] = {
    "flow_intro": (
        "The comparison is one division against one number: the busiest minute "
        "over sixty, against the lowest MPS in rate_limits. Both halves live on "
        "resources the send path never reads."
    ),
    "diagram_problem": D.chain(
        "t30022-p",
        "A morning batch outrunning the throughput assigned to the campaign",
        "Off peak everything delivers, so the failure is filed as intermittent "
        "and the ceiling that caused it is never looked up.",
        [
            ("Batch job fires", "whole queue at once"),
            ("Combined MPS spikes", "shared across the pool"),
            ("Carrier refuses", "30022 on the overflow"),
            ("Retry at lunchtime", "delivers, looks random"),
            ("More numbers bought", "same campaign, same limit"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "t30022-f",
        "Sorting a peak send rate against the MPS published on the campaign",
        "A minute average cannot see a one second burst, which is why under the "
        "ceiling and still failing is a real answer rather than a rounding error.",
        ("Peak minute over sixty", "against the lowest carrier MPS"),
        [
            ("No 30022 in the window", "the rate fits", "good"),
            ("Over the ceiling", "throttle, then vet the brand", "bad"),
            ("Under it, still failing", "smooth the send loop", "bad"),
            ("Piled on one handset", "per destination, deduplicate", "plain"),
        ],
    ),
}

V["twilio/number-missing-from-campaign-sender-pool"] = {
    "flow_intro": (
        "Two lists and a difference: every SMS capable US long code the account "
        "owns, and every number sitting in a Messaging Service pool. Nothing in "
        "the API shows both at once."
    ),
    "diagram_problem": D.chain(
        "tpool-p",
        "A number bought, deployed and sending while registered to nothing",
        "Every status a team checks is green. The gap is an absence from a list, "
        "and an absence is not something any single response reports.",
        [
            ("Number bought", "SMS capable, no error"),
            ("Never added to a pool", "nothing submitted anywhere"),
            ("Code sets From directly", "service bypassed entirely"),
            ("Carrier sees no campaign", "30034 on every US send"),
            ("Brand and campaign green", "so the number is blamed last"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "tpool-f",
        "Sorting owned numbers by which registered pool, if any, contains them",
        "Toll-free numbers are excluded on purpose. They verify on a different "
        "path and fail with 30032, and mixing them hides both problems.",
        ("Owned numbers minus pooled", "joined to the 30034s by from"),
        [
            ("In a registered pool", "covered by the campaign", "good"),
            ("In no pool, no traffic", "will fail at launch", "plain"),
            ("In no pool, failing now", "unregistered, add it", "bad"),
            ("Pool has no campaign", "fix the service, not the number", "bad"),
        ],
    ),
}

V["twilio/sender-pending-carrier-provisioning"] = {
    "flow_intro": (
        "The whole judgement is the age of the oldest failing message against "
        "twenty four hours, which is why the current time is passed into the "
        "classifier rather than read inside it."
    ),
    "diagram_problem": D.chain(
        "tprov-p",
        "A provisioning window restarted by the response to it",
        "Nothing is misconfigured at any step. The only thing that goes wrong is "
        "the reaction, and the reaction produces no error of its own.",
        [
            ("Number joins the pool", "carrier update begins"),
            ("Launch sends early", "30035 on every message"),
            ("Read as misconfigured", "no countdown to check"),
            ("Removed and re-added", "clock back to zero"),
            ("Repeat twice more", "one day becomes three"),
        ],
        fail_at=2,
        loop=(4, 3, "restart"),
    ),
    "diagram_fix": D.branch(
        "tprov-f",
        "Sorting a failing sender by how long it has been failing",
        "A number in no pool must never land in the waiting bucket. Nothing was "
        "submitted for it, so the window everyone is waiting on never started.",
        ("Oldest 30035 or 30024", "against the 24 hour window"),
        [
            ("Last send went through", "already provisioned", "good"),
            ("Inside the window", "wait, route elsewhere", "plain"),
            ("Past the window", "Support, with the PN SID", "bad"),
            ("In no pool at all", "waiting will not end it", "bad"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
