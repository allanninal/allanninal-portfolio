#!/usr/bin/env python3
"""Diagrams for the /twilio/ field notes, batch H.

Four Verify and Lookup notes. Same two shapes as the rest of the site: the
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

V["twilio/verify-conversion-rate-collapse"] = {
    "flow_intro": (
        "The script judges each country against the service's own baseline rather "
        "than a fixed percentage, and only above a volume floor, because a funnel "
        "converting at 25 percent and one converting at 70 percent are both normal."
    ),
    "diagram_problem": D.chain(
        "tvcr-p",
        "A pumped OTP delivered, billed, and never entered by anyone",
        "Nothing along the way fails. The send succeeds, the carrier delivers, "
        "the invoice grows, and the only trace is a code nobody typed in.",
        [
            ("Signup form hit", "public, no rate limit"),
            ("Verification starts", "one new number each time"),
            ("SMS delivered", "carrier collects its share"),
            ("Code never entered", "attempt stays unconverted"),
            ("Bill arrives", "no error code anywhere"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "tvcr-f",
        "Sorting countries by conversion rate against the service baseline",
        "Aggregated over the account the same data barely moves. Split by country, "
        "the attacked prefix separates from everything else at once.",
        ("Attempts Summary per country", "baseline first, then Country=ISO2"),
        [
            ("Near the baseline", "normal traffic", "good"),
            ("Under the volume floor", "too few to read", "plain"),
            ("Well below baseline", "watch a second window", "plain"),
            ("A fifth of baseline", "pumping in progress", "bad"),
        ],
    ),
}

V["twilio/verify-no-rate-limits"] = {
    "flow_intro": (
        "The script joins two responses per service, because a Rate Limit is only a "
        "named key: the bucket underneath it is the max per interval, and a limit "
        "without one enforces nothing at all."
    ),
    "diagram_problem": D.chain(
        "tvrl-p",
        "A scripted signup endpoint that meets no limit on the way through",
        "The per destination guard is real and always on. It simply never applies, "
        "because no destination is ever used twice.",
        [
            ("One host, one script", "ten thousand numbers"),
            ("Each number used once", "no repeat destination"),
            ("Platform guard misses", "keyed on the destination"),
            ("No Service Rate Limit", "opt in, never created"),
            ("Every start billed", "no ceiling at all"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "tvrl-f",
        "Sorting Verify Services by the tightest bucket that actually binds",
        "A limit with no buckets and a bucket of a thousand a minute both pass a "
        "review that only checks whether something exists.",
        ("RateLimits joined to Buckets", "normalised to starts per minute"),
        [
            ("Five per minute per key", "a real brake", "good"),
            ("Thousand per minute", "a resource, not a limit", "bad"),
            ("Limit with no buckets", "a name, nothing behind it", "bad"),
            ("No limits at all", "destination guard only", "bad"),
        ],
    ),
}

V["twilio/fraud-guard-blocking-prefix"] = {
    "flow_intro": (
        "Fraud Guard has no read API for its state, so the script infers the block "
        "from two other surfaces: unconverted attempts clustered on a prefix, and "
        "Lookup's sms_pumping_risk on one number in that range."
    ),
    "diagram_problem": D.chain(
        "tfgb-p",
        "A real user in a blocked prefix who cannot sign up for twelve hours",
        "The platform is correct and your customer is still locked out. The block "
        "is on the carrier range, and legitimate numbers share it.",
        [
            ("Pumping hits the prefix", "many numbers, one send each"),
            ("Fraud Guard reacts", "twelve hour SMS block"),
            ("Real user signs up", "same carrier range"),
            ("Delivery blocked", "60410 returned"),
            ("Retry re-arms it", "window starts again"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "tfgb-f",
        "Sorting prefix groups by what Lookup says about the range",
        "Blocked now, blocked twice last quarter and scoring 94 are three different "
        "problems on three different timescales.",
        ("Unconverted attempts by prefix", "one billed Lookup per group"),
        [
            ("No block, low score", "the failures are something else", "good"),
            ("No risk field returned", "unentitled, not clear", "plain"),
            ("Blocked in last 3 months", "the source is still arriving", "bad"),
            ("number_blocked true", "60410 for real users now", "bad"),
        ],
    ),
}

V["twilio/verify-sms-to-landline"] = {
    "flow_intro": (
        "The script reads lookup_enabled and skip_sms_to_landlines as a pair, "
        "because the skip depends on the lookup: set one without the other and the "
        "setting reads as protection while enforcing nothing."
    ),
    "diagram_problem": D.chain(
        "tvsl-p",
        "An OTP sent to a desk phone, billed, and expiring in silence",
        "With lookup off there is no 60205 to find this by. The verification is "
        "simply never converted, alongside every other abandoned signup.",
        [
            ("Form takes any digits", "valid E.164, desk phone"),
            ("Lookup disabled", "line type never checked"),
            ("SMS sent anyway", "attempt is billed"),
            ("No SMS inbox exists", "carrier drops it"),
            ("Pending until expiry", "counted as abandoned"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "tvsl-f",
        "Sorting destinations by line type before spending a message on them",
        "Fixed VoIP is the case that needs its own answer: rejecting it loses real "
        "users, accepting it produces failures nobody can reproduce.",
        ("Lookup line_type_intelligence", "plus the Service's two settings"),
        [
            ("mobile", "send the SMS", "good"),
            ("fixedVoip or unknown", "offer a voice call", "plain"),
            ("landline, pager, voicemail", "no SMS inbox exists", "bad"),
            ("skip on, lookup off", "a setting that does nothing", "bad"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
