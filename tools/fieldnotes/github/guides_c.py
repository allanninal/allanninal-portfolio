#!/usr/bin/env python3
"""/github/ field notes, batch C — the writing.

Four webhook failures, all of them visible through the hooks API and none of
them visible from the receiving end. A hook whose deliveries have been failing
for a month, a hook with no secret so nothing is signed, a hook that was never
subscribed to the event a handler was written for, and two hooks pointed at one
URL so every event arrives twice.

Two constraints shape every script here. GitHub masks a webhook secret as
`********` when it is set and omits the key entirely when it is not, so a
missing secret is a hard finding and a *wrong* secret is not detectable at all
until deliveries come back 401. And the delivery log is the best repair
primitive any provider in these notes offers: it says what failed, when, and
with which status code, and there is a redelivery endpoint to replay it. This
section is read only, so the scripts print that call rather than making it.
"""

CITE_REPO_HOOKS = ("Repository webhooks — GitHub REST API",
                   "https://docs.github.com/en/rest/repos/webhooks")
CITE_ORG_HOOKS = ("Organization webhooks — GitHub REST API",
                  "https://docs.github.com/en/rest/orgs/webhooks")
CITE_FAILED = ("Handling failed webhook deliveries — GitHub Docs",
               "https://docs.github.com/en/webhooks/using-webhooks/handling-failed-webhook-deliveries")
CITE_VALIDATE = ("Validating webhook deliveries — GitHub Docs",
                 "https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries")
CITE_TROUBLE = ("Troubleshooting webhooks — GitHub Docs",
                "https://docs.github.com/en/webhooks/testing-and-troubleshooting-webhooks/troubleshooting-webhooks")
CITE_EVENTS = ("Webhook events and payloads — GitHub Docs",
               "https://docs.github.com/en/webhooks/webhook-events-and-payloads")
CITE_BEST = ("Best practices for using webhooks — GitHub Docs",
             "https://docs.github.com/en/webhooks/using-webhooks/best-practices-for-using-webhooks")
CITE_CREATING = ("Creating webhooks — GitHub Docs",
                 "https://docs.github.com/en/webhooks/using-webhooks/creating-webhooks")
CITE_APP_HOOKS = ("GitHub App webhooks — GitHub REST API",
                  "https://docs.github.com/en/rest/apps/webhooks")

GUIDES = [

{
"slug": "webhook-deliveries-failing",
"title": "Webhook deliveries are failing and nobody reads the log",
"description": "GitHub records every delivery attempt with the response it got. Your receiver has no record at all, which is why a month of 5xx goes unnoticed.",
"h1": "webhook deliveries are failing and nobody reads the log",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github webhook not firing", "github webhook deliveries failing",
             "github webhook 500", "github redeliver webhook",
             "github hook last_response"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Someone opens a pull request and the bot that should comment on it says nothing. You grep your receiver's logs for the last hour and find no request at all, which points the finger at GitHub. It is not GitHub. The delivery happened, your server answered <code>502</code>, and GitHub wrote that down in a log you have never opened.",
"short_answer": """<p>Read <code>GET /repos/{owner}/{repo}/hooks</code> and look at <code>last_response</code> on each hook: <code>code</code>, <code>status</code> and <code>message</code> for the most recent attempt. One request, immediate verdict.</p>
<p>Then read <code>GET /repos/{owner}/{repo}/hooks/{hook_id}/deliveries?per_page=100</code>, where every attempt carries <code>status</code>, <code>status_code</code>, <code>event</code>, <code>duration</code>, <code>delivered_at</code>, <code>guid</code> and <code>redelivery</code>. Group the failures by status code, because the repair for a <code>401</code> and the repair for a timeout have nothing in common. Anything you lost can be replayed with the redelivery endpoint, but only inside the retention window.</p>""",
"problem": """<p>Every other integration failure leaves a trace on both sides. This one leaves a trace on GitHub's side only. Your receiver's access log records requests it handled; a request that arrived and blew up in a middlebox, or that arrived and returned <code>500</code> from a framework error page, may never reach the code that does your logging. From where you are standing, the events simply stopped.</p>
<p>So the discovery path is always the same and always late. A user notices that something downstream of an event did not happen. Someone re-runs it by hand. Weeks later a second report arrives, and only then does anyone open the hook and find several hundred failed deliveries stretching back to a deploy nobody connected to webhooks. By that point the oldest of those deliveries has aged out of the log and cannot be replayed at all.</p>""",
"why": """<p><strong>The delivery record belongs to GitHub, not to you.</strong> GitHub stores each attempt with the response it received, including attempts that your application never saw. A reverse proxy returning <code>413</code> on a large <code>push</code> payload, a WAF returning <code>403</code>, a platform returning <code>502</code> while a container restarts: all three are invisible in your logs and all three are one field in the delivery record.</p>
<p><strong>A failing hook is not a disabled hook.</strong> GitHub keeps trying, so nothing escalates on its own. The hook stays <code>active</code>, the delivery log fills with red, and no state change ever fires an alert. The only way this becomes visible is if something goes and looks.</p>
<p><strong>The status code is the whole diagnosis, and it gets thrown away.</strong> A run of <code>401</code> or <code>403</code> means your own server rejected GitHub, which is what a mismatched webhook secret looks like from the outside. A run of <code>5xx</code> means the payload arrived and your handler raised. A timeout means the handler is doing its work synchronously and ran past ten seconds. A missing status code means nothing answered at all: DNS, TLS or a closed port. Reporting these as one number called "failures" is how the repair gets guessed at.</p>
<p><strong>The log has a horizon.</strong> Deliveries are retained for a limited window, and the redelivery endpoint can only replay what is still in it. Every day this goes unnoticed converts recoverable events into permanently lost ones.</p>""",
"steps": [
 {"h": "Read last_response first, because it costs one request",
  "body": """<p><code>GET /repos/{owner}/{repo}/hooks</code> returns every hook with a <code>last_response</code> object. A <code>code</code> outside the 2xx range on any hook is enough to know something is wrong before you page a single delivery, and a <code>code</code> of <code>null</code> means the hook has never delivered anything at all &mdash; a different problem with a different cause.</p>"""},
 {"h": "Page the delivery log and bucket by what actually happened",
  "body": """<p><code>GET /repos/{owner}/{repo}/hooks/{hook_id}/deliveries?per_page=100</code>, following <code>rel="next"</code> in the <code>Link</code> header. Sort each record into a bucket by <code>status_code</code> and <code>status</code>: rejected (401, 403), server error (5xx), timed out, unreachable (no code at all), other client error (400, 404, 413). The dominant bucket is the finding.</p>"""},
 {"h": "Read the window, not just the count",
  "body": """<p>Keep the earliest and latest <code>delivered_at</code> for both successes and failures. If the newest delivery succeeded and every failure is older, this is already fixed and what remains is a backfill. If failures continue up to the present, it is live. Those two situations produce the same failure count and want opposite responses.</p>"""},
 {"h": "Fix the receiver for the bucket you found",
  "body": """<p>A 5xx run wants the exception traced. A timeout run wants the handler to answer immediately and do its work on a queue. A 401 or 403 run wants the signing secret compared against the one GitHub is signing with &mdash; and note that the API will never confirm that comparison for you; the delivery log is the only place a wrong secret becomes visible.</p>"""},
 {"h": "Replay what is still in the window",
  "body": """<p>Once the endpoint answers <code>2xx</code>, replay each failed delivery with <code>POST /repos/{owner}/{repo}/hooks/{hook_id}/deliveries/{delivery_id}/attempts</code>. The script prints that call for every failure it found rather than making it. Replays arrive with <code>redelivery: true</code> and the same <code>guid</code>, so a receiver that keys on the guid will treat them correctly.</p>"""},
],
"verify": """<p>Re-run the script after the receiver change. Every hook should report <code>clean</code>, or <code>recovered</code> with a backfill count that goes to zero once you have replayed it.</p>
<pre><code class="language-bash">python3 github_hook_delivery_audit.py --repo acme/api
# 2 hook(s), 0 failing, 0 delivery(ies) needing a replay</code></pre>""",
"code_intro": "Two GETs per hook and nothing else. The bucketing and the verdict are pure functions because the status code is the entire diagnosis here, and a classifier that collapses a timeout into a 5xx sends you to read a stack trace that does not exist. The redelivery endpoint is printed with the exact delivery id, never called.",
"py_file": "github_hook_delivery_audit.py",
"py": '''"""Report GitHub webhooks whose deliveries are failing, and say how they fail.

Read only. Every request is a GET, so a token with read access to the repository
and its hooks is enough. The redelivery call is printed for a human to run, never
made here: this script holds a credential that can reach your repositories.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_hook_delivery_audit")

API = "https://api.github.com"
UA = "github-hook-delivery-audit/1.0"

# Failure buckets, most diagnostic first. Ties in the dominant-bucket scan are
# broken by this order, so a hook failing equally often on two causes reports the
# one that names a specific repair rather than the one that says "other".
FAILURE_ORDER = ("rejected", "server-error", "timeout", "unreachable",
                 "client-error", "unknown")


def bucket(delivery):
    """Sort one delivery record into a bucket. Pure.

    status_code is the diagnosis. A record with no code at all never reached a
    server, which is a network problem; a record with 401 or 403 reached one that
    refused it, which is usually a signature the receiver would not accept. These
    want opposite repairs and are routinely reported as one number.
    """
    status = str(delivery.get("status") or "").strip().lower()
    raw = delivery.get("status_code")
    try:
        code = int(raw)
    except (TypeError, ValueError):
        code = 0

    if 200 <= code < 300:
        return "ok"
    if "tim" in status:
        return "timeout"
    if not code:
        return "unreachable"
    if code in (401, 403):
        return "rejected"
    if 400 <= code < 500:
        return "client-error"
    if 500 <= code < 600:
        return "server-error"
    return "unknown"


def triage(hook):
    """Read the hook's last_response, which is the one-request version of this.

    Pure. code is null on a hook that has never delivered anything, which is not
    a failure and must not be reported as one: it means the hook is new, is
    inactive, or is subscribed to events that have not happened.
    """
    last = hook.get("last_response") or {}
    code = last.get("code")
    if code is None:
        return ("never", "no delivery attempt recorded yet")
    try:
        code = int(code)
    except (TypeError, ValueError):
        return ("unknown", "unreadable last_response code %r" % (last.get("code"),))
    if 200 <= code < 300:
        return ("ok", "last attempt returned %d" % code)
    message = str(last.get("message") or "").strip()
    return ("failing", "last attempt returned %d%s"
            % (code, ": " + message if message else ""))


def summarize(deliveries):
    """Count deliveries by bucket and keep the ends of the window. Pure.

    delivered_at is ISO 8601 in UTC on every record, so string comparison orders
    them correctly and nothing needs parsing to find the first and last of each.
    """
    out = {"total": 0, "ok": 0, "failed": 0, "redeliveries": 0, "counts": {},
           "guids": {}, "last_ok": None, "first_failed": None, "last_failed": None}
    for d in deliveries or []:
        kind = bucket(d)
        when = str(d.get("delivered_at") or "")
        out["total"] += 1
        if d.get("redelivery"):
            out["redeliveries"] += 1
        if kind == "ok":
            out["ok"] += 1
            if when and (out["last_ok"] is None or when > out["last_ok"]):
                out["last_ok"] = when
            continue
        out["failed"] += 1
        out["counts"][kind] = out["counts"].get(kind, 0) + 1
        ids = out["guids"].setdefault(kind, [])
        if len(ids) < 5 and d.get("id") is not None:
            ids.append(d.get("id"))
        if when:
            if out["first_failed"] is None or when < out["first_failed"]:
                out["first_failed"] = when
            if out["last_failed"] is None or when > out["last_failed"]:
                out["last_failed"] = when
    return out


def verdict(summary):
    """Classify one hook from its delivery summary. Pure.

    Returns (state, detail). "recovered" exists because a fixed hook and a
    broken one produce the same failure count, and the difference between them
    is whether anything has succeeded since.
    """
    total = int(summary.get("total") or 0)
    if not total:
        return ("empty",
                "no deliveries in the retained window. Either nothing this hook "
                "subscribes to has happened, or the hook is not active.")

    failed = int(summary.get("failed") or 0)
    if not failed:
        return ("clean", "%d delivery(ies), all accepted" % total)

    last_ok = summary.get("last_ok")
    last_failed = summary.get("last_failed")
    if last_ok and last_failed and last_ok > last_failed:
        return ("recovered",
                "%d of %d failed, but the most recent delivery succeeded. The "
                "receiver is working; %d event(s) are still waiting on a replay."
                % (failed, total, failed))

    counts = summary.get("counts") or {}
    worst = None
    for kind in FAILURE_ORDER:
        n = counts.get(kind, 0)
        if n and (worst is None or n > counts[worst]):
            worst = kind
    n = counts.get(worst, 0)

    if worst == "rejected":
        return (worst,
                "%d of %d came back 401 or 403. Your own server refused GitHub. "
                "This is the only shape a mismatched webhook secret takes from "
                "outside: the API will not compare secrets for you." % (n, total))
    if worst == "server-error":
        return (worst,
                "%d of %d returned 5xx. The payload arrived and the handler "
                "raised, so the trace is in your application, not in the "
                "network." % (n, total))
    if worst == "timeout":
        return (worst,
                "%d of %d timed out. GitHub allows a receiver 10 seconds; a "
                "handler doing its real work synchronously runs past that as "
                "soon as the payload grows." % (n, total))
    if worst == "unreachable":
        return (worst,
                "%d of %d recorded no status code at all, so nothing answered: "
                "DNS, TLS, a closed port, or an allow-list that no longer "
                "matches GitHub's hook ranges." % (n, total))
    return (worst or "unknown",
            "%d of %d failed with a 4xx that is not an auth error, which is "
            "usually a route that moved (404) or a body the handler would not "
            "parse (400)." % (n, total))


def next_link(response):
    """The rel=next URL from the Link header, or None."""
    for part in (response.headers.get("Link") or "").split(","):
        chunk = part.strip()
        if chunk.startswith("<") and chunk.endswith('rel="next"'):
            return chunk[1:chunk.index(">")]
    return None


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from GitHub: GITHUB_TOKEN is missing, expired or "
                         "malformed")
    if r.status_code in (403, 404):
        raise SystemExit("%d from %s: reading hooks needs admin:repo_hook (or "
                         "the fine-grained Webhooks: Read permission). GitHub "
                         "returns 404 rather than 403 when a token cannot see a "
                         "resource at all." % (r.status_code, url))
    r.raise_for_status()
    return r


def page(session, url, key=None, limit=1000, **params):
    """Follow Link rel=next until the limit. Returns a flat list."""
    out = []
    while url and len(out) < limit:
        r = get(session, url, **params)
        body = r.json()
        out.extend(body if isinstance(body, list) else body.get(key) or [])
        url, params = next_link(r), {}
    return out[:limit]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", required=True, help="owner/name")
    ap.add_argument("--hook", type=int, default=None,
                    help="only this hook id (default: every hook on the repo)")
    ap.add_argument("--max-deliveries", type=int, default=300,
                    help="stop paging each hook's delivery log after this many")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_TOKEN (a read-only token is enough)")
        return 2

    owner, _, name = args.repo.partition("/")
    if not (owner and name):
        log.error("--repo takes owner/name, for example acme/api")
        return 2

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": UA,
    })

    base = "%s/repos/%s/%s/hooks" % (API, owner, name)
    hooks = page(session, base, per_page=100)
    if args.hook:
        hooks = [h for h in hooks if h.get("id") == args.hook]
    if not hooks:
        log.info("no webhooks on %s that this token can see", args.repo)
        return 0

    failing = replayable = 0
    for hook in hooks:
        hid = hook.get("id")
        url = (hook.get("config") or {}).get("url", "?")
        state, detail = triage(hook)
        log.info("hook %s %s  last_response: %s (%s)", hid, url, state, detail)

        deliveries = page(session, "%s/%s/deliveries" % (base, hid),
                          limit=args.max_deliveries, per_page=100)
        summary = summarize(deliveries)
        state, detail = verdict(summary)
        line = "  %-12s %s" % (state, detail)
        if state in ("clean", "empty"):
            log.info(line)
            continue

        log.warning(line)
        log.warning("  failures from %s to %s, %d redelivery(ies) already in "
                    "the log", summary["first_failed"], summary["last_failed"],
                    summary["redeliveries"])
        if state != "recovered":
            failing += 1
        replayable += summary["failed"]
        for kind, ids in sorted(summary["guids"].items()):
            for did in ids:
                log.warning("  repair: POST %s/%s/deliveries/%s/attempts  "
                            "(%s)", base, hid, did, kind)

    log.info("%d hook(s), %d failing, %d delivery(ies) needing a replay",
             len(hooks), failing, replayable)
    return 1 if failing else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-hook-delivery-audit.mjs",
"js": '''/**
 * Report GitHub webhooks whose deliveries are failing, and say how they fail.
 *
 * Read only. Every request is a GET. The redelivery call is printed for a human
 * to run, never made here.
 */
const API = 'https://api.github.com';
const UA = 'github-hook-delivery-audit/1.0';

// Failure buckets, most diagnostic first. Ties are broken by this order.
const FAILURE_ORDER = ['rejected', 'server-error', 'timeout', 'unreachable',
  'client-error', 'unknown'];

/**
 * Sort one delivery record into a bucket. Pure. A record with no status code
 * never reached a server; one with 401 or 403 reached one that refused it.
 */
export function bucket(delivery) {
  const status = String(delivery.status ?? '').trim().toLowerCase();
  const code = Number.parseInt(delivery.status_code, 10) || 0;
  if (code >= 200 && code < 300) return 'ok';
  if (status.includes('tim')) return 'timeout';
  if (!code) return 'unreachable';
  if (code === 401 || code === 403) return 'rejected';
  if (code >= 400 && code < 500) return 'client-error';
  if (code >= 500 && code < 600) return 'server-error';
  return 'unknown';
}

/**
 * Read the hook's last_response: the one-request version of this whole check.
 * A null code means the hook has never delivered anything, which is not a
 * failure.
 */
export function triage(hook) {
  const last = hook.last_response ?? {};
  if (last.code === null || last.code === undefined) {
    return ['never', 'no delivery attempt recorded yet'];
  }
  const code = Number.parseInt(last.code, 10);
  if (!Number.isFinite(code)) {
    return ['unknown', `unreadable last_response code ${JSON.stringify(last.code)}`];
  }
  if (code >= 200 && code < 300) return ['ok', `last attempt returned ${code}`];
  const message = String(last.message ?? '').trim();
  return ['failing',
    `last attempt returned ${code}${message ? `: ${message}` : ''}`];
}

/** Count deliveries by bucket and keep the ends of the window. Pure. */
export function summarize(deliveries) {
  const out = {
    total: 0, ok: 0, failed: 0, redeliveries: 0, counts: {}, guids: {},
    last_ok: null, first_failed: null, last_failed: null,
  };
  for (const d of deliveries ?? []) {
    const kind = bucket(d);
    const when = String(d.delivered_at ?? '');
    out.total += 1;
    if (d.redelivery) out.redeliveries += 1;
    if (kind === 'ok') {
      out.ok += 1;
      if (when && (out.last_ok === null || when > out.last_ok)) out.last_ok = when;
      continue;
    }
    out.failed += 1;
    out.counts[kind] = (out.counts[kind] ?? 0) + 1;
    const ids = (out.guids[kind] ??= []);
    if (ids.length < 5 && d.id !== undefined && d.id !== null) ids.push(d.id);
    if (when) {
      if (out.first_failed === null || when < out.first_failed) out.first_failed = when;
      if (out.last_failed === null || when > out.last_failed) out.last_failed = when;
    }
  }
  return out;
}

/** Classify one hook from its delivery summary. Pure. Returns [state, detail]. */
export function verdict(summary) {
  const total = summary.total ?? 0;
  if (!total) {
    return ['empty',
      'no deliveries in the retained window. Either nothing this hook ' +
      'subscribes to has happened, or the hook is not active.'];
  }
  const failed = summary.failed ?? 0;
  if (!failed) return ['clean', `${total} delivery(ies), all accepted`];

  if (summary.last_ok && summary.last_failed && summary.last_ok > summary.last_failed) {
    return ['recovered',
      `${failed} of ${total} failed, but the most recent delivery succeeded. ` +
      `The receiver is working; ${failed} event(s) are still waiting on a replay.`];
  }

  const counts = summary.counts ?? {};
  let worst = null;
  for (const kind of FAILURE_ORDER) {
    const n = counts[kind] ?? 0;
    if (n && (worst === null || n > counts[worst])) worst = kind;
  }
  const n = counts[worst] ?? 0;

  if (worst === 'rejected') {
    return [worst,
      `${n} of ${total} came back 401 or 403. Your own server refused GitHub. ` +
      'This is the only shape a mismatched webhook secret takes from outside: ' +
      'the API will not compare secrets for you.'];
  }
  if (worst === 'server-error') {
    return [worst,
      `${n} of ${total} returned 5xx. The payload arrived and the handler ` +
      'raised, so the trace is in your application, not in the network.'];
  }
  if (worst === 'timeout') {
    return [worst,
      `${n} of ${total} timed out. GitHub allows a receiver 10 seconds; a ` +
      'handler doing its real work synchronously runs past that as soon as the ' +
      'payload grows.'];
  }
  if (worst === 'unreachable') {
    return [worst,
      `${n} of ${total} recorded no status code at all, so nothing answered: ` +
      "DNS, TLS, a closed port, or an allow-list that no longer matches GitHub's " +
      'hook ranges.'];
  }
  return [worst ?? 'unknown',
    `${n} of ${total} failed with a 4xx that is not an auth error, which is ` +
    'usually a route that moved (404) or a body the handler would not parse (400).'];
}

function nextLink(res) {
  for (const part of (res.headers.get('link') ?? '').split(',')) {
    const chunk = part.trim();
    if (chunk.startsWith('<') && chunk.endsWith('rel="next"')) {
      return chunk.slice(1, chunk.indexOf('>'));
    }
  }
  return null;
}

async function get(token, url) {
  const res = await fetch(url, {
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      'User-Agent': UA,
    },
  });
  if (res.status === 401) {
    throw new Error('401 from GitHub: GITHUB_TOKEN is missing, expired or malformed');
  }
  if (res.status === 403 || res.status === 404) {
    throw new Error(`${res.status} from ${url}: reading hooks needs ` +
      'admin:repo_hook (or the fine-grained Webhooks: Read permission). GitHub ' +
      'returns 404 rather than 403 when a token cannot see a resource at all.');
  }
  if (!res.ok) throw new Error(`${res.status} from ${url}`);
  return res;
}

async function page(token, url, limit = 1000) {
  const out = [];
  let next = url;
  while (next && out.length < limit) {
    const res = await get(token, next);
    out.push(...(await res.json()));
    next = nextLink(res);
  }
  return out.slice(0, limit);
}

async function main() {
  const repo = process.argv[2];
  const token = process.env.GITHUB_TOKEN;
  if (!token) {
    console.error('set GITHUB_TOKEN (a read-only token is enough)');
    process.exitCode = 2;
    return;
  }
  if (!repo || !repo.includes('/')) {
    console.error('usage: node github-hook-delivery-audit.mjs owner/name');
    process.exitCode = 2;
    return;
  }

  const base = `${API}/repos/${repo}/hooks`;
  const hooks = await page(token, `${base}?per_page=100`);
  if (hooks.length === 0) {
    console.log(`no webhooks on ${repo} that this token can see`);
    return;
  }

  let failing = 0;
  let replayable = 0;
  for (const hook of hooks) {
    const url = hook.config?.url ?? '?';
    const [tstate, tdetail] = triage(hook);
    console.log(`hook ${hook.id} ${url}  last_response: ${tstate} (${tdetail})`);

    const deliveries = await page(token, `${base}/${hook.id}/deliveries?per_page=100`, 300);
    const summary = summarize(deliveries);
    const [state, detail] = verdict(summary);
    const line = `  ${state.padEnd(12)} ${detail}`;
    if (state === 'clean' || state === 'empty') { console.log(line); continue; }

    console.warn(line);
    console.warn(`  failures from ${summary.first_failed} to ${summary.last_failed}, ` +
      `${summary.redeliveries} redelivery(ies) already in the log`);
    if (state !== 'recovered') failing += 1;
    replayable += summary.failed;
    for (const [kind, ids] of Object.entries(summary.guids).sort()) {
      for (const id of ids) {
        console.warn(`  repair: POST ${base}/${hook.id}/deliveries/${id}/attempts  (${kind})`);
      }
    }
  }

  console.log(`${hooks.length} hook(s), ${failing} failing, ` +
    `${replayable} delivery(ies) needing a replay`);
  process.exitCode = failing ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing token, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The cases worth pinning are the ones that look alike from a distance. A delivery with no status code is not a 5xx. A hook whose failures all predate its last success is not broken. And <code>last_response.code</code> of <code>null</code> means nothing has ever been delivered, which a naive numeric comparison reads as a failure and reports as an outage.",
"test_py_file": "test_github_hook_delivery_audit.py",
"test_py": '''from github_hook_delivery_audit import bucket, summarize, triage, verdict


def delivery(code, status="failure", when="2026-08-01T10:00:00Z", did=1, redelivery=False):
    return {"id": did, "status": status, "status_code": code,
            "delivered_at": when, "redelivery": redelivery}


def test_two_hundred_is_the_only_success():
    assert bucket(delivery(200, "OK")) == "ok"
    assert bucket(delivery(204, "OK")) == "ok"


def test_no_status_code_is_unreachable_not_a_server_error():
    # Nothing answered, so there is no stack trace to go and read.
    assert bucket(delivery(0)) == "unreachable"
    assert bucket({"status": "failure"}) == "unreachable"


def test_a_timeout_is_its_own_bucket_whatever_the_code_says():
    assert bucket({"status": "timed out", "status_code": 0}) == "timeout"


def test_auth_failures_are_separated_from_other_client_errors():
    assert bucket(delivery(401)) == "rejected"
    assert bucket(delivery(403)) == "rejected"
    assert bucket(delivery(404)) == "client-error"
    assert bucket(delivery(502)) == "server-error"


def test_triage_treats_a_null_code_as_never_delivered():
    state, detail = triage({"last_response": {"code": None, "status": "unused"}})
    assert state == "never"
    assert "no delivery" in detail


def test_triage_reads_the_failing_code_and_message():
    state, detail = triage({"last_response": {"code": 502, "message": "Bad Gateway"}})
    assert state == "failing"
    assert "502" in detail and "Bad Gateway" in detail


def test_summarize_keeps_both_ends_of_the_window():
    s = summarize([
        delivery(200, "OK", "2026-08-01T10:00:00Z"),
        delivery(500, when="2026-08-02T10:00:00Z", did=2),
        delivery(500, when="2026-08-03T10:00:00Z", did=3, redelivery=True),
    ])
    assert s["total"] == 3 and s["ok"] == 1 and s["failed"] == 2
    assert s["first_failed"] == "2026-08-02T10:00:00Z"
    assert s["last_failed"] == "2026-08-03T10:00:00Z"
    assert s["last_ok"] == "2026-08-01T10:00:00Z"
    assert s["redeliveries"] == 1
    assert s["guids"]["server-error"] == [2, 3]


def test_an_empty_log_is_not_a_healthy_hook():
    state, _ = verdict(summarize([]))
    assert state == "empty"


def test_failures_older_than_the_last_success_are_already_fixed():
    s = summarize([delivery(500, when="2026-08-01T10:00:00Z"),
                   delivery(200, "OK", "2026-08-02T10:00:00Z", did=2)])
    state, detail = verdict(s)
    assert state == "recovered"
    assert "replay" in detail


def test_the_dominant_bucket_names_the_repair():
    s = summarize([delivery(500), delivery(500, did=2), delivery(404, did=3)])
    state, detail = verdict(s)
    assert state == "server-error"
    assert "handler" in detail


def test_a_run_of_401s_points_at_the_secret_without_claiming_to_read_it():
    s = summarize([delivery(401), delivery(401, did=2)])
    state, detail = verdict(s)
    assert state == "rejected"
    assert "will not compare secrets" in detail
''',
"test_js_file": "github-hook-delivery-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  bucket, summarize, triage, verdict,
} from './github-hook-delivery-audit.mjs';

const delivery = (code, status = 'failure', when = '2026-08-01T10:00:00Z',
  id = 1, redelivery = false) =>
  ({ id, status, status_code: code, delivered_at: when, redelivery });

test('two hundred is the only success', () => {
  assert.equal(bucket(delivery(200, 'OK')), 'ok');
  assert.equal(bucket(delivery(204, 'OK')), 'ok');
});

test('no status code is unreachable, not a server error', () => {
  assert.equal(bucket(delivery(0)), 'unreachable');
  assert.equal(bucket({ status: 'failure' }), 'unreachable');
});

test('a timeout is its own bucket whatever the code says', () => {
  assert.equal(bucket({ status: 'timed out', status_code: 0 }), 'timeout');
});

test('auth failures are separated from other client errors', () => {
  assert.equal(bucket(delivery(401)), 'rejected');
  assert.equal(bucket(delivery(403)), 'rejected');
  assert.equal(bucket(delivery(404)), 'client-error');
  assert.equal(bucket(delivery(502)), 'server-error');
});

test('triage treats a null code as never delivered', () => {
  const [state, detail] = triage({ last_response: { code: null, status: 'unused' } });
  assert.equal(state, 'never');
  assert.match(detail, /no delivery/);
});

test('triage reads the failing code and message', () => {
  const [state, detail] = triage({ last_response: { code: 502, message: 'Bad Gateway' } });
  assert.equal(state, 'failing');
  assert.match(detail, /502: Bad Gateway/);
});

test('summarize keeps both ends of the window', () => {
  const s = summarize([
    delivery(200, 'OK', '2026-08-01T10:00:00Z'),
    delivery(500, 'failure', '2026-08-02T10:00:00Z', 2),
    delivery(500, 'failure', '2026-08-03T10:00:00Z', 3, true),
  ]);
  assert.equal(s.total, 3);
  assert.equal(s.failed, 2);
  assert.equal(s.first_failed, '2026-08-02T10:00:00Z');
  assert.equal(s.last_failed, '2026-08-03T10:00:00Z');
  assert.equal(s.last_ok, '2026-08-01T10:00:00Z');
  assert.equal(s.redeliveries, 1);
  assert.deepEqual(s.guids['server-error'], [2, 3]);
});

test('an empty log is not a healthy hook', () => {
  assert.equal(verdict(summarize([]))[0], 'empty');
});

test('failures older than the last success are already fixed', () => {
  const s = summarize([
    delivery(500, 'failure', '2026-08-01T10:00:00Z'),
    delivery(200, 'OK', '2026-08-02T10:00:00Z', 2),
  ]);
  const [state, detail] = verdict(s);
  assert.equal(state, 'recovered');
  assert.match(detail, /replay/);
});

test('the dominant bucket names the repair', () => {
  const s = summarize([delivery(500), delivery(500, 'failure', '2026-08-01T10:00:00Z', 2),
    delivery(404, 'failure', '2026-08-01T10:00:00Z', 3)]);
  const [state, detail] = verdict(s);
  assert.equal(state, 'server-error');
  assert.match(detail, /handler/);
});

test('a run of 401s points at the secret without claiming to read it', () => {
  const s = summarize([delivery(401), delivery(401, 'failure', '2026-08-01T10:00:00Z', 2)]);
  const [state, detail] = verdict(s);
  assert.equal(state, 'rejected');
  assert.match(detail, /will not compare secrets/);
});
''',
"faq": [
 ("How long does GitHub keep webhook deliveries?",
  "Long enough to diagnose a problem you notice quickly and not long enough to diagnose one you notice late. The delivery log is a bounded window, and the redelivery endpoint can only replay what is still in it, so the practical answer is that every day a failure goes unnoticed converts recoverable events into lost ones. Read last_response on a schedule rather than reading the log after a complaint."),
 ("Why does my receiver have no record of the request?",
  "Because it never reached your application code. A reverse proxy rejecting a large push payload, a WAF returning 403, or a platform returning 502 during a restart all answer GitHub without your handler running. GitHub records what it received; your log records what your handler saw, and those are different sets."),
 ("Does the script redeliver the failed events for me?",
  "No. This section is read only, so it prints POST /repos/{owner}/{repo}/hooks/{hook_id}/deliveries/{delivery_id}/attempts with the exact delivery id for each failure and leaves the decision to you. Replaying into a receiver that is still broken just refills the log."),
 ("A redelivery arrived and my handler ran twice. Is that expected?",
  "Yes. A replay carries redelivery: true and the same guid as the original attempt, so it is the same event, not a new one. If running it twice caused a visible side effect, the handler is not idempotent, and GitHub's at-least-once delivery would have found that eventually anyway."),
 ("Every delivery returns 401. Can the script tell me whether my secret is wrong?",
  "No, and nothing can. The API returns the secret masked as ******** when it is set, so a wrong secret is indistinguishable from a right one at the configuration level. A sustained run of 401 or 403 in the delivery log is the only evidence that exists, which is exactly why the script reports that bucket separately instead of counting it as a generic failure."),
],
"related": [
 ("/github/webhook-no-secret/", "A webhook with no secret sends no signature"),
 ("/github/webhook-event-not-subscribed/", "The hook is not subscribed to your event"),
 ("/github/duplicate-webhooks/", "The same URL registered twice"),
],
"citations": [CITE_FAILED, CITE_REPO_HOOKS, CITE_TROUBLE, CITE_BEST],
},


{
"slug": "webhook-no-secret",
"title": "A webhook with no secret sends no signature to verify",
"description": "GitHub sends X-Hub-Signature-256 only when a secret is set. Without one the header is absent, and a receiver that checks it when present checks nothing.",
"h1": "a webhook with no secret sends no signature to verify",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github webhook secret", "x-hub-signature-256 missing",
             "github webhook signature verification", "validate github webhook",
             "github webhook config secret"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The receiver has a signature check. It reads <code>X-Hub-Signature-256</code>, computes an HMAC over the body, compares in constant time, and returns <code>401</code> when they differ. It has never returned <code>401</code>, because the hook it serves has no secret, so GitHub does not send the header, and the check quietly skips itself on every request.",
"short_answer": """<p>Read <code>GET /repos/{owner}/{repo}/hooks</code> and look at <code>config</code>. When a secret is set, <code>config.secret</code> comes back masked as <code>********</code>. When it is not, the <code>secret</code> key is <strong>absent from <code>config</code> entirely</strong>. Absence is the finding, and it is unambiguous.</p>
<p>What the API cannot tell you is whether a secret that <em>is</em> set matches the one in your environment. The value is masked, so a wrong secret and a right one look identical here. The only place a mismatch shows up is the delivery log, as a run of <code>401</code> or <code>403</code> coming back from your own server &mdash; which the script also counts, and reports as a separate state.</p>""",
"problem": """<p>A webhook URL is not a secret. It is in your infrastructure code, in the GitHub settings page, in the browser history of everyone who has ever configured it, and in the logs of every proxy between them. Without a signature, possession of that URL is authorisation: anyone who has it can post a payload shaped like a <code>push</code> and your handler will believe it.</p>
<p>What makes this worse than a plain missing check is that the check usually exists. The common receiver pattern is "if the header is present, verify it", which is defensive-looking code that is exactly equivalent to no verification when the header is never present. Nothing fails, no test catches it, and the endpoint looks hardened in review.</p>""",
"why": """<p><strong>GitHub sends the signature only when there is something to sign with.</strong> <code>X-Hub-Signature-256</code> is an HMAC-SHA256 of the raw request body keyed on the hook's secret. With no secret configured there is no key, so the header is omitted rather than sent empty. A receiver branching on its presence therefore takes the skip path every time.</p>
<p><strong>The absence is structural, not masked.</strong> This is the one webhook secret question the API answers honestly. A set secret is masked as <code>********</code>; an unset one is not a masked empty string, it is a missing key. So <code>"secret" not in config</code> is a real, reliable test, and it is worth running across every hook you own rather than the one you happen to be looking at.</p>
<p><strong>A wrong secret is invisible until deliveries fail.</strong> Rotating the secret on GitHub without updating the receiver, or the reverse, produces a configuration that looks perfect from the API: the key is there, masked, exactly as it should be. Every delivery then comes back <code>401</code> from your own server. That pattern in the delivery log is the entire observable surface of a mismatch, and the script treats a hook with a secret plus a run of auth failures as its own finding for that reason.</p>
<p><strong>Hooks accumulate in places nobody audits.</strong> The repository hook someone added by hand during an incident, the org hook created by a script three years ago, the App's own webhook: each is configured separately and each has its own secret or lack of one. One unsigned hook is enough to accept a forged event.</p>""",
"steps": [
 {"h": "List every hook the token can see, not just the obvious one",
  "body": """<p><code>GET /repos/{owner}/{repo}/hooks</code> for the repository and <code>GET /orgs/{org}/hooks</code> for the organization. These are independent resources; a repository can be covered by both, and the org hook is the one most likely to have been created once and never looked at again.</p>"""},
 {"h": "Test for the absence of the key, not for a falsy value",
  "body": """<p>The check is <code>"secret" not in hook["config"]</code>. Testing <code>config.get("secret")</code> for truthiness happens to work, but it reads as though an empty value were the expected shape, and it hides the fact that GitHub's answer here is structural: the key exists or it does not.</p>"""},
 {"h": "Count 401 and 403 responses in the delivery log",
  "body": """<p><code>GET /repos/{owner}/{repo}/hooks/{hook_id}/deliveries?per_page=100</code>. On a hook that <em>has</em> a secret, a sustained run of auth failures is the fingerprint of a mismatch between the value GitHub signs with and the value your receiver checks against. The script reports that separately from a plain missing secret because the repair is different: one sets a secret, the other reconciles two that already exist.</p>"""},
 {"h": "Make the receiver require the header",
  "body": """<p>Reject when <code>X-Hub-Signature-256</code> is missing rather than skipping the check. Compute the HMAC over the exact raw bytes of the request &mdash; not a re-serialised JSON object, whose key order and whitespace will differ &mdash; and compare with a constant-time function such as <code>hmac.compare_digest</code>.</p>"""},
 {"h": "Set the secret, then re-run and expect the masked value",
  "body": """<p>After setting a high-entropy secret on the hook, <code>config.secret</code> reads <code>********</code>. That is the strongest confirmation the API offers: it proves a secret exists, and it deliberately proves nothing about which one.</p>"""},
],
"verify": """<p>Re-run the script. Every hook should report <code>signed</code>, and the report should say plainly that a masked secret is not a verified one.</p>
<pre><code class="language-bash">python3 github_hook_secret_audit.py --repo acme/api --org acme
# 4 hook(s), 0 unsigned, 0 rejecting deliveries</code></pre>""",
"code_intro": "One list request per scope, plus one delivery page per hook to catch the mismatch case. The classifier is pure and its states are deliberately asymmetric: <code>unsigned</code> is a fact, <code>signed</code> is only the absence of evidence, and the detail string says so rather than implying the script checked something it cannot check.",
"py_file": "github_hook_secret_audit.py",
"py": '''"""Find GitHub webhooks with no secret, and hooks whose secret is being rejected.

Read only. Every request is a GET. The script can prove a hook has no secret,
because the key is simply absent from config. It cannot prove a secret is
correct: the value comes back masked, so a wrong secret and a right one are
indistinguishable until deliveries start failing.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_hook_secret_audit")

API = "https://api.github.com"
UA = "github-hook-secret-audit/1.0"

# What GitHub returns in place of a secret that is set. Its presence is the only
# positive signal available; its value carries no information at all.
MASK = "********"


def secret_state(hook):
    """Is a secret configured on this hook? Pure.

    GitHub masks a configured secret and omits the key when there is none, so
    absence is a real finding rather than an inference. Anything else about the
    secret, including whether it is the right one, is not knowable from here.
    """
    config = hook.get("config")
    if not isinstance(config, dict):
        return "unknown"
    if "secret" not in config:
        return "absent"
    value = config.get("secret")
    if value is None or str(value).strip() == "":
        return "absent"
    return "set"


def unauthorized(deliveries):
    """Count deliveries the receiver refused with 401 or 403. Pure.

    Returns (rejected, total). These are the responses your own server gave, so
    on a hook that has a secret they are the only visible trace of a mismatch
    between the value GitHub signs with and the value the receiver checks.
    """
    rejected = total = 0
    for d in deliveries or []:
        total += 1
        try:
            code = int(d.get("status_code"))
        except (TypeError, ValueError):
            continue
        if code in (401, 403):
            rejected += 1
    return rejected, total


def verdict(hook, rejected=0, delivered=0):
    """Classify one hook. Pure, so the asymmetry is visible and testable.

    Returns (state, detail). "unsigned" is a fact about the configuration.
    "signed" is the absence of evidence and says so.
    """
    state = secret_state(hook)
    url = (hook.get("config") or {}).get("url") or "the configured URL"

    if state == "unknown":
        return ("unknown", "no config on this hook, which should not happen; "
                           "re-read it with GET /repos/{owner}/{repo}/hooks/{id}")

    if state == "absent":
        return ("unsigned",
                "config has no secret key, so GitHub sends no X-Hub-Signature-256 "
                "header with these payloads. A receiver that verifies only when "
                "the header is present verifies nothing, and anyone who learns %s "
                "can post to it." % url)

    if rejected and delivered and rejected * 2 >= delivered:
        return ("rejected",
                "a secret is set and %d of %d recent deliveries came back 401 or "
                "403 from your server. That is what a mismatched secret looks "
                "like from here; the value itself is masked and cannot be "
                "compared." % (rejected, delivered))

    detail = ("a secret is set, so payloads are signed. The value is masked as "
              "%s, so this says nothing about whether it matches the one your "
              "receiver holds." % MASK)
    if rejected:
        detail += (" %d of %d recent deliveries were refused with 401 or 403, "
                   "which is worth reading before you trust it."
                   % (rejected, delivered))
    return ("signed", detail)


def next_link(response):
    """The rel=next URL from the Link header, or None."""
    for part in (response.headers.get("Link") or "").split(","):
        chunk = part.strip()
        if chunk.startswith("<") and chunk.endswith('rel="next"'):
            return chunk[1:chunk.index(">")]
    return None


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from GitHub: GITHUB_TOKEN is missing, expired or "
                         "malformed")
    if r.status_code in (403, 404):
        raise SystemExit("%d from %s: listing hooks needs admin:repo_hook for a "
                         "repository or admin:org_hook for an organization"
                         % (r.status_code, url))
    r.raise_for_status()
    return r


def page(session, url, limit=500, **params):
    out = []
    while url and len(out) < limit:
        r = get(session, url, **params)
        out.extend(r.json())
        url, params = next_link(r), {}
    return out[:limit]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", action="append", default=[],
                    help="owner/name; repeat for several repositories")
    ap.add_argument("--org", action="append", default=[],
                    help="organization login; repeat for several orgs")
    ap.add_argument("--max-deliveries", type=int, default=50,
                    help="deliveries to read per hook when looking for 401s "
                         "(0 to skip that read entirely)")
    args = ap.parse_args()

    if not (args.repo or args.org):
        log.error("pass at least one --repo owner/name or --org login")
        return 2

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_TOKEN (a read-only token is enough)")
        return 2

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": UA,
    })

    scopes = []
    for repo in args.repo:
        owner, _, name = repo.partition("/")
        if not (owner and name):
            log.error("--repo takes owner/name, for example acme/api")
            return 2
        scopes.append(("repo " + repo, "%s/repos/%s/%s/hooks" % (API, owner, name)))
    for org in args.org:
        scopes.append(("org " + org, "%s/orgs/%s/hooks" % (API, org)))

    unsigned = refusing = total = 0
    for label, base in scopes:
        for hook in page(session, base, per_page=100):
            total += 1
            rejected = delivered = 0
            if args.max_deliveries:
                rejected, delivered = unauthorized(
                    page(session, "%s/%s/deliveries" % (base, hook.get("id")),
                         limit=args.max_deliveries, per_page=100))
            state, detail = verdict(hook, rejected, delivered)
            url = (hook.get("config") or {}).get("url", "?")
            line = "%-8s %s %s  %s" % (state, label, url, detail)
            if state == "signed":
                log.info(line)
                continue
            log.warning(line)
            if state == "unsigned":
                unsigned += 1
                log.warning("  repair: set a high-entropy secret on this hook, "
                            "then make the receiver reject any request without "
                            "X-Hub-Signature-256 rather than skipping the check")
            elif state == "rejected":
                refusing += 1
                log.warning("  repair: compare the secret in your receiver's "
                            "environment with the one on the hook, then replay "
                            "with POST %s/%s/deliveries/{delivery_id}/attempts",
                            base, hook.get("id"))

    log.info("%d hook(s), %d unsigned, %d rejecting deliveries",
             total, unsigned, refusing)
    return 1 if (unsigned or refusing) else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-hook-secret-audit.mjs",
"js": '''/**
 * Find GitHub webhooks with no secret, and hooks whose secret is being rejected.
 *
 * Read only. The script can prove a hook has no secret, because the key is
 * absent from config. It cannot prove a secret is correct: the value comes back
 * masked, so a wrong secret and a right one are indistinguishable until
 * deliveries start failing.
 */
const API = 'https://api.github.com';
const UA = 'github-hook-secret-audit/1.0';

// What GitHub returns in place of a secret that is set. Its presence is the only
// positive signal available; its value carries no information at all.
const MASK = '********';

/**
 * Is a secret configured on this hook? Pure. GitHub masks a configured secret
 * and omits the key when there is none, so absence is a real finding.
 */
export function secretState(hook) {
  const config = hook.config;
  if (config === null || typeof config !== 'object') return 'unknown';
  if (!Object.prototype.hasOwnProperty.call(config, 'secret')) return 'absent';
  const value = config.secret;
  if (value === null || value === undefined || String(value).trim() === '') {
    return 'absent';
  }
  return 'set';
}

/**
 * Count deliveries the receiver refused with 401 or 403. Pure. On a hook that
 * has a secret these are the only visible trace of a mismatch.
 */
export function unauthorized(deliveries) {
  let rejected = 0;
  let total = 0;
  for (const d of deliveries ?? []) {
    total += 1;
    const code = Number.parseInt(d.status_code, 10);
    if (code === 401 || code === 403) rejected += 1;
  }
  return { rejected, total };
}

/**
 * Classify one hook. Pure. "unsigned" is a fact about the configuration;
 * "signed" is the absence of evidence and says so.
 */
export function verdict(hook, rejected = 0, delivered = 0) {
  const state = secretState(hook);
  const url = hook.config?.url ?? 'the configured URL';

  if (state === 'unknown') {
    return ['unknown', 'no config on this hook, which should not happen; ' +
      're-read it with GET /repos/{owner}/{repo}/hooks/{id}'];
  }

  if (state === 'absent') {
    return ['unsigned',
      'config has no secret key, so GitHub sends no X-Hub-Signature-256 header ' +
      'with these payloads. A receiver that verifies only when the header is ' +
      `present verifies nothing, and anyone who learns ${url} can post to it.`];
  }

  if (rejected && delivered && rejected * 2 >= delivered) {
    return ['rejected',
      `a secret is set and ${rejected} of ${delivered} recent deliveries came ` +
      'back 401 or 403 from your server. That is what a mismatched secret looks ' +
      'like from here; the value itself is masked and cannot be compared.'];
  }

  let detail = 'a secret is set, so payloads are signed. The value is masked as ' +
    `${MASK}, so this says nothing about whether it matches the one your ` +
    'receiver holds.';
  if (rejected) {
    detail += ` ${rejected} of ${delivered} recent deliveries were refused with ` +
      '401 or 403, which is worth reading before you trust it.';
  }
  return ['signed', detail];
}

function nextLink(res) {
  for (const part of (res.headers.get('link') ?? '').split(',')) {
    const chunk = part.trim();
    if (chunk.startsWith('<') && chunk.endsWith('rel="next"')) {
      return chunk.slice(1, chunk.indexOf('>'));
    }
  }
  return null;
}

async function get(token, url) {
  const res = await fetch(url, {
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      'User-Agent': UA,
    },
  });
  if (res.status === 401) {
    throw new Error('401 from GitHub: GITHUB_TOKEN is missing, expired or malformed');
  }
  if (res.status === 403 || res.status === 404) {
    throw new Error(`${res.status} from ${url}: listing hooks needs ` +
      'admin:repo_hook for a repository or admin:org_hook for an organization');
  }
  if (!res.ok) throw new Error(`${res.status} from ${url}`);
  return res;
}

async function page(token, url, limit = 500) {
  const out = [];
  let next = url;
  while (next && out.length < limit) {
    const res = await get(token, next);
    out.push(...(await res.json()));
    next = nextLink(res);
  }
  return out.slice(0, limit);
}

async function main() {
  const token = process.env.GITHUB_TOKEN;
  if (!token) {
    console.error('set GITHUB_TOKEN (a read-only token is enough)');
    process.exitCode = 2;
    return;
  }

  const scopes = [];
  for (const arg of process.argv.slice(2)) {
    if (arg.includes('/')) scopes.push([`repo ${arg}`, `${API}/repos/${arg}/hooks`]);
    else scopes.push([`org ${arg}`, `${API}/orgs/${arg}/hooks`]);
  }
  if (scopes.length === 0) {
    console.error('usage: node github-hook-secret-audit.mjs owner/name [org ...]');
    process.exitCode = 2;
    return;
  }

  let unsigned = 0;
  let refusing = 0;
  let total = 0;
  for (const [label, base] of scopes) {
    for (const hook of await page(token, `${base}?per_page=100`)) {
      total += 1;
      const deliveries = await page(token,
        `${base}/${hook.id}/deliveries?per_page=100`, 50);
      const { rejected, total: delivered } = unauthorized(deliveries);
      const [state, detail] = verdict(hook, rejected, delivered);
      const url = hook.config?.url ?? '?';
      const line = `${state.padEnd(8)} ${label} ${url}  ${detail}`;
      if (state === 'signed') { console.log(line); continue; }
      console.warn(line);
      if (state === 'unsigned') {
        unsigned += 1;
        console.warn('  repair: set a high-entropy secret on this hook, then ' +
          'make the receiver reject any request without X-Hub-Signature-256 ' +
          'rather than skipping the check');
      } else if (state === 'rejected') {
        refusing += 1;
        console.warn("  repair: compare the secret in your receiver's " +
          'environment with the one on the hook, then replay with POST ' +
          `${base}/${hook.id}/deliveries/{delivery_id}/attempts`);
      }
    }
  }

  console.log(`${total} hook(s), ${unsigned} unsigned, ${refusing} rejecting deliveries`);
  process.exitCode = (unsigned || refusing) ? 1 : 0;
}

// Only run when invoked directly, so importing this module from the test file
// does not run main(), fail on the missing token, and fail the test file with it.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The tests pin the distinction the whole note rests on: a missing <code>secret</code> key and a masked one are different answers, and neither of them is a promise that the secret is correct. The masked case is asserted to produce a detail string that admits what it does not know, because a report that says <code>signed</code> and stops is how a mismatched secret survives an audit.",
"test_py_file": "test_github_hook_secret_audit.py",
"test_py": '''from github_hook_secret_audit import secret_state, unauthorized, verdict

SIGNED = {"id": 1, "config": {"url": "https://hooks.example.com/gh",
                              "secret": "********", "content_type": "json"}}
UNSIGNED = {"id": 2, "config": {"url": "https://hooks.example.com/gh",
                                "content_type": "json"}}


def test_a_missing_key_is_the_finding():
    # GitHub omits the key entirely rather than returning an empty string.
    assert secret_state(UNSIGNED) == "absent"


def test_a_masked_value_means_a_secret_exists():
    assert secret_state(SIGNED) == "set"


def test_an_empty_secret_counts_as_absent():
    assert secret_state({"config": {"secret": "  "}}) == "absent"


def test_a_hook_without_config_is_not_silently_signed():
    assert secret_state({"id": 3}) == "unknown"
    assert verdict({"id": 3})[0] == "unknown"


def test_the_unsigned_detail_names_the_missing_header():
    state, detail = verdict(UNSIGNED)
    assert state == "unsigned"
    assert "X-Hub-Signature-256" in detail
    assert "hooks.example.com" in detail


def test_signed_admits_it_cannot_check_the_value():
    state, detail = verdict(SIGNED)
    assert state == "signed"
    assert "masked" in detail
    assert "whether it matches" in detail


def test_a_run_of_refusals_on_a_signed_hook_is_its_own_state():
    state, detail = verdict(SIGNED, rejected=18, delivered=20)
    assert state == "rejected"
    assert "mismatched secret" in detail


def test_one_refusal_in_fifty_is_not_a_mismatch():
    state, detail = verdict(SIGNED, rejected=1, delivered=50)
    assert state == "signed"
    assert "1 of 50" in detail


def test_unauthorized_counts_only_auth_failures():
    rejected, total = unauthorized([{"status_code": 401}, {"status_code": 403},
                                    {"status_code": 500}, {"status_code": 200},
                                    {"status_code": None}])
    assert (rejected, total) == (2, 5)
''',
"test_js_file": "github-hook-secret-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  secretState, unauthorized, verdict,
} from './github-hook-secret-audit.mjs';

const SIGNED = {
  id: 1,
  config: { url: 'https://hooks.example.com/gh', secret: '********', content_type: 'json' },
};
const UNSIGNED = {
  id: 2,
  config: { url: 'https://hooks.example.com/gh', content_type: 'json' },
};

test('a missing key is the finding', () => {
  assert.equal(secretState(UNSIGNED), 'absent');
});

test('a masked value means a secret exists', () => {
  assert.equal(secretState(SIGNED), 'set');
});

test('an empty secret counts as absent', () => {
  assert.equal(secretState({ config: { secret: '  ' } }), 'absent');
});

test('a hook without config is not silently signed', () => {
  assert.equal(secretState({ id: 3 }), 'unknown');
  assert.equal(verdict({ id: 3 })[0], 'unknown');
});

test('the unsigned detail names the missing header', () => {
  const [state, detail] = verdict(UNSIGNED);
  assert.equal(state, 'unsigned');
  assert.match(detail, /X-Hub-Signature-256/);
  assert.match(detail, /hooks\\.example\\.com/);
});

test('signed admits it cannot check the value', () => {
  const [state, detail] = verdict(SIGNED);
  assert.equal(state, 'signed');
  assert.match(detail, /masked/);
  assert.match(detail, /whether it matches/);
});

test('a run of refusals on a signed hook is its own state', () => {
  const [state, detail] = verdict(SIGNED, 18, 20);
  assert.equal(state, 'rejected');
  assert.match(detail, /mismatched secret/);
});

test('one refusal in fifty is not a mismatch', () => {
  const [state, detail] = verdict(SIGNED, 1, 50);
  assert.equal(state, 'signed');
  assert.match(detail, /1 of 50/);
});

test('unauthorized counts only auth failures', () => {
  const { rejected, total } = unauthorized([{ status_code: 401 },
    { status_code: 403 }, { status_code: 500 }, { status_code: 200 },
    { status_code: null }]);
  assert.equal(rejected, 2);
  assert.equal(total, 5);
});
''',
"faq": [
 ("Can the script tell me whether my webhook secret is correct?",
  "No. GitHub returns config.secret as ******** when a secret is set, so every set secret looks identical through the API. The script can prove a secret is missing, because then the key is absent from config altogether, and it can report a run of 401 or 403 responses in the delivery log, which is the only observable trace of a mismatch. It cannot compare values, and no read-only check can."),
 ("Why not just verify the signature when the header is present?",
  "Because with no secret configured the header is never present, so that branch never executes and the endpoint is unauthenticated while looking hardened. Require the header: a request without X-Hub-Signature-256 should be rejected, not waved through."),
 ("Is X-Hub-Signature good enough instead?",
  "That is the legacy SHA-1 header, kept for old receivers. GitHub sends both, and current guidance is to validate X-Hub-Signature-256 over the raw request body with a constant-time comparison. If your receiver only checks the SHA-1 header, treat that as a separate item on the same list."),
 ("Does a webhook secret protect the contents of the payload?",
  "No. A signature proves origin and integrity, not confidentiality. The payload still crosses the network in whatever the URL's scheme provides, which is why an http:// webhook URL is a distinct problem from an unsigned one."),
 ("What permission does this need?",
  "Reading hook configuration needs admin:repo_hook on a classic token for repository hooks, or admin:org_hook for organization hooks; on a fine-grained token it is the Webhooks: Read permission. Without it GitHub answers 404 rather than 403, so a missing permission reads like a missing repository."),
],
"related": [
 ("/github/webhook-deliveries-failing/", "Deliveries failing where nobody reads the log"),
 ("/github/duplicate-webhooks/", "The same URL registered twice"),
 ("/github/webhook-event-not-subscribed/", "The hook is not subscribed to your event"),
],
"citations": [CITE_VALIDATE, CITE_REPO_HOOKS, CITE_ORG_HOOKS, CITE_BEST],
},


{
"slug": "webhook-event-not-subscribed",
"title": "The hook is not subscribed to the event you are waiting for",
"description": "A handler written for release or workflow_job never runs, and there is no error to find. An unsubscribed event does not fail: the delivery never exists.",
"h1": "the hook is not subscribed to the event you are waiting for",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github webhook event not received", "github hook events array",
             "github webhook not triggering", "github webhook subscribe event",
             "workflow_job webhook missing"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The handler was written, reviewed, unit tested against a saved payload, and deployed. In production it has never executed once. There is no error anywhere because there is no failure anywhere: the hook was created years ago with <code>push</code> and <code>pull_request</code>, and the event your handler waits for has never been sent to it.",
"short_answer": """<p>Read <code>GET /repos/{owner}/{repo}/hooks</code> and diff the hook's <code>events</code> array against the set of events your handlers actually implement. An event in your code but not in that array can never arrive, and produces no error of any kind.</p>
<p>Then read <code>GET /repos/{owner}/{repo}/hooks/{hook_id}/deliveries?per_page=100</code> and collect the distinct <code>event</code> values that really appeared in the window. That splits "not subscribed" from "subscribed but nothing has happened", which look the same from your handler's point of view and want completely different responses.</p>""",
"problem": """<p>Most integration bugs announce themselves. This one is defined by the absence of an event, and absence has no timestamp, no status code and no log line. The handler is not broken; it is simply never invoked, which is indistinguishable from a quiet week.</p>
<p>The usual sequence: a hook is created early on with the two or three events the first feature needed. A year later someone adds a <code>release</code> handler, tests it locally by replaying a payload file, and ships. It works perfectly in every environment where it is exercised by hand, and never fires in the one where it matters. The bug is not in the code that was reviewed; it is in a configuration object nobody opened.</p>""",
"why": """<p><strong>An unsubscribed event is not refused, it is not generated.</strong> GitHub delivers only what the hook's <code>events</code> array lists. There is no rejected delivery, no entry in the log, nothing to alert on. The only artefact is a gap, and gaps are not monitored.</p>
<p><strong>Event names and action names get confused.</strong> The event is <code>pull_request</code>; <code>opened</code>, <code>closed</code> and <code>synchronize</code> are <em>actions</em> inside its payload. Subscribing to <code>pull_request.opened</code> is not a thing you can do, and a handler registered under that string will not match the header <code>X-GitHub-Event: pull_request</code> either. The same trap catches <code>pull-request</code> with a hyphen, which is how the resource is spelled in URLs and not how the event is spelled anywhere.</p>
<p><strong>Silence is ambiguous without the delivery log.</strong> A subscribed event that has not occurred looks exactly like an unsubscribed one. Collecting the distinct <code>event</code> values from recent deliveries turns that into two separate findings: one is a configuration change, the other is patience or a wrong repository.</p>
<p><strong>The wildcard hides the problem and creates another.</strong> <code>events: ["*"]</code> means nothing is ever missing, at the cost of receiving every event type GitHub has now and every one it adds later. It converts a subscription bug into a volume and cost problem, which is why the script reports it as its own state rather than as success.</p>""",
"steps": [
 {"h": "Write down the events your handlers actually implement",
  "body": """<p>Take the list from the router in your receiver &mdash; the switch on <code>X-GitHub-Event</code> &mdash; not from memory or from a document. That list is the contract; everything else in this check is a comparison against it. The script takes it as a repeated <code>--handles</code> argument.</p>"""},
 {"h": "Read the hook's events array",
  "body": """<p><code>GET /repos/{owner}/{repo}/hooks</code>. Compare canonically: lowercase, and treat a hyphen as an underscore, so <code>pull-request</code> in your list is recognised as a spelling of <code>pull_request</code> rather than reported as a missing subscription. Strip anything after a dot, because that is an action name and never a subscription.</p>"""},
 {"h": "Collect the events that were really delivered",
  "body": """<p><code>GET /repos/{owner}/{repo}/hooks/{hook_id}/deliveries?per_page=100</code> and take the distinct <code>event</code> values. Subscribed and seen is healthy. Subscribed and never seen inside a busy window is worth a look: it is often a hook on a fork, or on the wrong repository in an org that has three with similar names.</p>"""},
 {"h": "Report the traffic no handler implements",
  "body": """<p>The comparison runs both ways. Events arriving that nothing handles are volume you pay to receive, verify and discard &mdash; and on a monorepo the <code>push</code> payloads doing that are not small. Those are candidates for removal from the array, not additions to your code.</p>"""},
 {"h": "Add the missing events explicitly, not with a wildcard",
  "body": """<p>Update the hook's <code>events</code> to the exact GitHub names. Resist <code>["*"]</code>: it subscribes you to every event type that exists now and every one added in future, and it makes this class of bug undetectable by turning every question about coverage into "yes".</p>"""},
],
"verify": """<p>Re-run with the same <code>--handles</code> list. Every handler should map to a subscribed event, and the report should show no unhandled traffic worth removing.</p>
<pre><code class="language-bash">python3 github_hook_event_coverage.py --repo acme/api --handles push --handles pull_request --handles release
# 1 hook(s), 0 handler(s) with no subscription, 0 unhandled event(s) arriving</code></pre>""",
"code_intro": "One list request plus one page of deliveries per hook. The whole check is a set comparison, so it is one pure function with the network on either side of it &mdash; and it is the normalisation inside that function that does the real work, because <code>pull-request</code>, <code>pull_request.opened</code> and <code>Pull_Request</code> are all the same subscription and none of them is spelled the way GitHub spells it.",
"py_file": "github_hook_event_coverage.py",
"py": '''"""Compare the events a webhook is subscribed to against the ones you handle.

Read only. Two GETs per hook: the hook list, and one page of its delivery log to
see which events really arrived. An unsubscribed event produces no failure and no
delivery record, so the only way to find one is to compare two lists.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_hook_event_coverage")

API = "https://api.github.com"
UA = "github-hook-event-coverage/1.0"


def normalize(name):
    """Canonical form of an event name. Pure.

    Three spellings reach this function and none of them is always right. GitHub
    names events with underscores (pull_request), URLs use hyphens, and a handler
    is often registered under an action (pull_request.opened) which is a field
    inside the payload rather than something a hook can subscribe to.
    """
    base = str(name or "").strip().lower().replace("-", "_")
    if "." in base:
        base = base.split(".", 1)[0]
    return base


def coverage(handled, subscribed, seen=()):
    """Compare handlers, subscriptions and observed traffic. Pure.

    Returns a list of rows, one per event on either side, each with a state:

      missing    subscribed nowhere, so the handler can never run
      delivered  subscribed and seen in the delivery window
      quiet      subscribed but not seen, which may just mean nothing happened
      wildcard   the hook subscribes to everything, including future events
      unhandled  arriving or subscribed with no handler behind it
    """
    subs = {}
    wildcard = False
    for raw in subscribed or []:
        if str(raw).strip() == "*":
            wildcard = True
            continue
        subs[normalize(raw)] = str(raw)

    seen_events = {}
    for raw in seen or []:
        key = normalize(raw)
        seen_events[key] = seen_events.get(key, 0) + 1

    rows = []
    claimed = set()
    for raw in handled or []:
        key = normalize(raw)
        claimed.add(key)
        note = ""
        if str(raw) != key:
            note = "your handler is registered as %r; GitHub spells this %r" % (
                str(raw), key)
        if wildcard:
            state = "wildcard"
        elif key not in subs:
            state = "missing"
        elif key in seen_events:
            state = "delivered"
        else:
            state = "quiet"
        rows.append({"event": key, "handler": str(raw), "state": state,
                     "seen": seen_events.get(key, 0), "note": note})

    for key in sorted(set(subs) | set(seen_events)):
        if key in claimed:
            continue
        rows.append({"event": key, "handler": None, "state": "unhandled",
                     "seen": seen_events.get(key, 0),
                     "note": "subscribed" if key in subs else "arriving without a subscription"})
    return rows


def next_link(response):
    """The rel=next URL from the Link header, or None."""
    for part in (response.headers.get("Link") or "").split(","):
        chunk = part.strip()
        if chunk.startswith("<") and chunk.endswith('rel="next"'):
            return chunk[1:chunk.index(">")]
    return None


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from GitHub: GITHUB_TOKEN is missing, expired or "
                         "malformed")
    if r.status_code in (403, 404):
        raise SystemExit("%d from %s: reading hooks needs admin:repo_hook, and "
                         "GitHub answers 404 rather than 403 when the token "
                         "cannot see the resource at all" % (r.status_code, url))
    r.raise_for_status()
    return r


def page(session, url, limit=500, **params):
    out = []
    while url and len(out) < limit:
        r = get(session, url, **params)
        out.extend(r.json())
        url, params = next_link(r), {}
    return out[:limit]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", required=True, help="owner/name")
    ap.add_argument("--handles", action="append", default=[],
                    help="an event your receiver implements; repeat per event")
    ap.add_argument("--max-deliveries", type=int, default=200,
                    help="deliveries to read per hook when collecting the "
                         "events that really arrived")
    args = ap.parse_args()

    if not args.handles:
        log.error("pass --handles once per event your receiver implements, "
                  "taken from its switch on X-GitHub-Event")
        return 2

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_TOKEN (a read-only token is enough)")
        return 2

    owner, _, name = args.repo.partition("/")
    if not (owner and name):
        log.error("--repo takes owner/name, for example acme/api")
        return 2

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": UA,
    })

    base = "%s/repos/%s/%s/hooks" % (API, owner, name)
    hooks = page(session, base, per_page=100)
    if not hooks:
        log.info("no webhooks on %s that this token can see", args.repo)
        return 0

    missing = unhandled = 0
    for hook in hooks:
        hid = hook.get("id")
        url = (hook.get("config") or {}).get("url", "?")
        subscribed = hook.get("events") or []
        deliveries = page(session, "%s/%s/deliveries" % (base, hid),
                          limit=args.max_deliveries, per_page=100)
        seen = [d.get("event") for d in deliveries]
        log.info("hook %s %s  subscribes to %d event(s), %d delivery(ies) read",
                 hid, url, len(subscribed), len(deliveries))

        for row in coverage(args.handles, subscribed, seen):
            line = "  %-10s %s%s" % (row["state"], row["event"],
                                     "  " + row["note"] if row["note"] else "")
            if row["state"] in ("delivered", "quiet"):
                log.info(line)
                continue
            log.warning(line)
            if row["state"] == "missing":
                missing += 1
                log.warning("     repair: add %r to this hook's events array; "
                            "until then the handler cannot run and nothing will "
                            "report an error", row["event"])
            elif row["state"] == "unhandled":
                unhandled += 1
                log.warning("     %d delivery(ies) of an event nothing handles: "
                            "volume you receive, verify and discard",
                            row["seen"])
            elif row["state"] == "wildcard":
                log.warning("     the hook subscribes to *, so this arrives "
                            "along with every event type GitHub adds in future")

    log.info("%d hook(s), %d handler(s) with no subscription, %d unhandled "
             "event(s) arriving", len(hooks), missing, unhandled)
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-hook-event-coverage.mjs",
"js": '''/**
 * Compare the events a webhook is subscribed to against the ones you handle.
 *
 * Read only. Two GETs per hook: the hook list, and one page of its delivery log.
 * An unsubscribed event produces no failure and no delivery record, so the only
 * way to find one is to compare two lists.
 */
const API = 'https://api.github.com';
const UA = 'github-hook-event-coverage/1.0';

/**
 * Canonical form of an event name. Pure. GitHub names events with underscores,
 * URLs use hyphens, and handlers are often registered under an action
 * (pull_request.opened), which is a payload field and not a subscription.
 */
export function normalize(name) {
  const base = String(name ?? '').trim().toLowerCase().replaceAll('-', '_');
  return base.includes('.') ? base.slice(0, base.indexOf('.')) : base;
}

/**
 * Compare handlers, subscriptions and observed traffic. Pure. States:
 * missing, delivered, quiet, wildcard, unhandled.
 */
export function coverage(handled, subscribed, seen = []) {
  const subs = new Map();
  let wildcard = false;
  for (const raw of subscribed ?? []) {
    if (String(raw).trim() === '*') { wildcard = true; continue; }
    subs.set(normalize(raw), String(raw));
  }

  const seenEvents = new Map();
  for (const raw of seen ?? []) {
    const key = normalize(raw);
    seenEvents.set(key, (seenEvents.get(key) ?? 0) + 1);
  }

  const rows = [];
  const claimed = new Set();
  for (const raw of handled ?? []) {
    const key = normalize(raw);
    claimed.add(key);
    const note = String(raw) !== key
      ? `your handler is registered as '${raw}'; GitHub spells this '${key}'`
      : '';
    let state;
    if (wildcard) state = 'wildcard';
    else if (!subs.has(key)) state = 'missing';
    else if (seenEvents.has(key)) state = 'delivered';
    else state = 'quiet';
    rows.push({ event: key, handler: String(raw), state,
      seen: seenEvents.get(key) ?? 0, note });
  }

  for (const key of [...new Set([...subs.keys(), ...seenEvents.keys()])].sort()) {
    if (claimed.has(key)) continue;
    rows.push({ event: key, handler: null, state: 'unhandled',
      seen: seenEvents.get(key) ?? 0,
      note: subs.has(key) ? 'subscribed' : 'arriving without a subscription' });
  }
  return rows;
}

function nextLink(res) {
  for (const part of (res.headers.get('link') ?? '').split(',')) {
    const chunk = part.trim();
    if (chunk.startsWith('<') && chunk.endsWith('rel="next"')) {
      return chunk.slice(1, chunk.indexOf('>'));
    }
  }
  return null;
}

async function get(token, url) {
  const res = await fetch(url, {
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      'User-Agent': UA,
    },
  });
  if (res.status === 401) {
    throw new Error('401 from GitHub: GITHUB_TOKEN is missing, expired or malformed');
  }
  if (res.status === 403 || res.status === 404) {
    throw new Error(`${res.status} from ${url}: reading hooks needs ` +
      'admin:repo_hook, and GitHub answers 404 rather than 403 when the token ' +
      'cannot see the resource at all');
  }
  if (!res.ok) throw new Error(`${res.status} from ${url}`);
  return res;
}

async function page(token, url, limit = 500) {
  const out = [];
  let next = url;
  while (next && out.length < limit) {
    const res = await get(token, next);
    out.push(...(await res.json()));
    next = nextLink(res);
  }
  return out.slice(0, limit);
}

async function main() {
  const [repo, ...handles] = process.argv.slice(2);
  const token = process.env.GITHUB_TOKEN;
  if (!token) {
    console.error('set GITHUB_TOKEN (a read-only token is enough)');
    process.exitCode = 2;
    return;
  }
  if (!repo || !repo.includes('/') || handles.length === 0) {
    console.error('usage: node github-hook-event-coverage.mjs owner/name push pull_request');
    process.exitCode = 2;
    return;
  }

  const base = `${API}/repos/${repo}/hooks`;
  const hooks = await page(token, `${base}?per_page=100`);
  if (hooks.length === 0) {
    console.log(`no webhooks on ${repo} that this token can see`);
    return;
  }

  let missing = 0;
  let unhandled = 0;
  for (const hook of hooks) {
    const url = hook.config?.url ?? '?';
    const subscribed = hook.events ?? [];
    const deliveries = await page(token,
      `${base}/${hook.id}/deliveries?per_page=100`, 200);
    const seen = deliveries.map((d) => d.event);
    console.log(`hook ${hook.id} ${url}  subscribes to ${subscribed.length} ` +
      `event(s), ${deliveries.length} delivery(ies) read`);

    for (const row of coverage(handles, subscribed, seen)) {
      const line = `  ${row.state.padEnd(10)} ${row.event}` +
        (row.note ? `  ${row.note}` : '');
      if (row.state === 'delivered' || row.state === 'quiet') {
        console.log(line);
        continue;
      }
      console.warn(line);
      if (row.state === 'missing') {
        missing += 1;
        console.warn(`     repair: add '${row.event}' to this hook's events ` +
          'array; until then the handler cannot run and nothing will report an error');
      } else if (row.state === 'unhandled') {
        unhandled += 1;
        console.warn(`     ${row.seen} delivery(ies) of an event nothing ` +
          'handles: volume you receive, verify and discard');
      } else if (row.state === 'wildcard') {
        console.warn('     the hook subscribes to *, so this arrives along with ' +
          'every event type GitHub adds in future');
      }
    }
  }

  console.log(`${hooks.length} hook(s), ${missing} handler(s) with no ` +
    `subscription, ${unhandled} unhandled event(s) arriving`);
  process.exitCode = missing ? 1 : 0;
}

// Only run when invoked directly, so importing this module from the test file
// does not run main(), fail on the missing token, and fail the test file with it.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Two cases carry the note. A handler for an event the hook does not carry has to come out as <code>missing</code> even though nothing anywhere has failed, and a handler registered as <code>pull_request.opened</code> has to be recognised as the <code>pull_request</code> subscription it already has rather than reported as a second missing event that no one can add.",
"test_py_file": "test_github_hook_event_coverage.py",
"test_py": '''from github_hook_event_coverage import coverage, normalize


def rows_by_event(rows):
    return {r["event"]: r for r in rows}


def test_normalize_accepts_the_three_spellings_people_use():
    assert normalize("pull_request") == "pull_request"
    assert normalize("pull-request") == "pull_request"
    assert normalize("Pull_Request.opened") == "pull_request"
    assert normalize(None) == ""


def test_an_unsubscribed_handler_is_the_finding():
    rows = rows_by_event(coverage(["release"], ["push", "pull_request"], ["push"]))
    assert rows["release"]["state"] == "missing"


def test_an_action_suffix_matches_the_event_it_belongs_to():
    # pull_request.opened is not something a hook can subscribe to, and treating
    # it as a separate event invents a repair that cannot be carried out.
    rows = rows_by_event(coverage(["pull_request.opened"], ["pull_request"],
                                  ["pull_request"]))
    assert rows["pull_request"]["state"] == "delivered"
    assert "GitHub spells this" in rows["pull_request"]["note"]


def test_subscribed_but_unseen_is_not_the_same_as_unsubscribed():
    rows = rows_by_event(coverage(["release"], ["release", "push"], ["push"]))
    assert rows["release"]["state"] == "quiet"


def test_a_wildcard_is_reported_rather_than_counted_as_success():
    rows = rows_by_event(coverage(["release"], ["*"], ["push"]))
    assert rows["release"]["state"] == "wildcard"


def test_traffic_nothing_handles_is_reported_too():
    rows = rows_by_event(coverage(["push"], ["push", "status"],
                                  ["push", "status", "status"]))
    assert rows["status"]["state"] == "unhandled"
    assert rows["status"]["seen"] == 2
    assert rows["push"]["state"] == "delivered"


def test_an_event_arriving_without_a_subscription_is_still_surfaced():
    rows = rows_by_event(coverage(["push"], ["push"], ["push", "ping"]))
    assert rows["ping"]["state"] == "unhandled"
    assert "without a subscription" in rows["ping"]["note"]


def test_case_and_hyphens_do_not_create_phantom_findings():
    rows = coverage(["Pull-Request"], ["pull_request"], ["pull_request"])
    assert [r["state"] for r in rows] == ["delivered"]
''',
"test_js_file": "github-hook-event-coverage.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { coverage, normalize } from './github-hook-event-coverage.mjs';

const byEvent = (rows) => Object.fromEntries(rows.map((r) => [r.event, r]));

test('normalize accepts the three spellings people use', () => {
  assert.equal(normalize('pull_request'), 'pull_request');
  assert.equal(normalize('pull-request'), 'pull_request');
  assert.equal(normalize('Pull_Request.opened'), 'pull_request');
  assert.equal(normalize(null), '');
});

test('an unsubscribed handler is the finding', () => {
  const rows = byEvent(coverage(['release'], ['push', 'pull_request'], ['push']));
  assert.equal(rows.release.state, 'missing');
});

test('an action suffix matches the event it belongs to', () => {
  const rows = byEvent(coverage(['pull_request.opened'], ['pull_request'],
    ['pull_request']));
  assert.equal(rows.pull_request.state, 'delivered');
  assert.match(rows.pull_request.note, /GitHub spells this/);
});

test('subscribed but unseen is not the same as unsubscribed', () => {
  const rows = byEvent(coverage(['release'], ['release', 'push'], ['push']));
  assert.equal(rows.release.state, 'quiet');
});

test('a wildcard is reported rather than counted as success', () => {
  const rows = byEvent(coverage(['release'], ['*'], ['push']));
  assert.equal(rows.release.state, 'wildcard');
});

test('traffic nothing handles is reported too', () => {
  const rows = byEvent(coverage(['push'], ['push', 'status'],
    ['push', 'status', 'status']));
  assert.equal(rows.status.state, 'unhandled');
  assert.equal(rows.status.seen, 2);
  assert.equal(rows.push.state, 'delivered');
});

test('an event arriving without a subscription is still surfaced', () => {
  const rows = byEvent(coverage(['push'], ['push'], ['push', 'ping']));
  assert.equal(rows.ping.state, 'unhandled');
  assert.match(rows.ping.note, /without a subscription/);
});

test('case and hyphens do not create phantom findings', () => {
  const rows = coverage(['Pull-Request'], ['pull_request'], ['pull_request']);
  assert.deepEqual(rows.map((r) => r.state), ['delivered']);
});
''',
"faq": [
 ("Why is there no error when an event is not subscribed?",
  "Because nothing happens. GitHub generates a delivery only for events in the hook's events array; an unsubscribed event is not refused, it is never created. There is no failed delivery, no status code and nothing to alert on, which is why this has to be found by comparing two lists rather than by watching for errors."),
 ("Can I subscribe to pull_request.opened?",
  "No. pull_request is the event; opened is the action field inside its payload. Hooks subscribe to events, and your receiver branches on the action after it has already been handed the delivery. The script normalises an action suffix back to its event so that a handler named this way is not reported as an unfixable missing subscription."),
 ("The event is in the array but I have never received it. What now?",
  "That is the quiet state, and it has two ordinary explanations: the event genuinely has not occurred in the retained window, or the hook is on a different repository than you think, most often a fork or a similarly named repo in the same org. Check the hook's own repository before changing any configuration."),
 ("Should I just subscribe to everything with a wildcard?",
  "It removes this bug and adds two others. You receive every event type GitHub has and every one it ships later, so a monorepo's push payloads dominate your receiver's time and the amount of repository data leaving GitHub grows for no benefit. The script reports a wildcard as its own state rather than as coverage."),
 ("Does this work for organization hooks and GitHub App events too?",
  "The same comparison applies, with a different source list. Org hooks have their own events array on GET /orgs/{org}/hooks. A GitHub App's subscriptions are set on the App itself rather than per installation, so they are not in this endpoint at all and are read with the App's own credentials."),
],
"related": [
 ("/github/duplicate-webhooks/", "The same URL registered twice"),
 ("/github/webhook-deliveries-failing/", "Deliveries failing where nobody reads the log"),
 ("/github/webhook-no-secret/", "A webhook with no secret sends no signature"),
],
"citations": [CITE_EVENTS, CITE_TROUBLE, CITE_REPO_HOOKS, CITE_CREATING],
},


{
"slug": "duplicate-webhooks",
"title": "The same webhook URL is registered on the org and the repo",
"description": "Every event is processed twice because two independent hooks point at one URL. Dormant idempotency bugs start firing and nothing in either hook looks wrong.",
"h1": "the same webhook URL is registered on the org and the repo",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github duplicate webhook", "github webhook fires twice",
             "org and repo webhook same url", "github webhook duplicate events",
             "x-github-delivery idempotency"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The bot comments twice on every pull request. Someone checks the receiver for a retry loop, finds none, and blames GitHub for sending duplicates. GitHub is sending exactly one copy of the event to each hook that asked for it &mdash; and two hooks asked, one on the repository and one on the organization, both pointing at the same URL.",
"short_answer": """<p>Collect <code>config.url</code> from <code>GET /orgs/{org}/hooks</code> and from <code>GET /repos/{owner}/{repo}/hooks</code> for each repository, normalise the URLs, and group. Any endpoint reached by more than one active hook whose <code>events</code> arrays overlap receives every event in that overlap twice.</p>
<p>Two hooks on one URL are not automatically a duplicate: if their event sets are disjoint, that is a deliberate split and the script says so rather than raising it. The finding is the intersection, and it is what you print.</p>""",
"problem": """<p>Duplicate delivery is the failure that turns latent bugs into visible ones. Every handler that was written as though it would run once &mdash; posting a comment, incrementing a counter, sending a notification, creating a deployment &mdash; now runs twice, and the ones that were quietly non-idempotent for years all surface in the same week.</p>
<p>It is also hard to see from the receiver, because both copies are legitimate. Each has a valid signature, each has a plausible payload, and the two arrive within a second of each other from the same source. Nothing about a single request marks it as the second copy. The evidence lives on the configuration side, in two objects that were created by different people at different times, neither of which is wrong on its own.</p>""",
"why": """<p><strong>Org hooks and repo hooks are independent resources.</strong> Nothing warns you that a URL is already receiving these events from another scope. A platform team adds an org hook to cover every repository; a per-repo hook created two years earlier by a setup script is still there, and neither view shows the other.</p>
<p><strong>URLs are compared by humans and they differ cosmetically.</strong> One hook is <code>https://hooks.example.com/gh</code>, the other <code>https://hooks.example.com/gh/</code>, and a third is on <code>HTTPS://Hooks.Example.com/gh</code>. Those are the same endpoint. Any comparison that does not lowercase the host and drop a trailing slash reports a clean account.</p>
<p><strong>Overlap is the finding, not co-location.</strong> Two hooks on one URL where one carries <code>push</code> and the other carries <code>issues</code> is a reasonable arrangement. Reporting it as a duplicate is how a report loses trust on its first run, so the intersection of the event sets is computed and printed, with a wildcard treated as intersecting everything.</p>
<p><strong>Delivery guids answer the question your receiver actually has.</strong> GitHub retries and redeliveries reuse a delivery's guid, so keying on <code>X-GitHub-Delivery</code> makes those harmless. Whether the org copy and the repo copy of one event share a guid is something you can observe rather than assume: the script reads both delivery logs and reports whether the same guid appears under both hooks, or whether the same event arrived under two different guids. That difference decides whether guid-based idempotency will save you or whether you need to key on something in the payload.</p>""",
"steps": [
 {"h": "Gather hooks from every scope that can reach the repository",
  "body": """<p><code>GET /orgs/{org}/hooks</code> and <code>GET /repos/{owner}/{repo}/hooks</code>. A GitHub App's webhook is a third possible source; it is configured on the App itself and read with the App's own credentials through <code>GET /app/hook/config</code>, which a repository token cannot do &mdash; so if an App is involved, count it manually.</p>"""},
 {"h": "Normalise before comparing",
  "body": """<p>Reduce each <code>config.url</code> to a lowercase host plus path with no trailing slash and no query string. Scheme is dropped deliberately: an <code>http</code> hook and an <code>https</code> hook to the same host and path both deliver, so they are duplicates of each other regardless of the scheme problem they also represent.</p>"""},
 {"h": "Intersect the event sets",
  "body": """<p>Group hooks by normalised endpoint and compute the intersection of their <code>events</code> arrays, treating <code>["*"]</code> as intersecting everything. An empty intersection is a deliberate split and is reported as such; a non-empty one is the list of events being processed twice.</p>"""},
 {"h": "Check whether the copies share a delivery guid",
  "body": """<p>Read a page of deliveries from each hook on the shared endpoint. If the same <code>guid</code> appears under both, a receiver that dedupes on <code>X-GitHub-Delivery</code> already handles this. If the same event arrives in the same minute under two different guids, guid-level idempotency will not help and you need a key from the payload itself.</p>"""},
 {"h": "Delete one hook, and fix the handler anyway",
  "body": """<p>Keep one source of truth &mdash; usually the org hook, or the App if you have one &mdash; and remove the redundant hook. Independently make the side effects idempotent, because retries, redeliveries and GitHub's at-least-once delivery all produce repeats that deleting a hook will not prevent.</p>"""},
],
"verify": """<p>Re-run after removing the redundant hook. Each endpoint should be reached from exactly one scope, and any remaining shared endpoint should report a disjoint event split rather than an overlap.</p>
<pre><code class="language-bash">python3 github_duplicate_hooks.py --org acme --repo acme/api --repo acme/web
# 6 hook(s) across 5 endpoint(s), 0 duplicated, 0 latent</code></pre>""",
"code_intro": "The reads are trivial &mdash; two list endpoints and a page of deliveries &mdash; and every decision is in two pure functions: the URL normalisation, which is what makes the comparison find anything at all, and the grouping, which is what stops it from crying wolf about two hooks that deliberately split the events between them.",
"py_file": "github_duplicate_hooks.py",
"py": '''"""Find one webhook URL registered by more than one GitHub hook.

Read only. Org hooks and repo hooks are independent objects, so the same URL can
be registered in both scopes and every overlapping event is then delivered twice.
The script prints which hook to remove; it never removes one.
"""
import argparse
import logging
import os
import sys
from urllib.parse import urlsplit

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_duplicate_hooks")

API = "https://api.github.com"
UA = "github-duplicate-hooks/1.0"

# A hook subscribed to "*" receives every event type, current and future, so it
# intersects with anything the other hook on the same URL carries.
WILDCARD = "*"


def endpoint(url):
    """Reduce a webhook URL to lowercase host plus path. Pure.

    Two hooks created years apart by different people differ cosmetically far
    more often than they differ meaningfully: a trailing slash, a capitalised
    host, http where the other is https. All of those deliver to the same server,
    and a raw string comparison across them finds nothing and reports a clean
    account.
    """
    if not url:
        return ""
    parts = urlsplit(str(url).strip())
    host = (parts.hostname or "").lower()
    if not host:
        return str(url).strip().lower().rstrip("/")
    port = ":%d" % parts.port if parts.port not in (None, 80, 443) else ""
    return host + port + (parts.path or "").rstrip("/")


def overlap(a, b):
    """Events both hooks carry, as a sorted list. Pure.

    A wildcard subscribes to everything, so it overlaps whatever the other hook
    lists; two wildcards overlap on everything and are reported as such.
    """
    sa, sb = set(a or []), set(b or [])
    if WILDCARD in sa and WILDCARD in sb:
        return [WILDCARD]
    if WILDCARD in sa:
        return sorted(sb)
    if WILDCARD in sb:
        return sorted(sa)
    return sorted(sa & sb)


def group(hooks):
    """Group hooks by endpoint and classify each group. Pure.

    hooks: dicts with source, id, url, events and active.
    Returns rows sorted by endpoint, each with a state:

      unique    one hook, nothing to do
      duplicate two or more active hooks with events in common
      latent    a second hook exists but is inactive; re-enabling doubles delivery
      disjoint  several hooks on one URL that deliberately split the events
    """
    by_endpoint = {}
    for h in hooks or []:
        by_endpoint.setdefault(endpoint(h.get("url")), []).append(h)

    rows = []
    for target, members in sorted(by_endpoint.items()):
        active = [m for m in members if m.get("active", True)]
        shared = []
        for i, first in enumerate(active):
            for second in active[i + 1:]:
                shared.extend(e for e in overlap(first.get("events"),
                                                 second.get("events"))
                              if e not in shared)
        if len(members) == 1:
            state = "unique"
        elif len(active) < 2:
            state = "latent"
        elif shared:
            state = "duplicate"
        else:
            state = "disjoint"
        rows.append({"endpoint": target, "state": state, "hooks": members,
                     "shared": sorted(shared)})
    return rows


def guid_pairs(logs):
    """Do the copies share a delivery guid? Pure.

    logs: {source: [delivery, ...]} for one endpoint. Returns counts of guids
    seen under more than one source, and of (event, minute) slots covered by two
    sources under different guids. The first says guid-based idempotency already
    handles this; the second says it does not and the key has to come from the
    payload.
    """
    sources_by_guid = {}
    slots = {}
    for source, deliveries in (logs or {}).items():
        for d in deliveries or []:
            guid = d.get("guid")
            if guid:
                sources_by_guid.setdefault(guid, set()).add(source)
            when = str(d.get("delivered_at") or "")[:16]
            if when:
                slots.setdefault((str(d.get("event") or ""), when), {})[source] = guid
    shared = sum(1 for s in sources_by_guid.values() if len(s) > 1)
    twinned = sum(1 for seen in slots.values()
                  if len(seen) > 1 and len(set(seen.values())) > 1)
    return {"shared_guids": shared, "same_event_different_guid": twinned}


def next_link(response):
    """The rel=next URL from the Link header, or None."""
    for part in (response.headers.get("Link") or "").split(","):
        chunk = part.strip()
        if chunk.startswith("<") and chunk.endswith('rel="next"'):
            return chunk[1:chunk.index(">")]
    return None


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from GitHub: GITHUB_TOKEN is missing, expired or "
                         "malformed")
    if r.status_code in (403, 404):
        raise SystemExit("%d from %s: repository hooks need admin:repo_hook and "
                         "organization hooks need admin:org_hook; GitHub answers "
                         "404 rather than 403 when the token cannot see the "
                         "resource" % (r.status_code, url))
    r.raise_for_status()
    return r


def page(session, url, limit=500, **params):
    out = []
    while url and len(out) < limit:
        r = get(session, url, **params)
        out.extend(r.json())
        url, params = next_link(r), {}
    return out[:limit]


def collect(session, scopes):
    """Flatten every hook from every scope into the shape group() expects."""
    hooks = []
    for label, base in scopes:
        for h in page(session, base, per_page=100):
            hooks.append({
                "source": label,
                "base": base,
                "id": h.get("id"),
                "url": (h.get("config") or {}).get("url"),
                "events": h.get("events") or [],
                "active": bool(h.get("active", True)),
            })
    return hooks


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--org", action="append", default=[],
                    help="organization login; repeat for several orgs")
    ap.add_argument("--repo", action="append", default=[],
                    help="owner/name; repeat for several repositories")
    ap.add_argument("--max-deliveries", type=int, default=100,
                    help="deliveries to read per hook when checking whether the "
                         "copies share a guid (0 to skip)")
    args = ap.parse_args()

    if not (args.org or args.repo):
        log.error("pass at least one --org login or --repo owner/name")
        return 2

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_TOKEN (a read-only token is enough)")
        return 2

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": UA,
    })

    scopes = []
    for org in args.org:
        scopes.append(("org " + org, "%s/orgs/%s/hooks" % (API, org)))
    for repo in args.repo:
        owner, _, name = repo.partition("/")
        if not (owner and name):
            log.error("--repo takes owner/name, for example acme/api")
            return 2
        scopes.append(("repo " + repo, "%s/repos/%s/%s/hooks" % (API, owner, name)))

    hooks = collect(session, scopes)
    rows = group(hooks)

    duplicated = latent = 0
    for row in rows:
        members = ", ".join("%s#%s%s" % (m["source"], m["id"],
                                         "" if m["active"] else " (inactive)")
                            for m in row["hooks"])
        line = "%-10s %s  %s" % (row["state"], row["endpoint"] or "?", members)
        if row["state"] in ("unique", "disjoint"):
            log.info(line)
            if row["state"] == "disjoint":
                log.info("  no shared events: a deliberate split, not a duplicate")
            continue

        log.warning(line)
        if row["state"] == "latent":
            latent += 1
            log.warning("  only one hook is active. Re-enabling the other "
                        "doubles delivery of: %s",
                        ", ".join(overlap(row["hooks"][0]["events"],
                                          row["hooks"][-1]["events"])) or "nothing")
            continue

        duplicated += 1
        log.warning("  delivered twice: %s", ", ".join(row["shared"]))
        if args.max_deliveries:
            logs = {}
            for m in row["hooks"]:
                logs[m["source"]] = page(
                    session, "%s/%s/deliveries" % (m["base"], m["id"]),
                    limit=args.max_deliveries, per_page=100)
            pairs = guid_pairs(logs)
            log.warning("  %d guid(s) seen under more than one hook, %d event(s) "
                        "arriving twice under different guids",
                        pairs["shared_guids"], pairs["same_event_different_guid"])
            if pairs["same_event_different_guid"]:
                log.warning("  deduplicating on X-GitHub-Delivery will not catch "
                            "these; key the side effect on something in the "
                            "payload instead")
        log.warning("  repair: keep one source of truth and delete the other "
                    "hook by hand (DELETE is not something this script will do)")

    log.info("%d hook(s) across %d endpoint(s), %d duplicated, %d latent",
             len(hooks), len(rows), duplicated, latent)
    return 1 if duplicated else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-duplicate-hooks.mjs",
"js": '''/**
 * Find one webhook URL registered by more than one GitHub hook.
 *
 * Read only. Org hooks and repo hooks are independent objects, so the same URL
 * can be registered in both scopes and every overlapping event is delivered
 * twice. The script prints which hook to remove; it never removes one.
 */
const API = 'https://api.github.com';
const UA = 'github-duplicate-hooks/1.0';

// A hook subscribed to "*" receives every event type, so it intersects with
// anything the other hook on the same URL carries.
const WILDCARD = '*';

/**
 * Reduce a webhook URL to lowercase host plus path. Pure. Two hooks created
 * years apart differ cosmetically far more often than meaningfully, and a raw
 * string comparison across them reports a clean account.
 */
export function endpoint(url) {
  if (!url) return '';
  let parsed;
  try {
    parsed = new URL(String(url).trim());
  } catch {
    return String(url).trim().toLowerCase().replace(/\\/+$/, '');
  }
  const host = parsed.hostname.toLowerCase();
  const port = (parsed.port && parsed.port !== '80' && parsed.port !== '443')
    ? `:${parsed.port}` : '';
  return host + port + parsed.pathname.replace(/\\/+$/, '');
}

/** Events both hooks carry, sorted. Pure. A wildcard overlaps everything. */
export function overlap(a, b) {
  const sa = new Set(a ?? []);
  const sb = new Set(b ?? []);
  if (sa.has(WILDCARD) && sb.has(WILDCARD)) return [WILDCARD];
  if (sa.has(WILDCARD)) return [...sb].sort();
  if (sb.has(WILDCARD)) return [...sa].sort();
  return [...sa].filter((e) => sb.has(e)).sort();
}

/**
 * Group hooks by endpoint and classify each group. Pure. States: unique,
 * duplicate, latent, disjoint.
 */
export function group(hooks) {
  const byEndpoint = new Map();
  for (const h of hooks ?? []) {
    const key = endpoint(h.url);
    if (!byEndpoint.has(key)) byEndpoint.set(key, []);
    byEndpoint.get(key).push(h);
  }

  const rows = [];
  for (const target of [...byEndpoint.keys()].sort()) {
    const members = byEndpoint.get(target);
    const active = members.filter((m) => m.active !== false);
    const shared = [];
    for (let i = 0; i < active.length; i += 1) {
      for (let j = i + 1; j < active.length; j += 1) {
        for (const e of overlap(active[i].events, active[j].events)) {
          if (!shared.includes(e)) shared.push(e);
        }
      }
    }
    let state;
    if (members.length === 1) state = 'unique';
    else if (active.length < 2) state = 'latent';
    else if (shared.length) state = 'duplicate';
    else state = 'disjoint';
    rows.push({ endpoint: target, state, hooks: members, shared: shared.sort() });
  }
  return rows;
}

/**
 * Do the copies share a delivery guid? Pure. logs is {source: [delivery, ...]}
 * for one endpoint.
 */
export function guidPairs(logs) {
  const sourcesByGuid = new Map();
  const slots = new Map();
  for (const [source, deliveries] of Object.entries(logs ?? {})) {
    for (const d of deliveries ?? []) {
      if (d.guid) {
        if (!sourcesByGuid.has(d.guid)) sourcesByGuid.set(d.guid, new Set());
        sourcesByGuid.get(d.guid).add(source);
      }
      const when = String(d.delivered_at ?? '').slice(0, 16);
      if (when) {
        const key = `${d.event ?? ''}@${when}`;
        if (!slots.has(key)) slots.set(key, new Map());
        slots.get(key).set(source, d.guid);
      }
    }
  }
  let shared = 0;
  for (const sources of sourcesByGuid.values()) if (sources.size > 1) shared += 1;
  let twinned = 0;
  for (const seen of slots.values()) {
    if (seen.size > 1 && new Set(seen.values()).size > 1) twinned += 1;
  }
  return { shared_guids: shared, same_event_different_guid: twinned };
}

function nextLink(res) {
  for (const part of (res.headers.get('link') ?? '').split(',')) {
    const chunk = part.trim();
    if (chunk.startsWith('<') && chunk.endsWith('rel="next"')) {
      return chunk.slice(1, chunk.indexOf('>'));
    }
  }
  return null;
}

async function get(token, url) {
  const res = await fetch(url, {
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      'User-Agent': UA,
    },
  });
  if (res.status === 401) {
    throw new Error('401 from GitHub: GITHUB_TOKEN is missing, expired or malformed');
  }
  if (res.status === 403 || res.status === 404) {
    throw new Error(`${res.status} from ${url}: repository hooks need ` +
      'admin:repo_hook and organization hooks need admin:org_hook; GitHub ' +
      'answers 404 rather than 403 when the token cannot see the resource');
  }
  if (!res.ok) throw new Error(`${res.status} from ${url}`);
  return res;
}

async function page(token, url, limit = 500) {
  const out = [];
  let next = url;
  while (next && out.length < limit) {
    const res = await get(token, next);
    out.push(...(await res.json()));
    next = nextLink(res);
  }
  return out.slice(0, limit);
}

async function main() {
  const token = process.env.GITHUB_TOKEN;
  if (!token) {
    console.error('set GITHUB_TOKEN (a read-only token is enough)');
    process.exitCode = 2;
    return;
  }

  const scopes = [];
  for (const arg of process.argv.slice(2)) {
    if (arg.includes('/')) scopes.push([`repo ${arg}`, `${API}/repos/${arg}/hooks`]);
    else scopes.push([`org ${arg}`, `${API}/orgs/${arg}/hooks`]);
  }
  if (scopes.length === 0) {
    console.error('usage: node github-duplicate-hooks.mjs acme acme/api acme/web');
    process.exitCode = 2;
    return;
  }

  const hooks = [];
  for (const [source, base] of scopes) {
    for (const h of await page(token, `${base}?per_page=100`)) {
      hooks.push({ source, base, id: h.id, url: h.config?.url,
        events: h.events ?? [], active: h.active !== false });
    }
  }

  const rows = group(hooks);
  let duplicated = 0;
  let latent = 0;
  for (const row of rows) {
    const members = row.hooks
      .map((m) => `${m.source}#${m.id}${m.active ? '' : ' (inactive)'}`).join(', ');
    const line = `${row.state.padEnd(10)} ${row.endpoint || '?'}  ${members}`;
    if (row.state === 'unique' || row.state === 'disjoint') {
      console.log(line);
      if (row.state === 'disjoint') {
        console.log('  no shared events: a deliberate split, not a duplicate');
      }
      continue;
    }

    console.warn(line);
    if (row.state === 'latent') {
      latent += 1;
      const would = overlap(row.hooks[0].events, row.hooks[row.hooks.length - 1].events);
      console.warn('  only one hook is active. Re-enabling the other doubles ' +
        `delivery of: ${would.join(', ') || 'nothing'}`);
      continue;
    }

    duplicated += 1;
    console.warn(`  delivered twice: ${row.shared.join(', ')}`);
    const logs = {};
    for (const m of row.hooks) {
      logs[m.source] = await page(token,
        `${m.base}/${m.id}/deliveries?per_page=100`, 100);
    }
    const pairs = guidPairs(logs);
    console.warn(`  ${pairs.shared_guids} guid(s) seen under more than one hook, ` +
      `${pairs.same_event_different_guid} event(s) arriving twice under different guids`);
    if (pairs.same_event_different_guid) {
      console.warn('  deduplicating on X-GitHub-Delivery will not catch these; ' +
        'key the side effect on something in the payload instead');
    }
    console.warn('  repair: keep one source of truth and delete the other hook ' +
      'by hand (removal is not something this script will do)');
  }

  console.log(`${hooks.length} hook(s) across ${rows.length} endpoint(s), ` +
    `${duplicated} duplicated, ${latent} latent`);
  process.exitCode = duplicated ? 1 : 0;
}

// Only run when invoked directly, so importing this module from the test file
// does not run main(), fail on the missing token, and fail the test file with it.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The two failure modes of a duplicate report are pinned here: missing a real duplicate because one URL had a trailing slash, and flagging a pair of hooks that deliberately split the events between them. The inactive case has its own state because a disabled second hook is not delivering anything today and is one toggle away from delivering everything twice.",
"test_py_file": "test_github_duplicate_hooks.py",
"test_py": '''from github_duplicate_hooks import endpoint, group, guid_pairs, overlap


def hook(source, url, events, active=True, hid=1):
    return {"source": source, "id": hid, "url": url, "events": events,
            "active": active}


def test_endpoint_ignores_the_ways_two_urls_differ_cosmetically():
    same = "hooks.example.com/gh"
    assert endpoint("https://hooks.example.com/gh") == same
    assert endpoint("https://hooks.example.com/gh/") == same
    assert endpoint("HTTPS://Hooks.Example.com/gh") == same
    assert endpoint("http://hooks.example.com/gh?token=x") == same
    assert endpoint("https://hooks.example.com:8443/gh") == "hooks.example.com:8443/gh"
    assert endpoint(None) == ""


def test_overlap_treats_a_wildcard_as_covering_everything():
    assert overlap(["push"], ["push", "issues"]) == ["push"]
    assert overlap(["*"], ["push", "issues"]) == ["issues", "push"]
    assert overlap(["*"], ["*"]) == ["*"]
    assert overlap(["push"], ["issues"]) == []


def test_one_url_in_two_scopes_with_shared_events_is_the_finding():
    rows = group([hook("org acme", "https://hooks.example.com/gh", ["push"], hid=1),
                  hook("repo acme/api", "https://hooks.example.com/gh/",
                       ["push", "issues"], hid=2)])
    assert len(rows) == 1
    assert rows[0]["state"] == "duplicate"
    assert rows[0]["shared"] == ["push"]


def test_a_deliberate_split_is_not_reported_as_a_duplicate():
    rows = group([hook("org acme", "https://hooks.example.com/gh", ["push"], hid=1),
                  hook("repo acme/api", "https://hooks.example.com/gh",
                       ["issues"], hid=2)])
    assert rows[0]["state"] == "disjoint"
    assert rows[0]["shared"] == []


def test_an_inactive_second_hook_is_latent_rather_than_duplicate():
    rows = group([hook("org acme", "https://hooks.example.com/gh", ["push"], hid=1),
                  hook("repo acme/api", "https://hooks.example.com/gh", ["push"],
                       active=False, hid=2)])
    assert rows[0]["state"] == "latent"


def test_a_single_hook_is_unique():
    rows = group([hook("repo acme/api", "https://hooks.example.com/gh", ["push"])])
    assert rows[0]["state"] == "unique"


def test_guid_pairs_says_whether_delivery_id_dedup_would_help():
    shared = guid_pairs({
        "org acme": [{"guid": "g1", "event": "push",
                      "delivered_at": "2026-08-01T10:00:03Z"}],
        "repo acme/api": [{"guid": "g1", "event": "push",
                           "delivered_at": "2026-08-01T10:00:03Z"}],
    })
    assert shared["shared_guids"] == 1
    assert shared["same_event_different_guid"] == 0

    split = guid_pairs({
        "org acme": [{"guid": "g1", "event": "push",
                      "delivered_at": "2026-08-01T10:00:03Z"}],
        "repo acme/api": [{"guid": "g2", "event": "push",
                           "delivered_at": "2026-08-01T10:00:04Z"}],
    })
    assert split["shared_guids"] == 0
    assert split["same_event_different_guid"] == 1
''',
"test_js_file": "github-duplicate-hooks.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  endpoint, group, guidPairs, overlap,
} from './github-duplicate-hooks.mjs';

const hook = (source, url, events, active = true, id = 1) =>
  ({ source, id, url, events, active });

test('endpoint ignores the ways two urls differ cosmetically', () => {
  const same = 'hooks.example.com/gh';
  assert.equal(endpoint('https://hooks.example.com/gh'), same);
  assert.equal(endpoint('https://hooks.example.com/gh/'), same);
  assert.equal(endpoint('HTTPS://Hooks.Example.com/gh'), same);
  assert.equal(endpoint('http://hooks.example.com/gh?token=x'), same);
  assert.equal(endpoint('https://hooks.example.com:8443/gh'),
    'hooks.example.com:8443/gh');
  assert.equal(endpoint(null), '');
});

test('overlap treats a wildcard as covering everything', () => {
  assert.deepEqual(overlap(['push'], ['push', 'issues']), ['push']);
  assert.deepEqual(overlap(['*'], ['push', 'issues']), ['issues', 'push']);
  assert.deepEqual(overlap(['*'], ['*']), ['*']);
  assert.deepEqual(overlap(['push'], ['issues']), []);
});

test('one url in two scopes with shared events is the finding', () => {
  const rows = group([
    hook('org acme', 'https://hooks.example.com/gh', ['push'], true, 1),
    hook('repo acme/api', 'https://hooks.example.com/gh/', ['push', 'issues'], true, 2),
  ]);
  assert.equal(rows.length, 1);
  assert.equal(rows[0].state, 'duplicate');
  assert.deepEqual(rows[0].shared, ['push']);
});

test('a deliberate split is not reported as a duplicate', () => {
  const rows = group([
    hook('org acme', 'https://hooks.example.com/gh', ['push'], true, 1),
    hook('repo acme/api', 'https://hooks.example.com/gh', ['issues'], true, 2),
  ]);
  assert.equal(rows[0].state, 'disjoint');
  assert.deepEqual(rows[0].shared, []);
});

test('an inactive second hook is latent rather than duplicate', () => {
  const rows = group([
    hook('org acme', 'https://hooks.example.com/gh', ['push'], true, 1),
    hook('repo acme/api', 'https://hooks.example.com/gh', ['push'], false, 2),
  ]);
  assert.equal(rows[0].state, 'latent');
});

test('a single hook is unique', () => {
  const rows = group([hook('repo acme/api', 'https://hooks.example.com/gh', ['push'])]);
  assert.equal(rows[0].state, 'unique');
});

test('guidPairs says whether delivery id dedup would help', () => {
  const shared = guidPairs({
    'org acme': [{ guid: 'g1', event: 'push', delivered_at: '2026-08-01T10:00:03Z' }],
    'repo acme/api': [{ guid: 'g1', event: 'push', delivered_at: '2026-08-01T10:00:03Z' }],
  });
  assert.equal(shared.shared_guids, 1);
  assert.equal(shared.same_event_different_guid, 0);

  const split = guidPairs({
    'org acme': [{ guid: 'g1', event: 'push', delivered_at: '2026-08-01T10:00:03Z' }],
    'repo acme/api': [{ guid: 'g2', event: 'push', delivered_at: '2026-08-01T10:00:04Z' }],
  });
  assert.equal(split.shared_guids, 0);
  assert.equal(split.same_event_different_guid, 1);
});
''',
"faq": [
 ("Why does GitHub deliver the same event twice?",
  "It does not. It delivers once per hook that subscribes to the event, and two hooks subscribed. Organization webhooks and repository webhooks are independent objects with independent event lists, so a URL registered in both scopes receives one copy from each and neither hook looks wrong on its own."),
 ("Will deduplicating on X-GitHub-Delivery fix it?",
  "It fixes retries and redeliveries, which reuse a delivery's guid. Whether the org copy and the repo copy of one event carry the same guid is worth measuring rather than assuming, which is why the script reads both delivery logs and reports the answer for your account. If the same event arrives under two different guids, the idempotency key has to come from the payload instead."),
 ("Two hooks point at one URL but nothing is duplicated. Is that a problem?",
  "Not if their event arrays are disjoint, which is a legitimate way to split traffic between scopes. The script reports that as disjoint and moves on. The finding is the intersection of the event sets, not the shared URL."),
 ("Does the script delete the redundant hook?",
  "No. This section is read only, so it names the hook, its scope and its id, and leaves the removal to you. Deleting the wrong one of two identical-looking hooks stops delivery entirely, which is a worse outage than the duplicates."),
 ("What about a GitHub App as a third source?",
  "An App's webhook is configured on the App itself, not per installation, and is read through GET /app/hook/config with the App's JWT rather than a repository token. A repository token cannot see it, so if an App is installed on these repositories, count its webhook as another potential copy of the same events."),
],
"related": [
 ("/github/webhook-event-not-subscribed/", "The hook is not subscribed to your event"),
 ("/github/webhook-no-secret/", "A webhook with no secret sends no signature"),
 ("/github/webhook-deliveries-failing/", "Deliveries failing where nobody reads the log"),
],
"citations": [CITE_ORG_HOOKS, CITE_REPO_HOOKS, CITE_BEST, CITE_APP_HOOKS],
},

]
