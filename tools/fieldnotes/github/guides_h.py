#!/usr/bin/env python3
"""/github/ field notes, batch H — the writing.

Four notes about the credential itself: how much it is allowed to do, what
mechanism carries it, and where it ends up. They sit next to each other in the
index and they are deliberately not four ways of saying "fix your token".

The first is about *not enough*. A call is refused, and the response that
refused it carries both halves of the answer: what the token has and what the
endpoint accepts. The work is that scope satisfaction is not set membership —
the accepted list is alternatives, and scopes imply other scopes — so the
useful output is the single narrowest scope that would have worked.

The second is about *too much*, and it has to prove a negative. Nothing is
failing. The script therefore reports a capability inventory rather than an
error: the verbs a working token authorizes that the job it runs has never
used, counted against the repositories they reach.

The third is about a mechanism that was retired rather than a credential that
is wrong. A username and password is not a weak credential here, it is a
credential shape GitHub stopped accepting, and the script's most useful
behaviour is refusing to put one on the wire in order to prove it.

The fourth is a disclosure. Nothing fails, nothing is refused, and the finding
is arithmetic about copies: a credential in a URL is in the proxy log, the CI
transcript and the browser history. The script reports shape and location, and
never the value.

Read only throughout. Where the repair is a token to mint or a log to scrub,
the script prints it and stops.
"""

CITE_TROUBLESHOOT = ("Troubleshooting the REST API — GitHub Docs",
                     "https://docs.github.com/en/rest/using-the-rest-api/troubleshooting-the-rest-api")
CITE_AUTHENTICATING = ("Authenticating to the REST API — GitHub Docs",
                       "https://docs.github.com/en/rest/authentication/authenticating-to-the-rest-api")
CITE_OAUTH_SCOPES = ("Scopes for OAuth apps — GitHub Docs",
                     "https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/scopes-for-oauth-apps")
CITE_PATS = ("Managing your personal access tokens — GitHub Docs",
             "https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens")
CITE_APP_PERMS = ("Permissions required for GitHub Apps — GitHub Docs",
                  "https://docs.github.com/en/rest/authentication/permissions-required-for-github-apps")
CITE_CREDS_SECURE = ("Keeping your API credentials secure — GitHub Docs",
                     "https://docs.github.com/en/rest/authentication/keeping-your-api-credentials-secure")
CITE_GETTING_STARTED = ("Getting started with the REST API — GitHub Docs",
                        "https://docs.github.com/en/rest/using-the-rest-api/getting-started-with-the-rest-api")
CITE_REST_LIMITS = ("Rate limits for the REST API — GitHub Docs",
                    "https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api")
CITE_USERS = ("Users — GitHub REST API",
              "https://docs.github.com/en/rest/users/users")
CITE_ENDPOINTS = ("Endpoints available for fine-grained personal access tokens — GitHub Docs",
                  "https://docs.github.com/en/rest/overview/endpoints-available-for-fine-grained-personal-access-tokens")

GUIDES = [

{
"slug": "missing-oauth-scope",
"title": "The endpoint accepts a scope your token was never given",
"description": "x-oauth-scopes and x-accepted-oauth-scopes arrive on the same refused response. One says what the token holds, the other what would have worked.",
"h1": "the endpoint accepts a scope your token was never given",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github x-accepted-oauth-scopes", "github token missing scope 403",
             "github api must have admin rights to repository",
             "github personal access token scopes", "github oauth scope 404"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Nineteen calls work. The twentieth returns <code>403 {\"message\": \"Must have admin rights to Repository.\"}</code>, or worse, a bare <code>404</code> on a repository that is open in a browser tab beside you. The token is valid, it is not expired, it has not been revoked, and it is missing exactly one word from the list it was created with.",
"short_answer": """<p>Read two headers off the response that refused you. <code>x-oauth-scopes</code> is what the token holds. <code>x-accepted-oauth-scopes</code> is what that endpoint accepts. The difference is the repair, and GitHub puts both of them on the same response, including the 404 ones.</p>
<p>The subtlety is that the second header is a list of <em>alternatives</em>, not a list of requirements: <code>admin:repo_hook, write:repo_hook</code> means either will do. Scopes also imply other scopes, so a token holding <code>repo</code> already holds <code>public_repo</code> and does not need it added. The script below does that arithmetic and names the single narrowest scope that would have made the call succeed, rather than telling you to tick <code>repo</code> and move on.</p>""",
"problem": """<p>The refusal does not look like a permissions problem, which is most of why it takes an afternoon. On a public resource you get a 403 with prose about admin rights, which sends people to the repository settings page to check who is an admin. On a private one you get a 404, and everybody spends twenty minutes on spelling, owner names and letter case before anyone considers that the resource is being hidden rather than missing.</p>
<p>Then the fix overshoots. Someone re-mints the token with every box ticked, the call works, and the incident closes with a credential that can now delete repositories in order to list webhooks. That is <a href="/github/over-scoped-token/">a second problem</a>, created by the repair for the first one, and it is invisible because nothing about it fails.</p>
<p>And the header pair is genuinely easy to miss. Almost nobody logs response headers on a failure, so the one place GitHub names the answer is the one place the client throws away. The body carries a sentence of prose; the headers carry the scope.</p>""",
"why": """<p><strong>Scopes are fixed at creation.</strong> A classic personal access token or an OAuth token carries the scope set it was minted with, forever. There is no widening: adding a scope means a new token and a new deployment of it everywhere the old one lives. That is why the narrowest sufficient scope matters more here than it looks &mdash; you get one shot at choosing per rotation.</p>
<p><strong>The accepted list is a disjunction.</strong> <code>x-accepted-oauth-scopes: admin:repo_hook, write:repo_hook</code> is not two requirements, it is two ways to satisfy one. Reading it as a conjunction is how a token ends up with the administrative variant of a scope it only needed the write variant of.</p>
<p><strong>Scopes imply narrower scopes.</strong> <code>repo</code> covers <code>public_repo</code>, <code>repo:status</code>, <code>repo_deployment</code> and <code>security_events</code>. <code>admin:org</code> covers <code>write:org</code> which covers <code>read:org</code>. A naive set difference against <code>x-oauth-scopes</code> will therefore report scopes as missing that the token demonstrably already has, and the person reading the report stops trusting it.</p>
<p><strong>An empty accepted header is a different finding.</strong> <code>x-accepted-oauth-scopes:</code> with nothing after it means the endpoint accepts any authenticated token. If that call still failed, no scope will fix it and you are looking at the wrong cause &mdash; an SSO authorization, an installation that does not include the repository, or simply no access grant at all.</p>
<p><strong>Fine-grained tokens do not do scopes at all.</strong> They carry per-repository permissions instead, and <code>x-oauth-scopes</code> is absent rather than empty on their responses. If the header is not there, this note does not apply to your credential and <a href="/github/app-permission-missing/">the permissions model</a> is the one to read.</p>""",
"steps": [
 {"h": "Make the failing call again and keep the response headers",
  "body": """<p>Not <code>GET /user</code>, and not a call you expect to work: the exact path that was refused. Both headers ride on the failure, including on a 404, and the accepted list is per-endpoint, so a header pair collected somewhere else answers a different question than the one you asked.</p>"""},
 {"h": "Read x-oauth-scopes, and tell absent apart from empty",
  "body": """<p>Absent means the credential is not scope-based at all: a fine-grained token, an App installation token, or no credential. Present but empty means a scope-based token that was minted with none. Those are three different repairs and one of them is not on this page.</p>"""},
 {"h": "Expand what the token holds before you diff",
  "body": """<p><code>repo</code> implies half a dozen narrower scopes and <code>admin:org</code> implies two. Expand the held set through the implication table first, or the report will name scopes as missing that the call would already have accepted.</p>"""},
 {"h": "Treat the accepted list as alternatives and pick the narrowest",
  "body": """<p>Split <code>x-accepted-oauth-scopes</code> on commas, work out what each alternative is missing, and choose the one that adds the least. When both <code>repo</code> and <code>public_repo</code> would satisfy an endpoint, the answer is <code>public_repo</code> unless the resource is private.</p>"""},
 {"h": "Mint a new token with exactly that scope added",
  "body": """<p>Then deploy it everywhere the old one is and revoke the old one. If you use the GitHub CLI for a user-level credential, <code>gh auth refresh -h github.com -s SCOPE</code> adds one scope to the existing authorization; for a token in a secret store there is no shortcut, it is a new token.</p>"""},
],
"verify": """<p>Re-run against the same path with the new credential. The state should move from <code>missing-scope</code> to <code>scope-satisfied</code>, and the call itself should stop being refused.</p>
<pre><code class="language-bash">python3 github_scope_diff.py --path /repos/acme/api/hooks
# held: public_repo, read:org
# accepted: admin:repo_hook, write:repo_hook
# missing-scope: add write:repo_hook (narrowest of 2 alternatives) and the
# call succeeds; admin:repo_hook would also work and grants more</code></pre>""",
"code_intro": "Two GETs, one of them the call that failed. Everything that produces a finding is text: a parser that tells an absent header apart from an empty one, an implication closure so a held <code>repo</code> is not reported as missing <code>public_repo</code>, an alternatives solver over the accepted list, and a ranking that prefers the narrowest scope that works. All four are pure, so the tests can pose header pairs that would take a dozen tokens to reproduce for real.",
"py_file": "github_scope_diff.py",
"py": '''"""Name the narrowest scope that would have made a refused GitHub call succeed.

Read only. Both requests are GETs, and one of them is the call you are already
making. Nothing here mints, rotates or revokes anything: the repair is printed
for you to run.

The two headers that matter ride on the same response:

    x-oauth-scopes:          what this token holds
    x-accepted-oauth-scopes: what this endpoint accepts, as alternatives

Scope satisfaction is not set membership. The accepted list is a disjunction,
and held scopes imply narrower ones, so the diff has to be computed rather than
eyeballed.
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_scope_diff")

API = "https://api.github.com"
UA = "github-scope-diff/1.0"

# Holding the key already grants everything in the value, transitively. Only the
# implications that change a diff are listed; a scope absent from this table
# implies nothing, which is the common case.
IMPLIES = {
    "repo": ["public_repo", "repo:status", "repo_deployment", "repo:invite",
             "security_events"],
    "admin:org": ["write:org"],
    "write:org": ["read:org"],
    "admin:repo_hook": ["write:repo_hook"],
    "write:repo_hook": ["read:repo_hook"],
    "admin:org_hook": [],
    "admin:public_key": ["write:public_key"],
    "write:public_key": ["read:public_key"],
    "admin:gpg_key": ["write:gpg_key"],
    "write:gpg_key": ["read:gpg_key"],
    "user": ["read:user", "user:email", "user:follow"],
    "write:packages": ["read:packages"],
    "write:discussion": ["read:discussion"],
    "project": ["read:project"],
}

# Lower is narrower. Used only to break ties between alternatives that would
# both work, so the report recommends public_repo over repo rather than the one
# that happened to be listed first.
RANK = {
    "read:org": 10, "read:user": 10, "read:packages": 10, "read:project": 10,
    "read:discussion": 10, "read:repo_hook": 10, "repo:status": 12,
    "user:email": 12, "repo_deployment": 15, "security_events": 18,
    "public_repo": 20, "write:org": 30, "write:repo_hook": 30,
    "write:packages": 30, "write:discussion": 30, "gist": 25, "notifications": 25,
    "admin:repo_hook": 40, "admin:org_hook": 45, "workflow": 55, "repo": 60,
    "user": 60, "admin:org": 70, "delete_repo": 80, "delete:packages": 80,
    "site_admin": 95,
}
DEFAULT_RANK = 50


def parse_scopes(value):
    """Parse an x-oauth-scopes header value. Pure.

    Returns None when the header was absent and a list when it was present, so
    "this credential does not use scopes" stays distinguishable from "this
    credential was minted with none". They have different repairs and only one
    of them is on this page.
    """
    if value is None:
        return None
    return [s.strip() for s in str(value).split(",") if s.strip()]


def expand(scopes):
    """Close a held scope set over the implication table. Pure.

    Without this, a token holding repo is reported as missing public_repo, the
    reader tries it, nothing changes, and the report stops being believed.
    """
    seen, queue = set(), list(scopes or [])
    while queue:
        scope = queue.pop()
        if scope in seen:
            continue
        seen.add(scope)
        queue.extend(IMPLIES.get(scope, ()))
    return seen


def alternatives(value):
    """Parse x-accepted-oauth-scopes into alternative requirement sets. Pure.

    Commas separate alternatives, any one of which satisfies the endpoint.
    Whitespace inside one alternative is treated as a conjunction, which is
    defensive rather than common. None means the header was absent; an empty
    list means it was present and empty, which is the endpoint saying it accepts
    any authenticated caller.
    """
    if value is None:
        return None
    out = []
    for item in str(value).split(","):
        parts = sorted({p for p in item.replace(" and ", " ").split() if p})
        if parts:
            out.append(tuple(parts))
    return out


def satisfies(held, accepted):
    """Decide whether held scopes satisfy an accepted list. Pure.

    Returns (ok, options). ok is None when the endpoint named no scopes at all.
    options lists what each unmet alternative is missing, narrowest first, so
    the caller can recommend the cheapest one rather than the first one.
    """
    if accepted is None:
        return None, []
    if not accepted:
        return True, []
    have = expand(held or [])
    options = []
    for alt in accepted:
        missing = tuple(s for s in alt if s not in have)
        if not missing:
            return True, []
        options.append(missing)
    options.sort(key=lambda m: (len(m),
                                sum(RANK.get(s, DEFAULT_RANK) for s in m), m))
    return False, options


def verdict(status, held, accepted):
    """Turn a status code and a header pair into a finding. Pure."""
    if held is None:
        return ("not-a-scoped-credential",
                "the response carried no x-oauth-scopes header, so this is a "
                "fine-grained token, an App installation token or no credential "
                "at all. None of those use scopes; they use per-resource "
                "permissions, and the missing one is named by "
                "x-accepted-github-permissions instead.")
    if status < 400:
        return ("call-succeeded",
                "the call returned %d, so there is nothing to diff. Held: %s"
                % (status, ", ".join(held) or "none"))

    ok, options = satisfies(held, accepted)
    if ok is None:
        return ("endpoint-named-no-scopes",
                "the %d response carried no x-accepted-oauth-scopes header, so "
                "the endpoint did not name a scope. Scope is not the cause "
                "here; look at SSO authorization, App installation coverage or "
                "plain lack of access." % status)
    if ok and not accepted:
        return ("any-token-accepted",
                "x-accepted-oauth-scopes was present and empty, which means the "
                "endpoint accepts any authenticated token. The %d is therefore "
                "not about scopes and no scope will fix it." % status)
    if ok:
        return ("scope-satisfied",
                "the token already satisfies %s, so the %d has another cause. "
                "Held: %s" % (" or ".join("+".join(a) for a in accepted),
                              status, ", ".join(held) or "none"))

    cheapest = options[0]
    return ("missing-scope",
            "add %s (narrowest of %d alternative(s)) and the call succeeds. "
            "Held: %s. Accepted: %s"
            % ("+".join(cheapest), len(options), ", ".join(held) or "none",
               " or ".join("+".join(a) for a in accepted)))


def get(session, path):
    """One GET. Returns (status, json-or-None, lowercased headers)."""
    url = API + path if path.startswith("/") else path
    r = session.get(url, timeout=30)
    try:
        body = r.json()
    except ValueError:
        body = None
    return r.status_code, body, {k.lower(): v for k, v in r.headers.items()}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--path", default="/user",
                    help="the API path that was refused, for example "
                         "/repos/OWNER/REPO/hooks")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_TOKEN. An anonymous request carries no "
                  "x-oauth-scopes header at all, so there is nothing to diff")
        return 2

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": UA,
    })

    # GET /user is the cheapest place to read what the token holds, and it
    # answers even when the failing path 404s without headers.
    base_status, base_body, base_headers = get(session, "/user")
    held = parse_scopes(base_headers.get("x-oauth-scopes"))
    if base_status == 200 and isinstance(base_body, dict):
        log.info("authenticated as %s", base_body.get("login", "an unnamed user"))
    elif base_status == 401:
        log.error("GET /user returned 401, so the credential is rejected "
                  "outright. That is a different problem from a narrow one")
        return 2

    status, _, headers = get(session, args.path)
    # The failing response is the authoritative one for both headers; fall back
    # to the /user reading only where the failure omitted them.
    held = parse_scopes(headers.get("x-oauth-scopes")) or held
    accepted = alternatives(headers.get("x-accepted-oauth-scopes"))
    log.info("%s returned %d", args.path, status)
    log.info("held:     %s", ", ".join(held or []) if held is not None
             else "header absent, not a scoped credential")
    log.info("accepted: %s", headers.get("x-accepted-oauth-scopes",
                                         "header absent"))

    state, detail = verdict(status, held, accepted)
    log.info("%s: %s", state, detail)

    if state == "missing-scope":
        _, options = satisfies(held, accepted)
        want = "+".join(options[0])
        log.info("repair: mint a replacement token that adds %s, deploy it, "
                 "then revoke the old one. Scopes cannot be widened in place.",
                 want)
        log.info("repair: for a gh CLI credential, gh auth refresh -h "
                 "github.com -s %s", options[0][0])
    if state == "not-a-scoped-credential":
        log.info("repair: read x-accepted-github-permissions on the same "
                 "response and add that permission to the App or the "
                 "fine-grained token instead.")

    print(json.dumps({"path": args.path, "status": status, "held": held,
                      "accepted": accepted, "state": state}, indent=2))
    return 1 if state in ("missing-scope", "not-a-scoped-credential") else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-scope-diff.mjs",
"js": '''/**
 * Name the narrowest scope that would have made a refused GitHub call succeed.
 *
 * Read only. Both requests are GETs, and one of them is the call you are
 * already making. The repair is printed, never applied.
 *
 * x-oauth-scopes is what the token holds; x-accepted-oauth-scopes is what the
 * endpoint accepts, as alternatives. Held scopes imply narrower ones, so the
 * diff is computed rather than eyeballed.
 */
const API = 'https://api.github.com';
const UA = 'github-scope-diff/1.0';

/** Holding the key already grants everything in the value, transitively. */
export const IMPLIES = {
  repo: ['public_repo', 'repo:status', 'repo_deployment', 'repo:invite',
    'security_events'],
  'admin:org': ['write:org'],
  'write:org': ['read:org'],
  'admin:repo_hook': ['write:repo_hook'],
  'write:repo_hook': ['read:repo_hook'],
  'admin:org_hook': [],
  'admin:public_key': ['write:public_key'],
  'write:public_key': ['read:public_key'],
  'admin:gpg_key': ['write:gpg_key'],
  'write:gpg_key': ['read:gpg_key'],
  user: ['read:user', 'user:email', 'user:follow'],
  'write:packages': ['read:packages'],
  'write:discussion': ['read:discussion'],
  project: ['read:project'],
};

/** Lower is narrower. Only used to break ties between workable alternatives. */
export const RANK = {
  'read:org': 10, 'read:user': 10, 'read:packages': 10, 'read:project': 10,
  'read:discussion': 10, 'read:repo_hook': 10, 'repo:status': 12,
  'user:email': 12, repo_deployment: 15, security_events: 18,
  public_repo: 20, 'write:org': 30, 'write:repo_hook': 30,
  'write:packages': 30, 'write:discussion': 30, gist: 25, notifications: 25,
  'admin:repo_hook': 40, 'admin:org_hook': 45, workflow: 55, repo: 60,
  user: 60, 'admin:org': 70, delete_repo: 80, 'delete:packages': 80,
  site_admin: 95,
};
export const DEFAULT_RANK = 50;

/**
 * Parse an x-oauth-scopes header value. Pure.
 * null for an absent header, [] for a present but empty one: "does not use
 * scopes" and "was minted with none" are different findings.
 */
export function parseScopes(value) {
  if (value === null || value === undefined) return null;
  return String(value).split(',').map((s) => s.trim()).filter(Boolean);
}

/** Close a held scope set over the implication table. Pure. */
export function expand(scopes) {
  const seen = new Set();
  const queue = [...(scopes ?? [])];
  while (queue.length) {
    const scope = queue.pop();
    if (seen.has(scope)) continue;
    seen.add(scope);
    queue.push(...(IMPLIES[scope] ?? []));
  }
  return seen;
}

/**
 * Parse x-accepted-oauth-scopes into alternative requirement sets. Pure.
 * null for an absent header, [] for a present but empty one, which is the
 * endpoint saying it accepts any authenticated caller.
 */
export function alternatives(value) {
  if (value === null || value === undefined) return null;
  const out = [];
  for (const item of String(value).split(',')) {
    const parts = [...new Set(item.replace(/ and /g, ' ').split(/\\s+/)
      .filter(Boolean))].sort();
    if (parts.length) out.push(parts);
  }
  return out;
}

/**
 * Decide whether held scopes satisfy an accepted list. Pure.
 * Returns [ok, options]; ok is null when the endpoint named no scopes.
 */
export function satisfies(held, accepted) {
  if (accepted === null || accepted === undefined) return [null, []];
  if (!accepted.length) return [true, []];
  const have = expand(held ?? []);
  const options = [];
  for (const alt of accepted) {
    const missing = alt.filter((s) => !have.has(s));
    if (!missing.length) return [true, []];
    options.push(missing);
  }
  const cost = (m) => m.reduce((n, s) => n + (RANK[s] ?? DEFAULT_RANK), 0);
  options.sort((a, b) => (a.length - b.length) || (cost(a) - cost(b)) ||
    a.join().localeCompare(b.join()));
  return [false, options];
}

/** Turn a status code and a header pair into a finding. Pure. */
export function verdict(status, held, accepted) {
  if (held === null || held === undefined) {
    return ['not-a-scoped-credential',
      'the response carried no x-oauth-scopes header, so this is a ' +
      'fine-grained token, an App installation token or no credential at all. ' +
      'None of those use scopes; they use per-resource permissions, and the ' +
      'missing one is named by x-accepted-github-permissions instead.'];
  }
  if (status < 400) {
    return ['call-succeeded',
      `the call returned ${status}, so there is nothing to diff. Held: ` +
      `${held.join(', ') || 'none'}`];
  }

  const [ok, options] = satisfies(held, accepted);
  if (ok === null) {
    return ['endpoint-named-no-scopes',
      `the ${status} response carried no x-accepted-oauth-scopes header, so ` +
      'the endpoint did not name a scope. Scope is not the cause here; look ' +
      'at SSO authorization, App installation coverage or plain lack of access.'];
  }
  if (ok && !accepted.length) {
    return ['any-token-accepted',
      'x-accepted-oauth-scopes was present and empty, which means the ' +
      `endpoint accepts any authenticated token. The ${status} is therefore ` +
      'not about scopes and no scope will fix it.'];
  }
  if (ok) {
    return ['scope-satisfied',
      `the token already satisfies ${accepted.map((a) => a.join('+')).join(' or ')}, ` +
      `so the ${status} has another cause. Held: ${held.join(', ') || 'none'}`];
  }
  const cheapest = options[0];
  return ['missing-scope',
    `add ${cheapest.join('+')} (narrowest of ${options.length} alternative(s)) ` +
    `and the call succeeds. Held: ${held.join(', ') || 'none'}. ` +
    `Accepted: ${accepted.map((a) => a.join('+')).join(' or ')}`];
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
  const headers = {};
  for (const [k, v] of res.headers.entries()) headers[k.toLowerCase()] = v;
  return { status: res.status, body, headers };
}

async function main() {
  const token = process.env.GITHUB_TOKEN;
  if (!token) {
    console.error('set GITHUB_TOKEN. An anonymous request carries no ' +
      'x-oauth-scopes header at all, so there is nothing to diff');
    process.exitCode = 2;
    return;
  }
  const path = process.argv[2] ?? '/user';

  const base = await get(token, '/user');
  let held = parseScopes(base.headers['x-oauth-scopes'] ?? null);
  if (base.status === 200 && base.body) {
    console.log(`authenticated as ${base.body.login ?? 'an unnamed user'}`);
  } else if (base.status === 401) {
    console.error('GET /user returned 401, so the credential is rejected ' +
      'outright. That is a different problem from a narrow one');
    process.exitCode = 2;
    return;
  }

  const failing = await get(token, path);
  const onFailure = parseScopes(failing.headers['x-oauth-scopes'] ?? null);
  if (onFailure && onFailure.length) held = onFailure;
  const accepted = alternatives(failing.headers['x-accepted-oauth-scopes'] ?? null);

  console.log(`${path} returned ${failing.status}`);
  console.log(`held:     ${held === null ? 'header absent, not a scoped credential'
    : held.join(', ')}`);
  console.log(`accepted: ${failing.headers['x-accepted-oauth-scopes'] ?? 'header absent'}`);

  const [state, detail] = verdict(failing.status, held, accepted);
  console.log(`${state}: ${detail}`);

  if (state === 'missing-scope') {
    const [, options] = satisfies(held, accepted);
    console.log(`repair: mint a replacement token that adds ${options[0].join('+')}, ` +
      'deploy it, then revoke the old one. Scopes cannot be widened in place.');
    console.log('repair: for a gh CLI credential, gh auth refresh -h github.com ' +
      `-s ${options[0][0]}`);
  }
  if (state === 'not-a-scoped-credential') {
    console.log('repair: read x-accepted-github-permissions on the same ' +
      'response and add that permission to the App or the fine-grained token.');
  }

  console.log(JSON.stringify({ path, status: failing.status, held, accepted, state }, null, 2));
  process.exitCode = (state === 'missing-scope' ||
    state === 'not-a-scoped-credential') ? 1 : 0;
}

// Only run when invoked directly, so importing this module from the test file
// does not execute main(), fail on the missing token and set an exit code that
// fails the suite even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The cases worth pinning down are the ones a live token cannot easily produce: a header that is absent versus one that is present and empty, an accepted list where two alternatives both work and the narrower one has to win, and a token holding <code>repo</code> that must not be told to add <code>public_repo</code>. Every function takes strings and returns data, so each of those is three lines.",
"test_py_file": "test_github_scope_diff.py",
"test_py": '''from github_scope_diff import alternatives, expand, parse_scopes, satisfies, verdict


def test_an_absent_header_is_not_an_empty_scope_list():
    assert parse_scopes(None) is None
    assert parse_scopes("") == []
    assert parse_scopes("repo, read:org") == ["repo", "read:org"]


def test_holding_repo_already_holds_the_narrower_repo_scopes():
    have = expand(["repo"])
    assert "public_repo" in have
    assert "repo:status" in have
    assert "security_events" in have


def test_implication_is_transitive():
    have = expand(["admin:org"])
    assert "write:org" in have
    assert "read:org" in have


def test_expanding_nothing_is_empty_rather_than_an_error():
    assert expand(None) == set()
    assert expand([]) == set()


def test_the_accepted_header_is_parsed_as_alternatives():
    assert alternatives("admin:repo_hook, write:repo_hook") == [
        ("admin:repo_hook",), ("write:repo_hook",)]


def test_an_absent_accepted_header_is_not_an_empty_one():
    assert alternatives(None) is None
    assert alternatives("") == []


def test_a_token_holding_repo_does_not_need_public_repo_added():
    ok, options = satisfies(["repo"], alternatives("public_repo"))
    assert ok is True
    assert options == []


def test_the_narrowest_workable_alternative_wins():
    ok, options = satisfies([], alternatives("repo, public_repo"))
    assert ok is False
    assert options[0] == ("public_repo",)


def test_an_empty_accepted_list_is_satisfied_by_any_token():
    assert satisfies([], []) == (True, [])


def test_an_absent_accepted_list_cannot_be_judged():
    assert satisfies(["repo"], None) == (None, [])


def test_a_missing_scope_is_named_and_the_alternatives_counted():
    state, detail = verdict(403, ["public_repo", "read:org"],
                            alternatives("admin:repo_hook, write:repo_hook"))
    assert state == "missing-scope"
    assert "write:repo_hook" in detail
    assert "2 alternative(s)" in detail


def test_a_fine_grained_credential_is_sent_to_the_other_note():
    state, detail = verdict(403, None, alternatives("repo"))
    assert state == "not-a-scoped-credential"
    assert "x-accepted-github-permissions" in detail


def test_an_empty_accepted_header_rules_scope_out_entirely():
    state, detail = verdict(404, ["repo"], [])
    assert state == "any-token-accepted"
    assert "no scope will fix it" in detail


def test_an_absent_accepted_header_is_its_own_state():
    assert verdict(404, ["repo"], None)[0] == "endpoint-named-no-scopes"


def test_a_satisfied_token_that_still_failed_points_elsewhere():
    state, detail = verdict(404, ["repo"], alternatives("repo"))
    assert state == "scope-satisfied"
    assert "another cause" in detail


def test_a_successful_call_has_nothing_to_diff():
    assert verdict(200, ["repo"], alternatives("repo"))[0] == "call-succeeded"
''',
"test_js_file": "github-scope-diff.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  alternatives, expand, parseScopes, satisfies, verdict,
} from './github-scope-diff.mjs';

test('an absent header is not an empty scope list', () => {
  assert.equal(parseScopes(null), null);
  assert.deepEqual(parseScopes(''), []);
  assert.deepEqual(parseScopes('repo, read:org'), ['repo', 'read:org']);
});

test('holding repo already holds the narrower repo scopes', () => {
  const have = expand(['repo']);
  assert.ok(have.has('public_repo'));
  assert.ok(have.has('repo:status'));
  assert.ok(have.has('security_events'));
});

test('implication is transitive', () => {
  const have = expand(['admin:org']);
  assert.ok(have.has('write:org'));
  assert.ok(have.has('read:org'));
});

test('expanding nothing is empty rather than an error', () => {
  assert.equal(expand(null).size, 0);
  assert.equal(expand([]).size, 0);
});

test('the accepted header is parsed as alternatives', () => {
  assert.deepEqual(alternatives('admin:repo_hook, write:repo_hook'),
    [['admin:repo_hook'], ['write:repo_hook']]);
});

test('an absent accepted header is not an empty one', () => {
  assert.equal(alternatives(null), null);
  assert.deepEqual(alternatives(''), []);
});

test('a token holding repo does not need public_repo added', () => {
  const [ok, options] = satisfies(['repo'], alternatives('public_repo'));
  assert.equal(ok, true);
  assert.deepEqual(options, []);
});

test('the narrowest workable alternative wins', () => {
  const [ok, options] = satisfies([], alternatives('repo, public_repo'));
  assert.equal(ok, false);
  assert.deepEqual(options[0], ['public_repo']);
});

test('an empty accepted list is satisfied by any token', () => {
  assert.deepEqual(satisfies([], []), [true, []]);
});

test('an absent accepted list cannot be judged', () => {
  assert.deepEqual(satisfies(['repo'], null), [null, []]);
});

test('a missing scope is named and the alternatives counted', () => {
  const [state, detail] = verdict(403, ['public_repo', 'read:org'],
    alternatives('admin:repo_hook, write:repo_hook'));
  assert.equal(state, 'missing-scope');
  assert.match(detail, /write:repo_hook/);
  assert.match(detail, /2 alternative\\(s\\)/);
});

test('a fine-grained credential is sent to the other note', () => {
  const [state, detail] = verdict(403, null, alternatives('repo'));
  assert.equal(state, 'not-a-scoped-credential');
  assert.match(detail, /x-accepted-github-permissions/);
});

test('an empty accepted header rules scope out entirely', () => {
  const [state, detail] = verdict(404, ['repo'], []);
  assert.equal(state, 'any-token-accepted');
  assert.match(detail, /no scope will fix it/);
});

test('an absent accepted header is its own state', () => {
  assert.equal(verdict(404, ['repo'], null)[0], 'endpoint-named-no-scopes');
});

test('a satisfied token that still failed points elsewhere', () => {
  const [state, detail] = verdict(404, ['repo'], alternatives('repo'));
  assert.equal(state, 'scope-satisfied');
  assert.match(detail, /another cause/);
});

test('a successful call has nothing to diff', () => {
  assert.equal(verdict(200, ['repo'], alternatives('repo'))[0], 'call-succeeded');
});
''',
"faq": [
 ("Why do I get 404 instead of 403 when a scope is missing?",
  "Because a 403 on a private resource would confirm that the resource exists, and GitHub will not do that for a caller who is not allowed to know. So a token without repo asking about a private repository is told Not Found, exactly as it would be for a repository that was never created. The scope headers are still on that 404, which is what makes it diagnosable at all; the fuller triage of everything a 404 can be hiding is in the note on a permission error disguised as 404 Not Found."),
 ("Is x-accepted-oauth-scopes a list of scopes I need, or scopes that would work?",
  "Scopes that would work, any one of them. It is a disjunction. Reading admin:repo_hook, write:repo_hook as a requirement for both is how tokens end up with administrative rights they never needed: the write variant alone satisfies the endpoint. When more than one alternative is listed, take the narrowest, which for repository scopes usually means preferring public_repo to repo and the write: variant to the admin: one."),
 ("My token already has repo. Why does the report still say a scope is missing?",
  "Then the endpoint wants something outside the repo family. repo covers repository contents, statuses, deployments and invitations, but it does not cover organization administration, webhooks at the organization level, package publishing, or workflow files. Those are separate scopes: admin:org, admin:org_hook, write:packages, workflow. The accepted header names which one, and none of them are implied by repo however broad it feels."),
 ("Can I add a scope to a token that already exists?",
  "Not for a classic personal access token or an OAuth token: the scope set is fixed at creation, so a wider token is a new token, a new deployment and a revocation of the old one. The gh CLI is the one partial exception for a user-level credential, where gh auth refresh -s SCOPE re-runs the authorization with an extra scope. Fine-grained tokens and GitHub Apps are different again: their permissions can be edited in place, though an App's new permissions stay inert until each installation accepts them."),
 ("The response has no x-oauth-scopes header at all. What does that mean?",
  "That the credential is not scope-based. Fine-grained personal access tokens and GitHub App installation tokens carry per-repository, per-resource permissions instead, and they never emit that header, so an absent header is a statement about the credential type rather than about its breadth. For those, the header to read is x-accepted-github-permissions on the same response, and the repair is a permission rather than a scope."),
],
"related": [
 ("/github/404-masking-403/", "A permission error disguised as 404 Not Found"),
 ("/github/app-permission-missing/", "Resource not accessible by integration"),
 ("/github/over-scoped-token/", "A token that can delete repositories"),
],
"citations": [CITE_TROUBLESHOOT, CITE_OAUTH_SCOPES, CITE_PATS, CITE_APP_PERMS],
},

{
"slug": "over-scoped-token",
"title": "A read-only job holds a token that can delete repositories",
"description": "Nothing is failing, which is the finding. GET /user names the scopes the token holds, and a read-only job has never used most of the verbs they grant.",
"h1": "a read-only job holds a token that can delete repositories",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github token least privilege", "classic pat repo scope too broad",
             "fine-grained personal access token read only",
             "github x-oauth-scopes audit", "github token blast radius"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "There is no incident to attach this to. The job runs every ten minutes, lists open pull requests, posts a count to a dashboard and has not failed once this year. The token it uses was created in four seconds by ticking <code>repo</code>, and it can force-push to every private repository in the organization, rewrite webhooks and delete the lot.",
"short_answer": """<p>Read <code>x-oauth-scopes</code> off <code>GET /user</code> and compare it against what the job actually does. A read-only integration that holds <code>repo</code>, <code>workflow</code>, <code>admin:org</code>, <code>delete_repo</code> or <code>write:packages</code> is holding write authority it has never exercised, and the size of that authority is the number of repositories the account can reach.</p>
<p>There is a second, less obvious finding underneath. For a private repository, the minimum <em>classic</em> scope is <code>repo</code>, and <code>repo</code> is read and write together. You cannot fix that by choosing a narrower classic scope, because there isn't one. The repair is a different credential type: a fine-grained token or an App installation with <code>Contents: Read</code> and <code>Pull requests: Read</code>. The script prints that permission list for you to mint.</p>""",
"problem": """<p>The hard part is that there is nothing to debug. Every other note in this section starts from a failure; this one starts from a graph that is flat and a job that is green. That means it never gets prioritised, and it means the person who raises it has to argue rather than point.</p>
<p>It is also self-reinforcing. The habit that produces it is the same habit that resolves the last permissions ticket: something 403s, somebody ticks more boxes, the call works, the token is now broader and nobody narrows it afterwards. Every scope a token holds is the fossil of one incident, and none of them are ever removed.</p>
<p>Then the token spreads. It goes into CI, into a container image, into a developer's shell profile, into a script somebody copied. By the time it leaks &mdash; in a log line, a screenshot, a pull request diff &mdash; the question is not whether it was necessary but what it can reach, and the answer is every repository the account can see, with write.</p>""",
"why": """<p><strong>Classic scopes are coarse by design.</strong> <code>repo</code> is a single scope covering read, write, settings, deploy keys, statuses and invitations, across every repository the user can reach &mdash; public, private and organization-owned alike. It is not a per-repository grant and it has no read-only variant, so an integration that reads one private repository gets write on all of them.</p>
<p><strong>The blast radius is an account property, not a job property.</strong> A token scoped <code>repo</code> reaches whatever its owner reaches, so it grows when the owner joins a team. The job did not change, the credential did not change, and the number of repositories it can write to went up on somebody else's onboarding day.</p>
<p><strong>Some scopes are strictly destructive.</strong> <code>delete_repo</code> grants nothing readable at all &mdash; there is no read that requires it. If a read-only job holds it, that is unambiguous: it is not there for a reason anyone can name.</p>
<p><strong>Fine-grained tokens exist precisely for this.</strong> They select specific repositories and specific permissions at specific levels, so <code>Contents: Read</code> is a thing you can actually have. They also expire by default, which turns an unbounded leak into a bounded one.</p>
<p><strong>You cannot audit this from the outside.</strong> A read-only token can read its own scopes and nothing else: it cannot enumerate the other tokens on the account, cannot see when they were last used, and cannot tell you who else holds a copy of this one. The inventory this script produces is for the credential it is holding, and that limit is worth stating in the report rather than glossing.</p>""",
"steps": [
 {"h": "Read what the token holds, in one request",
  "body": """<p><code>GET /user</code> returns <code>x-oauth-scopes</code> on the response and the account's repository counts in the body. That is both halves of the inventory: what the credential may do, and how many repositories it may do it to. If the header is absent, you already have a fine-grained or App credential and this note is not about you.</p>"""},
 {"h": "Write down what the job actually reads",
  "body": """<p>Not what it might one day read. The list of endpoints it calls this week: pull requests, issues, workflow runs, organization members. This is the only input the audit needs that the API cannot supply, and it takes five minutes with the source open.</p>"""},
 {"h": "Subtract, and name the verbs rather than the scopes",
  "body": """<p>A report that says "you hold <code>admin:org</code>" gets nodded at. A report that says "this credential can add and remove organization members, and nothing it runs has ever done so" gets acted on. Translate every excess scope into the thing it authorizes.</p>"""},
 {"h": "Notice when the minimum classic scope is still too broad",
  "body": """<p>If the job reads a private repository, the smallest classic scope that works is <code>repo</code>, which includes write. There is no narrower tick box, so no amount of re-minting a classic token improves it. That is the signal to change credential type rather than to change scopes.</p>"""},
 {"h": "Mint the fine-grained replacement and run both in parallel",
  "body": """<p>Create the fine-grained token with the printed permission list, point a copy of the job at it, and let it run alongside the old one for a cycle. When the outputs match, cut over and revoke the classic token. Nothing about this is urgent, which is exactly why it needs to be scheduled.</p>"""},
],
"verify": """<p>Re-run against the fine-grained credential. The absence of <code>x-oauth-scopes</code> is the pass condition, and the script says so rather than reporting an empty scope list.</p>
<pre><code class="language-bash">GITHUB_TOKEN=$FINE_GRAINED python3 github_scope_blast_radius.py --needs pull-requests
# not-scope-based: no x-oauth-scopes header, so this credential carries
# per-repository permissions rather than account-wide scopes. Nothing to narrow.</code></pre>""",
"code_intro": "One GET, and it is <code>GET /user</code>. The rest is a capability model held in two tables: what each write-bearing scope authorizes, in verbs a non-engineer can read, and what the minimum classic scope and fine-grained permission set is for each kind of read a job declares. The interesting output is not a diff but a sentence about a working system, so the verdict has a state for <em>the minimum is still too broad</em>, which is the case no re-minting of a classic token can fix.",
"py_file": "github_scope_blast_radius.py",
"py": '''"""Inventory what a working GitHub token is allowed to do that it never does.

Read only, and in a stronger sense than usual: the single request is GET /user.
Nothing here probes a write to see whether it would be permitted, because a
probe that is permitted is a write. The repair, a fine-grained permission list,
is printed for you to mint.

Nothing is failing when you run this. That is the point of it.
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_scope_blast_radius")

API = "https://api.github.com"
UA = "github-scope-blast-radius/1.0"

# What each scope authorizes, phrased as the thing it lets somebody do rather
# than as the name of the scope. A report that names verbs gets acted on; a
# report that names scopes gets nodded at. Read-only scopes are absent from this
# table on purpose: holding one unnecessarily is untidy, not dangerous.
CAPABILITIES = {
    "repo": ["push to every public and private repository the account can reach",
             "create and remove branches, tags and releases",
             "change repository settings, collaborators and deploy keys"],
    "public_repo": ["push to every public repository the account can reach"],
    "delete_repo": ["permanently remove any repository the account administers"],
    "admin:org": ["add and remove organization members",
                  "create, rename and dissolve teams"],
    "write:org": ["change team membership and organization projects"],
    "admin:org_hook": ["create, edit and remove organization webhooks"],
    "admin:repo_hook": ["create, edit and remove repository webhooks"],
    "write:repo_hook": ["create and edit repository webhooks"],
    "workflow": ["change workflow files, which run on the next push"],
    "write:packages": ["publish and overwrite package versions"],
    "delete:packages": ["permanently remove published package versions"],
    "gist": ["create and edit gists on the account"],
    "user": ["change the account profile and its email addresses"],
    "admin:public_key": ["add an SSH key to the account"],
    "admin:gpg_key": ["add a signing key to the account"],
    "write:discussion": ["post and edit team discussions"],
    "notifications": ["mark notifications read and manage subscriptions"],
}

# The smallest classic scope that serves each kind of read. An empty list means
# no scope at all is required, which surprises people: public repository data is
# readable by any authenticated caller.
NEEDS_CLASSIC = {
    "public-repos": [],
    "private-repos": ["repo"],
    "pull-requests": ["repo"],
    "issues": ["repo"],
    "actions-runs": ["repo"],
    "org-members": ["read:org"],
    "repo-hooks": ["read:repo_hook"],
    "packages": ["read:packages"],
    "user-profile": ["read:user"],
}

# The same reads expressed as fine-grained permissions, which is the repair.
NEEDS_FINE_GRAINED = {
    "public-repos": ["Metadata: Read"],
    "private-repos": ["Contents: Read", "Metadata: Read"],
    "pull-requests": ["Metadata: Read", "Pull requests: Read"],
    "issues": ["Issues: Read", "Metadata: Read"],
    "actions-runs": ["Actions: Read", "Metadata: Read"],
    "org-members": ["Members: Read (organization)"],
    "repo-hooks": ["Webhooks: Read"],
    "packages": ["Packages: Read"],
    "user-profile": ["Profile: Read (account)"],
}

# Classic scopes that grant write and cannot be avoided for the reads that need
# them. Holding one of these is not a mistake in scope choice; it is the reason
# to stop using classic tokens.
UNAVOIDABLY_BROAD = {"repo", "public_repo"}


def held_scopes(headers):
    """Read x-oauth-scopes and say what kind of credential this is. Pure.

    Returns (scopes, kind). An absent header is the healthy answer here, not a
    missing one: fine-grained tokens and App installation tokens do not carry
    account-wide scopes at all.
    """
    lowered = {str(k).lower(): v for k, v in (headers or {}).items()}
    if "x-oauth-scopes" not in lowered:
        return None, "not-scope-based"
    raw = lowered["x-oauth-scopes"]
    return [s.strip() for s in str(raw).split(",") if s.strip()], "scope-based"


def required(reads):
    """Minimum classic scopes and fine-grained permissions for declared reads. Pure.

    Unrecognised names come back in `unknown` rather than being silently
    dropped, because a typo that quietly shrinks the requirement would make a
    token look over-scoped when it is not.
    """
    classic, fine, unknown = set(), set(), []
    for name in reads or []:
        key = str(name).strip().lower()
        if not key:
            continue
        if key not in NEEDS_CLASSIC:
            unknown.append(key)
            continue
        classic.update(NEEDS_CLASSIC[key])
        fine.update(NEEDS_FINE_GRAINED[key])
    return {"classic": sorted(classic), "fine_grained": sorted(fine),
            "unknown": sorted(unknown)}


def capabilities(scopes):
    """Every write verb the given scopes authorize, deduplicated. Pure."""
    verbs = []
    for scope in sorted(set(scopes or [])):
        for verb in CAPABILITIES.get(scope, ()):
            if verb not in verbs:
                verbs.append(verb)
    return verbs


def excess(held, needed_classic):
    """Scopes held that no declared read asks for. Pure.

    A plain difference against the minimum set, which is enough because the
    minimum is exact: anything outside it was not asked for, whether it is
    broader or merely unrelated.
    """
    needed = set(needed_classic or [])
    return sorted(s for s in set(held or []) if s not in needed)


def blast_radius(user, held):
    """How many repositories the write verbs reach. Pure.

    Counts from the GET /user body rather than a listing, so the audit stays one
    request. Returns None for the count when the body did not say, because a
    guessed number in a security report is worse than an absent one.
    """
    writes = [s for s in (held or []) if s in CAPABILITIES]
    body = user if isinstance(user, dict) else {}
    total = 0
    seen_any = False
    for field in ("public_repos", "total_private_repos"):
        value = body.get(field)
        if isinstance(value, int):
            total += value
            seen_any = True
    return {"repositories": total if seen_any else None,
            "write_scopes": writes,
            "verbs": capabilities(writes)}


def verdict(kind, held, needed, radius):
    """Turn the inventory into a finding about a system that is working. Pure."""
    if kind == "not-scope-based":
        return ("not-scope-based",
                "no x-oauth-scopes header, so this credential carries "
                "per-repository permissions rather than account-wide scopes. "
                "There is nothing to narrow here.")

    unnecessary = excess(held, needed["classic"])
    dangerous = [s for s in unnecessary if s in CAPABILITIES]
    reach = radius.get("repositories")
    where = ("%d repositories" % reach) if reach is not None \\
        else "every repository the account can reach"

    if dangerous:
        return ("over-scoped",
                "%d scope(s) held that no declared read needs, and %d of them "
                "grant write across %s: %s"
                % (len(unnecessary), len(dangerous), where, ", ".join(dangerous)))
    if unnecessary:
        return ("unused-scopes",
                "%d scope(s) held that no declared read needs: %s. None of them "
                "grant write, so this is untidy rather than dangerous."
                % (len(unnecessary), ", ".join(unnecessary)))
    if set(held or []) & UNAVOIDABLY_BROAD:
        return ("coarse-by-construction",
                "the scopes held are the minimum a classic token can have for "
                "these reads, and they still grant write across %s. No classic "
                "token is narrower than this one; the repair is a different "
                "credential type." % where)
    return ("least-privilege",
            "every scope held is required by a declared read, and none of them "
            "grant write.")


def get(session, path):
    """One GET. Returns (status, json-or-None, headers)."""
    url = API + path if path.startswith("/") else path
    r = session.get(url, timeout=30)
    try:
        body = r.json()
    except ValueError:
        body = None
    return r.status_code, body, dict(r.headers)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--needs", default="",
                    help="comma-separated list of what the job reads: " +
                         ", ".join(sorted(NEEDS_CLASSIC)))
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_TOKEN to the credential you want inventoried")
        return 2

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": UA,
    })

    status, body, headers = get(session, "/user")
    if status == 401:
        log.error("GET /user returned 401. This credential does not "
                  "authenticate, which is a different note")
        return 2
    if status != 200:
        log.error("GET /user returned %d; cannot inventory the credential", status)
        return 2

    held, kind = held_scopes(headers)
    needed = required([s for s in args.needs.split(",") if s.strip()])
    radius = blast_radius(body, held)

    log.info("authenticated as %s", (body or {}).get("login", "an unnamed user"))
    log.info("held:     %s", "header absent" if held is None
             else (", ".join(held) or "none"))
    log.info("required: %s", ", ".join(needed["classic"]) or
             "no scope at all for the declared reads")
    if needed["unknown"]:
        log.warning("unrecognised read(s) %s were ignored; a typo here makes a "
                    "token look broader than it is",
                    ", ".join(needed["unknown"]))

    for verb in radius["verbs"]:
        log.warning("this credential can %s", verb)

    state, detail = verdict(kind, held, needed, radius)
    log.info("%s: %s", state, detail)

    if state in ("over-scoped", "coarse-by-construction"):
        log.info("repair: mint a fine-grained token limited to the repositories "
                 "this job reads, with exactly: %s",
                 ", ".join(needed["fine_grained"]) or "Metadata: Read")
        log.info("repair: run both credentials side by side for one cycle, "
                 "compare the output, then revoke the classic token.")
    if state == "unused-scopes":
        log.info("repair: re-mint without %s. Scopes cannot be removed from an "
                 "existing classic token.",
                 ", ".join(excess(held, needed["classic"])))

    log.info("note: a read-only token can only inventory itself. It cannot "
             "enumerate the other tokens on this account or say who else holds "
             "a copy of this one.")

    print(json.dumps({"kind": kind, "held": held, "required": needed,
                      "blast_radius": radius, "state": state}, indent=2))
    return 0 if state in ("least-privilege", "not-scope-based") else 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-scope-blast-radius.mjs",
"js": '''/**
 * Inventory what a working GitHub token is allowed to do that it never does.
 *
 * Read only, and in a stronger sense than usual: the single request is
 * GET /user. Nothing here probes a write to see whether it would be permitted,
 * because a probe that is permitted is a write.
 *
 * Nothing is failing when you run this. That is the point of it.
 */
const API = 'https://api.github.com';
const UA = 'github-scope-blast-radius/1.0';

/** What each scope authorizes, phrased as a verb rather than as a scope name. */
export const CAPABILITIES = {
  repo: ['push to every public and private repository the account can reach',
    'create and remove branches, tags and releases',
    'change repository settings, collaborators and deploy keys'],
  public_repo: ['push to every public repository the account can reach'],
  delete_repo: ['permanently remove any repository the account administers'],
  'admin:org': ['add and remove organization members',
    'create, rename and dissolve teams'],
  'write:org': ['change team membership and organization projects'],
  'admin:org_hook': ['create, edit and remove organization webhooks'],
  'admin:repo_hook': ['create, edit and remove repository webhooks'],
  'write:repo_hook': ['create and edit repository webhooks'],
  workflow: ['change workflow files, which run on the next push'],
  'write:packages': ['publish and overwrite package versions'],
  'delete:packages': ['permanently remove published package versions'],
  gist: ['create and edit gists on the account'],
  user: ['change the account profile and its email addresses'],
  'admin:public_key': ['add an SSH key to the account'],
  'admin:gpg_key': ['add a signing key to the account'],
  'write:discussion': ['post and edit team discussions'],
  notifications: ['mark notifications read and manage subscriptions'],
};

/** The smallest classic scope that serves each kind of read. */
export const NEEDS_CLASSIC = {
  'public-repos': [],
  'private-repos': ['repo'],
  'pull-requests': ['repo'],
  issues: ['repo'],
  'actions-runs': ['repo'],
  'org-members': ['read:org'],
  'repo-hooks': ['read:repo_hook'],
  packages: ['read:packages'],
  'user-profile': ['read:user'],
};

/** The same reads expressed as fine-grained permissions, which is the repair. */
export const NEEDS_FINE_GRAINED = {
  'public-repos': ['Metadata: Read'],
  'private-repos': ['Contents: Read', 'Metadata: Read'],
  'pull-requests': ['Metadata: Read', 'Pull requests: Read'],
  issues: ['Issues: Read', 'Metadata: Read'],
  'actions-runs': ['Actions: Read', 'Metadata: Read'],
  'org-members': ['Members: Read (organization)'],
  'repo-hooks': ['Webhooks: Read'],
  packages: ['Packages: Read'],
  'user-profile': ['Profile: Read (account)'],
};

/** Classic scopes that grant write and cannot be avoided for some reads. */
export const UNAVOIDABLY_BROAD = new Set(['repo', 'public_repo']);

/** Read x-oauth-scopes and say what kind of credential this is. Pure. */
export function heldScopes(headers) {
  const lowered = {};
  for (const [k, v] of Object.entries(headers ?? {})) lowered[String(k).toLowerCase()] = v;
  if (!('x-oauth-scopes' in lowered)) return [null, 'not-scope-based'];
  const raw = lowered['x-oauth-scopes'];
  return [String(raw).split(',').map((s) => s.trim()).filter(Boolean), 'scope-based'];
}

/** Minimum classic scopes and fine-grained permissions for declared reads. Pure. */
export function required(reads) {
  const classic = new Set();
  const fine = new Set();
  const unknown = [];
  for (const name of reads ?? []) {
    const key = String(name).trim().toLowerCase();
    if (!key) continue;
    if (!(key in NEEDS_CLASSIC)) { unknown.push(key); continue; }
    for (const s of NEEDS_CLASSIC[key]) classic.add(s);
    for (const p of NEEDS_FINE_GRAINED[key]) fine.add(p);
  }
  return {
    classic: [...classic].sort(),
    fine_grained: [...fine].sort(),
    unknown: unknown.sort(),
  };
}

/** Every write verb the given scopes authorize, deduplicated. Pure. */
export function capabilities(scopes) {
  const verbs = [];
  for (const scope of [...new Set(scopes ?? [])].sort()) {
    for (const verb of CAPABILITIES[scope] ?? []) {
      if (!verbs.includes(verb)) verbs.push(verb);
    }
  }
  return verbs;
}

/** Scopes held that no declared read asks for. Pure. */
export function excess(held, neededClassic) {
  const needed = new Set(neededClassic ?? []);
  return [...new Set(held ?? [])].filter((s) => !needed.has(s)).sort();
}

/** How many repositories the write verbs reach. Pure. */
export function blastRadius(user, held) {
  const writes = (held ?? []).filter((s) => s in CAPABILITIES);
  const body = (user && typeof user === 'object') ? user : {};
  let total = 0;
  let seenAny = false;
  for (const field of ['public_repos', 'total_private_repos']) {
    if (Number.isInteger(body[field])) { total += body[field]; seenAny = true; }
  }
  return {
    repositories: seenAny ? total : null,
    write_scopes: writes,
    verbs: capabilities(writes),
  };
}

/** Turn the inventory into a finding about a system that is working. Pure. */
export function verdict(kind, held, needed, radius) {
  if (kind === 'not-scope-based') {
    return ['not-scope-based',
      'no x-oauth-scopes header, so this credential carries per-repository ' +
      'permissions rather than account-wide scopes. There is nothing to narrow here.'];
  }

  const unnecessary = excess(held, needed.classic);
  const dangerous = unnecessary.filter((s) => s in CAPABILITIES);
  const reach = radius.repositories;
  const where = (reach === null || reach === undefined)
    ? 'every repository the account can reach' : `${reach} repositories`;

  if (dangerous.length) {
    return ['over-scoped',
      `${unnecessary.length} scope(s) held that no declared read needs, and ` +
      `${dangerous.length} of them grant write across ${where}: ${dangerous.join(', ')}`];
  }
  if (unnecessary.length) {
    return ['unused-scopes',
      `${unnecessary.length} scope(s) held that no declared read needs: ` +
      `${unnecessary.join(', ')}. None of them grant write, so this is untidy ` +
      'rather than dangerous.'];
  }
  if ((held ?? []).some((s) => UNAVOIDABLY_BROAD.has(s))) {
    return ['coarse-by-construction',
      'the scopes held are the minimum a classic token can have for these ' +
      `reads, and they still grant write across ${where}. No classic token is ` +
      'narrower than this one; the repair is a different credential type.'];
  }
  return ['least-privilege',
    'every scope held is required by a declared read, and none of them grant write.'];
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
  const headers = {};
  for (const [k, v] of res.headers.entries()) headers[k] = v;
  return { status: res.status, body, headers };
}

async function main() {
  const token = process.env.GITHUB_TOKEN;
  if (!token) {
    console.error('set GITHUB_TOKEN to the credential you want inventoried');
    process.exitCode = 2;
    return;
  }
  const reads = (process.argv[2] ?? '').split(',').map((s) => s.trim()).filter(Boolean);

  const user = await get(token, '/user');
  if (user.status === 401) {
    console.error('GET /user returned 401. This credential does not ' +
      'authenticate, which is a different note');
    process.exitCode = 2;
    return;
  }
  if (user.status !== 200) {
    console.error(`GET /user returned ${user.status}; cannot inventory the credential`);
    process.exitCode = 2;
    return;
  }

  const [held, kind] = heldScopes(user.headers);
  const needed = required(reads);
  const radius = blastRadius(user.body, held);

  console.log(`authenticated as ${user.body?.login ?? 'an unnamed user'}`);
  console.log(`held:     ${held === null ? 'header absent' : (held.join(', ') || 'none')}`);
  console.log(`required: ${needed.classic.join(', ') || 'no scope at all for the declared reads'}`);
  if (needed.unknown.length) {
    console.warn(`unrecognised read(s) ${needed.unknown.join(', ')} were ignored; ` +
      'a typo here makes a token look broader than it is');
  }
  for (const verb of radius.verbs) console.warn(`this credential can ${verb}`);

  const [state, detail] = verdict(kind, held, needed, radius);
  console.log(`${state}: ${detail}`);

  if (state === 'over-scoped' || state === 'coarse-by-construction') {
    console.log('repair: mint a fine-grained token limited to the repositories ' +
      `this job reads, with exactly: ${needed.fine_grained.join(', ') || 'Metadata: Read'}`);
    console.log('repair: run both credentials side by side for one cycle, ' +
      'compare the output, then revoke the classic token.');
  }
  if (state === 'unused-scopes') {
    console.log(`repair: re-mint without ${excess(held, needed.classic).join(', ')}. ` +
      'Scopes cannot be removed from an existing classic token.');
  }
  console.log('note: a read-only token can only inventory itself. It cannot ' +
    'enumerate the other tokens on this account or say who else holds a copy.');

  console.log(JSON.stringify({
    kind, held, required: needed, blast_radius: radius, state,
  }, null, 2));
  process.exitCode = (state === 'least-privilege' || state === 'not-scope-based') ? 0 : 1;
}

// Only run when invoked directly, so importing this module from the test file
// does not execute main() and set an exit code that fails the suite.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The assertions here are about a healthy system, which makes them easy to get subtly wrong. The ones that matter: an absent scope header is the <em>pass</em>, not a failure; a job that reads only public data needs no scope whatsoever; <code>delete_repo</code> on a read-only job is flagged even though nothing has ever used it; and a token holding only <code>repo</code> for a private read is reported as coarse rather than excessive, because no classic token would be narrower.",
"test_py_file": "test_github_scope_blast_radius.py",
"test_py": '''from github_scope_blast_radius import (
    blast_radius, capabilities, excess, held_scopes, required, verdict)

USER = {"login": "octo-bot", "public_repos": 12, "total_private_repos": 88}


def test_an_absent_scope_header_means_a_fine_grained_credential():
    scopes, kind = held_scopes({"X-RateLimit-Limit": "5000"})
    assert scopes is None
    assert kind == "not-scope-based"


def test_the_header_is_read_case_insensitively():
    scopes, kind = held_scopes({"X-OAuth-Scopes": "repo, delete_repo"})
    assert scopes == ["repo", "delete_repo"]
    assert kind == "scope-based"


def test_a_token_minted_with_no_scopes_is_not_the_same_as_no_header():
    scopes, kind = held_scopes({"x-oauth-scopes": ""})
    assert scopes == []
    assert kind == "scope-based"


def test_reading_public_data_requires_no_scope_at_all():
    assert required(["public-repos"])["classic"] == []
    assert required(["public-repos"])["fine_grained"] == ["Metadata: Read"]


def test_a_private_read_needs_the_broadest_classic_scope_there_is():
    assert required(["pull-requests"])["classic"] == ["repo"]


def test_an_unrecognised_read_is_reported_rather_than_dropped():
    out = required(["pull-requests", "telemetry"])
    assert out["unknown"] == ["telemetry"]
    assert out["classic"] == ["repo"]


def test_capabilities_are_verbs_and_deduplicated():
    verbs = capabilities(["repo", "public_repo", "delete_repo"])
    assert any("permanently remove" in v for v in verbs)
    assert len(verbs) == len(set(verbs))


def test_read_only_scopes_authorize_no_verbs():
    assert capabilities(["read:org", "read:packages"]) == []


def test_excess_is_everything_outside_the_minimum():
    assert excess(["repo", "delete_repo", "read:org"], ["repo"]) == [
        "delete_repo", "read:org"]


def test_blast_radius_counts_public_and_private_together():
    radius = blast_radius(USER, ["repo"])
    assert radius["repositories"] == 100
    assert radius["write_scopes"] == ["repo"]


def test_a_body_without_counts_reports_no_number_rather_than_zero():
    assert blast_radius({}, ["repo"])["repositories"] is None


def test_a_fine_grained_token_is_the_pass_condition():
    state, detail = verdict("not-scope-based", None, required([]),
                            blast_radius(USER, None))
    assert state == "not-scope-based"
    assert "nothing to narrow" in detail


def test_a_read_only_job_holding_delete_repo_is_flagged():
    held = ["repo", "delete_repo", "workflow"]
    state, detail = verdict("scope-based", held, required(["pull-requests"]),
                            blast_radius(USER, held))
    assert state == "over-scoped"
    assert "delete_repo" in detail
    assert "100 repositories" in detail


def test_unused_read_scopes_are_untidy_rather_than_dangerous():
    held = ["repo", "read:packages"]
    state, detail = verdict("scope-based", held, required(["pull-requests"]),
                            blast_radius(USER, held))
    assert state == "unused-scopes"
    assert "untidy" in detail


def test_the_minimum_classic_scope_is_still_reported_as_too_broad():
    held = ["repo"]
    state, detail = verdict("scope-based", held, required(["pull-requests"]),
                            blast_radius(USER, held))
    assert state == "coarse-by-construction"
    assert "different credential type" in detail


def test_a_genuinely_minimal_token_is_clean():
    held = ["read:org"]
    state, _ = verdict("scope-based", held, required(["org-members"]),
                       blast_radius(USER, held))
    assert state == "least-privilege"
''',
"test_js_file": "github-scope-blast-radius.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  blastRadius, capabilities, excess, heldScopes, required, verdict,
} from './github-scope-blast-radius.mjs';

const USER = { login: 'octo-bot', public_repos: 12, total_private_repos: 88 };

test('an absent scope header means a fine-grained credential', () => {
  const [scopes, kind] = heldScopes({ 'X-RateLimit-Limit': '5000' });
  assert.equal(scopes, null);
  assert.equal(kind, 'not-scope-based');
});

test('the header is read case-insensitively', () => {
  const [scopes, kind] = heldScopes({ 'X-OAuth-Scopes': 'repo, delete_repo' });
  assert.deepEqual(scopes, ['repo', 'delete_repo']);
  assert.equal(kind, 'scope-based');
});

test('a token minted with no scopes is not the same as no header', () => {
  const [scopes, kind] = heldScopes({ 'x-oauth-scopes': '' });
  assert.deepEqual(scopes, []);
  assert.equal(kind, 'scope-based');
});

test('reading public data requires no scope at all', () => {
  assert.deepEqual(required(['public-repos']).classic, []);
  assert.deepEqual(required(['public-repos']).fine_grained, ['Metadata: Read']);
});

test('a private read needs the broadest classic scope there is', () => {
  assert.deepEqual(required(['pull-requests']).classic, ['repo']);
});

test('an unrecognised read is reported rather than dropped', () => {
  const out = required(['pull-requests', 'telemetry']);
  assert.deepEqual(out.unknown, ['telemetry']);
  assert.deepEqual(out.classic, ['repo']);
});

test('capabilities are verbs and deduplicated', () => {
  const verbs = capabilities(['repo', 'public_repo', 'delete_repo']);
  assert.ok(verbs.some((v) => v.includes('permanently remove')));
  assert.equal(verbs.length, new Set(verbs).size);
});

test('read-only scopes authorize no verbs', () => {
  assert.deepEqual(capabilities(['read:org', 'read:packages']), []);
});

test('excess is everything outside the minimum', () => {
  assert.deepEqual(excess(['repo', 'delete_repo', 'read:org'], ['repo']),
    ['delete_repo', 'read:org']);
});

test('blast radius counts public and private together', () => {
  const radius = blastRadius(USER, ['repo']);
  assert.equal(radius.repositories, 100);
  assert.deepEqual(radius.write_scopes, ['repo']);
});

test('a body without counts reports no number rather than zero', () => {
  assert.equal(blastRadius({}, ['repo']).repositories, null);
});

test('a fine-grained token is the pass condition', () => {
  const [state, detail] = verdict('not-scope-based', null, required([]),
    blastRadius(USER, null));
  assert.equal(state, 'not-scope-based');
  assert.match(detail, /nothing to narrow/);
});

test('a read-only job holding delete_repo is flagged', () => {
  const held = ['repo', 'delete_repo', 'workflow'];
  const [state, detail] = verdict('scope-based', held, required(['pull-requests']),
    blastRadius(USER, held));
  assert.equal(state, 'over-scoped');
  assert.match(detail, /delete_repo/);
  assert.match(detail, /100 repositories/);
});

test('unused read scopes are untidy rather than dangerous', () => {
  const held = ['repo', 'read:packages'];
  const [state, detail] = verdict('scope-based', held, required(['pull-requests']),
    blastRadius(USER, held));
  assert.equal(state, 'unused-scopes');
  assert.match(detail, /untidy/);
});

test('the minimum classic scope is still reported as too broad', () => {
  const held = ['repo'];
  const [state, detail] = verdict('scope-based', held, required(['pull-requests']),
    blastRadius(USER, held));
  assert.equal(state, 'coarse-by-construction');
  assert.match(detail, /different credential type/);
});

test('a genuinely minimal token is clean', () => {
  const held = ['read:org'];
  const [state] = verdict('scope-based', held, required(['org-members']),
    blastRadius(USER, held));
  assert.equal(state, 'least-privilege');
});
''',
"faq": [
 ("Nothing is broken. Why should I spend an afternoon on this?",
  "Because the cost is not paid now, it is paid on the day the token leaves the place you put it, and on that day the only question anyone asks is what it could reach. A classic token scoped repo can push to every repository its owner can see, so a leak in a CI log or a screenshot is an organization-wide event rather than a single-repository one. The work is small and schedulable today and unschedulable later, which is the entire argument."),
 ("Why can't I create a classic token that reads private repositories without writing them?",
  "Because that scope does not exist. The classic scope set has repo, which is read and write across everything the owner can reach, and public_repo, which is the same for public repositories only. There is no read-only variant and no per-repository selection, so for a private read the minimum is also the maximum. That is not a mistake you made in the token dialog; it is the reason fine-grained tokens were introduced."),
 ("Can this script check every token on my account?",
  "No, and no read-only script can. A token can read its own scopes and nothing else: there is no endpoint that lists the personal access tokens on an account for the token holder, no last-used timestamp exposed to it, and no way to discover other copies of itself. The inventory is for the credential in the environment when you ran it, so an account-wide audit means running it once per credential, from wherever that credential lives."),
 ("Should I use a fine-grained token or a GitHub App?",
  "A fine-grained token when the work belongs to a person and a short expiry is acceptable; a GitHub App when the work belongs to a system, needs to outlive whoever set it up, or needs a rate limit that scales with the installation. Both give you per-repository selection and per-resource permission levels, which is the property that matters here. The App additionally issues installation tokens that expire in an hour, which bounds a leak without anybody having to remember to rotate."),
 ("Does removing a scope risk breaking something I cannot see?",
  "It can, which is why the repair is to run both credentials in parallel for a cycle rather than to swap and hope. The failure mode of a too-narrow token is loud and specific: a 403 or a 404 with x-accepted-oauth-scopes naming what it wanted, which is exactly the note on an endpoint accepting a scope your token was never given. Narrowing is safe precisely because being too narrow is diagnosable in one response and being too broad is not diagnosable at all."),
],
"related": [
 ("/github/missing-oauth-scope/", "When the token is missing a scope instead"),
 ("/github/installation-repository-selection-partial/", "An App installed on a subset of repos"),
 ("/github/404-masking-403/", "A permission error disguised as 404 Not Found"),
],
"citations": [CITE_PATS, CITE_OAUTH_SCOPES, CITE_ENDPOINTS, CITE_USERS],
},

{
"slug": "basic-auth-password-removed",
"title": "The client still sends a username and password to the API",
"description": "401 Support for password authentication was removed. The credential is not the problem, the mechanism is. Check the scheme before anything goes on the wire.",
"h1": "the client still sends a username and password to the API",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["support for password authentication was removed",
             "github api 401 basic auth", "github invoke-webrequest credential 401",
             "github basic auth username password removed",
             "github authorization bearer header"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "<code>401 {\"message\": \"Support for password authentication was removed. Please use a personal access token instead.\"}</code>. The reflex is to go and mint a token, which is right, and then to paste it where the password was, which is half right, and then to be surprised when a different call still fails. The credential was never the problem. The envelope was.",
"short_answer": """<p>GitHub removed password authentication from the API. <code>Authorization: Basic base64(user:password)</code> is refused everywhere, permanently, and no password will ever work again. <code>Authorization: Bearer TOKEN</code> is the replacement, <code>Authorization: token TOKEN</code> is still accepted, and <code>Basic base64(user:token)</code> works on some paths and is not worth keeping.</p>
<p>Which of those you are sending is decidable offline, from the header alone, and the script below decides it before making any request. If the configured header is a username and a password, it <strong>refuses to send it</strong>: pushing an account password through one more proxy in order to be told it will not work is not a diagnostic, it is another copy of the password. It reports the shape, prints the replacement header, and separately proves your token is fine with a single <code>GET /user</code>.</p>""",
"problem": """<p>This one has an unusually long tail because it lives in places nobody greps. A PowerShell <code>Invoke-WebRequest -Credential</code> from a 2016 blog post. A <code>~/.netrc</code> entry. A CI job that reuses the same credentials as a Git remote. A library whose constructor still takes <code>(username, password)</code> and quietly builds a Basic header out of whatever it is handed. None of those look like an <code>Authorization</code> header at the call site, which is exactly why they survive the migration.</p>
<p>The error message is also, unusually, helpful enough to cause a second problem. It says "use a personal access token instead", so people put the token where the password was and leave the username in place. That produces <code>Basic base64(user:token)</code>, which works on enough paths to look like a fix and is a shape GitHub has been steering away from for years. The change gets marked done and the retired mechanism stays in the code.</p>
<p>And the failure is total rather than partial, which throws people off the scent. Almost every other credential problem in this section is one endpoint, one org, one repository. This one is every request, immediately, which reads like an outage. The team goes looking for a platform incident instead of for the four characters <code>Basic</code> in a config file.</p>""",
"why": """<p><strong>It is a mechanism removal, not a policy toggle.</strong> There is no organization setting, no plan tier and no header that re-enables it. Password authentication for the API is gone, so this is not something to negotiate with an administrator; it is something to change in the client.</p>
<p><strong>The three accepted shapes are not equivalent.</strong> <code>Bearer TOKEN</code> is the documented form and the one to use. <code>token TOKEN</code> is the older GitHub-specific form and still accepted. <code>Basic base64(user:token)</code> survives on parts of the API and on Git over HTTPS, which is why it lingers, but it carries a username that means nothing and encodes the secret in a way that invites it into places a header would not go.</p>
<p><strong>The distinction is visible without a request.</strong> Base64 is an encoding, not encryption: the client can decode its own header, look at the half after the first colon, and see whether it is a token or a password. That check costs nothing and can run at startup, which is where it belongs.</p>
<p><strong>Sending it to find out is the wrong move.</strong> The documented detection is to make the call and read the message, and for a token that is fine. For an account password it means transmitting a live password through your proxy, your egress logs and your terminal scrollback to learn something the header already told you. A diagnostic that creates a new copy of the secret is a bad diagnostic.</p>
<p><strong>A 401 with a different message is a different note.</strong> Bad credentials means the token itself is wrong, revoked or expired; this message means the mechanism is retired. Reading which of the two you got is the whole triage, and it takes one line.</p>""",
"steps": [
 {"h": "Capture the header the client actually sends",
  "body": """<p>Not what the config says, what goes on the wire. Most HTTP clients will log the request headers behind a debug flag, and library wrappers that take a username and password build the header for you without ever showing it. Put the value in an environment variable and hand it to the script; nothing about it needs to be pasted into a terminal.</p>"""},
 {"h": "Decode it locally and look at the half after the colon",
  "body": """<p>For a <code>Basic</code> header, that half is either a token &mdash; <code>ghp_</code>, <code>gho_</code>, <code>ghs_</code>, <code>github_pat_</code> or forty hex characters &mdash; or it is a password. This is the entire diagnosis and it happens on your machine, with no request and no third copy of the secret.</p>"""},
 {"h": "Do not send a password to confirm it",
  "body": """<p>You already know the answer, and the confirmation costs you a password in a proxy log. The script declines this one deliberately. If you genuinely need the response for a ticket, reproduce it with a throwaway account, not with the credential that is in production.</p>"""},
 {"h": "Prove the token separately",
  "body": """<p>One <code>GET /user</code> with <code>Authorization: Bearer</code> and the token from the environment. A 200 with your login says the credential is good and the mechanism was the only thing wrong, which is the sentence that closes the ticket.</p>"""},
 {"h": "Sweep the call sites, not just the client",
  "body": """<p><code>curl -u</code>, <code>--user</code>, <code>Invoke-WebRequest -Credential</code>, <code>~/.netrc</code>, and any library constructor taking two strings. Each one builds the retired header somewhere you will not find by searching for the word Authorization. Replace them all, then delete the username field entirely rather than leaving it set to something harmless.</p>"""},
],
"verify": """<p>Point the check at the corrected header. The scheme should classify as <code>bearer</code> and the probe should return your login.</p>
<pre><code class="language-bash">GITHUB_AUTH_HEADER="Bearer $GITHUB_TOKEN" python3 github_auth_scheme_check.py
# scheme: bearer, secret 40 char(s), no username
# probe: GET /user returned 200 as octo-bot
# ok: the documented scheme, and the credential behind it authenticates</code></pre>""",
"code_intro": "The interesting property of this script is a request it does not make. Classification is offline: decode the header, split on the first colon, decide whether the second half is a token or a password. Only the <code>Bearer</code> probe goes on the wire, and only with a credential read from the environment. The secret never appears in the output, in the log line, or in the JSON at the end &mdash; the report carries the scheme, the length and whether a username was present, which is everything the repair needs.",
"py_file": "github_auth_scheme_check.py",
"py": '''"""Decide which authentication mechanism a GitHub client is using, offline.

Read only, and one request: GET /user with a Bearer header built from the
environment. The script deliberately never transmits a username and password,
even to reproduce the documented 401. Sending a live password to be told it
will not work costs you a password in a proxy log and buys you nothing the
header did not already say.

Nothing here prints the secret. The report carries the scheme, the length and
whether a username was present.
"""
import argparse
import base64
import binascii
import json
import logging
import os
import re
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_auth_scheme_check")

API = "https://api.github.com"
UA = "github-auth-scheme-check/1.0"

# Prefixes GitHub issues its tokens with. The list is used only to answer "is
# the half after the colon a token or a password", so a new prefix appearing
# here later would make the check more precise rather than change its meaning.
TOKEN_PREFIXES = ("ghp_", "gho_", "ghu_", "ghs_", "ghr_", "github_pat_")
LEGACY_HEX = re.compile(r"^[0-9a-f]{40}$")

# The message that means the mechanism is retired, as opposed to a 401 whose
# message is about the credential itself being wrong.
REMOVED = "support for password authentication was removed"

# Call sites that build the retired header without the word Authorization ever
# appearing. Matched by shape; the matched text is never echoed.
CALL_SITES = (
    ("curl -u", re.compile(r"\\bcurl\\b[^\\n]*?\\s(-u|--user)\\s")),
    ("Invoke-WebRequest -Credential", re.compile(r"-Credential\\b")),
    ("netrc entry", re.compile(r"^\\s*machine\\s+[\\w.]*github", re.I)),
    ("two-string client constructor", re.compile(r"\\b(username|user)\\s*=\\s*[^,\\n]+,\\s*password\\s*=")),
)


def looks_like_token(secret):
    """Is this string shaped like a GitHub token rather than a password? Pure."""
    value = str(secret or "")
    if value.startswith(TOKEN_PREFIXES):
        return True
    return bool(LEGACY_HEX.match(value))


def parse_auth_header(value):
    """Describe an Authorization header without revealing what is in it. Pure.

    Returns the scheme, whether a username was present, the length of the
    secret and whether the secret is token-shaped. The secret itself is never
    part of the return value, so no caller can accidentally log it.
    """
    raw = (value or "").strip()
    if not raw:
        return {"scheme": None, "username_present": False, "secret_length": 0,
                "token_shaped": False, "decoded": True}
    parts = raw.split(None, 1)
    scheme = parts[0].lower()
    rest = parts[1].strip() if len(parts) > 1 else ""

    if scheme != "basic":
        return {"scheme": scheme, "username_present": False,
                "secret_length": len(rest), "token_shaped": looks_like_token(rest),
                "decoded": True}

    try:
        decoded = base64.b64decode(rest, validate=True).decode("utf-8")
    except (binascii.Error, UnicodeDecodeError, ValueError):
        return {"scheme": "basic", "username_present": False, "secret_length": 0,
                "token_shaped": False, "decoded": False}

    user, sep, secret = decoded.partition(":")
    return {"scheme": "basic", "username_present": bool(user) or bool(sep),
            "secret_length": len(secret), "token_shaped": looks_like_token(secret),
            "decoded": True}


def classify(parsed):
    """Name the mechanism from a parsed header. Pure."""
    scheme = (parsed or {}).get("scheme")
    if scheme is None:
        return "no-credential"
    if scheme == "basic":
        if not parsed.get("decoded"):
            return "undecodable-basic"
        return "token-basic" if parsed.get("token_shaped") else "password-basic"
    if scheme == "bearer":
        return "bearer"
    if scheme == "token":
        return "token-scheme"
    return "unknown-scheme"


def password_removed(body):
    """Does this response body carry the retired-mechanism message? Pure."""
    if isinstance(body, dict):
        text = str(body.get("message", ""))
    else:
        text = str(body or "")
    return REMOVED in " ".join(text.lower().split())


def replacement_header():
    """The one line that replaces every retired form. Pure."""
    return "Authorization: Bearer $GITHUB_TOKEN"


def scan_snippet(text):
    """Find call sites that build a username-and-password header. Pure.

    Reports the line number and the shape, never the line. A snippet audit that
    quotes the matching line back at you puts the credential in the report.
    """
    findings = []
    for number, line in enumerate(str(text or "").splitlines(), start=1):
        for label, pattern in CALL_SITES:
            if pattern.search(line):
                findings.append({"line": number, "form": label})
    return findings


def verdict(kind, probe_status, probe_body):
    """Turn the classification and the Bearer probe into a finding. Pure."""
    if kind == "password-basic":
        return ("password-basic",
                "the header is a username and a password. That mechanism was "
                "removed from the API and no password will ever be accepted "
                "again. Nothing was sent: the shape is the answer, and "
                "transmitting it would only add a copy of the password to your "
                "proxy log.")
    if kind == "token-basic":
        return ("token-basic",
                "the header is a username and a token. That still works on much "
                "of the API, which is why it survives, but the username is "
                "meaningless and the form is on the way out. Replace it.")
    if kind == "undecodable-basic":
        return ("undecodable-basic",
                "the header says Basic but the payload is not valid base64, so "
                "something is double-encoding or truncating it before it goes "
                "out. GitHub will read this as no credential at all.")
    if kind == "no-credential":
        return ("no-credential",
                "no Authorization header was configured, so requests go out "
                "anonymous rather than refused, and quietly get the 60 an hour "
                "tier instead of an error.")
    if kind == "unknown-scheme":
        return ("unknown-scheme",
                "the scheme is neither Basic, Bearer nor token, so GitHub will "
                "ignore it and treat the request as unauthenticated.")

    if probe_status == 200:
        return ("ok", "the documented scheme, and the credential behind it "
                      "authenticates.")
    if password_removed(probe_body):
        return ("password-removed-message",
                "the scheme looks right but GitHub still answered with the "
                "retired-mechanism message, so something downstream is "
                "rewriting the header into Basic before it leaves.")
    if probe_status == 401:
        return ("credential-rejected",
                "the mechanism is correct and the credential is not. That is a "
                "different problem from this one: the token is wrong, revoked "
                "or expired rather than badly wrapped.")
    return ("probe-inconclusive",
            "the scheme is correct; the probe returned %s rather than 200, so "
            "judge the credential separately." % probe_status)


def get(session, path):
    """One GET. Returns (status, json-or-None)."""
    url = API + path if path.startswith("/") else path
    r = session.get(url, timeout=30)
    try:
        return r.status_code, r.json()
    except ValueError:
        return r.status_code, None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--snippet-file",
                    help="optional path to a script or config to sweep for "
                         "call sites that build the retired header")
    args = ap.parse_args()

    configured = os.environ.get("GITHUB_AUTH_HEADER")
    parsed = parse_auth_header(configured)
    kind = classify(parsed)
    log.info("scheme: %s, secret %d char(s), %s",
             kind, parsed["secret_length"],
             "username present" if parsed["username_present"] else "no username")

    if kind == "password-basic":
        log.warning("not sending this header. A password is refused by every "
                    "endpoint, and posting it would put a live password in one "
                    "more log")

    probe_status, probe_body = None, None
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        session = requests.Session()
        session.headers.update({
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": UA,
        })
        probe_status, probe_body = get(session, "/user")
        who = (probe_body or {}).get("login", "an unnamed user") \\
            if isinstance(probe_body, dict) else "an unnamed user"
        log.info("probe: GET /user returned %s%s", probe_status,
                 " as " + who if probe_status == 200 else "")
    else:
        log.info("set GITHUB_TOKEN to also prove the credential itself is good")

    state, detail = verdict(kind, probe_status, probe_body)
    log.info("%s: %s", state, detail)

    if state in ("password-basic", "token-basic", "undecodable-basic",
                 "no-credential", "unknown-scheme"):
        log.info("repair: send exactly this and delete the username field: %s",
                 replacement_header())
        log.info("repair: Authorization: token TOKEN is still accepted if a "
                 "library will not emit Bearer, but Basic is not worth keeping.")

    sites = []
    if args.snippet_file:
        with open(args.snippet_file, "r", encoding="utf-8", errors="replace") as fh:
            sites = scan_snippet(fh.read())
        for site in sites:
            log.warning("line %d builds the retired header via %s",
                        site["line"], site["form"])
        if not sites:
            log.info("no call sites in %s build a username and password header",
                     args.snippet_file)

    print(json.dumps({"scheme": kind, "username_present": parsed["username_present"],
                      "secret_length": parsed["secret_length"],
                      "probe_status": probe_status, "call_sites": sites,
                      "state": state}, indent=2))
    return 0 if state == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-auth-scheme-check.mjs",
"js": '''/**
 * Decide which authentication mechanism a GitHub client is using, offline.
 *
 * Read only, and one request: GET /user with a Bearer header built from the
 * environment. The script deliberately never transmits a username and
 * password, even to reproduce the documented 401.
 *
 * Nothing here prints the secret. The report carries the scheme, the length
 * and whether a username was present.
 */
import { readFile } from 'node:fs/promises';

const API = 'https://api.github.com';
const UA = 'github-auth-scheme-check/1.0';

/** Prefixes GitHub issues its tokens with. */
export const TOKEN_PREFIXES = ['ghp_', 'gho_', 'ghu_', 'ghs_', 'ghr_', 'github_pat_'];
const LEGACY_HEX = /^[0-9a-f]{40}$/;

/** The message that means the mechanism is retired rather than the credential wrong. */
export const REMOVED = 'support for password authentication was removed';

/** Call sites that build the retired header without the word Authorization. */
export const CALL_SITES = [
  ['curl -u', /\\bcurl\\b[^\\n]*?\\s(-u|--user)\\s/],
  ['Invoke-WebRequest -Credential', /-Credential\\b/],
  ['netrc entry', /^\\s*machine\\s+[\\w.]*github/i],
  ['two-string client constructor', /\\b(username|user)\\s*=\\s*[^,\\n]+,\\s*password\\s*=/],
];

/** Is this string shaped like a GitHub token rather than a password? Pure. */
export function looksLikeToken(secret) {
  const value = String(secret ?? '');
  if (TOKEN_PREFIXES.some((p) => value.startsWith(p))) return true;
  return LEGACY_HEX.test(value);
}

/**
 * Describe an Authorization header without revealing what is in it. Pure.
 * The secret is never part of the return value, so no caller can log it.
 */
export function parseAuthHeader(value) {
  const raw = String(value ?? '').trim();
  if (!raw) {
    return { scheme: null, username_present: false, secret_length: 0,
      token_shaped: false, decoded: true };
  }
  const space = raw.indexOf(' ');
  const scheme = (space === -1 ? raw : raw.slice(0, space)).toLowerCase();
  const rest = space === -1 ? '' : raw.slice(space + 1).trim();

  if (scheme !== 'basic') {
    return { scheme, username_present: false, secret_length: rest.length,
      token_shaped: looksLikeToken(rest), decoded: true };
  }

  let decoded;
  try {
    const buf = Buffer.from(rest, 'base64');
    if (buf.toString('base64').replace(/=+$/, '') !== rest.replace(/=+$/, '')) {
      throw new Error('not base64');
    }
    decoded = buf.toString('utf8');
  } catch {
    return { scheme: 'basic', username_present: false, secret_length: 0,
      token_shaped: false, decoded: false };
  }

  const colon = decoded.indexOf(':');
  const user = colon === -1 ? decoded : decoded.slice(0, colon);
  const secret = colon === -1 ? '' : decoded.slice(colon + 1);
  return { scheme: 'basic', username_present: Boolean(user) || colon !== -1,
    secret_length: secret.length, token_shaped: looksLikeToken(secret),
    decoded: true };
}

/** Name the mechanism from a parsed header. Pure. */
export function classify(parsed) {
  const scheme = (parsed ?? {}).scheme;
  if (scheme === null || scheme === undefined) return 'no-credential';
  if (scheme === 'basic') {
    if (!parsed.decoded) return 'undecodable-basic';
    return parsed.token_shaped ? 'token-basic' : 'password-basic';
  }
  if (scheme === 'bearer') return 'bearer';
  if (scheme === 'token') return 'token-scheme';
  return 'unknown-scheme';
}

/** Does this response body carry the retired-mechanism message? Pure. */
export function passwordRemoved(body) {
  const text = (body && typeof body === 'object')
    ? String(body.message ?? '') : String(body ?? '');
  return text.toLowerCase().split(/\\s+/).join(' ').includes(REMOVED);
}

/** The one line that replaces every retired form. Pure. */
export function replacementHeader() {
  return 'Authorization: Bearer $GITHUB_TOKEN';
}

/**
 * Find call sites that build a username-and-password header. Pure.
 * Reports the line number and the shape, never the line itself.
 */
export function scanSnippet(text) {
  const findings = [];
  const lines = String(text ?? '').split('\\n');
  for (let i = 0; i < lines.length; i += 1) {
    for (const [label, pattern] of CALL_SITES) {
      if (pattern.test(lines[i])) findings.push({ line: i + 1, form: label });
    }
  }
  return findings;
}

/** Turn the classification and the Bearer probe into a finding. Pure. */
export function verdict(kind, probeStatus, probeBody) {
  if (kind === 'password-basic') {
    return ['password-basic',
      'the header is a username and a password. That mechanism was removed ' +
      'from the API and no password will ever be accepted again. Nothing was ' +
      'sent: the shape is the answer, and transmitting it would only add a ' +
      'copy of the password to your proxy log.'];
  }
  if (kind === 'token-basic') {
    return ['token-basic',
      'the header is a username and a token. That still works on much of the ' +
      'API, which is why it survives, but the username is meaningless and the ' +
      'form is on the way out. Replace it.'];
  }
  if (kind === 'undecodable-basic') {
    return ['undecodable-basic',
      'the header says Basic but the payload is not valid base64, so ' +
      'something is double-encoding or truncating it before it goes out. ' +
      'GitHub will read this as no credential at all.'];
  }
  if (kind === 'no-credential') {
    return ['no-credential',
      'no Authorization header was configured, so requests go out anonymous ' +
      'rather than refused, and quietly get the 60 an hour tier instead of an error.'];
  }
  if (kind === 'unknown-scheme') {
    return ['unknown-scheme',
      'the scheme is neither Basic, Bearer nor token, so GitHub will ignore ' +
      'it and treat the request as unauthenticated.'];
  }

  if (probeStatus === 200) {
    return ['ok', 'the documented scheme, and the credential behind it authenticates.'];
  }
  if (passwordRemoved(probeBody)) {
    return ['password-removed-message',
      'the scheme looks right but GitHub still answered with the ' +
      'retired-mechanism message, so something downstream is rewriting the ' +
      'header into Basic before it leaves.'];
  }
  if (probeStatus === 401) {
    return ['credential-rejected',
      'the mechanism is correct and the credential is not. That is a ' +
      'different problem from this one: the token is wrong, revoked or ' +
      'expired rather than badly wrapped.'];
  }
  return ['probe-inconclusive',
    `the scheme is correct; the probe returned ${probeStatus} rather than 200, ` +
    'so judge the credential separately.'];
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

async function main() {
  const configured = process.env.GITHUB_AUTH_HEADER;
  const parsed = parseAuthHeader(configured);
  const kind = classify(parsed);
  console.log(`scheme: ${kind}, secret ${parsed.secret_length} char(s), ` +
    `${parsed.username_present ? 'username present' : 'no username'}`);

  if (kind === 'password-basic') {
    console.warn('not sending this header. A password is refused by every ' +
      'endpoint, and posting it would put a live password in one more log');
  }

  let probeStatus = null;
  let probeBody = null;
  const token = process.env.GITHUB_TOKEN;
  if (token) {
    const probe = await get(token, '/user');
    probeStatus = probe.status;
    probeBody = probe.body;
    const who = probeBody?.login ?? 'an unnamed user';
    console.log(`probe: GET /user returned ${probeStatus}` +
      (probeStatus === 200 ? ` as ${who}` : ''));
  } else {
    console.log('set GITHUB_TOKEN to also prove the credential itself is good');
  }

  const [state, detail] = verdict(kind, probeStatus, probeBody);
  console.log(`${state}: ${detail}`);

  if (['password-basic', 'token-basic', 'undecodable-basic', 'no-credential',
    'unknown-scheme'].includes(state)) {
    console.log(`repair: send exactly this and delete the username field: ${replacementHeader()}`);
    console.log('repair: Authorization: token TOKEN is still accepted if a ' +
      'library will not emit Bearer, but Basic is not worth keeping.');
  }

  let sites = [];
  const snippetFile = process.argv[2];
  if (snippetFile) {
    sites = scanSnippet(await readFile(snippetFile, 'utf8'));
    for (const site of sites) {
      console.warn(`line ${site.line} builds the retired header via ${site.form}`);
    }
    if (!sites.length) {
      console.log(`no call sites in ${snippetFile} build a username and password header`);
    }
  }

  console.log(JSON.stringify({
    scheme: kind, username_present: parsed.username_present,
    secret_length: parsed.secret_length, probe_status: probeStatus,
    call_sites: sites, state,
  }, null, 2));
  process.exitCode = state === 'ok' ? 0 : 1;
}

// Only run when invoked directly, so importing this module from the test file
// does not execute main() and set an exit code that fails the suite.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The fixtures build their own base64 rather than hard-coding it, which keeps the fake credentials in the test obviously fake and keeps the point visible: the client can decode its own header. The assertions that matter are the two halves of the same <code>Basic</code> shape classifying differently, a malformed payload being reported as malformed rather than as a password, and the parser never returning the secret it just looked at.",
"test_py_file": "test_github_auth_scheme_check.py",
"test_py": '''import base64

from github_auth_scheme_check import (
    classify, parse_auth_header, password_removed, replacement_header,
    scan_snippet, verdict)

FAKE_TOKEN = "ghp_FAKE0000000001"
FAKE_PASSWORD = "hunter2"


def basic(user, secret):
    return "Basic " + base64.b64encode(
        ("%s:%s" % (user, secret)).encode()).decode()


def test_a_password_and_a_token_in_the_same_shape_classify_differently():
    assert classify(parse_auth_header(basic("octocat", FAKE_PASSWORD))) == "password-basic"
    assert classify(parse_auth_header(basic("octocat", FAKE_TOKEN))) == "token-basic"


def test_a_forty_character_hex_secret_is_read_as_a_legacy_token():
    assert classify(parse_auth_header(basic("octocat", "a" * 40))) == "token-basic"


def test_the_parser_never_returns_the_secret():
    parsed = parse_auth_header(basic("octocat", FAKE_PASSWORD))
    assert FAKE_PASSWORD not in str(parsed)
    assert parsed["secret_length"] == len(FAKE_PASSWORD)
    assert parsed["username_present"] is True


def test_bearer_and_token_schemes_are_recognised():
    assert classify(parse_auth_header("Bearer " + FAKE_TOKEN)) == "bearer"
    assert classify(parse_auth_header("token " + FAKE_TOKEN)) == "token-scheme"


def test_the_scheme_is_matched_case_insensitively():
    assert classify(parse_auth_header("BEARER " + FAKE_TOKEN)) == "bearer"


def test_an_absent_header_is_no_credential_rather_than_an_error():
    assert classify(parse_auth_header(None)) == "no-credential"
    assert classify(parse_auth_header("   ")) == "no-credential"


def test_a_broken_base64_payload_is_not_reported_as_a_password():
    assert classify(parse_auth_header("Basic not-base64!!")) == "undecodable-basic"


def test_an_unfamiliar_scheme_is_named_as_such():
    assert classify(parse_auth_header("Negotiate abcdef")) == "unknown-scheme"


def test_the_retired_mechanism_message_is_recognised_in_a_body():
    assert password_removed({"message": "Support for password authentication "
                                        "was removed. Please use a personal "
                                        "access token instead."}) is True
    assert password_removed({"message": "Bad credentials"}) is False


def test_the_message_match_survives_odd_whitespace():
    assert password_removed({"message": "support   for password\\nauthentication "
                                        "was removed"}) is True


def test_a_password_header_is_never_sent():
    state, detail = verdict("password-basic", None, None)
    assert state == "password-basic"
    assert "Nothing was sent" in detail


def test_a_username_and_token_is_flagged_even_though_it_works():
    state, detail = verdict("token-basic", 200, {"login": "octo-bot"})
    assert state == "token-basic"
    assert "on the way out" in detail


def test_a_correct_scheme_with_a_bad_token_is_a_different_problem():
    state, detail = verdict("bearer", 401, {"message": "Bad credentials"})
    assert state == "credential-rejected"
    assert "different problem" in detail


def test_the_retired_message_under_a_bearer_header_means_something_rewrites_it():
    state, _ = verdict("bearer", 401, {"message": "Support for password "
                                                  "authentication was removed."})
    assert state == "password-removed-message"


def test_a_working_bearer_header_is_the_pass():
    assert verdict("bearer", 200, {"login": "octo-bot"})[0] == "ok"


def test_call_sites_are_found_by_shape_and_never_quoted():
    text = "\\n".join([
        "curl -u octocat:%s https://api.github.com/user" % FAKE_PASSWORD,
        "Invoke-WebRequest -Uri $u -Credential $c",
        "client = Client(username=u, password=p)",
        "curl -H \\"Authorization: Bearer $T\\" https://api.github.com/user",
    ])
    sites = scan_snippet(text)
    assert {s["line"] for s in sites} == {1, 2, 3}
    assert FAKE_PASSWORD not in str(sites)


def test_the_replacement_is_a_header_rather_than_a_credential():
    assert replacement_header() == "Authorization: Bearer $GITHUB_TOKEN"
''',
"test_js_file": "github-auth-scheme-check.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  classify, parseAuthHeader, passwordRemoved, replacementHeader, scanSnippet, verdict,
} from './github-auth-scheme-check.mjs';

const FAKE_TOKEN = 'ghp_FAKE0000000001';
const FAKE_PASSWORD = 'hunter2';

const basic = (user, secret) =>
  `Basic ${Buffer.from(`${user}:${secret}`).toString('base64')}`;

test('a password and a token in the same shape classify differently', () => {
  assert.equal(classify(parseAuthHeader(basic('octocat', FAKE_PASSWORD))), 'password-basic');
  assert.equal(classify(parseAuthHeader(basic('octocat', FAKE_TOKEN))), 'token-basic');
});

test('a forty character hex secret is read as a legacy token', () => {
  assert.equal(classify(parseAuthHeader(basic('octocat', 'a'.repeat(40)))), 'token-basic');
});

test('the parser never returns the secret', () => {
  const parsed = parseAuthHeader(basic('octocat', FAKE_PASSWORD));
  assert.ok(!JSON.stringify(parsed).includes(FAKE_PASSWORD));
  assert.equal(parsed.secret_length, FAKE_PASSWORD.length);
  assert.equal(parsed.username_present, true);
});

test('bearer and token schemes are recognised', () => {
  assert.equal(classify(parseAuthHeader(`Bearer ${FAKE_TOKEN}`)), 'bearer');
  assert.equal(classify(parseAuthHeader(`token ${FAKE_TOKEN}`)), 'token-scheme');
});

test('the scheme is matched case-insensitively', () => {
  assert.equal(classify(parseAuthHeader(`BEARER ${FAKE_TOKEN}`)), 'bearer');
});

test('an absent header is no credential rather than an error', () => {
  assert.equal(classify(parseAuthHeader(null)), 'no-credential');
  assert.equal(classify(parseAuthHeader('   ')), 'no-credential');
});

test('a broken base64 payload is not reported as a password', () => {
  assert.equal(classify(parseAuthHeader('Basic not-base64!!')), 'undecodable-basic');
});

test('an unfamiliar scheme is named as such', () => {
  assert.equal(classify(parseAuthHeader('Negotiate abcdef')), 'unknown-scheme');
});

test('the retired mechanism message is recognised in a body', () => {
  assert.equal(passwordRemoved({
    message: 'Support for password authentication was removed. Please use a ' +
      'personal access token instead.',
  }), true);
  assert.equal(passwordRemoved({ message: 'Bad credentials' }), false);
});

test('the message match survives odd whitespace', () => {
  assert.equal(passwordRemoved({
    message: 'support   for password\\nauthentication was removed',
  }), true);
});

test('a password header is never sent', () => {
  const [state, detail] = verdict('password-basic', null, null);
  assert.equal(state, 'password-basic');
  assert.match(detail, /Nothing was sent/);
});

test('a username and token is flagged even though it works', () => {
  const [state, detail] = verdict('token-basic', 200, { login: 'octo-bot' });
  assert.equal(state, 'token-basic');
  assert.match(detail, /on the way out/);
});

test('a correct scheme with a bad token is a different problem', () => {
  const [state, detail] = verdict('bearer', 401, { message: 'Bad credentials' });
  assert.equal(state, 'credential-rejected');
  assert.match(detail, /different problem/);
});

test('the retired message under a bearer header means something rewrites it', () => {
  const [state] = verdict('bearer', 401, {
    message: 'Support for password authentication was removed.',
  });
  assert.equal(state, 'password-removed-message');
});

test('a working bearer header is the pass', () => {
  assert.equal(verdict('bearer', 200, { login: 'octo-bot' })[0], 'ok');
});

test('call sites are found by shape and never quoted', () => {
  const text = [
    `curl -u octocat:${FAKE_PASSWORD} https://api.github.com/user`,
    'Invoke-WebRequest -Uri $u -Credential $c',
    'client = Client(username=u, password=p)',
    'curl -H "Authorization: Bearer $T" https://api.github.com/user',
  ].join('\\n');
  const sites = scanSnippet(text);
  assert.deepEqual([...new Set(sites.map((s) => s.line))].sort(), [1, 2, 3]);
  assert.ok(!JSON.stringify(sites).includes(FAKE_PASSWORD));
});

test('the replacement is a header rather than a credential', () => {
  assert.equal(replacementHeader(), 'Authorization: Bearer $GITHUB_TOKEN');
});
''',
"faq": [
 ("I replaced the password with a token and kept the username. Is that fine?",
  "It works on much of the API, and it is still the wrong shape. Basic base64(user:token) carries a username that GitHub does not use, encodes the secret in a form that tempts people to put it in a URL, and is the one form the documentation has been steering away from for years. The supported header is Authorization: Bearer TOKEN, with Authorization: token TOKEN accepted as the older GitHub-specific spelling. Delete the username field rather than setting it to something harmless."),
 ("Can an organization owner or an enterprise plan re-enable password authentication?",
  "No. This is a removal rather than a setting: there is no toggle in organization settings, no plan that restores it, and no header or API version that opts back in. Anything that still works with a username and a password is not hitting the GitHub API, and anything that needs to keep working has to change its client."),
 ("Why does the script refuse to send the header to confirm the diagnosis?",
  "Because the confirmation is already in your hand and sending it is not free. Base64 is an encoding, so the client can decode its own header and read the half after the colon without a request; making the call instead puts a live account password into GitHub's request path, your egress proxy's log and whatever captures your terminal. That is a new copy of a secret bought in exchange for information you already had."),
 ("Git push over HTTPS still asks me for a username and password. Is that the same problem?",
  "It is the same removal wearing different clothes. Git over HTTPS also stopped accepting an account password, so the answer at that prompt is a personal access token in the password field, or better, a credential helper or SSH. The API and Git share the credential store often enough that a stale ~/.netrc entry or an old credential-helper cache will produce both failures at once, which is worth checking when the API fix does not seem to stick."),
 ("The header is a Bearer token and I still get 401. What now?",
  "Then the mechanism is right and the credential is not, which is a different diagnosis. A 401 whose message is about bad credentials means the token is wrong, revoked or expired rather than badly wrapped, and the repair is a new token rather than a new header. The one case worth ruling out first is a proxy or SDK that rewrites the header on the way out, which is why the script separates the retired-mechanism message from every other 401 rather than treating them as one."),
],
"related": [
 ("/github/token-in-query-string/", "The token is passed as a query parameter"),
 ("/github/rate-limit-unauthenticated/", "Requests go out anonymous, capped at 60 an hour"),
 ("/github/404-masking-403/", "A permission error disguised as 404 Not Found"),
],
"citations": [CITE_AUTHENTICATING, CITE_GETTING_STARTED, CITE_CREDS_SECURE, CITE_PATS],
},

{
"slug": "token-in-query-string",
"title": "The token is passed as an access_token query parameter",
"description": "GitHub ignores ?access_token= and the call drops to anonymous. The real cost is the copies it left behind in proxy logs, CI output and browser history.",
"h1": "the token is passed as an access_token query parameter",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github access_token query parameter removed",
             "github api token in url", "github token leaked in logs",
             "github requires authentication 401 access_token",
             "revoke leaked github token"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The call returns <code>401 {\"message\": \"Requires authentication\"}</code> for an endpoint that plainly ought to work, and the token in the URL is correct &mdash; you can paste it into a header and watch the same call succeed. That is the small half of this. The large half is that the URL is now in an access log, a CI transcript, a browser history and a support ticket, and nothing about that half produces an error at all.",
"short_answer": """<p>GitHub removed the <code>?access_token=</code> query parameter. A request carrying it is treated as unauthenticated, which means it silently falls to the 60-an-hour anonymous tier before it starts returning 401 on anything that requires a caller. Moving the credential into <code>Authorization: Bearer TOKEN</code> fixes the request.</p>
<p>It does not fix the disclosure, and the disclosure is the reason this note exists. A URL is the single most-copied string in any system: it is logged by your proxy, by GitHub, by every CDN in between, by the CI runner that echoed the command, and by the browser that opened it. Assume every token that has ever been in a URL is public. The script below audits URLs for credential-shaped values, reports their shape, location and a digest so you can correlate them, and prints a scrubbed URL to paste into the ticket. It never prints the value, and it never sends one.</p>""",
"problem": """<p>The obvious detection is the one you should not run. The documented tell is that <code>GET /rate_limit?access_token=TOKEN</code> reports a limit of 60 instead of 5,000, which is true, and which requires you to send a live credential in a URL one more time in order to prove that sending it in a URL was a mistake. Every hop that logs it gets a fresh copy. If you want that reading, it belongs to <a href="/github/rate-limit-unauthenticated/">the anonymous-tier note</a>, and the way to get it there is with the header removed rather than with the token relocated.</p>
<p>The failure is also split in a way that hides it. Endpoints that do not require authentication keep working, because an unauthenticated request to a public repository is a perfectly valid request. So the integration half-works: public reads succeed, private ones 401, and the quota quietly shrinks by a factor of eighty. That reads like a permissions problem, and people go looking at scopes.</p>
<p>Then there is where these URLs come from. Almost nobody types <code>?access_token=</code> deliberately in 2026. They inherit it: a code sample from 2015, a Postman collection, a webhook URL somebody parameterised, a wrapper that appends credentials for a different API and was pointed at this one. The string arrives already written, and the person deploying it has no reason to look at it.</p>""",
"why": """<p><strong>URLs are copied by design.</strong> A header is read by the server and forgotten. A URL is the identity of the request, so it is written into the access log, the error report, the trace span, the retry queue, the CI transcript and the browser's history, by components that are behaving correctly. There is no configuration that makes a query string as private as a header.</p>
<p><strong>Removing it from the code does not remove it from the logs.</strong> This is the part that turns a config change into an incident: the fix stops new copies being made and does nothing about existing ones. A credential that was in a URL has to be revoked and re-minted, not merely relocated.</p>
<p><strong>The degradation happens before the error.</strong> Because the parameter is ignored rather than rejected, the request is anonymous rather than refused. That is why the first symptom is usually a rate-limit surprise rather than a 401, and why the two notes sit next to each other: one is about the tier you fell to, this one is about how you got there.</p>
<p><strong>Shape is enough to identify a credential, and it is safe to print.</strong> <code>ghp_</code>, <code>gho_</code>, <code>ghu_</code>, <code>ghs_</code>, <code>ghr_</code> and <code>github_pat_</code> are documented prefixes, and forty hex characters is the legacy form. Naming the shape and a truncated digest tells you which credential you are looking at and lets you match two occurrences to each other, without the report becoming another copy of the secret.</p>
<p><strong>What a script cannot tell you.</strong> It cannot enumerate the places a URL has already been written, cannot read your proxy's retention policy, and cannot revoke anything from a read-only credential. It can tell you that the value in this URL is the value this process is holding, and that this value still authenticates, which is exactly enough to make revocation non-optional.</p>""",
"steps": [
 {"h": "Collect the URLs rather than the credentials",
  "body": """<p>Grep the access log, the CI transcript and the configuration for <code>api.github.com</code> and feed the matching lines to the script. You are looking for the shape of a request, not for a secret, so this step involves reading logs you already have rather than extracting anything new.</p>"""},
 {"h": "Classify by shape and fingerprint, never by value",
  "body": """<p>A truncated SHA-256 of the value is enough to say "this is the same credential as that one" across two log files, and is not enough to reconstruct it. Everything the report prints should survive being pasted into a ticket that a dozen people can read. Exempt the parameters that are legitimately forty hex characters &mdash; <code>sha</code>, <code>head</code>, <code>base</code> &mdash; or every commit id in the log gets reported as a legacy token and nobody reads the second page.</p>"""},
 {"h": "Ask whether the credential is still live",
  "body": """<p>One <code>GET /rate_limit</code> with the credential in the <strong>header</strong>. A 200 means the value sitting in your logs still works, which converts this from a tidy-up into a revocation. A 401 means it is already dead and the finding is historical.</p>"""},
 {"h": "Move the credential into the header and redeploy",
  "body": """<p><code>Authorization: Bearer TOKEN</code> on every request. Check the wrapper as well as the call site: a client that appends credentials to the query string usually does it in one place, and that place is not where you are looking.</p>"""},
 {"h": "Revoke, re-mint, and scrub what you can reach",
  "body": """<p>In that order. Revoke first, because scrubbing takes days and revocation takes seconds. Then re-mint, redeploy, and go through the log stores you control &mdash; and write down the ones you do not control, because those are the ones that make the revocation necessary rather than optional.</p>"""},
],
"verify": """<p>Re-run over the same log after the fix. A clean pass reports nothing found, and reports it against a credential the script has confirmed is live, so a clean pass means the URLs are clean rather than the token being dead.</p>
<pre><code class="language-bash">python3 github_token_in_url.py --from-file access.log
# credential in this process: sha256:4f2a1c9d0b77, still live
# scanned 812 url(s)
# no-credential-in-url: no query parameter carried a credential-shaped value</code></pre>""",
"code_intro": "This script is defined as much by what it will not do. It never sends a request with a credential in the URL, not even to reproduce the documented 60-versus-5,000 reading, because that reading costs a fresh copy of the secret in every log between here and GitHub. It never prints a value: findings carry a shape, a length and a twelve-character digest. The one live request is <code>GET /rate_limit</code> with the credential in a header, and it answers a single question &mdash; is the thing in your logs still usable.",
"py_file": "github_token_in_url.py",
"py": '''"""Find GitHub credentials sitting in URLs, without ever printing one.

Read only, and one request: GET /rate_limit with the credential in an
Authorization header. That call spends no quota and answers the only question
the API can answer here, which is whether the credential you are holding still
works.

Two things this deliberately does not do. It never issues a request with a
credential in the query string, not even to reproduce the documented
anonymous-tier reading, because doing so writes a fresh copy of the secret into
every log between here and GitHub. And it never emits a credential value: a
finding carries a shape, a length and a truncated digest, all of which are safe
to paste into a ticket.
"""
import argparse
import hashlib
import hmac
import json
import logging
import os
import re
import sys
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_token_in_url")

API = "https://api.github.com"
UA = "github-token-in-url/1.0"

# Documented token prefixes. Naming the shape tells you which credential to
# revoke; it is not itself a secret.
PREFIXES = (
    ("github_pat_", "fine-grained-pat"),
    ("ghp_", "classic-pat"),
    ("gho_", "oauth-token"),
    ("ghu_", "app-user-token"),
    ("ghs_", "app-installation-token"),
    ("ghr_", "refresh-token"),
)
LEGACY_HEX = re.compile(r"^[0-9a-f]{40}$")

# Parameter names that carry a credential whatever the value looks like.
SUSPECT_NAMES = {"access_token", "token", "oauth_token", "api_key", "apikey",
                 "client_secret", "private_token", "auth", "password", "secret"}

# Parameter names whose values are legitimately forty hex characters. Without
# these, every commit SHA in a URL is reported as a legacy token and the report
# becomes noise nobody reads.
GIT_OBJECT_NAMES = {"sha", "commit_sha", "head_sha", "base_sha", "tree_sha",
                    "oid", "ref", "base", "head"}

URL_PATTERN = re.compile(r"https?://[^\\s<>]+")

# Punctuation a log line puts after a URL. Stripped so a quoted URL does not
# carry its closing quote into the audit.
TRAILING = '"' + "'" + ">),.;"

REDACTED = "REDACTED"


def shape_of(value):
    """Name the kind of credential a string looks like. Pure.

    Returns a shape name, never the value. `opaque` means "long enough to be a
    secret and not in a documented form", which is worth reporting when it sits
    in a parameter called access_token.
    """
    text = str(value or "")
    for prefix, name in PREFIXES:
        if text.startswith(prefix):
            return name
    if LEGACY_HEX.match(text):
        return "legacy-hex40"
    return "opaque" if len(text) >= 16 else "short"


def fingerprint(value):
    """A twelve-character digest, for correlating two sightings. Pure.

    Truncated on purpose: enough to say "these two log lines carry the same
    credential", not enough to be a credential.
    """
    digest = hashlib.sha256(str(value or "").encode("utf-8")).hexdigest()
    return "sha256:" + digest[:12]


def same_credential(left, right):
    """Do two fingerprints describe the same value? Pure."""
    if not left or not right:
        return False
    return hmac.compare_digest(str(left), str(right))


def urls_in(text):
    """Every URL in a blob of log or configuration. Pure."""
    return [u.rstrip(TRAILING) for u in URL_PATTERN.findall(str(text or ""))]


def is_credential(name, value):
    """Would this query parameter be reported as carrying a credential? Pure.

    The single place that decision is made, so the reporter and the redactor
    cannot drift apart and start disagreeing about what counts as a secret.
    """
    lowered = str(name or "").lower()
    if lowered in SUSPECT_NAMES:
        return True
    if lowered in GIT_OBJECT_NAMES:
        return False
    return shape_of(value) not in ("short", "opaque")


def credential_params(url):
    """Credential-bearing query parameters in one URL. Pure.

    A parameter is reported when its name is a known credential name or when
    its value is shaped like a token, so a credential hiding under a harmless
    name is still found. The value is never in the return.
    """
    try:
        parts = urlsplit(str(url or ""))
    except ValueError:
        return []
    out = []
    for name, value in parse_qsl(parts.query, keep_blank_values=True):
        if not is_credential(name, value):
            continue
        out.append({"param": name, "shape": shape_of(value), "length": len(value),
                    "fingerprint": fingerprint(value),
                    "ignored_by_github": name.lower() == "access_token"})
    return out


def redact(url):
    """The same URL with every credential-bearing value replaced. Pure.

    This is the artefact you paste into a ticket. Anything that would be
    reported by credential_params is replaced, because both ask is_credential.
    """
    try:
        parts = urlsplit(str(url or ""))
    except ValueError:
        return REDACTED
    if not parts.query:
        return str(url or "")
    pairs = [(name, REDACTED if is_credential(name, value) else value)
             for name, value in parse_qsl(parts.query, keep_blank_values=True)]
    return urlunsplit((parts.scheme, parts.netloc, parts.path,
                       urlencode(pairs), parts.fragment))


def audit(entries):
    """Findings across many labelled URLs, with the redacted form attached. Pure.

    entries: [(label, url), ...] where label is a line number, a file name or
    anything else that helps somebody find the copy again.
    """
    findings = []
    for label, url in entries or []:
        for hit in credential_params(url):
            item = dict(hit)
            item["where"] = label
            item["redacted"] = redact(url)
            findings.append(item)
    return findings


def verdict(findings, live, held_fingerprint):
    """Turn the findings into a decision about revocation. Pure."""
    if not findings:
        return ("no-credential-in-url",
                "no query parameter carried a credential-shaped value.")

    matched = [f for f in findings
               if same_credential(f.get("fingerprint"), held_fingerprint)]
    ignored = [f for f in findings if f.get("ignored_by_github")]
    distinct = len({f.get("fingerprint") for f in findings})

    tail = (" %d of them use access_token, which GitHub ignores outright, so "
            "those requests went out anonymous rather than authenticated."
            % len(ignored)) if ignored else ""

    if matched and live:
        return ("live-credential-in-url",
                "%d occurrence(s) of %d distinct credential(s) in URLs, and one "
                "of them is the credential this process is holding, which still "
                "authenticates. Revoke it; relocating it to a header does not "
                "unwrite the log lines.%s" % (len(findings), distinct, tail))
    if matched:
        return ("dead-credential-in-url",
                "%d occurrence(s) in URLs match the credential this process "
                "holds, and that credential no longer authenticates. The "
                "exposure is historical, but the habit that created it is "
                "not.%s" % (len(findings), tail))
    return ("credential-in-url",
            "%d occurrence(s) of %d distinct credential-shaped value(s) in "
            "URLs. None match the credential this process holds, so their "
            "liveness cannot be judged from here; treat them as live until "
            "somebody proves otherwise.%s" % (len(findings), distinct, tail))


def get(session, path):
    """One GET. Returns (status, json-or-None)."""
    url = API + path if path.startswith("/") else path
    r = session.get(url, timeout=30)
    try:
        return r.status_code, r.json()
    except ValueError:
        return r.status_code, None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("urls", nargs="*", help="URLs to audit")
    ap.add_argument("--from-file",
                    help="a log or config file; every URL in it is audited")
    args = ap.parse_args()

    entries = [("argv[%d]" % i, u) for i, u in enumerate(args.urls, start=1)]
    if args.from_file:
        with open(args.from_file, "r", encoding="utf-8", errors="replace") as fh:
            for number, line in enumerate(fh, start=1):
                for url in urls_in(line):
                    entries.append(("%s:%d" % (args.from_file, number), url))

    token = os.environ.get("GITHUB_TOKEN")
    held_fingerprint, live = None, False
    if token:
        held_fingerprint = fingerprint(token)
        session = requests.Session()
        session.headers.update({
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": UA,
        })
        # In the header, never in the URL. GET /rate_limit spends no quota.
        status, _ = get(session, "/rate_limit")
        live = status == 200
        log.info("credential in this process: %s, %s", held_fingerprint,
                 "still live" if live else "not accepted (status %s)" % status)
    else:
        log.info("set GITHUB_TOKEN to also learn whether a credential found in "
                 "a URL is the one you are holding, and whether it still works")

    log.info("scanned %d url(s)", len(entries))
    findings = audit(entries)
    for item in findings:
        log.warning("%s carries %s (%s, %d chars) in ?%s= ; scrubbed: %s",
                    item["where"], item["fingerprint"], item["shape"],
                    item["length"], item["param"], item["redacted"])

    state, detail = verdict(findings, live, held_fingerprint)
    log.info("%s: %s", state, detail)

    if findings:
        log.info("repair: move the credential into Authorization: Bearer TOKEN "
                 "on every request, including inside any client wrapper that "
                 "appends parameters for you.")
        log.info("repair: revoke and re-mint before scrubbing. Revocation takes "
                 "seconds and log retention takes days.")
        log.info("note: this script cannot enumerate where a URL has already "
                 "been written, and it will not reproduce the leak to measure "
                 "it. The 60-versus-5000 reading belongs to the anonymous-tier "
                 "check, with the header removed rather than the token moved.")

    print(json.dumps({"scanned": len(entries), "findings": findings,
                      "state": state}, indent=2))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-token-in-url.mjs",
"js": '''/**
 * Find GitHub credentials sitting in URLs, without ever printing one.
 *
 * Read only, and one request: GET /rate_limit with the credential in an
 * Authorization header. That call spends no quota and answers the only
 * question the API can answer here.
 *
 * This never issues a request with a credential in the query string, not even
 * to reproduce the documented anonymous-tier reading, and it never emits a
 * credential value. Findings carry a shape, a length and a truncated digest.
 */
import { createHash, timingSafeEqual } from 'node:crypto';
import { readFile } from 'node:fs/promises';

const API = 'https://api.github.com';
const UA = 'github-token-in-url/1.0';

/** Documented token prefixes. The shape is not itself a secret. */
export const PREFIXES = [
  ['github_pat_', 'fine-grained-pat'],
  ['ghp_', 'classic-pat'],
  ['gho_', 'oauth-token'],
  ['ghu_', 'app-user-token'],
  ['ghs_', 'app-installation-token'],
  ['ghr_', 'refresh-token'],
];
const LEGACY_HEX = /^[0-9a-f]{40}$/;

/** Parameter names that carry a credential whatever the value looks like. */
export const SUSPECT_NAMES = new Set(['access_token', 'token', 'oauth_token',
  'api_key', 'apikey', 'client_secret', 'private_token', 'auth', 'password',
  'secret']);

/**
 * Parameter names whose values are legitimately forty hex characters. Without
 * these, every commit SHA in a URL is reported as a legacy token.
 */
export const GIT_OBJECT_NAMES = new Set(['sha', 'commit_sha', 'head_sha',
  'base_sha', 'tree_sha', 'oid', 'ref', 'base', 'head']);

const URL_PATTERN = /https?:\\/\\/[^\\s<>]+/g;

/** Punctuation a log line puts after a URL. */
const TRAILING = /["'>),.;]+$/;

export const REDACTED = 'REDACTED';

/** Name the kind of credential a string looks like. Pure. */
export function shapeOf(value) {
  const text = String(value ?? '');
  for (const [prefix, name] of PREFIXES) {
    if (text.startsWith(prefix)) return name;
  }
  if (LEGACY_HEX.test(text)) return 'legacy-hex40';
  return text.length >= 16 ? 'opaque' : 'short';
}

/** A twelve-character digest, for correlating two sightings. Pure. */
export function fingerprint(value) {
  const digest = createHash('sha256').update(String(value ?? ''), 'utf8').digest('hex');
  return `sha256:${digest.slice(0, 12)}`;
}

/** Do two fingerprints describe the same value? Pure. */
export function sameCredential(left, right) {
  if (!left || !right) return false;
  const a = Buffer.from(String(left));
  const b = Buffer.from(String(right));
  if (a.length !== b.length) return false;
  return timingSafeEqual(a, b);
}

/** Every URL in a blob of log or configuration. Pure. */
export function urlsIn(text) {
  return (String(text ?? '').match(URL_PATTERN) ?? [])
    .map((u) => u.replace(TRAILING, ''));
}

function paramsOf(url) {
  try {
    return new URL(String(url ?? '')).searchParams;
  } catch {
    return null;
  }
}

/**
 * Would this query parameter be reported as carrying a credential? Pure.
 * The single place that decision is made, so the reporter and the redactor
 * cannot drift apart about what counts as a secret.
 */
export function isCredential(name, value) {
  const lowered = String(name ?? '').toLowerCase();
  if (SUSPECT_NAMES.has(lowered)) return true;
  if (GIT_OBJECT_NAMES.has(lowered)) return false;
  const shape = shapeOf(value);
  return shape !== 'short' && shape !== 'opaque';
}

/** Credential-bearing query parameters in one URL. Pure. */
export function credentialParams(url) {
  const params = paramsOf(url);
  if (!params) return [];
  const out = [];
  for (const [name, value] of params.entries()) {
    if (!isCredential(name, value)) continue;
    out.push({
      param: name,
      shape: shapeOf(value),
      length: value.length,
      fingerprint: fingerprint(value),
      ignored_by_github: name.toLowerCase() === 'access_token',
    });
  }
  return out;
}

/** The same URL with every credential-bearing value replaced. Pure. */
export function redact(url) {
  let parsed;
  try {
    parsed = new URL(String(url ?? ''));
  } catch {
    return REDACTED;
  }
  if (!parsed.search) return String(url ?? '');
  const next = new URLSearchParams();
  for (const [name, value] of parsed.searchParams.entries()) {
    next.append(name, isCredential(name, value) ? REDACTED : value);
  }
  parsed.search = next.toString();
  return parsed.toString();
}

/** Findings across many labelled URLs, with the redacted form attached. Pure. */
export function audit(entries) {
  const findings = [];
  for (const [label, url] of entries ?? []) {
    for (const hit of credentialParams(url)) {
      findings.push({ ...hit, where: label, redacted: redact(url) });
    }
  }
  return findings;
}

/** Turn the findings into a decision about revocation. Pure. */
export function verdict(findings, live, heldFingerprint) {
  if (!findings || !findings.length) {
    return ['no-credential-in-url',
      'no query parameter carried a credential-shaped value.'];
  }

  const matched = findings.filter((f) => sameCredential(f.fingerprint, heldFingerprint));
  const ignored = findings.filter((f) => f.ignored_by_github);
  const distinct = new Set(findings.map((f) => f.fingerprint)).size;

  const tail = ignored.length
    ? ` ${ignored.length} of them use access_token, which GitHub ignores ` +
      'outright, so those requests went out anonymous rather than authenticated.'
    : '';

  if (matched.length && live) {
    return ['live-credential-in-url',
      `${findings.length} occurrence(s) of ${distinct} distinct credential(s) ` +
      'in URLs, and one of them is the credential this process is holding, ' +
      'which still authenticates. Revoke it; relocating it to a header does ' +
      `not unwrite the log lines.${tail}`];
  }
  if (matched.length) {
    return ['dead-credential-in-url',
      `${findings.length} occurrence(s) in URLs match the credential this ` +
      'process holds, and that credential no longer authenticates. The ' +
      `exposure is historical, but the habit that created it is not.${tail}`];
  }
  return ['credential-in-url',
    `${findings.length} occurrence(s) of ${distinct} distinct ` +
    'credential-shaped value(s) in URLs. None match the credential this ' +
    'process holds, so their liveness cannot be judged from here; treat them ' +
    `as live until somebody proves otherwise.${tail}`];
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
  return { status: res.status };
}

async function main() {
  const args = process.argv.slice(2);
  const fileIndex = args.indexOf('--from-file');
  const fromFile = fileIndex === -1 ? null : args[fileIndex + 1];
  const urlArgs = args.filter((a, i) =>
    a !== '--from-file' && i !== fileIndex + 1);

  const entries = urlArgs.map((u, i) => [`argv[${i + 1}]`, u]);
  if (fromFile) {
    const lines = (await readFile(fromFile, 'utf8')).split('\\n');
    for (let i = 0; i < lines.length; i += 1) {
      for (const url of urlsIn(lines[i])) entries.push([`${fromFile}:${i + 1}`, url]);
    }
  }

  const token = process.env.GITHUB_TOKEN;
  let heldFingerprint = null;
  let live = false;
  if (token) {
    heldFingerprint = fingerprint(token);
    // In the header, never in the URL. GET /rate_limit spends no quota.
    const rate = await get(token, '/rate_limit');
    live = rate.status === 200;
    console.log(`credential in this process: ${heldFingerprint}, ` +
      (live ? 'still live' : `not accepted (status ${rate.status})`));
  } else {
    console.log('set GITHUB_TOKEN to also learn whether a credential found in ' +
      'a URL is the one you are holding, and whether it still works');
  }

  console.log(`scanned ${entries.length} url(s)`);
  const findings = audit(entries);
  for (const item of findings) {
    console.warn(`${item.where} carries ${item.fingerprint} (${item.shape}, ` +
      `${item.length} chars) in ?${item.param}= ; scrubbed: ${item.redacted}`);
  }

  const [state, detail] = verdict(findings, live, heldFingerprint);
  console.log(`${state}: ${detail}`);

  if (findings.length) {
    console.log('repair: move the credential into Authorization: Bearer TOKEN ' +
      'on every request, including inside any client wrapper that appends ' +
      'parameters for you.');
    console.log('repair: revoke and re-mint before scrubbing. Revocation takes ' +
      'seconds and log retention takes days.');
    console.log('note: this script cannot enumerate where a URL has already ' +
      'been written, and it will not reproduce the leak to measure it.');
  }

  console.log(JSON.stringify({ scanned: entries.length, findings, state }, null, 2));
  process.exitCode = findings.length ? 1 : 0;
}

// Only run when invoked directly, so importing this module from the test file
// does not execute main() and set an exit code that fails the suite.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The load-bearing test in this file is a negative one: take an obviously fake token, put it through every function that produces output, and assert the value appears in none of them. The rest cover the cases that decide whether a report is useful &mdash; a credential hiding under an innocuous parameter name, two sightings of the same value correlating by digest, and a redacted URL that keeps the parts you need to find the request again.",
"test_py_file": "test_github_token_in_url.py",
"test_py": '''import json

from github_token_in_url import (
    audit, credential_params, fingerprint, is_credential, redact,
    same_credential, shape_of, urls_in, verdict)

FAKE = "ghp_FAKE0000000001"
OTHER = "ghs_FAKE0000000002"
BASE = "https://api.github.com/repos/acme/api/issues"


def test_documented_prefixes_are_named():
    assert shape_of(FAKE) == "classic-pat"
    assert shape_of(OTHER) == "app-installation-token"
    assert shape_of("github_pat_FAKE01") == "fine-grained-pat"
    assert shape_of("a" * 40) == "legacy-hex40"


def test_a_short_value_is_not_treated_as_a_credential():
    assert shape_of("30") == "short"
    assert shape_of("") == "short"


def test_a_fingerprint_is_short_stable_and_not_the_value():
    fp = fingerprint(FAKE)
    assert fp.startswith("sha256:")
    assert len(fp) == len("sha256:") + 12
    assert fp == fingerprint(FAKE)
    assert FAKE not in fp


def test_two_sightings_of_one_value_correlate():
    assert same_credential(fingerprint(FAKE), fingerprint(FAKE)) is True
    assert same_credential(fingerprint(FAKE), fingerprint(OTHER)) is False
    assert same_credential(None, fingerprint(FAKE)) is False


def test_the_named_parameter_is_found():
    hits = credential_params("%s?access_token=%s&state=open" % (BASE, FAKE))
    assert len(hits) == 1
    assert hits[0]["param"] == "access_token"
    assert hits[0]["shape"] == "classic-pat"
    assert hits[0]["ignored_by_github"] is True


def test_a_credential_hiding_under_a_harmless_name_is_still_found():
    hits = credential_params("%s?key=%s" % (BASE, FAKE))
    assert len(hits) == 1
    assert hits[0]["param"] == "key"
    assert hits[0]["ignored_by_github"] is False


def test_a_commit_sha_is_not_reported_as_a_legacy_token():
    assert shape_of("a" * 40) == "legacy-hex40"
    assert is_credential("sha", "a" * 40) is False
    assert credential_params("%s?sha=%s" % (BASE, "a" * 40)) == []


def test_a_credential_name_beats_the_git_object_exemption():
    assert is_credential("access_token", "a" * 40) is True


def test_ordinary_parameters_are_left_alone():
    assert credential_params("%s?state=open&per_page=100" % BASE) == []


def test_a_url_with_no_query_is_not_a_finding():
    assert credential_params(BASE) == []


def test_redaction_keeps_the_request_and_drops_the_secret():
    scrubbed = redact("%s?access_token=%s&state=open" % (BASE, FAKE))
    assert FAKE not in scrubbed
    assert "REDACTED" in scrubbed
    assert "state=open" in scrubbed
    assert "/repos/acme/api/issues" in scrubbed


def test_urls_are_pulled_out_of_a_log_line():
    line = '10.0.0.1 - - "GET %s?access_token=%s HTTP/1.1" 200' % (BASE, FAKE)
    found = urls_in(line)
    assert len(found) == 1
    assert found[0].startswith("https://api.github.com/")


def test_nothing_the_script_prints_contains_the_credential():
    entries = [("access.log:12", "%s?access_token=%s" % (BASE, FAKE))]
    findings = audit(entries)
    state, detail = verdict(findings, True, fingerprint(FAKE))
    printed = json.dumps(findings) + state + detail
    assert FAKE not in printed
    assert "sha256:" in printed


def test_a_live_match_demands_revocation():
    findings = audit([("access.log:12", "%s?access_token=%s" % (BASE, FAKE))])
    state, detail = verdict(findings, True, fingerprint(FAKE))
    assert state == "live-credential-in-url"
    assert "Revoke it" in detail
    assert "anonymous" in detail


def test_a_match_on_a_dead_credential_is_historical():
    findings = audit([("access.log:12", "%s?access_token=%s" % (BASE, FAKE))])
    state, detail = verdict(findings, False, fingerprint(FAKE))
    assert state == "dead-credential-in-url"
    assert "historical" in detail


def test_an_unknown_credential_is_assumed_live():
    findings = audit([("access.log:12", "%s?access_token=%s" % (BASE, OTHER))])
    state, detail = verdict(findings, True, fingerprint(FAKE))
    assert state == "credential-in-url"
    assert "treat them as live" in detail


def test_distinct_credentials_are_counted_separately():
    findings = audit([("a", "%s?access_token=%s" % (BASE, FAKE)),
                      ("b", "%s?access_token=%s" % (BASE, FAKE)),
                      ("c", "%s?access_token=%s" % (BASE, OTHER))])
    _, detail = verdict(findings, False, None)
    assert "3 occurrence(s)" in detail
    assert "2 distinct" in detail


def test_a_clean_scan_says_so():
    assert verdict([], True, fingerprint(FAKE))[0] == "no-credential-in-url"
''',
"test_js_file": "github-token-in-url.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  audit, credentialParams, fingerprint, isCredential, redact, sameCredential,
  shapeOf, urlsIn, verdict,
} from './github-token-in-url.mjs';

const FAKE = 'ghp_FAKE0000000001';
const OTHER = 'ghs_FAKE0000000002';
const BASE = 'https://api.github.com/repos/acme/api/issues';

test('documented prefixes are named', () => {
  assert.equal(shapeOf(FAKE), 'classic-pat');
  assert.equal(shapeOf(OTHER), 'app-installation-token');
  assert.equal(shapeOf('github_pat_FAKE01'), 'fine-grained-pat');
  assert.equal(shapeOf('a'.repeat(40)), 'legacy-hex40');
});

test('a short value is not treated as a credential', () => {
  assert.equal(shapeOf('30'), 'short');
  assert.equal(shapeOf(''), 'short');
});

test('a fingerprint is short, stable and not the value', () => {
  const fp = fingerprint(FAKE);
  assert.ok(fp.startsWith('sha256:'));
  assert.equal(fp.length, 'sha256:'.length + 12);
  assert.equal(fp, fingerprint(FAKE));
  assert.ok(!fp.includes(FAKE));
});

test('two sightings of one value correlate', () => {
  assert.equal(sameCredential(fingerprint(FAKE), fingerprint(FAKE)), true);
  assert.equal(sameCredential(fingerprint(FAKE), fingerprint(OTHER)), false);
  assert.equal(sameCredential(null, fingerprint(FAKE)), false);
});

test('the named parameter is found', () => {
  const hits = credentialParams(`${BASE}?access_token=${FAKE}&state=open`);
  assert.equal(hits.length, 1);
  assert.equal(hits[0].param, 'access_token');
  assert.equal(hits[0].shape, 'classic-pat');
  assert.equal(hits[0].ignored_by_github, true);
});

test('a credential hiding under a harmless name is still found', () => {
  const hits = credentialParams(`${BASE}?key=${FAKE}`);
  assert.equal(hits.length, 1);
  assert.equal(hits[0].param, 'key');
  assert.equal(hits[0].ignored_by_github, false);
});

test('a commit sha is not reported as a legacy token', () => {
  assert.equal(shapeOf('a'.repeat(40)), 'legacy-hex40');
  assert.equal(isCredential('sha', 'a'.repeat(40)), false);
  assert.deepEqual(credentialParams(`${BASE}?sha=${'a'.repeat(40)}`), []);
});

test('a credential name beats the git object exemption', () => {
  assert.equal(isCredential('access_token', 'a'.repeat(40)), true);
});

test('ordinary parameters are left alone', () => {
  assert.deepEqual(credentialParams(`${BASE}?state=open&per_page=100`), []);
});

test('a url with no query is not a finding', () => {
  assert.deepEqual(credentialParams(BASE), []);
});

test('redaction keeps the request and drops the secret', () => {
  const scrubbed = redact(`${BASE}?access_token=${FAKE}&state=open`);
  assert.ok(!scrubbed.includes(FAKE));
  assert.match(scrubbed, /REDACTED/);
  assert.match(scrubbed, /state=open/);
  assert.match(scrubbed, /\\/repos\\/acme\\/api\\/issues/);
});

test('urls are pulled out of a log line', () => {
  const line = `10.0.0.1 - - "GET ${BASE}?access_token=${FAKE} HTTP/1.1" 200`;
  const found = urlsIn(line);
  assert.equal(found.length, 1);
  assert.ok(found[0].startsWith('https://api.github.com/'));
});

test('nothing the script prints contains the credential', () => {
  const findings = audit([['access.log:12', `${BASE}?access_token=${FAKE}`]]);
  const [state, detail] = verdict(findings, true, fingerprint(FAKE));
  const printed = JSON.stringify(findings) + state + detail;
  assert.ok(!printed.includes(FAKE));
  assert.match(printed, /sha256:/);
});

test('a live match demands revocation', () => {
  const findings = audit([['access.log:12', `${BASE}?access_token=${FAKE}`]]);
  const [state, detail] = verdict(findings, true, fingerprint(FAKE));
  assert.equal(state, 'live-credential-in-url');
  assert.match(detail, /Revoke it/);
  assert.match(detail, /anonymous/);
});

test('a match on a dead credential is historical', () => {
  const findings = audit([['access.log:12', `${BASE}?access_token=${FAKE}`]]);
  const [state, detail] = verdict(findings, false, fingerprint(FAKE));
  assert.equal(state, 'dead-credential-in-url');
  assert.match(detail, /historical/);
});

test('an unknown credential is assumed live', () => {
  const findings = audit([['access.log:12', `${BASE}?access_token=${OTHER}`]]);
  const [state, detail] = verdict(findings, true, fingerprint(FAKE));
  assert.equal(state, 'credential-in-url');
  assert.match(detail, /treat them as live/);
});

test('distinct credentials are counted separately', () => {
  const findings = audit([
    ['a', `${BASE}?access_token=${FAKE}`],
    ['b', `${BASE}?access_token=${FAKE}`],
    ['c', `${BASE}?access_token=${OTHER}`],
  ]);
  const [, detail] = verdict(findings, false, null);
  assert.match(detail, /3 occurrence\\(s\\)/);
  assert.match(detail, /2 distinct/);
});

test('a clean scan says so', () => {
  assert.equal(verdict([], true, fingerprint(FAKE))[0], 'no-credential-in-url');
});
''',
"faq": [
 ("The token in the URL is correct. Why is the request unauthenticated?",
  "Because GitHub no longer reads it from there. Support for the access_token query parameter was removed, and a parameter that is not read is not an error: the request is simply processed as anonymous. That is why the first symptom is usually a rate-limit surprise rather than a 401, since anonymous callers get 60 requests an hour per IP address rather than 5,000 per token. Endpoints that need a caller then start answering Requires authentication, which is the loud half of the same cause."),
 ("Do I really have to revoke the token, or is moving it to a header enough?",
  "Revoke it. Moving the credential to a header stops new copies being written and does nothing at all about the ones already in your proxy's access log, GitHub's request path, the CI job's stored output, the trace store and whatever browser or terminal history saw it. You cannot audit all of those and you certainly cannot delete all of them, so the only thing that closes the exposure is making the value useless. Revoke first, re-mint, redeploy, and treat scrubbing as cleanup rather than as the fix."),
 ("Why does the script refuse to send the token in a URL to prove the problem?",
  "Because the proof costs a fresh copy of the secret in every log between your process and GitHub, and it tells you something you can determine without it. The documented reading is that a query-string credential reports a core limit of 60 instead of 5,000, and that reading is worth having, but the way to get it safely is to look at the tier with no credential at all, which is the anonymous-tier note. Reproducing a leak in order to measure it is not a diagnostic anyone should ship."),
 ("Is a truncated SHA-256 of the token safe to put in a ticket?",
  "Twelve hex characters of a SHA-256 is not reversible to the input, and its purpose is narrow: to say that the value in this log line is the same value as the one in that log line, or the same one this process is holding. It is a correlation handle rather than a redaction of a low-entropy field, which would be a different question. The alternative in practice is people pasting the last few characters of the real token, which is genuinely worse."),
 ("What about a token in the path, or in a webhook URL, rather than in the query string?",
  "Everything in this note applies with more force. A path is logged exactly like a query string, and a credential embedded in a webhook delivery URL is additionally sitting in the webhook's configuration where anybody with repository admin can read it back. The script audits query parameters because that is the form GitHub used to accept and the form that still shows up in old code, but the rule underneath it is simply that a URL is a public string and a header is not."),
],
"related": [
 ("/github/rate-limit-unauthenticated/", "Requests go out anonymous, capped at 60 an hour"),
 ("/github/basic-auth-password-removed/", "A username and password sent to the API"),
 ("/github/webhook-no-secret/", "A webhook configured with no secret"),
],
"citations": [CITE_CREDS_SECURE, CITE_AUTHENTICATING, CITE_TROUBLESHOOT, CITE_REST_LIMITS],
},

]
