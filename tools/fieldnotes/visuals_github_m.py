#!/usr/bin/env python3
"""Diagrams for the /github/ field notes, batch M.

Four notes that read the same webhook config object and reach four different
conclusions, so the diagrams have to make the difference visible rather than
repeat one picture four times.

The first is a switch. An inactive hook is not attempted at all, so the problem
chain ends in an empty log rather than a failure, and the fix branch sorts on
the three routes to off - each with its own repair, one of which is somebody
else's note.

The second is not a config problem. Both signature headers arrive on every
delivery and the receiver picks one, so the chain is a check that passes every
day while checking the weaker digest, and the branch is a source scan rather
than an API read. Its rows include the two answers the scan is not entitled to
turn into a verdict.

The third is a certificate. The chain is a self-signed cert during setup and a
box that never got unticked, and the branch turns on one field with three
readable states, where the middle row is the plaintext hook this note hands to
its neighbour.

The fourth is the transport. The chain is a hostname that became public without
its URL ever changing, and the branch separates a leak from a hook GitHub was
never able to reach, with one row for the field that reads compliant while
there is no TLS at all.

Drawn in GitHub blue. No em dashes inside SVG text: one mis-sniffed encoding
turns a single character into three mojibake ones inside an image, where
nothing downstream will catch it.
"""
import diagrams as D

# Set before the diagrams below are built, restored at the bottom of the module.
# Every diagram here is constructed at import time, so the theme has to be
# active across exactly this file and no further: visuals.py imports several of
# these modules in one process, and a theme left set would silently retint
# whichever section happened to be imported next.
BRAND = "#0969DA"
D.set_theme(BRAND)

V = {}

V["github/webhook-inactive"] = {
    "flow_intro": (
        "One GET carries the finding and it is a boolean, which is why the "
        "script spends its effort somewhere else. Reading the flag is a line; "
        "knowing which of the three ways a hook arrived at false is the part "
        "that decides what you do next. Two timestamps separate a hook that "
        "was created switched off from one that somebody toggled later, and "
        "the last recorded response separates both from a hook GitHub "
        "disabled after a run of failures. That third case is not this note's "
        "problem at all, and re-enabling it without fixing the receiver spends "
        "the retention window you needed for the replay."
    ),
    "diagram_problem": D.chain(
        "ghact-p",
        "An inactive webhook producing no deliveries and therefore no evidence",
        "There is no failure anywhere. The delivery log is empty rather than "
        "full, which reads as an event that never happened.",
        [
            ("Hook toggled off", "during an incident"),
            ("No deliveries", "and no failures either"),
            ("Receiver searched", "routing, ingress, queue"),
            ("Log is empty", "so GitHub is blamed"),
            ("Five weeks dark", "nobody reads a boolean"),
        ],
        fail_at=1,
        loop=(3, 2, "so the receiver is instrumented again"),
    ),
    "diagram_fix": D.branch(
        "ghact-f",
        "Sorting a hook by its active flag and the two timestamps beside it",
        "The first row is somebody else's problem wearing this one's clothes. "
        "The last is the row that sends you to the events array.",
        ("GET the hooks, read active", "with created_at and last_response"),
        [
            ("Off after failures", "fix the receiver, then re-enable", "bad"),
            ("Off and edited later", "toggled and never toggled back", "bad"),
            ("Off since creation", "has never delivered anything", "bad"),
            ("On and log is empty", "a question about events, not this", "plain"),
            ("On and delivering", "the hook is doing its job", "good"),
        ],
    ),
}

V["github/webhook-sha1-signature-only"] = {
    "flow_intro": (
        "The API half of this script proves only that signatures are being "
        "sent. Which header the receiver verifies is a decision in your own "
        "source, and GitHub records what it sent rather than what you checked, "
        "so a tool that stops at the API can print a recommendation and never "
        "a finding. The second half reads files. It reports line numbers and "
        "never lines, and it is built around the one detail that makes a naive "
        "search worse than none: the legacy header name is a prefix of the "
        "modern one, so a plain substring match flags every correct receiver "
        "on exactly the lines where it is right."
    ),
    "diagram_problem": D.chain(
        "ghsig-p",
        "A receiver verifying the legacy SHA-1 header while the SHA-256 one arrives unused",
        "Every input this receiver has ever seen is handled correctly. There "
        "is nothing in any log, because nothing goes wrong.",
        [
            ("Both headers sent", "SHA-1 and SHA-256"),
            ("Receiver reads SHA-1", "written in 2017"),
            ("Every check passes", "forgeries still rejected"),
            ("Grep finds a hit", "inside the 256 name"),
            ("Marked as reviewed", "and left for years"),
        ],
        fail_at=1,
        loop=(3, 2, "and the audit is signed off again"),
    ),
    "diagram_fix": D.branch(
        "ghsig-f",
        "Sorting a receiver by which signature header name appears in its source",
        "The middle two rows are what an honest scan owes you. Neither is a "
        "pass and neither is the finding.",
        ("Secret set, headers sent", "then scan the receiver source"),
        [
            ("Only the legacy name", "the SHA-256 header is ignored", "bad"),
            ("Both names present", "as strong as the weaker one", "bad"),
            ("Neither name found", "built at runtime, or not verified", "plain"),
            ("No secret on the hook", "nothing is signed at all", "plain"),
            ("Only the modern name", "the header to verify", "good"),
        ],
    ),
}

V["github/webhook-insecure-ssl"] = {
    "flow_intro": (
        "One field, three readable states, and a parse rather than a test. "
        "Both values of insecure_ssl are non-empty strings, so a truthy check "
        "reports every correctly configured hook as insecure and the tool gets "
        "switched off after its first run. The branch also gives one row away: "
        "a hook with no TLS at all belongs to the plaintext note, because a "
        "field about certificate verification describes nothing on a handshake "
        "that never happens. What is left is the finding, and the repair it "
        "prints is a whole config, because the config is replaced and the "
        "secret comes back masked."
    ),
    "diagram_problem": D.chain(
        "ghssl-p",
        "Certificate verification disabled during setup and never switched back on",
        "Deliveries succeed for the whole life of this problem, which is the "
        "only reason it lasts as long as it does.",
        [
            ("Self signed cert", "on staging, deliveries fail"),
            ("Verification off", "one box, error gone"),
            ("Cert fixed later", "box never unticked"),
            ("Every signal green", "log clean, URL is https"),
            ("Review reads zero", "and moves on", ),
        ],
        fail_at=1,
        loop=(3, 2, "so the next review passes too"),
    ),
    "diagram_fix": D.branch(
        "ghssl-f",
        "Sorting a hook on a two-value string that must be parsed and not tested",
        "The second row is the neighbouring note, handed over rather than "
        "counted. The third is why this parses instead of testing.",
        ("GET the hooks, read insecure_ssl", "against the URL scheme"),
        [
            ("https and set to 1", "GitHub checks no certificate", "bad"),
            ("No TLS at all", "a plaintext hook, not this", "plain"),
            ("Field unreadable", "reported, never rounded", "plain"),
            ("https and set to 0", "the certificate is checked", "good"),
        ],
    ),
}

V["github/webhook-http-url"] = {
    "flow_intro": (
        "The scheme is the whole read, and everything else in the script "
        "exists to stop two different problems being reported as one. A "
        "plaintext hook on a routable host is a readable feed of your "
        "repository; the same scheme on a loopback or a private range is a "
        "hook GitHub has never been able to reach, which is a dead integration "
        "rather than a leak. One small function names the trap that keeps this "
        "alive through real audits: on a hook with no TLS, insecure_ssl reads "
        "the reassuring zero, because there is no certificate to verify."
    ),
    "diagram_problem": D.chain(
        "ghurl-p",
        "An internal http URL that became publicly routable without ever changing",
        "Nothing about the hook changed. The network around it did, and the "
        "URL was never part of any migration checklist.",
        [
            ("Internal http URL", "no cert, no time to get one"),
            ("Host goes public", "URL never revisited"),
            ("Payloads in clear", "signed, and readable"),
            ("Audit reads the flag", "insecure_ssl says zero"),
            ("Passed as compliant", "for another year"),
        ],
        fail_at=1,
        loop=(3, 2, "and the next audit samples the same field"),
    ),
    "diagram_fix": D.branch(
        "ghurl-f",
        "Sorting a hook URL by scheme, and a plaintext one by whether GitHub can reach it",
        "The first two rows share a scheme and share nothing else. One is "
        "exposure, the other is a hook that has never worked.",
        ("GET the hooks, read config.url", "scheme first, then the host"),
        [
            ("http to a routable host", "payloads readable in transit", "bad"),
            ("http to a private range", "unreachable, never delivered", "bad"),
            ("https, verification off", "the certificate note, not this", "plain"),
            ("https and verified", "encrypted and authenticated", "good"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
