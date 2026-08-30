#!/usr/bin/env python3
"""/github/ field notes, batch J — the writing.

Four notes about requests that are refused, or should be, for a reason the
credential itself does not explain.

The first is a mismatch between a credential and a route. The token is valid,
the App is installed, the permissions are right, and the endpoint will never
accept it because it is asking about a user and an installation is not one. The
work is that no permission fixes this, so the report has to name a different
endpoint rather than a wider grant, and it has to do that from the path rather
than from a header somebody else's note already owns.

The second is a mismatch between a route and a principal, which is the same
sentence with the arrow reversed. Every call works. The finding is that the
thing making them is a person, and a person can resign. The script reads the
profile body rather than any permission surface, because the question is who
rather than what.

The third has no credential in it at all. A date string pinned in a header
years ago names a version that GitHub has since retired, and the integration
that never changed starts answering 410. The list of live versions is public,
so this is one of the few failures that is knowable long before it happens.

The fourth is arithmetic. A GitHub App JWT may not live longer than ten
minutes, the two numbers that decide that are chosen by your own code, and both
of them are readable in the payload without a key and without a request. The
script decodes, subtracts, and stops before the exchange that would mint a
token, because that exchange is a write.

Read only throughout, and in the fourth case barely on the network at all.
"""

CITE_APP_INSTALL_AUTH = ("Authenticating as a GitHub App installation — GitHub Docs",
                         "https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/authenticating-as-a-github-app-installation")
CITE_APP_USER_AUTH = ("Authenticating with a GitHub App on behalf of a user — GitHub Docs",
                      "https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/authenticating-with-a-github-app-on-behalf-of-a-user")
CITE_APP_PERMS = ("Permissions required for GitHub Apps — GitHub Docs",
                  "https://docs.github.com/en/rest/authentication/permissions-required-for-github-apps")
CITE_APP_ENDPOINTS = ("Endpoints available for GitHub App installation access tokens — GitHub Docs",
                      "https://docs.github.com/en/rest/overview/endpoints-available-for-github-app-installation-access-tokens")
CITE_JWT = ("Generating a JSON Web Token (JWT) for a GitHub App — GitHub Docs",
            "https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-a-json-web-token-jwt-for-a-github-app")
CITE_APP_AUTH = ("Authenticating as a GitHub App — GitHub Docs",
                 "https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/authenticating-as-a-github-app")
CITE_APPS_REST = ("Apps — GitHub REST API",
                  "https://docs.github.com/en/rest/apps/apps")
CITE_RFC7519 = ("JSON Web Token (JWT) — RFC 7519",
                "https://www.rfc-editor.org/rfc/rfc7519")
CITE_API_VERSIONS = ("API Versions — GitHub REST API",
                     "https://docs.github.com/en/rest/about-the-rest-api/api-versions")
CITE_BREAKING = ("Breaking changes — GitHub REST API",
                 "https://docs.github.com/en/rest/about-the-rest-api/breaking-changes")
CITE_META = ("Meta — GitHub REST API",
             "https://docs.github.com/en/rest/meta/meta")
CITE_GETTING_STARTED = ("Getting started with the REST API — GitHub Docs",
                        "https://docs.github.com/en/rest/using-the-rest-api/getting-started-with-the-rest-api")
CITE_USERS = ("Users — GitHub REST API",
              "https://docs.github.com/en/rest/users/users")
CITE_ABOUT_APPS = ("About creating GitHub Apps — GitHub Docs",
                   "https://docs.github.com/en/apps/creating-github-apps/about-creating-github-apps/about-creating-github-apps")
CITE_PATS = ("Managing your personal access tokens — GitHub Docs",
             "https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens")

GUIDES = [

{
"slug": "installation-token-rejected-by-endpoint",
"title": "Some endpoints refuse an installation token whatever it holds",
"description": "A valid installation token 403s on GET /user because that route needs a user. No permission opens it, so the repair is a different endpoint.",
"h1": "some endpoints refuse an installation token whatever it holds",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github app resource not accessible by integration user",
             "installation access token get user 403",
             "github app cannot call /user", "github app user-to-server token",
             "endpoints available for installation access tokens"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The App is installed. The JWT signs, the installation token mints, and nineteen calls in a row return exactly what they should. Then <code>GET /user</code> comes back <code>403 {\"message\": \"Resource not accessible by integration\"}</code>, somebody adds a permission, every installer is emailed to accept the upgrade, and the same 403 arrives again the next morning.",
"short_answer": """<p>That route does not accept installation access tokens, and no permission will change that. <code>GET /user</code> means <em>the user this credential belongs to</em>. An installation belongs to an App on an account, not to a person, so there is no user to return and the request is refused before permissions are consulted at all.</p>
<p>Prove it in two GETs. First <code>GET /installation/repositories</code>: a 200 there says the token is alive, valid and unexpired, which eliminates the entire credential from the investigation. Then repeat the failing path and look it up rather than debugging it, because the answer is a property of the route. The repair is a substitute endpoint &mdash; <code>/installation/repositories</code> for <code>/user/repos</code>, <code>/app</code> for <code>/user</code> &mdash; or, where the request genuinely needs a human, a user access token from the App's own authorization flow.</p>""",
"problem": """<p>The message is the problem. <em>Resource not accessible by integration</em> reads like a permissions error, it is the same sentence GitHub uses when a permission really is missing, and it sends every reader to the App settings page. So the permission gets added, the installers are chased for a week to accept the upgrade, and nothing changes &mdash; because the response never named a permission in the first place.</p>
<p>Then the loop tightens. The next theory is that the added permission was the wrong one, so a broader one goes on. An App that only ever needed to read pull requests ends up requesting organization administration, and it is still 403ing on <code>/user</code>, because the endpoint is not asking what the App may do. It is asking who the App is, and getting an answer it cannot use.</p>
<p>It is also unusually easy to inherit. Client libraries and Terraform providers written against personal access tokens call <code>/user</code> early, often just to log who is running. Point one of them at App credentials and it fails on that convenience call, long before it reaches anything you actually wanted. The failing line is in somebody else's code and the path never appears in yours.</p>""",
"why": """<p><strong>There are three credential classes, not one.</strong> A GitHub App can hold a JWT signed with its private key, which identifies the App; an installation access token, which acts as the App on one account; and a user access token, which acts as a person who authorized the App. Routes accept some of these and refuse others, and the refusal is a routing fact rather than a grant.</p>
<p><strong>The <code>/user</code> family is the boundary.</strong> Anything that means <em>the authenticated user</em> &mdash; <code>/user</code>, <code>/user/repos</code>, <code>/user/emails</code>, <code>/user/orgs</code>, <code>/user/installations</code>, <code>/notifications</code>, <code>/gists</code> &mdash; needs a user behind the credential. Installation tokens have none, so all of them refuse, and they refuse identically no matter which permissions the App requested.</p>
<p><strong>The refusal runs in the other direction too.</strong> <code>GET /app</code> and <code>GET /app/installations</code> want the App's JWT and will not take the installation token that the JWT produced. Sending the wrong one of your own two credentials is the same class of mistake, which is why the script sorts for both rather than only for the famous case.</p>
<p><strong>An absent header is a hint, not the diagnosis.</strong> A 403 that carries no <code>x-accepted-github-permissions</code> is a sign that no permission was at issue. That header is the instrument for <a href="/github/app-permission-missing/">the note on missing App permissions</a>; here it is only corroboration, because its absence tells you what the problem is <em>not</em>. The route table tells you what it is, and what to call instead.</p>
<p><strong>A read-only script cannot enumerate the boundary.</strong> There is no endpoint that returns "the set of routes installation tokens may use". The published lists are documentation, so the table below is curated rather than fetched, and the script says so: an unrecognised path gets a heuristic and a clearly labelled confidence rather than a confident wrong answer.</p>""",
"steps": [
 {"h": "Prove the token is alive before you debug anything else",
  "body": """<p><code>GET /installation/repositories</code> is answerable by an installation access token and by nothing else. A 200 there settles that the token minted correctly, has not passed its hour, and is installed somewhere. Every subsequent finding is then about the route, not the credential, and you have stopped guessing which of the two is broken.</p>"""},
 {"h": "Repeat the exact path that was refused",
  "body": """<p>Not an approximation of it. The audience is per route, so <code>/user</code> and <code>/users/octocat</code> give opposite answers despite looking alike, and a path with a query string on it reduces to the same route as one without. Take the path out of the failing log line verbatim.</p>"""},
 {"h": "Look up the route rather than reading the message",
  "body": """<p>Reduce the path to its template &mdash; <code>/repos/acme/api/issues</code> becomes <code>/repos/{owner}/{repo}/issues</code> &mdash; and ask which credential classes that template accepts. If installation tokens are on the list, this note does not apply and the 403 is about a permission after all. If they are not, no permission was ever going to work.</p>"""},
 {"h": "Take the substitute endpoint when there is one",
  "body": """<p><code>/user/repos</code> becomes <code>/installation/repositories</code>, which is better anyway: it returns exactly the repositories the installation covers rather than everything an account can see. <code>/user</code> becomes <code>/app</code> under the JWT if what you wanted was your own identity. Some routes have no equivalent, and the script says so plainly instead of inventing one.</p>"""},
 {"h": "Use a user access token only where a human is genuinely required",
  "body": """<p>Email addresses, notifications and gists belong to people. Reaching them means sending the installer through the App's authorization flow and holding a user access token for that person, which reintroduces exactly the human dependency an App was meant to remove. Worth doing deliberately, and worth not doing by accident.</p>"""},
],
"verify": """<p>Re-run against the substitute path. The state should move from <code>needs-user-context</code> to <code>endpoint-accepted</code>, with the same credential and no permission change anywhere.</p>
<pre><code class="language-bash">python3 github_endpoint_audience.py --path /user/repos
# installation token alive: GET /installation/repositories returned 200
# /user/repos returned 403
# needs-user-context: this route accepts u2s, any. An installation access token
# is not one of them, so no permission opens it.
# repair: call /installation/repositories instead

python3 github_endpoint_audience.py --path /installation/repositories
# endpoint-accepted: /installation/repositories returned 200</code></pre>""",
"code_intro": "Two GETs, one of which exists only to take the credential out of the argument. Everything that produces a finding is a lookup over two curated tables: which credential classes each route template accepts, and what to call instead when yours is not among them. The path reducer is the fiddly part &mdash; a full URL, a query string and a trailing slash all have to land on the same template &mdash; so it is pure, as is the heuristic that handles paths the table has never seen and the verdict that refuses to state a cause for them.",
"py_file": "github_endpoint_audience.py",
"py": '''"""Say why a working GitHub App installation token is refused by one route.

Read only. Two GETs: one that proves the token is alive, and one that repeats
the call that was already failing. Nothing is minted, accepted, widened or
changed. Where the repair is a different endpoint, it is printed.

Some REST routes are unreachable with a server-to-server installation token
whatever permissions the App holds. GET /user is the famous one: it means "the
user this credential belongs to", and an installation belongs to an account
rather than to a person. No permission opens it, because permission is not the
question being asked.

Credential classes, abbreviated the same way throughout:

    s2s   an installation access token, acting as the App on one account
    u2s   a user access token, acting as a person who authorized the App
    jwt   the App's own JSON Web Token, signed with its private key
    any   any authenticated caller, a personal access token included
    none  no credential at all
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_endpoint_audience")

API = "https://api.github.com"
UA = "github-endpoint-audience/1.0"

# Which credential classes each route template accepts. There is no endpoint
# that returns this, so the table is curated from the published lists rather
# than fetched, and anything absent from it is answered by heuristic with the
# uncertainty stated rather than hidden.
AUDIENCES = {
    "/": {"none", "any", "s2s", "u2s", "jwt"},
    "/meta": {"none", "any", "s2s", "u2s", "jwt"},
    "/versions": {"none", "any", "s2s", "u2s", "jwt"},
    "/rate_limit": {"any", "s2s", "u2s", "jwt"},
    "/app": {"jwt"},
    "/app/installations": {"jwt"},
    "/app/installations/{installation_id}": {"jwt"},
    "/installation/repositories": {"s2s"},
    "/user": {"any", "u2s"},
    "/user/repos": {"any", "u2s"},
    "/user/emails": {"any", "u2s"},
    "/user/orgs": {"any", "u2s"},
    "/user/keys": {"any", "u2s"},
    "/user/installations": {"any", "u2s"},
    "/notifications": {"any", "u2s"},
    "/gists": {"any", "u2s"},
    "/users/{username}": {"none", "any", "s2s", "u2s"},
    "/orgs/{org}": {"any", "s2s", "u2s"},
    "/orgs/{org}/repos": {"any", "s2s", "u2s"},
    "/orgs/{org}/members": {"any", "s2s", "u2s"},
    "/repos/{owner}/{repo}": {"any", "s2s", "u2s"},
    "/repos/{owner}/{repo}/issues": {"any", "s2s", "u2s"},
    "/repos/{owner}/{repo}/pulls": {"any", "s2s", "u2s"},
    "/repos/{owner}/{repo}/hooks": {"any", "s2s", "u2s"},
    "/repos/{owner}/{repo}/commits": {"any", "s2s", "u2s"},
    "/search/issues": {"any", "s2s", "u2s"},
}

# What to call instead. None for the second element means there is no
# server-to-server equivalent, which is a real answer and a better one than a
# nearby endpoint that returns different data.
SUBSTITUTES = {
    "/user": ("/app",
              "identifies the App itself, and is called with the App JWT "
              "rather than with the installation token"),
    "/user/repos": ("/installation/repositories",
                    "returns exactly the repositories this installation "
                    "covers, which is narrower and more accurate"),
    "/user/installations": ("/app/installations",
                            "lists the installations of this App, under the "
                            "App JWT"),
    "/user/orgs": ("/app/installations",
                   "each installation names the account it sits on, which is "
                   "the App equivalent of asking which orgs you are in"),
    "/user/emails": (None,
                     "email addresses belong to a person; only a user access "
                     "token can read them"),
    "/user/keys": (None,
                   "SSH keys belong to a person; only a user access token can "
                   "read them"),
    "/notifications": (None,
                       "notifications belong to a person; subscribe the App to "
                       "webhook events instead of polling a human inbox"),
    "/gists": (None, "GitHub Apps cannot reach gists at all"),
    "/app": (None,
             "this route is right, but it wants the App JWT; the installation "
             "token is the thing the JWT produces, not a substitute for it"),
    "/app/installations": (None,
                           "this route wants the App JWT, not the installation "
                           "token it produces"),
}

# Placeholder-free templates are matched first, so /user/repos wins over a
# same-shaped template with a variable in the first position.
ROUTES = sorted(AUDIENCES, key=lambda t: (t.count("{"), t))


def canonical(path):
    """Reduce a request path to the route template it matches. Pure.

    A full URL, a query string, a fragment and a trailing slash all have to
    land on the same template, because the path in a log line is rarely the
    tidy form. Returns None when nothing matches, which the caller reports as
    uncertainty rather than treating as a permitted route.
    """
    raw = str(path or "").split("?")[0].split("#")[0].strip()
    for prefix in ("https://api.github.com", "http://api.github.com"):
        if raw.startswith(prefix):
            raw = raw[len(prefix):]
    if not raw.startswith("/"):
        raw = "/" + raw
    parts = [p for p in raw.split("/") if p]
    if not parts:
        return "/"
    for template in ROUTES:
        segments = [p for p in template.split("/") if p]
        if len(segments) != len(parts):
            continue
        if all(s.startswith("{") or s == got for s, got in zip(segments, parts)):
            return template
    return None


def accepts(route):
    """The credential classes a known route template accepts. Pure."""
    found = AUDIENCES.get(route)
    return set(found) if found else None


def guess(path):
    """Heuristic audience for a path the table has never seen. Pure.

    Returns (classes, reason). classes is None where even the heuristic
    declines, because a guessed answer in this particular report would send
    somebody to rewrite a working call.
    """
    parts = [p for p in str(path or "").split("?")[0].split("/") if p]
    if not parts:
        return None, "an empty path matches nothing"
    head = parts[0]
    if head == "user":
        return ({"any", "u2s"},
                "every route under /user means the authenticated user, and an "
                "installation is not a user")
    if head == "app":
        return ({"jwt"},
                "routes under /app identify the App and are signed with the "
                "App JWT rather than an installation token")
    if head == "installation":
        return ({"s2s"},
                "routes under /installation are the installation's own view "
                "of itself")
    if head in ("notifications", "gists"):
        return ({"any", "u2s"},
                "this resource belongs to a person, so it needs a credential "
                "that has one behind it")
    return None, ("not in the table, and the first path segment carries no "
                  "rule this script is willing to apply")


def substitute(route):
    """The App-appropriate replacement for a route, if there is one. Pure."""
    return SUBSTITUTES.get(route)


def verdict(alive, status, route, classes, guessed=False):
    """Turn a liveness proof and a route lookup into a finding. Pure.

    alive is whether GET /installation/repositories returned 200, which is the
    only thing that distinguishes "the credential is broken" from "the route
    refuses this class of credential". Without it the two are the same 403.
    """
    if not alive:
        return ("not-an-installation-token",
                "GET /installation/repositories did not return 200, so this "
                "credential is not a live installation access token. Whatever "
                "the other call did, it is not the mismatch this script looks "
                "for.")
    if status is not None and status < 400:
        return ("endpoint-accepted",
                "%s returned %d with this installation token, so the route "
                "accepts it." % (route or "that path", status))
    if classes is None:
        return ("route-unknown",
                "this path is not in the route table and the heuristic "
                "declined it, so the audience is genuinely unknown. Check the "
                "published list of endpoints available to installation access "
                "tokens before rewriting anything.")

    hedge = " (by heuristic rather than from the table)" if guessed else ""
    if "s2s" in classes:
        return ("installation-tokens-accepted",
                "this route does accept installation access tokens%s, so the "
                "refusal is about a permission rather than about the "
                "credential class. Read x-accepted-github-permissions on the "
                "same response." % hedge)
    if "jwt" in classes and "u2s" not in classes:
        return ("needs-app-jwt",
                "this route wants the App's own JWT%s. The installation token "
                "is what the JWT produces, not a substitute for it: sign a "
                "fresh JWT and send that instead." % hedge)
    return ("needs-user-context",
            "this route accepts %s%s. An installation access token is not one "
            "of them, so no permission opens it: the credential has no user "
            "behind it and the route is asking about one."
            % (", ".join(sorted(classes)), hedge))


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
    ap.add_argument("--path", default="/user",
                    help="the API path that was refused, taken verbatim from "
                         "the failing log line")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_INSTALLATION_TOKEN") or \\
        os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_INSTALLATION_TOKEN to an installation access "
                  "token. Without one there is no credential class to test a "
                  "route against")
        return 2

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": UA,
    })

    # The liveness proof, and the only request here that is not the reader's
    # own call. Only an installation access token can answer it at all.
    probe_status, probe_body = get(session, "/installation/repositories?per_page=1")
    alive = probe_status == 200
    if alive:
        total = probe_body.get("total_count") if isinstance(probe_body, dict) else None
        log.info("installation token alive: GET /installation/repositories "
                 "returned 200 over %s repositories",
                 total if total is not None else "an unreported number of")
    else:
        log.info("GET /installation/repositories returned %d, so this is not "
                 "a live installation access token", probe_status)

    status = None
    if alive:
        status, _ = get(session, args.path)
        log.info("%s returned %d", args.path, status)

    route = canonical(args.path)
    classes = accepts(route) if route else None
    guessed = False
    if classes is None:
        classes, reason = guess(args.path)
        guessed = classes is not None
        log.info("route: %s", route or "not in the table (%s)" % reason)
    else:
        log.info("route: %s accepts %s", route, ", ".join(sorted(classes)))

    state, detail = verdict(alive, status, route, classes, guessed)
    log.info("%s: %s", state, detail)

    if state in ("needs-user-context", "needs-app-jwt"):
        swap = substitute(route)
        if swap and swap[0]:
            log.info("repair: call %s instead, which %s", swap[0], swap[1])
        elif swap:
            log.info("repair: there is no server-to-server equivalent. %s",
                     swap[1])
        else:
            log.info("repair: find the App equivalent of this route in the "
                     "published endpoint list, or authorize a user and hold a "
                     "user access token for them")
    if state == "installation-tokens-accepted":
        log.info("repair: this is a permissions finding rather than a "
                 "credential-class one; diff the App's permissions against "
                 "the header the failing response carried")

    print(json.dumps({"path": args.path, "route": route, "status": status,
                      "installation_token_alive": alive,
                      "accepts": sorted(classes) if classes else None,
                      "by_heuristic": guessed, "state": state}, indent=2))
    return 1 if state in ("needs-user-context", "needs-app-jwt") else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-endpoint-audience.mjs",
"js": '''/**
 * Say why a working GitHub App installation token is refused by one route.
 *
 * Read only. Two GETs: one that proves the token is alive, and one that
 * repeats the call that was already failing. The repair is a different
 * endpoint, and it is printed rather than applied.
 *
 * Credential classes, abbreviated throughout:
 *   s2s   an installation access token, acting as the App on one account
 *   u2s   a user access token, acting as a person who authorized the App
 *   jwt   the App's own JSON Web Token, signed with its private key
 *   any   any authenticated caller, a personal access token included
 *   none  no credential at all
 */
const API = 'https://api.github.com';
const UA = 'github-endpoint-audience/1.0';

/** Which credential classes each route template accepts. Curated, not fetched. */
export const AUDIENCES = {
  '/': ['none', 'any', 's2s', 'u2s', 'jwt'],
  '/meta': ['none', 'any', 's2s', 'u2s', 'jwt'],
  '/versions': ['none', 'any', 's2s', 'u2s', 'jwt'],
  '/rate_limit': ['any', 's2s', 'u2s', 'jwt'],
  '/app': ['jwt'],
  '/app/installations': ['jwt'],
  '/app/installations/{installation_id}': ['jwt'],
  '/installation/repositories': ['s2s'],
  '/user': ['any', 'u2s'],
  '/user/repos': ['any', 'u2s'],
  '/user/emails': ['any', 'u2s'],
  '/user/orgs': ['any', 'u2s'],
  '/user/keys': ['any', 'u2s'],
  '/user/installations': ['any', 'u2s'],
  '/notifications': ['any', 'u2s'],
  '/gists': ['any', 'u2s'],
  '/users/{username}': ['none', 'any', 's2s', 'u2s'],
  '/orgs/{org}': ['any', 's2s', 'u2s'],
  '/orgs/{org}/repos': ['any', 's2s', 'u2s'],
  '/orgs/{org}/members': ['any', 's2s', 'u2s'],
  '/repos/{owner}/{repo}': ['any', 's2s', 'u2s'],
  '/repos/{owner}/{repo}/issues': ['any', 's2s', 'u2s'],
  '/repos/{owner}/{repo}/pulls': ['any', 's2s', 'u2s'],
  '/repos/{owner}/{repo}/hooks': ['any', 's2s', 'u2s'],
  '/repos/{owner}/{repo}/commits': ['any', 's2s', 'u2s'],
  '/search/issues': ['any', 's2s', 'u2s'],
};

/** What to call instead. A null target means there is no s2s equivalent. */
export const SUBSTITUTES = {
  '/user': ['/app',
    'identifies the App itself, and is called with the App JWT rather than ' +
    'with the installation token'],
  '/user/repos': ['/installation/repositories',
    'returns exactly the repositories this installation covers, which is ' +
    'narrower and more accurate'],
  '/user/installations': ['/app/installations',
    'lists the installations of this App, under the App JWT'],
  '/user/orgs': ['/app/installations',
    'each installation names the account it sits on, which is the App ' +
    'equivalent of asking which orgs you are in'],
  '/user/emails': [null,
    'email addresses belong to a person; only a user access token can read them'],
  '/user/keys': [null,
    'SSH keys belong to a person; only a user access token can read them'],
  '/notifications': [null,
    'notifications belong to a person; subscribe the App to webhook events ' +
    'instead of polling a human inbox'],
  '/gists': [null, 'GitHub Apps cannot reach gists at all'],
  '/app': [null,
    'this route is right, but it wants the App JWT; the installation token is ' +
    'what the JWT produces, not a substitute for it'],
  '/app/installations': [null,
    'this route wants the App JWT, not the installation token it produces'],
};

/** Placeholder-free templates are matched first. */
const ROUTES = Object.keys(AUDIENCES).sort((a, b) => {
  const ca = (a.match(/\\{/g) ?? []).length;
  const cb = (b.match(/\\{/g) ?? []).length;
  return (ca - cb) || a.localeCompare(b);
});

/**
 * Reduce a request path to the route template it matches. Pure.
 * Full URLs, query strings, fragments and trailing slashes all land on the
 * same template. null when nothing matches.
 */
export function canonical(path) {
  let raw = String(path ?? '').split('?')[0].split('#')[0].trim();
  for (const prefix of ['https://api.github.com', 'http://api.github.com']) {
    if (raw.startsWith(prefix)) raw = raw.slice(prefix.length);
  }
  if (!raw.startsWith('/')) raw = `/${raw}`;
  const parts = raw.split('/').filter(Boolean);
  if (!parts.length) return '/';
  for (const template of ROUTES) {
    const segments = template.split('/').filter(Boolean);
    if (segments.length !== parts.length) continue;
    if (segments.every((s, i) => s.startsWith('{') || s === parts[i])) return template;
  }
  return null;
}

/** The credential classes a known route template accepts. Pure. */
export function accepts(route) {
  const found = AUDIENCES[route];
  return found ? new Set(found) : null;
}

/**
 * Heuristic audience for a path the table has never seen. Pure.
 * Returns [classes, reason]; classes is null where the heuristic declines.
 */
export function guess(path) {
  const parts = String(path ?? '').split('?')[0].split('/').filter(Boolean);
  if (!parts.length) return [null, 'an empty path matches nothing'];
  const head = parts[0];
  if (head === 'user') {
    return [new Set(['any', 'u2s']),
      'every route under /user means the authenticated user, and an ' +
      'installation is not a user'];
  }
  if (head === 'app') {
    return [new Set(['jwt']),
      'routes under /app identify the App and are signed with the App JWT ' +
      'rather than an installation token'];
  }
  if (head === 'installation') {
    return [new Set(['s2s']),
      "routes under /installation are the installation's own view of itself"];
  }
  if (head === 'notifications' || head === 'gists') {
    return [new Set(['any', 'u2s']),
      'this resource belongs to a person, so it needs a credential that has ' +
      'one behind it'];
  }
  return [null,
    'not in the table, and the first path segment carries no rule this ' +
    'script is willing to apply'];
}

/** The App-appropriate replacement for a route, if there is one. Pure. */
export function substitute(route) {
  return SUBSTITUTES[route] ?? null;
}

/** Turn a liveness proof and a route lookup into a finding. Pure. */
export function verdict(alive, status, route, classes, guessed = false) {
  if (!alive) {
    return ['not-an-installation-token',
      'GET /installation/repositories did not return 200, so this credential ' +
      'is not a live installation access token. Whatever the other call did, ' +
      'it is not the mismatch this script looks for.'];
  }
  if (status !== null && status !== undefined && status < 400) {
    return ['endpoint-accepted',
      `${route ?? 'that path'} returned ${status} with this installation ` +
      'token, so the route accepts it.'];
  }
  if (!classes) {
    return ['route-unknown',
      'this path is not in the route table and the heuristic declined it, so ' +
      'the audience is genuinely unknown. Check the published list of ' +
      'endpoints available to installation access tokens before rewriting ' +
      'anything.'];
  }

  const hedge = guessed ? ' (by heuristic rather than from the table)' : '';
  if (classes.has('s2s')) {
    return ['installation-tokens-accepted',
      `this route does accept installation access tokens${hedge}, so the ` +
      'refusal is about a permission rather than about the credential class. ' +
      'Read x-accepted-github-permissions on the same response.'];
  }
  if (classes.has('jwt') && !classes.has('u2s')) {
    return ['needs-app-jwt',
      `this route wants the App's own JWT${hedge}. The installation token is ` +
      'what the JWT produces, not a substitute for it: sign a fresh JWT and ' +
      'send that instead.'];
  }
  return ['needs-user-context',
    `this route accepts ${[...classes].sort().join(', ')}${hedge}. An ` +
    'installation access token is not one of them, so no permission opens ' +
    'it: the credential has no user behind it and the route is asking about one.'];
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
  const token = process.env.GITHUB_INSTALLATION_TOKEN ?? process.env.GITHUB_TOKEN;
  if (!token) {
    console.error('set GITHUB_INSTALLATION_TOKEN to an installation access ' +
      'token. Without one there is no credential class to test a route against');
    process.exitCode = 2;
    return;
  }
  const path = process.argv[2] ?? '/user';

  const probe = await get(token, '/installation/repositories?per_page=1');
  const alive = probe.status === 200;
  if (alive) {
    const total = probe.body?.total_count;
    console.log('installation token alive: GET /installation/repositories ' +
      `returned 200 over ${total ?? 'an unreported number of'} repositories`);
  } else {
    console.log(`GET /installation/repositories returned ${probe.status}, so ` +
      'this is not a live installation access token');
  }

  let status = null;
  if (alive) {
    ({ status } = await get(token, path));
    console.log(`${path} returned ${status}`);
  }

  const route = canonical(path);
  let classes = route ? accepts(route) : null;
  let guessed = false;
  if (!classes) {
    const [guessed_classes, reason] = guess(path);
    classes = guessed_classes;
    guessed = Boolean(classes);
    console.log(`route: ${route ?? `not in the table (${reason})`}`);
  } else {
    console.log(`route: ${route} accepts ${[...classes].sort().join(', ')}`);
  }

  const [state, detail] = verdict(alive, status, route, classes, guessed);
  console.log(`${state}: ${detail}`);

  if (state === 'needs-user-context' || state === 'needs-app-jwt') {
    const swap = substitute(route);
    if (swap && swap[0]) {
      console.log(`repair: call ${swap[0]} instead, which ${swap[1]}`);
    } else if (swap) {
      console.log(`repair: there is no server-to-server equivalent. ${swap[1]}`);
    } else {
      console.log('repair: find the App equivalent of this route in the ' +
        'published endpoint list, or authorize a user and hold a user access ' +
        'token for them');
    }
  }
  if (state === 'installation-tokens-accepted') {
    console.log('repair: this is a permissions finding rather than a ' +
      "credential-class one; diff the App's permissions against the header " +
      'the failing response carried');
  }

  console.log(JSON.stringify({
    path,
    route,
    status,
    installation_token_alive: alive,
    accepts: classes ? [...classes].sort() : null,
    by_heuristic: guessed,
    state,
  }, null, 2));
  process.exitCode = (state === 'needs-user-context' ||
    state === 'needs-app-jwt') ? 1 : 0;
}

// Only run when invoked directly, so importing this module from the test file
// does not execute main(), fail on the missing token and set an exit code that
// fails the suite even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The cases worth pinning are the ones that look alike and are not: <code>/user</code> against <code>/users/octocat</code>, a path with a query string against the same path without one, and a route that refuses because it wants a person against a route that refuses because it wants the App's own JWT. The liveness flag gets its own tests too, because a script that says <em>this route refuses your credential class</em> about a credential that expired an hour ago is confidently wrong.",
"test_py_file": "test_github_endpoint_audience.py",
"test_py": '''from github_endpoint_audience import (
    accepts, canonical, guess, substitute, verdict,
)


def test_a_concrete_path_reduces_to_its_template():
    assert canonical("/repos/acme/api/issues") == "/repos/{owner}/{repo}/issues"
    assert canonical("/users/octocat") == "/users/{username}"


def test_query_strings_fragments_and_slashes_do_not_change_the_route():
    assert canonical("/user/repos?per_page=100") == "/user/repos"
    assert canonical("/user/repos/") == "/user/repos"
    assert canonical("https://api.github.com/user/repos") == "/user/repos"
    assert canonical("user/repos") == "/user/repos"


def test_user_and_users_are_different_routes():
    assert canonical("/user") == "/user"
    assert canonical("/users/octocat") != "/user"


def test_an_unknown_path_is_not_forced_onto_a_template():
    assert canonical("/enterprises/acme/audit-log") is None


def test_the_route_table_answers_only_for_known_routes():
    assert "s2s" not in accepts("/user")
    assert "s2s" in accepts("/repos/{owner}/{repo}/issues")
    assert accepts("/nowhere") is None


def test_the_heuristic_covers_the_user_family_and_declines_the_rest():
    classes, _ = guess("/user/blocks")
    assert classes == {"any", "u2s"}
    classes, reason = guess("/enterprises/acme/audit-log")
    assert classes is None
    assert "not in the table" in reason


def test_the_heuristic_knows_app_routes_want_the_jwt():
    classes, _ = guess("/app/hook/config")
    assert classes == {"jwt"}


def test_a_dead_credential_is_never_reported_as_a_route_problem():
    state, detail = verdict(False, 403, "/user", {"any", "u2s"})
    assert state == "not-an-installation-token"
    assert "not the mismatch" in detail


def test_a_route_that_wants_a_person_names_that_and_not_a_permission():
    state, detail = verdict(True, 403, "/user", accepts("/user"))
    assert state == "needs-user-context"
    assert "no permission opens it" in detail


def test_a_route_that_wants_the_app_jwt_is_its_own_state():
    state, detail = verdict(True, 401, "/app", accepts("/app"))
    assert state == "needs-app-jwt"
    assert "sign a fresh JWT" in detail


def test_a_route_that_does_accept_installation_tokens_is_sent_elsewhere():
    state, detail = verdict(True, 403, "/repos/{owner}/{repo}/hooks",
                            accepts("/repos/{owner}/{repo}/hooks"))
    assert state == "installation-tokens-accepted"
    assert "x-accepted-github-permissions" in detail


def test_a_successful_call_is_not_a_finding():
    assert verdict(True, 200, "/installation/repositories",
                   accepts("/installation/repositories"))[0] == "endpoint-accepted"


def test_an_unknown_route_says_so_rather_than_guessing():
    state, detail = verdict(True, 403, None, None)
    assert state == "route-unknown"
    assert "genuinely unknown" in detail


def test_a_heuristic_answer_is_labelled_as_one():
    _, detail = verdict(True, 403, None, {"any", "u2s"}, guessed=True)
    assert "by heuristic" in detail


def test_substitutes_exist_where_there_is_an_equivalent_and_not_where_there_is_not():
    assert substitute("/user/repos")[0] == "/installation/repositories"
    assert substitute("/gists")[0] is None
    assert substitute("/repos/{owner}/{repo}") is None
''',
"test_js_file": "github-endpoint-audience.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  accepts, canonical, guess, substitute, verdict,
} from './github-endpoint-audience.mjs';

test('a concrete path reduces to its template', () => {
  assert.equal(canonical('/repos/acme/api/issues'), '/repos/{owner}/{repo}/issues');
  assert.equal(canonical('/users/octocat'), '/users/{username}');
});

test('query strings, fragments and slashes do not change the route', () => {
  assert.equal(canonical('/user/repos?per_page=100'), '/user/repos');
  assert.equal(canonical('/user/repos/'), '/user/repos');
  assert.equal(canonical('https://api.github.com/user/repos'), '/user/repos');
  assert.equal(canonical('user/repos'), '/user/repos');
});

test('user and users are different routes', () => {
  assert.equal(canonical('/user'), '/user');
  assert.notEqual(canonical('/users/octocat'), '/user');
});

test('an unknown path is not forced onto a template', () => {
  assert.equal(canonical('/enterprises/acme/audit-log'), null);
});

test('the route table answers only for known routes', () => {
  assert.ok(!accepts('/user').has('s2s'));
  assert.ok(accepts('/repos/{owner}/{repo}/issues').has('s2s'));
  assert.equal(accepts('/nowhere'), null);
});

test('the heuristic covers the user family and declines the rest', () => {
  const [classes] = guess('/user/blocks');
  assert.deepEqual([...classes].sort(), ['any', 'u2s']);
  const [none, reason] = guess('/enterprises/acme/audit-log');
  assert.equal(none, null);
  assert.match(reason, /not in the table/);
});

test('the heuristic knows app routes want the jwt', () => {
  const [classes] = guess('/app/hook/config');
  assert.deepEqual([...classes], ['jwt']);
});

test('a dead credential is never reported as a route problem', () => {
  const [state, detail] = verdict(false, 403, '/user', new Set(['any', 'u2s']));
  assert.equal(state, 'not-an-installation-token');
  assert.match(detail, /not the mismatch/);
});

test('a route that wants a person names that and not a permission', () => {
  const [state, detail] = verdict(true, 403, '/user', accepts('/user'));
  assert.equal(state, 'needs-user-context');
  assert.match(detail, /no permission opens it/);
});

test('a route that wants the app jwt is its own state', () => {
  const [state, detail] = verdict(true, 401, '/app', accepts('/app'));
  assert.equal(state, 'needs-app-jwt');
  assert.match(detail, /sign a fresh JWT/);
});

test('a route that does accept installation tokens is sent elsewhere', () => {
  const route = '/repos/{owner}/{repo}/hooks';
  const [state, detail] = verdict(true, 403, route, accepts(route));
  assert.equal(state, 'installation-tokens-accepted');
  assert.match(detail, /x-accepted-github-permissions/);
});

test('a successful call is not a finding', () => {
  const route = '/installation/repositories';
  assert.equal(verdict(true, 200, route, accepts(route))[0], 'endpoint-accepted');
});

test('an unknown route says so rather than guessing', () => {
  const [state, detail] = verdict(true, 403, null, null);
  assert.equal(state, 'route-unknown');
  assert.match(detail, /genuinely unknown/);
});

test('a heuristic answer is labelled as one', () => {
  const [, detail] = verdict(true, 403, null, new Set(['any', 'u2s']), true);
  assert.match(detail, /by heuristic/);
});

test('substitutes exist where there is an equivalent and not where there is not', () => {
  assert.equal(substitute('/user/repos')[0], '/installation/repositories');
  assert.equal(substitute('/gists')[0], null);
  assert.equal(substitute('/repos/{owner}/{repo}'), null);
});
''',
"faq": [
 ("Is this the same thing as a missing App permission?",
  "No, and the difference is whether a permission could ever help. A missing permission is a 403 on a route that does accept installation tokens, and the response names what it wanted in x-accepted-github-permissions. This is a 403 on a route that does not accept them at all, so that header is absent and there is nothing to add. The quickest discriminator is the header: present means go and diff the App's permissions, absent means the route is refusing the credential class and you need a different endpoint."),
 ("Why does GET /user work for my personal access token but not for the App?",
  "Because a personal access token has a person behind it and an installation access token does not. GET /user is defined as the account the credential belongs to, and an installation belongs to an App on an organization or user account rather than to a human being. There is no answer to return, so the request is refused. If your library calls /user for logging or for a whoami check, point it at GET /app under the App JWT, which returns the App's own id, slug and owner."),
 ("Can I get a token that does work on the user endpoints?",
  "Yes: a user access token, obtained by sending a person through the App's authorization flow so they consent, after which the App can act as them for the routes that need a user. It behaves quite differently from an installation token, since it is bounded by that person's own access as well as by the App's permissions, and it reintroduces a dependency on a specific human. That is worth doing on purpose for something like reading a signed-in user's email address, and worth avoiding for a background job."),
 ("The script says route-unknown. What now?",
  "It means the path is not in the curated table and the first segment carried no rule the script would apply, which happens for the newer and more specialised parts of the API. Nothing about the API reports its own credential-class rules, so there is no way to resolve it programmatically: read the published list of endpoints available for installation access tokens and, if the route is on it, the refusal is a permission after all. Reporting the uncertainty is deliberate, because a confident wrong answer here sends someone to rewrite a working call."),
 ("Does adding every permission to the App eventually make it work?",
  "It cannot, and this is the loop worth breaking. Permissions decide what an installation may do to resources; they do not give the installation a user, and the routes in question are asking for one. An App that keeps requesting broader permissions in pursuit of a route that will never accept it ends up with organization administration it never uses, which is a security finding created entirely by chasing the wrong cause. Stop when the failing response carries no accepted-permissions header."),
],
"related": [
 ("/github/app-permission-missing/", "Resource not accessible by integration"),
 ("/github/installation-repository-selection-partial/", "An installation that covers only some repositories"),
 ("/github/jwt-exp-too-far-future/", "An App JWT rejected on its expiry claim"),
],
"citations": [CITE_APP_INSTALL_AUTH, CITE_APP_ENDPOINTS, CITE_APP_USER_AUTH, CITE_APP_PERMS],
},

{
"slug": "unsupported-api-version",
"title": "A pinned X-GitHub-Api-Version stopped being supported",
"description": "GET /versions lists the versions GitHub still serves. Diff it against the date your client pins and a retirement becomes a calendar entry.",
"h1": "a pinned X-GitHub-Api-Version stopped being supported",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["x-github-api-version unsupported", "github api version 2022-11-28",
             "github rest api versions endpoint", "github api version retired",
             "github api breaking changes version pin"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Nothing was deployed. No token was rotated, no permission changed, no dependency was upgraded. On a Tuesday morning every request to the GitHub API starts coming back refused, with a message about an API version, and the only thing that moved is the date. The header responsible was copied out of a documentation sample in 2022 and has not been looked at since.",
"short_answer": """<p><code>GET /versions</code> returns the list of date-based API versions GitHub currently serves. It needs no token and costs nothing worth counting. Compare the value your client puts in <code>X-GitHub-Api-Version</code> against that list: if it is not on it, the pin is the cause and nothing about your credentials or your code is.</p>
<p>The interesting states are the ones either side of the failure. A pin that is <em>still supported but several versions behind</em> is the same problem before it becomes an incident, and it is the only moment at which you can fix it calmly. A pin that is not a valid date at all is a typo, which behaves differently again. And no pin is not automatically safe: an unpinned client rides GitHub's default, which is itself a version with a lifetime.</p>""",
"problem": """<p>The failure has no author. Every debugging instinct starts from <em>what changed</em>, and the honest answer is nothing: the same container image that worked on Monday fails on Tuesday. So the search goes to the places where things usually change &mdash; credentials, network, GitHub's status page &mdash; and a rotation gets done for no reason, which adds a second variable to an incident that had one.</p>
<p>The message does say what is wrong, and it is still missed, because a whole-integration outage does not look like a header problem. Everything fails at once, including the health check, so it reads like an authentication failure or a service outage. Nobody diffs a request header when the entire client is down; they look for something big, and the cause is eleven characters that nobody has read since they were pasted.</p>
<p>Underneath that is the reason it will happen again: nothing in the running system is watching the list. The version pin is a string in a constant file, the retirement is announced in a changelog, and the two are connected by somebody remembering. The gap between a version leaving the supported list and starting to answer with a refusal is months of warning that goes to an inbox rather than to a monitor.</p>""",
"why": """<p><strong>Versions are dates, and dates retire.</strong> <code>X-GitHub-Api-Version</code> takes a value like <code>2022-11-28</code>. New versions are published when a breaking change lands, old ones are supported for a period and then withdrawn, and a request pinned to a withdrawn one is refused outright rather than quietly upgraded. That refusal is deliberate: silently serving a newer version to a client that asked for an older one would break it in a subtler way.</p>
<p><strong>Sending no header is not the same as being safe.</strong> A request with no version header gets GitHub's current default, which today is <code>2022-11-28</code>. That is a real version with a real lifetime, so an unpinned client is pinned to whatever the server decides and will move under you when the default moves. Neither choice is free; pinning trades a surprise upgrade for a scheduled one.</p>
<p><strong>A refusal keys on the message, not the number.</strong> The status code you get for a bad version is not the interesting part &mdash; reports have it in the 400 family and as a <code>410 Gone</code> depending on the surface &mdash; and treating one particular number as the signature is how a check stops working. The message names the version, so that is what the script matches on.</p>
<p><strong>An invalid version is a different bug from a retired one.</strong> <code>2022-11-38</code> is not a date, and a value that was never a version behaves unlike one that was withdrawn. Both fail, but only one of them has a migration to plan; the other has a typo to fix, and the nearest supported version is almost certainly what was meant.</p>
<p><strong>Moving the pin is not a one-line change.</strong> Every version in between yours and the target exists because something breaking happened, so the repair is to read those notes and then move, rather than to jump to the newest value and find out at runtime. The script names the versions in between for exactly that reason.</p>""",
"steps": [
 {"h": "Find the value your client actually sends",
  "body": """<p>It is a constant somewhere, or a default inside a client library, and the two can disagree. Grep for <code>X-GitHub-Api-Version</code> across the repository and its lockfile-pinned dependencies. If nothing sets it, you are unpinned, which is its own state rather than a clean bill of health.</p>"""},
 {"h": "Ask GitHub what it still serves",
  "body": """<p><code>GET /versions</code> is unauthenticated and answers with a plain list of date strings. That makes this the rare check that can run from anywhere, including a monitoring job with no credential at all &mdash; though anonymous requests share the sixty-per-hour cap, so it is a check to run hourly rather than per request.</p>"""},
 {"h": "Sort the pin into one of five states rather than two",
  "body": """<p>Current, behind, retired, never-a-version, unpinned. Only one of those is an incident, but three of them are worth an alert, and collapsing them into <em>ok</em> and <em>not ok</em> throws away the months of warning that make this problem cheap to fix.</p>"""},
 {"h": "Read the notes for every version in between",
  "body": """<p>Each published version marks a breaking change. Moving from <code>2022-11-28</code> to a version three releases newer means three sets of notes, and the changes are usually small and specific &mdash; a field that stopped being returned, a parameter that became required. Reading them takes an afternoon; discovering them in production takes longer.</p>"""},
 {"h": "Put the comparison in the monitor, not in the incident",
  "body": """<p>The whole point of a public list of supported versions is that this failure is knowable in advance. Run the same script on a schedule and alert on <code>supported-behind</code>, so the version that disappears from the list gives you a ticket rather than an outage.</p>"""},
],
"verify": """<p>Run it with the pin your client uses. A healthy answer names the version and says it is the current one; a warning names the versions you are behind by.</p>
<pre><code class="language-bash">python3 github_api_version_pin.py --pinned 2022-11-28
# supported: 2022-11-28
# supported-current: 2022-11-28 is the newest version GitHub serves.

python3 github_api_version_pin.py --pinned 2021-04-01
# retired: 2021-04-01 is older than every supported version. Requests pinned
# to it are refused.
# repair: move the pin to 2022-11-28, reading the notes for 0 version(s) in
# between first</code></pre>""",
"code_intro": "One unauthenticated GET carries the check, and a second optional one confirms it live against the path that was failing. Everything that decides anything is pure and works on strings: a validator that knows a version is a date, a classifier with five states rather than two, a nearest-neighbour search that turns a typo into a suggestion, and a message matcher that keys on the words GitHub uses rather than on a status code that has been reported as more than one number.",
"py_file": "github_api_version_pin.py",
"py": '''"""Check the X-GitHub-Api-Version your client pins against the versions GitHub serves.

Read only, and mostly unauthenticated: GET /versions needs no credential and
returns the list of date-based REST API versions currently supported. Nothing
here changes a header, a deployment or a pin. The repair is printed.

The point of running this on a schedule rather than during an incident is that
a version leaves the supported list before it starts refusing requests. The
state worth alerting on is "supported but behind", which is the same problem
with months of notice attached.
"""
import argparse
import json
import logging
import os
import re
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_api_version_pin")

API = "https://api.github.com"
UA = "github-api-version-pin/1.0"

# The version a request gets when it carries no X-GitHub-Api-Version header.
# Unpinned is not unversioned: this value has a lifetime like any other.
SERVER_DEFAULT = "2022-11-28"

DATE = re.compile(r"^\\d{4}-\\d{2}-\\d{2}$")

# What a refusal about the version looks like in prose. Matched on words rather
# than on a status code, which has been reported as more than one number and is
# not something a check should depend on.
VERSION_WORDS = re.compile(
    r"api version|x-github-api-version|version.*(not supported|no longer)",
    re.IGNORECASE)


def is_version(value):
    """Whether a string is shaped like an API version. Pure.

    A date shape is necessary and not sufficient: 2022-11-38 passes the regex
    and is not a date, so the day and month are range checked too. A typo that
    looks like a version fails differently from one that does not.
    """
    text = str(value or "").strip()
    if not DATE.match(text):
        return False
    year, month, day = (int(p) for p in text.split("-"))
    return 2000 <= year <= 2999 and 1 <= month <= 12 and 1 <= day <= 31


def supported(body):
    """Parse the GET /versions body into a sorted list of versions. Pure.

    Anything that is not version-shaped is dropped rather than carried, because
    a junk entry that sorts to the end would make every real pin look retired.
    Date strings sort correctly as text, which is the one convenience of this
    format.
    """
    if not isinstance(body, list):
        return []
    return sorted({str(v).strip() for v in body if is_version(v)})


def behind(pin, versions):
    """Supported versions strictly newer than the pin. Pure.

    These are the breaking-change notes to read before moving, so the count
    matters as much as the target.
    """
    return [v for v in versions or [] if v > str(pin or "")]


def nearest(pin, versions):
    """The supported version closest to a pin, for the typo case. Pure.

    Compared as digit strings rather than parsed as dates, which is enough to
    order them and avoids pretending 2022-11-38 is a calendar date in order to
    say it is not one.
    """
    if not versions:
        return None
    target = re.sub(r"\\D", "", str(pin or "")) or "0"
    return min(versions, key=lambda v: (abs(int(re.sub(r"\\D", "", v)) - int(target)), v))


def classify(pin, versions):
    """Sort a pinned value into one of six states. Pure.

    Five of them are about the pin. The sixth is about not being able to judge
    at all, which is a real outcome when GET /versions is what is unreachable.
    """
    if not versions:
        return ("no-versions-list",
                "GET /versions returned nothing version-shaped, so the pin "
                "cannot be judged. That is a failure of the check rather than "
                "a finding about the pin.")

    newest = versions[-1]
    if pin is None or not str(pin).strip():
        state = "unpinned"
        detail = ("no X-GitHub-Api-Version header is sent, so requests get "
                  "GitHub's default of %s. That is a real version with a real "
                  "lifetime: unpinned means pinned by the server, and it moves "
                  "without asking." % SERVER_DEFAULT)
        if SERVER_DEFAULT not in versions:
            detail += (" The default this script knows about is not on the "
                       "served list any more, so check what the current one is.")
        return state, detail

    pin = str(pin).strip()
    if not is_version(pin):
        return ("malformed-pin",
                "%r is not shaped like an API version. It was never valid, so "
                "this is a typo rather than a retirement; the closest served "
                "version is %s." % (pin, nearest(pin, versions)))
    if pin in versions:
        newer = behind(pin, versions)
        if not newer:
            return ("supported-current",
                    "%s is the newest version GitHub serves." % pin)
        return ("supported-behind",
                "%s is still served, and %d newer version(s) exist: %s. This "
                "is the state to alert on, because it is this problem with "
                "notice attached." % (pin, len(newer), ", ".join(newer)))
    if pin < versions[0]:
        return ("retired",
                "%s is older than every supported version. Requests pinned to "
                "it are refused, and the oldest one still served is %s."
                % (pin, versions[0]))
    if pin > newest:
        return ("not-yet-supported",
                "%s is newer than every supported version, so it names a "
                "version that does not exist yet. Almost always a typo; the "
                "closest served version is %s." % (pin, nearest(pin, versions)))
    return ("unknown-version",
            "%s is a valid date and was never a published version. The "
            "closest served version is %s." % (pin, nearest(pin, versions)))


def confirms_version_refusal(status, message):
    """Whether a live response blames the API version. Pure.

    Keyed on the words rather than the status code. A refusal about the version
    is unambiguous in prose and has been reported under more than one number,
    so matching the number is how a check quietly stops working.
    """
    if status is None or status < 400:
        return False
    return bool(VERSION_WORDS.search(str(message or "")))


def get(session, path):
    """One GET. Returns (status, json-or-None)."""
    r = session.get(API + path, timeout=30)
    try:
        body = r.json()
    except ValueError:
        body = None
    return r.status_code, body


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pinned", default=os.environ.get("GITHUB_API_VERSION"),
                    help="the value your client sends in X-GitHub-Api-Version; "
                         "omit it to check the unpinned case")
    ap.add_argument("--path", default="/meta",
                    help="a path to re-send with the pin, to confirm the "
                         "verdict live")
    args = ap.parse_args()

    session = requests.Session()
    session.headers.update({
        "Accept": "application/vnd.github+json",
        "User-Agent": UA,
    })
    # Optional. GET /versions is public; a token only raises the rate limit
    # this check shares with every other anonymous caller on the address.
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        session.headers["Authorization"] = "Bearer " + token

    status, body = get(session, "/versions")
    if status != 200:
        log.error("GET /versions returned %d, so there is no list to compare "
                  "against", status)
        return 2
    versions = supported(body)
    log.info("supported: %s", ", ".join(versions) or "nothing version-shaped")

    state, detail = classify(args.pinned, versions)
    log.info("%s: %s", state, detail)

    # Confirmation, not diagnosis: send the pin at a cheap path and see whether
    # the response blames it.
    if args.pinned:
        session.headers["X-GitHub-Api-Version"] = str(args.pinned)
        live_status, live_body = get(session, args.path)
        message = live_body.get("message") if isinstance(live_body, dict) else None
        log.info("%s with the pin returned %d", args.path, live_status)
        if confirms_version_refusal(live_status, message):
            log.info("confirmed live: the response blames the version")
        elif live_status >= 400:
            log.info("the %d does not mention the version, so it has another "
                     "cause", live_status)

    if state in ("retired", "unknown-version", "not-yet-supported",
                 "malformed-pin"):
        target = versions[-1]
        log.info("repair: move the pin to %s, reading the notes for %d "
                 "version(s) in between first", target,
                 len(behind(args.pinned or "", versions)) - 1
                 if args.pinned else 0)
    if state == "supported-behind":
        log.info("repair: schedule the move to %s; nothing is failing yet, "
                 "which is the only good time to do it", versions[-1])

    print(json.dumps({"pinned": args.pinned, "supported": versions,
                      "behind_by": len(behind(args.pinned or "", versions)),
                      "state": state}, indent=2))
    return 1 if state in ("retired", "unknown-version", "not-yet-supported",
                          "malformed-pin") else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-api-version-pin.mjs",
"js": '''/**
 * Check the X-GitHub-Api-Version your client pins against the versions GitHub serves.
 *
 * Read only, and mostly unauthenticated: GET /versions needs no credential.
 * Nothing here changes a header, a deployment or a pin; the repair is printed.
 *
 * The state worth alerting on is "supported but behind", which is this problem
 * with months of notice attached.
 */
const API = 'https://api.github.com';
const UA = 'github-api-version-pin/1.0';

/** The version a request gets when it sends no header. Not unversioned. */
export const SERVER_DEFAULT = '2022-11-28';

const DATE = /^\\d{4}-\\d{2}-\\d{2}$/;

/** What a refusal about the version looks like in prose, not as a number. */
const VERSION_WORDS = /api version|x-github-api-version|version.*(not supported|no longer)/i;

/** Whether a string is shaped like an API version. Pure. */
export function isVersion(value) {
  const text = String(value ?? '').trim();
  if (!DATE.test(text)) return false;
  const [year, month, day] = text.split('-').map(Number);
  return year >= 2000 && year <= 2999 && month >= 1 && month <= 12 &&
    day >= 1 && day <= 31;
}

/** Parse the GET /versions body into a sorted list of versions. Pure. */
export function supported(body) {
  if (!Array.isArray(body)) return [];
  return [...new Set(body.map((v) => String(v).trim()).filter(isVersion))].sort();
}

/** Supported versions strictly newer than the pin. Pure. */
export function behind(pin, versions) {
  return (versions ?? []).filter((v) => v > String(pin ?? ''));
}

/** The supported version closest to a pin, for the typo case. Pure. */
export function nearest(pin, versions) {
  if (!versions || !versions.length) return null;
  const digits = (v) => Number(String(v ?? '').replace(/\\D/g, '') || '0');
  const target = digits(pin);
  return [...versions].sort((a, b) => (Math.abs(digits(a) - target) -
    Math.abs(digits(b) - target)) || a.localeCompare(b))[0];
}

/** Sort a pinned value into one of six states. Pure. */
export function classify(pin, versions) {
  if (!versions || !versions.length) {
    return ['no-versions-list',
      'GET /versions returned nothing version-shaped, so the pin cannot be ' +
      'judged. That is a failure of the check rather than a finding about the pin.'];
  }

  const newest = versions[versions.length - 1];
  if (pin === null || pin === undefined || !String(pin).trim()) {
    let detail = 'no X-GitHub-Api-Version header is sent, so requests get ' +
      `GitHub's default of ${SERVER_DEFAULT}. That is a real version with a ` +
      'real lifetime: unpinned means pinned by the server, and it moves ' +
      'without asking.';
    if (!versions.includes(SERVER_DEFAULT)) {
      detail += ' The default this script knows about is not on the served ' +
        'list any more, so check what the current one is.';
    }
    return ['unpinned', detail];
  }

  const value = String(pin).trim();
  if (!isVersion(value)) {
    return ['malformed-pin',
      `'${value}' is not shaped like an API version. It was never valid, so ` +
      'this is a typo rather than a retirement; the closest served version ' +
      `is ${nearest(value, versions)}.`];
  }
  if (versions.includes(value)) {
    const newer = behind(value, versions);
    if (!newer.length) {
      return ['supported-current', `${value} is the newest version GitHub serves.`];
    }
    return ['supported-behind',
      `${value} is still served, and ${newer.length} newer version(s) exist: ` +
      `${newer.join(', ')}. This is the state to alert on, because it is this ` +
      'problem with notice attached.'];
  }
  if (value < versions[0]) {
    return ['retired',
      `${value} is older than every supported version. Requests pinned to it ` +
      `are refused, and the oldest one still served is ${versions[0]}.`];
  }
  if (value > newest) {
    return ['not-yet-supported',
      `${value} is newer than every supported version, so it names a version ` +
      'that does not exist yet. Almost always a typo; the closest served ' +
      `version is ${nearest(value, versions)}.`];
  }
  return ['unknown-version',
    `${value} is a valid date and was never a published version. The closest ` +
    `served version is ${nearest(value, versions)}.`];
}

/** Whether a live response blames the API version. Pure. */
export function confirmsVersionRefusal(status, message) {
  if (status === null || status === undefined || status < 400) return false;
  return VERSION_WORDS.test(String(message ?? ''));
}

async function get(path, headers) {
  const res = await fetch(API + path, { headers });
  let body = null;
  try { body = await res.json(); } catch { body = null; }
  return { status: res.status, body };
}

async function main() {
  const pinned = process.argv[2] ?? process.env.GITHUB_API_VERSION ?? null;
  const path = process.argv[3] ?? '/meta';
  const headers = {
    Accept: 'application/vnd.github+json',
    'User-Agent': UA,
  };
  // Optional: a token only raises the rate limit this public check shares
  // with every other anonymous caller on the address.
  if (process.env.GITHUB_TOKEN) {
    headers.Authorization = `Bearer ${process.env.GITHUB_TOKEN}`;
  }

  const list = await get('/versions', headers);
  if (list.status !== 200) {
    console.error(`GET /versions returned ${list.status}, so there is no list ` +
      'to compare against');
    process.exitCode = 2;
    return;
  }
  const versions = supported(list.body);
  console.log(`supported: ${versions.join(', ') || 'nothing version-shaped'}`);

  const [state, detail] = classify(pinned, versions);
  console.log(`${state}: ${detail}`);

  if (pinned) {
    const live = await get(path, { ...headers, 'X-GitHub-Api-Version': String(pinned) });
    const message = live.body && typeof live.body === 'object' ? live.body.message : null;
    console.log(`${path} with the pin returned ${live.status}`);
    if (confirmsVersionRefusal(live.status, message)) {
      console.log('confirmed live: the response blames the version');
    } else if (live.status >= 400) {
      console.log(`the ${live.status} does not mention the version, so it has ` +
        'another cause');
    }
  }

  const broken = ['retired', 'unknown-version', 'not-yet-supported', 'malformed-pin'];
  if (broken.includes(state)) {
    const inBetween = pinned ? Math.max(behind(pinned, versions).length - 1, 0) : 0;
    console.log(`repair: move the pin to ${versions[versions.length - 1]}, ` +
      `reading the notes for ${inBetween} version(s) in between first`);
  }
  if (state === 'supported-behind') {
    console.log(`repair: schedule the move to ${versions[versions.length - 1]}; ` +
      'nothing is failing yet, which is the only good time to do it');
  }

  console.log(JSON.stringify({
    pinned,
    supported: versions,
    behind_by: behind(pinned ?? '', versions).length,
    state,
  }, null, 2));
  process.exitCode = broken.includes(state) ? 1 : 0;
}

// Only run when invoked directly, so importing this module from the test file
// does not execute main() and set an exit code that fails a passing suite.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Every case here is a string against a list, which is the whole argument for keeping the classifier away from the network: a retirement that will happen in eighteen months can be tested today. The ones that earn their place are the near-misses &mdash; a date that was never a version, a date shape that is not a date, and a pin that is supported and still worth an alert &mdash; plus the refusal matcher, which must not key on a status code.",
"test_py_file": "test_github_api_version_pin.py",
"test_py": '''from github_api_version_pin import (
    behind, classify, confirms_version_refusal, is_version, nearest, supported,
)

SERVED = ["2022-11-28", "2024-06-10", "2025-04-01"]


def test_a_version_is_a_real_date_and_not_just_a_date_shape():
    assert is_version("2022-11-28")
    assert not is_version("2022-11-38")
    assert not is_version("2022-13-01")
    assert not is_version("latest")
    assert not is_version(None)


def test_the_versions_body_is_sorted_and_junk_is_dropped():
    assert supported(["2024-06-10", "2022-11-28", "latest", ""]) == [
        "2022-11-28", "2024-06-10"]
    assert supported(None) == []
    assert supported({"versions": []}) == []


def test_being_behind_is_counted_as_the_notes_still_to_read():
    assert behind("2022-11-28", SERVED) == ["2024-06-10", "2025-04-01"]
    assert behind("2025-04-01", SERVED) == []


def test_the_nearest_served_version_is_offered_for_a_typo():
    assert nearest("2024-06-01", SERVED) == "2024-06-10"
    assert nearest("2022-11-38", SERVED) == "2022-11-28"
    assert nearest("2022-11-28", []) is None


def test_the_current_pin_is_the_quiet_state():
    state, detail = classify("2025-04-01", SERVED)
    assert state == "supported-current"
    assert "newest version" in detail


def test_a_supported_but_behind_pin_is_the_one_to_alert_on():
    state, detail = classify("2022-11-28", SERVED)
    assert state == "supported-behind"
    assert "2 newer version(s)" in detail
    assert "notice attached" in detail


def test_a_retired_pin_is_named_as_older_than_everything_served():
    state, detail = classify("2021-04-01", SERVED)
    assert state == "retired"
    assert "2022-11-28" in detail


def test_a_date_that_was_never_a_version_is_its_own_state():
    state, detail = classify("2024-06-11", SERVED)
    assert state == "unknown-version"
    assert "2024-06-10" in detail


def test_a_future_date_is_a_typo_rather_than_a_retirement():
    assert classify("2099-01-01", SERVED)[0] == "not-yet-supported"


def test_a_value_that_is_not_a_date_is_a_typo_and_says_so():
    state, detail = classify("2022-11-38", SERVED)
    assert state == "malformed-pin"
    assert "never valid" in detail


def test_sending_no_header_is_a_state_rather_than_a_pass():
    state, detail = classify(None, SERVED)
    assert state == "unpinned"
    assert "pinned by the server" in detail
    assert classify("", SERVED)[0] == "unpinned"


def test_an_unpinned_client_is_warned_when_the_known_default_is_gone():
    _, detail = classify(None, ["2025-04-01"])
    assert "not on the served list" in detail


def test_an_empty_versions_list_is_a_failure_of_the_check_not_a_finding():
    state, detail = classify("2022-11-28", [])
    assert state == "no-versions-list"
    assert "failure of the check" in detail


def test_a_refusal_is_matched_on_words_and_not_on_a_status_code():
    assert confirms_version_refusal(410, "The API version is no longer supported")
    assert confirms_version_refusal(400, "X-GitHub-Api-Version is not supported")
    assert not confirms_version_refusal(200, "The API version is no longer supported")
    assert not confirms_version_refusal(403, "Resource not accessible by integration")
    assert not confirms_version_refusal(None, None)
''',
"test_js_file": "github-api-version-pin.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  behind, classify, confirmsVersionRefusal, isVersion, nearest, supported,
} from './github-api-version-pin.mjs';

const SERVED = ['2022-11-28', '2024-06-10', '2025-04-01'];

test('a version is a real date and not just a date shape', () => {
  assert.ok(isVersion('2022-11-28'));
  assert.ok(!isVersion('2022-11-38'));
  assert.ok(!isVersion('2022-13-01'));
  assert.ok(!isVersion('latest'));
  assert.ok(!isVersion(null));
});

test('the versions body is sorted and junk is dropped', () => {
  assert.deepEqual(supported(['2024-06-10', '2022-11-28', 'latest', '']),
    ['2022-11-28', '2024-06-10']);
  assert.deepEqual(supported(null), []);
  assert.deepEqual(supported({ versions: [] }), []);
});

test('being behind is counted as the notes still to read', () => {
  assert.deepEqual(behind('2022-11-28', SERVED), ['2024-06-10', '2025-04-01']);
  assert.deepEqual(behind('2025-04-01', SERVED), []);
});

test('the nearest served version is offered for a typo', () => {
  assert.equal(nearest('2024-06-01', SERVED), '2024-06-10');
  assert.equal(nearest('2022-11-38', SERVED), '2022-11-28');
  assert.equal(nearest('2022-11-28', []), null);
});

test('the current pin is the quiet state', () => {
  const [state, detail] = classify('2025-04-01', SERVED);
  assert.equal(state, 'supported-current');
  assert.match(detail, /newest version/);
});

test('a supported but behind pin is the one to alert on', () => {
  const [state, detail] = classify('2022-11-28', SERVED);
  assert.equal(state, 'supported-behind');
  assert.match(detail, /2 newer version\\(s\\)/);
  assert.match(detail, /notice attached/);
});

test('a retired pin is named as older than everything served', () => {
  const [state, detail] = classify('2021-04-01', SERVED);
  assert.equal(state, 'retired');
  assert.match(detail, /2022-11-28/);
});

test('a date that was never a version is its own state', () => {
  const [state, detail] = classify('2024-06-11', SERVED);
  assert.equal(state, 'unknown-version');
  assert.match(detail, /2024-06-10/);
});

test('a future date is a typo rather than a retirement', () => {
  assert.equal(classify('2099-01-01', SERVED)[0], 'not-yet-supported');
});

test('a value that is not a date is a typo and says so', () => {
  const [state, detail] = classify('2022-11-38', SERVED);
  assert.equal(state, 'malformed-pin');
  assert.match(detail, /never valid/);
});

test('sending no header is a state rather than a pass', () => {
  const [state, detail] = classify(null, SERVED);
  assert.equal(state, 'unpinned');
  assert.match(detail, /pinned by the server/);
  assert.equal(classify('', SERVED)[0], 'unpinned');
});

test('an unpinned client is warned when the known default is gone', () => {
  const [, detail] = classify(null, ['2025-04-01']);
  assert.match(detail, /not on the served list/);
});

test('an empty versions list is a failure of the check not a finding', () => {
  const [state, detail] = classify('2022-11-28', []);
  assert.equal(state, 'no-versions-list');
  assert.match(detail, /failure of the check/);
});

test('a refusal is matched on words and not on a status code', () => {
  assert.ok(confirmsVersionRefusal(410, 'The API version is no longer supported'));
  assert.ok(confirmsVersionRefusal(400, 'X-GitHub-Api-Version is not supported'));
  assert.ok(!confirmsVersionRefusal(200, 'The API version is no longer supported'));
  assert.ok(!confirmsVersionRefusal(403, 'Resource not accessible by integration'));
  assert.ok(!confirmsVersionRefusal(null, null));
});
''',
"faq": [
 ("Should I pin a version at all, or leave the header off?",
  "Pin it. Leaving the header off does not opt out of versioning; it opts into whatever GitHub currently defaults to, which today is 2022-11-28 and will one day be something else. An unpinned client therefore gets a breaking change delivered on GitHub's schedule with no signal beforehand, while a pinned one gets a retirement it can see coming on a public list. The cost of pinning is that somebody has to move it, which is exactly the work the scheduled check turns into a ticket."),
 ("How much warning do I get before a version stops working?",
  "Enough to plan, if anything is watching. Versions are announced when they are published and retired after a supported period, and the practical signal is that a version stops appearing in GET /versions. That list is public and unauthenticated, so a daily job comparing your pin against it converts the whole problem into a ticket with a date on it. Waiting for the refusal instead means finding out during an outage, with no useful information in the error beyond the version string you already knew."),
 ("Does the version pin affect GraphQL as well?",
  "No. X-GitHub-Api-Version applies to the REST API only; the GraphQL API is versioned through schema evolution and deprecation notices rather than through date-stamped versions, so a GraphQL client has nothing to pin and nothing to retire. If part of your integration is GraphQL and part is REST, only the REST half is exposed to this, which is worth knowing when half your calls fail and half do not."),
 ("What is actually in a version change?",
  "Something breaking, by definition, which is why a new version exists at all. In practice they are narrow: a response field that stops being returned, a parameter that becomes required, a default that changes, an endpoint whose shape moves. Each published version has its own set of notes, and the reason to read every version between your pin and your target rather than only the target's is that the changes accumulate rather than replace one another."),
 ("My requests fail and the message says nothing about a version. Is this still it?",
  "Probably not. The refusal for a bad version names the version, and a script that keys on a status code alone will mistake an unrelated 4xx for this problem. If everything is failing and the message says Bad credentials, the cause is the credential rather than the header, and that has its own triage: the two 401 messages GitHub uses mean opposite things and are worth telling apart before anything else is touched."),
],
"related": [
 ("/github/bad-credentials-401/", "401 Bad credentials on every endpoint"),
 ("/github/rate-limit-unauthenticated/", "Unauthenticated and capped at 60 an hour"),
 ("/github/installation-token-rejected-by-endpoint/", "A route that refuses a valid installation token"),
],
"citations": [CITE_API_VERSIONS, CITE_BREAKING, CITE_META, CITE_GETTING_STARTED],
},

{
"slug": "wrong-identity-token",
"title": "The automation runs as a person who can leave the company",
"description": "GET /user returns a type and a profile. A type of User behind a background job is a dependency on somebody's employment rather than on your code.",
"h1": "the automation runs as a person who can leave the company",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github service account vs personal access token",
             "github bot identity commits attributed to employee",
             "github app bot login", "machine account github organization",
             "personal access token leaver deprovisioned"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The release notes are signed by someone who left in March. Every automated review comment carries a colleague's avatar, every bot commit says their name, and none of it is a display problem: the token doing the work was minted on their account four years ago, so the integration is not running as a service. It is running as them.",
"short_answer": """<p>Ask the credential who it is, not what it may do. <code>GET /user</code> returns <code>login</code>, <code>type</code> and the rest of a profile, and a <code>type</code> of <code>User</code> with a personal name, a bio and a face on it means your automation is a human being as far as GitHub is concerned. A GitHub App installation answers as <code>type: "Bot"</code> with a login ending in <code>[bot]</code>, which is the shape you want.</p>
<p>This note reads the body and nothing else. Not the scope header, not the expiry header: the question is not how much the credential can do or how long it lasts, but whose access it borrows. The answer decides what happens on the day that person is deprovisioned, and the script names the specific couplings &mdash; attribution, org membership, SSO session, seat &mdash; rather than leaving it at "use a service account".</p>""",
"problem": """<p>Nothing fails, for years. That is what makes it hard: the finding has no error attached and no incident to hang it on, so it lives in the same category as tidying up, and gets the same priority. The first time it becomes urgent is also the first time it is expensive, and by then the person who could explain the credential is the person who left.</p>
<p>The failure mode is a leaver process working correctly. An account is deprovisioned, its tokens die with it, its organization membership is removed, and half a dozen automations that nobody knew were tied to it stop within the hour. They fail with <code>401</code>, which sends everyone looking for a rotated secret, and the actual repair is not a rotation at all &mdash; it is finding a new owner for something that should never have had a personal one.</p>
<p>Before that, there is a quieter cost that is easier to argue with and worth arguing anyway: the history is wrong. A year of automated commits, comments and reviews is attributed to a named individual who did not write any of it, which corrupts blame, review statistics and any audit that asks who changed something. When the automation misbehaves, the name on the change belongs to a person who was on holiday.</p>""",
"why": """<p><strong>A personal access token is the person.</strong> It inherits their organization memberships, their team access, their SSO authorization and their two-factor state. None of that is a property of the automation, and all of it can change without anybody touching the integration &mdash; a team removal, an SSO session expiry, an account suspension.</p>
<p><strong>Type is the honest field.</strong> <code>type</code> is <code>User</code>, <code>Organization</code> or <code>Bot</code>, and a GitHub App installation acting on the API resolves to a <code>Bot</code> login of the form <code>my-app[bot]</code>. That login is what appears on commits and comments, which is why an App fixes the attribution problem as a side effect of fixing the ownership one.</p>
<p><strong>A machine account is a compromise, not a fix.</strong> A dedicated <code>acme-ci</code> login removes the dependency on one employee's employment and keeps every other property of a person: it consumes a seat, it needs two-factor authentication, it needs SSO authorization per organization, and its password lives somewhere. Some organizations forbid them outright. It is better than a colleague's token and it is not the same as an App.</p>
<p><strong>The evidence is circumstantial and should be reported as such.</strong> There is no field that says "this account is a human". What there is instead is a set of signals &mdash; a personal name, a bio, followers, a public email, <code>hireable</code> set &mdash; none of which is proof and all of which together are quite convincing. Naming the signals lets the reader disagree with the verdict, which a bare score does not.</p>
<p><strong>A read-only token can only see itself.</strong> This audit is about the credential it is holding. It cannot enumerate the other tokens on the account, cannot tell you who else holds a copy, and cannot see whether the person is still employed &mdash; only whether the account still answers. The organization list gives you the blast radius; HR gives you the deadline.</p>""",
"steps": [
 {"h": "Ask the credential who it is",
  "body": """<p>One <code>GET /user</code>. Read <code>type</code> first: <code>Bot</code> with a <code>[bot]</code> login and you are done, this note is not about you. <code>User</code> is where the work starts, and the rest of the body is what tells you whether that user is a person or a machine account somebody set up on purpose.</p>"""},
 {"h": "Count the human signals instead of guessing",
  "body": """<p>A personal name in two capitalised words. A bio. A public email. Followers. <code>hireable</code> set to true, which no service account has ever needed. Each is weak alone; three or four together are not. Report them individually so the person reading can point at the one you got wrong.</p>"""},
 {"h": "Ask what the identity is borrowing",
  "body": """<p><code>GET /user/orgs</code> lists the organizations this credential reaches through that account's membership. Every one of them is access that disappears when the membership does, and the list is usually longer than whoever owns the automation expects.</p>"""},
 {"h": "Look at the history the automation has already written",
  "body": """<p>Optionally point the script at a repository and it will count how many of the recent commits are attributed to this login. A number is more persuasive than a principle: four hundred commits signed by a colleague who has never opened the repository is the argument, and it is already in your git history.</p>"""},
 {"h": "Move to an App, and accept what changes",
  "body": """<p>A GitHub App installation is the durable answer: it belongs to the organization, its identity is <code>my-app[bot]</code>, and no leaver process touches it. Two things change on the way. Its tokens expire hourly and must be minted from a JWT, and a handful of endpoints stop working entirely because an installation has no user behind it. Both are known quantities, and both have their own notes.</p>"""},
],
"verify": """<p>Run it again once the App installation is doing the work. The state moves from <code>personal-account</code> to <code>app-installation</code>, and the couplings list becomes empty.</p>
<pre><code class="language-bash">GITHUB_TOKEN=$APP_INSTALLATION_TOKEN python3 github_actor_identity.py
# identity-unreadable: GET /user returned 403, which is what an installation
# access token gets: it has no user behind it. That is the healthy answer here.

GITHUB_TOKEN=$OLD_PAT python3 github_actor_identity.py --repo acme/api
# login=jdoe type=User
# personal-account: 4 human signal(s): a personal name is set; a bio is set;
# hireable is set, which no service account needs; 137 followers
# attribution: 412 of the last 100 commits in acme/api are attributed to jdoe</code></pre>""",
"code_intro": "One GET for the identity, one for the organizations it borrows, and an optional third for the attribution count. Nothing reads a scope header or an expiry header: this script has no opinion about what the credential may do. The classifier is pure and deliberately conservative &mdash; it distinguishes a person from a machine-shaped login from a login that is simply unclassifiable, because reporting a shared <code>ops</code> account as a human being is the kind of wrong answer that gets a whole report ignored. The public email address is counted as a signal and never printed.",
"py_file": "github_actor_identity.py",
"py": '''"""Say whether the credential doing your automation is a person.

Read only. Three GETs at most, all of them reads of things the credential can
already see: its own profile, the organizations it reaches, and optionally the
recent commits of one repository. Nothing is created, renamed or revoked, and
the repair is printed.

This script deliberately reads the response body rather than the response
headers. Scopes and expiry are different questions with different notes; the
question here is whose access this credential borrows, and the answer decides
what happens on somebody's last day.
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_actor_identity")

API = "https://api.github.com"
UA = "github-actor-identity/1.0"

# Login fragments that suggest an account was created for a machine. Matched as
# whole tokens after splitting on separators, so "cindy" is not read as "ci"
# and "abbot" is not read as "bot".
MACHINE_HINTS = {
    "bot", "bots", "ci", "cd", "svc", "service", "serviceaccount", "machine",
    "automation", "deploy", "deployer", "robot", "jenkins", "buildbot",
    "integration", "noreply", "actions", "runner",
}

# What stays coupled to a human being, per verdict. Phrased as the thing that
# happens rather than as the principle, because "use a service account" has
# been said in every one of these code reviews already.
COUPLINGS = {
    "personal-account": [
        "commits, comments and reviews are attributed to this person in the "
        "history, permanently",
        "deprovisioning the account kills every token on it, without warning "
        "and without naming what breaks",
        "removing them from an organization removes the automation's access "
        "to it on the same afternoon",
        "an expired SAML single sign-on session stops the token mid-run",
        "their two-factor changes, device losses and password resets are all "
        "in the failure path",
    ],
    "mixed-signals": [
        "the login is machine shaped and the profile is not, which usually "
        "means a person's account was renamed or a shared login sits on "
        "somebody's mailbox",
        "whoever controls that mailbox controls the credential",
    ],
    "machine-account": [
        "it still consumes a seat and still needs two-factor authentication",
        "it still needs SAML single sign-on authorization per organization",
        "its password and recovery codes live somewhere, and that somewhere "
        "needs an owner who is not one person",
    ],
    "unclassified-user": [
        "the account is a User with nothing that says who owns it, which is "
        "the state that produces an unattributable credential",
    ],
}


def identity(body):
    """Normalise the GET /user body into the fields that matter. Pure.

    Returns None when the body is not a profile at all, which is what an
    installation access token produces: it has no user, so there is nothing to
    read and that is the healthy answer.
    """
    if not isinstance(body, dict) or not body.get("login"):
        return None
    return {
        "login": str(body.get("login")),
        "type": str(body.get("type") or "Unknown"),
        "name": body.get("name") or None,
    }


def looks_like_a_person_name(value):
    """Whether a profile name reads as a personal name. Pure.

    Two or more capitalised alphabetic words. Wrong for mononyms and for a
    great many naming cultures, which is why it is one signal among several
    and never the verdict on its own.
    """
    parts = [p for p in str(value or "").replace(".", " ").split() if p]
    if len(parts) < 2:
        return False
    return all(p[:1].isupper() and p.isalpha() for p in parts)


def machine_shaped(login, declared=()):
    """Whether a login was plainly created for a machine. Pure.

    A declared list from your own inventory wins over the naming heuristic,
    because an organization that calls its machine account "hermes" knows
    something this script cannot.
    """
    name = str(login or "").lower()
    if name in {str(d).lower() for d in declared or ()}:
        return True
    if name.endswith("[bot]"):
        return True
    tokens = set()
    current = ""
    for ch in name:
        if ch.isalnum():
            current += ch
        else:
            tokens.add(current)
            current = ""
    tokens.add(current)
    return bool(tokens & MACHINE_HINTS)


def human_signals(body):
    """Evidence that this account belongs to a person. Pure.

    Each entry is a sentence rather than a score, so a reader can disagree with
    one of them without discarding the report. The email address is counted and
    never quoted: its presence is the signal, its value is somebody's inbox.
    """
    found = []
    if not isinstance(body, dict):
        return found
    if looks_like_a_person_name(body.get("name")):
        found.append("a personal name is set: %s" % body.get("name"))
    if body.get("bio"):
        found.append("a bio is set")
    if body.get("hireable"):
        found.append("hireable is set, which no service account needs")
    if body.get("email"):
        found.append("a public email address is set")
    if body.get("twitter_username"):
        found.append("a social handle is set")
    followers = body.get("followers")
    if isinstance(followers, int) and followers >= 5:
        found.append("%d followers" % followers)
    return found


def classify(ident, signals, machine):
    """Sort a credential's identity into one of six states. Pure."""
    if ident is None:
        return ("identity-unreadable",
                "the credential could not answer GET /user, which is what an "
                "installation access token does: it has no user behind it. "
                "That is the healthy answer to the question this script asks, "
                "and it is also why some endpoints refuse such tokens.")
    if ident["type"] == "Bot" or ident["login"].lower().endswith("[bot]"):
        return ("app-installation",
                "%s is a Bot identity, so the work is done by a GitHub App "
                "installation rather than by a person. Nothing here is "
                "coupled to anyone's employment." % ident["login"])
    if signals and machine:
        return ("mixed-signals",
                "%s is named like a machine account and carries %d human "
                "signal(s): %s. Usually a person's account renamed, or a "
                "shared login on one person's mailbox."
                % (ident["login"], len(signals), "; ".join(signals)))
    if signals:
        return ("personal-account",
                "%s is a %s with %d human signal(s): %s. The automation is "
                "running as a person."
                % (ident["login"], ident["type"], len(signals),
                   "; ".join(signals)))
    if machine:
        return ("machine-account",
                "%s is named like a machine account and carries no human "
                "signals. Better than a colleague's token, and still an "
                "account with a seat, a password and an SSO state."
                % ident["login"])
    return ("unclassified-user",
            "%s is a %s with no human signals and no machine naming, so this "
            "script will not guess. Somebody owns it; find out who before the "
            "question is urgent." % (ident["login"], ident["type"]))


def couplings(state):
    """What remains tied to a human being, given a verdict. Pure."""
    return list(COUPLINGS.get(state, []))


def attributed(commits, login):
    """How many of these commits are attributed to a login. Pure.

    author is null for a commit whose email matches no account, which is common
    and is not the same as being attributed to somebody else, so it is counted
    separately rather than folded into either side.
    """
    total = 0
    mine = 0
    unlinked = 0
    for commit in commits or []:
        if not isinstance(commit, dict):
            continue
        total += 1
        author = commit.get("author")
        if not isinstance(author, dict) or not author.get("login"):
            unlinked += 1
        elif str(author["login"]).lower() == str(login or "").lower():
            mine += 1
    return {"total": total, "attributed": mine, "unlinked": unlinked}


def get(session, path):
    """One GET. Returns (status, json-or-None)."""
    r = session.get(API + path, timeout=30)
    try:
        body = r.json()
    except ValueError:
        body = None
    return r.status_code, body


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", help="OWNER/REPO, to count how much of its "
                                   "recent history this identity signed")
    ap.add_argument("--machine-logins", default="",
                    help="comma-separated logins your inventory already calls "
                         "machine accounts")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_TOKEN to the credential your automation uses. "
                  "An anonymous request has no identity to report")
        return 2
    declared = [d.strip() for d in args.machine_logins.split(",") if d.strip()]

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": UA,
    })

    status, body = get(session, "/user")
    ident = identity(body) if status == 200 else None
    if ident:
        log.info("login=%s type=%s", ident["login"], ident["type"])
    else:
        log.info("GET /user returned %d with no profile in it", status)

    signals = human_signals(body if status == 200 else None)
    machine = machine_shaped(ident["login"], declared) if ident else False
    state, detail = classify(ident, signals, machine)
    log.info("%s: %s", state, detail)

    if ident and state != "app-installation":
        org_status, orgs = get(session, "/user/orgs")
        if org_status == 200 and isinstance(orgs, list):
            names = [o.get("login") for o in orgs if isinstance(o, dict)]
            log.info("this identity reaches %d organization(s) through one "
                     "person's membership: %s", len(names),
                     ", ".join(n for n in names if n) or "none listed")
        else:
            log.info("GET /user/orgs returned %d, so the organizations this "
                     "identity borrows could not be listed", org_status)

    if args.repo and ident:
        commit_status, commits = get(
            session, "/repos/%s/commits?per_page=100" % args.repo)
        if commit_status == 200:
            counts = attributed(commits, ident["login"])
            log.info("attribution: %d of the last %d commits in %s are "
                     "attributed to %s (%d are linked to no account at all)",
                     counts["attributed"], counts["total"], args.repo,
                     ident["login"], counts["unlinked"])
        else:
            log.info("GET commits for %s returned %d", args.repo, commit_status)

    for line in couplings(state):
        log.info("coupled: %s", line)

    if state in ("personal-account", "mixed-signals", "unclassified-user"):
        log.info("repair: install a GitHub App owned by the organization and "
                 "run the automation as its installation. The identity becomes "
                 "my-app[bot] and no leaver process touches it.")
        log.info("repair: if an App is genuinely not possible, create a "
                 "dedicated machine account, document its owner, and put its "
                 "credentials in the team's secret manager rather than on one "
                 "person's laptop.")

    print(json.dumps({"login": ident["login"] if ident else None,
                      "type": ident["type"] if ident else None,
                      "human_signals": signals, "machine_shaped": machine,
                      "state": state}, indent=2))
    return 1 if state in ("personal-account", "mixed-signals") else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-actor-identity.mjs",
"js": '''/**
 * Say whether the credential doing your automation is a person.
 *
 * Read only. Three GETs at most: the credential's own profile, the
 * organizations it reaches, and optionally the recent commits of one
 * repository. Nothing is created, renamed or revoked.
 *
 * This script reads the response body rather than the response headers.
 * Scopes and expiry are different questions; the one here is whose access this
 * credential borrows.
 */
const API = 'https://api.github.com';
const UA = 'github-actor-identity/1.0';

/** Login fragments that suggest a machine, matched as whole tokens. */
export const MACHINE_HINTS = new Set([
  'bot', 'bots', 'ci', 'cd', 'svc', 'service', 'serviceaccount', 'machine',
  'automation', 'deploy', 'deployer', 'robot', 'jenkins', 'buildbot',
  'integration', 'noreply', 'actions', 'runner',
]);

/** What stays coupled to a human being, per verdict. */
export const COUPLINGS = {
  'personal-account': [
    'commits, comments and reviews are attributed to this person in the ' +
    'history, permanently',
    'deprovisioning the account kills every token on it, without warning and ' +
    'without naming what breaks',
    "removing them from an organization removes the automation's access to it " +
    'on the same afternoon',
    'an expired SAML single sign-on session stops the token mid-run',
    'their two-factor changes, device losses and password resets are all in ' +
    'the failure path',
  ],
  'mixed-signals': [
    'the login is machine shaped and the profile is not, which usually means ' +
    "a person's account was renamed or a shared login sits on somebody's mailbox",
    'whoever controls that mailbox controls the credential',
  ],
  'machine-account': [
    'it still consumes a seat and still needs two-factor authentication',
    'it still needs SAML single sign-on authorization per organization',
    'its password and recovery codes live somewhere, and that somewhere needs ' +
    'an owner who is not one person',
  ],
  'unclassified-user': [
    'the account is a User with nothing that says who owns it, which is the ' +
    'state that produces an unattributable credential',
  ],
};

/** Normalise the GET /user body into the fields that matter. Pure. */
export function identity(body) {
  if (!body || typeof body !== 'object' || Array.isArray(body) || !body.login) {
    return null;
  }
  return {
    login: String(body.login),
    type: String(body.type ?? 'Unknown'),
    name: body.name ?? null,
  };
}

/** Whether a profile name reads as a personal name. Pure. */
export function looksLikeAPersonName(value) {
  const parts = String(value ?? '').replace(/\\./g, ' ').split(/\\s+/).filter(Boolean);
  if (parts.length < 2) return false;
  return parts.every((p) => /^[A-Za-z]+$/.test(p) && p[0] === p[0].toUpperCase());
}

/** Whether a login was plainly created for a machine. Pure. */
export function machineShaped(login, declared = []) {
  const name = String(login ?? '').toLowerCase();
  if (declared.map((d) => String(d).toLowerCase()).includes(name)) return true;
  if (name.endsWith('[bot]')) return true;
  const tokens = new Set(name.split(/[^a-z0-9]+/));
  for (const token of tokens) if (MACHINE_HINTS.has(token)) return true;
  return false;
}

/**
 * Evidence that this account belongs to a person. Pure.
 * The email address is counted and never quoted.
 */
export function humanSignals(body) {
  const found = [];
  if (!body || typeof body !== 'object') return found;
  if (looksLikeAPersonName(body.name)) found.push(`a personal name is set: ${body.name}`);
  if (body.bio) found.push('a bio is set');
  if (body.hireable) found.push('hireable is set, which no service account needs');
  if (body.email) found.push('a public email address is set');
  if (body.twitter_username) found.push('a social handle is set');
  if (Number.isInteger(body.followers) && body.followers >= 5) {
    found.push(`${body.followers} followers`);
  }
  return found;
}

/** Sort a credential's identity into one of six states. Pure. */
export function classify(ident, signals, machine) {
  if (!ident) {
    return ['identity-unreadable',
      'the credential could not answer GET /user, which is what an ' +
      'installation access token does: it has no user behind it. That is the ' +
      'healthy answer to the question this script asks, and it is also why ' +
      'some endpoints refuse such tokens.'];
  }
  if (ident.type === 'Bot' || ident.login.toLowerCase().endsWith('[bot]')) {
    return ['app-installation',
      `${ident.login} is a Bot identity, so the work is done by a GitHub App ` +
      'installation rather than by a person. Nothing here is coupled to ' +
      "anyone's employment."];
  }
  if (signals.length && machine) {
    return ['mixed-signals',
      `${ident.login} is named like a machine account and carries ` +
      `${signals.length} human signal(s): ${signals.join('; ')}. Usually a ` +
      "person's account renamed, or a shared login on one person's mailbox."];
  }
  if (signals.length) {
    return ['personal-account',
      `${ident.login} is a ${ident.type} with ${signals.length} human ` +
      `signal(s): ${signals.join('; ')}. The automation is running as a person.`];
  }
  if (machine) {
    return ['machine-account',
      `${ident.login} is named like a machine account and carries no human ` +
      'signals. Better than a colleague\\'s token, and still an account with ' +
      'a seat, a password and an SSO state.'];
  }
  return ['unclassified-user',
    `${ident.login} is a ${ident.type} with no human signals and no machine ` +
    'naming, so this script will not guess. Somebody owns it; find out who ' +
    'before the question is urgent.'];
}

/** What remains tied to a human being, given a verdict. Pure. */
export function couplings(state) {
  return [...(COUPLINGS[state] ?? [])];
}

/** How many of these commits are attributed to a login. Pure. */
export function attributed(commits, login) {
  let total = 0;
  let mine = 0;
  let unlinked = 0;
  for (const commit of commits ?? []) {
    if (!commit || typeof commit !== 'object') continue;
    total += 1;
    const author = commit.author;
    if (!author || typeof author !== 'object' || !author.login) unlinked += 1;
    else if (String(author.login).toLowerCase() === String(login ?? '').toLowerCase()) mine += 1;
  }
  return { total, attributed: mine, unlinked };
}

async function get(token, path) {
  const res = await fetch(API + path, {
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
  const token = process.env.GITHUB_TOKEN;
  if (!token) {
    console.error('set GITHUB_TOKEN to the credential your automation uses. ' +
      'An anonymous request has no identity to report');
    process.exitCode = 2;
    return;
  }
  const repo = process.argv[2] ?? null;
  const declared = (process.env.GITHUB_MACHINE_LOGINS ?? '')
    .split(',').map((d) => d.trim()).filter(Boolean);

  const me = await get(token, '/user');
  const ident = me.status === 200 ? identity(me.body) : null;
  if (ident) console.log(`login=${ident.login} type=${ident.type}`);
  else console.log(`GET /user returned ${me.status} with no profile in it`);

  const signals = humanSignals(me.status === 200 ? me.body : null);
  const machine = ident ? machineShaped(ident.login, declared) : false;
  const [state, detail] = classify(ident, signals, machine);
  console.log(`${state}: ${detail}`);

  if (ident && state !== 'app-installation') {
    const orgs = await get(token, '/user/orgs');
    if (orgs.status === 200 && Array.isArray(orgs.body)) {
      const names = orgs.body.map((o) => o?.login).filter(Boolean);
      console.log(`this identity reaches ${names.length} organization(s) ` +
        `through one person's membership: ${names.join(', ') || 'none listed'}`);
    } else {
      console.log(`GET /user/orgs returned ${orgs.status}, so the ` +
        'organizations this identity borrows could not be listed');
    }
  }

  if (repo && ident) {
    const commits = await get(token, `/repos/${repo}/commits?per_page=100`);
    if (commits.status === 200) {
      const counts = attributed(commits.body, ident.login);
      console.log(`attribution: ${counts.attributed} of the last ` +
        `${counts.total} commits in ${repo} are attributed to ${ident.login} ` +
        `(${counts.unlinked} are linked to no account at all)`);
    } else {
      console.log(`GET commits for ${repo} returned ${commits.status}`);
    }
  }

  for (const line of couplings(state)) console.log(`coupled: ${line}`);

  if (['personal-account', 'mixed-signals', 'unclassified-user'].includes(state)) {
    console.log('repair: install a GitHub App owned by the organization and ' +
      'run the automation as its installation. The identity becomes ' +
      'my-app[bot] and no leaver process touches it.');
    console.log('repair: if an App is genuinely not possible, create a ' +
      "dedicated machine account, document its owner, and put its credentials " +
      "in the team's secret manager rather than on one person's laptop.");
  }

  console.log(JSON.stringify({
    login: ident?.login ?? null,
    type: ident?.type ?? null,
    human_signals: signals,
    machine_shaped: machine,
    state,
  }, null, 2));
  process.exitCode = (state === 'personal-account' || state === 'mixed-signals') ? 1 : 0;
}

// Only run when invoked directly, so importing this module from the test file
// does not execute main() and set an exit code that fails a passing suite.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The awkward cases are the ones a real account will hand you: a machine login on a profile with somebody's face on it, a person whose profile is empty, and an installation token that cannot answer the question at all. Each of those has to come out as a distinct state rather than collapsing into <em>human</em> and <em>not human</em>, so they are the tests. The naming heuristic gets its own, because a login called <code>cindy</code> must not be read as containing <code>ci</code>.",
"test_py_file": "test_github_actor_identity.py",
"test_py": '''from github_actor_identity import (
    attributed, classify, couplings, human_signals, identity,
    looks_like_a_person_name, machine_shaped,
)

PERSON = {"login": "jdoe", "type": "User", "name": "Jane Doe", "bio": "SRE",
          "hireable": True, "followers": 137}
APP = {"login": "acme-deploy[bot]", "type": "Bot", "name": "acme-deploy"}
BARE = {"login": "wj4", "type": "User", "name": None, "followers": 0}


def test_a_profile_reduces_to_login_type_and_name():
    assert identity(PERSON) == {"login": "jdoe", "type": "User",
                                "name": "Jane Doe"}


def test_a_body_with_no_login_is_not_an_identity():
    assert identity(None) is None
    assert identity({"message": "Resource not accessible by integration"}) is None
    assert identity([]) is None


def test_a_personal_name_needs_two_capitalised_words():
    assert looks_like_a_person_name("Jane Doe")
    assert not looks_like_a_person_name("acme-deploy")
    assert not looks_like_a_person_name("Jane")
    assert not looks_like_a_person_name(None)


def test_machine_hints_are_matched_as_tokens_and_not_as_substrings():
    assert machine_shaped("acme-ci")
    assert machine_shaped("deploy_bot")
    assert machine_shaped("acme-deploy[bot]")
    assert not machine_shaped("cindy")
    assert not machine_shaped("abbotsford")


def test_a_declared_machine_login_beats_the_heuristic():
    assert machine_shaped("hermes", declared=["hermes"])
    assert not machine_shaped("hermes")


def test_human_signals_are_named_individually():
    signals = human_signals(PERSON)
    assert any("personal name" in s for s in signals)
    assert any("bio" in s for s in signals)
    assert any("hireable" in s for s in signals)
    assert any("137 followers" in s for s in signals)


def test_an_email_is_counted_and_never_quoted():
    signals = human_signals({"login": "x", "email": "jane@acme.example"})
    assert signals == ["a public email address is set"]


def test_a_quiet_profile_produces_no_signals():
    assert human_signals(BARE) == []
    assert human_signals(None) == []


def test_a_bot_identity_is_the_healthy_answer():
    state, detail = classify(identity(APP), [], True)
    assert state == "app-installation"
    assert "employment" in detail
    assert couplings(state) == []


def test_a_person_behind_the_automation_is_the_finding():
    state, detail = classify(identity(PERSON), human_signals(PERSON), False)
    assert state == "personal-account"
    assert "running as a person" in detail
    assert any("deprovisioning" in c for c in couplings(state))


def test_a_machine_login_with_a_human_profile_is_its_own_state():
    body = dict(PERSON, login="acme-ci")
    state, detail = classify(identity(body), human_signals(body), True)
    assert state == "mixed-signals"
    assert "renamed" in detail


def test_a_clean_machine_account_is_a_compromise_rather_than_a_pass():
    state, detail = classify(identity({"login": "acme-ci", "type": "User"}),
                             [], True)
    assert state == "machine-account"
    assert "still an account with a seat" in detail


def test_an_unreadable_identity_is_reported_as_the_healthy_case():
    state, detail = classify(None, [], False)
    assert state == "identity-unreadable"
    assert "no user behind it" in detail


def test_a_bare_user_account_is_not_guessed_at():
    state, detail = classify(identity(BARE), [], False)
    assert state == "unclassified-user"
    assert "will not guess" in detail


def test_attribution_separates_mine_theirs_and_unlinked():
    commits = [
        {"author": {"login": "jdoe"}},
        {"author": {"login": "JDOE"}},
        {"author": {"login": "someone"}},
        {"author": None},
        {},
    ]
    assert attributed(commits, "jdoe") == {"total": 5, "attributed": 2,
                                           "unlinked": 2}
    assert attributed(None, "jdoe") == {"total": 0, "attributed": 0,
                                        "unlinked": 0}
''',
"test_js_file": "github-actor-identity.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  attributed, classify, couplings, humanSignals, identity,
  looksLikeAPersonName, machineShaped,
} from './github-actor-identity.mjs';

const PERSON = {
  login: 'jdoe', type: 'User', name: 'Jane Doe', bio: 'SRE',
  hireable: true, followers: 137,
};
const APP = { login: 'acme-deploy[bot]', type: 'Bot', name: 'acme-deploy' };
const BARE = { login: 'wj4', type: 'User', name: null, followers: 0 };

test('a profile reduces to login, type and name', () => {
  assert.deepEqual(identity(PERSON), { login: 'jdoe', type: 'User', name: 'Jane Doe' });
});

test('a body with no login is not an identity', () => {
  assert.equal(identity(null), null);
  assert.equal(identity({ message: 'Resource not accessible by integration' }), null);
  assert.equal(identity([]), null);
});

test('a personal name needs two capitalised words', () => {
  assert.ok(looksLikeAPersonName('Jane Doe'));
  assert.ok(!looksLikeAPersonName('acme-deploy'));
  assert.ok(!looksLikeAPersonName('Jane'));
  assert.ok(!looksLikeAPersonName(null));
});

test('machine hints are matched as tokens and not as substrings', () => {
  assert.ok(machineShaped('acme-ci'));
  assert.ok(machineShaped('deploy_bot'));
  assert.ok(machineShaped('acme-deploy[bot]'));
  assert.ok(!machineShaped('cindy'));
  assert.ok(!machineShaped('abbotsford'));
});

test('a declared machine login beats the heuristic', () => {
  assert.ok(machineShaped('hermes', ['hermes']));
  assert.ok(!machineShaped('hermes'));
});

test('human signals are named individually', () => {
  const signals = humanSignals(PERSON);
  assert.ok(signals.some((s) => s.includes('personal name')));
  assert.ok(signals.some((s) => s.includes('bio')));
  assert.ok(signals.some((s) => s.includes('hireable')));
  assert.ok(signals.some((s) => s.includes('137 followers')));
});

test('an email is counted and never quoted', () => {
  const signals = humanSignals({ login: 'x', email: 'jane@acme.example' });
  assert.deepEqual(signals, ['a public email address is set']);
});

test('a quiet profile produces no signals', () => {
  assert.deepEqual(humanSignals(BARE), []);
  assert.deepEqual(humanSignals(null), []);
});

test('a bot identity is the healthy answer', () => {
  const [state, detail] = classify(identity(APP), [], true);
  assert.equal(state, 'app-installation');
  assert.match(detail, /employment/);
  assert.deepEqual(couplings(state), []);
});

test('a person behind the automation is the finding', () => {
  const [state, detail] = classify(identity(PERSON), humanSignals(PERSON), false);
  assert.equal(state, 'personal-account');
  assert.match(detail, /running as a person/);
  assert.ok(couplings(state).some((c) => c.includes('deprovisioning')));
});

test('a machine login with a human profile is its own state', () => {
  const body = { ...PERSON, login: 'acme-ci' };
  const [state, detail] = classify(identity(body), humanSignals(body), true);
  assert.equal(state, 'mixed-signals');
  assert.match(detail, /renamed/);
});

test('a clean machine account is a compromise rather than a pass', () => {
  const [state, detail] = classify(identity({ login: 'acme-ci', type: 'User' }), [], true);
  assert.equal(state, 'machine-account');
  assert.match(detail, /still an account with a seat/);
});

test('an unreadable identity is reported as the healthy case', () => {
  const [state, detail] = classify(null, [], false);
  assert.equal(state, 'identity-unreadable');
  assert.match(detail, /no user behind it/);
});

test('a bare user account is not guessed at', () => {
  const [state, detail] = classify(identity(BARE), [], false);
  assert.equal(state, 'unclassified-user');
  assert.match(detail, /will not guess/);
});

test('attribution separates mine, theirs and unlinked', () => {
  const commits = [
    { author: { login: 'jdoe' } },
    { author: { login: 'JDOE' } },
    { author: { login: 'someone' } },
    { author: null },
    {},
  ];
  assert.deepEqual(attributed(commits, 'jdoe'), { total: 5, attributed: 2, unlinked: 2 });
  assert.deepEqual(attributed(null, 'jdoe'), { total: 0, attributed: 0, unlinked: 0 });
});
''',
"faq": [
 ("Is a dedicated machine account good enough, or do I need an App?",
  "A machine account fixes the worst of it: the automation stops dying when one employee leaves, and the history stops being signed with their name. What it does not fix is that it is still an account. It consumes a licensed seat, it needs two-factor authentication and recovery codes that somebody must hold, it needs SAML authorization in every organization it touches, and some organizations forbid them by policy. An App installation belongs to the organization instead of to a login, which is why it is the durable answer where one is available."),
 ("How do I tell a Bot identity from a person if the login does not say [bot]?",
  "Read type rather than the login. GET /user returns type as User, Organization or Bot, and a GitHub App acting through an installation resolves to Bot. The [bot] suffix is a naming convention that follows from that rather than the thing being tested, so an account that merely calls itself something-bot is still a User and still has all of a user's couplings. The script checks both and treats the type field as the authority."),
 ("What breaks the moment the person is deprovisioned?",
  "Every token on their account stops working at once, so the symptom is a 401 across several unrelated integrations in the same hour. Their organization memberships go, which removes access even for credentials that survive. Anything relying on their SAML session stops at the next expiry rather than immediately, which is worse because it looks intermittent. What does not break is the history: commits and reviews stay attributed to them permanently, since attribution is recorded at the time of the action."),
 ("Can this script tell me whether the person still works here?",
  "No, and it is worth being clear about the limit. A read-only token can see whether the account still answers and which organizations it currently reaches, and that is all. It cannot enumerate other tokens on the account, cannot see when the credential was last used by somebody else, and has no view of employment at all. What it gives you is the list of things that would break, so the deadline can come from a system that does know."),
 ("The script says identity-unreadable. Is that bad?",
  "It is usually the answer you wanted. An installation access token cannot answer GET /user because it has no user behind it, so a credential that fails this particular question is exactly the credential that has no human coupling to report. It does have a consequence worth knowing: the same absence of a user is why a set of endpoints refuse installation tokens outright, whatever permissions the App holds, and that is its own note."),
],
"related": [
 ("/github/over-scoped-token/", "A token that can delete repositories"),
 ("/github/classic-pat-expired/", "A classic PAT that passed its expiry"),
 ("/github/installation-token-rejected-by-endpoint/", "Endpoints that refuse an installation token"),
],
"citations": [CITE_ABOUT_APPS, CITE_USERS, CITE_PATS, CITE_APP_INSTALL_AUTH],
},

{
"slug": "jwt-exp-too-far-future",
"title": "A GitHub App JWT that expires in an hour is refused",
"description": "The exp claim may sit at most ten minutes after iat. Decode the payload of your own JWT and the 401 becomes arithmetic, with no key and no request.",
"h1": "a GitHub App JWT that expires in an hour is refused",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github app jwt exp too far in the future",
             "expiration time claim exp is too far in the future",
             "github app jwt 10 minutes", "github app jwt 401",
             "github app jwt iat exp claims"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The private key is right, the App exists, the signature verifies and the request still comes back <code>401 {\"message\": \"'Expiration time' claim ('exp') is too far in the future\"}</code>. Three people regenerate the key. Somebody rewrites the signing code in a different library. The defect is one number, chosen three lines above the request, and it was wrong before anything was sent.",
"short_answer": """<p>A GitHub App JWT may not live longer than ten minutes. <code>exp</code> must be no more than 600 seconds after <code>iat</code>, and a JWT that asks for an hour &mdash; the comfortable default in every other system you have used &mdash; is refused before any signature or permission is considered.</p>
<p>You do not need GitHub to tell you this. A JWT is three base64url segments and the middle one is JSON, so <code>exp - iat</code> is a subtraction you can do on the machine that produced it, with no key, no network and nothing secret in the output. Set <code>iat</code> to sixty seconds in the past and <code>exp</code> to <code>iat + 540</code>, which leaves headroom on both ends, and mint a fresh JWT per exchange rather than caching one.</p>""",
"problem": """<p>The message is precise and it still sends people to the wrong place, because the word people see is <em>claim</em> and the thing people suspect is the key. A 401 from a credentialled request means the credential, so the key gets regenerated, the PEM gets re-checked for stray newlines, the library gets swapped, and none of that touches a number that the code itself chose.</p>
<p>The ten-minute ceiling is also genuinely surprising. An hour is the habit everywhere else, an hour is what most JWT examples use, and there is nothing about signing a token that suggests the recipient will audit how long you asked for. So the value gets copied from a general-purpose snippet, works nowhere, and looks like a library incompatibility.</p>
<p>Then it hides. A retry loop that mints the same over-long JWT every thirty seconds produces a steady stream of identical 401s that looks like an outage rather than a defect, and if the JWT is minted once at process start and cached, the failure arrives minutes after a deploy that appeared to go fine. Neither shape points at the line that set the number.</p>""",
"why": """<p><strong>Ten minutes is the maximum, not the recommendation.</strong> The JWT authenticates the App itself and exists only to be exchanged for an installation access token. It is a short-lived bearer credential by design, so the ceiling is enforced by the server, and asking for longer is rejected rather than trimmed.</p>
<p><strong>The two claims are yours, so the finding is local.</strong> <code>iat</code> and <code>exp</code> are numbers your signing code wrote into the payload. Reading them back needs no key: verification needs the key, decoding does not. That makes this one of the very few API failures you can prove entirely on your own machine, which is why the script does the arithmetic before it sends anything.</p>
<p><strong>The ceiling is checked before the clock.</strong> A lifetime over 600 seconds is wrong whatever time it is, while <em>expired</em> and <em>issued in the future</em> both depend on a local clock that may itself be the thing that is wrong. Testing the claim-relative fault first means the script does not blame drift for a defect that is present in the payload regardless.</p>
<p><strong>Clock drift is the neighbouring failure, not this one.</strong> If the machine signing the JWT runs a minute fast, <code>iat</code> lands in GitHub's future and the message names <code>iat</code> instead. The repair is different &mdash; backdate <code>iat</code>, and fix the clock &mdash; so the script reports it as its own state rather than folding it in here.</p>
<p><strong>Caching a JWT is what turns this into an intermittent bug.</strong> A JWT held for the life of a process is fine for nine minutes and then is not. Mint one per token exchange; it costs a signature, and the exchange is already the slow part.</p>""",
"steps": [
 {"h": "Take the JWT your own code produced",
  "body": """<p>Not a fresh one from a different code path: the actual value your integration puts in the <code>Authorization</code> header, exported to an environment variable for the length of this check. The whole argument is about what your signing code chose, so a JWT minted by the script would prove nothing about it.</p>"""},
 {"h": "Decode the payload, which needs no key",
  "body": """<p>Split on dots and base64url-decode the middle segment. That is the claims JSON: <code>iss</code>, <code>iat</code>, <code>exp</code>. Verification would need the public key; reading does not, and no part of this requires the private key to be on the machine at all.</p>"""},
 {"h": "Subtract, and compare against 600",
  "body": """<p><code>exp - iat</code> is the requested lifetime in seconds. Over 600 and GitHub refuses it. 3600 is the number to look for first, because an hour is the value that gets copied in from elsewhere, and the script prints exactly how many seconds have to come off.</p>"""},
 {"h": "Check the clock separately, and after",
  "body": """<p><code>iat</code> against the local clock gives the drift. A signing machine running fast puts <code>iat</code> in GitHub's future and produces a different message with a different repair. Reporting the skew as a number rather than a verdict keeps the two apart.</p>"""},
 {"h": "Set iat to now minus sixty and exp to iat plus 540",
  "body": """<p>Backdating <code>iat</code> a minute absorbs modest drift; a 540-second lifetime leaves a minute of headroom under the ceiling. Then mint per exchange rather than caching. Confirm with a single <code>GET /app</code>, which is the cheapest endpoint the JWT can reach, and stop there &mdash; minting an installation token is a write, and nothing on this page writes.</p>"""},
],
"verify": """<p>Re-run against the JWT your fixed signing code produces. The state moves from <code>exp-too-far-future</code> to <code>within-ceiling</code>, and the live confirmation agrees.</p>
<pre><code class="language-bash">GITHUB_APP_JWT=$(python3 sign_app_jwt.py) python3 github_app_jwt_claims.py
# iss=123456 iat=1772000000 exp=1772000540 lifetime=540s skew=-60s
# within-ceiling: the requested lifetime of 540s is inside the 600s ceiling.
# GET /app returned 200
# accepted: the JWT was accepted, so exp and iat are not the problem.</code></pre>""",
"code_intro": "The finding needs no network at all, and that shapes the whole script: decoding, the ceiling arithmetic and the skew are pure functions over a string, and the single GET is confirmation rather than diagnosis. The JWT is read from the environment and never printed, in whole or in part; what the report contains is three claim values and a number of seconds. It stops at <code>GET /app</code> deliberately. Exchanging the JWT for an installation token is a write, and this section does not write.",
"py_file": "github_app_jwt_claims.py",
"py": '''"""Audit the iat and exp claims of a GitHub App JWT before GitHub refuses them.

Read only, and mostly offline. The JWT is read from the environment, decoded
locally, and never printed: the report contains three claim values and a
number of seconds, which is everything needed to name the defect and nothing
that could be replayed.

A GitHub App JWT may live at most ten minutes. Both numbers that decide this
are chosen by your own signing code, and reading them back needs no key at all
- verification needs a key, decoding does not. The one request here is
GET /app, which confirms the local verdict. The script stops there on purpose:
exchanging a JWT for an installation access token is a write, and nothing in
this section writes.
"""
import argparse
import base64
import json
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_app_jwt_claims")

API = "https://api.github.com"
UA = "github-app-jwt-claims/1.0"

# The server-enforced maximum lifetime, and the values worth using instead.
# 540 leaves a minute of headroom under the ceiling; backdating iat by 60
# absorbs modest drift on the signing machine.
CEILING = 600
RECOMMENDED_LIFETIME = 540
RECOMMENDED_BACKDATE = 60

# How far ahead of the local clock iat may sit before it is worth reporting as
# drift rather than as noise.
SKEW_GRACE = 30


def decode_segment(segment):
    """Base64url-decode one JWT segment into a dict. Pure.

    Returns None rather than raising: a malformed JWT is a finding to report,
    not an exception to propagate out of a diagnostic script.
    """
    text = str(segment or "")
    padded = text + "=" * (-len(text) % 4)
    try:
        raw = base64.urlsafe_b64decode(padded.encode("ascii"))
        value = json.loads(raw.decode("utf-8"))
    except Exception:
        return None
    return value if isinstance(value, dict) else None


def claims(jwt):
    """Split a JWT and decode its header and payload. Pure.

    The signature segment is counted, to check the shape, and then discarded
    without being decoded, returned or logged. Nothing downstream needs it and
    a diagnostic tool has no business handling it.
    """
    parts = str(jwt or "").strip().split(".")
    if len(parts) != 3:
        return None, None
    return decode_segment(parts[0]), decode_segment(parts[1])


def lifetime(payload):
    """The requested lifetime in seconds, or None if it cannot be computed. Pure."""
    if not isinstance(payload, dict):
        return None
    iat, exp = payload.get("iat"), payload.get("exp")
    if not isinstance(iat, (int, float)) or not isinstance(exp, (int, float)):
        return None
    if isinstance(iat, bool) or isinstance(exp, bool):
        return None
    return int(exp) - int(iat)


def skew(payload, now):
    """How far iat sits from the local clock, in seconds. Pure.

    Negative means the JWT was backdated, which is what you want. Positive
    means the signing clock is ahead of this one.
    """
    if not isinstance(payload, dict):
        return None
    iat = payload.get("iat")
    if not isinstance(iat, (int, float)) or isinstance(iat, bool):
        return None
    return int(iat) - int(now)


def audit(payload, now):
    """Turn a decoded payload and a clock reading into a finding. Pure.

    Order matters. The ceiling is checked before anything clock-relative,
    because a lifetime over 600 seconds is wrong whatever time it is, while
    "expired" and "issued in the future" both depend on a local clock that may
    itself be the defect. Testing the claim-relative fault first stops the
    script blaming drift for a payload that is wrong regardless.
    """
    if not isinstance(payload, dict):
        return ("unreadable",
                "the middle segment did not decode to a JSON object, so this "
                "is not a well-formed JWT. Check what the signing code "
                "returned before looking at any claim.")
    if "iat" not in payload:
        return ("no-iat",
                "there is no iat claim. GitHub measures the lifetime from it, "
                "so a JWT without one cannot be judged against the ten minute "
                "ceiling and is refused.")
    if "exp" not in payload:
        return ("no-exp",
                "there is no exp claim, so the JWT never expires as far as the "
                "payload is concerned. That is exactly what the ceiling exists "
                "to prevent, and it is refused.")

    span = lifetime(payload)
    if span is None:
        return ("non-numeric-claim",
                "iat and exp must be numeric seconds since the epoch. One of "
                "them is not a number, which usually means a date string or a "
                "millisecond timestamp went in where seconds were expected.")
    if span <= 0:
        return ("exp-not-after-iat",
                "exp is %d second(s) before iat, so the JWT is expired at the "
                "moment it is signed." % -span)
    if span > CEILING:
        return ("exp-too-far-future",
                "the requested lifetime is %ds, which is %ds over the %ds "
                "ceiling. Remove %ds from exp and the claim is legal."
                % (span, span - CEILING, CEILING, span - RECOMMENDED_LIFETIME))

    drift = skew(payload, now)
    exp = int(payload["exp"])
    if exp <= int(now):
        return ("already-expired",
                "the lifetime is legal at %ds, and this JWT expired %ds ago. "
                "A JWT minted once and cached for the life of a process fails "
                "exactly like this, minutes after a deploy that looked fine."
                % (span, int(now) - exp))
    if drift is not None and drift > SKEW_GRACE:
        return ("iat-in-the-future",
                "the lifetime is legal at %ds, and iat is %ds ahead of this "
                "clock. If the signing machine is ahead of GitHub, iat lands "
                "in its future and the message names iat rather than exp. "
                "That is a different repair: backdate iat and fix the clock."
                % (span, drift))
    if exp - int(now) < 30:
        return ("expiring-imminently",
                "the lifetime is legal at %ds and only %ds of it remain, which "
                "is not enough to survive a retry. Mint per exchange rather "
                "than caching." % (span, exp - int(now)))
    return ("within-ceiling",
            "the requested lifetime of %ds is inside the %ds ceiling."
            % (span, CEILING))


def recommend(payload, now):
    """The claim values that would have worked. Pure."""
    iat = int(now) - RECOMMENDED_BACKDATE
    span = lifetime(payload)
    return {"iat": iat, "exp": iat + RECOMMENDED_LIFETIME,
            "lifetime": RECOMMENDED_LIFETIME,
            "seconds_to_remove": max((span or 0) - RECOMMENDED_LIFETIME, 0)}


def interpret(status, message):
    """Map a live GET /app response to the defect it names. Pure.

    GitHub's messages about these claims are specific and stable, and each one
    points at a different line of the signing code. Matched on the distinctive
    phrase rather than on the whole sentence.
    """
    if status == 200:
        return ("accepted",
                "the JWT was accepted, so exp and iat are not the problem.")
    text = str(message or "").lower()
    if "too far in the future" in text:
        return ("exp-too-far-future",
                "GitHub says exp is too far ahead of iat, which is the ceiling.")
    if "issued at" in text or "'iat'" in text:
        return ("iat-in-the-future",
                "GitHub says iat is in its future, which is clock drift on the "
                "signing machine rather than a lifetime problem.")
    if "numeric value representing the future" in text or "expired" in text:
        return ("already-expired",
                "GitHub says exp is not in the future, so this JWT was minted "
                "too long ago or the clock is behind.")
    if "could not be decoded" in text:
        return ("undecodable",
                "GitHub could not decode the JWT at all, which is a signing or "
                "encoding fault rather than a claim one.")
    if "integration not found" in text:
        return ("wrong-app-or-key",
                "the claims are acceptable and the App they name cannot be "
                "found, so iss or the signing key belongs to something else.")
    return ("unrelated",
            "the response does not mention a claim, so this failure has "
            "another cause.")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--offline", action="store_true",
                    help="skip the confirming GET /app and report the local "
                         "arithmetic only")
    args = ap.parse_args()

    jwt = os.environ.get("GITHUB_APP_JWT")
    if not jwt:
        log.error("set GITHUB_APP_JWT to the JWT your own signing code "
                  "produces. A JWT minted by this script would prove nothing "
                  "about yours")
        return 2

    now = time.time()
    header, payload = claims(jwt)
    if payload is None:
        log.error("the JWT did not decode into three segments with a JSON "
                  "payload in the middle")
        state, detail = audit(None, now)
        log.info("%s: %s", state, detail)
        return 1

    # Claim values only. The signature is never decoded and the JWT is never
    # printed, in whole or in part.
    log.info("iss=%s iat=%s exp=%s lifetime=%ss skew=%ss",
             payload.get("iss", "absent"), payload.get("iat", "absent"),
             payload.get("exp", "absent"),
             lifetime(payload) if lifetime(payload) is not None else "unknown",
             skew(payload, now) if skew(payload, now) is not None else "unknown")
    if isinstance(header, dict) and header.get("alg") not in (None, "RS256"):
        log.info("note: alg is %s rather than RS256, which is a different "
                 "defect from this one", header.get("alg"))

    state, detail = audit(payload, now)
    log.info("%s: %s", state, detail)

    if not args.offline:
        r = requests.get(API + "/app", timeout=30, headers={
            "Authorization": "Bearer " + jwt,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": UA,
        })
        try:
            body = r.json()
        except ValueError:
            body = None
        message = body.get("message") if isinstance(body, dict) else None
        log.info("GET /app returned %d", r.status_code)
        live_state, live_detail = interpret(r.status_code, message)
        log.info("%s: %s", live_state, live_detail)

    if state in ("exp-too-far-future", "no-exp", "no-iat", "exp-not-after-iat",
                 "non-numeric-claim", "already-expired", "expiring-imminently"):
        want = recommend(payload, now)
        log.info("repair: set iat=%d (now minus %ds) and exp=%d (iat plus "
                 "%ds), then mint a fresh JWT per token exchange rather than "
                 "caching one", want["iat"], RECOMMENDED_BACKDATE, want["exp"],
                 want["lifetime"])
        if want["seconds_to_remove"]:
            log.info("repair: that is %d second(s) off the current exp",
                     want["seconds_to_remove"])

    print(json.dumps({"iss": payload.get("iss"), "iat": payload.get("iat"),
                      "exp": payload.get("exp"), "lifetime": lifetime(payload),
                      "skew_seconds": skew(payload, now), "state": state},
                     indent=2))
    return 0 if state == "within-ceiling" else 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-app-jwt-claims.mjs",
"js": '''/**
 * Audit the iat and exp claims of a GitHub App JWT before GitHub refuses them.
 *
 * Read only, and mostly offline. The JWT is read from the environment,
 * decoded locally, and never printed: the report contains three claim values
 * and a number of seconds.
 *
 * Decoding needs no key; verification would. The single request is GET /app,
 * which confirms the local verdict. The script stops there on purpose:
 * exchanging a JWT for an installation access token is a write, and nothing
 * in this section writes.
 */
const API = 'https://api.github.com';
const UA = 'github-app-jwt-claims/1.0';

/** The server-enforced maximum lifetime, and the values worth using instead. */
export const CEILING = 600;
export const RECOMMENDED_LIFETIME = 540;
export const RECOMMENDED_BACKDATE = 60;

/** How far ahead of the local clock iat may sit before it is worth reporting. */
export const SKEW_GRACE = 30;

/** Base64url-decode one JWT segment into an object. Pure. null on anything odd. */
export function decodeSegment(segment) {
  try {
    const raw = Buffer.from(String(segment ?? ''), 'base64url').toString('utf8');
    const value = JSON.parse(raw);
    return (value && typeof value === 'object' && !Array.isArray(value)) ? value : null;
  } catch {
    return null;
  }
}

/**
 * Split a JWT and decode its header and payload. Pure.
 * The signature segment is counted and then discarded without being decoded,
 * returned or logged.
 */
export function claims(jwt) {
  const parts = String(jwt ?? '').trim().split('.');
  if (parts.length !== 3) return [null, null];
  return [decodeSegment(parts[0]), decodeSegment(parts[1])];
}

const numeric = (v) => typeof v === 'number' && Number.isFinite(v);

/** The requested lifetime in seconds, or null. Pure. */
export function lifetime(payload) {
  if (!payload || typeof payload !== 'object') return null;
  if (!numeric(payload.iat) || !numeric(payload.exp)) return null;
  return Math.trunc(payload.exp) - Math.trunc(payload.iat);
}

/** How far iat sits from the local clock, in seconds. Negative is backdated. Pure. */
export function skew(payload, now) {
  if (!payload || typeof payload !== 'object' || !numeric(payload.iat)) return null;
  return Math.trunc(payload.iat) - Math.trunc(now);
}

/**
 * Turn a decoded payload and a clock reading into a finding. Pure.
 * The ceiling is checked before anything clock-relative, because a lifetime
 * over 600 seconds is wrong whatever time it is.
 */
export function audit(payload, now) {
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)) {
    return ['unreadable',
      'the middle segment did not decode to a JSON object, so this is not a ' +
      'well-formed JWT. Check what the signing code returned before looking ' +
      'at any claim.'];
  }
  if (!('iat' in payload)) {
    return ['no-iat',
      'there is no iat claim. GitHub measures the lifetime from it, so a JWT ' +
      'without one cannot be judged against the ten minute ceiling and is refused.'];
  }
  if (!('exp' in payload)) {
    return ['no-exp',
      'there is no exp claim, so the JWT never expires as far as the payload ' +
      'is concerned. That is exactly what the ceiling exists to prevent, and ' +
      'it is refused.'];
  }

  const span = lifetime(payload);
  if (span === null) {
    return ['non-numeric-claim',
      'iat and exp must be numeric seconds since the epoch. One of them is ' +
      'not a number, which usually means a date string or a millisecond ' +
      'timestamp went in where seconds were expected.'];
  }
  if (span <= 0) {
    return ['exp-not-after-iat',
      `exp is ${-span} second(s) before iat, so the JWT is expired at the ` +
      'moment it is signed.'];
  }
  if (span > CEILING) {
    return ['exp-too-far-future',
      `the requested lifetime is ${span}s, which is ${span - CEILING}s over ` +
      `the ${CEILING}s ceiling. Remove ${span - RECOMMENDED_LIFETIME}s from ` +
      'exp and the claim is legal.'];
  }

  const drift = skew(payload, now);
  const exp = Math.trunc(payload.exp);
  if (exp <= Math.trunc(now)) {
    return ['already-expired',
      `the lifetime is legal at ${span}s, and this JWT expired ` +
      `${Math.trunc(now) - exp}s ago. A JWT minted once and cached for the ` +
      'life of a process fails exactly like this, minutes after a deploy that ' +
      'looked fine.'];
  }
  if (drift !== null && drift > SKEW_GRACE) {
    return ['iat-in-the-future',
      `the lifetime is legal at ${span}s, and iat is ${drift}s ahead of this ` +
      'clock. If the signing machine is ahead of GitHub, iat lands in its ' +
      'future and the message names iat rather than exp. That is a different ' +
      'repair: backdate iat and fix the clock.'];
  }
  if (exp - Math.trunc(now) < 30) {
    return ['expiring-imminently',
      `the lifetime is legal at ${span}s and only ${exp - Math.trunc(now)}s of ` +
      'it remain, which is not enough to survive a retry. Mint per exchange ' +
      'rather than caching.'];
  }
  return ['within-ceiling',
    `the requested lifetime of ${span}s is inside the ${CEILING}s ceiling.`];
}

/** The claim values that would have worked. Pure. */
export function recommend(payload, now) {
  const iat = Math.trunc(now) - RECOMMENDED_BACKDATE;
  const span = lifetime(payload);
  return {
    iat,
    exp: iat + RECOMMENDED_LIFETIME,
    lifetime: RECOMMENDED_LIFETIME,
    seconds_to_remove: Math.max((span ?? 0) - RECOMMENDED_LIFETIME, 0),
  };
}

/** Map a live GET /app response to the defect it names. Pure. */
export function interpret(status, message) {
  if (status === 200) {
    return ['accepted', 'the JWT was accepted, so exp and iat are not the problem.'];
  }
  const text = String(message ?? '').toLowerCase();
  if (text.includes('too far in the future')) {
    return ['exp-too-far-future',
      'GitHub says exp is too far ahead of iat, which is the ceiling.'];
  }
  if (text.includes('issued at') || text.includes("'iat'")) {
    return ['iat-in-the-future',
      'GitHub says iat is in its future, which is clock drift on the signing ' +
      'machine rather than a lifetime problem.'];
  }
  if (text.includes('numeric value representing the future') || text.includes('expired')) {
    return ['already-expired',
      'GitHub says exp is not in the future, so this JWT was minted too long ' +
      'ago or the clock is behind.'];
  }
  if (text.includes('could not be decoded')) {
    return ['undecodable',
      'GitHub could not decode the JWT at all, which is a signing or encoding ' +
      'fault rather than a claim one.'];
  }
  if (text.includes('integration not found')) {
    return ['wrong-app-or-key',
      'the claims are acceptable and the App they name cannot be found, so ' +
      'iss or the signing key belongs to something else.'];
  }
  return ['unrelated',
    'the response does not mention a claim, so this failure has another cause.'];
}

async function main() {
  const jwt = process.env.GITHUB_APP_JWT;
  if (!jwt) {
    console.error('set GITHUB_APP_JWT to the JWT your own signing code ' +
      'produces. A JWT minted by this script would prove nothing about yours');
    process.exitCode = 2;
    return;
  }
  const offline = process.argv.includes('--offline');
  const now = Date.now() / 1000;
  const [header, payload] = claims(jwt);
  if (!payload) {
    console.error('the JWT did not decode into three segments with a JSON ' +
      'payload in the middle');
    const [state, detail] = audit(null, now);
    console.log(`${state}: ${detail}`);
    process.exitCode = 1;
    return;
  }

  // Claim values only. The signature is never decoded and the JWT is never
  // printed, in whole or in part.
  console.log(`iss=${payload.iss ?? 'absent'} iat=${payload.iat ?? 'absent'} ` +
    `exp=${payload.exp ?? 'absent'} lifetime=${lifetime(payload) ?? 'unknown'}s ` +
    `skew=${skew(payload, now) ?? 'unknown'}s`);
  if (header && header.alg && header.alg !== 'RS256') {
    console.log(`note: alg is ${header.alg} rather than RS256, which is a ` +
      'different defect from this one');
  }

  const [state, detail] = audit(payload, now);
  console.log(`${state}: ${detail}`);

  if (!offline) {
    const res = await fetch(`${API}/app`, {
      headers: {
        Authorization: `Bearer ${jwt}`,
        Accept: 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
        'User-Agent': UA,
      },
    });
    let body = null;
    try { body = await res.json(); } catch { body = null; }
    const message = body && typeof body === 'object' ? body.message : null;
    console.log(`GET /app returned ${res.status}`);
    const [liveState, liveDetail] = interpret(res.status, message);
    console.log(`${liveState}: ${liveDetail}`);
  }

  const broken = ['exp-too-far-future', 'no-exp', 'no-iat', 'exp-not-after-iat',
    'non-numeric-claim', 'already-expired', 'expiring-imminently'];
  if (broken.includes(state)) {
    const want = recommend(payload, now);
    console.log(`repair: set iat=${want.iat} (now minus ${RECOMMENDED_BACKDATE}s) ` +
      `and exp=${want.exp} (iat plus ${want.lifetime}s), then mint a fresh JWT ` +
      'per token exchange rather than caching one');
    if (want.seconds_to_remove) {
      console.log(`repair: that is ${want.seconds_to_remove} second(s) off the ` +
        'current exp');
    }
  }

  console.log(JSON.stringify({
    iss: payload.iss ?? null,
    iat: payload.iat ?? null,
    exp: payload.exp ?? null,
    lifetime: lifetime(payload),
    skew_seconds: skew(payload, now),
    state,
  }, null, 2));
  process.exitCode = state === 'within-ceiling' ? 0 : 1;
}

// Only run when invoked directly, so importing this module from the test file
// does not execute main() and set an exit code that fails a passing suite.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Every JWT in these tests is assembled from claims by a three-line helper, with the literal <code>sig</code> where a signature would be: obviously fake, and short enough that nobody will ever mistake it for a credential. That is the whole benefit of a check that needs no key &mdash; an hour-long lifetime, a clock a minute fast and a token that expired yesterday are all three lines each, and the ordering rule (the ceiling before the clock) gets a test of its own.",
"test_py_file": "test_github_app_jwt_claims.py",
"test_py": '''import base64
import json

from github_app_jwt_claims import (
    CEILING, audit, claims, decode_segment, interpret, lifetime, recommend, skew,
)

NOW = 1_772_000_000


def seg(value):
    raw = base64.urlsafe_b64encode(json.dumps(value).encode()).decode()
    return raw.rstrip("=")


def token(payload, header=None):
    """An obviously fake JWT: real claims, and the word sig for a signature."""
    return "%s.%s.sig" % (seg(header or {"alg": "RS256", "typ": "JWT"}),
                          seg(payload))


def test_a_segment_decodes_without_any_key():
    assert decode_segment(seg({"iss": "123456"})) == {"iss": "123456"}
    assert decode_segment("not base64 at all!!") is None
    assert decode_segment(seg([1, 2])) is None


def test_a_jwt_splits_into_a_header_and_a_payload():
    header, payload = claims(token({"iat": NOW, "exp": NOW + 540}))
    assert header["alg"] == "RS256"
    assert payload["exp"] - payload["iat"] == 540


def test_something_that_is_not_three_segments_decodes_to_nothing():
    assert claims("abc.def") == (None, None)
    assert claims("") == (None, None)
    assert claims(None) == (None, None)


def test_lifetime_and_skew_are_plain_arithmetic():
    payload = {"iat": NOW - 60, "exp": NOW + 480}
    assert lifetime(payload) == 540
    assert skew(payload, NOW) == -60
    assert lifetime({"iat": "2026-01-01", "exp": NOW}) is None
    assert skew({}, NOW) is None


def test_an_hour_long_jwt_is_the_headline_finding():
    state, detail = audit({"iat": NOW, "exp": NOW + 3600}, NOW)
    assert state == "exp-too-far-future"
    assert "3600s" in detail
    assert "3000s over" in detail


def test_the_ceiling_is_checked_before_the_clock():
    # Both faults present: an hour-long lifetime signed by a clock ten minutes
    # fast. The payload fault wins, because it is true whatever the time is.
    state, _ = audit({"iat": NOW + 600, "exp": NOW + 600 + 3600}, NOW)
    assert state == "exp-too-far-future"


def test_exactly_the_ceiling_is_still_legal():
    assert audit({"iat": NOW, "exp": NOW + CEILING}, NOW)[0] == "within-ceiling"
    assert audit({"iat": NOW, "exp": NOW + CEILING + 1}, NOW)[0] == "exp-too-far-future"


def test_a_missing_claim_is_named_rather_than_computed_around():
    assert audit({"exp": NOW + 300}, NOW)[0] == "no-iat"
    assert audit({"iat": NOW}, NOW)[0] == "no-exp"


def test_milliseconds_where_seconds_were_expected_are_caught():
    state, detail = audit({"iat": "1772000000", "exp": "1772000540"}, NOW)
    assert state == "non-numeric-claim"
    assert "millisecond" in detail


def test_exp_before_iat_is_its_own_state():
    state, detail = audit({"iat": NOW, "exp": NOW - 10}, NOW)
    assert state == "exp-not-after-iat"
    assert "10 second(s) before" in detail


def test_a_cached_jwt_that_ran_out_is_told_apart_from_a_long_one():
    state, detail = audit({"iat": NOW - 900, "exp": NOW - 360}, NOW)
    assert state == "already-expired"
    assert "cached" in detail


def test_a_fast_signing_clock_is_reported_as_drift_and_not_as_the_ceiling():
    state, detail = audit({"iat": NOW + 300, "exp": NOW + 540}, NOW)
    assert state == "iat-in-the-future"
    assert "different repair" in detail


def test_a_jwt_about_to_expire_is_flagged_before_it_does():
    assert audit({"iat": NOW - 580, "exp": NOW + 20}, NOW)[0] == "expiring-imminently"


def test_a_healthy_jwt_says_so_without_qualification():
    state, detail = audit({"iat": NOW - 60, "exp": NOW + 480}, NOW)
    assert state == "within-ceiling"
    assert "540s" in detail


def test_the_recommendation_is_a_pair_of_numbers_to_paste():
    want = recommend({"iat": NOW, "exp": NOW + 3600}, NOW)
    assert want["iat"] == NOW - 60
    assert want["exp"] == NOW + 480
    assert want["seconds_to_remove"] == 3060


def test_the_live_messages_map_to_the_same_states_as_the_local_check():
    assert interpret(200, None)[0] == "accepted"
    assert interpret(401, "'Expiration time' claim ('exp') is too far in the "
                          "future")[0] == "exp-too-far-future"
    assert interpret(401, "'Issued at' claim ('iat') is in the "
                          "future")[0] == "iat-in-the-future"
    assert interpret(401, "'Expiration time' claim ('exp') must be a numeric "
                          "value representing the future time"
                     )[0] == "already-expired"
    assert interpret(401, "A JSON web token could not be "
                          "decoded")[0] == "undecodable"
    assert interpret(404, "Integration not found")[0] == "wrong-app-or-key"
    assert interpret(403, "Resource not accessible by integration")[0] == "unrelated"
''',
"test_js_file": "github-app-jwt-claims.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  CEILING, audit, claims, decodeSegment, interpret, lifetime, recommend, skew,
} from './github-app-jwt-claims.mjs';

const NOW = 1772000000;

const seg = (value) => Buffer.from(JSON.stringify(value)).toString('base64url');

/** An obviously fake JWT: real claims, and the word sig for a signature. */
const token = (payload, header = { alg: 'RS256', typ: 'JWT' }) =>
  `${seg(header)}.${seg(payload)}.sig`;

test('a segment decodes without any key', () => {
  assert.deepEqual(decodeSegment(seg({ iss: '123456' })), { iss: '123456' });
  assert.equal(decodeSegment('%%%'), null);
  assert.equal(decodeSegment(seg([1, 2])), null);
});

test('a jwt splits into a header and a payload', () => {
  const [header, payload] = claims(token({ iat: NOW, exp: NOW + 540 }));
  assert.equal(header.alg, 'RS256');
  assert.equal(payload.exp - payload.iat, 540);
});

test('something that is not three segments decodes to nothing', () => {
  assert.deepEqual(claims('abc.def'), [null, null]);
  assert.deepEqual(claims(''), [null, null]);
  assert.deepEqual(claims(null), [null, null]);
});

test('lifetime and skew are plain arithmetic', () => {
  const payload = { iat: NOW - 60, exp: NOW + 480 };
  assert.equal(lifetime(payload), 540);
  assert.equal(skew(payload, NOW), -60);
  assert.equal(lifetime({ iat: '2026-01-01', exp: NOW }), null);
  assert.equal(skew({}, NOW), null);
});

test('an hour long jwt is the headline finding', () => {
  const [state, detail] = audit({ iat: NOW, exp: NOW + 3600 }, NOW);
  assert.equal(state, 'exp-too-far-future');
  assert.match(detail, /3600s/);
  assert.match(detail, /3000s over/);
});

test('the ceiling is checked before the clock', () => {
  const [state] = audit({ iat: NOW + 600, exp: NOW + 600 + 3600 }, NOW);
  assert.equal(state, 'exp-too-far-future');
});

test('exactly the ceiling is still legal', () => {
  assert.equal(audit({ iat: NOW, exp: NOW + CEILING }, NOW)[0], 'within-ceiling');
  assert.equal(audit({ iat: NOW, exp: NOW + CEILING + 1 }, NOW)[0], 'exp-too-far-future');
});

test('a missing claim is named rather than computed around', () => {
  assert.equal(audit({ exp: NOW + 300 }, NOW)[0], 'no-iat');
  assert.equal(audit({ iat: NOW }, NOW)[0], 'no-exp');
});

test('milliseconds where seconds were expected are caught', () => {
  const [state, detail] = audit({ iat: '1772000000', exp: '1772000540' }, NOW);
  assert.equal(state, 'non-numeric-claim');
  assert.match(detail, /millisecond/);
});

test('exp before iat is its own state', () => {
  const [state, detail] = audit({ iat: NOW, exp: NOW - 10 }, NOW);
  assert.equal(state, 'exp-not-after-iat');
  assert.match(detail, /10 second\\(s\\) before/);
});

test('a cached jwt that ran out is told apart from a long one', () => {
  const [state, detail] = audit({ iat: NOW - 900, exp: NOW - 360 }, NOW);
  assert.equal(state, 'already-expired');
  assert.match(detail, /cached/);
});

test('a fast signing clock is reported as drift and not as the ceiling', () => {
  const [state, detail] = audit({ iat: NOW + 300, exp: NOW + 540 }, NOW);
  assert.equal(state, 'iat-in-the-future');
  assert.match(detail, /different repair/);
});

test('a jwt about to expire is flagged before it does', () => {
  assert.equal(audit({ iat: NOW - 580, exp: NOW + 20 }, NOW)[0], 'expiring-imminently');
});

test('a healthy jwt says so without qualification', () => {
  const [state, detail] = audit({ iat: NOW - 60, exp: NOW + 480 }, NOW);
  assert.equal(state, 'within-ceiling');
  assert.match(detail, /540s/);
});

test('the recommendation is a pair of numbers to paste', () => {
  const want = recommend({ iat: NOW, exp: NOW + 3600 }, NOW);
  assert.equal(want.iat, NOW - 60);
  assert.equal(want.exp, NOW + 480);
  assert.equal(want.seconds_to_remove, 3060);
});

test('the live messages map to the same states as the local check', () => {
  assert.equal(interpret(200, null)[0], 'accepted');
  assert.equal(interpret(401, "'Expiration time' claim ('exp') is too far in the future")[0],
    'exp-too-far-future');
  assert.equal(interpret(401, "'Issued at' claim ('iat') is in the future")[0],
    'iat-in-the-future');
  assert.equal(interpret(401,
    "'Expiration time' claim ('exp') must be a numeric value representing the future time")[0],
  'already-expired');
  assert.equal(interpret(401, 'A JSON web token could not be decoded')[0], 'undecodable');
  assert.equal(interpret(404, 'Integration not found')[0], 'wrong-app-or-key');
  assert.equal(interpret(403, 'Resource not accessible by integration')[0], 'unrelated');
});
''',
"faq": [
 ("Why ten minutes rather than an hour?",
  "Because the JWT is not the working credential. Its only job is to prove the App owns its private key for long enough to exchange it for an installation access token, and that exchange takes milliseconds. A short ceiling limits what a leaked JWT is worth: an hour of App-level authority is a meaningful prize, ten minutes is barely worth stealing. The installation token that comes out of the exchange lasts an hour instead, and that one is scoped to a single installation and its permissions rather than to the whole App."),
 ("Is it exp minus iat, or exp minus now?",
  "GitHub measures the requested lifetime as exp minus iat, so a JWT can be refused for being too long even when it would expire two minutes from now by your clock. That is why the check is local arithmetic rather than a comparison against the current time, and why the script tests the ceiling before it tests anything clock-relative: a lifetime over 600 seconds is wrong regardless of what time either machine thinks it is."),
 ("I set exp to iat plus 600 exactly and it still fails sometimes. Why?",
  "Because iat is compared against GitHub's clock, not yours, and a signing machine running even slightly fast pushes the whole window forward. At exactly 600 there is no headroom for that, so the request lands on the wrong side of the boundary intermittently, which is the worst way for it to fail. Setting iat sixty seconds in the past and exp to iat plus 540 leaves slack at both ends, and costs nothing since the JWT is discarded after the exchange anyway."),
 ("Can I reuse one JWT for several installations?",
  "You can, within its lifetime, since the JWT authenticates the App rather than any one installation. The reason not to hold it longer than a single burst of work is that a cached JWT is the direct cause of the intermittent variant of this failure: it works for the first several minutes after a deploy and then starts returning 401 with a message about exp, which looks like an unrelated outage. Signing is cheap. Mint one per exchange and the class of bug disappears."),
 ("The message names iat rather than exp. Is that the same problem?",
  "No, and the difference is which machine is wrong. Too far in the future means the lifetime you asked for exceeds the ceiling, which is a defect in your code. An iat in the future means the moment you claim to have signed at has not happened yet as far as GitHub is concerned, which is clock drift on the signing host. The repair for the first is a smaller exp; the repair for the second is to backdate iat by a minute and then to fix the clock, because drift that is large enough to break a JWT will break other things too."),
],
"related": [
 ("/github/installation-token-rejected-by-endpoint/", "Endpoints that refuse an installation token"),
 ("/github/app-permission-missing/", "Resource not accessible by integration"),
 ("/github/bad-credentials-401/", "401 Bad credentials on every endpoint"),
],
"citations": [CITE_JWT, CITE_APP_AUTH, CITE_APPS_REST, CITE_RFC7519],
},

]
