#!/usr/bin/env python3
"""Diagrams for the /stripe/ field notes, batch X.

Same two shapes as the rest of the site: the problem is a chain that breaks at
one step, the fix is a branch, because every script in this section classifies
what it finds rather than guessing. Drawn in Stripe indigo.

No em dashes inside SVG text. One mis-sniffed encoding turns a single character
into three mojibake ones inside an image, where nothing will catch it.
"""
import diagrams as D

# Set before the diagrams below are built, restored at the bottom of the module.
# Every diagram here is constructed at import time, so the theme has to be active
# across exactly this file and no further.
BRAND = "#635BFF"
D.set_theme(BRAND)

V = {}

V["stripe/report-run-failed-silently"] = {
    "flow_intro": (
        "The script reads what Stripe actually did rather than what the job logged, "
        "then asks the question the run list cannot answer on its own: which nights "
        "produced no run at all."
    ),
    "diagram_problem": D.chain(
        "srrfs-p",
        "A report run failing after the create call returned 200",
        "The job exits zero on the receipt. Everything that can go wrong is "
        "evaluated afterwards, where nobody is looking.",
        [
            ("Job posts a run", "interval computed locally"),
            ("Stripe returns 200", "status pending"),
            ("Job exits zero", "success recorded"),
            ("Run fails", "error on the object"),
            ("No file lands", "found at month end"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "srrfs-f",
        "Sorting report runs by status, by age and by the nights that are missing",
        "A window of successful runs is still a broken export if one night has no "
        "run in it at all.",
        ("GET /v1/reporting/report_runs", "plus enabled_events on the endpoints"),
        [
            ("All succeeded, event subscribed", "clear", "good"),
            ("Pending over an hour", "stalled, treat it as failed", "bad"),
            ("Status failed", "read error, fix the parameter", "bad"),
            ("A day with no run", "the scheduler never fired", "bad"),
            ("Clean but unsubscribed", "next failure is silent", "plain"),
        ],
    ),
}

V["stripe/report-interval-past-data-available-end"] = {
    "flow_intro": (
        "The script compares what each run asked for against the window Stripe had "
        "finalized, because a short report and a complete one look identical from "
        "every field on the run object."
    ),
    "diagram_problem": D.chain(
        "sride-p",
        "A report run reaching past data available end and succeeding anyway",
        "Truncation is a success, not an error, so every guard rail watching status "
        "reports the night as healthy.",
        [
            ("Job asks to midnight", "interval_end in local time"),
            ("Data not final yet", "availability still behind"),
            ("Stripe answers short", "no error raised"),
            ("Run says succeeded", "file arrives, loads"),
            ("Totals under count", "re run gives more"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "sride-f",
        "Sorting report intervals against the finalized availability window",
        "Landing exactly on the boundary is not safe. It is the same request that "
        "gets truncated the night Stripe finalizes an hour later.",
        ("GET /v1/reporting/report_types", "compared with each run interval"),
        [
            ("Well inside the window", "covered", "good"),
            ("Within an hour of the edge", "a coin flip, move the job", "plain"),
            ("Past data_available_end", "short, and it still succeeded", "bad"),
            ("Window itself 36h stale", "defer, do not retry", "bad"),
        ],
    ),
}

V["stripe/sigma-scheduled-query-failing"] = {
    "flow_intro": (
        "The script reads the terminal state of every run, then checks the one thing "
        "no status can show: whether runs are still being produced at all."
    ),
    "diagram_problem": D.chain(
        "ssqr-p",
        "A Sigma scheduled query timing out and reporting the failure as no email",
        "The query was never edited. The tables it scans grew until the run stopped "
        "fitting its execution budget.",
        [
            ("Query fits budget", "written on small tables"),
            ("Data grows", "run time climbs"),
            ("Run times out", "status timed_out"),
            ("No email sent", "no bounce, no error"),
            ("Read as a quiet week", "six weeks pass"),
        ],
        fail_at=1,
        loop=(4, 1, "every later run fails the same way"),
    ),
    "diagram_fix": D.branch(
        "ssqr-f",
        "Sorting scheduled query runs by terminal state, cadence and result expiry",
        "A run can be completed and still have lost its data, because results "
        "expire whether or not anyone downloaded them.",
        ("GET /v1/sigma/scheduled_query_runs", "plus the cadence you expect"),
        [
            ("Completed, result live", "clear", "good"),
            ("Completed, result expired", "success with nothing to fetch", "bad"),
            ("timed_out or failed", "narrow the query, do not retry", "bad"),
            ("Newest run past cadence", "the schedule has stopped", "bad"),
        ],
    ),
}

V["stripe/terminal-readers-offline"] = {
    "flow_intro": (
        "The script trusts last_seen_at rather than status, and refuses to judge a "
        "reader whose timestamp arrived in the wrong units, because that mistake "
        "flags an entire fleet as decades stale."
    ),
    "diagram_problem": D.chain(
        "stro-p",
        "A Terminal reader going offline and leaving no failed payments behind",
        "Nothing fails, because nothing starts. The outage is an absence of records "
        "rather than a list of them.",
        [
            ("Router reboots", "reader loses network"),
            ("Reader goes offline", "actions refused"),
            ("No PaymentIntent", "nothing created"),
            ("No failed charges", "no alert fires"),
            ("Found on Monday", "by the missing takings"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "stro-f",
        "Sorting Terminal readers by check in age rather than by reported status",
        "status lags reality and last_seen_at is in milliseconds, so both the "
        "ordering and the units decide whether this check is worth running.",
        ("GET /v1/terminal/readers", "last_seen_at against a millisecond clock"),
        [
            ("Checked in minutes ago", "online", "good"),
            ("Online but stale 6h", "unusable whatever status says", "bad"),
            ("status offline", "power cycle, check the network", "bad"),
            ("Action failed", "reachable but wedged", "bad"),
            ("Timestamp in seconds", "refuse to judge, fix the units", "plain"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
