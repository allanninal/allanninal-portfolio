#!/usr/bin/env python3
"""Diagrams for the /twilio/ field notes, batch E.

The plumbing notes: a number shadowed by an Application SID, an empty sender
pool, a From that cannot do SMS, and a Messaging Service with no delivery
signal. Same two shapes as the rest of the site, because every script here
sorts what it found rather than guessing: the problem is a chain that breaks at
one step, the fix is a branch. Drawn in Twilio red.

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

V["twilio/number-conflicting-url-and-application-sid"] = {
    "flow_intro": (
        "The script resolves the Application before it judges the number, because "
        "the field everyone reads is the one field Twilio does not read. Matching "
        "URLs are deliberately not a finding: only a gap between them is."
    ),
    "diagram_problem": D.chain(
        "tnap-p",
        "An afternoon spent editing a webhook URL that nothing ever requests",
        "Nothing fails. The write succeeds, the API returns the new value, and "
        "calls keep arriving at a host that was retired last spring.",
        [
            ("voice_url edited", "the write returns 200"),
            ("App SID still set", "it wins outright"),
            ("Number url ignored", "never requested"),
            ("Old app answers", "retired endpoint"),
            ("Blamed on caching", "then on DNS"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "tnap-f",
        "Sorting numbers by which resource actually serves their traffic",
        "An app with no url is a live outage; a shadowed url is a stale endpoint. "
        "One report, two very different mornings.",
        ("Numbers joined to Applications", "on voice and sms app sid"),
        [
            ("No app sid", "the number's own url is read", "good"),
            ("Urls agree", "app routed, nothing surprising", "plain"),
            ("Urls differ", "the number's url is inert", "bad"),
            ("App has no url", "calls route nowhere", "bad"),
        ],
    ),
}

V["twilio/messaging-service-empty-sender-pool"] = {
    "flow_intro": (
        "Three sender lists, read separately, and a classifier that refuses to "
        "call a pool empty until all three are in hand. An unread list and an "
        "empty one are different facts with opposite repairs."
    ),
    "diagram_problem": D.chain(
        "tesp-p",
        "A Messaging Service created by automation that never received a sender",
        "The rejection happens before a Message exists, so nothing appears in the "
        "Messages list and nothing appears on the bill.",
        [
            ("Service created", "by a setup script"),
            ("Senders never added", "second call skipped"),
            ("App sends by SID", "MessagingServiceSid"),
            ("Rejected 21704", "at request time"),
            ("No Message row", "nothing to find later"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "tesp-f",
        "Sorting Messaging Services by what their sender pool can actually reach",
        "Not empty is not the same as usable. Alphanumeric only sends nothing to "
        "the US or Canada, and that is 21703, not 21704.",
        ("Numbers, alpha senders, short codes", "three lists per service"),
        [
            ("A long code in the pool", "ready to send", "good"),
            ("Short code only", "sends, no long code fallback", "plain"),
            ("Alpha senders only", "US and CA fail with 21703", "bad"),
            ("All three empty", "every send 21704", "bad"),
        ],
    ),
}

V["twilio/from-number-not-sms-capable"] = {
    "flow_intro": (
        "One error code with four unrelated causes, so the classifier checks them "
        "in the order Twilio does: format, then ownership, then capabilities. A "
        "subaccount number reported as voice only sends somebody the wrong way."
    ),
    "diagram_problem": D.chain(
        "tfnc-p",
        "A working phone number that rejects every message it is asked to send",
        "The number demonstrably works, so the error looks wrong and the next step "
        "is a retry rather than a question about which of four things happened.",
        [
            ("Number answers calls", "voice is fine"),
            ("Used as an SMS From", "by a new job"),
            ("capabilities.sms false", "voice only number"),
            ("Every send 21606", "rejected at request time"),
            ("Retried all night", "no message created"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "tfnc-f",
        "Sorting senders by which of the four causes of 21606 they carry",
        "Only one of these is about capabilities. The other three are format, "
        "ownership and provisioning, and none is fixed by buying a number.",
        ("Lookup by exact number", "capabilities plus account_sid"),
        [
            ("sms true, owned here", "clear to send", "good"),
            ("Not in E.164", "rejected before ownership", "plain"),
            ("Another subaccount", "capable, still 21606", "bad"),
            ("capabilities.sms false", "no setting turns it on", "bad"),
        ],
    ),
}

V["twilio/messaging-service-no-status-callback"] = {
    "flow_intro": (
        "The sink and the subscription are judged as a pair, because a sink "
        "subscribed to voice events and a sink that is not active both look like "
        "instrumentation from a distance and report nothing."
    ),
    "diagram_problem": D.chain(
        "tmsc-p",
        "A dashboard reporting every message as sent while none of them arrived",
        "The create response is an acceptance. Everything that decides whether a "
        "human saw the message happens afterwards, and reports somewhere else.",
        [
            ("Messages.create", "returns queued"),
            ("App records sent", "final state written"),
            ("Terminal status fires", "no callback set"),
            ("21610 and 30007 lost", "only in Twilio logs"),
            ("List rots quietly", "months of it"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "tmsc-f",
        "Sorting services by whether any delivery signal actually reaches you",
        "A sink believed to be working is worse than none at all, so it gets its "
        "own state rather than being counted as instrumented.",
        ("Services, sinks, subscriptions", "read and joined"),
        [
            ("status_callback set", "status and error_code arrive", "good"),
            ("Active messaging sink", "Event Streams carries it", "plain"),
            ("Sink not active", "believed working, delivers nothing", "bad"),
            ("Neither configured", "no delivery signal at all", "bad"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
