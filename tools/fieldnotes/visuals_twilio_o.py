#!/usr/bin/env python3
"""Diagrams for the /twilio/ field notes, batch O.

Four failures arranged around the TLS handshake: two that end during it, one
that happens after it when the bytes coming back will not parse, and one that is
visible in configuration before anything is attempted at all. The problem is a
chain that breaks at one step, the fix is a branch, because every script in this
batch sorts what it finds rather than guessing. Drawn in Twilio red.

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

V["twilio/webhook-tls-handshake-failure-11220"] = {
    "flow_intro": (
        "The script keys on host and port with the port always written out, and "
        "counts every code logged against that listener rather than only the "
        "11220s, because the other codes are what decide which of three things "
        "an 11220 means."
    ),
    "diagram_problem": D.chain(
        "thsk-p",
        "A webhook refused during TLS negotiation, before any certificate is sent",
        "Nothing is validated and nothing is rejected on trust. The two ends "
        "simply found no version or cipher they both support.",
        [
            ("Call arrives", "handler is healthy"),
            ("Twilio connects", "TCP opens fine"),
            ("Client offers", "versions and ciphers"),
            ("No intersection", "connection reset"),
            ("Logged 11220", "certificate never seen"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "thsk-f",
        "Sorting listeners by the mix of error codes logged against each one",
        "A certificate code means the handshake reached the stage where "
        "certificates are sent. A code that needed a response means it finished.",
        ("Alerts at error and warning", "keyed on host and port"),
        [
            ("No 11220 here", "healthy listener", "good"),
            ("11220 plus 1123x", "clear the certificate first", "plain"),
            ("11220 plus answered calls", "one node, old config", "bad"),
            ("11220 and nothing else", "no shared cipher suite", "bad"),
        ],
    ),
}

V["twilio/webhook-tls-chain-untrusted-11237"] = {
    "flow_intro": (
        "The script counts 11237 and 11235 separately, because one is a trust "
        "problem and the other is a naming problem, and then reads the TwiML "
        "Applications, whose URLs never show up on the numbers that use them."
    ),
    "diagram_problem": D.chain(
        "tchain-p",
        "A leaf certificate accepted by a browser and refused by Twilio",
        "The browser filled in the intermediate your server left out. Twilio "
        "validates with what was actually presented and nothing more.",
        [
            ("Certificate issued", "valid for a year"),
            ("Only the leaf installed", "intermediates omitted"),
            ("Browser shows padlock", "it fetched the rest"),
            ("Twilio validates", "no path to a root"),
            ("Logged 11237", "every webhook refused"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "tchain-f",
        "Sorting hosts by which certificate path failure was logged",
        "An expiry on the same host is usually not a second fault: a renewal "
        "rewrites the file the chain is read from.",
        ("Alerts plus Applications", "grouped by hostname"),
        [
            ("No 11237 or 11235", "chain verifies", "good"),
            ("11236 as well", "one bad renewal, fix once", "plain"),
            ("11235 on an address", "needs a name, not a reissue", "bad"),
            ("11237 with no answers", "leaf only, or a private CA", "bad"),
        ],
    ),
}

V["twilio/webhook-http-protocol-violation-11206"] = {
    "flow_intro": (
        "The script reads the list to find the endpoints and then fetches a "
        "small sample of alerts one at a time, because response_headers is "
        "populated only by GET /v1/Alerts/{Sid} and appears on no row of the list."
    ),
    "diagram_problem": D.chain(
        "tproto-p",
        "A response your server logged as 200 and Twilio could not parse",
        "The handler succeeded and the framework wrote a header block. What "
        "left the socket was not a well formed HTTP response.",
        [
            ("Handler runs", "returns valid TwiML"),
            ("Cookie is set", "raw value, no encoding"),
            ("Server emits it", "no complaint at all"),
            ("Client parse fails", "logged 11206"),
            ("Your log says 200", "nothing to grep for"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "tproto-f",
        "Sorting fetched alerts by what the response headers show",
        "A row from the list has no response_headers at all. Reading that "
        "absence as an empty header block misreports every alert on the account.",
        ("One alert fetched on its own", "GET /v1/Alerts/{Sid}"),
        [
            ("Headers clean", "look at the body framing", "plain"),
            ("Never fetched", "the list cannot answer this", "plain"),
            ("Set-Cookie with no name", "or control characters", "bad"),
            ("No header block", "plain HTTP on an https port", "bad"),
        ],
    ),
}

V["twilio/phone-number-insecure-or-unreachable-webhook-url"] = {
    "flow_intro": (
        "The script reads configuration rather than alerts, and classifies the "
        "host before the scheme: a URL can be both cleartext and unroutable, and "
        "only one of those is costing anything today."
    ),
    "diagram_problem": D.chain(
        "turl-p",
        "A tunnel URL pasted into a live number on a Friday afternoon",
        "It answered perfectly all afternoon. Nothing recorded that the URL "
        "belonged to a session rather than to a service.",
        [
            ("Tunnel started", "laptop, one afternoon"),
            ("URL set on number", "API returns 200"),
            ("Demo works", "every request answered"),
            ("Laptop sleeps", "tunnel closes"),
            ("Number is dead", "11205 from then on"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "turl-f",
        "Sorting configured webhook URLs by what is wrong with them",
        "Numbers and TwiML Applications both, because an attached app's URLs "
        "win outright and never appear on the number.",
        ("Every URL field on both", "numbers and applications"),
        [
            ("https, public host", "nothing to do", "good"),
            ("Dev tunnel host", "working, counting down", "plain"),
            ("http scheme", "signature in clear on the wire", "bad"),
            ("Private or loopback", "never reachable from Twilio", "bad"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
