#!/usr/bin/env python3
"""Diagrams for the /twilio/ field notes, batch S.

Four Verify settings nobody revisits after the integration works. Same two
shapes as the rest of the site: the problem is a chain that breaks at one step,
the fix is a branch, because every script in this section classifies what it
finds rather than guessing. Drawn in Twilio red.

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

V["twilio/verify-code-length-too-short"] = {
    "flow_intro": (
        "The script prints the keyspace and the number of starts an attacker "
        "needs rather than the length itself, because 4 and 6 read as "
        "neighbouring integers and are a hundredfold apart in work."
    ),
    "diagram_problem": D.chain(
        "tvcl-p",
        "A four digit code ground down five guesses at a time",
        "No step here errors. Each verification is started, checked five times "
        "and abandoned exactly as the API intends.",
        [
            ("Length set to 4", "quicker to read in QA"),
            ("Ten thousand codes", "the whole keyspace"),
            ("Five checks spent", "60202, verification dead"),
            ("Start another", "budget resets, free"),
            ("Even odds by 1000", "no alert anywhere"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "tvcl-f",
        "Sorting Verify Services by how much work one code is worth",
        "A custom code flag outranks the length outright: the field still reads "
        "6 while your own generator decides what gets sent.",
        ("GET Verify Services", "code_length, custom_code_enabled"),
        [
            ("Six digits or more", "keyspace is not the weak link", "good"),
            ("Five digits", "an afternoon of scripted starts", "plain"),
            ("Four digits", "ten thousand codes, five at a time", "bad"),
            ("custom_code_enabled", "length describes nothing", "bad"),
        ],
    ),
}

V["twilio/verify-max-check-attempts"] = {
    "flow_intro": (
        "The script reads the HTTP status alongside the body, because Verify "
        "soft deletes a verification once it resolves: a 404 here is the healthy "
        "answer and treating it as an error reports a working account as broken."
    ),
    "diagram_problem": D.chain(
        "tvmc-p",
        "A keystroke handler that spends the check budget before the last digit",
        "The failure lands on the one request that was correct. The four before "
        "it were genuine checks against a half typed code.",
        [
            ("User types code", "handler fires per keystroke"),
            ("Partial codes checked", "four real failures"),
            ("Last digit arrives", "the code is right"),
            ("Budget already gone", "60202 on a 429"),
            ("Retry loop begins", "nothing can approve it"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "tvmc-f",
        "Sorting verification lookups by status and by the clock",
        "Same status, two responses: inside the ten minute window somebody is "
        "waiting, outside it the record is only evidence of a rate.",
        ("GET one Verification", "HTTP status plus status field"),
        [
            ("404 returned", "soft deleted, it resolved", "good"),
            ("pending", "checks still available", "good"),
            ("Burned, past its life", "counts towards the rate", "plain"),
            ("Burned, still live", "a user stuck on that screen", "bad"),
        ],
    ),
}

V["twilio/verify-max-send-attempts"] = {
    "flow_intro": (
        "The script measures the smallest gap between sends, not just how many "
        "there were: four over three minutes is a person in bad coverage, four "
        "over six seconds is code firing on its own."
    ),
    "diagram_problem": D.chain(
        "tvms-p",
        "A resend button with no cooldown draining the send budget in seconds",
        "Every send in the burst succeeded, was delivered and was billed. The "
        "only failure is the press that finally returns 60203.",
        [
            ("SMS takes 11 seconds", "slower than the user waits"),
            ("Resend, resend, resend", "no cooldown on the button"),
            ("Four codes delivered", "all billed, all valid"),
            ("Fifth press", "60203, budget spent"),
            ("Clears on a check", "which never happens"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "tvms-f",
        "Sorting verifications by send count and by the spacing between sends",
        "A channel escalation from SMS to a call is a good design and still "
        "spends from the same five.",
        ("send_code_attempts", "count, channel and time"),
        [
            ("One send", "the design working", "good"),
            ("Spaced like a person", "resends a minute apart", "good"),
            ("Gap under 30 seconds", "something resent on its own", "bad"),
            ("Five sends", "60203 until a check lands", "bad"),
        ],
    ),
}

V["twilio/verify-do-not-share-warning-off"] = {
    "flow_intro": (
        "The script joins the Services to the account's Templates, because the "
        "flag appends to Twilio's default body: set a custom default template and "
        "a true flag stops meaning the warning went out."
    ),
    "diagram_problem": D.chain(
        "tvdsw-p",
        "A bare OTP read aloud to somebody claiming to be support",
        "Nothing is compromised and no request is malformed. The code is valid, "
        "delivered on time, and the session logs say the verification succeeded.",
        [
            ("Caller phones customer", "claims to be your support"),
            ("Verification started", "by the caller, on cue"),
            ("Code arrives", "digits and nothing else"),
            ("No caution line", "flag off since day one"),
            ("Customer reads it out", "logged as a success"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "tvdsw-f",
        "Sorting Verify Services by whether the warning reaches the handset",
        "A template SID the key cannot resolve is missing information rather "
        "than evidence, so it gets its own answer instead of a guess.",
        ("Services joined to Templates", "flag, template sid, dtmf"),
        [
            ("Flag on, default body", "the warning ships", "good"),
            ("Flag on, custom template", "body is whatever it says", "plain"),
            ("Template not readable", "unknown, not covered", "plain"),
            ("Flag off", "the code and nothing else", "bad"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
