#!/usr/bin/env python3
"""Diagrams for the /twilio/ field notes, batch D.

Four webhook failures that all land in the same alerts list and look identical
from the outside. The problem is a chain that breaks at one step, the fix is a
branch, because every script in this batch sorts what it finds rather than
guessing. Drawn in Twilio red.

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

V["twilio/status-callback-webhook-failing-11200"] = {
    "flow_intro": (
        "The script matches the logged URL against the configured one on host and "
        "path, because Twilio appends its own parameters to the URL it fetches and "
        "a raw string comparison would file every alert under some other webhook."
    ),
    "diagram_problem": D.chain(
        "tscb-p",
        "A delivery update lost because the status callback returned a 500",
        "The message itself is fine at every step. Only the copy of the news "
        "that was pushed to you is lost, and only your database notices.",
        [
            ("Message sent", "API returns 201"),
            ("Carrier delivers", "status is delivered"),
            ("Callback fires", "one attempt, best effort"),
            ("Handler returns 500", "logged as 11200"),
            ("Row still queued", "no retry, no replay"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "tscb-f",
        "Sorting 11200 alerts by whether the URL is a configured status callback",
        "The two roles need different repairs. A failing callback loses "
        "bookkeeping you can re-read; a failing handler loses the call itself.",
        ("Alerts joined to config", "services and numbers"),
        [
            ("No 11200 at all", "callbacks landing", "good"),
            ("A handful on a callback", "slow handler under load", "plain"),
            ("Many on a callback", "your state is stale", "bad"),
            ("On an inbound handler", "the call itself dropped", "bad"),
        ],
    ),
}

V["twilio/webhook-connection-timeout-11205"] = {
    "flow_intro": (
        "The script sweeps once and keeps 11200 alongside 11205, because a host "
        "carrying both answered some of the time, and that is capacity rather "
        "than a firewall."
    ),
    "diagram_problem": D.chain(
        "tto-p",
        "A webhook request that never reaches the application at all",
        "Nothing in your own stack records this. There is no request id and no "
        "log line, because the connection was never established.",
        [
            ("Call arrives", "Twilio fetches the webhook"),
            ("DNS resolves", "the name is fine"),
            ("TCP handshake", "10 seconds allowed"),
            ("Nothing answers", "firewall or dead host"),
            ("11205 logged", "access log empty"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "tto-f",
        "Sorting hosts by the two error codes they produced in the same window",
        "A private address is proof on a single alert. No allowlist reaches an "
        "address Twilio can never dial.",
        ("Alerts grouped by host", "11205 beside 11200"),
        [
            ("No connection failures", "reachable", "good"),
            ("One or two only", "a restart or a scale event", "plain"),
            ("Both codes on one host", "capacity, not firewall", "bad"),
            ("11205 and nothing else", "never reachable at all", "bad"),
        ],
    ),
}

V["twilio/webhook-tls-certificate-expired-11236"] = {
    "flow_intro": (
        "The script groups on host and port rather than hostname, because a "
        "certificate is presented by whatever terminates TLS on a port and one "
        "name can front two listeners with two renewal stories."
    ),
    "diagram_problem": D.chain(
        "tcrt-p",
        "Every webhook to one hostname refused the second a certificate lapsed",
        "There is no gradient here. The certificate is valid until its notAfter "
        "timestamp and refused immediately afterwards.",
        [
            ("Renewal job broke", "90 days earlier, silently"),
            ("Certificate expires", "at one exact second"),
            ("Twilio validates chain", "before sending anything"),
            ("Validation fails", "11236, no request made"),
            ("Every number down", "voice, SMS and callbacks"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "tcrt-f",
        "Sorting hosts by what the alert timestamps can honestly support",
        "An oldest alert sitting on the edge of the 30 day window is the "
        "retention boundary, not the moment the certificate expired.",
        ("11236 grouped by host and port", "first and last date_generated"),
        [
            ("Quiet for hours", "renewed, outage measurable", "good"),
            ("Few, spread over days", "one stale node in a pool", "plain"),
            ("Cliff inside the window", "expired at that second", "bad"),
            ("Oldest at the window edge", "expiry predates retention", "bad"),
        ],
    ),
}

V["twilio/webhook-dns-resolution-failure-11210"] = {
    "flow_intro": (
        "The script reads the configuration as well as the alerts, because an "
        "alert exists only if Twilio tried: a number nobody dialled this month is "
        "broken and silent at the same time."
    ),
    "diagram_problem": D.chain(
        "tdns-p",
        "An inbound call ended by a hostname that only resolves on a laptop",
        "There is nothing to retry into. No connection, no response, and a "
        "fallback on the same name fails identically.",
        [
            ("URL copied over", "works on the developer machine"),
            ("Caller dials", "Twilio fetches the webhook"),
            ("Public DNS asked", "no record published"),
            ("NXDOMAIN", "11210 bad host name"),
            ("Call ends", "fallback shares the name"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "tdns-f",
        "Sorting webhook hostnames by the shape of the name itself",
        "Only the last label separates hooks.example.com from hooks.example, and "
        "one of those can never resolve.",
        ("Alerts plus every number URL", "hostname and its class"),
        [
            ("Ordinary public name", "record missing or lapsed", "bad"),
            ("Reserved suffix or one label", "never worked outside", "bad"),
            ("Tunnel hostname", "dev leftover, dead already", "bad"),
            ("Configured but never used", "no alert, still broken", "plain"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
