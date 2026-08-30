#!/usr/bin/env python3
"""Diagrams for the /slack/ field notes, batch N.

Three notes about transports and the things that arrive on them, drawn so that
no two of them share a shape. One is the only chain in the section where cause
and effect happen in the same second, which is exactly why it gets misread as
the one failure that is spread over minutes. One has four months between its
third box and its fifth, and the box in the middle is not a mistake at all: a
laptop closed. And one puts its failure on an event that is not a deploy, which
is the whole reason it can be audited in advance. Drawn in Slack aubergine.

No em dashes inside SVG text. One mis-sniffed encoding turns a single character
into three mojibake ones inside an image, where nothing will catch it.
"""
import diagrams as D

# Set before the diagrams below are built, restored at the bottom of the module.
# Every diagram here is constructed at import time, so the theme has to be
# active across exactly this file and no further: visuals.py imports several of
# these modules in one process, and a theme left set would silently retint
# whichever section happened to be imported next.
BRAND = "#4A154B"
D.set_theme(BRAND)

V = {}

V["slack/app-mention-vs-message-double-fire"] = {
    "flow_intro": (
        "The only chain in this section whose cause and effect land in the same "
        "second. Every other duplicate in these notes is separated by a minute "
        "or five, and that difference is the whole diagnosis, which is why the "
        "chain ends on a dedupe store being shipped rather than on the "
        "duplicates themselves. The fix branch is one subtraction wide: two "
        "red rows for the pair that belongs here, and two plain rows handing "
        "the other spacings to the notes that own them."
    ),
    "diagram_problem": D.chain(
        "skdbfire-p",
        "Two handlers subscribed to overlapping events, replying twice to one mention",
        "Nothing in this chain is a mistake in isolation. A mention handler is "
        "correct, a keyword handler is correct, and the overlap between them is "
        "written down nowhere and appears the first time somebody says the "
        "bot's name.",
        [
            ("Mention handler", "app_mention only"),
            ("Second handler", "message.channels"),
            ("One sentence", "two events, two ids"),
            ("Two replies", "milliseconds apart"),
            ("Blamed on retries", "a dedupe store ships"),
        ],
        fail_at=0,
    ),
    "diagram_fix": D.branch(
        "skdbfire-f",
        "The subscription list read for overlaps, and reply pairs sorted by their spacing",
        "The overlap is knowable from two lines of configuration before anyone "
        "complains. The history read only confirms it, and the gap between the "
        "copies decides which of three notes you are actually reading.",
        ("bot_events and one page", "two lines and a subtraction"),
        [
            ("app_mention and message both subscribed",
             "one sentence, two deliveries, two event ids", "bad"),
            ("Two replies under a second apart",
             "one utterance handled twice in the same tick", "bad"),
            ("Sixty or three hundred seconds apart",
             "a retry, and the dedupe note owns it", "plain"),
            ("No mention in front of the pair",
             "an echo loop rather than an overlap", "plain"),
            ("Both subscribed, message handler guarded",
             "the overlap is known about and handled", "good"),
        ],
    ),
}

V["slack/http-or-dead-tunnel-request-url"] = {
    "flow_intro": (
        "Four months separate the third box from the fifth, and the third box "
        "is not a mistake: somebody closed a laptop. That is what makes this "
        "chain unusual to read, because there is no step in it anybody would "
        "have reviewed. The fix branch never leaves the manifest. Its two plain "
        "rows are both refusals: one because Socket Mode makes the whole "
        "question moot, and one because a hostname that looks right is not a "
        "hostname anybody dialled."
    ),
    "diagram_problem": D.chain(
        "skdturl-p",
        "A Request URL verified on a development tunnel and left in the production app",
        "Verification is a moment and delivery is a habit. The tick records "
        "that one exchange succeeded, keeps recording it forever, and says "
        "nothing whatsoever about whether the address still answers.",
        [
            ("Tunnel started", "on a laptop, in March"),
            ("URL verified", "one exchange, one tick"),
            ("Laptop closed", "the host stops existing"),
            ("Config unchanged", "still green, still saved"),
            ("Months of silence", "no error anywhere"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "skdturl-f",
        "Every configured URL classified from its hostname, with nothing sent to it",
        "The finding is in the string, which is stronger evidence than a "
        "request would be and costs the production endpoint nothing. A host "
        "that answers a bare GET can still be the wrong deployment.",
        ("Every URL in the manifest", "read, never dialled"),
        [
            ("A development tunnel hostname",
             "verified while it ran, gone ever since", "bad"),
            ("Plain http, or an address only you can reach",
             "could not have verified in this form", "bad"),
            ("Socket Mode is on",
             "none of these fields is used for delivery", "plain"),
            ("A routable public hostname",
             "no complaint, which is not a health check", "plain"),
            ("Production host, delivery seen today",
             "the address is not what is wrong", "good"),
        ],
    ),
}

V["slack/rtm-legacy-still-used"] = {
    "flow_intro": (
        "The failure here sits on an event that is not a deploy and not a code "
        "change: somebody added a scope. That is the entire reason this one can "
        "be audited in advance, and the reason the chain reaches its error "
        "through four boxes in which nothing at all goes wrong. The fix branch "
        "separates stable from doomed, because an old app quietly running RTM "
        "and a modern app calling rtm.connect are the same deprecation and "
        "completely different mornings."
    ),
    "diagram_problem": D.chain(
        "skrtmx-p",
        "A classic app on RTM losing its transport when the grant is reissued",
        "Nothing degrades. RTM works exactly as well on the last day as on the "
        "first, and the trigger is not a release: a scope is added, the grant "
        "comes back in the current vocabulary, and the current vocabulary has "
        "no client in it.",
        [
            ("Classic app", "client scope granted"),
            ("RTM connects", "four years, no incidents"),
            ("A scope is added", "the grant is reissued"),
            ("needed: client", "missing_scope on connect"),
            ("No screen grants it", "an unplanned migration"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "skrtmx-f",
        "The scope vocabulary, the client, and the replacement crossed without opening a socket",
        "Three reads and no connection. The grant header carries the same fact "
        "rtm.connect would return, only earlier and without minting a session "
        "nobody asked for.",
        ("Grant, client, configuration", "three reads, no socket opened"),
        [
            ("rtm.connect against a granular grant",
             "cannot connect, and cannot be granted", "bad"),
            ("Socket Mode on, nothing subscribed",
             "connected, healthy, and carrying nothing", "bad"),
            ("Classic grant still running RTM",
             "stable until the next reinstall", "plain"),
            ("Classic scopes, no RTM client",
             "a grant to tidy, which is the note next door", "plain"),
            ("Socket Mode with its events subscribed",
             "where RTM was always going", "good"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
