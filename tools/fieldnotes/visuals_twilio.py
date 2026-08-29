#!/usr/bin/env python3
"""Diagrams for the /twilio/ field notes, batch A.

Same two shapes as the rest of the site: the problem is a chain that breaks at
one step, the fix is a branch, because every script in this section classifies
what it finds rather than guessing. Drawn in Twilio red.

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

V["twilio/phone-number-still-on-demo-twiml"] = {
    "flow_intro": (
        "The script matches on host and path rather than on the whole URL, because "
        "the demo endpoint appears over http and https, with and without a query "
        "string, and pointing at several different demo documents."
    ),
    "diagram_problem": D.chain(
        "tdemo-p",
        "A call answered by Twilio's demo TwiML while the application waits",
        "Every step here succeeds. The webhook returns 200 with valid TwiML, so "
        "there is no failure anywhere for monitoring to notice.",
        [
            ("Number bought", "demo voice_url by default"),
            ("Caller dials", "call starts normally"),
            ("Twilio fetches", "demo.twilio.com answers 200"),
            ("Demo greeting", "your app never called"),
            ("Call completed", "nothing logged"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "tdemo-f",
        "Sorting phone numbers by what their voice and SMS handlers point at",
        "A number with no handler at all belongs in the same report: same cause, "
        "same fix, and it is billed every month for answering nothing.",
        ("GET IncomingPhoneNumbers.json", "voice_url, sms_url, application sids"),
        [
            ("Points at your app", "configured, leave it", "good"),
            ("Unedited TwiML Bin", "check it is deliberate", "plain"),
            ("demo.twilio.com", "never wired up, fix now", "bad"),
            ("No handler at all", "bought, billed, silent", "bad"),
        ],
    ),
}

V["twilio/inbound-webhook-black-hole"] = {
    "flow_intro": (
        "The script joins three responses, because no single one shows the failure: "
        "the routing mode is on the Messaging Service, the pool is a subresource of "
        "it, and sms_url lives on the number in the account API."
    ),
    "diagram_problem": D.chain(
        "tibh-p",
        "An inbound SMS dropped because the number has no sms_url",
        "The service URL is set and correct. It is simply not the URL that wins "
        "when the service defers to the sender's webhook.",
        [
            ("Reply arrives", "STOP or a customer answer"),
            ("Matched to number", "in the sender pool"),
            ("Defer to number", "service URL ignored"),
            ("sms_url is blank", "no request made"),
            ("Nothing logged", "no 4xx, no alert"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "tibh-f",
        "Sorting Messaging Services by where their inbound messages actually land",
        "Two settings, two ways to lose everything: the number without a URL, and "
        "the service that took the routing back and never set one.",
        ("Service, pool and numbers", "joined on the PN sid"),
        [
            ("Centralised on service", "one URL for the pool", "good"),
            ("Every number wired", "routed per sender", "good"),
            ("Blank sms_url in pool", "those numbers drop inbound", "bad"),
            ("No inbound_request_url", "whole pool drops inbound", "bad"),
        ],
    ),
}

V["twilio/messaging-service-not-a2p-registered"] = {
    "flow_intro": (
        "The script reads one boolean per service to find the candidates, then "
        "confirms each against the campaign subresource, because a service can be "
        "flagged registered while the campaign underneath is suspended."
    ),
    "diagram_problem": D.chain(
        "ta2p-p",
        "A cloned Messaging Service rejecting every US send with 30034",
        "Nothing along the way refuses the work. The service is created, named "
        "and filled with numbers, and only the carrier says no.",
        [
            ("Brand approved", "once, for the account"),
            ("Second service made", "staging or a new tenant"),
            ("Numbers added", "API returns 201"),
            ("No campaign attached", "registration is per service"),
            ("Every US send 30034", "found in production"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "ta2p-f",
        "Sorting Messaging Services by campaign state and by US senders in the pool",
        "The same missing campaign is a ticket on an empty service and an outage "
        "on one that is already sending.",
        ("GET Services and Usa2p", "plus the US long codes in each pool"),
        [
            ("Campaign VERIFIED", "registered, sending", "good"),
            ("No campaign, no US senders", "register before launch", "plain"),
            ("No campaign, US senders", "every send 30034 now", "bad"),
            ("Campaign not VERIFIED", "sends like no campaign", "bad"),
        ],
    ),
}

V["twilio/phone-number-missing-fallback-url"] = {
    "flow_intro": (
        "The script resolves the Application SID before judging the number, because "
        "when one is set it wins outright and every URL on the number, fallback "
        "included, is ignored."
    ),
    "diagram_problem": D.chain(
        "tfb-p",
        "A caller dropped during a ninety second deploy because no fallback is set",
        "Inbound voice has no retry. The caller is on the line now, so the fallback "
        "URL is the only mitigation that works while the app is broken.",
        [
            ("Deploy starts", "handler down 90 seconds"),
            ("Caller dials", "call connects to Twilio"),
            ("Webhook returns 502", "error 11200 logged"),
            ("No fallback_url", "nowhere to go"),
            ("Call terminated", "no retry, no queue"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "tfb-f",
        "Sorting numbers by whether their effective handler has a fallback",
        "Reading the fallback off the number when an Application SID is set is the "
        "exact mistake that reports an exposed number as protected.",
        ("Numbers plus their Applications", "effective handler per channel"),
        [
            ("Fallback on the handler", "covered", "good"),
            ("No handler on either channel", "a different report", "plain"),
            ("Live handler, no fallback", "one non 2xx drops the call", "bad"),
            ("Fallback on the wrong object", "app sid wins, number ignored", "bad"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
