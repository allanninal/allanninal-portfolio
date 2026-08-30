#!/usr/bin/env python3
"""/github/ field notes, batch W — the writing.

Four notes about a gate that sits outside the credential entirely. The section
already publishes a long shelf about tokens that are too narrow, expired,
revoked or the wrong type, and the trap with an organization-policy batch is
that it becomes a fifth way of saying "mint a better token". None of these four
is that. In all four the credential is valid, correctly scoped, and refused
anyway, because an organization has placed a condition on it that no amount of
reminting satisfies.

The first two are a pair and they are written to stay a pair. One is a
credential that was never authorized for an organization's SAML single sign-on
at all: the first call it ever makes is refused, the refusal carries a URL, and
a human authorizes it once. The other is a credential that *was* authorized and
whose session lapsed on the organization's schedule: it worked yesterday, it is
refused today, and authorizing it again fixes it until the next lapse. They
produce the same status code and the same header name, so they are separated by
the things that actually differ — the first reads a header on the refusal and
needs no privilege at all, the second reads a dated authorization record that
only an owner can see, and their repairs are "once" against "again, on a
timetable, unless you move off user tokens".

Neither of them is the omission note the section already publishes. That one
owns a 200 with organizations quietly missing from the body and the
`partial-results` form of the header. These two own outright refusals and the
`required` form. Both scripts here parse the two forms apart on purpose and
hand the other case to the other note rather than absorbing it.

The third owns a policy that blocks an application rather than a token. An
organization can decide which OAuth Apps may touch its data at all, and until an
owner approves one, every token that app ever issues is refused for that
organization while working perfectly on personal repositories. Its cruelty is
the asymmetry of visibility: the app's own author cannot see that they are
blocked, only a member of the organization can, so the script says out loud
whose hands it needs to run in.

The fourth owns a token that is waiting for a person. A fine-grained token can
be created, correctly permissioned, and completely powerless because the
organization requires an owner to approve it and nobody has. The section already
publishes the fine-grained 403 whose cause is a missing permission, and this is
not that: a missing permission fails one endpoint family everywhere, and a
pending approval fails every endpoint family in one namespace. That difference
is shaped like an owner rather than like an endpoint, and it is measurable.

Nothing here writes, and one thing more: nothing here authorizes, approves or
requests. Every note in this batch is about an approval that has not happened,
which makes it exactly the batch where a helpful tool would be tempted to
trigger one. These print the step and the URL for a person to act on, and stop.
Every script GETs, prints its read cost before it spends it, and exits.
"""

CITE_SSO_AUTHORIZE = ("Authorizing a personal access token for use with SAML single sign-on — GitHub Docs",
                      "https://docs.github.com/en/enterprise-cloud@latest/authentication/authenticating-with-saml-single-sign-on/authorizing-a-personal-access-token-for-use-with-saml-single-sign-on")
CITE_SSO_REST = ("Authenticating to the REST API with SAML single sign-on — GitHub Docs",
                 "https://docs.github.com/en/enterprise-cloud@latest/rest/overview/authenticating-to-the-rest-api")
CITE_SAML_ABOUT = ("About authentication with SAML single sign-on — GitHub Docs",
                   "https://docs.github.com/en/enterprise-cloud@latest/authentication/authenticating-with-saml-single-sign-on/about-authentication-with-saml-single-sign-on")
CITE_APP_INSTALL_AUTH = ("Authenticating as a GitHub App installation — GitHub Docs",
                         "https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/authenticating-as-a-github-app-installation")
CITE_ORGS_REST = ("Organizations — GitHub REST API",
                  "https://docs.github.com/en/rest/orgs/orgs")
CITE_SAML_ENFORCE = ("Enforcing SAML single sign-on for your organization — GitHub Docs",
                     "https://docs.github.com/en/enterprise-cloud@latest/organizations/managing-saml-single-sign-on-for-your-organization/enforcing-saml-single-sign-on-for-your-organization")
CITE_OAUTH_RESTRICTIONS = ("About OAuth app access restrictions — GitHub Docs",
                           "https://docs.github.com/en/organizations/managing-oauth-access-to-your-organizations-data/about-oauth-app-access-restrictions")
CITE_OAUTH_APPROVE = ("Approving OAuth apps for your organization — GitHub Docs",
                      "https://docs.github.com/en/organizations/managing-oauth-access-to-your-organizations-data/approving-oauth-apps-for-your-organization")
CITE_APPS_DIFFERENCES = ("Differences between GitHub Apps and OAuth apps — GitHub Docs",
                         "https://docs.github.com/en/apps/creating-github-apps/about-creating-github-apps/differences-between-github-apps-and-oauth-apps")
CITE_REST_TROUBLESHOOT = ("Troubleshooting the REST API — GitHub Docs",
                          "https://docs.github.com/en/rest/using-the-rest-api/troubleshooting-the-rest-api")
CITE_PAT_POLICY = ("Setting a personal access token policy for your organization — GitHub Docs",
                   "https://docs.github.com/en/organizations/managing-programmatic-access-to-your-organization/setting-a-personal-access-token-policy-for-your-organization")
CITE_MANAGE_PATS = ("Managing your personal access tokens — GitHub Docs",
                    "https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens")
CITE_PAT_REQUESTS_REST = ("Personal access tokens — GitHub REST API",
                          "https://docs.github.com/en/rest/orgs/personal-access-tokens")
CITE_PAT_REVIEW = ("Reviewing and revoking personal access tokens in your organization — GitHub Docs",
                   "https://docs.github.com/en/organizations/managing-programmatic-access-to-your-organization/reviewing-and-revoking-personal-access-tokens-in-your-organization")

GUIDES = [
{
"slug": "saml-token-not-authorized",
"title": "The token is valid and was never SSO-authorized for the org",
"description": "An org that enforces SAML refuses every token until a human authorizes it. The refusal carries x-github-sso: required and the URL that fixes it.",
"h1": "The token is valid and was never SSO-authorized for the org",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github resource protected by organization saml enforcement",
             "github token not authorized for organization sso",
             "x-github-sso required url header",
             "authorize personal access token saml single sign on",
             "github api 403 saml enforcement automation"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The token was minted ten minutes ago with every scope the endpoint documents. <code>GET /user</code> works. <code>GET /orgs/acme</code> works. <code>GET /orgs/acme/repos</code> comes back <code>403 {\"message\": \"Resource protected by organization SAML enforcement. You must grant your OAuth token access to this organization.\"}</code>, and on some endpoints it does not even say that much — it returns a bare <code>404</code> on a repository that is open in the next browser tab. Nothing is wrong with the credential. The organization enforces SAML single sign-on, which means every token has to be individually authorized against it by a person, in a browser, and this one never has been.",
"short_answer": """<p>SAML enforcement adds a gate that has nothing to do with scopes. A classic personal access token or an OAuth token is valid the moment it is minted, and it holds <em>no</em> access to an SSO-enforced organization until a human authorizes that specific token for that specific organization. A brand-new, perfectly-scoped token is refused on its first call.</p>
<p>The refusal names itself. GitHub puts <code>x-github-sso: required; url=https://github.com/orgs/ORG/sso?authorization_request=...</code> on the response, and that URL is the repair. Visit it, authorize the token, and the same call succeeds. The URL is short-lived — treat it as good for about an hour — and <code>https://github.com/orgs/ORG/sso</code> reaches the same place without one.</p>
<p>Read the header's <em>form</em>, not just its presence. <code>required</code> on a refusal is this note. <code>partial-results</code> on a <code>200</code> is <a href="/github/saml-partial-results/">a different problem</a> where nothing was refused and organizations were quietly left out of a list instead.</p>""",
"problem": """<p>Everything about this failure argues for the credential. It is a 403, which is what a missing scope produces. It happens on a token somebody just created, which is the thing they most recently changed. It happens on some calls and not others, which is what a scope gap looks like. And the fix people reach for — mint a wider token — is fast enough to try four times before anyone questions it. All four are refused identically, because all four are unauthorized in exactly the same way.</p>
<p>Then the 404s start arriving and the search widens. SAML enforcement does not always announce itself: on repository endpoints it can present as plain <code>Not Found</code>, indistinguishable from a typo, a deleted repository or a token with no access at all. Somebody checks the spelling, then the owner name, then the case of both, and the ticket that eventually gets written says the API is inconsistent. It is consistent. It is refusing to confirm that a private resource exists to a credential the organization has not admitted.</p>
<p>The part that turns an afternoon into a fortnight is automation. A person hits this once, sees the browser prompt, clicks through it and never thinks about it again — so the institutional memory of the problem is a shrug. A CI job cannot click anything. It gets the 403, retries with backoff, retries again on the next run, and the graph of failures looks like a flaky API rather than a locked door. Nothing about a retry loop can ever open this, and the fact that a human fixed it in four seconds last time is why nobody suspects that.</p>""",
"why": """<p><strong>Validity and authorization are two different questions.</strong> A token is valid if GitHub recognises it and it has not expired or been revoked; <code>GET /user</code> answers that. A token is <em>authorized</em> for an organization if a human has granted that individual credential access to that organization through the identity provider, and nothing about minting a token does that. So the healthy-looking half of the diagnosis — the token authenticates, it names the right account, it carries the right scopes — is all true and all beside the point.</p>
<p><strong>The header is the only place GitHub explains itself, and it arrives on the failure.</strong> <code>x-github-sso</code> is a response header, so it is invisible to anyone reading a body, a log line of the message string, or an exception that captured only the status. Most HTTP clients throw away headers on a non-2xx by default. That is the single practical reason this problem stays unsolved for weeks: the explanation was delivered and discarded.</p>
<p><strong>The two forms of that header mean opposite things.</strong> <code>required; url=...</code> appears on a refusal and means nothing was returned. <code>partial-results; organizations=21955855,20582480</code> appears on a <code>200</code> and means something was returned with pieces missing. Code that tests only for the header's presence will treat a silently truncated list as a hard failure, or worse, treat a hard failure as a truncation and carry on. Parse the form.</p>
<p><strong>The URL in the header is a one-time, time-limited handoff to a person.</strong> It carries an <code>authorization_request</code> identifier and it goes stale, which is why a URL pasted into a ticket last Tuesday takes today's reader to a page that no longer means anything. The stable address is <code>https://github.com/orgs/ORG/sso</code>. Either way the click is the point: authorization is a human control, deliberately, and a script that could perform it would be a hole in the control rather than a feature.</p>
<p><strong>Which credentials are subject to this is a short and useful list.</strong> Classic personal access tokens, OAuth tokens and an App's user-to-server tokens are all authorized per token, per organization. An App <em>installation</em> token is not: it belongs to an installation the organization already approved, and it does not depend on any human's SAML session. That single line is the whole answer for unattended automation, and it is why the repair for a CI job is not "authorize this token" but "stop using a user token here".</p>
<p><strong>A fine-grained token fails this differently.</strong> It has no per-token SSO authorization page. Its access to an organization is settled when it is created and by the organization's token policy, so a fine-grained token that cannot see an organization is usually <a href="/github/fine-grained-pat-pending-approval/">waiting for an owner to approve it</a> rather than waiting for an SSO click. The script names the credential type before it offers an SSO repair, because offering the wrong one costs a day.</p>""",
"steps": [
 {"h": "Establish that the credential is fine, so it stops being the suspect",
  "body": """<p>One read of <code>GET /user</code>. If that returns <code>200</code> the token is valid, unexpired and unrevoked, and the account it belongs to is named in the output. That reading exists to close a door: everything after it is about an organization's opinion of a credential that GitHub itself is perfectly happy with.</p>"""},
 {"h": "Take the pair of org reads that makes the signature",
  "body": """<p>The script reads <code>GET /orgs/{org}</code> and then <code>GET /orgs/{org}/repos?per_page=1</code>. Public organization metadata answering <code>200</code> while the listing answers <code>403</code> or <code>404</code> is the shape of SAML enforcement, and it also rules out the mundane explanations — a misspelled organization would fail both, a dead token would fail all three.</p>"""},
 {"h": "Read x-github-sso off the refusal and parse its form",
  "body": """<p>The header is taken from the response object, not the body, and split into a form and its parameters. <code>required</code> is this note and carries a URL. <code>partial-results</code> is not this note at all and carries organization IDs; the script says so and points at the note that owns it instead of forcing the case into a verdict about refusals.</p>"""},
 {"h": "Price the credential type before printing an SSO repair",
  "body": """<p>The token's prefix says what it is, locally, without a request. A classic token, an OAuth token or a user-to-server token can be authorized by a click. An installation token is not subject to this at all, so an SSO verdict against one means something else is wrong. A fine-grained token has no authorization URL to visit and is routed to the pending-approval note. The wrong repair here is expensive, so the script refuses to guess.</p>"""},
 {"h": "Print the URL for a person, and never open it",
  "body": """<p>The script prints the authorization URL from the header, or the stable <code>/orgs/ORG/sso</code> address when the header did not carry one, together with the note that it expires. It does not follow it, cannot follow it, and should not: this is a control that exists to require a human. For anything unattended, the printed repair names the durable answer instead, which is an App installation token that no SAML session can lapse under.</p>"""},
],
"verify": """<p>After somebody visits the URL and authorizes the token, the same three reads come back clean and the header is gone.</p>
<pre><code class="language-bash">GITHUB_TOKEN=$READ_ONLY_TOKEN python3 github_sso_required.py acme-corp
# read cost: 3 request(s) against the core hourly quota
# token: classic PAT, account=octobot
# GET /orgs/acme-corp -> 200
# GET /orgs/acme-corp/repos -> 403
# x-github-sso: form=required
# sso-authorization-required: this organization enforces SAML single sign-on and
#   this credential has never been authorized against it. The token is valid;
#   the organization has not admitted it.
# credential: a classic PAT is authorized per token, per organization, by a
#   person. Reminting it wider cannot change this answer.
# repair: open https://github.com/orgs/acme-corp/sso?authorization_request=AB12CD
#   in a browser and authorize this token for acme-corp. That URL is
#   short-lived; https://github.com/orgs/acme-corp/sso reaches the same page.
#   This script does not open it and must not: the click is the control.
# unattended: a user token here will need this click again whenever the
#   organization's SAML session lapses. An App installation token does not.</code></pre>""",
"code_intro": "The live part is three GETs and the rest is a header parser with opinions. The parser earns its place twice: once because the two forms of <code>x-github-sso</code> mean opposite things and code that only tests for presence gets one of them backwards, and once because the URL it extracts is the entire repair. Everything else is a small table from credential prefix to whether a click can even help, which is the check that stops an SSO answer being handed to an installation token that was refused for a completely different reason.",
"py_file": "github_sso_required.py",
"py": '''"""Tell a SAML refusal apart from every other 403, from one response header.

Read only. GET requests and nothing else, and one promise beyond that: this
script never authorizes anything. Authorizing a token against an organization
that enforces SAML single sign-on is deliberately a human step taken in a
browser, and a tool that performed it on your behalf would be a hole in the
control it is diagnosing. So this reads the refusal, prints the URL a person
has to visit, and stops there.

The finding is one response header. On a refusal, `x-github-sso` carries the
`required` form and a URL. On a successful cross-organization listing the same
header can carry the `partial-results` form instead, which is a different
problem with a different repair, and this script names it and hands it over
rather than flattening the two into one verdict.

What this can and cannot see: it can prove that this organization refuses this
credential and that GitHub attributed the refusal to SAML. It cannot tell you
whether the token was authorized once and lapsed, because a read-only token
cannot read its own authorization history; that needs an organization owner and
is the sibling note. Pass --worked-before if you know it used to succeed and
this script will send you there instead of offering a first-time repair.

Environment:

    GITHUB_TOKEN    the token that is being refused
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_sso_required")

API = "https://api.github.com"
UA = "github-sso-required/1.0"

SSO_HEADER = "x-github-sso"

# The two forms, and they are opposites. `required` arrives on a response that
# returned nothing; `partial-results` arrives on a 200 that returned most of
# something. Testing for the header without reading the form gets one of them
# exactly backwards.
FORM_REQUIRED = "required"
FORM_PARTIAL = "partial-results"

# Longest prefixes first so a future prefix extending an existing one is not
# swallowed by its shorter neighbour.
TOKEN_PREFIXES = (
    ("github_pat_", "fine-grained PAT"),
    ("ghp_", "classic PAT"),
    ("gho_", "OAuth user token"),
    ("ghu_", "App user-to-server token"),
    ("ghs_", "App installation token"),
    ("ghr_", "App refresh token"),
)

# Whether a click on the authorization URL can help this kind of credential.
# Getting this wrong costs a day, because the repair printed for one kind is
# useless and misleading for another.
CLICK_HELPS = {
    "classic PAT": (True, "a classic PAT is authorized per token, per "
                          "organization, by a person. Reminting it wider "
                          "cannot change this answer."),
    "OAuth user token": (True, "an OAuth token is authorized per token, per "
                               "organization, by the person who granted it."),
    "App user-to-server token": (True, "a user-to-server token inherits the "
                                       "user's SAML standing, so the same "
                                       "click applies to it."),
    "fine-grained PAT": (False, "a fine-grained PAT has no per-token SSO "
                                "authorization page. Its access to an "
                                "organization is settled at creation and by "
                                "the organization's token policy, so a refusal "
                                "here is usually a token waiting for an owner "
                                "to approve it."),
    "App installation token": (False, "an installation token is not subject to "
                                      "per-token SSO authorization at all. If "
                                      "one is being refused, SAML is not the "
                                      "reason and this note is the wrong one."),
    "App refresh token": (False, "a refresh token is not used against these "
                                 "endpoints; exchange it first."),
    "unknown": (False, "the credential type could not be named from its "
                       "prefix, so nothing here prices whether a click helps."),
}

STABLE_SSO_URL = "https://github.com/orgs/%s/sso"


def read_cost():
    """Requests this run will spend against the core quota. Pure."""
    return 3


def token_kind(token):
    """Name the credential from its prefix. Pure; nothing leaves the machine."""
    value = (token or "").strip()
    for prefix, name in TOKEN_PREFIXES:
        if value.startswith(prefix):
            return name
    return "unknown"


def parse_sso_header(value):
    """Split x-github-sso into a form and its parameters. Pure.

    Returns {"form": str|None, "url": str|None, "organizations": [str]}. The
    header is `form; key=value; key=value`, and the value of `url` contains its
    own `=` characters, so the split is on the first one only.
    """
    out = {"form": None, "url": None, "organizations": []}
    if not value:
        return out
    parts = [p.strip() for p in str(value).split(";") if p.strip()]
    if not parts:
        return out
    out["form"] = parts[0].lower()
    for part in parts[1:]:
        if "=" not in part:
            continue
        key, _, val = part.partition("=")
        key, val = key.strip().lower(), val.strip()
        if key == "url":
            out["url"] = val
        elif key == "organizations":
            out["organizations"] = [i.strip() for i in val.split(",") if i.strip()]
    return out


def enforcement_signature(meta_status, listing_status, sso):
    """Classify one pair of organization reads plus the header. Pure.

    (state, detail). The pair matters: a misspelled organization fails both
    reads, a dead credential fails everything, and SAML enforcement is the case
    where the public metadata is readable and the listing is not.
    """
    form = (sso or {}).get("form")
    refused = listing_status in (403, 404)
    if form == FORM_PARTIAL:
        return ("partial-results-not-a-refusal",
                "the header carries the partial-results form, which arrives on "
                "a response that succeeded with organizations left out of it. "
                "That is a different problem: nothing was refused here.")
    if refused and form == FORM_REQUIRED:
        return ("sso-authorization-required",
                "this organization enforces SAML single sign-on and this "
                "credential has not been authorized against it. The token is "
                "valid; the organization has not admitted it.")
    if refused and meta_status == 200:
        return ("refused-without-sso-header",
                "the organization is readable and the listing is not, but "
                "GitHub did not attribute the refusal to SAML. Look at the "
                "scopes the endpoint accepts, or at an organization policy "
                "that blocks the application rather than the token.")
    if refused:
        return ("organization-unreadable",
                "even the organization's own record could not be read, so this "
                "may be a name that does not resolve rather than a gate. Check "
                "the spelling before reading anything else into it.")
    if form == FORM_REQUIRED:
        return ("sso-required-on-a-success",
                "the listing succeeded and still carried the required form. "
                "Treat the header as advance warning: another endpoint on this "
                "organization will refuse the same credential.")
    return ("no-refusal-to-explain",
            "the listing succeeded and carried no SAML header, so this "
            "credential is authorized for this organization right now.")


def authorize_url(sso, org):
    """The address a person has to open. Pure. (url, source).

    The header's URL carries a short-lived authorization_request identifier, so
    a URL copied into a ticket last week is already stale. The stable address
    reaches the same page and never expires, which is the one worth printing
    when the header did not supply one.
    """
    from_header = (sso or {}).get("url")
    if from_header:
        return (from_header, "from the x-github-sso header, and short-lived: "
                             "treat it as good for about an hour")
    return (STABLE_SSO_URL % org,
            "the stable organization address, because the refusal carried no "
            "URL of its own")


def click_verdict(kind):
    """Can a human authorization click change this answer. Pure. (bool, detail)."""
    return CLICK_HELPS.get(kind, CLICK_HELPS["unknown"])


def which_sso_note(worked_before):
    """First authorization, or a lapsed one. Pure. (state, detail).

    A read-only token cannot read its own authorization history, so the one
    fact that separates these is the caller's own: did this credential ever
    succeed against this organization. Asked rather than guessed.
    """
    if worked_before:
        return ("session-lapse",
                "this credential succeeded here before, so it was authorized "
                "once and the authorization has lapsed rather than never "
                "existing. The click is the same; what changes is that it will "
                "be needed again on the organization's schedule.")
    return ("first-authorization",
            "no prior success was reported, so treat this as a credential that "
            "has never been authorized for this organization. One click "
            "settles it until the organization's session interval says "
            "otherwise.")


def repair(state, org, url, kind, worked_before):
    """The sentence a reader has to act on. Pure."""
    helps, _detail = click_verdict(kind)
    if state != "sso-authorization-required":
        if state == "partial-results-not-a-refusal":
            return ("read the withheld organization IDs out of the header and "
                    "treat the response as incomplete. Nothing here needs "
                    "authorizing to make a call succeed, because the call "
                    "succeeded.")
        if state == "refused-without-sso-header":
            return ("diff the scopes the refusal names against the ones the "
                    "credential holds, and check whether the organization "
                    "restricts the application itself.")
        if state == "organization-unreadable":
            return "check the organization name, then read this again."
        return "nothing on SAML. This credential is admitted to %s today." % org
    if not helps:
        return ("do not send anyone to the SSO page for this credential type. "
                "The refusal is real and SAML is not the explanation for it.")
    lead = ("open %s in a browser and authorize this credential for %s. This "
            "script does not open it and must not: the click is the control."
            % (url, org))
    if worked_before:
        return (lead + " Expect to do it again whenever the organization's "
                       "SAML session lapses, and move anything unattended onto "
                       "an App installation token, which does not lapse with a "
                       "person's session.")
    return (lead + " For anything unattended, prefer an App installation "
                   "token: it belongs to an installation the organization "
                   "already approved and is never subject to this click.")


def get(session, path):
    """One GET. Returns the response object."""
    r = session.get(API + path, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from GitHub: GITHUB_TOKEN is missing, malformed "
                         "or revoked. That is a different note; this one starts "
                         "from a credential GitHub still recognises.")
    return r


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("org", help="the organization login being refused")
    ap.add_argument("--worked-before", action="store_true",
                    help="this credential succeeded against this organization "
                         "in the past, which makes it a lapse rather than a "
                         "first authorization")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_TOKEN (a read-only token is enough)")
        return 2

    log.info("read cost: %d request(s) against the core hourly quota", read_cost())

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        # GitHub rejects requests with no User-Agent outright.
        "User-Agent": UA,
    })

    kind = token_kind(token)
    me = get(session, "/user")
    account = (me.json() or {}).get("login") if me.status_code == 200 else None
    log.info("token: %s, account=%s", kind, account or "unreadable")

    meta = get(session, "/orgs/" + args.org)
    log.info("GET /orgs/%s -> %s", args.org, meta.status_code)

    listing = get(session, "/orgs/%s/repos?per_page=1" % args.org)
    log.info("GET /orgs/%s/repos -> %s", args.org, listing.status_code)

    raw = listing.headers.get(SSO_HEADER) or meta.headers.get(SSO_HEADER)
    sso = parse_sso_header(raw)
    log.info("%s: form=%s", SSO_HEADER, sso["form"] or "absent")

    state, detail = enforcement_signature(meta.status_code, listing.status_code, sso)
    log.info("%s: %s", state, detail)

    helps, click_detail = click_verdict(kind)
    log.info("credential: %s", click_detail)

    url, url_source = authorize_url(sso, args.org)
    history_state, history_detail = which_sso_note(args.worked_before)
    if state == "sso-authorization-required":
        log.info("authorization url: %s (%s)", url, url_source)
        log.info("%s: %s", history_state, history_detail)
    log.info("repair: %s", repair(state, args.org, url, kind, args.worked_before))

    print(json.dumps({
        "organization": args.org,
        "account": account,
        "token_kind": kind,
        "org_read_status": meta.status_code,
        "listing_status": listing.status_code,
        "sso_header": sso,
        "state": state,
        "detail": detail,
        "click_can_help": helps,
        "authorization_url": url if state == "sso-authorization-required" else None,
        "history_state": history_state,
        "repair": repair(state, args.org, url, kind, args.worked_before),
    }, indent=2, default=str))
    return 1 if state == "sso-authorization-required" else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-sso-required.mjs",
"js": '''/**
 * Tell a SAML refusal apart from every other 403, from one response header.
 *
 * Read only, and one promise beyond that: this script never authorizes
 * anything. Authorizing a credential against an organization that enforces
 * SAML is deliberately a human step taken in a browser, so this reads the
 * refusal, prints the URL a person has to visit, and stops.
 *
 * The two forms of x-github-sso mean opposite things. `required` arrives on a
 * response that returned nothing. `partial-results` arrives on a 200 that
 * returned most of something, which is a different note entirely.
 *
 * Environment:
 *   GITHUB_TOKEN         the credential being refused
 *   GITHUB_ORG           the organization login being refused
 *   GITHUB_WORKED_BEFORE set to 1 if this credential used to succeed here
 */
const API = 'https://api.github.com';
const UA = 'github-sso-required/1.0';

export const SSO_HEADER = 'x-github-sso';
export const FORM_REQUIRED = 'required';
export const FORM_PARTIAL = 'partial-results';

/** Longest prefixes first. */
export const TOKEN_PREFIXES = [
  ['github_pat_', 'fine-grained PAT'],
  ['ghp_', 'classic PAT'],
  ['gho_', 'OAuth user token'],
  ['ghu_', 'App user-to-server token'],
  ['ghs_', 'App installation token'],
  ['ghr_', 'App refresh token'],
];

/** Whether a click on the authorization URL can help this credential type. */
export const CLICK_HELPS = {
  'classic PAT': [true, 'a classic PAT is authorized per token, per organization, '
    + 'by a person. Reminting it wider cannot change this answer.'],
  'OAuth user token': [true, 'an OAuth token is authorized per token, per '
    + 'organization, by the person who granted it.'],
  'App user-to-server token': [true, 'a user-to-server token inherits the user of '
    + 'record SAML standing, so the same click applies to it.'],
  'fine-grained PAT': [false, 'a fine-grained PAT has no per-token SSO '
    + 'authorization page. Its access is settled at creation and by the '
    + 'organization token policy, so a refusal here is usually a token waiting '
    + 'for an owner to approve it.'],
  'App installation token': [false, 'an installation token is not subject to '
    + 'per-token SSO authorization at all. If one is refused, SAML is not why.'],
  'App refresh token': [false, 'a refresh token is not used against these '
    + 'endpoints; exchange it first.'],
  unknown: [false, 'the credential type could not be named from its prefix, so '
    + 'nothing here prices whether a click helps.'],
};

export const STABLE_SSO_URL = (org) => `https://github.com/orgs/${org}/sso`;

/** Requests this run will spend against the core quota. Pure. */
export function readCost() {
  return 3;
}

/** Name the credential from its prefix. Pure. */
export function tokenKind(token) {
  const value = String(token ?? '').trim();
  for (const [prefix, name] of TOKEN_PREFIXES) {
    if (value.startsWith(prefix)) return name;
  }
  return 'unknown';
}

/** Split x-github-sso into a form and its parameters. Pure. */
export function parseSsoHeader(value) {
  const out = { form: null, url: null, organizations: [] };
  if (!value) return out;
  const parts = String(value).split(';').map((p) => p.trim()).filter(Boolean);
  if (parts.length === 0) return out;
  out.form = parts[0].toLowerCase();
  for (const part of parts.slice(1)) {
    const at = part.indexOf('=');
    if (at < 0) continue;
    const key = part.slice(0, at).trim().toLowerCase();
    const val = part.slice(at + 1).trim();
    if (key === 'url') out.url = val;
    else if (key === 'organizations') {
      out.organizations = val.split(',').map((i) => i.trim()).filter(Boolean);
    }
  }
  return out;
}

/** Classify one pair of organization reads plus the header. Pure. */
export function enforcementSignature(metaStatus, listingStatus, sso) {
  const form = (sso || {}).form;
  const refused = listingStatus === 403 || listingStatus === 404;
  if (form === FORM_PARTIAL) {
    return ['partial-results-not-a-refusal', 'the header carries the '
      + 'partial-results form, which arrives on a response that succeeded with '
      + 'organizations left out of it. Nothing was refused here.'];
  }
  if (refused && form === FORM_REQUIRED) {
    return ['sso-authorization-required', 'this organization enforces SAML single '
      + 'sign-on and this credential has not been authorized against it. The '
      + 'token is valid; the organization has not admitted it.'];
  }
  if (refused && metaStatus === 200) {
    return ['refused-without-sso-header', 'the organization is readable and the '
      + 'listing is not, but GitHub did not attribute the refusal to SAML.'];
  }
  if (refused) {
    return ['organization-unreadable', 'even the organization own record could '
      + 'not be read, so this may be a name that does not resolve.'];
  }
  if (form === FORM_REQUIRED) {
    return ['sso-required-on-a-success', 'the listing succeeded and still carried '
      + 'the required form. Another endpoint will refuse the same credential.'];
  }
  return ['no-refusal-to-explain', 'the listing succeeded and carried no SAML '
    + 'header, so this credential is authorized for this organization right now.'];
}

/** The address a person has to open. Pure. [url, source]. */
export function authorizeUrl(sso, org) {
  const fromHeader = (sso || {}).url;
  if (fromHeader) {
    return [fromHeader, 'from the x-github-sso header, and short-lived: treat it '
      + 'as good for about an hour'];
  }
  return [STABLE_SSO_URL(org), 'the stable organization address, because the '
    + 'refusal carried no URL of its own'];
}

/** Can a human authorization click change this answer. Pure. */
export function clickVerdict(kind) {
  return CLICK_HELPS[kind] || CLICK_HELPS.unknown;
}

/** First authorization, or a lapsed one. Pure. */
export function whichSsoNote(workedBefore) {
  if (workedBefore) {
    return ['session-lapse', 'this credential succeeded here before, so it was '
      + 'authorized once and the authorization has lapsed. The click is the same; '
      + 'what changes is that it will be needed again on a schedule.'];
  }
  return ['first-authorization', 'no prior success was reported, so treat this as '
    + 'a credential that has never been authorized for this organization.'];
}

/** The sentence a reader has to act on. Pure. */
export function repair(state, org, url, kind, workedBefore) {
  const [helps] = clickVerdict(kind);
  if (state !== 'sso-authorization-required') {
    if (state === 'partial-results-not-a-refusal') {
      return 'read the withheld organization IDs out of the header and treat the '
        + 'response as incomplete. Nothing here needs authorizing.';
    }
    if (state === 'refused-without-sso-header') {
      return 'diff the scopes the refusal names against the ones the credential '
        + 'holds, and check whether the organization restricts the application.';
    }
    if (state === 'organization-unreadable') {
      return 'check the organization name, then read this again.';
    }
    return `nothing on SAML. This credential is admitted to ${org} today.`;
  }
  if (!helps) {
    return 'do not send anyone to the SSO page for this credential type. The '
      + 'refusal is real and SAML is not the explanation for it.';
  }
  const lead = `open ${url} in a browser and authorize this credential for ${org}. `
    + 'This script does not open it and must not: the click is the control.';
  if (workedBefore) {
    return `${lead} Expect to do it again whenever the SAML session lapses, and `
      + 'move anything unattended onto an App installation token.';
  }
  return `${lead} For anything unattended, prefer an App installation token: it `
    + 'belongs to an installation the organization already approved.';
}

function headers(token) {
  return {
    Authorization: `Bearer ${token}`,
    Accept: 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
    'User-Agent': UA,
  };
}

async function main() {
  const token = process.env.GITHUB_TOKEN;
  const org = process.env.GITHUB_ORG;
  if (!token || !org) {
    console.error('set GITHUB_TOKEN (read-only is enough) and GITHUB_ORG');
    process.exitCode = 2;
    return;
  }
  const workedBefore = process.env.GITHUB_WORKED_BEFORE === '1';

  console.log(`read cost: ${readCost()} request(s) against the core hourly quota`);

  const h = headers(token);
  const me = await fetch(`${API}/user`, { headers: h });
  const kind = tokenKind(token);
  const account = me.status === 200 ? (await me.json()).login : null;
  console.log(`token: ${kind}, account=${account ?? 'unreadable'}`);

  const meta = await fetch(`${API}/orgs/${org}`, { headers: h });
  console.log(`GET /orgs/${org} -> ${meta.status}`);
  const listing = await fetch(`${API}/orgs/${org}/repos?per_page=1`, { headers: h });
  console.log(`GET /orgs/${org}/repos -> ${listing.status}`);

  const raw = listing.headers.get(SSO_HEADER) || meta.headers.get(SSO_HEADER);
  const sso = parseSsoHeader(raw);
  console.log(`${SSO_HEADER}: form=${sso.form ?? 'absent'}`);

  const [state, detail] = enforcementSignature(meta.status, listing.status, sso);
  console.log(`${state}: ${detail}`);
  const [helps, clickDetail] = clickVerdict(kind);
  console.log(`credential: ${clickDetail}`);

  const [url, urlSource] = authorizeUrl(sso, org);
  const [historyState] = whichSsoNote(workedBefore);
  if (state === 'sso-authorization-required') {
    console.log(`authorization url: ${url} (${urlSource})`);
  }
  console.log(`repair: ${repair(state, org, url, kind, workedBefore)}`);

  console.log(JSON.stringify({
    organization: org,
    account,
    token_kind: kind,
    org_read_status: meta.status,
    listing_status: listing.status,
    sso_header: sso,
    state,
    detail,
    click_can_help: helps,
    authorization_url: state === 'sso-authorization-required' ? url : null,
    history_state: historyState,
    repair: repair(state, org, url, kind, workedBefore),
  }, null, 2));
  process.exitCode = state === 'sso-authorization-required' ? 1 : 0;
}

// Guarded so importing this file from the test runner does not start a run.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The parser is asserted first and hardest, because the whole note rests on it: the URL contains its own <code>=</code> characters and a naive split loses half of it, and the two forms have to come out as different verdicts rather than as one header that was present. Then the pair of organization reads, where the point of the second read is that a misspelled organization and an enforced one are not allowed to produce the same answer. The last group is the guardrail: an installation token that gets refused must never be handed an SSO repair, and the sentence the script prints has to keep saying that the click belongs to a person.",
"test_py_file": "test_github_sso_required.py",
"test_py": '''from github_sso_required import (
    FORM_PARTIAL, FORM_REQUIRED, authorize_url, click_verdict,
    enforcement_signature, parse_sso_header, read_cost, repair, token_kind,
    which_sso_note,
)

REQUIRED_HEADER = ("required; url=https://github.com/orgs/acme-corp/sso"
                   "?authorization_request=AB12CD")
PARTIAL_HEADER = "partial-results; organizations=21955855,20582480"


def test_the_required_form_keeps_its_whole_url():
    # The URL contains = characters of its own. Splitting on every one of them
    # is the bug that turns the repair into a fragment.
    sso = parse_sso_header(REQUIRED_HEADER)
    assert sso["form"] == FORM_REQUIRED
    assert sso["url"].endswith("?authorization_request=AB12CD")
    assert sso["url"].startswith("https://github.com/orgs/acme-corp/sso")


def test_the_partial_form_is_a_different_finding_not_a_refusal():
    sso = parse_sso_header(PARTIAL_HEADER)
    assert sso["form"] == FORM_PARTIAL
    assert sso["organizations"] == ["21955855", "20582480"]
    state, detail = enforcement_signature(200, 200, sso)
    assert state == "partial-results-not-a-refusal"
    assert "Nothing was refused" in detail or "nothing was refused" in detail


def test_an_absent_header_parses_without_inventing_a_form():
    assert parse_sso_header(None) == {"form": None, "url": None,
                                      "organizations": []}
    assert parse_sso_header("")["form"] is None
    assert parse_sso_header("required")["url"] is None


def test_the_signature_is_a_pair_of_reads_not_one_status():
    sso = parse_sso_header(REQUIRED_HEADER)
    assert enforcement_signature(200, 403, sso)[0] == "sso-authorization-required"
    # SAML can mask as a bare 404, so the same pair with a 404 is the same
    # finding rather than a missing organization.
    assert enforcement_signature(200, 404, sso)[0] == "sso-authorization-required"


def test_a_misspelled_org_is_never_reported_as_saml():
    empty = parse_sso_header(None)
    state, detail = enforcement_signature(404, 404, empty)
    assert state == "organization-unreadable"
    assert "spelling" in detail


def test_a_refusal_without_the_header_is_handed_elsewhere():
    empty = parse_sso_header(None)
    state, detail = enforcement_signature(200, 403, empty)
    assert state == "refused-without-sso-header"
    assert "did not attribute" in detail


def test_a_clean_read_is_reported_as_authorized_today():
    empty = parse_sso_header(None)
    assert enforcement_signature(200, 200, empty)[0] == "no-refusal-to-explain"
    # The header on a success is advance warning rather than nothing.
    warned = parse_sso_header(REQUIRED_HEADER)
    assert enforcement_signature(200, 200, warned)[0] == "sso-required-on-a-success"


def test_the_url_falls_back_to_the_address_that_never_expires():
    url, source = authorize_url(parse_sso_header(REQUIRED_HEADER), "acme-corp")
    assert "authorization_request=AB12CD" in url and "short-lived" in source
    url, source = authorize_url(parse_sso_header(None), "acme-corp")
    assert url == "https://github.com/orgs/acme-corp/sso"
    assert "stable" in source


def test_an_installation_token_is_never_sent_to_the_sso_page():
    helps, detail = click_verdict("App installation token")
    assert helps is False
    assert "not subject to" in detail
    fix = repair("sso-authorization-required", "acme-corp",
                 "https://github.com/orgs/acme-corp/sso",
                 "App installation token", False)
    assert "do not send anyone to the SSO page" in fix


def test_a_fine_grained_token_is_routed_to_the_approval_note():
    helps, detail = click_verdict("fine-grained PAT")
    assert helps is False
    assert "waiting for an owner" in detail


def test_a_classic_token_gets_the_click_and_the_warning_about_widening():
    helps, detail = click_verdict("classic PAT")
    assert helps is True
    assert "Reminting it wider cannot change this answer" in detail


def test_the_repair_says_the_click_belongs_to_a_person():
    fix = repair("sso-authorization-required", "acme-corp",
                 "https://github.com/orgs/acme-corp/sso", "classic PAT", False)
    assert "does not open it and must not" in fix
    assert "installation token" in fix


def test_a_prior_success_points_at_the_lapse_note_instead():
    state, detail = which_sso_note(True)
    assert state == "session-lapse"
    assert "lapsed" in detail
    assert which_sso_note(False)[0] == "first-authorization"
    fix = repair("sso-authorization-required", "acme-corp",
                 "https://github.com/orgs/acme-corp/sso", "classic PAT", True)
    assert "again" in fix


def test_the_credential_type_comes_from_its_prefix_locally():
    # Obviously fake, and short. Nothing in this suite is a real credential.
    assert token_kind("ghp_fake") == "classic PAT"
    assert token_kind("gho_fake") == "OAuth user token"
    assert token_kind("ghs_fake") == "App installation token"
    assert token_kind("github_pat_x") == "fine-grained PAT"
    assert token_kind("nope") == "unknown"


def test_the_run_costs_three_reads():
    assert read_cost() == 3
''',
"test_js_file": "github-sso-required.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  FORM_PARTIAL, FORM_REQUIRED, authorizeUrl, clickVerdict, enforcementSignature,
  parseSsoHeader, readCost, repair, tokenKind, whichSsoNote,
} from './github-sso-required.mjs';

const REQUIRED_HEADER = 'required; url=https://github.com/orgs/acme-corp/sso'
  + '?authorization_request=AB12CD';
const PARTIAL_HEADER = 'partial-results; organizations=21955855,20582480';

test('the required form keeps its whole url', () => {
  const sso = parseSsoHeader(REQUIRED_HEADER);
  assert.equal(sso.form, FORM_REQUIRED);
  assert.ok(sso.url.endsWith('?authorization_request=AB12CD'));
});

test('the partial form is a different finding not a refusal', () => {
  const sso = parseSsoHeader(PARTIAL_HEADER);
  assert.equal(sso.form, FORM_PARTIAL);
  assert.deepEqual(sso.organizations, ['21955855', '20582480']);
  assert.equal(enforcementSignature(200, 200, sso)[0], 'partial-results-not-a-refusal');
});

test('an absent header parses without inventing a form', () => {
  assert.deepEqual(parseSsoHeader(null), { form: null, url: null, organizations: [] });
  assert.equal(parseSsoHeader('required').url, null);
});

test('the signature is a pair of reads not one status', () => {
  const sso = parseSsoHeader(REQUIRED_HEADER);
  assert.equal(enforcementSignature(200, 403, sso)[0], 'sso-authorization-required');
  assert.equal(enforcementSignature(200, 404, sso)[0], 'sso-authorization-required');
});

test('a misspelled org is never reported as saml', () => {
  assert.equal(enforcementSignature(404, 404, parseSsoHeader(null))[0],
    'organization-unreadable');
});

test('a refusal without the header is handed elsewhere', () => {
  assert.equal(enforcementSignature(200, 403, parseSsoHeader(null))[0],
    'refused-without-sso-header');
});

test('the url falls back to the address that never expires', () => {
  const [url, source] = authorizeUrl(parseSsoHeader(null), 'acme-corp');
  assert.equal(url, 'https://github.com/orgs/acme-corp/sso');
  assert.ok(source.includes('stable'));
});

test('an installation token is never sent to the sso page', () => {
  const [helps] = clickVerdict('App installation token');
  assert.equal(helps, false);
  const fix = repair('sso-authorization-required', 'acme-corp',
    'https://github.com/orgs/acme-corp/sso', 'App installation token', false);
  assert.ok(fix.includes('do not send anyone to the SSO page'));
});

test('the repair says the click belongs to a person', () => {
  const fix = repair('sso-authorization-required', 'acme-corp',
    'https://github.com/orgs/acme-corp/sso', 'classic PAT', false);
  assert.ok(fix.includes('does not open it and must not'));
});

test('a prior success points at the lapse note instead', () => {
  assert.equal(whichSsoNote(true)[0], 'session-lapse');
  assert.equal(whichSsoNote(false)[0], 'first-authorization');
});

test('the credential type comes from its prefix locally', () => {
  assert.equal(tokenKind('ghp_fake'), 'classic PAT');
  assert.equal(tokenKind('ghs_fake'), 'App installation token');
  assert.equal(tokenKind('nope'), 'unknown');
});

test('the run costs three reads', () => {
  assert.equal(readCost(), 3);
});
''',
"faq": [
 ("Is this the same as the note about organizations missing from a list?",
  "No, and the header is what separates them. That note is about a <code>200</code>: the call succeeded, some organizations were quietly left out of the body, and the header carries the <code>partial-results</code> form naming their IDs. This note is about a refusal: nothing came back, and the header carries the <code>required</code> form plus a URL. One is silent under-reporting you have to detect, the other is a locked door that tells you where the key is. The scripts in both notes parse the form for exactly this reason."),
 ("How is this different from the token whose SAML session expired?",
  "By history and by what happens next. This note is a credential that has never been authorized for the organization at all, so its very first call is refused and one click settles it. The <a href=\"/github/saml-session-expired/\">lapse</a> is a credential that was authorized, worked for weeks and started being refused with no change to anything, because the organization requires re-authentication on an interval. The refusals look identical; the repairs differ in that one of them recurs on a timetable. This script asks whether the credential ever worked here rather than guessing, and hands you over when the answer is yes."),
 ("Can the script authorize the token for me if I give it more permission?",
  "No, and it is important that the answer is no. SSO authorization is a control that exists specifically to require a person and an identity provider in the loop. A tool that could satisfy it on your behalf would not be a convenience, it would be the removal of the control. So the script prints the URL, says that it will not open it, and exits. The only automation-shaped answer to this problem is to stop using a credential that needs the click, which means a GitHub App installation token."),
 ("Why does the failure sometimes look like 404 instead of 403?",
  "For the same reason a great many GitHub refusals do: confirming that a private resource exists would leak it to a caller with no right to know. On organization endpoints the enforcement message is usually explicit, and on repository endpoints under an enforcing organization you can get a bare <code>Not Found</code> instead. The header is the constant. It arrives on both, which is why the script reads the response object rather than matching on the message string, and why matching on the message alone is how people end up chasing a typo for a day."),
 ("Our CI job hits this every few weeks. What is the actual fix?",
  "Move it off a user credential. Classic tokens, OAuth tokens and user-to-server tokens all depend on a person's standing with the identity provider, which is a dependency no unattended job should have; it is also why the job fails at unrelated times, since it fails when a human's session lapses. An App installation token is issued to an installation the organization already approved, expires on its own predictable one-hour clock, and is never subject to per-token SSO authorization. The click disappears rather than being scheduled."),
],
"related": [
 ("/github/saml-session-expired/", "The same refusal, on a token that was authorized once"),
 ("/github/saml-partial-results/", "The 200 that quietly leaves organizations out"),
 ("/github/404-masking-403/", "Why the refusal sometimes arrives as Not Found"),
],
"citations": [CITE_SSO_AUTHORIZE, CITE_SSO_REST, CITE_SAML_ABOUT, CITE_APP_INSTALL_AUTH],
},
{
"slug": "saml-session-expired",
"title": "The SAML session lapsed and the authorization went with it",
"description": "A token authorized weeks ago starts failing again. The org's credential authorizations carry an expiry date, so the next lapse is a forecast, not a surprise.",
"h1": "The SAML session lapsed and the authorization went with it",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github saml session expired token 403",
             "github credential authorizations expires at",
             "saml sso token stopped working after a week",
             "github sso re-authentication interval automation",
             "authorized_credential_expires_at github api"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Nobody touched anything. The nightly job ran for six weeks, and this morning it returned <code>403</code> on every organization call with a message about SAML enforcement. Somebody logs into GitHub in a browser to check, comes back, reruns the job, and it works. The ticket gets closed as transient. Eight days later it happens again, at a different hour, and the second ticket says the API is flaky. It is not flaky and it is not random: the authorization that credential holds against the organization has an expiry date, the organization set the interval, and the browser login that &ldquo;fixed&rdquo; it was a person quietly renewing something they did not know they were renewing.",
"short_answer": """<p>Authorizing a token for an SSO-enforced organization is not permanent. The authorization is tied to a SAML session with the identity provider, and organizations can require re-authentication on an interval, so a credential that was authorized correctly starts being refused again when that session lapses. The refusal is identical to <a href=\"/github/saml-token-not-authorized/\">the one a never-authorized token gets</a>, which is why this reads as flakiness.</p>
<p>There is a dated record behind it. With <code>admin:org</code>, <code>GET /orgs/{org}/credential-authorizations</code> lists every SSO-authorized credential with <code>credential_id</code>, <code>credential_type</code>, <code>token_last_eight</code>, <code>credential_accessed_at</code> and — the field this note is about — <code>authorized_credential_expires_at</code>.</p>
<p>That last field turns an outage into a calendar entry. Match your credential to its record by the last eight characters, read the expiry, and you know the date the job will start failing before it does. The durable repair is not a better reminder: it is an App installation token, which does not depend on any human's session.</p>""",
"problem": """<p>The signature of this problem is that it fixes itself. Someone investigates, opens GitHub in a browser to look at the organization, authenticates through the identity provider because that is what opening GitHub does at a company with SSO, and by the time they get back to the terminal the failing call succeeds. That sequence teaches exactly the wrong lesson. The retry looked like the fix, so the runbook that gets written says &ldquo;rerun it&rdquo;, and the actual cause — a human's browser login renewing a session the automation depends on — is invisible to everyone including the person who did it.</p>
<p>Then it recurs on a period nobody recognises. The organization's re-authentication interval might be a week, a fortnight or a day, and the lapse lands wherever the clock lands: mid-run, over a weekend, on a bank holiday. Because it is a duration since a login rather than a time of day, the failures do not line up on a chart, and the pattern-matching people are good at finds nothing. Two of these tickets in a quarter get filed under transient. Six of them get filed under &ldquo;GitHub is unreliable&rdquo;.</p>
<p>The cruellest version is the one where nothing recurs for months because the person who owns the token happens to be at their desk every morning. Their daily browser login keeps the session alive and the automation alive with it. Then they go on leave, and the job that has never failed in a year fails on day three of their holiday, in a way nobody else can reproduce and nobody thinks to connect to an absence.</p>""",
"why": """<p><strong>The authorization has a lifetime, and the lifetime is the organization's to set.</strong> Authorizing a credential records a grant against your SAML identity, not a permanent property of the token. When the organization requires re-authentication and the session lapses, previously authorized credentials go back to being refused. Nothing about the token changed — it has not expired, it has not been revoked, its scopes are the same — which is precisely why every check anyone runs on the token comes back clean.</p>
<p><strong>The refusal is byte-for-byte the one a new token gets.</strong> Same status, same message, same <code>x-github-sso: required</code> header with a fresh URL. So the header alone cannot tell a lapse from a first authorization; it only tells you SAML is involved. What separates them is history: did this credential ever succeed here. That history is not in the response, and a read-only token cannot enumerate its own past, which is why the two cases need two different readings and get two different notes.</p>
<p><strong>The authoritative reading needs an owner, and it is worth the borrow.</strong> <code>GET /orgs/{org}/credential-authorizations</code> is an <code>admin:org</code> endpoint, so the credential being diagnosed usually cannot read it — you run this with a second, administrative credential and ask about the first. That is unusual for this section and it is the point: the record contains a date the failing credential is not allowed to know about itself.</p>
<p><strong>Matching happens locally and the eight characters never leave.</strong> Records identify credentials by <code>token_last_eight</code>. The script computes the last eight of the credential in the environment, compares in memory, and prints only whether a record matched. It never logs those characters and never puts them in its JSON, because a fragment of a live credential in a CI log is still a fragment of a live credential, and eight characters is enough to correlate a token across systems.</p>
<p><strong>The expiry field converts this from an outage into a forecast.</strong> This is the whole reason to run the script when nothing is broken. <code>authorized_credential_expires_at</code> says when the grant stops; <code>credential_accessed_at</code> says when it was last used and therefore proves it did work. A run that reports &ldquo;active, three days left, last used four hours ago&rdquo; is a warning with a date on it, and it is the only form of this problem that can be dealt with calmly.</p>
<p><strong>And the honest limit: the interval itself is not published.</strong> The API gives you this grant's expiry, not the organization's re-authentication policy, so the script reports the window it can measure and says the cadence is inferred rather than read. That is sufficient for the decision that matters, because the decision is not &ldquo;how often should we re-authorize&rdquo;. It is &ldquo;should an unattended job depend on a human's session at all&rdquo;, and the answer to that one does not need a number.</p>""",
"steps": [
 {"h": "Confirm the credential is refused and that SAML is why",
  "body": """<p>Two reads with the credential under investigation: <code>GET /user</code> to establish it is alive, and one organization listing to see whether it is currently refused and whether <code>x-github-sso</code> is on the response. This is deliberately the same evidence the first-authorization note gathers, because up to here the two problems are genuinely identical and pretending otherwise would be a lie in the shape of a script.</p>"""},
 {"h": "Borrow an administrative credential for the record",
  "body": """<p><code>GITHUB_ADMIN_TOKEN</code>, held by an organization owner, reads <code>GET /orgs/{org}/credential-authorizations</code>. The credential being diagnosed cannot read this and does not need to: it supplies the last eight characters to match on and nothing else. Without the admin credential the script says plainly that the lapse cannot be proven and that the header reading is all you have.</p>"""},
 {"h": "Match on the last eight, in memory, and print none of them",
  "body": """<p>The comparison is local. The script derives the last eight characters of the credential in the environment, finds the record whose <code>token_last_eight</code> equals it, and reports <code>matched</code> or <code>no matching record</code>. Those characters appear in no log line and in no JSON field. A record that does not exist is its own finding: a credential with no authorization record was never authorized, which is the sibling note rather than this one.</p>"""},
 {"h": "Read the two dates and turn them into a sentence",
  "body": """<p><code>authorized_credential_expires_at</code> against the current time gives lapsed, expiring soon, or active with a number of days on it. <code>credential_accessed_at</code> proves the credential really was working, which is the fact that makes this a lapse rather than a first authorization. The output is a date, not an adjective.</p>"""},
 {"h": "Print the renewal, then print the way out of renewing",
  "body": """<p>The immediate repair is the same click as the first time, and the script says so without pretending it is a solution: it will be needed again, on an interval the API does not publish. The second line is the one worth acting on — an App installation token belongs to an installation the organization approved and does not lapse when a person stops logging in. Nothing is renewed, authorized or requested by this script.</p>"""},
],
"verify": """<p>Run it while everything works. A number of days is a better finding than an outage.</p>
<pre><code class="language-bash">GITHUB_TOKEN=$READ_ONLY_TOKEN GITHUB_ADMIN_TOKEN=$OWNER_TOKEN \\
    python3 github_sso_session_clock.py acme-corp
# read cost: 3 request(s) against the core hourly quota
# credential: classic PAT, account=octobot
# GET /orgs/acme-corp/repos -> 200, x-github-sso: absent
# credential-authorizations: 214 record(s) read, 1 matched
#   (matched on the last eight characters, in memory; they are not printed)
# credential_type=personal access token  credential_accessed_at=2026-08-31T04:11:07Z
# authorized_credential_expires_at=2026-09-03T09:22:41Z
# authorization-expiring: this authorization lapses in 3 day(s). The credential
#   is fine; the organization's SAML session behind it is what runs out.
# cadence: the organization's re-authentication interval is not published by the
#   API. What is readable is this grant's expiry, and it will recur.
# repair: a person re-authenticates at https://github.com/orgs/acme-corp/sso
#   before that date. This script does not and will not do it. For the nightly
#   job, move to an App installation token, which never lapses with a person's
#   identity-provider session.</code></pre>""",
"code_intro": "Two things make this script different from every other credential check in the section. It holds two credentials and asks one about the other, because the record that carries the date is an owner-only read and the credential in trouble is not allowed to see its own grant. And it does a match it refuses to print: the last eight characters identify a record, they are compared in memory, and they appear in no output, because eight live characters in a CI log are still eight live characters. Everything else is date arithmetic against <code>authorized_credential_expires_at</code>, which is the field that turns this from an incident into a diary entry.",
"py_file": "github_sso_session_clock.py",
"py": '''"""Read the expiry on a SAML credential authorization before it lapses.

Read only, and it authorizes nothing. The repair for a lapsed SAML session is a
person re-authenticating in a browser; this script reports the date that will
become necessary and never performs it.

Two credentials, on purpose. GITHUB_TOKEN is the credential in trouble.
GITHUB_ADMIN_TOKEN belongs to an organization owner and is the only one that
can read GET /orgs/{org}/credential-authorizations, where the dated record
lives. The credential being diagnosed is not permitted to know its own expiry,
which is the reason this note needs a second reader at all.

The match on token_last_eight happens in memory and those characters are never
logged or serialised. Eight characters of a live credential are still part of a
live credential, and they are enough to correlate one across systems.

What this can and cannot see: it can read this grant's expiry, when the
credential was last used, and therefore whether a refusal is a lapse or a
credential that was never authorized. It cannot read the organization's
re-authentication interval, which is not published by the API, so the cadence is
reported as inferred rather than measured.

Environment:

    GITHUB_TOKEN        the credential being diagnosed
    GITHUB_ADMIN_TOKEN  an organization owner's credential, admin:org (optional)
"""
import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_sso_session_clock")

API = "https://api.github.com"
UA = "github-sso-session-clock/1.0"

SSO_HEADER = "x-github-sso"

# Inside this window the answer is "arrange it now" rather than "it is fine".
EXPIRING_SOON_DAYS = 7

TOKEN_PREFIXES = (
    ("github_pat_", "fine-grained PAT"),
    ("ghp_", "classic PAT"),
    ("gho_", "OAuth user token"),
    ("ghu_", "App user-to-server token"),
    ("ghs_", "App installation token"),
    ("ghr_", "App refresh token"),
)

# Credentials that hang off a person's identity-provider session, and therefore
# lapse when it does. The installation token is the one that does not, which is
# the entire durable repair.
LAPSES_WITH_A_PERSON = {
    "classic PAT": True,
    "OAuth user token": True,
    "App user-to-server token": True,
    "fine-grained PAT": True,
    "App installation token": False,
    "App refresh token": False,
    "unknown": True,
}


def read_cost(with_admin=True, pages=1):
    """Requests this run will spend against the core quota. Pure.

    Two reads with the credential under investigation, plus one page of
    authorization records per page walked with the owner's credential.
    """
    return 2 + (pages if with_admin else 0)


def token_kind(token):
    """Name the credential from its prefix. Pure; nothing leaves the machine."""
    value = (token or "").strip()
    for prefix, name in TOKEN_PREFIXES:
        if value.startswith(prefix):
            return name
    return "unknown"


def last_eight(token):
    """The eight characters a record is matched on. Pure.

    Returned for an in-memory comparison only. Every caller in this script
    keeps the result out of logs and out of the report.
    """
    value = (token or "").strip()
    return value[-8:] if len(value) >= 8 else ""


def match_authorization(records, tail):
    """Find the record for this credential. Pure.

    Compares token_last_eight and returns the record or None. A missing match
    is a real finding rather than an error: a credential with no authorization
    record has never been authorized for this organization.
    """
    if not tail:
        return None
    for record in records or []:
        if not isinstance(record, dict):
            continue
        if str(record.get("token_last_eight") or "") == tail:
            return record
    return None


def parse_ts(value):
    """ISO 8601 with a Z into an aware datetime, or None. Pure."""
    if not value:
        return None
    text = str(value).strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def days_left(expires_at, now):
    """Whole days from now until the grant lapses, negative if it has. Pure."""
    when = parse_ts(expires_at)
    if when is None:
        return None
    return int((when - now).total_seconds() // 86400)


def authorization_state(record, now, refused):
    """Classify one credential's SAML standing. Pure. (state, detail).

    The record and the current refusal are read together, because either alone
    gets a case wrong: a missing record with no refusal is simply an
    organization that does not enforce SAML, and an active record beside a
    refusal is a refusal SAML does not explain.
    """
    if record is None:
        if refused:
            return ("never-authorized",
                    "no authorization record exists for this credential, so it "
                    "has never been authorized for this organization. That is a "
                    "first authorization rather than a lapse, and a different "
                    "note owns it.")
        return ("no-record-no-refusal",
                "no authorization record and nothing being refused, which is "
                "what an organization that does not enforce SAML looks like.")
    remaining = days_left(record.get("authorized_credential_expires_at"), now)
    if remaining is None:
        return ("expiry-not-published",
                "the record exists but carries no expiry, so this grant is not "
                "on a clock the API will show you. A refusal here is worth "
                "re-reading the header for.")
    if remaining < 0:
        return ("authorization-lapsed",
                "this authorization expired %d day(s) ago. The credential is "
                "unchanged and valid; the SAML session behind it ran out."
                % abs(remaining))
    if remaining <= EXPIRING_SOON_DAYS:
        return ("authorization-expiring",
                "this authorization lapses in %d day(s). The credential is "
                "fine; the organization's SAML session behind it is what runs "
                "out." % remaining)
    return ("authorization-active",
            "this authorization is good for another %d day(s)." % remaining)


def lapse_evidence(record):
    """Did this credential demonstrably work here. Pure. (bool, detail)."""
    if record is None:
        return (False, "no record, so there is no evidence of past use.")
    used = parse_ts(record.get("credential_accessed_at"))
    if used is None:
        return (False, "the record carries no last-used time, so past success "
                       "is not provable from it.")
    return (True, "the record was last used at %s, which proves this credential "
                  "did work against this organization." % used.isoformat())


def cadence_note(state):
    """What recurrence a reader should expect. Pure."""
    if state in ("authorization-lapsed", "authorization-expiring",
                 "authorization-active"):
        return ("the organization's re-authentication interval is not published "
                "by the API. What is readable is this grant's expiry, and it "
                "will recur.")
    return ("nothing to forecast from this reading.")


def unattended_verdict(kind):
    """Does this credential type depend on a person staying logged in. Pure."""
    if LAPSES_WITH_A_PERSON.get(kind, True):
        return (True, "a %s hangs off a person's identity-provider session, so "
                      "an unattended job holding one fails whenever that person "
                      "stops logging in." % kind)
    return (False, "a %s does not depend on anyone's identity-provider session, "
                   "which is why it is the answer for unattended work." % kind)


def repair(state, org, kind):
    """The sentence a reader has to act on. Pure."""
    depends, _ = unattended_verdict(kind)
    renew = ("a person re-authenticates at https://github.com/orgs/%s/sso "
             "before that date. This script does not and will not do it."
             % org)
    if state == "authorization-lapsed":
        return (renew.replace("before that date", "to restore this credential")
                + (" For anything unattended, move to an App installation "
                   "token, which never lapses with a person's session."
                   if depends else ""))
    if state == "authorization-expiring":
        return (renew + (" For the job that depends on this, move to an App "
                         "installation token, which never lapses with a "
                         "person's session." if depends else ""))
    if state == "never-authorized":
        return ("authorize the credential for the first time, which is the "
                "sibling problem: the refusal is the same and the repair does "
                "not recur on a session clock.")
    if state == "authorization-active":
        return ("nothing today. Note the date and decide whether an unattended "
                "job should be depending on a human session at all.")
    if state == "expiry-not-published":
        return ("read the refusal's x-github-sso header instead; this record "
                "will not tell you when the grant ends.")
    return "nothing on SAML here."


def get(session, url):
    """One GET. Returns the response object."""
    r = session.get(url, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from GitHub: a credential is missing, malformed "
                         "or revoked. That is a different note.")
    return r


def session_for(token):
    s = requests.Session()
    s.headers.update({
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        # GitHub rejects requests with no User-Agent outright.
        "User-Agent": UA,
    })
    return s


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("org", help="the organization enforcing SAML")
    ap.add_argument("--pages", type=int, default=1,
                    help="pages of credential authorizations to walk")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_TOKEN (the credential being diagnosed)")
        return 2
    admin = os.environ.get("GITHUB_ADMIN_TOKEN")

    log.info("read cost: %d request(s) against the core hourly quota",
             read_cost(bool(admin), max(1, args.pages)))

    kind = token_kind(token)
    subject = session_for(token)
    me = get(subject, API + "/user")
    account = (me.json() or {}).get("login") if me.status_code == 200 else None
    log.info("credential: %s, account=%s", kind, account or "unreadable")

    listing = get(subject, API + "/orgs/%s/repos?per_page=1" % args.org)
    sso_form = (listing.headers.get(SSO_HEADER) or "").split(";")[0].strip().lower()
    log.info("GET /orgs/%s/repos -> %s, %s: %s", args.org, listing.status_code,
             SSO_HEADER, sso_form or "absent")
    refused = listing.status_code in (403, 404)

    records = []
    if admin:
        owner = session_for(admin)
        url = (API + "/orgs/%s/credential-authorizations?per_page=100"
               % args.org)
        for _page in range(max(1, args.pages)):
            page = get(owner, url)
            if page.status_code != 200:
                log.warning("credential-authorizations returned HTTP %s. That "
                            "endpoint needs admin:org, so this is usually the "
                            "wrong credential rather than a missing record.",
                            page.status_code)
                break
            body = page.json()
            records.extend(body if isinstance(body, list) else [])
            nxt = (page.links or {}).get("next", {}).get("url")
            if not nxt:
                break
            url = nxt
    else:
        log.warning("no GITHUB_ADMIN_TOKEN, so the dated record cannot be read. "
                    "Without it a lapse and a first authorization look "
                    "identical, and the header is all you have.")

    # Compared in memory. These characters are never logged and never appear in
    # the report below.
    record = match_authorization(records, last_eight(token))
    if admin:
        log.info("credential-authorizations: %d record(s) read, %d matched "
                 "(matched on the last eight characters, in memory; they are "
                 "not printed)", len(records), 1 if record else 0)
    if record:
        log.info("credential_type=%s credential_accessed_at=%s",
                 record.get("credential_type"), record.get("credential_accessed_at"))
        log.info("authorized_credential_expires_at=%s",
                 record.get("authorized_credential_expires_at"))

    now = datetime.now(timezone.utc)
    state, detail = authorization_state(record, now, refused)
    proven, proof = lapse_evidence(record)
    log.info("%s: %s", state, detail)
    log.info("past use: %s", proof)
    log.info("cadence: %s", cadence_note(state))
    depends, depends_detail = unattended_verdict(kind)
    log.info("unattended: %s", depends_detail)
    log.info("repair: %s", repair(state, args.org, kind))

    print(json.dumps({
        "organization": args.org,
        "account": account,
        "credential_kind": kind,
        "listing_status": listing.status_code,
        "sso_form": sso_form or None,
        "records_read": len(records),
        "record_matched": bool(record),
        "credential_type": (record or {}).get("credential_type"),
        "credential_accessed_at": (record or {}).get("credential_accessed_at"),
        "authorized_credential_expires_at":
            (record or {}).get("authorized_credential_expires_at"),
        "days_left": days_left((record or {}).get(
            "authorized_credential_expires_at"), now),
        "state": state,
        "detail": detail,
        "past_use_proven": proven,
        "depends_on_a_person": depends,
        "repair": repair(state, args.org, kind),
    }, indent=2, default=str))
    return 1 if state in ("authorization-lapsed", "authorization-expiring") else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-sso-session-clock.mjs",
"js": '''/**
 * Read the expiry on a SAML credential authorization before it lapses.
 *
 * Read only, and it authorizes nothing. The repair for a lapsed SAML session is
 * a person re-authenticating in a browser; this reports the date that will
 * become necessary and never performs it.
 *
 * Two credentials on purpose: the one in trouble, and an organization owner one
 * that can read GET /orgs/{org}/credential-authorizations, where the dated
 * record lives. The match on token_last_eight happens in memory and those
 * characters are never logged or serialised.
 *
 * Environment:
 *   GITHUB_TOKEN        the credential being diagnosed
 *   GITHUB_ADMIN_TOKEN  an organization owner credential with admin:org
 *   GITHUB_ORG          the organization enforcing SAML
 */
const API = 'https://api.github.com';
const UA = 'github-sso-session-clock/1.0';

export const SSO_HEADER = 'x-github-sso';
export const EXPIRING_SOON_DAYS = 7;

export const TOKEN_PREFIXES = [
  ['github_pat_', 'fine-grained PAT'],
  ['ghp_', 'classic PAT'],
  ['gho_', 'OAuth user token'],
  ['ghu_', 'App user-to-server token'],
  ['ghs_', 'App installation token'],
  ['ghr_', 'App refresh token'],
];

/** Credentials that hang off a person identity-provider session. */
export const LAPSES_WITH_A_PERSON = {
  'classic PAT': true,
  'OAuth user token': true,
  'App user-to-server token': true,
  'fine-grained PAT': true,
  'App installation token': false,
  'App refresh token': false,
  unknown: true,
};

/** Requests this run will spend against the core quota. Pure. */
export function readCost(withAdmin = true, pages = 1) {
  return 2 + (withAdmin ? pages : 0);
}

/** Name the credential from its prefix. Pure. */
export function tokenKind(token) {
  const value = String(token ?? '').trim();
  for (const [prefix, name] of TOKEN_PREFIXES) {
    if (value.startsWith(prefix)) return name;
  }
  return 'unknown';
}

/** The eight characters a record is matched on. Pure, and never printed. */
export function lastEight(token) {
  const value = String(token ?? '').trim();
  return value.length >= 8 ? value.slice(-8) : '';
}

/** Find the record for this credential. Pure. */
export function matchAuthorization(records, tail) {
  if (!tail) return null;
  for (const record of records || []) {
    if (!record || typeof record !== 'object') continue;
    if (String(record.token_last_eight ?? '') === tail) return record;
  }
  return null;
}

/** ISO 8601 into epoch milliseconds, or null. Pure. */
export function parseTs(value) {
  if (!value) return null;
  const ms = Date.parse(String(value));
  return Number.isNaN(ms) ? null : ms;
}

/** Whole days until the grant lapses, negative if it has. Pure. */
export function daysLeft(expiresAt, nowMs) {
  const when = parseTs(expiresAt);
  if (when === null) return null;
  return Math.floor((when - nowMs) / 86400000);
}

/** Classify one credential SAML standing. Pure. [state, detail]. */
export function authorizationState(record, nowMs, refused) {
  if (!record) {
    if (refused) {
      return ['never-authorized', 'no authorization record exists for this '
        + 'credential, so it has never been authorized for this organization. '
        + 'That is a first authorization rather than a lapse.'];
    }
    return ['no-record-no-refusal', 'no authorization record and nothing being '
      + 'refused, which is what an organization without SAML looks like.'];
  }
  const remaining = daysLeft(record.authorized_credential_expires_at, nowMs);
  if (remaining === null) {
    return ['expiry-not-published', 'the record exists but carries no expiry, so '
      + 'this grant is not on a clock the API will show you.'];
  }
  if (remaining < 0) {
    return ['authorization-lapsed', `this authorization expired ${Math.abs(remaining)} `
      + 'day(s) ago. The credential is unchanged and valid; the SAML session '
      + 'behind it ran out.'];
  }
  if (remaining <= EXPIRING_SOON_DAYS) {
    return ['authorization-expiring', `this authorization lapses in ${remaining} `
      + 'day(s). The credential is fine; the SAML session behind it runs out.'];
  }
  return ['authorization-active', `this authorization is good for another ${remaining} day(s).`];
}

/** Did this credential demonstrably work here. Pure. */
export function lapseEvidence(record) {
  if (!record) return [false, 'no record, so there is no evidence of past use.'];
  const used = parseTs(record.credential_accessed_at);
  if (used === null) {
    return [false, 'the record carries no last-used time, so past success is not '
      + 'provable from it.'];
  }
  return [true, `the record was last used at ${new Date(used).toISOString()}, `
    + 'which proves this credential did work against this organization.'];
}

/** What recurrence a reader should expect. Pure. */
export function cadenceNote(state) {
  const clocked = ['authorization-lapsed', 'authorization-expiring',
    'authorization-active'];
  if (clocked.includes(state)) {
    return 'the organization re-authentication interval is not published by the '
      + 'API. What is readable is this grant expiry, and it will recur.';
  }
  return 'nothing to forecast from this reading.';
}

/** Does this credential type depend on a person staying logged in. Pure. */
export function unattendedVerdict(kind) {
  if (LAPSES_WITH_A_PERSON[kind] ?? true) {
    return [true, `a ${kind} hangs off a person identity-provider session, so an `
      + 'unattended job holding one fails whenever that person stops logging in.'];
  }
  return [false, `a ${kind} does not depend on anyone identity-provider session, `
    + 'which is why it is the answer for unattended work.'];
}

/** The sentence a reader has to act on. Pure. */
export function repair(state, org, kind) {
  const [depends] = unattendedVerdict(kind);
  const moveOff = depends ? ' For anything unattended, move to an App '
    + 'installation token, which never lapses with a person session.' : '';
  const renew = `a person re-authenticates at https://github.com/orgs/${org}/sso. `
    + 'This script does not and will not do it.';
  if (state === 'authorization-lapsed') return renew + moveOff;
  if (state === 'authorization-expiring') return `${renew} Do it before that date.${moveOff}`;
  if (state === 'never-authorized') {
    return 'authorize the credential for the first time, which is the sibling '
      + 'problem: the refusal is the same and the repair does not recur.';
  }
  if (state === 'authorization-active') {
    return 'nothing today. Note the date and decide whether an unattended job '
      + 'should depend on a human session at all.';
  }
  if (state === 'expiry-not-published') {
    return 'read the refusal x-github-sso header instead; this record will not '
      + 'tell you when the grant ends.';
  }
  return 'nothing on SAML here.';
}

function headers(token) {
  return {
    Authorization: `Bearer ${token}`,
    Accept: 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
    'User-Agent': UA,
  };
}

async function main() {
  const token = process.env.GITHUB_TOKEN;
  const org = process.env.GITHUB_ORG;
  if (!token || !org) {
    console.error('set GITHUB_TOKEN (the credential being diagnosed) and GITHUB_ORG');
    process.exitCode = 2;
    return;
  }
  const admin = process.env.GITHUB_ADMIN_TOKEN;
  console.log(`read cost: ${readCost(Boolean(admin))} request(s) against the core hourly quota`);

  const kind = tokenKind(token);
  const me = await fetch(`${API}/user`, { headers: headers(token) });
  const account = me.status === 200 ? (await me.json()).login : null;
  console.log(`credential: ${kind}, account=${account ?? 'unreadable'}`);

  const listing = await fetch(`${API}/orgs/${org}/repos?per_page=1`,
    { headers: headers(token) });
  const ssoForm = (listing.headers.get(SSO_HEADER) || '').split(';')[0].trim().toLowerCase();
  console.log(`GET /orgs/${org}/repos -> ${listing.status}, ${SSO_HEADER}: ${ssoForm || 'absent'}`);
  const refused = listing.status === 403 || listing.status === 404;

  let records = [];
  if (admin) {
    const page = await fetch(
      `${API}/orgs/${org}/credential-authorizations?per_page=100`,
      { headers: headers(admin) },
    );
    if (page.status === 200) {
      const body = await page.json();
      records = Array.isArray(body) ? body : [];
    } else {
      console.warn(`credential-authorizations returned HTTP ${page.status}; that `
        + 'endpoint needs admin:org.');
    }
  } else {
    console.warn('no GITHUB_ADMIN_TOKEN, so the dated record cannot be read and a '
      + 'lapse looks exactly like a first authorization.');
  }

  // Compared in memory. These characters are never logged or serialised.
  const record = matchAuthorization(records, lastEight(token));
  console.log(`credential-authorizations: ${records.length} record(s) read, `
    + `${record ? 1 : 0} matched`);

  const now = Date.now();
  const [state, detail] = authorizationState(record, now, refused);
  const [proven, proof] = lapseEvidence(record);
  console.log(`${state}: ${detail}`);
  console.log(`past use: ${proof}`);
  console.log(`cadence: ${cadenceNote(state)}`);
  const [depends, dependsDetail] = unattendedVerdict(kind);
  console.log(`unattended: ${dependsDetail}`);
  console.log(`repair: ${repair(state, org, kind)}`);

  console.log(JSON.stringify({
    organization: org,
    account,
    credential_kind: kind,
    listing_status: listing.status,
    sso_form: ssoForm || null,
    records_read: records.length,
    record_matched: Boolean(record),
    credential_accessed_at: record?.credential_accessed_at ?? null,
    authorized_credential_expires_at: record?.authorized_credential_expires_at ?? null,
    days_left: daysLeft(record?.authorized_credential_expires_at, now),
    state,
    detail,
    past_use_proven: proven,
    depends_on_a_person: depends,
    repair: repair(state, org, kind),
  }, null, 2));
  process.exitCode = ['authorization-lapsed', 'authorization-expiring'].includes(state) ? 1 : 0;
}

// Guarded so importing this file from the test runner does not start a run.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The first assertion is the one that keeps this note honest about its own limit: with no record to read, a lapse and a first authorization are indistinguishable, and the script has to say so rather than pick. Then the clock, which is the whole finding — expired yesterday, expiring in three days, and comfortably active have to be three different sentences with numbers in them. The last group is the discipline: the last eight characters are what the match runs on, so a test asserts they are absent from the report the script prints, because the moment they appear in a CI log they are a fragment of a live credential sitting in a log.",
"test_py_file": "test_github_sso_session_clock.py",
"test_py": '''import json
from datetime import datetime, timedelta, timezone

from github_sso_session_clock import (
    authorization_state, cadence_note, days_left, lapse_evidence, last_eight,
    match_authorization, parse_ts, read_cost, repair, token_kind,
    unattended_verdict,
)

NOW = datetime(2026, 8, 31, 12, 0, 0, tzinfo=timezone.utc)


def record(days, tail="fake1234", used="2026-08-31T04:11:07Z"):
    when = NOW + timedelta(days=days)
    return {
        "credential_id": 161195,
        "credential_type": "personal access token",
        "token_last_eight": tail,
        "credential_accessed_at": used,
        "authorized_credential_expires_at": when.isoformat().replace("+00:00", "Z"),
    }


def test_without_a_record_a_lapse_and_a_first_authorization_are_the_same():
    # The honest limit of this note. No admin credential means no record, and
    # the refusal alone cannot tell the two apart.
    state, detail = authorization_state(None, NOW, refused=True)
    assert state == "never-authorized"
    assert "first authorization rather than a lapse" in detail
    assert authorization_state(None, NOW, refused=False)[0] == "no-record-no-refusal"


def test_the_clock_produces_three_different_sentences():
    assert authorization_state(record(-1), NOW, True)[0] == "authorization-lapsed"
    assert authorization_state(record(3), NOW, False)[0] == "authorization-expiring"
    assert authorization_state(record(30), NOW, False)[0] == "authorization-active"


def test_the_lapsed_verdict_counts_the_days_it_has_been_dead():
    _state, detail = authorization_state(record(-4), NOW, True)
    assert "4 day(s) ago" in detail
    assert "credential is unchanged and valid" in detail


def test_the_expiring_verdict_is_a_forecast_with_a_number_on_it():
    _state, detail = authorization_state(record(3), NOW, False)
    assert "3 day(s)" in detail
    assert days_left(record(3)["authorized_credential_expires_at"], NOW) == 3
    assert days_left(record(-2)["authorized_credential_expires_at"], NOW) == -2


def test_a_record_with_no_expiry_is_not_reported_as_active():
    bare = {"token_last_eight": "fake1234", "credential_accessed_at": None}
    state, _ = authorization_state(bare, NOW, True)
    assert state == "expiry-not-published"


def test_the_match_runs_on_the_last_eight_and_nothing_else():
    tail = last_eight("ghp_fake1234")
    assert tail == "fake1234"
    records = [record(9, tail="other000"), record(2, tail=tail)]
    assert match_authorization(records, tail)["token_last_eight"] == tail
    assert match_authorization(records, "nomatch0") is None
    assert match_authorization(records, "") is None
    assert last_eight("short") == ""


def test_the_last_eight_never_reaches_the_report():
    # The characters identify a record. They are also eight characters of a
    # live credential, so nothing the script prints may contain them.
    tail = last_eight("ghp_fake1234")
    matched = match_authorization([record(5, tail=tail)], tail)
    state, detail = authorization_state(matched, NOW, False)
    report = json.dumps({
        "state": state,
        "detail": detail,
        "record_matched": bool(matched),
        "days_left": days_left(matched["authorized_credential_expires_at"], NOW),
        "repair": repair(state, "acme-corp", "classic PAT"),
        "cadence": cadence_note(state),
    })
    assert tail not in report


def test_past_use_is_what_proves_this_was_a_lapse():
    proven, detail = lapse_evidence(record(-1))
    assert proven is True and "did work against this organization" in detail
    assert lapse_evidence(None)[0] is False
    assert lapse_evidence(record(-1, used=None))[0] is False


def test_the_cadence_is_reported_as_inferred_not_measured():
    note = cadence_note("authorization-expiring")
    assert "not published" in note
    assert "will recur" in note
    assert cadence_note("no-record-no-refusal") == "nothing to forecast from this reading."


def test_an_installation_token_is_the_only_one_that_does_not_lapse():
    depends, detail = unattended_verdict("classic PAT")
    assert depends is True and "stops logging in" in detail
    depends, detail = unattended_verdict("App installation token")
    assert depends is False and "unattended work" in detail


def test_the_repair_renews_and_then_says_stop_renewing():
    fix = repair("authorization-expiring", "acme-corp", "classic PAT")
    assert "https://github.com/orgs/acme-corp/sso" in fix
    assert "does not and will not do it" in fix
    assert "App installation token" in fix
    # Nothing is offered for a credential that does not lapse with a person.
    assert "App installation token" not in repair(
        "authorization-expiring", "acme-corp", "App installation token")


def test_a_missing_record_sends_the_reader_to_the_sibling_note():
    fix = repair("never-authorized", "acme-corp", "classic PAT")
    assert "first time" in fix
    assert "does not recur" in fix


def test_timestamps_survive_both_spellings_of_utc():
    assert parse_ts("2026-09-03T09:22:41Z") == parse_ts("2026-09-03T09:22:41+00:00")
    assert parse_ts("not a date") is None
    assert parse_ts(None) is None


def test_the_credential_type_comes_from_its_prefix():
    assert token_kind("ghp_fake") == "classic PAT"
    assert token_kind("ghs_fake") == "App installation token"
    assert token_kind("nope") == "unknown"


def test_the_run_costs_two_reads_plus_the_record_pages():
    assert read_cost(False) == 2
    assert read_cost(True, 1) == 3
    assert read_cost(True, 3) == 5
''',
"test_js_file": "github-sso-session-clock.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  authorizationState, cadenceNote, daysLeft, lapseEvidence, lastEight,
  matchAuthorization, parseTs, readCost, repair, tokenKind, unattendedVerdict,
} from './github-sso-session-clock.mjs';

const NOW = Date.parse('2026-08-31T12:00:00Z');

function record(days, tail = 'fake1234', used = '2026-08-31T04:11:07Z') {
  return {
    credential_id: 161195,
    credential_type: 'personal access token',
    token_last_eight: tail,
    credential_accessed_at: used,
    authorized_credential_expires_at: new Date(NOW + days * 86400000).toISOString(),
  };
}

test('without a record a lapse and a first authorization are the same', () => {
  assert.equal(authorizationState(null, NOW, true)[0], 'never-authorized');
  assert.equal(authorizationState(null, NOW, false)[0], 'no-record-no-refusal');
});

test('the clock produces three different sentences', () => {
  assert.equal(authorizationState(record(-1), NOW, true)[0], 'authorization-lapsed');
  assert.equal(authorizationState(record(3), NOW, false)[0], 'authorization-expiring');
  assert.equal(authorizationState(record(30), NOW, false)[0], 'authorization-active');
});

test('the expiring verdict is a forecast with a number on it', () => {
  const [, detail] = authorizationState(record(3), NOW, false);
  assert.ok(detail.includes('3 day(s)'));
  assert.equal(daysLeft(record(3).authorized_credential_expires_at, NOW), 3);
  assert.equal(daysLeft(record(-2).authorized_credential_expires_at, NOW), -2);
});

test('a record with no expiry is not reported as active', () => {
  assert.equal(authorizationState({ token_last_eight: 'fake1234' }, NOW, true)[0],
    'expiry-not-published');
});

test('the match runs on the last eight and nothing else', () => {
  const tail = lastEight('ghp_fake1234');
  assert.equal(tail, 'fake1234');
  const records = [record(9, 'other000'), record(2, tail)];
  assert.equal(matchAuthorization(records, tail).token_last_eight, tail);
  assert.equal(matchAuthorization(records, 'nomatch0'), null);
  assert.equal(lastEight('short'), '');
});

test('the last eight never reaches the report', () => {
  const tail = lastEight('ghp_fake1234');
  const matched = matchAuthorization([record(5, tail)], tail);
  const [state, detail] = authorizationState(matched, NOW, false);
  const report = JSON.stringify({
    state, detail, record_matched: Boolean(matched),
    repair: repair(state, 'acme-corp', 'classic PAT'),
    cadence: cadenceNote(state),
  });
  assert.ok(!report.includes(tail));
});

test('past use is what proves this was a lapse', () => {
  assert.equal(lapseEvidence(record(-1))[0], true);
  assert.equal(lapseEvidence(null)[0], false);
  assert.equal(lapseEvidence(record(-1, 'fake1234', null))[0], false);
});

test('the cadence is reported as inferred not measured', () => {
  assert.ok(cadenceNote('authorization-expiring').includes('not published'));
  assert.equal(cadenceNote('no-record-no-refusal'), 'nothing to forecast from this reading.');
});

test('an installation token is the only one that does not lapse', () => {
  assert.equal(unattendedVerdict('classic PAT')[0], true);
  assert.equal(unattendedVerdict('App installation token')[0], false);
});

test('the repair renews and then says stop renewing', () => {
  const fix = repair('authorization-expiring', 'acme-corp', 'classic PAT');
  assert.ok(fix.includes('https://github.com/orgs/acme-corp/sso'));
  assert.ok(fix.includes('does not and will not do it'));
  assert.ok(fix.includes('App installation token'));
  assert.ok(!repair('authorization-expiring', 'acme-corp', 'App installation token')
    .includes('App installation token'));
});

test('timestamps survive both spellings of utc', () => {
  assert.equal(parseTs('2026-09-03T09:22:41Z'), parseTs('2026-09-03T09:22:41+00:00'));
  assert.equal(parseTs('not a date'), null);
});

test('the credential type comes from its prefix', () => {
  assert.equal(tokenKind('ghp_fake'), 'classic PAT');
  assert.equal(tokenKind('ghs_fake'), 'App installation token');
});

test('the run costs two reads plus the record pages', () => {
  assert.equal(readCost(false), 2);
  assert.equal(readCost(true, 3), 5);
});
''',
"faq": [
 ("How do I tell this apart from a token that was never authorized?",
  "By history, and the API will not give you it from the refusal. Both produce the same status, the same message and the same <code>x-github-sso: required</code> header, so nothing on the failing response separates them. The separator is <code>GET /orgs/{org}/credential-authorizations</code>, which needs <code>admin:org</code>: a credential with a record was authorized and its grant has an expiry, and a credential with no record has <a href=\"/github/saml-token-not-authorized/\">never been authorized at all</a>. Without an owner's credential you cannot prove which, and the script says so rather than picking."),
 ("Is this the same as the token itself expiring?",
  "No. <a href=\"/github/token-expiring-soon/\">Token expiry</a> is a property of the credential: it was created with a lifetime, the clock is the token's own, and when it runs out the token is dead everywhere including on your personal repositories. This is a property of a grant between that credential and one organization. The token stays perfectly alive and keeps working on everything else; one organization stops accepting it. Two different clocks, two different repairs, and a token can be well inside its own lifetime while its SAML authorization has already lapsed."),
 ("Why did logging into GitHub in a browser fix the job?",
  "Because the browser login re-authenticated the person with the identity provider, and the credential's authorization is tied to that session. It is the most misleading fix in this section: it is done by a human, in a different application, minutes before somebody reruns the job and concludes the rerun worked. That is how this ends up in a runbook as &ldquo;retry it&rdquo;. It also explains the version of the problem that only happens when one particular person is on holiday, since their daily login was renewing the session for everybody."),
 ("Can the script re-authorize the credential when it sees the expiry coming?",
  "It cannot and it should not. Renewing a SAML session means authenticating a human with an identity provider, which is the control the whole mechanism exists to enforce; a tool that could do it would be a way around the control rather than a feature of it. What the script does instead is give you a date, early enough to act on. If the answer to a date on a calendar is &ldquo;we cannot schedule a human for that&rdquo;, then the finding is not the date, it is that an unattended job is holding the wrong kind of credential."),
 ("Why does the script never print the last eight characters it matched on?",
  "Because they are eight characters of a live credential and the output of a diagnostic script ends up in CI logs, tickets and pasted terminal transcripts. GitHub publishes <code>token_last_eight</code> on its own records for humans to eyeball in a settings page; that is a different context from a log line that gets indexed. The match is done in memory, the report says <code>record_matched: true</code>, and a test asserts those characters do not appear anywhere in what gets printed."),
],
"related": [
 ("/github/saml-token-not-authorized/", "The identical refusal, on a credential never authorized"),
 ("/github/token-expiring-soon/", "The other clock: the credential's own lifetime"),
 ("/github/wrong-identity-token/", "Why automation should not run as a person at all"),
],
"citations": [CITE_SSO_AUTHORIZE, CITE_ORGS_REST, CITE_SAML_ENFORCE, CITE_APP_INSTALL_AUTH],
},
{
"slug": "oauth-app-access-restricted",
"title": "The org restricts OAuth Apps and this one was never approved",
"description": "An org policy blocks OAuth Apps wholesale. The token works on personal repos, 403s on every org resource, and the refusal carries no SSO header at all.",
"h1": "The org restricts OAuth Apps and this one was never approved",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github oauth app access restrictions 403",
             "organization has enabled oauth app access restrictions",
             "github third party application restrictions api",
             "oauth app approval organization github",
             "oauth app blocked org repos 403 personal works"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The integration works. Customers sign in, it reads their repositories, and the reviews are good. Then one customer files a ticket saying it shows them nothing, and their logs show <code>403</code> on every call that touches their organization while the calls against their personal repositories return happily. The token is fine. The scopes are the same ones every other customer granted. The account is a member of the organization and can see all of it in a browser. What is different is a setting neither of you can see from where you are standing: the organization has decided which OAuth Apps may touch its data, and yours is not on the list.",
"short_answer": """<p>An organization can restrict OAuth App access to its data. When that policy is on, an application must be approved by an organization owner before <em>any</em> token it issues can read organization resources, and until then those tokens are refused for that organization while working normally everywhere else.</p>
<p>The finding is a shape, not a header. The same token succeeds on <code>GET /user/repos</code> and is refused on <code>GET /orgs/{org}/repos</code>, the refusal message mentions OAuth App access restrictions, and — the reading that does the real work — there is <strong>no</strong> <code>x-github-sso</code> header on it. A SAML refusal always carries that header. This one never does, which is how you tell a policy about the application apart from a policy about the token.</p>
<p>The repair belongs to an organization owner, who approves the application, or to you, by replacing the OAuth App with a GitHub App whose access is granted per installation instead of by a blanket policy.</p>""",
"problem": """<p>This one is expensive because of who can see it. The organization's OAuth App policy is org-owner territory: a member sees the effect, the app's author sees nothing at all. So the two people trying to solve it are looking at different halves of a picture that only makes sense assembled. The author checks the app's registration, the scopes, the callback URL and the token issuance, and finds everything correct — because everything is correct. The customer checks their own account, sees they are a member with plenty of access, and reasonably concludes the integration is broken.</p>
<p>The support thread that follows is a classic. Reauthorize, says the author. Same result. Try a fresh account, says the author. Same result, because the policy is about the application and not the person. Try a different organization, and it suddenly works, which sends everyone off to look for something unusual about the first organization's repositories. Nothing about the repositories is unusual. A single checkbox in the organization's settings is.</p>
<p>The failing shape also mimics two other problems closely enough to waste days on either. It looks like a missing scope, because it is a 403 that appears on some resources and not others. It looks like SAML enforcement, because it is an organization refusing a valid token. Both of those have loud, readable signals attached — a header naming the scope that would have worked, or a header naming SSO — and this one's distinguishing feature is the absence of both, which is exactly the sort of evidence nobody goes looking for.</p>""",
"why": """<p><strong>The gate is on the application, not on the credential.</strong> Every other refusal in this section is about the token: too narrow, expired, revoked, unauthorized. This is a policy that names your OAuth App and refuses everything it ever issues for that organization. That is why reissuing a token changes nothing, why a different user's token behaves identically, and why the failure is perfectly consistent per organization rather than per account.</p>
<p><strong>The absence of the SAML header is the load-bearing reading.</strong> Both an unapproved OAuth App and an unauthorized token are organizations refusing a valid credential, and both are 403. SAML enforcement always announces itself with <code>x-github-sso</code>; the OAuth restriction never does. So the script records the header's absence explicitly as evidence rather than as a nothing, and refuses to call an OAuth restriction while that header is present.</p>
<p><strong>The message string is corroboration, not proof.</strong> GitHub's wording about OAuth App access restrictions is helpful and it is prose, which means it can be rewritten at any time without warning. A diagnostic that matches only on the sentence breaks silently on the day the sentence changes, and a diagnostic that ignores it throws away the one direct statement of the cause. The script does both: the behavioural shape decides the verdict, the message raises the confidence, and the two are reported separately so a reader can see which they are relying on.</p>
<p><strong>A restricted token can see less than no token at all.</strong> The most vivid evidence in the run is free: read the same organization listing with no credential. Anonymous callers see public repositories, so a run where the anonymous read returns <code>200</code> and the authenticated one returns <code>403</code> is a token being actively refused rather than merely under-privileged. That contrast is impossible to argue with, and it costs nothing against the core quota because unauthenticated requests draw on a separate bucket.</p>
<p><strong>Only a member can run the diagnosis.</strong> This is the honest limit and it needs stating in the output, not in a footnote. The organization's policy is not readable from the app's side at all, so the app's author cannot confirm this even with perfect logs. The script has to be run by somebody holding a token issued to that application, by a member of that organization. If you are the author, this note is the thing to send to your customer.</p>
<p><strong>GitHub Apps do not have this failure mode.</strong> An OAuth App asks for a blanket organization-wide policy decision; a GitHub App is installed on specific accounts and repositories with permissions the installer accepts. The approval is still a human step, but it is part of installing rather than a policy your app has to discover it has fallen foul of, and the App can see its own installations through the API. That is the structural repair when the same ticket arrives from a third customer.</p>""",
"steps": [
 {"h": "Name the credential, because this policy only touches OAuth Apps",
  "body": """<p>The prefix is read locally. OAuth App access restrictions govern tokens issued by an OAuth App, so a token from one is in scope and a fine-grained personal access token or an App installation token is not — those get refused by different mechanisms with different repairs. Naming the credential first stops the whole diagnosis being aimed at the wrong gate.</p>"""},
 {"h": "Take the two-namespace reading that makes the shape",
  "body": """<p><code>GET /user/repos?per_page=1</code> and <code>GET /orgs/{org}/repos?per_page=1</code> with the same token, back to back. Personal succeeding while organization is refused is the signature. Both failing is a credential problem and a different note; both succeeding means nothing is restricted for this application today.</p>"""},
 {"h": "Read the absence of x-github-sso as evidence",
  "body": """<p>The script records whether the SAML header was on the refusal. Present means this is SAML enforcement and the diagnosis stops here with a pointer to the note that owns it. Absent, alongside the two-namespace shape, is what makes it an application-level restriction. The header being missing is a finding, and the script prints it as one rather than saying nothing.</p>"""},
 {"h": "Compare against a request with no credential at all",
  "body": """<p>One unauthenticated read of the same organization listing. If an anonymous caller gets <code>200</code> where the authenticated token gets <code>403</code>, the token is being refused rather than being under-privileged, which is the difference between a policy and a permission. It costs nothing against your core quota because it draws on the unauthenticated bucket instead.</p>"""},
 {"h": "Print who has to act, and say plainly who can even see this",
  "body": """<p>The repair is an organization owner approving the application in the organization's third-party access settings, and the script names that rather than pretending there is an API for it. It also prints the visibility asymmetry: the app's author cannot confirm this from their side, so the run has to happen with a member's token. Nothing here approves, requests approval, or asks anybody for anything.</p>"""},
],
"verify": """<p>Once an owner approves the application, the organization listing starts answering the same token that was refused an hour ago.</p>
<pre><code class="language-bash">GITHUB_TOKEN=$OAUTH_USER_TOKEN python3 github_oauth_app_restriction.py acme-corp
# read cost: 3 request(s) against the core hourly quota, plus 1 unauthenticated
#   request against the separate 60-an-hour anonymous bucket
# credential: OAuth user token, account=dana
# GET /user/repos -> 200
# GET /orgs/acme-corp/repos -> 403
# x-github-sso: absent, and that absence is the finding: a SAML refusal always
#   carries this header
# message: matched the documented OAuth App restriction wording
# anonymous read of the same listing -> 200
# restricted-below-anonymous: this token is refused where no token at all
#   succeeds, so it is being blocked rather than under-privileged
# oauth-app-restricted: acme-corp restricts which OAuth Apps may access its
#   data and this application has not been approved. No scope, no reissued
#   token and no other user account will change that.
# visibility: the application's author cannot see this policy from their side.
#   This run needs a token issued to the app, held by a member of acme-corp.
# repair: an owner of acme-corp approves the application in the organization's
#   third-party access settings. There is no API that grants it and this script
#   does not ask for it. Structurally, a GitHub App is installed per account
#   rather than approved by blanket policy.</code></pre>""",
"code_intro": "The verdict comes from a shape and two absences, which is unusual enough to be worth saying out loud. The shape is one token reading two namespaces. The first absence is <code>x-github-sso</code>, whose presence would make this a SAML problem instead; the script treats not finding it as a positive reading rather than as nothing happening. The second is the lack of any endpoint that publishes the policy, which is why the message string is scored separately as corroboration and why the run ends by naming the person who has to act. The anonymous read at the end is four lines of code and the most convincing line of output.",
"py_file": "github_oauth_app_restriction.py",
"py": '''"""Show that an organization is refusing an application rather than a token.

Read only. GET requests and nothing else, and it approves nothing: approving an
OAuth App for an organization is an owner's decision made in the organization's
settings, there is no API that performs it, and this script neither asks for it
nor pretends to.

The verdict is a behavioural shape plus two absences. One token reads two
namespaces, personal and organization; a refusal on the second while the first
succeeds is the shape. The refusal carrying no x-github-sso header is the first
absence, and it is what separates an application-level policy from SAML
enforcement. The lack of any endpoint that publishes the policy is the second,
which is why the message string is scored as corroboration rather than proof.

What this can and cannot see: it can prove that this organization refuses this
credential where an anonymous caller succeeds, and that GitHub did not
attribute the refusal to SAML. It cannot read the organization's OAuth App
policy, because that needs owner access, and it cannot be run usefully by the
application's author at all -- the policy is invisible from the app's side. Run
it with a token issued to the application, held by a member of the
organization.

Environment:

    GITHUB_TOKEN    a token issued by the OAuth App, held by an org member
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_oauth_app_restriction")

API = "https://api.github.com"
UA = "github-oauth-app-restriction/1.0"

SSO_HEADER = "x-github-sso"
ACCEPTED_SCOPES_HEADER = "x-accepted-oauth-scopes"

TOKEN_PREFIXES = (
    ("github_pat_", "fine-grained PAT"),
    ("ghp_", "classic PAT"),
    ("gho_", "OAuth user token"),
    ("ghu_", "App user-to-server token"),
    ("ghs_", "App installation token"),
    ("ghr_", "App refresh token"),
)

# Credentials this policy can actually govern. It restricts OAuth Apps, so a
# token issued by one is in scope and the rest are refused, when they are
# refused, by other mechanisms with other repairs.
GOVERNED_BY_OAUTH_POLICY = {
    "OAuth user token": True,
    "unknown": True,
    "classic PAT": False,
    "fine-grained PAT": False,
    "App user-to-server token": False,
    "App installation token": False,
    "App refresh token": False,
}

# Corroboration only. This is prose written by GitHub and it can be reworded
# without warning, so matching it raises confidence and never decides the
# verdict on its own.
RESTRICTION_PHRASES = (
    "oauth app access restrictions",
    "oauth application access restrictions",
    "third-party application",
    "has not been granted access",
)


def read_cost():
    """Authenticated requests this run spends. Pure.

    The anonymous read is deliberately not counted here: it draws on the
    separate 60-an-hour unauthenticated bucket rather than on core quota.
    """
    return 3


def token_kind(token):
    """Name the credential from its prefix. Pure; nothing leaves the machine."""
    value = (token or "").strip()
    for prefix, name in TOKEN_PREFIXES:
        if value.startswith(prefix):
            return name
    return "unknown"


def governed(kind):
    """Can this policy apply to this credential at all. Pure. (bool, detail)."""
    if GOVERNED_BY_OAUTH_POLICY.get(kind, True):
        return (True, "this policy governs tokens issued by an OAuth App, and "
                      "a %s is one of those." % kind)
    return (False, "a %s is not issued by an OAuth App, so this policy does not "
                   "govern it. A refusal here has another cause and another "
                   "note." % kind)


def message_signature(message):
    """Score the refusal's prose. Pure. (matched, phrase or None).

    Deliberately a list of substrings rather than one exact sentence, because
    the wording is not an API contract and a diagnostic that hangs on it breaks
    silently the day it is edited.
    """
    text = str(message or "").lower()
    for phrase in RESTRICTION_PHRASES:
        if phrase in text:
            return (True, phrase)
    return (False, None)


def namespace_shape(personal_status, org_status):
    """The two-namespace reading. Pure. (state, detail)."""
    personal_ok = personal_status == 200
    org_refused = org_status in (403, 404)
    if personal_ok and org_refused:
        return ("personal-ok-org-refused",
                "the same token reads personal repositories and is refused on "
                "this organization, which is a gate around the organization "
                "rather than a problem with the credential.")
    if not personal_ok and org_refused:
        return ("refused-everywhere",
                "the token is refused on personal repositories too, so this is "
                "the credential rather than any organization policy.")
    if personal_ok and not org_refused:
        return ("nothing-refused",
                "both namespaces answered, so nothing is being restricted for "
                "this application today.")
    return ("unclassified-shape",
            "the pair of reads does not match a shape this script knows how to "
            "name; report both statuses rather than guessing.")


def anonymous_contrast(anon_status, token_status):
    """Compare a credentialled read against no credential at all. Pure."""
    if anon_status == 200 and token_status in (403, 404):
        return ("restricted-below-anonymous",
                "this token is refused where no token at all succeeds, so it is "
                "being blocked rather than being under-privileged.")
    if anon_status in (403, 404) and token_status in (403, 404):
        return ("private-to-everyone",
                "an anonymous caller cannot see this organization's listing "
                "either, so the contrast proves nothing here. The organization "
                "may simply have no public repositories.")
    return ("no-contrast",
            "the authenticated read succeeded, so there is nothing to contrast.")


def discriminate(shape, sso_form, accepted_scopes, matched, kind):
    """The verdict. Pure. (state, detail).

    Order matters. SAML is checked first because its header is unambiguous, the
    scope header second because it names its own repair, and the OAuth
    restriction last because it is the diagnosis of exclusion -- established by
    a shape and by what is missing.
    """
    ok, _detail = governed(kind)
    if sso_form:
        return ("saml-not-oauth-restriction",
                "the refusal carries x-github-sso, so this is SAML enforcement "
                "and not an application policy. Two different notes, and the "
                "header settles which.")
    if accepted_scopes:
        return ("scope-shaped-refusal",
                "the refusal names the scopes it accepts in "
                "x-accepted-oauth-scopes, which an application restriction does "
                "not do. Diff that against what the token holds first.")
    if shape == "refused-everywhere":
        return ("credential-problem",
                "the token is refused in its own namespace, so nothing about "
                "an organization's policy explains it.")
    if shape == "nothing-refused":
        return ("not-restricted",
                "this application is reaching the organization's resources "
                "right now.")
    if shape != "personal-ok-org-refused":
        return ("undetermined",
                "the reads do not form a shape this script will put a name to.")
    if not ok:
        return ("not-an-oauth-app-credential",
                "the shape is right but the credential is not one this policy "
                "governs, so look for an organization gate that applies to this "
                "credential type instead.")
    if matched:
        return ("oauth-app-restricted",
                "this organization restricts which OAuth Apps may access its "
                "data and this application has not been approved. No scope, no "
                "reissued token and no other user account will change that.")
    return ("oauth-app-restricted-likely",
            "the shape is exactly an application restriction and the refusal's "
            "wording did not match anything known, which happens when GitHub "
            "rewords a message. Treat the shape as the finding and the wording "
            "as unavailable corroboration.")


def visibility_note():
    """Who can and cannot run this diagnosis. Pure."""
    return ("the application's author cannot see this policy from their side. "
            "This run needs a token issued to the app, held by a member of the "
            "organization.")


def repair(state, org):
    """The sentence a reader has to act on. Pure."""
    if state in ("oauth-app-restricted", "oauth-app-restricted-likely"):
        return ("an owner of %s approves the application in the organization's "
                "third-party access settings. There is no API that grants it "
                "and this script does not ask for it. Structurally, a GitHub "
                "App is installed per account rather than approved by blanket "
                "policy, which removes this failure mode." % org)
    if state == "saml-not-oauth-restriction":
        return ("authorize the credential for the organization through the URL "
                "in the x-github-sso header; that is a different repair.")
    if state == "scope-shaped-refusal":
        return ("compare the accepted scopes against the ones the token holds "
                "and mint the narrowest one that closes the gap.")
    if state == "credential-problem":
        return ("fix the credential first; no organization policy is in play "
                "while personal reads are failing too.")
    if state == "not-an-oauth-app-credential":
        return ("find the gate that applies to this credential type. An OAuth "
                "App policy is not it.")
    if state == "not-restricted":
        return "nothing. This application is not being restricted by %s." % org
    return ("report both statuses and the headers; this run did not reach a "
            "verdict worth acting on.")


def get(session, url):
    """One GET. Returns the response object."""
    r = session.get(url, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from GitHub: GITHUB_TOKEN is missing, malformed "
                         "or revoked. That is a different note.")
    return r


def body_message(response):
    """The API's message string, if the body has one. Pure enough."""
    try:
        payload = response.json()
    except ValueError:
        return ""
    return (payload or {}).get("message", "") if isinstance(payload, dict) else ""


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("org", help="the organization refusing the application")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_TOKEN (a read-only token issued by the app)")
        return 2

    log.info("read cost: %d request(s) against the core hourly quota, plus 1 "
             "unauthenticated request against the separate 60-an-hour "
             "anonymous bucket", read_cost())

    common = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        # GitHub rejects requests with no User-Agent outright.
        "User-Agent": UA,
    }
    session = requests.Session()
    session.headers.update(dict(common, Authorization="Bearer " + token))

    kind = token_kind(token)
    me = get(session, API + "/user")
    account = (me.json() or {}).get("login") if me.status_code == 200 else None
    log.info("credential: %s, account=%s", kind, account or "unreadable")

    personal = get(session, API + "/user/repos?per_page=1")
    log.info("GET /user/repos -> %s", personal.status_code)

    org_listing = get(session, API + "/orgs/%s/repos?per_page=1" % args.org)
    log.info("GET /orgs/%s/repos -> %s", args.org, org_listing.status_code)

    sso_form = (org_listing.headers.get(SSO_HEADER) or "").split(";")[0].strip().lower()
    accepted = org_listing.headers.get(ACCEPTED_SCOPES_HEADER)
    log.info("%s: %s", SSO_HEADER,
             sso_form or "absent, and that absence is the finding: a SAML "
                         "refusal always carries this header")
    matched, phrase = message_signature(body_message(org_listing))
    log.info("message: %s", "matched the documented OAuth App restriction "
                            "wording" if matched else "did not match any known "
                            "restriction wording")

    anonymous = requests.Session()
    anonymous.headers.update(common)
    anon = anonymous.get(API + "/orgs/%s/repos?per_page=1" % args.org, timeout=30)
    log.info("anonymous read of the same listing -> %s", anon.status_code)
    contrast_state, contrast_detail = anonymous_contrast(
        anon.status_code, org_listing.status_code)
    log.info("%s: %s", contrast_state, contrast_detail)

    shape, shape_detail = namespace_shape(personal.status_code,
                                          org_listing.status_code)
    log.info("%s: %s", shape, shape_detail)

    state, detail = discriminate(shape, sso_form, accepted, matched, kind)
    log.info("%s: %s", state, detail)
    log.info("visibility: %s", visibility_note())
    log.info("repair: %s", repair(state, args.org))

    print(json.dumps({
        "organization": args.org,
        "account": account,
        "credential_kind": kind,
        "personal_status": personal.status_code,
        "org_status": org_listing.status_code,
        "anonymous_status": anon.status_code,
        "sso_header": sso_form or None,
        "accepted_scopes_header": accepted,
        "message_matched": matched,
        "message_phrase": phrase,
        "shape": shape,
        "contrast": contrast_state,
        "state": state,
        "detail": detail,
        "visibility": visibility_note(),
        "repair": repair(state, args.org),
    }, indent=2, default=str))
    return 1 if state.startswith("oauth-app-restricted") else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-oauth-app-restriction.mjs",
"js": '''/**
 * Show that an organization is refusing an application rather than a token.
 *
 * Read only, and it approves nothing: approving an OAuth App for an
 * organization is an owner decision made in the organization settings, there is
 * no API that performs it, and this script neither asks for it nor pretends to.
 *
 * The verdict is a behavioural shape plus two absences: one token reading two
 * namespaces, a refusal with no x-github-sso header on it, and no endpoint
 * anywhere that publishes the policy.
 *
 * Environment:
 *   GITHUB_TOKEN    a token issued by the OAuth App, held by an org member
 *   GITHUB_ORG      the organization refusing the application
 */
const API = 'https://api.github.com';
const UA = 'github-oauth-app-restriction/1.0';

export const SSO_HEADER = 'x-github-sso';
export const ACCEPTED_SCOPES_HEADER = 'x-accepted-oauth-scopes';

export const TOKEN_PREFIXES = [
  ['github_pat_', 'fine-grained PAT'],
  ['ghp_', 'classic PAT'],
  ['gho_', 'OAuth user token'],
  ['ghu_', 'App user-to-server token'],
  ['ghs_', 'App installation token'],
  ['ghr_', 'App refresh token'],
];

/** Credentials this policy can actually govern. */
export const GOVERNED_BY_OAUTH_POLICY = {
  'OAuth user token': true,
  unknown: true,
  'classic PAT': false,
  'fine-grained PAT': false,
  'App user-to-server token': false,
  'App installation token': false,
  'App refresh token': false,
};

/** Corroboration only. GitHub prose can be reworded without warning. */
export const RESTRICTION_PHRASES = [
  'oauth app access restrictions',
  'oauth application access restrictions',
  'third-party application',
  'has not been granted access',
];

/** Authenticated requests this run spends. The anonymous read is separate. */
export function readCost() {
  return 3;
}

/** Name the credential from its prefix. Pure. */
export function tokenKind(token) {
  const value = String(token ?? '').trim();
  for (const [prefix, name] of TOKEN_PREFIXES) {
    if (value.startsWith(prefix)) return name;
  }
  return 'unknown';
}

/** Can this policy apply to this credential at all. Pure. */
export function governed(kind) {
  if (GOVERNED_BY_OAUTH_POLICY[kind] ?? true) {
    return [true, `this policy governs tokens issued by an OAuth App, and a ${kind} is one.`];
  }
  return [false, `a ${kind} is not issued by an OAuth App, so this policy does `
    + 'not govern it. A refusal here has another cause and another note.'];
}

/** Score the refusal prose. Pure. [matched, phrase]. */
export function messageSignature(message) {
  const text = String(message ?? '').toLowerCase();
  for (const phrase of RESTRICTION_PHRASES) {
    if (text.includes(phrase)) return [true, phrase];
  }
  return [false, null];
}

/** The two-namespace reading. Pure. */
export function namespaceShape(personalStatus, orgStatus) {
  const personalOk = personalStatus === 200;
  const orgRefused = orgStatus === 403 || orgStatus === 404;
  if (personalOk && orgRefused) {
    return ['personal-ok-org-refused', 'the same token reads personal '
      + 'repositories and is refused on this organization, which is a gate '
      + 'around the organization rather than a problem with the credential.'];
  }
  if (!personalOk && orgRefused) {
    return ['refused-everywhere', 'the token is refused on personal repositories '
      + 'too, so this is the credential rather than any organization policy.'];
  }
  if (personalOk && !orgRefused) {
    return ['nothing-refused', 'both namespaces answered, so nothing is being '
      + 'restricted for this application today.'];
  }
  return ['unclassified-shape', 'the pair of reads does not match a shape this '
    + 'script knows how to name.'];
}

/** Compare a credentialled read against no credential at all. Pure. */
export function anonymousContrast(anonStatus, tokenStatus) {
  const refused = tokenStatus === 403 || tokenStatus === 404;
  if (anonStatus === 200 && refused) {
    return ['restricted-below-anonymous', 'this token is refused where no token '
      + 'at all succeeds, so it is being blocked rather than under-privileged.'];
  }
  if ((anonStatus === 403 || anonStatus === 404) && refused) {
    return ['private-to-everyone', 'an anonymous caller cannot see this listing '
      + 'either, so the contrast proves nothing here.'];
  }
  return ['no-contrast', 'the authenticated read succeeded, so there is nothing '
    + 'to contrast.'];
}

/** The verdict. Pure. [state, detail]. */
export function discriminate(shape, ssoForm, acceptedScopes, matched, kind) {
  const [ok] = governed(kind);
  if (ssoForm) {
    return ['saml-not-oauth-restriction', 'the refusal carries x-github-sso, so '
      + 'this is SAML enforcement and not an application policy.'];
  }
  if (acceptedScopes) {
    return ['scope-shaped-refusal', 'the refusal names the scopes it accepts in '
      + 'x-accepted-oauth-scopes, which an application restriction does not do.'];
  }
  if (shape === 'refused-everywhere') {
    return ['credential-problem', 'the token is refused in its own namespace, so '
      + 'no organization policy explains it.'];
  }
  if (shape === 'nothing-refused') {
    return ['not-restricted', 'this application is reaching the organization '
      + 'resources right now.'];
  }
  if (shape !== 'personal-ok-org-refused') {
    return ['undetermined', 'the reads do not form a shape this script will put '
      + 'a name to.'];
  }
  if (!ok) {
    return ['not-an-oauth-app-credential', 'the shape is right but the credential '
      + 'is not one this policy governs.'];
  }
  if (matched) {
    return ['oauth-app-restricted', 'this organization restricts which OAuth Apps '
      + 'may access its data and this application has not been approved. No '
      + 'scope, no reissued token and no other user account will change that.'];
  }
  return ['oauth-app-restricted-likely', 'the shape is exactly an application '
    + 'restriction and the wording did not match anything known, which happens '
    + 'when GitHub rewords a message.'];
}

/** Who can and cannot run this diagnosis. Pure. */
export function visibilityNote() {
  return 'the application author cannot see this policy from their side. This run '
    + 'needs a token issued to the app, held by a member of the organization.';
}

/** The sentence a reader has to act on. Pure. */
export function repair(state, org) {
  if (state === 'oauth-app-restricted' || state === 'oauth-app-restricted-likely') {
    return `an owner of ${org} approves the application in the organization `
      + 'third-party access settings. There is no API that grants it and this '
      + 'script does not ask for it. Structurally, a GitHub App is installed per '
      + 'account rather than approved by blanket policy.';
  }
  if (state === 'saml-not-oauth-restriction') {
    return 'authorize the credential through the URL in the x-github-sso header.';
  }
  if (state === 'scope-shaped-refusal') {
    return 'compare the accepted scopes against the ones the token holds.';
  }
  if (state === 'credential-problem') {
    return 'fix the credential first; no organization policy is in play.';
  }
  if (state === 'not-an-oauth-app-credential') {
    return 'find the gate that applies to this credential type.';
  }
  if (state === 'not-restricted') {
    return `nothing. This application is not being restricted by ${org}.`;
  }
  return 'report both statuses and the headers; this run reached no verdict.';
}

function headers(token) {
  const common = {
    Accept: 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
    'User-Agent': UA,
  };
  return token ? { ...common, Authorization: `Bearer ${token}` } : common;
}

async function main() {
  const token = process.env.GITHUB_TOKEN;
  const org = process.env.GITHUB_ORG;
  if (!token || !org) {
    console.error('set GITHUB_TOKEN (issued by the app) and GITHUB_ORG');
    process.exitCode = 2;
    return;
  }
  console.log(`read cost: ${readCost()} request(s) against the core hourly quota, `
    + 'plus 1 unauthenticated request against the separate anonymous bucket');

  const kind = tokenKind(token);
  const me = await fetch(`${API}/user`, { headers: headers(token) });
  const account = me.status === 200 ? (await me.json()).login : null;
  console.log(`credential: ${kind}, account=${account ?? 'unreadable'}`);

  const personal = await fetch(`${API}/user/repos?per_page=1`, { headers: headers(token) });
  console.log(`GET /user/repos -> ${personal.status}`);

  const orgListing = await fetch(`${API}/orgs/${org}/repos?per_page=1`,
    { headers: headers(token) });
  console.log(`GET /orgs/${org}/repos -> ${orgListing.status}`);

  const ssoForm = (orgListing.headers.get(SSO_HEADER) || '').split(';')[0].trim().toLowerCase();
  const accepted = orgListing.headers.get(ACCEPTED_SCOPES_HEADER);
  console.log(`${SSO_HEADER}: ${ssoForm || 'absent, and that absence is the finding'}`);

  let message = '';
  try {
    const body = await orgListing.json();
    message = body && typeof body === 'object' ? (body.message || '') : '';
  } catch { message = ''; }
  const [matched, phrase] = messageSignature(message);
  console.log(`message: ${matched ? 'matched the documented restriction wording'
    : 'did not match any known restriction wording'}`);

  const anon = await fetch(`${API}/orgs/${org}/repos?per_page=1`, { headers: headers(null) });
  console.log(`anonymous read of the same listing -> ${anon.status}`);
  const [contrastState, contrastDetail] = anonymousContrast(anon.status, orgListing.status);
  console.log(`${contrastState}: ${contrastDetail}`);

  const [shape, shapeDetail] = namespaceShape(personal.status, orgListing.status);
  console.log(`${shape}: ${shapeDetail}`);
  const [state, detail] = discriminate(shape, ssoForm, accepted, matched, kind);
  console.log(`${state}: ${detail}`);
  console.log(`visibility: ${visibilityNote()}`);
  console.log(`repair: ${repair(state, org)}`);

  console.log(JSON.stringify({
    organization: org,
    account,
    credential_kind: kind,
    personal_status: personal.status,
    org_status: orgListing.status,
    anonymous_status: anon.status,
    sso_header: ssoForm || null,
    accepted_scopes_header: accepted,
    message_matched: matched,
    message_phrase: phrase,
    shape,
    contrast: contrastState,
    state,
    detail,
    visibility: visibilityNote(),
    repair: repair(state, org),
  }, null, 2));
  process.exitCode = state.startsWith('oauth-app-restricted') ? 1 : 0;
}

// Guarded so importing this file from the test runner does not start a run.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Two of these tests exist to stop this note eating its neighbours. A refusal carrying <code>x-github-sso</code> has to come back as SAML no matter how perfectly the rest of the evidence fits an application restriction, and a refusal carrying <code>x-accepted-oauth-scopes</code> has to come back as a scope problem for the same reason: both of those name their own repair, and a diagnosis of exclusion must never outrank a direct statement. The rest asserts that the verdict survives GitHub rewording its message — the shape still decides, the wording only raises confidence — and that a token refused where an anonymous caller succeeds is reported as blocked rather than as under-privileged.",
"test_py_file": "test_github_oauth_app_restriction.py",
"test_py": '''from github_oauth_app_restriction import (
    anonymous_contrast, discriminate, governed, message_signature,
    namespace_shape, read_cost, repair, token_kind, visibility_note,
)

RESTRICTED = ("Although you appear to have the correct authorization "
              "credentials, the acme-corp organization has enabled OAuth App "
              "access restrictions.")


def test_the_shape_is_one_token_reading_two_namespaces():
    state, detail = namespace_shape(200, 403)
    assert state == "personal-ok-org-refused"
    assert "rather than a problem with the credential" in detail
    assert namespace_shape(403, 403)[0] == "refused-everywhere"
    assert namespace_shape(200, 200)[0] == "nothing-refused"


def test_a_saml_header_outranks_every_other_piece_of_evidence():
    # Even with the perfect shape and the exact message, a refusal that names
    # SSO is the other note. A diagnosis of exclusion never beats a statement.
    matched, _ = message_signature(RESTRICTED)
    state, detail = discriminate("personal-ok-org-refused", "required", None,
                                 matched, "OAuth user token")
    assert state == "saml-not-oauth-restriction"
    assert "x-github-sso" in detail


def test_an_accepted_scopes_header_outranks_it_too():
    state, _ = discriminate("personal-ok-org-refused", "", "repo, read:org",
                            True, "OAuth user token")
    assert state == "scope-shaped-refusal"


def test_the_verdict_survives_github_rewording_the_message():
    matched, phrase = message_signature(RESTRICTED)
    assert matched is True and phrase == "oauth app access restrictions"
    confident, _ = discriminate("personal-ok-org-refused", "", None, matched,
                                "OAuth user token")
    assert confident == "oauth-app-restricted"
    # Same shape, message reworded into something unrecognised. The shape still
    # decides; only the confidence drops.
    silent, detail = message_signature("Something entirely new was written here")
    assert silent is False and detail is None
    likely, why = discriminate("personal-ok-org-refused", "", None, silent,
                               "OAuth user token")
    assert likely == "oauth-app-restricted-likely"
    assert "rewords" in why


def test_a_token_refused_below_anonymous_is_blocked_not_underprivileged():
    state, detail = anonymous_contrast(200, 403)
    assert state == "restricted-below-anonymous"
    assert "no token at all succeeds" in detail
    assert anonymous_contrast(404, 403)[0] == "private-to-everyone"
    assert anonymous_contrast(200, 200)[0] == "no-contrast"


def test_only_an_oauth_app_credential_is_governed_by_this_policy():
    ok, _ = governed("OAuth user token")
    assert ok is True
    ok, detail = governed("App installation token")
    assert ok is False and "not issued by an OAuth App" in detail
    state, _ = discriminate("personal-ok-org-refused", "", None, True,
                            "App installation token")
    assert state == "not-an-oauth-app-credential"


def test_a_credential_failing_everywhere_is_never_an_org_policy():
    state, _ = discriminate("refused-everywhere", "", None, True, "OAuth user token")
    assert state == "credential-problem"
    assert "no organization policy is in play" in repair(state, "acme-corp")


def test_the_repair_names_a_person_and_denies_an_api():
    fix = repair("oauth-app-restricted", "acme-corp")
    assert "an owner of acme-corp approves the application" in fix
    assert "no API that grants it" in fix
    assert "does not ask for it" in fix
    assert "GitHub App" in fix


def test_the_visibility_limit_is_part_of_the_output():
    note = visibility_note()
    assert "author cannot see this policy" in note
    assert "member of the" in note


def test_the_credential_type_comes_from_its_prefix():
    assert token_kind("gho_fake") == "OAuth user token"
    assert token_kind("ghs_fake") == "App installation token"
    assert token_kind("nope") == "unknown"


def test_the_anonymous_read_is_not_charged_to_core_quota():
    assert read_cost() == 3
''',
"test_js_file": "github-oauth-app-restriction.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  anonymousContrast, discriminate, governed, messageSignature, namespaceShape,
  readCost, repair, tokenKind, visibilityNote,
} from './github-oauth-app-restriction.mjs';

const RESTRICTED = 'Although you appear to have the correct authorization '
  + 'credentials, the acme-corp organization has enabled OAuth App access restrictions.';

test('the shape is one token reading two namespaces', () => {
  assert.equal(namespaceShape(200, 403)[0], 'personal-ok-org-refused');
  assert.equal(namespaceShape(403, 403)[0], 'refused-everywhere');
  assert.equal(namespaceShape(200, 200)[0], 'nothing-refused');
});

test('a saml header outranks every other piece of evidence', () => {
  const [matched] = messageSignature(RESTRICTED);
  assert.equal(
    discriminate('personal-ok-org-refused', 'required', null, matched, 'OAuth user token')[0],
    'saml-not-oauth-restriction',
  );
});

test('an accepted scopes header outranks it too', () => {
  assert.equal(
    discriminate('personal-ok-org-refused', '', 'repo, read:org', true, 'OAuth user token')[0],
    'scope-shaped-refusal',
  );
});

test('the verdict survives github rewording the message', () => {
  const [matched, phrase] = messageSignature(RESTRICTED);
  assert.equal(matched, true);
  assert.equal(phrase, 'oauth app access restrictions');
  assert.equal(
    discriminate('personal-ok-org-refused', '', null, matched, 'OAuth user token')[0],
    'oauth-app-restricted',
  );
  const [silent] = messageSignature('Something entirely new was written here');
  assert.equal(silent, false);
  assert.equal(
    discriminate('personal-ok-org-refused', '', null, silent, 'OAuth user token')[0],
    'oauth-app-restricted-likely',
  );
});

test('a token refused below anonymous is blocked not underprivileged', () => {
  assert.equal(anonymousContrast(200, 403)[0], 'restricted-below-anonymous');
  assert.equal(anonymousContrast(404, 403)[0], 'private-to-everyone');
  assert.equal(anonymousContrast(200, 200)[0], 'no-contrast');
});

test('only an oauth app credential is governed by this policy', () => {
  assert.equal(governed('OAuth user token')[0], true);
  assert.equal(governed('App installation token')[0], false);
  assert.equal(
    discriminate('personal-ok-org-refused', '', null, true, 'App installation token')[0],
    'not-an-oauth-app-credential',
  );
});

test('the repair names a person and denies an api', () => {
  const fix = repair('oauth-app-restricted', 'acme-corp');
  assert.ok(fix.includes('an owner of acme-corp approves the application'));
  assert.ok(fix.includes('no API that grants it'));
  assert.ok(fix.includes('does not ask for it'));
});

test('the visibility limit is part of the output', () => {
  assert.ok(visibilityNote().includes('cannot see this policy'));
});

test('the credential type comes from its prefix', () => {
  assert.equal(tokenKind('gho_fake'), 'OAuth user token');
  assert.equal(tokenKind('nope'), 'unknown');
});

test('the anonymous read is not charged to core quota', () => {
  assert.equal(readCost(), 3);
});
''',
"faq": [
 ("Why does the same app work for one customer and not another?",
  "Because the policy belongs to the organization, not to your application or to their account. An organization that has turned on OAuth App access restrictions blocks every app it has not approved, and one that has not turned them on blocks nothing. So your integration behaves perfectly for nine customers and is invisible to the tenth, with identical code, identical scopes and identical tokens. It is also why reauthorizing, reissuing the token or trying another member of the same organization changes nothing at all."),
 ("How is this different from the SAML refusals?",
  "SAML enforcement refuses a <em>token</em> that a person has not authorized for the organization, and it always says so in the <code>x-github-sso</code> header. This refuses an <em>application</em> that an owner has not approved, and it never sends that header. The practical consequence is different too: under SAML, each user authorizes their own credential and the app is fine; under an OAuth App restriction, no user can fix it for themselves no matter how many times they click, because the decision is about your app and is made once for the whole organization."),
 ("I am the app's author. Can I detect this from my side?",
  "Not directly, and that is the most frustrating property of this problem. The organization's application policy is not exposed to the app, so from where you stand a restricted organization looks like a customer whose calls return 403 for no visible reason. What you can do is instrument the shape: log when a token succeeds against <code>/user/repos</code> and fails against an organization endpoint with no <code>x-github-sso</code> header, and surface that to the customer as a message naming the approval step. The diagnosis has to run on their side; the explanation can come from yours."),
 ("Is the message string reliable enough to match on?",
  "It is worth reading and not worth depending on. GitHub's wording here is unusually explicit, which makes it excellent corroboration, but it is prose rather than an API contract and it has been edited before. A checker built only on the sentence goes quietly wrong the day it changes — quietly, because it will simply stop finding anything. The script scores the message separately from the verdict, so a rewording downgrades the finding from confident to likely instead of erasing it."),
 ("What does moving to a GitHub App actually change?",
  "It replaces a blanket organization policy with an installation. A GitHub App is installed on an account, on selected repositories, with permissions the installer accepts, and the App can read its own installations through the API — so the equivalent of this problem is visible to you rather than only to your customer. The human approval does not disappear, and should not; what disappears is the situation where the approval is invisible from both sides at once, along with the token-per-user model that made the failure look like it was about credentials."),
],
"related": [
 ("/github/saml-token-not-authorized/", "The refusal that does carry an SSO header"),
 ("/github/missing-oauth-scope/", "When the refusal names the scope it wanted"),
 ("/github/oauth-token-revoked-by-user/", "One user revoking your app, not an org blocking it"),
],
"citations": [CITE_OAUTH_RESTRICTIONS, CITE_OAUTH_APPROVE, CITE_APPS_DIFFERENCES, CITE_REST_TROUBLESHOOT],
},
{
"slug": "fine-grained-pat-pending-approval",
"title": "A fine-grained token that is waiting for an org owner",
"description": "GET /user works, the permissions are right, and every org resource 403s. A pending approval fails per owner; a missing permission fails per endpoint.",
"h1": "A fine-grained token that is waiting for an org owner",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["fine grained pat pending approval organization",
             "github fine-grained token 403 on org repos",
             "personal access token requires approval owner",
             "github personal-access-token-requests api",
             "fine grained token works personal fails org"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The token was created this morning. The permissions were ticked carefully against the documentation, the resource owner was set to the organization, and the settings page shows it exists with everything it needs. <code>GET /user</code> returns <code>200</code>. Reads against your own repositories return <code>200</code>. Every single call that touches the organization returns <code>403</code>, or <code>404</code>, and the permission the endpoint names is one the token visibly holds. Nothing is missing. The token is sitting in a queue waiting for an organization owner to approve it, and the API has no interest in telling you that.",
"short_answer": """<p>An organization can require owner approval for any fine-grained personal access token that targets its resources. Until somebody approves the request, the token holds its permissions on paper and none of them in practice — it authenticates perfectly and is refused on everything the organization owns.</p>
<p>The tell is the <em>shape</em> of the failures, not any header. A missing permission fails one endpoint family everywhere: issues are refused on your own repositories too. A pending approval fails every endpoint family in one namespace: repositories, issues and members all refused under the organization while personal reads succeed. One is endpoint-shaped, the other is owner-shaped, and a handful of cheap GETs tells them apart.</p>
<p>Where an owner's credential is available, <code>GET /orgs/{org}/personal-access-token-requests</code> lists the waiting requests and settles it outright. The repair is a person approving one; there is nothing to re-request, because the request already exists.</p>""",
"problem": """<p>The reason this eats a day is that every instinct is to fix the token, and the token is already correct. The 403 mentions a permission, the permission is right there on the settings page with a tick beside it, so the natural conclusion is that the tick did not take. Somebody edits the token. Nothing changes. Somebody deletes it and makes a new one, which feels like progress and is actually the worst available move: creating a token against an organization that requires approval simply files a second request behind the first, so the queue got longer and the wait started over.</p>
<p>Meanwhile the evidence looks contradictory in a way that invites theories. The credential authenticates, which rules out most things. It reads personal repositories, which rules out most of the rest. It fails on organization resources with a message about permissions it demonstrably has. People start suspecting propagation delay, then caching, then the organization's SAML setup, then a GitHub incident. All of those are reasonable guesses about a system that is behaving exactly as designed and simply has not told anyone.</p>
<p>The last twist is who is waiting on whom. The approval request landed in an organization owner's settings page, which for a large organization is a list nobody reads daily and for a small one is a page whose existence is not widely known. Nobody was notified in a way that felt urgent. So the engineer waits for a system to finish something, the owner has no idea anybody is blocked, and the fix is a click that takes four seconds once somebody says the word &ldquo;approve&rdquo; out loud.</p>""",
"why": """<p><strong>Permissions and admission are two separate questions.</strong> A fine-grained token's permissions describe what it may do <em>if</em> it is allowed near a resource owner at all. The organization's token policy decides whether it is allowed near. That is why the settings page and the refusal can both be telling the truth simultaneously, and why nothing you change on the token moves the answer: the token was never the disputed thing.</p>
<p><strong>The refusal's header cannot settle it, and knowing why saves the afternoon.</strong> <code>x-accepted-github-permissions</code> names what the <em>endpoint</em> accepts. It is a property of the endpoint, so it can turn up on a refusal whatever the underlying cause, and it never names what the token holds. <a href=\"/github/resource-not-accessible-by-pat/\">That asymmetry has its own note</a>; here the consequence is narrower and more useful — the header is not the discriminator, so do not spend an hour reading it as one.</p>
<p><strong>The discriminator is the shape, and the shape is measurable.</strong> A missing permission is endpoint-shaped: whatever the token cannot do, it cannot do anywhere, including on repositories it owns outright. A pending approval is owner-shaped: everything fails under one resource owner and nothing fails under another. Probing two namespaces across three endpoint families settles which, in six requests, without a single write.</p>
<p><strong>No <code>x-github-sso</code> and no OAuth restriction message.</strong> Both of the neighbouring organization gates announce themselves. SAML enforcement puts a header on the refusal; an OAuth App restriction says so in the message and applies only to OAuth Apps, which a fine-grained token is not. Their absence beside an owner-shaped failure is what leaves pending approval standing, and the script records those absences as evidence rather than skipping past them.</p>
<p><strong>There is an authoritative reading, and it belongs to somebody else.</strong> <code>GET /orgs/{org}/personal-access-token-requests</code> lists the pending requests with the requester, the permissions asked for and the date. It needs <code>admin:org</code>, so the person who is blocked usually cannot run it — which is fitting, because the person who can run it is exactly the person who can end the wait. The script reads it with a second credential when one is offered and corroborates the behavioural finding with a date.</p>
<p><strong>Detect the pending state; never trigger it.</strong> Approving is a write and this script does not write, but the sharper rule is that it never asks for approval either. The request already exists — it was filed when the token was created — so there is nothing to resubmit, and resubmitting would only add a duplicate to somebody's queue. The output names the settings page where an owner approves the waiting request, and stops.</p>""",
"steps": [
 {"h": "Confirm the credential type, because this policy is fine-grained only",
  "body": """<p>Read locally from the prefix. Organization approval policy applies to fine-grained personal access tokens; a classic token reaching the same organization is governed by SAML authorization instead, and an App installation token by the installation. Getting this wrong sends you to a settings page that has no row for your credential.</p>"""},
 {"h": "Probe two namespaces across three endpoint families",
  "body": """<p>Six cheap reads: the authenticated user, personal repositories and personal issues, then the organization's repositories, issues and members. All of them <code>per_page=1</code>. The point is not any single status but the pattern across them, which is why the script insists on more than one family before it will say anything at all.</p>"""},
 {"h": "Decide whether the failure is owner-shaped or endpoint-shaped",
  "body": """<p>Every organization family refused while personal families answer is owner-shaped: the gate is the resource owner, and pending approval is what that looks like. One family refused in both namespaces is endpoint-shaped: the token is short a permission and the note that owns that is a click away. Anything else is reported as unclassified rather than forced into a verdict.</p>"""},
 {"h": "Record the absences that rule out the neighbouring gates",
  "body": """<p>The script notes whether <code>x-github-sso</code> was on any refusal and whether the message matched an OAuth App restriction. Both absent, beside an owner-shaped failure, is what leaves this diagnosis standing. It also states in the output that <code>x-accepted-github-permissions</code> is not a discriminator here, because that header is where people spend the hour they did not need to spend.</p>"""},
 {"h": "Corroborate with an owner's credential, and print the approval step",
  "body": """<p>Given <code>GITHUB_ADMIN_TOKEN</code>, the script reads the organization's pending token requests, finds the one filed by this account, and reports how many days it has been waiting. Then it prints where an owner approves it. It does not approve, does not request, and does not re-request: the request already exists, and filing another only puts a duplicate in the queue.</p>"""},
],
"verify": """<p>After an owner approves the waiting request, the same six probes come back and only the shape has changed.</p>
<pre><code class="language-bash">GITHUB_TOKEN=$FINE_GRAINED_TOKEN GITHUB_ADMIN_TOKEN=$OWNER_TOKEN \\
    python3 github_pat_pending_approval.py acme-corp
# read cost: 7 request(s) against the core hourly quota including one read
#   with the owner's credential
# credential: fine-grained PAT, account=dana
# personal  user=200  repositories=200  issues=200
# org       repositories=403  issues=403  members=403
# shape: owner-shaped - every organization family is refused and no personal
#   family is, so the gate is the resource owner and not any endpoint
# x-github-sso: absent on every refusal
# oauth restriction wording: not present
# note: x-accepted-github-permissions describes what the endpoint accepts and
#   never what the token holds, so it cannot settle this either way
# pending-org-approval: this token is waiting for an organization owner to
#   approve it. Its permissions are held on paper and none in practice.
# pending request: filed 6 day(s) ago by dana, repository_selection=all
# repair: an owner of acme-corp approves the waiting request under the
#   organization's personal access tokens settings. This script does not
#   approve it and does not ask for it. Do not create a replacement token:
#   the request already exists and a new one only queues behind it.</code></pre>""",
"code_intro": "The interesting function takes no arguments from the network. <code>probe_shape</code> receives two lists of endpoint family and status and answers one question — is this failure shaped like an owner or shaped like an endpoint — which is the whole diagnosis and is pure arithmetic over six numbers. Everything around it is the discipline that makes the arithmetic trustworthy: refusing to answer on a single family, recording two absent signals as evidence rather than as nothing, saying out loud that the permissions header cannot settle this, and treating the owner's view of the pending queue as corroboration rather than as the primary reading, because the person who is blocked usually cannot take it.",
"py_file": "github_pat_pending_approval.py",
"py": '''"""Tell a token waiting for an owner apart from a token short a permission.

Read only. GET requests and nothing else, and a second promise this note needs
more than most: it never approves anything and never asks for approval. The
request this script detects already exists -- it was filed the moment the token
was created -- so there is nothing to resubmit, and resubmitting would only put
a duplicate into somebody's queue.

The diagnosis is a shape. A missing permission is endpoint-shaped: whatever the
token cannot do, it cannot do anywhere, including on repositories the account
owns outright. A pending organization approval is owner-shaped: every endpoint
family fails under one resource owner while personal reads succeed. Six cheap
reads separate them.

What this can and cannot see: it can prove the shape, and it can record that
neither of the neighbouring gates announced itself. It cannot read the
organization's token policy, and it cannot read the pending request with the
credential that is blocked by it -- that needs admin:org, which is why the
authoritative reading is optional here and belongs to the person who can also
end the wait.

Environment:

    GITHUB_TOKEN        the fine-grained token being refused
    GITHUB_ADMIN_TOKEN  an organization owner's credential, admin:org (optional)
"""
import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_pat_pending_approval")

API = "https://api.github.com"
UA = "github-pat-pending-approval/1.0"

SSO_HEADER = "x-github-sso"
ACCEPTED_PERMISSIONS_HEADER = "x-accepted-github-permissions"

TOKEN_PREFIXES = (
    ("github_pat_", "fine-grained PAT"),
    ("ghp_", "classic PAT"),
    ("gho_", "OAuth user token"),
    ("ghu_", "App user-to-server token"),
    ("ghs_", "App installation token"),
    ("ghr_", "App refresh token"),
)

# Two namespaces, several endpoint families each. The families matter more than
# the endpoints: the question is whether refusals cluster by owner or by
# family, and one endpoint cannot answer that.
PERSONAL_PROBES = (
    ("user", "/user"),
    ("repositories", "/user/repos?per_page=1"),
    ("issues", "/issues?per_page=1"),
)
ORG_PROBES = (
    ("repositories", "/orgs/%s/repos?per_page=1"),
    ("issues", "/orgs/%s/issues?per_page=1"),
    ("members", "/orgs/%s/members?per_page=1"),
)

REFUSED = (403, 404)

# Corroboration for ruling the neighbouring gate out, never for ruling this one
# in. The wording belongs to GitHub and can be edited at any time.
OAUTH_RESTRICTION_PHRASES = (
    "oauth app access restrictions",
    "third-party application",
)


def read_cost(with_admin=False):
    """Requests this run will spend against the core quota. Pure."""
    return len(PERSONAL_PROBES) + len(ORG_PROBES) + (1 if with_admin else 0)


def token_kind(token):
    """Name the credential from its prefix. Pure; nothing leaves the machine."""
    value = (token or "").strip()
    for prefix, name in TOKEN_PREFIXES:
        if value.startswith(prefix):
            return name
    return "unknown"


def probe_shape(personal, org):
    """Is this failure shaped like an owner or like an endpoint. Pure.

    personal, org: [(family, status), ...]. Returns (shape, detail).

    The refusal to answer on thin evidence is deliberate. One organization
    family failing tells you nothing about whether the gate is the owner, and a
    script that guesses there sends people to the wrong settings page.
    """
    if len(org) < 2:
        return ("insufficient-evidence",
                "fewer than two organization endpoint families were read, and "
                "one family cannot show whether refusals cluster by owner.")
    org_refused = [f for f, s in org if s in REFUSED]
    org_ok = [f for f, s in org if s == 200]
    personal_ok = [f for f, s in personal if s == 200]
    personal_refused = [f for f, s in personal if s in REFUSED]

    if not personal_ok:
        return ("credential-shaped",
                "nothing succeeded in the personal namespace either, so the "
                "credential itself is the thing to look at first.")
    if len(org_refused) == len(org) and not personal_refused:
        return ("owner-shaped",
                "every organization family is refused and no personal family "
                "is, so the gate is the resource owner and not any endpoint.")
    if org_ok and org_refused:
        shared = sorted(set(org_refused) & set(f for f, s in personal
                                               if s in REFUSED))
        if shared:
            return ("endpoint-shaped",
                    "the same family is refused in both namespaces (%s), which "
                    "is a permission the token does not hold rather than an "
                    "owner refusing it." % ", ".join(shared))
        return ("endpoint-shaped",
                "some organization families answer and others do not, so the "
                "owner is admitting this token and individual permissions are "
                "what is short.")
    if not org_refused:
        return ("nothing-refused",
                "every family answered in both namespaces, so nothing is "
                "waiting on anybody today.")
    return ("unclassified-shape",
            "the pattern does not match owner-shaped or endpoint-shaped; "
            "report the statuses rather than naming a cause.")


def header_is_not_the_discriminator():
    """The sentence that saves an hour. Pure."""
    return ("x-accepted-github-permissions describes what the endpoint accepts "
            "and never what the token holds, so it cannot settle this either "
            "way.")


def oauth_wording(message):
    """Did the refusal blame an OAuth App restriction. Pure."""
    text = str(message or "").lower()
    return any(p in text for p in OAUTH_RESTRICTION_PHRASES)


def classify(shape, kind, sso_seen, oauth_seen):
    """The verdict. Pure. (state, detail).

    The neighbouring gates are checked before the shape, because each of them
    announces itself and a diagnosis established by exclusion must never
    outrank one that was stated outright.
    """
    if kind != "fine-grained PAT":
        return ("not-a-fine-grained-token",
                "organization approval policy applies to fine-grained personal "
                "access tokens. A %s reaching this organization is governed by "
                "something else, with a different repair." % kind)
    if sso_seen:
        return ("saml-enforcement",
                "a refusal carried x-github-sso, so SAML enforcement is in play "
                "and that is a different note.")
    if oauth_seen:
        return ("oauth-app-restriction",
                "the refusal blamed OAuth App access restrictions, which govern "
                "applications rather than personal access tokens.")
    if shape == "owner-shaped":
        return ("pending-org-approval",
                "this token is waiting for an organization owner to approve it. "
                "Its permissions are held on paper and none in practice, which "
                "is why editing them changes nothing.")
    if shape == "endpoint-shaped":
        return ("permission-shaped",
                "the refusals follow an endpoint family rather than an owner, "
                "so this is a permission the token does not hold.")
    if shape == "credential-shaped":
        return ("credential-problem",
                "personal reads are failing too, so start with the credential.")
    if shape == "nothing-refused":
        return ("not-blocked", "nothing was refused during this run.")
    return ("undetermined",
            "not enough evidence to name a cause. Read more families before "
            "acting on this.")


def days_pending(created_at, now):
    """Whole days a request has been waiting. Pure."""
    if not created_at:
        return None
    text = str(created_at).strip().replace("Z", "+00:00")
    try:
        when = datetime.fromisoformat(text)
    except ValueError:
        return None
    if not when.tzinfo:
        when = when.replace(tzinfo=timezone.utc)
    return int((now - when).total_seconds() // 86400)


def find_request(requests_list, login):
    """The pending request filed by this account, if any. Pure.

    Matching is on the requester's login, which is public information and safe
    to print, unlike anything derived from the credential itself.
    """
    for item in requests_list or []:
        if not isinstance(item, dict):
            continue
        owner = item.get("owner") or {}
        if str(owner.get("login") or "").lower() == str(login or "").lower():
            return item
    return None


def repair(state, org):
    """The sentence a reader has to act on. Pure."""
    if state == "pending-org-approval":
        return ("an owner of %s approves the waiting request under the "
                "organization's personal access tokens settings. This script "
                "does not approve it and does not ask for it. Do not create a "
                "replacement token: the request already exists and a new one "
                "only queues behind it." % org)
    if state == "permission-shaped":
        return ("read x-accepted-github-permissions off the refusal, tick that "
                "permission on the token, and expect the organization to "
                "re-approve the change if it requires approval.")
    if state == "saml-enforcement":
        return "follow the SSO authorization URL on the refusal instead."
    if state == "oauth-app-restriction":
        return ("have an owner approve the application; this is a policy about "
                "an app rather than about a token.")
    if state == "not-a-fine-grained-token":
        return ("find the gate that applies to this credential type before "
                "looking at any approval queue.")
    if state == "credential-problem":
        return "fix the credential; no organization queue is involved yet."
    if state == "not-blocked":
        return "nothing. This token is reaching %s right now." % org
    return "read more endpoint families and run this again."


def get(session, url):
    """One GET. Returns the response object."""
    r = session.get(url, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from GitHub: GITHUB_TOKEN is missing, malformed "
                         "or revoked. That is a different note.")
    return r


def session_for(token):
    s = requests.Session()
    s.headers.update({
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        # GitHub rejects requests with no User-Agent outright.
        "User-Agent": UA,
    })
    return s


def body_message(response):
    """The API's message string, if the body has one."""
    try:
        payload = response.json()
    except ValueError:
        return ""
    return (payload or {}).get("message", "") if isinstance(payload, dict) else ""


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("org", help="the organization whose resources are refused")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_TOKEN (the fine-grained token being refused)")
        return 2
    admin = os.environ.get("GITHUB_ADMIN_TOKEN")

    log.info("read cost: %d request(s) against the core hourly quota%s",
             read_cost(bool(admin)),
             " including one read with the owner's credential" if admin else "")

    kind = token_kind(token)
    session = session_for(token)

    personal = []
    account = None
    for family, path in PERSONAL_PROBES:
        response = get(session, API + path)
        personal.append((family, response.status_code))
        if family == "user" and response.status_code == 200:
            account = (response.json() or {}).get("login")
    log.info("credential: %s, account=%s", kind, account or "unreadable")
    log.info("personal  %s", "  ".join("%s=%s" % (f, s) for f, s in personal))

    org_results = []
    sso_seen = False
    oauth_seen = False
    accepted_seen = None
    for family, template in ORG_PROBES:
        response = get(session, API + (template % args.org))
        org_results.append((family, response.status_code))
        if response.status_code in REFUSED:
            if response.headers.get(SSO_HEADER):
                sso_seen = True
            if oauth_wording(body_message(response)):
                oauth_seen = True
            accepted_seen = (response.headers.get(ACCEPTED_PERMISSIONS_HEADER)
                             or accepted_seen)
    log.info("org       %s", "  ".join("%s=%s" % (f, s) for f, s in org_results))

    shape, shape_detail = probe_shape(personal, org_results)
    log.info("shape: %s - %s", shape, shape_detail)
    log.info("%s: %s", SSO_HEADER,
             "present on a refusal" if sso_seen else "absent on every refusal")
    log.info("oauth restriction wording: %s",
             "present" if oauth_seen else "not present")
    log.info("note: %s", header_is_not_the_discriminator())

    state, detail = classify(shape, kind, sso_seen, oauth_seen)
    log.info("%s: %s", state, detail)

    pending = None
    waiting_days = None
    if admin:
        owner_session = session_for(admin)
        listing = get(owner_session,
                      API + "/orgs/%s/personal-access-token-requests?per_page=100"
                      % args.org)
        if listing.status_code == 200:
            body = listing.json()
            pending = find_request(body if isinstance(body, list) else [], account)
            if pending:
                waiting_days = days_pending(pending.get("created_at"),
                                            datetime.now(timezone.utc))
                log.info("pending request: filed %s day(s) ago by %s, "
                         "repository_selection=%s",
                         waiting_days, account,
                         pending.get("repository_selection"))
            else:
                log.info("pending request: none filed by %s is waiting, which "
                         "argues against this verdict", account)
        else:
            log.warning("personal-access-token-requests returned HTTP %s; that "
                        "endpoint needs admin:org", listing.status_code)

    log.info("repair: %s", repair(state, args.org))

    print(json.dumps({
        "organization": args.org,
        "account": account,
        "credential_kind": kind,
        "personal": dict(personal),
        "org": dict(org_results),
        "shape": shape,
        "shape_detail": shape_detail,
        "sso_header_seen": sso_seen,
        "oauth_wording_seen": oauth_seen,
        "accepted_permissions_header": accepted_seen,
        "accepted_permissions_note": header_is_not_the_discriminator(),
        "pending_request_found": bool(pending),
        "pending_request_days": waiting_days,
        "state": state,
        "detail": detail,
        "repair": repair(state, args.org),
    }, indent=2, default=str))
    return 1 if state == "pending-org-approval" else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-pat-pending-approval.mjs",
"js": '''/**
 * Tell a token waiting for an owner apart from a token short a permission.
 *
 * Read only, and it never approves anything or asks for approval. The request
 * this script detects already exists: it was filed the moment the token was
 * created, so there is nothing to resubmit and resubmitting would only put a
 * duplicate into somebody queue.
 *
 * A missing permission is endpoint-shaped: whatever the token cannot do, it
 * cannot do anywhere. A pending organization approval is owner-shaped: every
 * endpoint family fails under one resource owner while personal reads succeed.
 *
 * Environment:
 *   GITHUB_TOKEN        the fine-grained token being refused
 *   GITHUB_ADMIN_TOKEN  an organization owner credential with admin:org
 *   GITHUB_ORG          the organization whose resources are refused
 */
const API = 'https://api.github.com';
const UA = 'github-pat-pending-approval/1.0';

export const SSO_HEADER = 'x-github-sso';
export const ACCEPTED_PERMISSIONS_HEADER = 'x-accepted-github-permissions';

export const TOKEN_PREFIXES = [
  ['github_pat_', 'fine-grained PAT'],
  ['ghp_', 'classic PAT'],
  ['gho_', 'OAuth user token'],
  ['ghu_', 'App user-to-server token'],
  ['ghs_', 'App installation token'],
  ['ghr_', 'App refresh token'],
];

export const PERSONAL_PROBES = [
  ['user', '/user'],
  ['repositories', '/user/repos?per_page=1'],
  ['issues', '/issues?per_page=1'],
];
export const ORG_PROBES = [
  ['repositories', (org) => `/orgs/${org}/repos?per_page=1`],
  ['issues', (org) => `/orgs/${org}/issues?per_page=1`],
  ['members', (org) => `/orgs/${org}/members?per_page=1`],
];

export const REFUSED = [403, 404];

export const OAUTH_RESTRICTION_PHRASES = [
  'oauth app access restrictions',
  'third-party application',
];

/** Requests this run will spend against the core quota. Pure. */
export function readCost(withAdmin = false) {
  return PERSONAL_PROBES.length + ORG_PROBES.length + (withAdmin ? 1 : 0);
}

/** Name the credential from its prefix. Pure. */
export function tokenKind(token) {
  const value = String(token ?? '').trim();
  for (const [prefix, name] of TOKEN_PREFIXES) {
    if (value.startsWith(prefix)) return name;
  }
  return 'unknown';
}

/** Is this failure shaped like an owner or like an endpoint. Pure. */
export function probeShape(personal, org) {
  if (org.length < 2) {
    return ['insufficient-evidence', 'fewer than two organization endpoint '
      + 'families were read, and one family cannot show whether refusals '
      + 'cluster by owner.'];
  }
  const refused = (s) => REFUSED.includes(s);
  const orgRefused = org.filter(([, s]) => refused(s)).map(([f]) => f);
  const orgOk = org.filter(([, s]) => s === 200).map(([f]) => f);
  const personalOk = personal.filter(([, s]) => s === 200).map(([f]) => f);
  const personalRefused = personal.filter(([, s]) => refused(s)).map(([f]) => f);

  if (personalOk.length === 0) {
    return ['credential-shaped', 'nothing succeeded in the personal namespace '
      + 'either, so the credential itself is the thing to look at first.'];
  }
  if (orgRefused.length === org.length && personalRefused.length === 0) {
    return ['owner-shaped', 'every organization family is refused and no '
      + 'personal family is, so the gate is the resource owner and not any endpoint.'];
  }
  if (orgOk.length > 0 && orgRefused.length > 0) {
    const shared = orgRefused.filter((f) => personalRefused.includes(f)).sort();
    if (shared.length > 0) {
      return ['endpoint-shaped', `the same family is refused in both namespaces `
        + `(${shared.join(', ')}), which is a permission the token does not hold `
        + 'rather than an owner refusing it.'];
    }
    return ['endpoint-shaped', 'some organization families answer and others do '
      + 'not, so the owner is admitting this token and individual permissions '
      + 'are what is short.'];
  }
  if (orgRefused.length === 0) {
    return ['nothing-refused', 'every family answered in both namespaces, so '
      + 'nothing is waiting on anybody today.'];
  }
  return ['unclassified-shape', 'the pattern does not match owner-shaped or '
    + 'endpoint-shaped; report the statuses rather than naming a cause.'];
}

/** The sentence that saves an hour. Pure. */
export function headerIsNotTheDiscriminator() {
  return 'x-accepted-github-permissions describes what the endpoint accepts and '
    + 'never what the token holds, so it cannot settle this either way.';
}

/** Did the refusal blame an OAuth App restriction. Pure. */
export function oauthWording(message) {
  const text = String(message ?? '').toLowerCase();
  return OAUTH_RESTRICTION_PHRASES.some((p) => text.includes(p));
}

/** The verdict. Pure. [state, detail]. */
export function classify(shape, kind, ssoSeen, oauthSeen) {
  if (kind !== 'fine-grained PAT') {
    return ['not-a-fine-grained-token', 'organization approval policy applies to '
      + `fine-grained personal access tokens. A ${kind} is governed by something `
      + 'else, with a different repair.'];
  }
  if (ssoSeen) {
    return ['saml-enforcement', 'a refusal carried x-github-sso, so SAML '
      + 'enforcement is in play and that is a different note.'];
  }
  if (oauthSeen) {
    return ['oauth-app-restriction', 'the refusal blamed OAuth App access '
      + 'restrictions, which govern applications rather than personal tokens.'];
  }
  if (shape === 'owner-shaped') {
    return ['pending-org-approval', 'this token is waiting for an organization '
      + 'owner to approve it. Its permissions are held on paper and none in '
      + 'practice, which is why editing them changes nothing.'];
  }
  if (shape === 'endpoint-shaped') {
    return ['permission-shaped', 'the refusals follow an endpoint family rather '
      + 'than an owner, so this is a permission the token does not hold.'];
  }
  if (shape === 'credential-shaped') {
    return ['credential-problem', 'personal reads are failing too, so start with '
      + 'the credential.'];
  }
  if (shape === 'nothing-refused') {
    return ['not-blocked', 'nothing was refused during this run.'];
  }
  return ['undetermined', 'not enough evidence to name a cause.'];
}

/** Whole days a request has been waiting. Pure. */
export function daysPending(createdAt, nowMs) {
  if (!createdAt) return null;
  const when = Date.parse(String(createdAt));
  if (Number.isNaN(when)) return null;
  return Math.floor((nowMs - when) / 86400000);
}

/** The pending request filed by this account, if any. Pure. */
export function findRequest(requestsList, login) {
  for (const item of requestsList || []) {
    if (!item || typeof item !== 'object') continue;
    const owner = item.owner || {};
    if (String(owner.login ?? '').toLowerCase() === String(login ?? '').toLowerCase()) {
      return item;
    }
  }
  return null;
}

/** The sentence a reader has to act on. Pure. */
export function repair(state, org) {
  if (state === 'pending-org-approval') {
    return `an owner of ${org} approves the waiting request under the `
      + 'organization personal access tokens settings. This script does not '
      + 'approve it and does not ask for it. Do not create a replacement token: '
      + 'the request already exists and a new one only queues behind it.';
  }
  if (state === 'permission-shaped') {
    return 'read x-accepted-github-permissions off the refusal, tick that '
      + 'permission on the token, and expect the organization to re-approve it.';
  }
  if (state === 'saml-enforcement') {
    return 'follow the SSO authorization URL on the refusal instead.';
  }
  if (state === 'oauth-app-restriction') {
    return 'have an owner approve the application; this is a policy about an app.';
  }
  if (state === 'not-a-fine-grained-token') {
    return 'find the gate that applies to this credential type first.';
  }
  if (state === 'credential-problem') {
    return 'fix the credential; no organization queue is involved yet.';
  }
  if (state === 'not-blocked') {
    return `nothing. This token is reaching ${org} right now.`;
  }
  return 'read more endpoint families and run this again.';
}

function headers(token) {
  return {
    Authorization: `Bearer ${token}`,
    Accept: 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
    'User-Agent': UA,
  };
}

async function main() {
  const token = process.env.GITHUB_TOKEN;
  const org = process.env.GITHUB_ORG;
  if (!token || !org) {
    console.error('set GITHUB_TOKEN (the fine-grained token) and GITHUB_ORG');
    process.exitCode = 2;
    return;
  }
  const admin = process.env.GITHUB_ADMIN_TOKEN;
  console.log(`read cost: ${readCost(Boolean(admin))} request(s) against the core hourly quota`);

  const kind = tokenKind(token);
  const personal = [];
  let account = null;
  for (const [family, path] of PERSONAL_PROBES) {
    const response = await fetch(API + path, { headers: headers(token) });
    personal.push([family, response.status]);
    if (family === 'user' && response.status === 200) {
      account = (await response.json()).login;
    }
  }
  console.log(`credential: ${kind}, account=${account ?? 'unreadable'}`);
  console.log(`personal  ${personal.map(([f, s]) => `${f}=${s}`).join('  ')}`);

  const orgResults = [];
  let ssoSeen = false;
  let oauthSeen = false;
  let acceptedSeen = null;
  for (const [family, template] of ORG_PROBES) {
    const response = await fetch(API + template(org), { headers: headers(token) });
    orgResults.push([family, response.status]);
    if (REFUSED.includes(response.status)) {
      if (response.headers.get(SSO_HEADER)) ssoSeen = true;
      acceptedSeen = response.headers.get(ACCEPTED_PERMISSIONS_HEADER) || acceptedSeen;
      try {
        const body = await response.json();
        if (body && typeof body === 'object' && oauthWording(body.message)) oauthSeen = true;
      } catch { /* an empty body is not evidence either way */ }
    }
  }
  console.log(`org       ${orgResults.map(([f, s]) => `${f}=${s}`).join('  ')}`);

  const [shape, shapeDetail] = probeShape(personal, orgResults);
  console.log(`shape: ${shape} - ${shapeDetail}`);
  console.log(`${SSO_HEADER}: ${ssoSeen ? 'present on a refusal' : 'absent on every refusal'}`);
  console.log(`note: ${headerIsNotTheDiscriminator()}`);

  const [state, detail] = classify(shape, kind, ssoSeen, oauthSeen);
  console.log(`${state}: ${detail}`);

  let pending = null;
  let waitingDays = null;
  if (admin) {
    const listing = await fetch(
      `${API}/orgs/${org}/personal-access-token-requests?per_page=100`,
      { headers: headers(admin) },
    );
    if (listing.status === 200) {
      const body = await listing.json();
      pending = findRequest(Array.isArray(body) ? body : [], account);
      if (pending) {
        waitingDays = daysPending(pending.created_at, Date.now());
        console.log(`pending request: filed ${waitingDays} day(s) ago by ${account}`);
      } else {
        console.log(`pending request: none filed by ${account} is waiting`);
      }
    } else {
      console.warn(`personal-access-token-requests returned HTTP ${listing.status}; `
        + 'that endpoint needs admin:org');
    }
  }

  console.log(`repair: ${repair(state, org)}`);
  console.log(JSON.stringify({
    organization: org,
    account,
    credential_kind: kind,
    personal: Object.fromEntries(personal),
    org: Object.fromEntries(orgResults),
    shape,
    shape_detail: shapeDetail,
    sso_header_seen: ssoSeen,
    oauth_wording_seen: oauthSeen,
    accepted_permissions_header: acceptedSeen,
    accepted_permissions_note: headerIsNotTheDiscriminator(),
    pending_request_found: Boolean(pending),
    pending_request_days: waitingDays,
    state,
    detail,
    repair: repair(state, org),
  }, null, 2));
  process.exitCode = state === 'pending-org-approval' ? 1 : 0;
}

// Guarded so importing this file from the test runner does not start a run.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The two shapes are asserted side by side, because the note is the difference between them and a reader should be able to see it in the fixtures: the same three families, refused under one owner in the first and refused under one family in the second. Then the refusals to answer — one organization family is not enough evidence, and a personal namespace that is also failing is a credential problem rather than a queue. The last group holds the line on the repair: an approval that is printed and never requested, and an explicit instruction not to mint a replacement token, since that is the move everybody makes and it lengthens the queue it was meant to jump.",
"test_py_file": "test_github_pat_pending_approval.py",
"test_py": '''from datetime import datetime, timezone

from github_pat_pending_approval import (
    classify, days_pending, find_request, header_is_not_the_discriminator,
    oauth_wording, probe_shape, read_cost, repair, token_kind,
)

NOW = datetime(2026, 8, 31, 12, 0, 0, tzinfo=timezone.utc)

PERSONAL_OK = [("user", 200), ("repositories", 200), ("issues", 200)]
ORG_ALL_REFUSED = [("repositories", 403), ("issues", 403), ("members", 403)]
ORG_ONE_FAMILY = [("repositories", 200), ("issues", 403), ("members", 200)]


def test_an_owner_shaped_failure_refuses_every_family_in_one_namespace():
    shape, detail = probe_shape(PERSONAL_OK, ORG_ALL_REFUSED)
    assert shape == "owner-shaped"
    assert "the gate is the resource owner" in detail
    state, why = classify(shape, "fine-grained PAT", False, False)
    assert state == "pending-org-approval"
    assert "on paper and none in practice" in why


def test_an_endpoint_shaped_failure_follows_one_family_everywhere():
    # The same token, the same organization, and a completely different cause:
    # issues are refused in both namespaces, so the permission is what is short.
    personal = [("user", 200), ("repositories", 200), ("issues", 403)]
    shape, detail = probe_shape(personal, ORG_ONE_FAMILY)
    assert shape == "endpoint-shaped"
    assert "issues" in detail
    assert classify(shape, "fine-grained PAT", False, False)[0] == "permission-shaped"


def test_one_organization_family_is_not_enough_to_name_a_cause():
    shape, detail = probe_shape(PERSONAL_OK, [("repositories", 403)])
    assert shape == "insufficient-evidence"
    assert "one family cannot show" in detail
    assert classify(shape, "fine-grained PAT", False, False)[0] == "undetermined"


def test_a_failing_personal_namespace_is_a_credential_not_a_queue():
    personal = [("user", 200), ("repositories", 403), ("issues", 403)]
    dead = [("user", 403), ("repositories", 403), ("issues", 403)]
    assert probe_shape(dead, ORG_ALL_REFUSED)[0] == "credential-shaped"
    # A partly-failing personal namespace is not owner-shaped either.
    assert probe_shape(personal, ORG_ALL_REFUSED)[0] != "owner-shaped"


def test_a_clean_run_says_nothing_is_waiting():
    ok = [("repositories", 200), ("issues", 200), ("members", 200)]
    assert probe_shape(PERSONAL_OK, ok)[0] == "nothing-refused"
    assert classify("nothing-refused", "fine-grained PAT", False, False)[0] == "not-blocked"


def test_the_neighbouring_gates_outrank_the_shape_because_they_announce_themselves():
    assert classify("owner-shaped", "fine-grained PAT", True, False)[0] == "saml-enforcement"
    assert classify("owner-shaped", "fine-grained PAT", False, True)[0] == "oauth-app-restriction"
    assert oauth_wording("the acme-corp organization has enabled OAuth App "
                         "access restrictions") is True
    assert oauth_wording("Resource not accessible by personal access token") is False


def test_a_classic_token_is_never_sent_to_the_approval_queue():
    state, detail = classify("owner-shaped", "classic PAT", False, False)
    assert state == "not-a-fine-grained-token"
    assert "different repair" in detail


def test_the_permissions_header_is_stated_not_to_be_the_discriminator():
    note = header_is_not_the_discriminator()
    assert "never what the token holds" in note
    assert "cannot settle this" in note


def test_the_repair_prints_the_approval_and_forbids_a_second_token():
    fix = repair("pending-org-approval", "acme-corp")
    assert "an owner of acme-corp approves the waiting request" in fix
    assert "does not approve it and does not ask for it" in fix
    assert "Do not create a replacement token" in fix


def test_the_pending_request_is_matched_on_a_public_login():
    pending = [{"id": 42, "owner": {"login": "Dana"},
                "repository_selection": "all",
                "created_at": "2026-08-25T09:00:00Z"}]
    found = find_request(pending, "dana")
    assert found["id"] == 42
    assert find_request(pending, "someone-else") is None
    assert days_pending(found["created_at"], NOW) == 6
    assert days_pending(None, NOW) is None
    assert days_pending("not a date", NOW) is None


def test_the_credential_type_comes_from_its_prefix():
    assert token_kind("github_pat_x") == "fine-grained PAT"
    assert token_kind("ghp_fake") == "classic PAT"
    assert token_kind("nope") == "unknown"


def test_the_run_costs_six_reads_or_seven():
    assert read_cost() == 6
    assert read_cost(True) == 7
''',
"test_js_file": "github-pat-pending-approval.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  classify, daysPending, findRequest, headerIsNotTheDiscriminator, oauthWording,
  probeShape, readCost, repair, tokenKind,
} from './github-pat-pending-approval.mjs';

const NOW = Date.parse('2026-08-31T12:00:00Z');
const PERSONAL_OK = [['user', 200], ['repositories', 200], ['issues', 200]];
const ORG_ALL_REFUSED = [['repositories', 403], ['issues', 403], ['members', 403]];
const ORG_ONE_FAMILY = [['repositories', 200], ['issues', 403], ['members', 200]];

test('an owner shaped failure refuses every family in one namespace', () => {
  const [shape, detail] = probeShape(PERSONAL_OK, ORG_ALL_REFUSED);
  assert.equal(shape, 'owner-shaped');
  assert.ok(detail.includes('the gate is the resource owner'));
  assert.equal(classify(shape, 'fine-grained PAT', false, false)[0], 'pending-org-approval');
});

test('an endpoint shaped failure follows one family everywhere', () => {
  const personal = [['user', 200], ['repositories', 200], ['issues', 403]];
  const [shape, detail] = probeShape(personal, ORG_ONE_FAMILY);
  assert.equal(shape, 'endpoint-shaped');
  assert.ok(detail.includes('issues'));
  assert.equal(classify(shape, 'fine-grained PAT', false, false)[0], 'permission-shaped');
});

test('one organization family is not enough to name a cause', () => {
  assert.equal(probeShape(PERSONAL_OK, [['repositories', 403]])[0], 'insufficient-evidence');
  assert.equal(classify('insufficient-evidence', 'fine-grained PAT', false, false)[0],
    'undetermined');
});

test('a failing personal namespace is a credential not a queue', () => {
  const dead = [['user', 403], ['repositories', 403], ['issues', 403]];
  assert.equal(probeShape(dead, ORG_ALL_REFUSED)[0], 'credential-shaped');
});

test('the neighbouring gates outrank the shape', () => {
  assert.equal(classify('owner-shaped', 'fine-grained PAT', true, false)[0], 'saml-enforcement');
  assert.equal(classify('owner-shaped', 'fine-grained PAT', false, true)[0],
    'oauth-app-restriction');
  assert.equal(oauthWording('has enabled OAuth App access restrictions'), true);
  assert.equal(oauthWording('Resource not accessible by personal access token'), false);
});

test('a classic token is never sent to the approval queue', () => {
  assert.equal(classify('owner-shaped', 'classic PAT', false, false)[0],
    'not-a-fine-grained-token');
});

test('the permissions header is stated not to be the discriminator', () => {
  assert.ok(headerIsNotTheDiscriminator().includes('never what the token holds'));
});

test('the repair prints the approval and forbids a second token', () => {
  const fix = repair('pending-org-approval', 'acme-corp');
  assert.ok(fix.includes('an owner of acme-corp approves the waiting request'));
  assert.ok(fix.includes('does not approve it and does not ask for it'));
  assert.ok(fix.includes('Do not create a replacement token'));
});

test('the pending request is matched on a public login', () => {
  const pending = [{
    id: 42, owner: { login: 'Dana' }, repository_selection: 'all',
    created_at: '2026-08-25T09:00:00Z',
  }];
  assert.equal(findRequest(pending, 'dana').id, 42);
  assert.equal(findRequest(pending, 'someone-else'), null);
  assert.equal(daysPending('2026-08-25T09:00:00Z', NOW), 6);
  assert.equal(daysPending(null, NOW), null);
});

test('the credential type comes from its prefix', () => {
  assert.equal(tokenKind('github_pat_x'), 'fine-grained PAT');
  assert.equal(tokenKind('nope'), 'unknown');
});

test('the run costs six reads or seven', () => {
  assert.equal(readCost(), 6);
  assert.equal(readCost(true), 7);
});
''',
"faq": [
 ("How is this different from a fine-grained token that is missing a permission?",
  "By the shape of what fails. A missing permission is endpoint-shaped: the token cannot read issues, and it cannot read issues anywhere, including on repositories the account owns. A pending approval is owner-shaped: repositories, issues and members are all refused under the organization and all succeed personally. The <a href=\"/github/resource-not-accessible-by-pat/\">permission note</a> is where you go once the shape says endpoint; this one is where you go when it says owner. Same status code, same message, opposite repairs."),
 ("The refusal names a permission my token already has. What is going on?",
  "It names what the <em>endpoint</em> accepts. <code>x-accepted-github-permissions</code> is a property of the route, not of your credential, so it appears whether or not the permission is your problem, and it never states what the token holds. That is why it cannot settle this case, and why people lose an hour comparing it against a settings page that already agrees with it. The script prints that sentence in its output deliberately, because the header is the most convincing wrong lead in the whole diagnosis."),
 ("Why did creating a new token make it worse?",
  "Because creating a token against an organization that requires approval files a new request. The old one is still in the queue, yours is now behind it, and an owner opening the page sees two entries from the same person for what looks like the same thing. Nothing about a fresh token shortens the wait, and each attempt makes the queue harder for the person who has to act on it. There is nothing to resubmit: the request that matters already exists."),
 ("Can the script request approval, or nudge the owner?",
  "No. It detects the pending state and prints the step; it does not approve, request or re-request anything, and that restraint is the design rather than a limitation. The request is already filed, so the useful action is human and social — tell an owner it is waiting. What the script contributes to that conversation is a sentence with a number in it: this token has been waiting six days, here is where the approval lives. That is considerably more actionable than &ldquo;the API is returning 403&rdquo;."),
 ("Is this the same as a GitHub App waiting to be installed?",
  "No, and they are easy to confuse because both end in an owner clicking approve. This is a personal access token filed under an organization's token policy: the credential exists, belongs to a person, and is powerless until approved. An App awaiting installation is an application that has no credential for that organization at all yet, and its diagnosis runs through the App's own installation endpoints rather than through a token's behaviour. The scripts read different things because there are different things to read."),
],
"related": [
 ("/github/resource-not-accessible-by-pat/", "The endpoint-shaped version, where a permission is short"),
 ("/github/oauth-app-access-restricted/", "The same kind of org policy, aimed at applications"),
 ("/github/404-masking-403/", "Why some of these refusals arrive as Not Found"),
],
"citations": [CITE_PAT_POLICY, CITE_MANAGE_PATS, CITE_PAT_REQUESTS_REST, CITE_PAT_REVIEW],
},
]
