#!/usr/bin/env python3
"""/github/ field notes, batch I — the writing.

Four notes that all end at a refusal and reach it by four different routes.
None of them is a fifth way of saying "rotate the token", and two of them are
about a request whose credential is perfect.

The first is about a header that is not the credential at all. GitHub applies
the User-Agent rule before it looks at authentication, so the refusal is a 403
on endpoints that need no credential, and the only thing that separates it from
the other three 403s in this section is the sentence in the body. The script
sorts the 403 first and grades the header second.

The second is about the word in front of the credential rather than the
credential. A GitHub credential announces its own type in its first few
characters, so the pairing of scheme word to credential type is decided on the
client's own machine, before a socket is opened.

The third and fourth are both "the token is gone", and they are deliberately
not the same note. The third is a clock: a class of token that emits no expiry
header is removed after a year of disuse, and the margin against that window is
arithmetic on how often your own job runs, which means it can be computed a
year in advance. The fourth is a decision somebody else made this morning, so
there is no clock at all, and the only reading available is the shape of a
population: one refusal among many successes is that person, every refusal at
once is you.

Read only throughout. Where the repair is a header to set, a token to mint or a
person to ask, the script prints it and stops.
"""

CITE_TROUBLESHOOT = ("Troubleshooting the REST API — GitHub Docs",
                     "https://docs.github.com/en/rest/using-the-rest-api/troubleshooting-the-rest-api")
CITE_GETTING_STARTED = ("Getting started with the REST API — GitHub Docs",
                        "https://docs.github.com/en/rest/using-the-rest-api/getting-started-with-the-rest-api")
CITE_AUTHENTICATING = ("Authenticating to the REST API — GitHub Docs",
                       "https://docs.github.com/en/rest/authentication/authenticating-to-the-rest-api")
CITE_CREDS_SECURE = ("Keeping your API credentials secure — GitHub Docs",
                     "https://docs.github.com/en/rest/authentication/keeping-your-api-credentials-secure")
CITE_PATS = ("Managing your personal access tokens — GitHub Docs",
             "https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens")
CITE_RATE_LIMIT_ENDPOINT = ("Rate limit — GitHub REST API",
                            "https://docs.github.com/en/rest/rate-limit/rate-limit")
CITE_REST_LIMITS = ("Rate limits for the REST API — GitHub Docs",
                    "https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api")
CITE_JWT = ("Generating a JSON Web Token for a GitHub App — GitHub Docs",
            "https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-a-json-web-token-jwt-for-a-github-app")
CITE_APP_AUTH = ("Authenticating with a GitHub App — GitHub Docs",
                 "https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/about-authentication-with-a-github-app")
CITE_OAUTH_APPS_API = ("OAuth applications — GitHub REST API",
                       "https://docs.github.com/en/rest/apps/oauth-applications")
CITE_AUTHORIZING = ("Authorizing OAuth apps — GitHub Docs",
                    "https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps")
CITE_REVOKING = ("Reviewing and revoking authorization of GitHub Apps — GitHub Docs",
                 "https://docs.github.com/en/apps/using-github-apps/reviewing-and-revoking-authorization-of-github-apps")
CITE_USERS = ("Users — GitHub REST API",
              "https://docs.github.com/en/rest/users/users")

GUIDES = [

{
"slug": "user-agent-missing",
"title": "Every request 403s because there is no User-Agent header",
"description": "GitHub applies the User-Agent rule before it looks at your credential, so this 403 hits endpoints that need no credential at all. The body names the rule.",
"h1": "every request 403s because there is no User-Agent header",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github api 403 user agent", "request forbidden by administrative rules",
             "github api requires user agent header", "github 403 not rate limit",
             "github api user agent best practice"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "<code>403 {&quot;message&quot;:&quot;Request forbidden by administrative rules. Please make sure your request has a User-Agent header.&quot;}</code> &mdash; and it happens on the REST root, which any anonymous caller can read. Nobody looks at the body, because 403 in this API almost always means quota or permissions, and both of those theories send you somewhere the answer is not.",
"short_answer": """<p>GitHub requires a <code>User-Agent</code> header on every API request and refuses the ones that arrive without it. That check runs <em>before</em> authentication, which is why the refusal lands on endpoints that need no token and why widening the token changes nothing.</p>
<p>So the first move is not a request, it is a sort. A 403 from this API is one of four things: the User-Agent rule, primary quota exhaustion, a secondary limit, or a permission. Exactly one of them names itself in the response body, and it is this one. The script below classifies the 403 from the body and the headers, then grades the <code>User-Agent</code> the client actually put on the wire &mdash; which it reads off its own request object rather than off a second request &mdash; and prints a replacement string that names your application and a way to reach you.</p>""",
"problem": """<p>The status code is the trap. Everybody in this section has been trained that 403 means rate limit or permissions, so the first twenty minutes go to <code>GET /rate_limit</code>, which reports five thousand requests remaining, and the next twenty go to the repository settings page, which shows the account as an admin. Both readings are correct and neither is relevant.</p>
<p>Then the credential gets blamed. The token is re-minted, and re-minted wider, and the failure does not move, because the request never got as far as the credential. A token with every box ticked is refused exactly as fast as no token at all, which leaves behind <a href="/github/over-scoped-token/">a permanently over-broad credential</a> and an unsolved problem.</p>
<p>It shows up in a specific place, too, which is why it feels like it comes out of nowhere. Every serious GitHub SDK sets a <code>User-Agent</code> for you, so this never happens while you are prototyping with Octokit or PyGithub. It happens the day somebody drops to a raw socket, a shell script, a Lambda runtime with a hand-built request, or a language's bare standard-library HTTP client &mdash; the layer under the SDK, where nothing is set for you.</p>""",
"why": """<p><strong>The rule is applied before authentication.</strong> This is the single most useful fact here. A request with no <code>User-Agent</code> is refused whether it carries a perfect token, an expired one or none, and it is refused on paths that have no permission model at all. If a call to the REST root 403s, no amount of work on the credential can matter, because the credential was never consulted.</p>
<p><strong>The body names the rule in words.</strong> GitHub does not leave you guessing on this one: the message asks for a <code>User-Agent</code> header by name. That makes it the only 403 in this section you can identify from a single response without a control request, a header pair or a second endpoint &mdash; provided somebody logs the body, which is the part that usually goes missing.</p>
<p><strong>A library default satisfies the rule and fails the intent.</strong> <code>python-requests/2.31.0</code> is a <code>User-Agent</code>, so the request works. It also describes several million other callers, so when your integration starts behaving badly there is nothing for GitHub to identify but the address it came from. The documented ask is for the header to name the application or the account operating it, and the difference only ever matters on the day somebody needs to reach you.</p>
<p><strong>It is a default, not a per-request argument.</strong> A header applied at each call site survives exactly as long as nobody adds a new call site. Set it once on the session, the client instance or the transport, so the request that forgets it cannot be constructed.</p>
<p><strong>What a script cannot tell you is what the network did.</strong> A header that your process set and a proxy stripped looks, from GitHub's side, exactly like a header you never set. The one reading that distinguishes them is on your own machine: what the HTTP client recorded as sent, after redirects and after every interceptor. That is a property of the request object, not of the response, and it costs nothing to look at.</p>""",
"steps": [
 {"h": "Read the body of the 403 before anything else",
  "body": """<p>Not the status, the body. If the message mentions administrative rules or asks for a <code>User-Agent</code>, you are done diagnosing and the rest of this page is about the repair. If it says <code>Resource not accessible by integration</code> or mentions a secondary rate limit, this is not your problem and the script will say so rather than guessing.</p>"""},
 {"h": "Confirm the 403 is not quota, in the same response",
  "body": """<p><code>x-ratelimit-remaining</code> rides on the refusal. A value above zero rules out primary exhaustion without a second call. A value of zero sends you to <a href="/github/rate-limit-core-exhausted/">the core quota note</a>, and no header will help there.</p>"""},
 {"h": "Ask your own client what it actually sent",
  "body": """<p>After the request, the header set is on the request object: <code>response.request.headers</code> in requests, the object you passed in <code>fetch</code>. This is the wire truth after redirects and interceptors, and it separates "we never set it" from "we set it and something removed it". Those have different repairs and only one of them is in your code.</p>"""},
 {"h": "Set a descriptive default on the client, not on the call",
  "body": """<p><code>acme-repo-auditor/1.2 (+https://acme.example/contact)</code>: the application, its version, and somewhere to reach whoever runs it. Put it on the session or transport so the header is present on requests nobody has written yet.</p>"""},
 {"h": "Re-run the same path and check the grade, not just the status",
  "body": """<p>A 200 with <code>python-requests/2.31.0</code> is a pass on the rule and a fail on the point of it. The script reports that state separately, because it is the one that will still be true in a year if you only ever look at status codes.</p>"""},
],
"verify": """<p>Two runs against the same path. The first reproduces the refusal by removing the header entirely; the second sets a descriptive one and shows the request succeeding without any credential at all, which is the clearest possible demonstration that the credential was never the subject.</p>
<pre><code class="language-bash">python3 github_user_agent_403.py --path / --no-user-agent
# / returned 403
# user-agent sent: none
# user-agent-missing: the body names the rule: GitHub requires a User-Agent
#   header on every API request and refuses the ones that arrive without it.

python3 github_user_agent_403.py --path / --app "Acme Repo Auditor" \\
    --contact https://acme.example/contact
# / returned 200
# user-agent sent: acme-repo-auditor/1.0 (+https://acme.example/contact)
# user-agent-ok: the request succeeded and the header identifies the caller.</code></pre>""",
"code_intro": "One GET, and the half of the answer that matters never comes back over the wire: the client reads what it sent off its own request object. Everything that produces a finding is pure &mdash; a classifier that sorts a 403 by the sentence in its body, a grader that tells an absent header from a library default from a descriptive one, and a builder for the replacement string. The reproduction flag is the only part that needs the network, and it is a GET to a path any anonymous caller may read.",
"py_file": "github_user_agent_403.py",
"py": '''"""Sort a GitHub 403 by cause, then grade the User-Agent the client sent.

Read only. One GET, to a path you choose, defaulting to the REST root, which
any anonymous caller may read. Nothing here writes, nothing needs a scope, and
the credential is optional because the rule this note is about is applied
before the credential is looked at.

GitHub requires a User-Agent header on every API request. Requests without one
are refused with a 403 whose body names the rule. That makes it the only 403 in
this API you can identify from a single response, and the easiest one to
mistake for the other three, all of which produce the same status code.
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_user_agent_403")

API = "https://api.github.com"

# The User-Agent strings HTTP clients supply when nobody sets one. They satisfy
# the rule, so the request works. They also describe several million other
# callers, which is the half of the ask they fail: the documented request is
# for a header naming the application or the account behind it.
LIBRARY_DEFAULTS = (
    "python-requests/", "python-urllib/", "urllib3/", "python-httpx/", "httpx/",
    "go-http-client/", "node-fetch/", "undici", "node/", "axios/", "got (",
    "okhttp/", "java/", "apache-httpclient/", "curl/", "libcurl/", "wget/",
    "httpie/", "postmanruntime/", "restsharp/", "guzzlehttp/", "faraday",
    "ruby/", "php/", "dart/", "reqwest/", "http.rb/", "python/",
)


def _has_version(text):
    """True when some token in the string looks like name/1.2. Pure helper."""
    for part in str(text).split():
        if "/" in part:
            tail = part.split("/", 1)[1].lstrip("vV")
            if tail[:1].isdigit():
                return True
    return False


def grade_user_agent(value):
    """Grade a User-Agent string. Pure.

    Five grades, because "absent" and "present but useless" are different
    findings with different urgencies: one is why the request is being refused
    right now, the other is why nobody will be able to reach you later.
    """
    if value is None:
        return ("absent",
                "no User-Agent header at all. GitHub refuses the request "
                "before it considers the credential, so this fails on "
                "endpoints that need no credential.")
    text = str(value).strip()
    if not text:
        return ("empty",
                "the header is present with an empty value, which is refused "
                "exactly as if it had never been set.")
    low = text.lower()
    for prefix in LIBRARY_DEFAULTS:
        if low.startswith(prefix):
            return ("library-default",
                    "the header names the HTTP library rather than your "
                    "integration. The request works; nobody at GitHub can "
                    "tell your traffic from anyone else's using that library.")
    has_version = _has_version(text)
    has_contact = "http" in low or "@" in text
    if has_version and has_contact:
        return ("descriptive",
                "names the application, a version and a way to reach you. "
                "Nothing to change.")
    if has_version or has_contact:
        return ("named",
                "identifies the caller, but only halfway. Add whichever half "
                "is missing: a version, or a URL or address to reach you at.")
    return ("opaque",
            "present and custom, but it names nothing anyone could act on. "
            "Add a version and a contact.")


def classify_403(message, headers):
    """Sort a 403 into the four things it means on this API. Pure.

    Order matters. The User-Agent rule names itself, so it is checked first and
    never inferred. A secondary limit says so in the body. Primary exhaustion
    says so in a header rather than in words. Everything else is authorization,
    and none of it is repaired by a header.
    """
    text = (message or "").lower()
    head = {str(k).lower(): str(v) for k, v in (headers or {}).items()}
    if "user-agent" in text or "administrative rules" in text:
        return ("user-agent-rule",
                "the body names the rule: GitHub requires a User-Agent header "
                "on every API request and refuses the ones that arrive "
                "without it.")
    if "secondary rate limit" in text or "abuse detection" in text:
        return ("secondary-rate-limit",
                "a secondary limit, which is about the shape of the traffic "
                "rather than the number of requests. Slow down and honour "
                "retry-after; no header changes this.")
    if head.get("x-ratelimit-remaining") == "0":
        return ("primary-rate-limit",
                "x-ratelimit-remaining is zero, so this is the hourly quota "
                "and the reset time is on the same response.")
    if "saml" in text or "single sign-on" in text or "sso" in text:
        return ("sso-enforcement",
                "an organization enforcing SSO is hiding the resource from a "
                "credential that has not been authorized for it.")
    if ("not accessible by integration" in text or "must have admin" in text
            or "resource not accessible" in text or "permission" in text):
        return ("permission",
                "an authorization refusal: the credential reached GitHub, was "
                "accepted, and is not allowed to do this.")
    if "ip address" in text or "allow list" in text or "allowlist" in text:
        return ("ip-allow-list",
                "an organization IP allow list refused the source address. "
                "The repair is a network conversation, not a code change.")
    return ("unclassified-403",
            "the body does not match any of the shapes this script knows. "
            "Read it literally; it is the most specific thing you have.")


def verdict(status, message, headers, user_agent_sent):
    """Combine a status, a body message and what the client actually sent. Pure.

    A successful request is still worth a finding. The rule is satisfied by any
    non-empty string, so a 200 proves nothing about whether the header names
    anything, and that is the state that survives for years unnoticed.
    """
    grade, detail = grade_user_agent(user_agent_sent)
    if status == 403:
        cause, why = classify_403(message, headers)
        if cause == "user-agent-rule":
            return ("user-agent-missing",
                    "%s What the client actually sent: %s."
                    % (why, "nothing"
                       if grade in ("absent", "empty") else repr(user_agent_sent)))
        return (cause, "%s This is a 403, but not the one this page is about, "
                       "and no User-Agent will repair it." % why)
    if status == 401:
        return ("not-a-user-agent-problem",
                "a 401 means a credential was received and refused, or was "
                "required and never arrived. The User-Agent rule answers 403 "
                "and never 401.")
    if status >= 400:
        return ("other-failure",
                "status %d, which the User-Agent rule does not produce. The "
                "header that was sent grades as %s." % (status, grade))
    if grade in ("descriptive", "named"):
        return ("user-agent-ok",
                "the request succeeded and the header identifies the caller. "
                "%s" % detail)
    return ("identifiable-agent-missing",
            "the request succeeded, so the rule itself is satisfied, but %s"
            % detail)


def suggest_user_agent(app, version="1.0", contact=None):
    """Build the replacement header value. Pure.

    Deliberately boring: a slug, a version, and a contact in the parenthesised
    form GitHub's own examples use. The value of this function is that it
    always produces something that grades as descriptive.
    """
    slug = "".join(c if c.isalnum() else "-" for c in str(app).lower())
    while "--" in slug:
        slug = slug.replace("--", "-")
    slug = slug.strip("-") or "unnamed-integration"
    agent = "%s/%s" % (slug, version)
    if contact:
        agent += " (+%s)" % contact
    return agent


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--path", default="/",
                    help="the API path that was refused. The default is the "
                         "REST root, which any anonymous caller may read")
    ap.add_argument("--app", default="",
                    help="the name of your integration, for the suggested header")
    ap.add_argument("--contact", default="",
                    help="a URL or address GitHub could use to reach you")
    ap.add_argument("--no-user-agent", action="store_true",
                    help="reproduce the refusal by removing the header entirely")
    args = ap.parse_args()

    session = requests.Session()
    session.headers.update({
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    if args.no_user_agent:
        # requests drops a header set to None rather than falling back to its
        # own default, which is the only way to actually reproduce this from a
        # client that is trying to be helpful.
        session.headers["User-Agent"] = None
    elif args.app:
        session.headers["User-Agent"] = suggest_user_agent(
            args.app, contact=args.contact or None)

    token = os.environ.get("GITHUB_TOKEN")
    if token:
        session.headers["Authorization"] = "Bearer " + token
    else:
        log.info("no GITHUB_TOKEN set, which is fine: the User-Agent rule is "
                 "applied before authentication, so an anonymous request "
                 "demonstrates it exactly as well")

    url = API + args.path if args.path.startswith("/") else args.path
    response = session.get(url, timeout=30)
    try:
        body = response.json()
    except ValueError:
        body = None
    message = body.get("message") if isinstance(body, dict) else None
    headers = {k.lower(): v for k, v in response.headers.items()}

    # The authoritative reading of what went on the wire, after redirects and
    # after whatever the library added. It lives on the request object the
    # client already holds, so it needs no second request and no control.
    sent = response.request.headers.get("User-Agent")

    log.info("%s returned %d", args.path, response.status_code)
    log.info("user-agent sent: %s", sent if sent else "none")
    log.info("body message:    %s", message or "none")
    log.info("remaining quota: %s", headers.get("x-ratelimit-remaining", "not reported"))

    state, detail = verdict(response.status_code, message, headers, sent)
    log.info("%s: %s", state, detail)

    if state in ("user-agent-missing", "identifiable-agent-missing"):
        want = suggest_user_agent(args.app or "your integration",
                                  contact=args.contact or "https://example.com/contact")
        log.info("repair: set this once on the session, client or transport, "
                 "never per request: User-Agent: %s", want)
        log.info("repair: a request that forgets the header should be "
                 "impossible to construct, not merely rare.")

    print(json.dumps({"path": args.path, "status": response.status_code,
                      "user_agent_sent": sent, "message": message,
                      "state": state}, indent=2))
    return 1 if state in ("user-agent-missing", "identifiable-agent-missing") else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-user-agent-403.mjs",
"js": '''/**
 * Sort a GitHub 403 by cause, then grade the User-Agent the client sent.
 *
 * Read only. One GET, defaulting to the REST root, which any anonymous caller
 * may read. The credential is optional, because the rule this note is about is
 * applied before the credential is looked at.
 *
 * One honest difference from the Python version: Node's fetch supplies a
 * default User-Agent of its own when you omit the header, so the reproduction
 * flag here cannot actually produce a request with no header. What this script
 * grades is the header it configured, which is what your code controls.
 */
const API = 'https://api.github.com';

/** The User-Agent strings HTTP clients supply when nobody sets one. */
export const LIBRARY_DEFAULTS = [
  'python-requests/', 'python-urllib/', 'urllib3/', 'python-httpx/', 'httpx/',
  'go-http-client/', 'node-fetch/', 'undici', 'node/', 'axios/', 'got (',
  'okhttp/', 'java/', 'apache-httpclient/', 'curl/', 'libcurl/', 'wget/',
  'httpie/', 'postmanruntime/', 'restsharp/', 'guzzlehttp/', 'faraday',
  'ruby/', 'php/', 'dart/', 'reqwest/', 'http.rb/', 'python/',
];

/** True when some token in the string looks like name/1.2. Pure. */
function hasVersion(text) {
  for (const part of String(text).split(/\\s+/)) {
    if (part.includes('/')) {
      const tail = part.slice(part.indexOf('/') + 1).replace(/^[vV]+/, '');
      if (tail.length && tail[0] >= '0' && tail[0] <= '9') return true;
    }
  }
  return false;
}

/** Grade a User-Agent string. Pure. Five grades, not two. */
export function gradeUserAgent(value) {
  if (value === null || value === undefined) {
    return ['absent',
      'no User-Agent header at all. GitHub refuses the request before it ' +
      'considers the credential, so this fails on endpoints that need no ' +
      'credential.'];
  }
  const text = String(value).trim();
  if (!text) {
    return ['empty',
      'the header is present with an empty value, which is refused exactly ' +
      'as if it had never been set.'];
  }
  const low = text.toLowerCase();
  for (const prefix of LIBRARY_DEFAULTS) {
    if (low.startsWith(prefix)) {
      return ['library-default',
        'the header names the HTTP library rather than your integration. The ' +
        'request works; nobody at GitHub can tell your traffic from anyone ' +
        "else's using that library."];
    }
  }
  const version = hasVersion(text);
  const contact = low.includes('http') || text.includes('@');
  if (version && contact) {
    return ['descriptive',
      'names the application, a version and a way to reach you. Nothing to change.'];
  }
  if (version || contact) {
    return ['named',
      'identifies the caller, but only halfway. Add whichever half is ' +
      'missing: a version, or a URL or address to reach you at.'];
  }
  return ['opaque',
    'present and custom, but it names nothing anyone could act on. Add a ' +
    'version and a contact.'];
}

/** Sort a 403 into the four things it means on this API. Pure. */
export function classify403(message, headers) {
  const text = String(message ?? '').toLowerCase();
  const head = {};
  for (const [k, v] of Object.entries(headers ?? {})) head[String(k).toLowerCase()] = String(v);
  if (text.includes('user-agent') || text.includes('administrative rules')) {
    return ['user-agent-rule',
      'the body names the rule: GitHub requires a User-Agent header on every ' +
      'API request and refuses the ones that arrive without it.'];
  }
  if (text.includes('secondary rate limit') || text.includes('abuse detection')) {
    return ['secondary-rate-limit',
      'a secondary limit, which is about the shape of the traffic rather ' +
      'than the number of requests. Slow down and honour retry-after; no ' +
      'header changes this.'];
  }
  if (head['x-ratelimit-remaining'] === '0') {
    return ['primary-rate-limit',
      'x-ratelimit-remaining is zero, so this is the hourly quota and the ' +
      'reset time is on the same response.'];
  }
  if (text.includes('saml') || text.includes('single sign-on') || text.includes('sso')) {
    return ['sso-enforcement',
      'an organization enforcing SSO is hiding the resource from a ' +
      'credential that has not been authorized for it.'];
  }
  if (text.includes('not accessible by integration') || text.includes('must have admin')
      || text.includes('resource not accessible') || text.includes('permission')) {
    return ['permission',
      'an authorization refusal: the credential reached GitHub, was ' +
      'accepted, and is not allowed to do this.'];
  }
  if (text.includes('ip address') || text.includes('allow list') || text.includes('allowlist')) {
    return ['ip-allow-list',
      'an organization IP allow list refused the source address. The repair ' +
      'is a network conversation, not a code change.'];
  }
  return ['unclassified-403',
    'the body does not match any of the shapes this script knows. Read it ' +
    'literally; it is the most specific thing you have.'];
}

/** Combine a status, a body message and what the client actually sent. Pure. */
export function verdict(status, message, headers, userAgentSent) {
  const [grade, detail] = gradeUserAgent(userAgentSent);
  if (status === 403) {
    const [cause, why] = classify403(message, headers);
    if (cause === 'user-agent-rule') {
      const shown = (grade === 'absent' || grade === 'empty')
        ? 'nothing' : JSON.stringify(userAgentSent);
      return ['user-agent-missing', `${why} What the client actually sent: ${shown}.`];
    }
    return [cause, `${why} This is a 403, but not the one this page is ` +
      'about, and no User-Agent will repair it.'];
  }
  if (status === 401) {
    return ['not-a-user-agent-problem',
      'a 401 means a credential was received and refused, or was required ' +
      'and never arrived. The User-Agent rule answers 403 and never 401.'];
  }
  if (status >= 400) {
    return ['other-failure',
      `status ${status}, which the User-Agent rule does not produce. The ` +
      `header that was sent grades as ${grade}.`];
  }
  if (grade === 'descriptive' || grade === 'named') {
    return ['user-agent-ok',
      `the request succeeded and the header identifies the caller. ${detail}`];
  }
  return ['identifiable-agent-missing',
    `the request succeeded, so the rule itself is satisfied, but ${detail}`];
}

/** Build the replacement header value. Pure. */
export function suggestUserAgent(app, version = '1.0', contact = null) {
  let slug = String(app).toLowerCase().split('').map(
    (c) => (/[a-z0-9]/.test(c) ? c : '-')).join('');
  while (slug.includes('--')) slug = slug.replaceAll('--', '-');
  slug = slug.replace(/^-+|-+$/g, '') || 'unnamed-integration';
  let agent = `${slug}/${version}`;
  if (contact) agent += ` (+${contact})`;
  return agent;
}

function arg(name, fallback) {
  const i = process.argv.indexOf(name);
  return i === -1 ? fallback : process.argv[i + 1];
}

async function main() {
  const path = arg('--path', '/');
  const app = arg('--app', '');
  const contact = arg('--contact', '');
  const strip = process.argv.includes('--no-user-agent');

  const headers = {
    Accept: 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
  };
  if (!strip && app) headers['User-Agent'] = suggestUserAgent(app, '1.0', contact || null);

  const token = process.env.GITHUB_TOKEN;
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  } else {
    console.log('no GITHUB_TOKEN set, which is fine: the User-Agent rule is ' +
      'applied before authentication, so an anonymous request demonstrates it ' +
      'exactly as well');
  }

  const url = path.startsWith('/') ? API + path : path;
  const res = await fetch(url, { headers });
  let body = null;
  try { body = await res.json(); } catch { body = null; }
  const message = body && typeof body === 'object' ? body.message ?? null : null;
  const seen = {};
  for (const [k, v] of res.headers.entries()) seen[k.toLowerCase()] = v;

  // What this script configured, which is the part your code controls. Node
  // adds a default of its own when the key is absent, so an absent key here
  // does not mean an absent header on the wire.
  const sent = headers['User-Agent'] ?? null;

  console.log(`${path} returned ${res.status}`);
  console.log(`user-agent configured: ${sent ?? 'none, so Node supplied its own'}`);
  console.log(`body message:          ${message ?? 'none'}`);
  console.log(`remaining quota:       ${seen['x-ratelimit-remaining'] ?? 'not reported'}`);

  const [state, detail] = verdict(res.status, message, seen, sent);
  console.log(`${state}: ${detail}`);

  if (state === 'user-agent-missing' || state === 'identifiable-agent-missing') {
    const want = suggestUserAgent(app || 'your integration', '1.0',
      contact || 'https://example.com/contact');
    console.log('repair: set this once on the client or transport, never per ' +
      `request: User-Agent: ${want}`);
  }

  console.log(JSON.stringify({ path, status: res.status, userAgentSent: sent, message, state }, null, 2));
  process.exitCode = (state === 'user-agent-missing' ||
    state === 'identifiable-agent-missing') ? 1 : 0;
}

// Only run when invoked directly, so importing this module from the test file
// does not fire a live request and set an exit code the suite then inherits.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The cases worth pinning are the ones that are awkward to produce on demand: a 403 that is quota rather than a header, a 403 that is a permission, a header that satisfies the rule and identifies nobody, and a request that succeeded while still being wrong. All four functions take strings and return tuples, so each of those is two lines and no network.",
"test_py_file": "test_github_user_agent_403.py",
"test_py": '''from github_user_agent_403 import (
    classify_403, grade_user_agent, suggest_user_agent, verdict,
)


def test_an_absent_header_is_not_an_empty_one():
    assert grade_user_agent(None)[0] == "absent"
    assert grade_user_agent("")[0] == "empty"
    assert grade_user_agent("   ")[0] == "empty"


def test_a_library_default_satisfies_the_rule_and_identifies_nobody():
    assert grade_user_agent("python-requests/2.31.0")[0] == "library-default"
    assert grade_user_agent("Go-http-client/1.1")[0] == "library-default"
    assert grade_user_agent("curl/8.4.0")[0] == "library-default"


def test_a_named_application_with_a_version_and_a_contact_is_descriptive():
    grade, _ = grade_user_agent("acme-repo-auditor/1.2 (+https://acme.example)")
    assert grade == "descriptive"


def test_half_an_identity_is_reported_as_half():
    assert grade_user_agent("acme-repo-auditor/1.2")[0] == "named"
    assert grade_user_agent("acme (+https://acme.example)")[0] == "named"
    assert grade_user_agent("auditor")[0] == "opaque"


def test_the_user_agent_rule_names_itself_in_the_body():
    state, detail = classify_403(
        "Request forbidden by administrative rules. Please make sure your "
        "request has a User-Agent header.", {})
    assert state == "user-agent-rule"
    assert "User-Agent" in detail


def test_quota_exhaustion_is_read_from_a_header_not_from_words():
    state, _ = classify_403("API rate limit exceeded",
                            {"X-RateLimit-Remaining": "0"})
    assert state == "primary-rate-limit"


def test_a_secondary_limit_is_not_confused_with_the_primary_one():
    state, _ = classify_403("You have exceeded a secondary rate limit",
                            {"x-ratelimit-remaining": "4998"})
    assert state == "secondary-rate-limit"


def test_a_permission_refusal_is_sorted_away_from_this_page():
    state, _ = classify_403("Resource not accessible by integration", {})
    assert state == "permission"


def test_an_unfamiliar_403_is_admitted_rather_than_guessed():
    assert classify_403("Something new", {})[0] == "unclassified-403"


def test_the_missing_header_verdict_says_what_was_actually_sent():
    state, detail = verdict(
        403, "Request forbidden by administrative rules. Please make sure "
             "your request has a User-Agent header.", {}, None)
    assert state == "user-agent-missing"
    assert "nothing" in detail


def test_a_quota_403_is_not_reported_as_a_header_problem():
    state, detail = verdict(403, "API rate limit exceeded",
                            {"x-ratelimit-remaining": "0"}, "acme/1.0 (+http://a)")
    assert state == "primary-rate-limit"
    assert "no User-Agent will repair it" in detail


def test_a_401_is_sent_to_the_credential_notes():
    assert verdict(401, "Bad credentials", {}, "acme/1.0")[0] == "not-a-user-agent-problem"


def test_a_successful_request_with_a_default_agent_is_still_a_finding():
    state, _ = verdict(200, None, {}, "python-requests/2.31.0")
    assert state == "identifiable-agent-missing"


def test_a_successful_request_with_a_descriptive_agent_passes():
    state, _ = verdict(200, None, {}, "acme-auditor/1.2 (+https://acme.example)")
    assert state == "user-agent-ok"


def test_the_suggested_header_always_grades_as_descriptive():
    agent = suggest_user_agent("Acme Repo Auditor!", "1.2",
                               "https://acme.example/contact")
    assert agent == "acme-repo-auditor/1.2 (+https://acme.example/contact)"
    assert grade_user_agent(agent)[0] == "descriptive"


def test_an_unnameable_application_still_produces_a_usable_header():
    assert suggest_user_agent("!!!").startswith("unnamed-integration/")
''',
"test_js_file": "github-user-agent-403.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  classify403, gradeUserAgent, suggestUserAgent, verdict,
} from './github-user-agent-403.mjs';

test('an absent header is not an empty one', () => {
  assert.equal(gradeUserAgent(null)[0], 'absent');
  assert.equal(gradeUserAgent('')[0], 'empty');
  assert.equal(gradeUserAgent('   ')[0], 'empty');
});

test('a library default satisfies the rule and identifies nobody', () => {
  assert.equal(gradeUserAgent('python-requests/2.31.0')[0], 'library-default');
  assert.equal(gradeUserAgent('Go-http-client/1.1')[0], 'library-default');
  assert.equal(gradeUserAgent('curl/8.4.0')[0], 'library-default');
});

test('a named application with a version and a contact is descriptive', () => {
  assert.equal(gradeUserAgent('acme-repo-auditor/1.2 (+https://acme.example)')[0],
    'descriptive');
});

test('half an identity is reported as half', () => {
  assert.equal(gradeUserAgent('acme-repo-auditor/1.2')[0], 'named');
  assert.equal(gradeUserAgent('acme (+https://acme.example)')[0], 'named');
  assert.equal(gradeUserAgent('auditor')[0], 'opaque');
});

test('the user-agent rule names itself in the body', () => {
  const [state, detail] = classify403(
    'Request forbidden by administrative rules. Please make sure your '
    + 'request has a User-Agent header.', {});
  assert.equal(state, 'user-agent-rule');
  assert.ok(detail.includes('User-Agent'));
});

test('quota exhaustion is read from a header not from words', () => {
  assert.equal(classify403('API rate limit exceeded',
    { 'X-RateLimit-Remaining': '0' })[0], 'primary-rate-limit');
});

test('a secondary limit is not confused with the primary one', () => {
  assert.equal(classify403('You have exceeded a secondary rate limit',
    { 'x-ratelimit-remaining': '4998' })[0], 'secondary-rate-limit');
});

test('a permission refusal is sorted away from this page', () => {
  assert.equal(classify403('Resource not accessible by integration', {})[0],
    'permission');
});

test('an unfamiliar 403 is admitted rather than guessed', () => {
  assert.equal(classify403('Something new', {})[0], 'unclassified-403');
});

test('the missing header verdict says what was actually sent', () => {
  const [state, detail] = verdict(403,
    'Request forbidden by administrative rules. Please make sure your '
    + 'request has a User-Agent header.', {}, null);
  assert.equal(state, 'user-agent-missing');
  assert.ok(detail.includes('nothing'));
});

test('a quota 403 is not reported as a header problem', () => {
  const [state, detail] = verdict(403, 'API rate limit exceeded',
    { 'x-ratelimit-remaining': '0' }, 'acme/1.0 (+http://a)');
  assert.equal(state, 'primary-rate-limit');
  assert.ok(detail.includes('no User-Agent will repair it'));
});

test('a 401 is sent to the credential notes', () => {
  assert.equal(verdict(401, 'Bad credentials', {}, 'acme/1.0')[0],
    'not-a-user-agent-problem');
});

test('a successful request with a default agent is still a finding', () => {
  assert.equal(verdict(200, null, {}, 'python-requests/2.31.0')[0],
    'identifiable-agent-missing');
});

test('a successful request with a descriptive agent passes', () => {
  assert.equal(verdict(200, null, {}, 'acme-auditor/1.2 (+https://acme.example)')[0],
    'user-agent-ok');
});

test('the suggested header always grades as descriptive', () => {
  const agent = suggestUserAgent('Acme Repo Auditor!', '1.2',
    'https://acme.example/contact');
  assert.equal(agent, 'acme-repo-auditor/1.2 (+https://acme.example/contact)');
  assert.equal(gradeUserAgent(agent)[0], 'descriptive');
});

test('an unnameable application still produces a usable header', () => {
  assert.ok(suggestUserAgent('!!!').startsWith('unnamed-integration/'));
});
''',
"faq": [
 ("Why does this fail on endpoints that need no authentication at all?",
  "Because the User-Agent check runs before authentication is considered. The request is refused as malformed rather than as unauthorized, so the presence, absence or breadth of a token has no effect on it. That is also the fastest way to confirm the diagnosis: if the REST root, which any anonymous caller can read, answers 403, the problem cannot be about permissions or scopes, because no permission was ever consulted."),
 ("My SDK works and my curl one-liner does not. Is that the same problem?",
  "Almost certainly. Every serious GitHub SDK sets a User-Agent for you, and curl sets one too, so the pure form of this failure needs a client that sets nothing at all: a raw socket, a hand-built request in a Lambda runtime, a language's bare standard-library HTTP client, or a proxy configuration that strips unknown headers on the way out. The tell is the sentence in the body, which asks for the header by name whatever produced the request."),
 ("Does GitHub care what the User-Agent says, or only that it exists?",
  "The rule only checks that it exists, so any non-empty string makes the 403 go away. The documented ask is different from the enforced rule: GitHub asks for the header to name your application or your account. That difference has no effect until the day your integration is behaving badly and somebody at GitHub wants to tell you, at which point python-requests/2.31.0 identifies several million callers and none of them are reachable."),
 ("Is this the same as being rate limited?",
  "No, and the response tells you so in two places. A quota 403 carries x-ratelimit-remaining: 0 and a reset timestamp; a secondary limit says secondary rate limit in the body and usually carries retry-after. The User-Agent 403 carries neither, and its body asks for a header. Sorting on the body first is what stops the investigation going to the rate limit endpoint, which will cheerfully report five thousand requests remaining while every call fails."),
 ("I set the header and it still is not arriving. Where did it go?",
  "Ask your own HTTP client rather than GitHub. The request object records what was actually sent after redirects and interceptors, so response.request.headers in requests, or the object you passed to fetch, is the wire truth. A header set in your code and absent there was removed by something between the two: an interceptor, a redirect that rebuilt the request, or an egress proxy. That is a different repair from adding the header, and only one of them is in your source."),
],
"related": [
 ("/github/404-masking-403/", "A permission error disguised as 404 Not Found"),
 ("/github/rate-limit-core-exhausted/", "The core hourly quota is exhausted"),
 ("/github/bad-credentials-401/", "401 Bad credentials on every endpoint"),
],
"citations": [CITE_GETTING_STARTED, CITE_TROUBLESHOOT, CITE_REST_LIMITS, CITE_AUTHENTICATING],
},

{
"slug": "wrong-authorization-scheme",
"title": "A JWT sent as token, and the 401 blames the credential",
"description": "Bearer and the legacy token word are not interchangeable. An App JWT sent under token fails as Bad credentials, and its own shape says which is right.",
"h1": "a JWT sent as token, and the 401 blames the credential",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github authorization bearer vs token", "github app jwt 401 bad credentials",
             "authorization header github api scheme", "github jwt could not be decoded",
             "github api token scheme deprecated"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The App is registered, the private key is the right one, the JWT is freshly signed and it verifies in three different debuggers. GitHub answers <code>401 {&quot;message&quot;:&quot;Bad credentials&quot;}</code>. The credential in that request is perfect. The word in front of it is not, and the message never mentions words.",
"short_answer": """<p><code>Authorization: Bearer &lt;value&gt;</code> works for every GitHub credential. The older <code>Authorization: token &lt;value&gt;</code> works for personal access tokens, OAuth user tokens and installation access tokens, and does <strong>not</strong> work for a GitHub App JWT. That one pairing &mdash; a JWT under the <code>token</code> word &mdash; fails with the generic bad-credentials message, which names the credential and says nothing about the envelope.</p>
<p>You do not need a request to find this. A GitHub credential announces its own type in its first few characters: <code>ghp_</code>, <code>gho_</code>, <code>ghu_</code>, <code>ghs_</code>, <code>ghr_</code>, <code>github_pat_</code>, and a JWT announces itself by having three dot-separated segments. The script below reads the shape on your own machine, decides which scheme word belongs in front of it, and only then sends the same path twice &mdash; once with the word you configured and once with <code>Bearer</code> &mdash; so the difference is attributable to the word alone.</p>""",
"problem": """<p>The message is the whole problem. <code>Bad credentials</code> is a sentence about the value, so every instinct it triggers is about the value: regenerate the private key, check the App id, re-copy the PEM, confirm the key was not the one that got rotated last month. People burn an afternoon generating keys, and each new key fails identically, because each new key is being handed over in an envelope GitHub will not open.</p>
<p>What makes it stick is that the wrong word usually works. A team writes the <code>token</code> spelling once, for a personal access token, five years ago. It works. It goes into the shared HTTP helper. Everything built on that helper works for years. Then somebody adds GitHub App authentication through the same helper, and the one credential type that will not accept the legacy word goes through the code path that hard-codes it.</p>
<p>And the near-miss is worse than the miss. Sending a PAT to an App-only endpoint gives you a different and much more helpful message about a JSON web token that could not be decoded, which at least names the subject. Sending a JWT under <code>token</code> gives you the same three words a dead token gives you, so the two most common App-authentication failures are indistinguishable from the response and completely different in their repairs.</p>""",
"why": """<p><strong>Bearer is the general case and <code>token</code> is a survivor.</strong> GitHub's current documentation writes <code>Authorization: Bearer</code> everywhere. The <code>token</code> spelling predates it, is still accepted for the credential types it always covered, and is exactly the kind of thing that stays in a codebase for a decade because removing it would be a change with no visible benefit &mdash; right up until it meets the one credential type it never covered.</p>
<p><strong>The credential's own text tells you its type.</strong> Since the prefixed token formats landed, a value beginning <code>ghp_</code> is a classic personal access token, <code>gho_</code> an OAuth user token, <code>ghu_</code> a user-to-server token, <code>ghs_</code> an installation access token, <code>ghr_</code> a refresh token, and <code>github_pat_</code> a fine-grained personal access token. None of that needs a request, which means the pairing can be checked at startup rather than discovered in production.</p>
<p><strong>A JWT is recognisable without being decoded.</strong> Three dot-separated base64url segments, the first of which begins <code>eyJ</code>, because that is what an opening brace and a quote encode to. This script deliberately stops there and does not decode the payload: what the claims say is a genuinely different question from what word goes in front of them.</p>
<p><strong>A bare value with no scheme is refused too.</strong> <code>Authorization: ghp_&hellip;</code> with no word at all is not a shorthand for anything. GitHub cannot tell what it is being offered and answers with the same bad-credentials message, which is the second-most common version of this and the one that survives a careless string concatenation.</p>
<p><strong>The scheme word is not the only thing that can be wrong.</strong> A credential of the right type under the right word can still be refused for being dead, for belonging to the wrong account, or for being aimed at an endpoint that will not accept its type. This script answers exactly one of those questions and hands off the others rather than pretending the envelope explains everything.</p>""",
"steps": [
 {"h": "Name the credential type from its own first characters",
  "body": """<p>Do this locally, before anything is sent. A prefix match or a three-segment shape is all it takes, and it costs no request, no quota and no log line containing a secret. Print the type, never the value.</p>"""},
 {"h": "Look up which scheme words that type accepts",
  "body": """<p>An App JWT accepts <code>Bearer</code> only. Personal access tokens, OAuth user tokens and installation tokens accept <code>Bearer</code> and the legacy <code>token</code> word. A refresh token accepts neither, because it is not an API credential at all: it is exchanged for one.</p>"""},
 {"h": "Parse the Authorization header your client is really building",
  "body": """<p>Split it on whitespace. One word means there is no scheme at all. Two means a scheme and a value. Watch for <code>Basic</code>, which is a <a href="/github/basic-auth-password-removed/">different retired mechanism</a> with a different repair, and for anything that is neither <code>Bearer</code> nor <code>token</code>, which GitHub does not read.</p>"""},
 {"h": "Send the same path twice, with the two words",
  "body": """<p>This is the only network step, and it is the experiment that isolates the variable: same path, same credential, same everything except the scheme word. If the status moves, the word was the cause. If both fail identically, the envelope is innocent and the credential is not.</p>"""},
 {"h": "Fix it once, in the place that builds the header",
  "body": """<p>Not at the call site that failed. The whole failure mode is a helper that hard-codes one word for every credential it will ever carry, so the repair is to make that helper emit <code>Bearer</code> for all of them and then delete the alternative.</p>"""},
],
"verify": """<p>The pair of statuses is the result. A 401 under <code>token</code> and a 200 under <code>Bearer</code>, from the same credential against the same path, is a complete proof that nothing about the credential needed changing.</p>
<pre><code class="language-bash">python3 github_auth_scheme.py --path /app --scheme token
# credential type: app-jwt
# jwt-with-token-scheme: an App JWT is only read under Bearer. Under the token
#   scheme it is refused with the generic bad-credentials message.
# as configured (token):  401 Bad credentials
# as recommended (Bearer): 200
# repair: change the word token to Bearer and send the same JWT</code></pre>""",
"code_intro": "The diagnosis is local. A prefix table and a shape test name the credential type from its own first characters, an acceptance table says which scheme words that type takes, and a parser splits the header your client builds; none of them touch the network and none of them return the credential's value. Only the confirmation goes out, as two GETs to the same path that differ in one word. The 401 message table is small on purpose: GitHub uses very few sentences for authentication failures, and the useful work is mapping them onto causes rather than collecting them.",
"py_file": "github_auth_scheme.py",
"py": '''"""Check the Authorization scheme word against the shape of the credential.

Read only. The diagnosis is computed on this machine from the credential's own
first characters; the only network work is two GETs to the same path that
differ in one word, which is the experiment that isolates the variable.

Bearer works for every GitHub credential. The older token word works for
personal access tokens, OAuth user tokens and installation access tokens, and
not for a GitHub App JWT. That one pairing fails with the generic bad
credentials message, which names the credential and hides the envelope.

The credential value is never printed, logged or returned. Only its type is.
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_auth_scheme")

API = "https://api.github.com"
UA = "github-auth-scheme/1.0 (+https://example.com/contact)"

# GitHub's prefixed credential formats. Longest first so github_pat_ is not
# shadowed by a shorter neighbour if this table ever grows one.
PREFIXES = (
    ("github_pat_", "fine-grained-pat"),
    ("ghp_", "classic-pat"),
    ("gho_", "oauth-user-token"),
    ("ghu_", "user-to-server-token"),
    ("ghs_", "installation-token"),
    ("ghr_", "refresh-token"),
)

# The base64url alphabet, plus padding, which is what a JWT's three segments are
# drawn from. Used for recognition only; nothing here decodes anything.
B64URL = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_=")

# What each credential type accepts in front of it, lowercased. Bearer is
# correct for all of them; the legacy word is accepted for everything except an
# App JWT, which is the pairing this note exists for.
ACCEPTS = {
    "app-jwt": ("bearer",),
    "classic-pat": ("bearer", "token"),
    "fine-grained-pat": ("bearer", "token"),
    "oauth-user-token": ("bearer", "token"),
    "user-to-server-token": ("bearer", "token"),
    "installation-token": ("bearer", "token"),
    "legacy-pat": ("bearer", "token"),
    "refresh-token": (),
    "unknown": ("bearer", "token"),
    "absent": (),
}

# The short set of sentences GitHub uses for an authentication failure. The
# value of this table is that two of them are much more specific than the third.
MESSAGES = (
    ("a json web token could not be decoded",
     ("jwt-expected",
      "the endpoint wanted an App JWT and got something that is not one. That "
      "is a credential type mismatch rather than a scheme one, and it is the "
      "helpful failure: it names its subject.")),
    ("requires authentication",
     ("nothing-arrived",
      "no Authorization header reached GitHub at all, so the scheme word is "
      "not the question yet. Something between your process and GitHub "
      "dropped the header.")),
    ("bad credentials",
     ("received-and-refused",
      "GitHub parsed something and did not accept it. A JWT under the token "
      "word produces exactly this, and so does a dead token, so the message "
      "alone does not separate them.")),
)


def looks_like_jwt(value):
    """Recognise a JWT by shape alone. Pure.

    Three dot separated base64url segments, the first of which starts with the
    encoding of an opening brace and a quote. The payload is deliberately not
    decoded: what the claims say is a different question and a different note.
    """
    if not value:
        return False
    parts = str(value).split(".")
    if len(parts) != 3 or not all(parts):
        return False
    if not all(set(p) <= B64URL for p in parts):
        return False
    return parts[0].startswith("eyJ")


def credential_kind(value):
    """Name a credential's type from its own text. Pure.

    Returns a type name and never the value, so this can be called on the real
    secret and its result can go straight into a log line.
    """
    if value is None or not str(value).strip():
        return "absent"
    text = str(value).strip()
    if looks_like_jwt(text):
        return "app-jwt"
    for prefix, kind in PREFIXES:
        if text.startswith(prefix):
            return kind
    if len(text) == 40 and all(c in "0123456789abcdef" for c in text.lower()):
        return "legacy-pat"
    return "unknown"


def parse_authorization(header):
    """Split an Authorization header into a scheme and whether a value follows.

    Pure. The value is never returned: nothing downstream has a reason to hold
    it, and every structure that does is another copy of the secret.
    """
    if header is None:
        return {"scheme": None, "has_credential": False, "words": 0}
    words = str(header).split()
    if not words:
        return {"scheme": None, "has_credential": False, "words": 0}
    if len(words) == 1:
        return {"scheme": None, "has_credential": True, "words": 1}
    return {"scheme": words[0], "has_credential": True, "words": len(words)}


def check_pairing(scheme, kind):
    """Decide whether a scheme word and a credential type belong together. Pure.

    Returns (state, detail, repair). Five of the seven states are decided
    without a request, which is the point: this is a startup assertion, not an
    incident tool.
    """
    word = (scheme or "").lower()
    if kind == "absent":
        return ("no-credential",
                "there is no credential to pair a scheme with. The variable "
                "holding it is empty or unset.",
                "set the credential in the environment and read it from there")
    if word == "basic":
        return ("basic-scheme",
                "Basic is a retired mechanism for this API. It fails for a "
                "reason that has nothing to do with which credential you hold.",
                "send Authorization: Bearer with the token instead of Basic")
    if scheme is None:
        return ("scheme-missing",
                "the header carries a bare value with no word in front of it. "
                "GitHub cannot tell what it is being offered and refuses it "
                "with the same message a dead token gets.",
                "prefix the value with Bearer and a single space")
    if word not in ("bearer", "token"):
        return ("unknown-scheme",
                "%s is not a scheme this API reads. Only Bearer and the legacy "
                "token word are accepted." % scheme,
                "replace the scheme word with Bearer")
    if kind == "refresh-token":
        return ("refresh-token-sent",
                "a refresh token is not an API credential under any scheme. It "
                "is exchanged for a user token, and that result is what goes "
                "on the wire.",
                "exchange the refresh token first, then send what comes back")
    if kind == "app-jwt" and word == "token":
        return ("jwt-with-token-scheme",
                "an App JWT is only read under Bearer. Under the token word it "
                "is refused with the generic bad credentials message, which "
                "names the credential and hides the envelope.",
                "change the word token to Bearer and send the same JWT")
    if word == "token":
        return ("legacy-scheme-accepted",
                "the token word still works for this credential type, so "
                "nothing is failing because of it today. It is the older "
                "spelling, and it is the one that breaks when the same code "
                "path later carries a JWT.",
                "move this helper to Bearer for every credential type")
    return ("bearer-ok",
            "Bearer is correct for this credential type, so the envelope is "
            "not the problem. If the call still fails, the credential itself "
            "is the subject.",
            "none")


def explain_401(message):
    """Map GitHub's short set of authentication messages onto causes. Pure."""
    text = (message or "").strip().lower().rstrip(".")
    for needle, result in MESSAGES:
        if needle in text:
            return result
    return ("unmapped-message",
            "not one of the sentences GitHub uses for an authentication "
            "failure, so read it literally rather than through this table.")


def get(path, scheme, token):
    """One GET under one scheme word. Returns (status, message)."""
    url = API + path if path.startswith("/") else path
    response = requests.get(url, timeout=30, headers={
        "Authorization": "%s %s" % (scheme, token),
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": UA,
    })
    try:
        body = response.json()
    except ValueError:
        body = None
    return response.status_code, (body.get("message")
                                  if isinstance(body, dict) else None)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--path", default="/user",
                    help="the API path that was refused")
    ap.add_argument("--scheme", default="token",
                    help="the scheme word your client currently sends")
    ap.add_argument("--offline", action="store_true",
                    help="do the pairing check and send nothing at all")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    kind = credential_kind(token)
    if kind == "absent":
        log.error("set GITHUB_TOKEN. There is no credential to pair a scheme "
                  "with, which is its own answer but not this one")
        return 2

    header = parse_authorization("%s %s" % (args.scheme, token))
    state, detail, repair = check_pairing(header["scheme"], kind)

    log.info("credential type: %s", kind)
    log.info("scheme word:     %s", header["scheme"] or "none, a bare value")
    log.info("accepted words:  %s", ", ".join(ACCEPTS.get(kind, ())) or "none")
    log.info("%s: %s", state, detail)

    result = {"path": args.path, "credential_type": kind,
              "scheme": header["scheme"], "state": state}

    if not args.offline:
        configured = get(args.path, args.scheme, token)
        log.info("as configured (%s):  %d %s", args.scheme, configured[0],
                 configured[1] or "")
        if configured[0] == 401:
            cause, why = explain_401(configured[1])
            log.info("  %s: %s", cause, why)
        result["configured"] = {"scheme": args.scheme, "status": configured[0],
                                "message": configured[1]}

        if args.scheme.lower() != "bearer":
            recommended = get(args.path, "Bearer", token)
            log.info("as recommended (Bearer): %d %s", recommended[0],
                     recommended[1] or "")
            result["recommended"] = {"scheme": "Bearer",
                                     "status": recommended[0],
                                     "message": recommended[1]}
            if recommended[0] != configured[0]:
                log.info("the scheme word alone changed the outcome, which is "
                         "as close to proof as this gets")
            elif configured[0] >= 400:
                log.info("both words failed identically, so the envelope is "
                         "innocent. Look at the credential itself, the "
                         "account it belongs to, or the endpoint's own rules")

    if repair != "none":
        log.info("repair: %s", repair)
    print(json.dumps(result, indent=2))
    return 1 if state in ("jwt-with-token-scheme", "scheme-missing",
                          "unknown-scheme", "basic-scheme",
                          "refresh-token-sent") else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-auth-scheme.mjs",
"js": '''/**
 * Check the Authorization scheme word against the shape of the credential.
 *
 * Read only. The diagnosis is local: a credential announces its own type in
 * its first few characters, so the pairing is decided before a socket opens.
 * The only network work is two GETs to the same path differing in one word.
 *
 * The credential value is never printed, logged or returned. Only its type is.
 */
const API = 'https://api.github.com';
const UA = 'github-auth-scheme/1.0 (+https://example.com/contact)';

/** GitHub's prefixed credential formats. */
export const PREFIXES = [
  ['github_pat_', 'fine-grained-pat'],
  ['ghp_', 'classic-pat'],
  ['gho_', 'oauth-user-token'],
  ['ghu_', 'user-to-server-token'],
  ['ghs_', 'installation-token'],
  ['ghr_', 'refresh-token'],
];

/** What each credential type accepts in front of it, lowercased. */
export const ACCEPTS = {
  'app-jwt': ['bearer'],
  'classic-pat': ['bearer', 'token'],
  'fine-grained-pat': ['bearer', 'token'],
  'oauth-user-token': ['bearer', 'token'],
  'user-to-server-token': ['bearer', 'token'],
  'installation-token': ['bearer', 'token'],
  'legacy-pat': ['bearer', 'token'],
  'refresh-token': [],
  unknown: ['bearer', 'token'],
  absent: [],
};

const B64URL = /^[A-Za-z0-9_=-]+$/;

/**
 * Recognise a JWT by shape alone. Pure.
 * The payload is deliberately not decoded: what the claims say is a different
 * question and a different note.
 */
export function looksLikeJwt(value) {
  if (!value) return false;
  const parts = String(value).split('.');
  if (parts.length !== 3 || parts.some((p) => !p)) return false;
  if (!parts.every((p) => B64URL.test(p))) return false;
  return parts[0].startsWith('eyJ');
}

/** Name a credential's type from its own text. Pure. Never returns the value. */
export function credentialKind(value) {
  if (value === null || value === undefined || !String(value).trim()) return 'absent';
  const text = String(value).trim();
  if (looksLikeJwt(text)) return 'app-jwt';
  for (const [prefix, kind] of PREFIXES) {
    if (text.startsWith(prefix)) return kind;
  }
  if (text.length === 40 && /^[0-9a-f]+$/.test(text.toLowerCase())) return 'legacy-pat';
  return 'unknown';
}

/** Split an Authorization header into a scheme and whether a value follows. Pure. */
export function parseAuthorization(header) {
  if (header === null || header === undefined) {
    return { scheme: null, hasCredential: false, words: 0 };
  }
  const words = String(header).split(/\\s+/).filter(Boolean);
  if (!words.length) return { scheme: null, hasCredential: false, words: 0 };
  if (words.length === 1) return { scheme: null, hasCredential: true, words: 1 };
  return { scheme: words[0], hasCredential: true, words: words.length };
}

/** Decide whether a scheme word and a credential type belong together. Pure. */
export function checkPairing(scheme, kind) {
  const word = String(scheme ?? '').toLowerCase();
  if (kind === 'absent') {
    return ['no-credential',
      'there is no credential to pair a scheme with. The variable holding it ' +
      'is empty or unset.',
      'set the credential in the environment and read it from there'];
  }
  if (word === 'basic') {
    return ['basic-scheme',
      'Basic is a retired mechanism for this API. It fails for a reason that ' +
      'has nothing to do with which credential you hold.',
      'send Authorization: Bearer with the token instead of Basic'];
  }
  if (scheme === null || scheme === undefined) {
    return ['scheme-missing',
      'the header carries a bare value with no word in front of it. GitHub ' +
      'cannot tell what it is being offered and refuses it with the same ' +
      'message a dead token gets.',
      'prefix the value with Bearer and a single space'];
  }
  if (word !== 'bearer' && word !== 'token') {
    return ['unknown-scheme',
      `${scheme} is not a scheme this API reads. Only Bearer and the legacy ` +
      'token word are accepted.',
      'replace the scheme word with Bearer'];
  }
  if (kind === 'refresh-token') {
    return ['refresh-token-sent',
      'a refresh token is not an API credential under any scheme. It is ' +
      'exchanged for a user token, and that result is what goes on the wire.',
      'exchange the refresh token first, then send what comes back'];
  }
  if (kind === 'app-jwt' && word === 'token') {
    return ['jwt-with-token-scheme',
      'an App JWT is only read under Bearer. Under the token word it is ' +
      'refused with the generic bad credentials message, which names the ' +
      'credential and hides the envelope.',
      'change the word token to Bearer and send the same JWT'];
  }
  if (word === 'token') {
    return ['legacy-scheme-accepted',
      'the token word still works for this credential type, so nothing is ' +
      'failing because of it today. It is the older spelling, and it is the ' +
      'one that breaks when the same code path later carries a JWT.',
      'move this helper to Bearer for every credential type'];
  }
  return ['bearer-ok',
    'Bearer is correct for this credential type, so the envelope is not the ' +
    'problem. If the call still fails, the credential itself is the subject.',
    'none'];
}

/** The short set of sentences GitHub uses for an authentication failure. */
export const MESSAGES = [
  ['a json web token could not be decoded',
    ['jwt-expected',
      'the endpoint wanted an App JWT and got something that is not one. That ' +
      'is a credential type mismatch rather than a scheme one, and it is the ' +
      'helpful failure: it names its subject.']],
  ['requires authentication',
    ['nothing-arrived',
      'no Authorization header reached GitHub at all, so the scheme word is ' +
      'not the question yet. Something between your process and GitHub ' +
      'dropped the header.']],
  ['bad credentials',
    ['received-and-refused',
      'GitHub parsed something and did not accept it. A JWT under the token ' +
      'word produces exactly this, and so does a dead token, so the message ' +
      'alone does not separate them.']],
];

/** Map GitHub's authentication messages onto causes. Pure. */
export function explain401(message) {
  const text = String(message ?? '').trim().toLowerCase().replace(/\\.+$/, '');
  for (const [needle, result] of MESSAGES) {
    if (text.includes(needle)) return result;
  }
  return ['unmapped-message',
    'not one of the sentences GitHub uses for an authentication failure, so ' +
    'read it literally rather than through this table.'];
}

async function get(path, scheme, token) {
  const url = path.startsWith('/') ? API + path : path;
  const res = await fetch(url, {
    headers: {
      Authorization: `${scheme} ${token}`,
      Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      'User-Agent': UA,
    },
  });
  let body = null;
  try { body = await res.json(); } catch { body = null; }
  return [res.status, body && typeof body === 'object' ? body.message ?? null : null];
}

function arg(name, fallback) {
  const i = process.argv.indexOf(name);
  return i === -1 ? fallback : process.argv[i + 1];
}

async function main() {
  const path = arg('--path', '/user');
  const scheme = arg('--scheme', 'token');
  const offline = process.argv.includes('--offline');

  const token = process.env.GITHUB_TOKEN;
  const kind = credentialKind(token);
  if (kind === 'absent') {
    console.error('set GITHUB_TOKEN. There is no credential to pair a scheme ' +
      'with, which is its own answer but not this one');
    process.exitCode = 2;
    return;
  }

  const header = parseAuthorization(`${scheme} ${token}`);
  const [state, detail, repair] = checkPairing(header.scheme, kind);

  console.log(`credential type: ${kind}`);
  console.log(`scheme word:     ${header.scheme ?? 'none, a bare value'}`);
  console.log(`accepted words:  ${(ACCEPTS[kind] ?? []).join(', ') || 'none'}`);
  console.log(`${state}: ${detail}`);

  const result = { path, credentialType: kind, scheme: header.scheme, state };

  if (!offline) {
    const [status, message] = await get(path, scheme, token);
    console.log(`as configured (${scheme}):  ${status} ${message ?? ''}`);
    if (status === 401) {
      const [cause, why] = explain401(message);
      console.log(`  ${cause}: ${why}`);
    }
    result.configured = { scheme, status, message };

    if (scheme.toLowerCase() !== 'bearer') {
      const [status2, message2] = await get(path, 'Bearer', token);
      console.log(`as recommended (Bearer): ${status2} ${message2 ?? ''}`);
      result.recommended = { scheme: 'Bearer', status: status2, message: message2 };
      if (status2 !== status) {
        console.log('the scheme word alone changed the outcome, which is as ' +
          'close to proof as this gets');
      } else if (status >= 400) {
        console.log('both words failed identically, so the envelope is ' +
          'innocent. Look at the credential itself, the account it belongs ' +
          "to, or the endpoint's own rules");
      }
    }
  }

  if (repair !== 'none') console.log(`repair: ${repair}`);
  console.log(JSON.stringify(result, null, 2));
  process.exitCode = ['jwt-with-token-scheme', 'scheme-missing', 'unknown-scheme',
    'basic-scheme', 'refresh-token-sent'].includes(state) ? 1 : 0;
}

// Only run when invoked directly, so importing this module from the test file
// does not fire live requests and set an exit code the suite then inherits.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Every fixture below is a shape rather than a secret: obviously fake stand-ins a few characters long, because the functions only ever look at prefixes and segment counts. That is what makes the whole diagnosis testable without a live App, and it is also the argument for running it as a startup assertion rather than as an incident tool.",
"test_py_file": "test_github_auth_scheme.py",
"test_py": '''from github_auth_scheme import (
    check_pairing, credential_kind, explain_401, looks_like_jwt,
    parse_authorization,
)

FAKE_JWT = "eyJhbG.eyJpc3M.sig"


def test_a_jwt_is_recognised_by_shape_without_being_decoded():
    assert looks_like_jwt(FAKE_JWT) is True
    assert looks_like_jwt("eyJhbG.eyJpc3M") is False
    assert looks_like_jwt("eyJhbG..sig") is False
    assert looks_like_jwt("not.a.jwt") is False
    assert looks_like_jwt("") is False


def test_each_prefix_names_its_credential_type():
    assert credential_kind("ghp_fake") == "classic-pat"
    assert credential_kind("gho_fake") == "oauth-user-token"
    assert credential_kind("ghu_fake") == "user-to-server-token"
    assert credential_kind("ghs_fake") == "installation-token"
    assert credential_kind("ghr_fake") == "refresh-token"
    assert credential_kind("github_pat_fk") == "fine-grained-pat"


def test_a_jwt_wins_over_the_prefix_table():
    assert credential_kind(FAKE_JWT) == "app-jwt"


def test_the_unprefixed_legacy_shape_is_still_recognised():
    assert credential_kind("0" * 40) == "legacy-pat"
    assert credential_kind("something-else") == "unknown"
    assert credential_kind(None) == "absent"
    assert credential_kind("   ") == "absent"


def test_a_bare_value_has_no_scheme():
    assert parse_authorization("ghp_fake")["scheme"] is None
    assert parse_authorization("ghp_fake")["has_credential"] is True


def test_a_scheme_and_a_value_are_split_on_whitespace():
    parsed = parse_authorization("Bearer  ghp_fake")
    assert parsed["scheme"] == "Bearer"
    assert parsed["words"] == 2


def test_an_absent_header_is_not_an_empty_one():
    assert parse_authorization(None)["has_credential"] is False
    assert parse_authorization("")["has_credential"] is False


def test_a_jwt_under_the_token_word_is_the_headline_failure():
    state, detail, repair = check_pairing("token", "app-jwt")
    assert state == "jwt-with-token-scheme"
    assert "Bearer" in detail
    assert "Bearer" in repair


def test_a_jwt_under_bearer_is_fine():
    assert check_pairing("Bearer", "app-jwt")[0] == "bearer-ok"


def test_the_scheme_word_is_read_case_insensitively():
    assert check_pairing("bearer", "app-jwt")[0] == "bearer-ok"
    assert check_pairing("TOKEN", "app-jwt")[0] == "jwt-with-token-scheme"


def test_a_pat_under_the_legacy_word_works_and_is_still_reported():
    state, detail, _ = check_pairing("token", "classic-pat")
    assert state == "legacy-scheme-accepted"
    assert "nothing is failing because of it today" in detail


def test_a_bare_value_is_its_own_state():
    assert check_pairing(None, "classic-pat")[0] == "scheme-missing"


def test_basic_is_sent_to_the_other_note():
    assert check_pairing("Basic", "classic-pat")[0] == "basic-scheme"


def test_an_unread_scheme_word_is_named():
    state, detail, _ = check_pairing("OAuth", "classic-pat")
    assert state == "unknown-scheme"
    assert "OAuth" in detail


def test_a_refresh_token_is_not_an_api_credential():
    assert check_pairing("Bearer", "refresh-token")[0] == "refresh-token-sent"


def test_no_credential_is_not_a_scheme_problem():
    assert check_pairing("Bearer", "absent")[0] == "no-credential"


def test_the_specific_messages_beat_the_generic_one():
    assert explain_401("A JSON web token could not be decoded.")[0] == "jwt-expected"
    assert explain_401("Requires authentication")[0] == "nothing-arrived"
    assert explain_401("Bad credentials")[0] == "received-and-refused"


def test_an_unfamiliar_message_is_admitted_rather_than_guessed():
    assert explain_401("Something else entirely")[0] == "unmapped-message"
    assert explain_401(None)[0] == "unmapped-message"
''',
"test_js_file": "github-auth-scheme.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  checkPairing, credentialKind, explain401, looksLikeJwt, parseAuthorization,
} from './github-auth-scheme.mjs';

const FAKE_JWT = 'eyJhbG.eyJpc3M.sig';

test('a jwt is recognised by shape without being decoded', () => {
  assert.equal(looksLikeJwt(FAKE_JWT), true);
  assert.equal(looksLikeJwt('eyJhbG.eyJpc3M'), false);
  assert.equal(looksLikeJwt('eyJhbG..sig'), false);
  assert.equal(looksLikeJwt('not.a.jwt'), false);
  assert.equal(looksLikeJwt(''), false);
});

test('each prefix names its credential type', () => {
  assert.equal(credentialKind('ghp_fake'), 'classic-pat');
  assert.equal(credentialKind('gho_fake'), 'oauth-user-token');
  assert.equal(credentialKind('ghu_fake'), 'user-to-server-token');
  assert.equal(credentialKind('ghs_fake'), 'installation-token');
  assert.equal(credentialKind('ghr_fake'), 'refresh-token');
  assert.equal(credentialKind('github_pat_fk'), 'fine-grained-pat');
});

test('a jwt wins over the prefix table', () => {
  assert.equal(credentialKind(FAKE_JWT), 'app-jwt');
});

test('the unprefixed legacy shape is still recognised', () => {
  assert.equal(credentialKind('0'.repeat(40)), 'legacy-pat');
  assert.equal(credentialKind('something-else'), 'unknown');
  assert.equal(credentialKind(null), 'absent');
  assert.equal(credentialKind('   '), 'absent');
});

test('a bare value has no scheme', () => {
  assert.equal(parseAuthorization('ghp_fake').scheme, null);
  assert.equal(parseAuthorization('ghp_fake').hasCredential, true);
});

test('a scheme and a value are split on whitespace', () => {
  const parsed = parseAuthorization('Bearer  ghp_fake');
  assert.equal(parsed.scheme, 'Bearer');
  assert.equal(parsed.words, 2);
});

test('an absent header is not an empty one', () => {
  assert.equal(parseAuthorization(null).hasCredential, false);
  assert.equal(parseAuthorization('').hasCredential, false);
});

test('a jwt under the token word is the headline failure', () => {
  const [state, detail, repair] = checkPairing('token', 'app-jwt');
  assert.equal(state, 'jwt-with-token-scheme');
  assert.ok(detail.includes('Bearer'));
  assert.ok(repair.includes('Bearer'));
});

test('a jwt under bearer is fine', () => {
  assert.equal(checkPairing('Bearer', 'app-jwt')[0], 'bearer-ok');
});

test('the scheme word is read case insensitively', () => {
  assert.equal(checkPairing('bearer', 'app-jwt')[0], 'bearer-ok');
  assert.equal(checkPairing('TOKEN', 'app-jwt')[0], 'jwt-with-token-scheme');
});

test('a pat under the legacy word works and is still reported', () => {
  const [state, detail] = checkPairing('token', 'classic-pat');
  assert.equal(state, 'legacy-scheme-accepted');
  assert.ok(detail.includes('nothing is failing because of it today'));
});

test('a bare value is its own state', () => {
  assert.equal(checkPairing(null, 'classic-pat')[0], 'scheme-missing');
});

test('basic is sent to the other note', () => {
  assert.equal(checkPairing('Basic', 'classic-pat')[0], 'basic-scheme');
});

test('an unread scheme word is named', () => {
  const [state, detail] = checkPairing('OAuth', 'classic-pat');
  assert.equal(state, 'unknown-scheme');
  assert.ok(detail.includes('OAuth'));
});

test('a refresh token is not an api credential', () => {
  assert.equal(checkPairing('Bearer', 'refresh-token')[0], 'refresh-token-sent');
});

test('no credential is not a scheme problem', () => {
  assert.equal(checkPairing('Bearer', 'absent')[0], 'no-credential');
});

test('the specific messages beat the generic one', () => {
  assert.equal(explain401('A JSON web token could not be decoded.')[0], 'jwt-expected');
  assert.equal(explain401('Requires authentication')[0], 'nothing-arrived');
  assert.equal(explain401('Bad credentials')[0], 'received-and-refused');
});

test('an unfamiliar message is admitted rather than guessed', () => {
  assert.equal(explain401('Something else entirely')[0], 'unmapped-message');
  assert.equal(explain401(null)[0], 'unmapped-message');
});
''',
"faq": [
 ("Is token deprecated, or does it still work?",
  "It still works, for the credential types it always covered: personal access tokens, OAuth user tokens and installation access tokens. GitHub's current documentation writes Bearer everywhere, and Bearer is accepted for all of those too, so there is no case where token is the only thing that works and one important case where it is the thing that fails. Treat it as a spelling to migrate away from rather than an error to panic about, and migrate it in the helper that builds the header rather than at each call site."),
 ("Why does a JWT under token give the same message as a dead token?",
  "Because GitHub is deliberately unhelpful about credentials it will not accept. Bad credentials is what you get whenever something was received in the Authorization header and refused, and it is identical for a refused JWT, an expired token, a truncated value and a token from a different account. That is a security property rather than an oversight, and it is why the diagnosis has to come from the shape of what you sent rather than from what came back."),
 ("Can I tell what kind of credential I am holding without calling the API?",
  "Yes, for anything minted since GitHub introduced prefixed token formats. ghp_ is a classic personal access token, gho_ an OAuth user token, ghu_ a user-to-server token, ghs_ an installation access token, ghr_ a refresh token, and github_pat_ a fine-grained personal access token. A JWT is three dot-separated base64url segments starting eyJ. The one gap is the old unprefixed forty-character hexadecimal token, which is recognisable by shape but says nothing about its own type."),
 ("The header has the right word and the call still fails. What now?",
  "Then the envelope is innocent and the subject is the credential, the identity behind it, or the endpoint. Run the pair anyway: two identical failures under two different words is a real result and it rules out this whole page in one step. After that the questions are whether the credential is alive at all, whether it belongs to the account you think it does, and whether the endpoint accepts that credential type, and each of those is a separate check."),
 ("Should I ever send Authorization without a scheme word at all?",
  "No. A bare value in the header is not a shorthand that GitHub tolerates; it is refused with the same message a dead credential gets, which makes it one of the more expensive typos available. It usually arrives through string formatting: a template that lost its prefix, a configuration value that was supposed to include the word and did not, or two layers that each assume the other adds it. Asserting on the parsed scheme at startup costs nothing and catches all three."),
],
"related": [
 ("/github/bad-credentials-401/", "401 Bad credentials on every endpoint"),
 ("/github/basic-auth-password-removed/", "A username and password sent to the API"),
 ("/github/token-in-query-string/", "The token passed as a query parameter"),
],
"citations": [CITE_AUTHENTICATING, CITE_JWT, CITE_APP_AUTH, CITE_TROUBLESHOOT],
},

{
"slug": "unused-classic-token-auto-revoked",
"title": "A classic token nobody used for a year is deleted for you",
"description": "GitHub removes classic tokens after a year of disuse, and that class emits no expiry header. The only clock is how often your own job exercises it.",
"h1": "a classic token nobody used for a year is deleted for you",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github token removed for inactivity", "classic pat deleted after a year",
             "github personal access token unused revoked",
             "github token keep alive rate_limit", "github credential liveness check"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The restore drill is on a Tuesday morning and the token that has been sitting in the vault since the runbook was written answers <code>401</code>. It has not expired, because it was created with no expiry. Nobody revoked it. It is not in the account's token list at all, because GitHub removed it for going a year without being used, and the reason it went a year without being used is that it is a token for emergencies.",
"short_answer": """<p>GitHub deletes classic personal access tokens that have not been used for a year. There is no warning header, no notification and nothing in the API to read, because the only credential class this applies to is also the class that never carried an expiry to count down.</p>
<p>So the clock cannot come from GitHub, and it does not have to. It comes from your side: for each stored credential, how often does something actually exercise it? Subtract that from the one-year window and you have the margin. A daily job has 364 days of it. A quarterly job has 274. An annual disaster-recovery drill has none, and the token backing it is going to be gone the next time it matters.</p>
<p>The repair is a probe that doubles as a keep-alive. <code>GET /rate_limit</code> costs no quota, needs no scope and counts as a use, so a scheduled call per credential both proves the credential still works and stops the reaper reaching it. The script below runs that probe across a manifest of credentials and prints the schedule it would take to keep each one alive.</p>""",
"problem": """<p>What makes this one nasty is the correlation. The credentials most likely to be reaped are the credentials reserved for the moments you can least afford to be without them: break-glass access, a restore path, an annual compliance export, a failover script that has never once had to run. Frequency of use is inversely related to importance here, and the policy is indexed on frequency.</p>
<p>It also fails silently in a way that expiry does not. An expiring token has a date on it, so somebody at some point wrote that date on a calendar or a dashboard. A classic token created with <em>no expiration</em> looks permanent, is documented as permanent, and is treated as permanent by every runbook that mentions it. The dormancy rule is the one clock nobody set, and it starts running the moment the token stops being used.</p>
<p>Then the recovery is worse than a rotation. A token that expired can be reissued from the same place with the same settings and the person who created it can usually be found. A token that was reaped is gone from the list entirely, which means there is often no record of what scopes it had, which account it belonged to, or who created it &mdash; and you are reconstructing all of that during the incident the token existed for.</p>""",
"why": """<p><strong>The API cannot tell you when a credential was last used.</strong> Not for a token you hold, and certainly not for the others on the account: a read-only credential cannot enumerate an account's tokens at all. So there is no endpoint to poll for this and no header to watch. The measurement has to be made on your side, out of something you already know, which is the schedule of the jobs that use each credential.</p>
<p><strong>Only one credential class is reapable.</strong> Fine-grained personal access tokens carry an expiry by default and are governed by that date. Installation access tokens live for an hour. OAuth user tokens die when somebody <a href="/github/oauth-token-revoked-by-user/">revokes the authorization</a>, which is a decision rather than a clock. The dormancy rule is about classic personal access tokens created without an expiry, and the script's first job is to say whether the credential in front of it is even in that class.</p>
<p><strong>The absent header is the tell.</strong> A credential that reports <code>github-authentication-token-expiration</code> has a date, and the countdown on that date is <a href="/github/token-expiring-soon/">a different note</a> with a different repair. A credential that reports nothing is the one this page is about. That is a clean split: the tokens whose death you can see coming in a header are exactly the tokens that dormancy cannot take, and the tokens dormancy can take announce nothing at all.</p>
<p><strong>The probe is free and it is also the fix.</strong> <code>GET /rate_limit</code> does not consume quota, requires no scope, and is a use of the credential. So a monthly scheduled call per credential is both the monitoring and the mitigation, which is unusual enough to be worth stating plainly: there is no separate remediation to build.</p>
<p><strong>The probe has to run on its own schedule.</strong> This is the part that gets implemented wrong. A liveness check inside the annual job runs annually, which is the interval that caused the problem. The probe belongs in something that runs on its own cadence and touches every stored credential, including the ones no running job currently uses.</p>""",
"steps": [
 {"h": "Write down every credential and the cadence that exercises it",
  "body": """<p>One line each: the environment variable it lives in, what uses it, and how often that runs. This is the input the API cannot supply and the reason this check is a five-minute conversation rather than a monitoring integration. Include the credentials nothing currently uses, which are the ones at risk.</p>"""},
 {"h": "Probe each one with a call that costs nothing",
  "body": """<p><code>GET /rate_limit</code> is free of quota and needs no scope, so it works for the narrowest credential you own. A 200 says the credential is alive today. A 401 says it is already gone, and for this class of token there is nothing to un-revoke.</p>"""},
 {"h": "Read the expiry header to decide whether dormancy even applies",
  "body": """<p>If <code>github-authentication-token-expiration</code> comes back, the credential has a date and a different note owns it. If it does not, and the value looks like a classic token, it is in the reapable class and the margin calculation is the next step.</p>"""},
 {"h": "Subtract the cadence from the window and look at the margin",
  "body": """<p>A year minus the exercise interval. Zero or less means the reaper wins by definition. Under about two months means one skipped run, one paused pipeline or one quiet quarter loses the race. Anything else is covered by the job itself and needs nothing.</p>"""},
 {"h": "Schedule the probe separately from the job it protects",
  "body": """<p>Monthly is enough, and it is twelve free requests a year per credential. Put it somewhere that runs on its own cadence, give it the whole manifest, and alert on the 401 rather than on the margin &mdash; the margin is what you fix in advance, the 401 is what you never want to see.</p>"""},
],
"verify": """<p>Run it against the manifest. The state to look for is not a failure, it is the annual credential with no margin, which is reported while everything is still working.</p>
<pre><code class="language-bash">python3 github_token_dormancy.py --manifest credentials.json
# GITHUB_TOKEN        nightly sync           covered        margin 364d
# EXPORT_TOKEN        quarterly export       covered        margin 274d
# DR_RESTORE_TOKEN    annual restore drill   reap-race-lost margin 0d
#   repair: probe this credential every 30 days. GET /rate_limit costs no
#   quota, needs no scope, and counts as a use, so the probe is the fix.
#   crontab: 0 6 1 * *</code></pre>""",
"code_intro": "One free request per credential, and the arithmetic that matters happens without any. The pure half is a class test that decides whether a credential is even reapable, a margin calculation against the one-year window, a state machine over the probe result and the cadence, and a recommendation that turns a cadence into a crontab line. The manifest is the only input the API cannot provide, which is why it is a file you write rather than something the script discovers.",
"py_file": "github_token_dormancy.py",
"py": '''"""Say which stored credentials will be reaped for disuse before they are needed.

Read only, and free: one GET /rate_limit per credential, which consumes no
quota and requires no scope. That call is also the mitigation, because it
counts as a use, so running this on a schedule is both the monitoring and the
repair. Nothing here mints, rotates or revokes anything.

GitHub removes classic personal access tokens that have gone a year without
being used. That class of credential carries no expiry and emits no header, so
the clock cannot come from the API. It comes from the manifest: how often each
credential is actually exercised by the job that owns it.

Manifest format, a JSON list:

    [{"env": "GITHUB_TOKEN", "label": "nightly sync",
      "exercised_every_days": 1},
     {"env": "DR_RESTORE_TOKEN", "label": "annual restore drill",
      "exercised_every_days": 365}]
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_token_dormancy")

API = "https://api.github.com"
UA = "github-token-dormancy/1.0 (+https://example.com/contact)"

# The published dormancy window, and the margin below which one skipped run
# loses the race. Both are arguments rather than constants at the call sites
# so a stricter shop can tighten them without editing the logic.
WINDOW_DAYS = 365
TIGHT_DAYS = 60


def token_class(value):
    """Name the credential class from its prefix. Pure. Never returns the value."""
    if value is None or not str(value).strip():
        return "absent"
    text = str(value).strip()
    if text.startswith("github_pat_"):
        return "fine-grained"
    if text.startswith("ghp_"):
        return "classic"
    if text.startswith("ghs_"):
        return "installation"
    if text.startswith("gho_") or text.startswith("ghu_"):
        return "oauth"
    if len(text) == 40 and all(c in "0123456789abcdef" for c in text.lower()):
        return "classic"
    return "unknown"


def reap_exposure(kind, expires_header):
    """Decide whether a credential is even in the class the reaper can take. Pure.

    The header check comes first and wins. A credential that reports an expiry
    has a date, and a date is a different clock with a different note attached
    to it; dormancy cannot reach it.
    """
    if expires_header:
        return ("not-reapable-expiring",
                "this credential reports an expiry, so it dies on a date "
                "rather than from disuse. The countdown on that date is a "
                "different check.")
    if kind == "classic":
        return ("reapable",
                "a classic token with no expiry reported. This is the only "
                "class GitHub removes for disuse, and it emits no header to "
                "warn you.")
    if kind == "fine-grained":
        return ("not-reapable-fine-grained",
                "fine-grained tokens carry an expiry by default, so they are "
                "governed by a date even when this request did not show one.")
    if kind == "installation":
        return ("not-reapable-short-lived",
                "an installation access token lives about an hour. It is "
                "minted per run and dormancy is meaningless for it.")
    if kind == "oauth":
        return ("not-reapable-oauth",
                "an OAuth user token dies when somebody revokes the "
                "authorization, which is a decision rather than a clock.")
    return ("unknown-class",
            "the credential does not match a known prefix, so its class "
            "cannot be named from its text. Treat it as reapable until "
            "somebody confirms otherwise.")


def margin_days(interval_days, window_days=WINDOW_DAYS):
    """Days of headroom between one use and the reaping window. Pure.

    None when the cadence is unknown, because guessing here produces a
    confident wrong answer about a credential nobody is watching.
    """
    try:
        interval = float(interval_days)
    except (TypeError, ValueError):
        return None
    return window_days - interval


def dormancy_state(probe_status, exposure, interval_days,
                   window_days=WINDOW_DAYS, tight_days=TIGHT_DAYS):
    """Turn a probe result and an exercise cadence into a finding. Pure."""
    if probe_status == 401:
        return ("already-gone",
                "the credential is refused. For this class there is nothing "
                "to un-revoke: mint a replacement and record what it is for.")
    if probe_status is None or probe_status >= 400:
        return ("unreachable",
                "the probe did not come back cleanly, so nothing can be said "
                "about the credential yet. Fix the probe first.")
    if exposure != "reapable" and exposure != "unknown-class":
        return ("not-reapable",
                "alive, and not in the class that gets reaped for disuse.")
    margin = margin_days(interval_days, window_days)
    if margin is None:
        return ("cadence-unknown",
                "alive, and reapable, but the manifest does not say how often "
                "anything exercises it. That is the number this check needs.")
    if margin <= 0:
        return ("reap-race-lost",
                "alive today, and nothing exercises it inside the window. "
                "This credential will be removed before it is next needed.")
    if margin < tight_days:
        return ("reap-race-tight",
                "alive, with less headroom than one skipped run. A paused "
                "pipeline or a quiet quarter loses this race.")
    return ("covered",
            "alive, and exercised often enough that the job itself keeps the "
            "credential from going dormant.")


def probe_interval(interval_days, window_days=WINDOW_DAYS):
    """Recommend a keep-alive cadence in days. Pure.

    At most thirty days, because a monthly probe leaves eleven months of
    margin and costs twelve free requests a year. Never slower than the job it
    protects, because a probe slower than the job adds nothing to it.
    """
    try:
        interval = float(interval_days)
    except (TypeError, ValueError):
        interval = float(window_days)
    return int(max(1, min(30.0, interval)))


def keepalive_cron(days):
    """A crontab line for a keep-alive at the given cadence. Pure."""
    if days <= 1:
        return "0 6 * * *"
    if days <= 7:
        return "0 6 * * 1"
    return "0 6 1 * *"


def probe(token):
    """One free GET. Returns (status, expiry header or None)."""
    response = requests.get(API + "/rate_limit", timeout=30, headers={
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": UA,
    })
    headers = {k.lower(): v for k, v in response.headers.items()}
    return response.status_code, headers.get("github-authentication-token-expiration")


def load_manifest(path):
    """Read the manifest, or build a one-entry one from the environment."""
    if path:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    return [{"env": "GITHUB_TOKEN", "label": "the credential in GITHUB_TOKEN",
             "exercised_every_days": None}]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest",
                    help="JSON list of {env, label, exercised_every_days}")
    ap.add_argument("--window-days", type=int, default=WINDOW_DAYS,
                    help="the dormancy window to measure against")
    ap.add_argument("--tight-days", type=int, default=TIGHT_DAYS,
                    help="margin below which one skipped run loses the race")
    args = ap.parse_args()

    entries = load_manifest(args.manifest)
    findings = []
    for entry in entries:
        name = entry.get("env", "")
        label = entry.get("label", name)
        cadence = entry.get("exercised_every_days")
        token = os.environ.get(name)
        if not token:
            log.warning("%-20s %-24s no value in the environment", name, label)
            findings.append({"env": name, "state": "not-set"})
            continue

        kind = token_class(token)
        status, expires = probe(token)
        exposure, exposure_detail = reap_exposure(kind, expires)
        state, detail = dormancy_state(status, exposure, cadence,
                                       args.window_days, args.tight_days)
        margin = margin_days(cadence, args.window_days)
        log.info("%-20s %-24s %-16s margin %s", name, label, state,
                 "%dd" % margin if margin is not None else "unknown")
        log.info("    class %s: %s", kind, exposure_detail)
        log.info("    %s", detail)

        if state in ("reap-race-lost", "reap-race-tight", "cadence-unknown"):
            every = probe_interval(cadence, args.window_days)
            log.info("    repair: probe this credential every %d days. "
                     "GET /rate_limit costs no quota, needs no scope, and "
                     "counts as a use, so the probe is the fix.", every)
            log.info("    crontab: %s", keepalive_cron(every))
            log.info("    repair: schedule it separately from the job that "
                     "owns the credential. A check inside an annual job runs "
                     "annually, which is the interval that caused this.")
        if state == "already-gone":
            log.info("    repair: mint a replacement, then record its purpose "
                     "and owner somewhere the next drill will find them.")

        findings.append({"env": name, "label": label, "class": kind,
                         "exposure": exposure, "status": status,
                         "margin_days": margin, "state": state})

    print(json.dumps(findings, indent=2))
    bad = {"reap-race-lost", "reap-race-tight", "already-gone"}
    return 1 if any(f.get("state") in bad for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-token-dormancy.mjs",
"js": '''/**
 * Say which stored credentials will be reaped for disuse before they are needed.
 *
 * Read only, and free: one GET /rate_limit per credential, which consumes no
 * quota and requires no scope. That call is also the mitigation, because it
 * counts as a use of the credential.
 *
 * GitHub removes classic personal access tokens that have gone a year without
 * being used. That class carries no expiry and emits no header, so the clock
 * comes from the manifest rather than from the API.
 */
import { readFileSync } from 'node:fs';

const API = 'https://api.github.com';
const UA = 'github-token-dormancy/1.0 (+https://example.com/contact)';

export const WINDOW_DAYS = 365;
export const TIGHT_DAYS = 60;

/** Name the credential class from its prefix. Pure. Never returns the value. */
export function tokenClass(value) {
  if (value === null || value === undefined || !String(value).trim()) return 'absent';
  const text = String(value).trim();
  if (text.startsWith('github_pat_')) return 'fine-grained';
  if (text.startsWith('ghp_')) return 'classic';
  if (text.startsWith('ghs_')) return 'installation';
  if (text.startsWith('gho_') || text.startsWith('ghu_')) return 'oauth';
  if (text.length === 40 && /^[0-9a-f]+$/.test(text.toLowerCase())) return 'classic';
  return 'unknown';
}

/** Decide whether a credential is in the class the reaper can take. Pure. */
export function reapExposure(kind, expiresHeader) {
  if (expiresHeader) {
    return ['not-reapable-expiring',
      'this credential reports an expiry, so it dies on a date rather than ' +
      'from disuse. The countdown on that date is a different check.'];
  }
  if (kind === 'classic') {
    return ['reapable',
      'a classic token with no expiry reported. This is the only class ' +
      'GitHub removes for disuse, and it emits no header to warn you.'];
  }
  if (kind === 'fine-grained') {
    return ['not-reapable-fine-grained',
      'fine-grained tokens carry an expiry by default, so they are governed ' +
      'by a date even when this request did not show one.'];
  }
  if (kind === 'installation') {
    return ['not-reapable-short-lived',
      'an installation access token lives about an hour. It is minted per ' +
      'run and dormancy is meaningless for it.'];
  }
  if (kind === 'oauth') {
    return ['not-reapable-oauth',
      'an OAuth user token dies when somebody revokes the authorization, ' +
      'which is a decision rather than a clock.'];
  }
  return ['unknown-class',
    'the credential does not match a known prefix, so its class cannot be ' +
    'named from its text. Treat it as reapable until somebody confirms ' +
    'otherwise.'];
}

/** Days of headroom between one use and the reaping window. Pure. */
export function marginDays(intervalDays, windowDays = WINDOW_DAYS) {
  const interval = Number(intervalDays);
  if (intervalDays === null || intervalDays === undefined
      || intervalDays === '' || Number.isNaN(interval)) return null;
  return windowDays - interval;
}

/** Turn a probe result and an exercise cadence into a finding. Pure. */
export function dormancyState(probeStatus, exposure, intervalDays,
  windowDays = WINDOW_DAYS, tightDays = TIGHT_DAYS) {
  if (probeStatus === 401) {
    return ['already-gone',
      'the credential is refused. For this class there is nothing to ' +
      'un-revoke: mint a replacement and record what it is for.'];
  }
  if (probeStatus === null || probeStatus === undefined || probeStatus >= 400) {
    return ['unreachable',
      'the probe did not come back cleanly, so nothing can be said about ' +
      'the credential yet. Fix the probe first.'];
  }
  if (exposure !== 'reapable' && exposure !== 'unknown-class') {
    return ['not-reapable',
      'alive, and not in the class that gets reaped for disuse.'];
  }
  const margin = marginDays(intervalDays, windowDays);
  if (margin === null) {
    return ['cadence-unknown',
      'alive, and reapable, but the manifest does not say how often anything ' +
      'exercises it. That is the number this check needs.'];
  }
  if (margin <= 0) {
    return ['reap-race-lost',
      'alive today, and nothing exercises it inside the window. This ' +
      'credential will be removed before it is next needed.'];
  }
  if (margin < tightDays) {
    return ['reap-race-tight',
      'alive, with less headroom than one skipped run. A paused pipeline or ' +
      'a quiet quarter loses this race.'];
  }
  return ['covered',
    'alive, and exercised often enough that the job itself keeps the ' +
    'credential from going dormant.'];
}

/** Recommend a keep-alive cadence in days. Pure. */
export function probeInterval(intervalDays, windowDays = WINDOW_DAYS) {
  let interval = Number(intervalDays);
  if (intervalDays === null || intervalDays === undefined
      || intervalDays === '' || Number.isNaN(interval)) interval = windowDays;
  return Math.trunc(Math.max(1, Math.min(30, interval)));
}

/** A crontab line for a keep-alive at the given cadence. Pure. */
export function keepaliveCron(days) {
  if (days <= 1) return '0 6 * * *';
  if (days <= 7) return '0 6 * * 1';
  return '0 6 1 * *';
}

async function probe(token) {
  const res = await fetch(`${API}/rate_limit`, {
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      'User-Agent': UA,
    },
  });
  return [res.status, res.headers.get('github-authentication-token-expiration')];
}

function arg(name, fallback) {
  const i = process.argv.indexOf(name);
  return i === -1 ? fallback : process.argv[i + 1];
}

async function main() {
  const manifestPath = arg('--manifest', null);
  const entries = manifestPath
    ? JSON.parse(readFileSync(manifestPath, 'utf8'))
    : [{ env: 'GITHUB_TOKEN', label: 'the credential in GITHUB_TOKEN', exercised_every_days: null }];

  const findings = [];
  for (const entry of entries) {
    const name = entry.env ?? '';
    const label = entry.label ?? name;
    const cadence = entry.exercised_every_days ?? null;
    const token = process.env[name];
    if (!token) {
      console.warn(`${name.padEnd(20)} ${String(label).padEnd(24)} no value in the environment`);
      findings.push({ env: name, state: 'not-set' });
      continue;
    }

    const kind = tokenClass(token);
    const [status, expires] = await probe(token);
    const [exposure, exposureDetail] = reapExposure(kind, expires);
    const [state, detail] = dormancyState(status, exposure, cadence);
    const margin = marginDays(cadence);
    console.log(`${name.padEnd(20)} ${String(label).padEnd(24)} ${state.padEnd(16)} `
      + `margin ${margin === null ? 'unknown' : `${margin}d`}`);
    console.log(`    class ${kind}: ${exposureDetail}`);
    console.log(`    ${detail}`);

    if (state === 'reap-race-lost' || state === 'reap-race-tight' || state === 'cadence-unknown') {
      const every = probeInterval(cadence);
      console.log(`    repair: probe this credential every ${every} days. `
        + 'GET /rate_limit costs no quota, needs no scope, and counts as a '
        + 'use, so the probe is the fix.');
      console.log(`    crontab: ${keepaliveCron(every)}`);
      console.log('    repair: schedule it separately from the job that owns '
        + 'the credential. A check inside an annual job runs annually, which '
        + 'is the interval that caused this.');
    }
    if (state === 'already-gone') {
      console.log('    repair: mint a replacement, then record its purpose and '
        + 'owner somewhere the next drill will find them.');
    }

    findings.push({ env: name, label, class: kind, exposure, status, marginDays: margin, state });
  }

  console.log(JSON.stringify(findings, null, 2));
  const bad = ['reap-race-lost', 'reap-race-tight', 'already-gone'];
  process.exitCode = findings.some((f) => bad.includes(f.state)) ? 1 : 0;
}

// Only run when invoked directly, so importing this module from the test file
// does not fire live requests and set an exit code the suite then inherits.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The arithmetic is the part worth pinning, because the whole finding is one subtraction and the interesting cases are the boundaries: exactly a year, one day inside it, an unknown cadence that must not be guessed at, and a credential whose expiry header takes it out of scope entirely. None of it needs a token, and the fixtures that stand in for one are four characters long.",
"test_py_file": "test_github_token_dormancy.py",
"test_py": '''from github_token_dormancy import (
    dormancy_state, keepalive_cron, margin_days, probe_interval, reap_exposure,
    token_class,
)


def test_each_prefix_names_its_class():
    assert token_class("ghp_fake") == "classic"
    assert token_class("github_pat_fk") == "fine-grained"
    assert token_class("ghs_fake") == "installation"
    assert token_class("gho_fake") == "oauth"
    assert token_class("ghu_fake") == "oauth"
    assert token_class("0" * 40) == "classic"
    assert token_class("something") == "unknown"
    assert token_class(None) == "absent"


def test_an_expiry_header_takes_a_credential_out_of_scope():
    state, detail = reap_exposure("classic", "2026-09-30 12:00:00 UTC")
    assert state == "not-reapable-expiring"
    assert "different check" in detail


def test_a_classic_token_with_no_expiry_is_the_reapable_class():
    assert reap_exposure("classic", None)[0] == "reapable"


def test_the_other_classes_die_of_other_causes():
    assert reap_exposure("fine-grained", None)[0] == "not-reapable-fine-grained"
    assert reap_exposure("installation", None)[0] == "not-reapable-short-lived"
    assert reap_exposure("oauth", None)[0] == "not-reapable-oauth"
    assert reap_exposure("unknown", None)[0] == "unknown-class"


def test_margin_is_the_window_minus_the_cadence():
    assert margin_days(1) == 364
    assert margin_days(90) == 275
    assert margin_days(365) == 0


def test_an_unknown_cadence_is_not_guessed_at():
    assert margin_days(None) is None
    assert margin_days("sometimes") is None


def test_an_annual_job_has_lost_the_race_before_it_starts():
    state, detail = dormancy_state(200, "reapable", 365)
    assert state == "reap-race-lost"
    assert "before it is next needed" in detail


def test_one_day_inside_the_window_is_still_tight():
    assert dormancy_state(200, "reapable", 364)[0] == "reap-race-tight"


def test_a_frequent_job_keeps_its_own_credential_alive():
    assert dormancy_state(200, "reapable", 1)[0] == "covered"
    assert dormancy_state(200, "reapable", 90)[0] == "covered"


def test_a_reaped_credential_is_already_gone():
    state, detail = dormancy_state(401, "reapable", 1)
    assert state == "already-gone"
    assert "nothing to un-revoke" in detail


def test_a_credential_out_of_scope_is_reported_as_such():
    assert dormancy_state(200, "not-reapable-expiring", 365)[0] == "not-reapable"


def test_an_unknown_class_is_treated_as_reapable():
    assert dormancy_state(200, "unknown-class", 365)[0] == "reap-race-lost"


def test_a_missing_cadence_is_its_own_state():
    state, detail = dormancy_state(200, "reapable", None)
    assert state == "cadence-unknown"
    assert "how often" in detail


def test_a_broken_probe_says_nothing_about_the_credential():
    assert dormancy_state(500, "reapable", 1)[0] == "unreachable"
    assert dormancy_state(None, "reapable", 1)[0] == "unreachable"


def test_the_probe_is_never_slower_than_a_month():
    assert probe_interval(365) == 30
    assert probe_interval(90) == 30
    assert probe_interval(7) == 7
    assert probe_interval(1) == 1


def test_an_unknown_cadence_gets_the_monthly_probe():
    assert probe_interval(None) == 30


def test_the_cadence_becomes_a_crontab_line():
    assert keepalive_cron(1) == "0 6 * * *"
    assert keepalive_cron(7) == "0 6 * * 1"
    assert keepalive_cron(30) == "0 6 1 * *"
''',
"test_js_file": "github-token-dormancy.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  dormancyState, keepaliveCron, marginDays, probeInterval, reapExposure,
  tokenClass,
} from './github-token-dormancy.mjs';

test('each prefix names its class', () => {
  assert.equal(tokenClass('ghp_fake'), 'classic');
  assert.equal(tokenClass('github_pat_fk'), 'fine-grained');
  assert.equal(tokenClass('ghs_fake'), 'installation');
  assert.equal(tokenClass('gho_fake'), 'oauth');
  assert.equal(tokenClass('ghu_fake'), 'oauth');
  assert.equal(tokenClass('0'.repeat(40)), 'classic');
  assert.equal(tokenClass('something'), 'unknown');
  assert.equal(tokenClass(null), 'absent');
});

test('an expiry header takes a credential out of scope', () => {
  const [state, detail] = reapExposure('classic', '2026-09-30 12:00:00 UTC');
  assert.equal(state, 'not-reapable-expiring');
  assert.ok(detail.includes('different check'));
});

test('a classic token with no expiry is the reapable class', () => {
  assert.equal(reapExposure('classic', null)[0], 'reapable');
});

test('the other classes die of other causes', () => {
  assert.equal(reapExposure('fine-grained', null)[0], 'not-reapable-fine-grained');
  assert.equal(reapExposure('installation', null)[0], 'not-reapable-short-lived');
  assert.equal(reapExposure('oauth', null)[0], 'not-reapable-oauth');
  assert.equal(reapExposure('unknown', null)[0], 'unknown-class');
});

test('margin is the window minus the cadence', () => {
  assert.equal(marginDays(1), 364);
  assert.equal(marginDays(90), 275);
  assert.equal(marginDays(365), 0);
});

test('an unknown cadence is not guessed at', () => {
  assert.equal(marginDays(null), null);
  assert.equal(marginDays('sometimes'), null);
});

test('an annual job has lost the race before it starts', () => {
  const [state, detail] = dormancyState(200, 'reapable', 365);
  assert.equal(state, 'reap-race-lost');
  assert.ok(detail.includes('before it is next needed'));
});

test('one day inside the window is still tight', () => {
  assert.equal(dormancyState(200, 'reapable', 364)[0], 'reap-race-tight');
});

test('a frequent job keeps its own credential alive', () => {
  assert.equal(dormancyState(200, 'reapable', 1)[0], 'covered');
  assert.equal(dormancyState(200, 'reapable', 90)[0], 'covered');
});

test('a reaped credential is already gone', () => {
  const [state, detail] = dormancyState(401, 'reapable', 1);
  assert.equal(state, 'already-gone');
  assert.ok(detail.includes('nothing to un-revoke'));
});

test('a credential out of scope is reported as such', () => {
  assert.equal(dormancyState(200, 'not-reapable-expiring', 365)[0], 'not-reapable');
});

test('an unknown class is treated as reapable', () => {
  assert.equal(dormancyState(200, 'unknown-class', 365)[0], 'reap-race-lost');
});

test('a missing cadence is its own state', () => {
  const [state, detail] = dormancyState(200, 'reapable', null);
  assert.equal(state, 'cadence-unknown');
  assert.ok(detail.includes('how often'));
});

test('a broken probe says nothing about the credential', () => {
  assert.equal(dormancyState(500, 'reapable', 1)[0], 'unreachable');
  assert.equal(dormancyState(null, 'reapable', 1)[0], 'unreachable');
});

test('the probe is never slower than a month', () => {
  assert.equal(probeInterval(365), 30);
  assert.equal(probeInterval(90), 30);
  assert.equal(probeInterval(7), 7);
  assert.equal(probeInterval(1), 1);
});

test('an unknown cadence gets the monthly probe', () => {
  assert.equal(probeInterval(null), 30);
});

test('the cadence becomes a crontab line', () => {
  assert.equal(keepaliveCron(1), '0 6 * * *');
  assert.equal(keepaliveCron(7), '0 6 * * 1');
  assert.equal(keepaliveCron(30), '0 6 1 * *');
});
''',
"faq": [
 ("Which tokens does GitHub actually remove for inactivity?",
  "Classic personal access tokens that have gone a year without being used. Fine-grained personal access tokens are governed by the expiry date they are created with, installation access tokens for GitHub Apps live about an hour and are minted per run, and OAuth user tokens end when somebody revokes the authorization rather than when they go quiet. So the exposure is narrow, but it lands on exactly the credential type people reach for when they want something that never expires."),
 ("Can I ask the API when a token was last used?",
  "No. A read-only credential can read its own scopes and its own account, and it cannot enumerate the tokens on that account or see when any of them were last exercised. That is why this check takes a manifest: the cadence at which each credential is used is something you know and the API does not. The one thing the API will tell you is whether the credential works right now, which is the probe."),
 ("Does GET /rate_limit really count as using the token?",
  "It is an authenticated request made with that credential, which is what the dormancy rule counts. It is also the cheapest request available: it does not consume any of your hourly quota, it needs no scope at all, and it works for the narrowest credential you own. That combination is unusual enough to build on, because it means the monitoring and the mitigation are the same call and there is no separate remediation to write."),
 ("Should I just add an expiry to everything instead?",
  "Mostly yes, and it changes which problem you have rather than removing it. A credential with an expiry announces itself through a response header, which makes the countdown visible and automatable, and it converts an unbounded leak into a bounded one. It also means somebody has to rotate on a schedule. The genuinely bad option is the one this note is about: a credential with no expiry, no header and no scheduled use, which looks permanent right up to the moment it is not."),
 ("How do I tell a reaped token from an expired or revoked one?",
  "Usually you cannot, from the response. All three answer 401 Bad credentials, because GitHub does not explain refusals. The discriminator is the record you kept rather than anything that came back: a token with an expiry date died on a date you could have predicted, a token somebody revoked has an audit entry, and a token that is simply absent from the account's list with neither of those explanations went dormant. Which is why the useful work is the margin calculation, done a year before the 401."),
],
"related": [
 ("/github/token-expiring-soon/", "The token expires in days and nobody is watching"),
 ("/github/classic-pat-expired/", "A classic PAT passed its expiry date"),
 ("/github/over-scoped-token/", "A token that can delete repositories"),
],
"citations": [CITE_PATS, CITE_RATE_LIMIT_ENDPOINT, CITE_AUTHENTICATING, CITE_CREDS_SECURE],
},

{
"slug": "oauth-token-revoked-by-user",
"title": "One user revoked your app and only their token is dead",
"description": "A single 401 among healthy tokens is a revocation, not an outage. Read the population: one dead token is that person, every token dead at once is you.",
"h1": "one user revoked your app and only their token is dead",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github oauth token revoked", "github oauth 401 one user",
             "github revoke application authorization", "github oauth token lifetime",
             "reauthorize github oauth app user"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "One customer's sync has been failing since Thursday. Everybody else is fine. The token has not expired, because OAuth user tokens do not expire; nothing was deployed; the error is <code>401 Bad credentials</code> and the retry loop has been dutifully re-attempting it every fifteen minutes for four days. The user clicked <em>Revoke</em> on a settings page you will never see.",
"short_answer": """<p>Stop reading the failing request and read the population. Probe every stored user token with <code>GET /user</code> and count the answers. <strong>One refusal among many successes</strong> is that individual's revocation, and the only repair is asking that person to authorize again. <strong>Every token refused at once</strong> is not about the users at all &mdash; it is your application: a rotated client secret, a suspended app, or an organization owner revoking the authorization for everyone in one action.</p>
<p>The second thing to fix is the retry policy. A revoked user token never recovers on its own, so every retry against it is guaranteed waste, and a fleet of dead connections retried on a schedule is a reliable way to trip <a href="/github/secondary-limit-concurrency/">a secondary limit</a> for the users who are still working. Treat a 401 on a stored user token as terminal: mark the connection broken, stop the schedule, and prompt for a fresh authorization.</p>""",
"problem": """<p>It presents as a transient failure, and it is the opposite of one. Re-running the OAuth flow fixes it instantly, which teaches everyone that the token was "stale" and that reconnecting is a routine remedy. So the retry loop stays, the alert stays a warning, and nothing in the system ever records that a user made a decision about your access.</p>
<p>Nothing tells you either. A classic OAuth App receives no notification when somebody revokes its authorization; the token simply stops working on the next call. There is no expiry to watch, no webhook to subscribe to and no field to poll, so the first evidence is a failure somewhere downstream, usually in whichever job happened to touch that user next.</p>
<p>And the two causes look identical from inside a single request. A 401 on one connection is a person; a 401 on one connection is also what your application looks like in the ninety seconds after somebody rotates the client secret, if that connection is the only one you happened to try. The information that separates them does not exist in any one response. It only exists across the set.</p>""",
"why": """<p><strong>OAuth user tokens have no expiry to blame.</strong> Unless your app has opted into expiring user-to-server tokens, a user token issued through the web flow keeps working indefinitely. So "it expired" is not available as an explanation, and everything that kills such a token is somebody's decision: the user's, an organization owner's, or yours.</p>
<p><strong>Revocation is immediate and it is not announced.</strong> The moment a user removes the authorization from their settings, every token issued under it stops being accepted. There is no grace period and no notification to the integration. A GitHub App that uses user-to-server tokens does get told, through a <code>github_app_authorization</code> webhook with the <code>revoked</code> action; a classic OAuth App does not, which is exactly why a probe has to exist.</p>
<p><strong>An organization owner can revoke for everyone at once.</strong> If the app was authorized against an organization with third-party access restrictions, an owner removing that approval invalidates the whole cohort in one action. That is the case that looks like an outage and gets escalated as one, and the population reading is what distinguishes it from a client-secret rotation in the same minute.</p>
<p><strong>The definitive check needs application credentials, not a user token.</strong> There is an endpoint that lets an OAuth App ask about a specific token using its own client id and secret, and it answers cleanly for a revoked one. It is a write-shaped call and it wants a secret this section's scripts do not hold, so the probe here uses <code>GET /user</code> per token instead. That costs one request against each user's own quota, which is worth stating rather than hiding.</p>
<p><strong>A 401 on a stored user token is terminal.</strong> This is the operational conclusion and it is worth more than the diagnosis. Retrying cannot help, backing off cannot help, and a schedule that keeps trying converts one broken connection into a permanent stream of refusals that competes with the users who are still working.</p>""",
"steps": [
 {"h": "Gather every stored user token from the environment",
  "body": """<p>One variable per connection, named so they can be collected by prefix. Never a literal in the source and never a value in a log line: the report names the variable and the login, which are the two things a human can act on.</p>"""},
 {"h": "Probe each one with GET /user and record the login",
  "body": """<p>A 200 names the account the token belongs to, which is also the cheapest way to notice a connection that is alive but attached to the wrong person. A 401 is the finding. Do this for the whole set, not just the one that failed.</p>"""},
 {"h": "Read the counts before you read any single result",
  "body": """<p>Some dead and some alive is individual revocation. All dead is the application. Exactly one token stored and it is dead is genuinely inconclusive, and the script says so rather than picking the more likely answer, because the two repairs go to different people.</p>"""},
 {"h": "Mark the broken connections terminal and stop retrying them",
  "body": """<p>Not a longer backoff, an off switch. Set the connection's state to needs-reauthorization, remove it from the schedule and surface it in whatever the user actually looks at. The failure is not going to resolve itself and the retries are competing for quota with the users who are fine.</p>"""},
 {"h": "Send the affected people back through the authorization flow",
  "body": """<p>The script prints the authorize URL with your client id and the scopes you need. That is the entire repair for the individual case; there is nothing to fix on your side, and the sooner the person sees the prompt the shorter the outage they experience.</p>"""},
],
"verify": """<p>The output is a census. The line that matters is the verdict at the bottom, because it is the one that decides who gets contacted: one person, or everybody.</p>
<pre><code class="language-bash">python3 github_user_token_liveness.py --env-prefix GH_USER_TOKEN_
# GH_USER_TOKEN_ALICE    alive     alice-dev
# GH_USER_TOKEN_BEN      rejected  -
# GH_USER_TOKEN_CHO      alive     cho-ops
# individual-revocation: 1 of 3 stored tokens is refused while others work,
#   so this is that person's decision rather than an application problem.
# GH_USER_TOKEN_BEN: terminal. Stop retrying and ask for a fresh authorization:
#   https://github.com/login/oauth/authorize?client_id=Iv1.example&scope=repo</code></pre>""",
"code_intro": "One GET per stored token, and the diagnosis is in the counting rather than in any single response. The pure half is a collector that pulls tokens out of a mapping by prefix without ever returning them anywhere else, a classifier for one probe, the population reading that turns a set of results into a cause, a disposition function that says which states are worth retrying, and a builder for the authorization URL. Nothing writes, and the one endpoint that would answer this definitively is named and deliberately not called.",
"py_file": "github_user_token_liveness.py",
"py": '''"""Tell an individual OAuth revocation apart from an application wide one.

Read only. One GET /user per stored user token, which is the cheapest call
that answers "is this credential still accepted, and whose is it". Nothing here
mints, refreshes or revokes anything; the repair is a URL that is printed for
the affected person to open.

The reading is a population, not a request. One refusal among many successes is
that user's revocation. Every refusal at once is the application: a rotated
client secret, a suspended app, or an organization owner removing the approval
for a whole cohort. No single response can tell those apart.

The definitive per-token check lives at /applications/{client_id}/token, which
is a write shaped call needing the client secret. This section's scripts do not
hold application secrets and do not make that call.
"""
import argparse
import json
import logging
import os
import sys
from urllib.parse import urlencode

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_user_token_liveness")

API = "https://api.github.com"
UA = "github-user-token-liveness/1.0 (+https://example.com/contact)"
AUTHORIZE = "https://github.com/login/oauth/authorize"


def collect_tokens(environ, prefix):
    """Gather stored user tokens out of a mapping by prefix. Pure.

    Values leave here only to be sent. Everything the report prints is the
    variable name and the login, which are the two things a person can act on
    and neither of which is a secret.
    """
    return sorted((name, value) for name, value in environ.items()
                  if name.startswith(prefix) and value)


def token_result(status, message=None):
    """Classify one liveness probe. Pure.

    Four states, because a 403 is not a revocation: it is an account or an
    organization refusing something the credential is otherwise entitled to
    present, and it does not mean the authorization is gone.
    """
    if status == 200:
        return "alive"
    if status == 401:
        return "rejected"
    if status == 403:
        return "forbidden"
    return "error"


def population_verdict(results):
    """Read the fleet rather than the request. Pure.

    results: [(name, state), ...]. The counts are the diagnosis; no individual
    response contains this information.
    """
    if not results:
        return ("no-tokens",
                "nothing was collected, so there is nothing to read. Check the "
                "prefix the variables are named with.")
    alive = [n for n, s in results if s == "alive"]
    rejected = [n for n, s in results if s == "rejected"]
    if not rejected:
        return ("all-healthy",
                "every stored token is accepted, so no authorization has been "
                "revoked. Whatever you are chasing is somewhere else.")
    if len(results) == 1:
        return ("single-token-inconclusive",
                "one token is stored and it is refused. That is consistent "
                "with this user revoking, and equally consistent with the "
                "application being suspended or its secret rotated. With one "
                "sample the two cannot be separated.")
    if alive:
        return ("individual-revocation",
                "%d of %d stored tokens are refused while others work, so this "
                "is those people's decision rather than an application "
                "problem: %s" % (len(rejected), len(results),
                                 ", ".join(rejected)))
    return ("application-wide",
            "all %d stored tokens are refused at once. Users do not coordinate "
            "revocations. Look at the application: a rotated client secret, a "
            "suspended app, or an organization owner removing the approval for "
            "the whole cohort." % len(results))


def retry_disposition(state):
    """Say whether a state should ever be retried. Pure.

    The operationally valuable half of this note. A revoked user token does not
    recover, so a schedule that keeps trying turns one broken connection into a
    permanent stream of refusals competing with the users who still work.
    """
    if state == "rejected":
        return ("terminal",
                "a revoked or invalid user token never recovers on its own. "
                "Mark the connection broken, take it off the schedule, and ask "
                "the person to authorize again.")
    if state == "forbidden":
        return ("terminal",
                "the credential was accepted and the action was refused. "
                "Retrying changes nothing; this is an access question.")
    if state == "error":
        return ("retryable",
                "the probe itself did not complete, so nothing is known about "
                "the credential. This one is worth trying again.")
    return ("none", "nothing to retry.")


def authorize_url(client_id, scopes=(), redirect_uri=None, state=None):
    """Build the URL that starts the authorization flow again. Pure.

    This is the whole repair for an individual revocation: there is nothing to
    fix on your side, only a person to ask.
    """
    params = [("client_id", client_id)]
    if scopes:
        params.append(("scope", " ".join(scopes)))
    if redirect_uri:
        params.append(("redirect_uri", redirect_uri))
    if state:
        params.append(("state", state))
    return AUTHORIZE + "?" + urlencode(params)


def probe(token):
    """One GET /user. Returns (status, login, message)."""
    response = requests.get(API + "/user", timeout=30, headers={
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": UA,
    })
    try:
        body = response.json()
    except ValueError:
        body = None
    if isinstance(body, dict):
        return response.status_code, body.get("login"), body.get("message")
    return response.status_code, None, None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--env-prefix", default="GH_USER_TOKEN_",
                    help="collect every environment variable with this prefix")
    ap.add_argument("--scopes", default="",
                    help="space separated scopes for the printed authorize URL")
    args = ap.parse_args()

    stored = collect_tokens(os.environ, args.env_prefix)
    if not stored:
        log.error("no variables found with the prefix %s. Store one token per "
                  "connection so the set can be read as a set", args.env_prefix)
        return 2

    client_id = os.environ.get("GITHUB_OAUTH_CLIENT_ID", "")
    results, findings = [], []
    for name, token in stored:
        status, login, message = probe(token)
        state = token_result(status, message)
        results.append((name, state))
        log.info("%-24s %-9s %s", name, state, login or "-")
        findings.append({"env": name, "state": state, "login": login,
                         "status": status})

    verdict, detail = population_verdict(results)
    log.info("%s: %s", verdict, detail)

    for name, state in results:
        if state == "alive":
            continue
        disposition, why = retry_disposition(state)
        log.info("%s: %s. %s", name, disposition, why)

    if verdict in ("individual-revocation", "single-token-inconclusive"):
        if client_id:
            url = authorize_url(client_id,
                                args.scopes.split() if args.scopes else ())
            log.info("repair: send the affected people through the flow again: "
                     "%s", url)
        else:
            log.info("repair: set GITHUB_OAUTH_CLIENT_ID to have the authorize "
                     "URL printed here.")
    if verdict == "application-wide":
        log.info("repair: this is not the users. Check whether the client "
                 "secret was rotated, whether the application is suspended, "
                 "and whether an organization owner removed its approval.")

    print(json.dumps({"verdict": verdict, "tokens": findings}, indent=2))
    return 1 if verdict != "all-healthy" else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-user-token-liveness.mjs",
"js": '''/**
 * Tell an individual OAuth revocation apart from an application wide one.
 *
 * Read only. One GET /user per stored user token. Nothing here mints,
 * refreshes or revokes anything; the repair is a URL printed for the affected
 * person to open.
 *
 * The reading is a population, not a request. One refusal among many successes
 * is that user's decision. Every refusal at once is the application. No single
 * response can tell those apart.
 *
 * The definitive per-token check lives at /applications/{client_id}/token,
 * which is a write shaped call needing the client secret. This script does not
 * hold application secrets and does not make that call.
 */
const API = 'https://api.github.com';
const UA = 'github-user-token-liveness/1.0 (+https://example.com/contact)';
const AUTHORIZE = 'https://github.com/login/oauth/authorize';

/** Gather stored user tokens out of a mapping by prefix. Pure. */
export function collectTokens(environ, prefix) {
  return Object.entries(environ ?? {})
    .filter(([name, value]) => name.startsWith(prefix) && value)
    .sort(([a], [b]) => a.localeCompare(b));
}

/** Classify one liveness probe. Pure. A 403 is not a revocation. */
export function tokenResult(status) {
  if (status === 200) return 'alive';
  if (status === 401) return 'rejected';
  if (status === 403) return 'forbidden';
  return 'error';
}

/** Read the fleet rather than the request. Pure. */
export function populationVerdict(results) {
  if (!results || !results.length) {
    return ['no-tokens',
      'nothing was collected, so there is nothing to read. Check the prefix ' +
      'the variables are named with.'];
  }
  const alive = results.filter(([, s]) => s === 'alive').map(([n]) => n);
  const rejected = results.filter(([, s]) => s === 'rejected').map(([n]) => n);
  if (!rejected.length) {
    return ['all-healthy',
      'every stored token is accepted, so no authorization has been revoked. ' +
      'Whatever you are chasing is somewhere else.'];
  }
  if (results.length === 1) {
    return ['single-token-inconclusive',
      'one token is stored and it is refused. That is consistent with this ' +
      'user revoking, and equally consistent with the application being ' +
      'suspended or its secret rotated. With one sample the two cannot be ' +
      'separated.'];
  }
  if (alive.length) {
    return ['individual-revocation',
      `${rejected.length} of ${results.length} stored tokens are refused ` +
      'while others work, so this is those people\\'s decision rather than an ' +
      `application problem: ${rejected.join(', ')}`];
  }
  return ['application-wide',
    `all ${results.length} stored tokens are refused at once. Users do not ` +
    'coordinate revocations. Look at the application: a rotated client ' +
    'secret, a suspended app, or an organization owner removing the approval ' +
    'for the whole cohort.'];
}

/** Say whether a state should ever be retried. Pure. */
export function retryDisposition(state) {
  if (state === 'rejected') {
    return ['terminal',
      'a revoked or invalid user token never recovers on its own. Mark the ' +
      'connection broken, take it off the schedule, and ask the person to ' +
      'authorize again.'];
  }
  if (state === 'forbidden') {
    return ['terminal',
      'the credential was accepted and the action was refused. Retrying ' +
      'changes nothing; this is an access question.'];
  }
  if (state === 'error') {
    return ['retryable',
      'the probe itself did not complete, so nothing is known about the ' +
      'credential. This one is worth trying again.'];
  }
  return ['none', 'nothing to retry.'];
}

/** Build the URL that starts the authorization flow again. Pure. */
export function authorizeUrl(clientId, scopes = [], redirectUri = null, state = null) {
  const params = new URLSearchParams([['client_id', clientId]]);
  if (scopes && scopes.length) params.append('scope', scopes.join(' '));
  if (redirectUri) params.append('redirect_uri', redirectUri);
  if (state) params.append('state', state);
  return `${AUTHORIZE}?${params.toString()}`;
}

async function probe(token) {
  const res = await fetch(`${API}/user`, {
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      'User-Agent': UA,
    },
  });
  let body = null;
  try { body = await res.json(); } catch { body = null; }
  const login = body && typeof body === 'object' ? body.login ?? null : null;
  return [res.status, login];
}

function arg(name, fallback) {
  const i = process.argv.indexOf(name);
  return i === -1 ? fallback : process.argv[i + 1];
}

async function main() {
  const prefix = arg('--env-prefix', 'GH_USER_TOKEN_');
  const scopes = arg('--scopes', '');

  const stored = collectTokens(process.env, prefix);
  if (!stored.length) {
    console.error(`no variables found with the prefix ${prefix}. Store one ` +
      'token per connection so the set can be read as a set');
    process.exitCode = 2;
    return;
  }

  const clientId = process.env.GITHUB_OAUTH_CLIENT_ID ?? '';
  const results = [];
  const findings = [];
  for (const [name, token] of stored) {
    const [status, login] = await probe(token);
    const state = tokenResult(status);
    results.push([name, state]);
    console.log(`${name.padEnd(24)} ${state.padEnd(9)} ${login ?? '-'}`);
    findings.push({ env: name, state, login, status });
  }

  const [verdict, detail] = populationVerdict(results);
  console.log(`${verdict}: ${detail}`);

  for (const [name, state] of results) {
    if (state === 'alive') continue;
    const [disposition, why] = retryDisposition(state);
    console.log(`${name}: ${disposition}. ${why}`);
  }

  if (verdict === 'individual-revocation' || verdict === 'single-token-inconclusive') {
    if (clientId) {
      const url = authorizeUrl(clientId, scopes ? scopes.split(' ').filter(Boolean) : []);
      console.log(`repair: send the affected people through the flow again: ${url}`);
    } else {
      console.log('repair: set GITHUB_OAUTH_CLIENT_ID to have the authorize ' +
        'URL printed here.');
    }
  }
  if (verdict === 'application-wide') {
    console.log('repair: this is not the users. Check whether the client ' +
      'secret was rotated, whether the application is suspended, and whether ' +
      'an organization owner removed its approval.');
  }

  console.log(JSON.stringify({ verdict, tokens: findings }, null, 2));
  process.exitCode = verdict === 'all-healthy' ? 0 : 1;
}

// Only run when invoked directly, so importing this module from the test file
// does not fire live requests and set an exit code the suite then inherits.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The whole diagnosis is a count, so the tests are populations rather than responses: one dead among three, three dead out of three, one dead out of one, and the empty set. The last two are the ones worth being strict about, because a single stored token genuinely cannot distinguish the two causes and a script that guesses there sends the wrong person an email.",
"test_py_file": "test_github_user_token_liveness.py",
"test_py": '''from github_user_token_liveness import (
    authorize_url, collect_tokens, population_verdict, retry_disposition,
    token_result,
)

ENV = {
    "GH_USER_TOKEN_BEN": "gho_fake2",
    "GH_USER_TOKEN_ALICE": "gho_fake1",
    "GITHUB_TOKEN": "ghp_fake",
    "GH_USER_TOKEN_EMPTY": "",
}


def test_tokens_are_collected_by_prefix_and_sorted():
    found = collect_tokens(ENV, "GH_USER_TOKEN_")
    assert [name for name, _ in found] == ["GH_USER_TOKEN_ALICE",
                                           "GH_USER_TOKEN_BEN"]


def test_an_unrelated_variable_is_not_collected():
    assert all(name != "GITHUB_TOKEN" for name, _ in
               collect_tokens(ENV, "GH_USER_TOKEN_"))


def test_an_empty_value_is_not_a_stored_token():
    assert all(name != "GH_USER_TOKEN_EMPTY" for name, _ in
               collect_tokens(ENV, "GH_USER_TOKEN_"))


def test_a_403_is_not_a_revocation():
    assert token_result(200) == "alive"
    assert token_result(401) == "rejected"
    assert token_result(403) == "forbidden"
    assert token_result(500) == "error"


def test_one_refusal_among_successes_is_that_person():
    state, detail = population_verdict([("a", "alive"), ("b", "rejected"),
                                        ("c", "alive")])
    assert state == "individual-revocation"
    assert "1 of 3" in detail
    assert "b" in detail


def test_every_token_refused_at_once_is_the_application():
    state, detail = population_verdict([("a", "rejected"), ("b", "rejected"),
                                        ("c", "rejected")])
    assert state == "application-wide"
    assert "do not coordinate" in detail


def test_one_stored_token_cannot_separate_the_two_causes():
    state, detail = population_verdict([("a", "rejected")])
    assert state == "single-token-inconclusive"
    assert "cannot be separated" in detail


def test_a_healthy_fleet_says_look_elsewhere():
    assert population_verdict([("a", "alive"), ("b", "alive")])[0] == "all-healthy"


def test_an_empty_fleet_is_not_a_verdict_about_users():
    assert population_verdict([])[0] == "no-tokens"


def test_errors_alone_are_not_read_as_an_application_failure():
    assert population_verdict([("a", "error"), ("b", "error")])[0] == "all-healthy"


def test_a_revoked_token_is_terminal_rather_than_retryable():
    disposition, detail = retry_disposition("rejected")
    assert disposition == "terminal"
    assert "never recovers" in detail


def test_a_failed_probe_is_the_only_retryable_state():
    assert retry_disposition("error")[0] == "retryable"
    assert retry_disposition("forbidden")[0] == "terminal"
    assert retry_disposition("alive")[0] == "none"


def test_the_authorize_url_carries_the_client_id_and_the_scopes():
    url = authorize_url("Iv1.example", ["repo", "read:org"])
    assert url.startswith("https://github.com/login/oauth/authorize?")
    assert "client_id=Iv1.example" in url
    assert "scope=repo+read%3Aorg" in url


def test_optional_parameters_are_omitted_rather_than_sent_empty():
    url = authorize_url("Iv1.example")
    assert "scope=" not in url
    assert "redirect_uri=" not in url
    assert "state=" not in url


def test_a_redirect_and_a_state_are_encoded():
    url = authorize_url("Iv1.example", ["repo"], "https://app.example/cb", "xyz")
    assert "redirect_uri=https%3A%2F%2Fapp.example%2Fcb" in url
    assert "state=xyz" in url
''',
"test_js_file": "github-user-token-liveness.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  authorizeUrl, collectTokens, populationVerdict, retryDisposition, tokenResult,
} from './github-user-token-liveness.mjs';

const ENV = {
  GH_USER_TOKEN_BEN: 'gho_fake2',
  GH_USER_TOKEN_ALICE: 'gho_fake1',
  GITHUB_TOKEN: 'ghp_fake',
  GH_USER_TOKEN_EMPTY: '',
};

test('tokens are collected by prefix and sorted', () => {
  assert.deepEqual(collectTokens(ENV, 'GH_USER_TOKEN_').map(([n]) => n),
    ['GH_USER_TOKEN_ALICE', 'GH_USER_TOKEN_BEN']);
});

test('an unrelated variable is not collected', () => {
  assert.ok(collectTokens(ENV, 'GH_USER_TOKEN_').every(([n]) => n !== 'GITHUB_TOKEN'));
});

test('an empty value is not a stored token', () => {
  assert.ok(collectTokens(ENV, 'GH_USER_TOKEN_')
    .every(([n]) => n !== 'GH_USER_TOKEN_EMPTY'));
});

test('a 403 is not a revocation', () => {
  assert.equal(tokenResult(200), 'alive');
  assert.equal(tokenResult(401), 'rejected');
  assert.equal(tokenResult(403), 'forbidden');
  assert.equal(tokenResult(500), 'error');
});

test('one refusal among successes is that person', () => {
  const [state, detail] = populationVerdict([['a', 'alive'], ['b', 'rejected'], ['c', 'alive']]);
  assert.equal(state, 'individual-revocation');
  assert.ok(detail.includes('1 of 3'));
  assert.ok(detail.includes('b'));
});

test('every token refused at once is the application', () => {
  const [state, detail] = populationVerdict([['a', 'rejected'], ['b', 'rejected'], ['c', 'rejected']]);
  assert.equal(state, 'application-wide');
  assert.ok(detail.includes('do not coordinate'));
});

test('one stored token cannot separate the two causes', () => {
  const [state, detail] = populationVerdict([['a', 'rejected']]);
  assert.equal(state, 'single-token-inconclusive');
  assert.ok(detail.includes('cannot be separated'));
});

test('a healthy fleet says look elsewhere', () => {
  assert.equal(populationVerdict([['a', 'alive'], ['b', 'alive']])[0], 'all-healthy');
});

test('an empty fleet is not a verdict about users', () => {
  assert.equal(populationVerdict([])[0], 'no-tokens');
});

test('errors alone are not read as an application failure', () => {
  assert.equal(populationVerdict([['a', 'error'], ['b', 'error']])[0], 'all-healthy');
});

test('a revoked token is terminal rather than retryable', () => {
  const [disposition, detail] = retryDisposition('rejected');
  assert.equal(disposition, 'terminal');
  assert.ok(detail.includes('never recovers'));
});

test('a failed probe is the only retryable state', () => {
  assert.equal(retryDisposition('error')[0], 'retryable');
  assert.equal(retryDisposition('forbidden')[0], 'terminal');
  assert.equal(retryDisposition('alive')[0], 'none');
});

test('the authorize url carries the client id and the scopes', () => {
  const url = authorizeUrl('Iv1.example', ['repo', 'read:org']);
  assert.ok(url.startsWith('https://github.com/login/oauth/authorize?'));
  assert.ok(url.includes('client_id=Iv1.example'));
  assert.ok(url.includes('scope=repo+read%3Aorg'));
});

test('optional parameters are omitted rather than sent empty', () => {
  const url = authorizeUrl('Iv1.example');
  assert.ok(!url.includes('scope='));
  assert.ok(!url.includes('redirect_uri='));
  assert.ok(!url.includes('state='));
});

test('a redirect and a state are encoded', () => {
  const url = authorizeUrl('Iv1.example', ['repo'], 'https://app.example/cb', 'xyz');
  assert.ok(url.includes('redirect_uri=https%3A%2F%2Fapp.example%2Fcb'));
  assert.ok(url.includes('state=xyz'));
});
''',
"faq": [
 ("Do GitHub OAuth user tokens expire on their own?",
  "Not by default. A user token issued through the classic OAuth web flow keeps working indefinitely unless somebody ends it, which is why an expiry is never the explanation for one of these 401s. GitHub Apps can opt into expiring user-to-server tokens, which last eight hours and come with a refresh token; if you are using those, a 401 might just mean the access token aged out and the refresh flow needs to run. For a classic OAuth App there is no such possibility and the 401 is always somebody's decision."),
 ("How do I know it was the user and not my own application?",
  "Count. One refusal among several successes is that individual, because users do not coordinate revocations with each other. Every stored token refused within the same window is your side: a rotated client secret, a suspended application, or an organization owner withdrawing the approval for everyone who authorized through that organization. If you only store one token you genuinely cannot tell, and the honest thing is to check the application's own status before emailing the customer."),
 ("Is there a way to check one token without spending that user's quota?",
  "There is an endpoint for exactly this: an OAuth App can ask about a specific token by authenticating with its own client id and secret, and it answers cleanly for one that has been revoked. It is a write-shaped call and it needs an application secret, so the scripts in this section do not make it; they use GET /user per token instead, which costs one request from each user's own hourly allowance. If you already handle client secrets safely in a backend service, the dedicated endpoint is the better instrument."),
 ("Will GitHub tell me when somebody revokes?",
  "It depends what your integration is. A GitHub App receives a github_app_authorization webhook with the revoked action when a user removes their authorization, so an App can react immediately and mark the connection broken without polling anything. A classic OAuth App gets nothing at all: the token simply stops being accepted on the next call. That asymmetry is the strongest practical argument for a periodic liveness probe if you are still on an OAuth App."),
 ("Why does retrying make things worse rather than just being useless?",
  "Because the requests are not free even when they fail. A dead connection retried every fifteen minutes is ninety-six guaranteed refusals a day, and if a whole cohort was revoked at once that becomes thousands, all competing for the same limits as the users who are still working. GitHub also treats sustained bursts of failing authenticated requests as exactly the kind of traffic shape its secondary limits exist for, so a retry loop against revoked tokens can degrade the customers who did nothing."),
],
"related": [
 ("/github/bad-credentials-401/", "401 Bad credentials on every endpoint"),
 ("/github/retry-after-ignored/", "The client ignores retry-after and keeps going"),
 ("/github/secondary-limit-concurrency/", "Concurrency trips a secondary rate limit"),
],
"citations": [CITE_AUTHORIZING, CITE_REVOKING, CITE_OAUTH_APPS_API, CITE_USERS],
},

]
