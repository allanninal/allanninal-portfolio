#!/usr/bin/env python3
"""Diagrams for the /twilio/ field notes, batch T.

Four SIP and carrier failures that all carry an error code and none of which
that code explains on its own. Same two shapes as the rest of the site: the
problem is a chain that breaks at one step, the fix is a branch, because every
script in this section classifies what it finds rather than guessing. Drawn in
Twilio red.

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

V["twilio/sip-endpoint-not-registered-32009"] = {
    "flow_intro": (
        "The script preserves the case of the dialled username and folds it only "
        "after the exact comparison has already failed. A parser that lowercases "
        "on the way in destroys the one piece of evidence that separates a typo "
        "from an endpoint that went offline."
    ),
    "diagram_problem": D.chain(
        "t32009-p",
        "A Dial to a SIP endpoint refused because no registration matched the username",
        "The parent call runs its TwiML and ends normally, so the only trace is "
        "an alert against a child leg nobody joined back to anything.",
        [
            ("Credential created", "saved as Reception"),
            ("TwiML dials lower case", "reads identical to a human"),
            ("Twilio looks up", "exact match, nothing found"),
            ("32009 on the child leg", "user is not registered"),
            ("Parent completes", "dashboards see nothing"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "t32009-f",
        "Sorting 32009 alerts by which of five things went wrong",
        "An exact username match means the endpoint was merely offline. Everything "
        "above it is yours, and none of it fixes itself when the softphone "
        "reconnects.",
        ("Alerts joined to SIP domains", "dialled user, sip_registration, credentials"),
        [
            ("Username matches exactly", "registration had lapsed", "plain"),
            ("Matches only on case", "two different endpoints", "bad"),
            ("Username unknown", "never going to connect", "bad"),
            ("sip_registration false", "nothing may register at all", "bad"),
        ],
    ),
}

V["twilio/sip-infrastructure-communication-error-32011"] = {
    "flow_intro": (
        "The script reduces every enabled sip_url to a hostname before it counts "
        "anything. Three rows in the console that resolve to one machine share a "
        "firewall rule, an uplink and a power feed, and the console view argues "
        "the opposite."
    ),
    "diagram_problem": D.chain(
        "t32011-p",
        "Twilio unable to reach an origination host that three URIs all point at",
        "The trunk was configured for redundancy years ago and nobody since has "
        "resolved the three entries to see how many machines they name.",
        [
            ("Three origination URIs", "different ports, one host"),
            ("Firewall rule expires", "signalling range dropped"),
            ("INVITE gets no answer", "every URI, same box"),
            ("32011 on every call", "cause is outside Twilio"),
            ("Blamed on the network", "config looks redundant"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "t32011-f",
        "Sorting trunks by what their origination path can actually survive",
        "A diverse, ordered path that still throws 32011 is the useful answer: it "
        "sends you to the firewall and the TLS version instead of the topology.",
        ("Trunks plus their OriginationUrls", "hostname, transport, enabled, priority"),
        [
            ("Diverse hosts, alerts", "look at the edge, not the config", "plain"),
            ("One priority for all", "load balancing, not failover", "plain"),
            ("Every URI one host", "three rows, one machine", "bad"),
            ("Secure trunk, no TLS URI", "fails every call", "bad"),
        ],
    ),
}

V["twilio/trunk-cps-limit-exceeded-32001"] = {
    "flow_intro": (
        "The script buckets start_time to the second, because the ceiling is "
        "enforced against a one second window and every graph anyone owns "
        "aggregates coarser than that. A minute bucket divides the peak by sixty "
        "and still looks plausible."
    ),
    "diagram_problem": D.chain(
        "t32001-p",
        "A campaign burst shedding calls in one second and vanishing into the hourly rate",
        "The run recovers by itself as the queue drains, so by the time anyone "
        "looks the only evidence left is a rate computed at the wrong resolution.",
        [
            ("Batch opens", "dialer takes every channel"),
            ("First second saturates", "peak far above the mean"),
            ("Ceiling enforced", "32001, calls thrown away"),
            ("Hourly rate looks fine", "burst divided by 3600"),
            ("Blamed on the list", "limit ruled out by mistake"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "t32001-f",
        "Sorting a window of calls by its busiest single second, not its average",
        "A peak several times the mean is reported even when it clears the "
        "ceiling, because the shape is stable and the volume is not.",
        ("Calls bucketed per second", "peak, mean, ceiling you supply"),
        [
            ("Peak near the mean", "flat traffic, nothing to do", "good"),
            ("Peak four times the mean", "will breach as the list grows", "plain"),
            ("Peak on the ceiling", "one more call and it sheds", "bad"),
            ("32001 in the window", "calls already thrown away", "bad"),
        ],
    ),
}

V["twilio/carrier-blocked-caller-id-32017"] = {
    "flow_intro": (
        "The script sums answered seconds over completed calls only. Averaging "
        "duration across calls that rang out hands every busy dialer a flattering "
        "number and turns the whole check into decoration."
    ),
    "diagram_problem": D.chain(
        "t32017-p",
        "A number scored down by carrier analytics until the calls stop connecting",
        "Nothing in your account changed. The decision was made on the other side "
        "of the boundary using outcomes you can read but were not aggregating.",
        [
            ("High volume, short calls", "few answered, quickly ended"),
            ("Analytics score falls", "answer rate and duration"),
            ("Handsets label it", "answered even less often"),
            ("Carrier blocks outright", "32017, one network first"),
            ("Traffic rotates", "fresh number, same clock"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "t32017-f",
        "Sorting caller IDs by the two metrics the score is actually built from",
        "The point is finding the number that is next, not only the one already "
        "refused. Both are read from call records you already have.",
        ("Alerts joined to per number tallies", "answer rate, mean answered duration"),
        [
            ("Too few attempts", "no rate worth reading", "plain"),
            ("Good rate and duration", "nothing to change", "good"),
            ("Short answered calls", "the metric that pulls hardest", "bad"),
            ("32017 already raised", "carrier side, register it", "bad"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
