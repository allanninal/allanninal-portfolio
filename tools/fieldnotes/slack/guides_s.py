#!/usr/bin/env python3
"""/slack/ field notes, batch S - the writing.

Four notes about a file you cannot get at, written so that no two of them read
the same field or reach the same conclusion. All four are file-visibility notes
and that is exactly why they are separated by what the script reads rather than
by what the reader was trying to do.

The first is a file with no audience at all. The upload sequence finished
cleanly, nothing errored, and channel_id was never passed - so the file exists,
is well formed, has a permalink, and is shared into nothing. The reading is the
`shares` object beside the legacy arrays, and the answer is a count.

The second is a file with an audience that does not include you. It is shared,
properly, into a room your token is not in, and files.info says not_visible.
The reading is the error string, sorted into four that look alike and mean
different things, and then the room named by the event payload rather than by
the API - because a not_visible answer tells you nothing about where the file
lives.

The third is a file that stopped existing while the message that carried it did
not. The symptom is on the message side: an old post still renders a link, an
index still holds an id, and both point at nothing. The reading is a batch of
files.info calls over references harvested from history, and the answer is a
fraction that grows.

The fourth is not about permission at all. The file is there, the token is
right, and the header was left off the fetch - so Slack answered 200 with its
sign-in page and the downloader wrote the login screen to disk. The reading is
the bytes already on that disk, held against the mimetype and size the API
reports. Nothing here fetches the file, and nothing prints a url_private: doing
either would need the credential under audit or hand over the content.

Read only throughout, and more strictly than usual. Nothing in this batch
uploads, shares, revokes or deletes a file, and nothing downloads one. files.list
and files.info are reads; every repair is printed for a human to run.
"""

CITE_FILES_INFO = ("files.info method reference - Slack Docs",
                   "https://docs.slack.dev/reference/methods/files.info")
CITE_FILES_LIST = ("files.list method reference - Slack Docs",
                   "https://docs.slack.dev/reference/methods/files.list")
CITE_COMPLETE_UPLOAD = ("files.completeUploadExternal method reference - Slack Docs",
                        "https://docs.slack.dev/reference/methods/"
                        "files.completeUploadExternal")
CITE_GET_UPLOAD_URL = ("files.getUploadURLExternal method reference - Slack Docs",
                       "https://docs.slack.dev/reference/methods/"
                       "files.getUploadURLExternal")
CITE_WORKING_FILES = ("Working with files - Slack Docs",
                      "https://docs.slack.dev/messaging/working-with-files")
CITE_FILE_SHARED = ("file_shared event reference - Slack Docs",
                    "https://docs.slack.dev/reference/events/file_shared")
CITE_FILE_DELETED = ("file_deleted event reference - Slack Docs",
                     "https://docs.slack.dev/reference/events/file_deleted")
CITE_USERS_CONVERSATIONS = ("users.conversations method reference - Slack Docs",
                            "https://docs.slack.dev/reference/methods/"
                            "users.conversations")
CITE_CONV_HISTORY = ("conversations.history method reference - Slack Docs",
                     "https://docs.slack.dev/reference/methods/conversations.history")
CITE_SDK_SHARES = ("python-slack-sdk #1575: files uploaded but not shared",
                   "https://github.com/slackapi/python-slack-sdk/issues/1575")
CITE_SO_DOWNLOAD = ("Stack Overflow: downloading a Slack file returns the sign-in page",
                    "https://stackoverflow.com/questions/36144761")
CITE_SO_PUBLIC = ("Stack Overflow: url_private, permalink and permalink_public",
                  "https://stackoverflow.com/questions/57253156")
CITE_WEB_API = ("Web API - Slack Docs", "https://docs.slack.dev/apis/web-api/")

GUIDES = []

GUIDES.append({
"slug": "file-not-shared-to-channel",
"title": "Files that uploaded fine and were shared into no channel",
"description": "files.completeUploadExternal shares only when channel_id is passed. Find every file your app owns whose shares object and legacy arrays are both empty.",
"h1": "Files that uploaded fine and were shared into no channel",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack file uploaded but not in channel",
             "files.completeUploadExternal channel_id",
             "slack file shares object empty",
             "slack unshared file audit",
             "slack file not visible to team"],
"deps": "Python 3.9+ with requests, or Node.js 18+; a bot token with files:read",
"lead": "The nightly job uploads a CSV every morning and logs <em>uploaded ok</em> every morning. Nobody has ever seen one. The channel it was supposed to land in has been empty for eleven weeks, and <code>files.list</code> comes back with seventy-seven CSVs, all present, all owned by the app, all shared into nothing at all.</p><p>No call failed. <code>files.completeUploadExternal</code> registered every one of them and returned <code>ok: true</code>. Uploading a file and sharing a file are two things, the second one is a parameter, and the parameter was never passed.",
"short_answer": """<p>Sharing is not a side effect of uploading. <code>files.completeUploadExternal</code> puts the file in the workspace, and it shares it into a conversation only if you pass <code>channel_id</code>. Leave that off and you get a complete, well-formed, permanently stored file that is <strong>visible to the identity that uploaded it and to nobody else</strong>. The legacy <code>files.upload</code> had the same split, through its <code>channels</code> parameter, so this survived the migration intact.</p>
<p>Every file records where it is shared, twice. The modern <code>shares</code> object has a <code>public</code> map and a <code>private</code> map keyed by conversation id; the older <code>channels</code>, <code>groups</code> and <code>ims</code> arrays carry the same fact split by conversation type. <strong>A file with nothing in either representation has no audience.</strong> Page <code>files.list?count=200&amp;types=all&amp;user=&lt;your bot's user id&gt;</code> with <code>files:read</code>, and count them.</p>
<p>The number that matters is a proportion, not a total. Seventy-seven orphans out of eighty files your app has ever uploaded is a broken upload path. Seventy-seven out of nine thousand is somebody's abandoned experiment from 2023.</p>""",
"problem": """<p>What makes this one hide so well is that there is no error anywhere and no missing piece anywhere. The bytes went up. The file object came back with an id, a permalink, a mimetype and a size. Logging <code>ok: true</code> is honest. The app is not broken in any sense that a monitor can see, and the failure is a human one: a person opened Slack, searched for the report, and did not find it, and then assumed they had the wrong channel.</p>
<p>The usual route in is a refactor. An app that used <code>files.upload</code> with <code>channels="#reports"</code> gets migrated to the three-step flow, and the new final call takes <code>channel_id</code> instead - a different name, in a different position, requiring an <strong>id</strong> rather than a name. Someone drops it while getting the rest of the sequence working, the uploads start succeeding, and the missing parameter never comes back. The tests pass because the tests assert on <code>ok</code>.</p>
<p>The second route is deliberate and worse. A team decides to upload first and post a link afterwards, because that feels tidier than passing a channel to an upload call. Then the second step is either never written or is written to post <code>permalink</code> - and a <code>permalink</code> is a page in the Slack client that enforces the file's permissions, so everybody who clicks it gets told they do not have access to this file. The link is right there in the channel and it opens nothing. That reads as a Slack bug and is not one.</p>
<p>There is also a shape of this that is not a bug at all and must not be reported as one. A file shared only into a private channel has an empty <code>channels</code> array, because private channels live in <code>groups</code> and in <code>shares.private</code>. A file shared only into a DM has both of those empty and something in <code>ims</code>. A checker written against <code>channels</code> alone flags every one of them, produces a wall of false findings on its first run, and gets switched off in the same week. Reading both representations is not thoroughness here, it is the difference between a useful check and a noisy one.</p>""",
"why": """<p><strong>Nothing errors, so the only signal is a count.</strong> There is no error string to search for and no failed call to alert on. The finding is arithmetic: how many of the files this app owns have zero share targets. That is why the script reports a proportion of the app's own output rather than a list of ids - a list of ids invites someone to fix seventy-seven rows and leave the upload path alone.</p>
<p><strong>The fact is stored twice and both copies have to be read.</strong> <code>shares.public</code> and <code>shares.private</code> are the current representation; <code>channels</code>, <code>groups</code> and <code>ims</code> are the old one. Slack populates both, but which one is populated for a given file has varied by upload path and by age, and reading either alone is wrong in one direction or the other. The script unions them and says which bucket each share came from.</p>
<p><strong>Shared into a private channel is a share.</strong> The most damaging false positive this check can produce is reporting correctly-shared private files as orphans, because it destroys trust in the run. <code>private-only</code> and <code>dm-only</code> are separate verdicts here, reported as context and never as findings.</p>
<p><strong>An unshared file that is also public is the worst row on the list, and it is a different note.</strong> A file with no share targets and <code>public_url_shared: true</code> is unreachable inside Slack and readable by anyone on the internet holding the link. The script gives it its own verdict and points at the note that owns that problem, because the repair is a revocation rather than a share.</p>
<p><strong>Posting the permalink is the repair, and it works for a reason worth knowing.</strong> Putting a file's <code>permalink</code> in a message to a channel makes Slack unfurl it and grants that channel's members access to the file. That is the documented way to share a file after the fact, and it is why <em>post a link later</em> is a plan that can work - as long as the link is posted with the bot into a real conversation, rather than pasted into a wiki.</p>
<p><strong>An external file is not yours to judge.</strong> <code>is_external</code> files are hosted elsewhere and Slack holds a reference, not the bytes. Their sharing state is somebody else's system's problem and the script says so instead of counting them.</p>""",
"steps": [
 {"h": "Page files.list, scoped to the identity that does the uploading",
  "body": """<p><code>files.list?count=200&amp;types=all&amp;user=&lt;U...&gt;</code>, following <code>paging.pages</code>. The <code>user</code> filter is what turns a workspace-wide inventory into an audit of your app's own output, and the id you want is the <code>user_id</code> from <code>auth.test</code> - a bot's files are owned by its bot user.</p>"""},
 {"h": "Read both representations of the share, not the convenient one",
  "body": """<p><code>buckets</code> merges <code>shares.public</code> and <code>shares.private</code> with the legacy <code>channels</code>, <code>groups</code> and <code>ims</code> arrays and returns the three buckets separately. A file is unshared only when all three come back empty.</p>"""},
 {"h": "Separate the four states that look like zero from the outside",
  "body": """<p><code>share_state</code> returns <code>unshared</code>, <code>link-only</code>, <code>dm-only</code>, <code>private-only</code>, <code>shared</code> or <code>external</code>. Only the first two are findings. <code>dm-only</code> and <code>private-only</code> are narrow audiences and are printed as context, because reporting them as faults is how this check gets ignored.</p>"""},
 {"h": "Read the proportion rather than the total",
  "body": """<p><code>orphan_rate</code> divides the unreachable files by everything the app owns. A high proportion says the upload path is missing <code>channel_id</code> today; a handful against thousands says somebody experimented once. The two want completely different conversations and the total on its own does not distinguish them.</p>"""},
 {"h": "Pass channel_id at upload time rather than fixing the rows",
  "body": """<p>The repair the script prints is a code change: <code>files.completeUploadExternal?files=[...]&amp;channel_id=C0123456789</code>, with a channel <strong>id</strong> - the new flow rejects names and user ids where the old one accepted <code>#reports</code>. Add <code>initial_comment</code> while you are there, so the file arrives with a sentence explaining it.</p>"""},
 {"h": "Share what already exists by posting its permalink",
  "body": """<p>For files that are already up, the way to give them an audience is to post their <code>permalink</code> into a channel with the bot. Slack expands the link and the channel's members gain access. That call is a write, so the script prints it rather than making it.</p>"""},
],
"verify": """<p>Re-run after the deploy. The number to watch is the proportion, and it should stop growing before it starts shrinking.</p>
<pre><code class="language-bash">python3 slack_unshared_files.py
# identity   U07BOT9QD (reports-bot) in Northwind
# scope      files:read granted
# files      312 file(s) owned by U07BOT9QD, over 2 page(s)
# state      unshared       F08K2M4QX daily-sales.csv  no channel, no private channel and
#                           no DM. The upload finished and channel_id was never passed
# state      link-only      F08K2M55Z q3-export.csv  shared into no conversation and
#                           readable by anyone holding permalink_public
# state      private-only   F08K2M77A incident-log.txt  shared into 1 private channel
# state      shared         F08K2M91B runbook.pdf  shared into 2 conversation(s)
# verdict    77 of 312 file(s) owned by this app have no audience in Slack (24.7%)
#   repair: pass channel_id (a C id, not a name) to files.completeUploadExternal
#   repair: to share a file that already exists, post its permalink into the channel</code></pre>""",
"code_intro": "One paginated GET and nothing else. The pure functions are the whole argument: <code>buckets</code> reads the two representations of a share together so that a private channel is not mistaken for an absence, <code>share_state</code> keeps the four zero-looking states apart, and <code>orphan_rate</code> turns the list into the proportion that is the actual finding. The token needs <code>files:read</code>; sharing needs <code>files:write</code>, which this script deliberately does not use.",
"py_file": "slack_unshared_files.py",
"py": '''"""Find the files your app uploaded and gave to nobody.

Read only. One paginated GET against files.list and no writes at all: sharing a
file, revoking a link and deleting a file all need files:write, and all three
are printed here rather than performed. A bot token with files:read is enough.

The question is not whether the upload worked - it did, or the file would not be
in the list. The question is whether anything was passed to
files.completeUploadExternal to say where the file should go, and the answer
lives in the share fields of every file the app owns.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_unshared_files")

API = "https://slack.com/api/"

# The two verdicts that mean nobody in the workspace can reach the file. Kept as
# a constant because the rate and the report have to agree on what counts.
UNREACHABLE = ("unshared", "link-only")


def buckets(f):
    """Where is this file shared? Read from both representations. Pure.

    Slack records the same fact twice. The modern `shares` object carries a
    `public` map and a `private` map, each keyed by conversation id. The older
    `channels`, `groups` and `ims` arrays carry it split by conversation type:
    public channels, private channels, direct messages.

    Reading only one of them is the mistake this function exists to prevent.
    `channels` is empty for a file shared into a private channel, so a check
    built on it alone reports every correctly-shared private file as an orphan,
    produces a wall of false findings on its first run, and gets switched off.

    Returns {"public": [...], "private": [...], "dm": [...]}, sorted.
    """
    f = f or {}
    out = {"public": set(), "private": set(), "dm": set()}
    shares = f.get("shares")
    if isinstance(shares, dict):
        for name in ("public", "private"):
            group = shares.get(name)
            if isinstance(group, dict):
                out[name].update(str(k) for k in group if k)
    for name, legacy in (("public", "channels"), ("private", "groups"), ("dm", "ims")):
        for cid in f.get(legacy) or []:
            if cid:
                out[name].add(str(cid))
    return {k: sorted(v) for k, v in out.items()}


def share_targets(f):
    """Every conversation this file is shared into, deduplicated. Pure."""
    got = buckets(f)
    return sorted(set(got["public"]) | set(got["private"]) | set(got["dm"]))


def share_state(f):
    """Classify one file by the audience it actually has. Pure.

    Returns (state, detail). Four of the six states look like zero from a
    distance and only two of them are findings:

      unshared      no conversation of any kind. The file exists and nobody can
                    find it. This is the note.
      link-only     no conversation, and public_url_shared is true. Unreachable
                    inside Slack and readable by anyone on the internet, which
                    is worse and is a different repair.
      dm-only       shared, into direct messages only. A narrow audience is not
                    an absent one.
      private-only  shared, into private channels only. Also not a fault.
      shared        reachable from at least one channel.
      external      hosted somewhere else; Slack holds a link, not the bytes,
                    and the sharing question belongs to that other system.
    """
    f = f or {}
    if f.get("is_external"):
        return ("external", "hosted outside Slack, so Slack holds a reference rather "
                            "than the bytes and its share fields describe nothing")
    got = buckets(f)
    targets = sorted(set(got["public"]) | set(got["private"]) | set(got["dm"]))
    if not targets:
        if f.get("public_url_shared"):
            return ("link-only", "shared into no conversation and readable by anyone "
                                 "holding permalink_public. Invisible inside Slack and "
                                 "visible outside it, which is the worse half of both")
        return ("unshared", "no channel, no private channel and no DM. The upload "
                            "finished, the file exists, and completeUploadExternal was "
                            "called without channel_id")
    if not got["public"] and not got["private"]:
        return ("dm-only", "shared into %d direct message conversation(s) and no "
                           "channel. Only the people in those conversations can find "
                           "it" % len(got["dm"]))
    if not got["public"]:
        return ("private-only", "shared into %d private channel(s). That is a real "
                                "share, and a file in a private channel has an empty "
                                "channels array by design" % len(got["private"]))
    return ("shared", "shared into %d conversation(s)" % len(targets))


def orphan_rate(states):
    """What proportion of this app's own output has no audience? Pure.

    Returns (unreachable, total, percent). External files are excluded from the
    denominator: their sharing state is another system's, and leaving them in
    would move the number for a reason that has nothing to do with the bug.
    """
    counted = [s for s in states if s != "external"]
    total = len(counted)
    bad = sum(1 for s in counted if s in UNREACHABLE)
    return (bad, total, 0.0 if not total else round(100.0 * bad / total, 1))


def page_files(session, user, page_size, max_pages):
    """Page files.list. A read, and the only network call this script makes."""
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
    ap.add_argument("--user", default="",
                    help="owner to audit; defaults to this token's own user id")
    ap.add_argument("--all-users", action="store_true",
                    help="audit every file in the workspace rather than the app's own")
    ap.add_argument("--page-size", type=int, default=200)
    ap.add_argument("--max-pages", type=int, default=25)
    ap.add_argument("--show", default="unshared,link-only",
                    help="comma separated states to print in full")
    args = ap.parse_args()

    token = os.environ.get(args.token_env)
    if not token:
        log.error("set %s to a bot token with files:read", args.token_env)
        return 2

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

    wanted = {w.strip() for w in args.show.split(",") if w.strip()}
    states = []
    for f in files:
        state, detail = share_state(f)
        states.append(state)
        name = f.get("name") or f.get("title") or "?"
        line = ("state      %-14s %s %s  %s", state, f.get("id") or "?", name, detail)
        if state in UNREACHABLE:
            log.warning(*line)
        elif state in wanted:
            log.info(*line)

    bad, total, percent = orphan_rate(states)
    if not bad:
        log.info("verdict    clean          every file this app owns is shared somewhere")
        return 0
    log.warning("verdict    %d of %d file(s) owned by this app have no audience in "
                "Slack (%.1f%%)", bad, total, percent)
    log.warning("  repair: pass channel_id (a C id, not a name) to "
                "files.completeUploadExternal, with initial_comment beside it")
    log.warning("  repair: to share a file that already exists, post its permalink "
                "into the channel with the bot; Slack expands it and grants access")
    if "link-only" in states:
        log.warning("  repair: the link-only rows are also readable without a Slack "
                    "login; revoke those with files.revokePublicURL first")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-unshared-files.mjs",
"js": '''/**
 * Find the files your app uploaded and gave to nobody.
 *
 * Read only. One paginated GET against files.list and no writes at all: sharing
 * a file, revoking a link and deleting a file all need files:write, and all
 * three are printed here rather than performed. A bot token with files:read is
 * enough.
 *
 * The question is not whether the upload worked - it did, or the file would not
 * be in the list. The question is whether anything was passed to
 * files.completeUploadExternal to say where the file should go.
 */

const API = 'https://slack.com/api/';

// The two verdicts that mean nobody in the workspace can reach the file.
export const UNREACHABLE = ['unshared', 'link-only'];

/**
 * Where is this file shared? Read from both representations. Pure.
 *
 * Slack records the same fact twice: the modern `shares` object with `public`
 * and `private` maps keyed by conversation id, and the older `channels`,
 * `groups` and `ims` arrays split by conversation type. Reading only `channels`
 * reports every correctly-shared private file as an orphan, which is how a
 * check like this one gets switched off in its first week.
 */
export function buckets(f) {
  const file = f ?? {};
  const out = { public: new Set(), private: new Set(), dm: new Set() };
  const shares = file.shares;
  if (shares && typeof shares === 'object' && !Array.isArray(shares)) {
    for (const name of ['public', 'private']) {
      const group = shares[name];
      if (group && typeof group === 'object' && !Array.isArray(group)) {
        for (const key of Object.keys(group)) if (key) out[name].add(String(key));
      }
    }
  }
  for (const [name, legacy] of [['public', 'channels'], ['private', 'groups'],
    ['dm', 'ims']]) {
    for (const cid of file[legacy] ?? []) if (cid) out[name].add(String(cid));
  }
  return {
    public: [...out.public].sort(),
    private: [...out.private].sort(),
    dm: [...out.dm].sort(),
  };
}

/** Every conversation this file is shared into, deduplicated. Pure. */
export function shareTargets(f) {
  const got = buckets(f);
  return [...new Set([...got.public, ...got.private, ...got.dm])].sort();
}

/**
 * Classify one file by the audience it actually has. Pure.
 * Returns [state, detail]; only unshared and link-only are findings.
 */
export function shareState(f) {
  const file = f ?? {};
  if (file.is_external) {
    return ['external', 'hosted outside Slack, so Slack holds a reference rather than '
      + 'the bytes and its share fields describe nothing'];
  }
  const got = buckets(file);
  const targets = [...new Set([...got.public, ...got.private, ...got.dm])];
  if (!targets.length) {
    if (file.public_url_shared) {
      return ['link-only', 'shared into no conversation and readable by anyone holding '
        + 'permalink_public. Invisible inside Slack and visible outside it, which is '
        + 'the worse half of both'];
    }
    return ['unshared', 'no channel, no private channel and no DM. The upload finished, '
      + 'the file exists, and completeUploadExternal was called without channel_id'];
  }
  if (!got.public.length && !got.private.length) {
    return ['dm-only', `shared into ${got.dm.length} direct message conversation(s) and `
      + 'no channel. Only the people in those conversations can find it'];
  }
  if (!got.public.length) {
    return ['private-only', `shared into ${got.private.length} private channel(s). That `
      + 'is a real share, and a file in a private channel has an empty channels array '
      + 'by design'];
  }
  return ['shared', `shared into ${targets.length} conversation(s)`];
}

/**
 * What proportion of this app's own output has no audience? Pure.
 * Returns [unreachable, total, percent]. External files leave the denominator.
 */
export function orphanRate(states) {
  const counted = (states ?? []).filter((s) => s !== 'external');
  const total = counted.length;
  const bad = counted.filter((s) => UNREACHABLE.includes(s)).length;
  const percent = total ? Math.round((1000 * bad) / total) / 10 : 0;
  return [bad, total, percent];
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

  const owner = args.includes('--all-users')
    ? '' : (arg(args, '--user', '') || who.user_id || '');
  const [files, pages] = await pageFiles(headers, owner,
    Number(arg(args, '--page-size', '200')), Number(arg(args, '--max-pages', '25')));
  console.log(`files      ${files.length} file(s) owned by ${owner || 'anyone'}, over `
    + `${pages} page(s)`);

  const wanted = new Set(String(arg(args, '--show', 'unshared,link-only'))
    .split(',').map((w) => w.trim()).filter(Boolean));
  const states = [];
  for (const f of files) {
    const [state, detail] = shareState(f);
    states.push(state);
    const name = f.name ?? f.title ?? '?';
    const line = `state      ${state.padEnd(14)} ${f.id ?? '?'} ${name}  ${detail}`;
    if (UNREACHABLE.includes(state)) console.warn(line);
    else if (wanted.has(state)) console.log(line);
  }

  const [bad, total, percent] = orphanRate(states);
  if (!bad) {
    console.log('verdict    clean          every file this app owns is shared somewhere');
    return;
  }
  console.warn(`verdict    ${bad} of ${total} file(s) owned by this app have no `
    + `audience in Slack (${percent}%)`);
  console.warn('  repair: pass channel_id (a C id, not a name) to '
    + 'files.completeUploadExternal, with initial_comment beside it');
  console.warn('  repair: to share a file that already exists, post its permalink into '
    + 'the channel with the bot; Slack expands it and grants access');
  if (states.includes('link-only')) {
    console.warn('  repair: the link-only rows are also readable without a Slack login; '
      + 'revoke those with files.revokePublicURL first');
  }
  process.exitCode = 1;
}

// Only run when invoked directly, so importing this module in the tests does
// not execute main() and fail the file on a missing token.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The assertions that matter are the ones about not crying wolf. A file shared only into a private channel has an empty <code>channels</code> array and must not be reported as an orphan, so there is a test for exactly that shape, written from the field a naive checker would have read. <code>buckets</code> is tested against both representations separately and against a file that carries both, because Slack populates them inconsistently by upload path and by age. And <code>orphan_rate</code> is tested for what it leaves out of the denominator, since a proportion that moves when an external file appears is not measuring the bug.",
"test_py_file": "test_slack_unshared_files.py",
"test_py": '''from slack_unshared_files import buckets, orphan_rate, share_state, share_targets


def test_the_modern_shares_object_is_read():
    f = {"shares": {"public": {"C111": [{"ts": "1.1"}]}, "private": {}}}
    assert buckets(f)["public"] == ["C111"]
    assert share_targets(f) == ["C111"]


def test_the_legacy_arrays_are_read_too():
    f = {"channels": ["C111"], "groups": ["G222"], "ims": ["D333"]}
    got = buckets(f)
    assert got == {"public": ["C111"], "private": ["G222"], "dm": ["D333"]}


def test_both_representations_of_the_same_share_collapse_to_one_target():
    f = {"shares": {"public": {"C111": []}}, "channels": ["C111"]}
    assert share_targets(f) == ["C111"]


def test_an_empty_file_object_has_no_targets_and_does_not_raise():
    assert share_targets({}) == []
    assert share_targets(None) == []
    assert buckets({"shares": []})["public"] == []


def test_a_file_shared_nowhere_is_the_finding():
    state, detail = share_state({"id": "F1", "shares": {"public": {}, "private": {}}})
    assert state == "unshared"
    assert "channel_id" in detail


def test_a_private_channel_share_is_a_share_and_not_an_orphan():
    state, detail = share_state({"id": "F1", "channels": [], "groups": ["G222"]})
    assert state == "private-only"
    assert "empty channels array" in detail


def test_a_dm_only_share_is_narrow_rather_than_absent():
    assert share_state({"id": "F1", "ims": ["D333"]})[0] == "dm-only"


def test_a_public_url_on_a_file_nobody_can_reach_gets_its_own_verdict():
    state, detail = share_state({"id": "F1", "public_url_shared": True})
    assert state == "link-only"
    assert "permalink_public" in detail


def test_a_public_url_on_a_shared_file_is_not_this_note():
    assert share_state({"id": "F1", "channels": ["C111"],
                        "public_url_shared": True})[0] == "shared"


def test_an_external_file_is_not_judged_by_slack_share_fields():
    assert share_state({"id": "F1", "is_external": True})[0] == "external"


def test_the_rate_is_a_proportion_of_what_the_app_owns():
    bad, total, percent = orphan_rate(["unshared", "unshared", "shared", "shared"])
    assert (bad, total, percent) == (2, 4, 50.0)


def test_link_only_counts_as_unreachable_inside_slack():
    assert orphan_rate(["link-only", "shared"])[0] == 1


def test_external_files_leave_the_denominator_alone():
    assert orphan_rate(["unshared", "shared", "external"]) == (1, 2, 50.0)


def test_narrow_audiences_are_not_counted_as_orphans():
    assert orphan_rate(["dm-only", "private-only", "shared"])[0] == 0


def test_an_empty_run_reports_zero_rather_than_dividing_by_it():
    assert orphan_rate([]) == (0, 0, 0.0)
''',
"test_js_file": "slack-unshared-files.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  buckets, orphanRate, shareState, shareTargets,
} from './slack-unshared-files.mjs';

test('the modern shares object is read', () => {
  const f = { shares: { public: { C111: [{ ts: '1.1' }] }, private: {} } };
  assert.deepEqual(buckets(f).public, ['C111']);
  assert.deepEqual(shareTargets(f), ['C111']);
});

test('the legacy arrays are read too', () => {
  const f = { channels: ['C111'], groups: ['G222'], ims: ['D333'] };
  assert.deepEqual(buckets(f), { public: ['C111'], private: ['G222'], dm: ['D333'] });
});

test('both representations of the same share collapse to one target', () => {
  const f = { shares: { public: { C111: [] } }, channels: ['C111'] };
  assert.deepEqual(shareTargets(f), ['C111']);
});

test('an empty file object has no targets and does not throw', () => {
  assert.deepEqual(shareTargets({}), []);
  assert.deepEqual(shareTargets(null), []);
  assert.deepEqual(buckets({ shares: [] }).public, []);
});

test('a file shared nowhere is the finding', () => {
  const [state, detail] = shareState({ id: 'F1', shares: { public: {}, private: {} } });
  assert.equal(state, 'unshared');
  assert.match(detail, /channel_id/);
});

test('a private channel share is a share and not an orphan', () => {
  const [state, detail] = shareState({ id: 'F1', channels: [], groups: ['G222'] });
  assert.equal(state, 'private-only');
  assert.match(detail, /empty channels array/);
});

test('a dm only share is narrow rather than absent', () => {
  assert.equal(shareState({ id: 'F1', ims: ['D333'] })[0], 'dm-only');
});

test('a public url on a file nobody can reach gets its own verdict', () => {
  const [state, detail] = shareState({ id: 'F1', public_url_shared: true });
  assert.equal(state, 'link-only');
  assert.match(detail, /permalink_public/);
});

test('a public url on a shared file is not this note', () => {
  assert.equal(shareState({ id: 'F1', channels: ['C111'], public_url_shared: true })[0],
    'shared');
});

test('an external file is not judged by Slack share fields', () => {
  assert.equal(shareState({ id: 'F1', is_external: true })[0], 'external');
});

test('the rate is a proportion of what the app owns', () => {
  assert.deepEqual(orphanRate(['unshared', 'unshared', 'shared', 'shared']),
    [2, 4, 50]);
});

test('link only counts as unreachable inside Slack', () => {
  assert.equal(orphanRate(['link-only', 'shared'])[0], 1);
});

test('external files leave the denominator alone', () => {
  assert.deepEqual(orphanRate(['unshared', 'shared', 'external']), [1, 2, 50]);
});

test('narrow audiences are not counted as orphans', () => {
  assert.equal(orphanRate(['dm-only', 'private-only', 'shared'])[0], 0);
});

test('an empty run reports zero rather than dividing by it', () => {
  assert.deepEqual(orphanRate([]), [0, 0, 0]);
});
''',
"faq": [
 ("The upload returned ok and the file has a permalink. How is it not shared?",
  "Because uploading and sharing are two operations and only one of them happened. files.completeUploadExternal registers the file in the workspace, and it puts the file into a conversation only when you pass channel_id. Without that the file is complete, addressable and owned by the uploading identity, with an empty shares object. Everything the API told you was true; it just never said anything about an audience, because you never asked for one."),
 ("Can somebody find the file by searching Slack?",
  "No. Search follows the same permissions as everything else, so a file with no share targets is not in anyone's search results but the uploader's. This is the part that makes the bug expensive: the people looking for the file conclude they are searching wrong, and the app's own logs say the upload succeeded, so neither side has a reason to suspect the other."),
 ("We post the permalink in a message afterwards. Why does that not work?",
  "It does work, if the bot posts it into the conversation. Slack expands a file permalink in a message and grants that channel's members access to the file, which is the documented way to share after the fact. What does not work is putting the permalink somewhere outside Slack - a ticket, a wiki, an email - because a permalink is a page that enforces the file's permissions, and everyone who clicks it is told they do not have access."),
 ("Why does the script insist on reading both the shares object and the old arrays?",
  "Because either one alone gives a wrong answer. shares.public and shares.private are the current representation; channels, groups and ims are the older one, and which is populated has varied with the upload path and the file's age. Read only channels and every file shared into a private channel or a DM looks like an orphan. Read only shares and some older files look like orphans. The union is the only version of this check that is worth running twice."),
 ("Some of the orphans also have public_url_shared set. Is that better or worse?",
  "Worse, and the script gives it a different verdict for that reason. A file with no share targets and a public URL cannot be reached from inside Slack at all, so no member will ever stumble on it and mention it, while the public link keeps serving the bytes to anyone who has it. Revoke those first, then decide where the file should have been shared."),
],
"related": [
 ("/slack/public-file-links-exposed/", "the same file, made readable by strangers instead"),
 ("/slack/file-not-visible/", "shared properly, into a room your token is not in"),
 ("/slack/pagination-not-followed/", "why a first-page read finds nothing to report"),
],
"citations": [CITE_COMPLETE_UPLOAD, CITE_FILES_LIST, CITE_SDK_SHARES, CITE_WORKING_FILES],
})

GUIDES.append({
"slug": "file-not-visible",
"title": "not_visible: the file exists and your token is not in the room",
"description": "files.info answers not_visible, file_not_found, file_deleted and access_denied. Only one of those is about membership, and the API will not name the room.",
"h1": "not_visible: the file exists and your token is not in the room",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack not_visible files.info",
             "slack file_not_found vs not_visible",
             "slack file_shared event cannot read file",
             "slack access_denied file connect",
             "slack bot cannot see file in private channel"],
"deps": "Python 3.9+ with requests, or Node.js 18+; a bot token with files:read plus channels:read, groups:read, im:read and mpim:read to read its own membership",
"lead": "A <code>file_shared</code> event arrives. It carries a file id, a user, a channel and a timestamp, and the handler does the obvious next thing: <code>files.info</code> on that id, so it can index the attachment. Slack answers <code>{\"ok\": false, \"error\": \"not_visible\"}</code>.</p><p>The id is not wrong. Slack just handed it to you. The file has not been deleted, the token is valid, and <code>files:read</code> is granted. <code>not_visible</code> means the file exists and this token is not part of its audience &mdash; and unlike almost every other Slack error, it will not tell you a single thing about where the file actually lives.",
"short_answer": """<p>File visibility follows conversation visibility. A file is readable by a token that can see at least one conversation the file is shared into, and by nobody else. So a file shared only into a private channel your bot is not in, or into a DM between two other people, or into an externally shared Slack Connect channel, is invisible to you even though an event just told you it exists.</p>
<p><strong>Four errors come back from <code>files.info</code> and they are not interchangeable.</strong> <code>not_visible</code> means it exists and is not for you, and the repair is membership. <code>file_not_found</code> means no such file for this token, and the repair is a correct id or a correct workspace. <code>file_deleted</code> means it is gone. <code>access_denied</code> means a Slack Connect sharing policy, set by an admin, is the blocker rather than your app. Treating all four as <em>cannot read file</em> is what turns a five-minute fix into a week.</p>
<p>The part that hurts is that <code>not_visible</code> returns no file object, so the API cannot tell you which conversation to be invited to. <strong>The event can.</strong> A <code>file_shared</code> payload carries <code>channel_id</code>, and comparing that against <code>users.conversations</code> for the bot turns an unactionable error into the name of a channel and a request to be added to it.</p>""",
"problem": """<p>The reason this is confusing rather than merely annoying is that the event already told you about the file, and it is entirely reasonable to read that as permission. It is not. Events carry ids more liberally than the API grants access to what they name. Your app is subscribed to <code>file_shared</code>, the subscription fires for shares in conversations the app is in, and the payload is a pointer rather than a grant &mdash; and in the case of a file shared into several conversations at once, the pointer can outlive the one conversation you were entitled to see it in.</p>
<p>The second thing that goes wrong is the retry. <code>not_visible</code> is not a transient error and there is no amount of backoff that fixes it, but it looks exactly like one from the shape of the code: a call failed, so retry it. An indexer that treats it as retryable spends its rate limit on a file it will never be allowed to read, and the queue grows for a reason that has nothing to do with load. Only <code>file_deleted</code> and <code>not_visible</code> are permanent among the four; a <code>missing_scope</code> in the same position is permanent until somebody reinstalls, which is also not a retry.</p>
<p>Then there is the case that looks identical and is not a permission problem at all. <code>file_not_found</code> is what you get for an id that this token's workspace has never heard of &mdash; a file id copied from a different workspace, a truncated id, an id from a Grid workspace the app was not installed into. Slack deliberately answers <code>file_not_found</code> rather than <code>not_visible</code> there, because telling you that a file exists somewhere you cannot see would itself be a disclosure. The two errors are the API being careful, and reading them as the same thing throws away the care.</p>
<p>Slack Connect is the fourth flavour and the one nobody can fix in code. An externally shared channel is subject to sharing policy on both sides, and <code>access_denied</code>, along with the more explicit <code>slack_connect_file_link_sharing_blocked</code>, means an administrator has decided files do not cross that boundary. There is no scope for it and no membership change that helps. The right output is the sentence <em>this is a policy, ask an admin</em>, not another retry.</p>""",
"why": """<p><strong>not_visible and file_not_found are the whole note.</strong> One says <em>exists, not for you</em> and is fixed by an invitation. The other says <em>no such file here</em> and is fixed by looking at where the id came from. They are one character apart in a log line and a week apart in what you do about them, and a script that prints the raw error string and stops has done nothing that reading the log would not have.</p>
<p><strong>The API refuses to say where the file is, so the event has to.</strong> A <code>not_visible</code> response contains no <code>channels</code>, no <code>groups</code>, no <code>ims</code> &mdash; nothing. That is correct behaviour and it is also why so many teams get stuck: there is no read that turns the error into an action. The <code>channel_id</code> on the event payload is the one place the room is named, which is why this script takes saved event payloads as input rather than bare file ids.</p>
<p><strong>Membership is a set intersection, and it is worth doing explicitly.</strong> <code>users.conversations</code> for the bot, across <code>public_channel</code>, <code>private_channel</code>, <code>im</code> and <code>mpim</code>, is the set of rooms this token can see into. The room from the event either is in that set or is not, and the answer is either <em>you are a member and something else is wrong</em> or <em>invite the bot to this channel</em>.</p>
<p><strong>A bot that cannot enumerate private channels cannot tell the two apart, and should say so.</strong> Without <code>groups:read</code>, <code>users.conversations</code> will not return private channels, so a private room the bot is genuinely in looks like a room it is not in. The script checks the granted scopes first and marks the membership answer as undecidable rather than reporting a wrong one confidently.</p>
<p><strong>None of these four errors is retryable, and three of them are not even permanent in the same way.</strong> The script labels each verdict with what to do next &mdash; invite, correct the id, drop the reference, ask an admin &mdash; because the single most common wrong response to all four is a backoff loop.</p>
<p><strong>A file you can read is not the end of the check.</strong> If <code>files.info</code> succeeds, the useful follow-up is whether the conversations the file is shared into overlap with the ones your bot is in, because a file readable today through one shared channel becomes unreadable the moment the bot is removed from it. That is the same error arriving later.</p>""",
"steps": [
 {"h": "Keep the event payloads, not just the file ids",
  "body": """<p>The script reads a JSON array of saved <code>file_shared</code> events with <code>--events</code>. <code>event_rooms</code> pulls <code>channel_id</code>, <code>channel</code> and <code>item.channel</code> out of whatever shape the payload has. That field is the only place the room is named once the API has said <code>not_visible</code>, so an indexer that logs the id and discards the envelope has thrown away its own diagnosis.</p>"""},
 {"h": "Confirm the scopes before believing the membership answer",
  "body": """<p><code>auth.test</code> returns <code>X-OAuth-Scopes</code> in the response headers. Without <code>groups:read</code> the bot cannot list private channels, so <em>not a member</em> and <em>cannot tell</em> look the same. The script reports which one it is looking at rather than assuming.</p>"""},
 {"h": "Sort the four errors before doing anything else",
  "body": """<p><code>visibility</code> maps the <code>files.info</code> response to <code>readable</code>, <code>not-in-the-room</code>, <code>unknown-id</code>, <code>deleted</code>, <code>connect-policy</code>, <code>credential</code> or <code>other</code>. Everything after this step branches on that verdict, and no branch of it is a retry.</p>"""},
 {"h": "Intersect the room from the event with the rooms the bot is in",
  "body": """<p><code>join_gap</code> takes the rooms named by the event and the rooms from <code>users.conversations</code>, and returns <code>member</code>, <code>outside</code> or <code>nowhere</code>. <code>outside</code> is the actionable one: it names a channel, and the repair is one invitation.</p>"""},
 {"h": "Read member plus not_visible as the interesting contradiction",
  "body": """<p>If the bot is in the room the event named and <code>files.info</code> still says <code>not_visible</code>, the file was shared into more than one conversation and the share you were told about is not the one that survived, or the file moved to a Connect channel. That combination is rare and worth printing loudly, because it is the only case here that is not a one-line fix.</p>"""},
 {"h": "Take the repair per verdict rather than per file",
  "body": """<p><code>repair_for</code> prints the sentence that goes with the verdict: invite the bot, check where the id came from, drop the stored reference, or ask an admin about Slack Connect file sharing. Four verdicts, four repairs, and the reason to separate them is that only one of them is yours to carry out.</p>"""},
],
"verify": """<p>Run it over the events your handler failed on. The output you want names a channel, because a channel is something you can ask to be added to.</p>
<pre><code class="language-bash">python3 slack_file_visibility.py --events failed-events.json
# identity   U07BOT9QD in Northwind
# scope      files:read groups:read granted
# member     bot is in 41 conversation(s)
# check      not-in-the-room F08K2M4QX  exists, and this token is not part of its
#                           audience. The API will not say where it lives
# room       outside        F08K2M4QX  the event named C05SEC9QT and the bot is not in it
#   repair: invite the bot to C05SEC9QT, or have the file shared into a channel it is in
# check      unknown-id     F04ZZZ1QQ  no such file for this token. Slack answers
#                           file_not_found rather than admitting it exists elsewhere
#   repair: check the workspace the id came from before changing any permission
# check      connect-policy F08K3P2QW  a Slack Connect sharing policy is the blocker
#   repair: this is an admin setting on one side of the external channel, not a scope
# verdict    3 of 12 file(s) unreadable; 1 of them is one invitation away</code></pre>""",
"code_intro": "Two reads and three pure functions. <code>visibility</code> is the error taxonomy and does the bulk of the work, because the whole cost of this bug is four errors being treated as one. <code>event_rooms</code> exists because the API refuses to name the room and the event payload does not. <code>join_gap</code> is a set intersection, kept as its own function so the case where the bot <em>is</em> in the room and still cannot read the file is a named outcome rather than a gap in an if-statement.",
"py_file": "slack_file_visibility.py",
"py": '''"""Sort the reasons your token cannot read a Slack file, and name the room.

Read only. files.info and users.conversations are reads; nothing here shares,
downloads or deletes anything, and the file's bytes are never fetched.

The point of the script is that four different errors mean four different
things, and that the one which means "you are not in the room" is the only one
Slack will not give you a room for. The room comes from the file_shared event
payload instead, which is why this takes saved events rather than bare ids.
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_file_visibility")

API = "https://slack.com/api/"

# The taxonomy. Every value is (verdict, detail), and no verdict here is
# retryable: three are permanent and one wants a human with admin rights.
ERRORS = {
    "not_visible": (
        "not-in-the-room",
        "exists, and this token is not part of its audience. The API will not say "
        "where it lives, because saying so would be the disclosure it is refusing"),
    "file_not_found": (
        "unknown-id",
        "no such file for this token. Slack answers file_not_found rather than "
        "admitting a file exists somewhere you cannot see, so this is usually an id "
        "from another workspace or a truncated one"),
    "file_deleted": (
        "deleted",
        "the file is gone. The id stays a valid-looking string forever, which is why "
        "stored references rot rather than fail loudly"),
    "access_denied": (
        "connect-policy",
        "a Slack Connect sharing policy is the blocker rather than your app. An "
        "administrator on one side of the external channel decided files do not cross "
        "it"),
    "slack_connect_file_link_sharing_blocked": (
        "connect-policy",
        "file link sharing is switched off for this external channel by policy"),
    "slack_connect_canvas_sharing_blocked": (
        "connect-policy",
        "canvas sharing is switched off for this external channel by policy"),
    "missing_scope": (
        "credential",
        "files:read is not granted to this token. That is a reinstall, not a retry"),
    "not_authed": ("credential", "no token reached Slack on this call"),
    "invalid_auth": ("credential", "the token is not valid for this workspace"),
    "token_revoked": ("credential", "the app was uninstalled and the token is dead"),
    "account_inactive": ("credential", "the installing user was deactivated"),
}

REPAIRS = {
    "not-in-the-room": "invite the bot to the conversation the file lives in, or have "
                       "the file shared into a channel the bot is already in",
    "unknown-id": "check the workspace the id came from before changing any permission",
    "deleted": "drop the stored reference; subscribe to file_deleted so the next one "
               "goes away on its own",
    "connect-policy": "this is an admin setting on one side of the external channel, "
                      "not a scope and not a code change",
    "credential": "grant files:read and reinstall; no membership change helps here",
    "other": "read the raw error string, then the method reference for files.info",
    "malformed": "the response carried neither ok nor an error, which is a transport "
                 "problem rather than a Slack one",
}


def visibility(payload):
    """What did files.info actually say? Pure.

    Returns (verdict, detail). The two verdicts this function exists to keep
    apart are not-in-the-room and unknown-id: one is fixed by an invitation and
    the other by looking at where the id came from, they are one word apart in
    a log line, and every retry loop ever written treats them as the same.
    """
    p = payload or {}
    if p.get("ok") is True:
        return ("readable", "files.info returned the file object")
    error = str(p.get("error") or "").strip()
    if not error:
        return ("malformed", "no ok and no error field in the response")
    if error in ERRORS:
        return ERRORS[error]
    return ("other", "%s is not one of the four visibility errors; treat it on its own "
                     "terms" % error)


def event_rooms(event):
    """Which conversation did the event say the file was shared into? Pure.

    The only place the room is named once files.info has answered not_visible.
    file_shared payloads have moved fields around over the years, so all three
    shapes are read: the modern channel_id, the older bare channel, and the
    item wrapper some subscriptions still deliver.
    """
    e = event or {}
    inner = e.get("event") if isinstance(e.get("event"), dict) else e
    out = []
    for holder in (inner, inner.get("item") if isinstance(inner.get("item"), dict)
                   else {}, inner.get("file") if isinstance(inner.get("file"), dict)
                   else {}):
        for key in ("channel_id", "channel"):
            value = holder.get(key)
            if isinstance(value, str) and value:
                out.append(value)
    seen, unique = set(), []
    for room in out:
        if room not in seen:
            seen.add(room)
            unique.append(room)
    return unique


def join_gap(rooms, my_rooms, decidable=True):
    """Is the bot in any room the event named? Pure.

    Returns (verdict, rooms). member means the bot is in one of them and the
    file is still unreadable, which is the interesting contradiction. outside
    names the channel to be invited to. nowhere means the event never said.
    undecidable means the token cannot enumerate its own private channels, so
    "not a member" and "cannot tell" are the same answer and must not be
    reported as the first one.
    """
    theirs = [str(r) for r in rooms or [] if r]
    if not theirs:
        return ("nowhere", [])
    if not decidable:
        return ("undecidable", sorted(set(theirs)))
    mine = {str(r) for r in my_rooms or [] if r}
    overlap = sorted({r for r in theirs if r in mine})
    if overlap:
        return ("member", overlap)
    return ("outside", sorted(set(theirs)))


def repair_for(verdict):
    """The sentence that goes with a verdict. Pure."""
    return REPAIRS.get(verdict, REPAIRS["other"])


def load_events(path):
    """Saved file_shared payloads, or bare ids, whichever you kept."""
    raw = json.loads(open(path, encoding="utf-8").read())
    if isinstance(raw, dict):
        raw = raw.get("events") or raw.get("payloads") or [raw]
    out = []
    for row in raw or []:
        if isinstance(row, str):
            out.append({"file_id": row})
        elif isinstance(row, dict):
            out.append(row)
    return out


def file_id_of(event):
    """The file id, from whichever of the three shapes carries it."""
    e = event or {}
    inner = e.get("event") if isinstance(e.get("event"), dict) else e
    for holder in (inner, inner.get("file") if isinstance(inner.get("file"), dict)
                   else {}):
        for key in ("file_id", "id"):
            value = holder.get(key)
            if isinstance(value, str) and value:
                return value
    return ""


def bot_conversations(session, limit):
    """The rooms this token can see into. A read, paginated by cursor."""
    rooms, cursor = set(), ""
    for _ in range(limit):
        params = {"types": "public_channel,private_channel,im,mpim", "limit": "200",
                  "exclude_archived": "false"}
        if cursor:
            params["cursor"] = cursor
        body = session.get(API + "users.conversations", params=params,
                           timeout=30).json()
        if body.get("ok") is not True:
            log.warning("member     unavailable    %s", body.get("error"))
            return rooms, False
        rooms.update(str((c or {}).get("id") or "") for c in body.get("channels") or [])
        cursor = ((body.get("response_metadata") or {}).get("next_cursor") or "")
        if not cursor:
            break
    rooms.discard("")
    return rooms, True


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--events", default="",
                    help="a JSON file of saved file_shared payloads, or of file ids")
    ap.add_argument("--file", action="append", default=[],
                    help="one file id to check; repeatable")
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN")
    ap.add_argument("--max-pages", type=int, default=20)
    args = ap.parse_args()

    events = load_events(args.events) if args.events else []
    events.extend({"file_id": f} for f in args.file)
    if not events:
        log.error("pass --events FILE, or one or more --file F...")
        return 2

    token = os.environ.get(args.token_env)
    if not token:
        log.error("set %s to a bot token with files:read", args.token_env)
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + token})
    who_resp = s.get(API + "auth.test", timeout=30)
    who = who_resp.json()
    if who.get("ok") is not True:
        log.error("auth.test  unavailable    %s", who.get("error"))
        return 2
    log.info("identity   %s in %s", who.get("user_id"), who.get("team"))

    granted = {sc.strip() for sc in
               (who_resp.headers.get("x-oauth-scopes") or "").split(",") if sc.strip()}
    log.info("scope      %s granted",
             " ".join(sorted(granted & {"files:read", "groups:read"})) or "neither")
    decidable = "groups:read" in granted or not granted
    if not decidable:
        log.warning("scope      groups:read is missing, so a private channel the bot is "
                    "in reads the same as one it is not in")

    my_rooms, listed = bot_conversations(s, args.max_pages)
    if listed:
        log.info("member     bot is in %d conversation(s)", len(my_rooms))

    unreadable, invitable = 0, 0
    for event in events:
        fid = file_id_of(event)
        if not fid:
            log.warning("check      no-file-id     an event with no file id in it")
            continue
        body = s.get(API + "files.info", params={"file": fid}, timeout=30).json()
        verdict, detail = visibility(body)
        if verdict == "readable":
            log.info("check      readable       %s", fid)
            continue
        unreadable += 1
        log.warning("check      %-14s %s  %s", verdict, fid, detail)
        if verdict != "not-in-the-room":
            log.warning("  repair: %s", repair_for(verdict))
            continue
        where, rooms = join_gap(event_rooms(event), my_rooms, decidable and listed)
        if where == "outside":
            invitable += 1
            log.warning("room       outside        %s  the event named %s and the bot "
                        "is not in it", fid, ", ".join(rooms))
            log.warning("  repair: invite the bot to %s, or have the file shared into a "
                        "channel it is in", rooms[0])
        elif where == "member":
            log.warning("room       member         %s  the bot IS in %s and still "
                        "cannot read the file, so the share you were told about is not "
                        "the one that survived", fid, ", ".join(rooms))
        elif where == "undecidable":
            log.warning("room       undecidable    %s  named %s, and this token cannot "
                        "enumerate private channels", fid, ", ".join(rooms))
        else:
            log.warning("room       nowhere        %s  the event never named a channel, "
                        "so keep the whole payload next time", fid)
            log.warning("  repair: %s", repair_for(verdict))

    if not unreadable:
        log.info("verdict    clean          every file in this run is readable")
        return 0
    log.warning("verdict    %d of %d file(s) unreadable; %d of them %s one invitation "
                "away", unreadable, len(events), invitable,
                "is" if invitable == 1 else "are")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-file-visibility.mjs",
"js": '''/**
 * Sort the reasons your token cannot read a Slack file, and name the room.
 *
 * Read only. files.info and users.conversations are reads; nothing here shares,
 * downloads or deletes anything, and the file's bytes are never fetched.
 *
 * Four different errors mean four different things, and the one that means "you
 * are not in the room" is the only one Slack will not give you a room for. The
 * room comes from the file_shared event payload instead.
 */

import { readFile } from 'node:fs/promises';

const API = 'https://slack.com/api/';

// The taxonomy. No verdict here is retryable.
export const ERRORS = {
  not_visible: ['not-in-the-room',
    'exists, and this token is not part of its audience. The API will not say where '
    + 'it lives, because saying so would be the disclosure it is refusing'],
  file_not_found: ['unknown-id',
    'no such file for this token. Slack answers file_not_found rather than admitting '
    + 'a file exists somewhere you cannot see, so this is usually an id from another '
    + 'workspace or a truncated one'],
  file_deleted: ['deleted',
    'the file is gone. The id stays a valid-looking string forever, which is why '
    + 'stored references rot rather than fail loudly'],
  access_denied: ['connect-policy',
    'a Slack Connect sharing policy is the blocker rather than your app. An '
    + 'administrator on one side of the external channel decided files do not cross it'],
  slack_connect_file_link_sharing_blocked: ['connect-policy',
    'file link sharing is switched off for this external channel by policy'],
  slack_connect_canvas_sharing_blocked: ['connect-policy',
    'canvas sharing is switched off for this external channel by policy'],
  missing_scope: ['credential',
    'files:read is not granted to this token. That is a reinstall, not a retry'],
  not_authed: ['credential', 'no token reached Slack on this call'],
  invalid_auth: ['credential', 'the token is not valid for this workspace'],
  token_revoked: ['credential', 'the app was uninstalled and the token is dead'],
  account_inactive: ['credential', 'the installing user was deactivated'],
};

export const REPAIRS = {
  'not-in-the-room': 'invite the bot to the conversation the file lives in, or have '
    + 'the file shared into a channel the bot is already in',
  'unknown-id': 'check the workspace the id came from before changing any permission',
  deleted: 'drop the stored reference; subscribe to file_deleted so the next one goes '
    + 'away on its own',
  'connect-policy': 'this is an admin setting on one side of the external channel, not '
    + 'a scope and not a code change',
  credential: 'grant files:read and reinstall; no membership change helps here',
  other: 'read the raw error string, then the method reference for files.info',
  malformed: 'the response carried neither ok nor an error, which is a transport '
    + 'problem rather than a Slack one',
};

/**
 * What did files.info actually say? Pure.
 * Returns [verdict, detail]; not-in-the-room and unknown-id are the pair that
 * every retry loop ever written treats as the same thing.
 */
export function visibility(payload) {
  const p = payload ?? {};
  if (p.ok === true) return ['readable', 'files.info returned the file object'];
  const error = String(p.error ?? '').trim();
  if (!error) return ['malformed', 'no ok and no error field in the response'];
  if (Object.prototype.hasOwnProperty.call(ERRORS, error)) return ERRORS[error];
  return ['other', `${error} is not one of the four visibility errors; treat it on its `
    + 'own terms'];
}

/**
 * Which conversation did the event say the file was shared into? Pure.
 * The only place the room is named once files.info has answered not_visible.
 */
export function eventRooms(event) {
  const e = event ?? {};
  const inner = (e.event && typeof e.event === 'object') ? e.event : e;
  const holders = [inner];
  for (const key of ['item', 'file']) {
    if (inner[key] && typeof inner[key] === 'object') holders.push(inner[key]);
  }
  const out = [];
  for (const holder of holders) {
    for (const key of ['channel_id', 'channel']) {
      const value = holder[key];
      if (typeof value === 'string' && value) out.push(value);
    }
  }
  return [...new Set(out)];
}

/**
 * Is the bot in any room the event named? Pure.
 * Returns [verdict, rooms]: member, outside, nowhere or undecidable.
 */
export function joinGap(rooms, myRooms, decidable = true) {
  const theirs = (rooms ?? []).filter(Boolean).map(String);
  if (!theirs.length) return ['nowhere', []];
  if (!decidable) return ['undecidable', [...new Set(theirs)].sort()];
  const mine = new Set((myRooms ?? []).filter(Boolean).map(String));
  const overlap = [...new Set(theirs.filter((r) => mine.has(r)))].sort();
  if (overlap.length) return ['member', overlap];
  return ['outside', [...new Set(theirs)].sort()];
}

/** The sentence that goes with a verdict. Pure. */
export function repairFor(verdict) {
  return REPAIRS[verdict] ?? REPAIRS.other;
}

/** The file id, from whichever of the three shapes carries it. Pure. */
export function fileIdOf(event) {
  const e = event ?? {};
  const inner = (e.event && typeof e.event === 'object') ? e.event : e;
  const holders = [inner];
  if (inner.file && typeof inner.file === 'object') holders.push(inner.file);
  for (const holder of holders) {
    for (const key of ['file_id', 'id']) {
      const value = holder[key];
      if (typeof value === 'string' && value) return value;
    }
  }
  return '';
}

function arg(args, name, fallback = null) {
  const i = args.indexOf(name);
  return i === -1 ? fallback : args[i + 1];
}

function argAll(args, name) {
  const out = [];
  for (let i = 0; i < args.length; i += 1) {
    if (args[i] === name && args[i + 1] !== undefined) out.push(args[i + 1]);
  }
  return out;
}

function loadEvents(raw) {
  let rows = raw;
  if (rows && !Array.isArray(rows) && typeof rows === 'object') {
    rows = rows.events ?? rows.payloads ?? [rows];
  }
  const out = [];
  for (const row of rows ?? []) {
    if (typeof row === 'string') out.push({ file_id: row });
    else if (row && typeof row === 'object') out.push(row);
  }
  return out;
}

async function botConversations(headers, maxPages) {
  const rooms = new Set();
  let cursor = '';
  for (let i = 0; i < maxPages; i += 1) {
    const params = new URLSearchParams({
      types: 'public_channel,private_channel,im,mpim',
      limit: '200',
      exclude_archived: 'false',
    });
    if (cursor) params.set('cursor', cursor);
    const body = await (await fetch(`${API}users.conversations?${params}`,
      { headers })).json();
    if (body.ok !== true) {
      console.warn(`member     unavailable    ${body.error}`);
      return [rooms, false];
    }
    for (const c of body.channels ?? []) if (c?.id) rooms.add(String(c.id));
    cursor = (body.response_metadata ?? {}).next_cursor ?? '';
    if (!cursor) break;
  }
  return [rooms, true];
}

async function main() {
  const args = process.argv.slice(2);
  const eventsFile = arg(args, '--events', '');
  const events = eventsFile
    ? loadEvents(JSON.parse(await readFile(eventsFile, 'utf8'))) : [];
  events.push(...argAll(args, '--file').map((f) => ({ file_id: f })));
  if (!events.length) {
    console.error('pass --events FILE, or one or more --file F...');
    process.exitCode = 2;
    return;
  }

  const tokenEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
  const token = process.env[tokenEnv];
  if (!token) {
    console.error(`set ${tokenEnv} to a bot token with files:read`);
    process.exitCode = 2;
    return;
  }
  const headers = { Authorization: `Bearer ${token}` };
  const whoResp = await fetch(`${API}auth.test`, { headers });
  const who = await whoResp.json();
  if (who.ok !== true) {
    console.error(`auth.test  unavailable    ${who.error}`);
    process.exitCode = 2;
    return;
  }
  console.log(`identity   ${who.user_id} in ${who.team}`);

  const granted = new Set((whoResp.headers.get('x-oauth-scopes') ?? '')
    .split(',').map((sc) => sc.trim()).filter(Boolean));
  const shown = ['files:read', 'groups:read'].filter((sc) => granted.has(sc));
  console.log(`scope      ${shown.join(' ') || 'neither'} granted`);
  const decidable = granted.has('groups:read') || granted.size === 0;
  if (!decidable) {
    console.warn('scope      groups:read is missing, so a private channel the bot is in '
      + 'reads the same as one it is not in');
  }

  const [myRooms, listed] = await botConversations(headers,
    Number(arg(args, '--max-pages', '20')));
  if (listed) console.log(`member     bot is in ${myRooms.size} conversation(s)`);

  let unreadable = 0;
  let invitable = 0;
  for (const event of events) {
    const fid = fileIdOf(event);
    if (!fid) {
      console.warn('check      no-file-id     an event with no file id in it');
      continue;
    }
    const params = new URLSearchParams({ file: fid });
    const body = await (await fetch(`${API}files.info?${params}`, { headers })).json();
    const [verdict, detail] = visibility(body);
    if (verdict === 'readable') {
      console.log(`check      readable       ${fid}`);
      continue;
    }
    unreadable += 1;
    console.warn(`check      ${verdict.padEnd(14)} ${fid}  ${detail}`);
    if (verdict !== 'not-in-the-room') {
      console.warn(`  repair: ${repairFor(verdict)}`);
      continue;
    }
    const [where, rooms] = joinGap(eventRooms(event), [...myRooms],
      decidable && listed);
    if (where === 'outside') {
      invitable += 1;
      console.warn(`room       outside        ${fid}  the event named ${rooms.join(', ')} `
        + 'and the bot is not in it');
      console.warn(`  repair: invite the bot to ${rooms[0]}, or have the file shared `
        + 'into a channel it is in');
    } else if (where === 'member') {
      console.warn(`room       member         ${fid}  the bot IS in ${rooms.join(', ')} `
        + 'and still cannot read the file, so the share you were told about is not the '
        + 'one that survived');
    } else if (where === 'undecidable') {
      console.warn(`room       undecidable    ${fid}  named ${rooms.join(', ')}, and `
        + 'this token cannot enumerate private channels');
    } else {
      console.warn(`room       nowhere        ${fid}  the event never named a channel, `
        + 'so keep the whole payload next time');
      console.warn(`  repair: ${repairFor(verdict)}`);
    }
  }

  if (!unreadable) {
    console.log('verdict    clean          every file in this run is readable');
    return;
  }
  console.warn(`verdict    ${unreadable} of ${events.length} file(s) unreadable; `
    + `${invitable} of them ${invitable === 1 ? 'is' : 'are'} one invitation away`);
  process.exitCode = 1;
}

// Only run when invoked directly, so importing this module in the tests does
// not execute main() and fail the file on a missing token.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Two assertions carry this suite. The first is that <code>not_visible</code> and <code>file_not_found</code> never come back as the same verdict, written as an explicit inequality rather than as two separate checks, because the whole note is that those two get merged. The second is that <code>join_gap</code> refuses to answer when the token cannot enumerate private channels: <em>not a member</em> and <em>cannot tell</em> are different, and a script that confidently reports the first when it means the second sends somebody to add a bot that is already there.",
"test_py_file": "test_slack_file_visibility.py",
"test_py": '''from slack_file_visibility import (event_rooms, file_id_of, join_gap, repair_for,
                                   visibility)


def test_an_ok_response_is_readable():
    assert visibility({"ok": True, "file": {"id": "F1"}})[0] == "readable"


def test_not_visible_is_about_the_room_and_says_the_api_will_not_name_it():
    verdict, detail = visibility({"ok": False, "error": "not_visible"})
    assert verdict == "not-in-the-room"
    assert "will not say where it lives" in detail


def test_file_not_found_is_about_the_id_and_not_about_permission():
    verdict, detail = visibility({"ok": False, "error": "file_not_found"})
    assert verdict == "unknown-id"
    assert "another workspace" in detail


def test_the_two_errors_this_note_exists_for_are_never_the_same_verdict():
    assert visibility({"ok": False, "error": "not_visible"})[0] \\
        != visibility({"ok": False, "error": "file_not_found"})[0]


def test_a_deleted_file_is_its_own_verdict():
    assert visibility({"ok": False, "error": "file_deleted"})[0] == "deleted"


def test_every_slack_connect_refusal_lands_on_policy():
    for error in ("access_denied", "slack_connect_file_link_sharing_blocked",
                  "slack_connect_canvas_sharing_blocked"):
        assert visibility({"ok": False, "error": error})[0] == "connect-policy"


def test_a_credential_problem_is_not_a_visibility_problem():
    for error in ("missing_scope", "not_authed", "invalid_auth", "token_revoked"):
        assert visibility({"ok": False, "error": error})[0] == "credential"


def test_an_unknown_error_is_not_forced_into_the_taxonomy():
    verdict, detail = visibility({"ok": False, "error": "ratelimited"})
    assert verdict == "other"
    assert "ratelimited" in detail


def test_a_response_with_neither_ok_nor_error_is_malformed():
    assert visibility({})[0] == "malformed"
    assert visibility(None)[0] == "malformed"


def test_every_verdict_has_a_repair_and_none_of_them_is_a_retry():
    for verdict in ("not-in-the-room", "unknown-id", "deleted", "connect-policy",
                    "credential", "other", "malformed"):
        assert repair_for(verdict)
        assert "retry" not in repair_for(verdict).lower()


def test_the_room_is_read_from_all_three_event_shapes():
    assert event_rooms({"channel_id": "C111"}) == ["C111"]
    assert event_rooms({"event": {"channel_id": "C222"}}) == ["C222"]
    assert event_rooms({"event": {"item": {"channel": "C333"}}}) == ["C333"]


def test_a_repeated_room_is_named_once():
    assert event_rooms({"channel_id": "C111",
                        "item": {"channel": "C111"}}) == ["C111"]


def test_an_event_with_no_channel_names_nothing():
    assert event_rooms({"file_id": "F1"}) == []
    assert event_rooms(None) == []


def test_the_file_id_is_read_from_the_wrapper_or_the_file_object():
    assert file_id_of({"file_id": "F1"}) == "F1"
    assert file_id_of({"event": {"file": {"id": "F2"}}}) == "F2"
    assert file_id_of({}) == ""


def test_a_room_the_bot_is_not_in_is_the_actionable_answer():
    verdict, rooms = join_gap(["C111"], {"C999"})
    assert verdict == "outside"
    assert rooms == ["C111"]


def test_a_room_the_bot_is_in_is_the_interesting_contradiction():
    assert join_gap(["C111"], {"C111", "C999"}) == ("member", ["C111"])


def test_an_event_that_named_no_room_leaves_nowhere_to_go():
    assert join_gap([], {"C111"}) == ("nowhere", [])


def test_membership_is_undecidable_without_the_scope_to_enumerate_it():
    verdict, rooms = join_gap(["C111"], set(), decidable=False)
    assert verdict == "undecidable"
    assert rooms == ["C111"]


def test_undecidable_is_never_reported_as_outside():
    assert join_gap(["C111"], set(), decidable=False)[0] \\
        != join_gap(["C111"], set(), decidable=True)[0]
''',
"test_js_file": "slack-file-visibility.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  eventRooms, fileIdOf, joinGap, repairFor, visibility,
} from './slack-file-visibility.mjs';

test('an ok response is readable', () => {
  assert.equal(visibility({ ok: true, file: { id: 'F1' } })[0], 'readable');
});

test('not_visible is about the room and says the API will not name it', () => {
  const [verdict, detail] = visibility({ ok: false, error: 'not_visible' });
  assert.equal(verdict, 'not-in-the-room');
  assert.match(detail, /will not say where it lives/);
});

test('file_not_found is about the id and not about permission', () => {
  const [verdict, detail] = visibility({ ok: false, error: 'file_not_found' });
  assert.equal(verdict, 'unknown-id');
  assert.match(detail, /another workspace/);
});

test('the two errors this note exists for are never the same verdict', () => {
  assert.notEqual(visibility({ ok: false, error: 'not_visible' })[0],
    visibility({ ok: false, error: 'file_not_found' })[0]);
});

test('a deleted file is its own verdict', () => {
  assert.equal(visibility({ ok: false, error: 'file_deleted' })[0], 'deleted');
});

test('every Slack Connect refusal lands on policy', () => {
  for (const error of ['access_denied', 'slack_connect_file_link_sharing_blocked',
    'slack_connect_canvas_sharing_blocked']) {
    assert.equal(visibility({ ok: false, error })[0], 'connect-policy');
  }
});

test('a credential problem is not a visibility problem', () => {
  for (const error of ['missing_scope', 'not_authed', 'invalid_auth', 'token_revoked']) {
    assert.equal(visibility({ ok: false, error })[0], 'credential');
  }
});

test('an unknown error is not forced into the taxonomy', () => {
  const [verdict, detail] = visibility({ ok: false, error: 'ratelimited' });
  assert.equal(verdict, 'other');
  assert.match(detail, /ratelimited/);
});

test('a response with neither ok nor error is malformed', () => {
  assert.equal(visibility({})[0], 'malformed');
  assert.equal(visibility(null)[0], 'malformed');
});

test('a prototype key is not mistaken for a Slack error', () => {
  assert.equal(visibility({ ok: false, error: 'constructor' })[0], 'other');
});

test('every verdict has a repair and none of them is a retry', () => {
  for (const verdict of ['not-in-the-room', 'unknown-id', 'deleted', 'connect-policy',
    'credential', 'other', 'malformed']) {
    assert.ok(repairFor(verdict));
    assert.doesNotMatch(repairFor(verdict).toLowerCase(), /retry/);
  }
});

test('the room is read from all three event shapes', () => {
  assert.deepEqual(eventRooms({ channel_id: 'C111' }), ['C111']);
  assert.deepEqual(eventRooms({ event: { channel_id: 'C222' } }), ['C222']);
  assert.deepEqual(eventRooms({ event: { item: { channel: 'C333' } } }), ['C333']);
});

test('a repeated room is named once', () => {
  assert.deepEqual(eventRooms({ channel_id: 'C111', item: { channel: 'C111' } }),
    ['C111']);
});

test('an event with no channel names nothing', () => {
  assert.deepEqual(eventRooms({ file_id: 'F1' }), []);
  assert.deepEqual(eventRooms(null), []);
});

test('the file id is read from the wrapper or the file object', () => {
  assert.equal(fileIdOf({ file_id: 'F1' }), 'F1');
  assert.equal(fileIdOf({ event: { file: { id: 'F2' } } }), 'F2');
  assert.equal(fileIdOf({}), '');
});

test('a room the bot is not in is the actionable answer', () => {
  const [verdict, rooms] = joinGap(['C111'], ['C999']);
  assert.equal(verdict, 'outside');
  assert.deepEqual(rooms, ['C111']);
});

test('a room the bot is in is the interesting contradiction', () => {
  assert.deepEqual(joinGap(['C111'], ['C111', 'C999']), ['member', ['C111']]);
});

test('an event that named no room leaves nowhere to go', () => {
  assert.deepEqual(joinGap([], ['C111']), ['nowhere', []]);
});

test('membership is undecidable without the scope to enumerate it', () => {
  const [verdict, rooms] = joinGap(['C111'], [], false);
  assert.equal(verdict, 'undecidable');
  assert.deepEqual(rooms, ['C111']);
});

test('undecidable is never reported as outside', () => {
  assert.notEqual(joinGap(['C111'], [], false)[0], joinGap(['C111'], [], true)[0]);
});
''',
"faq": [
 ("Slack sent me the file id in an event. Why can I not read the file?",
  "Because an event is a notification, not a grant. Event payloads carry ids more liberally than the Web API grants access to what they name, and a file shared into several conversations can reach you through a subscription while the conversation you were entitled to see it in is not the one it ended up in. The id is genuine and the access is separate, which is exactly what not_visible is saying."),
 ("What is the difference between not_visible and file_not_found?",
  "not_visible means the file exists and this token is not part of its audience. file_not_found means there is no such file for this token at all - a wrong id, a truncated id, or an id from a different workspace. Slack answers file_not_found rather than not_visible in that case on purpose, because confirming that a file exists somewhere you cannot see would itself leak something. One is fixed by an invitation and the other by looking at where the id came from."),
 ("Should I retry a not_visible error?",
  "No. None of the four errors in this family is transient. not_visible and file_deleted are permanent until somebody changes the world, missing_scope is permanent until a reinstall, and access_denied is permanent until an administrator changes a policy. An indexer that backs off and retries on not_visible spends its rate limit on a file it will never be allowed to read, and the queue grows for reasons that have nothing to do with load."),
 ("How do I find out which channel to be invited to?",
  "Not from the API. A not_visible response contains no file object at all, so there are no channels, groups or ims fields to read. The channel_id on the event payload is the only place the room is named, which is why this script takes saved events rather than bare ids. If your handler logs the file id and discards the envelope, it has thrown away its own diagnosis."),
 ("The bot is in the channel the event named and files.info still says not_visible. What now?",
  "That is the one case here that is not a one-line fix, and the script prints it loudly for that reason. It means the share you were told about is not the share that survived: the file was shared into more than one conversation, or moved to a Slack Connect channel where policy applies, or the message carrying it was deleted from the channel the bot is in. Check the channel is not external before assuming anything about membership."),
],
"related": [
 ("/slack/private-channel-invisible/", "the same ambiguity, one level up at the channel"),
 ("/slack/bot-not-in-channel/", "the membership that most of these errors come down to"),
 ("/slack/file-deleted-link-rot/", "when the file really is gone rather than hidden"),
],
"citations": [CITE_FILES_INFO, CITE_FILE_SHARED, CITE_USERS_CONVERSATIONS, CITE_FILES_LIST],
})

GUIDES.append({
"slug": "file-deleted-link-rot",
"title": "file_deleted: the message survives and the file does not",
"description": "Deleting a file does not touch messages that link to it. Harvest file references from history and your store, then count the fraction that no longer resolve.",
"h1": "file_deleted: the message survives and the file does not",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack file_deleted files.info",
             "slack broken file link in message",
             "slack file tombstone message",
             "slack file id no longer exists",
             "slack file_deleted event subscribe"],
"deps": "Python 3.9+ with requests, or Node.js 18+; a bot token with files:read and channels:history",
"lead": "The knowledge base was built two years ago by walking every channel, pulling every attachment, and storing the file ids beside the extracted text. It worked. It still works, for most of it. Roughly one search result in nine now opens to <code>{\"ok\": false, \"error\": \"file_deleted\"}</code>, and last quarter it was one in twelve.</p><p>Nobody broke anything. People delete files, admins tidy up, and retention policies run on a schedule. What nobody did was tell the index &mdash; and the messages that carried those files are still sitting in the channels, still rendering a link, still looking exactly like they did when the file was there.",
"short_answer": """<p>Deleting a file removes the file. It does not touch the message that linked to it, the id you stored in a database, or the search index you built from either. <strong>The reference is not invalidated, it is orphaned</strong>, and a <code>F</code> id stays a plausible-looking string forever, so nothing fails until somebody follows it.</p>
<p>The symptom shows up on the message side and the cause is on the file side. In channel history a deleted attachment leaves a stub: the message still exists, its <code>files</code> array still has an entry, and that entry has lost the fields that made it a file &mdash; often carrying <code>mode: "tombstone"</code>, always missing <code>url_private</code> and <code>mimetype</code>. Links pasted as text are worse: the URL is still there in full and there is nothing about it that looks wrong.</p>
<p>Measure it rather than fixing rows. Harvest every file reference you can find &mdash; from <code>conversations.history</code>, from your own stored ids &mdash; batch them through <code>files.info</code>, and count. The number worth reporting is the <strong>dangling fraction of the references you could decide</strong>: <code>file_deleted</code> against <code>ok</code>. A <code>not_visible</code> in the same batch is a membership problem and must be excluded, or the number measures two things at once and means neither.</p>""",
"problem": """<p>The reason this decays instead of breaking is that every individual piece behaves correctly. Slack deletes the file because someone asked it to. The message stays because deleting a file is not deleting a message. Your database keeps the row because nothing told it otherwise. Each component is right and the system as a whole has quietly stopped being true, one file at a time, at whatever rate your workspace deletes things.</p>
<p>Slack does emit a <code>file_deleted</code> event, and subscribing to it is the actual fix. Almost nobody does, because the event exists for a case that has not happened yet when the integration is written: the day you ingest a file, its deletion is hypothetical. It stays hypothetical for months. By the time the first support ticket arrives about a broken link, there are thousands of stale rows and no record of which ones went when, because the event you were not subscribed to is the only thing that would have told you.</p>
<p>The message-side view is the part that misleads people during the investigation. Someone reports a broken link, a developer opens the channel, and the message is right there with an attachment on it. It looks completely normal in the client - the deletion is rendered as a small absence rather than as an error. The developer concludes the app has the wrong id. In the API the same message carries a <code>files</code> entry stripped down to almost nothing, and it is a stub rather than a file, but only if you know to look at which fields have gone.</p>
<p>And there is a second, quieter source of the same symptom that must not be confused with it. A message may reference a file the bot simply cannot read, which answers <code>not_visible</code>, and that has nothing to do with deletion. If those land in the same bucket, the dangling fraction rises whenever the bot is removed from a channel and falls whenever it is added to one, which makes the number useless for the thing it is meant to measure: whether your references are rotting and how fast.</p>""",
"why": """<p><strong>The symptom is on the message side and the cause is on the file side.</strong> That split is why this gets misdiagnosed. What people see is an old post with a link that opens nothing; what happened is a file object being removed somewhere else entirely, possibly by a retention policy with no human involved. The script deliberately reads both ends - references out of history, verdicts out of <code>files.info</code> - because either alone tells half the story.</p>
<p><strong>A file id never stops looking valid.</strong> There is no checksum, no expiry in the string, and no shape difference between an id that resolves and one that does not. This is the property that makes the decay silent, and it is the reason the only honest check is to ask the API about every reference rather than to validate them locally.</p>
<p><strong>The fraction is the finding; the count is noise.</strong> Forty dangling references means nothing on its own. Forty out of four hundred means one in ten of your index is dead, and forty out of forty thousand means somebody deleted a folder once. The script divides, and it divides only by the references it could actually decide.</p>
<p><strong>not_visible is excluded from the denominator on purpose.</strong> Unreadable is not deleted. Mixing them makes the number move when the bot's channel membership changes, which is a different note and a different repair, and a metric that responds to two unrelated causes cannot be used to detect either.</p>
<p><strong>Links pasted as text rot invisibly, and blocks hide them.</strong> A file permalink can sit in a message's <code>text</code>, inside a <code>rich_text</code> block several levels down, or in an attachment. Harvesting only the <code>files</code> array finds the attachments and misses every link somebody pasted, which is usually the older and more valuable half of the corpus.</p>
<p><strong>The repair is an event subscription, and the fallback is a tombstone.</strong> Subscribe to <code>file_deleted</code> and remove the reference when it fires. For everything already stored, re-validate on a schedule and mark the dead ones as dead rather than serving a link that fails - a result that says <em>this file was deleted</em> is a better answer than a link that goes nowhere, and it costs one column.</p>""",
"steps": [
 {"h": "Harvest references from both places they hide",
  "body": """<p><code>file_ids_in</code> takes one message and returns every file id it mentions: the entries in <code>files</code>, and the ids inside any Slack file permalink in <code>text</code>, in nested <code>blocks</code>, or in <code>attachments</code>. The pasted links are the half that a naive harvest misses, and they are usually the older half.</p>"""},
 {"h": "Read the message-side stub before you ask the API anything",
  "body": """<p><code>attachment_state</code> classifies a <code>files</code> entry as <code>tombstone</code>, <code>stub</code> or <code>present</code>. A tombstone is Slack telling you outright; a stub is an entry that has lost <code>mimetype</code> and <code>url_private</code>, which happens both for deletion and for a file this token cannot read. The stub verdict is a suspicion, not a verdict, and the script says so.</p>"""},
 {"h": "Batch the unique ids through files.info and classify each answer",
  "body": """<p><code>classify_ref</code> maps a response to <code>live</code>, <code>deleted</code>, <code>unknown</code>, <code>unreadable</code> or <code>undecided</code>. Deduplicate first: a popular file referenced in forty messages is one API call, and the rate limit on <code>files.info</code> is not generous.</p>"""},
 {"h": "Compute the fraction over decidable references only",
  "body": """<p><code>rot</code> divides <code>deleted</code> by <code>deleted + live</code>. Everything else - unreadable, undecided - is reported beside the fraction and kept out of it. A rot rate that moves when the bot joins a channel is measuring channel membership, not rot.</p>"""},
 {"h": "Run it twice, a month apart, and compare",
  "body": """<p>A single run gives you a number with no meaning attached. Two runs give you a direction, and a direction is what tells you whether this is a historical clean-up that already happened or a policy that is still eating your corpus. The script prints the fraction in a form that is trivial to store.</p>"""},
 {"h": "Subscribe to file_deleted, then tombstone what is already dead",
  "body": """<p>The repair is two changes. Subscribe to the <code>file_deleted</code> event with <code>files:read</code> so future deletions remove the reference at the time they happen. Then mark the existing dead references as dead rather than deleting the rows - a search result that says the file was removed is a better answer than a link that fails, and it also preserves the evidence for the next run.</p>"""},
],
"verify": """<p>The output to keep is the last line. Store it, run it again next month, and compare the two numbers rather than reading either one on its own.</p>
<pre><code class="language-bash">python3 slack_file_link_rot.py --channel C024BE91L --refs index-file-ids.json
# identity   U07BOT9QD in Northwind
# refs       412 reference(s): 316 from history, 96 from index-file-ids.json
# message    tombstone      F06AAA1QQ  Slack has already replaced this attachment
# message    stub           F06BBB2QQ  an id and nothing else; files.info decides
# check      deleted        F06AAA1QQ  the file is gone and the message that carried
#                           it is still in the channel
# check      unreadable     F07CCC3QQ  not_visible, which is membership and not rot
# rot        47 of 391 decidable reference(s) no longer resolve (12.0%)
# rot        21 reference(s) left out: 18 unreadable, 3 undecided
#   repair: subscribe to file_deleted and drop the reference when it fires
#   repair: tombstone the dead references rather than serving a link that fails</code></pre>""",
"code_intro": "One harvest, one batch of reads, one division. <code>file_ids_in</code> walks a message including its nested blocks, because a permalink pasted as text is a reference and looks nothing like an attachment. <code>attachment_state</code> reads the message-side symptom and is careful to call it a suspicion. <code>classify_ref</code> turns each <code>files.info</code> answer into one word, and <code>rot</code> divides by the references it could decide and no others - which is the one design decision in this script that keeps the number meaning something.",
"py_file": "slack_file_link_rot.py",
"py": '''"""Measure how much of what you stored about Slack files no longer exists.

Read only. conversations.history and files.info are reads; nothing here deletes
a file, removes a message or repairs a reference. The repairs are printed.

The shape of the bug is that deleting a file does not touch anything that points
at it, so references rot silently and at whatever rate your workspace deletes
things. The number worth having is a fraction, and the one design decision here
is what goes in the denominator: only references this token could actually
decide. A file it cannot read is not a file that was deleted.
"""
import argparse
import json
import logging
import os
import re
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_file_link_rot")

API = "https://slack.com/api/"

# A Slack file permalink carries the file id as a path segment, between the
# uploader and the filename. Matching inside the URL rather than matching bare
# F-ids anywhere in the text, because "F" plus capitals is a common enough
# string in ordinary prose to poison the harvest.
FILE_URL = re.compile(r"https?://[^\\s|<>]*slack\\.com/files/[^\\s|<>]*?"
                      r"/(F[A-Z0-9]{6,})", re.IGNORECASE)


def _strings_in(node, out, depth=0):
    """Every string anywhere in a blocks tree. Recursive, depth-capped."""
    if depth > 12:
        return out
    if isinstance(node, str):
        out.append(node)
    elif isinstance(node, dict):
        for value in node.values():
            _strings_in(value, out, depth + 1)
    elif isinstance(node, (list, tuple)):
        for value in node:
            _strings_in(value, out, depth + 1)
    return out


def file_ids_in(message):
    """Every file this message refers to, from both places they hide. Pure.

    Two kinds of reference, and a harvest that finds only the first is the
    version of this check that reports a healthy corpus:

      attachments   entries in the message's `files` array, which is what most
                    people look at because it is the obvious one.
      links         a file permalink pasted into `text`, buried in a rich_text
                    block, or sitting in an attachment. Older, usually more
                    valuable, and completely invisible to a harvest that reads
                    the files array alone.

    Returns ids in first-seen order, deduplicated and upper-cased.
    """
    m = message or {}
    found = []
    for entry in m.get("files") or []:
        fid = (entry or {}).get("id")
        if isinstance(fid, str) and fid:
            found.append(fid)
    haystack = _strings_in(m.get("text"), [])
    _strings_in(m.get("blocks"), haystack)
    _strings_in(m.get("attachments"), haystack)
    for chunk in haystack:
        for hit in FILE_URL.finditer(chunk):
            found.append(hit.group(1))
    seen, out = set(), []
    for fid in found:
        upper = fid.upper()
        if upper not in seen:
            seen.add(upper)
            out.append(upper)
    return out


def attachment_state(entry):
    """What does the message itself say about this attachment? Pure.

    Returns (state, detail). This is the message-side symptom and it is
    deliberately weaker than the API-side verdict:

      tombstone  Slack has replaced the file with a marker. Conclusive.
      stub       the entry has an id and has lost the fields that made it a
                 file. Consistent with deletion and equally consistent with a
                 file this token cannot read, so it is a suspicion.
      present    the entry still describes a file.
    """
    e = entry or {}
    if str(e.get("mode") or "").lower() == "tombstone":
        return ("tombstone", "Slack has already replaced this attachment with a "
                             "tombstone, so the deletion is not in doubt")
    if not e.get("mimetype") and not e.get("url_private"):
        return ("stub", "an id and nothing else. That is what history returns for a "
                        "file that was deleted and also for one this token cannot "
                        "read, so files.info decides which")
    return ("present", "the entry still describes a file")


def classify_ref(payload):
    """One files.info answer, in one word. Pure.

    live       resolves, and counts in the denominator.
    deleted    file_deleted, and counts in both.
    unknown    file_not_found: no such file for this token. Counts as dangling
               because a reference you cannot resolve is dead to you either
               way, and is reported separately so a workspace mix-up is
               visible.
    unreadable not_visible or access_denied. NOT rot, and excluded from the
               fraction: mixing it in makes the number move when the bot's
               channel membership changes.
    undecided  anything else, including a rate limit or a scope problem.
    """
    p = payload or {}
    if p.get("ok") is True:
        return "live"
    error = str(p.get("error") or "")
    if error == "file_deleted":
        return "deleted"
    if error == "file_not_found":
        return "unknown"
    if error in ("not_visible", "access_denied",
                 "slack_connect_file_link_sharing_blocked"):
        return "unreadable"
    return "undecided"


def rot(verdicts):
    """The dangling fraction, over the references that could be decided. Pure.

    Returns (dangling, decidable, percent, excluded). A reference this token
    could not resolve one way or the other is left out of both halves rather
    than counted as healthy, because counting it as healthy is how a rot rate
    quietly reports success while the corpus dies.
    """
    counts = {}
    for v in verdicts or []:
        counts[v] = counts.get(v, 0) + 1
    dangling = counts.get("deleted", 0) + counts.get("unknown", 0)
    decidable = dangling + counts.get("live", 0)
    excluded = counts.get("unreadable", 0) + counts.get("undecided", 0)
    percent = 0.0 if not decidable else round(100.0 * dangling / decidable, 1)
    return (dangling, decidable, percent, excluded)


def read_history(session, channel, pages, limit):
    """Page conversations.history. A read."""
    out, cursor = [], ""
    for _ in range(pages):
        params = {"channel": channel, "limit": str(limit)}
        if cursor:
            params["cursor"] = cursor
        body = session.get(API + "conversations.history", params=params,
                           timeout=30).json()
        if body.get("ok") is not True:
            log.warning("history    unavailable    %s: %s", channel, body.get("error"))
            return out
        out.extend(body.get("messages") or [])
        cursor = (body.get("response_metadata") or {}).get("next_cursor") or ""
        if not cursor:
            break
    return out


def load_refs(path):
    """The ids your own store believes in."""
    raw = json.loads(open(path, encoding="utf-8").read())
    if isinstance(raw, dict):
        raw = raw.get("files") or raw.get("ids") or raw.get("refs") or []
    out = []
    for row in raw or []:
        if isinstance(row, str):
            out.append(row.upper())
        elif isinstance(row, dict) and isinstance(row.get("id"), str):
            out.append(row["id"].upper())
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--channel", action="append", default=[],
                    help="a channel id to harvest references from; repeatable")
    ap.add_argument("--refs", default="",
                    help="a JSON file of file ids your own store holds")
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN")
    ap.add_argument("--pages", type=int, default=10)
    ap.add_argument("--limit", type=int, default=200)
    ap.add_argument("--max-checks", type=int, default=500,
                    help="cap on files.info calls; it is a tier 4 method, not free")
    args = ap.parse_args()

    if not args.channel and not args.refs:
        log.error("pass --channel C..., or --refs FILE, or both")
        return 2

    token = os.environ.get(args.token_env)
    if not token:
        log.error("set %s to a bot token with files:read", args.token_env)
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + token})
    who = s.get(API + "auth.test", timeout=30).json()
    if who.get("ok") is not True:
        log.error("auth.test  unavailable    %s", who.get("error"))
        return 2
    log.info("identity   %s in %s", who.get("user_id"), who.get("team"))

    from_history, order = [], []
    for channel in args.channel:
        for message in read_history(s, channel, args.pages, args.limit):
            for entry in message.get("files") or []:
                state, detail = attachment_state(entry)
                if state != "present":
                    log.info("message    %-14s %s  %s", state,
                             (entry or {}).get("id") or "?", detail)
            from_history.extend(file_ids_in(message))
    from_store = load_refs(args.refs) if args.refs else []

    seen = set()
    for fid in from_history + from_store:
        if fid not in seen:
            seen.add(fid)
            order.append(fid)
    log.info("refs       %d reference(s): %d from history, %d from %s",
             len(order), len(set(from_history)), len(set(from_store)),
             args.refs or "no store")

    verdicts = []
    for fid in order[:args.max_checks]:
        body = s.get(API + "files.info", params={"file": fid}, timeout=30).json()
        verdict = classify_ref(body)
        verdicts.append(verdict)
        if verdict == "deleted":
            log.warning("check      deleted        %s  the file is gone and anything "
                        "that points at it is not", fid)
        elif verdict == "unknown":
            log.warning("check      unknown        %s  file_not_found: no such file for "
                        "this token, which may be a different workspace", fid)
        elif verdict == "unreadable":
            log.info("check      unreadable     %s  not_visible, which is membership "
                     "and not rot", fid)
        elif verdict == "undecided":
            log.info("check      undecided      %s  neither resolved nor refused "
                     "cleanly", fid)

    dangling, decidable, percent, excluded = rot(verdicts)
    if not decidable:
        log.warning("rot        nothing decidable in this run; check files:read and "
                    "the bot's channel membership")
        return 1
    log.info("rot        %d of %d decidable reference(s) no longer resolve (%.1f%%)",
             dangling, decidable, percent)
    if excluded:
        log.info("rot        %d reference(s) left out of that fraction on purpose",
                 excluded)
    if not dangling:
        return 0
    log.warning("  repair: subscribe to the file_deleted event and drop the reference "
                "when it fires; that is the only version of this that stays fixed")
    log.warning("  repair: tombstone the dead references rather than serving a link "
                "that fails, and keep the row so the next run can compare")
    log.warning("  repair: if the content has to outlive Slack, copy the bytes at "
                "ingestion time; Slack is a transport, not an archive")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-file-link-rot.mjs",
"js": '''/**
 * Measure how much of what you stored about Slack files no longer exists.
 *
 * Read only. conversations.history and files.info are reads; nothing here
 * deletes a file, removes a message or repairs a reference. Repairs are printed.
 *
 * Deleting a file does not touch anything that points at it, so references rot
 * silently. The number worth having is a fraction, and the one design decision
 * here is what goes in the denominator: only references this token could
 * actually decide. A file it cannot read is not a file that was deleted.
 */

import { readFile } from 'node:fs/promises';

const API = 'https://slack.com/api/';

// A Slack file permalink carries the id as a path segment. Matching inside the
// URL rather than matching bare F-ids anywhere in the text, because "F" plus
// capitals is a common enough string in prose to poison the harvest.
const FILE_URL = /https?:\\/\\/[^\\s|<>]*slack\\.com\\/files\\/[^\\s|<>]*?\\/(F[A-Z0-9]{6,})/gi;

function stringsIn(node, out, depth = 0) {
  if (depth > 12) return out;
  if (typeof node === 'string') out.push(node);
  else if (Array.isArray(node)) for (const v of node) stringsIn(v, out, depth + 1);
  else if (node && typeof node === 'object') {
    for (const v of Object.values(node)) stringsIn(v, out, depth + 1);
  }
  return out;
}

/**
 * Every file this message refers to, from both places they hide. Pure.
 *
 * Attachments live in the `files` array and are the obvious half. Permalinks
 * pasted into `text`, buried in a rich_text block or sitting in an attachment
 * are the older half, and a harvest that reads only `files` reports a healthy
 * corpus while missing most of it.
 */
export function fileIdsIn(message) {
  const m = message ?? {};
  const found = [];
  for (const entry of m.files ?? []) {
    const fid = (entry ?? {}).id;
    if (typeof fid === 'string' && fid) found.push(fid);
  }
  const haystack = stringsIn(m.text, []);
  stringsIn(m.blocks, haystack);
  stringsIn(m.attachments, haystack);
  for (const chunk of haystack) {
    FILE_URL.lastIndex = 0;
    let hit = FILE_URL.exec(chunk);
    while (hit) {
      found.push(hit[1]);
      hit = FILE_URL.exec(chunk);
    }
  }
  const seen = new Set();
  const out = [];
  for (const fid of found) {
    const upper = fid.toUpperCase();
    if (!seen.has(upper)) {
      seen.add(upper);
      out.push(upper);
    }
  }
  return out;
}

/**
 * What does the message itself say about this attachment? Pure.
 * Returns [state, detail]; stub is a suspicion rather than a verdict.
 */
export function attachmentState(entry) {
  const e = entry ?? {};
  if (String(e.mode ?? '').toLowerCase() === 'tombstone') {
    return ['tombstone', 'Slack has already replaced this attachment with a tombstone, '
      + 'so the deletion is not in doubt'];
  }
  if (!e.mimetype && !e.url_private) {
    return ['stub', 'an id and nothing else. That is what history returns for a file '
      + 'that was deleted and also for one this token cannot read, so files.info '
      + 'decides which'];
  }
  return ['present', 'the entry still describes a file'];
}

/**
 * One files.info answer, in one word. Pure.
 * live, deleted, unknown, unreadable or undecided; unreadable is not rot.
 */
export function classifyRef(payload) {
  const p = payload ?? {};
  if (p.ok === true) return 'live';
  const error = String(p.error ?? '');
  if (error === 'file_deleted') return 'deleted';
  if (error === 'file_not_found') return 'unknown';
  if (['not_visible', 'access_denied',
    'slack_connect_file_link_sharing_blocked'].includes(error)) return 'unreadable';
  return 'undecided';
}

/**
 * The dangling fraction, over the references that could be decided. Pure.
 * Returns [dangling, decidable, percent, excluded].
 */
export function rot(verdicts) {
  const counts = {};
  for (const v of verdicts ?? []) counts[v] = (counts[v] ?? 0) + 1;
  const dangling = (counts.deleted ?? 0) + (counts.unknown ?? 0);
  const decidable = dangling + (counts.live ?? 0);
  const excluded = (counts.unreadable ?? 0) + (counts.undecided ?? 0);
  const percent = decidable ? Math.round((1000 * dangling) / decidable) / 10 : 0;
  return [dangling, decidable, percent, excluded];
}

function arg(args, name, fallback = null) {
  const i = args.indexOf(name);
  return i === -1 ? fallback : args[i + 1];
}

function argAll(args, name) {
  const out = [];
  for (let i = 0; i < args.length; i += 1) {
    if (args[i] === name && args[i + 1] !== undefined) out.push(args[i + 1]);
  }
  return out;
}

async function readHistory(headers, channel, pages, limit) {
  const out = [];
  let cursor = '';
  for (let i = 0; i < pages; i += 1) {
    const params = new URLSearchParams({ channel, limit: String(limit) });
    if (cursor) params.set('cursor', cursor);
    const body = await (await fetch(`${API}conversations.history?${params}`,
      { headers })).json();
    if (body.ok !== true) {
      console.warn(`history    unavailable    ${channel}: ${body.error}`);
      return out;
    }
    out.push(...(body.messages ?? []));
    cursor = (body.response_metadata ?? {}).next_cursor ?? '';
    if (!cursor) break;
  }
  return out;
}

function loadRefs(raw) {
  let rows = raw;
  if (rows && !Array.isArray(rows) && typeof rows === 'object') {
    rows = rows.files ?? rows.ids ?? rows.refs ?? [];
  }
  const out = [];
  for (const row of rows ?? []) {
    if (typeof row === 'string') out.push(row.toUpperCase());
    else if (row && typeof row.id === 'string') out.push(row.id.toUpperCase());
  }
  return out;
}

async function main() {
  const args = process.argv.slice(2);
  const channels = argAll(args, '--channel');
  const refsFile = arg(args, '--refs', '');
  if (!channels.length && !refsFile) {
    console.error('pass --channel C..., or --refs FILE, or both');
    process.exitCode = 2;
    return;
  }

  const tokenEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
  const token = process.env[tokenEnv];
  if (!token) {
    console.error(`set ${tokenEnv} to a bot token with files:read`);
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
  console.log(`identity   ${who.user_id} in ${who.team}`);

  const pages = Number(arg(args, '--pages', '10'));
  const limit = Number(arg(args, '--limit', '200'));
  const fromHistory = [];
  for (const channel of channels) {
    for (const message of await readHistory(headers, channel, pages, limit)) {
      for (const entry of message.files ?? []) {
        const [state, detail] = attachmentState(entry);
        if (state !== 'present') {
          console.log(`message    ${state.padEnd(14)} ${(entry ?? {}).id ?? '?'}  `
            + `${detail}`);
        }
      }
      fromHistory.push(...fileIdsIn(message));
    }
  }
  const fromStore = refsFile
    ? loadRefs(JSON.parse(await readFile(refsFile, 'utf8'))) : [];

  const order = [...new Set([...fromHistory, ...fromStore])];
  console.log(`refs       ${order.length} reference(s): ${new Set(fromHistory).size} `
    + `from history, ${new Set(fromStore).size} from ${refsFile || 'no store'}`);

  const maxChecks = Number(arg(args, '--max-checks', '500'));
  const verdicts = [];
  for (const fid of order.slice(0, maxChecks)) {
    const params = new URLSearchParams({ file: fid });
    const body = await (await fetch(`${API}files.info?${params}`, { headers })).json();
    const verdict = classifyRef(body);
    verdicts.push(verdict);
    if (verdict === 'deleted') {
      console.warn(`check      deleted        ${fid}  the file is gone and anything `
        + 'that points at it is not');
    } else if (verdict === 'unknown') {
      console.warn(`check      unknown        ${fid}  file_not_found: no such file for `
        + 'this token, which may be a different workspace');
    } else if (verdict === 'unreadable') {
      console.log(`check      unreadable     ${fid}  not_visible, which is membership `
        + 'and not rot');
    } else if (verdict === 'undecided') {
      console.log(`check      undecided      ${fid}  neither resolved nor refused `
        + 'cleanly');
    }
  }

  const [dangling, decidable, percent, excluded] = rot(verdicts);
  if (!decidable) {
    console.warn('rot        nothing decidable in this run; check files:read and the '
      + "bot's channel membership");
    process.exitCode = 1;
    return;
  }
  console.log(`rot        ${dangling} of ${decidable} decidable reference(s) no longer `
    + `resolve (${percent}%)`);
  if (excluded) {
    console.log(`rot        ${excluded} reference(s) left out of that fraction on `
      + 'purpose');
  }
  if (!dangling) return;
  console.warn('  repair: subscribe to the file_deleted event and drop the reference '
    + 'when it fires; that is the only version of this that stays fixed');
  console.warn('  repair: tombstone the dead references rather than serving a link that '
    + 'fails, and keep the row so the next run can compare');
  console.warn('  repair: if the content has to outlive Slack, copy the bytes at '
    + 'ingestion time; Slack is a transport, not an archive');
  process.exitCode = 1;
}

// Only run when invoked directly, so importing this module in the tests does
// not execute main() and fail the file on a missing token.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The harvest is tested against a permalink buried three levels down in a <code>rich_text</code> block, because that is the shape a real pasted link has and the shape a flat scan misses. <code>rot</code> is tested for its denominator more than for its numerator: an unreadable reference must not count as healthy and must not count as dangling, and there is an explicit test that a run consisting entirely of unreadable references reports nothing decidable rather than a comfortable zero per cent.",
"test_py_file": "test_slack_file_link_rot.py",
"test_py": '''from slack_file_link_rot import attachment_state, classify_ref, file_ids_in, rot

PERMALINK = "https://northwind.slack.com/files/U07BOT9QD/F06AAA1QQ/report.pdf"


def test_an_attachment_is_the_obvious_half_of_the_harvest():
    assert file_ids_in({"files": [{"id": "F06AAA1QQ"}]}) == ["F06AAA1QQ"]


def test_a_permalink_pasted_as_text_is_the_half_that_gets_missed():
    assert file_ids_in({"text": "see %s for the numbers" % PERMALINK}) == ["F06AAA1QQ"]


def test_a_permalink_buried_in_a_rich_text_block_is_still_found():
    message = {"blocks": [{"type": "rich_text", "elements": [
        {"type": "rich_text_section", "elements": [
            {"type": "link", "url": PERMALINK, "text": "the report"}]}]}]}
    assert file_ids_in(message) == ["F06AAA1QQ"]


def test_a_permalink_in_an_attachment_counts_as_a_reference():
    assert file_ids_in({"attachments": [{"text": PERMALINK}]}) == ["F06AAA1QQ"]


def test_the_same_file_referenced_twice_is_one_call():
    message = {"files": [{"id": "F06AAA1QQ"}], "text": PERMALINK}
    assert file_ids_in(message) == ["F06AAA1QQ"]


def test_an_id_shaped_word_in_prose_is_not_harvested():
    assert file_ids_in({"text": "FRIDAY and F06AAA1QQ are not links"}) == []


def test_a_message_with_no_files_at_all_yields_nothing():
    assert file_ids_in({"text": "no attachments here"}) == []
    assert file_ids_in(None) == []


def test_a_tombstone_is_conclusive():
    state, detail = attachment_state({"id": "F1", "mode": "tombstone"})
    assert state == "tombstone"
    assert "not in doubt" in detail


def test_a_stripped_entry_is_a_suspicion_rather_than_a_verdict():
    state, detail = attachment_state({"id": "F1"})
    assert state == "stub"
    assert "files.info decides which" in detail


def test_a_real_attachment_is_present():
    assert attachment_state({"id": "F1", "mimetype": "application/pdf",
                             "url_private": "https://files.slack.com/x"})[0] == "present"


def test_the_four_files_info_answers_are_four_different_words():
    assert classify_ref({"ok": True}) == "live"
    assert classify_ref({"ok": False, "error": "file_deleted"}) == "deleted"
    assert classify_ref({"ok": False, "error": "file_not_found"}) == "unknown"
    assert classify_ref({"ok": False, "error": "not_visible"}) == "unreadable"


def test_anything_unexpected_is_undecided_rather_than_assumed_healthy():
    assert classify_ref({"ok": False, "error": "ratelimited"}) == "undecided"
    assert classify_ref({}) == "undecided"
    assert classify_ref(None) == "undecided"


def test_the_fraction_is_over_decidable_references_only():
    dangling, decidable, percent, excluded = rot(
        ["deleted", "deleted", "live", "live", "unreadable"])
    assert (dangling, decidable, excluded) == (2, 4, 1)
    assert percent == 50.0


def test_an_unreadable_reference_is_neither_healthy_nor_rotten():
    with_it = rot(["deleted", "live", "unreadable"])
    without_it = rot(["deleted", "live"])
    assert with_it[2] == without_it[2]


def test_a_run_of_nothing_but_unreadable_reports_nothing_decidable():
    dangling, decidable, percent, excluded = rot(["unreadable", "unreadable"])
    assert decidable == 0
    assert percent == 0.0
    assert excluded == 2


def test_file_not_found_counts_as_dangling_and_is_still_named_separately():
    assert rot(["unknown", "live"])[0] == 1
    assert classify_ref({"ok": False, "error": "file_not_found"}) != "deleted"


def test_an_empty_run_does_not_divide_by_zero():
    assert rot([]) == (0, 0, 0.0, 0)
''',
"test_js_file": "slack-file-link-rot.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  attachmentState, classifyRef, fileIdsIn, rot,
} from './slack-file-link-rot.mjs';

const PERMALINK = 'https://northwind.slack.com/files/U07BOT9QD/F06AAA1QQ/report.pdf';

test('an attachment is the obvious half of the harvest', () => {
  assert.deepEqual(fileIdsIn({ files: [{ id: 'F06AAA1QQ' }] }), ['F06AAA1QQ']);
});

test('a permalink pasted as text is the half that gets missed', () => {
  assert.deepEqual(fileIdsIn({ text: `see ${PERMALINK} for the numbers` }),
    ['F06AAA1QQ']);
});

test('a permalink buried in a rich_text block is still found', () => {
  const message = {
    blocks: [{
      type: 'rich_text',
      elements: [{
        type: 'rich_text_section',
        elements: [{ type: 'link', url: PERMALINK, text: 'the report' }],
      }],
    }],
  };
  assert.deepEqual(fileIdsIn(message), ['F06AAA1QQ']);
});

test('a permalink in an attachment counts as a reference', () => {
  assert.deepEqual(fileIdsIn({ attachments: [{ text: PERMALINK }] }), ['F06AAA1QQ']);
});

test('the same file referenced twice is one call', () => {
  assert.deepEqual(fileIdsIn({ files: [{ id: 'F06AAA1QQ' }], text: PERMALINK }),
    ['F06AAA1QQ']);
});

test('the global regex does not skip a second message', () => {
  assert.deepEqual(fileIdsIn({ text: PERMALINK }), ['F06AAA1QQ']);
  assert.deepEqual(fileIdsIn({ text: PERMALINK }), ['F06AAA1QQ']);
});

test('an id shaped word in prose is not harvested', () => {
  assert.deepEqual(fileIdsIn({ text: 'FRIDAY and F06AAA1QQ are not links' }), []);
});

test('a message with no files at all yields nothing', () => {
  assert.deepEqual(fileIdsIn({ text: 'no attachments here' }), []);
  assert.deepEqual(fileIdsIn(null), []);
});

test('a tombstone is conclusive', () => {
  const [state, detail] = attachmentState({ id: 'F1', mode: 'tombstone' });
  assert.equal(state, 'tombstone');
  assert.match(detail, /not in doubt/);
});

test('a stripped entry is a suspicion rather than a verdict', () => {
  const [state, detail] = attachmentState({ id: 'F1' });
  assert.equal(state, 'stub');
  assert.match(detail, /files\\.info decides which/);
});

test('a real attachment is present', () => {
  assert.equal(attachmentState({
    id: 'F1', mimetype: 'application/pdf', url_private: 'https://files.slack.com/x',
  })[0], 'present');
});

test('the four files.info answers are four different words', () => {
  assert.equal(classifyRef({ ok: true }), 'live');
  assert.equal(classifyRef({ ok: false, error: 'file_deleted' }), 'deleted');
  assert.equal(classifyRef({ ok: false, error: 'file_not_found' }), 'unknown');
  assert.equal(classifyRef({ ok: false, error: 'not_visible' }), 'unreadable');
});

test('anything unexpected is undecided rather than assumed healthy', () => {
  assert.equal(classifyRef({ ok: false, error: 'ratelimited' }), 'undecided');
  assert.equal(classifyRef({}), 'undecided');
  assert.equal(classifyRef(null), 'undecided');
});

test('the fraction is over decidable references only', () => {
  const [dangling, decidable, percent, excluded] = rot(
    ['deleted', 'deleted', 'live', 'live', 'unreadable']);
  assert.deepEqual([dangling, decidable, excluded], [2, 4, 1]);
  assert.equal(percent, 50);
});

test('an unreadable reference is neither healthy nor rotten', () => {
  assert.equal(rot(['deleted', 'live', 'unreadable'])[2],
    rot(['deleted', 'live'])[2]);
});

test('a run of nothing but unreadable reports nothing decidable', () => {
  const [, decidable, percent, excluded] = rot(['unreadable', 'unreadable']);
  assert.equal(decidable, 0);
  assert.equal(percent, 0);
  assert.equal(excluded, 2);
});

test('file_not_found counts as dangling and is still named separately', () => {
  assert.equal(rot(['unknown', 'live'])[0], 1);
  assert.notEqual(classifyRef({ ok: false, error: 'file_not_found' }), 'deleted');
});

test('an empty run does not divide by zero', () => {
  assert.deepEqual(rot([]), [0, 0, 0, 0]);
});
''',
"faq": [
 ("Why does deleting a file not remove the message that shared it?",
  "Because they are different objects with different owners. A message belongs to the person who posted it and lives in a conversation; a file belongs to whoever uploaded it and lives in the workspace's file store. Deleting one does not authorise deleting the other, and Slack does not. What you get instead is a message whose attachment has been reduced to a marker, which reads as normal in the client and reads as a stub in the API."),
 ("Is there a way to be told when a file is deleted?",
  "Yes, and it is the actual fix. Slack emits a file_deleted event to apps subscribed to it with files:read. Handle it by removing or tombstoning the reference at the moment it happens, and the decay stops. The reason so few integrations do this is timing: on the day you build the ingestion, deletion is hypothetical, and by the time it is not, there are thousands of stale rows and no record of when any of them died."),
 ("Should a not_visible reference count towards the rot rate?",
  "No, and this is the one number in the script that would be easy to get wrong. Unreadable is not deleted. If they share a bucket, the rot rate rises whenever the bot is removed from a channel and falls whenever somebody adds it to one, so the metric responds to two unrelated causes and cannot be used to detect either. The script divides by the references it could decide and reports the excluded ones beside the fraction."),
 ("Can I get a deleted file back?",
  "Not through the API. Deletion is not reversible for an app, and files removed by a workspace retention policy are gone in the same way. That is the argument for copying anything that has to outlive Slack into your own store at ingestion time, using the authenticated download URL - Slack is a transport for files, not an archive of them, and treating it as the second is how a retention policy becomes a data-loss policy nobody chose."),
 ("The rot rate is 12% and I do not know whether that is bad. What should I compare it to?",
  "The same number from last month. A single reading has no meaning attached; a direction has. If it is flat, some files were deleted once and the corpus is stable. If it is climbing, something is deleting continuously - most often a retention policy - and the ingestion needs to copy rather than reference. The script prints the fraction in a form you can store precisely so that the second run is a comparison rather than a fresh guess."),
],
"related": [
 ("/slack/file-not-visible/", "the unreadable references this one refuses to count"),
 ("/slack/http-200-ok-false/", "why file_deleted arrived inside a successful response"),
 ("/slack/pagination-not-followed/", "harvesting one page of history and calling it the corpus"),
],
"citations": [CITE_FILES_INFO, CITE_FILE_DELETED, CITE_CONV_HISTORY, CITE_FILES_LIST],
})

GUIDES.append({
"slug": "file-download-without-auth",
"title": "url_private without a bearer header saves the login page",
"description": "An unauthenticated fetch of url_private returns HTTP 200 and Slack's sign-in page. Compare the bytes your downloader saved with the mimetype files.info gives.",
"h1": "url_private without a bearer header saves the login page",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack url_private download html",
             "slack file download authorization bearer",
             "slack downloaded file is sign in page",
             "url_private_download vs permalink",
             "slack file download 200 html"],
"deps": "Python 3.9+ with requests, or Node.js 18+; a bot token with files:read, plus the files your downloader already wrote to disk",
"lead": "The archiver has been running for a year and has never logged an error. Every fetch returned <code>200</code>, every write succeeded, and the folder has fourteen thousand files in it. Then somebody tries to open one and their PDF reader says the file is damaged.</p><p>All fourteen thousand are three kilobytes. All fourteen thousand start with <code>&lt;!DOCTYPE html&gt;</code>. Fetching <code>url_private</code> without an <code>Authorization</code> header does not return <code>401</code> &mdash; it returns <code>200</code> and Slack's sign-in page, and a downloader that follows redirects and writes the body writes the login screen to disk, once per file, silently, for a year.",
"short_answer": """<p><code>url_private</code> and <code>url_private_download</code> are authenticated URLs on <code>files.slack.com</code>. They serve the file only to a request carrying <code>Authorization: Bearer &lt;token&gt;</code>. <strong>Without that header the response is HTTP 200 with an HTML sign-in page</strong>, not a 401, so every check that trusts the status code passes and every downloader that saves the body saves the wrong bytes.</p>
<p>This is the same trap as the Web API's <code>ok: false</code> inside a 200, moved to a different host. It has two extra ways to bite. <code>permalink</code> is a page in the Slack client rather than a file and must never be used as a download URL. And several HTTP clients strip <code>Authorization</code> when a request is redirected to another host, which reproduces the bug exactly on a client that <em>is</em> sending the header.</p>
<p>You can find every corrupted file without downloading anything. <code>files.info</code> reports the file's <code>mimetype</code> and <code>size</code>; the bytes are already on your disk. <strong>Compare them.</strong> An HTML header where the API says <code>application/pdf</code>, or three kilobytes where the API says four megabytes, is the whole finding &mdash; and doing it this way means the audit never needs the credential it is auditing and never sends the file anywhere.</p>""",
"problem": """<p>Every layer here behaves plausibly and the result is still garbage. Slack answers 200 because it is serving a real page: you asked an anonymous browser-shaped question and got the anonymous browser-shaped answer, which is <em>please sign in</em>. The HTTP client returns success because the request succeeded. The code writes the body because the body is what it asked for. Nothing in that chain is a bug, and nothing in that chain is checking whether the thing on disk is the thing that was wanted.</p>
<p>The corruption is uniform, which is what makes it survive so long. Every file in the folder is the same three kilobytes of the same markup, so spot-checking two of them looks consistent, file counts look right, disk usage looks plausible for a lot of small screenshots, and the archive appears healthy by every measure except opening a file. Teams usually find this when somebody needs one specific document a year later, which is the worst possible moment.</p>
<p>The near-miss version is more interesting, because the code looks correct. A client that sets the header on the initial request but drops it across a cross-host redirect gets exactly the same login page. Python's <code>requests</code> strips <code>Authorization</code> when a redirect changes host; several other stacks do the same, on purpose, as a credential-leak defence. So <em>we do send the bearer token</em> is true and the file on disk is still HTML, and the fix is about redirect handling rather than about headers.</p>
<p>Then there is the URL that was never going to work. <code>permalink</code> is the human-facing page for a file, and it is the most obvious-looking field in the response, so it gets stored as <em>the URL of the file</em> constantly. Fetching it authenticated returns a Slack web page; fetching it unauthenticated returns a sign-in page. <code>permalink_public</code>, when it exists at all, is a wrapper page rather than raw bytes, and it only exists for files that were deliberately made public - which is a separate and worse problem than this one.</p>
<p>The last thing worth saying is what this script deliberately does not do. It does not fetch anything from <code>files.slack.com</code>, and it does not print a <code>url_private</code>. Fetching to prove the point would either need the exact credential under audit or would pull the content of every file through the auditing process, and a <code>url_private</code> in a log line is one paste away from being a capability somebody else holds. The API describes the file, the bytes are already on the disk, and the comparison is offline.</p>""",
"why": """<p><strong>The status code is not the answer, again.</strong> Slack's Web API puts failures in a 200 body and its file host puts them in a 200 page. Once you know that, the rule generalises: on anything Slack-shaped, the check is what came back, not what number came with it.</p>
<p><strong>The API already told you what the file should be.</strong> <code>mimetype</code> and <code>size</code> come back from <code>files.info</code> for free, and together they are a complete contract for what should be on disk. Almost nobody compares against them, which is why this corruption is invisible - not because it is hard to detect, but because there is no line of code anywhere asking the question.</p>
<p><strong>The audit must not need the credential it is auditing.</strong> A check that downloads the files to test them requires the working token, which is exactly the thing you suspect is missing, and it moves the content of every file through one more process. Reading the first few hundred bytes off your own disk answers the same question with no token and no transfer.</p>
<p><strong>A url_private is a capability once you attach a token, so it does not belong in a log.</strong> The script classifies URLs and prints the class and a redacted host-and-path-kind, never the URL itself and never a query string. <code>pub_secret</code> values in particular are the whole secret.</p>
<p><strong>Redirect handling is a separate failure with an identical symptom.</strong> Because it looks like the header is being sent - it is, on the first hop - it survives code review and gets diagnosed as a Slack problem. The script cannot see your HTTP client, so the note names it explicitly as the thing to check when the header is provably present and the file on disk is still HTML.</p>
<p><strong>Size and type are different findings and want different fixes.</strong> HTML in place of a PDF is authentication. A file that is the right type and the wrong length is a truncated write, a stream closed early, or a mis-declared <code>length</code> at upload time. Reporting both as <em>download broken</em> merges an auth bug with an I/O bug.</p>
<p><strong>A validation step at write time makes the whole class of bug impossible.</strong> Compare <code>Content-Type</code> against the API's <code>mimetype</code> before saving, and refuse to write a file whose length does not match <code>size</code>. That is four lines, and it converts a year of silent corruption into an error on the first file.</p>""",
"steps": [
 {"h": "Classify the URL your app stored, with no token at all",
  "body": """<p><code>--urls stored-urls.json</code> runs <code>url_class</code> over the download URLs your app kept and needs no credential. <code>web-page</code> means somebody stored <code>permalink</code>, which was never going to return a file. <code>public-link</code> means the file was made public, which is a different note and a worse problem. <code>private-bytes</code> is the only class that is correct here, and it is the one that needs the header.</p>"""},
 {"h": "Ask files.info what the file is supposed to be",
  "body": """<p><code>mimetype</code>, <code>size</code>, <code>filetype</code> and <code>name</code>, for each id your downloader wrote. This is the contract. It is one read per file and it needs <code>files:read</code> and nothing else.</p>"""},
 {"h": "Read the first bytes of what you already saved",
  "body": """<p><code>sniff</code> takes the leading bytes off your local copy and names the format from its magic number - <code>%PDF-</code>, the PNG signature, <code>PK\\x03\\x04</code> for anything zip-shaped including Office documents - and, crucially, recognises an HTML document. No network, and no need for the token.</p>"""},
 {"h": "Hold the two against each other",
  "body": """<p><code>saved_verdict</code> returns <code>login-page</code>, <code>empty</code>, <code>truncated</code>, <code>size-mismatch</code>, <code>type-mismatch</code> or <code>ok</code>. The HTML check runs before the size checks on purpose: a login page is also the wrong size, and reporting it as <em>size-mismatch</em> would send somebody to look at their write buffer instead of their headers.</p>"""},
 {"h": "Separate the auth finding from the I/O finding",
  "body": """<p><code>login-page</code> is authentication and the repair is a header. <code>truncated</code> is a write that stopped early or a stream that was not drained. They arrive in the same run and they have nothing to do with each other, and a single <em>corrupt</em> bucket costs a day.</p>"""},
 {"h": "If the header is provably present, look at redirects next",
  "body": """<p>A client that sets <code>Authorization</code> and then follows a redirect to another host may drop it - Python's <code>requests</code> does exactly this, deliberately. Same symptom, different cause, and the script cannot see it from here, so it prints the check rather than performing it: log the final URL and whether the header survived the last hop.</p>"""},
 {"h": "Validate at write time so this can never be silent again",
  "body": """<p>The printed repair is a code change: compare the response <code>Content-Type</code> against the API's <code>mimetype</code> and the byte count against <code>size</code>, and refuse the write when either disagrees. Four lines, and the failure becomes loud on the first file instead of quiet for a year.</p>"""},
],
"verify": """<p>Point it at the folder your downloader filled. Nothing is fetched from Slack's file host and no URL is printed in full.</p>
<pre><code class="language-bash">python3 slack_download_audit.py --saved archive-index.json
# identity   U07BOT9QD in Northwind
# url        private-bytes  F08K2M4QX  https://files.slack.com/files-pri/...  needs a
#                           bearer header on every hop
# saved      login-page     F08K2M4QX  the bytes on disk begin an HTML document and
#                           files.info says application/pdf. That is the sign-in page
# saved      truncated      F08K2M55Z  3 KB on disk against 4.1 MB reported; a write
#                           that stopped early, which is not the same bug
# url        web-page       F08K2M77A  https://northwind.slack.com/files/...  a
#                           permalink is a page in the client, not the file
# saved      ok             F08K2M91B  runbook.pdf 812 KB, application/pdf
# verdict    2 of 4 saved file(s) are not what the API says they are
#   repair: send Authorization: Bearer on every fetch of url_private_download
#   repair: compare Content-Type against mimetype before writing, and refuse on a
#           mismatch rather than saving the body</code></pre>""",
"code_intro": "Nothing here fetches a file and nothing here prints a URL. <code>url_class</code> decides which of the four Slack URL kinds you stored and whether it needs a header; <code>redact</code> exists so the answer can be logged without logging a capability. <code>sniff</code> reads the leading bytes of your own copy, and <code>saved_verdict</code> holds them against the <code>mimetype</code> and <code>size</code> the API reports. The order of the checks inside that last function is the design: HTML is tested before length, because a login page is also the wrong size and the wrong size sends people to the wrong place.",
"py_file": "slack_download_audit.py",
"py": '''"""Check whether your downloader saved Slack files or Slack's sign-in page.

Read only, and narrower than that: the only network call is files.info, which
describes a file without transferring it. This script never fetches
url_private, never follows a Slack file URL, and never prints one.

Fetching to prove the point would be wrong twice over. It would need the exact
credential under audit - the missing header is the thing being investigated -
and it would pull the content of every file through one more process. The API
already reports the mimetype and the size, and the bytes are already on your
disk, so the comparison is offline and needs no token for the interesting half.
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_download_audit")

API = "https://slack.com/api/"
HEAD_BYTES = 512

# Leading bytes, as latin-1 text so the table reads as a table. The zip
# signature covers docx, xlsx, pptx and every other Office format, which is why
# compatibility below is more forgiving than equality.
MAGIC = (
    ("%PDF-", "application/pdf"),
    ("\\x89PNG\\r\\n\\x1a\\n", "image/png"),
    ("\\xff\\xd8\\xff", "image/jpeg"),
    ("GIF87a", "image/gif"),
    ("GIF89a", "image/gif"),
    ("PK\\x03\\x04", "application/zip"),
    ("\\x1f\\x8b", "application/gzip"),
    ("OggS", "audio/ogg"),
    ("ID3", "audio/mpeg"),
    ("RIFF", "audio/wav"),
    ("\\x00\\x00\\x00", "video/mp4"),
)

HTML_STARTS = ("<!doctype html", "<html", "<head", "<!-- ")


def _text(head):
    """The leading bytes as latin-1 text. Never decodes lossily enough to lie."""
    if head is None:
        return ""
    if isinstance(head, str):
        return head[:HEAD_BYTES]
    return bytes(head)[:HEAD_BYTES].decode("latin-1", "replace")


def sniff(head):
    """What are these bytes, judged only by how they start? Pure.

    Returns a mimetype or "". The case this function exists for is the first
    one checked: an HTML document where a file was expected is Slack's sign-in
    page, served with HTTP 200 to a request that carried no Authorization
    header.
    """
    text = _text(head)
    stripped = text.lstrip()
    lowered = stripped.lower()
    if any(lowered.startswith(start) for start in HTML_STARTS):
        return "text/html"
    if "<title>slack" in lowered or "signin_form" in lowered:
        return "text/html"
    for prefix, mimetype in MAGIC:
        if text.startswith(prefix):
            return mimetype
    return ""


def compatible(sniffed, declared):
    """Do a sniffed type and an API mimetype describe the same file? Pure.

    Zip is the whole reason this is not equality: every Office format is a zip
    archive, so PK\\x03\\x04 is the honest answer for a .docx and reporting it as
    a mismatch would bury the real findings under paperwork.
    """
    if not sniffed or not declared:
        return True
    left, right = sniffed.lower(), declared.lower()
    if left == right:
        return True
    if left == "application/zip":
        return any(token in right for token in
                   ("zip", "officedocument", "opendocument", "epub", "jar"))
    if left.split("/")[0] == right.split("/")[0] == "image":
        return True
    return False


def url_class(url):
    """Which kind of Slack URL is this, and does it need a header? Pure.

    Returns (kind, needs_header, detail), and never the URL itself.

      private-bytes  files-pri or files-tmb: the file, served only to a request
                     carrying Authorization: Bearer. This is the correct one.
      web-page       a permalink. A page in the Slack client, not the file, and
                     the most common thing to have stored by mistake because it
                     is the friendliest looking field in the response.
      public-link    a pub_secret link, which serves the bytes to anyone at all.
                     A different and worse problem.
      elsewhere      not a Slack file URL; an external file lives on its own host.
    """
    text = str(url or "").strip()
    if not text:
        return ("missing", False, "no download URL was stored for this file")
    low = text.lower()
    if not low.startswith(("http://", "https://")):
        return ("not-a-url", False, "not a URL at all, so nothing was ever going to "
                                    "come back from it")
    if "pub_secret=" in low or "slack-files.com" in low:
        return ("public-link", False, "a public file link. It serves the bytes to "
                                      "anyone holding it, with no Slack login, which "
                                      "is a data exposure rather than a download bug")
    if "/files-pri/" in low or "/files-tmb/" in low:
        return ("private-bytes", True, "the file itself, served only to a request "
                                       "carrying an Authorization bearer header on "
                                       "every hop including redirects")
    if "/files/" in low or "/archives/" in low:
        return ("web-page", False, "a permalink, which is a page in the Slack client "
                                   "rather than the file. Authenticated or not, this "
                                   "returns markup")
    return ("elsewhere", False, "not a Slack file host, so this is an external file "
                                "and its access rules are somebody else's")


def redact(url):
    """Host and path kind, with the identifiers and the query removed. Pure.

    A url_private is a capability the moment a token is attached to it, and a
    pub_secret query string is a capability on its own. Neither belongs in a log
    line, a ticket or a screenshot, so this is what the script prints instead.
    """
    text = str(url or "").strip()
    if not text:
        return ""
    text = text.split("?", 1)[0].split("#", 1)[0]
    parts = text.split("/")
    if len(parts) < 4:
        return text
    return "/".join(parts[:4]) + "/..."


def saved_verdict(info, saved_size, head=b""):
    """Is the file on disk the file the API describes? Pure.

    Returns (verdict, detail). The order of the checks is the design of this
    function: the HTML test runs before the length tests, because a sign-in page
    is also the wrong size, and reporting it as a size problem sends somebody to
    look at their write buffer when the fault is in their headers.
    """
    f = info or {}
    declared = str(f.get("mimetype") or "")
    size = f.get("size")
    size = size if isinstance(size, int) and not isinstance(size, bool) else None
    sniffed = sniff(head)

    if not saved_size:
        return ("empty", "nothing was written. A zero byte file is a fetch that "
                         "returned no body, or a write that never happened")
    if sniffed == "text/html" and "html" not in declared.lower():
        return ("login-page", "the bytes on disk begin an HTML document and files.info "
                              "says %s. That is Slack's sign-in page, served with HTTP "
                              "200 to a fetch that carried no Authorization header"
                % (declared or "something else"))
    if size is not None and size > 0 and saved_size != size:
        if saved_size * 4 < size:
            return ("truncated", "%d byte(s) on disk against %d reported. A write that "
                                 "stopped early or a stream that was not drained, which "
                                 "is not the same bug as a missing header"
                    % (saved_size, size))
        return ("size-mismatch", "%d byte(s) on disk against %d reported" % (saved_size,
                                                                             size))
    if not compatible(sniffed, declared):
        return ("type-mismatch", "the bytes look like %s and files.info says %s"
                % (sniffed, declared))
    return ("ok", "%s, %d byte(s), matching what files.info reports"
            % (declared or "unknown type", saved_size))


def load_saved(path):
    """Whatever your downloader wrote down: {id: path}, or a list of records."""
    raw = json.loads(open(path, encoding="utf-8").read())
    if isinstance(raw, dict) and not raw.get("files"):
        return [(str(k), str(v)) for k, v in raw.items() if isinstance(v, str)]
    rows = raw.get("files") if isinstance(raw, dict) else raw
    out = []
    for row in rows or []:
        if isinstance(row, dict):
            fid = row.get("id") or row.get("file_id") or ""
            where = row.get("path") or row.get("saved") or ""
            if fid and where:
                out.append((str(fid), str(where)))
    return out


def head_and_size(path):
    """The leading bytes and the length of a local file. No network."""
    try:
        with open(path, "rb") as fh:
            head = fh.read(HEAD_BYTES)
        return head, os.path.getsize(path)
    except OSError as err:
        log.warning("saved      unreadable     %s  %s", path, err)
        return b"", None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--saved", default="",
                    help="a JSON map of file id to the local path your downloader wrote")
    ap.add_argument("--urls", default="",
                    help="a JSON list of stored download URLs; classified with no token")
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN")
    args = ap.parse_args()

    if not args.saved and not args.urls:
        log.error("pass --saved FILE, or --urls FILE to classify stored URLs offline")
        return 2

    bad_urls = 0
    if args.urls:
        for url in json.loads(open(args.urls, encoding="utf-8").read()) or []:
            kind, needs, detail = url_class(url)
            line = ("url        %-14s %s  %s", kind, redact(url), detail)
            if kind == "private-bytes":
                log.info(*line)
            else:
                bad_urls += 1
                log.warning(*line)
            if needs:
                log.info("           this one is correct and it is the one that needs "
                         "the header")
        if not args.saved:
            if bad_urls:
                log.warning("verdict    %d stored URL(s) are not the file", bad_urls)
                return 1
            log.info("verdict    clean          every stored URL is a private file URL")
            return 0

    token = os.environ.get(args.token_env)
    if not token:
        log.error("set %s to a bot token with files:read", args.token_env)
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + token})
    who = s.get(API + "auth.test", timeout=30).json()
    if who.get("ok") is not True:
        log.error("auth.test  unavailable    %s", who.get("error"))
        return 2
    log.info("identity   %s in %s", who.get("user_id"), who.get("team"))

    rows = load_saved(args.saved)
    if not rows:
        log.error("no {id: path} records found in %s", args.saved)
        return 2

    broken = 0
    for fid, where in rows:
        body = s.get(API + "files.info", params={"file": fid}, timeout=30).json()
        if body.get("ok") is not True:
            log.warning("info       unavailable    %s  %s", fid, body.get("error"))
            continue
        info = body.get("file") or {}
        kind, _needs, detail = url_class(info.get("url_private_download")
                                         or info.get("url_private"))
        log.info("url        %-14s %s  %s  %s", kind, fid,
                 redact(info.get("url_private_download") or info.get("url_private")),
                 detail)
        head, saved_size = head_and_size(where)
        if saved_size is None:
            continue
        verdict, why = saved_verdict(info, saved_size, head)
        if verdict == "ok":
            log.info("saved      ok             %s  %s", fid, why)
            continue
        broken += 1
        log.warning("saved      %-14s %s  %s", verdict, fid, why)

    if not broken:
        log.info("verdict    clean          every saved file matches what files.info "
                 "reports")
        return 0
    log.warning("verdict    %d of %d saved file(s) are not what the API says they are",
                broken, len(rows))
    log.warning("  repair: send Authorization: Bearer on every fetch of "
                "url_private_download, and never use permalink as a download URL")
    log.warning("  repair: compare the response Content-Type against the API mimetype "
                "before writing, and refuse the write on a mismatch")
    log.warning("  repair: if the header is provably sent, check redirects; several "
                "HTTP clients drop Authorization when a redirect changes host")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-download-audit.mjs",
"js": '''/**
 * Check whether your downloader saved Slack files or Slack's sign-in page.
 *
 * Read only, and narrower than that: the only network call is files.info, which
 * describes a file without transferring it. This script never fetches
 * url_private, never follows a Slack file URL, and never prints one.
 *
 * Fetching to prove the point would need the exact credential under audit - the
 * missing header is the thing being investigated - and would pull the content
 * of every file through one more process. The API reports the mimetype and the
 * size, the bytes are already on disk, so the comparison is offline.
 */

import { readFile, stat } from 'node:fs/promises';

const API = 'https://slack.com/api/';
const HEAD_BYTES = 512;

// Leading bytes, as latin-1 text so the table reads as a table. The zip
// signature covers every Office format, which is why compatibility below is
// more forgiving than equality.
const MAGIC = [
  ['%PDF-', 'application/pdf'],
  ['\\x89PNG\\r\\n\\x1a\\n', 'image/png'],
  ['\\xff\\xd8\\xff', 'image/jpeg'],
  ['GIF87a', 'image/gif'],
  ['GIF89a', 'image/gif'],
  ['PK\\x03\\x04', 'application/zip'],
  ['\\x1f\\x8b', 'application/gzip'],
  ['OggS', 'audio/ogg'],
  ['ID3', 'audio/mpeg'],
  ['RIFF', 'audio/wav'],
  ['\\x00\\x00\\x00', 'video/mp4'],
];

const HTML_STARTS = ['<!doctype html', '<html', '<head', '<!-- '];

function asText(head) {
  if (head === null || head === undefined) return '';
  if (typeof head === 'string') return head.slice(0, HEAD_BYTES);
  let out = '';
  for (let i = 0; i < Math.min(head.length, HEAD_BYTES); i += 1) {
    out += String.fromCharCode(head[i]);
  }
  return out;
}

/**
 * What are these bytes, judged only by how they start? Pure.
 * Returns a mimetype or ''. HTML is checked first because HTML is the note.
 */
export function sniff(head) {
  const text = asText(head);
  const lowered = text.trimStart().toLowerCase();
  if (HTML_STARTS.some((start) => lowered.startsWith(start))) return 'text/html';
  if (lowered.includes('<title>slack') || lowered.includes('signin_form')) {
    return 'text/html';
  }
  for (const [prefix, mimetype] of MAGIC) {
    if (text.startsWith(prefix)) return mimetype;
  }
  return '';
}

/**
 * Do a sniffed type and an API mimetype describe the same file? Pure.
 * Zip is why this is not equality: every Office format is a zip archive.
 */
export function compatible(sniffed, declared) {
  if (!sniffed || !declared) return true;
  const left = sniffed.toLowerCase();
  const right = declared.toLowerCase();
  if (left === right) return true;
  if (left === 'application/zip') {
    return ['zip', 'officedocument', 'opendocument', 'epub', 'jar']
      .some((token) => right.includes(token));
  }
  if (left.split('/')[0] === 'image' && right.split('/')[0] === 'image') return true;
  return false;
}

/**
 * Which kind of Slack URL is this, and does it need a header? Pure.
 * Returns [kind, needsHeader, detail], and never the URL itself.
 */
export function urlClass(url) {
  const text = String(url ?? '').trim();
  if (!text) return ['missing', false, 'no download URL was stored for this file'];
  const low = text.toLowerCase();
  if (!low.startsWith('http://') && !low.startsWith('https://')) {
    return ['not-a-url', false, 'not a URL at all, so nothing was ever going to come '
      + 'back from it'];
  }
  if (low.includes('pub_secret=') || low.includes('slack-files.com')) {
    return ['public-link', false, 'a public file link. It serves the bytes to anyone '
      + 'holding it, with no Slack login, which is a data exposure rather than a '
      + 'download bug'];
  }
  if (low.includes('/files-pri/') || low.includes('/files-tmb/')) {
    return ['private-bytes', true, 'the file itself, served only to a request carrying '
      + 'an Authorization bearer header on every hop including redirects'];
  }
  if (low.includes('/files/') || low.includes('/archives/')) {
    return ['web-page', false, 'a permalink, which is a page in the Slack client rather '
      + 'than the file. Authenticated or not, this returns markup'];
  }
  return ['elsewhere', false, 'not a Slack file host, so this is an external file and '
    + "its access rules are somebody else's"];
}

/**
 * Host and path kind, with the identifiers and the query removed. Pure.
 * A url_private is a capability once a token is attached; a pub_secret query
 * string is a capability on its own. Neither belongs in a log line.
 */
export function redact(url) {
  let text = String(url ?? '').trim();
  if (!text) return '';
  text = text.split('?')[0];
  text = text.split('#')[0];
  const parts = text.split('/');
  if (parts.length < 4) return text;
  return `${parts.slice(0, 4).join('/')}/...`;
}

/**
 * Is the file on disk the file the API describes? Pure.
 * Returns [verdict, detail]. The HTML test runs before the length tests, because
 * a sign-in page is also the wrong size and the wrong size sends people to the
 * wrong place.
 */
export function savedVerdict(info, savedSize, head = '') {
  const f = info ?? {};
  const declared = String(f.mimetype ?? '');
  const size = (typeof f.size === 'number' && Number.isFinite(f.size)) ? f.size : null;
  const sniffed = sniff(head);

  if (!savedSize) {
    return ['empty', 'nothing was written. A zero byte file is a fetch that returned '
      + 'no body, or a write that never happened'];
  }
  if (sniffed === 'text/html' && !declared.toLowerCase().includes('html')) {
    return ['login-page', 'the bytes on disk begin an HTML document and files.info says '
      + `${declared || 'something else'}. That is Slack's sign-in page, served with `
      + 'HTTP 200 to a fetch that carried no Authorization header'];
  }
  if (size !== null && size > 0 && savedSize !== size) {
    if (savedSize * 4 < size) {
      return ['truncated', `${savedSize} byte(s) on disk against ${size} reported. A `
        + 'write that stopped early or a stream that was not drained, which is not the '
        + 'same bug as a missing header'];
    }
    return ['size-mismatch', `${savedSize} byte(s) on disk against ${size} reported`];
  }
  if (!compatible(sniffed, declared)) {
    return ['type-mismatch', `the bytes look like ${sniffed} and files.info says `
      + `${declared}`];
  }
  return ['ok', `${declared || 'unknown type'}, ${savedSize} byte(s), matching what `
    + 'files.info reports'];
}

function arg(args, name, fallback = null) {
  const i = args.indexOf(name);
  return i === -1 ? fallback : args[i + 1];
}

function loadSaved(raw) {
  if (raw && !Array.isArray(raw) && typeof raw === 'object' && !raw.files) {
    return Object.entries(raw).filter(([, v]) => typeof v === 'string')
      .map(([k, v]) => [String(k), String(v)]);
  }
  const rows = (raw && !Array.isArray(raw)) ? raw.files : raw;
  const out = [];
  for (const row of rows ?? []) {
    if (row && typeof row === 'object') {
      const fid = row.id ?? row.file_id ?? '';
      const where = row.path ?? row.saved ?? '';
      if (fid && where) out.push([String(fid), String(where)]);
    }
  }
  return out;
}

async function headAndSize(path) {
  try {
    const bytes = await readFile(path);
    const info = await stat(path);
    return [bytes.subarray(0, HEAD_BYTES), info.size];
  } catch (err) {
    console.warn(`saved      unreadable     ${path}  ${err.message}`);
    return ['', null];
  }
}

async function main() {
  const args = process.argv.slice(2);
  const savedFile = arg(args, '--saved', '');
  const urlsFile = arg(args, '--urls', '');
  if (!savedFile && !urlsFile) {
    console.error('pass --saved FILE, or --urls FILE to classify stored URLs offline');
    process.exitCode = 2;
    return;
  }

  let badUrls = 0;
  if (urlsFile) {
    for (const url of JSON.parse(await readFile(urlsFile, 'utf8')) ?? []) {
      const [kind, needs, detail] = urlClass(url);
      const line = `url        ${kind.padEnd(14)} ${redact(url)}  ${detail}`;
      if (kind === 'private-bytes') console.log(line);
      else {
        badUrls += 1;
        console.warn(line);
      }
      if (needs) {
        console.log('           this one is correct and it is the one that needs the '
          + 'header');
      }
    }
    if (!savedFile) {
      if (badUrls) {
        console.warn(`verdict    ${badUrls} stored URL(s) are not the file`);
        process.exitCode = 1;
      } else {
        console.log('verdict    clean          every stored URL is a private file URL');
      }
      return;
    }
  }

  const tokenEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
  const token = process.env[tokenEnv];
  if (!token) {
    console.error(`set ${tokenEnv} to a bot token with files:read`);
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
  console.log(`identity   ${who.user_id} in ${who.team}`);

  const rows = loadSaved(JSON.parse(await readFile(savedFile, 'utf8')));
  if (!rows.length) {
    console.error(`no {id: path} records found in ${savedFile}`);
    process.exitCode = 2;
    return;
  }

  let broken = 0;
  for (const [fid, where] of rows) {
    const params = new URLSearchParams({ file: fid });
    const body = await (await fetch(`${API}files.info?${params}`, { headers })).json();
    if (body.ok !== true) {
      console.warn(`info       unavailable    ${fid}  ${body.error}`);
      continue;
    }
    const info = body.file ?? {};
    const target = info.url_private_download ?? info.url_private;
    const [kind, , detail] = urlClass(target);
    console.log(`url        ${kind.padEnd(14)} ${fid}  ${redact(target)}  ${detail}`);
    const [head, savedSize] = await headAndSize(where);
    if (savedSize === null) continue;
    const [verdict, why] = savedVerdict(info, savedSize, head);
    if (verdict === 'ok') {
      console.log(`saved      ok             ${fid}  ${why}`);
      continue;
    }
    broken += 1;
    console.warn(`saved      ${verdict.padEnd(14)} ${fid}  ${why}`);
  }

  if (!broken) {
    console.log('verdict    clean          every saved file matches what files.info '
      + 'reports');
    return;
  }
  console.warn(`verdict    ${broken} of ${rows.length} saved file(s) are not what the `
    + 'API says they are');
  console.warn('  repair: send Authorization: Bearer on every fetch of '
    + 'url_private_download, and never use permalink as a download URL');
  console.warn('  repair: compare the response Content-Type against the API mimetype '
    + 'before writing, and refuse the write on a mismatch');
  console.warn('  repair: if the header is provably sent, check redirects; several HTTP '
    + 'clients drop Authorization when a redirect changes host');
  process.exitCode = 1;
}

// Only run when invoked directly, so importing this module in the tests does
// not execute main() and fail the file on a missing token.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The load-bearing assertion is an ordering one: a three-kilobyte HTML document standing in for a four-megabyte PDF must come back as <code>login-page</code> and not as <code>truncated</code>, even though it is also the wrong size, because the two verdicts send you to different files in your own codebase. <code>redact</code> is tested for what it removes rather than what it keeps, with a <code>pub_secret</code> query string that must not survive. And a <code>.docx</code> is tested as a zip archive, since a check that reports every Office document as a type mismatch is a check nobody reads twice.",
"test_py_file": "test_slack_download_audit.py",
"test_py": '''from slack_download_audit import compatible, redact, saved_verdict, sniff, url_class

SIGNIN = b"<!DOCTYPE html>\\n<html lang=\\"en\\"><head><title>Slack</title>"
PDF = b"%PDF-1.7\\n%\\xe2\\xe3\\xcf\\xd3\\n"


def test_the_sign_in_page_is_recognised_as_html():
    assert sniff(SIGNIN) == "text/html"
    assert sniff(b"  <html>") == "text/html"


def test_the_common_formats_are_recognised_by_their_magic_numbers():
    assert sniff(PDF) == "application/pdf"
    assert sniff(b"\\x89PNG\\r\\n\\x1a\\nrest") == "image/png"
    assert sniff(b"\\xff\\xd8\\xff\\xe0jpeg") == "image/jpeg"
    assert sniff(b"PK\\x03\\x04docx") == "application/zip"


def test_unknown_bytes_are_not_guessed_at():
    assert sniff(b"\\x07\\x07\\x07nothing") == ""
    assert sniff(b"") == ""
    assert sniff(None) == ""


def test_an_office_document_is_a_zip_and_that_is_not_a_mismatch():
    docx = ("application/vnd.openxmlformats-officedocument."
            "wordprocessingml.document")
    assert compatible("application/zip", docx) is True


def test_an_unknown_sniff_never_manufactures_a_mismatch():
    assert compatible("", "application/pdf") is True
    assert compatible("application/pdf", "") is True


def test_html_against_a_pdf_is_a_mismatch():
    assert compatible("text/html", "application/pdf") is False


def test_the_private_file_url_is_the_only_one_that_needs_a_header():
    kind, needs, _ = url_class("https://files.slack.com/files-pri/T1-F1/report.pdf")
    assert kind == "private-bytes"
    assert needs is True


def test_a_permalink_is_a_page_and_was_never_going_to_be_a_file():
    kind, needs, detail = url_class(
        "https://northwind.slack.com/files/U07BOT9QD/F06AAA1QQ/report.pdf")
    assert kind == "web-page"
    assert needs is False
    assert "page in the Slack client" in detail


def test_a_public_link_is_named_as_an_exposure_rather_than_a_download_bug():
    kind, _, detail = url_class(
        "https://files.slack.com/files-pri/T1-F1/report.pdf?pub_secret=abc123")
    assert kind == "public-link"
    assert "exposure" in detail


def test_a_missing_or_broken_url_has_its_own_verdicts():
    assert url_class("")[0] == "missing"
    assert url_class(None)[0] == "missing"
    assert url_class("files.slack.com/files-pri/x")[0] == "not-a-url"


def test_an_external_file_url_is_somebody_elses_problem():
    assert url_class("https://example.com/report.pdf")[0] == "elsewhere"


def test_redact_keeps_the_host_and_the_path_kind_and_nothing_else():
    assert redact("https://files.slack.com/files-pri/T1-F1/report.pdf") \\
        == "https://files.slack.com/files-pri/..."


def test_redact_removes_the_query_string_because_that_is_where_the_secret_is():
    out = redact("https://files.slack.com/files-pri/T1-F1/r.pdf?pub_secret=abc123")
    assert "pub_secret" not in out
    assert "abc123" not in out


def test_the_sign_in_page_saved_over_a_pdf_is_the_finding():
    verdict, detail = saved_verdict(
        {"mimetype": "application/pdf", "size": 4194304}, len(SIGNIN), SIGNIN)
    assert verdict == "login-page"
    assert "no Authorization header" in detail


def test_a_login_page_is_never_reported_as_a_size_problem():
    verdict, _ = saved_verdict({"mimetype": "application/pdf", "size": 4194304},
                               3000, SIGNIN)
    assert verdict == "login-page"
    assert verdict != "truncated"


def test_a_genuine_html_file_is_not_a_login_page():
    assert saved_verdict({"mimetype": "text/html", "size": len(SIGNIN)},
                         len(SIGNIN), SIGNIN)[0] == "ok"


def test_a_short_write_is_truncated_rather_than_a_header_problem():
    verdict, detail = saved_verdict({"mimetype": "application/pdf", "size": 4194304},
                                    3000, PDF)
    assert verdict == "truncated"
    assert "not the same bug" in detail


def test_a_small_difference_is_a_size_mismatch_and_not_a_truncation():
    assert saved_verdict({"mimetype": "application/pdf", "size": 1000},
                         900, PDF)[0] == "size-mismatch"


def test_nothing_on_disk_is_its_own_verdict():
    assert saved_verdict({"mimetype": "application/pdf", "size": 10}, 0, b"")[0] \\
        == "empty"


def test_the_right_length_and_the_wrong_format_is_a_type_mismatch():
    assert saved_verdict({"mimetype": "image/png", "size": len(PDF)},
                         len(PDF), PDF)[0] == "type-mismatch"


def test_a_matching_file_is_ok():
    verdict, detail = saved_verdict({"mimetype": "application/pdf", "size": len(PDF)},
                                    len(PDF), PDF)
    assert verdict == "ok"
    assert "matching what files.info reports" in detail


def test_a_file_the_api_reports_no_size_for_is_still_judged_on_its_bytes():
    assert saved_verdict({"mimetype": "application/pdf"}, 1234, PDF)[0] == "ok"
    assert saved_verdict({"mimetype": "application/pdf"}, 1234, SIGNIN)[0] \\
        == "login-page"
''',
"test_js_file": "slack-download-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  compatible, redact, savedVerdict, sniff, urlClass,
} from './slack-download-audit.mjs';

const bytes = (s) => Uint8Array.from([...s].map((c) => c.charCodeAt(0)));
const SIGNIN = bytes('<!DOCTYPE html>\\n<html lang="en"><head><title>Slack</title>');
const PDF = bytes('%PDF-1.7\\n%\\xe2\\xe3\\xcf\\xd3\\n');

test('the sign in page is recognised as HTML', () => {
  assert.equal(sniff(SIGNIN), 'text/html');
  assert.equal(sniff(bytes('  <html>')), 'text/html');
});

test('the common formats are recognised by their magic numbers', () => {
  assert.equal(sniff(PDF), 'application/pdf');
  assert.equal(sniff(bytes('\\x89PNG\\r\\n\\x1a\\nrest')), 'image/png');
  assert.equal(sniff(bytes('\\xff\\xd8\\xff\\xe0jpeg')), 'image/jpeg');
  assert.equal(sniff(bytes('PK\\x03\\x04docx')), 'application/zip');
});

test('unknown bytes are not guessed at', () => {
  assert.equal(sniff(bytes('\\x07\\x07\\x07nothing')), '');
  assert.equal(sniff(bytes('')), '');
  assert.equal(sniff(null), '');
});

test('an Office document is a zip and that is not a mismatch', () => {
  const docx = 'application/vnd.openxmlformats-officedocument.'
    + 'wordprocessingml.document';
  assert.equal(compatible('application/zip', docx), true);
});

test('an unknown sniff never manufactures a mismatch', () => {
  assert.equal(compatible('', 'application/pdf'), true);
  assert.equal(compatible('application/pdf', ''), true);
});

test('HTML against a PDF is a mismatch', () => {
  assert.equal(compatible('text/html', 'application/pdf'), false);
});

test('the private file URL is the only one that needs a header', () => {
  const [kind, needs] = urlClass('https://files.slack.com/files-pri/T1-F1/report.pdf');
  assert.equal(kind, 'private-bytes');
  assert.equal(needs, true);
});

test('a permalink is a page and was never going to be a file', () => {
  const [kind, needs, detail] = urlClass(
    'https://northwind.slack.com/files/U07BOT9QD/F06AAA1QQ/report.pdf');
  assert.equal(kind, 'web-page');
  assert.equal(needs, false);
  assert.match(detail, /page in the Slack client/);
});

test('a public link is named as an exposure rather than a download bug', () => {
  const [kind, , detail] = urlClass(
    'https://files.slack.com/files-pri/T1-F1/report.pdf?pub_secret=abc123');
  assert.equal(kind, 'public-link');
  assert.match(detail, /exposure/);
});

test('a missing or broken URL has its own verdicts', () => {
  assert.equal(urlClass('')[0], 'missing');
  assert.equal(urlClass(null)[0], 'missing');
  assert.equal(urlClass('files.slack.com/files-pri/x')[0], 'not-a-url');
});

test('an external file URL is somebody elses problem', () => {
  assert.equal(urlClass('https://example.com/report.pdf')[0], 'elsewhere');
});

test('redact keeps the host and the path kind and nothing else', () => {
  assert.equal(redact('https://files.slack.com/files-pri/T1-F1/report.pdf'),
    'https://files.slack.com/files-pri/...');
});

test('redact removes the query string because that is where the secret is', () => {
  const out = redact('https://files.slack.com/files-pri/T1-F1/r.pdf?pub_secret=abc123');
  assert.doesNotMatch(out, /pub_secret/);
  assert.doesNotMatch(out, /abc123/);
});

test('the sign in page saved over a PDF is the finding', () => {
  const [verdict, detail] = savedVerdict(
    { mimetype: 'application/pdf', size: 4194304 }, SIGNIN.length, SIGNIN);
  assert.equal(verdict, 'login-page');
  assert.match(detail, /no Authorization header/);
});

test('a login page is never reported as a size problem', () => {
  const [verdict] = savedVerdict({ mimetype: 'application/pdf', size: 4194304 },
    3000, SIGNIN);
  assert.equal(verdict, 'login-page');
  assert.notEqual(verdict, 'truncated');
});

test('a genuine HTML file is not a login page', () => {
  assert.equal(savedVerdict({ mimetype: 'text/html', size: SIGNIN.length },
    SIGNIN.length, SIGNIN)[0], 'ok');
});

test('a short write is truncated rather than a header problem', () => {
  const [verdict, detail] = savedVerdict({ mimetype: 'application/pdf', size: 4194304 },
    3000, PDF);
  assert.equal(verdict, 'truncated');
  assert.match(detail, /not the same bug/);
});

test('a small difference is a size mismatch and not a truncation', () => {
  assert.equal(savedVerdict({ mimetype: 'application/pdf', size: 1000 },
    900, PDF)[0], 'size-mismatch');
});

test('nothing on disk is its own verdict', () => {
  assert.equal(savedVerdict({ mimetype: 'application/pdf', size: 10 }, 0,
    bytes(''))[0], 'empty');
});

test('the right length and the wrong format is a type mismatch', () => {
  assert.equal(savedVerdict({ mimetype: 'image/png', size: PDF.length },
    PDF.length, PDF)[0], 'type-mismatch');
});

test('a matching file is ok', () => {
  const [verdict, detail] = savedVerdict({ mimetype: 'application/pdf',
    size: PDF.length }, PDF.length, PDF);
  assert.equal(verdict, 'ok');
  assert.match(detail, /matching what files\\.info reports/);
});

test('a file the API reports no size for is still judged on its bytes', () => {
  assert.equal(savedVerdict({ mimetype: 'application/pdf' }, 1234, PDF)[0], 'ok');
  assert.equal(savedVerdict({ mimetype: 'application/pdf' }, 1234, SIGNIN)[0],
    'login-page');
});
''',
"faq": [
 ("Why does Slack return 200 instead of 401 for an unauthenticated file fetch?",
  "Because it is answering the request it thinks it received. An anonymous request for a file URL looks like a person clicking a link in a browser, and the correct response to a person who is not signed in is a sign-in page, served with 200 like any other page. It is the same shape as the Web API putting ok: false inside a 200, moved to a different host, and it defeats the same reflex: checking the status code and moving on."),
 ("What is the difference between url_private, permalink and permalink_public?",
  "url_private and url_private_download are the file, on files.slack.com, served only to a request carrying a bearer token. permalink is a page in the Slack client that shows the file to a signed-in human; it is not a download URL and never returns the bytes. permalink_public exists only for files that were deliberately made public and is a wrapper page rather than raw bytes - and its existence is a separate and more serious finding than a broken download."),
 ("We definitely send the Authorization header and we still get HTML. What else could it be?",
  "Redirects. Several HTTP clients drop the Authorization header when a redirect changes host, as a deliberate defence against leaking credentials to third parties - Python's requests does exactly this. The first hop carries the header, the second does not, and the response body is the sign-in page again. Log the final URL and whether the header survived the last hop; the symptom is identical and the fix is in your client configuration rather than your code."),
 ("Why does this script not just download one file and check it?",
  "Two reasons, and both are about what an audit should cost. It would need the working credential, which is precisely the thing under investigation, so the check would fail for the same reason the downloader did and tell you nothing new. And it would pull the content of every audited file through one more process, which for an archive of exports and screenshots is a real cost. files.info reports the mimetype and size, your disk holds the bytes, and the comparison needs neither a transfer nor the token being questioned."),
 ("Everything downloaded a year ago is the login page. Can I re-fetch it?",
  "Usually yes, if the files still exist - fix the header, delete the local copies, and run the archiver again over the same ids. The part to check first is how many of those ids still resolve, because a year is long enough for deletions and retention to have removed some of them, and a re-fetch will report those separately. Whatever you do, add the Content-Type and length validation at write time before the second run, so the retry cannot fail the same way."),
],
"related": [
 ("/slack/public-file-links-exposed/", "the file URL that works for everyone instead of nobody"),
 ("/slack/http-200-ok-false/", "the same 200-means-nothing trap on the Web API"),
 ("/slack/file-deleted-link-rot/", "how many of those ids still resolve a year later"),
],
"citations": [CITE_FILES_INFO, CITE_WORKING_FILES, CITE_SO_DOWNLOAD, CITE_SO_PUBLIC],
})
