#!/usr/bin/env python3
"""Diagrams for the /llm/ field notes, batch C.

Two shapes repeat here because the batch is two pairs. The key notes both fail
the same way: a state change that everyone reads as an ending, and a credential
that the ending never touched, so the problem chain runs from a deliberate
administrative act to a live key nobody lists. The caching notes are the two
halves of one setting, so their fix branches are deliberately mirror images:
one sorts a workload by whether caching was ever switched on, the other by
whether it earns back the premium it charges.

Drawn in the section's teal. No em dashes inside SVG text: one mis-sniffed
encoding turns a single character into three mojibake ones inside an image,
where nothing will catch it.
"""
import diagrams as D

# Set before the diagrams below are built, restored at the bottom of the module.
# Every diagram here is constructed at import time, so the theme has to be active
# across exactly this file and no further: visuals.py imports several of these
# modules in one process, and a theme left set would silently retint whichever
# section happened to be imported next.
BRAND = "#0D9488"
D.set_theme(BRAND)

V = {}

V["llm/key-owner-lost-project-access"] = {
    "flow_intro": (
        "The script walks projects before it walks keys, because the field that "
        "carries the finding is a filter on the per project key listing and there "
        "is no organization wide call that returns it."
    ),
    "diagram_problem": D.chain(
        "lkey-p",
        "An offboarding that removes the membership and leaves the credential",
        "Every step here is somebody doing their job correctly. The key survives "
        "because nothing in the sequence was ever pointed at it.",
        [
            ("Engineer mints a key", "personal, works instantly"),
            ("Key ships to production", "in a nightly job"),
            ("Engineer leaves", "SSO revoked same day"),
            ("Membership removed", "console access gone"),
            ("Key still authenticates", "and still bills"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "lkey-f",
        "Sorting inactive owner keys by whether anything still depends on them",
        "A key used this morning and a key never used once need opposite actions, "
        "so revoking them in one pass is how a cleanup becomes an outage.",
        ("Keys per project", "owner_project_access=inactive"),
        [
            ("Owner still has access", "nothing to do here", "good"),
            ("Never authenticated", "revoke it today", "plain"),
            ("Idle for months", "re-issue, then revoke", "bad"),
            ("Used this morning", "production is holding it", "bad"),
        ],
    ),
}

V["llm/archived-project-still-holds-keys"] = {
    "flow_intro": (
        "The script prints whether its own listing covered archived projects "
        "before it prints any finding, because the failure this note describes "
        "is an audit that returns a clean result over a partial universe."
    ),
    "diagram_problem": D.chain(
        "larc-p",
        "A project archived to close it, and the keys the archive never touched",
        "Archiving changes two fields on the project. It does not enumerate, "
        "disable or delete anything inside it.",
        [
            ("Prototype winds down", "team moves on"),
            ("Project archived", "the only closing action"),
            ("Keys left enabled", "nothing cascades"),
            ("Dropped from listings", "default excludes archived"),
            ("Audit never sees them", "and reports clean"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "larc-f",
        "Sorting archived projects by what their keys have done since the archive",
        "The comparison is last_used_at against archived_at, which is the only "
        "way to tell dead weight from an integration nobody knows is running.",
        ("Projects with include_archived", "keys read per archived project"),
        [
            ("Archived, no keys", "genuinely closed", "good"),
            ("Keys never used", "revoke, no risk", "plain"),
            ("Last used pre archive", "dead weight, remove", "bad"),
            ("Used after archiving", "closed on paper only", "bad"),
        ],
    ),
}

V["llm/prompt-caching-never-used"] = {
    "flow_intro": (
        "The script sums four token fields and two of them are nested inside a "
        "cache_creation object, which is the difference between finding this "
        "problem and inventing it on an organization that caches heavily."
    ),
    "diagram_problem": D.chain(
        "lpcn-p",
        "A stable prefix reprocessed at full price on every single call",
        "There is no error, no header and no warning anywhere in this sequence. "
        "The only evidence is a usage field that has always been zero.",
        [
            ("Long stable prefix", "prompt, tools, examples"),
            ("No cache_control sent", "caching is opt in"),
            ("Prefix reprocessed", "billed at base input"),
            ("Response looks normal", "nothing to log"),
            ("Read tokens stay zero", "for every bucket"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "lpcn-f",
        "Sorting a workload by what its cache read and write totals actually say",
        "Zero reads has two completely different meanings depending on the write "
        "column, and only one of them is this note.",
        ("Usage report by model", "and by workspace, 30 days"),
        [
            ("Reads above zero", "caching is on here", "good"),
            ("Little uncached input", "too quiet to judge", "plain"),
            ("Zero reads, zero writes", "never switched on", "bad"),
            ("Zero reads, writes paid", "on and losing money", "bad"),
        ],
    ),
}

V["llm/cache-writes-with-no-reads"] = {
    "flow_intro": (
        "The script keeps the two cache TTLs apart all the way through, because "
        "a 5m write and a 1h write are priced differently and the break even "
        "ratio a key has to clear depends on how its writes split between them."
    ),
    "diagram_problem": D.chain(
        "lcwr-p",
        "A premium paid on every call for a lookup that never happens",
        "Nothing here is broken. The API caches what it was asked to cache and "
        "bills the documented rate for doing it.",
        [
            ("Caching switched on", "cost optimisation"),
            ("Request id in the prefix", "before the breakpoint"),
            ("Prefix differs each call", "lookup misses"),
            ("Fresh entry written", "1.25x or 2x base input"),
            ("Entry expires unread", "surcharge, no payback"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "lcwr-f",
        "Sorting keys by read tokens per write token against their own break even",
        "The report carries token sums and no request count, so this ratio is "
        "tokens over tokens rather than reads over calls.",
        ("Hourly buckets by api_key_id", "writes split by TTL"),
        [
            ("Well above break even", "caching is paying", "good"),
            ("No writes, no reads", "the other note", "plain"),
            ("Barely above the line", "one quiet week from losing", "bad"),
            ("Below break even", "costs more than off", "bad"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
