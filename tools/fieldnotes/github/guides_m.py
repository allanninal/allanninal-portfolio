#!/usr/bin/env python3
"""/github/ field notes, batch M — the writing.

Four notes that all read the same small JSON object, the webhook's config, and
reach four different conclusions from four different fields. Keeping them apart
was the whole job, because a batch like this becomes one note four times if
nobody insists otherwise.

The first is a switch. A hook's `active` flag can be false, and an inactive
hook produces no deliveries at all, so there is no failure anywhere to find.
The interesting part is not the boolean, which takes one line to read: it is
that a hook arrives at false by three different routes, and the repair differs
by route. Somebody created it that way, somebody toggled it off during an
incident, or GitHub switched it off after a long run of failures. The last of
those means the hook is a symptom rather than the cause.

The second is not a configuration problem at all. GitHub sends two signature
headers, the legacy HMAC-SHA1 `X-Hub-Signature` and `X-Hub-Signature-256`, and
which one your receiver verifies is a decision in your own source code that no
API read can see. So this note does the only honest thing: it confirms from the
API that signatures are being sent, then reads your receiver's source from disk
and reports which header name appears in it. The trap is that the modern header
name contains the legacy one as a prefix, so a naive substring search reports
every correct receiver as legacy.

The third is certificate verification. `config.insecure_ssl` set to "1" tells
GitHub not to check your endpoint's TLS certificate, which usually happens once
during setup to get past a self-signed cert and is then never undone.
Deliveries succeed the whole time, which is exactly why nobody looks. The
consequence is impersonation rather than eavesdropping: anything that can win
the race for your hostname receives your payloads, correctly signed.

The fourth is the transport itself. An `http://` webhook URL is plaintext, and
the hinge of that note is that `insecure_ssl` is meaningless on a hook with no
TLS at all, so a hook can pass the field a security review checks while sending
everything in the clear.

Read only throughout. The two notes that end in a config change print the
change; they never make it.
"""

CITE_REPO_HOOKS = ("Repository webhooks — GitHub REST API",
                   "https://docs.github.com/en/rest/repos/webhooks")
CITE_ORG_HOOKS = ("Organization webhooks — GitHub REST API",
                  "https://docs.github.com/en/rest/orgs/webhooks")
CITE_VALIDATE = ("Validating webhook deliveries — GitHub Docs",
                 "https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries")
CITE_FAILED = ("Handling failed webhook deliveries — GitHub Docs",
               "https://docs.github.com/en/webhooks/using-webhooks/handling-failed-webhook-deliveries")
CITE_TROUBLESHOOT = ("Troubleshooting webhooks — GitHub Docs",
                     "https://docs.github.com/en/webhooks/testing-and-troubleshooting-webhooks/troubleshooting-webhooks")
CITE_ABOUT = ("About webhooks — GitHub Docs",
              "https://docs.github.com/en/webhooks/about-webhooks")
CITE_CREATING = ("Creating webhooks — GitHub Docs",
                 "https://docs.github.com/en/webhooks/using-webhooks/creating-webhooks")
CITE_BEST_PRACTICES = ("Best practices for using webhooks — GitHub Docs",
                       "https://docs.github.com/en/webhooks/using-webhooks/best-practices-for-using-webhooks")
CITE_APP_HOOKS = ("Webhooks — GitHub Apps REST API",
                  "https://docs.github.com/en/rest/apps/webhooks")

GUIDES = [

{
"slug": "webhook-inactive",
"title": "The webhook exists but somebody switched it off",
"description": "An inactive hook produces no deliveries at all, so there is no failure to find. Read the active flag, then work out which of three ways it got there.",
"h1": "the webhook exists but somebody switched it off",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github webhook active false",
             "github webhook not firing no errors",
             "github disabled my webhook",
             "webhook delivery log empty github",
             "re-enable github webhook"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The hook is right there in the repository's settings, pointed at the right URL, subscribed to the right events, with a secret set and a green tick beside it from the last time anyone looked. The delivery log is not full of failures. It is empty, and it has been empty for five weeks. Nothing is broken because nothing is running: <code>active</code> is <code>false</code>.",
"short_answer": """<p>Read <code>GET /repos/{owner}/{repo}/hooks</code> and look at the <code>active</code> boolean on each hook. <code>false</code> is the finding, and it is the whole finding &mdash; an inactive hook is not attempted, so it generates no delivery record, no failure and no error anywhere.</p>
<p>The part worth a script is what comes next, because a hook reaches <code>active: false</code> by three routes with three different repairs. It was created that way and has never delivered anything; somebody toggled it off during an incident and never toggled it back; or GitHub switched it off after a long run of failed deliveries. <code>last_response.code</code> separates the third from the other two, and <code>created_at</code> against <code>updated_at</code> separates the first from the second. Re-enabling a hook that GitHub disabled, without fixing the receiver first, just gets it disabled again.</p>""",
"problem": """<p>This one hides because every instinct points somewhere else. An event that never arrives sends you to your receiver: the routing, the ingress, the signature check, the queue. All of them are fine. Then it sends you to GitHub's delivery log, which is where an experienced person goes second, and the log is empty &mdash; so the conclusion is that GitHub did not send the event, and the search moves to whether the event fires at all. Nobody looks at a boolean that has been <code>false</code> since March, because the settings page shows the hook and a hook you can see feels like a hook that is running.</p>
<p>The toggling itself is usually legitimate and usually forgotten. Somebody switches a hook off at two in the morning because the receiver is melting under a migration and the retries are making it worse. That is exactly the right call. The incident ends, the receiver is fixed, the deploy goes out, and the one action that has no ticket attached is the one that gets left: turning it back on. The integration stays dark, and because it produces silence rather than errors, the silence is the last thing anyone questions.</p>
<p>The third route is worse to get wrong. GitHub can disable a hook itself after a sustained run of failures, which means an inactive hook is sometimes the aftermath of a completely different problem rather than a problem of its own. Flipping it back on without fixing whatever was returning 500 puts you back where you started in a day, having spent the retention window you needed to replay the lost events.</p>""",
"why": """<p><strong>An inactive hook is not attempted, so nothing records it.</strong> This is the difference between this note and a hook whose deliveries are failing. A failing hook writes a record for every attempt, with a status code and a duration you can read. An inactive one writes nothing, so the two symptoms that look identical from your receiver &mdash; no request arrived &mdash; are opposites in the delivery log: a wall of 5xx or a blank page.</p>
<p><strong>The flag is per hook, not per event and not per repository.</strong> Turning one hook off does not affect an organization hook pointed at the same URL, which is how an integration can go half dark: the org-level copy keeps delivering for some repositories while the repo-level hook for the one that matters is off. Read every scope that can reach the repository, not just the one you were told about.</p>
<p><strong><code>updated_at</code> dates the change, but not precisely.</strong> It moves whenever any part of the hook config is edited, so it is evidence rather than proof: a hook whose <code>updated_at</code> equals its <code>created_at</code> has never been edited at all, which makes <code>active: false</code> an original choice. A hook edited later might have been toggled then, or might have had its URL changed then and been toggled at some other moment the API does not record.</p>
<p><strong><code>last_response</code> is the tell for an automatic disable.</strong> It carries the code, status and message from the most recent attempt, and it survives the hook being switched off. An inactive hook whose last recorded response was a 500 or a timeout was almost certainly disabled rather than toggled, and that changes the order of the repair. Fix the receiver, then re-enable.</p>
<p><strong>Re-enabling is a write, so this script does not do it.</strong> It prints the request. That is not squeamishness: turning a hook back on is exactly the action you want a human to take deliberately, after deciding the endpoint can survive the replay that follows. The script's job is to tell you which of the three situations you are in, so the decision is an informed one.</p>""",
"steps": [
 {"h": "Read the flag before you read anything else",
  "body": """<p><code>GET /repos/{owner}/{repo}/hooks</code> returns every hook the token can see, each with <code>id</code>, <code>active</code>, <code>events</code>, <code>config</code>, <code>created_at</code>, <code>updated_at</code> and <code>last_response</code>. One request answers the question. Do this before instrumenting the receiver, because an inactive hook makes every other measurement meaningless.</p>"""},
 {"h": "Do not trust a truthy test on the boolean",
  "body": """<p>The field is a real JSON boolean, but it does not always arrive as one. Config files, form posts, Terraform state and hand-rolled clients all have their own idea of how to spell false, and <code>"false"</code> is a non-empty string that a truthy test reads as on. Parse it to three states &mdash; on, off, and unreadable &mdash; and report the third rather than guessing at it.</p>"""},
 {"h": "Ask how it got there",
  "body": """<p>Compare <code>created_at</code> with <code>updated_at</code>, and read <code>last_response.code</code>. A failing last response on an inactive hook means GitHub probably disabled it, an <code>updated_at</code> later than <code>created_at</code> means it was edited at some point after creation, and the two timestamps being equal means it has been off since the day it was made and has never delivered anything.</p>"""},
 {"h": "Corroborate with an empty delivery log",
  "body": """<p><code>GET /repos/{owner}/{repo}/hooks/{hook_id}/deliveries</code> on an inactive hook returns whatever was delivered before it was switched off, and nothing since. That gives you the date the silence started from the other direction, and it tells you how much of the gap still falls inside the retention window and can therefore be replayed.</p>"""},
 {"h": "Fix the receiver first if the log says so",
  "body": """<p>Re-enable last, not first. If the last response was a failure, the hook was switched off for a reason that has not gone away, and switching it on again buys you a day. When you do re-enable, expect a burst: everything queued behind a redelivery run arrives at once, which is a second reason to be sure the endpoint is healthy before the flag flips.</p>"""},
],
"verify": """<p>Once the flag is back on, the same read reports <code>active</code> and the delivery log starts filling again within a minute of the next matching event.</p>
<pre><code class="language-bash">GITHUB_TOKEN=$GH_READONLY python3 github_hook_active_audit.py --repo acme-corp/api
# 3 hook(s) on acme-corp/api, 1 inactive
# inactive-after-failures: hook 512334455 is switched off, and its last
# recorded response was 502. GitHub disables a hook after a sustained run of
# failures, so this is an aftermath rather than a cause.
# repair: fix the receiver for the 502 first, then re-enable with
# gh api --method PATCH /repos/acme-corp/api/hooks/512334455 -F active=true

# after the receiver is fixed and an owner re-enables it
# active: hook 512334455 is switched on</code></pre>""",
"code_intro": "One GET carries the finding and one optional GET dates it. Everything that decides anything is pure: a three-state read of a boolean that arrives as a boolean, a number or a string depending on what wrote it; a comparison of two timestamps with enough tolerance that a hook written and read in the same second is not called edited; the last recorded response code, which can be absent, null or a string; and a verdict that separates the three ways a hook ends up switched off, because they do not share a repair. Re-enabling is a write, so the script prints the request rather than making it.",
"py_file": "github_hook_active_audit.py",
"py": '''"""Say whether a GitHub webhook is switched off, and which of three ways it happened.

Read only. Every call is a GET. Re-enabling a hook is a write and this script
does not do it: it prints the request for you to run once you have decided the
endpoint can survive being switched back on.

An inactive hook is not attempted, so it produces no delivery record, no
failure and no error. That is what makes it hard to find - the delivery log is
empty rather than full of 5xx, so the evidence looks like the absence of
events rather than the absence of a hook.

Three routes lead to active: false, and they do not share a repair:

    created inactive     never delivered anything, updated_at == created_at
    toggled off later    somebody switched it off, updated_at > created_at
    disabled by GitHub   a sustained run of failures, last_response is 4xx/5xx

Environment:

    GITHUB_TOKEN    a read-only token that can see the repository's hooks
"""
import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_hook_active_audit")

API = "https://api.github.com"
UA = "github-hook-active-audit/1.0"

# Spellings of the boolean seen in the wild. GitHub returns a real JSON boolean,
# but the value reaches this script through whatever wrote the hook: a form
# post, a config file, a Terraform state, a client that stringifies everything.
TRUTHY = ("true", "1", "yes", "on")
FALSY = ("false", "0", "no", "off")

# States that mean a hook is delivering nothing at all.
OFF_STATES = ("inactive-after-failures", "inactive-toggled",
              "inactive-since-creation", "inactive-undated")


def active_state(hook):
    """Three-state read of the active flag: on, off or unknown. Pure.

    Deliberately not a boolean. A truthy test on this field reads the string
    "false" as on, and an absent field as off, and both of those are wrong in
    the direction that matters: one hides a dead hook, the other invents one.
    """
    if not isinstance(hook, dict) or "active" not in hook:
        return "unknown"
    raw = hook["active"]
    if isinstance(raw, bool):
        return "on" if raw else "off"
    if isinstance(raw, (int, float)):
        return "on" if raw else "off"
    text = str(raw).strip().lower()
    if text in TRUTHY:
        return "on"
    if text in FALSY:
        return "off"
    return "unknown"


def last_code(hook):
    """The status code of the most recent delivery attempt, or None. Pure.

    last_response survives the hook being switched off, which is the only
    reason this script can tell a disable from a toggle.
    """
    if not isinstance(hook, dict):
        return None
    resp = hook.get("last_response")
    if not isinstance(resp, dict):
        return None
    code = resp.get("code")
    if code is None or code == "":
        return None
    try:
        return int(code)
    except (TypeError, ValueError):
        return None


def failed_last(hook):
    """Whether the most recent recorded response was a failure. Pure."""
    code = last_code(hook)
    return code is not None and code >= 400


def parsed_time(text):
    """An ISO 8601 timestamp as an aware datetime, or None. Pure."""
    raw = str(text or "").strip()
    if not raw or raw.lower() in ("null", "none"):
        return None
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        when = datetime.fromisoformat(raw)
    except ValueError:
        return None
    return when if when.tzinfo else when.replace(tzinfo=timezone.utc)


def days_since(text, now):
    """Whole days between a timestamp and now, or None. Pure."""
    when = parsed_time(text)
    if when is None or now is None:
        return None
    return (now - when).days


def edited_after_creation(hook, tolerance_seconds=90):
    """True, False or None - was this hook changed after it was made? Pure.

    None when either timestamp is missing or unparseable, because "we cannot
    tell" is a real answer here and reporting it as "never edited" would put
    the reader in the wrong one of three repairs. The tolerance exists because
    a hook created and configured in one API call comes back with two
    timestamps a second or two apart.
    """
    if not isinstance(hook, dict):
        return None
    created = parsed_time(hook.get("created_at"))
    updated = parsed_time(hook.get("updated_at"))
    if created is None or updated is None:
        return None
    return (updated - created).total_seconds() > tolerance_seconds


def newest_delivery(deliveries):
    """The most recent delivered_at across delivery records, or None. Pure."""
    best, best_at = None, None
    for row in deliveries or []:
        if not isinstance(row, dict):
            continue
        when = parsed_time(row.get("delivered_at"))
        if when is None:
            continue
        if best_at is None or when > best_at:
            best, best_at = str(row.get("delivered_at")), when
    return best


def silent_days(deliveries, now):
    """Days since the last delivery, or None when there has never been one. Pure."""
    return days_since(newest_delivery(deliveries), now)


def classify(hook, deliveries=None, now=None):
    """Sort one hook into a state and a sentence. Pure.

    deliveries is optional and only ever corroborates. The finding lives in the
    hook record; the log dates it and says how much is still replayable.
    """
    ident = "hook %s" % (hook.get("id", "?") if isinstance(hook, dict) else "?")
    state = active_state(hook)
    if state == "unknown":
        return ("unknown",
                "%s does not report a readable active flag. Read it in the "
                "repository's settings before trusting anything else here."
                % ident)
    if state == "off":
        if failed_last(hook):
            return ("inactive-after-failures",
                    "%s is switched off, and its last recorded response was "
                    "%d. GitHub disables a hook after a sustained run of "
                    "failures, so this is an aftermath rather than a cause."
                    % (ident, last_code(hook)))
        edited = edited_after_creation(hook)
        if edited is True:
            age = days_since(hook.get("updated_at"), now)
            return ("inactive-toggled",
                    "%s is switched off and was last edited %s%s. It delivered "
                    "before that and has delivered nothing since."
                    % (ident, hook.get("updated_at", "at an unrecorded time"),
                       ", %d day(s) ago" % age if age is not None else ""))
        if edited is False:
            return ("inactive-since-creation",
                    "%s is switched off and has never been edited, so it was "
                    "created inactive and has never delivered anything."
                    % ident)
        return ("inactive-undated",
                "%s is switched off. Its timestamps are missing, so which of "
                "the three ways it got there cannot be told from here." % ident)
    quiet = silent_days(deliveries, now)
    if deliveries is not None and newest_delivery(deliveries) is None:
        return ("active-but-silent",
                "%s is switched on and the delivery log is empty. The hook is "
                "not the problem: either nothing it subscribes to has "
                "happened, or it subscribes to the wrong events." % ident)
    if quiet is not None and quiet >= 30:
        return ("active-but-quiet",
                "%s is switched on and its last delivery was %d day(s) ago."
                % (ident, quiet))
    return ("active", "%s is switched on." % ident)


def repair(state, hook, repo="OWNER/REPO"):
    """The request or the decision a reader has to make. Pure.

    Every branch that ends in a config change prints the change. Turning a hook
    back on is a deliberate act with a burst of traffic behind it, and this
    script is read only in any case.
    """
    hook_id = hook.get("id", "HOOK_ID") if isinstance(hook, dict) else "HOOK_ID"
    enable = ("gh api --method PATCH /repos/%s/hooks/%s -F active=true"
              % (repo, hook_id))
    if state == "inactive-after-failures":
        return ("fix the receiver for the recorded response code first, then "
                "re-enable with %s. Re-enabling before the receiver is fixed "
                "gets the hook disabled again and spends the retention window "
                "you need for the replay." % enable)
    if state == "inactive-toggled":
        return ("confirm the endpoint is healthy and can take a burst, then "
                "re-enable with %s." % enable)
    if state == "inactive-since-creation":
        return ("this hook has never delivered anything. Either it was made "
                "inactive by mistake, in which case %s, or it was superseded "
                "by another hook and should be deleted." % enable)
    if state == "inactive-undated":
        return ("read the delivery log for the date the silence started, then "
                "decide. When you re-enable: %s." % enable)
    if state in ("active-but-silent", "active-but-quiet"):
        return ("nothing here. The hook is on, so look at its events array "
                "and at whether anything it subscribes to has happened.")
    if state == "unknown":
        return "read the active flag in the repository's settings by hand."
    return "nothing. This hook is on."


def summarize(hooks):
    """Counts across every hook read. Pure."""
    rows = [h for h in (hooks or []) if isinstance(h, dict)]
    off = [h for h in rows if active_state(h) == "off"]
    return {"total": len(rows), "inactive": len(off),
            "active": len([h for h in rows if active_state(h) == "on"]),
            "inactive_ids": [h.get("id") for h in off]}


def get(session, path):
    """One GET. Returns (status, json-or-None)."""
    url = API + path if path.startswith("/") else path
    r = session.get(url, timeout=30)
    try:
        body = r.json()
    except ValueError:
        body = None
    return r.status_code, body


def list_hooks(session, scope):
    """Hooks for a repo (owner/name) or an org (@org). Read only."""
    path = ("/orgs/%s/hooks?per_page=100" % scope[1:] if scope.startswith("@")
            else "/repos/%s/hooks?per_page=100" % scope)
    status, body = get(session, path)
    if status != 200 or not isinstance(body, list):
        log.error("GET %s returned %d; a token that cannot read hooks reports "
                  "no hooks rather than an error you would notice", path, status)
        return []
    return body


def list_deliveries(session, scope, hook_id, limit=30):
    """Recent delivery records for one hook. Read only, corroboration only."""
    base = ("/orgs/%s/hooks/%s/deliveries" % (scope[1:], hook_id)
            if scope.startswith("@")
            else "/repos/%s/hooks/%s/deliveries" % (scope, hook_id))
    status, body = get(session, "%s?per_page=%d" % (base, limit))
    if status != 200 or not isinstance(body, list):
        return None
    return body


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", action="append", default=[],
                    help="owner/name; repeatable")
    ap.add_argument("--org", action="append", default=[],
                    help="organization login; repeatable")
    ap.add_argument("--no-deliveries", action="store_true",
                    help="skip the corroborating read of the delivery log")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_TOKEN to a read-only token that can see the "
                  "repository's hooks")
        return 2
    scopes = list(args.repo) + ["@" + o for o in args.org]
    if not scopes:
        log.error("pass at least one --repo owner/name or --org login")
        return 2

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": UA,
    })

    now = datetime.now(timezone.utc)
    findings = []
    for scope in scopes:
        label = scope[1:] if scope.startswith("@") else scope
        hooks = list_hooks(session, scope)
        stats = summarize(hooks)
        log.info("%d hook(s) on %s, %d inactive", stats["total"], label,
                 stats["inactive"])
        for hook in hooks:
            deliveries = None
            if not args.no_deliveries:
                deliveries = list_deliveries(session, scope, hook.get("id"))
            state, detail = classify(hook, deliveries, now)
            findings.append({"scope": label, "hook_id": hook.get("id"),
                             "state": state, "detail": detail,
                             "last_delivery": newest_delivery(deliveries)})
            if state != "active":
                log.info("%s: %s", state, detail)
                log.info("repair: %s", repair(state, hook, label))
        if stats["inactive"] == 0:
            log.info("active: no hook on %s is switched off", label)

    print(json.dumps({"scopes": scopes, "findings": findings},
                     indent=2, default=str))
    return 1 if any(f["state"] in OFF_STATES for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-hook-active-audit.mjs",
"js": '''/**
 * Say whether a GitHub webhook is switched off, and which of three ways it happened.
 *
 * Read only. Every call is a GET. Re-enabling a hook is a write and is not done
 * here: the script prints the request for you to run once you have decided the
 * endpoint can survive being switched back on.
 *
 * Environment:
 *   GITHUB_TOKEN   a read-only token that can see the repository's hooks
 *
 * Usage:
 *   node github-hook-active-audit.mjs acme-corp/api @acme-corp
 */
const API = 'https://api.github.com';
const UA = 'github-hook-active-audit/1.0';

const TRUTHY = ['true', '1', 'yes', 'on'];
const FALSY = ['false', '0', 'no', 'off'];

/** States that mean a hook is delivering nothing at all. */
export const OFF_STATES = [
  'inactive-after-failures', 'inactive-toggled',
  'inactive-since-creation', 'inactive-undated',
];

/**
 * Three-state read of the active flag: on, off or unknown. Pure.
 * A truthy test reads the string 'false' as on and an absent field as off.
 */
export function activeState(hook) {
  if (!hook || typeof hook !== 'object' || !('active' in hook)) return 'unknown';
  const raw = hook.active;
  if (typeof raw === 'boolean') return raw ? 'on' : 'off';
  if (typeof raw === 'number') return raw ? 'on' : 'off';
  const text = String(raw ?? '').trim().toLowerCase();
  if (TRUTHY.includes(text)) return 'on';
  if (FALSY.includes(text)) return 'off';
  return 'unknown';
}

/** The status code of the most recent delivery attempt, or null. Pure. */
export function lastCode(hook) {
  if (!hook || typeof hook !== 'object') return null;
  const resp = hook.last_response;
  if (!resp || typeof resp !== 'object') return null;
  const code = resp.code;
  if (code === null || code === undefined || code === '') return null;
  const n = Number(code);
  return Number.isFinite(n) ? Math.trunc(n) : null;
}

/** Whether the most recent recorded response was a failure. Pure. */
export function failedLast(hook) {
  const code = lastCode(hook);
  return code !== null && code >= 400;
}

/** An ISO 8601 timestamp as epoch milliseconds, or null. Pure. */
export function parsedTime(text) {
  const raw = String(text ?? '').trim();
  if (!raw || ['null', 'none'].includes(raw.toLowerCase())) return null;
  const ms = Date.parse(raw);
  return Number.isNaN(ms) ? null : ms;
}

/** Whole days between a timestamp and now, or null. Pure. */
export function daysSince(text, nowMs) {
  const when = parsedTime(text);
  if (when === null || nowMs === null || nowMs === undefined) return null;
  return Math.floor((nowMs - when) / 86400000);
}

/** true, false or null - was this hook changed after it was made? Pure. */
export function editedAfterCreation(hook, toleranceSeconds = 90) {
  if (!hook || typeof hook !== 'object') return null;
  const created = parsedTime(hook.created_at);
  const updated = parsedTime(hook.updated_at);
  if (created === null || updated === null) return null;
  return (updated - created) / 1000 > toleranceSeconds;
}

/** The most recent delivered_at across delivery records, or null. Pure. */
export function newestDelivery(deliveries) {
  let best = null;
  let bestAt = null;
  for (const row of deliveries ?? []) {
    if (!row || typeof row !== 'object') continue;
    const when = parsedTime(row.delivered_at);
    if (when === null) continue;
    if (bestAt === null || when > bestAt) {
      best = String(row.delivered_at);
      bestAt = when;
    }
  }
  return best;
}

/** Days since the last delivery, or null when there has never been one. Pure. */
export function silentDays(deliveries, nowMs) {
  return daysSince(newestDelivery(deliveries), nowMs);
}

/** Sort one hook into a state and a sentence. Pure. */
export function classify(hook, deliveries = null, nowMs = null) {
  const ident = `hook ${(hook && typeof hook === 'object' ? hook.id : null) ?? '?'}`;
  const state = activeState(hook);
  if (state === 'unknown') {
    return ['unknown',
      `${ident} does not report a readable active flag. Read it in the ` +
      'repository\\'s settings before trusting anything else here.'];
  }
  if (state === 'off') {
    if (failedLast(hook)) {
      return ['inactive-after-failures',
        `${ident} is switched off, and its last recorded response was ` +
        `${lastCode(hook)}. GitHub disables a hook after a sustained run of ` +
        'failures, so this is an aftermath rather than a cause.'];
    }
    const edited = editedAfterCreation(hook);
    if (edited === true) {
      const age = daysSince(hook.updated_at, nowMs);
      return ['inactive-toggled',
        `${ident} is switched off and was last edited ` +
        `${hook.updated_at ?? 'at an unrecorded time'}` +
        `${age !== null ? `, ${age} day(s) ago` : ''}. It delivered before ` +
        'that and has delivered nothing since.'];
    }
    if (edited === false) {
      return ['inactive-since-creation',
        `${ident} is switched off and has never been edited, so it was ` +
        'created inactive and has never delivered anything.'];
    }
    return ['inactive-undated',
      `${ident} is switched off. Its timestamps are missing, so which of the ` +
      'three ways it got there cannot be told from here.'];
  }
  const quiet = silentDays(deliveries, nowMs);
  if (deliveries !== null && newestDelivery(deliveries) === null) {
    return ['active-but-silent',
      `${ident} is switched on and the delivery log is empty. The hook is not ` +
      'the problem: either nothing it subscribes to has happened, or it ' +
      'subscribes to the wrong events.'];
  }
  if (quiet !== null && quiet >= 30) {
    return ['active-but-quiet',
      `${ident} is switched on and its last delivery was ${quiet} day(s) ago.`];
  }
  return ['active', `${ident} is switched on.`];
}

/** The request or the decision a reader has to make. Pure. */
export function repair(state, hook, repo = 'OWNER/REPO') {
  const hookId = (hook && typeof hook === 'object' ? hook.id : null) ?? 'HOOK_ID';
  const enable = `gh api --method PATCH /repos/${repo}/hooks/${hookId} -F active=true`;
  if (state === 'inactive-after-failures') {
    return 'fix the receiver for the recorded response code first, then ' +
      `re-enable with ${enable}. Re-enabling before the receiver is fixed gets ` +
      'the hook disabled again and spends the retention window you need for ' +
      'the replay.';
  }
  if (state === 'inactive-toggled') {
    return 'confirm the endpoint is healthy and can take a burst, then ' +
      `re-enable with ${enable}.`;
  }
  if (state === 'inactive-since-creation') {
    return 'this hook has never delivered anything. Either it was made ' +
      `inactive by mistake, in which case ${enable}, or it was superseded by ` +
      'another hook and should be deleted.';
  }
  if (state === 'inactive-undated') {
    return 'read the delivery log for the date the silence started, then ' +
      `decide. When you re-enable: ${enable}.`;
  }
  if (state === 'active-but-silent' || state === 'active-but-quiet') {
    return 'nothing here. The hook is on, so look at its events array and at ' +
      'whether anything it subscribes to has happened.';
  }
  if (state === 'unknown') {
    return 'read the active flag in the repository\\'s settings by hand.';
  }
  return 'nothing. This hook is on.';
}

/** Counts across every hook read. Pure. */
export function summarize(hooks) {
  const rows = (hooks ?? []).filter((h) => h && typeof h === 'object');
  const off = rows.filter((h) => activeState(h) === 'off');
  return {
    total: rows.length,
    inactive: off.length,
    active: rows.filter((h) => activeState(h) === 'on').length,
    inactive_ids: off.map((h) => h.id),
  };
}

async function get(token, path) {
  const res = await fetch(path.startsWith('/') ? API + path : path, {
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      'User-Agent': UA,
    },
  });
  let body = null;
  try { body = await res.json(); } catch { body = null; }
  return { status: res.status, body };
}

async function listHooks(token, scope) {
  const path = scope.startsWith('@')
    ? `/orgs/${scope.slice(1)}/hooks?per_page=100`
    : `/repos/${scope}/hooks?per_page=100`;
  const { status, body } = await get(token, path);
  if (status !== 200 || !Array.isArray(body)) {
    console.error(`GET ${path} returned ${status}; a token that cannot read ` +
      'hooks reports no hooks rather than an error you would notice');
    return [];
  }
  return body;
}

async function listDeliveries(token, scope, hookId, limit = 30) {
  const base = scope.startsWith('@')
    ? `/orgs/${scope.slice(1)}/hooks/${hookId}/deliveries`
    : `/repos/${scope}/hooks/${hookId}/deliveries`;
  const { status, body } = await get(token, `${base}?per_page=${limit}`);
  if (status !== 200 || !Array.isArray(body)) return null;
  return body;
}

async function main() {
  const token = process.env.GITHUB_TOKEN;
  if (!token) {
    console.error('set GITHUB_TOKEN to a read-only token that can see the ' +
      "repository's hooks");
    process.exitCode = 2;
    return;
  }
  const scopes = process.argv.slice(2);
  if (scopes.length === 0) {
    console.error('pass at least one owner/name, or @org for an organization');
    process.exitCode = 2;
    return;
  }

  const now = Date.now();
  const findings = [];
  for (const scope of scopes) {
    const label = scope.startsWith('@') ? scope.slice(1) : scope;
    const hooks = await listHooks(token, scope);
    const stats = summarize(hooks);
    console.log(`${stats.total} hook(s) on ${label}, ${stats.inactive} inactive`);
    for (const hook of hooks) {
      const deliveries = await listDeliveries(token, scope, hook.id);
      const [state, detail] = classify(hook, deliveries, now);
      findings.push({
        scope: label,
        hook_id: hook.id,
        state,
        detail,
        last_delivery: newestDelivery(deliveries),
      });
      if (state !== 'active') {
        console.log(`${state}: ${detail}`);
        console.log(`repair: ${repair(state, hook, label)}`);
      }
    }
    if (stats.inactive === 0) {
      console.log(`active: no hook on ${label} is switched off`);
    }
  }

  console.log(JSON.stringify({ scopes, findings }, null, 2));
  process.exitCode = findings.some((f) => OFF_STATES.includes(f.state)) ? 1 : 0;
}

// Only run when invoked directly, so importing this module from the test file
// does not execute main(), fail on the missing token and set an exit code that
// fails the suite even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The cases worth pinning are the ones where a shortcut would lie. A truthy test on <code>active</code> calls the string <code>\"false\"</code> an on hook and an absent field an off one, so both are tested explicitly and the absent case is <em>unknown</em> rather than either. After that: the three routes to off producing three different states and three different repairs, an inactive hook with a failing last response never being reported as a simple toggle, and an on hook with an empty log being sent to a different note instead of being called a finding here.",
"test_py_file": "test_github_hook_active_audit.py",
"test_py": '''from datetime import datetime, timezone

from github_hook_active_audit import (
    active_state, classify, days_since, edited_after_creation, failed_last,
    last_code, newest_delivery, repair, silent_days, summarize,
)

NOW = datetime(2026, 8, 30, 12, 0, 0, tzinfo=timezone.utc)

FRESH = {"id": 1, "active": True, "created_at": "2026-01-04T10:00:00Z",
         "updated_at": "2026-01-04T10:00:01Z"}
TOGGLED = {"id": 2, "active": False, "created_at": "2026-01-04T10:00:00Z",
           "updated_at": "2026-07-26T02:11:00Z"}
BORN_OFF = {"id": 3, "active": False, "created_at": "2026-01-04T10:00:00Z",
            "updated_at": "2026-01-04T10:00:02Z"}
DISABLED = {"id": 4, "active": False, "created_at": "2026-01-04T10:00:00Z",
            "updated_at": "2026-07-26T02:11:00Z",
            "last_response": {"code": 502, "status": "bad gateway"}}


def test_a_truthy_test_would_get_the_string_false_wrong():
    assert active_state({"active": "false"}) == "off"
    assert active_state({"active": "0"}) == "off"
    assert active_state({"active": 0}) == "off"
    assert active_state({"active": "true"}) == "on"
    assert active_state({"active": 1}) == "on"


def test_an_absent_flag_is_unknown_and_not_off():
    assert active_state({"id": 1}) == "unknown"
    assert active_state({"active": None}) == "unknown"
    assert active_state({"active": "maybe"}) == "unknown"
    assert active_state(None) == "unknown"


def test_the_last_response_code_survives_every_shape_it_arrives_in():
    assert last_code(DISABLED) == 502
    assert last_code({"last_response": {"code": "500"}}) == 500
    assert last_code({"last_response": {"code": None}}) is None
    assert last_code({"last_response": {}}) is None
    assert last_code({"id": 1}) is None
    assert failed_last(DISABLED)
    assert not failed_last({"last_response": {"code": 200}})


def test_a_hook_configured_in_one_call_is_not_called_edited():
    assert edited_after_creation(BORN_OFF) is False
    assert edited_after_creation(TOGGLED) is True
    assert edited_after_creation({"created_at": "2026-01-04T10:00:00Z"}) is None


def test_the_three_routes_to_off_are_three_different_states():
    assert classify(DISABLED, None, NOW)[0] == "inactive-after-failures"
    assert classify(TOGGLED, None, NOW)[0] == "inactive-toggled"
    assert classify(BORN_OFF, None, NOW)[0] == "inactive-since-creation"


def test_a_disabled_hook_is_never_reported_as_a_plain_toggle():
    state, detail = classify(DISABLED, None, NOW)
    assert state == "inactive-after-failures"
    assert "502" in detail
    assert "aftermath" in detail


def test_an_off_hook_with_no_timestamps_says_so_rather_than_guessing():
    state, detail = classify({"id": 9, "active": False}, None, NOW)
    assert state == "inactive-undated"
    assert "cannot be told from here" in detail


def test_an_on_hook_with_an_empty_log_is_sent_to_a_different_question():
    state, detail = classify(FRESH, [], NOW)
    assert state == "active-but-silent"
    assert "not the problem" in detail
    assert "events array" in repair(state, FRESH)


def test_an_on_hook_with_a_recent_delivery_is_simply_active():
    log = [{"delivered_at": "2026-08-30T09:00:00Z", "status": "OK"}]
    assert classify(FRESH, log, NOW)[0] == "active"


def test_the_delivery_log_is_read_for_its_newest_row_not_its_first():
    log = [{"delivered_at": "2026-08-01T09:00:00Z"},
           {"delivered_at": "2026-08-29T09:00:00Z"},
           {"delivered_at": "not a date"},
           "junk"]
    assert newest_delivery(log) == "2026-08-29T09:00:00Z"
    assert silent_days(log, NOW) == 1
    assert newest_delivery([]) is None
    assert silent_days([], NOW) is None


def test_the_repair_for_a_disabled_hook_puts_the_receiver_first():
    text = repair("inactive-after-failures", DISABLED, "acme-corp/api")
    assert text.index("fix the receiver") < text.index("re-enable")
    assert "/repos/acme-corp/api/hooks/4" in text


def test_the_summary_counts_the_hooks_that_are_off():
    stats = summarize([FRESH, TOGGLED, DISABLED, {"id": 5}])
    assert stats["total"] == 4
    assert stats["inactive"] == 2
    assert stats["active"] == 1
    assert stats["inactive_ids"] == [2, 4]


def test_days_since_refuses_to_invent_an_age():
    assert days_since("2026-08-27T12:00:00Z", NOW) == 3
    assert days_since("", NOW) is None
    assert days_since("null", NOW) is None
''',
"test_js_file": "github-hook-active-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  activeState, classify, daysSince, editedAfterCreation, failedLast,
  lastCode, newestDelivery, repair, silentDays, summarize,
} from './github-hook-active-audit.mjs';

const NOW = Date.parse('2026-08-30T12:00:00Z');

const FRESH = {
  id: 1, active: true,
  created_at: '2026-01-04T10:00:00Z', updated_at: '2026-01-04T10:00:01Z',
};
const TOGGLED = {
  id: 2, active: false,
  created_at: '2026-01-04T10:00:00Z', updated_at: '2026-07-26T02:11:00Z',
};
const BORN_OFF = {
  id: 3, active: false,
  created_at: '2026-01-04T10:00:00Z', updated_at: '2026-01-04T10:00:02Z',
};
const DISABLED = {
  id: 4, active: false,
  created_at: '2026-01-04T10:00:00Z', updated_at: '2026-07-26T02:11:00Z',
  last_response: { code: 502, status: 'bad gateway' },
};

test('a truthy test would get the string false wrong', () => {
  assert.equal(activeState({ active: 'false' }), 'off');
  assert.equal(activeState({ active: '0' }), 'off');
  assert.equal(activeState({ active: 0 }), 'off');
  assert.equal(activeState({ active: 'true' }), 'on');
  assert.equal(activeState({ active: 1 }), 'on');
});

test('an absent flag is unknown and not off', () => {
  assert.equal(activeState({ id: 1 }), 'unknown');
  assert.equal(activeState({ active: null }), 'unknown');
  assert.equal(activeState({ active: 'maybe' }), 'unknown');
  assert.equal(activeState(null), 'unknown');
});

test('the last response code survives every shape it arrives in', () => {
  assert.equal(lastCode(DISABLED), 502);
  assert.equal(lastCode({ last_response: { code: '500' } }), 500);
  assert.equal(lastCode({ last_response: { code: null } }), null);
  assert.equal(lastCode({ last_response: {} }), null);
  assert.equal(lastCode({ id: 1 }), null);
  assert.ok(failedLast(DISABLED));
  assert.ok(!failedLast({ last_response: { code: 200 } }));
});

test('a hook configured in one call is not called edited', () => {
  assert.equal(editedAfterCreation(BORN_OFF), false);
  assert.equal(editedAfterCreation(TOGGLED), true);
  assert.equal(editedAfterCreation({ created_at: '2026-01-04T10:00:00Z' }), null);
});

test('the three routes to off are three different states', () => {
  assert.equal(classify(DISABLED, null, NOW)[0], 'inactive-after-failures');
  assert.equal(classify(TOGGLED, null, NOW)[0], 'inactive-toggled');
  assert.equal(classify(BORN_OFF, null, NOW)[0], 'inactive-since-creation');
});

test('a disabled hook is never reported as a plain toggle', () => {
  const [state, detail] = classify(DISABLED, null, NOW);
  assert.equal(state, 'inactive-after-failures');
  assert.match(detail, /502/);
  assert.match(detail, /aftermath/);
});

test('an off hook with no timestamps says so rather than guessing', () => {
  const [state, detail] = classify({ id: 9, active: false }, null, NOW);
  assert.equal(state, 'inactive-undated');
  assert.match(detail, /cannot be told from here/);
});

test('an on hook with an empty log is sent to a different question', () => {
  const [state, detail] = classify(FRESH, [], NOW);
  assert.equal(state, 'active-but-silent');
  assert.match(detail, /not the problem/);
  assert.match(repair(state, FRESH), /events array/);
});

test('an on hook with a recent delivery is simply active', () => {
  const log = [{ delivered_at: '2026-08-30T09:00:00Z', status: 'OK' }];
  assert.equal(classify(FRESH, log, NOW)[0], 'active');
});

test('the delivery log is read for its newest row not its first', () => {
  const log = [
    { delivered_at: '2026-08-01T09:00:00Z' },
    { delivered_at: '2026-08-29T09:00:00Z' },
    { delivered_at: 'not a date' },
    'junk',
  ];
  assert.equal(newestDelivery(log), '2026-08-29T09:00:00Z');
  assert.equal(silentDays(log, NOW), 1);
  assert.equal(newestDelivery([]), null);
  assert.equal(silentDays([], NOW), null);
});

test('the repair for a disabled hook puts the receiver first', () => {
  const text = repair('inactive-after-failures', DISABLED, 'acme-corp/api');
  assert.ok(text.indexOf('fix the receiver') < text.indexOf('re-enable'));
  assert.match(text, /\\/repos\\/acme-corp\\/api\\/hooks\\/4/);
});

test('the summary counts the hooks that are off', () => {
  const stats = summarize([FRESH, TOGGLED, DISABLED, { id: 5 }]);
  assert.equal(stats.total, 4);
  assert.equal(stats.inactive, 2);
  assert.equal(stats.active, 1);
  assert.deepEqual(stats.inactive_ids, [2, 4]);
});

test('daysSince refuses to invent an age', () => {
  assert.equal(daysSince('2026-08-27T12:00:00Z', NOW), 3);
  assert.equal(daysSince('', NOW), null);
  assert.equal(daysSince('null', NOW), null);
});
''',
"faq": [
 ("How is this different from deliveries that are failing?",
  "They are opposites in the one place that matters. A failing hook is attempted every time, so GitHub writes a delivery record for each attempt with a status code, a duration and a response body you can read. An inactive hook is not attempted at all, so there is nothing to read: the log stops dead at the moment it was switched off. From the receiver's side both look like a request that never arrived, which is why the delivery log is the first thing to check and the shape of what you find there tells you which note you are in."),
 ("Does GitHub really disable webhooks by itself?",
  "Yes, after a sustained run of failed deliveries. That is why the script checks last_response before it checks the timestamps: an inactive hook whose most recent recorded response was a 502 or a timeout was almost certainly switched off for you rather than by anyone, and it is a symptom of a receiver problem rather than a problem of its own. Turning it back on without fixing the receiver gets it disabled again, and burns the retention window you would have used to replay the events you missed."),
 ("Why not just re-enable it in the script?",
  "Two reasons, and only one of them is that this section never writes. The other is that re-enabling releases a burst: anything you replay from the retention window arrives at once, on top of live traffic, against an endpoint that has not handled a request in weeks. That is a decision to take deliberately, with somebody watching. The script prints the exact request so the decision is one keystroke away, and so it is still a decision."),
 ("Can I tell who switched it off, and when?",
  "Not from the hook record. It carries created_at and updated_at, and updated_at moves for any edit to the hook, so it dates the most recent change of any kind rather than the toggle specifically. There is no actor field. If you need the name, the organization audit log has the event; the API-visible evidence here is limited to the fact that something changed after creation and the date the deliveries stopped, which the script reads from the other end of the delivery log."),
 ("The hook is on and still nothing arrives. What now?",
  "Then this is not your note, and the script says so rather than shrugging. An active hook with an empty delivery log means either that nothing it subscribes to has actually happened, or that it subscribes to events your handler is not waiting for, which is a different read of a different field. Check the events array against the events your code handles before you touch anything else, and confirm the hook you are looking at is the one whose URL your receiver serves."),
],
"related": [
 ("/github/webhook-deliveries-failing/", "Deliveries failing where nobody reads the log"),
 ("/github/webhook-event-not-subscribed/", "The hook is not subscribed to your event"),
 ("/github/webhook-insecure-ssl/", "Certificate verification switched off on the hook"),
],
"citations": [CITE_REPO_HOOKS, CITE_ORG_HOOKS, CITE_TROUBLESHOOT, CITE_FAILED],
},

{
"slug": "webhook-sha1-signature-only",
"title": "The receiver still checks the legacy SHA-1 signature",
"description": "GitHub sends X-Hub-Signature and X-Hub-Signature-256. Which one your code verifies is invisible to the API, so read the headers, then read your source.",
"h1": "the receiver still checks the legacy SHA-1 signature",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["x-hub-signature-256 vs x-hub-signature",
             "github webhook sha1 signature deprecated",
             "verify github webhook signature sha256",
             "github webhook hmac sha1 legacy header",
             "which github signature header to check"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The receiver verifies. It reads a signature header, computes an HMAC over the raw body, compares in constant time and returns <code>401</code> when they differ. It has been doing that since 2017, which is the problem: the header it reads is <code>X-Hub-Signature</code>, the SHA-1 one GitHub keeps sending for the sake of receivers exactly like this one.",
"short_answer": """<p>GitHub sends two signature headers on every delivery from a hook that has a secret: <code>X-Hub-Signature</code>, an HMAC-SHA1 kept for backwards compatibility, and <code>X-Hub-Signature-256</code>, the HMAC-SHA256 one you should be verifying. Both are present, both are computed from the same secret, and a receiver that checks only the first passes every test it has.</p>
<p>This is a receiver-side choice, so no API read can see it. What the API can do is establish that signatures are being sent at all &mdash; <code>config.secret</code> masked as <code>********</code> on <code>GET /repos/{owner}/{repo}/hooks</code>, and both header names listed under <code>request.headers</code> on a delivery &mdash; and then the script reads your receiver's source from disk and reports which header name appears in it. The trap there is that the modern name contains the legacy name as a prefix, so a naive substring search reports every correct receiver as a legacy one.</p>""",
"problem": """<p>Nothing fails, which is the entire difficulty. A SHA-1 signature check rejects forged payloads and accepts genuine ones, so the integration behaves correctly on every input anybody has ever sent it. There is no error log, no failed delivery, no alert. The only way to discover it is to go and look at a line of code that has not been touched in years and has no reason to draw attention to itself, because it is in the part of the receiver that works.</p>
<p>The search is also easy to do badly. Somebody greps the repository for <code>X-Hub-Signature</code>, finds a hit, and concludes the receiver is legacy &mdash; except the hit is inside <code>X-Hub-Signature-256</code>, because one string is a prefix of the other. The same mistake runs the other way in code: a header lookup written as a <code>startswith</code> or a loose match will happily read the modern header into a routine that then verifies it as SHA-1 and fails every time, which at least announces itself. The silent version is the one that greps clean and is wrong.</p>
<p>And the framing gets confused with a different problem. A hook with no secret sends no signature header at all, so a receiver written to verify <em>if the header is present</em> verifies nothing; that is a different note with a different finding. Here the secret exists, the headers arrive, the verification runs, and the digest is a weaker one than the one sitting in the next header along.</p>""",
"why": """<p><strong>Both headers are always sent when a secret is set.</strong> GitHub did not replace the SHA-1 header, it added the SHA-256 one alongside it, precisely so that receivers written before the change kept working. That is a kindness with a cost: nothing about a legacy receiver is broken, so nothing about it gets noticed.</p>
<p><strong>The API's blind spot here is total and worth stating.</strong> GitHub knows what it sent. It has no idea what you checked. Every entry in a delivery record describes the request GitHub made and the response your server gave, and there is no field anywhere that reports which header your code read. Any tool that claims to detect this from the API alone is guessing.</p>
<p><strong>So the evidence has to come from your own source, and that is a proxy too.</strong> A grep for a header name finds the ordinary case, where the name is a literal in the code. It cannot see a header name built at runtime, read from configuration, or hidden behind a framework helper, and it cannot tell a live verification from a commented-out one. The script reports what it found and says plainly what it cannot see, rather than converting a text search into a verdict it has not earned.</p>
<p><strong>Accepting either header is not half a fix.</strong> A receiver that tries SHA-256 and falls back to SHA-1 accepts a SHA-1 signature from anyone who can produce one, which is exactly the population that could produce one before. The weaker check is the one that decides. Support for both is a migration state, not a destination, and the script reports it as a finding rather than as a pass.</p>
<p><strong>Nothing in the repair touches GitHub.</strong> This is the one webhook problem in this batch that is fixed entirely in your code: read <code>X-Hub-Signature-256</code>, compute the HMAC over the exact raw request bytes, compare with a constant-time comparison, reject when the header is missing, and delete the SHA-1 branch. The hook config is already correct, which is why no amount of staring at it helps.</p>""",
"steps": [
 {"h": "Confirm a signature is being sent at all",
  "body": """<p><code>GET /repos/{owner}/{repo}/hooks</code> and read <code>config</code>. A secret that is set comes back masked as <code>********</code>; when there is no secret the key is absent entirely and GitHub sends neither header, which is a different problem with a different note. This step is what makes the rest of the check meaningful.</p>"""},
 {"h": "Read one delivery's request headers",
  "body": """<p><code>GET /repos/{owner}/{repo}/hooks/{hook_id}/deliveries</code> for a recent id, then the single-delivery endpoint for the detail. <code>request.headers</code> lists what GitHub actually sent, including both signature header names. This is evidence, not diagnosis: it proves the modern header was available to your receiver.</p>"""},
 {"h": "Search your receiver, with the prefix trap in mind",
  "body": """<p>Normalise each line, remove every occurrence of the modern name first, and only then look for the legacy one in what is left. Doing it in the other order, or with a plain substring test, reports a correct receiver as a legacy one on every single line where it gets it right.</p>"""},
 {"h": "Report line numbers, never lines",
  "body": """<p>The script prints the file and the line number and which header name was found there. It does not print the line, because source that handles signatures is exactly the source most likely to have a secret sitting on the line above, and a diagnostic tool that pastes your code into a terminal or a CI log is a poor trade for the convenience.</p>"""},
 {"h": "Move the check, then remove the fallback",
  "body": """<p>Switch the comparison to <code>X-Hub-Signature-256</code> and the digest to SHA-256 over the raw bytes. Then delete the SHA-1 path rather than keeping it as a fallback: a receiver that accepts either is exactly as strong as the weaker of the two. Reject a request whose header is missing instead of skipping the check.</p>"""},
],
"verify": """<p>After the change the scan finds the modern name and nothing else, and the receiver returns <code>401</code> for a request with no signature header rather than accepting it.</p>
<pre><code class="language-bash">GITHUB_TOKEN=$GH_READONLY python3 github_hook_signature_headers.py \\
  --repo acme-corp/api --receiver ../receiver/src
# hook 512334455: secret is set, GitHub sent both signature headers
# source scan: 2 reference(s) across 1 file(s)
#   receiver/src/hooks.py:41 legacy X-Hub-Signature
#   receiver/src/hooks.py:44 legacy X-Hub-Signature
# sha1-only: the receiver names only the legacy SHA-1 header. GitHub sent the
# SHA-256 header on the same request and it is being ignored.
# repair: verify X-Hub-Signature-256 over the raw request bytes with a
# constant-time comparison, then delete the SHA-1 branch.

# after the change
# sha256-only: the receiver names only X-Hub-Signature-256</code></pre>""",
"code_intro": "Two GETs establish that signatures are being sent, and then the script does something the other notes in this section do not: it reads files. That is the only honest way to answer this one, because the decision it is about lives in your source and nothing at GitHub records it. The pure core is a header-name scanner built around the fact that the legacy name is a prefix of the modern one, a normaliser for the underscore and case variants that different runtimes hand you, a reporter that emits line numbers and never line contents, and a verdict that treats accepting both headers as a finding rather than as a pass.",
"py_file": "github_hook_signature_headers.py",
"py": '''"""Report which webhook signature header your receiver actually verifies.

Read only in both senses. Every API call is a GET, and the local source scan
opens files for reading and prints line numbers rather than lines.

GitHub sends two signature headers on every delivery from a hook that has a
secret set:

    X-Hub-Signature        HMAC-SHA1, kept for backwards compatibility
    X-Hub-Signature-256    HMAC-SHA256, the one to verify

Which of them your receiver checks is a decision in your own code. No API read
can see it, so this script establishes from the API that both headers were
sent, then searches your receiver's source for the header names and reports
what it found. That is a proxy and it is described as one: a header name built
at runtime, read from configuration or hidden inside a framework helper is
invisible to a text search.

The one subtlety worth the code: "x-hub-signature" is a prefix of
"x-hub-signature-256", so a plain substring search reports every correct
receiver as a legacy one. The modern name is removed from each line before the
legacy name is looked for.

The secret is never printed. config.secret comes back masked and this script
reports its presence only.

Environment:

    GITHUB_TOKEN    a read-only token that can see the repository's hooks
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_hook_signature_headers")

API = "https://api.github.com"
UA = "github-hook-signature-headers/1.0"

MODERN = "x-hub-signature-256"
LEGACY = "x-hub-signature"

# Source files worth opening. Everything else in a repository is noise, and a
# scan that opens every file is a scan that reads secrets out of .env by
# accident.
SUFFIXES = (".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".rb", ".go", ".php",
            ".java", ".kt", ".cs", ".rs", ".ex", ".exs")

# States that mean the reader has something to change.
FINDINGS = ("sha1-only", "both-accepted", "no-verification-found")


def normalized(text):
    """Lower-cased, with underscores folded to hyphens. Pure.

    The same header reaches code as X-Hub-Signature-256, x-hub-signature-256
    and HTTP_X_HUB_SIGNATURE_256 depending on the runtime, and all three should
    count as the same reference.
    """
    return str(text or "").lower().replace("_", "-")


def secret_state(hook):
    """Whether the hook has a secret set: set, absent or unknown. Pure.

    The value is masked by GitHub and is never returned by this function. A set
    secret is a key present in config; an unset one is a key that is not there
    at all, which is a different note.
    """
    if not isinstance(hook, dict):
        return "unknown"
    config = hook.get("config")
    if not isinstance(config, dict):
        return "unknown"
    return "set" if "secret" in config else "absent"


def redacted_config(config):
    """A copy of a hook config safe to print. Pure.

    The secret arrives masked, so printing it would leak nothing today. It is
    replaced anyway, because the guarantee this section makes is about what the
    script can emit rather than about what GitHub happens to send.
    """
    if not isinstance(config, dict):
        return {}
    out = dict(config)
    if "secret" in out:
        out["secret"] = "<set>"
    return out


def header_names(headers):
    """Normalised header names from a delivery record. Pure. Values discarded.

    request.headers is an object, but the same data reaches this function as a
    list of name/value pairs or as raw header lines depending on what stored
    it, so all three shapes are accepted and only the names survive.
    """
    names = []
    if isinstance(headers, dict):
        names = list(headers.keys())
    elif isinstance(headers, list):
        for row in headers:
            if isinstance(row, dict) and row.get("name"):
                names.append(row["name"])
            elif isinstance(row, str) and ":" in row:
                names.append(row.split(":", 1)[0])
            elif isinstance(row, str):
                names.append(row)
    return [normalized(n).strip() for n in names]


def signature_headers(headers):
    """Which signature headers GitHub sent on a delivery. Pure.

    Exact name matching, so the prefix problem does not arise here; it arises
    in the source scan below, where the names appear inside other text.
    """
    names = header_names(headers)
    return {"sha256": MODERN in names, "sha1": LEGACY in names}


def scan_line(line):
    """Which signature header names a single line refers to. Pure.

    The modern name is removed first. Looking for the legacy name in the raw
    line instead finds a hit inside every correct reference, which turns a
    passing receiver into a finding on every line where it is right.
    """
    norm = normalized(line)
    kinds = []
    if MODERN in norm:
        kinds.append("sha256")
        norm = norm.replace(MODERN, " ")
    if LEGACY in norm:
        kinds.append("sha1")
    return kinds


def scan_source(text, path="<source>"):
    """Every signature header reference in a file, as (path, line, kind). Pure.

    Line numbers only. The contents of a line that handles signatures are the
    contents most likely to sit next to a secret, and a diagnostic that pastes
    them into a terminal or a CI log has made the problem worse.
    """
    hits = []
    for number, line in enumerate(str(text or "").splitlines(), start=1):
        for kind in scan_line(line):
            hits.append((path, number, kind))
    return hits


def receiver_state(hits):
    """What the scan says the receiver names. Pure.

    none means the header names do not appear in the source that was scanned,
    which is not the same as "does not verify" and is not reported as if it
    were.
    """
    kinds = {kind for _, _, kind in hits or []}
    if not kinds:
        return "none"
    if kinds == {"sha256"}:
        return "sha256-only"
    if kinds == {"sha1"}:
        return "sha1-only"
    return "both"


def format_hit(hit):
    """One line of the scan report. Pure. Never includes source text."""
    path, number, kind = hit
    name = "X-Hub-Signature-256" if kind == "sha256" else "X-Hub-Signature"
    label = "modern" if kind == "sha256" else "legacy"
    return "%s:%d %s %s" % (path, number, label, name)


def verdict(secret, sig=None, receiver=None):
    """Combine the API evidence and the source scan into a finding. Pure.

    secret is the output of secret_state, sig the output of signature_headers
    or None when no delivery was read, receiver the output of receiver_state or
    None when no source was scanned.
    """
    if secret == "absent":
        return ("no-secret",
                "this hook has no secret, so GitHub sends neither signature "
                "header and there is nothing for the receiver to verify. That "
                "is a different and larger problem than which digest you use.")
    if sig is not None and not sig.get("sha256") and not sig.get("sha1"):
        return ("headers-missing",
                "the delivery that was read carries no signature header at "
                "all. Either it predates the secret being set, or the record "
                "is not a delivery from this hook.")
    if receiver is None:
        return ("not-scanned",
                "GitHub sent the SHA-256 header. Which header the receiver "
                "verifies is not visible from the API, so point the scan at "
                "the receiver's source to get an answer rather than a "
                "recommendation.")
    if receiver == "none":
        return ("no-verification-found",
                "neither signature header name appears in the source that was "
                "scanned. Either the receiver does not verify, or it builds "
                "the header name at runtime, or the verification lives "
                "somewhere the scan was not pointed at.")
    if receiver == "sha1-only":
        return ("sha1-only",
                "the receiver names only the legacy SHA-1 header. GitHub sent "
                "the SHA-256 header on the same request and it is being "
                "ignored.")
    if receiver == "both":
        return ("both-accepted",
                "the receiver names both headers. A receiver that accepts "
                "either is exactly as strong as the weaker one, so this is a "
                "migration state rather than a finished one.")
    return ("sha256-only",
            "the receiver names only X-Hub-Signature-256, which is the header "
            "to verify.")


def repair(state):
    """The change to make, in the reader's own code. Pure."""
    if state == "no-secret":
        return ("set a secret on the hook first. Until there is one, GitHub "
                "sends no signature and no digest choice matters.")
    if state == "headers-missing":
        return ("read a delivery from after the secret was set, then re-run.")
    if state == "not-scanned":
        return ("re-run with --receiver pointed at the source tree that "
                "handles the webhook.")
    if state == "no-verification-found":
        return ("confirm by hand that the receiver verifies at all. If it does "
                "not, verify X-Hub-Signature-256 over the raw request bytes "
                "with a constant-time comparison and reject a request whose "
                "header is missing.")
    if state in ("sha1-only", "both-accepted"):
        return ("verify X-Hub-Signature-256 over the raw request bytes with a "
                "constant-time comparison, then delete the SHA-1 branch rather "
                "than keeping it as a fallback.")
    return "nothing. This receiver verifies the header GitHub wants it to."


def scan_paths(paths, suffixes=SUFFIXES, max_bytes=2_000_000):
    """Walk files and directories, scanning source for header references.

    Read only: files are opened for reading and only line numbers leave this
    function.
    """
    hits = []
    scanned = []
    for root in paths or []:
        for path in _walk(root, suffixes):
            try:
                if os.path.getsize(path) > max_bytes:
                    continue
                with open(path, "r", encoding="utf-8", errors="replace") as fh:
                    text = fh.read()
            except OSError as exc:
                log.warning("could not read %s: %s", path, exc)
                continue
            scanned.append(path)
            hits.extend(scan_source(text, path))
    return hits, scanned


def _walk(root, suffixes):
    """Every candidate source file under a path."""
    if os.path.isfile(root):
        return [root]
    out = []
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in
                   (".git", "node_modules", "venv", ".venv", "__pycache__", "dist", "build")]
        for name in files:
            if name.endswith(suffixes):
                out.append(os.path.join(base, name))
    return out


def get(session, path):
    """One GET. Returns (status, json-or-None)."""
    url = API + path if path.startswith("/") else path
    r = session.get(url, timeout=30)
    try:
        body = r.json()
    except ValueError:
        body = None
    return r.status_code, body


def latest_delivery_headers(session, repo, hook_id):
    """The request headers of the most recent delivery, or None. Read only."""
    status, rows = get(session, "/repos/%s/hooks/%s/deliveries?per_page=10"
                       % (repo, hook_id))
    if status != 200 or not isinstance(rows, list) or not rows:
        return None
    for row in rows:
        if not isinstance(row, dict) or not row.get("id"):
            continue
        status, body = get(session, "/repos/%s/hooks/%s/deliveries/%s"
                           % (repo, hook_id, row["id"]))
        if status == 200 and isinstance(body, dict):
            request = body.get("request")
            if isinstance(request, dict):
                return request.get("headers")
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", required=True, help="owner/name")
    ap.add_argument("--hook-id", help="one hook; omit to check every hook")
    ap.add_argument("--receiver", action="append", default=[],
                    help="file or directory to scan for header names; repeatable")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_TOKEN to a read-only token that can see the "
                  "repository's hooks")
        return 2

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": UA,
    })

    status, hooks = get(session, "/repos/%s/hooks?per_page=100" % args.repo)
    if status != 200 or not isinstance(hooks, list):
        log.error("GET /repos/%s/hooks returned %d", args.repo, status)
        return 2
    if args.hook_id:
        hooks = [h for h in hooks if str(h.get("id")) == str(args.hook_id)]

    hits, scanned = scan_paths(args.receiver)
    state_of_receiver = receiver_state(hits) if args.receiver else None
    if args.receiver:
        log.info("source scan: %d reference(s) across %d file(s)",
                 len(hits), len(set(p for p, _, _ in hits)))
        for hit in hits:
            log.info("  %s", format_hit(hit))

    findings = []
    for hook in hooks:
        secret = secret_state(hook)
        headers = None
        if secret == "set":
            headers = latest_delivery_headers(session, args.repo, hook.get("id"))
        sig = signature_headers(headers) if headers is not None else None
        state, detail = verdict(secret, sig, state_of_receiver)
        log.info("hook %s: secret is %s, %s", hook.get("id"), secret,
                 "GitHub sent both signature headers"
                 if sig and sig["sha1"] and sig["sha256"]
                 else "no delivery headers were read")
        log.info("%s: %s", state, detail)
        log.info("repair: %s", repair(state))
        findings.append({"hook_id": hook.get("id"), "secret": secret,
                         "signature_headers": sig, "state": state,
                         "detail": detail,
                         "config": redacted_config(hook.get("config"))})

    print(json.dumps({"repo": args.repo, "files_scanned": len(scanned),
                      "references": [format_hit(h) for h in hits],
                      "findings": findings}, indent=2, default=str))
    return 1 if any(f["state"] in FINDINGS for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-hook-signature-headers.mjs",
"js": '''/**
 * Report which webhook signature header your receiver actually verifies.
 *
 * Read only in both senses: every API call is a GET, and the local source scan
 * opens files for reading and prints line numbers rather than lines.
 *
 * GitHub sends X-Hub-Signature (HMAC-SHA1, legacy) and X-Hub-Signature-256
 * (HMAC-SHA256) on every delivery from a hook that has a secret. Which one the
 * receiver checks lives in your source and no API read can see it, so the API
 * half of this script only establishes that both were sent.
 *
 * The secret is never printed; its presence is reported and nothing else.
 *
 * Environment:
 *   GITHUB_TOKEN   a read-only token that can see the repository's hooks
 *
 * Usage:
 *   node github-hook-signature-headers.mjs acme-corp/api ../receiver/src
 */
import { readFile, readdir, stat } from 'node:fs/promises';
import path from 'node:path';

const API = 'https://api.github.com';
const UA = 'github-hook-signature-headers/1.0';

export const MODERN = 'x-hub-signature-256';
export const LEGACY = 'x-hub-signature';

const SUFFIXES = ['.py', '.js', '.mjs', '.cjs', '.ts', '.tsx', '.rb', '.go',
  '.php', '.java', '.kt', '.cs', '.rs', '.ex', '.exs'];
const SKIP_DIRS = ['.git', 'node_modules', 'venv', '.venv', '__pycache__',
  'dist', 'build'];

/** States that mean the reader has something to change. */
export const FINDINGS = ['sha1-only', 'both-accepted', 'no-verification-found'];

/** Lower-cased, with underscores folded to hyphens. Pure. */
export function normalized(text) {
  return String(text ?? '').toLowerCase().replaceAll('_', '-');
}

/** Whether the hook has a secret set: set, absent or unknown. Pure. */
export function secretState(hook) {
  if (!hook || typeof hook !== 'object') return 'unknown';
  const config = hook.config;
  if (!config || typeof config !== 'object') return 'unknown';
  return 'secret' in config ? 'set' : 'absent';
}

/** A copy of a hook config safe to print. Pure. */
export function redactedConfig(config) {
  if (!config || typeof config !== 'object') return {};
  const out = { ...config };
  if ('secret' in out) out.secret = '<set>';
  return out;
}

/** Normalised header names from a delivery record. Pure. Values discarded. */
export function headerNames(headers) {
  let names = [];
  if (Array.isArray(headers)) {
    for (const row of headers) {
      if (row && typeof row === 'object' && row.name) names.push(row.name);
      else if (typeof row === 'string') names.push(row.includes(':') ? row.split(':')[0] : row);
    }
  } else if (headers && typeof headers === 'object') {
    names = Object.keys(headers);
  }
  return names.map((n) => normalized(n).trim());
}

/** Which signature headers GitHub sent on a delivery. Pure. */
export function signatureHeaders(headers) {
  const names = headerNames(headers);
  return { sha256: names.includes(MODERN), sha1: names.includes(LEGACY) };
}

/**
 * Which signature header names a single line refers to. Pure.
 * The modern name is removed first, because the legacy name is a prefix of it.
 */
export function scanLine(line) {
  let norm = normalized(line);
  const kinds = [];
  if (norm.includes(MODERN)) {
    kinds.push('sha256');
    norm = norm.replaceAll(MODERN, ' ');
  }
  if (norm.includes(LEGACY)) kinds.push('sha1');
  return kinds;
}

/** Every signature header reference in a file, as [path, line, kind]. Pure. */
export function scanSource(text, filePath = '<source>') {
  const hits = [];
  const lines = String(text ?? '').split('\\n');
  for (let i = 0; i < lines.length; i += 1) {
    for (const kind of scanLine(lines[i])) hits.push([filePath, i + 1, kind]);
  }
  return hits;
}

/** What the scan says the receiver names. Pure. */
export function receiverState(hits) {
  const kinds = new Set((hits ?? []).map(([, , kind]) => kind));
  if (kinds.size === 0) return 'none';
  if (kinds.size === 1 && kinds.has('sha256')) return 'sha256-only';
  if (kinds.size === 1 && kinds.has('sha1')) return 'sha1-only';
  return 'both';
}

/** One line of the scan report. Pure. Never includes source text. */
export function formatHit(hit) {
  const [filePath, number, kind] = hit;
  const name = kind === 'sha256' ? 'X-Hub-Signature-256' : 'X-Hub-Signature';
  const label = kind === 'sha256' ? 'modern' : 'legacy';
  return `${filePath}:${number} ${label} ${name}`;
}

/** Combine the API evidence and the source scan into a finding. Pure. */
export function verdict(secret, sig = null, receiver = null) {
  if (secret === 'absent') {
    return ['no-secret',
      'this hook has no secret, so GitHub sends neither signature header and ' +
      'there is nothing for the receiver to verify. That is a different and ' +
      'larger problem than which digest you use.'];
  }
  if (sig !== null && !sig.sha256 && !sig.sha1) {
    return ['headers-missing',
      'the delivery that was read carries no signature header at all. Either ' +
      'it predates the secret being set, or the record is not a delivery from ' +
      'this hook.'];
  }
  if (receiver === null) {
    return ['not-scanned',
      'GitHub sent the SHA-256 header. Which header the receiver verifies is ' +
      'not visible from the API, so point the scan at the receiver\\'s source ' +
      'to get an answer rather than a recommendation.'];
  }
  if (receiver === 'none') {
    return ['no-verification-found',
      'neither signature header name appears in the source that was scanned. ' +
      'Either the receiver does not verify, or it builds the header name at ' +
      'runtime, or the verification lives somewhere the scan was not pointed at.'];
  }
  if (receiver === 'sha1-only') {
    return ['sha1-only',
      'the receiver names only the legacy SHA-1 header. GitHub sent the ' +
      'SHA-256 header on the same request and it is being ignored.'];
  }
  if (receiver === 'both') {
    return ['both-accepted',
      'the receiver names both headers. A receiver that accepts either is ' +
      'exactly as strong as the weaker one, so this is a migration state ' +
      'rather than a finished one.'];
  }
  return ['sha256-only',
    'the receiver names only X-Hub-Signature-256, which is the header to verify.'];
}

/** The change to make, in the reader's own code. Pure. */
export function repair(state) {
  if (state === 'no-secret') {
    return 'set a secret on the hook first. Until there is one, GitHub sends ' +
      'no signature and no digest choice matters.';
  }
  if (state === 'headers-missing') {
    return 'read a delivery from after the secret was set, then re-run.';
  }
  if (state === 'not-scanned') {
    return 're-run with a path to the source tree that handles the webhook.';
  }
  if (state === 'no-verification-found') {
    return 'confirm by hand that the receiver verifies at all. If it does ' +
      'not, verify X-Hub-Signature-256 over the raw request bytes with a ' +
      'constant-time comparison and reject a request whose header is missing.';
  }
  if (state === 'sha1-only' || state === 'both-accepted') {
    return 'verify X-Hub-Signature-256 over the raw request bytes with a ' +
      'constant-time comparison, then delete the SHA-1 branch rather than ' +
      'keeping it as a fallback.';
  }
  return 'nothing. This receiver verifies the header GitHub wants it to.';
}

async function walk(root) {
  const info = await stat(root).catch(() => null);
  if (!info) return [];
  if (info.isFile()) return [root];
  const out = [];
  const entries = await readdir(root, { withFileTypes: true }).catch(() => []);
  for (const entry of entries) {
    if (entry.isDirectory()) {
      if (SKIP_DIRS.includes(entry.name)) continue;
      out.push(...await walk(path.join(root, entry.name)));
    } else if (SUFFIXES.some((s) => entry.name.endsWith(s))) {
      out.push(path.join(root, entry.name));
    }
  }
  return out;
}

async function scanPaths(paths) {
  const hits = [];
  const scanned = [];
  for (const root of paths ?? []) {
    for (const file of await walk(root)) {
      const text = await readFile(file, 'utf8').catch(() => null);
      if (text === null) continue;
      scanned.push(file);
      hits.push(...scanSource(text, file));
    }
  }
  return { hits, scanned };
}

async function get(token, endpoint) {
  const res = await fetch(endpoint.startsWith('/') ? API + endpoint : endpoint, {
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      'User-Agent': UA,
    },
  });
  let body = null;
  try { body = await res.json(); } catch { body = null; }
  return { status: res.status, body };
}

async function latestDeliveryHeaders(token, repo, hookId) {
  const list = await get(token, `/repos/${repo}/hooks/${hookId}/deliveries?per_page=10`);
  if (list.status !== 200 || !Array.isArray(list.body)) return null;
  for (const row of list.body) {
    if (!row || typeof row !== 'object' || !row.id) continue;
    const one = await get(token, `/repos/${repo}/hooks/${hookId}/deliveries/${row.id}`);
    if (one.status === 200 && one.body && typeof one.body === 'object') {
      const request = one.body.request;
      if (request && typeof request === 'object') return request.headers;
    }
  }
  return null;
}

async function main() {
  const token = process.env.GITHUB_TOKEN;
  if (!token) {
    console.error('set GITHUB_TOKEN to a read-only token that can see the ' +
      "repository's hooks");
    process.exitCode = 2;
    return;
  }
  const [repo, ...receivers] = process.argv.slice(2);
  if (!repo) {
    console.error('usage: node github-hook-signature-headers.mjs owner/name [receiver-path...]');
    process.exitCode = 2;
    return;
  }

  const { status, body: hooks } = await get(token, `/repos/${repo}/hooks?per_page=100`);
  if (status !== 200 || !Array.isArray(hooks)) {
    console.error(`GET /repos/${repo}/hooks returned ${status}`);
    process.exitCode = 2;
    return;
  }

  const { hits, scanned } = await scanPaths(receivers);
  const stateOfReceiver = receivers.length ? receiverState(hits) : null;
  if (receivers.length) {
    const files = new Set(hits.map(([f]) => f));
    console.log(`source scan: ${hits.length} reference(s) across ${files.size} file(s)`);
    for (const hit of hits) console.log(`  ${formatHit(hit)}`);
  }

  const findings = [];
  for (const hook of hooks) {
    const secret = secretState(hook);
    const headers = secret === 'set'
      ? await latestDeliveryHeaders(token, repo, hook.id)
      : null;
    const sig = headers !== null && headers !== undefined ? signatureHeaders(headers) : null;
    const [state, detail] = verdict(secret, sig, stateOfReceiver);
    console.log(`hook ${hook.id}: secret is ${secret}, ` +
      (sig && sig.sha1 && sig.sha256
        ? 'GitHub sent both signature headers'
        : 'no delivery headers were read'));
    console.log(`${state}: ${detail}`);
    console.log(`repair: ${repair(state)}`);
    findings.push({
      hook_id: hook.id,
      secret,
      signature_headers: sig,
      state,
      detail,
      config: redactedConfig(hook.config),
    });
  }

  console.log(JSON.stringify({
    repo,
    files_scanned: scanned.length,
    references: hits.map(formatHit),
    findings,
  }, null, 2));
  process.exitCode = findings.some((f) => FINDINGS.includes(f.state)) ? 1 : 0;
}

// Only run when invoked directly, so importing this module from the test file
// does not execute main() and set an exit code that fails the suite even as
// every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "One test matters more than the rest: a line that names only <code>X-Hub-Signature-256</code> must produce a modern reference and no legacy one. Get that wrong and the tool reports every correct receiver as a legacy one, on every line where it is right. The others pin the runtime spellings of the same header, the guarantee that the scan emits line numbers and never line contents, the difference between a receiver that names both headers and one that names the right one, and the two states this note refuses to claim &mdash; a hook with no secret, and a source tree where nothing was found.",
"test_py_file": "test_github_hook_signature_headers.py",
"test_py": '''from github_hook_signature_headers import (
    format_hit, header_names, normalized, receiver_state, redacted_config,
    repair, scan_line, scan_source, secret_state, signature_headers, verdict,
)

MODERN_LINE = 'sig = request.headers["X-Hub-Signature-256"]'
LEGACY_LINE = 'sig = request.headers["X-Hub-Signature"]'
WSGI_LINE = 'sig = environ["HTTP_X_HUB_SIGNATURE_256"]'

SECRET_SET = {"id": 1, "config": {"url": "https://example.com/hook",
                                  "secret": "********", "content_type": "json"}}
NO_SECRET = {"id": 2, "config": {"url": "https://example.com/hook",
                                 "content_type": "json"}}


def test_the_modern_header_is_not_read_as_a_legacy_one():
    assert scan_line(MODERN_LINE) == ["sha256"]
    assert scan_line(LEGACY_LINE) == ["sha1"]
    assert scan_line("nothing to see here") == []


def test_a_line_naming_both_headers_reports_both():
    line = 'const h = req.headers["x-hub-signature-256"] ?? req.headers["x-hub-signature"];'
    assert scan_line(line) == ["sha256", "sha1"]


def test_the_runtime_spellings_are_the_same_header():
    assert scan_line(WSGI_LINE) == ["sha256"]
    assert scan_line("X_HUB_SIGNATURE") == ["sha1"]
    assert normalized("X-Hub_Signature-256") == "x-hub-signature-256"


def test_the_scan_reports_line_numbers_and_never_lines():
    text = "\\n".join(["import os", LEGACY_LINE, "", MODERN_LINE])
    hits = scan_source(text, "receiver/hooks.py")
    assert hits == [("receiver/hooks.py", 2, "sha1"),
                    ("receiver/hooks.py", 4, "sha256")]
    rendered = [format_hit(h) for h in hits]
    assert rendered[0] == "receiver/hooks.py:2 legacy X-Hub-Signature"
    assert rendered[1] == "receiver/hooks.py:4 modern X-Hub-Signature-256"
    assert not any("request.headers" in line for line in rendered)


def test_the_receiver_state_separates_only_legacy_from_both():
    assert receiver_state([("a", 1, "sha1")]) == "sha1-only"
    assert receiver_state([("a", 1, "sha256")]) == "sha256-only"
    assert receiver_state([("a", 1, "sha256"), ("a", 1, "sha1")]) == "both"
    assert receiver_state([]) == "none"


def test_a_masked_secret_is_presence_and_never_a_value():
    assert secret_state(SECRET_SET) == "set"
    assert secret_state(NO_SECRET) == "absent"
    assert secret_state({"id": 3}) == "unknown"
    safe = redacted_config(SECRET_SET["config"])
    assert safe["secret"] == "<set>"
    assert "********" not in str(safe)


def test_header_names_are_matched_exactly_and_values_dropped():
    sent = {"X-Hub-Signature": "sha1=deadbeef",
            "X-Hub-Signature-256": "sha256=deadbeef",
            "Content-Type": "application/json"}
    assert signature_headers(sent) == {"sha256": True, "sha1": True}
    assert signature_headers({"X-Hub-Signature-256": "x"}) == {"sha256": True, "sha1": False}
    assert signature_headers({}) == {"sha256": False, "sha1": False}
    assert "deadbeef" not in str(header_names(sent))


def test_delivery_headers_arrive_in_more_than_one_shape():
    as_list = [{"name": "X-Hub-Signature-256", "value": "sha256=x"},
               {"name": "Content-Type", "value": "application/json"}]
    assert signature_headers(as_list)["sha256"] is True
    assert signature_headers(["X-Hub-Signature: sha1=x"])["sha1"] is True
    assert signature_headers(None) == {"sha256": False, "sha1": False}


def test_a_legacy_receiver_is_the_finding():
    state, detail = verdict("set", {"sha256": True, "sha1": True}, "sha1-only")
    assert state == "sha1-only"
    assert "being ignored" in detail
    assert "constant-time" in repair(state)


def test_accepting_both_headers_is_still_a_finding():
    state, detail = verdict("set", {"sha256": True, "sha1": True}, "both")
    assert state == "both-accepted"
    assert "weaker" in detail


def test_a_hook_with_no_secret_is_sent_to_a_different_note():
    state, detail = verdict("absent", None, "sha1-only")
    assert state == "no-secret"
    assert "different and larger problem" in detail


def test_with_no_source_the_script_declines_to_guess():
    state, detail = verdict("set", {"sha256": True, "sha1": True}, None)
    assert state == "not-scanned"
    assert "not visible from the API" in detail


def test_finding_nothing_is_not_reported_as_finding_a_problem():
    state, detail = verdict("set", {"sha256": True, "sha1": True}, "none")
    assert state == "no-verification-found"
    assert "at runtime" in detail


def test_a_correct_receiver_passes():
    state, _ = verdict("set", {"sha256": True, "sha1": True}, "sha256-only")
    assert state == "sha256-only"
    assert repair(state).startswith("nothing")
''',
"test_js_file": "github-hook-signature-headers.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  formatHit, headerNames, normalized, receiverState, redactedConfig,
  repair, scanLine, scanSource, secretState, signatureHeaders, verdict,
} from './github-hook-signature-headers.mjs';

const MODERN_LINE = 'const sig = req.headers["X-Hub-Signature-256"];';
const LEGACY_LINE = 'const sig = req.headers["X-Hub-Signature"];';
const WSGI_LINE = 'sig = environ["HTTP_X_HUB_SIGNATURE_256"]';

const SECRET_SET = {
  id: 1,
  config: { url: 'https://example.com/hook', secret: '********', content_type: 'json' },
};
const NO_SECRET = {
  id: 2,
  config: { url: 'https://example.com/hook', content_type: 'json' },
};

test('the modern header is not read as a legacy one', () => {
  assert.deepEqual(scanLine(MODERN_LINE), ['sha256']);
  assert.deepEqual(scanLine(LEGACY_LINE), ['sha1']);
  assert.deepEqual(scanLine('nothing to see here'), []);
});

test('a line naming both headers reports both', () => {
  const line = 'const h = req.headers["x-hub-signature-256"] ?? req.headers["x-hub-signature"];';
  assert.deepEqual(scanLine(line), ['sha256', 'sha1']);
});

test('the runtime spellings are the same header', () => {
  assert.deepEqual(scanLine(WSGI_LINE), ['sha256']);
  assert.deepEqual(scanLine('X_HUB_SIGNATURE'), ['sha1']);
  assert.equal(normalized('X-Hub_Signature-256'), 'x-hub-signature-256');
});

test('the scan reports line numbers and never lines', () => {
  const text = ['import os', LEGACY_LINE, '', MODERN_LINE].join('\\n');
  const hits = scanSource(text, 'receiver/hooks.js');
  assert.deepEqual(hits, [
    ['receiver/hooks.js', 2, 'sha1'],
    ['receiver/hooks.js', 4, 'sha256'],
  ]);
  const rendered = hits.map(formatHit);
  assert.equal(rendered[0], 'receiver/hooks.js:2 legacy X-Hub-Signature');
  assert.equal(rendered[1], 'receiver/hooks.js:4 modern X-Hub-Signature-256');
  assert.ok(!rendered.some((line) => line.includes('req.headers')));
});

test('the receiver state separates only legacy from both', () => {
  assert.equal(receiverState([['a', 1, 'sha1']]), 'sha1-only');
  assert.equal(receiverState([['a', 1, 'sha256']]), 'sha256-only');
  assert.equal(receiverState([['a', 1, 'sha256'], ['a', 1, 'sha1']]), 'both');
  assert.equal(receiverState([]), 'none');
});

test('a masked secret is presence and never a value', () => {
  assert.equal(secretState(SECRET_SET), 'set');
  assert.equal(secretState(NO_SECRET), 'absent');
  assert.equal(secretState({ id: 3 }), 'unknown');
  const safe = redactedConfig(SECRET_SET.config);
  assert.equal(safe.secret, '<set>');
  assert.ok(!JSON.stringify(safe).includes('********'));
});

test('header names are matched exactly and values dropped', () => {
  const sent = {
    'X-Hub-Signature': 'sha1=deadbeef',
    'X-Hub-Signature-256': 'sha256=deadbeef',
    'Content-Type': 'application/json',
  };
  assert.deepEqual(signatureHeaders(sent), { sha256: true, sha1: true });
  assert.deepEqual(signatureHeaders({ 'X-Hub-Signature-256': 'x' }),
    { sha256: true, sha1: false });
  assert.deepEqual(signatureHeaders({}), { sha256: false, sha1: false });
  assert.ok(!JSON.stringify(headerNames(sent)).includes('deadbeef'));
});

test('delivery headers arrive in more than one shape', () => {
  const asList = [
    { name: 'X-Hub-Signature-256', value: 'sha256=x' },
    { name: 'Content-Type', value: 'application/json' },
  ];
  assert.equal(signatureHeaders(asList).sha256, true);
  assert.equal(signatureHeaders(['X-Hub-Signature: sha1=x']).sha1, true);
  assert.deepEqual(signatureHeaders(null), { sha256: false, sha1: false });
});

test('a legacy receiver is the finding', () => {
  const [state, detail] = verdict('set', { sha256: true, sha1: true }, 'sha1-only');
  assert.equal(state, 'sha1-only');
  assert.match(detail, /being ignored/);
  assert.match(repair(state), /constant-time/);
});

test('accepting both headers is still a finding', () => {
  const [state, detail] = verdict('set', { sha256: true, sha1: true }, 'both');
  assert.equal(state, 'both-accepted');
  assert.match(detail, /weaker/);
});

test('a hook with no secret is sent to a different note', () => {
  const [state, detail] = verdict('absent', null, 'sha1-only');
  assert.equal(state, 'no-secret');
  assert.match(detail, /different and larger problem/);
});

test('with no source the script declines to guess', () => {
  const [state, detail] = verdict('set', { sha256: true, sha1: true }, null);
  assert.equal(state, 'not-scanned');
  assert.match(detail, /not visible from the API/);
});

test('finding nothing is not reported as finding a problem', () => {
  const [state, detail] = verdict('set', { sha256: true, sha1: true }, 'none');
  assert.equal(state, 'no-verification-found');
  assert.match(detail, /at runtime/);
});

test('a correct receiver passes', () => {
  const [state] = verdict('set', { sha256: true, sha1: true }, 'sha256-only');
  assert.equal(state, 'sha256-only');
  assert.ok(repair(state).startsWith('nothing'));
});
''',
"faq": [
 ("Is the SHA-1 header actually insecure?",
  "The practical answer is that HMAC-SHA1 has held up better than bare SHA-1, and nobody is forging your webhook payloads this afternoon. The reason to move is not an imminent break, it is that you are choosing the weaker of two digests that are already both being sent to you, at no cost and with no migration, and that every security questionnaire and every auditor from now on will ask about it. GitHub keeps sending the SHA-1 header for compatibility, not as a recommendation."),
 ("Why does the script read my source instead of just checking the API?",
  "Because the API genuinely cannot answer this. GitHub records what it sent and what your server replied; there is no field anywhere describing which header your code read. A script that stopped at the API could only ever print a recommendation. Reading the source turns it into a finding for the ordinary case where the header name is a literal in the code, and the script is explicit that a name built at runtime or wrapped in a framework helper is invisible to it."),
 ("It found nothing at all in my receiver. Is that good?",
  "No, and the script does not call it good. Finding neither header name means one of three things: the receiver does not verify signatures, the header name is constructed rather than written out, or the scan was pointed at the wrong directory. Only the first is a serious problem and it is the most serious one in this note, so the state is reported as its own thing rather than being folded into a pass. Check by hand which of the three you are in."),
 ("We check the SHA-256 header and fall back to SHA-1 for old clients. Is that fine?",
  "There are no old clients. GitHub is the only sender, and it sends both headers on every delivery, so a fallback path cannot be reached by any legitimate request that could not also satisfy the modern check. What it can be reached by is a request carrying only a SHA-1 signature, which is to say the exact request you would want rejected. Accepting either header leaves you as strong as the weaker one, so the script reports it as a finding."),
 ("Does any of this change what I do about the raw body?",
  "It is the part people get wrong immediately after switching headers. The HMAC is computed over the exact bytes GitHub sent, so a framework that parses JSON and hands you a dict has already destroyed the input: re-serialising it produces different bytes and a signature that never matches. Capture the raw body before anything parses it, verify against that, and only then parse. This is also why a form-encoded hook breaks naive verification, which is a separate note."),
],
"related": [
 ("/github/webhook-no-secret/", "A webhook with no secret sends no signature"),
 ("/github/webhook-deliveries-failing/", "Deliveries failing where nobody reads the log"),
 ("/github/webhook-http-url/", "A webhook posting to a plain http:// URL"),
],
"citations": [CITE_VALIDATE, CITE_REPO_HOOKS, CITE_BEST_PRACTICES, CITE_APP_HOOKS],
},

{
"slug": "webhook-insecure-ssl",
"title": "SSL verification is switched off on the webhook",
"description": "config.insecure_ssl set to 1 tells GitHub not to check your endpoint's certificate. Deliveries keep succeeding, which is exactly why nobody looks.",
"h1": "SSL verification is switched off on the webhook",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github webhook insecure_ssl",
             "disable ssl verification github webhook",
             "github webhook self signed certificate",
             "insecure_ssl 1 webhook config",
             "github webhook certificate verification off"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The URL starts with <code>https</code>. The delivery log is clean, every attempt is a <code>200</code>, and the hook has a secret so the payloads are signed. Everything a review asks about is green. One field in the same config object says <code>&quot;insecure_ssl&quot;: &quot;1&quot;</code>, which means GitHub has not looked at your certificate since somebody set that during the initial deploy in 2023.",
"short_answer": """<p>Read <code>GET /repos/{owner}/{repo}/hooks</code> and look at <code>config.insecure_ssl</code>. <code>"1"</code> means GitHub skips verification of your endpoint's TLS certificate; <code>"0"</code> means it checks. The value is a string, which matters, because <code>"0"</code> is a non-empty string and a truthy test on it reports every correctly configured hook as insecure.</p>
<p>Deliveries succeed either way, so nothing surfaces this. What you have lost is not encryption but identity: the connection is still TLS, but GitHub will accept whatever certificate is presented, so anything that can answer for your hostname &mdash; a stale DNS record somebody else now owns, a compromised load balancer, a machine on the path &mdash; receives your payloads, correctly signed with your secret, and can replay them at your real endpoint afterwards. Fix the certificate first, set the flag back to <code>"0"</code>, then rotate the secret.</p>""",
"problem": """<p>It gets switched on for an honest reason and stays on for a stupid one. Somebody is bringing the receiver up on staging behind a self-signed certificate, or an internal CA that GitHub has never heard of, and deliveries fail with a TLS error. There is a checkbox that makes the error go away, they tick it, the integration starts working, and the ticket closes. The certificate gets fixed a fortnight later and nobody goes back to untick the box, because by then nothing is broken and the box is two screens deep in a settings page nobody has a reason to open.</p>
<p>After that it is invisible by construction. Every other signal says the integration is healthy: deliveries succeed, the log is clean, the URL is <code>https</code>, the payloads are signed. A security review that looks at the URL scheme sees TLS and moves on. The one field that says otherwise is a string of one character in an object most people never print, and it is spelled in a way that reads as reassuring: <code>insecure_ssl</code> is <code>"0"</code> when things are <em>fine</em>, so a skim looking for a scary value finds a zero and relaxes.</p>
<p>Then the repair goes wrong in its own particular way. Setting the flag back is a config update, and a webhook's <code>config</code> is replaced rather than merged, so the natural instinct &mdash; read the config, change one field, write it back &mdash; sends back the masked secret, which means the hook's secret becomes the literal string of asterisks or is dropped entirely. Signature verification breaks on the next delivery and the change gets reverted by somebody who concludes the flag was load bearing.</p>""",
"why": """<p><strong>The flag disables verification, not encryption.</strong> The bytes are still inside TLS, so this is not the same as posting in the clear. What goes away is the guarantee that the endpoint on the other end is yours. An attacker no longer needs to read the wire; they need to be answered instead of you, which is a much older and much easier trick than breaking a cipher.</p>
<p><strong>A signed payload does not protect you here.</strong> The signature proves GitHub sent it. It says nothing about who received it, and it travels in the same request, so an impersonating endpoint collects a stream of genuine, correctly signed payloads. Those payloads carry repository names, branch names, commit messages, issue bodies and pull request diffsets depending on the events, and they can be replayed against your real receiver later, because they will verify perfectly.</p>
<p><strong>It is a string, and the wrong test on it inverts the answer.</strong> <code>config.insecure_ssl</code> comes back as <code>"0"</code> or <code>"1"</code>, and both are non-empty strings. Anyone who writes <code>if config["insecure_ssl"]</code> flags every safe hook in the organization and learns to ignore the tool. Parse the value; do not test it.</p>
<p><strong>Turning it off is not the whole repair.</strong> Setting the flag back to <code>"0"</code> while the certificate is still bad turns a silent exposure into a wall of failed deliveries, which is better but is not what anyone wants at four on a Friday. Install a certificate the public trust store accepts first, confirm it independently, then flip the flag. If the endpoint is genuinely internal and cannot have a public certificate, the fix is a public gateway in front of it, not a permanent exemption.</p>
<p><strong>And the secret has to be rotated afterwards.</strong> For as long as verification was off, any endpoint that managed to be answered instead of yours received payloads signed with your secret. The secret itself is not in the payload, so it was not disclosed &mdash; but the window during which the traffic could be collected and replayed was real, and rotation is the only thing that closes it. Rotate by sending the full config with a new secret, not by patching one field.</p>""",
"steps": [
 {"h": "Read the flag on every hook, in every scope",
  "body": """<p><code>GET /repos/{owner}/{repo}/hooks</code> and <code>GET /orgs/{org}/hooks</code> both return <code>config.insecure_ssl</code>. A GitHub App's own hook exposes the same field at <code>GET /app/hook/config</code>. Read all the scopes that can reach the repository, because the one that was set up by hand during an incident is rarely the one anybody remembers.</p>"""},
 {"h": "Parse the value rather than testing it",
  "body": """<p>Accept <code>"1"</code>, <code>1</code> and <code>true</code> as on; <code>"0"</code>, <code>0</code> and <code>false</code> as off; anything else as unreadable. A truthy test reports <code>"0"</code> as insecure, which is the failure mode that gets a security tool switched off after its first run.</p>"""},
 {"h": "Skip the hooks that are a different problem",
  "body": """<p>A hook whose URL is <code>http://</code> performs no TLS handshake at all, so <code>insecure_ssl</code> describes nothing and is not the finding to report there. The script says so and points at the other question, rather than counting a plaintext hook as a certificate problem and letting the real one hide inside the number.</p>"""},
 {"h": "Date it from updated_at",
  "body": """<p><code>updated_at</code> moves on any config change, so a hook that has not been touched in eleven months has had verification off for at least that long. It is a lower bound rather than a start date, and the script says <em>at least</em> for that reason, but it is usually enough to answer the only question anybody asks next.</p>"""},
 {"h": "Fix the certificate, then the flag, then the secret",
  "body": """<p>In that order. Install a certificate that chains to a public root, verify it from outside your network, then send the hook's full config with <code>insecure_ssl</code> set to <code>"0"</code> &mdash; the whole object, including the URL, the content type and a freshly generated secret, because the config is replaced and the secret you read back is a mask.</p>"""},
],
"verify": """<p>The re-read shows <code>"0"</code>, deliveries keep succeeding, and a request to the endpoint from a machine with a normal trust store completes without a certificate warning.</p>
<pre><code class="language-bash">GITHUB_TOKEN=$GH_READONLY python3 github_hook_ssl_verification.py --repo acme-corp/api
# 3 hook(s) on acme-corp/api
# verification-off: hook 512334455 posts to https://hooks.acme.io/github with
# certificate verification disabled, and has not been edited for at least 341
# day(s). Deliveries succeed, so nothing else reports this.
# repair: install a certificate that chains to a public root, confirm it from
# outside your network, then send the hook's full config with insecure_ssl "0"
# and a new secret. The config is replaced, not merged, and the secret you read
# back is a mask.

# after the change
# verified: hook 512334455 posts to https://hooks.acme.io/github and GitHub
# checks the certificate</code></pre>""",
"code_intro": "One GET per scope, and the whole finding is one field. The care goes into not getting a two-value string wrong in either direction: a truthy test calls every safe hook insecure, and a falsy test on an absent field calls an unknown hook safe, so the parse has three outcomes and the third is reported rather than rounded. The rest of the pure core keeps this note out of its neighbour's territory &mdash; a hook with no TLS at all is handed to the plaintext question instead of being counted here &mdash; and dates the exposure as a lower bound from the one timestamp that exists. The repair is printed, and it is printed as a whole config rather than a single field, because the config is replaced and the secret comes back masked.",
"py_file": "github_hook_ssl_verification.py",
"py": '''"""Find webhooks GitHub delivers to without checking the TLS certificate.

Read only. Every call is a GET. Changing the flag is a write and this script
does not do it: it prints the request, as a full config rather than a single
field, because a webhook's config is replaced rather than merged and the secret
you read back is a mask.

config.insecure_ssl set to "1" tells GitHub to skip verification of the
endpoint's certificate. The connection is still TLS, so this is not the same as
posting in the clear; what is lost is the guarantee that the endpoint is yours.
Anything that can be answered instead of you receives correctly signed payloads
and can replay them afterwards.

Deliveries succeed the whole time, which is why nothing else reports this.

The secret is never printed. Its presence is read only to decide whether the
repair needs to mention rotation.

Environment:

    GITHUB_TOKEN    a read-only token that can see the repository's hooks
"""
import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_hook_ssl_verification")

API = "https://api.github.com"
UA = "github-hook-ssl-verification/1.0"

# The two-value string, in every spelling it arrives in. Both "0" and "1" are
# non-empty strings, so a truthy test on this field reports every correctly
# configured hook as insecure. Parse it; do not test it.
INSECURE_ON = ("1", "true", "yes", "on")
INSECURE_OFF = ("0", "false", "no", "off")


def config_of(hook):
    """The config object of a hook, or an empty dict. Pure."""
    if not isinstance(hook, dict):
        return {}
    config = hook.get("config")
    return config if isinstance(config, dict) else {}


def insecure_flag(hook):
    """Three-state read of insecure_ssl: on, off or unknown. Pure.

    on  means GitHub does not check the certificate
    off means it does
    unknown means the field was absent or unreadable, which is reported rather
            than rounded to either answer
    """
    config = config_of(hook)
    if "insecure_ssl" not in config:
        return "unknown"
    raw = config["insecure_ssl"]
    if isinstance(raw, bool):
        return "on" if raw else "off"
    if isinstance(raw, (int, float)):
        return "on" if raw else "off"
    text = str(raw).strip().lower()
    if text in INSECURE_ON:
        return "on"
    if text in INSECURE_OFF:
        return "off"
    return "unknown"


def scheme_of(hook):
    """The URL scheme of a hook, lower-cased, or "" when there is none. Pure."""
    url = str(config_of(hook).get("url") or "").strip()
    if "://" not in url:
        return ""
    return url.split("://", 1)[0].lower()


def endpoint(hook):
    """The hook's URL with any query string dropped. Pure.

    A URL is printable, a query string is not reliably so: hooks created by
    hand sometimes carry a token in one, and this script prints its findings.
    """
    url = str(config_of(hook).get("url") or "").strip()
    return url.split("?", 1)[0] if url else "an unset URL"


def has_secret(hook):
    """Whether the hook has a secret set. Pure. The value is never read."""
    return "secret" in config_of(hook)


def parsed_time(text):
    """An ISO 8601 timestamp as an aware datetime, or None. Pure."""
    raw = str(text or "").strip()
    if not raw or raw.lower() in ("null", "none"):
        return None
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        when = datetime.fromisoformat(raw)
    except ValueError:
        return None
    return when if when.tzinfo else when.replace(tzinfo=timezone.utc)


def unchanged_days(hook, now):
    """Days since the hook config was last edited, or None. Pure.

    A lower bound on how long verification has been off, never a start date:
    updated_at moves on any change to the hook, so it says "not since then"
    rather than "since then".
    """
    if not isinstance(hook, dict) or now is None:
        return None
    when = parsed_time(hook.get("updated_at"))
    if when is None:
        return None
    return (now - when).days


def classify(hook, now=None):
    """Sort one hook into a state and a sentence. Pure.

    A hook with no TLS at all is handed to the plaintext question rather than
    counted here. insecure_ssl describes a handshake that hook never performs,
    and folding the two together lets the real finding hide inside a number.
    """
    ident = "hook %s" % (hook.get("id", "?") if isinstance(hook, dict) else "?")
    scheme = scheme_of(hook)
    flag = insecure_flag(hook)
    if not scheme:
        return ("no-url",
                "%s has no usable URL in its config, so there is nothing to "
                "verify a certificate against." % ident)
    if scheme != "https":
        return ("not-applicable",
                "%s posts to a %s:// URL, so no certificate is checked because "
                "no TLS handshake happens. insecure_ssl is not the finding "
                "here; the scheme is." % (ident, scheme))
    if flag == "on":
        age = unchanged_days(hook, now)
        return ("verification-off",
                "%s posts to %s with certificate verification disabled%s. "
                "Deliveries succeed, so nothing else reports this."
                % (ident, endpoint(hook),
                   ", and has not been edited for at least %d day(s)" % age
                   if age is not None else ""))
    if flag == "unknown":
        return ("flag-unreadable",
                "%s does not report a readable insecure_ssl value. Read it in "
                "the hook's settings rather than assuming either answer."
                % ident)
    return ("verified",
            "%s posts to %s and GitHub checks the certificate."
            % (ident, endpoint(hook)))


def repair(state, hook):
    """The change to make, printed as a whole config. Pure.

    Never a single-field update. A webhook's config is replaced rather than
    merged, and config.secret comes back masked, so a read-modify-write of one
    field writes the mask back as the secret or drops it.
    """
    if state == "verification-off":
        rotate = (" and a new secret" if has_secret(hook)
                  else " and a secret, since this hook has none")
        return ("install a certificate that chains to a public root, confirm "
                "it from outside your network, then send the hook's full "
                "config with insecure_ssl \\"0\\"%s. The config is replaced, not "
                "merged, and the secret you read back is a mask." % rotate)
    if state == "not-applicable":
        return ("move the receiver behind HTTPS and change the URL. Until "
                "then insecure_ssl is a field about a handshake this hook "
                "never performs.")
    if state == "flag-unreadable":
        return ("open the hook's settings and read the SSL verification "
                "setting by hand.")
    if state == "no-url":
        return ("set a URL on this hook, or delete it. A hook with no endpoint "
                "delivers nothing and hides in every audit that counts hooks.")
    return "nothing. GitHub verifies this endpoint's certificate."


def summarize(hooks, now=None):
    """Counts across every hook read. Pure."""
    rows = [h for h in (hooks or []) if isinstance(h, dict)]
    states = [classify(h, now)[0] for h in rows]
    return {"total": len(rows),
            "verification_off": states.count("verification-off"),
            "verified": states.count("verified"),
            "plaintext": states.count("not-applicable"),
            "unreadable": states.count("flag-unreadable") + states.count("no-url")}


def get(session, path):
    """One GET. Returns (status, json-or-None)."""
    url = API + path if path.startswith("/") else path
    r = session.get(url, timeout=30)
    try:
        body = r.json()
    except ValueError:
        body = None
    return r.status_code, body


def list_hooks(session, scope):
    """Hooks for a repo (owner/name) or an org (@org). Read only."""
    path = ("/orgs/%s/hooks?per_page=100" % scope[1:] if scope.startswith("@")
            else "/repos/%s/hooks?per_page=100" % scope)
    status, body = get(session, path)
    if status != 200 or not isinstance(body, list):
        log.error("GET %s returned %d", path, status)
        return []
    return body


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", action="append", default=[],
                    help="owner/name; repeatable")
    ap.add_argument("--org", action="append", default=[],
                    help="organization login; repeatable")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_TOKEN to a read-only token that can see the "
                  "repository's hooks")
        return 2
    scopes = list(args.repo) + ["@" + o for o in args.org]
    if not scopes:
        log.error("pass at least one --repo owner/name or --org login")
        return 2

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": UA,
    })

    now = datetime.now(timezone.utc)
    findings = []
    for scope in scopes:
        label = scope[1:] if scope.startswith("@") else scope
        hooks = list_hooks(session, scope)
        stats = summarize(hooks, now)
        log.info("%d hook(s) on %s", stats["total"], label)
        for hook in hooks:
            state, detail = classify(hook, now)
            findings.append({"scope": label, "hook_id": hook.get("id"),
                             "state": state, "detail": detail,
                             "url": endpoint(hook),
                             "secret_set": has_secret(hook)})
            if state != "verified":
                log.info("%s: %s", state, detail)
                log.info("repair: %s", repair(state, hook))
        if stats["verification_off"] == 0:
            log.info("verified: no hook on %s has certificate verification "
                     "disabled", label)

    print(json.dumps({"scopes": scopes, "findings": findings},
                     indent=2, default=str))
    return 1 if any(f["state"] == "verification-off" for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-hook-ssl-verification.mjs",
"js": '''/**
 * Find webhooks GitHub delivers to without checking the TLS certificate.
 *
 * Read only. Every call is a GET. Changing the flag is a write and is not done
 * here: the script prints the request, as a full config rather than a single
 * field, because a webhook's config is replaced rather than merged and the
 * secret you read back is a mask.
 *
 * config.insecure_ssl set to "1" tells GitHub to skip verification of the
 * endpoint's certificate. The connection is still TLS; what is lost is the
 * guarantee that the endpoint is yours.
 *
 * The secret is never printed. Its presence is read only to decide whether the
 * repair needs to mention rotation.
 *
 * Environment:
 *   GITHUB_TOKEN   a read-only token that can see the repository's hooks
 *
 * Usage:
 *   node github-hook-ssl-verification.mjs acme-corp/api @acme-corp
 */
const API = 'https://api.github.com';
const UA = 'github-hook-ssl-verification/1.0';

const INSECURE_ON = ['1', 'true', 'yes', 'on'];
const INSECURE_OFF = ['0', 'false', 'no', 'off'];

/** The config object of a hook, or an empty object. Pure. */
export function configOf(hook) {
  if (!hook || typeof hook !== 'object') return {};
  const config = hook.config;
  return config && typeof config === 'object' ? config : {};
}

/**
 * Three-state read of insecure_ssl: on, off or unknown. Pure.
 * Both '0' and '1' are non-empty strings, so a truthy test reports every
 * correctly configured hook as insecure.
 */
export function insecureFlag(hook) {
  const config = configOf(hook);
  if (!('insecure_ssl' in config)) return 'unknown';
  const raw = config.insecure_ssl;
  if (typeof raw === 'boolean') return raw ? 'on' : 'off';
  if (typeof raw === 'number') return raw ? 'on' : 'off';
  const text = String(raw ?? '').trim().toLowerCase();
  if (INSECURE_ON.includes(text)) return 'on';
  if (INSECURE_OFF.includes(text)) return 'off';
  return 'unknown';
}

/** The URL scheme of a hook, lower-cased, or '' when there is none. Pure. */
export function schemeOf(hook) {
  const url = String(configOf(hook).url ?? '').trim();
  if (!url.includes('://')) return '';
  return url.split('://')[0].toLowerCase();
}

/** The hook's URL with any query string dropped. Pure. */
export function endpoint(hook) {
  const url = String(configOf(hook).url ?? '').trim();
  return url ? url.split('?')[0] : 'an unset URL';
}

/** Whether the hook has a secret set. Pure. The value is never read. */
export function hasSecret(hook) {
  return 'secret' in configOf(hook);
}

/** An ISO 8601 timestamp as epoch milliseconds, or null. Pure. */
export function parsedTime(text) {
  const raw = String(text ?? '').trim();
  if (!raw || ['null', 'none'].includes(raw.toLowerCase())) return null;
  const ms = Date.parse(raw);
  return Number.isNaN(ms) ? null : ms;
}

/** Days since the hook config was last edited, or null. Pure. A lower bound. */
export function unchangedDays(hook, nowMs) {
  if (!hook || typeof hook !== 'object' || nowMs === null || nowMs === undefined) {
    return null;
  }
  const when = parsedTime(hook.updated_at);
  if (when === null) return null;
  return Math.floor((nowMs - when) / 86400000);
}

/** Sort one hook into a state and a sentence. Pure. */
export function classify(hook, nowMs = null) {
  const ident = `hook ${(hook && typeof hook === 'object' ? hook.id : null) ?? '?'}`;
  const scheme = schemeOf(hook);
  const flag = insecureFlag(hook);
  if (!scheme) {
    return ['no-url',
      `${ident} has no usable URL in its config, so there is nothing to ` +
      'verify a certificate against.'];
  }
  if (scheme !== 'https') {
    return ['not-applicable',
      `${ident} posts to a ${scheme}:// URL, so no certificate is checked ` +
      'because no TLS handshake happens. insecure_ssl is not the finding ' +
      'here; the scheme is.'];
  }
  if (flag === 'on') {
    const age = unchangedDays(hook, nowMs);
    return ['verification-off',
      `${ident} posts to ${endpoint(hook)} with certificate verification ` +
      `disabled${age !== null ? `, and has not been edited for at least ${age} day(s)` : ''}. ` +
      'Deliveries succeed, so nothing else reports this.'];
  }
  if (flag === 'unknown') {
    return ['flag-unreadable',
      `${ident} does not report a readable insecure_ssl value. Read it in the ` +
      "hook's settings rather than assuming either answer."];
  }
  return ['verified',
    `${ident} posts to ${endpoint(hook)} and GitHub checks the certificate.`];
}

/** The change to make, printed as a whole config. Pure. */
export function repair(state, hook) {
  if (state === 'verification-off') {
    const rotate = hasSecret(hook)
      ? ' and a new secret'
      : ' and a secret, since this hook has none';
    return 'install a certificate that chains to a public root, confirm it ' +
      "from outside your network, then send the hook's full config with " +
      `insecure_ssl "0"${rotate}. The config is replaced, not merged, and the ` +
      'secret you read back is a mask.';
  }
  if (state === 'not-applicable') {
    return 'move the receiver behind HTTPS and change the URL. Until then ' +
      'insecure_ssl is a field about a handshake this hook never performs.';
  }
  if (state === 'flag-unreadable') {
    return "open the hook's settings and read the SSL verification setting by hand.";
  }
  if (state === 'no-url') {
    return 'set a URL on this hook, or delete it. A hook with no endpoint ' +
      'delivers nothing and hides in every audit that counts hooks.';
  }
  return "nothing. GitHub verifies this endpoint's certificate.";
}

/** Counts across every hook read. Pure. */
export function summarize(hooks, nowMs = null) {
  const rows = (hooks ?? []).filter((h) => h && typeof h === 'object');
  const states = rows.map((h) => classify(h, nowMs)[0]);
  const count = (name) => states.filter((s) => s === name).length;
  return {
    total: rows.length,
    verification_off: count('verification-off'),
    verified: count('verified'),
    plaintext: count('not-applicable'),
    unreadable: count('flag-unreadable') + count('no-url'),
  };
}

async function get(token, path) {
  const res = await fetch(path.startsWith('/') ? API + path : path, {
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      'User-Agent': UA,
    },
  });
  let body = null;
  try { body = await res.json(); } catch { body = null; }
  return { status: res.status, body };
}

async function listHooks(token, scope) {
  const path = scope.startsWith('@')
    ? `/orgs/${scope.slice(1)}/hooks?per_page=100`
    : `/repos/${scope}/hooks?per_page=100`;
  const { status, body } = await get(token, path);
  if (status !== 200 || !Array.isArray(body)) {
    console.error(`GET ${path} returned ${status}`);
    return [];
  }
  return body;
}

async function main() {
  const token = process.env.GITHUB_TOKEN;
  if (!token) {
    console.error('set GITHUB_TOKEN to a read-only token that can see the ' +
      "repository's hooks");
    process.exitCode = 2;
    return;
  }
  const scopes = process.argv.slice(2);
  if (scopes.length === 0) {
    console.error('pass at least one owner/name, or @org for an organization');
    process.exitCode = 2;
    return;
  }

  const now = Date.now();
  const findings = [];
  for (const scope of scopes) {
    const label = scope.startsWith('@') ? scope.slice(1) : scope;
    const hooks = await listHooks(token, scope);
    const stats = summarize(hooks, now);
    console.log(`${stats.total} hook(s) on ${label}`);
    for (const hook of hooks) {
      const [state, detail] = classify(hook, now);
      findings.push({
        scope: label,
        hook_id: hook.id,
        state,
        detail,
        url: endpoint(hook),
        secret_set: hasSecret(hook),
      });
      if (state !== 'verified') {
        console.log(`${state}: ${detail}`);
        console.log(`repair: ${repair(state, hook)}`);
      }
    }
    if (stats.verification_off === 0) {
      console.log(`verified: no hook on ${label} has certificate verification disabled`);
    }
  }

  console.log(JSON.stringify({ scopes, findings }, null, 2));
  process.exitCode = findings.some((f) => f.state === 'verification-off') ? 1 : 0;
}

// Only run when invoked directly, so importing this module from the test file
// does not execute main() and set an exit code that fails the suite even as
// every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The first test is the one that decides whether anybody keeps using the tool: <code>&quot;0&quot;</code> is a non-empty string, so a truthy test on <code>insecure_ssl</code> marks every correctly configured hook as insecure and the second run never happens. The rest pin the other spellings the field arrives in, the refusal to guess when it is absent, the boundary with the plaintext note &mdash; an <code>http://</code> hook is handed over rather than counted &mdash; the age being reported as a lower bound, and a repair that describes a whole config because a single-field update writes the masked secret back.",
"test_py_file": "test_github_hook_ssl_verification.py",
"test_py": '''from datetime import datetime, timezone

from github_hook_ssl_verification import (
    classify, endpoint, has_secret, insecure_flag, repair, scheme_of,
    summarize, unchanged_days,
)

NOW = datetime(2026, 8, 30, 12, 0, 0, tzinfo=timezone.utc)

OPEN = {"id": 1, "updated_at": "2025-09-23T08:00:00Z",
        "config": {"url": "https://hooks.acme.io/github", "insecure_ssl": "1",
                   "secret": "********", "content_type": "json"}}
SAFE = {"id": 2, "updated_at": "2026-08-01T08:00:00Z",
        "config": {"url": "https://hooks.acme.io/github", "insecure_ssl": "0",
                   "secret": "********", "content_type": "json"}}
PLAIN = {"id": 3, "updated_at": "2026-08-01T08:00:00Z",
         "config": {"url": "http://hooks.acme.io/github", "insecure_ssl": "0"}}


def test_the_string_zero_is_not_a_finding():
    assert insecure_flag(SAFE) == "off"
    assert insecure_flag({"config": {"insecure_ssl": 0}}) == "off"
    assert insecure_flag({"config": {"insecure_ssl": False}}) == "off"
    assert classify(SAFE, NOW)[0] == "verified"


def test_every_spelling_of_on_is_on():
    assert insecure_flag(OPEN) == "on"
    assert insecure_flag({"config": {"insecure_ssl": 1}}) == "on"
    assert insecure_flag({"config": {"insecure_ssl": True}}) == "on"
    assert insecure_flag({"config": {"insecure_ssl": "true"}}) == "on"


def test_an_absent_flag_is_unknown_rather_than_either_answer():
    assert insecure_flag({"config": {"url": "https://x.example"}}) == "unknown"
    assert insecure_flag({"config": {"insecure_ssl": "maybe"}}) == "unknown"
    assert insecure_flag({"id": 4}) == "unknown"
    state, detail = classify({"id": 4, "config": {"url": "https://x.example"}}, NOW)
    assert state == "flag-unreadable"
    assert "rather than assuming" in detail


def test_a_plaintext_hook_is_handed_to_the_other_question():
    state, detail = classify(PLAIN, NOW)
    assert state == "not-applicable"
    assert "the scheme is" in detail
    assert "behind HTTPS" in repair(state, PLAIN)


def test_the_finding_names_the_endpoint_and_dates_it_as_a_lower_bound():
    state, detail = classify(OPEN, NOW)
    assert state == "verification-off"
    assert "https://hooks.acme.io/github" in detail
    assert "at least 341 day(s)" in detail
    assert unchanged_days(OPEN, NOW) == 341


def test_a_hook_with_no_url_is_its_own_state():
    state, _ = classify({"id": 5, "config": {"insecure_ssl": "1"}}, NOW)
    assert state == "no-url"


def test_the_printed_url_drops_any_query_string():
    hook = {"id": 6, "config": {"url": "https://hooks.acme.io/github?token=abc123"}}
    assert endpoint(hook) == "https://hooks.acme.io/github"
    assert scheme_of(hook) == "https"
    assert scheme_of({"config": {"url": "not-a-url"}}) == ""


def test_the_repair_is_a_whole_config_not_one_field():
    text = repair("verification-off", OPEN)
    assert "full" in text
    assert "replaced, not merged" in text
    assert "new secret" in text


def test_a_hook_with_no_secret_gets_told_to_set_one():
    hookless = {"id": 7, "config": {"url": "https://x.example", "insecure_ssl": "1"}}
    assert not has_secret(hookless)
    assert "since this hook has none" in repair("verification-off", hookless)


def test_the_summary_keeps_the_plaintext_hooks_out_of_the_finding_count():
    stats = summarize([OPEN, SAFE, PLAIN], NOW)
    assert stats == {"total": 3, "verification_off": 1, "verified": 1,
                     "plaintext": 1, "unreadable": 0}


def test_an_unparseable_timestamp_produces_no_age():
    assert unchanged_days({"updated_at": "whenever"}, NOW) is None
    assert unchanged_days({"id": 1}, NOW) is None
''',
"test_js_file": "github-hook-ssl-verification.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  classify, endpoint, hasSecret, insecureFlag, repair, schemeOf,
  summarize, unchangedDays,
} from './github-hook-ssl-verification.mjs';

const NOW = Date.parse('2026-08-30T12:00:00Z');

const OPEN = {
  id: 1, updated_at: '2025-09-23T08:00:00Z',
  config: {
    url: 'https://hooks.acme.io/github', insecure_ssl: '1',
    secret: '********', content_type: 'json',
  },
};
const SAFE = {
  id: 2, updated_at: '2026-08-01T08:00:00Z',
  config: {
    url: 'https://hooks.acme.io/github', insecure_ssl: '0',
    secret: '********', content_type: 'json',
  },
};
const PLAIN = {
  id: 3, updated_at: '2026-08-01T08:00:00Z',
  config: { url: 'http://hooks.acme.io/github', insecure_ssl: '0' },
};

test('the string zero is not a finding', () => {
  assert.equal(insecureFlag(SAFE), 'off');
  assert.equal(insecureFlag({ config: { insecure_ssl: 0 } }), 'off');
  assert.equal(insecureFlag({ config: { insecure_ssl: false } }), 'off');
  assert.equal(classify(SAFE, NOW)[0], 'verified');
});

test('every spelling of on is on', () => {
  assert.equal(insecureFlag(OPEN), 'on');
  assert.equal(insecureFlag({ config: { insecure_ssl: 1 } }), 'on');
  assert.equal(insecureFlag({ config: { insecure_ssl: true } }), 'on');
  assert.equal(insecureFlag({ config: { insecure_ssl: 'true' } }), 'on');
});

test('an absent flag is unknown rather than either answer', () => {
  assert.equal(insecureFlag({ config: { url: 'https://x.example' } }), 'unknown');
  assert.equal(insecureFlag({ config: { insecure_ssl: 'maybe' } }), 'unknown');
  assert.equal(insecureFlag({ id: 4 }), 'unknown');
  const [state, detail] = classify({ id: 4, config: { url: 'https://x.example' } }, NOW);
  assert.equal(state, 'flag-unreadable');
  assert.match(detail, /rather than assuming/);
});

test('a plaintext hook is handed to the other question', () => {
  const [state, detail] = classify(PLAIN, NOW);
  assert.equal(state, 'not-applicable');
  assert.match(detail, /the scheme is/);
  assert.match(repair(state, PLAIN), /behind HTTPS/);
});

test('the finding names the endpoint and dates it as a lower bound', () => {
  const [state, detail] = classify(OPEN, NOW);
  assert.equal(state, 'verification-off');
  assert.match(detail, /https:\\/\\/hooks\\.acme\\.io\\/github/);
  assert.match(detail, /at least 341 day\\(s\\)/);
  assert.equal(unchangedDays(OPEN, NOW), 341);
});

test('a hook with no url is its own state', () => {
  const [state] = classify({ id: 5, config: { insecure_ssl: '1' } }, NOW);
  assert.equal(state, 'no-url');
});

test('the printed url drops any query string', () => {
  const hook = { id: 6, config: { url: 'https://hooks.acme.io/github?token=abc123' } };
  assert.equal(endpoint(hook), 'https://hooks.acme.io/github');
  assert.equal(schemeOf(hook), 'https');
  assert.equal(schemeOf({ config: { url: 'not-a-url' } }), '');
});

test('the repair is a whole config not one field', () => {
  const text = repair('verification-off', OPEN);
  assert.match(text, /full/);
  assert.match(text, /replaced, not merged/);
  assert.match(text, /new secret/);
});

test('a hook with no secret gets told to set one', () => {
  const hookless = { id: 7, config: { url: 'https://x.example', insecure_ssl: '1' } };
  assert.ok(!hasSecret(hookless));
  assert.match(repair('verification-off', hookless), /since this hook has none/);
});

test('the summary keeps the plaintext hooks out of the finding count', () => {
  assert.deepEqual(summarize([OPEN, SAFE, PLAIN], NOW), {
    total: 3, verification_off: 1, verified: 1, plaintext: 1, unreadable: 0,
  });
});

test('an unparseable timestamp produces no age', () => {
  assert.equal(unchangedDays({ updated_at: 'whenever' }, NOW), null);
  assert.equal(unchangedDays({ id: 1 }, NOW), null);
});
''',
"faq": [
 ("If the connection is still encrypted, what exactly is the risk?",
  "Impersonation rather than eavesdropping. TLS gives you two things, confidentiality and identity, and this flag throws away the second while keeping the first. GitHub will complete a handshake with any certificate that is presented, so an endpoint that manages to be answered instead of yours - through a stale DNS record somebody else registered, a compromised proxy, an internal resolver pointed at the wrong place - receives your payloads in full. It also receives them correctly signed, which means it can replay them at your real receiver later and they will verify."),
 ("Why does a truthy check on insecure_ssl not work?",
  "Because the value is a string and both of its values are non-empty. \"0\" and \"1\" are equally truthy in Python, JavaScript, Ruby and everything else you might write the check in, so a naive test flags every hook in the organization including the correctly configured ones. That is worse than not checking, because the first run produces a page of false positives and the tool gets ignored. Parse the value into three states and report the third rather than folding an unreadable field into either answer."),
 ("The certificate is genuinely internal. Can we leave it off?",
  "Not as a permanent arrangement, because the exemption is invisible and it outlives the reason for it every time. If GitHub has to reach the endpoint, the endpoint is on the public internet and can have a publicly trusted certificate - that is a free and automated thing now. If it genuinely cannot, put a small gateway in front of it that terminates a real certificate and forwards inside your network, and keep verification on for the hop GitHub makes."),
 ("Do we really have to rotate the secret?",
  "The secret was never sent in the payload, so it was not disclosed by this. What was exposed is every payload signed with it, to anything that succeeded in being answered instead of your endpoint during the window - and those payloads replay cleanly. Rotating closes that, and it is cheap. If the flag was on for a week on a staging hook nobody could reach, use your judgement; if it has been on for eleven months on a production hook, rotate."),
 ("Why does the script print a whole config instead of one field?",
  "Because a webhook's config is replaced rather than merged, and config.secret comes back masked as asterisks. The obvious repair - read the config, change insecure_ssl, write it back - sends the mask as the secret, so the hook's secret becomes a literal row of asterisks or is dropped, signature verification breaks on the next delivery, and somebody reverts the change believing the flag was load bearing. Send the URL, the content type, the flag and a freshly generated secret together."),
],
"related": [
 ("/github/webhook-http-url/", "A webhook posting to a plain http:// URL"),
 ("/github/webhook-no-secret/", "A webhook with no secret sends no signature"),
 ("/github/webhook-deliveries-failing/", "Deliveries failing where nobody reads the log"),
],
"citations": [CITE_REPO_HOOKS, CITE_TROUBLESHOOT, CITE_CREATING, CITE_ORG_HOOKS],
},

{
"slug": "webhook-http-url",
"title": "The webhook posts your payloads to an http:// URL",
"description": "GitHub delivers to http:// if you ask it to. Payloads and their signature cross the network in the clear, and insecure_ssl still reads a reassuring 0.",
"h1": "the webhook posts your payloads to an http:// URL",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github webhook http url not https",
             "github webhook plaintext payload",
             "webhook url insecure scheme",
             "github webhook localhost url",
             "webhook payload sent in the clear"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The hook works. It has a secret, it is subscribed to the right events, the delivery log is a column of <code>200</code>s, and <code>insecure_ssl</code> reads <code>0</code>, which is the field the last security review looked at. The URL is <code>http://hooks.internal.acme.io/github</code>, so every payload and the signature that authenticates it have been crossing the network as plain text since the day it was created.",
"short_answer": """<p>Read <code>GET /repos/{owner}/{repo}/hooks</code> and <code>GET /orgs/{org}/hooks</code>, take <code>config.url</code>, and look at the scheme. Anything that is not <code>https</code> is the finding. GitHub will deliver to <code>http://</code> without complaint, and nothing in the UI, the delivery log or the API warns about it.</p>
<p>The detail that keeps this hidden is that <code>insecure_ssl</code> stays <code>"0"</code> on a plaintext hook, because there is no certificate to verify when there is no TLS. So the field a reviewer checks says the reassuring thing while the transport is completely open. A signature does not help either: it proves the payload came from GitHub, it does not conceal a single byte of it, and it travels in a header of the same cleartext request.</p>""",
"problem": """<p>Almost every one of these starts as a hostname that was internal when it was written. Somebody points a hook at a box inside the network during a migration, on a plain port because there is no certificate for an internal name and getting one is a week of someone else's time. Then the box moves behind a public load balancer, or the DNS name becomes externally resolvable, or the whole thing gets lifted into a cloud account, and the URL survives every one of those moves untouched, because it never stopped working.</p>
<p>What makes it stay hidden is that all the usual instruments read green. The delivery log is full of successes, since plaintext delivery succeeds perfectly well. The secret is set, so the payloads are signed and the receiver's verification passes. <code>insecure_ssl</code> is <code>"0"</code>, which is the value everyone is looking for, and it is <code>"0"</code> precisely because GitHub is not verifying a certificate it was never offered. Three separate healthy-looking signals, one of them actively misleading.</p>
<p>The other family is the reverse: an <code>http://</code> URL pointing at <code>localhost</code>, a <code>192.168.</code> address or a tunnel hostname left over from development. That one is not a confidentiality problem, because GitHub cannot reach it at all &mdash; it is a hook that has been failing or timing out since it was created, sitting in a list of hooks that somebody is going to count as working. The script separates the two, because one needs a certificate and the other needs deleting.</p>""",
"why": """<p><strong>What crosses the wire is the repository, not just an event name.</strong> Webhook payloads are large and specific: commit messages, branch names, file paths, the full body of an issue or a pull request comment, the login of everyone involved. On a private repository that is the private repository, arriving in readable JSON at every device on the path. The signature is in a header of the same request and is equally readable.</p>
<p><strong>The signature proves origin and provides nothing else.</strong> This is the confusion worth naming, because it is the reason people are comfortable. HMAC gives you integrity and authenticity: nobody can alter the payload or forge one without the secret. It gives you no confidentiality at all. An observer reads the whole payload and, separately, can replay the entire request verbatim at your receiver, signature included, as many times as they like.</p>
<p><strong><code>insecure_ssl</code> is not a safety net.</strong> It governs certificate verification during a TLS handshake, and an <code>http://</code> hook never performs one, so the field sits at its default and means nothing. A hook can therefore pass an audit that checks the flag while being the least protected hook in the organization. That is why this note reads the scheme and the neighbouring note reads the flag, and why each hands the other its own cases rather than counting them.</p>
<p><strong>An unreachable URL is a different finding with a similar shape.</strong> <code>http://localhost:3000/hooks</code> is not leaking anything, because GitHub's delivery infrastructure cannot route to your laptop. It is a dead hook, and it will show as connection errors or timeouts in the delivery log. Reporting it as a confidentiality problem wastes the reader's afternoon; reporting it as a hook that has never worked is useful.</p>
<p><strong>The repair includes a rotation, and the URL is not the only thing to send.</strong> The secret has been signing payloads on an open channel, so change it. And because a webhook's config is replaced rather than merged, the update carries the new URL, the content type and the new secret together &mdash; a partial write here is the standard way to end up with a hook whose secret is the literal mask it was read back as.</p>""",
"steps": [
 {"h": "Collect the URLs from every scope",
  "body": """<p>Repository hooks, organization hooks and a GitHub App's own hook are three independent places a URL can live. Read all of them, because the plaintext one is almost never the hook anybody remembers creating: it is the one added during a migration by somebody who has since changed teams.</p>"""},
 {"h": "Parse the scheme, and normalise before you judge",
  "body": """<p>Lower-case it and take what precedes <code>://</code>. A URL with no scheme at all, or one with something unexpected, is its own answer rather than being folded into either the safe or the unsafe pile. Strip any query string and any <code>user:pass@</code> before printing, because this script prints its findings and those are the two places a credential hides in a URL.</p>"""},
 {"h": "Split leaking from unreachable",
  "body": """<p>Check whether the host is a loopback address, a private range, a link-local address or an obviously local name. A plaintext hook on a routable host is exposing payloads; a plaintext hook on <code>localhost</code> is a hook that has never delivered anything. Same field, different finding, different repair.</p>"""},
 {"h": "Notice when the compliant-looking field is the misleading one",
  "body": """<p>A hook with an <code>http://</code> URL and <code>insecure_ssl</code> at <code>"0"</code> reads as compliant on the field most checklists sample. The script calls that combination out by name, because it is the specific reason this problem survives audits that were genuinely performed.</p>"""},
 {"h": "Move it behind HTTPS, then rotate",
  "body": """<p>Put the receiver behind a certificate that chains to a public root, update the hook with the full config &mdash; new URL, content type, new secret &mdash; and confirm the next delivery succeeds. Rotate rather than reuse: that secret has been travelling in cleartext next to the payloads it signs.</p>"""},
],
"verify": """<p>The re-read shows an <code>https</code> scheme on every hook, and the delivery log continues without a gap.</p>
<pre><code class="language-bash">GITHUB_TOKEN=$GH_READONLY python3 github_hook_transport.py --repo acme-corp/api --org acme-corp
# 3 hook(s) on acme-corp/api, 2 hook(s) on acme-corp
# plaintext: hook 512334455 posts to http://hooks.internal.acme.io/github over
# an unencrypted connection. insecure_ssl reads "0", which is what a hook with
# no TLS at all always reads.
# repair: move the receiver behind HTTPS, then send the hook's full config with
# the new URL, the content type and a new secret. Rotate: that secret has been
# signing payloads on an open channel.
# plaintext-unreachable: hook 512334999 posts to http://localhost:3000/hooks,
# which GitHub cannot route to. This hook has never delivered anything.

# after the change
# encrypted: hook 512334455 posts to https://hooks.acme.io/github</code></pre>""",
"code_intro": "One GET per scope and one field, and the interesting part is everything the script refuses to conflate. A plaintext hook on a routable host is leaking payloads; the same scheme on a loopback or private address is a hook GitHub has never been able to reach, which is a different sentence and a different repair. An <code>https</code> hook with certificate verification disabled belongs to the neighbouring note and is handed over rather than counted here. And one small pure function exists only to name the trap: a hook whose <code>insecure_ssl</code> reads <code>0</code> while its URL has no TLS at all, which is how this survives an audit that was actually carried out.",
"py_file": "github_hook_transport.py",
"py": '''"""Find webhooks that deliver over plaintext HTTP, and say which ones leak.

Read only. Every call is a GET. Changing a hook's URL is a write and this
script does not do it: it prints the change, as a full config rather than a
single field, because a webhook's config is replaced rather than merged and the
secret you read back is a mask.

GitHub will deliver to an http:// URL without complaint. The payload and the
signature header that authenticates it both cross the network as plain text. A
signature proves the payload came from GitHub; it conceals nothing and it can
be replayed by anyone who saw it.

Two things that look the same in this field are kept apart:

    http:// on a routable host      payloads are readable in transit
    http:// on a private address    GitHub cannot route there at all, so this
                                    hook has never delivered anything

And one thing that hides here is named: insecure_ssl reads "0" on a plaintext
hook, because there is no certificate to verify when there is no TLS, so the
field an audit samples reports the reassuring value.

The secret is never printed, and neither is any query string or userinfo in a
hook URL.

Environment:

    GITHUB_TOKEN    a read-only token that can see the repository's hooks
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_hook_transport")

API = "https://api.github.com"
UA = "github-hook-transport/1.0"

# Names that never resolve to somewhere GitHub can deliver.
LOCAL_NAMES = ("localhost", "localhost.localdomain", "ip6-localhost")
LOCAL_SUFFIXES = (".localhost", ".local", ".internal", ".lan", ".home.arpa",
                  ".localdomain")

# States that mean payloads are readable in transit.
LEAKING = ("plaintext",)


def config_of(hook):
    """The config object of a hook, or an empty dict. Pure."""
    if not isinstance(hook, dict):
        return {}
    config = hook.get("config")
    return config if isinstance(config, dict) else {}


def raw_url(hook):
    """The configured URL, trimmed, or "". Pure."""
    return str(config_of(hook).get("url") or "").strip()


def safe_url(url):
    """A URL with its query string and any userinfo removed. Pure.

    This script prints URLs, and those are the two places a credential hides in
    one: a token in a query parameter and a user:pass pair before the host.
    """
    text = str(url or "").strip()
    if not text:
        return ""
    text = text.split("?", 1)[0].split("#", 1)[0]
    if "://" in text:
        scheme, rest = text.split("://", 1)
    else:
        scheme, rest = "", text
    if "@" in rest:
        rest = rest.rsplit("@", 1)[1]
        rest = "<redacted>@" + rest
    return ("%s://%s" % (scheme, rest)) if scheme else rest


def scheme_of(url):
    """The lower-cased scheme of a URL, or "". Pure."""
    text = str(url or "").strip()
    return text.split("://", 1)[0].lower() if "://" in text else ""


def host_of(url):
    """The lower-cased host of a URL, without port or userinfo. Pure."""
    text = str(url or "").strip()
    rest = text.split("://", 1)[1] if "://" in text else text
    rest = rest.split("/", 1)[0]
    if "@" in rest:
        rest = rest.rsplit("@", 1)[1]
    if rest.startswith("["):
        return rest[1:].split("]", 1)[0].lower()
    return rest.split(":", 1)[0].lower()


def is_private_host(host):
    """Whether a host is somewhere GitHub's delivery network cannot reach. Pure.

    Deliberately a name and address test rather than a DNS lookup. A resolver
    inside your network answers differently from GitHub's, so resolving here
    would produce an answer about the wrong network, and a script that makes
    DNS queries for every hook in an organization is a different kind of tool.
    """
    name = str(host or "").strip().lower().strip(".")
    if not name:
        return False
    if name in LOCAL_NAMES or name.endswith(LOCAL_SUFFIXES):
        return True
    if name in ("::1", "0:0:0:0:0:0:0:1"):
        return True
    if name.startswith(("fd", "fc", "fe80:")) and ":" in name:
        return True
    parts = name.split(".")
    if len(parts) == 4 and all(p.isdigit() and len(p) <= 3 for p in parts):
        octets = [int(p) for p in parts]
        if any(o > 255 for o in octets):
            return False
        if octets[0] in (0, 127, 10):
            return True
        if octets[0] == 192 and octets[1] == 168:
            return True
        if octets[0] == 172 and 16 <= octets[1] <= 31:
            return True
        if octets[0] == 169 and octets[1] == 254:
            return True
    return False


def insecure_ssl_reads(hook):
    """The insecure_ssl value as text, or "" when absent. Pure.

    Read as text on purpose. This script does not interpret the flag - that is
    the certificate-verification question - it only needs to report what an
    audit sampling the field would have seen.
    """
    config = config_of(hook)
    if "insecure_ssl" not in config:
        return ""
    return str(config["insecure_ssl"]).strip().lower()


def looks_compliant(hook):
    """Whether a plaintext hook reads as safe on the field audits sample. Pure.

    The whole reason this problem survives a review that was genuinely carried
    out: insecure_ssl is "0" on a hook with no TLS, because there is no
    certificate to verify.
    """
    return (scheme_of(raw_url(hook)) not in ("https", "")
            and insecure_ssl_reads(hook) in ("0", "false"))


def has_secret(hook):
    """Whether the hook has a secret set. Pure. The value is never read."""
    return "secret" in config_of(hook)


def classify(hook):
    """Sort one hook into a state and a sentence. Pure."""
    ident = "hook %s" % (hook.get("id", "?") if isinstance(hook, dict) else "?")
    url = raw_url(hook)
    scheme = scheme_of(url)
    if not url or not scheme:
        return ("no-scheme",
                "%s has no usable URL in its config, so nothing can be said "
                "about how it delivers." % ident)
    if scheme == "https":
        if insecure_ssl_reads(hook) in ("1", "true"):
            return ("encrypted-unverified",
                    "%s posts to %s over TLS, but with certificate "
                    "verification disabled. The transport is encrypted and "
                    "unauthenticated, which is a different question from this "
                    "one." % (ident, safe_url(url)))
        return ("encrypted",
                "%s posts to %s over TLS." % (ident, safe_url(url)))
    if scheme != "http":
        return ("unknown-scheme",
                "%s posts to a %s:// URL, which is not a scheme GitHub "
                "delivers to. Read the URL by hand." % (ident, scheme))
    if is_private_host(host_of(url)):
        return ("plaintext-unreachable",
                "%s posts to %s, which GitHub cannot route to. This hook has "
                "never delivered anything, and it is not leaking payloads "
                "either." % (ident, safe_url(url)))
    suffix = (" insecure_ssl reads \\"%s\\", which is what a hook with no TLS "
              "at all always reads." % insecure_ssl_reads(hook)
              if looks_compliant(hook) else "")
    return ("plaintext",
            "%s posts to %s over an unencrypted connection.%s"
            % (ident, safe_url(url), suffix))


def repair(state, hook):
    """The change to make, printed as a whole config. Pure."""
    if state == "plaintext":
        rotate = (" and a new secret. Rotate: that secret has been signing "
                  "payloads on an open channel." if has_secret(hook)
                  else " and a secret, since this hook has none.")
        return ("move the receiver behind HTTPS, then send the hook's full "
                "config with the new URL, the content type%s The config is "
                "replaced, not merged, and the secret you read back is a mask."
                % rotate)
    if state == "plaintext-unreachable":
        return ("delete this hook, or point it at an endpoint GitHub can "
                "reach over HTTPS. Its delivery log will be connection errors "
                "and timeouts for as far back as the retention window goes.")
    if state == "encrypted-unverified":
        return ("this is the certificate-verification question rather than "
                "the transport one. Fix the certificate, then set insecure_ssl "
                "back to \\"0\\" as part of a full config update.")
    if state in ("no-scheme", "unknown-scheme"):
        return ("read the hook's URL by hand. A hook GitHub cannot parse a "
                "scheme from is not delivering anything.")
    return "nothing. This hook delivers over TLS."


def summarize(hooks):
    """Counts across every hook read. Pure."""
    rows = [h for h in (hooks or []) if isinstance(h, dict)]
    states = [classify(h)[0] for h in rows]
    return {"total": len(rows),
            "plaintext": states.count("plaintext"),
            "unreachable": states.count("plaintext-unreachable"),
            "encrypted": states.count("encrypted") + states.count("encrypted-unverified"),
            "unreadable": states.count("no-scheme") + states.count("unknown-scheme")}


def get(session, path):
    """One GET. Returns (status, json-or-None)."""
    url = API + path if path.startswith("/") else path
    r = session.get(url, timeout=30)
    try:
        body = r.json()
    except ValueError:
        body = None
    return r.status_code, body


def list_hooks(session, scope):
    """Hooks for a repo (owner/name) or an org (@org). Read only."""
    path = ("/orgs/%s/hooks?per_page=100" % scope[1:] if scope.startswith("@")
            else "/repos/%s/hooks?per_page=100" % scope)
    status, body = get(session, path)
    if status != 200 or not isinstance(body, list):
        log.error("GET %s returned %d", path, status)
        return []
    return body


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", action="append", default=[],
                    help="owner/name; repeatable")
    ap.add_argument("--org", action="append", default=[],
                    help="organization login; repeatable")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_TOKEN to a read-only token that can see the "
                  "repository's hooks")
        return 2
    scopes = list(args.repo) + ["@" + o for o in args.org]
    if not scopes:
        log.error("pass at least one --repo owner/name or --org login")
        return 2

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": UA,
    })

    findings = []
    for scope in scopes:
        label = scope[1:] if scope.startswith("@") else scope
        hooks = list_hooks(session, scope)
        stats = summarize(hooks)
        log.info("%d hook(s) on %s", stats["total"], label)
        for hook in hooks:
            state, detail = classify(hook)
            findings.append({"scope": label, "hook_id": hook.get("id"),
                             "state": state, "detail": detail,
                             "url": safe_url(raw_url(hook)),
                             "looks_compliant": looks_compliant(hook)})
            if state != "encrypted":
                log.info("%s: %s", state, detail)
                log.info("repair: %s", repair(state, hook))
        if stats["plaintext"] == 0:
            log.info("encrypted: no hook on %s delivers over plaintext HTTP "
                     "to a routable host", label)

    print(json.dumps({"scopes": scopes, "findings": findings},
                     indent=2, default=str))
    return 1 if any(f["state"] in LEAKING for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-hook-transport.mjs",
"js": '''/**
 * Find webhooks that deliver over plaintext HTTP, and say which ones leak.
 *
 * Read only. Every call is a GET. Changing a hook's URL is a write and is not
 * done here: the script prints the change, as a full config rather than a
 * single field, because a webhook's config is replaced rather than merged and
 * the secret you read back is a mask.
 *
 * Two things that look the same in this field are kept apart: http:// on a
 * routable host means payloads are readable in transit, while http:// on a
 * private address means GitHub cannot route there at all and the hook has
 * never delivered anything.
 *
 * The secret is never printed, and neither is any query string or userinfo in
 * a hook URL.
 *
 * Environment:
 *   GITHUB_TOKEN   a read-only token that can see the repository's hooks
 *
 * Usage:
 *   node github-hook-transport.mjs acme-corp/api @acme-corp
 */
const API = 'https://api.github.com';
const UA = 'github-hook-transport/1.0';

const LOCAL_NAMES = ['localhost', 'localhost.localdomain', 'ip6-localhost'];
const LOCAL_SUFFIXES = ['.localhost', '.local', '.internal', '.lan',
  '.home.arpa', '.localdomain'];

/** States that mean payloads are readable in transit. */
export const LEAKING = ['plaintext'];

/** The config object of a hook, or an empty object. Pure. */
export function configOf(hook) {
  if (!hook || typeof hook !== 'object') return {};
  const config = hook.config;
  return config && typeof config === 'object' ? config : {};
}

/** The configured URL, trimmed, or ''. Pure. */
export function rawUrl(hook) {
  return String(configOf(hook).url ?? '').trim();
}

/** A URL with its query string and any userinfo removed. Pure. */
export function safeUrl(url) {
  let text = String(url ?? '').trim();
  if (!text) return '';
  text = text.split('?')[0].split('#')[0];
  let scheme = '';
  let rest = text;
  if (text.includes('://')) {
    const idx = text.indexOf('://');
    scheme = text.slice(0, idx);
    rest = text.slice(idx + 3);
  }
  if (rest.includes('@')) {
    rest = `<redacted>@${rest.slice(rest.lastIndexOf('@') + 1)}`;
  }
  return scheme ? `${scheme}://${rest}` : rest;
}

/** The lower-cased scheme of a URL, or ''. Pure. */
export function schemeOf(url) {
  const text = String(url ?? '').trim();
  return text.includes('://') ? text.slice(0, text.indexOf('://')).toLowerCase() : '';
}

/** The lower-cased host of a URL, without port or userinfo. Pure. */
export function hostOf(url) {
  const text = String(url ?? '').trim();
  let rest = text.includes('://') ? text.slice(text.indexOf('://') + 3) : text;
  rest = rest.split('/')[0];
  if (rest.includes('@')) rest = rest.slice(rest.lastIndexOf('@') + 1);
  if (rest.startsWith('[')) return rest.slice(1).split(']')[0].toLowerCase();
  return rest.split(':')[0].toLowerCase();
}

/**
 * Whether a host is somewhere GitHub's delivery network cannot reach. Pure.
 * A name and address test rather than a DNS lookup: a resolver inside your
 * network answers differently from GitHub's.
 */
export function isPrivateHost(host) {
  const name = String(host ?? '').trim().toLowerCase().replace(/^\\.+|\\.+$/g, '');
  if (!name) return false;
  if (LOCAL_NAMES.includes(name)) return true;
  if (LOCAL_SUFFIXES.some((s) => name.endsWith(s))) return true;
  if (name === '::1' || name === '0:0:0:0:0:0:0:1') return true;
  if (name.includes(':') && (name.startsWith('fd') || name.startsWith('fc') || name.startsWith('fe80:'))) {
    return true;
  }
  const parts = name.split('.');
  if (parts.length === 4 && parts.every((p) => /^[0-9]{1,3}$/.test(p))) {
    const o = parts.map(Number);
    if (o.some((n) => n > 255)) return false;
    if ([0, 127, 10].includes(o[0])) return true;
    if (o[0] === 192 && o[1] === 168) return true;
    if (o[0] === 172 && o[1] >= 16 && o[1] <= 31) return true;
    if (o[0] === 169 && o[1] === 254) return true;
  }
  return false;
}

/** The insecure_ssl value as text, or '' when absent. Pure. */
export function insecureSslReads(hook) {
  const config = configOf(hook);
  if (!('insecure_ssl' in config)) return '';
  return String(config.insecure_ssl).trim().toLowerCase();
}

/** Whether a plaintext hook reads as safe on the field audits sample. Pure. */
export function looksCompliant(hook) {
  const scheme = schemeOf(rawUrl(hook));
  return scheme !== 'https' && scheme !== '' && ['0', 'false'].includes(insecureSslReads(hook));
}

/** Whether the hook has a secret set. Pure. The value is never read. */
export function hasSecret(hook) {
  return 'secret' in configOf(hook);
}

/** Sort one hook into a state and a sentence. Pure. */
export function classify(hook) {
  const ident = `hook ${(hook && typeof hook === 'object' ? hook.id : null) ?? '?'}`;
  const url = rawUrl(hook);
  const scheme = schemeOf(url);
  if (!url || !scheme) {
    return ['no-scheme',
      `${ident} has no usable URL in its config, so nothing can be said about ` +
      'how it delivers.'];
  }
  if (scheme === 'https') {
    if (['1', 'true'].includes(insecureSslReads(hook))) {
      return ['encrypted-unverified',
        `${ident} posts to ${safeUrl(url)} over TLS, but with certificate ` +
        'verification disabled. The transport is encrypted and ' +
        'unauthenticated, which is a different question from this one.'];
    }
    return ['encrypted', `${ident} posts to ${safeUrl(url)} over TLS.`];
  }
  if (scheme !== 'http') {
    return ['unknown-scheme',
      `${ident} posts to a ${scheme}:// URL, which is not a scheme GitHub ` +
      'delivers to. Read the URL by hand.'];
  }
  if (isPrivateHost(hostOf(url))) {
    return ['plaintext-unreachable',
      `${ident} posts to ${safeUrl(url)}, which GitHub cannot route to. This ` +
      'hook has never delivered anything, and it is not leaking payloads either.'];
  }
  const suffix = looksCompliant(hook)
    ? ` insecure_ssl reads "${insecureSslReads(hook)}", which is what a hook ` +
      'with no TLS at all always reads.'
    : '';
  return ['plaintext',
    `${ident} posts to ${safeUrl(url)} over an unencrypted connection.${suffix}`];
}

/** The change to make, printed as a whole config. Pure. */
export function repair(state, hook) {
  if (state === 'plaintext') {
    const rotate = hasSecret(hook)
      ? ' and a new secret. Rotate: that secret has been signing payloads on an open channel.'
      : ' and a secret, since this hook has none.';
    return 'move the receiver behind HTTPS, then send the hook\\'s full config ' +
      `with the new URL, the content type${rotate} The config is replaced, ` +
      'not merged, and the secret you read back is a mask.';
  }
  if (state === 'plaintext-unreachable') {
    return 'delete this hook, or point it at an endpoint GitHub can reach ' +
      'over HTTPS. Its delivery log will be connection errors and timeouts ' +
      'for as far back as the retention window goes.';
  }
  if (state === 'encrypted-unverified') {
    return 'this is the certificate-verification question rather than the ' +
      'transport one. Fix the certificate, then set insecure_ssl back to "0" ' +
      'as part of a full config update.';
  }
  if (state === 'no-scheme' || state === 'unknown-scheme') {
    return "read the hook's URL by hand. A hook GitHub cannot parse a scheme " +
      'from is not delivering anything.';
  }
  return 'nothing. This hook delivers over TLS.';
}

/** Counts across every hook read. Pure. */
export function summarize(hooks) {
  const rows = (hooks ?? []).filter((h) => h && typeof h === 'object');
  const states = rows.map((h) => classify(h)[0]);
  const count = (name) => states.filter((s) => s === name).length;
  return {
    total: rows.length,
    plaintext: count('plaintext'),
    unreachable: count('plaintext-unreachable'),
    encrypted: count('encrypted') + count('encrypted-unverified'),
    unreadable: count('no-scheme') + count('unknown-scheme'),
  };
}

async function get(token, path) {
  const res = await fetch(path.startsWith('/') ? API + path : path, {
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      'User-Agent': UA,
    },
  });
  let body = null;
  try { body = await res.json(); } catch { body = null; }
  return { status: res.status, body };
}

async function listHooks(token, scope) {
  const path = scope.startsWith('@')
    ? `/orgs/${scope.slice(1)}/hooks?per_page=100`
    : `/repos/${scope}/hooks?per_page=100`;
  const { status, body } = await get(token, path);
  if (status !== 200 || !Array.isArray(body)) {
    console.error(`GET ${path} returned ${status}`);
    return [];
  }
  return body;
}

async function main() {
  const token = process.env.GITHUB_TOKEN;
  if (!token) {
    console.error('set GITHUB_TOKEN to a read-only token that can see the ' +
      "repository's hooks");
    process.exitCode = 2;
    return;
  }
  const scopes = process.argv.slice(2);
  if (scopes.length === 0) {
    console.error('pass at least one owner/name, or @org for an organization');
    process.exitCode = 2;
    return;
  }

  const findings = [];
  for (const scope of scopes) {
    const label = scope.startsWith('@') ? scope.slice(1) : scope;
    const hooks = await listHooks(token, scope);
    const stats = summarize(hooks);
    console.log(`${stats.total} hook(s) on ${label}`);
    for (const hook of hooks) {
      const [state, detail] = classify(hook);
      findings.push({
        scope: label,
        hook_id: hook.id,
        state,
        detail,
        url: safeUrl(rawUrl(hook)),
        looks_compliant: looksCompliant(hook),
      });
      if (state !== 'encrypted') {
        console.log(`${state}: ${detail}`);
        console.log(`repair: ${repair(state, hook)}`);
      }
    }
    if (stats.plaintext === 0) {
      console.log(`encrypted: no hook on ${label} delivers over plaintext ` +
        'HTTP to a routable host');
    }
  }

  console.log(JSON.stringify({ scopes, findings }, null, 2));
  process.exitCode = findings.some((f) => LEAKING.includes(f.state)) ? 1 : 0;
}

// Only run when invoked directly, so importing this module from the test file
// does not execute main() and set an exit code that fails the suite even as
// every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Two separations carry this note and both are tested directly: a plaintext hook on a routable host is a leak, the same scheme on <code>localhost</code> or a private range is a hook that has never delivered, and neither is allowed to be reported as the other. After that, the small function whose only job is to name the trap &mdash; an <code>http://</code> hook whose <code>insecure_ssl</code> reads <code>0</code> &mdash; the URL redaction that has to survive both a query string and a <code>user:pass@</code> prefix, and the private-range boundaries where <code>172.15</code> and <code>172.32</code> are public and everything between them is not.",
"test_py_file": "test_github_hook_transport.py",
"test_py": '''from github_hook_transport import (
    classify, host_of, is_private_host, looks_compliant, repair, safe_url,
    scheme_of, summarize,
)

OPEN = {"id": 1, "config": {"url": "http://hooks.acme.io/github",
                            "insecure_ssl": "0", "secret": "********",
                            "content_type": "json"}}
LOCAL = {"id": 2, "config": {"url": "http://localhost:3000/hooks",
                             "insecure_ssl": "0"}}
TLS = {"id": 3, "config": {"url": "https://hooks.acme.io/github",
                           "insecure_ssl": "0", "secret": "********"}}
UNVERIFIED = {"id": 4, "config": {"url": "https://hooks.acme.io/github",
                                  "insecure_ssl": "1", "secret": "********"}}


def test_plaintext_on_a_routable_host_is_the_finding():
    state, detail = classify(OPEN)
    assert state == "plaintext"
    assert "unencrypted connection" in detail
    assert "signing payloads on an open channel" in repair(state, OPEN)


def test_plaintext_on_localhost_is_a_dead_hook_not_a_leak():
    state, detail = classify(LOCAL)
    assert state == "plaintext-unreachable"
    assert "never delivered anything" in detail
    assert "delete this hook" in repair(state, LOCAL)


def test_the_certificate_question_is_handed_to_the_other_note():
    state, detail = classify(UNVERIFIED)
    assert state == "encrypted-unverified"
    assert "different question" in detail
    assert classify(TLS)[0] == "encrypted"


def test_the_compliant_looking_field_is_named_in_the_finding():
    assert looks_compliant(OPEN)
    assert not looks_compliant(TLS)
    assert not looks_compliant(UNVERIFIED)
    assert "what a hook with no TLS at all always reads" in classify(OPEN)[1]


def test_a_plaintext_hook_with_no_insecure_ssl_field_is_still_the_finding():
    hook = {"id": 5, "config": {"url": "http://hooks.acme.io/github"}}
    assert not looks_compliant(hook)
    assert classify(hook)[0] == "plaintext"


def test_the_private_ranges_stop_where_they_should():
    assert is_private_host("10.0.0.1")
    assert is_private_host("192.168.1.7")
    assert is_private_host("172.16.0.1")
    assert is_private_host("172.31.255.254")
    assert is_private_host("127.0.0.1")
    assert is_private_host("169.254.169.254")
    assert not is_private_host("172.15.0.1")
    assert not is_private_host("172.32.0.1")
    assert not is_private_host("8.8.8.8")
    assert not is_private_host("hooks.acme.io")


def test_local_names_and_ipv6_loopback_count_as_unreachable():
    assert is_private_host("localhost")
    assert is_private_host("build-01.internal")
    assert is_private_host("printer.local")
    assert is_private_host("::1")
    assert is_private_host("fd00::1")
    assert not is_private_host("")
    assert not is_private_host(None)


def test_the_printed_url_survives_a_query_string_and_a_userinfo_prefix():
    assert safe_url("http://hooks.acme.io/github?token=abc123") == "http://hooks.acme.io/github"
    assert safe_url("https://bot:hunter2@hooks.acme.io/x") == "https://<redacted>@hooks.acme.io/x"
    assert "hunter2" not in safe_url("https://bot:hunter2@hooks.acme.io/x")
    assert safe_url("") == ""


def test_the_host_is_parsed_out_of_the_shapes_a_url_arrives_in():
    assert host_of("http://hooks.acme.io:8080/github") == "hooks.acme.io"
    assert host_of("http://bot:pw@10.0.0.4/hooks") == "10.0.0.4"
    assert host_of("http://[::1]:3000/hooks") == "::1"
    assert scheme_of("HTTP://hooks.acme.io") == "http"
    assert scheme_of("hooks.acme.io") == ""


def test_a_hook_with_no_url_is_not_counted_either_way():
    state, _ = classify({"id": 6, "config": {}})
    assert state == "no-scheme"
    assert classify({"id": 7, "config": {"url": "ftp://x.example/h"}})[0] == "unknown-scheme"


def test_the_summary_separates_leaking_from_unreachable():
    stats = summarize([OPEN, LOCAL, TLS, UNVERIFIED])
    assert stats == {"total": 4, "plaintext": 1, "unreachable": 1,
                     "encrypted": 2, "unreadable": 0}
''',
"test_js_file": "github-hook-transport.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  classify, hostOf, isPrivateHost, looksCompliant, repair, safeUrl,
  schemeOf, summarize,
} from './github-hook-transport.mjs';

const OPEN = {
  id: 1,
  config: {
    url: 'http://hooks.acme.io/github', insecure_ssl: '0',
    secret: '********', content_type: 'json',
  },
};
const LOCAL = {
  id: 2,
  config: { url: 'http://localhost:3000/hooks', insecure_ssl: '0' },
};
const TLS = {
  id: 3,
  config: { url: 'https://hooks.acme.io/github', insecure_ssl: '0', secret: '********' },
};
const UNVERIFIED = {
  id: 4,
  config: { url: 'https://hooks.acme.io/github', insecure_ssl: '1', secret: '********' },
};

test('plaintext on a routable host is the finding', () => {
  const [state, detail] = classify(OPEN);
  assert.equal(state, 'plaintext');
  assert.match(detail, /unencrypted connection/);
  assert.match(repair(state, OPEN), /signing payloads on an open channel/);
});

test('plaintext on localhost is a dead hook not a leak', () => {
  const [state, detail] = classify(LOCAL);
  assert.equal(state, 'plaintext-unreachable');
  assert.match(detail, /never delivered anything/);
  assert.match(repair(state, LOCAL), /delete this hook/);
});

test('the certificate question is handed to the other note', () => {
  const [state, detail] = classify(UNVERIFIED);
  assert.equal(state, 'encrypted-unverified');
  assert.match(detail, /different question/);
  assert.equal(classify(TLS)[0], 'encrypted');
});

test('the compliant looking field is named in the finding', () => {
  assert.ok(looksCompliant(OPEN));
  assert.ok(!looksCompliant(TLS));
  assert.ok(!looksCompliant(UNVERIFIED));
  assert.match(classify(OPEN)[1], /what a hook with no TLS at all always reads/);
});

test('a plaintext hook with no insecure_ssl field is still the finding', () => {
  const hook = { id: 5, config: { url: 'http://hooks.acme.io/github' } };
  assert.ok(!looksCompliant(hook));
  assert.equal(classify(hook)[0], 'plaintext');
});

test('the private ranges stop where they should', () => {
  assert.ok(isPrivateHost('10.0.0.1'));
  assert.ok(isPrivateHost('192.168.1.7'));
  assert.ok(isPrivateHost('172.16.0.1'));
  assert.ok(isPrivateHost('172.31.255.254'));
  assert.ok(isPrivateHost('127.0.0.1'));
  assert.ok(isPrivateHost('169.254.169.254'));
  assert.ok(!isPrivateHost('172.15.0.1'));
  assert.ok(!isPrivateHost('172.32.0.1'));
  assert.ok(!isPrivateHost('8.8.8.8'));
  assert.ok(!isPrivateHost('hooks.acme.io'));
});

test('local names and ipv6 loopback count as unreachable', () => {
  assert.ok(isPrivateHost('localhost'));
  assert.ok(isPrivateHost('build-01.internal'));
  assert.ok(isPrivateHost('printer.local'));
  assert.ok(isPrivateHost('::1'));
  assert.ok(isPrivateHost('fd00::1'));
  assert.ok(!isPrivateHost(''));
  assert.ok(!isPrivateHost(null));
});

test('the printed url survives a query string and a userinfo prefix', () => {
  assert.equal(safeUrl('http://hooks.acme.io/github?token=abc123'),
    'http://hooks.acme.io/github');
  assert.equal(safeUrl('https://bot:hunter2@hooks.acme.io/x'),
    'https://<redacted>@hooks.acme.io/x');
  assert.ok(!safeUrl('https://bot:hunter2@hooks.acme.io/x').includes('hunter2'));
  assert.equal(safeUrl(''), '');
});

test('the host is parsed out of the shapes a url arrives in', () => {
  assert.equal(hostOf('http://hooks.acme.io:8080/github'), 'hooks.acme.io');
  assert.equal(hostOf('http://bot:pw@10.0.0.4/hooks'), '10.0.0.4');
  assert.equal(hostOf('http://[::1]:3000/hooks'), '::1');
  assert.equal(schemeOf('HTTP://hooks.acme.io'), 'http');
  assert.equal(schemeOf('hooks.acme.io'), '');
});

test('a hook with no url is not counted either way', () => {
  assert.equal(classify({ id: 6, config: {} })[0], 'no-scheme');
  assert.equal(classify({ id: 7, config: { url: 'ftp://x.example/h' } })[0],
    'unknown-scheme');
});

test('the summary separates leaking from unreachable', () => {
  assert.deepEqual(summarize([OPEN, LOCAL, TLS, UNVERIFIED]), {
    total: 4, plaintext: 1, unreachable: 1, encrypted: 2, unreadable: 0,
  });
});
''',
"faq": [
 ("The payload is signed. Does that not make plaintext acceptable?",
  "No, because a signature is about authenticity and not about secrecy. HMAC proves the payload came from GitHub and has not been altered; it does not hide a single byte of it, and the signature travels in a header of the same unencrypted request. Anyone on the path reads the commit messages, branch names, issue bodies and logins in full, and can replay the exact request at your receiver afterwards - it will verify, because it is genuine. Signing solves forgery. It does not solve reading."),
 ("Why does insecure_ssl still say 0 on a plaintext hook?",
  "Because that field is about verifying a certificate during a TLS handshake, and an http:// hook never performs one. There is nothing to verify, so the field stays at its default and reports the value everybody is looking for. That is the specific reason this survives audits: a checklist that samples insecure_ssl sees a compliant hook. The script names that combination explicitly in its output rather than leaving the reader to notice it."),
 ("Our receiver is inside the network on a plain port. What are the options?",
  "If GitHub is delivering to it successfully, it is not inside the network in any useful sense - the route from GitHub's delivery infrastructure to that host exists, and so does the route for everyone in between. The workable shape is a small public endpoint that terminates a real certificate, verifies the signature, and forwards inwards. If GitHub genuinely cannot reach the host, the hook has never worked and the script reports it as unreachable instead."),
 ("Is a hook pointed at localhost or a tunnel actually a problem?",
  "It is a different problem. GitHub cannot route to a loopback or private address, so nothing is leaking and nothing is arriving either: the delivery log will be connection errors for as far back as it goes. What makes it worth reporting is that it sits in the hook list looking like a working integration, so somebody counts it, and a handler somewhere has been waiting for events since the day the tunnel was closed. Delete it or repoint it."),
 ("How much of the repository actually goes over the wire?",
  "More than people expect. A push payload carries the branch, the commits with their messages and author details, and the list of files added, removed and modified. An issue or pull request payload carries the entire body and title. A comment payload carries the comment. Over an open channel, on a private repository, that is a readable feed of your development work, and the volume depends entirely on which events the hook subscribes to - which is worth reading at the same time."),
],
"related": [
 ("/github/webhook-insecure-ssl/", "Certificate verification switched off on the hook"),
 ("/github/webhook-no-secret/", "A webhook with no secret sends no signature"),
 ("/github/webhook-sha1-signature-only/", "A receiver still checking the SHA-1 signature"),
],
"citations": [CITE_REPO_HOOKS, CITE_VALIDATE, CITE_ORG_HOOKS, CITE_ABOUT],
},

]
