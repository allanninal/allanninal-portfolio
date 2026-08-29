#!/usr/bin/env python3
"""Diagrams for the /twilio/ field notes, batch I.

The voice batch. Same two shapes as the rest of the site: the problem is a chain
that breaks at one step, the fix is a branch, because every script in this
section classifies what it finds rather than guessing. Drawn in Twilio red.

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

V["twilio/trunk-missing-disaster-recovery-url"] = {
    "flow_intro": (
        "The script keeps not checked and checked but empty apart, because a trunk "
        "audited without the origination fetch must never be reported as having no "
        "origination URIs. One reads as reassuring and is not."
    ),
    "diagram_problem": D.chain(
        "ttrunk-p",
        "Inbound calls dropped while the PBX is unreachable and no recovery URL is set",
        "Nothing here is logged as a call failure. The trunk did what it was "
        "configured to do, which was nothing.",
        [
            ("Trunk created", "recovery url left empty"),
            ("Runs for a year", "origination answers fine"),
            ("Firewall rule expires", "every URI unreachable"),
            ("No recovery TwiML", "nowhere to send the call"),
            ("Callers dropped", "blamed on the PBX"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "ttrunk-f",
        "Sorting SIP trunks by what happens when origination stops answering",
        "One enabled origination URI is not a finding on its own. Combined with an "
        "empty recovery URL it is a single host between you and a dropped call.",
        ("GET Trunks and OriginationUrls", "recovery url, scheme, enabled URIs"),
        [
            ("Recovery url on https", "covered, leave it", "good"),
            ("Recovery url on http", "cleartext when degraded", "plain"),
            ("One enabled URI", "single host, no spare", "plain"),
            ("No recovery url", "outage drops every call", "bad"),
        ],
    ),
}

V["twilio/sip-domain-no-auth-type"] = {
    "flow_intro": (
        "The script reads auth_type as a list rather than a string, then counts what "
        "is mapped to each mode it names. Declaring a mode and mapping something to "
        "it are two different operations, and only the second one lets a call in."
    ),
    "diagram_problem": D.chain(
        "tsipd-p",
        "A SIP INVITE refused at authentication before the voice url is fetched",
        "The rejection happens upstream of everything you can see. No TwiML ran, "
        "so there is no alert and no request in your logs.",
        [
            ("Domain created", "name and voice url set"),
            ("auth_type left empty", "no mode declared"),
            ("PBX sends INVITE", "credentials presented"),
            ("Refused at auth", "voice url never fetched"),
            ("Silence your side", "evidence is on the PBX"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "tsipd-f",
        "Sorting SIP domains by whether anything can actually authenticate to them",
        "One of two declared modes left unmapped is the case that gets reported as "
        "intermittent, because the reporter cannot see which half is failing.",
        ("Domains plus their mappings", "auth_type, credential lists, IP ACLs"),
        [
            ("Both declared and mapped", "routed, leave it", "good"),
            ("No fallback url", "one non 2xx drops the call", "plain"),
            ("One mode unmapped", "half the callers refused", "bad"),
            ("auth_type empty", "no traffic at all", "bad"),
        ],
    ),
}

V["twilio/dial-invalid-caller-id-13214"] = {
    "flow_intro": (
        "The script sweeps Alerts at the error and the warning level and merges on "
        "the alert sid, because several of the 132xx Dial errors are warnings and an "
        "error only query reports a clean account while the calls keep failing."
    ),
    "diagram_problem": D.chain(
        "t13214-p",
        "A forwarded call rejected because the inbound caller ID was passed through",
        "Most inbound calls carry a clean number, so the forwarding code looks "
        "correct. The failures are the calls where the carrier sent something else.",
        [
            ("Inbound call arrives", "carrier sends a bad From"),
            ("Dial has no callerId", "pass through is the default"),
            ("Bad value forwarded", "onto the outbound leg"),
            ("Carrier rejects", "13214 on a child call"),
            ("Parent completes", "logged at warning level"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "t13214-f",
        "Sorting 13214 alerts by what the caller ID on the call actually was",
        "A well formed number can still be a 13214. Twilio presents only caller IDs "
        "the account owns or has verified, whatever the formatting.",
        ("Alerts joined to their calls", "from, direction, verified caller IDs"),
        [
            ("Owned or verified", "look at the TwiML instead", "plain"),
            ("Valid but not yours", "verify it or stop using it", "bad"),
            ("Not E.164, inbound leg", "pass through, fix the Dial", "bad"),
            ("Withheld or SIP URI", "never presentable", "bad"),
        ],
    ),
}

V["twilio/outbound-call-failure-rate-spike"] = {
    "flow_intro": (
        "The script fetches both halves of the ratio over one window, because a count "
        "of failures rises with traffic and a threshold set on it either fires every "
        "good week or never fires at all."
    ),
    "diagram_problem": D.chain(
        "tcfr-p",
        "A rising outbound failure rate that no single alert accounts for",
        "Nothing broke loudly. The share of calls ending in failed moved, and a "
        "share is not an event, so nothing raised it.",
        [
            ("Calls start failing", "status failed, no pattern"),
            ("No code dominates", "four causes, one word"),
            ("Alerts look normal", "some are only warnings"),
            ("Count without a rate", "moves with traffic"),
            ("Nobody can localise it", "support has no lead"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "tcfr-f",
        "Sorting outbound calls into buckets and judging each bucket on its own rate",
        "Where the failures concentrate is the diagnosis. One prefix is geo or "
        "normalisation, one direction is your dialling code or your TwiML.",
        ("Failed and completed calls", "bucketed by direction and prefix"),
        [
            ("Below the volume floor", "too few to read a rate", "plain"),
            ("Under the threshold", "normal for this bucket", "good"),
            ("Over the threshold", "localised, go to Events", "bad"),
            ("Every call failed", "a permission, not a rate", "bad"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
