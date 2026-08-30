#!/usr/bin/env python3
"""/github/ field notes, batch L — the writing.

Four notes about a GitHub App whose configuration page and whose running
reality have come apart. In every one of them the settings screen is telling
the truth and so is the API, and they are describing different things.

The first is a switch somebody else flipped. An organization owner suspended
the installation rather than removing it, so the record survives, the stored id
still resolves, and every token minted against it is refused. The interesting
output is not a repair the reader can run: it is that the state is not
retryable, so the integration should stop rather than fail on a schedule for a
month.

The second is a change that was made and never landed. Adding a permission to
an App does not apply it to installations that already exist; each of them has
to accept the upgrade, and until then that installation's tokens carry the
grant it agreed to. The report is therefore a per-installation list rather than
a verdict, because one fleet holds both answers at once.

The third is a subscription that could not be made. A GitHub App receives only
the events it declares, and it can only declare an event whose gating
permission it holds, so the checkbox is not offered and nothing anywhere
records the absence. The repair has three steps in a fixed order and the script
prints all three.

The fourth is a narrowing the reader's own code asked for. The token endpoint
accepts a repository list and a permission map that cut the token below the
installation's grant, so one code path 404s on a repository the App is
plainly installed on. The script reads what the token can reach, never mints
one, and says out loud which half of the comparison it cannot see.

Read only throughout, and in the fourth case deliberately incomplete rather
than confidently wrong.
"""

CITE_SUSPEND = ("Suspending a GitHub App installation — GitHub Docs",
                "https://docs.github.com/en/apps/maintaining-github-apps/suspending-a-github-app-installation")
CITE_APPS_REST = ("Apps — GitHub REST API",
                  "https://docs.github.com/en/rest/apps/apps")
CITE_APP_INSTALL_AUTH = ("Authenticating as a GitHub App installation — GitHub Docs",
                         "https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/authenticating-as-a-github-app-installation")
CITE_APP_AUTH = ("Authenticating as a GitHub App — GitHub Docs",
                 "https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/authenticating-as-a-github-app")
CITE_EDIT_PERMS = ("Editing a GitHub App's permissions — GitHub Docs",
                   "https://docs.github.com/en/apps/maintaining-github-apps/editing-a-github-apps-permissions")
CITE_APP_PERMS = ("Permissions required for GitHub Apps — GitHub Docs",
                  "https://docs.github.com/en/rest/authentication/permissions-required-for-github-apps")
CITE_INSTALLATIONS = ("Installations — GitHub REST API",
                      "https://docs.github.com/en/rest/apps/installations")
CITE_WEBHOOK_EVENTS = ("Webhook events and payloads — GitHub Docs",
                       "https://docs.github.com/en/webhooks/webhook-events-and-payloads")
CITE_APP_WEBHOOKS = ("Using webhooks with GitHub Apps — GitHub Docs",
                     "https://docs.github.com/en/apps/creating-github-apps/registering-a-github-app/using-webhooks-with-github-apps")
CITE_INSTALL_TOKEN = ("Generating an installation access token for a GitHub App — GitHub Docs",
                      "https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-an-installation-access-token-for-a-github-app")

GUIDES = [

{
"slug": "installation-suspended",
"title": "The installation is suspended and every call it makes 403s",
"description": "A suspended App installation still lists, still resolves and refuses everything. suspended_at on the installation record is the only clean signal.",
"h1": "the installation is suspended and every call it makes 403s",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github app installation suspended",
             "suspended_at github installation",
             "github app 403 no permission change",
             "github app webhooks stopped suddenly",
             "unsuspend github app installation"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Nothing was deployed and nothing was rotated. At some point on Thursday every call the App makes to one organization started coming back <code>403</code>, and the webhook deliveries that used to arrive every few minutes stopped entirely. The App is still installed &mdash; you can see it in the list, the installation id you stored still resolves &mdash; and it does not work.",
"short_answer": """<p>Somebody with owner rights on that organization suspended the installation instead of removing it. Suspension keeps the record and revokes the capability: the installation still appears in <code>GET /app/installations</code>, the stored id still resolves, and every token minted against it is refused while event delivery stops.</p>
<p>The one clean signal is <code>suspended_at</code> on the installation record, read with the App's JWT. A non-null value is the finding, and <code>suspended_by</code> names who did it. From inside the failing process you cannot tell this apart from anything else that returns 403, because a suspended installation refuses uniformly and names no reason. The important consequence is not a fix you can apply: it is that this state is <em>not retryable</em>, so the correct behaviour is to stop and report rather than back off and try again for a month.</p>""",
"problem": """<p>It looks transient, and it is treated as transient. A blanket 403 that arrives without a deploy is exactly what an expiring credential looks like, or a rate limit, or a bad five minutes at GitHub, so the retry logic that everybody sensibly wrote does what it was built to do. It backs off, it tries again, it backs off further. There is no interval at which this succeeds, and the loop has no exit condition because the failure never changes shape.</p>
<p>The credential gets rotated next, because that is the reflex. A new JWT is signed, a fresh installation token is minted, and the mint even appears to work &mdash; suspension does not always fail loudly at the point you would most like it to. Then the new token gets the same 403 as the old one, and now there is a second variable in an incident that had one, plus a key rotation nobody planned in the middle of it.</p>
<p>Underneath both is the assumption that the App's own settings page is the state of the world. It is not. The App's page shows what the App asks for; the organization's Installed GitHub Apps page shows what one account has decided about it, and suspension lives there. The person who suspended it did so from a screen the App's developers usually cannot see, often during a security review, often meaning to do exactly this and expecting the App's operator to notice.</p>""",
"why": """<p><strong>Suspension is a third state, between installed and not.</strong> An owner can remove an installation, which deletes the record, or suspend it, which keeps everything and turns it off. The record retains its id, its account, its repository selection and its permissions, so every read that looks for existence finds it. The capability is what was withdrawn, and nothing about existence reports that.</p>
<p><strong>The refusal is uniform and unhelpful.</strong> Requests made with a token belonging to a suspended installation are refused, and the refusal does not say <em>suspended</em>. That is why a process holding only an installation token cannot diagnose itself: every hypothesis it might test &mdash; a permission, a repository, a route &mdash; produces the same answer.</p>
<p><strong>Webhooks stop at the same moment.</strong> Suspension turns off event delivery as well as API access, which is worth knowing because the two symptoms usually get filed as separate incidents by separate people. A push-based integration that also polls will notice the polling break first and spend an hour before somebody says the deliveries stopped too.</p>
<p><strong>Only the App's JWT can see it.</strong> <code>suspended_at</code> and <code>suspended_by</code> live on the installation record, and installation records are read with the App's own JWT rather than with a token minted from them. So the diagnosis has to be made by something holding the private key. If your integration only ever holds installation tokens, it structurally cannot tell you why it is broken, and that is an argument for the health check being a separate thing from the worker.</p>
<p><strong>Unsuspending is not yours to do.</strong> The account owner suspended it and the account owner reverses it, from that organization's Installed GitHub Apps page. There is an API for it and it is a write, so this script does not touch it &mdash; and it would not help anyway, since an App unsuspending itself would defeat the point of the feature. What the script can do is name the account, the id, the moment and the person, which is the whole content of the message you need to send.</p>""",
"steps": [
 {"h": "Stop trusting the failing process to explain itself",
  "body": """<p>A worker holding an installation token sees one 403 and can distinguish nothing. Do the diagnosis from something that holds the App's JWT, which in most deployments means a small separate script rather than a new code path inside the worker. That separation is the point: the worker's credential is the thing that has been switched off.</p>"""},
 {"h": "List the installations and read the timestamp",
  "body": """<p><code>GET /app/installations</code> returns every current installation with <code>id</code>, <code>account.login</code>, <code>repository_selection</code>, <code>created_at</code>, <code>suspended_at</code> and <code>suspended_by</code>. A non-null <code>suspended_at</code> on the row you care about is the answer, and nothing else in the response is ambiguous about it. Paginate: an App on a few hundred accounts does not fit on one page.</p>"""},
 {"h": "Check whether your id is on the list at all",
  "body": """<p>An absent id is a different failure with a similar smell. Uninstalling and reinstalling produces a new installation id, so a stored one can stop resolving without anybody suspending anything. The script separates the two because the message you send differs: one asks an owner to unsuspend, the other asks your own code to resolve the id at runtime.</p>"""},
 {"h": "Corroborate with the token, do not diagnose with it",
  "body": """<p>If you have an installation token to hand, <code>GET /installation/repositories</code> with it. A 403 there alongside a non-null <code>suspended_at</code> ties the symptom to the cause in one report, which is what makes the message to the organization owner short. A 403 there with <em>no</em> suspension is a different note entirely, and the script says so rather than reaching for the nearest explanation.</p>"""},
 {"h": "Make the state non-retryable in your own code",
  "body": """<p>This is the durable part. Treat suspension as terminal for that installation: stop the queue for it, mark it, alert once, and stop spending quota. The list of installations is cheap to read on a schedule, so the transition from active to suspended can be a notification rather than a discovery made three weeks later by a customer.</p>"""},
],
"verify": """<p>Once an owner has unsuspended, the same read flips to <code>active</code> with no change on your side. Nothing needs redeploying, because nothing on your side was ever wrong.</p>
<pre><code class="language-bash">GITHUB_APP_JWT=$(python3 sign_app_jwt.py) python3 github_installation_suspension.py --installation-id 41234567
# 3 installation(s) visible to this App
# suspended: installation 41234567 on acme-corp was suspended at
# 2026-08-27T09:14:22Z by octo-admin, 3 day(s) ago
# repair: an organization owner unsuspends it from the org's Installed
# GitHub Apps page. Retrying cannot help: stop the queue for this installation.

# after the owner acts
# active: installation 41234567 on acme-corp is listed and not suspended</code></pre>""",
"code_intro": "One paginated GET does the work, and one optional GET turns a diagnosis into a corroborated one. Everything that produces a finding is pure: reading a timestamp that can be missing, null, empty or the string <code>null</code> depending on which layer of tooling handled the JSON; turning it into an age; matching a configured id against the list whether it was stored as a number or as a string; and a verdict that refuses to call anything suspended on the strength of a 403 alone. The only thing the script prints that a reader can act on is a sentence to send to somebody else.",
"py_file": "github_installation_suspension.py",
"py": '''"""Say whether a GitHub App installation is suspended, and stop retrying if so.

Read only. GETs against the App's own installation records with the App JWT,
plus one optional probe with an installation access token. Nothing is minted,
unsuspended or changed. There is an endpoint that unsuspends an installation
and it is a write, so this script does not call it; it prints the request you
have to make of an organization owner instead.

An owner can suspend an installation rather than removing it. The record
survives, so the App still lists it and a stored id still resolves, but tokens
minted for it are refused and webhook delivery stops. The only clean signal is
the suspended_at field on the installation record, which is readable with the
App's JWT and not with a token minted from it.

Environment:

    GITHUB_APP_JWT              the JWT your own signing code produced
    GITHUB_INSTALLATION_TOKEN   optional, used only to corroborate
"""
import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_installation_suspension")

API = "https://api.github.com"
UA = "github-installation-suspension/1.0"

# States that no amount of waiting will clear. Reporting this is the point of
# the script: a suspended installation fails identically forever, so a backoff
# loop around it is a way of spending quota on a decision somebody already made.
TERMINAL = ("suspended", "not-listed")


def suspended_at(inst):
    """The suspension timestamp on an installation record, or None. Pure.

    Tolerant on purpose. Depending on which layer deserialised the JSON the
    absent case arrives as a missing key, as None, as an empty string or as the
    four characters n-u-l-l, and treating any of those as a timestamp would
    report a healthy installation as suspended.
    """
    if not isinstance(inst, dict):
        return None
    raw = inst.get("suspended_at")
    if raw is None:
        return None
    text = str(raw).strip()
    if not text or text.lower() in ("null", "none"):
        return None
    return text


def is_suspended(inst):
    """Whether an installation record carries a suspension. Pure."""
    return suspended_at(inst) is not None


def suspended_by(inst):
    """Who suspended it, where the record says. Pure.

    suspended_by is a user object when it is present at all, and it can be
    absent on a record that is genuinely suspended, so an unknown actor is
    never taken as evidence that nothing happened.
    """
    if not isinstance(inst, dict):
        return None
    who = inst.get("suspended_by")
    if isinstance(who, dict):
        login = who.get("login")
        return str(login) if login else None
    if isinstance(who, str) and who.strip():
        return who.strip()
    return None


def parsed_time(text):
    """An ISO 8601 timestamp as an aware datetime, or None. Pure."""
    raw = str(text or "").strip()
    if not raw:
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


def account_of(inst):
    """The login of the account an installation sits on. Pure."""
    if not isinstance(inst, dict):
        return "an unnamed account"
    account = inst.get("account")
    if isinstance(account, dict) and account.get("login"):
        return str(account["login"])
    return "an unnamed account"


def find(installations, installation_id):
    """The record for one installation id, or None. Pure.

    The id is compared as text because it reaches this script from a config
    file, an environment variable or a command line, and 41234567 and the
    string "41234567" are the same installation.
    """
    if installation_id is None:
        return None
    wanted = str(installation_id).strip()
    for inst in installations or []:
        if isinstance(inst, dict) and str(inst.get("id", "")).strip() == wanted:
            return inst
    return None


def summarize(installations):
    """Counts across every installation the App can see. Pure."""
    rows = [i for i in (installations or []) if isinstance(i, dict)]
    suspended = [i for i in rows if is_suspended(i)]
    return {"total": len(rows), "suspended": len(suspended),
            "active": len(rows) - len(suspended),
            "suspended_ids": [i.get("id") for i in suspended]}


def verdict(target, probe_status=None, now=None):
    """Turn one installation record and an optional probe into a finding. Pure.

    target is the record for the installation being asked about, or None when
    the id is not in the list at all. probe_status is what an installation
    access token got from GET /installation/repositories, where one was
    available; it corroborates and never decides, because a 403 on its own is
    the least specific thing the GitHub API says.
    """
    if target is None:
        return ("not-listed",
                "this installation id is not among the ones the App can see. "
                "Suspension keeps the record, so an absent id means the App "
                "was removed and possibly reinstalled under a new id, which "
                "is a different repair.")
    ident = "installation %s on %s" % (target.get("id", "?"), account_of(target))
    when = suspended_at(target)
    if when is not None:
        age = days_since(when, now)
        who = suspended_by(target)
        return ("suspended",
                "%s was suspended at %s%s%s. Every token minted for it is "
                "refused and webhook delivery has stopped. Retrying cannot "
                "clear this." % (ident, when,
                                 " by %s" % who if who else "",
                                 ", %d day(s) ago" % age if age is not None else ""))
    if probe_status in (401, 403):
        return ("active-but-refused",
                "%s is listed and not suspended, yet an installation token "
                "got %d. The refusal is about a permission, a route or the "
                "token itself rather than about suspension."
                % (ident, probe_status))
    return ("active", "%s is listed and not suspended." % ident)


def retryable(state):
    """Whether a caller should ever try this installation again. Pure."""
    return state not in TERMINAL


def repair(state, target):
    """The sentence a reader has to act on. Pure."""
    if state == "suspended":
        return ("an organization owner unsuspends it from the %s account's "
                "Installed GitHub Apps page. Retrying cannot help: stop the "
                "queue for this installation and alert once."
                % account_of(target))
    if state == "not-listed":
        return ("resolve the installation id at runtime from the org's own "
                "installation record, or from the installation.id field on an "
                "incoming webhook, rather than storing it.")
    if state == "active-but-refused":
        return ("read the accepted-permissions header on the failing response "
                "and diff it against the permissions this installation "
                "granted. Suspension is not the cause here.")
    return "nothing. This installation is usable."


def get(session, path):
    """One GET. Returns (status, json-or-None)."""
    url = API + path if path.startswith("/") else path
    r = session.get(url, timeout=30)
    try:
        body = r.json()
    except ValueError:
        body = None
    return r.status_code, body


def list_installations(session, pages=10):
    """Every installation this App can see, paginated. Read only."""
    out = []
    for page in range(1, pages + 1):
        status, body = get(session, "/app/installations?per_page=100&page=%d" % page)
        if status != 200 or not isinstance(body, list):
            if page == 1:
                log.error("GET /app/installations returned %d; the JWT is the "
                          "credential this endpoint wants", status)
            break
        out.extend(body)
        if len(body) < 100:
            break
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--installation-id",
                    default=os.environ.get("GITHUB_INSTALLATION_ID"),
                    help="the installation to ask about; omit to report on all")
    args = ap.parse_args()

    jwt = os.environ.get("GITHUB_APP_JWT")
    if not jwt:
        log.error("set GITHUB_APP_JWT to the JWT your own signing code "
                  "produced. suspended_at lives on the installation record, "
                  "and installation records are read with the App's JWT")
        return 2

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + jwt,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": UA,
    })

    installations = list_installations(session)
    stats = summarize(installations)
    log.info("%d installation(s) visible to this App, %d suspended",
             stats["total"], stats["suspended"])

    probe_status = None
    token = os.environ.get("GITHUB_INSTALLATION_TOKEN")
    if token:
        probe = requests.Session()
        probe.headers.update({
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": UA,
        })
        probe_status, _ = get(probe, "/installation/repositories?per_page=1")
        log.info("installation token: GET /installation/repositories returned %d",
                 probe_status)

    now = datetime.now(timezone.utc)
    findings = []
    if args.installation_id:
        target = find(installations, args.installation_id)
        state, detail = verdict(target, probe_status, now)
        findings.append({"installation_id": args.installation_id, "state": state,
                         "detail": detail, "retryable": retryable(state)})
        log.info("%s: %s", state, detail)
        log.info("repair: %s", repair(state, target))
    else:
        for inst in installations:
            state, detail = verdict(inst, None, now)
            findings.append({"installation_id": inst.get("id"), "state": state,
                             "detail": detail, "retryable": retryable(state)})
            if state != "active":
                log.info("%s: %s", state, detail)
                log.info("repair: %s", repair(state, inst))
        if stats["suspended"] == 0:
            log.info("active: no installation of this App is suspended")

    print(json.dumps({"visible": stats["total"], "suspended": stats["suspended"],
                      "suspended_ids": stats["suspended_ids"],
                      "probe_status": probe_status,
                      "findings": findings}, indent=2, default=str))
    return 1 if any(not f["retryable"] for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-installation-suspension.mjs",
"js": '''/**
 * Say whether a GitHub App installation is suspended, and stop retrying if so.
 *
 * Read only. GETs against the App's own installation records with the App JWT,
 * plus one optional probe with an installation access token. The endpoint that
 * unsuspends an installation is a write and is not called here; the script
 * prints the request you have to make of an organization owner instead.
 *
 * Environment:
 *   GITHUB_APP_JWT             the JWT your own signing code produced
 *   GITHUB_INSTALLATION_TOKEN  optional, used only to corroborate
 *   GITHUB_INSTALLATION_ID     optional, the installation to ask about
 */
const API = 'https://api.github.com';
const UA = 'github-installation-suspension/1.0';

/** States no amount of waiting will clear. */
export const TERMINAL = ['suspended', 'not-listed'];

/**
 * The suspension timestamp on an installation record, or null. Pure.
 * Absent arrives as a missing key, null, an empty string or the four
 * characters n-u-l-l depending on what deserialised the JSON.
 */
export function suspendedAt(inst) {
  if (!inst || typeof inst !== 'object') return null;
  const raw = inst.suspended_at;
  if (raw === null || raw === undefined) return null;
  const text = String(raw).trim();
  if (!text || ['null', 'none'].includes(text.toLowerCase())) return null;
  return text;
}

/** Whether an installation record carries a suspension. Pure. */
export function isSuspended(inst) {
  return suspendedAt(inst) !== null;
}

/** Who suspended it, where the record says. Pure. */
export function suspendedBy(inst) {
  if (!inst || typeof inst !== 'object') return null;
  const who = inst.suspended_by;
  if (who && typeof who === 'object') return who.login ? String(who.login) : null;
  if (typeof who === 'string' && who.trim()) return who.trim();
  return null;
}

/** An ISO 8601 timestamp as epoch milliseconds, or null. Pure. */
export function parsedTime(text) {
  const raw = String(text ?? '').trim();
  if (!raw) return null;
  const ms = Date.parse(raw);
  return Number.isNaN(ms) ? null : ms;
}

/** Whole days between a timestamp and now, or null. Pure. */
export function daysSince(text, nowMs) {
  const when = parsedTime(text);
  if (when === null || nowMs === null || nowMs === undefined) return null;
  return Math.floor((nowMs - when) / 86400000);
}

/** The login of the account an installation sits on. Pure. */
export function accountOf(inst) {
  if (!inst || typeof inst !== 'object') return 'an unnamed account';
  const account = inst.account;
  if (account && typeof account === 'object' && account.login) return String(account.login);
  return 'an unnamed account';
}

/** The record for one installation id, or null. Pure. Compared as text. */
export function find(installations, installationId) {
  if (installationId === null || installationId === undefined) return null;
  const wanted = String(installationId).trim();
  for (const inst of installations ?? []) {
    if (inst && typeof inst === 'object' && String(inst.id ?? '').trim() === wanted) return inst;
  }
  return null;
}

/** Counts across every installation the App can see. Pure. */
export function summarize(installations) {
  const rows = (installations ?? []).filter((i) => i && typeof i === 'object');
  const suspended = rows.filter(isSuspended);
  return {
    total: rows.length,
    suspended: suspended.length,
    active: rows.length - suspended.length,
    suspended_ids: suspended.map((i) => i.id),
  };
}

/** Turn one installation record and an optional probe into a finding. Pure. */
export function verdict(target, probeStatus = null, nowMs = null) {
  if (!target) {
    return ['not-listed',
      'this installation id is not among the ones the App can see. ' +
      'Suspension keeps the record, so an absent id means the App was ' +
      'removed and possibly reinstalled under a new id, which is a ' +
      'different repair.'];
  }
  const ident = `installation ${target.id ?? '?'} on ${accountOf(target)}`;
  const when = suspendedAt(target);
  if (when !== null) {
    const age = daysSince(when, nowMs);
    const who = suspendedBy(target);
    return ['suspended',
      `${ident} was suspended at ${when}${who ? ` by ${who}` : ''}` +
      `${age !== null ? `, ${age} day(s) ago` : ''}. Every token minted for ` +
      'it is refused and webhook delivery has stopped. Retrying cannot clear this.'];
  }
  if (probeStatus === 401 || probeStatus === 403) {
    return ['active-but-refused',
      `${ident} is listed and not suspended, yet an installation token got ` +
      `${probeStatus}. The refusal is about a permission, a route or the ` +
      'token itself rather than about suspension.'];
  }
  return ['active', `${ident} is listed and not suspended.`];
}

/** Whether a caller should ever try this installation again. Pure. */
export function retryable(state) {
  return !TERMINAL.includes(state);
}

/** The sentence a reader has to act on. Pure. */
export function repair(state, target) {
  if (state === 'suspended') {
    return `an organization owner unsuspends it from the ${accountOf(target)} ` +
      "account's Installed GitHub Apps page. Retrying cannot help: stop the " +
      'queue for this installation and alert once.';
  }
  if (state === 'not-listed') {
    return 'resolve the installation id at runtime from the org\\'s own ' +
      'installation record, or from the installation.id field on an incoming ' +
      'webhook, rather than storing it.';
  }
  if (state === 'active-but-refused') {
    return 'read the accepted-permissions header on the failing response and ' +
      'diff it against the permissions this installation granted. Suspension ' +
      'is not the cause here.';
  }
  return 'nothing. This installation is usable.';
}

async function get(credential, path) {
  const url = path.startsWith('/') ? API + path : path;
  const res = await fetch(url, {
    headers: {
      Authorization: `Bearer ${credential}`,
      Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      'User-Agent': UA,
    },
  });
  let body = null;
  try { body = await res.json(); } catch { body = null; }
  return { status: res.status, body };
}

async function listInstallations(jwt, pages = 10) {
  const out = [];
  for (let page = 1; page <= pages; page += 1) {
    const { status, body } = await get(jwt, `/app/installations?per_page=100&page=${page}`);
    if (status !== 200 || !Array.isArray(body)) {
      if (page === 1) {
        console.error(`GET /app/installations returned ${status}; the JWT is ` +
          'the credential this endpoint wants');
      }
      break;
    }
    out.push(...body);
    if (body.length < 100) break;
  }
  return out;
}

async function main() {
  const jwt = process.env.GITHUB_APP_JWT;
  if (!jwt) {
    console.error('set GITHUB_APP_JWT to the JWT your own signing code ' +
      'produced. suspended_at lives on the installation record, and ' +
      "installation records are read with the App's JWT");
    process.exitCode = 2;
    return;
  }
  const installationId = process.argv[2] ?? process.env.GITHUB_INSTALLATION_ID ?? null;

  const installations = await listInstallations(jwt);
  const stats = summarize(installations);
  console.log(`${stats.total} installation(s) visible to this App, ` +
    `${stats.suspended} suspended`);

  let probeStatus = null;
  const token = process.env.GITHUB_INSTALLATION_TOKEN;
  if (token) {
    ({ status: probeStatus } = await get(token, '/installation/repositories?per_page=1'));
    console.log('installation token: GET /installation/repositories returned ' +
      `${probeStatus}`);
  }

  const now = Date.now();
  const findings = [];
  if (installationId) {
    const target = find(installations, installationId);
    const [state, detail] = verdict(target, probeStatus, now);
    findings.push({ installation_id: installationId, state, detail, retryable: retryable(state) });
    console.log(`${state}: ${detail}`);
    console.log(`repair: ${repair(state, target)}`);
  } else {
    for (const inst of installations) {
      const [state, detail] = verdict(inst, null, now);
      findings.push({ installation_id: inst.id, state, detail, retryable: retryable(state) });
      if (state !== 'active') {
        console.log(`${state}: ${detail}`);
        console.log(`repair: ${repair(state, inst)}`);
      }
    }
    if (stats.suspended === 0) {
      console.log('active: no installation of this App is suspended');
    }
  }

  console.log(JSON.stringify({
    visible: stats.total,
    suspended: stats.suspended,
    suspended_ids: stats.suspended_ids,
    probe_status: probeStatus,
    findings,
  }, null, 2));
  process.exitCode = findings.some((f) => !f.retryable) ? 1 : 0;
}

// Only run when invoked directly, so importing this module from the test file
// does not execute main(), fail on the missing JWT and set an exit code that
// fails the suite even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The cases worth pinning are the shapes an absent timestamp arrives in, because every one of them has to mean <em>not suspended</em> and a single miss turns a healthy fleet into a false alarm. After that: an id stored as a string matching a record that holds a number, a suspension whose actor is unknown still being a suspension, and the two negative results the script must never conflate &mdash; an id that is missing from the list, and a 403 on an installation that is demonstrably active.",
"test_py_file": "test_github_installation_suspension.py",
"test_py": '''from datetime import datetime, timezone

from github_installation_suspension import (
    account_of, days_since, find, is_suspended, repair, retryable,
    summarize, suspended_at, suspended_by, verdict,
)

NOW = datetime(2026, 8, 30, 12, 0, 0, tzinfo=timezone.utc)
LIVE = {"id": 41234567, "account": {"login": "acme-corp"}, "suspended_at": None}
DEAD = {"id": 41234568, "account": {"login": "beta-inc"},
        "suspended_at": "2026-08-27T09:14:22Z",
        "suspended_by": {"login": "octo-admin"}}


def test_every_shape_of_absent_timestamp_means_not_suspended():
    assert not is_suspended({"id": 1})
    assert not is_suspended({"id": 1, "suspended_at": None})
    assert not is_suspended({"id": 1, "suspended_at": ""})
    assert not is_suspended({"id": 1, "suspended_at": "   "})
    assert not is_suspended({"id": 1, "suspended_at": "null"})


def test_a_real_timestamp_is_a_suspension():
    assert is_suspended(DEAD)
    assert suspended_at(DEAD) == "2026-08-27T09:14:22Z"


def test_a_suspension_with_no_named_actor_is_still_a_suspension():
    anon = {"id": 9, "suspended_at": "2026-08-27T09:14:22Z", "suspended_by": None}
    assert is_suspended(anon)
    assert suspended_by(anon) is None
    assert suspended_by(DEAD) == "octo-admin"


def test_the_age_is_measured_from_the_timestamp():
    assert days_since("2026-08-27T09:14:22Z", NOW) == 3
    assert days_since("not a date", NOW) is None
    assert days_since(None, NOW) is None


def test_an_id_matches_whether_it_was_stored_as_text_or_a_number():
    assert find([LIVE, DEAD], 41234568) is DEAD
    assert find([LIVE, DEAD], "41234568") is DEAD
    assert find([LIVE, DEAD], " 41234568 ") is DEAD
    assert find([LIVE, DEAD], 999) is None


def test_the_summary_counts_both_sides():
    stats = summarize([LIVE, DEAD, {"id": 3}])
    assert stats == {"total": 3, "suspended": 1, "active": 2,
                     "suspended_ids": [41234568]}


def test_a_suspended_installation_names_the_moment_and_the_actor():
    state, detail = verdict(DEAD, None, NOW)
    assert state == "suspended"
    assert "octo-admin" in detail
    assert "3 day(s) ago" in detail
    assert not retryable(state)


def test_a_missing_id_is_never_reported_as_a_suspension():
    state, detail = verdict(None, 403, NOW)
    assert state == "not-listed"
    assert "different repair" in detail
    assert not retryable(state)


def test_a_403_on_an_active_installation_is_sent_elsewhere():
    state, detail = verdict(LIVE, 403, NOW)
    assert state == "active-but-refused"
    assert "rather than about suspension" in detail
    assert retryable(state)


def test_an_active_installation_with_no_probe_is_just_active():
    assert verdict(LIVE, None, NOW)[0] == "active"
    assert retryable("active")


def test_the_repair_for_a_suspension_names_the_account_and_forbids_retrying():
    text = repair("suspended", DEAD)
    assert "beta-inc" in text
    assert "Retrying cannot help" in text


def test_the_account_falls_back_rather_than_raising():
    assert account_of({"id": 1}) == "an unnamed account"
    assert account_of(None) == "an unnamed account"
''',
"test_js_file": "github-installation-suspension.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  accountOf, daysSince, find, isSuspended, repair, retryable,
  summarize, suspendedAt, suspendedBy, verdict,
} from './github-installation-suspension.mjs';

const NOW = Date.parse('2026-08-30T12:00:00Z');
const LIVE = { id: 41234567, account: { login: 'acme-corp' }, suspended_at: null };
const DEAD = {
  id: 41234568,
  account: { login: 'beta-inc' },
  suspended_at: '2026-08-27T09:14:22Z',
  suspended_by: { login: 'octo-admin' },
};

test('every shape of absent timestamp means not suspended', () => {
  assert.ok(!isSuspended({ id: 1 }));
  assert.ok(!isSuspended({ id: 1, suspended_at: null }));
  assert.ok(!isSuspended({ id: 1, suspended_at: '' }));
  assert.ok(!isSuspended({ id: 1, suspended_at: '   ' }));
  assert.ok(!isSuspended({ id: 1, suspended_at: 'null' }));
});

test('a real timestamp is a suspension', () => {
  assert.ok(isSuspended(DEAD));
  assert.equal(suspendedAt(DEAD), '2026-08-27T09:14:22Z');
});

test('a suspension with no named actor is still a suspension', () => {
  const anon = { id: 9, suspended_at: '2026-08-27T09:14:22Z', suspended_by: null };
  assert.ok(isSuspended(anon));
  assert.equal(suspendedBy(anon), null);
  assert.equal(suspendedBy(DEAD), 'octo-admin');
});

test('the age is measured from the timestamp', () => {
  assert.equal(daysSince('2026-08-27T09:14:22Z', NOW), 3);
  assert.equal(daysSince('not a date', NOW), null);
  assert.equal(daysSince(null, NOW), null);
});

test('an id matches whether it was stored as text or a number', () => {
  assert.equal(find([LIVE, DEAD], 41234568), DEAD);
  assert.equal(find([LIVE, DEAD], '41234568'), DEAD);
  assert.equal(find([LIVE, DEAD], ' 41234568 '), DEAD);
  assert.equal(find([LIVE, DEAD], 999), null);
});

test('the summary counts both sides', () => {
  assert.deepEqual(summarize([LIVE, DEAD, { id: 3 }]), {
    total: 3, suspended: 1, active: 2, suspended_ids: [41234568],
  });
});

test('a suspended installation names the moment and the actor', () => {
  const [state, detail] = verdict(DEAD, null, NOW);
  assert.equal(state, 'suspended');
  assert.match(detail, /octo-admin/);
  assert.match(detail, /3 day\\(s\\) ago/);
  assert.ok(!retryable(state));
});

test('a missing id is never reported as a suspension', () => {
  const [state, detail] = verdict(null, 403, NOW);
  assert.equal(state, 'not-listed');
  assert.match(detail, /different repair/);
  assert.ok(!retryable(state));
});

test('a 403 on an active installation is sent elsewhere', () => {
  const [state, detail] = verdict(LIVE, 403, NOW);
  assert.equal(state, 'active-but-refused');
  assert.match(detail, /rather than about suspension/);
  assert.ok(retryable(state));
});

test('an active installation with no probe is just active', () => {
  assert.equal(verdict(LIVE, null, NOW)[0], 'active');
  assert.ok(retryable('active'));
});

test('the repair for a suspension names the account and forbids retrying', () => {
  const text = repair('suspended', DEAD);
  assert.match(text, /beta-inc/);
  assert.match(text, /Retrying cannot help/);
});

test('the account falls back rather than throwing', () => {
  assert.equal(accountOf({ id: 1 }), 'an unnamed account');
  assert.equal(accountOf(null), 'an unnamed account');
});
''',
"faq": [
 ("What is the difference between suspending and uninstalling?",
  "Uninstalling deletes the installation record, so the id stops resolving and the App disappears from the account's list. Suspending keeps everything and switches it off: the record, the id, the repository selection and the granted permissions all survive, tokens minted against it are refused and webhook delivery stops. That is why existence checks are useless here. The script separates the two because the message differs: a suspension needs an owner to reverse a deliberate decision, a missing id usually needs your code to stop storing one."),
 ("Why can my worker not diagnose this itself?",
  "Because suspended_at lives on the installation record, and installation records are read with the App's JWT rather than with a token minted from one. A worker that only ever holds installation tokens sees one uniform 403 and has no read that distinguishes suspension from a missing permission or an unreachable route. If you want the worker to know, give the health check the private key and keep it separate from the work, or have it treat a blanket 403 as a signal to ask a different process rather than as a reason to retry."),
 ("Can the script unsuspend the installation for me?",
  "There is an endpoint for it and it is a write, so no. It also would not be the right thing even if this section allowed writes, because an App that can unsuspend itself makes the feature meaningless: suspension exists precisely so an account owner can stop an App without negotiating with it. What the script does instead is produce the message worth sending, with the account name, the installation id, the moment and the person who did it, so the conversation starts from facts."),
 ("Our webhooks stopped at the same time. Is that the same incident?",
  "Almost certainly, and it is worth saying so early because the two symptoms usually get filed separately. Suspension turns off event delivery as well as API access, so a push-based integration and a polling one break together on the same account. If deliveries stopped for one organization and carried on for the others, look at that organization's installation record before you look at your receiver, your signature verification or your ingress."),
 ("How do we find out sooner next time?",
  "Read the installation list on a schedule and treat the transition from active to suspended as an event rather than as a state you discover during an outage. It is one paginated GET with the JWT you already hold, it costs almost nothing, and it gives you the account, the moment and the actor. The second half is making the state terminal in your own code, so the queue for that installation stops instead of spending a month failing on a timer that no interval can satisfy."),
],
"related": [
 ("/github/app-permission-upgrade-not-accepted/", "A permission upgrade installations never accepted"),
 ("/github/installation-repository-selection-partial/", "An installation that covers only some repositories"),
 ("/github/webhook-deliveries-failing/", "Webhook deliveries that have been failing unnoticed"),
],
"citations": [CITE_SUSPEND, CITE_APPS_REST, CITE_APP_INSTALL_AUTH, CITE_APP_AUTH],
},

{
"slug": "app-permission-upgrade-not-accepted",
"title": "A new App permission that installers never accepted",
"description": "Adding a permission to a GitHub App does not apply it to existing installations. Diff the App declaration against each installation grant to find the laggards.",
"h1": "a new App permission that installers never accepted",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github app permission upgrade not accepted",
             "github app new permission pending approval",
             "installations still 403 after adding permission",
             "github app permissions per installation",
             "accept permission request github app"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The permission was added a fortnight ago. The App's settings page shows it, the pull request that used it was merged, and the feature works &mdash; for about two thirds of customers. The rest still get <code>403 {\"message\": \"Resource not accessible by integration\"}</code> on exactly the call the permission was added for, and there is no pattern in which ones. Big orgs and small, old installs and new.",
"short_answer": """<p>Changing an App's permissions does not change the installations that already exist. Each one has to accept the upgrade, usually by an owner acting on an email, and until they do that installation's tokens carry the permission map it originally agreed to. The App's declaration and the installation's grant are two different objects, and only one of them is on the settings page you have been looking at.</p>
<p>Read both and subtract. <code>GET /app</code> with the App's JWT returns the permissions the App declares today; <code>GET /app/installations</code> returns each installation with the permissions it actually granted. Any installation whose map is behind the declaration &mdash; a permission absent, or held at <code>read</code> where the App now asks for <code>write</code> &mdash; is a laggard, and the output you want is the list of their ids and account logins rather than a yes or a no.</p>
<p>This is not <a href="/github/app-permission-missing/">the note about a permission the App never asked for</a>. There the fix is to add it and the instrument is the accepted-permissions header on the failing response. Here the permission has already been added, the header would name something the App genuinely holds, and the missing step is consent.</p>""",
"problem": """<p>The randomness is what wastes the week. Two customers on the same plan, using the same feature, one works and one does not, and every property you can think to correlate against comes back flat. So the theories get exotic: a cache somewhere, a region, a race in the token minting, an org policy nobody can name. The App gets redeployed, which changes nothing, and then redeployed with logging, which proves only that the 403 is real.</p>
<p>The settings page actively misleads, and it is not lying. It shows the App's permissions and they are correct. Every screenshot in the incident channel is of that page, and the thing being debugged is a different object entirely: the grant that one organization accepted at one moment in the past. Nothing on the App's own page tells you how many installations are still living on an older version of it.</p>
<p>Then the panic revert makes it worse. Rolling the permission back on the App does not restore the installations that already accepted the upgrade to a common state either; it just adds a second axis of drift, and now some installations hold <em>more</em> than the App declares. The fleet ends up in three configurations instead of two, and the only way anybody notices is a report that reads them one at a time.</p>""",
"why": """<p><strong>A declaration and a grant are separate objects.</strong> <code>GET /app</code> returns what the App asks for. Each entry in <code>GET /app/installations</code> returns what one account agreed to. They are equal at the moment of installation and they drift the instant you edit the App, which is the whole mechanism of this failure.</p>
<p><strong>Consent is per installation and it is a human act.</strong> GitHub emails the account's owners with a request to review the new permissions, and the upgrade applies when one of them accepts. Nothing about that is on your schedule. A large organization can sit on the email for a month, and an account whose owner has left can sit on it forever, which is why the laggard list tends to have a long tail rather than a clean split.</p>
<p><strong>Levels drift as well as presence.</strong> The interesting laggard is often not missing a permission at all: it granted <code>issues: read</code> and the App now declares <code>issues: write</code>. A check that only asks whether the key exists reports that installation as current, and it will still 403 on every write. Compare ranks, not keys.</p>
<p><strong>The reverse case is real and means something else.</strong> An installation can hold <em>more</em> than the App declares, which happens after a permission is removed from the App rather than added. That is not a fault to chase, it is a fact worth printing: those installations are carrying access the App no longer claims to need, and the tidy-up is a separate decision from the one you are making today.</p>
<p><strong>Events drift with permissions.</strong> The same acceptance step gates the App's webhook subscriptions, so an installation behind on permissions is frequently behind on events too, and the second symptom shows up weeks later as a handler that runs for some accounts and not others. The script reports both from the same pair of reads, and <a href="/github/app-not-subscribed-to-event/">the note on App event subscriptions</a> covers the case where nobody subscribed at all.</p>""",
"steps": [
 {"h": "Read what the App declares today",
  "body": """<p><code>GET /app</code> with the App's JWT returns <code>permissions</code> and <code>events</code> as the App currently defines them. This is the same information as the settings page, fetched rather than screenshotted, and it is one half of a comparison rather than an answer on its own.</p>"""},
 {"h": "Read what each installation actually granted",
  "body": """<p><code>GET /app/installations</code> returns a record per account, each carrying its own <code>permissions</code> map and <code>events</code> list. Paginate properly; the installation that is behind is disproportionately likely to be an old one, and old ones are at the bottom of the list. This is also where <code>suspended_at</code> lives, which is worth reading in the same pass.</p>"""},
 {"h": "Compare ranks rather than keys",
  "body": """<p>Treat the levels as ordered: absent is below <code>read</code>, which is below <code>write</code>, which is below <code>admin</code>. An installation is behind if any declared permission is held at a lower rank, which catches both the missing key and the <code>read</code>-where-<code>write</code>-is-declared case that a set difference misses entirely.</p>"""},
 {"h": "Print the laggards, grouped by what they are missing",
  "body": """<p>The deliverable is a list: installation id, account login, and the specific permissions that are behind. Grouping by the missing set usually collapses a hundred rows into two or three cohorts, and the cohorts correspond to the versions of the App people accepted, which is the pattern that looked random from inside the 403.</p>"""},
 {"h": "Chase acceptance, and make the App tolerate the gap meanwhile",
  "body": """<p>Owners accept from their organization's Installed GitHub Apps page. While you wait, have the App branch on the installation's own permission map rather than on the App's declaration &mdash; you have already read it &mdash; so a laggard degrades to a feature that is off rather than to a 403 in a log nobody reads.</p>"""},
],
"verify": """<p>After an owner accepts, the same pair of reads moves that installation from <code>upgrade-pending</code> to <code>current</code>, with no deploy on your side.</p>
<pre><code class="language-bash">GITHUB_APP_JWT=$(python3 sign_app_jwt.py) python3 github_permission_upgrade_lag.py
# app declares 5 permission(s) and 4 event(s)
# upgrades-pending: 2 of 7 installation(s) are behind the App declaration
#   41234568 beta-inc: issues absent (declared write)
#   41234570 gamma-ltd: checks read, declared write
# repair: an owner on each account accepts the pending permission request
# from that org's Installed GitHub Apps page

# after both accept
# all-current: every installation has accepted what the App declares</code></pre>""",
"code_intro": "Two GETs, one of them paginated, and everything after them is arithmetic on two dictionaries. The rank function is the whole trick: it puts absent, <code>read</code>, <code>write</code> and <code>admin</code> on one scale so that a missing permission and an under-granted one are the same finding, and it is deliberately tolerant about case and whitespace because these values pass through a lot of hands. The surplus direction is computed too, since an installation holding more than the App declares is a real state with a different meaning.",
"py_file": "github_permission_upgrade_lag.py",
"py": '''"""Find GitHub App installations still living on an older permission grant.

Read only. Two GETs with the App's JWT: the App's own declaration and the list
of installations. Nothing is granted, accepted, upgraded or changed. Accepting
a permission upgrade is a human act performed by an account owner, so the
script prints who has to be asked and for what.

Editing an App's permissions does not apply the change to installations that
already exist. Each installation keeps the grant it accepted until an owner
accepts the new one, so the App declaration and the installation grant are two
different objects that drift apart the moment the App is edited.

Environment:

    GITHUB_APP_JWT   the JWT your own signing code produced
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_permission_upgrade_lag")

API = "https://api.github.com"
UA = "github-permission-upgrade-lag/1.0"

# Permission levels are ordered, not a set. An installation that granted read
# where the App declares write is behind, and a check that only compares keys
# calls it current and then wonders why the writes keep failing.
RANK = {"none": 0, "read": 1, "write": 2, "admin": 3}


def rank(level):
    """A permission level as a comparable integer. Pure.

    Anything unrecognised sorts as none rather than raising, because a level
    this script has not heard of is not evidence that access was granted.
    """
    return RANK.get(str(level or "none").strip().lower(), 0)


def permission_gap(declared, granted):
    """Declared permissions an installation holds at a lower level. Pure.

    Returns [(permission, declared_level, granted_level), ...] sorted by name.
    granted_level is the literal string "absent" where the key is missing, so
    the report can say which of the two shapes it found.
    """
    out = []
    for name, wanted in sorted((declared or {}).items()):
        have = (granted or {}).get(name)
        if rank(have) < rank(wanted):
            out.append((name, str(wanted), str(have) if have else "absent"))
    return out


def permission_surplus(declared, granted):
    """Permissions an installation holds beyond what the App declares. Pure."""
    out = []
    for name, have in sorted((granted or {}).items()):
        wanted = (declared or {}).get(name)
        if rank(have) > rank(wanted):
            out.append((name, str(wanted) if wanted else "not declared", str(have)))
    return out


def event_gap(declared_events, granted_events):
    """Declared events an installation has not accepted. Pure."""
    have = {str(e).strip().lower() for e in (granted_events or [])}
    return sorted({str(e).strip().lower() for e in (declared_events or [])} - have)


def classify(declared_permissions, declared_events, inst):
    """Sort one installation against the App declaration. Pure.

    Returns a row: account, id, state, and the three diffs. The state is
    upgrade-pending when anything declared is not held, grant-ahead when the
    installation holds more than the App declares and nothing less, and
    current when the two maps agree.
    """
    inst = inst if isinstance(inst, dict) else {}
    account = inst.get("account") or {}
    gaps = permission_gap(declared_permissions, inst.get("permissions"))
    extra = permission_surplus(declared_permissions, inst.get("permissions"))
    events = event_gap(declared_events, inst.get("events"))
    if gaps or events:
        state = "upgrade-pending"
    elif extra:
        state = "grant-ahead"
    else:
        state = "current"
    return {"installation_id": inst.get("id"),
            "account": account.get("login") if isinstance(account, dict) else None,
            "state": state, "permission_gap": gaps,
            "permission_surplus": extra, "event_gap": events}


def verdict(rows):
    """Turn the per-installation rows into one finding. Pure."""
    rows = rows or []
    if not rows:
        return ("no-installations",
                "this App has no installations, so there is nothing to be "
                "behind. Nothing here is evidence about permissions.")
    behind = [r for r in rows if r["state"] == "upgrade-pending"]
    if behind:
        return ("upgrades-pending",
                "%d of %d installation(s) are behind the App declaration. "
                "Their tokens carry the permission map they accepted, not the "
                "one the App settings page shows."
                % (len(behind), len(rows)))
    ahead = [r for r in rows if r["state"] == "grant-ahead"]
    if ahead:
        return ("grants-ahead",
                "%d of %d installation(s) hold more than the App declares, "
                "which happens after a permission is removed rather than "
                "added. Nothing is failing; the access is simply unused."
                % (len(ahead), len(rows)))
    return ("all-current",
            "all %d installation(s) have accepted what the App declares."
            % len(rows))


def cohorts(rows):
    """Group the laggards by exactly what they are missing. Pure.

    A hundred rows usually collapse to two or three, and the cohorts are the
    versions of the App people accepted. That is the pattern which looked
    random from inside a single 403.
    """
    out = {}
    for row in rows or []:
        if row["state"] != "upgrade-pending":
            continue
        key = ", ".join("%s %s (declared %s)" % (n, g, d)
                        for n, d, g in row["permission_gap"]) or "events only"
        out.setdefault(key, []).append(row["account"] or row["installation_id"])
    return {k: sorted(map(str, v)) for k, v in sorted(out.items())}


def get(session, path):
    """One GET. Returns (status, json-or-None)."""
    url = API + path if path.startswith("/") else path
    r = session.get(url, timeout=30)
    try:
        body = r.json()
    except ValueError:
        body = None
    return r.status_code, body


def list_installations(session, pages=10):
    """Every installation this App can see, paginated. Read only."""
    out = []
    for page in range(1, pages + 1):
        status, body = get(session, "/app/installations?per_page=100&page=%d" % page)
        if status != 200 or not isinstance(body, list):
            if page == 1:
                log.error("GET /app/installations returned %d; this endpoint "
                          "wants the App JWT", status)
            break
        out.extend(body)
        if len(body) < 100:
            break
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--account", default=None,
                    help="report on one account login only")
    args = ap.parse_args()

    jwt = os.environ.get("GITHUB_APP_JWT")
    if not jwt:
        log.error("set GITHUB_APP_JWT to the JWT your own signing code "
                  "produced. Both reads here are App-level and neither one "
                  "accepts an installation token")
        return 2

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + jwt,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": UA,
    })

    status, app = get(session, "/app")
    if status != 200 or not isinstance(app, dict):
        log.error("GET /app returned %d, so there is no declaration to "
                  "compare against", status)
        return 2
    declared_permissions = app.get("permissions") or {}
    declared_events = app.get("events") or []
    log.info("app declares %d permission(s) and %d event(s)",
             len(declared_permissions), len(declared_events))

    installations = list_installations(session)
    rows = [classify(declared_permissions, declared_events, i) for i in installations]
    if args.account:
        rows = [r for r in rows if r["account"] == args.account]

    state, detail = verdict(rows)
    log.info("%s: %s", state, detail)
    for row in rows:
        if row["state"] == "upgrade-pending":
            for name, want, have in row["permission_gap"]:
                log.info("  %s %s: %s %s, declared %s",
                         row["installation_id"], row["account"], name, have, want)
            if row["event_gap"]:
                log.info("  %s %s: events not accepted: %s",
                         row["installation_id"], row["account"],
                         ", ".join(row["event_gap"]))
        if row["state"] == "grant-ahead":
            for name, want, have in row["permission_surplus"]:
                log.info("  %s %s holds %s %s, %s",
                         row["installation_id"], row["account"], name, have, want)

    if state == "upgrades-pending":
        log.info("repair: an owner on each account accepts the pending "
                 "permission request from that org's Installed GitHub Apps "
                 "page. Until then, branch on the installation's own "
                 "permission map rather than on the App declaration")
    elif state == "grants-ahead":
        log.info("repair: nothing urgent. Those installations carry access "
                 "the App no longer declares, which is a tidy-up rather than "
                 "an outage")

    print(json.dumps({"declared_permissions": declared_permissions,
                      "declared_events": sorted(str(e) for e in declared_events),
                      "state": state, "cohorts": cohorts(rows),
                      "installations": rows}, indent=2, default=str))
    return 1 if state == "upgrades-pending" else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-permission-upgrade-lag.mjs",
"js": '''/**
 * Find GitHub App installations still living on an older permission grant.
 *
 * Read only. Two GETs with the App's JWT: the App's own declaration and the
 * list of installations. Accepting a permission upgrade is a human act
 * performed by an account owner, so the script prints who has to be asked and
 * for what rather than doing anything itself.
 *
 * Environment:
 *   GITHUB_APP_JWT   the JWT your own signing code produced
 */
const API = 'https://api.github.com';
const UA = 'github-permission-upgrade-lag/1.0';

/** Permission levels are ordered, not a set. */
export const RANK = { none: 0, read: 1, write: 2, admin: 3 };

/** A permission level as a comparable integer. Pure. */
export function rank(level) {
  const key = String(level ?? 'none').trim().toLowerCase();
  return Object.prototype.hasOwnProperty.call(RANK, key) ? RANK[key] : 0;
}

/**
 * Declared permissions an installation holds at a lower level. Pure.
 * Returns [[permission, declaredLevel, grantedLevel], ...] sorted by name.
 */
export function permissionGap(declared, granted) {
  const out = [];
  for (const name of Object.keys(declared ?? {}).sort()) {
    const wanted = declared[name];
    const have = (granted ?? {})[name];
    if (rank(have) < rank(wanted)) {
      out.push([name, String(wanted), have ? String(have) : 'absent']);
    }
  }
  return out;
}

/** Permissions an installation holds beyond what the App declares. Pure. */
export function permissionSurplus(declared, granted) {
  const out = [];
  for (const name of Object.keys(granted ?? {}).sort()) {
    const have = granted[name];
    const wanted = (declared ?? {})[name];
    if (rank(have) > rank(wanted)) {
      out.push([name, wanted ? String(wanted) : 'not declared', String(have)]);
    }
  }
  return out;
}

/** Declared events an installation has not accepted. Pure. */
export function eventGap(declaredEvents, grantedEvents) {
  const have = new Set((grantedEvents ?? []).map((e) => String(e).trim().toLowerCase()));
  return [...new Set((declaredEvents ?? []).map((e) => String(e).trim().toLowerCase()))]
    .filter((e) => !have.has(e)).sort();
}

/** Sort one installation against the App declaration. Pure. */
export function classify(declaredPermissions, declaredEvents, inst) {
  const row = inst && typeof inst === 'object' ? inst : {};
  const account = row.account && typeof row.account === 'object' ? row.account : {};
  const gaps = permissionGap(declaredPermissions, row.permissions);
  const extra = permissionSurplus(declaredPermissions, row.permissions);
  const events = eventGap(declaredEvents, row.events);
  let state = 'current';
  if (gaps.length || events.length) state = 'upgrade-pending';
  else if (extra.length) state = 'grant-ahead';
  return {
    installation_id: row.id ?? null,
    account: account.login ?? null,
    state,
    permission_gap: gaps,
    permission_surplus: extra,
    event_gap: events,
  };
}

/** Turn the per-installation rows into one finding. Pure. */
export function verdict(rows) {
  const all = rows ?? [];
  if (!all.length) {
    return ['no-installations',
      'this App has no installations, so there is nothing to be behind. ' +
      'Nothing here is evidence about permissions.'];
  }
  const behind = all.filter((r) => r.state === 'upgrade-pending');
  if (behind.length) {
    return ['upgrades-pending',
      `${behind.length} of ${all.length} installation(s) are behind the App ` +
      'declaration. Their tokens carry the permission map they accepted, not ' +
      'the one the App settings page shows.'];
  }
  const ahead = all.filter((r) => r.state === 'grant-ahead');
  if (ahead.length) {
    return ['grants-ahead',
      `${ahead.length} of ${all.length} installation(s) hold more than the ` +
      'App declares, which happens after a permission is removed rather than ' +
      'added. Nothing is failing; the access is simply unused.'];
  }
  return ['all-current',
    `all ${all.length} installation(s) have accepted what the App declares.`];
}

/** Group the laggards by exactly what they are missing. Pure. */
export function cohorts(rows) {
  const out = new Map();
  for (const row of rows ?? []) {
    if (row.state !== 'upgrade-pending') continue;
    const key = row.permission_gap
      .map(([n, d, g]) => `${n} ${g} (declared ${d})`).join(', ') || 'events only';
    if (!out.has(key)) out.set(key, []);
    out.get(key).push(String(row.account ?? row.installation_id));
  }
  return Object.fromEntries([...out.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([k, v]) => [k, v.sort()]));
}

async function get(jwt, path) {
  const url = path.startsWith('/') ? API + path : path;
  const res = await fetch(url, {
    headers: {
      Authorization: `Bearer ${jwt}`,
      Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      'User-Agent': UA,
    },
  });
  let body = null;
  try { body = await res.json(); } catch { body = null; }
  return { status: res.status, body };
}

async function listInstallations(jwt, pages = 10) {
  const out = [];
  for (let page = 1; page <= pages; page += 1) {
    const { status, body } = await get(jwt, `/app/installations?per_page=100&page=${page}`);
    if (status !== 200 || !Array.isArray(body)) {
      if (page === 1) {
        console.error(`GET /app/installations returned ${status}; this ` +
          'endpoint wants the App JWT');
      }
      break;
    }
    out.push(...body);
    if (body.length < 100) break;
  }
  return out;
}

async function main() {
  const jwt = process.env.GITHUB_APP_JWT;
  if (!jwt) {
    console.error('set GITHUB_APP_JWT to the JWT your own signing code ' +
      'produced. Both reads here are App-level and neither one accepts an ' +
      'installation token');
    process.exitCode = 2;
    return;
  }
  const only = process.argv[2] ?? null;

  const app = await get(jwt, '/app');
  if (app.status !== 200 || !app.body || typeof app.body !== 'object') {
    console.error(`GET /app returned ${app.status}, so there is no ` +
      'declaration to compare against');
    process.exitCode = 2;
    return;
  }
  const declaredPermissions = app.body.permissions ?? {};
  const declaredEvents = app.body.events ?? [];
  console.log(`app declares ${Object.keys(declaredPermissions).length} ` +
    `permission(s) and ${declaredEvents.length} event(s)`);

  const installations = await listInstallations(jwt);
  let rows = installations.map((i) => classify(declaredPermissions, declaredEvents, i));
  if (only) rows = rows.filter((r) => r.account === only);

  const [state, detail] = verdict(rows);
  console.log(`${state}: ${detail}`);
  for (const row of rows) {
    if (row.state === 'upgrade-pending') {
      for (const [name, want, have] of row.permission_gap) {
        console.log(`  ${row.installation_id} ${row.account}: ${name} ${have}, declared ${want}`);
      }
      if (row.event_gap.length) {
        console.log(`  ${row.installation_id} ${row.account}: events not ` +
          `accepted: ${row.event_gap.join(', ')}`);
      }
    }
    if (row.state === 'grant-ahead') {
      for (const [name, want, have] of row.permission_surplus) {
        console.log(`  ${row.installation_id} ${row.account} holds ${name} ${have}, ${want}`);
      }
    }
  }

  if (state === 'upgrades-pending') {
    console.log('repair: an owner on each account accepts the pending ' +
      "permission request from that org's Installed GitHub Apps page. Until " +
      "then, branch on the installation's own permission map rather than on " +
      'the App declaration');
  } else if (state === 'grants-ahead') {
    console.log('repair: nothing urgent. Those installations carry access the ' +
      'App no longer declares, which is a tidy-up rather than an outage');
  }

  console.log(JSON.stringify({
    declared_permissions: declaredPermissions,
    declared_events: [...declaredEvents].map(String).sort(),
    state,
    cohorts: cohorts(rows),
    installations: rows,
  }, null, 2));
  process.exitCode = state === 'upgrades-pending' ? 1 : 0;
}

// Only run when invoked directly, so importing this module from the test file
// does not execute main(), fail on the missing JWT and set an exit code that
// fails the suite even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The test that matters most is the one where nothing is missing: an installation that granted <code>read</code> against an App that now declares <code>write</code> has every key it should have and is still broken. After that, the direction of the comparison in both senses, an unrecognised level being treated as no access rather than as an exception, and the cohort grouping actually collapsing two accounts with the same gap into one line.",
"test_py_file": "test_github_permission_upgrade_lag.py",
"test_py": '''from github_permission_upgrade_lag import (
    classify, cohorts, event_gap, permission_gap, permission_surplus, rank,
    verdict,
)

DECLARED = {"contents": "read", "issues": "write", "checks": "write"}
EVENTS = ["push", "issues", "check_run"]


def install(ident, login, permissions, events=None):
    return {"id": ident, "account": {"login": login},
            "permissions": permissions, "events": events or EVENTS}


def test_levels_are_ordered_and_absent_is_the_bottom():
    assert rank("admin") > rank("write") > rank("read") > rank(None)
    assert rank("READ ") == rank("read")


def test_an_unrecognised_level_is_treated_as_no_access():
    assert rank("superuser") == 0


def test_a_present_key_at_too_low_a_level_is_still_a_gap():
    gaps = permission_gap(DECLARED, {"contents": "read", "issues": "read",
                                     "checks": "write"})
    assert gaps == [("issues", "write", "read")]


def test_a_missing_key_reports_as_absent_rather_than_as_a_level():
    gaps = permission_gap(DECLARED, {"contents": "read", "checks": "write"})
    assert gaps == [("issues", "write", "absent")]


def test_an_installation_that_matches_has_no_gap():
    assert permission_gap(DECLARED, dict(DECLARED)) == []


def test_holding_more_than_the_app_declares_is_its_own_finding():
    extra = permission_surplus(DECLARED, {"contents": "write", "issues": "write",
                                          "checks": "write"})
    assert extra == [("contents", "read", "write")]
    undeclared = permission_surplus(DECLARED, dict(DECLARED, members="read"))
    assert undeclared == [("members", "not declared", "read")]


def test_events_are_compared_case_and_space_insensitively():
    assert event_gap(EVENTS, [" Push ", "issues", "check_run"]) == []
    assert event_gap(EVENTS, ["push"]) == ["check_run", "issues"]


def test_an_installation_behind_on_anything_is_upgrade_pending():
    row = classify(DECLARED, EVENTS,
                   install(1, "beta-inc", {"contents": "read", "checks": "write"}))
    assert row["state"] == "upgrade-pending"
    assert row["account"] == "beta-inc"
    assert row["permission_gap"] == [("issues", "write", "absent")]


def test_an_installation_behind_only_on_events_is_still_pending():
    row = classify(DECLARED, EVENTS, install(2, "acme", dict(DECLARED), ["push"]))
    assert row["state"] == "upgrade-pending"
    assert row["event_gap"] == ["check_run", "issues"]


def test_an_installation_that_agrees_is_current():
    assert classify(DECLARED, EVENTS, install(3, "acme", dict(DECLARED)))["state"] == "current"


def test_the_verdict_reports_pending_before_anything_else():
    rows = [classify(DECLARED, EVENTS, install(1, "a", dict(DECLARED))),
            classify(DECLARED, EVENTS, install(2, "b", {"contents": "read"}))]
    state, detail = verdict(rows)
    assert state == "upgrades-pending"
    assert "1 of 2" in detail


def test_a_fleet_that_is_only_ahead_is_not_an_outage():
    rows = [classify(DECLARED, EVENTS,
                     install(1, "a", dict(DECLARED, contents="write")))]
    state, detail = verdict(rows)
    assert state == "grants-ahead"
    assert "Nothing is failing" in detail


def test_an_app_with_no_installations_says_so_rather_than_all_current():
    assert verdict([])[0] == "no-installations"


def test_all_current_when_every_map_agrees():
    rows = [classify(DECLARED, EVENTS, install(i, str(i), dict(DECLARED)))
            for i in range(3)]
    assert verdict(rows)[0] == "all-current"


def test_accounts_missing_the_same_thing_collapse_into_one_cohort():
    rows = [classify(DECLARED, EVENTS, install(1, "beta", {"contents": "read", "checks": "write"})),
            classify(DECLARED, EVENTS, install(2, "gamma", {"contents": "read", "checks": "write"})),
            classify(DECLARED, EVENTS, install(3, "delta", dict(DECLARED)))]
    grouped = cohorts(rows)
    assert len(grouped) == 1
    assert list(grouped.values())[0] == ["beta", "gamma"]
''',
"test_js_file": "github-permission-upgrade-lag.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  classify, cohorts, eventGap, permissionGap, permissionSurplus, rank, verdict,
} from './github-permission-upgrade-lag.mjs';

const DECLARED = { contents: 'read', issues: 'write', checks: 'write' };
const EVENTS = ['push', 'issues', 'check_run'];

function install(id, login, permissions, events = null) {
  return { id, account: { login }, permissions, events: events ?? EVENTS };
}

test('levels are ordered and absent is the bottom', () => {
  assert.ok(rank('admin') > rank('write'));
  assert.ok(rank('write') > rank('read'));
  assert.ok(rank('read') > rank(null));
  assert.equal(rank('READ '), rank('read'));
});

test('an unrecognised level is treated as no access', () => {
  assert.equal(rank('superuser'), 0);
});

test('a present key at too low a level is still a gap', () => {
  const gaps = permissionGap(DECLARED, { contents: 'read', issues: 'read', checks: 'write' });
  assert.deepEqual(gaps, [['issues', 'write', 'read']]);
});

test('a missing key reports as absent rather than as a level', () => {
  const gaps = permissionGap(DECLARED, { contents: 'read', checks: 'write' });
  assert.deepEqual(gaps, [['issues', 'write', 'absent']]);
});

test('an installation that matches has no gap', () => {
  assert.deepEqual(permissionGap(DECLARED, { ...DECLARED }), []);
});

test('holding more than the app declares is its own finding', () => {
  assert.deepEqual(
    permissionSurplus(DECLARED, { contents: 'write', issues: 'write', checks: 'write' }),
    [['contents', 'read', 'write']],
  );
  assert.deepEqual(
    permissionSurplus(DECLARED, { ...DECLARED, members: 'read' }),
    [['members', 'not declared', 'read']],
  );
});

test('events are compared case and space insensitively', () => {
  assert.deepEqual(eventGap(EVENTS, [' Push ', 'issues', 'check_run']), []);
  assert.deepEqual(eventGap(EVENTS, ['push']), ['check_run', 'issues']);
});

test('an installation behind on anything is upgrade pending', () => {
  const row = classify(DECLARED, EVENTS, install(1, 'beta-inc', { contents: 'read', checks: 'write' }));
  assert.equal(row.state, 'upgrade-pending');
  assert.equal(row.account, 'beta-inc');
  assert.deepEqual(row.permission_gap, [['issues', 'write', 'absent']]);
});

test('an installation behind only on events is still pending', () => {
  const row = classify(DECLARED, EVENTS, install(2, 'acme', { ...DECLARED }, ['push']));
  assert.equal(row.state, 'upgrade-pending');
  assert.deepEqual(row.event_gap, ['check_run', 'issues']);
});

test('an installation that agrees is current', () => {
  assert.equal(classify(DECLARED, EVENTS, install(3, 'acme', { ...DECLARED })).state, 'current');
});

test('the verdict reports pending before anything else', () => {
  const rows = [
    classify(DECLARED, EVENTS, install(1, 'a', { ...DECLARED })),
    classify(DECLARED, EVENTS, install(2, 'b', { contents: 'read' })),
  ];
  const [state, detail] = verdict(rows);
  assert.equal(state, 'upgrades-pending');
  assert.match(detail, /1 of 2/);
});

test('a fleet that is only ahead is not an outage', () => {
  const rows = [classify(DECLARED, EVENTS, install(1, 'a', { ...DECLARED, contents: 'write' }))];
  const [state, detail] = verdict(rows);
  assert.equal(state, 'grants-ahead');
  assert.match(detail, /Nothing is failing/);
});

test('an app with no installations says so rather than all current', () => {
  assert.equal(verdict([])[0], 'no-installations');
});

test('all current when every map agrees', () => {
  const rows = [0, 1, 2].map((i) => classify(DECLARED, EVENTS, install(i, String(i), { ...DECLARED })));
  assert.equal(verdict(rows)[0], 'all-current');
});

test('accounts missing the same thing collapse into one cohort', () => {
  const rows = [
    classify(DECLARED, EVENTS, install(1, 'beta', { contents: 'read', checks: 'write' })),
    classify(DECLARED, EVENTS, install(2, 'gamma', { contents: 'read', checks: 'write' })),
    classify(DECLARED, EVENTS, install(3, 'delta', { ...DECLARED })),
  ];
  const grouped = cohorts(rows);
  assert.equal(Object.keys(grouped).length, 1);
  assert.deepEqual(Object.values(grouped)[0], ['beta', 'gamma']);
});
''',
"faq": [
 ("How is this different from a permission the App never asked for?",
  "By whether the App itself declares it. When the App never requested the permission, GET /app shows it absent, the failing response names what it wanted in its accepted-permissions header, and the repair is to edit the App. That case has its own note. Here GET /app shows the permission present, so the header would name something the App genuinely holds, and the diff that matters is between the App and each installation. The quick discriminator is that this failure affects some installations and not others; a genuinely missing permission fails everywhere at once."),
 ("Why does the App settings page look correct?",
  "Because it is correct, about the App. It shows the declaration: what this App asks for from anyone who installs it. It does not show the grant, which is what one account agreed to at one moment and which is what tokens for that account actually carry. The two are equal at install time and drift the instant the App is edited. This is why the incident channel fills up with screenshots that all show the right thing while the integration keeps failing for a third of customers."),
 ("Can the App force the upgrade, or re-request it?",
  "It cannot force it. GitHub emails the account's owners with the request when the App's permissions change, and it applies when one of them accepts from the organization's Installed GitHub Apps page. You can prompt again by sending people the direct link to that page, which is more effective than the email for accounts where the original went to someone who has left. Everything about this is a write and a human decision, which is why this script reports rather than acts."),
 ("What should the App do while an installation is behind?",
  "Branch on the installation's own permission map, which you have already read, rather than on what the App declares. Then a laggard degrades to a feature that is switched off with a clear log line, instead of to a 403 that surfaces as a support ticket weeks later. It also makes the failure legible in your own telemetry: you can count installations by capability rather than discovering the split from a customer who happened to complain."),
 ("An installation holds more than the App declares. Is that a problem?",
  "It is not an outage and it is worth writing down. That state appears after a permission is removed from the App rather than added, since removal does not retroactively narrow grants that were already accepted. Those installations carry access the App no longer claims to need, which is a real if quiet security finding: the blast radius of a leaked token for those accounts is larger than your documentation says. Reinstallation resets it, which is a heavier ask than an acceptance."),
],
"related": [
 ("/github/app-permission-missing/", "Resource not accessible by integration"),
 ("/github/app-not-subscribed-to-event/", "An App event subscription that was never declared"),
 ("/github/installation-suspended/", "An installation suspended rather than removed"),
],
"citations": [CITE_EDIT_PERMS, CITE_APPS_REST, CITE_APP_PERMS, CITE_INSTALLATIONS],
},

{
"slug": "app-not-subscribed-to-event",
"title": "The App was never subscribed to the event it waits for",
"description": "A GitHub App receives only the events it declares, and can only declare ones its permissions gate. GET /app names both, so the gap is readable.",
"h1": "the App was never subscribed to the event it waits for",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github app not receiving webhook events",
             "github app subscribe to event permission",
             "pull_request_review_thread event not received",
             "github app events array GET /app",
             "app webhook handler never fires"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The handler was written, unit tested against a payload fixture, code reviewed and shipped. In production it has never run. Not once, not slowly, not with an error &mdash; the delivery log has thousands of entries and none of them is that event. There is nothing to debug, because nothing happened.",
"short_answer": """<p>A GitHub App receives only the webhook events it subscribes to, and the subscription is a property of the App itself. <code>GET /app</code> with the App's JWT returns the <code>events</code> array: if the event you are waiting for is not in it, no delivery for that event has ever been created and none ever will be until it is.</p>
<p>The part that catches people is that the subscription is gated by permission. An App can only declare an event whose permission it holds &mdash; <code>pull_request</code> needs <code>pull_requests</code>, <code>check_run</code> needs <code>checks</code> &mdash; and when the permission is absent the checkbox is not offered at all, so the subscription silently never happens and nothing records the attempt. The repair therefore has three ordered steps: add the permission, subscribe to the event, then get every installation to accept the upgrade. Doing only the last is the common mistake.</p>
<p>This is the App-side twin of <a href="/github/webhook-event-not-subscribed/">the note about a repository webhook that is not subscribed to an event</a>, and the difference is worth being exact about. That one is a hook you created on a repository or an organization, whose <code>events</code> list you read from <code>GET /repos/{owner}/{repo}/hooks</code> and which a repo admin can widen in ten seconds. This one is the subscription declared by the App, read from <code>GET /app</code>, gated by App permissions, and inert until installations consent.</p>""",
"problem": """<p>The absence of evidence is the whole difficulty. Every other webhook failure leaves a trace &mdash; a delivery with a 500, a timeout, a signature rejection &mdash; and can be pulled up in the delivery log and stared at. An unsubscribed event produces no delivery, so the log is not empty, it is full of other things, and the thing you are looking for is not there to be looked at. There is no error to search for and no correlation id to follow.</p>
<p>So the search goes to the receiver, and stays there. The routing table gets instrumented, the signature verification gets a debug branch, the ingress logs get grepped for the event name, and every one of those investigations correctly reports that nothing arrived. Hours go into proving a negative about code that was never involved. The strong smell that ought to redirect it &mdash; that <em>other</em> events arrive perfectly &mdash; reads as reassurance instead of as the clue it is.</p>
<p>The permission gate is what makes it stick. Somebody eventually goes to the App's settings to subscribe, finds the event is not offered, and concludes that GitHub does not support it. The event is real and documented; it is simply hidden behind a permission the App does not hold, and the settings page does not explain the connection. That is a very short step from filing the whole thing as a platform limitation and writing a polling loop instead.</p>""",
"why": """<p><strong>The App's subscription list is a single object.</strong> One App, one <code>events</code> array, one webhook URL. Unlike repository hooks there is no per-account variation to chase: if the array does not contain the event, no installation of the App receives it, anywhere. That makes the check cheap and the answer total.</p>
<p><strong>Permissions gate which events can be declared.</strong> Each event is tied to a permission that governs the resource it describes, and the App must hold that permission before the event can be selected. This is why so many reports of a missing event turn into a report that the event does not exist: the interface omits what you are not entitled to, without saying why.</p>
<p><strong>Subscribing is a permission change, so it needs acceptance.</strong> Adding the gating permission edits the App, which puts every existing installation into the pending state described in <a href="/github/app-permission-upgrade-not-accepted/">the note on unaccepted permission upgrades</a>. The event will start arriving from accounts that accept and not from the others, which produces a second, later, partial-looking failure if you were not expecting it.</p>
<p><strong>The delivery log is corroboration, not proof.</strong> <code>GET /app/hook/deliveries</code> shows the events that actually arrived within the retention window. An event absent from it is consistent with not being subscribed and also with simply not having happened &mdash; nobody opened a pull request this week &mdash; so it can confirm a finding the <code>events</code> array already made and it cannot make one on its own.</p>
<p><strong>Names are exact and the mapping is curated.</strong> GitHub spells events with underscores, and there is no endpoint that returns the event-to-permission mapping, so the table in the script is written from the documentation rather than fetched. An event it has never heard of gets reported as unknown, with the subscription answer given plainly and the permission answer withheld, which is more useful than a confident guess about a gate.</p>""",
"steps": [
 {"h": "Write down the events your handlers actually implement",
  "body": """<p>Not the ones in the design document. Grep the receiver for the event names it switches on, and use exactly those spellings. This list is the input to the whole check, and the most common way the check comes back clean on a broken system is that the list was written from memory.</p>"""},
 {"h": "Read the App's declaration",
  "body": """<p><code>GET /app</code> with the App's JWT returns <code>events</code> and <code>permissions</code> together, which is convenient because you need both. Anything in your handler list and not in <code>events</code> has never been delivered. There is no per-installation nuance at this step: the App subscribes or it does not.</p>"""},
 {"h": "Check whether the gating permission is even held",
  "body": """<p>For each unsubscribed event, look up the permission that gates it and check the App's map. Absent means you cannot simply tick a box &mdash; the box will not be there &mdash; and the first step is the permission. Present means the subscription is a one-line change to the App, followed by the acceptance round.</p>"""},
 {"h": "Corroborate against what has actually arrived",
  "body": """<p><code>GET /app/hook/deliveries</code> lists recent deliveries with an <code>event</code> field each. Collect the distinct values. A subscribed event that has never arrived is usually quiet rather than broken, and saying so stops the next person from unsubscribing something that works.</p>"""},
 {"h": "Do the three steps in order",
  "body": """<p>Add the permission, subscribe to the event, then get each installation's owner to accept. Skipping the first leaves the checkbox missing; skipping the last leaves the event arriving from some accounts and not others, which looks like a completely different bug and gets investigated as one.</p>"""},
],
"verify": """<p>After the subscription is added and accepted, the same read moves the event from <code>not-subscribed</code> to <code>subscribed</code>, and the delivery log starts carrying it the next time one happens.</p>
<pre><code class="language-bash">GITHUB_APP_JWT=$(python3 sign_app_jwt.py) python3 github_app_event_subscriptions.py \\
  --handles push,pull_request,pull_request_review_thread,release
# app subscribes to 2 event(s), holds 3 permission(s)
# handlers-unreachable: 2 of 4 handled event(s) can never fire
#   pull_request_review_thread: not subscribed, and the pull_requests
#   permission that gates it is not held
#   release: not subscribed, but the contents permission that gates it is held
# repair, in order: add pull_requests, subscribe, then have every
# installation accept the upgrade

# after all three steps
# all-subscribed: every handled event is declared by the App</code></pre>""",
"code_intro": "Two GETs and a curated table. The subscription half is a set membership test and is exact; the permission half is a lookup in a mapping written from the documentation, because nothing in the API returns which permission gates which event. That asymmetry is reflected in the output: an event the table does not know still gets a truthful subscription answer, and gets <code>unknown</code> rather than a guess for the gate. The normalisation is deliberately narrow &mdash; case and surrounding space only &mdash; so that a genuinely misspelled event name stays visible instead of being silently corrected.",
"py_file": "github_app_event_subscriptions.py",
"py": '''"""Find webhook events a GitHub App's handlers wait for and never receive.

Read only. Two GETs with the App's JWT: the App's own record and its recent
webhook deliveries. Nothing is subscribed, permitted or changed. Subscribing is
an edit to the App and then a human acceptance on every installation, so the
script prints the three steps in the order they have to happen.

A GitHub App receives only the events it declares, and it can only declare an
event whose gating permission it holds. When the permission is absent the
subscription checkbox is not offered at all, so the subscription silently never
happens and nothing anywhere records the attempt.

This is the App-side case. A repository or organization webhook has its own
events list, read from the repository hooks endpoint, which is a different
object with a different repair.

Environment:

    GITHUB_APP_JWT   the JWT your own signing code produced
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_app_event_subscriptions")

API = "https://api.github.com"
UA = "github-app-event-subscriptions/1.0"

# Which App permission gates which event. Nothing in the API returns this, so
# the table is written from the documentation rather than fetched, and an event
# that is not in it is reported as unknown rather than guessed at. A wrong
# answer here sends somebody to request a permission they do not need.
EVENT_PERMISSION = {
    "check_run": "checks",
    "check_suite": "checks",
    "commit_comment": "contents",
    "create": "contents",
    "delete": "contents",
    "deployment": "deployments",
    "deployment_status": "deployments",
    "fork": "metadata",
    "issue_comment": "issues",
    "issues": "issues",
    "label": "metadata",
    "member": "members",
    "membership": "members",
    "milestone": "issues",
    "organization": "members",
    "public": "metadata",
    "pull_request": "pull_requests",
    "pull_request_review": "pull_requests",
    "pull_request_review_comment": "pull_requests",
    "pull_request_review_thread": "pull_requests",
    "push": "contents",
    "release": "contents",
    "repository": "metadata",
    "repository_dispatch": "contents",
    "star": "metadata",
    "status": "statuses",
    "team_add": "members",
    "watch": "metadata",
    "workflow_dispatch": "actions",
    "workflow_job": "actions",
    "workflow_run": "actions",
}

# Every event carries metadata implicitly, so an App that holds nothing still
# holds this one. Listing it keeps the "not permitted" branch honest.
ALWAYS_HELD = ("metadata",)


def normalize(event):
    """An event name reduced to the form GitHub spells it in. Pure.

    Case and surrounding whitespace only. A genuinely misspelled name is left
    misspelled so it stays visible as unknown, because quietly correcting it
    would hide the actual mistake in a report about missing events.
    """
    return str(event or "").strip().lower()


def gating_permission(event):
    """The App permission that gates an event, or None if unknown. Pure."""
    return EVENT_PERMISSION.get(normalize(event))


def holds(permissions, name):
    """Whether the App holds a permission at read or better. Pure."""
    if name in ALWAYS_HELD:
        return True
    value = (permissions or {}).get(name)
    return bool(value) and str(value).strip().lower() != "none"


def seen_events(deliveries):
    """Distinct event names in a delivery log page. Pure."""
    out = set()
    for row in deliveries or []:
        if isinstance(row, dict) and row.get("event"):
            out.add(normalize(row["event"]))
    return out


def subscription_state(event, subscribed, permissions, seen=None):
    """Sort one handled event into a state. Pure.

    subscribed is the App's events array, permissions its permission map, seen
    the distinct events observed in the delivery log. seen only ever refines a
    positive answer: an event that has not arrived may simply not have
    happened, so its absence is never a finding on its own.
    """
    name = normalize(event)
    declared = {normalize(e) for e in (subscribed or [])}
    gate = gating_permission(name)
    if name in declared:
        if seen is not None and name in seen:
            return ("subscribed-and-arriving",
                    "%s is declared by the App and has arrived recently." % name)
        return ("subscribed-not-yet-seen",
                "%s is declared by the App but has not arrived in the "
                "retention window, which usually means it has not happened "
                "rather than that it is broken." % name)
    if gate is None:
        return ("not-subscribed-gate-unknown",
                "%s is not declared by the App, so it has never been "
                "delivered. This script does not know which permission gates "
                "it; check the published event list before requesting one."
                % name)
    if not holds(permissions, gate):
        return ("not-subscribed-blocked",
                "%s is not declared, and the %s permission that gates it is "
                "not held. The subscription cannot be ticked until the "
                "permission is added." % (name, gate))
    return ("not-subscribed-permitted",
            "%s is not declared, but the %s permission that gates it is held, "
            "so subscribing is an edit to the App followed by an acceptance "
            "round." % (name, gate))


def rows(handled, subscribed, permissions, seen=None):
    """One row per handled event, in the order they were given. Pure."""
    out = []
    for event in handled or []:
        state, detail = subscription_state(event, subscribed, permissions, seen)
        out.append({"event": normalize(event), "state": state, "detail": detail,
                    "gated_by": gating_permission(event)})
    return out


def verdict(report):
    """Turn the rows into one finding. Pure."""
    report = report or []
    if not report:
        return ("nothing-handled",
                "no handled events were supplied, so there is nothing to "
                "compare the App's subscriptions against.")
    unreachable = [r for r in report if r["state"].startswith("not-subscribed")]
    if unreachable:
        return ("handlers-unreachable",
                "%d of %d handled event(s) can never fire, because the App "
                "does not declare them." % (len(unreachable), len(report)))
    quiet = [r for r in report if r["state"] == "subscribed-not-yet-seen"]
    if quiet:
        return ("all-subscribed-some-quiet",
                "every handled event is declared. %d of them has not arrived "
                "in the retention window, which is not by itself a fault."
                % len(quiet))
    return ("all-subscribed",
            "every handled event is declared by the App and arriving.")


def repair_steps(report):
    """The ordered repair, as lines. Pure.

    Order matters and is the point of the note: add the permission, subscribe,
    then have installations accept. Doing only the last is the usual mistake.
    """
    blocked = sorted({r["gated_by"] for r in report or []
                      if r["state"] == "not-subscribed-blocked" and r["gated_by"]})
    missing = sorted({r["event"] for r in report or []
                      if r["state"].startswith("not-subscribed")})
    if not missing:
        return []
    steps = []
    if blocked:
        steps.append("add the %s permission to the App; until then the "
                     "subscription cannot be selected at all"
                     % ", ".join(blocked))
    steps.append("subscribe the App to %s" % ", ".join(missing))
    steps.append("have an owner on every installation accept the resulting "
                 "permission request, or the event will arrive from some "
                 "accounts and not others")
    return steps


def get(session, path):
    """One GET. Returns (status, json-or-None)."""
    url = API + path if path.startswith("/") else path
    r = session.get(url, timeout=30)
    try:
        body = r.json()
    except ValueError:
        body = None
    return r.status_code, body


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--handles", default="",
                    help="comma-separated event names your handlers implement, "
                         "spelled the way GitHub spells them")
    args = ap.parse_args()

    jwt = os.environ.get("GITHUB_APP_JWT")
    if not jwt:
        log.error("set GITHUB_APP_JWT to the JWT your own signing code "
                  "produced. The App's events array is on the App record, "
                  "which an installation token cannot read")
        return 2

    handled = [h for h in (p.strip() for p in args.handles.split(",")) if h]
    if not handled:
        log.error("pass --handles with the event names your receiver "
                  "implements; without them there is nothing to compare")
        return 2

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + jwt,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": UA,
    })

    status, app = get(session, "/app")
    if status != 200 or not isinstance(app, dict):
        log.error("GET /app returned %d, so the App's subscriptions cannot be "
                  "read", status)
        return 2
    subscribed = app.get("events") or []
    permissions = app.get("permissions") or {}
    log.info("app subscribes to %d event(s), holds %d permission(s)",
             len(subscribed), len(permissions))

    seen = None
    d_status, deliveries = get(session, "/app/hook/deliveries?per_page=100")
    if d_status == 200 and isinstance(deliveries, list):
        seen = seen_events(deliveries)
        log.info("delivery log shows %d distinct event(s) in the retention "
                 "window", len(seen))
    else:
        log.info("delivery log unavailable (%d); the subscription answer does "
                 "not depend on it", d_status)

    report = rows(handled, subscribed, permissions, seen)
    state, detail = verdict(report)
    log.info("%s: %s", state, detail)
    for row in report:
        if row["state"] != "subscribed-and-arriving":
            log.info("  %s", row["detail"])

    for i, line in enumerate(repair_steps(report), start=1):
        log.info("repair step %d: %s", i, line)

    print(json.dumps({"subscribed": sorted(normalize(e) for e in subscribed),
                      "permissions": permissions,
                      "seen_in_deliveries": sorted(seen) if seen is not None else None,
                      "state": state, "events": report}, indent=2, default=str))
    return 1 if state == "handlers-unreachable" else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-app-event-subscriptions.mjs",
"js": '''/**
 * Find webhook events a GitHub App's handlers wait for and never receive.
 *
 * Read only. Two GETs with the App's JWT: the App's own record and its recent
 * webhook deliveries. Subscribing is an edit to the App and then a human
 * acceptance on every installation, so the script prints the three steps in
 * the order they have to happen.
 *
 * This is the App-side case. A repository or organization webhook has its own
 * events list, which is a different object with a different repair.
 *
 * Environment:
 *   GITHUB_APP_JWT   the JWT your own signing code produced
 */
const API = 'https://api.github.com';
const UA = 'github-app-event-subscriptions/1.0';

/** Which App permission gates which event. Curated, not fetched. */
export const EVENT_PERMISSION = {
  check_run: 'checks',
  check_suite: 'checks',
  commit_comment: 'contents',
  create: 'contents',
  delete: 'contents',
  deployment: 'deployments',
  deployment_status: 'deployments',
  fork: 'metadata',
  issue_comment: 'issues',
  issues: 'issues',
  label: 'metadata',
  member: 'members',
  membership: 'members',
  milestone: 'issues',
  organization: 'members',
  public: 'metadata',
  pull_request: 'pull_requests',
  pull_request_review: 'pull_requests',
  pull_request_review_comment: 'pull_requests',
  pull_request_review_thread: 'pull_requests',
  push: 'contents',
  release: 'contents',
  repository: 'metadata',
  repository_dispatch: 'contents',
  star: 'metadata',
  status: 'statuses',
  team_add: 'members',
  watch: 'metadata',
  workflow_dispatch: 'actions',
  workflow_job: 'actions',
  workflow_run: 'actions',
};

/** Permissions every App holds implicitly. */
export const ALWAYS_HELD = ['metadata'];

/** An event name reduced to the form GitHub spells it in. Pure. */
export function normalize(event) {
  return String(event ?? '').trim().toLowerCase();
}

/** The App permission that gates an event, or null if unknown. Pure. */
export function gatingPermission(event) {
  return EVENT_PERMISSION[normalize(event)] ?? null;
}

/** Whether the App holds a permission at read or better. Pure. */
export function holds(permissions, name) {
  if (ALWAYS_HELD.includes(name)) return true;
  const value = (permissions ?? {})[name];
  return Boolean(value) && String(value).trim().toLowerCase() !== 'none';
}

/** Distinct event names in a delivery log page. Pure. */
export function seenEvents(deliveries) {
  const out = new Set();
  for (const row of deliveries ?? []) {
    if (row && typeof row === 'object' && row.event) out.add(normalize(row.event));
  }
  return out;
}

/** Sort one handled event into a state. Pure. */
export function subscriptionState(event, subscribed, permissions, seen = null) {
  const name = normalize(event);
  const declared = new Set((subscribed ?? []).map(normalize));
  const gate = gatingPermission(name);
  if (declared.has(name)) {
    if (seen && seen.has(name)) {
      return ['subscribed-and-arriving',
        `${name} is declared by the App and has arrived recently.`];
    }
    return ['subscribed-not-yet-seen',
      `${name} is declared by the App but has not arrived in the retention ` +
      'window, which usually means it has not happened rather than that it ' +
      'is broken.'];
  }
  if (gate === null) {
    return ['not-subscribed-gate-unknown',
      `${name} is not declared by the App, so it has never been delivered. ` +
      'This script does not know which permission gates it; check the ' +
      'published event list before requesting one.'];
  }
  if (!holds(permissions, gate)) {
    return ['not-subscribed-blocked',
      `${name} is not declared, and the ${gate} permission that gates it is ` +
      'not held. The subscription cannot be ticked until the permission is added.'];
  }
  return ['not-subscribed-permitted',
    `${name} is not declared, but the ${gate} permission that gates it is ` +
    'held, so subscribing is an edit to the App followed by an acceptance round.'];
}

/** One row per handled event, in the order they were given. Pure. */
export function rows(handled, subscribed, permissions, seen = null) {
  return (handled ?? []).map((event) => {
    const [state, detail] = subscriptionState(event, subscribed, permissions, seen);
    return { event: normalize(event), state, detail, gated_by: gatingPermission(event) };
  });
}

/** Turn the rows into one finding. Pure. */
export function verdict(report) {
  const all = report ?? [];
  if (!all.length) {
    return ['nothing-handled',
      'no handled events were supplied, so there is nothing to compare the ' +
      "App's subscriptions against."];
  }
  const unreachable = all.filter((r) => r.state.startsWith('not-subscribed'));
  if (unreachable.length) {
    return ['handlers-unreachable',
      `${unreachable.length} of ${all.length} handled event(s) can never ` +
      'fire, because the App does not declare them.'];
  }
  const quiet = all.filter((r) => r.state === 'subscribed-not-yet-seen');
  if (quiet.length) {
    return ['all-subscribed-some-quiet',
      `every handled event is declared. ${quiet.length} of them has not ` +
      'arrived in the retention window, which is not by itself a fault.'];
  }
  return ['all-subscribed',
    'every handled event is declared by the App and arriving.'];
}

/** The ordered repair, as lines. Pure. */
export function repairSteps(report) {
  const all = report ?? [];
  const blocked = [...new Set(all
    .filter((r) => r.state === 'not-subscribed-blocked' && r.gated_by)
    .map((r) => r.gated_by))].sort();
  const missing = [...new Set(all
    .filter((r) => r.state.startsWith('not-subscribed'))
    .map((r) => r.event))].sort();
  if (!missing.length) return [];
  const steps = [];
  if (blocked.length) {
    steps.push(`add the ${blocked.join(', ')} permission to the App; until ` +
      'then the subscription cannot be selected at all');
  }
  steps.push(`subscribe the App to ${missing.join(', ')}`);
  steps.push('have an owner on every installation accept the resulting ' +
    'permission request, or the event will arrive from some accounts and not others');
  return steps;
}

async function get(jwt, path) {
  const url = path.startsWith('/') ? API + path : path;
  const res = await fetch(url, {
    headers: {
      Authorization: `Bearer ${jwt}`,
      Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      'User-Agent': UA,
    },
  });
  let body = null;
  try { body = await res.json(); } catch { body = null; }
  return { status: res.status, body };
}

async function main() {
  const jwt = process.env.GITHUB_APP_JWT;
  if (!jwt) {
    console.error('set GITHUB_APP_JWT to the JWT your own signing code ' +
      "produced. The App's events array is on the App record, which an " +
      'installation token cannot read');
    process.exitCode = 2;
    return;
  }
  const handled = (process.argv[2] ?? '').split(',').map((s) => s.trim()).filter(Boolean);
  if (!handled.length) {
    console.error('pass the event names your receiver implements as the first ' +
      'argument, comma separated; without them there is nothing to compare');
    process.exitCode = 2;
    return;
  }

  const app = await get(jwt, '/app');
  if (app.status !== 200 || !app.body || typeof app.body !== 'object') {
    console.error(`GET /app returned ${app.status}, so the App's ` +
      'subscriptions cannot be read');
    process.exitCode = 2;
    return;
  }
  const subscribed = app.body.events ?? [];
  const permissions = app.body.permissions ?? {};
  console.log(`app subscribes to ${subscribed.length} event(s), holds ` +
    `${Object.keys(permissions).length} permission(s)`);

  let seen = null;
  const log = await get(jwt, '/app/hook/deliveries?per_page=100');
  if (log.status === 200 && Array.isArray(log.body)) {
    seen = seenEvents(log.body);
    console.log(`delivery log shows ${seen.size} distinct event(s) in the ` +
      'retention window');
  } else {
    console.log(`delivery log unavailable (${log.status}); the subscription ` +
      'answer does not depend on it');
  }

  const report = rows(handled, subscribed, permissions, seen);
  const [state, detail] = verdict(report);
  console.log(`${state}: ${detail}`);
  for (const row of report) {
    if (row.state !== 'subscribed-and-arriving') console.log(`  ${row.detail}`);
  }
  repairSteps(report).forEach((line, i) => {
    console.log(`repair step ${i + 1}: ${line}`);
  });

  console.log(JSON.stringify({
    subscribed: subscribed.map(normalize).sort(),
    permissions,
    seen_in_deliveries: seen ? [...seen].sort() : null,
    state,
    events: report,
  }, null, 2));
  process.exitCode = state === 'handlers-unreachable' ? 1 : 0;
}

// Only run when invoked directly, so importing this module from the test file
// does not execute main(), fail on the missing JWT and set an exit code that
// fails the suite even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Three distinctions carry the whole script and each gets tests. An unsubscribed event whose permission is missing is not the same finding as one whose permission is held, because only the first has a step before the checkbox. A subscribed event that has not arrived is not a fault, so the delivery log must never be allowed to turn silence into a finding. And an event the table has never heard of must still get a truthful subscription answer while withholding the permission one.",
"test_py_file": "test_github_app_event_subscriptions.py",
"test_py": '''from github_app_event_subscriptions import (
    gating_permission, holds, normalize, repair_steps, rows, seen_events,
    subscription_state, verdict,
)

SUBSCRIBED = ["push", "issues"]
PERMISSIONS = {"contents": "read", "issues": "write", "metadata": "read"}


def test_names_are_normalised_for_case_and_space_only():
    assert normalize("  Pull_Request ") == "pull_request"
    assert normalize("pull-request") == "pull-request"


def test_a_misspelled_event_stays_unknown_rather_than_being_corrected():
    assert gating_permission("pull-request") is None
    assert gating_permission("pull_request") == "pull_requests"


def test_metadata_counts_as_held_even_when_absent_from_the_map():
    assert holds({}, "metadata")
    assert not holds({}, "checks")
    assert not holds({"checks": "none"}, "checks")
    assert holds({"checks": "read"}, "checks")


def test_an_unsubscribed_event_without_its_permission_is_blocked():
    state, detail = subscription_state("pull_request_review_thread", SUBSCRIBED,
                                       PERMISSIONS)
    assert state == "not-subscribed-blocked"
    assert "pull_requests permission" in detail
    assert "cannot be ticked" in detail


def test_an_unsubscribed_event_whose_permission_is_held_is_a_lighter_repair():
    state, detail = subscription_state("release", SUBSCRIBED, PERMISSIONS)
    assert state == "not-subscribed-permitted"
    assert "contents permission" in detail


def test_an_unknown_event_gets_a_subscription_answer_and_no_permission_guess():
    state, detail = subscription_state("sponsorship_tier_change", SUBSCRIBED,
                                       PERMISSIONS)
    assert state == "not-subscribed-gate-unknown"
    assert "does not know which permission" in detail


def test_a_subscribed_event_seen_in_the_log_is_healthy():
    seen = seen_events([{"event": "push"}, {"event": "Push"}, {"nope": 1}])
    assert seen == {"push"}
    assert subscription_state("push", SUBSCRIBED, PERMISSIONS, seen)[0] == \\
        "subscribed-and-arriving"


def test_silence_in_the_delivery_log_is_never_a_finding_on_its_own():
    state, detail = subscription_state("issues", SUBSCRIBED, PERMISSIONS, set())
    assert state == "subscribed-not-yet-seen"
    assert "rather than that it is broken" in detail


def test_any_unsubscribed_handler_makes_the_whole_report_unreachable():
    report = rows(["push", "release"], SUBSCRIBED, PERMISSIONS, {"push"})
    state, detail = verdict(report)
    assert state == "handlers-unreachable"
    assert "1 of 2" in detail


def test_a_fully_subscribed_quiet_app_is_not_reported_as_broken():
    report = rows(["push", "issues"], SUBSCRIBED, PERMISSIONS, {"push"})
    assert verdict(report)[0] == "all-subscribed-some-quiet"


def test_a_fully_subscribed_busy_app_is_clean():
    report = rows(["push", "issues"], SUBSCRIBED, PERMISSIONS, {"push", "issues"})
    assert verdict(report)[0] == "all-subscribed"


def test_no_handled_events_is_not_a_pass():
    assert verdict([])[0] == "nothing-handled"


def test_the_repair_puts_the_permission_before_the_subscription():
    report = rows(["pull_request_review_thread"], SUBSCRIBED, PERMISSIONS)
    steps = repair_steps(report)
    assert len(steps) == 3
    assert "add the pull_requests permission" in steps[0]
    assert "subscribe the App to pull_request_review_thread" in steps[1]
    assert "accept" in steps[2]


def test_the_permission_step_is_skipped_when_the_permission_is_already_held():
    steps = repair_steps(rows(["release"], SUBSCRIBED, PERMISSIONS))
    assert len(steps) == 2
    assert steps[0].startswith("subscribe the App to release")


def test_a_clean_report_has_no_repair():
    assert repair_steps(rows(["push"], SUBSCRIBED, PERMISSIONS, {"push"})) == []
''',
"test_js_file": "github-app-event-subscriptions.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  gatingPermission, holds, normalize, repairSteps, rows, seenEvents,
  subscriptionState, verdict,
} from './github-app-event-subscriptions.mjs';

const SUBSCRIBED = ['push', 'issues'];
const PERMISSIONS = { contents: 'read', issues: 'write', metadata: 'read' };

test('names are normalised for case and space only', () => {
  assert.equal(normalize('  Pull_Request '), 'pull_request');
  assert.equal(normalize('pull-request'), 'pull-request');
});

test('a misspelled event stays unknown rather than being corrected', () => {
  assert.equal(gatingPermission('pull-request'), null);
  assert.equal(gatingPermission('pull_request'), 'pull_requests');
});

test('metadata counts as held even when absent from the map', () => {
  assert.ok(holds({}, 'metadata'));
  assert.ok(!holds({}, 'checks'));
  assert.ok(!holds({ checks: 'none' }, 'checks'));
  assert.ok(holds({ checks: 'read' }, 'checks'));
});

test('an unsubscribed event without its permission is blocked', () => {
  const [state, detail] = subscriptionState('pull_request_review_thread', SUBSCRIBED, PERMISSIONS);
  assert.equal(state, 'not-subscribed-blocked');
  assert.match(detail, /pull_requests permission/);
  assert.match(detail, /cannot be ticked/);
});

test('an unsubscribed event whose permission is held is a lighter repair', () => {
  const [state, detail] = subscriptionState('release', SUBSCRIBED, PERMISSIONS);
  assert.equal(state, 'not-subscribed-permitted');
  assert.match(detail, /contents permission/);
});

test('an unknown event gets a subscription answer and no permission guess', () => {
  const [state, detail] = subscriptionState('sponsorship_tier_change', SUBSCRIBED, PERMISSIONS);
  assert.equal(state, 'not-subscribed-gate-unknown');
  assert.match(detail, /does not know which permission/);
});

test('a subscribed event seen in the log is healthy', () => {
  const seen = seenEvents([{ event: 'push' }, { event: 'Push' }, { nope: 1 }]);
  assert.deepEqual([...seen], ['push']);
  assert.equal(subscriptionState('push', SUBSCRIBED, PERMISSIONS, seen)[0],
    'subscribed-and-arriving');
});

test('silence in the delivery log is never a finding on its own', () => {
  const [state, detail] = subscriptionState('issues', SUBSCRIBED, PERMISSIONS, new Set());
  assert.equal(state, 'subscribed-not-yet-seen');
  assert.match(detail, /rather than that it is broken/);
});

test('any unsubscribed handler makes the whole report unreachable', () => {
  const report = rows(['push', 'release'], SUBSCRIBED, PERMISSIONS, new Set(['push']));
  const [state, detail] = verdict(report);
  assert.equal(state, 'handlers-unreachable');
  assert.match(detail, /1 of 2/);
});

test('a fully subscribed quiet app is not reported as broken', () => {
  const report = rows(['push', 'issues'], SUBSCRIBED, PERMISSIONS, new Set(['push']));
  assert.equal(verdict(report)[0], 'all-subscribed-some-quiet');
});

test('a fully subscribed busy app is clean', () => {
  const report = rows(['push', 'issues'], SUBSCRIBED, PERMISSIONS, new Set(['push', 'issues']));
  assert.equal(verdict(report)[0], 'all-subscribed');
});

test('no handled events is not a pass', () => {
  assert.equal(verdict([])[0], 'nothing-handled');
});

test('the repair puts the permission before the subscription', () => {
  const steps = repairSteps(rows(['pull_request_review_thread'], SUBSCRIBED, PERMISSIONS));
  assert.equal(steps.length, 3);
  assert.match(steps[0], /add the pull_requests permission/);
  assert.match(steps[1], /subscribe the App to pull_request_review_thread/);
  assert.match(steps[2], /accept/);
});

test('the permission step is skipped when the permission is already held', () => {
  const steps = repairSteps(rows(['release'], SUBSCRIBED, PERMISSIONS));
  assert.equal(steps.length, 2);
  assert.ok(steps[0].startsWith('subscribe the App to release'));
});

test('a clean report has no repair', () => {
  assert.deepEqual(repairSteps(rows(['push'], SUBSCRIBED, PERMISSIONS, new Set(['push']))), []);
});
''',
"faq": [
 ("How is this different from a repository webhook that is not subscribed?",
  "They are two different objects with two different repairs. A repository or organization webhook is something you created on a repository; its events list is read from the repository hooks endpoint, a repo admin can widen it in seconds, and nothing about it is gated by App permissions. This note is about the subscription declared by the App itself, read from GET /app, which applies to every installation at once, cannot include an event whose permission the App lacks, and does not take effect on existing installations until their owners accept. If you are not using a GitHub App at all, you want the repository hook note instead."),
 ("Why is the event missing from the subscription list in the App settings?",
  "Because the App does not hold the permission that gates it, and the interface omits what you are not entitled to rather than showing it disabled with an explanation. This is the single most common reason people conclude that GitHub does not support an event they can plainly see documented. Add the gating permission first and the checkbox appears. The script names the permission for you precisely so this step does not turn into a search."),
 ("The delivery log has no entries for the event. Is that the proof?",
  "No, and treating it as proof is how a working subscription gets removed. An event absent from the delivery log is equally consistent with nobody having triggered it in the retention window, which for a quiet repository is entirely normal. The authoritative answer is the events array on the App record, which says what will ever be delivered rather than what happened to be delivered lately. The log is useful for the opposite direction: an event that has arrived is definitely subscribed."),
 ("I subscribed to the event and it still does not arrive for some accounts.",
  "That is the acceptance step, and it is a separate note. Adding the gating permission changed the App's permissions, so every installation that existed before the change is still running on the grant it accepted, and the new subscription is inert for those accounts until an owner accepts. The symptom is characteristic: the event arrives from newly installed accounts and from accounts that acted on the email, and not from anybody else, which looks random until you list the installations."),
 ("Can the script subscribe the App for me?",
  "No. Editing an App's events and permissions is a write, and this section's scripts never write. It also would not finish the job: the acceptance round is a human act performed by an account owner on every existing installation, and no API call you make can substitute for it. What the script does is print the three steps in the order they have to happen, with the permission named, which is the part people get wrong when they work from the settings page alone."),
],
"related": [
 ("/github/webhook-event-not-subscribed/", "A repository hook not subscribed to an event"),
 ("/github/app-permission-upgrade-not-accepted/", "A permission upgrade installations never accepted"),
 ("/github/webhook-deliveries-failing/", "Webhook deliveries that have been failing unnoticed"),
],
"citations": [CITE_WEBHOOK_EVENTS, CITE_APP_WEBHOOKS, CITE_APPS_REST, CITE_APP_PERMS],
},

{
"slug": "app-token-scoped-down-too-far",
"title": "The installation token was narrowed below what the job needs",
"description": "An installation token can be minted for fewer repositories and permissions than the installation holds. One code path 404s while every other one works.",
"h1": "the installation token was narrowed below what the job needs",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github app installation token repository_ids",
             "scoped installation access token 404",
             "github app 404 on repo it is installed on",
             "installation token permissions subset",
             "narrow github app token repositories"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The App is installed on the repository. You can see the installation, the repository is in its list, the permissions are generous, and one job gets <code>404</code> every time it touches that repository. The other four jobs, using the same App, on the same repository, are fine. Nobody has changed the App in months.",
"short_answer": """<p>The token that job is using was deliberately narrowed when it was minted. The endpoint that mints an installation access token accepts a repository list and a permission map in its body, and either of them cuts the token below what the installation actually holds. A token minted for repository A cannot see repository B, and one minted with only <code>contents: read</code> cannot touch issues, however wide the installation is.</p>
<p>Because the narrowing produces a <code>404</code> rather than a <code>403</code> for repositories, it reads as <em>this does not exist</em> rather than as <em>you were not given this</em>, which is why the search goes to the App and the installation and stays there. The fix is to widen the mint request, not the App.</p>
<p>Check it by asking the token what it can reach. <code>GET /installation/repositories</code> with that specific token returns exactly the repositories that token covers, and comparing that against what the job needs is the finding. There is a blind spot to state plainly: a token cannot report its own permission map. The mint response echoed it back to your code and there is no read that recovers it, so the permission half of this check is only possible if you kept that response.</p>""",
"problem": """<p>Everything you would naturally check comes back clean, and each clean answer sends you further from the cause. The App is installed. The repository is in the installation. The permissions on the App are broad. The other jobs work. Every one of those facts is true and none of them is about the credential the failing job is holding, because the narrowing happened in four lines of minting code that nobody thinks of as configuration.</p>
<p>The 404 makes it worse, and it is doing the right thing. GitHub answers <code>404</code> rather than <code>403</code> when a credential is not entitled to know whether a private resource exists, which is correct and which means the response is deliberately indistinguishable from a typo in the repository name. So the first hour goes on spelling, then on whether the repository was renamed, then on whether it was archived, and all three investigations conclude that the repository is fine.</p>
<p>Then somebody widens the App. It does not help, because the App was never the constraint, and now the App holds permissions it does not need in order to fix a problem it did not have. Two rounds of that and the installation is carrying organization administration for a job that reads issue titles, which is a real security regression produced entirely by debugging in the wrong object.</p>""",
"why": """<p><strong>The mint request can narrow, never widen.</strong> The body of the token request accepts a repository list, a repository id list, and a permission map, and each is intersected with the installation's grant. You cannot mint a token more powerful than the installation; you can very easily mint one much less powerful, and there is no warning when you do, because narrowing is the feature.</p>
<p><strong>Narrowing is good practice, which is why it is everywhere.</strong> A job that touches one repository should hold a token for one repository. The advice is right and the failure mode is its shadow: the narrowest sensible token for last quarter's job is too narrow for this quarter's, and the mint request is the last place anybody looks because it was written once and never revisited.</p>
<p><strong>Repositories fail as 404 and permissions fail as 403.</strong> Two different symptoms from one cause, which is why they get filed as two different bugs. A repository outside the token's set does not exist as far as that token is concerned; a permission below what the endpoint needs produces the familiar refusal instead. The script checks both because the reader usually only has one of them.</p>
<p><strong>A token cannot introspect its own permissions.</strong> This is the honest limit of the check. <code>GET /installation/repositories</code> tells you the repository half exactly, and nothing returns the permission map a token was minted with. The mint response contained it and only your own code ever saw it. So the script takes that saved response when you have it and, when you do not, says the permission half is unknown rather than implying the token is fine.</p>
<p><strong>This is the opposite failure to a token that holds too much.</strong> <a href="/github/over-scoped-token/">Over-scoping</a> is a security finding about a credential that can do more than its job; this is an availability finding about one that can do less. It is also not <a href="/github/installation-repository-selection-partial/">an installation that covers only some repositories</a>: there the installation itself is narrow and every token from it is, here the installation is wide and one token is not.</p>""",
"steps": [
 {"h": "Write down what this specific job needs",
  "body": """<p>The repositories it touches, in <code>owner/name</code> form, and the permissions it uses with the level it uses them at. This is the comparison's right-hand side and it has to be the real list rather than the aspirational one; a job that reads one repository and writes a comment on another needs both named.</p>"""},
 {"h": "Ask the token what it can reach",
  "body": """<p><code>GET /installation/repositories</code> with the failing job's own token returns exactly the repositories that token covers, plus a <code>repository_selection</code> of <code>all</code> or <code>selected</code>. A <code>selected</code> here on an installation you know is org-wide is the narrowing, visible in one field.</p>"""},
 {"h": "Confirm per repository rather than trusting the list",
  "body": """<p>For each repository the job needs, <code>GET /repos/{owner}/{repo}</code> with the same token. A 200 is reach, a 404 is not-in-this-token, and doing it directly catches the case where the list was truncated by pagination and you drew the wrong conclusion from a partial page.</p>"""},
 {"h": "Recover the permission map from the mint response, or admit you cannot",
  "body": """<p>The response your minting code received echoes back <code>permissions</code> and <code>repository_selection</code> for the token it issued. If you log or keep that, feed it in and the permission half becomes exact. If you do not, no read recovers it, and the script reports the permission half as unknown rather than passing it.</p>"""},
 {"h": "Widen the mint, not the App",
  "body": """<p>Add the missing repositories and permissions to the token request that the job makes, keeping it as narrow as the job genuinely is. Nothing about the App changes, no installer has to accept anything, and the security posture stays where it was. If the mint asks for something the installation does not hold, <em>then</em> the App is the constraint and it is a different note.</p>"""},
],
"verify": """<p>After the mint request is widened, the same reads show the repository in reach and the permission at the level the job needs, with no change to the App at all.</p>
<pre><code class="language-bash">python3 github_token_reach.py --repo acme/api --repo acme/docs \\
  --needs contents:read,issues:write --grant mint-response.json
# token reaches 1 repository, repository_selection=selected
# repos-out-of-reach: acme/docs is not in this token's repository set
# repair: add acme/docs to the repository list in the token request this job
# makes. The installation already covers it, so the App does not change.

# after widening the mint request
# reach-covers-the-job: this token reaches every repository the job needs
# and holds every permission at the level it asked for</code></pre>""",
"code_intro": "One paginated GET for reach, one cheap GET per repository the job names, and no mint anywhere &mdash; minting is a write and this section does not write, so the script reads the token you already hold. The comparisons are pure and slightly fussy: repository names are matched case-insensitively because GitHub treats them that way and configuration files do not, permission levels are ranked so that <code>read</code>-where-<code>write</code>-is-needed counts as a shortfall, and the verdict has a state whose entire job is to say that the permission half could not be seen.",
"py_file": "github_token_reach.py",
"py": '''"""Say whether an installation access token was narrowed below what a job needs.

Read only. One paginated GET for what the token reaches, one GET per
repository the job names. The token endpoint that would mint a wider token is
a write and is not called here: the script reads the token you already hold
and prints the mint request you should be making instead.

An installation access token can be minted for fewer repositories and fewer
permissions than the installation holds, by naming them in the mint request
body. The result is a 404 on a repository the App is plainly installed on,
from one code path, while every other path using the same App works.

There is a blind spot and the report states it. A token cannot report its own
permission map; the mint response echoed it back to your own code and no read
recovers it afterwards. Pass that saved response with --grant to make the
permission half exact, or the script reports it as unseen rather than passing.

Environment:

    GITHUB_INSTALLATION_TOKEN   the token the failing job holds
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_token_reach")

API = "https://api.github.com"
UA = "github-token-reach/1.0"

RANK = {"none": 0, "read": 1, "write": 2, "admin": 3}


def rank(level):
    """A permission level as a comparable integer. Pure."""
    return RANK.get(str(level or "none").strip().lower(), 0)


def parse_needs(spec):
    """Turn contents:read,issues:write into a map. Pure.

    A bare name with no colon is taken as read, which is the level somebody
    means when they write down a permission without thinking about it.
    """
    out = {}
    for chunk in str(spec or "").split(","):
        item = chunk.strip()
        if not item:
            continue
        name, _, level = item.partition(":")
        name = name.strip().lower()
        if name:
            out[name] = (level.strip().lower() or "read")
    return out


def parse_grant(body):
    """Read a saved mint response into the facts it carries. Pure.

    Only three fields matter and any of them can be absent. permissions is
    None rather than an empty map when it is missing, because "this token was
    granted nothing" and "we did not see the grant" are opposite findings.
    """
    body = body if isinstance(body, dict) else {}
    permissions = body.get("permissions")
    repos = body.get("repositories")
    names = []
    if isinstance(repos, list):
        for repo in repos:
            if isinstance(repo, dict) and repo.get("full_name"):
                names.append(str(repo["full_name"]))
            elif isinstance(repo, str):
                names.append(repo)
    return {"permissions": permissions if isinstance(permissions, dict) else None,
            "repository_selection": body.get("repository_selection"),
            "repositories": names}


def repo_gap(reachable, needed):
    """Needed repositories the token cannot reach. Pure.

    Case-insensitive, because GitHub treats owner/name that way and the
    configuration file that lists them does not.
    """
    have = {str(r).strip().lower() for r in (reachable or [])}
    return [r for r in (needed or []) if str(r).strip().lower() not in have]


def permission_shortfall(granted, needed):
    """Needed permissions the token holds at a lower level. Pure.

    Returns None when the grant was never seen, which the caller reports as a
    blind spot rather than as a pass.
    """
    if granted is None:
        return None
    out = []
    for name, wanted in sorted((needed or {}).items()):
        have = (granted or {}).get(name)
        if rank(have) < rank(wanted):
            out.append((name, str(wanted), str(have) if have else "absent"))
    return out


def verdict(alive, missing_repos, shortfall, selection):
    """Turn reach, grant and need into a finding. Pure.

    Order matters: an unreachable repository is reported before a permission
    shortfall, because a 404 is the symptom people arrive with and fixing the
    permission first would leave them with the same 404.
    """
    if not alive:
        return ("token-not-alive",
                "GET /installation/repositories did not return 200, so this "
                "is not a working installation access token and the "
                "narrowing question does not arise yet.")
    if missing_repos:
        return ("repos-out-of-reach",
                "%s not in this token's repository set, so every call about "
                "them answers 404 whatever the App holds. Widen the "
                "repository list in the mint request."
                % ", ".join(missing_repos))
    if shortfall is None:
        return ("narrowing-not-visible",
                "every repository the job needs is reachable. The permission "
                "half cannot be checked: a token does not report its own "
                "permission map, and no saved mint response was supplied.")
    if shortfall:
        return ("permissions-below-need",
                "%s. The mint request asked for less than the job uses, which "
                "fails as 403 rather than as 404."
                % "; ".join("%s is %s, the job needs %s" % (n, h, w)
                            for n, w, h in shortfall))
    if str(selection or "").strip().lower() == "selected":
        return ("narrowed-but-sufficient",
                "this token is narrowed to a repository subset and the subset "
                "still covers the job. Nothing to change.")
    return ("reach-covers-the-job",
            "this token reaches every repository the job needs and holds "
            "every permission at the level it asked for.")


def repair(state, missing_repos, shortfall):
    """The change to make, in the mint request rather than in the App. Pure."""
    if state == "repos-out-of-reach":
        return ("add %s to the repository list in the token request this job "
                "makes. If the installation already covers them, the App does "
                "not change at all." % ", ".join(missing_repos))
    if state == "permissions-below-need":
        return ("raise %s in the permission map of the token request. If the "
                "installation does not hold it either, that is an App "
                "permission problem instead."
                % ", ".join("%s to %s" % (n, w) for n, w, _ in shortfall))
    if state == "narrowing-not-visible":
        return ("keep the mint response your code already receives, with the "
                "token value stripped, and pass it back in. It is the only "
                "place the granted permission map is ever visible.")
    return "nothing. This token is not the constraint."


def get(session, path):
    """One GET. Returns (status, json-or-None)."""
    url = API + path if path.startswith("/") else path
    r = session.get(url, timeout=30)
    try:
        body = r.json()
    except ValueError:
        body = None
    return r.status_code, body


def reachable_repositories(session, pages=10):
    """Every repository this token reaches. Returns (alive, names, selection)."""
    names, selection, alive = [], None, False
    for page in range(1, pages + 1):
        status, body = get(session,
                           "/installation/repositories?per_page=100&page=%d" % page)
        if status != 200 or not isinstance(body, dict):
            if page == 1:
                log.error("GET /installation/repositories returned %d; only an "
                          "installation access token can answer it", status)
            break
        alive = True
        selection = body.get("repository_selection", selection)
        rows = body.get("repositories") or []
        names.extend(str(r.get("full_name")) for r in rows
                     if isinstance(r, dict) and r.get("full_name"))
        if len(rows) < 100:
            break
    return alive, names, selection


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", action="append", default=[],
                    help="a repository the job needs, as owner/name; repeatable")
    ap.add_argument("--needs", default="",
                    help="permissions the job uses, as contents:read,issues:write")
    ap.add_argument("--grant", default=None,
                    help="path to the saved mint response body, token stripped")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_INSTALLATION_TOKEN") or \\
        os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_INSTALLATION_TOKEN to the token the failing job "
                  "holds. The narrowing is a property of that token and of no "
                  "other credential")
        return 2

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": UA,
    })

    alive, reach, selection = reachable_repositories(session)
    if alive:
        log.info("token reaches %d repository(ies), repository_selection=%s",
                 len(reach), selection or "unreported")

    # Confirming per repository rather than trusting the list, which can be
    # truncated by a pagination cap the caller did not notice.
    confirmed = []
    for name in args.repo:
        if not alive:
            break
        status, _ = get(session, "/repos/%s" % name.strip())
        log.info("GET /repos/%s returned %d", name.strip(), status)
        if status == 200:
            confirmed.append(name.strip())
    reach_all = sorted({*reach, *confirmed})

    grant = {"permissions": None, "repository_selection": selection,
             "repositories": []}
    if args.grant:
        try:
            with open(args.grant, encoding="utf-8") as fh:
                grant = parse_grant(json.load(fh))
        except (OSError, ValueError) as exc:
            log.error("could not read the saved mint response: %s", exc)
        else:
            selection = grant.get("repository_selection") or selection

    missing = repo_gap(reach_all, args.repo)
    shortfall = permission_shortfall(grant["permissions"], parse_needs(args.needs))
    state, detail = verdict(alive, missing, shortfall, selection)
    log.info("%s: %s", state, detail)
    log.info("repair: %s", repair(state, missing, shortfall))

    print(json.dumps({"reachable": reach_all, "repository_selection": selection,
                      "needed_repositories": args.repo,
                      "missing_repositories": missing,
                      "permission_shortfall": shortfall,
                      "state": state}, indent=2, default=str))
    return 1 if state in ("repos-out-of-reach", "permissions-below-need") else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-token-reach.mjs",
"js": '''/**
 * Say whether an installation access token was narrowed below what a job needs.
 *
 * Read only. One paginated GET for what the token reaches, one GET per
 * repository the job names. The token endpoint that would mint a wider token
 * is a write and is not called here: the script reads the token you already
 * hold and prints the mint request you should be making instead.
 *
 * A token cannot report its own permission map. The mint response echoed it
 * back to your own code and no read recovers it afterwards, so pass that saved
 * response as the third argument to make the permission half exact.
 *
 * Environment:
 *   GITHUB_INSTALLATION_TOKEN   the token the failing job holds
 */
import { readFile } from 'node:fs/promises';

const API = 'https://api.github.com';
const UA = 'github-token-reach/1.0';

export const RANK = { none: 0, read: 1, write: 2, admin: 3 };

/** A permission level as a comparable integer. Pure. */
export function rank(level) {
  const key = String(level ?? 'none').trim().toLowerCase();
  return Object.prototype.hasOwnProperty.call(RANK, key) ? RANK[key] : 0;
}

/** Turn contents:read,issues:write into a map. Pure. Bare names mean read. */
export function parseNeeds(spec) {
  const out = {};
  for (const chunk of String(spec ?? '').split(',')) {
    const item = chunk.trim();
    if (!item) continue;
    const at = item.indexOf(':');
    const name = (at === -1 ? item : item.slice(0, at)).trim().toLowerCase();
    const level = (at === -1 ? '' : item.slice(at + 1)).trim().toLowerCase();
    if (name) out[name] = level || 'read';
  }
  return out;
}

/** Read a saved mint response into the facts it carries. Pure. */
export function parseGrant(body) {
  const row = body && typeof body === 'object' ? body : {};
  const permissions = row.permissions && typeof row.permissions === 'object'
    ? row.permissions : null;
  const names = [];
  if (Array.isArray(row.repositories)) {
    for (const repo of row.repositories) {
      if (repo && typeof repo === 'object' && repo.full_name) names.push(String(repo.full_name));
      else if (typeof repo === 'string') names.push(repo);
    }
  }
  return {
    permissions,
    repository_selection: row.repository_selection ?? null,
    repositories: names,
  };
}

/** Needed repositories the token cannot reach. Pure. Case-insensitive. */
export function repoGap(reachable, needed) {
  const have = new Set((reachable ?? []).map((r) => String(r).trim().toLowerCase()));
  return (needed ?? []).filter((r) => !have.has(String(r).trim().toLowerCase()));
}

/**
 * Needed permissions the token holds at a lower level. Pure.
 * null when the grant was never seen, which is a blind spot and not a pass.
 */
export function permissionShortfall(granted, needed) {
  if (granted === null || granted === undefined) return null;
  const out = [];
  for (const name of Object.keys(needed ?? {}).sort()) {
    const wanted = needed[name];
    const have = granted[name];
    if (rank(have) < rank(wanted)) {
      out.push([name, String(wanted), have ? String(have) : 'absent']);
    }
  }
  return out;
}

/** Turn reach, grant and need into a finding. Pure. */
export function verdict(alive, missingRepos, shortfall, selection) {
  if (!alive) {
    return ['token-not-alive',
      'GET /installation/repositories did not return 200, so this is not a ' +
      'working installation access token and the narrowing question does not ' +
      'arise yet.'];
  }
  if (missingRepos && missingRepos.length) {
    return ['repos-out-of-reach',
      `${missingRepos.join(', ')} not in this token's repository set, so ` +
      'every call about them answers 404 whatever the App holds. Widen the ' +
      'repository list in the mint request.'];
  }
  if (shortfall === null || shortfall === undefined) {
    return ['narrowing-not-visible',
      'every repository the job needs is reachable. The permission half ' +
      'cannot be checked: a token does not report its own permission map, ' +
      'and no saved mint response was supplied.'];
  }
  if (shortfall.length) {
    return ['permissions-below-need',
      `${shortfall.map(([n, w, h]) => `${n} is ${h}, the job needs ${w}`).join('; ')}. ` +
      'The mint request asked for less than the job uses, which fails as 403 ' +
      'rather than as 404.'];
  }
  if (String(selection ?? '').trim().toLowerCase() === 'selected') {
    return ['narrowed-but-sufficient',
      'this token is narrowed to a repository subset and the subset still ' +
      'covers the job. Nothing to change.'];
  }
  return ['reach-covers-the-job',
    'this token reaches every repository the job needs and holds every ' +
    'permission at the level it asked for.'];
}

/** The change to make, in the mint request rather than in the App. Pure. */
export function repair(state, missingRepos, shortfall) {
  if (state === 'repos-out-of-reach') {
    return `add ${(missingRepos ?? []).join(', ')} to the repository list in ` +
      'the token request this job makes. If the installation already covers ' +
      'them, the App does not change at all.';
  }
  if (state === 'permissions-below-need') {
    return `raise ${(shortfall ?? []).map(([n, w]) => `${n} to ${w}`).join(', ')} ` +
      'in the permission map of the token request. If the installation does ' +
      'not hold it either, that is an App permission problem instead.';
  }
  if (state === 'narrowing-not-visible') {
    return 'keep the mint response your code already receives, with the token ' +
      'value stripped, and pass it back in. It is the only place the granted ' +
      'permission map is ever visible.';
  }
  return 'nothing. This token is not the constraint.';
}

async function get(token, path) {
  const url = path.startsWith('/') ? API + path : path;
  const res = await fetch(url, {
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

async function reachableRepositories(token, pages = 10) {
  const names = [];
  let selection = null;
  let alive = false;
  for (let page = 1; page <= pages; page += 1) {
    const { status, body } = await get(token,
      `/installation/repositories?per_page=100&page=${page}`);
    if (status !== 200 || !body || typeof body !== 'object') {
      if (page === 1) {
        console.error(`GET /installation/repositories returned ${status}; ` +
          'only an installation access token can answer it');
      }
      break;
    }
    alive = true;
    selection = body.repository_selection ?? selection;
    const rows = body.repositories ?? [];
    for (const r of rows) if (r && r.full_name) names.push(String(r.full_name));
    if (rows.length < 100) break;
  }
  return { alive, names, selection };
}

async function main() {
  const token = process.env.GITHUB_INSTALLATION_TOKEN ?? process.env.GITHUB_TOKEN;
  if (!token) {
    console.error('set GITHUB_INSTALLATION_TOKEN to the token the failing job ' +
      'holds. The narrowing is a property of that token and of no other credential');
    process.exitCode = 2;
    return;
  }
  const needed = (process.argv[2] ?? '').split(',').map((s) => s.trim()).filter(Boolean);
  const needs = parseNeeds(process.argv[3] ?? '');
  const grantPath = process.argv[4] ?? null;

  const { alive, names, selection: seen } = await reachableRepositories(token);
  let selection = seen;
  if (alive) {
    console.log(`token reaches ${names.length} repository(ies), ` +
      `repository_selection=${selection ?? 'unreported'}`);
  }

  // Confirming per repository rather than trusting the list, which can be
  // truncated by a pagination cap the caller did not notice.
  const confirmed = [];
  for (const name of alive ? needed : []) {
    const { status } = await get(token, `/repos/${name}`);
    console.log(`GET /repos/${name} returned ${status}`);
    if (status === 200) confirmed.push(name);
  }
  const reachAll = [...new Set([...names, ...confirmed])].sort();

  let grant = { permissions: null, repository_selection: selection, repositories: [] };
  if (grantPath) {
    try {
      grant = parseGrant(JSON.parse(await readFile(grantPath, 'utf8')));
      selection = grant.repository_selection ?? selection;
    } catch (err) {
      console.error(`could not read the saved mint response: ${err.message}`);
    }
  }

  const missing = repoGap(reachAll, needed);
  const shortfall = permissionShortfall(grant.permissions, needs);
  const [state, detail] = verdict(alive, missing, shortfall, selection);
  console.log(`${state}: ${detail}`);
  console.log(`repair: ${repair(state, missing, shortfall)}`);

  console.log(JSON.stringify({
    reachable: reachAll,
    repository_selection: selection,
    needed_repositories: needed,
    missing_repositories: missing,
    permission_shortfall: shortfall,
    state,
  }, null, 2));
  process.exitCode = ['repos-out-of-reach', 'permissions-below-need'].includes(state) ? 1 : 0;
}

// Only run when invoked directly, so importing this module from the test file
// does not execute main(), fail on the missing token and set an exit code that
// fails the suite even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The test this script exists for is the one that distinguishes <em>no shortfall</em> from <em>no visibility</em>: an empty list of missing permissions and an unseen grant are the same shape in a careless implementation and opposite findings in a useful one. The rest pin the ordering, since a reader arriving with a 404 must be told about the unreachable repository before anything else, and the small cruelties of real input: repository names in the wrong case, a permission written with no level, a mint response with no permissions block.",
"test_py_file": "test_github_token_reach.py",
"test_py": '''from github_token_reach import (
    parse_grant, parse_needs, permission_shortfall, rank, repair, repo_gap,
    verdict,
)

MINT = {"expires_at": "2026-08-30T13:00:00Z",
        "permissions": {"contents": "read", "metadata": "read"},
        "repository_selection": "selected",
        "repositories": [{"full_name": "acme/api"}]}


def test_a_bare_permission_name_means_read():
    assert parse_needs("contents, issues:write") == {"contents": "read",
                                                     "issues": "write"}
    assert parse_needs("") == {}
    assert parse_needs("  ,  ") == {}


def test_levels_are_ranked_rather_than_compared_as_strings():
    assert rank("write") > rank("read") > rank(None)
    assert rank("nonsense") == 0


def test_a_mint_response_is_read_for_the_three_fields_that_matter():
    grant = parse_grant(MINT)
    assert grant["permissions"] == {"contents": "read", "metadata": "read"}
    assert grant["repository_selection"] == "selected"
    assert grant["repositories"] == ["acme/api"]


def test_a_mint_response_with_no_permissions_block_is_unseen_not_empty():
    assert parse_grant({"repository_selection": "all"})["permissions"] is None
    assert parse_grant(None)["permissions"] is None


def test_repository_names_match_regardless_of_case():
    assert repo_gap(["acme/API"], ["Acme/api"]) == []
    assert repo_gap(["acme/api"], ["acme/api", "acme/docs"]) == ["acme/docs"]


def test_an_unseen_grant_is_not_a_permission_pass():
    assert permission_shortfall(None, {"issues": "write"}) is None
    assert permission_shortfall({}, {"issues": "write"}) == [("issues", "write", "absent")]


def test_read_where_write_is_needed_is_a_shortfall():
    assert permission_shortfall({"issues": "read"}, {"issues": "write"}) == \\
        [("issues", "write", "read")]
    assert permission_shortfall({"issues": "write"}, {"issues": "read"}) == []


def test_an_unreachable_repository_is_reported_before_a_permission_shortfall():
    state, detail = verdict(True, ["acme/docs"], [("issues", "write", "read")],
                            "selected")
    assert state == "repos-out-of-reach"
    assert "acme/docs" in detail


def test_a_permission_shortfall_names_both_levels():
    state, detail = verdict(True, [], [("issues", "write", "read")], "all")
    assert state == "permissions-below-need"
    assert "issues is read, the job needs write" in detail


def test_an_unseen_grant_gets_its_own_state_rather_than_a_clean_bill():
    state, detail = verdict(True, [], None, "all")
    assert state == "narrowing-not-visible"
    assert "does not report its own permission map" in detail


def test_a_narrowed_token_that_still_covers_the_job_is_not_a_fault():
    assert verdict(True, [], [], "selected")[0] == "narrowed-but-sufficient"


def test_a_wide_token_that_covers_the_job_is_clean():
    assert verdict(True, [], [], "all")[0] == "reach-covers-the-job"


def test_a_dead_token_is_never_reported_as_a_narrowing():
    state, detail = verdict(False, ["acme/docs"], None, None)
    assert state == "token-not-alive"
    assert "does not arise yet" in detail


def test_the_repair_points_at_the_mint_request_and_not_at_the_app():
    text = repair("repos-out-of-reach", ["acme/docs"], None)
    assert "token request" in text
    assert "the App does not change" in text
    assert "mint response" in repair("narrowing-not-visible", [], None)
    assert repair("reach-covers-the-job", [], []) == "nothing. This token is not the constraint."
''',
"test_js_file": "github-token-reach.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  parseGrant, parseNeeds, permissionShortfall, rank, repair, repoGap, verdict,
} from './github-token-reach.mjs';

const MINT = {
  expires_at: '2026-08-30T13:00:00Z',
  permissions: { contents: 'read', metadata: 'read' },
  repository_selection: 'selected',
  repositories: [{ full_name: 'acme/api' }],
};

test('a bare permission name means read', () => {
  assert.deepEqual(parseNeeds('contents, issues:write'),
    { contents: 'read', issues: 'write' });
  assert.deepEqual(parseNeeds(''), {});
  assert.deepEqual(parseNeeds('  ,  '), {});
});

test('levels are ranked rather than compared as strings', () => {
  assert.ok(rank('write') > rank('read'));
  assert.ok(rank('read') > rank(null));
  assert.equal(rank('nonsense'), 0);
});

test('a mint response is read for the three fields that matter', () => {
  const grant = parseGrant(MINT);
  assert.deepEqual(grant.permissions, { contents: 'read', metadata: 'read' });
  assert.equal(grant.repository_selection, 'selected');
  assert.deepEqual(grant.repositories, ['acme/api']);
});

test('a mint response with no permissions block is unseen not empty', () => {
  assert.equal(parseGrant({ repository_selection: 'all' }).permissions, null);
  assert.equal(parseGrant(null).permissions, null);
});

test('repository names match regardless of case', () => {
  assert.deepEqual(repoGap(['acme/API'], ['Acme/api']), []);
  assert.deepEqual(repoGap(['acme/api'], ['acme/api', 'acme/docs']), ['acme/docs']);
});

test('an unseen grant is not a permission pass', () => {
  assert.equal(permissionShortfall(null, { issues: 'write' }), null);
  assert.deepEqual(permissionShortfall({}, { issues: 'write' }),
    [['issues', 'write', 'absent']]);
});

test('read where write is needed is a shortfall', () => {
  assert.deepEqual(permissionShortfall({ issues: 'read' }, { issues: 'write' }),
    [['issues', 'write', 'read']]);
  assert.deepEqual(permissionShortfall({ issues: 'write' }, { issues: 'read' }), []);
});

test('an unreachable repository is reported before a permission shortfall', () => {
  const [state, detail] = verdict(true, ['acme/docs'], [['issues', 'write', 'read']], 'selected');
  assert.equal(state, 'repos-out-of-reach');
  assert.match(detail, /acme\\/docs/);
});

test('a permission shortfall names both levels', () => {
  const [state, detail] = verdict(true, [], [['issues', 'write', 'read']], 'all');
  assert.equal(state, 'permissions-below-need');
  assert.match(detail, /issues is read, the job needs write/);
});

test('an unseen grant gets its own state rather than a clean bill', () => {
  const [state, detail] = verdict(true, [], null, 'all');
  assert.equal(state, 'narrowing-not-visible');
  assert.match(detail, /does not report its own permission map/);
});

test('a narrowed token that still covers the job is not a fault', () => {
  assert.equal(verdict(true, [], [], 'selected')[0], 'narrowed-but-sufficient');
});

test('a wide token that covers the job is clean', () => {
  assert.equal(verdict(true, [], [], 'all')[0], 'reach-covers-the-job');
});

test('a dead token is never reported as a narrowing', () => {
  const [state, detail] = verdict(false, ['acme/docs'], null, null);
  assert.equal(state, 'token-not-alive');
  assert.match(detail, /does not arise yet/);
});

test('the repair points at the mint request and not at the app', () => {
  const text = repair('repos-out-of-reach', ['acme/docs'], null);
  assert.match(text, /token request/);
  assert.match(text, /the App does not change/);
  assert.match(repair('narrowing-not-visible', [], null), /mint response/);
  assert.equal(repair('reach-covers-the-job', [], []),
    'nothing. This token is not the constraint.');
});
''',
"faq": [
 ("Why a 404 and not a 403 when the repository is out of reach?",
  "Because GitHub answers 404 rather than 403 whenever a credential is not entitled to know that a private resource exists. Returning 403 would confirm the repository is there, which leaks the thing the permission model is protecting. The consequence for debugging is that a narrowed token and a misspelled repository name produce exactly the same response, so the first hour usually goes on spelling, renames and archived repositories, all of which come back fine. Ask the token what it reaches and the ambiguity disappears."),
 ("Is this the same as an installation that only covers some repositories?",
  "No, and the two are easy to confuse because both end in a 404 on a repository you can see in the browser. There the installation itself is narrow, so every token minted from it is narrow in the same way and the fix is to add repositories to the installation. Here the installation is wide and one token was cut down when it was minted, so other jobs using the same App work perfectly and the fix is four lines of your own minting code. The discriminator is whether other code paths reach the repository."),
 ("Why can the script not just read the token's permissions?",
  "Because nothing returns them. GET /installation/repositories answers the repository half exactly, and there is no equivalent read for the permission map a token was minted with. It appears once, in the response your own minting code received, and after that it is gone. That is why the script has a state whose only job is to say the permission half was not visible, and why the practical advice is to keep that response, with the token value stripped out, wherever you keep your logs."),
 ("Should we stop narrowing tokens then?",
  "No. Narrowing is the right default and this note is not an argument against it; a job that touches one repository should hold a token that reaches one repository, so that a leak is bounded. The failure is drift, not the practice: the narrowest correct token for the job as it was written is too narrow for the job as it is now, and nothing tells you when that line is crossed. Run this check in the job's own test suite, with the repositories and permissions it declares, and the drift becomes a failing test rather than a 404 in production."),
 ("Widening the mint request did not help. What now?",
  "Then the installation really is the constraint, because the mint request can only intersect with what the installation holds and can never exceed it. Check whether the installation covers the repository at all, and whether the App holds the permission you asked the token to carry. Those are two different published notes, and the useful thing about having run this check first is that you now know the narrowing was not in your own minting code, which is the cheapest of the three things to rule out."),
],
"related": [
 ("/github/installation-repository-selection-partial/", "An installation that covers only some repositories"),
 ("/github/over-scoped-token/", "A read-only job holding a token that can do anything"),
 ("/github/app-permission-missing/", "Resource not accessible by integration"),
],
"citations": [CITE_INSTALL_TOKEN, CITE_APP_INSTALL_AUTH, CITE_APPS_REST, CITE_APP_PERMS],
},

]
