#!/usr/bin/env python3
"""/slack/ field notes, batch T - the writing.

Two notes about the size and the age of what you put in Slack, and two about
the delivery mode you chose for the app, written so that no two of them read
the same field or end in the same repair.

The first is a ceiling. Slack caps one file at 1 GB and almost nobody meets
that number: the byte transfer is a plain request to a storage host that is not
Slack, it does not inherit the Slack client's timeouts, and it gives up first.
The reading is the size distribution of what the app has already uploaded, and
the finding is predictive rather than historical - the upload that breaks next
quarter is already in the list today.

The second is a clock. A workspace retention policy deletes messages and files
on a schedule that nobody tells the app about, so an integration that treats
Slack as its archive inherits somebody else's deletion policy as its data-loss
policy. The reading is a bisection: probe history at increasing ages until the
results stop, and report the boundary in days. That is a different failure from
a file being deleted while its message survives, which is its own note - here
nothing is rotting, everything older than a line is simply gone, uniformly, on
purpose, by policy.

The third is a configuration collision. One Slack app has one configuration and
Slack has no notion of environments, so an app with Socket Mode switched on for
local development still carries the Request URL it was given for production.
The reading is two manifest fields held together, and the corroboration is the
spacing between duplicate messages, because two live delivery paths and Slack's
own retry ladder look identical until you measure the gap.

The fourth is a dead end rather than a fault. Socket Mode apps cannot be listed
on the Slack Marketplace, so an app built on Socket Mode and later pointed at
other workspaces has to change its delivery architecture before it can be
distributed at all. Nothing is broken, nothing errors, and the finding is that
the road ends. The reading is the manifest crossed against how many team ids
your own installation store holds.

Read only throughout. Nothing here uploads, deletes, shares, opens a socket or
sends a byte to a Request URL: files.list, files.info, conversations.history,
auth.test, team.info and apps.manifest.export are reads, and every repair is
printed for a human to run.
"""

CITE_FILES_LIST = ("files.list method reference - Slack Docs",
                   "https://docs.slack.dev/reference/methods/files.list")
CITE_FILES_INFO = ("files.info method reference - Slack Docs",
                   "https://docs.slack.dev/reference/methods/files.info")
CITE_GET_UPLOAD_URL = ("files.getUploadURLExternal method reference - Slack Docs",
                       "https://docs.slack.dev/reference/methods/"
                       "files.getUploadURLExternal")
CITE_WORKING_FILES = ("Working with files - Slack Docs",
                      "https://docs.slack.dev/messaging/working-with-files")
CITE_UPLOAD_CHANGELOG = ("A better way to upload files is here to stay - Slack changelog",
                         "https://docs.slack.dev/changelog/"
                         "2024-04-a-better-way-to-upload-files-is-here-to-stay/")
CITE_SDK_LARGE = ("python-slack-sdk #1681: large file uploads fail",
                  "https://github.com/slackapi/python-slack-sdk/issues/1681")
CITE_CONV_HISTORY = ("conversations.history method reference - Slack Docs",
                     "https://docs.slack.dev/reference/methods/conversations.history")
CITE_RETRIEVING = ("Retrieving messages - Slack Docs",
                   "https://docs.slack.dev/messaging/retrieving-messages")
CITE_SOCKET_MODE = ("Using Socket Mode - Slack Docs",
                    "https://docs.slack.dev/apis/events-api/using-socket-mode")
CITE_EVENTS_API = ("Events API - Slack Docs", "https://docs.slack.dev/apis/events-api/")
CITE_MANIFEST_EXPORT = ("apps.manifest.export method reference - Slack Docs",
                        "https://docs.slack.dev/reference/methods/apps.manifest.export")
CITE_MANIFEST_REF = ("App manifest reference - Slack Docs",
                     "https://docs.slack.dev/reference/app-manifest")
CITE_OAUTH_INSTALL = ("Installing with OAuth - Slack Docs",
                      "https://docs.slack.dev/authentication/installing-with-oauth")
CITE_RATE_CHANGELOG = ("Rate limit changes for non-Marketplace apps - Slack changelog",
                       "https://docs.slack.dev/changelog/2025/05/29/"
                       "rate-limit-changes-for-non-marketplace-apps/")
CITE_SO_BOTH_ON = ("Stack Overflow: Socket Mode app also has a Request URL configured",
                   "https://stackoverflow.com/questions/57065187")

GUIDES = []

GUIDES.append({
"slug": "file-size-limit",
"title": "The 1 GB file ceiling, and how much headroom is left",
"description": "Slack caps one file at 1 GB and the byte transfer gives up long before that. Read the size distribution of what your app uploads, not the last failure.",
"h1": "The 1 GB file ceiling, and how much headroom is left",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack file_too_large upload",
             "slack file size limit 1gb",
             "slack getUploadURLExternal large file timeout",
             "slack upload fails over 20mb",
             "slack workspace file storage quota"],
"deps": "Python 3.9+ with requests, or Node.js 18+; a bot token with files:read",
"lead": "The nightly export used to be four megabytes. It is sixty now, because the company grew, and three mornings a week it does not arrive. The log is no help: sometimes <code>file_too_large</code>, sometimes <code>internal_error</code>, most often a read timeout from a host that is not <code>slack.com</code> at all and that nobody on the team has ever heard of.</p><p>Nothing changed in the code. The file crossed a line that is not in the code, and the line it crossed is not the 1&nbsp;GB one in the documentation.",
"short_answer": """<p>Slack caps a single file at <strong>1 GB</strong>. That is the documented ceiling and it is almost never the one you hit. The modern upload sends your bytes to an <code>upload_url</code> on a storage host that is not a Slack API host, with a plain HTTP request that inherits none of your Slack client's timeout, retry or proxy settings, and that request is what fails first. Reports of the SDK helpers failing start well under a hundred megabytes on ordinary connections, which is thirty times below the cap.</p>
<p>So read the distribution rather than the last failure. <code>files.list?count=200&amp;types=all&amp;user=&lt;your bot's user id&gt;</code> returns <code>size</code> in bytes for every file, and the two numbers worth reporting are <strong>the biggest file as a percentage of the ceiling</strong> and <strong>how many files sit in the band where the transfer times out</strong>. A size finding is predictive: the upload that breaks next quarter is already in the list today, one growth curve away from the edge.</p>
<p>There is a second ceiling wearing the same error string. Workspaces have an aggregate storage quota, and when it is full, uploads fail with <code>file_too_large</code> regardless of the file. <code>file_too_large</code> on a four-megabyte CSV is not about that CSV, and no amount of compressing it will help.</p>""",
"problem": """<p>What makes this one drag on is that it is intermittent by construction. The code is the same code, the token is the same token, the channel is the same channel, and the only thing moving is the data. So the failure arrives as <em>sometimes</em>, which is the word that sends a team looking at the network, at Slack's status page, at the scheduler, at everything except the one variable that is quietly increasing every week.</p>
<p>The error strings actively mislead. A file over the per-file cap comes back <code>file_too_large</code>, which is honest. A workspace that has filled its storage quota comes back <code>file_too_large</code> on a small file, which is not. A transfer that ran long comes back as a socket timeout from a storage hostname, with no Slack error at all, because that step is not a Slack API call and there is no <code>ok: false</code> anywhere in it. And a genuinely large upload sometimes comes back <code>internal_error</code>, which reads like Slack having a bad day and is usually the size in a different costume. Four symptoms, three subsystems, one growth curve.</p>
<p>Then the retry makes it worse in a way that is specific to size. Retrying a failed <code>chat.postMessage</code> costs a few hundred bytes. Retrying a failed 600 MB upload sends 600 MB again, three times, and the job that was late is now saturating the link it was already timing out on. An exponential backoff written for API calls is the wrong policy for a byte transfer, and applying it to one turns a slow morning into an outage.</p>
<p>The honest conclusion is usually that the file does not belong in Slack. Slack is a chat product with a file store attached to it, not an object store with a chat interface, and a nightly multi-hundred-megabyte artifact wants S3 or GCS and a message containing a link. That is not a workaround, it is the shape the system wanted from the beginning. One thing this note is deliberately not about: a file that arrives with <code>size: 0</code> is not a size problem at all, it is the three-step upload sequence stopping in the middle, and that has <a href="/slack/incomplete-external-upload/">its own note</a>.</p>""",
"why": """<p><strong>The documented ceiling is not the operative one.</strong> 1 GB is where Slack refuses. The band where the plain HTTP transfer starts to lose is far below it and is a property of your link, your client's default timeout and the storage host's patience, not of Slack. The script therefore carries two edges and both of them are arguments, because the useful one is the one you measured on your own network.</p>
<p><strong>A size finding is a distribution, not an event.</strong> One failed upload tells you almost nothing. The list of every file the app owns, sorted into bands, tells you whether you are near an edge, how near, and how fast you are approaching it. That is why the report leads with the biggest file as a fraction of the cap rather than with a list of failures.</p>
<p><strong><code>file_too_large</code> has two meanings and only one of them is about the file.</strong> Over the per-file cap it is literal. Well under it, the workspace's aggregate storage quota is full and the error is about the workspace. The repairs have nothing in common: split the file, or go and delete years of old files and ask about the plan.</p>
<p><strong>The byte step is not a Slack API call and does not behave like one.</strong> No <code>ok: false</code>, no <code>Retry-After</code>, no rate-limit headers, no Slack SDK retry policy, no Slack SDK timeout. It is a request to a storage URL with whatever defaults your HTTP library ships with, which for several popular ones is no timeout at all in one direction and thirty seconds in the other.</p>
<p><strong>A transfer timeout is arithmetic before it is a mystery.</strong> Bytes times eight, divided by the link speed, is the number of seconds the upload needs. If that is larger than the timeout you configured, the upload cannot succeed on a perfectly healthy network, and no retry policy fixes a budget that never balanced.</p>
<p><strong>Zero bytes is a different failure and gets handed off rather than counted.</strong> A registered file of length zero means the completion call worked and the transfer did not. It is a broken sequence, not a large file, and folding it into a size report would put a stalled upload and a growing export in the same bucket when they want opposite repairs.</p>""",
"steps": [
 {"h": "Page files.list, scoped to the identity that uploads",
  "body": """<p><code>files.list?count=200&amp;types=all&amp;user=&lt;U...&gt;</code>, following <code>paging.pages</code>. The <code>user</code> filter turns a workspace inventory into an audit of your own output, and the id is the <code>user_id</code> that <code>auth.test</code> returns. Everything after this is arithmetic on the <code>size</code> field.</p>"""},
 {"h": "Put the band edges where your evidence is, not where the docs are",
  "body": """<p><code>band</code> takes the ceiling, the transfer band and the headroom fraction as arguments, defaulting to 1 GB, 25 MB and three quarters. The default transfer band is a starting point drawn from what people report; the number that belongs there is the size at which <em>your</em> uploads started getting slow, and you already have that number.</p>"""},
 {"h": "Read the biggest file as a fraction of the cap",
  "body": """<p><code>size_profile</code> returns the counts per band, the biggest file, and what percentage of the ceiling that biggest file is. A workspace at 3% has no size problem and should stop reading. A workspace at 78% has one scheduled for whenever the data grows by a third.</p>"""},
 {"h": "Do the transfer arithmetic before blaming the network",
  "body": """<p><code>timeout_budget</code> takes a size, a link speed in megabits and the timeout your client is configured with, and returns the seconds the transfer needs. <code>impossible</code> means the upload cannot finish on a healthy link, which is a configuration bug rather than an infrastructure one and is fixed by a larger number in your own code.</p>"""},
 {"h": "Sort a recorded failure into which ceiling it actually hit",
  "body": """<p><code>refusal_cause</code> takes the error string and the size from your own logs and names the limit: the per-file cap, the workspace storage quota, the transfer, or something that is not about size at all. Four causes, four repairs, and only one of them involves making the file smaller.</p>"""},
 {"h": "Move the big ones out of Slack and post a link instead",
  "body": """<p>The repair the script prints for the top band is an architectural one: upload to object storage, post a message with the link, and let Slack carry the notification rather than the payload. Every repair here is printed rather than performed, because uploading, deleting and revoking are all writes.</p>"""},
],
"verify": """<p>Re-run after the export moves. The number to watch is the percentage of the ceiling, and it should stop climbing.</p>
<pre><code class="language-bash">python3 slack_file_sizes.py --link-mbps 40 --client-timeout 30
# identity   U07BOT9QD (reports-bot) in Northwind
# scope      files:read granted
# files      312 file(s) owned by U07BOT9QD, over 2 page(s)
# band       transfer-band  F08K2M4QX warehouse-dump.csv  61.4 MB, above the band where
#                           the plain byte transfer starts to time out
# band       no-headroom    F08K5N1QT archive-2026.zip  812.0 MB, 79.3% of the 1 GB
#                           per-file ceiling. The next growth crosses it
# profile    biggest 812.0 MB (79.3% of the ceiling); 14 file(s) in the transfer band
# budget     impossible     812.0 MB needs 170.2s at 40 Mbps and the client gives up
#                           after 30s, so this upload cannot finish on a healthy link
# cause      workspace-quota  the recorded file_too_large was on a 4.0 MB file, which is
#                           far under the cap: the workspace storage quota is the limit
# verdict    15 of 312 file(s) are at or near a limit
#   repair: raise the byte-step timeout; it is a plain HTTP request, not a Slack call
#   repair: put the big artifacts in object storage and post a link into the channel</code></pre>""",
"code_intro": "One paginated GET and four pure functions, none of which needs a network. <code>band</code> sorts a file by size against edges you supply rather than against the documented cap, because the documented cap is not the one that breaks you. <code>size_profile</code> turns the list into the two numbers that are the actual finding. <code>timeout_budget</code> is the arithmetic that decides whether a timeout was ever survivable. <code>refusal_cause</code> exists because <code>file_too_large</code> means two different things and the repairs have nothing in common.",
"py_file": "slack_file_sizes.py",
"py": '''"""Measure how close your uploads are to the ceiling that will stop them.

Read only. files.list, auth.test and team.info are reads. Nothing here mints an
upload URL, sends a byte anywhere, deletes a file or fetches a url_private: a
bot token with files:read is enough, and every repair is printed.

Slack caps one file at 1 GB. That number is almost never the one you meet. The
byte transfer in the middle of the modern upload goes to a storage host that is
not a Slack API host, over a plain HTTP request that inherits none of your
Slack client's timeout or retry configuration, and it is the step that gives up
first. So the question is not "which upload failed" but "how much room is
left", and that is a distribution rather than an error.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_file_sizes")

API = "https://slack.com/api/"

# The documented per-file ceiling: one gibibyte. Everything below it is a
# property of your link and your HTTP client rather than of Slack, which is why
# the other two edges are arguments with soft defaults.
CEILING = 1024 ** 3
# Where the plain byte transfer starts being the problem instead of the size.
# Drawn from what people report rather than from any published number; replace
# it with the size at which your own uploads got slow.
TRANSFER_BAND = 25 * 1024 * 1024
# What counts as no room left. A file this close to the cap crosses it on the
# day the data grows, which is a date rather than a possibility.
NEAR = 0.75

# The bands that are worth waking somebody for. Kept as a constant so the rows
# printed and the number in the verdict cannot drift apart.
FINDINGS = ("over-ceiling", "no-headroom", "transfer-band")


def human(size):
    """Bytes as something a person can read. Pure."""
    try:
        n = float(size)
    except (TypeError, ValueError):
        return "?"
    for unit in ("B", "KB", "MB", "GB"):
        if abs(n) < 1024 or unit == "GB":
            return "%.1f %s" % (n, unit)
        n /= 1024.0
    return "%.1f GB" % n


def band(f, ceiling=CEILING, transfer=TRANSFER_BAND, near=NEAR):
    """Which size band is one file in? Pure. Returns (band, size, detail).

    The bands are deliberately not "ok" and "too big". A file at 79% of the
    ceiling is not a failure today and is a scheduled one, and a file in the
    transfer band fails on a slow morning and succeeds on a fast one. Those are
    the two states this note exists to name.

    empty is classified and then handed off: a registered file of length zero
    is the upload sequence stopping in the middle, not a size, and counting it
    here would put a stalled transfer and a growing export in one bucket.
    """
    row = f or {}
    if row.get("is_external"):
        return ("external", 0, "hosted outside Slack, so the bytes and their limits "
                               "belong to another system")
    raw = row.get("size")
    if raw is None:
        return ("unknown", 0, "no size field, so this file cannot be measured")
    try:
        size = int(raw)
    except (TypeError, ValueError):
        return ("unknown", 0, "size is not a number, so this file cannot be measured")
    if size <= 0:
        return ("empty", size, "registered with zero bytes. That is the transfer step "
                               "failing rather than a size limit, and it is a "
                               "different note")
    if size > ceiling:
        return ("over-ceiling", size, "%s, past the %s per-file ceiling. Slack refuses "
                                      "this outright" % (human(size), human(ceiling)))
    if size >= ceiling * near:
        return ("no-headroom", size, "%s, %.1f%% of the %s per-file ceiling. The next "
                                     "growth crosses it"
                                     % (human(size), 100.0 * size / ceiling,
                                        human(ceiling)))
    if size >= transfer:
        return ("transfer-band", size, "%s, above the band where the plain byte "
                                       "transfer starts to time out" % human(size))
    return ("fine", size, "%s, comfortably inside every limit" % human(size))


def size_profile(files, ceiling=CEILING, transfer=TRANSFER_BAND, near=NEAR):
    """The distribution, because one file's size is not a finding. Pure.

    Returns (counts, biggest, percent) where counts maps band name to a count,
    biggest is (file_id, name, size) or None, and percent is the biggest file
    as a percentage of the ceiling. That last number is the whole report: it
    says how much of the runway is left, which a list of failures does not.
    """
    counts, biggest = {}, None
    for f in files or []:
        name, size, _detail = band(f, ceiling, transfer, near)
        counts[name] = counts.get(name, 0) + 1
        if name in ("external", "unknown"):
            continue
        if biggest is None or size > biggest[2]:
            biggest = ((f or {}).get("id") or "?",
                       (f or {}).get("name") or (f or {}).get("title") or "?", size)
    percent = 0.0 if not biggest or not ceiling else round(
        100.0 * biggest[2] / ceiling, 1)
    return (counts, biggest, percent)


def timeout_budget(size, mbps, timeout_s):
    """How long does the byte step need, against the timeout you gave it? Pure.

    Returns (seconds, verdict, detail). impossible is the interesting verdict:
    it means the transfer could not have finished on a completely healthy link,
    so the failure is a number in your own configuration rather than anything
    about Slack, the network or the file.
    """
    try:
        n = float(size)
        rate = float(mbps)
        budget = float(timeout_s)
    except (TypeError, ValueError):
        return (0.0, "unknown", "a size, a link speed and a timeout are all needed")
    if n <= 0 or rate <= 0 or budget <= 0:
        return (0.0, "unknown", "a size, a link speed and a timeout are all needed")
    seconds = round(n * 8.0 / (rate * 1000000.0), 1)
    if seconds > budget:
        return (seconds, "impossible", "%s needs %.1fs at %g Mbps and the client gives "
                                       "up after %gs, so this upload cannot finish on "
                                       "a healthy link" % (human(n), seconds, rate,
                                                           budget))
    if seconds > budget / 2.0:
        return (seconds, "tight", "%s needs %.1fs at %g Mbps against a %gs timeout. A "
                                  "slow morning is enough to lose it"
                                  % (human(n), seconds, rate, budget))
    return (seconds, "comfortable", "%s needs %.1fs at %g Mbps against a %gs timeout"
                                    % (human(n), seconds, rate, budget))


def refusal_cause(error, size, ceiling=CEILING, transfer=TRANSFER_BAND):
    """Which limit did a failure you already recorded actually hit? Pure.

    Returns (cause, detail). file_too_large is the reason this function exists:
    over the cap it is about the file, and well under it, it is about the
    workspace's aggregate storage quota. Same string, unrelated repairs.
    """
    err = str(error or "").strip().lower()
    try:
        n = int(size)
    except (TypeError, ValueError):
        n = 0
    if err in ("file_too_large", "too_large", "request_entity_too_large"):
        if n and n > ceiling:
            return ("ceiling", "%s is past the %s per-file cap. Split it, compress it, "
                               "or put it somewhere that is not Slack"
                               % (human(n), human(ceiling)))
        if n:
            return ("workspace-quota", "%s is far under the %s cap, so the refusal is "
                                       "about the workspace's aggregate storage rather "
                                       "than this file" % (human(n), human(ceiling)))
        return ("ceiling-or-quota", "file_too_large with no size recorded. Record the "
                                    "byte count and this becomes decidable")
    if err in ("", "none", "timeout", "timed_out", "read_timeout", "connection_error"):
        if n >= transfer:
            return ("transfer", "no Slack error at all: the byte step is a plain HTTP "
                                "request to a storage host and it ran out of time. "
                                "Raise that client's timeout, not the retry count")
        return ("not-a-size-problem", "a transport failure on a small file, which is "
                                      "the network rather than any Slack limit")
    if err == "internal_error" and n >= transfer:
        return ("large-internal-error", "internal_error on %s. On a large upload this "
                                        "is usually the size wearing a different "
                                        "costume; treat it as the transfer" % human(n))
    if err in ("invalid_arguments", "invalid_length"):
        return ("declared-length", "the declared length and the bytes disagreed. That "
                                   "is the upload sequence rather than a size limit")
    return ("not-a-size-problem", "%s is not one of the size errors; read it on its "
                                  "own terms" % (err or "an empty error string"))


def page_files(session, user, page_size, max_pages):
    """Page files.list. A read, and the only paginated call here."""
    out, page, pages = [], 1, 1
    while page <= min(pages, max_pages):
        params = {"count": str(page_size), "types": "all", "page": str(page)}
        if user:
            params["user"] = user
        body = session.get(API + "files.list", params=params, timeout=30).json()
        if body.get("ok") is not True:
            log.error("files.list unavailable    %s", body.get("error"))
            return out, pages
        out.extend(body.get("files") or [])
        pages = int((body.get("paging") or {}).get("pages") or 1)
        page += 1
    return out, pages


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN",
                    help="environment variable holding the bot token")
    ap.add_argument("--user", default="", help="owner to audit; defaults to this token")
    ap.add_argument("--all-users", action="store_true",
                    help="measure every file in the workspace, not just the app's")
    ap.add_argument("--transfer-mb", type=float, default=TRANSFER_BAND / 1048576.0,
                    help="size above which your own transfers get slow")
    ap.add_argument("--near", type=float, default=NEAR,
                    help="fraction of the ceiling that counts as no headroom")
    ap.add_argument("--link-mbps", type=float, default=0.0,
                    help="uplink speed, for the transfer arithmetic")
    ap.add_argument("--client-timeout", type=float, default=0.0,
                    help="the timeout your HTTP client uses for the byte step")
    ap.add_argument("--failed-error", default="",
                    help="an error string your logs recorded for a failed upload")
    ap.add_argument("--failed-size", type=int, default=0,
                    help="the byte count of that failed upload")
    ap.add_argument("--page-size", type=int, default=200)
    ap.add_argument("--max-pages", type=int, default=25)
    args = ap.parse_args()

    token = os.environ.get(args.token_env)
    if not token:
        log.error("set %s to a bot token with files:read", args.token_env)
        return 2
    transfer = int(args.transfer_mb * 1048576)

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + token})
    who_resp = s.get(API + "auth.test", timeout=30)
    who = who_resp.json()
    if who.get("ok") is not True:
        log.error("auth.test  unavailable    %s", who.get("error"))
        return 2
    log.info("identity   %s (%s) in %s", who.get("user_id"), who.get("user"),
             who.get("team"))
    scopes = who_resp.headers.get("x-oauth-scopes") or ""
    if scopes and "files:read" not in scopes.split(","):
        log.warning("scope      files:read is not granted; files.list will refuse")

    owner = "" if args.all_users else (args.user or who.get("user_id") or "")
    files, pages = page_files(s, owner, args.page_size, args.max_pages)
    log.info("files      %d file(s) owned by %s, over %d page(s)",
             len(files), owner or "anyone", pages)

    flagged = 0
    for f in files:
        name, _size, detail = band(f, CEILING, transfer, args.near)
        if name not in FINDINGS:
            continue
        flagged += 1
        log.warning("band       %-14s %s %s  %s", name, f.get("id") or "?",
                    f.get("name") or "?", detail)

    counts, biggest, percent = size_profile(files, CEILING, transfer, args.near)
    if biggest:
        log.info("profile    biggest %s (%.1f%% of the ceiling); %d file(s) in the "
                 "transfer band", human(biggest[2]), percent,
                 counts.get("transfer-band", 0))
    if counts.get("empty"):
        log.info("handoff    %d file(s) registered with zero bytes: a stalled upload "
                 "sequence rather than a size limit", counts["empty"])

    if biggest and args.link_mbps and args.client_timeout:
        _sec, verdict, detail = timeout_budget(biggest[2], args.link_mbps,
                                               args.client_timeout)
        (log.warning if verdict == "impossible" else log.info)(
            "budget     %-14s %s", verdict, detail)

    if args.failed_error or args.failed_size:
        cause, detail = refusal_cause(args.failed_error, args.failed_size, CEILING,
                                      transfer)
        log.warning("cause      %-14s %s", cause, detail)

    if not flagged:
        log.info("verdict    clear          nothing this app owns is near a limit")
        return 0
    log.warning("verdict    %d of %d file(s) are at or near a limit", flagged,
                len(files))
    log.warning("  repair: raise the timeout on the byte step; it is a plain HTTP "
                "request to a storage host and does not use your Slack client's")
    log.warning("  repair: put the large artifacts in object storage and post a link "
                "into the channel, so Slack carries the notification not the payload")
    log.warning("  repair: if the error was file_too_large on a small file, the "
                "workspace storage quota is full and no code change will help")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-file-sizes.mjs",
"js": '''/**
 * Measure how close your uploads are to the ceiling that will stop them.
 *
 * Read only. files.list, auth.test and team.info are reads. Nothing here mints
 * an upload URL, sends a byte anywhere, deletes a file or fetches a
 * url_private: a bot token with files:read is enough.
 *
 * Slack caps one file at 1 GB and that is almost never the number you meet.
 * The byte transfer goes to a storage host that is not a Slack API host, over a
 * plain HTTP request that inherits none of your Slack client's configuration,
 * and it is the step that gives up first.
 */

const API = 'https://slack.com/api/';

/** The documented per-file ceiling: one gibibyte. */
export const CEILING = 1024 ** 3;
/** Where the plain byte transfer starts being the problem instead of the size. */
export const TRANSFER_BAND = 25 * 1024 * 1024;
/** What counts as no room left: a file this close crosses the cap on growth. */
export const NEAR = 0.75;
/** The bands worth waking somebody for. */
export const FINDINGS = ['over-ceiling', 'no-headroom', 'transfer-band'];

/** Bytes as something a person can read. Pure. */
export function human(size) {
  let n = Number(size);
  if (!Number.isFinite(n)) return '?';
  for (const unit of ['B', 'KB', 'MB', 'GB']) {
    if (Math.abs(n) < 1024 || unit === 'GB') return `${n.toFixed(1)} ${unit}`;
    n /= 1024;
  }
  return `${n.toFixed(1)} GB`;
}

/**
 * Which size band is one file in? Pure. Returns [band, size, detail].
 *
 * The bands are not "ok" and "too big". A file at 79% of the ceiling is a
 * scheduled failure, and a file in the transfer band fails on a slow morning.
 * A zero-byte file is classified and handed off: that is a stalled upload
 * sequence rather than a size, and it wants the opposite repair.
 */
export function band(f, ceiling = CEILING, transfer = TRANSFER_BAND, near = NEAR) {
  const row = f ?? {};
  if (row.is_external) {
    return ['external', 0, 'hosted outside Slack, so the bytes and their limits belong '
      + 'to another system'];
  }
  if (row.size === undefined || row.size === null) {
    return ['unknown', 0, 'no size field, so this file cannot be measured'];
  }
  const size = Number.parseInt(row.size, 10);
  if (!Number.isFinite(size)) {
    return ['unknown', 0, 'size is not a number, so this file cannot be measured'];
  }
  if (size <= 0) {
    return ['empty', size, 'registered with zero bytes. That is the transfer step '
      + 'failing rather than a size limit, and it is a different note'];
  }
  if (size > ceiling) {
    return ['over-ceiling', size, `${human(size)}, past the ${human(ceiling)} per-file `
      + 'ceiling. Slack refuses this outright'];
  }
  if (size >= ceiling * near) {
    const pct = ((100 * size) / ceiling).toFixed(1);
    return ['no-headroom', size, `${human(size)}, ${pct}% of the ${human(ceiling)} `
      + 'per-file ceiling. The next growth crosses it'];
  }
  if (size >= transfer) {
    return ['transfer-band', size, `${human(size)}, above the band where the plain byte `
      + 'transfer starts to time out'];
  }
  return ['fine', size, `${human(size)}, comfortably inside every limit`];
}

/**
 * The distribution, because one file's size is not a finding. Pure.
 * Returns [counts, biggest, percent]; percent is the runway that is left.
 */
export function sizeProfile(files, ceiling = CEILING, transfer = TRANSFER_BAND,
  near = NEAR) {
  const counts = {};
  let biggest = null;
  for (const f of files ?? []) {
    const [name, size] = band(f, ceiling, transfer, near);
    counts[name] = (counts[name] ?? 0) + 1;
    if (name === 'external' || name === 'unknown') continue;
    if (biggest === null || size > biggest[2]) {
      biggest = [(f ?? {}).id ?? '?', (f ?? {}).name ?? (f ?? {}).title ?? '?', size];
    }
  }
  const percent = !biggest || !ceiling
    ? 0 : Math.round((1000 * biggest[2]) / ceiling) / 10;
  return [counts, biggest, percent];
}

/**
 * How long does the byte step need, against the timeout you gave it? Pure.
 * Returns [seconds, verdict, detail]; impossible means the budget never
 * balanced, which is a number in your own configuration rather than a network.
 */
export function timeoutBudget(size, mbps, timeoutS) {
  const n = Number(size);
  const rate = Number(mbps);
  const budget = Number(timeoutS);
  if (![n, rate, budget].every(Number.isFinite) || n <= 0 || rate <= 0 || budget <= 0) {
    return [0, 'unknown', 'a size, a link speed and a timeout are all needed'];
  }
  const seconds = Math.round((n * 8 * 10) / (rate * 1000000)) / 10;
  if (seconds > budget) {
    return [seconds, 'impossible', `${human(n)} needs ${seconds.toFixed(1)}s at `
      + `${rate} Mbps and the client gives up after ${budget}s, so this upload cannot `
      + 'finish on a healthy link'];
  }
  if (seconds > budget / 2) {
    return [seconds, 'tight', `${human(n)} needs ${seconds.toFixed(1)}s at ${rate} Mbps `
      + `against a ${budget}s timeout. A slow morning is enough to lose it`];
  }
  return [seconds, 'comfortable', `${human(n)} needs ${seconds.toFixed(1)}s at `
    + `${rate} Mbps against a ${budget}s timeout`];
}

/**
 * Which limit did a failure you already recorded actually hit? Pure.
 * file_too_large is the reason this exists: over the cap it is about the file,
 * well under it, it is about the workspace's aggregate storage quota.
 */
export function refusalCause(error, size, ceiling = CEILING,
  transfer = TRANSFER_BAND) {
  const err = String(error ?? '').trim().toLowerCase();
  const n = Number.parseInt(size, 10) || 0;
  if (['file_too_large', 'too_large', 'request_entity_too_large'].includes(err)) {
    if (n && n > ceiling) {
      return ['ceiling', `${human(n)} is past the ${human(ceiling)} per-file cap. Split `
        + 'it, compress it, or put it somewhere that is not Slack'];
    }
    if (n) {
      return ['workspace-quota', `${human(n)} is far under the ${human(ceiling)} cap, `
        + 'so the refusal is about the workspace aggregate storage rather than this '
        + 'file'];
    }
    return ['ceiling-or-quota', 'file_too_large with no size recorded. Record the byte '
      + 'count and this becomes decidable'];
  }
  if (['', 'none', 'timeout', 'timed_out', 'read_timeout', 'connection_error']
    .includes(err)) {
    if (n >= transfer) {
      return ['transfer', 'no Slack error at all: the byte step is a plain HTTP request '
        + 'to a storage host and it ran out of time. Raise that client timeout, not '
        + 'the retry count'];
    }
    return ['not-a-size-problem', 'a transport failure on a small file, which is the '
      + 'network rather than any Slack limit'];
  }
  if (err === 'internal_error' && n >= transfer) {
    return ['large-internal-error', `internal_error on ${human(n)}. On a large upload `
      + 'this is usually the size wearing a different costume; treat it as the '
      + 'transfer'];
  }
  if (['invalid_arguments', 'invalid_length'].includes(err)) {
    return ['declared-length', 'the declared length and the bytes disagreed. That is '
      + 'the upload sequence rather than a size limit'];
  }
  return ['not-a-size-problem', `${err || 'an empty error string'} is not one of the `
    + 'size errors; read it on its own terms'];
}

function arg(args, name, fallback = null) {
  const i = args.indexOf(name);
  return i === -1 ? fallback : args[i + 1];
}

async function pageFiles(headers, user, pageSize, maxPages) {
  const files = [];
  let page = 1;
  let pages = 1;
  while (page <= Math.min(pages, maxPages)) {
    const params = new URLSearchParams({
      count: String(pageSize), types: 'all', page: String(page),
    });
    if (user) params.set('user', user);
    const body = await (await fetch(`${API}files.list?${params}`, { headers })).json();
    if (body.ok !== true) {
      console.error(`files.list unavailable    ${body.error}`);
      return [files, pages];
    }
    files.push(...(body.files ?? []));
    pages = Number((body.paging ?? {}).pages ?? 1) || 1;
    page += 1;
  }
  return [files, pages];
}

async function main() {
  const args = process.argv.slice(2);
  const tokenEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
  const token = process.env[tokenEnv];
  if (!token) {
    console.error(`set ${tokenEnv} to a bot token with files:read`);
    process.exitCode = 2;
    return;
  }
  const transfer = Math.round(Number(arg(args, '--transfer-mb',
    TRANSFER_BAND / 1048576)) * 1048576);
  const near = Number(arg(args, '--near', NEAR));
  const mbps = Number(arg(args, '--link-mbps', 0));
  const clientTimeout = Number(arg(args, '--client-timeout', 0));

  const headers = { Authorization: `Bearer ${token}` };
  const whoResp = await fetch(`${API}auth.test`, { headers });
  const who = await whoResp.json();
  if (who.ok !== true) {
    console.error(`auth.test  unavailable    ${who.error}`);
    process.exitCode = 2;
    return;
  }
  console.log(`identity   ${who.user_id} (${who.user}) in ${who.team}`);
  const scopes = whoResp.headers.get('x-oauth-scopes') ?? '';
  if (scopes && !scopes.split(',').includes('files:read')) {
    console.warn('scope      files:read is not granted; files.list will refuse');
  }

  const owner = args.includes('--all-users') ? '' : (arg(args, '--user', '')
    || who.user_id || '');
  const [files, pages] = await pageFiles(headers, owner,
    Number(arg(args, '--page-size', 200)), Number(arg(args, '--max-pages', 25)));
  console.log(`files      ${files.length} file(s) owned by ${owner || 'anyone'}, over `
    + `${pages} page(s)`);

  let flagged = 0;
  for (const f of files) {
    const [name, , detail] = band(f, CEILING, transfer, near);
    if (!FINDINGS.includes(name)) continue;
    flagged += 1;
    console.warn(`band       ${name.padEnd(14)} ${f.id ?? '?'} ${f.name ?? '?'}  `
      + `${detail}`);
  }

  const [counts, biggest, percent] = sizeProfile(files, CEILING, transfer, near);
  if (biggest) {
    console.log(`profile    biggest ${human(biggest[2])} (${percent}% of the ceiling); `
      + `${counts['transfer-band'] ?? 0} file(s) in the transfer band`);
  }
  if (counts.empty) {
    console.log(`handoff    ${counts.empty} file(s) registered with zero bytes: a `
      + 'stalled upload sequence rather than a size limit');
  }
  if (biggest && mbps && clientTimeout) {
    const [, verdict, detail] = timeoutBudget(biggest[2], mbps, clientTimeout);
    const line = `budget     ${verdict.padEnd(14)} ${detail}`;
    if (verdict === 'impossible') console.warn(line); else console.log(line);
  }
  const failedError = arg(args, '--failed-error', '');
  const failedSize = Number(arg(args, '--failed-size', 0));
  if (failedError || failedSize) {
    const [cause, detail] = refusalCause(failedError, failedSize, CEILING, transfer);
    console.warn(`cause      ${cause.padEnd(14)} ${detail}`);
  }

  if (!flagged) {
    console.log('verdict    clear          nothing this app owns is near a limit');
    return;
  }
  console.warn(`verdict    ${flagged} of ${files.length} file(s) are at or near a limit`);
  console.warn('  repair: raise the timeout on the byte step; it is a plain HTTP '
    + 'request to a storage host and does not use your Slack client configuration');
  console.warn('  repair: put the large artifacts in object storage and post a link '
    + 'into the channel, so Slack carries the notification and not the payload');
  process.exitCode = 1;
}

// Only run when invoked directly, so importing this module in the tests does
// not execute main() and fail the file on a missing token.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The assertions worth reading are the boundaries. A zero-byte file has to come back as <code>empty</code> rather than as the smallest file in the report, because it is a stalled sequence and belongs to another note. <code>file_too_large</code> is tested twice, once over the cap and once far under it, since the same string means the file and then the workspace. And <code>timeout_budget</code> is tested for the case where the arithmetic never balanced, which is the finding that saves the most time: no retry policy rescues a transfer that needs longer than the timeout allows.",
"test_py_file": "test_slack_file_sizes.py",
"test_py": '''from slack_file_sizes import band, refusal_cause, size_profile, timeout_budget

MB = 1024 * 1024
GB = 1024 * MB


def test_a_small_file_is_inside_every_limit():
    name, size, _detail = band({"id": "F1", "size": 4 * MB})
    assert name == "fine"
    assert size == 4 * MB


def test_a_file_in_the_transfer_band_is_flagged_below_the_cap():
    name, _size, detail = band({"id": "F1", "size": 61 * MB})
    assert name == "transfer-band"
    assert "time out" in detail


def test_the_band_edge_is_an_argument_not_a_constant():
    assert band({"size": 61 * MB}, transfer=200 * MB)[0] == "fine"


def test_three_quarters_of_the_ceiling_is_a_scheduled_failure():
    name, _size, detail = band({"id": "F1", "size": 812 * MB})
    assert name == "no-headroom"
    assert "79.3%" in detail


def test_past_the_ceiling_is_refused_outright():
    assert band({"size": GB + 1})[0] == "over-ceiling"


def test_zero_bytes_is_handed_off_rather_than_called_small():
    name, _size, detail = band({"id": "F1", "size": 0})
    assert name == "empty"
    assert "different note" in detail


def test_an_external_file_is_not_measured_against_slack_limits():
    assert band({"is_external": True, "size": 9 * GB})[0] == "external"


def test_a_file_with_no_size_field_is_unknown_rather_than_zero():
    assert band({"id": "F1"})[0] == "unknown"
    assert band({"id": "F1", "size": "big"})[0] == "unknown"


def test_the_profile_reports_the_biggest_as_a_fraction_of_the_ceiling():
    counts, biggest, percent = size_profile([
        {"id": "F1", "name": "a.csv", "size": 4 * MB},
        {"id": "F2", "name": "b.zip", "size": 812 * MB},
    ])
    assert counts == {"fine": 1, "no-headroom": 1}
    assert biggest == ("F2", "b.zip", 812 * MB)
    assert percent == 79.3


def test_external_and_unmeasurable_files_cannot_become_the_biggest():
    _counts, biggest, _percent = size_profile([
        {"id": "F1", "size": 4 * MB},
        {"id": "F2", "is_external": True, "size": 9 * GB},
    ])
    assert biggest[0] == "F1"


def test_an_empty_run_reports_no_biggest_rather_than_dividing():
    assert size_profile([]) == ({}, None, 0.0)


def test_a_transfer_that_needs_longer_than_the_timeout_is_impossible():
    seconds, verdict, detail = timeout_budget(812 * MB, 40, 30)
    assert verdict == "impossible"
    assert seconds == 170.3
    assert "healthy link" in detail


def test_a_transfer_using_most_of_the_budget_is_tight():
    assert timeout_budget(60 * MB, 40, 20)[1] == "tight"


def test_a_small_transfer_is_comfortable():
    assert timeout_budget(4 * MB, 40, 30)[1] == "comfortable"


def test_the_budget_needs_all_three_numbers():
    assert timeout_budget(4 * MB, 0, 30)[1] == "unknown"
    assert timeout_budget(None, 40, 30)[1] == "unknown"


def test_file_too_large_over_the_cap_is_about_the_file():
    cause, _detail = refusal_cause("file_too_large", GB + 1)
    assert cause == "ceiling"


def test_file_too_large_on_a_small_file_is_about_the_workspace():
    cause, detail = refusal_cause("file_too_large", 4 * MB)
    assert cause == "workspace-quota"
    assert "aggregate storage" in detail


def test_no_error_at_all_on_a_large_file_is_the_byte_transfer():
    cause, detail = refusal_cause("", 300 * MB)
    assert cause == "transfer"
    assert "timeout" in detail


def test_internal_error_on_a_large_upload_is_read_as_the_transfer():
    assert refusal_cause("internal_error", 300 * MB)[0] == "large-internal-error"


def test_a_length_complaint_belongs_to_the_upload_sequence_note():
    assert refusal_cause("invalid_arguments", 4 * MB)[0] == "declared-length"


def test_an_unrelated_error_is_not_dressed_up_as_a_size_problem():
    assert refusal_cause("not_in_channel", 4 * MB)[0] == "not-a-size-problem"
''',
"test_js_file": "slack-file-sizes.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  band, refusalCause, sizeProfile, timeoutBudget,
} from './slack-file-sizes.mjs';

const MB = 1024 * 1024;
const GB = 1024 * MB;

test('a small file is inside every limit', () => {
  const [name, size] = band({ id: 'F1', size: 4 * MB });
  assert.equal(name, 'fine');
  assert.equal(size, 4 * MB);
});

test('a file in the transfer band is flagged below the cap', () => {
  const [name, , detail] = band({ id: 'F1', size: 61 * MB });
  assert.equal(name, 'transfer-band');
  assert.match(detail, /time out/);
});

test('the band edge is an argument not a constant', () => {
  assert.equal(band({ size: 61 * MB }, GB, 200 * MB)[0], 'fine');
});

test('three quarters of the ceiling is a scheduled failure', () => {
  const [name, , detail] = band({ id: 'F1', size: 812 * MB });
  assert.equal(name, 'no-headroom');
  assert.match(detail, /79\\.3%/);
});

test('past the ceiling is refused outright', () => {
  assert.equal(band({ size: GB + 1 })[0], 'over-ceiling');
});

test('zero bytes is handed off rather than called small', () => {
  const [name, , detail] = band({ id: 'F1', size: 0 });
  assert.equal(name, 'empty');
  assert.match(detail, /different note/);
});

test('an external file is not measured against Slack limits', () => {
  assert.equal(band({ is_external: true, size: 9 * GB })[0], 'external');
});

test('a file with no size field is unknown rather than zero', () => {
  assert.equal(band({ id: 'F1' })[0], 'unknown');
  assert.equal(band({ id: 'F1', size: 'big' })[0], 'unknown');
});

test('the profile reports the biggest as a fraction of the ceiling', () => {
  const [counts, biggest, percent] = sizeProfile([
    { id: 'F1', name: 'a.csv', size: 4 * MB },
    { id: 'F2', name: 'b.zip', size: 812 * MB },
  ]);
  assert.deepEqual(counts, { fine: 1, 'no-headroom': 1 });
  assert.deepEqual(biggest, ['F2', 'b.zip', 812 * MB]);
  assert.equal(percent, 79.3);
});

test('external and unmeasurable files cannot become the biggest', () => {
  const [, biggest] = sizeProfile([
    { id: 'F1', size: 4 * MB },
    { id: 'F2', is_external: true, size: 9 * GB },
  ]);
  assert.equal(biggest[0], 'F1');
});

test('an empty run reports no biggest rather than dividing', () => {
  assert.deepEqual(sizeProfile([]), [{}, null, 0]);
});

test('a transfer that needs longer than the timeout is impossible', () => {
  const [seconds, verdict, detail] = timeoutBudget(812 * MB, 40, 30);
  assert.equal(verdict, 'impossible');
  assert.equal(seconds, 170.3);
  assert.match(detail, /healthy link/);
});

test('a transfer using most of the budget is tight', () => {
  assert.equal(timeoutBudget(60 * MB, 40, 20)[1], 'tight');
});

test('a small transfer is comfortable', () => {
  assert.equal(timeoutBudget(4 * MB, 40, 30)[1], 'comfortable');
});

test('the budget needs all three numbers', () => {
  assert.equal(timeoutBudget(4 * MB, 0, 30)[1], 'unknown');
  assert.equal(timeoutBudget(null, 40, 30)[1], 'unknown');
});

test('file_too_large over the cap is about the file', () => {
  assert.equal(refusalCause('file_too_large', GB + 1)[0], 'ceiling');
});

test('file_too_large on a small file is about the workspace', () => {
  const [cause, detail] = refusalCause('file_too_large', 4 * MB);
  assert.equal(cause, 'workspace-quota');
  assert.match(detail, /aggregate storage/);
});

test('no error at all on a large file is the byte transfer', () => {
  const [cause, detail] = refusalCause('', 300 * MB);
  assert.equal(cause, 'transfer');
  assert.match(detail, /timeout/);
});

test('internal_error on a large upload is read as the transfer', () => {
  assert.equal(refusalCause('internal_error', 300 * MB)[0], 'large-internal-error');
});

test('a length complaint belongs to the upload sequence note', () => {
  assert.equal(refusalCause('invalid_arguments', 4 * MB)[0], 'declared-length');
});

test('an unrelated error is not dressed up as a size problem', () => {
  assert.equal(refusalCause('not_in_channel', 4 * MB)[0], 'not-a-size-problem');
});
''',
"faq": [
 ("The documentation says 1 GB. Why does a 60 MB file fail?",
  "Because the cap and the failure are in different places. 1 GB is where Slack refuses the file. The byte transfer in the middle of the upload is a plain HTTP request to a storage host that is not a Slack API host, and it inherits none of your Slack client's timeout, retry or proxy configuration, so it times out at whatever your HTTP library's default happens to be. That number is usually thirty seconds, which at a typical office uplink is somewhere in the tens of megabytes."),
 ("We get file_too_large on a four megabyte CSV. How is that possible?",
  "The workspace has run out of aggregate file storage. The per-file cap and the workspace quota share an error string, and when the quota is the one you hit, the size of the file you happened to be uploading is irrelevant. Nothing you do to that CSV will change the answer: somebody has to delete old files or the workspace needs more storage. The script tells the two apart by comparing the recorded size against the cap."),
 ("Should we just retry the upload with backoff?",
  "Not with the policy you use for API calls. Retrying a failed chat.postMessage costs a few hundred bytes; retrying a failed 600 MB upload sends 600 MB again, and three attempts turn a slow morning into a saturated link. If the transfer arithmetic says the file needs longer than your timeout allows, every retry is guaranteed to fail in exactly the same way. Fix the timeout first, then retry once."),
 ("What size is actually safe to send to Slack?",
  "There is no published safe number, which is why the script takes the band edge as an argument rather than asserting one. The number that belongs there is the size at which your own uploads started getting slow, and you can read that off your own logs. As a starting point, anything in the tens of megabytes deserves a deliberate decision, and anything in the hundreds belongs in object storage with a link posted into the channel."),
 ("The file appears in Slack but it is empty. Is that this problem?",
  "No, and the script separates it out deliberately. A file registered with size zero means the completion call succeeded and the byte transfer did not, which is the upload sequence breaking in the middle rather than any size limit. It is counted and handed off rather than folded into the size report, because the two want opposite repairs: one wants a smaller file and the other wants the transfer to actually happen."),
],
"related": [
 ("/slack/incomplete-external-upload/", "the same sequence stopping between its three calls"),
 ("/slack/files-upload-retired/", "the method these limits used to apply to"),
 ("/slack/file-retention-deletes-history/", "the other reason a file is not where you left it"),
],
"citations": [CITE_GET_UPLOAD_URL, CITE_FILES_LIST, CITE_SDK_LARGE, CITE_WORKING_FILES],
})

GUIDES.append({
"slug": "file-retention-deletes-history",
"title": "Retention deletes the history your app treats as storage",
"description": "An admin sets a policy and messages and files stop existing on a schedule. Bisect conversations.history to measure the horizon in days before it costs you.",
"h1": "Retention deletes the history your app treats as storage",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack retention policy deletes files",
             "slack conversations.history returns nothing old",
             "slack message retention api",
             "slack free plan 90 day history limit",
             "slack as system of record"],
"deps": "Python 3.9+ with requests, or Node.js 18+; a bot token with channels:read, channels:history and files:read",
"lead": "The compliance export has a hole in it, and the hole is suspiciously tidy. Everything from the last three months is there. Everything before that is not, in every channel, for every kind of content, with no gaps at the edges and no errors in the ingestion log. It looks like a bug in the backfill, so somebody rewrites the backfill.</p><p>It is not a bug. An administrator set a retention policy at some point, possibly years ago, possibly before your app existed, and Slack has been quietly deleting the workspace's own history ever since. Nothing announced it, because there is no announcement.",
"short_answer": """<p>Workspace and Enterprise Grid admins can set retention policies that <strong>delete messages and files after a fixed period</strong>, and free workspaces additionally stop returning history past a fixed age. Neither is reported to apps. There is no field on <code>team.info</code>, no header, and no error: content simply stops existing, and <code>conversations.history</code> answers <code>ok: true</code> with an empty array for the range where it used to answer with messages.</p>
<p>So you have to measure it. Probe <code>conversations.history?channel=C...&amp;oldest=&lt;t&gt;&amp;latest=&lt;t+7d&gt;&amp;limit=10</code> at increasing ages &mdash; thirty days, sixty, ninety, a year, two &mdash; and find the age at which results stop coming back. <strong>The finding is a number in days</strong>, and it is a property of the workspace rather than of any one message or file.</p>
<p>The measurement is only meaningful across several channels. A single channel that was quiet last spring looks exactly like a retention boundary, so the script requires <strong>agreement</strong>: two or more channels stopping at the same age is a policy, and channels stopping at different ages is a set of quiet channels. One channel that still returns older history than the others disproves the whole thing.</p>""",
"problem": """<p>The reason this gets misdiagnosed is that it is too clean. Real bugs are ragged &mdash; they lose some records, they fail on Tuesdays, they break for one channel. Retention removes everything older than a line, everywhere, with no exceptions, which does not look like anything going wrong. It looks like the ingestion never ran, so the first suspect is always the ingestion, and rewriting it produces exactly the same hole.</p>
<p>The second thing that hides it is that it is retroactive from your point of view but not from Slack's. Nothing was deleted at export time. The messages were deleted continuously, a day at a time, for as long as the policy has been on, and the day the app finally goes looking for them is simply the day it finds out. An integration that treats Slack as its system of record has silently adopted somebody else's retention policy as its data-loss policy, and nobody in the room ever decided that.</p>
<p>Retention deletes <strong>messages as well as files</strong>, which is what separates this from a file being deleted on its own. When a file is deleted individually, the message that carried it survives and keeps rendering a link, so an index develops dead references while the surrounding text stays put &mdash; that is <a href="/slack/file-deleted-link-rot/">its own note</a> and its shape is a growing fraction of broken pointers. Retention takes the message and the file together, so there is no dangling reference to find. There is nothing at all before the boundary, which is why the detector has to be a search for an edge rather than a scan for failures.</p>
<p>The free plan complicates the reading in a way worth being honest about. On free workspaces, history older than the plan's limit is not returned even though it has not necessarily been deleted, and from an app's side that is indistinguishable from retention: the same empty array at the same kind of boundary. The measurement is identical, the number is identical, and only the repair differs &mdash; one is a conversation with an admin about a policy, the other is a conversation about a plan. The script reports the boundary and names both possibilities rather than picking one it cannot verify.</p>""",
"why": """<p><strong>There is no read that returns the policy.</strong> A bot token cannot ask what the retention setting is; Grid admin methods can get close with admin scopes that a runtime app does not have. So the only available measurement is the effect, and the effect is an age. Everything in this script exists to turn "old stuff is missing" into a number somebody can take to an administrator.</p>
<p><strong>A quiet channel is the false positive that ruins this check.</strong> An empty window means either that the content was deleted or that nothing was said. Those are indistinguishable in one channel and separable across several, which is why the script probes a set and reports agreement rather than a boundary per channel. A single-channel run is explicitly labelled undecidable.</p>
<p><strong>History that reappears past an empty window disproves a horizon.</strong> If a channel returns nothing at ninety days and something at a year, that is a quiet stretch, not a policy: retention is monotonic, and anything non-monotonic is evidence against the finding rather than noise in it. The script names that state <code>ragged</code> and refuses to draw a boundary through it.</p>
<p><strong>The boundary is worth snapping to a policy value.</strong> Measured boundaries land near round numbers because the settings are round numbers, and a measurement of eighty-eight days is a ninety-day policy. Saying "ninety days" is what makes the finding actionable; saying "somewhere between sixty and ninety" invites another week of probing.</p>
<p><strong>The gap that matters is against your own lookback.</strong> A ninety-day horizon is fine for an app that reads a week and fatal for one that backfills a year. The number to report is the shortfall between what the workspace keeps and what your app assumes, because that difference is data you are already losing every day.</p>
<p><strong>The repair is to stop treating Slack as the archive.</strong> Copy what matters into your own store at ingestion time, message text with its <code>ts</code> and file bytes through the authenticated download, and treat Slack as transport. Where genuine compliance retention is required, that is what Grid's Discovery and audit surfaces exist for, and they are a different product decision rather than a scope you can add.</p>""",
"steps": [
 {"h": "Pick several channels the bot is already in",
  "body": """<p>One channel cannot answer this. The script takes <code>--channels</code>, or falls back to the public channels <code>conversations.list</code> reports the bot as a member of, and probes each of them independently so that the answers can be compared.</p>"""},
 {"h": "Probe a ladder of ages rather than bisecting blind",
  "body": """<p><code>probe_windows</code> builds a seven-day window at thirty, sixty, ninety, a hundred and eighty, three hundred and sixty-five and seven hundred and thirty days ago. Six reads per channel finds the decade-old edge as fast as a bisection and, unlike a bisection, the intermediate results are all still meaningful when the answer turns out to be ragged.</p>"""},
 {"h": "Find the edge, and refuse to find one that is not there",
  "body": """<p><code>horizon</code> returns <code>boundary</code>, <code>no-boundary</code>, <code>silent</code>, <code>ragged</code> or <code>undecidable</code>. Only the first is a finding. <code>silent</code> means even the newest window was empty, so the channel is quiet and the probe decided nothing at all.</p>"""},
 {"h": "Require the channels to agree before calling it a policy",
  "body": """<p><code>agreement</code> takes every channel's answer. Two or more boundaries at the same age is a workspace setting; different ages are quiet channels; and a single channel still returning older history than the rest is a contradiction that ends the investigation rather than a row to ignore.</p>"""},
 {"h": "Snap the measurement to the setting it probably is",
  "body": """<p><code>snap_to_policy</code> maps a measured age to the nearest of the round values these policies actually take. Ninety days carries an extra sentence, because ninety is also where a free workspace stops returning history and this measurement cannot tell those apart.</p>"""},
 {"h": "Report the shortfall against what your app assumes",
  "body": """<p><code>expectation_gap</code> takes the measured horizon and the <code>--lookback-days</code> your app backfills. <code>losing</code> with a number is the sentence to put in the ticket: the app reads back a year, the workspace keeps ninety days, and two hundred and seventy-five days of every backfill were gone before it started.</p>"""},
],
"verify": """<p>The output to aim for is a single number and the word <code>policy</code> beside it, because that is the version of this finding an administrator can act on.</p>
<pre><code class="language-bash">python3 slack_retention_horizon.py --lookback-days 365
# identity   U07BOT9QD (reports-bot) in Northwind
# probe      C01ENG9QT  30d:10 60d:10 90d:7 180d:0 365d:0 730d:0
# probe      C02OPS4QW  30d:10 60d:10 90d:4 180d:0 365d:0 730d:0
# probe      C03RND7QX  30d:10 60d:9  90d:6 180d:0 365d:0 730d:0
# horizon    boundary       C01ENG9QT  history stops between 90 and 180 days
# horizon    boundary       C02OPS4QW  history stops between 90 and 180 days
# agreement  policy         3 channel(s) stop at the same age, which is a workspace
#                           setting rather than three quiet channels
# policy     90 days        also the free plan's visible history limit; this probe
#                           cannot tell a retention policy from a plan limit
# files      boundary       files.list returns nothing older than 180 days either
# gap        losing         the app backfills 365 day(s) and the workspace keeps about
#                           180; 185 day(s) of every backfill were gone before it ran
#   repair: copy message text with its ts, and file bytes, into your own store
#   repair: ask an admin for the actual retention setting rather than inferring it</code></pre>""",
"code_intro": "Two reads and five pure functions, and all the interesting work is in refusing to answer. <code>horizon</code> has five outcomes and only one of them is a finding, because an empty window is ambiguous by construction. <code>agreement</code> is the guard that turns three ambiguous channels into one unambiguous workspace answer, or into an explicit contradiction. <code>snap_to_policy</code> makes the number sayable, and <code>expectation_gap</code> turns it into the sentence that belongs in the ticket.",
"py_file": "slack_retention_horizon.py",
"py": '''"""Measure how far back this workspace's history actually goes.

Read only. conversations.list, conversations.history, files.list and auth.test
are reads; nothing here writes, deletes or downloads anything, and no file
bytes and no url_private are ever fetched.

Retention policies delete messages and files on a schedule that no API reports.
There is no field to query and no error to catch: content stops existing, and
history calls answer ok with an empty array. So the policy is measured from its
effect, by asking about progressively older windows until the answers stop, and
the finding is an age in days.

The trap is that a quiet channel is also empty. That is why nothing here draws
a conclusion from one channel.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_retention_horizon")

API = "https://slack.com/api/"
DAY = 86400

# Ages to probe, in days, newest first. A ladder rather than a bisection: the
# same six reads, and every intermediate answer stays meaningful when the shape
# turns out to be ragged rather than a clean edge.
LADDER = (30, 60, 90, 180, 365, 730)

# The round numbers retention settings are actually set to. A measurement of 88
# days is a 90 day policy, and saying so is what makes the finding actionable.
POLICY_VALUES = (30, 60, 90, 180, 365)


def probe_windows(now, ladder=LADDER, span_days=7):
    """The windows to ask about. Pure. Returns [(age_days, oldest, latest), ...].

    A window rather than an open-ended oldest, because "everything since two
    years ago" returns the most recent page and tells you nothing about two
    years ago. A week is wide enough that an active channel has something in it
    and narrow enough that the edge stays sharp.
    """
    try:
        base = int(now)
    except (TypeError, ValueError):
        return []
    out = []
    for age in sorted({int(a) for a in ladder if int(a) > 0}):
        oldest = base - age * DAY
        out.append((age, oldest, oldest + span_days * DAY))
    return out


def horizon(probes):
    """Where does the history stop? Pure. Returns (verdict, boundary_days, detail).

    probes is [(age_days, count), ...] in any order. Five outcomes and only one
    of them is a finding:

      boundary     results at some ages and none beyond a point. The edge.
      no-boundary  results at every age probed, so nothing was found in range.
      silent       nothing at any age, including the newest. The channel is
                   quiet and this probe has decided precisely nothing.
      ragged       history reappears past an empty window. Retention is
                   monotonic, so this is a quiet stretch and evidence against a
                   horizon rather than noise inside one.
      undecidable  fewer than two probes to compare.
    """
    rows = sorted((int(a), int(c)) for a, c in (probes or []))
    if len(rows) < 2:
        return ("undecidable", 0, "at least two ages are needed to find an edge")
    if all(c <= 0 for _a, c in rows):
        return ("silent", 0, "every window was empty, including the newest. This "
                             "channel is quiet and the probe decides nothing")
    if all(c > 0 for _a, c in rows):
        return ("no-boundary", 0, "history came back at every age probed, out to %d "
                                  "day(s). Nothing here indicates a horizon in that "
                                  "range" % rows[-1][0])
    first_empty = next(a for a, c in rows if c <= 0)
    if any(c > 0 for a, c in rows if a > first_empty):
        return ("ragged", 0, "history reappears past an empty window at %d day(s). "
                             "Retention is monotonic, so this is a quiet stretch "
                             "rather than an edge" % first_empty)
    last_full = max(a for a, c in rows if c > 0)
    return ("boundary", first_empty, "history stops between %d and %d day(s)"
                                     % (last_full, first_empty))


def agreement(answers):
    """Do the channels agree on the same edge? Pure.

    answers is [(channel, verdict, days), ...]. One channel cannot distinguish
    a retention policy from a channel nobody used, so this is where an
    ambiguous per-channel reading becomes a workspace-level one, or is refused.

    Returns (verdict, days, detail).
    """
    rows = list(answers or [])
    edges = [(c, d) for c, v, d in rows if v == "boundary" and d]
    if any(v == "no-boundary" for _c, v, _d in rows) and edges:
        return ("contradicted", 0, "at least one channel still returns history older "
                                   "than the edge the others show, so this is not a "
                                   "workspace-wide policy")
    if len(edges) < 2:
        return ("insufficient", 0, "%d channel(s) produced an edge. Two that agree are "
                                   "the minimum for calling this a policy" % len(edges))
    days = sorted(d for _c, d in edges)
    if days[0] != days[-1]:
        return ("disagreement", 0, "the channels stop at different ages (%d to %d "
                                   "day(s)), which is what a set of quiet channels "
                                   "looks like" % (days[0], days[-1]))
    return ("policy", days[0], "%d channel(s) stop at the same age, which is a "
                               "workspace setting rather than %d quiet channels"
                               % (len(edges), len(edges)))


def snap_to_policy(days):
    """Name the setting a measured boundary probably is. Pure.

    Returns (label, detail). Ninety carries an extra sentence because ninety is
    also where a free workspace stops returning history, and from an app's side
    a plan limit and a deletion policy are the same empty array.
    """
    try:
        n = int(days)
    except (TypeError, ValueError):
        return ("unknown", "no boundary to name")
    if n <= 0:
        return ("unknown", "no boundary to name")
    nearest = min(POLICY_VALUES, key=lambda v: abs(v - n))
    if abs(nearest - n) > nearest * 0.25:
        return ("custom", "%d day(s) is not near any of the usual settings, so ask for "
                          "the configured value rather than guessing at it" % n)
    if nearest == 90:
        return ("90 days", "also the free plan's visible history limit; this probe "
                           "cannot tell a retention policy from a plan limit, and the "
                           "two want different conversations")
    return ("%d days" % nearest, "a measured edge at %d day(s), which is the %d day "
                                 "setting" % (n, nearest))


def expectation_gap(retention_days, lookback_days):
    """What does your app assume, against what the workspace keeps? Pure.

    Returns (verdict, shortfall_days, detail). losing with a number is the
    sentence that belongs in the ticket, because it says how much of every
    backfill was already gone before the backfill started.
    """
    try:
        keeps = int(retention_days)
        wants = int(lookback_days)
    except (TypeError, ValueError):
        return ("unknown", 0, "both the measured horizon and the app's lookback are "
                              "needed")
    if keeps <= 0 or wants <= 0:
        return ("unknown", 0, "both the measured horizon and the app's lookback are "
                              "needed")
    if keeps >= wants * 1.5:
        return ("covered", 0, "the workspace keeps %d day(s) and the app reads back "
                              "%d" % (keeps, wants))
    if keeps >= wants:
        return ("tight", 0, "the workspace keeps %d day(s) and the app reads back %d. "
                            "One policy change closes that" % (keeps, wants))
    return ("losing", wants - keeps, "the app backfills %d day(s) and the workspace "
                                     "keeps about %d; %d day(s) of every backfill were "
                                     "gone before it ran"
                                     % (wants, keeps, wants - keeps))


def count_window(session, channel, oldest, latest, limit=10):
    """How many messages are in this window? A read."""
    body = session.get(API + "conversations.history", timeout=30, params={
        "channel": channel, "oldest": str(oldest), "latest": str(latest),
        "limit": str(limit), "inclusive": "true"}).json()
    if body.get("ok") is not True:
        return None, str(body.get("error") or "")
    return len(body.get("messages") or []), ""


def count_files(session, oldest, latest, limit=10):
    """How many files are in this window? A read, and no bytes are fetched."""
    body = session.get(API + "files.list", timeout=30, params={
        "ts_from": str(oldest), "ts_to": str(latest), "count": str(limit),
        "types": "all"}).json()
    if body.get("ok") is not True:
        return None, str(body.get("error") or "")
    return len(body.get("files") or []), ""


def member_channels(session, wanted):
    """Channels to probe: the ones asked for, or the ones the bot is in. A read."""
    if wanted:
        return [c.strip() for c in wanted.split(",") if c.strip()]
    body = session.get(API + "conversations.list", timeout=30, params={
        "types": "public_channel", "exclude_archived": "true", "limit": "200"}).json()
    if body.get("ok") is not True:
        log.error("conversations.list unavailable    %s", body.get("error"))
        return []
    return [c.get("id") for c in body.get("channels") or [] if c.get("is_member")]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN",
                    help="environment variable holding the bot token")
    ap.add_argument("--channels", default="",
                    help="comma separated channel ids; defaults to the bot's channels")
    ap.add_argument("--max-channels", type=int, default=3,
                    help="how many channels to probe; two is the minimum that decides")
    ap.add_argument("--lookback-days", type=int, default=0,
                    help="how far back your app assumes it can read")
    ap.add_argument("--span-days", type=int, default=7,
                    help="width of each probe window")
    ap.add_argument("--skip-files", action="store_true",
                    help="probe messages only")
    args = ap.parse_args()

    token = os.environ.get(args.token_env)
    if not token:
        log.error("set %s to a bot token with channels:history", args.token_env)
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + token})
    who = s.get(API + "auth.test", timeout=30).json()
    if who.get("ok") is not True:
        log.error("auth.test  unavailable    %s", who.get("error"))
        return 2
    log.info("identity   %s (%s) in %s", who.get("user_id"), who.get("user"),
             who.get("team"))

    channels = member_channels(s, args.channels)[:max(1, args.max_channels)]
    if not channels:
        log.error("channels   none to probe; pass --channels or invite the bot")
        return 2

    windows = probe_windows(time.time(), LADDER, args.span_days)
    answers = []
    for channel in channels:
        probes, cells = [], []
        for age, oldest, latest in windows:
            count, error = count_window(s, channel, oldest, latest)
            if count is None:
                log.warning("probe      %s  %dd unavailable: %s", channel, age, error)
                continue
            probes.append((age, count))
            cells.append("%dd:%d" % (age, count))
        log.info("probe      %s  %s", channel, " ".join(cells))
        verdict, days, detail = horizon(probes)
        answers.append((channel, verdict, days))
        (log.warning if verdict == "boundary" else log.info)(
            "horizon    %-14s %s  %s", verdict, channel, detail)

    state, days, detail = agreement(answers)
    (log.warning if state == "policy" else log.info)(
        "agreement  %-14s %s", state, detail)

    if state == "policy":
        label, note = snap_to_policy(days)
        log.warning("policy     %-14s %s", label, note)

    if not args.skip_files:
        probes = []
        for age, oldest, latest in windows:
            count, error = count_files(s, oldest, latest)
            if count is None:
                log.info("files      %dd unavailable: %s", age, error)
                continue
            probes.append((age, count))
        fverdict, fdays, fdetail = horizon(probes)
        log.info("files      %-14s %s", fverdict, fdetail)
        if fverdict == "boundary" and state != "policy":
            days = days or fdays

    if args.lookback_days and days:
        gap, shortfall, gdetail = expectation_gap(days, args.lookback_days)
        (log.warning if gap == "losing" else log.info)("gap        %-14s %s", gap,
                                                       gdetail)
        if gap == "losing":
            log.warning("  repair: copy message text with its ts, and file bytes "
                        "through the authenticated download, into your own store at "
                        "ingestion time")
            log.warning("  repair: ask an admin for the configured retention setting "
                        "rather than inferring it, and record %d day(s) as the number "
                        "the app may assume", days)
            log.warning("  repair: where retention is a compliance requirement, that "
                        "is what Grid's Discovery and audit surfaces are for")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-retention-horizon.mjs",
"js": '''/**
 * Measure how far back this workspace's history actually goes.
 *
 * Read only. conversations.list, conversations.history, files.list and
 * auth.test are reads; nothing here writes, deletes or downloads anything, and
 * no file bytes and no url_private are ever fetched.
 *
 * Retention policies delete messages and files on a schedule that no API
 * reports, so the policy is measured from its effect: ask about progressively
 * older windows until the answers stop. The trap is that a quiet channel is
 * also empty, which is why nothing here concludes anything from one channel.
 */

const API = 'https://slack.com/api/';
const DAY = 86400;

/** Ages to probe, in days. A ladder rather than a bisection. */
export const LADDER = [30, 60, 90, 180, 365, 730];
/** The round numbers retention settings are actually set to. */
export const POLICY_VALUES = [30, 60, 90, 180, 365];

/**
 * The windows to ask about. Pure. Returns [[ageDays, oldest, latest], ...].
 * A window rather than an open-ended oldest, because "everything since two
 * years ago" returns the most recent page and says nothing about two years ago.
 */
export function probeWindows(now, ladder = LADDER, spanDays = 7) {
  const base = Number.parseInt(now, 10);
  if (!Number.isFinite(base)) return [];
  const ages = [...new Set((ladder ?? []).map((a) => Number.parseInt(a, 10)))]
    .filter((a) => Number.isFinite(a) && a > 0).sort((a, b) => a - b);
  return ages.map((age) => {
    const oldest = base - age * DAY;
    return [age, oldest, oldest + spanDays * DAY];
  });
}

/**
 * Where does the history stop? Pure. Returns [verdict, boundaryDays, detail].
 * Five outcomes and only boundary is a finding: silent means the channel was
 * quiet, and ragged means history reappears past an empty window, which is
 * evidence against a horizon rather than noise inside one.
 */
export function horizon(probes) {
  const rows = (probes ?? []).map(([a, c]) => [Number.parseInt(a, 10),
    Number.parseInt(c, 10)]).sort((x, y) => x[0] - y[0]);
  if (rows.length < 2) {
    return ['undecidable', 0, 'at least two ages are needed to find an edge'];
  }
  if (rows.every(([, c]) => c <= 0)) {
    return ['silent', 0, 'every window was empty, including the newest. This channel '
      + 'is quiet and the probe decides nothing'];
  }
  if (rows.every(([, c]) => c > 0)) {
    return ['no-boundary', 0, `history came back at every age probed, out to `
      + `${rows[rows.length - 1][0]} day(s). Nothing here indicates a horizon in that `
      + 'range'];
  }
  const firstEmpty = rows.find(([, c]) => c <= 0)[0];
  if (rows.some(([a, c]) => a > firstEmpty && c > 0)) {
    return ['ragged', 0, `history reappears past an empty window at ${firstEmpty} `
      + 'day(s). Retention is monotonic, so this is a quiet stretch rather than an '
      + 'edge'];
  }
  const lastFull = Math.max(...rows.filter(([, c]) => c > 0).map(([a]) => a));
  return ['boundary', firstEmpty, `history stops between ${lastFull} and ${firstEmpty} `
    + 'day(s)'];
}

/**
 * Do the channels agree on the same edge? Pure. Returns [verdict, days, detail].
 * One channel cannot tell a retention policy from a channel nobody used.
 */
export function agreement(answers) {
  const rows = answers ?? [];
  const edges = rows.filter(([, v, d]) => v === 'boundary' && d);
  if (rows.some(([, v]) => v === 'no-boundary') && edges.length) {
    return ['contradicted', 0, 'at least one channel still returns history older than '
      + 'the edge the others show, so this is not a workspace-wide policy'];
  }
  if (edges.length < 2) {
    return ['insufficient', 0, `${edges.length} channel(s) produced an edge. Two that `
      + 'agree are the minimum for calling this a policy'];
  }
  const days = edges.map(([, , d]) => d).sort((a, b) => a - b);
  if (days[0] !== days[days.length - 1]) {
    return ['disagreement', 0, `the channels stop at different ages (${days[0]} to `
      + `${days[days.length - 1]} day(s)), which is what a set of quiet channels looks `
      + 'like'];
  }
  return ['policy', days[0], `${edges.length} channel(s) stop at the same age, which is `
    + `a workspace setting rather than ${edges.length} quiet channels`];
}

/**
 * Name the setting a measured boundary probably is. Pure.
 * Ninety carries an extra sentence: it is also where a free workspace stops
 * returning history, and a plan limit and a deletion policy look identical.
 */
export function snapToPolicy(days) {
  const n = Number.parseInt(days, 10);
  if (!Number.isFinite(n) || n <= 0) return ['unknown', 'no boundary to name'];
  const nearest = POLICY_VALUES.reduce((best, v) => (Math.abs(v - n)
    < Math.abs(best - n) ? v : best), POLICY_VALUES[0]);
  if (Math.abs(nearest - n) > nearest * 0.25) {
    return ['custom', `${n} day(s) is not near any of the usual settings, so ask for `
      + 'the configured value rather than guessing at it'];
  }
  if (nearest === 90) {
    return ['90 days', 'also the free plan visible history limit; this probe cannot '
      + 'tell a retention policy from a plan limit, and the two want different '
      + 'conversations'];
  }
  return [`${nearest} days`, `a measured edge at ${n} day(s), which is the ${nearest} `
    + 'day setting'];
}

/**
 * What does your app assume, against what the workspace keeps? Pure.
 * Returns [verdict, shortfallDays, detail].
 */
export function expectationGap(retentionDays, lookbackDays) {
  const keeps = Number.parseInt(retentionDays, 10);
  const wants = Number.parseInt(lookbackDays, 10);
  if (!Number.isFinite(keeps) || !Number.isFinite(wants) || keeps <= 0 || wants <= 0) {
    return ['unknown', 0, 'both the measured horizon and the app lookback are needed'];
  }
  if (keeps >= wants * 1.5) {
    return ['covered', 0, `the workspace keeps ${keeps} day(s) and the app reads back `
      + `${wants}`];
  }
  if (keeps >= wants) {
    return ['tight', 0, `the workspace keeps ${keeps} day(s) and the app reads back `
      + `${wants}. One policy change closes that`];
  }
  return ['losing', wants - keeps, `the app backfills ${wants} day(s) and the workspace `
    + `keeps about ${keeps}; ${wants - keeps} day(s) of every backfill were gone before `
    + 'it ran'];
}

function arg(args, name, fallback = null) {
  const i = args.indexOf(name);
  return i === -1 ? fallback : args[i + 1];
}

async function countWindow(headers, channel, oldest, latest, limit = 10) {
  const params = new URLSearchParams({
    channel, oldest: String(oldest), latest: String(latest), limit: String(limit),
    inclusive: 'true',
  });
  const body = await (await fetch(`${API}conversations.history?${params}`,
    { headers })).json();
  if (body.ok !== true) return [null, String(body.error ?? '')];
  return [(body.messages ?? []).length, ''];
}

async function countFiles(headers, oldest, latest, limit = 10) {
  const params = new URLSearchParams({
    ts_from: String(oldest), ts_to: String(latest), count: String(limit), types: 'all',
  });
  const body = await (await fetch(`${API}files.list?${params}`, { headers })).json();
  if (body.ok !== true) return [null, String(body.error ?? '')];
  return [(body.files ?? []).length, ''];
}

async function memberChannels(headers, wanted) {
  if (wanted) return wanted.split(',').map((c) => c.trim()).filter(Boolean);
  const params = new URLSearchParams({
    types: 'public_channel', exclude_archived: 'true', limit: '200',
  });
  const body = await (await fetch(`${API}conversations.list?${params}`,
    { headers })).json();
  if (body.ok !== true) {
    console.error(`conversations.list unavailable    ${body.error}`);
    return [];
  }
  return (body.channels ?? []).filter((c) => c.is_member).map((c) => c.id);
}

async function main() {
  const args = process.argv.slice(2);
  const tokenEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
  const token = process.env[tokenEnv];
  if (!token) {
    console.error(`set ${tokenEnv} to a bot token with channels:history`);
    process.exitCode = 2;
    return;
  }
  const headers = { Authorization: `Bearer ${token}` };
  const who = await (await fetch(`${API}auth.test`, { headers })).json();
  if (who.ok !== true) {
    console.error(`auth.test  unavailable    ${who.error}`);
    process.exitCode = 2;
    return;
  }
  console.log(`identity   ${who.user_id} (${who.user}) in ${who.team}`);

  const maxChannels = Math.max(1, Number(arg(args, '--max-channels', 3)));
  const channels = (await memberChannels(headers, arg(args, '--channels', '')))
    .slice(0, maxChannels);
  if (!channels.length) {
    console.error('channels   none to probe; pass --channels or invite the bot');
    process.exitCode = 2;
    return;
  }

  const windows = probeWindows(Math.floor(Date.now() / 1000), LADDER,
    Number(arg(args, '--span-days', 7)));
  const answers = [];
  for (const channel of channels) {
    const probes = [];
    const cells = [];
    for (const [age, oldest, latest] of windows) {
      const [count, error] = await countWindow(headers, channel, oldest, latest);
      if (count === null) {
        console.warn(`probe      ${channel}  ${age}d unavailable: ${error}`);
        continue;
      }
      probes.push([age, count]);
      cells.push(`${age}d:${count}`);
    }
    console.log(`probe      ${channel}  ${cells.join(' ')}`);
    const [verdict, days, detail] = horizon(probes);
    answers.push([channel, verdict, days]);
    const line = `horizon    ${verdict.padEnd(14)} ${channel}  ${detail}`;
    if (verdict === 'boundary') console.warn(line); else console.log(line);
  }

  const [state, days, detail] = agreement(answers);
  const line = `agreement  ${state.padEnd(14)} ${detail}`;
  if (state === 'policy') console.warn(line); else console.log(line);
  if (state === 'policy') {
    const [label, note] = snapToPolicy(days);
    console.warn(`policy     ${label.padEnd(14)} ${note}`);
  }

  let horizonDays = days;
  if (!args.includes('--skip-files')) {
    const probes = [];
    for (const [age, oldest, latest] of windows) {
      const [count, error] = await countFiles(headers, oldest, latest);
      if (count === null) {
        console.log(`files      ${age}d unavailable: ${error}`);
        continue;
      }
      probes.push([age, count]);
    }
    const [fverdict, fdays, fdetail] = horizon(probes);
    console.log(`files      ${fverdict.padEnd(14)} ${fdetail}`);
    if (fverdict === 'boundary' && state !== 'policy') horizonDays = horizonDays || fdays;
  }

  const lookback = Number(arg(args, '--lookback-days', 0));
  if (lookback && horizonDays) {
    const [gap, , gdetail] = expectationGap(horizonDays, lookback);
    const gline = `gap        ${gap.padEnd(14)} ${gdetail}`;
    if (gap === 'losing') console.warn(gline); else console.log(gline);
    if (gap === 'losing') {
      console.warn('  repair: copy message text with its ts, and file bytes through '
        + 'the authenticated download, into your own store at ingestion time');
      console.warn('  repair: ask an admin for the configured retention setting rather '
        + `than inferring it, and record ${horizonDays} day(s) as the assumption`);
      process.exitCode = 1;
    }
  }
}

// Only run when invoked directly, so importing this module in the tests does
// not execute main() and fail the file on a missing token.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Every test here is about not declaring a boundary that is not there. A channel with nothing in any window has to come back <code>silent</code> rather than as an edge at thirty days, because a quiet channel is the false positive that would make this check worthless. History that reappears past an empty window has to come back <code>ragged</code>, since retention is monotonic and anything else is evidence against the finding. And <code>agreement</code> is tested for the case that ends the investigation: one channel still holding older history than the others disproves a workspace-wide policy outright.",
"test_py_file": "test_slack_retention_horizon.py",
"test_py": '''from slack_retention_horizon import (agreement, expectation_gap, horizon,
                                     probe_windows, snap_to_policy)

DAY = 86400


def test_the_windows_are_bounded_rather_than_open_ended():
    got = probe_windows(1000000, ladder=(30,), span_days=7)
    assert got == [(30, 1000000 - 30 * DAY, 1000000 - 30 * DAY + 7 * DAY)]


def test_the_ladder_is_sorted_and_deduplicated():
    assert [a for a, _o, _l in probe_windows(1000000, ladder=(90, 30, 30))] == [30, 90]


def test_a_bad_clock_produces_no_windows_rather_than_raising():
    assert probe_windows(None) == []


def test_an_edge_is_reported_between_the_two_ages_that_bracket_it():
    verdict, days, detail = horizon([(30, 10), (90, 7), (180, 0), (365, 0)])
    assert (verdict, days) == ("boundary", 180)
    assert "between 90 and 180" in detail


def test_history_at_every_age_is_not_a_boundary():
    assert horizon([(30, 10), (365, 4), (730, 2)])[0] == "no-boundary"


def test_a_quiet_channel_is_silent_rather_than_an_edge_at_thirty_days():
    verdict, _days, detail = horizon([(30, 0), (90, 0), (365, 0)])
    assert verdict == "silent"
    assert "decides nothing" in detail


def test_history_reappearing_past_an_empty_window_is_ragged():
    verdict, days, _detail = horizon([(30, 8), (90, 0), (365, 6)])
    assert (verdict, days) == ("ragged", 0)


def test_one_probe_cannot_find_an_edge():
    assert horizon([(30, 10)])[0] == "undecidable"
    assert horizon([])[0] == "undecidable"


def test_two_channels_stopping_at_the_same_age_is_a_policy():
    verdict, days, detail = agreement([("C1", "boundary", 180),
                                       ("C2", "boundary", 180)])
    assert (verdict, days) == ("policy", 180)
    assert "workspace setting" in detail


def test_one_channel_is_never_enough_to_call_it_a_policy():
    assert agreement([("C1", "boundary", 180)])[0] == "insufficient"


def test_channels_stopping_at_different_ages_are_just_quiet():
    assert agreement([("C1", "boundary", 90), ("C2", "boundary", 365)])[0] == \\
        "disagreement"


def test_a_channel_with_older_history_disproves_the_whole_finding():
    verdict, _days, detail = agreement([("C1", "boundary", 180),
                                        ("C2", "boundary", 180),
                                        ("C3", "no-boundary", 0)])
    assert verdict == "contradicted"
    assert "not a workspace-wide policy" in detail


def test_a_measured_edge_snaps_to_the_setting_it_probably_is():
    label, _detail = snap_to_policy(188)
    assert label == "180 days"


def test_ninety_days_carries_the_free_plan_caveat():
    label, detail = snap_to_policy(88)
    assert label == "90 days"
    assert "plan limit" in detail


def test_an_edge_near_nothing_familiar_is_not_forced_onto_a_setting():
    assert snap_to_policy(500)[0] == "custom"
    assert snap_to_policy(0)[0] == "unknown"


def test_a_backfill_longer_than_the_horizon_is_losing_data_every_day():
    verdict, shortfall, detail = expectation_gap(180, 365)
    assert (verdict, shortfall) == ("losing", 185)
    assert "before it ran" in detail


def test_a_horizon_that_only_just_covers_the_lookback_is_tight():
    assert expectation_gap(400, 365)[0] == "tight"


def test_plenty_of_room_is_reported_as_covered():
    assert expectation_gap(730, 30)[0] == "covered"


def test_the_gap_needs_both_numbers():
    assert expectation_gap(0, 365)[0] == "unknown"
    assert expectation_gap(180, None)[0] == "unknown"
''',
"test_js_file": "slack-retention-horizon.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  agreement, expectationGap, horizon, probeWindows, snapToPolicy,
} from './slack-retention-horizon.mjs';

const DAY = 86400;

test('the windows are bounded rather than open ended', () => {
  assert.deepEqual(probeWindows(1000000, [30], 7),
    [[30, 1000000 - 30 * DAY, 1000000 - 30 * DAY + 7 * DAY]]);
});

test('the ladder is sorted and deduplicated', () => {
  assert.deepEqual(probeWindows(1000000, [90, 30, 30]).map(([a]) => a), [30, 90]);
});

test('a bad clock produces no windows rather than throwing', () => {
  assert.deepEqual(probeWindows(null), []);
});

test('an edge is reported between the two ages that bracket it', () => {
  const [verdict, days, detail] = horizon([[30, 10], [90, 7], [180, 0], [365, 0]]);
  assert.equal(verdict, 'boundary');
  assert.equal(days, 180);
  assert.match(detail, /between 90 and 180/);
});

test('history at every age is not a boundary', () => {
  assert.equal(horizon([[30, 10], [365, 4], [730, 2]])[0], 'no-boundary');
});

test('a quiet channel is silent rather than an edge at thirty days', () => {
  const [verdict, , detail] = horizon([[30, 0], [90, 0], [365, 0]]);
  assert.equal(verdict, 'silent');
  assert.match(detail, /decides nothing/);
});

test('history reappearing past an empty window is ragged', () => {
  const [verdict, days] = horizon([[30, 8], [90, 0], [365, 6]]);
  assert.equal(verdict, 'ragged');
  assert.equal(days, 0);
});

test('one probe cannot find an edge', () => {
  assert.equal(horizon([[30, 10]])[0], 'undecidable');
  assert.equal(horizon([])[0], 'undecidable');
});

test('two channels stopping at the same age is a policy', () => {
  const [verdict, days, detail] = agreement([['C1', 'boundary', 180],
    ['C2', 'boundary', 180]]);
  assert.equal(verdict, 'policy');
  assert.equal(days, 180);
  assert.match(detail, /workspace setting/);
});

test('one channel is never enough to call it a policy', () => {
  assert.equal(agreement([['C1', 'boundary', 180]])[0], 'insufficient');
});

test('channels stopping at different ages are just quiet', () => {
  assert.equal(agreement([['C1', 'boundary', 90], ['C2', 'boundary', 365]])[0],
    'disagreement');
});

test('a channel with older history disproves the whole finding', () => {
  const [verdict, , detail] = agreement([['C1', 'boundary', 180],
    ['C2', 'boundary', 180], ['C3', 'no-boundary', 0]]);
  assert.equal(verdict, 'contradicted');
  assert.match(detail, /not a workspace-wide policy/);
});

test('a measured edge snaps to the setting it probably is', () => {
  assert.equal(snapToPolicy(188)[0], '180 days');
});

test('ninety days carries the free plan caveat', () => {
  const [label, detail] = snapToPolicy(88);
  assert.equal(label, '90 days');
  assert.match(detail, /plan limit/);
});

test('an edge near nothing familiar is not forced onto a setting', () => {
  assert.equal(snapToPolicy(500)[0], 'custom');
  assert.equal(snapToPolicy(0)[0], 'unknown');
});

test('a backfill longer than the horizon is losing data every day', () => {
  const [verdict, shortfall, detail] = expectationGap(180, 365);
  assert.equal(verdict, 'losing');
  assert.equal(shortfall, 185);
  assert.match(detail, /before it ran/);
});

test('a horizon that only just covers the lookback is tight', () => {
  assert.equal(expectationGap(400, 365)[0], 'tight');
});

test('plenty of room is reported as covered', () => {
  assert.equal(expectationGap(730, 30)[0], 'covered');
});

test('the gap needs both numbers', () => {
  assert.equal(expectationGap(0, 365)[0], 'unknown');
  assert.equal(expectationGap(180, null)[0], 'unknown');
});
''',
"faq": [
 ("Can I just read the retention setting from the API?",
  "Not with a bot token. There is no field on team.info and no header that reports it, and the Grid admin surfaces that come closest need admin scopes that a runtime app does not hold. That is precisely why this note is a measurement rather than a lookup: the only thing a read-scoped token can observe is the effect, which is that history stops at a certain age. The number you measure is the number to take to an administrator for confirmation."),
 ("How is this different from a file being deleted?",
  "A deleted file leaves its message behind. The post still renders, the link still looks like a link, and your index develops dead pointers among live ones, which is a growing fraction of broken references and a different note. Retention removes the message and the file together, so before the boundary there is nothing at all: no dangling reference to find and no fraction to compute, just an edge. That is why this detector searches for an edge instead of scanning for failures."),
 ("Our free workspace has never had a retention policy. Why is history missing?",
  "Free workspaces stop returning history past a fixed age, whether or not anything was deleted. From your app's side the two are identical: the same empty array at the same kind of boundary, with the same ok: true. The script reports the boundary and names both possibilities rather than picking the one it cannot verify, because the repairs differ completely - one is a conversation about a policy and the other is a conversation about a plan."),
 ("Why does the script insist on probing several channels?",
  "Because one channel cannot distinguish deletion from silence. An empty window means either that the content was removed or that nobody posted, and a channel that was busy last year and quiet this spring produces a perfect-looking boundary that is entirely fictional. Two channels stopping at the same age is a workspace setting. Two channels stopping at different ages is two quiet channels, and the script says so rather than picking the more alarming reading."),
 ("What should we actually do about it?",
  "Stop treating Slack as the archive. Copy what matters into your own store at ingestion time - message text with its ts, and file bytes through the authenticated download - so that your record is yours rather than a view onto someone else's retention setting. Then get the configured number from an admin and write it down as the maximum lookback your app is allowed to assume. Where retention is a compliance obligation, that is what Enterprise Grid's Discovery and audit surfaces exist for."),
],
"related": [
 ("/slack/file-deleted-link-rot/", "one file deleted while the message that carried it survives"),
 ("/slack/file-download-without-auth/", "copying the bytes out, and the header that has to be on the request"),
 ("/slack/non-marketplace-history-clamp/", "the other reason a history read comes back short"),
],
"citations": [CITE_CONV_HISTORY, CITE_FILES_LIST, CITE_RETRIEVING, CITE_FILES_INFO],
})

GUIDES.append({
"slug": "socket-mode-and-request-url-both-on",
"title": "Socket Mode and a Request URL both switched on",
"description": "Socket Mode hides the Request URL, it does not clear it. One app configuration serves every environment, so whichever process is connected takes the events.",
"h1": "Socket Mode and a Request URL both switched on",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack socket mode and request url both configured",
             "slack events handled twice locally",
             "slack app dev and prod same app id",
             "slack socket_mode_enabled request_url manifest",
             "slack no environments separate apps"],
"deps": "Python 3.9+ with requests, or Node.js 18+; an app configuration token for the manifest read, and optionally a bot token with channels:history",
"lead": "Two people are debugging the same incident from opposite ends. One says the bot replied twice to a single mention. The other, running the app on her laptop, says her local console is full of production events that have nothing to do with what she is working on, and that <em>staging</em> has been silent since Tuesday.</p><p>Both are describing the same thing. There is one Slack app here, not three, and one app has one configuration: one Socket Mode switch, one Request URL, one set of subscriptions, shared by every environment that happens to be running.",
"short_answer": """<p>Slack has <strong>no notion of environments</strong>. An app is a single configuration with a single delivery path, and turning Socket Mode on moves delivery to the WebSocket. The Request URL you configured before that is <strong>still stored in the manifest</strong> &mdash; the screen stops showing it, nothing clears it, and it becomes live again the instant somebody switches Socket Mode off.</p>
<p>The read is two fields held together. <code>apps.manifest.export?app_id=A...</code> gives you <code>settings.socket_mode_enabled</code> alongside <code>settings.event_subscriptions.request_url</code>, <code>settings.interactivity.request_url</code> and the <code>url</code> on every slash command. <strong>Socket Mode on plus a stored URL is the finding</strong>, and the stored URL is usually a tunnel that stopped existing months ago.</p>
<p>The damage is not really the stale string, though. It is that a developer running the app locally with the app-level token opens a connection <em>for the app</em>, and the app is the production app, so events belonging to the live workspace arrive on a laptop. When duplicates appear, the spacing tells you which kind you have: copies a second or two apart are <strong>two live handlers</strong>, and copies about a minute or five minutes apart are <a href="/slack/duplicate-processing-on-retry/">Slack retrying</a>, which is a different note with a different fix.</p>""",
"problem": """<p>The route in is always the same and always reasonable. The app is built for production with an HTTPS Request URL. Then somebody needs to develop against it, a public endpoint on a laptop is inconvenient, and Socket Mode is the documented answer &mdash; it is genuinely the right tool for developing behind a firewall. The switch gets flipped on the app that already exists, because creating a second app means a second set of tokens, a second manifest, a second install, and that is twenty minutes nobody has on a Tuesday.</p>
<p>From that moment the workspace's events go wherever the socket is. Production stops receiving anything and does not know it: no error, no failed delivery, no auto-disable, just a Request URL that nothing calls any more. Meanwhile the laptop receives real user interactions, and if the local build happens to post messages, it posts them into the real workspace with the real bot's name on them.</p>
<p>Then the switch gets flipped back before a release, or somebody else flips it, and everything inverts. The stored Request URL comes back to life, still pointing at whatever it pointed at when it was last edited, which for a lot of apps is a tunnel hostname from a laptop that has since been reimaged. Slack does not re-verify it and does not need to: it verified once, long ago, and that tick has never been re-examined since. That failure mode is <a href="/slack/http-or-dead-tunnel-request-url/">its own note</a>; what this one owns is the configuration that makes flipping between them possible at all.</p>
<p>The duplicate messages are what usually starts the investigation, and they send people to the wrong place. Slack does retry event deliveries, on a documented ladder, and there is a well-worn note about handling those idempotently. But two copies of a message arriving a second apart are not a retry &mdash; nothing in Slack's ladder is that fast &mdash; they are two processes that both received the same event and both acted on it. The gap between the copies is the discriminator, and it costs one <code>conversations.history</code> call to read.</p>""",
"why": """<p><strong>One app is one configuration, and that is the whole root cause.</strong> There is no environment dimension anywhere in the app model: not in the manifest, not in the tokens, not in the subscriptions. Every mitigation people invent &mdash; feature flags, environment checks in the handler, only running the dev process sometimes &mdash; is working around the absence of something Slack does not have.</p>
<p><strong>Socket Mode hides the Request URL rather than clearing it.</strong> The field disappears from the configuration screen, which reads as removed, and the manifest still carries the string. That gap between what the screen shows and what the configuration holds is exactly why this has to be read from the manifest and cannot be checked by looking at the app page.</p>
<p><strong>A socket is opened for the app, not for an environment.</strong> The app-level token belongs to the app, so any process holding it can connect and start consuming the workspace's events. A laptop is not a subscriber to a subset; it is a peer of production, and Slack will happily deliver to it.</p>
<p><strong>The spacing between duplicates is the discriminator.</strong> Two live handlers produce copies seconds apart with different message ids. Slack's own retries arrive on a ladder measured in minutes. Reading the gap decides which note you are in, and the script names the retry case explicitly so it can be handed off rather than half-fixed here.</p>
<p><strong>A stored URL under Socket Mode is dormant rather than broken today.</strong> It delivers nothing right now, which is why nothing alerts on it, and it is one switch away from being the only delivery path again. The script reports it as a finding for that reason and says plainly that it is not currently receiving anything.</p>
<p><strong>The repair is two apps, and that is the supported pattern.</strong> A development app with Socket Mode on and no Request URL, a production app with an HTTPS Request URL and Socket Mode off, two manifests, two app ids, two token sets. It is more setup than a switch and it is the only configuration where flipping one does not change the other.</p>""",
"steps": [
 {"h": "Export the manifest, because the app page will not show you this",
  "body": """<p>The Request URL fields are hidden while Socket Mode is on, so the screen cannot answer the question. <code>apps.manifest.export</code> with an <strong>app configuration token</strong> can, and so can a manifest JSON you downloaded yourself and pass with <code>--manifest</code>. A bot token cannot read app configuration at all.</p>"""},
 {"h": "Walk every surface that stores a URL, not just the events one",
  "body": """<p><code>configured_urls</code> returns the event subscriptions URL, the interactivity URL, the menu options URL and the URL on each slash command. Slash commands are where the forgotten tunnel hostnames live, because nobody thinks of a slash command as part of the event configuration.</p>"""},
 {"h": "Hold the socket switch and the stored URLs in one verdict",
  "body": """<p><code>delivery_state</code> returns <code>both</code>, <code>socket-only</code>, <code>http-only</code>, <code>neither</code> or <code>unreadable</code>. <code>both</code> is the finding. <code>neither</code> is worth its own name: an app with no socket and no URL is inert and nothing has been delivered to it since it was created.</p>"""},
 {"h": "Say which app id each environment is actually using",
  "body": """<p><code>environment_shape</code> takes the app ids your environments run against, which you pass with <code>--apps dev=A01...,prod=A02...</code>. <code>shared-app</code> is the root cause in one word: the environments are not separate systems, they are the same registration seen from different machines.</p>"""},
 {"h": "Measure the gap between duplicates before blaming retries",
  "body": """<p><code>gap_shape</code> takes the timestamps of identical app-authored messages and returns <code>simultaneous</code>, <code>retry-shaped</code>, <code>unexplained</code> or <code>single</code>. Anything at a second or two is two live handlers; a minute or five minutes is Slack's retry ladder and belongs to the retry note.</p>"""},
 {"h": "Split the app in two rather than coordinating the switch",
  "body": """<p>The printed repair is a second Slack app for development, with Socket Mode on and no Request URL, and production left on HTTPS with Socket Mode off. Creating apps and editing manifests are writes; this script prints the plan and performs none of it.</p>"""},
],
"verify": """<p>After the split, the production manifest should have a URL and no socket, and the development manifest a socket and no URL. Run it against both.</p>
<pre><code class="language-bash">python3 slack_delivery_paths.py --manifest prod-app.json --apps dev=A01DEV9QT,prod=A01DEV9QT \\
    --channel C01ENG9QT
# manifest   socket mode on, 3 stored Request URL(s)
# url        event subscriptions   https://a1b2c3.ngrok.io/slack/events
# url        interactivity         https://a1b2c3.ngrok.io/slack/interact
# url        slash /deploy         https://hooks.acme.example/slack/deploy
# paths      both           Socket Mode is on and 3 Request URL(s) are still stored.
#                           They deliver nothing today and become live the moment the
#                           socket is switched off
# apps       shared-app     dev and prod run against the same app id, so they share one
#                           configuration and one delivery path
# duplicate  simultaneous   two copies 1.4s apart: Slack's retry ladder is never this
#                           fast, so two handlers both acted on one event
# verdict    collision      one configuration, both delivery paths, every environment
#   repair: create a second Slack app for development, Socket Mode on, no Request URL
#   repair: leave production on HTTPS with Socket Mode off, and never flip either</code></pre>""",
"code_intro": "One manifest read, one optional history read, and five pure functions. <code>configured_urls</code> exists because the slash commands are the surfaces everyone forgets. <code>delivery_state</code> is the two-field cross that is the whole finding. <code>environment_shape</code> names the root cause rather than the symptom. <code>gap_shape</code> is the measurement that keeps this note out of the retry note's territory, and <code>finding</code> is the small matrix that combines what is configured with what was observed.",
"py_file": "slack_delivery_paths.py",
"py": '''"""Find the app that has both delivery mechanisms configured at once.

Read only. apps.manifest.export and conversations.history are reads; nothing
here edits a manifest, creates an app, opens a socket or sends anything to a
Request URL. Every repair is printed.

Slack has no environments. One app is one configuration: one Socket Mode
switch, one Request URL, one set of subscriptions, shared by every process that
holds the app's credentials. Turning Socket Mode on moves delivery to the
socket and leaves the Request URL stored, hidden on the configuration screen
and still present in the manifest.
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_delivery_paths")

API = "https://slack.com/api/"

# Slack's event retry ladder, roughly: a minute, five minutes, an hour. Bands
# rather than points, because the delay is approximate and the only thing that
# matters is telling a retry apart from a second live handler.
RETRY_BANDS = ((25.0, 95.0), (240.0, 360.0), (3300.0, 3900.0))
# Above this, two copies are too far apart to be two handlers reacting to one
# delivery. Below it, no retry ladder is ever that fast.
TOGETHER = 2.0


def configured_urls(manifest):
    """Every Request URL stored in this app's configuration. Pure.

    Returns [(surface, url), ...]. The events URL is the one everybody checks
    and the slash commands are the ones that keep a hostname from somebody's
    laptop for years, because nobody thinks of a slash command as part of the
    event configuration.
    """
    m = manifest if isinstance(manifest, dict) else {}
    settings = m.get("settings") if isinstance(m.get("settings"), dict) else {}
    events = settings.get("event_subscriptions")
    inter = settings.get("interactivity")
    out = []
    if isinstance(events, dict) and events.get("request_url"):
        out.append(("event subscriptions", str(events["request_url"])))
    if isinstance(inter, dict):
        if inter.get("request_url"):
            out.append(("interactivity", str(inter["request_url"])))
        if inter.get("message_menu_options_url"):
            out.append(("menu options", str(inter["message_menu_options_url"])))
    features = m.get("features") if isinstance(m.get("features"), dict) else {}
    for cmd in features.get("slash_commands") or []:
        if isinstance(cmd, dict) and cmd.get("url"):
            out.append(("slash %s" % (cmd.get("command") or "?"), str(cmd["url"])))
    return out


def delivery_state(manifest):
    """How many ways can events reach this app? Pure.

    Returns (state, detail, urls). both is the finding: Socket Mode carries the
    traffic today and the stored URLs become the delivery path again the moment
    somebody switches it off, without anything being edited or re-verified.
    """
    if not isinstance(manifest, dict) or not manifest:
        return ("unreadable", "no manifest was supplied, and a bot token cannot read "
                              "app configuration", [])
    settings = manifest.get("settings") if isinstance(manifest.get("settings"),
                                                      dict) else {}
    socket = bool(settings.get("socket_mode_enabled"))
    urls = configured_urls(manifest)
    if socket and urls:
        return ("both", "Socket Mode is on and %d Request URL(s) are still stored. "
                        "They deliver nothing today and become live the moment the "
                        "socket is switched off" % len(urls), urls)
    if socket:
        return ("socket-only", "Socket Mode is on and no Request URL is stored, which "
                               "is one delivery path and no ambiguity", urls)
    if urls:
        return ("http-only", "delivery is over HTTPS to %d configured URL(s) and "
                             "Socket Mode is off" % len(urls), urls)
    return ("neither", "no Socket Mode and no Request URL. Nothing has ever been "
                       "delivered to this app", urls)


def environment_shape(app_ids):
    """Do your environments share one app registration? Pure.

    app_ids maps an environment name to the app id it runs against. shared-app
    is the root cause of this note stated in one word: the environments are not
    separate systems, they are one registration seen from different machines.
    """
    rows = {k: str(v or "").strip() for k, v in (app_ids or {}).items()}
    rows = {k: v for k, v in rows.items() if v}
    if not rows:
        return ("unknown", "no app ids were supplied, so the environments cannot be "
                           "compared")
    if len(rows) < 2:
        return ("single-environment", "only one environment was named, so there is "
                                      "nothing to share")
    distinct = sorted(set(rows.values()))
    if len(distinct) == 1:
        return ("shared-app", "%s run against the same app id, so they share one "
                              "configuration and one delivery path"
                              % " and ".join(sorted(rows)))
    if len(distinct) == len(rows):
        return ("separate-apps", "%d environment(s), %d app id(s): each one has its own "
                                 "configuration" % (len(rows), len(distinct)))
    return ("partly-shared", "%d environment(s) across %d app id(s), so at least two of "
                             "them share a configuration" % (len(rows), len(distinct)))


def gap_shape(timestamps):
    """Two copies of one message: what does the spacing say? Pure.

    Returns (shape, seconds, detail). This is the boundary against the retry
    note. Slack's retry ladder is measured in minutes, so anything at a second
    or two is two processes that both received the same event, and that is a
    delivery-path problem rather than an idempotency one.
    """
    values = []
    for t in timestamps or []:
        try:
            values.append(float(t))
        except (TypeError, ValueError):
            continue
    values.sort()
    if len(values) < 2:
        return ("single", 0.0, "one copy, so there is nothing to compare")
    gap = round(min(b - a for a, b in zip(values, values[1:])), 1)
    if gap <= TOGETHER:
        return ("simultaneous", gap, "two copies %.1fs apart. Slack's retry ladder is "
                                     "never this fast, so two handlers both acted on "
                                     "one event" % gap)
    for low, high in RETRY_BANDS:
        if low <= gap <= high:
            return ("retry-shaped", gap, "two copies %.1fs apart, which is Slack "
                                         "retrying a delivery it thinks failed. That "
                                         "is an idempotency problem, not this one"
                                         % gap)
    return ("unexplained", gap, "two copies %.1fs apart, which matches neither two live "
                                "handlers nor the retry ladder. Look at your own "
                                "scheduling" % gap)


def finding(state, env, shape):
    """Cross what is configured with what was observed. Pure.

    Returns (verdict, detail). collision is the strongest form and the only one
    where all three inputs agree; two-listeners is the same conclusion reached
    from evidence when the manifest was not available.
    """
    if state == "unreadable":
        return ("unreadable", "without the manifest the configuration half of this "
                              "check is missing, and only the duplicates can speak")
    if state == "both" and env == "shared-app":
        return ("collision", "one configuration, both delivery paths, and every "
                             "environment running against it. This is the whole note "
                             "in one app")
    if state == "both":
        return ("stale-url", "Socket Mode carries the traffic and the stored Request "
                             "URL is dormant. It is one switch away from being the "
                             "only delivery path again")
    if state == "neither":
        return ("inert", "no delivery path is configured at all, so nothing reaches "
                         "this app by any route")
    if shape == "simultaneous":
        return ("two-listeners", "the manifest looks clean and two processes are still "
                                 "acting on the same event. Two instances are sharing "
                                 "one app's credentials")
    if shape == "retry-shaped":
        return ("retries", "the duplicates are on Slack's retry ladder, which is a "
                           "different note and a different repair")
    if env == "shared-app":
        return ("shared-config", "one delivery path today, and every environment on one "
                                 "app id. Nothing is duplicated yet and one switch "
                                 "changes that")
    return ("clear", "one delivery path, and nothing suggesting a second listener")


def load_manifest(args):
    """From a file, or from apps.manifest.export with a configuration token."""
    if args.manifest:
        raw = json.loads(open(args.manifest, encoding="utf-8").read())
        return raw.get("manifest", raw)
    token = os.environ.get(args.config_token_env)
    if not token or not args.app_id:
        log.warning("manifest   supply --manifest, or set %s and pass --app-id; a bot "
                    "token cannot read app configuration", args.config_token_env)
        return None
    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + token})
    body = s.get(API + "apps.manifest.export", timeout=30,
                 params={"app_id": args.app_id}).json()
    if body.get("ok") is not True:
        log.error("manifest   unavailable    %s", body.get("error"))
        return None
    return body.get("manifest") or {}


def duplicate_gaps(session, channel, limit=200):
    """Timestamps of identical app-authored messages in one channel. A read."""
    body = session.get(API + "conversations.history", timeout=30,
                       params={"channel": channel, "limit": str(limit)}).json()
    if body.get("ok") is not True:
        log.warning("history    unavailable    %s", body.get("error"))
        return []
    groups = {}
    for m in body.get("messages") or []:
        if not m.get("bot_id") and not m.get("app_id"):
            continue
        key = (m.get("bot_id") or m.get("app_id"), (m.get("text") or "").strip())
        if not key[1]:
            continue
        groups.setdefault(key, []).append(m.get("ts"))
    return [ts for ts in groups.values() if len(ts) > 1]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", default="", help="path to an exported manifest")
    ap.add_argument("--config-token-env", default="SLACK_CONFIG_TOKEN",
                    help="environment variable holding an app configuration token")
    ap.add_argument("--app-id", default="", help="app id, for the manifest read")
    ap.add_argument("--apps", default="",
                    help="environment=app_id pairs, comma separated")
    ap.add_argument("--channel", default="",
                    help="a channel to read for duplicate app-authored messages")
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN",
                    help="environment variable holding a bot token, for the history read")
    args = ap.parse_args()

    manifest = load_manifest(args)
    state, detail, urls = delivery_state(manifest)
    if manifest is not None:
        settings = (manifest or {}).get("settings") or {}
        log.info("manifest   socket mode %s, %d stored Request URL(s)",
                 "on" if settings.get("socket_mode_enabled") else "off", len(urls))
    for surface, url in urls:
        log.info("url        %-21s %s", surface, url)
    (log.warning if state in ("both", "neither") else log.info)(
        "paths      %-14s %s", state, detail)

    pairs = {}
    for chunk in args.apps.split(","):
        if "=" in chunk:
            name, value = chunk.split("=", 1)
            pairs[name.strip()] = value.strip()
    env, env_detail = environment_shape(pairs)
    (log.warning if env in ("shared-app", "partly-shared") else log.info)(
        "apps       %-14s %s", env, env_detail)

    shape = "single"
    if args.channel:
        token = os.environ.get(args.token_env)
        if not token:
            log.warning("history    set %s to read duplicates", args.token_env)
        else:
            s = requests.Session()
            s.headers.update({"Authorization": "Bearer " + token})
            for group in duplicate_gaps(s, args.channel):
                shape, _gap, gap_detail = gap_shape(group)
                (log.warning if shape == "simultaneous" else log.info)(
                    "duplicate  %-14s %s", shape, gap_detail)
                if shape == "simultaneous":
                    break

    verdict, why = finding(state, env, shape)
    if verdict in ("collision", "two-listeners", "stale-url", "inert"):
        log.warning("verdict    %-14s %s", verdict, why)
        log.warning("  repair: create a second Slack app for development, with Socket "
                    "Mode on and no Request URL of any kind")
        log.warning("  repair: leave production on HTTPS with Socket Mode off, so no "
                    "switch on one app can move where events are delivered")
        log.warning("  repair: give each app its own bot token, app-level token and "
                    "signing secret; Slack has no environments, so two apps is the "
                    "separation")
        return 1
    log.info("verdict    %-14s %s", verdict, why)
    return 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-delivery-paths.mjs",
"js": '''/**
 * Find the app that has both delivery mechanisms configured at once.
 *
 * Read only. apps.manifest.export and conversations.history are reads; nothing
 * here edits a manifest, creates an app, opens a socket or sends anything to a
 * Request URL.
 *
 * Slack has no environments. One app is one configuration, shared by every
 * process holding the app's credentials, and turning Socket Mode on moves
 * delivery to the socket while leaving the Request URL stored in the manifest.
 */

import { readFileSync } from 'node:fs';

const API = 'https://slack.com/api/';

/** Slack's retry ladder, roughly: a minute, five minutes, an hour. */
export const RETRY_BANDS = [[25, 95], [240, 360], [3300, 3900]];
/** Below this, no retry ladder is ever that fast: it is two live handlers. */
export const TOGETHER = 2;

/**
 * Every Request URL stored in this app's configuration. Pure.
 * The slash commands are the surfaces that keep a laptop hostname for years,
 * because nobody thinks of a slash command as part of event configuration.
 */
export function configuredUrls(manifest) {
  const m = (manifest && typeof manifest === 'object') ? manifest : {};
  const settings = (m.settings && typeof m.settings === 'object') ? m.settings : {};
  const events = settings.event_subscriptions;
  const inter = settings.interactivity;
  const out = [];
  if (events && typeof events === 'object' && events.request_url) {
    out.push(['event subscriptions', String(events.request_url)]);
  }
  if (inter && typeof inter === 'object') {
    if (inter.request_url) out.push(['interactivity', String(inter.request_url)]);
    if (inter.message_menu_options_url) {
      out.push(['menu options', String(inter.message_menu_options_url)]);
    }
  }
  const features = (m.features && typeof m.features === 'object') ? m.features : {};
  for (const cmd of features.slash_commands ?? []) {
    if (cmd && typeof cmd === 'object' && cmd.url) {
      out.push([`slash ${cmd.command ?? '?'}`, String(cmd.url)]);
    }
  }
  return out;
}

/**
 * How many ways can events reach this app? Pure. Returns [state, detail, urls].
 * both is the finding: the stored URLs deliver nothing today and become the
 * delivery path again the moment the socket is switched off.
 */
export function deliveryState(manifest) {
  if (!manifest || typeof manifest !== 'object' || !Object.keys(manifest).length) {
    return ['unreadable', 'no manifest was supplied, and a bot token cannot read app '
      + 'configuration', []];
  }
  const settings = (manifest.settings && typeof manifest.settings === 'object')
    ? manifest.settings : {};
  const socket = Boolean(settings.socket_mode_enabled);
  const urls = configuredUrls(manifest);
  if (socket && urls.length) {
    return ['both', `Socket Mode is on and ${urls.length} Request URL(s) are still `
      + 'stored. They deliver nothing today and become live the moment the socket is '
      + 'switched off', urls];
  }
  if (socket) {
    return ['socket-only', 'Socket Mode is on and no Request URL is stored, which is '
      + 'one delivery path and no ambiguity', urls];
  }
  if (urls.length) {
    return ['http-only', `delivery is over HTTPS to ${urls.length} configured URL(s) `
      + 'and Socket Mode is off', urls];
  }
  return ['neither', 'no Socket Mode and no Request URL. Nothing has ever been '
    + 'delivered to this app', urls];
}

/**
 * Do your environments share one app registration? Pure.
 * shared-app is the root cause in one word: the environments are not separate
 * systems, they are one registration seen from different machines.
 */
export function environmentShape(appIds) {
  const rows = {};
  for (const [k, v] of Object.entries(appIds ?? {})) {
    const id = String(v ?? '').trim();
    if (id) rows[k] = id;
  }
  const names = Object.keys(rows);
  if (!names.length) {
    return ['unknown', 'no app ids were supplied, so the environments cannot be '
      + 'compared'];
  }
  if (names.length < 2) {
    return ['single-environment', 'only one environment was named, so there is nothing '
      + 'to share'];
  }
  const distinct = [...new Set(Object.values(rows))];
  if (distinct.length === 1) {
    return ['shared-app', `${names.sort().join(' and ')} run against the same app id, `
      + 'so they share one configuration and one delivery path'];
  }
  if (distinct.length === names.length) {
    return ['separate-apps', `${names.length} environment(s), ${distinct.length} app `
      + 'id(s): each one has its own configuration'];
  }
  return ['partly-shared', `${names.length} environment(s) across ${distinct.length} `
    + 'app id(s), so at least two of them share a configuration'];
}

/**
 * Two copies of one message: what does the spacing say? Pure.
 * The boundary against the retry note: Slack's ladder is measured in minutes,
 * so a gap of a second or two is two processes that both got the same event.
 */
export function gapShape(timestamps) {
  const values = (timestamps ?? []).map(Number).filter(Number.isFinite)
    .sort((a, b) => a - b);
  if (values.length < 2) {
    return ['single', 0, 'one copy, so there is nothing to compare'];
  }
  let smallest = Infinity;
  for (let i = 1; i < values.length; i += 1) {
    smallest = Math.min(smallest, values[i] - values[i - 1]);
  }
  const gap = Math.round(smallest * 10) / 10;
  if (gap <= TOGETHER) {
    return ['simultaneous', gap, `two copies ${gap.toFixed(1)}s apart. Slack's retry `
      + 'ladder is never this fast, so two handlers both acted on one event'];
  }
  for (const [low, high] of RETRY_BANDS) {
    if (gap >= low && gap <= high) {
      return ['retry-shaped', gap, `two copies ${gap.toFixed(1)}s apart, which is Slack `
        + 'retrying a delivery it thinks failed. That is an idempotency problem, not '
        + 'this one'];
    }
  }
  return ['unexplained', gap, `two copies ${gap.toFixed(1)}s apart, which matches `
    + 'neither two live handlers nor the retry ladder. Look at your own scheduling'];
}

/**
 * Cross what is configured with what was observed. Pure.
 * collision is the strongest form; two-listeners is the same conclusion
 * reached from evidence alone when the manifest was not available.
 */
export function finding(state, env, shape) {
  if (state === 'unreadable') {
    return ['unreadable', 'without the manifest the configuration half of this check is '
      + 'missing, and only the duplicates can speak'];
  }
  if (state === 'both' && env === 'shared-app') {
    return ['collision', 'one configuration, both delivery paths, and every environment '
      + 'running against it. This is the whole note in one app'];
  }
  if (state === 'both') {
    return ['stale-url', 'Socket Mode carries the traffic and the stored Request URL is '
      + 'dormant. It is one switch away from being the only delivery path again'];
  }
  if (state === 'neither') {
    return ['inert', 'no delivery path is configured at all, so nothing reaches this '
      + 'app by any route'];
  }
  if (shape === 'simultaneous') {
    return ['two-listeners', 'the manifest looks clean and two processes are still '
      + 'acting on the same event. Two instances are sharing one app credentials'];
  }
  if (shape === 'retry-shaped') {
    return ['retries', 'the duplicates are on Slack retry ladder, which is a different '
      + 'note and a different repair'];
  }
  if (env === 'shared-app') {
    return ['shared-config', 'one delivery path today, and every environment on one app '
      + 'id. Nothing is duplicated yet and one switch changes that'];
  }
  return ['clear', 'one delivery path, and nothing suggesting a second listener'];
}

function arg(args, name, fallback = null) {
  const i = args.indexOf(name);
  return i === -1 ? fallback : args[i + 1];
}

async function loadManifest(args) {
  const path = arg(args, '--manifest', '');
  if (path) {
    const raw = JSON.parse(readFileSync(path, 'utf-8'));
    return raw.manifest ?? raw;
  }
  const tokenEnv = arg(args, '--config-token-env', 'SLACK_CONFIG_TOKEN');
  const token = process.env[tokenEnv];
  const appId = arg(args, '--app-id', '');
  if (!token || !appId) {
    console.warn(`manifest   supply --manifest, or set ${tokenEnv} and pass --app-id; a `
      + 'bot token cannot read app configuration');
    return null;
  }
  const params = new URLSearchParams({ app_id: appId });
  const body = await (await fetch(`${API}apps.manifest.export?${params}`,
    { headers: { Authorization: `Bearer ${token}` } })).json();
  if (body.ok !== true) {
    console.error(`manifest   unavailable    ${body.error}`);
    return null;
  }
  return body.manifest ?? {};
}

async function duplicateGaps(headers, channel, limit = 200) {
  const params = new URLSearchParams({ channel, limit: String(limit) });
  const body = await (await fetch(`${API}conversations.history?${params}`,
    { headers })).json();
  if (body.ok !== true) {
    console.warn(`history    unavailable    ${body.error}`);
    return [];
  }
  const groups = new Map();
  for (const m of body.messages ?? []) {
    if (!m.bot_id && !m.app_id) continue;
    const text = (m.text ?? '').trim();
    if (!text) continue;
    const key = `${m.bot_id ?? m.app_id}::${text}`;
    groups.set(key, [...(groups.get(key) ?? []), m.ts]);
  }
  return [...groups.values()].filter((ts) => ts.length > 1);
}

async function main() {
  const args = process.argv.slice(2);
  const manifest = await loadManifest(args);
  const [state, detail, urls] = deliveryState(manifest);
  if (manifest) {
    const settings = manifest.settings ?? {};
    console.log(`manifest   socket mode ${settings.socket_mode_enabled ? 'on' : 'off'}, `
      + `${urls.length} stored Request URL(s)`);
  }
  for (const [surface, url] of urls) {
    console.log(`url        ${surface.padEnd(21)} ${url}`);
  }
  const pathLine = `paths      ${state.padEnd(14)} ${detail}`;
  if (state === 'both' || state === 'neither') console.warn(pathLine);
  else console.log(pathLine);

  const pairs = {};
  for (const chunk of (arg(args, '--apps', '') ?? '').split(',')) {
    const at = chunk.indexOf('=');
    if (at !== -1) pairs[chunk.slice(0, at).trim()] = chunk.slice(at + 1).trim();
  }
  const [env, envDetail] = environmentShape(pairs);
  const envLine = `apps       ${env.padEnd(14)} ${envDetail}`;
  if (env === 'shared-app' || env === 'partly-shared') console.warn(envLine);
  else console.log(envLine);

  let shape = 'single';
  const channel = arg(args, '--channel', '');
  if (channel) {
    const tokenEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
    const token = process.env[tokenEnv];
    if (!token) {
      console.warn(`history    set ${tokenEnv} to read duplicates`);
    } else {
      const headers = { Authorization: `Bearer ${token}` };
      for (const group of await duplicateGaps(headers, channel)) {
        const [got, , gapDetail] = gapShape(group);
        shape = got;
        const dupLine = `duplicate  ${got.padEnd(14)} ${gapDetail}`;
        if (got === 'simultaneous') { console.warn(dupLine); break; }
        console.log(dupLine);
      }
    }
  }

  const [verdict, why] = finding(state, env, shape);
  if (['collision', 'two-listeners', 'stale-url', 'inert'].includes(verdict)) {
    console.warn(`verdict    ${verdict.padEnd(14)} ${why}`);
    console.warn('  repair: create a second Slack app for development, with Socket Mode '
      + 'on and no Request URL of any kind');
    console.warn('  repair: leave production on HTTPS with Socket Mode off, so no '
      + 'switch on one app can move where events are delivered');
    process.exitCode = 1;
    return;
  }
  console.log(`verdict    ${verdict.padEnd(14)} ${why}`);
}

// Only run when invoked directly, so importing this module in the tests does
// not execute main() and fail the file on a missing manifest.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The tests are mostly about the two boundaries this note has with its neighbours. <code>gap_shape</code> is asserted at a second and a half and again at sixty seconds, because that difference is the entire line between this note and the retry one, and getting it wrong sends somebody to write idempotency code for a problem that is really two processes. The other set is about the manifest shape: a slash command URL has to count as a stored delivery path, since it is the surface that keeps a dead tunnel hostname longest, and an empty manifest has to come back <code>unreadable</code> rather than <code>neither</code>.",
"test_py_file": "test_slack_delivery_paths.py",
"test_py": '''from slack_delivery_paths import (configured_urls, delivery_state,
                                  environment_shape, finding, gap_shape)

SOCKET_AND_URL = {
    "settings": {
        "socket_mode_enabled": True,
        "event_subscriptions": {"request_url": "https://a1.ngrok.io/slack/events"},
    },
}


def test_every_surface_that_stores_a_url_is_walked():
    got = configured_urls({
        "settings": {
            "event_subscriptions": {"request_url": "https://acme.dev/e"},
            "interactivity": {"request_url": "https://acme.dev/i",
                              "message_menu_options_url": "https://acme.dev/o"},
        },
        "features": {"slash_commands": [{"command": "/deploy",
                                         "url": "https://acme.dev/d"}]},
    })
    assert [name for name, _url in got] == ["event subscriptions", "interactivity",
                                            "menu options", "slash /deploy"]


def test_a_slash_command_url_counts_as_a_stored_delivery_path():
    m = {"settings": {"socket_mode_enabled": True},
         "features": {"slash_commands": [{"command": "/x", "url": "https://acme.dev/x"}]}}
    assert delivery_state(m)[0] == "both"


def test_an_empty_manifest_is_unreadable_rather_than_empty_of_paths():
    assert delivery_state({})[0] == "unreadable"
    assert delivery_state(None)[0] == "unreadable"


def test_socket_mode_with_a_stored_url_is_the_finding():
    state, detail, urls = delivery_state(SOCKET_AND_URL)
    assert state == "both"
    assert len(urls) == 1
    assert "switched off" in detail


def test_socket_mode_alone_is_one_path_and_no_ambiguity():
    assert delivery_state({"settings": {"socket_mode_enabled": True}})[0] == \\
        "socket-only"


def test_an_https_url_without_socket_mode_is_the_ordinary_shape():
    m = {"settings": {"event_subscriptions": {"request_url": "https://acme.dev/e"}}}
    assert delivery_state(m)[0] == "http-only"


def test_no_socket_and_no_url_means_nothing_is_delivered_at_all():
    assert delivery_state({"settings": {}})[0] == "neither"


def test_two_environments_on_one_app_id_is_the_root_cause():
    verdict, detail = environment_shape({"dev": "A01", "prod": "A01"})
    assert verdict == "shared-app"
    assert "one configuration" in detail


def test_two_environments_with_their_own_apps_are_separate():
    assert environment_shape({"dev": "A01", "prod": "A02"})[0] == "separate-apps"


def test_three_environments_sharing_two_apps_are_partly_shared():
    assert environment_shape({"dev": "A01", "stg": "A01",
                              "prod": "A02"})[0] == "partly-shared"


def test_one_environment_or_none_decides_nothing():
    assert environment_shape({"prod": "A01"})[0] == "single-environment"
    assert environment_shape({})[0] == "unknown"
    assert environment_shape({"prod": ""})[0] == "unknown"


def test_copies_a_second_apart_are_two_handlers_not_a_retry():
    shape, gap, detail = gap_shape(["1000.000100", "1001.400100"])
    assert shape == "simultaneous"
    assert gap == 1.4
    assert "two handlers" in detail


def test_copies_a_minute_apart_belong_to_the_retry_note():
    shape, _gap, detail = gap_shape(["1000.000100", "1060.000100"])
    assert shape == "retry-shaped"
    assert "idempotency" in detail


def test_the_five_minute_rung_is_also_a_retry():
    assert gap_shape(["1000.0", "1300.0"])[0] == "retry-shaped"


def test_a_gap_matching_nothing_is_left_unexplained():
    assert gap_shape(["1000.0", "1010.0"])[0] == "unexplained"


def test_one_copy_is_not_a_duplicate():
    assert gap_shape(["1000.0"])[0] == "single"
    assert gap_shape([])[0] == "single"
    assert gap_shape(["not-a-ts", "1000.0"])[0] == "single"


def test_the_smallest_gap_in_a_group_is_the_one_that_decides():
    assert gap_shape(["1000.0", "1060.0", "1061.0"])[0] == "simultaneous"


def test_both_paths_on_one_shared_app_is_the_whole_note():
    verdict, detail = finding("both", "shared-app", "simultaneous")
    assert verdict == "collision"
    assert "every environment" in detail


def test_both_paths_without_the_environment_evidence_is_still_a_finding():
    assert finding("both", "unknown", "single")[0] == "stale-url"


def test_duplicates_alone_still_reach_the_same_conclusion():
    assert finding("socket-only", "unknown", "simultaneous")[0] == "two-listeners"


def test_a_retry_shaped_duplicate_is_handed_to_the_other_note():
    assert finding("http-only", "separate-apps", "retry-shaped")[0] == "retries"


def test_a_clean_app_says_so():
    assert finding("http-only", "separate-apps", "single")[0] == "clear"
    assert finding("unreadable", "unknown", "single")[0] == "unreadable"
''',
"test_js_file": "slack-delivery-paths.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  configuredUrls, deliveryState, environmentShape, finding, gapShape,
} from './slack-delivery-paths.mjs';

const SOCKET_AND_URL = {
  settings: {
    socket_mode_enabled: true,
    event_subscriptions: { request_url: 'https://a1.ngrok.io/slack/events' },
  },
};

test('every surface that stores a url is walked', () => {
  const got = configuredUrls({
    settings: {
      event_subscriptions: { request_url: 'https://acme.dev/e' },
      interactivity: {
        request_url: 'https://acme.dev/i',
        message_menu_options_url: 'https://acme.dev/o',
      },
    },
    features: { slash_commands: [{ command: '/deploy', url: 'https://acme.dev/d' }] },
  });
  assert.deepEqual(got.map(([name]) => name),
    ['event subscriptions', 'interactivity', 'menu options', 'slash /deploy']);
});

test('a slash command url counts as a stored delivery path', () => {
  const m = {
    settings: { socket_mode_enabled: true },
    features: { slash_commands: [{ command: '/x', url: 'https://acme.dev/x' }] },
  };
  assert.equal(deliveryState(m)[0], 'both');
});

test('an empty manifest is unreadable rather than empty of paths', () => {
  assert.equal(deliveryState({})[0], 'unreadable');
  assert.equal(deliveryState(null)[0], 'unreadable');
});

test('socket mode with a stored url is the finding', () => {
  const [state, detail, urls] = deliveryState(SOCKET_AND_URL);
  assert.equal(state, 'both');
  assert.equal(urls.length, 1);
  assert.match(detail, /switched off/);
});

test('socket mode alone is one path and no ambiguity', () => {
  assert.equal(deliveryState({ settings: { socket_mode_enabled: true } })[0],
    'socket-only');
});

test('an https url without socket mode is the ordinary shape', () => {
  const m = { settings: { event_subscriptions: { request_url: 'https://acme.dev/e' } } };
  assert.equal(deliveryState(m)[0], 'http-only');
});

test('no socket and no url means nothing is delivered at all', () => {
  assert.equal(deliveryState({ settings: {} })[0], 'neither');
});

test('two environments on one app id is the root cause', () => {
  const [verdict, detail] = environmentShape({ dev: 'A01', prod: 'A01' });
  assert.equal(verdict, 'shared-app');
  assert.match(detail, /one configuration/);
});

test('two environments with their own apps are separate', () => {
  assert.equal(environmentShape({ dev: 'A01', prod: 'A02' })[0], 'separate-apps');
});

test('three environments sharing two apps are partly shared', () => {
  assert.equal(environmentShape({ dev: 'A01', stg: 'A01', prod: 'A02' })[0],
    'partly-shared');
});

test('one environment or none decides nothing', () => {
  assert.equal(environmentShape({ prod: 'A01' })[0], 'single-environment');
  assert.equal(environmentShape({})[0], 'unknown');
  assert.equal(environmentShape({ prod: '' })[0], 'unknown');
});

test('copies a second apart are two handlers not a retry', () => {
  const [shape, gap, detail] = gapShape(['1000.000100', '1001.400100']);
  assert.equal(shape, 'simultaneous');
  assert.equal(gap, 1.4);
  assert.match(detail, /two handlers/);
});

test('copies a minute apart belong to the retry note', () => {
  const [shape, , detail] = gapShape(['1000.000100', '1060.000100']);
  assert.equal(shape, 'retry-shaped');
  assert.match(detail, /idempotency/);
});

test('the five minute rung is also a retry', () => {
  assert.equal(gapShape(['1000.0', '1300.0'])[0], 'retry-shaped');
});

test('a gap matching nothing is left unexplained', () => {
  assert.equal(gapShape(['1000.0', '1010.0'])[0], 'unexplained');
});

test('one copy is not a duplicate', () => {
  assert.equal(gapShape(['1000.0'])[0], 'single');
  assert.equal(gapShape([])[0], 'single');
  assert.equal(gapShape(['not-a-ts', '1000.0'])[0], 'single');
});

test('the smallest gap in a group is the one that decides', () => {
  assert.equal(gapShape(['1000.0', '1060.0', '1061.0'])[0], 'simultaneous');
});

test('both paths on one shared app is the whole note', () => {
  const [verdict, detail] = finding('both', 'shared-app', 'simultaneous');
  assert.equal(verdict, 'collision');
  assert.match(detail, /every environment/);
});

test('both paths without the environment evidence is still a finding', () => {
  assert.equal(finding('both', 'unknown', 'single')[0], 'stale-url');
});

test('duplicates alone still reach the same conclusion', () => {
  assert.equal(finding('socket-only', 'unknown', 'simultaneous')[0], 'two-listeners');
});

test('a retry shaped duplicate is handed to the other note', () => {
  assert.equal(finding('http-only', 'separate-apps', 'retry-shaped')[0], 'retries');
});

test('a clean app says so', () => {
  assert.equal(finding('http-only', 'separate-apps', 'single')[0], 'clear');
  assert.equal(finding('unreadable', 'unknown', 'single')[0], 'unreadable');
});
''',
"faq": [
 ("If Socket Mode is on, does Slack really still call my Request URL?",
  "No, and that is the trap rather than the relief. While Socket Mode is on, delivery goes down the WebSocket and the stored URL receives nothing, which is why nothing alerts and why the configuration can sit like this for a year. The URL is not gone though: it is still in the manifest, still verified from whenever it was last checked, and it becomes the only delivery path again the moment somebody turns the switch off. Dormant is not the same as removed."),
 ("Why not just add an environment check in the handler?",
  "Because the event has already been delivered to the wrong place by then. If a laptop holds the app-level token and opens a socket, Slack sends it real workspace events, and a check inside the handler can only decide to ignore them - production never receives them at all. The problem is at the delivery layer and no amount of code in the consumer moves it."),
 ("We see the bot replying twice. Is this the same as the retry problem?",
  "Measure the gap and you will know. Slack retries a delivery it believes failed on a ladder measured in minutes, so two copies about sixty seconds or five minutes apart are retries and want an idempotency key. Two copies a second or two apart cannot be retries - nothing in the ladder is that fast - and mean two processes both received the same event. The script reads the timestamps of identical app-authored messages and names which one you have."),
 ("Can I keep one app and just be careful about who runs what?",
  "You can, and it holds until the first time two people are working at once. The failure is not carelessness, it is that the configuration has no room to express two environments: one switch, one URL, one set of subscriptions, and every process holding the credentials is a peer. Two apps costs a second install and a second set of tokens, and it makes the failure structurally impossible rather than a matter of discipline."),
 ("Which app should keep the Request URL?",
  "Production, always, with Socket Mode off. The development app gets Socket Mode on and no Request URL at all, so there is nothing stored to become live later. Keeping a URL on the development app is how this comes back: somebody turns Socket Mode off to test something, a tunnel hostname from months ago wakes up, and the whole cycle starts again."),
],
"related": [
 ("/slack/duplicate-processing-on-retry/", "duplicates from Slack's retry ladder, minutes apart rather than seconds"),
 ("/slack/http-or-dead-tunnel-request-url/", "the tunnel hostname the stored URL usually turns out to be"),
 ("/slack/socket-mode-blocks-distribution/", "the other cost of the same delivery choice"),
],
"citations": [CITE_SOCKET_MODE, CITE_MANIFEST_EXPORT, CITE_SO_BOTH_ON, CITE_EVENTS_API],
})

GUIDES.append({
"slug": "socket-mode-blocks-distribution",
"title": "Socket Mode apps cannot be listed on the Marketplace",
"description": "Distribution needs a public HTTPS Request URL. Cross the manifest against your own install store before a customer asks for the app, not after.",
"h1": "Socket Mode apps cannot be listed on the Marketplace",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack socket mode marketplace rejected",
             "slack distribute socket mode app",
             "slack app public distribution request url",
             "socket mode vs events api distribution",
             "slack marketplace requirements http endpoint"],
"deps": "Python 3.9+ with requests, or Node.js 18+; an app configuration token for the manifest read, and your own installation records",
"lead": "The app has been running happily for a year. It was built on Socket Mode on the first afternoon, because Socket Mode is genuinely the fastest way from nothing to a working Slack app, and it has never given anybody a moment's trouble.</p><p>Then a customer asks whether they can install it in their workspace. Then two more do. Then somebody starts the Marketplace submission and discovers that the answer is not a form to fill in: the delivery architecture the app was built on is not one the Marketplace accepts, and the work is not a submission, it is a migration.",
"short_answer": """<p>Socket Mode apps <strong>cannot be listed on the Slack Marketplace</strong>. A publicly distributed app has to expose a public HTTPS Request URL and receive events over the Events API. Socket Mode exists for apps that live behind a firewall and for internal or org-deployed use, and that is a product boundary rather than a scope, a setting or anything you can negotiate in code.</p>
<p>Because the constraint is about the transport rather than the logic, it is readable ahead of time. <code>apps.manifest.export</code> gives you <code>settings.socket_mode_enabled</code>; your own OAuth configuration says whether the app is meant to leave this workspace; and <code>auth.test</code> across the installations you have stored says whether it <em>already</em> has, by counting distinct <code>team_id</code> values. <strong>Socket Mode plus more than one workspace is an app that is already distributed on a transport that cannot be listed.</strong></p>
<p>It compounds, too. Marketplace approval is also what lifts the <a href="/slack/non-marketplace-history-clamp/">clamp on <code>conversations.history</code></a> for non-Marketplace apps, so a Socket Mode app that reads history is held at the clamped limits with no route out that does not go through the same rewrite. And the false positive is worth stating plainly: Socket Mode in a single internal workspace is <strong>the supported use of the feature</strong> and must never be reported as a fault.</p>""",
"problem": """<p>The reason this catches good teams is that Socket Mode is the correct choice right up until the moment it is not, and nothing marks the moment. There is no deprecation warning, no <code>ok: false</code>, no rate limit, no email. The app works exactly as well on the day it becomes commercially interesting as it did on the day it was written, and the constraint only surfaces when somebody reads the distribution requirements, which is usually after a customer has been promised a date.</p>
<p>What makes it expensive is that the change is infrastructural rather than logical. Bolt supports both receivers, so most of the application code survives a move to HTTP unchanged. What does not survive is the deployment: an app that has never needed an inbound public endpoint now needs one, with TLS, a hostname, a load balancer if it matters, signature verification on every request, and a three-second response budget that a socket consumer never had to think about. That is a platform project appearing in the middle of a sales conversation.</p>
<p>The org-deployment case is the one people get wrong in the other direction. Socket Mode is allowed for apps deployed across an Enterprise Grid organisation, so an app installed in eleven workspaces inside one enterprise is not evidence of anything. Eleven workspaces across eleven <em>unrelated</em> enterprises is. The difference is <code>enterprise_id</code>, and a check that counts <code>team_id</code> alone reports the healthy Grid case as a violation.</p>
<p>Then there is the quiet compounding with rate limits. Slack tightened <code>conversations.history</code> for apps that are not on the Marketplace, and Marketplace listing is the route back to the old limits. An app on Socket Mode is not eligible for that listing, so if it polls history it is stuck at the clamped rate permanently, and the two problems have exactly one shared fix. Discovering them separately, six months apart, is how one architectural decision gets rediscovered twice.</p>""",
"why": """<p><strong>Eligibility is a fact about the transport, not about the code.</strong> Nothing in the handler, the scopes or the manifest's feature list moves it. That is what makes it checkable early and cheaply: two fields and a count, months before anybody opens the submission form.</p>
<p><strong>Intent is readable before it is acted on.</strong> An OAuth redirect configuration, org deployment being enabled, and a public install flow are all signs that the app is meant to leave this workspace. Crossing those with the socket switch turns "we might distribute this one day" into a decision with a known cost attached today.</p>
<p><strong>Installations you already hold are the strongest evidence there is.</strong> More than one unrelated <code>team_id</code> in your installation store means the app is distributed in fact, whatever the plan said. The script counts <code>enterprise_id</code> alongside it, because a Grid organisation is many workspaces and one customer.</p>
<p><strong>The correct use of Socket Mode must not be reported as a fault.</strong> One workspace, no redirect URLs, no distribution intent: that is the feature working as designed, and a checker that flags it teaches people to ignore the checker. <code>internal-fine</code> is a verdict here, printed as such.</p>
<p><strong>The clamp and the listing share one fix, so they should be found together.</strong> If the app reads <code>conversations.history</code>, the transport decision has already cost it the un-clamped rate limits as well as the listing. Reporting both at once is the difference between one architecture conversation and two.</p>
<p><strong>The migration is countable, so count it.</strong> Every surface that needs a public URL after the move &mdash; events, interactivity, options, each slash command &mdash; is in the manifest already. Printing that list turns "we would have to rewrite it" into a specific number of endpoints, which is a much better sentence to bring to a planning meeting.</p>""",
"steps": [
 {"h": "Read the socket switch out of the manifest, not out of memory",
  "body": """<p><code>apps.manifest.export</code> with an app configuration token, or a manifest JSON passed with <code>--manifest</code>. A bot token cannot read app configuration, so this is one of the few checks in this section that needs a second credential class.</p>"""},
 {"h": "Decide whether this app is even meant to leave the workspace",
  "body": """<p><code>distribution_intent</code> returns <code>distributed</code>, <code>preparing</code>, <code>internal</code> or <code>unreadable</code> from the OAuth redirect configuration and the org deployment flag. An internal app on Socket Mode is not a finding and the script has to be able to say so.</p>"""},
 {"h": "Count workspaces and enterprises, not just installs",
  "body": """<p><code>install_spread</code> takes the <code>auth.test</code> responses you already store per installation and separates <code>multi-workspace</code> from <code>grid-org</code>. Eleven workspaces in one enterprise is org deployment, which Socket Mode supports; eleven unrelated ones are distribution, which it does not.</p>"""},
 {"h": "Cross the transport with the intent",
  "body": """<p><code>eligibility</code> returns <code>blocked-and-shipped</code>, <code>blocked</code>, <code>org-only</code>, <code>internal-fine</code> or <code>eligible</code>. The first is the emergency: the app is already installed in unrelated workspaces on a transport that cannot be listed.</p>"""},
 {"h": "Add up the clamp while you are here",
  "body": """<p><code>clamp_exposure</code> asks whether the app reads <code>conversations.history</code>. If it does, the same transport decision has already cost it the un-clamped rate limits, and the two findings share one repair. Finding them separately, six months apart, is the expensive way.</p>"""},
 {"h": "Print the endpoints the migration needs, and change nothing",
  "body": """<p><code>migration_surfaces</code> lists every surface that will need a public URL. Editing a manifest, creating an app and submitting to the Marketplace are all writes and all human decisions; the script produces the list and stops.</p>"""},
],
"verify": """<p>After the migration the manifest has no socket and a URL on every surface, and the same command comes back <code>eligible</code>.</p>
<pre><code class="language-bash">python3 slack_distribution_block.py --manifest app.json --installs installs.json \\
    --reads-history
# manifest   socket mode on
# intent     preparing      an OAuth redirect configuration is present, so this app is
#                           set up to be installed somewhere other than here
# installs   multi-workspace  4 workspace(s) across 0 enterprise(s): they do not
#                           all share one enterprise, so this app is already distributed
# verdict    blocked-and-shipped  already installed in unrelated workspaces on a
#                           transport the Marketplace does not accept
# clamp      compounded     listing is also what lifts the conversations.history clamp,
#                           so the same rewrite is the only route to either
# migrate    needs-url      event subscriptions
# migrate    needs-url      interactivity
# migrate    needs-url      slash /report
#   repair: stand up a public HTTPS endpoint, configure the 3 surface(s) above
#   repair: switch Socket Mode off, re-verify, and keep it on a separate dev app</code></pre>""",
"code_intro": "A manifest read, your own installation records, and five pure functions that never touch the network. <code>distribution_intent</code> and <code>install_spread</code> answer the plan and the reality separately, because those disagree more often than anybody expects. <code>eligibility</code> is the cross, and it has a verdict for the case that is not a fault at all. <code>clamp_exposure</code> pulls in the rate-limit half of the same decision, and <code>migration_surfaces</code> turns a vague rewrite into a countable list of endpoints.",
"py_file": "slack_distribution_block.py",
"py": '''"""Check whether this app can ever be listed, before somebody promises it.

Read only. apps.manifest.export and auth.test are reads; nothing here edits a
manifest, creates an app, submits anything or opens a socket. Every repair is
printed for a human to carry out.

Socket Mode apps cannot be listed on the Slack Marketplace: a publicly
distributed app must expose a public HTTPS Request URL. That is a property of
the transport rather than of the code, which means it can be checked months
before the submission form is opened, from two manifest fields and a count of
the workspaces your own installation store already holds.
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_distribution_block")

API = "https://slack.com/api/"


def socket_enabled(manifest):
    """Is Socket Mode on? Pure. None when the manifest could not be read."""
    if not isinstance(manifest, dict) or not manifest:
        return None
    settings = manifest.get("settings")
    if not isinstance(settings, dict):
        return False
    return bool(settings.get("socket_mode_enabled"))


def distribution_intent(manifest):
    """Is this app meant to leave this workspace? Pure. Returns (intent, detail).

    There is no single manifest field that says "this app is distributed", so
    this reads the configuration that distribution requires: an OAuth redirect
    setup, and org deployment. An internal app on Socket Mode is the supported
    use of the feature and this function exists so it can be said out loud.
    """
    if not isinstance(manifest, dict) or not manifest:
        return ("unreadable", "no manifest, so the intent cannot be read")
    settings = manifest.get("settings") if isinstance(manifest.get("settings"),
                                                      dict) else {}
    oauth = manifest.get("oauth_config") if isinstance(manifest.get("oauth_config"),
                                                       dict) else {}
    redirects = [r for r in (oauth.get("redirect_urls") or []) if r]
    if settings.get("is_distributed") is True:
        return ("distributed", "the manifest reports the app as distributed")
    if settings.get("org_deploy_enabled"):
        return ("preparing", "org deployment is enabled, so this app is set up to be "
                             "installed across an organisation")
    if redirects:
        return ("preparing", "%d OAuth redirect URL(s) are configured, so this app is "
                             "set up to be installed somewhere other than here"
                             % len(redirects))
    return ("internal", "no redirect URLs and no org deployment: this app installs "
                        "here and nowhere else")


def install_spread(rows):
    """How far has this app already spread? Pure.

    rows are auth.test-shaped dicts from your own installation store. Counting
    team_id alone is the mistake: an Enterprise Grid organisation is many
    workspaces and one customer, and Socket Mode is permitted there. Unrelated
    enterprises are the finding.

    Returns (spread, teams, orgs, detail).
    """
    teams, orgs, loose = set(), set(), 0
    for row in rows or []:
        if not isinstance(row, dict) or not row.get("team_id"):
            continue
        teams.add(str(row["team_id"]))
        if row.get("enterprise_id"):
            orgs.add(str(row["enterprise_id"]))
        else:
            loose += 1
    if not teams:
        return ("unknown", 0, 0, "no installation records were supplied, so the spread "
                                 "is unmeasured")
    if len(teams) == 1:
        return ("single-workspace", 1, len(orgs), "one workspace holds this app")
    if len(orgs) == 1 and not loose:
        return ("grid-org", len(teams), 1, "%d workspace(s) inside one enterprise, "
                                           "which is org deployment rather than public "
                                           "distribution" % len(teams))
    return ("multi-workspace", len(teams), len(orgs),
            "%d workspace(s) across %d enterprise(s): they do not all share one "
            "enterprise, so this app is already distributed"
            % (len(teams), len(orgs)))


def eligibility(socket, intent, spread):
    """Can this app be listed on the Marketplace? Pure. Returns (verdict, detail).

    internal-fine is here on purpose. Socket Mode in one workspace with no
    distribution configured is the feature working as designed, and a checker
    that reports it as a violation is a checker people switch off.
    """
    if socket is None:
        return ("unreadable", "the manifest was not read, so the transport is unknown")
    if not socket:
        return ("eligible", "delivery is over HTTPS, so the transport is not what "
                            "stands between this app and a listing")
    if spread == "multi-workspace":
        return ("blocked-and-shipped", "already installed in unrelated workspaces on a "
                                       "transport the Marketplace does not accept. The "
                                       "migration is overdue rather than upcoming")
    if intent in ("distributed", "preparing"):
        return ("blocked", "Socket Mode and a distribution configuration. The listing "
                           "cannot happen on this transport, and the work is a "
                           "migration rather than a submission")
    if spread == "grid-org":
        return ("org-only", "Socket Mode across one enterprise is supported. It is "
                            "public listing that this transport rules out, so this is "
                            "a ceiling rather than a fault")
    return ("internal-fine", "one workspace, no distribution configured: this is the "
                             "supported use of Socket Mode and not a finding")


def clamp_exposure(socket, intent, reads_history):
    """Does the transport choice also cost the history rate limits? Pure.

    Marketplace approval is what lifts the clamp on conversations.history for
    non-Marketplace apps, so an app that cannot be listed cannot be unclamped
    either. Two problems, one repair, and finding them six months apart is how
    one decision gets rediscovered twice.
    """
    if not reads_history:
        return ("not-exposed", "this app does not read conversations.history, so the "
                               "clamp is not part of the cost")
    if socket and intent in ("distributed", "preparing"):
        return ("compounded", "listing is also what lifts the conversations.history "
                              "clamp, so the same rewrite is the only route to either")
    if socket:
        return ("clamped-internally", "an internal app is still subject to the clamp "
                                      "unless it is reclassified, which is a separate "
                                      "conversation from listing")
    return ("listable", "the transport is not in the way; approval is the remaining "
                        "step for the clamp as well")


def migration_surfaces(manifest):
    """What has to gain a public URL before submission? Pure.

    Returns [(surface, state), ...] with state in (needs-url, has-url). The
    point is a number: "we would have to rewrite it" is a worse sentence to
    bring to a planning meeting than "four endpoints".
    """
    m = manifest if isinstance(manifest, dict) else {}
    settings = m.get("settings") if isinstance(m.get("settings"), dict) else {}
    features = m.get("features") if isinstance(m.get("features"), dict) else {}
    events = settings.get("event_subscriptions") if isinstance(
        settings.get("event_subscriptions"), dict) else {}
    inter = settings.get("interactivity") if isinstance(
        settings.get("interactivity"), dict) else {}
    out = []
    subscribed = list(events.get("bot_events") or []) + list(
        events.get("user_events") or [])
    if subscribed:
        out.append(("event subscriptions",
                    "has-url" if events.get("request_url") else "needs-url"))
    if inter.get("is_enabled") or inter.get("request_url"):
        out.append(("interactivity",
                    "has-url" if inter.get("request_url") else "needs-url"))
        if inter.get("message_menu_options_url"):
            out.append(("menu options", "has-url"))
    for cmd in features.get("slash_commands") or []:
        if not isinstance(cmd, dict):
            continue
        out.append(("slash %s" % (cmd.get("command") or "?"),
                    "has-url" if cmd.get("url") else "needs-url"))
    return out


def load_manifest(args):
    """From a file, or from apps.manifest.export with a configuration token."""
    if args.manifest:
        raw = json.loads(open(args.manifest, encoding="utf-8").read())
        return raw.get("manifest", raw)
    token = os.environ.get(args.config_token_env)
    if not token or not args.app_id:
        log.warning("manifest   supply --manifest, or set %s and pass --app-id; a bot "
                    "token cannot read app configuration", args.config_token_env)
        return None
    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + token})
    body = s.get(API + "apps.manifest.export", timeout=30,
                 params={"app_id": args.app_id}).json()
    if body.get("ok") is not True:
        log.error("manifest   unavailable    %s", body.get("error"))
        return None
    return body.get("manifest") or {}


def load_installs(args):
    """Your own installation records, or one auth.test for the token at hand."""
    if args.installs:
        rows = json.loads(open(args.installs, encoding="utf-8").read())
        return rows if isinstance(rows, list) else [rows]
    token = os.environ.get(args.token_env)
    if not token:
        return []
    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + token})
    body = s.get(API + "auth.test", timeout=30).json()
    if body.get("ok") is not True:
        log.warning("auth.test  unavailable    %s", body.get("error"))
        return []
    return [body]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", default="", help="path to an exported manifest")
    ap.add_argument("--config-token-env", default="SLACK_CONFIG_TOKEN",
                    help="environment variable holding an app configuration token")
    ap.add_argument("--app-id", default="", help="app id, for the manifest read")
    ap.add_argument("--installs", default="",
                    help="path to a JSON array of auth.test-shaped install records")
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN",
                    help="environment variable holding a bot token")
    ap.add_argument("--reads-history", action="store_true",
                    help="this app calls conversations.history")
    args = ap.parse_args()

    manifest = load_manifest(args)
    socket = socket_enabled(manifest)
    log.info("manifest   socket mode %s",
             "unknown" if socket is None else ("on" if socket else "off"))

    intent, intent_detail = distribution_intent(manifest)
    log.info("intent     %-14s %s", intent, intent_detail)

    spread, teams, orgs, spread_detail = install_spread(load_installs(args))
    log.info("installs   %-14s %s", spread, spread_detail)

    verdict, detail = eligibility(socket, intent, spread)
    findings = ("blocked", "blocked-and-shipped")
    (log.warning if verdict in findings else log.info)("verdict    %-14s %s", verdict,
                                                       detail)

    clamp, clamp_detail = clamp_exposure(socket, intent, args.reads_history)
    (log.warning if clamp == "compounded" else log.info)("clamp      %-14s %s", clamp,
                                                         clamp_detail)

    if verdict in findings:
        needed = [s for s, state in migration_surfaces(manifest) if state == "needs-url"]
        for surface, state in migration_surfaces(manifest):
            log.warning("migrate    %-14s %s", state, surface)
        log.warning("  repair: stand up a public HTTPS endpoint and configure the %d "
                    "surface(s) that need one", len(needed))
        log.warning("  repair: switch Socket Mode off, re-verify each URL, and keep "
                    "Socket Mode on a separate development app")
        log.warning("  repair: budget signature verification and a three second "
                    "response on every request; a socket consumer never needed either")
        log.info("  note: %d workspace(s) and %d enterprise(s) in the records read",
                 teams, orgs)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-distribution-block.mjs",
"js": '''/**
 * Check whether this app can ever be listed, before somebody promises it.
 *
 * Read only. apps.manifest.export and auth.test are reads; nothing here edits a
 * manifest, creates an app, submits anything or opens a socket.
 *
 * Socket Mode apps cannot be listed on the Slack Marketplace: a publicly
 * distributed app must expose a public HTTPS Request URL. That is a property of
 * the transport rather than of the code, so it is checkable months before the
 * submission form is opened.
 */

import { readFileSync } from 'node:fs';

const API = 'https://slack.com/api/';

/** Is Socket Mode on? Pure. null when the manifest could not be read. */
export function socketEnabled(manifest) {
  if (!manifest || typeof manifest !== 'object' || !Object.keys(manifest).length) {
    return null;
  }
  const settings = manifest.settings;
  if (!settings || typeof settings !== 'object') return false;
  return Boolean(settings.socket_mode_enabled);
}

/**
 * Is this app meant to leave this workspace? Pure. Returns [intent, detail].
 * No single manifest field says "distributed", so this reads the configuration
 * distribution requires: OAuth redirects, and org deployment.
 */
export function distributionIntent(manifest) {
  if (!manifest || typeof manifest !== 'object' || !Object.keys(manifest).length) {
    return ['unreadable', 'no manifest, so the intent cannot be read'];
  }
  const settings = (manifest.settings && typeof manifest.settings === 'object')
    ? manifest.settings : {};
  const oauth = (manifest.oauth_config && typeof manifest.oauth_config === 'object')
    ? manifest.oauth_config : {};
  const redirects = (oauth.redirect_urls ?? []).filter(Boolean);
  if (settings.is_distributed === true) {
    return ['distributed', 'the manifest reports the app as distributed'];
  }
  if (settings.org_deploy_enabled) {
    return ['preparing', 'org deployment is enabled, so this app is set up to be '
      + 'installed across an organisation'];
  }
  if (redirects.length) {
    return ['preparing', `${redirects.length} OAuth redirect URL(s) are configured, so `
      + 'this app is set up to be installed somewhere other than here'];
  }
  return ['internal', 'no redirect URLs and no org deployment: this app installs here '
    + 'and nowhere else'];
}

/**
 * How far has this app already spread? Pure. Returns [spread, teams, orgs, detail].
 * Counting team_id alone is the mistake: a Grid organisation is many workspaces
 * and one customer, and Socket Mode is permitted there.
 */
export function installSpread(rows) {
  const teams = new Set();
  const orgs = new Set();
  let loose = 0;
  for (const row of rows ?? []) {
    if (!row || typeof row !== 'object' || !row.team_id) continue;
    teams.add(String(row.team_id));
    if (row.enterprise_id) orgs.add(String(row.enterprise_id)); else loose += 1;
  }
  if (!teams.size) {
    return ['unknown', 0, 0, 'no installation records were supplied, so the spread is '
      + 'unmeasured'];
  }
  if (teams.size === 1) {
    return ['single-workspace', 1, orgs.size, 'one workspace holds this app'];
  }
  if (orgs.size === 1 && !loose) {
    return ['grid-org', teams.size, 1, `${teams.size} workspace(s) inside one `
      + 'enterprise, which is org deployment rather than public distribution'];
  }
  return ['multi-workspace', teams.size, orgs.size, `${teams.size} workspace(s) across `
    + `${orgs.size} enterprise(s): they do not all share one enterprise, so this app is `
    + 'already distributed'];
}

/**
 * Can this app be listed on the Marketplace? Pure. Returns [verdict, detail].
 * internal-fine is here on purpose: Socket Mode in one workspace with no
 * distribution configured is the feature working as designed.
 */
export function eligibility(socket, intent, spread) {
  if (socket === null || socket === undefined) {
    return ['unreadable', 'the manifest was not read, so the transport is unknown'];
  }
  if (!socket) {
    return ['eligible', 'delivery is over HTTPS, so the transport is not what stands '
      + 'between this app and a listing'];
  }
  if (spread === 'multi-workspace') {
    return ['blocked-and-shipped', 'already installed in unrelated workspaces on a '
      + 'transport the Marketplace does not accept. The migration is overdue rather '
      + 'than upcoming'];
  }
  if (intent === 'distributed' || intent === 'preparing') {
    return ['blocked', 'Socket Mode and a distribution configuration. The listing '
      + 'cannot happen on this transport, and the work is a migration rather than a '
      + 'submission'];
  }
  if (spread === 'grid-org') {
    return ['org-only', 'Socket Mode across one enterprise is supported. It is public '
      + 'listing that this transport rules out, so this is a ceiling rather than a '
      + 'fault'];
  }
  return ['internal-fine', 'one workspace, no distribution configured: this is the '
    + 'supported use of Socket Mode and not a finding'];
}

/**
 * Does the transport choice also cost the history rate limits? Pure.
 * Marketplace approval is what lifts the clamp on conversations.history, so an
 * app that cannot be listed cannot be unclamped either.
 */
export function clampExposure(socket, intent, readsHistory) {
  if (!readsHistory) {
    return ['not-exposed', 'this app does not read conversations.history, so the clamp '
      + 'is not part of the cost'];
  }
  if (socket && (intent === 'distributed' || intent === 'preparing')) {
    return ['compounded', 'listing is also what lifts the conversations.history clamp, '
      + 'so the same rewrite is the only route to either'];
  }
  if (socket) {
    return ['clamped-internally', 'an internal app is still subject to the clamp unless '
      + 'it is reclassified, which is a separate conversation from listing'];
  }
  return ['listable', 'the transport is not in the way; approval is the remaining step '
    + 'for the clamp as well'];
}

/**
 * What has to gain a public URL before submission? Pure.
 * Returns [[surface, state], ...]. The point is a number: "four endpoints" is a
 * better sentence in a planning meeting than "we would have to rewrite it".
 */
export function migrationSurfaces(manifest) {
  const m = (manifest && typeof manifest === 'object') ? manifest : {};
  const settings = (m.settings && typeof m.settings === 'object') ? m.settings : {};
  const features = (m.features && typeof m.features === 'object') ? m.features : {};
  const events = (settings.event_subscriptions
    && typeof settings.event_subscriptions === 'object')
    ? settings.event_subscriptions : {};
  const inter = (settings.interactivity && typeof settings.interactivity === 'object')
    ? settings.interactivity : {};
  const out = [];
  const subscribed = [...(events.bot_events ?? []), ...(events.user_events ?? [])];
  if (subscribed.length) {
    out.push(['event subscriptions', events.request_url ? 'has-url' : 'needs-url']);
  }
  if (inter.is_enabled || inter.request_url) {
    out.push(['interactivity', inter.request_url ? 'has-url' : 'needs-url']);
    if (inter.message_menu_options_url) out.push(['menu options', 'has-url']);
  }
  for (const cmd of features.slash_commands ?? []) {
    if (!cmd || typeof cmd !== 'object') continue;
    out.push([`slash ${cmd.command ?? '?'}`, cmd.url ? 'has-url' : 'needs-url']);
  }
  return out;
}

function arg(args, name, fallback = null) {
  const i = args.indexOf(name);
  return i === -1 ? fallback : args[i + 1];
}

async function loadManifest(args) {
  const path = arg(args, '--manifest', '');
  if (path) {
    const raw = JSON.parse(readFileSync(path, 'utf-8'));
    return raw.manifest ?? raw;
  }
  const tokenEnv = arg(args, '--config-token-env', 'SLACK_CONFIG_TOKEN');
  const token = process.env[tokenEnv];
  const appId = arg(args, '--app-id', '');
  if (!token || !appId) {
    console.warn(`manifest   supply --manifest, or set ${tokenEnv} and pass --app-id; a `
      + 'bot token cannot read app configuration');
    return null;
  }
  const params = new URLSearchParams({ app_id: appId });
  const body = await (await fetch(`${API}apps.manifest.export?${params}`,
    { headers: { Authorization: `Bearer ${token}` } })).json();
  if (body.ok !== true) {
    console.error(`manifest   unavailable    ${body.error}`);
    return null;
  }
  return body.manifest ?? {};
}

async function loadInstalls(args) {
  const path = arg(args, '--installs', '');
  if (path) {
    const rows = JSON.parse(readFileSync(path, 'utf-8'));
    return Array.isArray(rows) ? rows : [rows];
  }
  const tokenEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
  const token = process.env[tokenEnv];
  if (!token) return [];
  const body = await (await fetch(`${API}auth.test`,
    { headers: { Authorization: `Bearer ${token}` } })).json();
  if (body.ok !== true) {
    console.warn(`auth.test  unavailable    ${body.error}`);
    return [];
  }
  return [body];
}

async function main() {
  const args = process.argv.slice(2);
  const manifest = await loadManifest(args);
  const socket = socketEnabled(manifest);
  console.log(`manifest   socket mode ${socket === null ? 'unknown' : (socket ? 'on' : 'off')}`);

  const [intent, intentDetail] = distributionIntent(manifest);
  console.log(`intent     ${intent.padEnd(14)} ${intentDetail}`);

  const [spread, teams, orgs, spreadDetail] = installSpread(await loadInstalls(args));
  console.log(`installs   ${spread.padEnd(14)} ${spreadDetail}`);

  const [verdict, detail] = eligibility(socket, intent, spread);
  const findings = ['blocked', 'blocked-and-shipped'];
  const line = `verdict    ${verdict.padEnd(14)} ${detail}`;
  if (findings.includes(verdict)) console.warn(line); else console.log(line);

  const [clamp, clampDetail] = clampExposure(socket, intent,
    args.includes('--reads-history'));
  const clampLine = `clamp      ${clamp.padEnd(14)} ${clampDetail}`;
  if (clamp === 'compounded') console.warn(clampLine); else console.log(clampLine);

  if (findings.includes(verdict)) {
    const surfaces = migrationSurfaces(manifest);
    const needed = surfaces.filter(([, state]) => state === 'needs-url');
    for (const [surface, state] of surfaces) {
      console.warn(`migrate    ${state.padEnd(14)} ${surface}`);
    }
    console.warn(`  repair: stand up a public HTTPS endpoint and configure the `
      + `${needed.length} surface(s) that need one`);
    console.warn('  repair: switch Socket Mode off, re-verify each URL, and keep Socket '
      + 'Mode on a separate development app');
    console.log(`  note: ${teams} workspace(s) and ${orgs} enterprise(s) in the records`);
    process.exitCode = 1;
  }
}

// Only run when invoked directly, so importing this module in the tests does
// not execute main() and fail the file on a missing manifest.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Two assertions here are worth more than the rest. Socket Mode in a single workspace with nothing configured for distribution has to come back <code>internal-fine</code>, because that is the feature being used correctly and a check that calls it a violation gets switched off within a week. And a Grid organisation with eleven workspaces and one <code>enterprise_id</code> has to come back <code>grid-org</code> rather than <code>multi-workspace</code>, since counting <code>team_id</code> alone turns the one supported multi-workspace case into a false alarm.",
"test_py_file": "test_slack_distribution_block.py",
"test_py": '''from slack_distribution_block import (clamp_exposure, distribution_intent,
                                       eligibility, install_spread,
                                       migration_surfaces, socket_enabled)

SOCKET_APP = {"settings": {"socket_mode_enabled": True}}
DISTRIBUTED = {"settings": {"socket_mode_enabled": True},
               "oauth_config": {"redirect_urls": ["https://acme.dev/oauth"]}}


def test_the_socket_switch_is_read_from_the_manifest():
    assert socket_enabled(SOCKET_APP) is True
    assert socket_enabled({"settings": {}}) is False


def test_an_absent_manifest_leaves_the_transport_unknown():
    assert socket_enabled({}) is None
    assert socket_enabled(None) is None


def test_a_redirect_configuration_means_the_app_is_meant_to_travel():
    intent, detail = distribution_intent(DISTRIBUTED)
    assert intent == "preparing"
    assert "somewhere other than here" in detail


def test_org_deployment_also_counts_as_preparing():
    assert distribution_intent({"settings": {"org_deploy_enabled": True}})[0] == \\
        "preparing"


def test_an_explicit_distributed_flag_is_taken_at_its_word():
    assert distribution_intent({"settings": {"is_distributed": True}})[0] == \\
        "distributed"


def test_no_redirects_and_no_org_deployment_is_an_internal_app():
    assert distribution_intent(SOCKET_APP)[0] == "internal"
    assert distribution_intent({})[0] == "unreadable"


def test_unrelated_workspaces_mean_the_app_is_already_distributed():
    spread, teams, orgs, detail = install_spread([
        {"team_id": "T1"}, {"team_id": "T2"}, {"team_id": "T3", "enterprise_id": "E9"},
    ])
    assert spread == "multi-workspace"
    assert (teams, orgs) == (3, 1)
    assert "already distributed" in detail


def test_one_enterprise_with_many_workspaces_is_org_deployment():
    spread, teams, orgs, detail = install_spread([
        {"team_id": "T1", "enterprise_id": "E1"},
        {"team_id": "T2", "enterprise_id": "E1"},
    ])
    assert spread == "grid-org"
    assert (teams, orgs) == (2, 1)
    assert "rather than public distribution" in detail


def test_one_workspace_is_one_workspace():
    assert install_spread([{"team_id": "T1"}])[0] == "single-workspace"


def test_no_records_leaves_the_spread_unmeasured():
    assert install_spread([])[0] == "unknown"
    assert install_spread([None, {"user_id": "U1"}])[0] == "unknown"


def test_socket_mode_in_one_internal_workspace_is_not_a_fault():
    verdict, detail = eligibility(True, "internal", "single-workspace")
    assert verdict == "internal-fine"
    assert "not a finding" in detail


def test_socket_mode_with_a_distribution_setup_is_blocked():
    assert eligibility(True, "preparing", "single-workspace")[0] == "blocked"


def test_socket_mode_already_in_unrelated_workspaces_is_the_emergency():
    verdict, detail = eligibility(True, "internal", "multi-workspace")
    assert verdict == "blocked-and-shipped"
    assert "overdue" in detail


def test_socket_mode_across_one_enterprise_is_a_ceiling_not_a_fault():
    assert eligibility(True, "internal", "grid-org")[0] == "org-only"


def test_an_http_app_is_not_blocked_by_its_transport():
    assert eligibility(False, "preparing", "multi-workspace")[0] == "eligible"


def test_an_unread_manifest_produces_no_verdict():
    assert eligibility(None, "unreadable", "unknown")[0] == "unreadable"


def test_reading_history_on_a_blocked_app_compounds_the_problem():
    state, detail = clamp_exposure(True, "preparing", True)
    assert state == "compounded"
    assert "same rewrite" in detail


def test_an_internal_socket_app_that_reads_history_is_still_clamped():
    assert clamp_exposure(True, "internal", True)[0] == "clamped-internally"


def test_an_app_that_does_not_read_history_is_not_exposed_to_the_clamp():
    assert clamp_exposure(True, "preparing", False)[0] == "not-exposed"


def test_an_http_app_that_reads_history_only_needs_approval():
    assert clamp_exposure(False, "preparing", True)[0] == "listable"


def test_the_migration_is_a_countable_list_of_endpoints():
    got = migration_surfaces({
        "settings": {
            "event_subscriptions": {"bot_events": ["app_mention"]},
            "interactivity": {"is_enabled": True},
        },
        "features": {"slash_commands": [{"command": "/report"}]},
    })
    assert got == [("event subscriptions", "needs-url"), ("interactivity", "needs-url"),
                   ("slash /report", "needs-url")]


def test_surfaces_that_already_have_a_url_are_not_counted_as_work():
    got = migration_surfaces({
        "settings": {"event_subscriptions": {"bot_events": ["app_mention"],
                                             "request_url": "https://acme.dev/e"}},
    })
    assert got == [("event subscriptions", "has-url")]


def test_an_app_with_nothing_configured_needs_nothing_migrated():
    assert migration_surfaces({}) == []
    assert migration_surfaces(None) == []
''',
"test_js_file": "slack-distribution-block.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  clampExposure, distributionIntent, eligibility, installSpread, migrationSurfaces,
  socketEnabled,
} from './slack-distribution-block.mjs';

const SOCKET_APP = { settings: { socket_mode_enabled: true } };
const DISTRIBUTED = {
  settings: { socket_mode_enabled: true },
  oauth_config: { redirect_urls: ['https://acme.dev/oauth'] },
};

test('the socket switch is read from the manifest', () => {
  assert.equal(socketEnabled(SOCKET_APP), true);
  assert.equal(socketEnabled({ settings: {} }), false);
});

test('an absent manifest leaves the transport unknown', () => {
  assert.equal(socketEnabled({}), null);
  assert.equal(socketEnabled(null), null);
});

test('a redirect configuration means the app is meant to travel', () => {
  const [intent, detail] = distributionIntent(DISTRIBUTED);
  assert.equal(intent, 'preparing');
  assert.match(detail, /somewhere other than here/);
});

test('org deployment also counts as preparing', () => {
  assert.equal(distributionIntent({ settings: { org_deploy_enabled: true } })[0],
    'preparing');
});

test('an explicit distributed flag is taken at its word', () => {
  assert.equal(distributionIntent({ settings: { is_distributed: true } })[0],
    'distributed');
});

test('no redirects and no org deployment is an internal app', () => {
  assert.equal(distributionIntent(SOCKET_APP)[0], 'internal');
  assert.equal(distributionIntent({})[0], 'unreadable');
});

test('unrelated workspaces mean the app is already distributed', () => {
  const [spread, teams, , detail] = installSpread([{ team_id: 'T1' },
    { team_id: 'T2' }, { team_id: 'T3', enterprise_id: 'E9' }]);
  assert.equal(spread, 'multi-workspace');
  assert.equal(teams, 3);
  assert.match(detail, /already distributed/);
});

test('one enterprise with many workspaces is org deployment', () => {
  const [spread, teams, orgs, detail] = installSpread([
    { team_id: 'T1', enterprise_id: 'E1' },
    { team_id: 'T2', enterprise_id: 'E1' },
  ]);
  assert.equal(spread, 'grid-org');
  assert.equal(teams, 2);
  assert.equal(orgs, 1);
  assert.match(detail, /rather than public distribution/);
});

test('one workspace is one workspace', () => {
  assert.equal(installSpread([{ team_id: 'T1' }])[0], 'single-workspace');
});

test('no records leaves the spread unmeasured', () => {
  assert.equal(installSpread([])[0], 'unknown');
  assert.equal(installSpread([null, { user_id: 'U1' }])[0], 'unknown');
});

test('socket mode in one internal workspace is not a fault', () => {
  const [verdict, detail] = eligibility(true, 'internal', 'single-workspace');
  assert.equal(verdict, 'internal-fine');
  assert.match(detail, /not a finding/);
});

test('socket mode with a distribution setup is blocked', () => {
  assert.equal(eligibility(true, 'preparing', 'single-workspace')[0], 'blocked');
});

test('socket mode already in unrelated workspaces is the emergency', () => {
  const [verdict, detail] = eligibility(true, 'internal', 'multi-workspace');
  assert.equal(verdict, 'blocked-and-shipped');
  assert.match(detail, /overdue/);
});

test('socket mode across one enterprise is a ceiling not a fault', () => {
  assert.equal(eligibility(true, 'internal', 'grid-org')[0], 'org-only');
});

test('an http app is not blocked by its transport', () => {
  assert.equal(eligibility(false, 'preparing', 'multi-workspace')[0], 'eligible');
});

test('an unread manifest produces no verdict', () => {
  assert.equal(eligibility(null, 'unreadable', 'unknown')[0], 'unreadable');
});

test('reading history on a blocked app compounds the problem', () => {
  const [state, detail] = clampExposure(true, 'preparing', true);
  assert.equal(state, 'compounded');
  assert.match(detail, /same rewrite/);
});

test('an internal socket app that reads history is still clamped', () => {
  assert.equal(clampExposure(true, 'internal', true)[0], 'clamped-internally');
});

test('an app that does not read history is not exposed to the clamp', () => {
  assert.equal(clampExposure(true, 'preparing', false)[0], 'not-exposed');
});

test('an http app that reads history only needs approval', () => {
  assert.equal(clampExposure(false, 'preparing', true)[0], 'listable');
});

test('the migration is a countable list of endpoints', () => {
  const got = migrationSurfaces({
    settings: {
      event_subscriptions: { bot_events: ['app_mention'] },
      interactivity: { is_enabled: true },
    },
    features: { slash_commands: [{ command: '/report' }] },
  });
  assert.deepEqual(got, [['event subscriptions', 'needs-url'],
    ['interactivity', 'needs-url'], ['slash /report', 'needs-url']]);
});

test('surfaces that already have a url are not counted as work', () => {
  const got = migrationSurfaces({
    settings: {
      event_subscriptions: { bot_events: ['app_mention'],
        request_url: 'https://acme.dev/e' },
    },
  });
  assert.deepEqual(got, [['event subscriptions', 'has-url']]);
});

test('an app with nothing configured needs nothing migrated', () => {
  assert.deepEqual(migrationSurfaces({}), []);
  assert.deepEqual(migrationSurfaces(null), []);
});
''',
"faq": [
 ("Is this a rule or just a recommendation?",
  "It is a requirement of listing. A publicly distributed app has to receive events at a public HTTPS Request URL, and Socket Mode does not provide one, so an app built on it is not eligible for the Marketplace regardless of how well it works. Socket Mode is intended for apps behind a firewall and for internal or org-deployed use, and those remain entirely supported. What is ruled out is the public listing."),
 ("We have eleven workspaces on Socket Mode and nobody has complained. Are we fine?",
  "Check whether those eleven share an enterprise_id. Many workspaces inside one Enterprise Grid organisation is org deployment, which Socket Mode supports, and that is why the script separates grid-org from multi-workspace instead of counting installs. Eleven unrelated workspaces is a different story: the app is distributed in fact, on a transport that cannot be listed, and the migration is already overdue."),
 ("How much of our code has to change?",
  "Usually very little. Bolt supports both a socket receiver and an HTTP receiver, so the handlers, the routing and the business logic normally survive the switch untouched. What changes is the deployment: a public hostname with TLS, signature verification on every inbound request, and a three second response budget that a socket consumer never had to meet. It is a platform project rather than a rewrite, which is a much better thing to discover early."),
 ("What does this have to do with rate limits?",
  "Marketplace approval is also the route back to the un-clamped conversations.history limits for apps that are not on the Marketplace. So an app that cannot be listed cannot be unclamped either, and if it polls history it is stuck at the clamped rate permanently. The two constraints have one shared repair, which is why the script reports them together rather than leaving the second to be rediscovered six months later."),
 ("Can we keep Socket Mode for development after we migrate?",
  "Yes, and you should - on a separate app. A development app with Socket Mode on and no Request URL, and a production app on HTTPS with Socket Mode off, is the configuration that keeps both benefits without either one changing where events go. Keeping both switches on one app is a different problem with its own note, and it is the one that produces duplicate messages and silent staging environments."),
],
"related": [
 ("/slack/non-marketplace-history-clamp/", "the rate limit that the same listing would lift"),
 ("/slack/app-level-token-missing-connections-write/", "the credential Socket Mode needs before any of this"),
 ("/slack/socket-mode-and-request-url-both-on/", "the other cost of one app configuration"),
],
"citations": [CITE_SOCKET_MODE, CITE_OAUTH_INSTALL, CITE_RATE_CHANGELOG, CITE_MANIFEST_REF],
})
