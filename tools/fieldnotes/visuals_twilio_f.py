#!/usr/bin/env python3
"""Diagrams for the /twilio/ field notes, batch F.

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

V["twilio/sms-pumping-protection-30450"] = {
    "flow_intro": (
        "The script groups the failures by dialling code rather than by number, "
        "because the block is scoped to a destination or a region: per number, "
        "one event looks like two hundred unrelated one-offs."
    ),
    "diagram_problem": D.chain(
        "tpmp-p",
        "An OTP burst refused by SMS Pumping Protection and recovering by itself",
        "Nothing here is broken by the time anyone looks. The block lifts on its "
        "own, and the only record left is an integer on a few hundred messages.",
        [
            ("Sign-ins spike", "one new country"),
            ("Pattern matched", "looks like pumping"),
            ("Sends refused", "error 30450"),
            ("Block lifts", "15 to 30 minutes"),
            ("Nobody finds it", "dashboards green"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "tpmp-f",
        "Sorting destination prefixes by the shape of their blocked window",
        "A burst that already stopped and a prefix still failing now need "
        "different answers: one is a safe list entry, the other is a ticket.",
        ("Messages paged by date", "grouped by dialling code"),
        [
            ("No 30450 at all", "clean, leave it", "good"),
            ("One or two blocked", "too few to escalate", "plain"),
            ("Short window, ended", "lifted itself, safe list it", "bad"),
            ("Half the prefix, still now", "outage for that country", "bad"),
        ],
    ),
}

V["twilio/body-exceeds-1600-chars-21617"] = {
    "flow_intro": (
        "The script reads two lists, because the failure and its warning signs "
        "live apart: Monitor Alerts holds the rejections that never became "
        "messages, and the Messages list holds the bodies that are nearly there."
    ),
    "diagram_problem": D.chain(
        "t1600-p",
        "A rendered template rejected with 21617 and leaving no Message row",
        "The template is fine for almost everyone. It is the one customer with "
        "long interpolated values whose message never exists at all.",
        [
            ("Template renders", "long name, long address"),
            ("Body past 1600", "after substitution"),
            ("API rejects", "error 21617"),
            ("No Message created", "nothing to page for"),
            ("Delivery rate flat", "never in the denominator"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "t1600-f",
        "Sorting senders by how close their longest body came to the ceiling",
        "Near misses are the only early warning this failure has: a sender at "
        "1250 characters is one longer customer name from dropping a message.",
        ("Alerts plus Messages", "rejections and body lengths"),
        [
            ("Short bodies", "fine, nothing to do", "good"),
            ("Over 320 characters", "cost and carriers notice", "plain"),
            ("Longest near 1600", "next long name is rejected", "bad"),
            ("21617 in Alerts", "already losing sends", "bad"),
        ],
    ),
}

V["twilio/ucs2-segment-inflation"] = {
    "flow_intro": (
        "The script recomputes the encoding from the body rather than trusting "
        "num_segments, because the billed count tells you the cost while the "
        "recomputation tells you which character caused it."
    ),
    "diagram_problem": D.chain(
        "tucs-p",
        "A curly apostrophe moving a whole template from GSM-7 to UCS-2",
        "Every step succeeds and every message is delivered. The only thing "
        "that changes is the number of segments each send is billed for.",
        [
            ("Copy edited", "straight quote to curly"),
            ("Body leaves GSM-7", "one character decides"),
            ("70 per segment", "instead of 160"),
            ("Segments triple", "no error code"),
            ("Bill triples", "found six weeks later"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "tucs-f",
        "Sorting message bodies by whether their UCS-2 encoding was avoidable",
        "An emoji and a curly quote are not the same finding: one is a price "
        "worth paying and the other is a substitution nobody chose.",
        ("Body recomputed offline", "alphabet, units, segments"),
        [
            ("All GSM-7", "cheapest it can be", "good"),
            ("Billed under raw cost", "Smart Encoding is covering", "plain"),
            ("Emoji or non Latin", "UCS-2 is correct here", "plain"),
            ("Only smart punctuation", "extra segments every send", "bad"),
        ],
    ),
}

V["twilio/messaging-queue-overflow-30001"] = {
    "flow_intro": (
        "The script totals segments rather than messages, because the queue is "
        "measured in segments: a three segment body takes three slots, which is "
        "how a job that fitted last month stops fitting."
    ),
    "diagram_problem": D.chain(
        "tqov-p",
        "A bulk run overflowing the queue behind a single long code",
        "The producer is not at fault for being fast. The sender drains at "
        "about one segment a second whatever is handed to it.",
        [
            ("List grows", "40k recipients"),
            ("Job dispatches", "11 minutes"),
            ("One long code", "about 1 MPS"),
            ("Queue full", "30001 and 21611"),
            ("Rest arrive late", "next afternoon"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "tqov-f",
        "Sorting senders by hours of queued segments against what they can drain",
        "The useful row is the one with no failures yet and more than ten hours "
        "of segments behind it, a week before the incident.",
        ("Segments per sender", "divided by its throughput"),
        [
            ("Well under capacity", "clean", "good"),
            ("Still draining", "queued but inside the window", "plain"),
            ("Past ten hours", "next run this size overflows", "bad"),
            ("30001 or 21611 seen", "already refusing work", "bad"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
