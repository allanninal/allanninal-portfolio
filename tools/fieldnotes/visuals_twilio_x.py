#!/usr/bin/env python3
"""Diagrams for the /twilio/ field notes, batch X.

Five failures around a sender pool and a clock. Two of them have no error code
at all, which is why the fix diagrams here spend so much of their space on the
states that are fine: an audit for a silent problem is only useful if a reader
can tell at a glance which of its findings are findings. Same two shapes as the
rest of the site, the problem as a chain that breaks at one step and the fix as a
branch, drawn in Twilio red.

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

V["twilio/number-not-in-messaging-service"] = {
    "flow_intro": (
        "The script takes a set difference and then asks one more question of "
        "each gap, because a number sending unpooled traffic today and one that "
        "has never sent anything need the same repair on very different days."
    ),
    "diagram_problem": D.chain(
        "tnims-p",
        "A number bought in a hurry, sending outside every Messaging Service",
        "Nothing along this line fails. Sender selection simply never runs, so "
        "the features that live on a service never apply to the traffic.",
        [
            ("Number bought", "for one quick test"),
            ("Pointed at code", "bare From in the send"),
            ("Never pooled", "no service holds it"),
            ("No selection", "no sticky sender, no geomatch"),
            ("Filtered more", "reads as deliverability"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "tnims-f",
        "Sorting owned numbers by pool membership and by whether they send",
        "Voice only numbers leave the report entirely. A pool cannot help them, "
        "and listing them is how a report teaches people to skim it.",
        ("Numbers minus pooled sids", "joined on the PN sid"),
        [
            ("In a sender pool", "selection applies", "good"),
            ("Not SMS capable", "out of scope", "plain"),
            ("Unpooled, no traffic", "pool it or release it", "plain"),
            ("Unpooled and sending", "unregistered traffic now", "bad"),
        ],
    ),
}

V["twilio/no-sender-matching-destination"] = {
    "flow_intro": (
        "Coverage is decided on two axes at once, country and message type, "
        "because a pool can satisfy either one alone and still leave sender "
        "selection with no candidate at all."
    ),
    "diagram_problem": D.chain(
        "t21703-p",
        "A populated sender pool with nothing eligible for a US recipient",
        "The service has senders and sends all day. Alphanumeric sender IDs are "
        "simply not candidates for a US or Canadian destination.",
        [
            ("Pool has senders", "three alpha senders"),
            ("Send to a US number", "first US customer"),
            ("Selection runs", "looks for a US sender"),
            ("Nothing eligible", "alpha cannot reach US"),
            ("Rejected 21703", "reads as empty pool"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "t21703-f",
        "Sorting a pool against one destination on country and on message type",
        "An empty pool is kept as its own answer: that is 21704 on every send "
        "rather than 21703 on this destination, and a different repair.",
        ("Three sender lists plus Lookup", "country and capabilities"),
        [
            ("Local sender, right type", "covered", "good"),
            ("No sender at all", "21704, other note", "plain"),
            ("No US or CA sender", "alpha does not count", "bad"),
            ("No MMS in country", "text sends, media 21703", "bad"),
        ],
    ),
}

V["twilio/multiple-tollfree-in-one-pool"] = {
    "flow_intro": (
        "The rule is a property of the pool rather than of any number in it, so "
        "the count is per service and the toll-free test matches the numbering "
        "plan rather than a prefix string."
    ),
    "diagram_problem": D.chain(
        "ttfp-p",
        "A second toll-free sender added for throughput, and the pool blocked",
        "The verification records stay in order throughout. What changed is the "
        "shape of the pool, and the judgement comes from the carrier.",
        [
            ("One toll-free sender", "verified, sending"),
            ("Second one added", "for more throughput"),
            ("Volume alternates", "between both senders"),
            ("Carrier sees snowshoe", "blocks the numbers"),
            ("Whole pool 30032", "the old number too"),
        ],
        fail_at=3,
        loop=(4, 1, "resubmitting verification changes nothing"),
    ),
    "diagram_fix": D.branch(
        "ttfp-f",
        "Sorting sender pools by how many toll-free numbers share them",
        "Long codes in the same pool are printed as context, not as a finding. "
        "The rule being checked is strictly the toll-free count.",
        ("PhoneNumbers per service", "numbering plan, not prefixes"),
        [
            ("No toll-free in pool", "not this note", "good"),
            ("Exactly one", "the recommended shape", "good"),
            ("Two or more", "carriers read it as snowshoeing", "bad"),
            ("Two, with 30032s", "already blocked, split now", "bad"),
        ],
    ),
}

V["twilio/messaging-service-validity-period-too-long"] = {
    "flow_intro": (
        "The setting alone proves nothing, so the script measures the queue as "
        "well: date_sent minus date_created per message, bucketed by the service "
        "whose ceiling governs it."
    ),
    "diagram_problem": D.chain(
        "tvpl-p",
        "A passcode delivered ten hours late and recorded as a success",
        "Every status here is green. The only trace of the wait is the gap "
        "between two timestamps that nothing draws attention to.",
        [
            ("Ten hour ceiling", "the untouched default"),
            ("Campaign queues first", "sender is busy"),
            ("Passcode waits", "well inside its deadline"),
            ("Delivered at 4pm", "requested at 6am"),
            ("Counted as sent", "user asked for three more"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "tvpl-f",
        "Sorting services by their ceiling and by the wait actually measured",
        "The API has no field for what a service carries, so the traffic type is "
        "declared rather than guessed from a friendly name.",
        ("validity_period plus queue wait", "per Messaging Service"),
        [
            ("Ceiling below the default", "watch 30036 instead", "good"),
            ("Default, declared bulk", "what the default is for", "good"),
            ("Default, nothing declared", "say which traffic it carries", "plain"),
            ("Default, waits measured", "late passcodes, not failures", "bad"),
        ],
    ),
}

V["twilio/sms-reply-loop-rate-limit-14107"] = {
    "flow_intro": (
        "Density is measured in a sliding window rather than by clock minute, "
        "and both directions are fetched, because half a conversation makes a "
        "loop look like a flood and points the repair at the wrong place."
    ),
    "diagram_problem": D.chain(
        "t14107-p",
        "Two auto-replying numbers holding a conversation with each other",
        "Every message in the loop sends successfully and is billed. The rate "
        "limit is the only thing in the system that ever objects.",
        [
            ("Handler always replies", "good manners"),
            ("Second number does too", "a test harness"),
            ("They find each other", "one message starts it"),
            ("Thirty in thirty seconds", "the pair ceiling"),
            ("Rejected 14107", "reads as throughput"),
        ],
        fail_at=3,
        loop=(3, 2, "each reply is the next message in"),
    ),
    "diagram_fix": D.branch(
        "t14107-f",
        "Sorting a pair's history by density and by which directions appear",
        "The quiet case is the one under the ceiling: nothing fails, nothing "
        "stops it, and every segment is billed.",
        ("Both directions merged", "sliding thirty second window"),
        [
            ("Sparse traffic", "an ordinary conversation", "good"),
            ("Dense, one direction", "send loop, fix the sender", "bad"),
            ("Dense, both directions", "handler answering itself", "bad"),
            ("Repeats under the limit", "loops on, never trips", "bad"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
