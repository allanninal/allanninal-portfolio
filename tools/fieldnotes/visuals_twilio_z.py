#!/usr/bin/env python3
"""Diagrams for the /twilio/ field notes, batch Z.

The same two shapes as the rest of the site: the problem is a chain that breaks
at one step, the fix is a branch, because every script in this section sorts
what it finds rather than guessing at it. Drawn in Twilio red.

Four of the five notes here are clocks, so the chains are mostly time passing
rather than a request failing. That is the point of them.

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

V["twilio/sole-prop-otp-never-accepted"] = {
    "flow_intro": (
        "The script reads identity_status rather than status, because the two "
        "move independently and a brand can read APPROVED while the handset "
        "that was supposed to prove the owner exists never replied."
    ),
    "diagram_problem": D.chain(
        "tsotp-p",
        "A Sole Proprietor brand blocked by a passcode the owner never answered",
        "Nothing here errors. The registration is accepted, a text is sent, and "
        "the step that fails is a person not replying to it.",
        [
            ("Brand submitted", "brand_type SOLE_PROPRIETOR"),
            ("Passcode texted", "to the owner's mobile"),
            ("24 hours pass", "no reply from that handset"),
            ("identity_status stuck", "still SELF_DECLARED"),
            ("Every US send 30034", "campaign cannot register"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "tsotp-f",
        "Sorting Sole Proprietor brands by whether the handset ever replied",
        "An unverified brand with no passcode subresource is a different "
        "conversation: nothing was ever sent, so re-sending is not the repair.",
        ("GET a2p/BrandRegistrations", "brand_type, identity_status, date_created"),
        [
            ("VERIFIED or VETTED", "the handset replied", "good"),
            ("Under 24 hours old", "passcode in flight", "plain"),
            ("Past 24 hours", "expired unanswered, re-send", "bad"),
            ("No otps link", "never raised, check the filing", "bad"),
        ],
    ),
}

V["twilio/sole-prop-extra-numbers-unregistered"] = {
    "flow_intro": (
        "The script follows brand_registration_sid from the campaign to the "
        "brand before it counts anything, because the one number limit is a "
        "property of the brand and nothing on the Messaging Service mentions it."
    ),
    "diagram_problem": D.chain(
        "tspool-p",
        "Extra senders added to a Sole Proprietor pool that can only hold one",
        "The add returns success. The pool looks configured. Only the A2P "
        "registration of the extra numbers never happens.",
        [
            ("Sole Prop brand", "one campaign, one number"),
            ("Three numbers added", "API returns created"),
            ("Two stay UNREGISTERED", "silently, forever"),
            ("Service picks a sender", "per message, from three"),
            ("30034 at random", "retrying sometimes works"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "tspool-f",
        "Sorting Messaging Services by brand type against sender pool size",
        "An empty pool on the same brand fails consistently rather than "
        "intermittently, and the repair is to add one rather than remove several.",
        ("Campaign, brand and pool", "joined on brand_registration_sid"),
        [
            ("Not a Sole Prop brand", "pool size is not capped", "good"),
            ("Exactly one number", "the supported shape", "good"),
            ("More than one", "the extras never register", "bad"),
            ("Empty pool", "every send fails, always", "bad"),
        ],
    ),
}

V["twilio/tmobile-brand-daily-segment-cap"] = {
    "flow_intro": (
        "The script sums num_segments rather than counting messages, and says "
        "so: the Messages list does not name the carrier, so the total is an "
        "upper bound on the T-Mobile share rather than the number being capped."
    ),
    "diagram_problem": D.chain(
        "ttmo-p",
        "A day's sends running into a daily segment allowance held at the brand",
        "The cap lives in T-Mobile's systems, against the brand. Nothing on the "
        "Twilio side refuses the send until the allowance is already gone.",
        [
            ("Morning batch", "delivers normally"),
            ("Second campaign sends", "same brand, same pool"),
            ("Allowance exhausted", "segments, not messages"),
            ("T-Mobile sends fail", "30023, others fine"),
            ("Midnight Pacific", "counter resets, repeats"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "ttmo-f",
        "Sorting a brand's day by observed cap errors against derived ceiling",
        "An observed 30023 is evidence and outranks the arithmetic, because the "
        "segment total covers every carrier and is only a bound.",
        ("Brand tier plus today's segments", "brand_type, russell_3000, num_segments"),
        [
            ("30023 seen today", "the allowance ran out", "bad"),
            ("Past the ceiling", "bound crossed, throttle now", "bad"),
            ("Above 80 percent", "spread the rest of the day", "plain"),
            ("No readable tier", "supply the ceiling yourself", "plain"),
        ],
    ),
}

V["twilio/tollfree-edit-window-expiring"] = {
    "flow_intro": (
        "The script reads only edit_allowed and edit_expiration. Whether the "
        "rejection can be corrected at all is a separate question, and the "
        "window closes at the same rate while that one is being answered."
    ),
    "diagram_problem": D.chain(
        "ttfew-p",
        "An edit window closing on a rejected toll-free verification",
        "Nothing changes state when the window lapses. The status reads "
        "TWILIO_REJECTED before and after, so there is no event to notice.",
        [
            ("Verification rejected", "number already blocked"),
            ("Edit window opens", "edit_allowed true"),
            ("Fix sits in a queue", "sprint time, not wall time"),
            ("edit_expiration passes", "no console nag, no alert"),
            ("Fresh submission only", "full review, weeks"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "ttfew-f",
        "Sorting rejected toll-free records by what is left of the edit window",
        "edit_allowed absent from the response is not edit_allowed false: one "
        "is unknown, the other sends somebody down the expensive path.",
        ("GET Tollfree/Verifications", "Status TWILIO_REJECTED"),
        [
            ("Days of window left", "outside the horizon", "good"),
            ("edit_allowed false", "no deadline to race", "plain"),
            ("Inside the horizon", "correct it before it lapses", "bad"),
            ("Expiration already past", "boolean disagrees with clock", "bad"),
        ],
    ),
}

V["twilio/link-shortening-cert-expiring"] = {
    "flow_intro": (
        "The script reads the certificate and the replacement together, because "
        "a live certificate days from expiry with a replacement still in "
        "validation reads as handled from either field on its own."
    ),
    "diagram_problem": D.chain(
        "tlsc-p",
        "A branded short domain going dark when its uploaded certificate expires",
        "The certificate sits in Twilio's infrastructure, outside every renewal "
        "process your team runs, on a date chosen a year or two ago.",
        [
            ("Certificate uploaded", "bring your own, fixed expiry"),
            ("Not auto renewed", "unless Twilio managed"),
            ("30131 warning", "logged at warning level"),
            ("Expiry passes", "links fail TLS on the click"),
            ("30120 and 30129", "sends failing, clicks at zero"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "tlsc-f",
        "Sorting link shortening domains by expiry and by replacement state",
        "An empty certificate response is a Twilio managed domain or a wrong "
        "domain sid. Reporting it as clean is the one mistake worth avoiding.",
        ("Certificate per domain sid", "date_expires, cert_in_validation"),
        [
            ("Outside the window", "nothing to do", "good"),
            ("Replacement validating", "live cert healthy, finish it", "plain"),
            ("Inside the window", "reissue and upload now", "bad"),
            ("Already expired", "every short link is broken", "bad"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
