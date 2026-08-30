#!/usr/bin/env python3
"""/github/ field notes, batch X — the writing.

Four notes about organization policy rather than about credentials. The section
already publishes a long shelf of token notes, so the risk with anything
labelled "permissions" is that it becomes a fifth way of saying "your token is
too narrow". None of these four is that. In all four the token is valid,
unchanged, and passes every check anybody thinks to run on it.

The first owns a refusal that is about the *address* rather than the
credential. An organization IP allow list judges where the request came from,
so the identical token succeeds from a laptop and is refused from a CI runner,
and the refusal names the address GitHub saw in its own body. The section's
existing 403 sort lives in the User-Agent note and sorts four causes from the
body; this is a fifth, it names itself in a different sentence, and it is the
only one whose evidence is an IP address rather than a header.

The second owns access that vanished for some accounts and not others. Turning
on a two-factor requirement does not merely refuse non-compliant members, it
*removes* them, and nobody tells the integration. The account is gone while its
token is perfectly healthy, so every credential check passes and every
organization repository answers 404. One membership read settles it, and the
status code that settles it is a redirect nobody expects.

The third owns an organization-wide default that re-grades every repository at
once. Base permission is one field on the organization, and tightening it from
read to none removes implicit access from every member simultaneously, machine
accounts included. That is a different object from a person's role on one
repository, which the section already publishes: nothing is revoked from the
account, no write is refused, and the symptom is a list that got shorter.

The fourth owns a state that is neither installed nor absent. When somebody
without owner rights asks to install a GitHub App on an organization it becomes
a request an owner must approve, and until they do the App has no installation
at all while the product that started the flow believes it is connected. The
section already publishes an App absent from a repository; this is an App
absent from an account it thinks it has, and the honest part of the note is
that the API publishes no pending-request list, so the pending state is only
separable from an abandoned one by reconciling against your own record.

Nothing here writes. Two of these notes are about an approval and an allow-list
entry that somebody has to add, and in both cases the script prints the request
for a human to make rather than making it. The fourth in particular never asks
for an installation and never approves one: it detects the state and prints the
step. Every script GETs, prints its read cost before it spends it, and exits.
"""

CITE_IP_ALLOW_LIST = ("Managing allowed IP addresses for your organization — GitHub Docs",
                      "https://docs.github.com/en/organizations/keeping-your-organization-secure/managing-security-settings-for-your-organization/managing-allowed-ip-addresses-for-your-organization")
CITE_APP_IP_ALLOW_LIST = ("Managing allowed IP addresses for a GitHub App — GitHub Docs",
                          "https://docs.github.com/en/apps/maintaining-github-apps/managing-allowed-ip-addresses-for-a-github-app")
CITE_GRAPHQL_ORG = ("Organization — GitHub GraphQL API reference",
                    "https://docs.github.com/en/graphql/reference/objects#organization")
CITE_REST_BEST = ("Best practices for using the REST API — GitHub Docs",
                  "https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api")
CITE_ORG_MEMBERS = ("Organization members — GitHub REST API",
                    "https://docs.github.com/en/rest/orgs/members")
CITE_ORGS = ("Organizations — GitHub REST API",
             "https://docs.github.com/en/rest/orgs/orgs")
CITE_2FA = ("Requiring two-factor authentication in your organization — GitHub Docs",
            "https://docs.github.com/en/organizations/keeping-your-organization-secure/managing-two-factor-authentication-for-your-organization/requiring-two-factor-authentication-in-your-organization")
CITE_USERS = ("Users — GitHub REST API",
              "https://docs.github.com/en/rest/users/users")
CITE_BASE_PERMISSIONS = ("Setting base permissions for an organization — GitHub Docs",
                         "https://docs.github.com/en/organizations/managing-user-access-to-your-organizations-repositories/managing-repository-roles/setting-base-permissions-for-an-organization")
CITE_REPOS = ("Repositories — GitHub REST API",
              "https://docs.github.com/en/rest/repos/repos")
CITE_PAGINATION = ("Using pagination in the REST API — GitHub Docs",
                   "https://docs.github.com/en/rest/using-the-rest-api/using-pagination-in-the-rest-api")
CITE_APPS = ("Apps — GitHub REST API",
             "https://docs.github.com/en/rest/apps/apps")
CITE_REQUESTING_APP = ("Requesting a GitHub App from your organization owner — GitHub Docs",
                       "https://docs.github.com/en/apps/using-github-apps/requesting-a-github-app-from-your-organization-owner")
CITE_INSTALLING_APP = ("Installing a GitHub App from a third party — GitHub Docs",
                       "https://docs.github.com/en/apps/using-github-apps/installing-a-github-app-from-a-third-party")
CITE_APP_AUTH = ("Authenticating as a GitHub App — GitHub Docs",
                 "https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/authenticating-as-a-github-app")

GUIDES = [
{
"slug": "ip-allow-list-blocks-requests",
"title": "The org's IP allow list refuses the runner, not the token",
"description": "The same token succeeds from a laptop and 403s from CI. The refusal names the address GitHub saw, which is the one piece of evidence no other 403 carries.",
"h1": "The org's IP allow list refuses the runner, not the token",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github api 403 ip allow list",
             "github organization ip allow list ci runner",
             "not permitted to access this resource github",
             "github actions runner egress ip blocked org",
             "github app ip allow list installation token"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The job fails in CI and passes on the laptop. Same repository, same endpoint, same token — the engineer copies the token out of the secret store and runs the identical command locally to prove it, and it works. So the token is fine, and the code is fine, and the only thing left is the API, which is up. Meanwhile anonymous calls to the organization's public repositories keep answering 200 from the same runner, which is taken as proof that the network is fine too. It is not the token and not the network. The organization restricts which source addresses may reach it, and the runner's address has never been on the list.",
"short_answer": """<p>An organization IP allow list is a check on <em>where the request came from</em>, applied to a credential that is otherwise perfectly good. Ephemeral CI egress addresses and serverless NAT pools are rarely on it, which is why the laptop succeeds and the runner does not.</p>
<p>Read the body of the 403. This refusal is the only one on the API that names an IP address: <code>Although you appear to have the correct authorization credentials, the ACME organization has an IP allow list enabled, and 203.0.113.9 is not permitted to access this resource.</code> That address is the one GitHub actually saw, which is better evidence than any echo service, because it is the address the rule was applied to. Where you hold <code>admin:org</code>, the list itself is readable through the GraphQL <code>ipAllowListEntries</code> field and can be compared against that address directly.</p>""",
"problem": """<p>What makes this expensive is that every cheap experiment exonerates the thing that is broken. Copy the token to a laptop: it works, so the token is good. Curl a public repository from the runner: it answers, so egress is good. Read the token's scopes: they are what they always were. Each of those is a true observation and none of them touches the actual rule, because the rule only applies to the organization's own resources and only to the address the request arrives from.</p>
<p>Then the search goes somewhere unhelpful. A 403 is the status a missing permission produces, so somebody widens the token, and the refusal is unchanged. Somebody swaps a classic token for a fine-grained one, and it is unchanged again. Somebody moves the job to a different runner pool and it starts working, which looks like the fix but is really the first correct reading anybody has taken: that pool's egress happens to be allowed.</p>
<p>The other reason it hides is that the change is usually not yours. Somebody in the organization turned on an allow list, or added an entry and removed a broader one, and the integration is not mentioned in that work at all. From inside the failing job there is no event, no deprecation notice and no header. There is a sentence in a response body that most clients throw away in favour of the status code.</p>""",
"why": """<p><strong>The check runs against the connection, not the credential.</strong> An allow list narrows the set of source addresses permitted to reach the organization's resources. Passing it is a precondition; it is not something a token can carry. That is why widening scopes changes nothing and why the same token is simultaneously allowed and refused, depending only on which machine it is used from.</p>
<p><strong>The refusal names the address, and that is the whole diagnostic.</strong> Every other 403 on this API describes a rule; this one describes a rule and then tells you the value that failed it. A runner behind a NAT pool does not know its own egress address, and teams routinely paste the address of the wrong gateway into a change request. GitHub is telling you, in the error, which address the decision was made about. Compare that against the CIDRs you believe you egress from before you ask anybody to add anything.</p>
<p><strong>It is a different 403 from the other four, and it says so.</strong> The section's <a href="/github/user-agent-missing/">User-Agent note</a> owns the sort of a 403 into its causes from the response body, and this is a fifth entry in that sort rather than a second copy of it. Primary quota exhaustion says <em>API rate limit exceeded</em> and comes with <code>x-ratelimit-remaining: 0</code>. A secondary limit says <em>secondary rate limit</em> and usually carries <code>retry-after</code>. The User-Agent rule names the header. A missing permission names the resource and nothing else. This one, alone, contains a dotted quad or a colonned IPv6 address, which is a signal you can key on without reading English.</p>
<p><strong>Which list judges you depends on what kind of credential it is.</strong> A GitHub App can maintain its own allow list, and where an organization has enabled the setting, the App's ranges are contributed automatically — but that covers <em>installation</em> tokens. A user-to-server token acts for a person, so it is judged against the organization's own list even when the App's ranges are allowed. That distinction accounts for the confusing case where an App's background sync works and the same App's interactive calls do not.</p>
<p><strong>The rule is org state and needs org access to read.</strong> A repository-scoped read-only token sees the effect, never the rule. This is a real blind spot and the script reports it as one: without <code>admin:org</code>-class access, the entries are unreadable and the finding rests on the refusal body alone, which is enough to name the cause and not enough to say which entry would have covered you. Say that plainly rather than printing a confident diff of an empty list.</p>""",
"steps": [
 {"h": "Run it from the machine that is failing",
  "body": """<p>This is the one diagnostic in the section where the location of the process is part of the input. Run the script on the runner, in the function, inside the container — wherever the 403 happens. Run it on a laptop and it will cheerfully report that everything is fine, which is exactly the misleading result that sent you here.</p>"""},
 {"h": "Sort the 403 before believing anything about it",
  "body": """<p>The script probes one organization-scoped path and classifies the refusal from the body and the headers: quota, secondary limit, the User-Agent rule, a permission, or the allow list. Only the last of those contains an IP address, so the classification does not depend on matching a sentence GitHub may reword.</p>"""},
 {"h": "Take the address out of GitHub's own error",
  "body": """<p>When the classification is the allow list, the script lifts the address out of the message and prints it as the address GitHub saw. Pass <code>--egress 203.0.113.0/24</code> with the ranges you believe your jobs leave from and it does the containment arithmetic locally: if the observed address is outside every range you declared, your egress assumption is wrong and adding those ranges to the allow list would not have helped.</p>"""},
 {"h": "Read the list itself, if your token is allowed to",
  "body": """<p>With <code>--org-allow-list</code> and an <code>admin:org</code>-class token, the script runs one GraphQL query for <code>ipAllowListEnabledSetting</code> and the entries, and reports whether the observed address is covered, covered by an entry that is switched off, or not covered at all. The query is refused before it is sent if the document contains a mutation. Without that access the script says the list is unreadable rather than implying it is empty.</p>"""},
 {"h": "Pair it with the reading from the machine that works",
  "body": """<p>A script cannot be in two places at once, so pass the other machine's status with <code>--seen-elsewhere 200</code>. A 403 here beside a 200 there, with the same token, is the network path stated as a fact rather than a hunch, and it is the sentence to put in the change request. The repair the script prints is a request for somebody with organization admin to add a range, or for the job to be moved behind a fixed-address gateway that is already allowed. It adds nothing itself.</p>"""},
],
"verify": """<p>Once the range is added, the same probe from the same runner stops being refused and the observed address is reported as covered.</p>
<pre><code class="language-bash">GITHUB_TOKEN=$READ_ONLY_TOKEN python3 github_ip_allow_list.py acme \\
    --egress 198.51.100.0/24 --seen-elsewhere 200
# read cost: 2 REST request(s) against the core hourly quota, 0 GraphQL point(s)
# probe: GET /orgs/acme/repos?per_page=1 -> HTTP 403
# refusal: ip-allow-list — the body names an IP address, which no other 403 on
#   this API does. This is a check on the source address, not on the token.
# address GitHub saw: 203.0.113.9
# egress-assumption-wrong: the address GitHub saw is outside every range you
#   declared (198.51.100.0/24), so adding those ranges would not have helped.
# paired reading: network-path — refused here, 200 elsewhere, same token.
# repair: ask an owner of acme to add 203.0.113.9/32, or the runner pool's
#   documented egress range, to the organization IP allow list. Nothing here
#   adds it: that is an organization setting and this script only reads.</code></pre>""",
"code_intro": "The live part is two GETs and, only if you ask for it, one GraphQL query. Everything that decides anything is pure: the classifier that sorts a 403 by what its body contains, the scan that lifts an address out of a sentence without a regular expression to get wrong, the CIDR arithmetic, and the pairing of two readings taken from two machines. That matters here more than usual, because the interesting inputs are refusals you cannot conveniently reproduce — you would need to be on the blocked runner to produce one, and the tests need to hold a dozen of them at once.",
"py_file": "github_ip_allow_list.py",
"py": '''"""Say whether a 403 came from an organization IP allow list.

Read only. Two GETs, plus one optional GraphQL query, which is a read that
happens to travel over the same verb a write would. Nothing is added to any
allow list: an allow-list entry is organization state, so the script compares
what is there against the address GitHub saw and prints the request for
somebody with organization admin to make.

The point of the note: this refusal is a check on the source address, not on
the credential. The identical token succeeds from a laptop and is refused from
an ephemeral CI runner, which is why every experiment that varies the token
comes back clean.

What this can and cannot see: the refusal body names the address GitHub applied
the rule to, which is stronger evidence than any echo service. The list itself
is organization state and needs admin:org-class access; without it this script
reports the effect and says the rule is unreadable rather than pretending an
unreadable list is an empty one.

Environment:

    GITHUB_TOKEN    the same read-only token the failing job holds
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_ip_allow_list")

API = "https://api.github.com"
UA = "github-ip-allow-list/1.0"

# Sentences the four other causes of a 403 put in the body. Matched in
# lowercase and only as corroboration: the decisive test for an allow-list
# refusal is that the body contains an IP address, which none of the others do,
# so a reworded sentence cannot silently break the classification.
QUOTA_MARKERS = ("api rate limit exceeded",)
SECONDARY_MARKERS = ("secondary rate limit",)
USER_AGENT_MARKERS = ("user-agent", "user agent")
ALLOW_LIST_MARKERS = ("ip allow list", "not permitted to access this resource")

# Read for ipAllowListEnabledSetting and the entries. One query, one point, and
# it is refused before it is sent if the document stops being a read.
ALLOW_LIST_QUERY = """
query($login: String!) {
  organization(login: $login) {
    ipAllowListEnabledSetting
    ipAllowListForInstalledAppsEnabledSetting
    ipAllowListEntries(first: 100) {
      nodes { allowListValue isActive name }
    }
  }
}
"""

# Which list judges which credential. An App-managed allow list contributes the
# App's ranges for installation tokens; a user-to-server token acts for a
# person and is judged against the organization's own list regardless.
TOKEN_PREFIXES = (
    ("github_pat_", "fine-grained PAT"),
    ("ghp_", "classic PAT"),
    ("gho_", "OAuth user token"),
    ("ghu_", "App user-to-server token"),
    ("ghs_", "App installation token"),
    ("ghr_", "App refresh token"),
)

APP_MANAGED_APPLIES = ("App installation token",)


def read_cost(with_allow_list=False):
    """(REST requests, GraphQL points) this run will spend. Pure.

    Printed before anything is spent. The GraphQL half is counted separately
    because it comes out of a different budget and a reader deciding whether to
    pass --org-allow-list is deciding about that budget, not this one.
    """
    return (2, 1 if with_allow_list else 0)


def token_kind(token):
    """Name the credential from its prefix. Pure; nothing leaves the machine."""
    value = (token or "").strip()
    for prefix, name in TOKEN_PREFIXES:
        if value.startswith(prefix):
            return name
    return "unknown"


def list_that_applies(kind):
    """Which allow list judges this credential. Pure. (which, detail).

    The case that confuses people: an App with its own allow list keeps its
    background sync working while the same App's interactive calls are refused,
    because those calls carry a user-to-server token and are judged against the
    organization's list.
    """
    if kind in APP_MANAGED_APPLIES:
        return ("org-list-plus-app-managed",
                "an installation token is judged against the organization's "
                "list, and where the organization has enabled the App-managed "
                "setting the App's own ranges are contributed to it "
                "automatically.")
    if kind == "App user-to-server token":
        return ("org-list-only",
                "a user-to-server token acts for a person, so it is judged "
                "against the organization's own list even when the App's "
                "ranges are allowed. An App whose background sync works and "
                "whose interactive calls do not is this exact case.")
    return ("org-list-only",
            "this credential carries no App identity, so only the "
            "organization's own allow list applies to it.")


def looks_like_ipv4(text):
    """Four dot-separated numbers in 0..255. Pure. No regular expression.

    Written as arithmetic rather than a pattern because the input is a
    human-readable sentence and the parts that matter -- a trailing full stop,
    a leading bracket -- are easier to strip than to describe in a pattern.
    """
    parts = str(text or "").split(".")
    if len(parts) != 4:
        return False
    for part in parts:
        if not part.isdigit() or len(part) > 3:
            return False
        if int(part) > 255:
            return False
    return True


def looks_like_ipv6(text):
    """A rough IPv6 test: colons, hex groups only. Pure.

    Rough on purpose. The script never does arithmetic on an IPv6 address; it
    only needs to recognise one well enough to report it and to say that the
    containment check was not run.
    """
    value = str(text or "")
    if value.count(":") < 2:
        return False
    for group in value.split(":"):
        if group == "":
            continue
        if len(group) > 4:
            return False
        for ch in group.lower():
            if ch not in "0123456789abcdef":
                return False
    return True


def address_in_message(message):
    """The address GitHub says it saw, or None. Pure.

    Tokenised rather than matched, so punctuation attached to the address --
    the full stop that ends the sentence, a comma, a closing bracket -- does
    not have to be anticipated in a pattern.
    """
    for raw in str(message or "").split():
        candidate = raw.strip(".,;:()[]<>\\"'")
        if looks_like_ipv4(candidate) or looks_like_ipv6(candidate):
            return candidate
    return None


def header_value(headers, name):
    """Case-insensitive header read against a plain dict. Pure."""
    if not isinstance(headers, dict):
        return None
    wanted = str(name).lower()
    for key, value in headers.items():
        if str(key).lower() == wanted:
            return value
    return None


def classify_refusal(status, body_text, headers=None):
    """Sort one refusal into its cause. Pure. (state, detail).

    The decisive test for this note's cause is structural: the body contains an
    IP address. Every other 403 on this API describes a rule and names no
    address, so the classification survives GitHub rewording the sentence.
    """
    text = str(body_text or "").lower()
    if int(status or 0) not in (401, 403, 429):
        return ("not-a-refusal",
                "HTTP %s is not a refusal, so there is nothing here to sort."
                % status)
    if any(m in text for m in SECONDARY_MARKERS):
        return ("secondary-limit",
                "the body names a secondary rate limit. Wait for retry-after "
                "and slow down; no allow-list entry is involved.")
    if any(m in text for m in QUOTA_MARKERS) or header_value(
            headers, "x-ratelimit-remaining") in ("0", 0):
        return ("primary-quota-exhausted",
                "primary quota is spent. x-ratelimit-reset says when it "
                "returns, and the address is not the problem.")
    if address_in_message(body_text) is not None:
        return ("ip-allow-list",
                "the body names an IP address, which no other 403 on this API "
                "does. This is a check on where the request came from, not on "
                "what it carried.")
    if any(m in text for m in ALLOW_LIST_MARKERS):
        return ("ip-allow-list-unaddressed",
                "the body reads like an allow-list refusal but names no "
                "address. Treat the cause as the allow list and get the "
                "egress address another way.")
    if any(m in text for m in USER_AGENT_MARKERS):
        return ("user-agent-rule",
                "the body names the User-Agent header. That check runs before "
                "authentication and has its own note.")
    if int(status) == 401:
        return ("credential-rejected",
                "401 means the credential itself was not accepted. An allow "
                "list refuses with 403 and a body that names an address.")
    return ("permission-or-role",
            "no rule named itself in the body, which is what a missing "
            "permission or too low a repository role looks like.")


def ipv4_to_int(text):
    """Dotted quad to an integer, or None. Pure."""
    if not looks_like_ipv4(text):
        return None
    total = 0
    for part in str(text).split("."):
        total = (total << 8) + int(part)
    return total


def cidr_contains(cidr, address):
    """Is this address inside this CIDR. Pure. True, False or None.

    None means "not evaluated" -- an IPv6 entry, or something this script does
    not parse -- and it is deliberately not False. Reporting an unevaluated
    entry as a miss is how a script tells somebody their address is not covered
    when the entry covering it was simply one it could not read.
    """
    value = str(cidr or "").strip()
    if not value:
        return None
    if "/" in value:
        net, _, bits = value.partition("/")
        if not bits.isdigit():
            return None
        prefix = int(bits)
    else:
        net, prefix = value, 32
    if ":" in net or ":" in str(address or ""):
        return None
    left, right = ipv4_to_int(net), ipv4_to_int(address)
    if left is None or right is None or prefix > 32:
        return None
    if prefix == 0:
        return True
    mask = (0xFFFFFFFF << (32 - prefix)) & 0xFFFFFFFF
    return (left & mask) == (right & mask)


def covered_by(entries, address):
    """Does any active entry cover this address. Pure. (state, entry).

    Ordered so that an inactive entry that would have covered the address is
    reported as its own state. That is the most useful finding the list can
    produce: somebody already added the range and then switched it off, and a
    plain "not covered" would send you to add it a second time.
    """
    if address is None:
        return ("address-unknown", None)
    if not entries:
        return ("no-entries", None)
    inactive = None
    unevaluated = False
    for entry in entries:
        hit = cidr_contains(entry.get("value"), address)
        if hit is None:
            unevaluated = True
            continue
        if hit and entry.get("active"):
            return ("covered", entry)
        if hit:
            inactive = inactive or entry
    if inactive is not None:
        return ("covered-but-inactive", inactive)
    if unevaluated:
        return ("not-covered-some-unevaluated", None)
    return ("not-covered", None)


def egress_assumption(declared, address):
    """Compare the ranges you believe you leave from against the real one. Pure."""
    if address is None:
        return ("address-unknown",
                "no address was reported, so there is nothing to compare your "
                "declared egress against.")
    if not declared:
        return ("nothing-declared",
                "pass --egress with the ranges you believe this job leaves "
                "from and this becomes a check rather than a reading.")
    for cidr in declared:
        if cidr_contains(cidr, address) is True:
            return ("egress-as-expected",
                    "the address GitHub saw is inside %s, so your egress "
                    "assumption holds and the range simply is not allowed "
                    "yet." % cidr)
    return ("egress-assumption-wrong",
            "the address GitHub saw is outside every range you declared (%s), "
            "so adding those ranges would not have helped. Find out what this "
            "job really egresses through before asking for a change."
            % ", ".join(declared))


def paired_reading(status_here, status_elsewhere):
    """Two readings of the same call from two machines. Pure. (state, detail)."""
    here = int(status_here or 0)
    there = None if status_elsewhere is None else int(status_elsewhere)
    if there is None:
        return ("single-reading",
                "only this machine was read. Pass --seen-elsewhere with the "
                "status the same token gets from a machine that works and the "
                "network path stops being a hunch.")
    if here == 403 and there == 200:
        return ("network-path",
                "the same token is refused here and accepted there, so the "
                "difference is the source address and nothing else.")
    if here == 403 and there == 403:
        return ("refused-everywhere",
                "both addresses are refused. Either the allow list covers "
                "neither, or the cause is the credential after all.")
    if here == 200:
        return ("no-refusal",
                "this machine was not refused, so there is nothing to explain "
                "from here. Run this on the machine that fails.")
    return ("inconclusive",
            "the pair of statuses does not describe an allow list. Sort the "
            "refusal by its body first.")


def words(document):
    """Bare words in a GraphQL document. Pure. No regular expression."""
    out, current = [], ""
    for ch in str(document or ""):
        if ch.isalnum() or ch == "_":
            current += ch
        else:
            if current:
                out.append(current.lower())
            current = ""
    if current:
        out.append(current.lower())
    return out


def refuses_mutation(document):
    """Would this document change something. Pure.

    The GraphQL endpoint takes reads and writes over one verb, so the guard
    lives beside the sender rather than in a comment. This script sends one
    constant document; the guard exists so that editing the constant cannot
    quietly turn a read-only tool into a writing one.
    """
    banned = {"mutation", "subscription"}
    return bool(banned.intersection(words(document)))


def allow_list_from_graphql(body):
    """Normalise the GraphQL answer. Pure. (setting, apps_setting, entries, note)."""
    if not isinstance(body, dict):
        return (None, None, [], "no readable GraphQL body came back.")
    errors = body.get("errors") or []
    org = ((body.get("data") or {}).get("organization")) or {}
    if not org:
        detail = errors[0].get("message") if errors and isinstance(errors[0], dict) else ""
        return (None, None, [],
                "the organization block was not returned: %s. Reading an IP "
                "allow list needs admin:org-class access, so an unreadable "
                "list here means your token, not an empty list."
                % (detail or "no organization in the response"))
    nodes = ((org.get("ipAllowListEntries") or {}).get("nodes")) or []
    entries = []
    for node in nodes:
        if not isinstance(node, dict):
            continue
        entries.append({"value": node.get("allowListValue"),
                        "active": bool(node.get("isActive")),
                        "name": node.get("name") or ""})
    return (org.get("ipAllowListEnabledSetting"),
            org.get("ipAllowListForInstalledAppsEnabledSetting"),
            entries,
            "read %d entr(y/ies)." % len(entries))


def verdict(refusal_state, coverage_state, setting):
    """The finding, in one state. Pure. (state, detail)."""
    if refusal_state not in ("ip-allow-list", "ip-allow-list-unaddressed"):
        return (refusal_state,
                "this refusal is not an allow-list refusal, so the rest of "
                "this script is not about your problem.")
    if str(setting or "").upper() == "DISABLED":
        return ("allow-list-disabled",
                "the organization reports the allow list as disabled, which "
                "does not agree with the refusal. Check that you read the "
                "same organization the failing call was made against.")
    if coverage_state == "covered-but-inactive":
        return ("entry-exists-but-is-off",
                "an entry covering this address exists and is switched off. "
                "Somebody already did the work; it just is not active.")
    if coverage_state == "covered":
        return ("covered-yet-refused",
                "an active entry covers this address, so either the refusal "
                "predates the entry or the call was against a different "
                "organization. Re-run the probe before escalating.")
    if coverage_state in ("not-covered", "not-covered-some-unevaluated"):
        return ("address-not-covered",
                "no active entry covers the address GitHub saw. This is the "
                "ordinary case and the repair is one entry.")
    return ("rule-unreadable",
            "the refusal is an allow-list refusal and the list itself could "
            "not be read, which needs admin:org-class access. The cause is "
            "established; the entry that would have covered you is not.")


def repair(state, address, org):
    """The sentence a reader has to act on. Pure. Nothing here is executed."""
    if state == "entry-exists-but-is-off":
        return ("ask an owner of %s to switch the existing entry back on. "
                "Adding a second entry for the same range will not help while "
                "the first one is inactive." % org)
    if state in ("address-not-covered", "rule-unreadable"):
        return ("ask an owner of %s to add %s, or the documented egress range "
                "of this runner pool, to the organization IP allow list. For "
                "a GitHub App, enabling the App-managed allow list contributes "
                "its ranges for installation tokens. Nothing here adds "
                "anything." % (org, (address or "this job's egress range") +
                               ("/32" if address and "." in address else "")))
    if state == "covered-yet-refused":
        return ("re-run the probe from this machine. A covered address that "
                "is still refused usually means the reading and the refusal "
                "came from different places or different organizations.")
    if state == "allow-list-disabled":
        return ("confirm which organization the failing call names. A "
                "disabled list cannot produce this refusal.")
    return ("sort the refusal by its body before doing anything about "
            "addresses. This script found no allow-list refusal to repair.")


def get(session, path):
    """One GET. Returns the response object."""
    response = session.get(API + path, timeout=30)
    if response.status_code == 401:
        log.warning("401 from GitHub on %s: the credential itself was not "
                    "accepted, which is a different note", path)
    return response


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("org", help="the organization the calls are refused by")
    parser.add_argument("--path",
                        help="the org-scoped path to probe, default "
                             "/orgs/{org}/repos?per_page=1")
    parser.add_argument("--egress", action="append", default=[],
                        help="a CIDR you believe this job leaves from; repeatable")
    parser.add_argument("--seen-elsewhere", type=int,
                        help="the status the same token gets from a machine "
                             "that works")
    parser.add_argument("--org-allow-list", action="store_true",
                        help="read the list itself; needs admin:org-class access")
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_TOKEN (the same read-only token the failing job holds)")
        return 2

    rest, points = read_cost(args.org_allow_list)
    log.info("read cost: %d REST request(s) against the core hourly quota, "
             "%d GraphQL point(s)", rest, points)

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        # GitHub refuses requests with no User-Agent before it looks at auth.
        "User-Agent": UA,
    })

    kind = token_kind(token)
    which_list, which_detail = list_that_applies(kind)
    log.info("token: %s. %s: %s", kind, which_list, which_detail)

    path = args.path or ("/orgs/%s/repos?per_page=1" % args.org)
    probe = get(session, path)
    log.info("probe: GET %s -> HTTP %s", path, probe.status_code)
    body_text = probe.text or ""
    refusal_state, refusal_detail = classify_refusal(
        probe.status_code, body_text, dict(probe.headers))
    log.info("refusal: %s. %s", refusal_state, refusal_detail)

    address = address_in_message(body_text)
    if address:
        log.info("address GitHub saw: %s", address)

    egress_state, egress_detail = egress_assumption(args.egress, address)
    log.info("%s: %s", egress_state, egress_detail)

    setting, apps_setting, entries, note = None, None, [], "not read"
    if args.org_allow_list:
        if refuses_mutation(ALLOW_LIST_QUERY):
            log.error("the allow-list document is not a read; refusing to send it")
            return 2
        graph = session.post(API + "/graphql",
                             json={"query": ALLOW_LIST_QUERY,
                                   "variables": {"login": args.org}},
                             timeout=30)
        try:
            payload = graph.json()
        except ValueError:
            payload = None
        setting, apps_setting, entries, note = allow_list_from_graphql(payload)
        log.info("allow list: setting=%s, apps=%s, %s", setting, apps_setting, note)

    coverage_state, entry = covered_by(entries, address) if args.org_allow_list \\
        else ("rule-unread", None)
    if args.org_allow_list:
        log.info("coverage: %s%s", coverage_state,
                 "" if entry is None else " by %r" % entry.get("value"))

    paired_state, paired_detail = paired_reading(probe.status_code, args.seen_elsewhere)
    log.info("paired reading: %s. %s", paired_state, paired_detail)

    state, detail = verdict(refusal_state, coverage_state, setting)
    log.info("%s: %s", state, detail)
    log.info("repair: %s", repair(state, address, args.org))

    print(json.dumps({
        "organization": args.org,
        "probe_path": path,
        "probe_status": probe.status_code,
        "token_kind": kind,
        "list_that_applies": which_list,
        "refusal_state": refusal_state,
        "address_github_saw": address,
        "declared_egress": args.egress,
        "egress_state": egress_state,
        "allow_list_setting": setting,
        "app_managed_setting": apps_setting,
        "entries_read": len(entries),
        "coverage_state": coverage_state,
        "paired_state": paired_state,
        "state": state,
        "detail": detail,
        "repair": repair(state, address, args.org),
    }, indent=2, default=str))
    return 1 if state in ("address-not-covered", "entry-exists-but-is-off",
                          "rule-unreadable") else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-ip-allow-list.mjs",
"js": '''/**
 * Say whether a 403 came from an organization IP allow list.
 *
 * Read only. Two GETs, plus one optional GraphQL query, which is a read that
 * happens to travel over the same verb a write would. Nothing is added to any
 * allow list: the script compares what is there against the address GitHub
 * saw and prints the request for an organization owner to make.
 *
 * The refusal is a check on the source address, not on the credential, which
 * is why the identical token succeeds from a laptop and fails on a runner.
 *
 * Environment:
 *   GITHUB_TOKEN       the same read-only token the failing job holds
 *   GITHUB_ORG         the organization the calls are refused by
 *   GITHUB_PROBE_PATH  optional org-scoped path to probe
 *   GITHUB_EGRESS      optional comma-separated CIDRs you believe you use
 *   GITHUB_ELSEWHERE   optional status the same token gets from a good machine
 *   GITHUB_READ_LIST   set to 1 to read the list itself (needs admin:org)
 */
const API = 'https://api.github.com';
const UA = 'github-ip-allow-list/1.0';

/** Sentences the other causes of a 403 put in the body. Corroboration only. */
export const QUOTA_MARKERS = ['api rate limit exceeded'];
export const SECONDARY_MARKERS = ['secondary rate limit'];
export const USER_AGENT_MARKERS = ['user-agent', 'user agent'];
export const ALLOW_LIST_MARKERS = ['ip allow list', 'not permitted to access this resource'];

/** One query, one point, refused before it is sent if it stops being a read. */
export const ALLOW_LIST_QUERY = `
query($login: String!) {
  organization(login: $login) {
    ipAllowListEnabledSetting
    ipAllowListForInstalledAppsEnabledSetting
    ipAllowListEntries(first: 100) {
      nodes { allowListValue isActive name }
    }
  }
}
`;

export const TOKEN_PREFIXES = [
  ['github_pat_', 'fine-grained PAT'],
  ['ghp_', 'classic PAT'],
  ['gho_', 'OAuth user token'],
  ['ghu_', 'App user-to-server token'],
  ['ghs_', 'App installation token'],
  ['ghr_', 'App refresh token'],
];

export const APP_MANAGED_APPLIES = ['App installation token'];

/** [REST requests, GraphQL points] this run will spend. Pure. */
export function readCost(withAllowList = false) {
  return [2, withAllowList ? 1 : 0];
}

/** Name the credential from its prefix. Pure. */
export function tokenKind(token) {
  const value = String(token ?? '').trim();
  for (const [prefix, name] of TOKEN_PREFIXES) {
    if (value.startsWith(prefix)) return name;
  }
  return 'unknown';
}

/** Which allow list judges this credential. Pure. [which, detail]. */
export function listThatApplies(kind) {
  if (APP_MANAGED_APPLIES.includes(kind)) {
    return ['org-list-plus-app-managed', "an installation token is judged "
      + "against the organization's list, and where the organization has "
      + "enabled the App-managed setting the App's own ranges are contributed "
      + 'to it automatically.'];
  }
  if (kind === 'App user-to-server token') {
    return ['org-list-only', 'a user-to-server token acts for a person, so it '
      + "is judged against the organization's own list even when the App's "
      + 'ranges are allowed. An App whose background sync works and whose '
      + 'interactive calls do not is this exact case.'];
  }
  return ['org-list-only', 'this credential carries no App identity, so only '
    + "the organization's own allow list applies to it."];
}

/** Four dot-separated numbers in 0..255. Pure. No regular expression. */
export function looksLikeIpv4(text) {
  const parts = String(text ?? '').split('.');
  if (parts.length !== 4) return false;
  for (const part of parts) {
    if (part.length === 0 || part.length > 3) return false;
    for (const ch of part) if (ch < '0' || ch > '9') return false;
    if (Number(part) > 255) return false;
  }
  return true;
}

/** A rough IPv6 test. The script never does arithmetic on one. Pure. */
export function looksLikeIpv6(text) {
  const value = String(text ?? '');
  if ((value.match(/:/g) || []).length < 2) return false;
  for (const group of value.split(':')) {
    if (group === '') continue;
    if (group.length > 4) return false;
    for (const ch of group.toLowerCase()) {
      if (!'0123456789abcdef'.includes(ch)) return false;
    }
  }
  return true;
}

/** The address GitHub says it saw, or null. Pure. Tokenised, not matched. */
export function addressInMessage(message) {
  for (const raw of String(message ?? '').split(/\\s+/)) {
    let candidate = raw;
    while (candidate.length && '.,;:()[]<>"\\''.includes(candidate[candidate.length - 1])) {
      candidate = candidate.slice(0, -1);
    }
    while (candidate.length && '.,;:()[]<>"\\''.includes(candidate[0])) {
      candidate = candidate.slice(1);
    }
    if (looksLikeIpv4(candidate) || looksLikeIpv6(candidate)) return candidate;
  }
  return null;
}

/** Case-insensitive header read against a plain object. Pure. */
export function headerValue(headers, name) {
  if (!headers || typeof headers !== 'object') return null;
  const wanted = String(name).toLowerCase();
  for (const key of Object.keys(headers)) {
    if (key.toLowerCase() === wanted) return headers[key];
  }
  return null;
}

/** Sort one refusal into its cause. Pure. [state, detail]. */
export function classifyRefusal(status, bodyText, headers = null) {
  const text = String(bodyText ?? '').toLowerCase();
  const code = Number(status) || 0;
  if (![401, 403, 429].includes(code)) {
    return ['not-a-refusal', `HTTP ${status} is not a refusal, so there is `
      + 'nothing here to sort.'];
  }
  if (SECONDARY_MARKERS.some((m) => text.includes(m))) {
    return ['secondary-limit', 'the body names a secondary rate limit. Wait '
      + 'for retry-after and slow down; no allow-list entry is involved.'];
  }
  const remaining = headerValue(headers, 'x-ratelimit-remaining');
  if (QUOTA_MARKERS.some((m) => text.includes(m)) || String(remaining) === '0') {
    return ['primary-quota-exhausted', 'primary quota is spent. '
      + 'x-ratelimit-reset says when it returns, and the address is not the '
      + 'problem.'];
  }
  if (addressInMessage(bodyText) !== null) {
    return ['ip-allow-list', 'the body names an IP address, which no other 403 '
      + 'on this API does. This is a check on where the request came from, not '
      + 'on what it carried.'];
  }
  if (ALLOW_LIST_MARKERS.some((m) => text.includes(m))) {
    return ['ip-allow-list-unaddressed', 'the body reads like an allow-list '
      + 'refusal but names no address. Treat the cause as the allow list and '
      + 'get the egress address another way.'];
  }
  if (USER_AGENT_MARKERS.some((m) => text.includes(m))) {
    return ['user-agent-rule', 'the body names the User-Agent header. That '
      + 'check runs before authentication and has its own note.'];
  }
  if (code === 401) {
    return ['credential-rejected', '401 means the credential itself was not '
      + 'accepted. An allow list refuses with 403 and a body that names an '
      + 'address.'];
  }
  return ['permission-or-role', 'no rule named itself in the body, which is '
    + 'what a missing permission or too low a repository role looks like.'];
}

/** Dotted quad to a number, or null. Pure. */
export function ipv4ToInt(text) {
  if (!looksLikeIpv4(text)) return null;
  let total = 0;
  for (const part of String(text).split('.')) total = total * 256 + Number(part);
  return total;
}

/** Is this address inside this CIDR. Pure. true, false or null for unevaluated. */
export function cidrContains(cidr, address) {
  const value = String(cidr ?? '').trim();
  if (!value) return null;
  let net = value;
  let prefix = 32;
  if (value.includes('/')) {
    const cut = value.indexOf('/');
    net = value.slice(0, cut);
    const bits = value.slice(cut + 1);
    if (!bits.length || [...bits].some((c) => c < '0' || c > '9')) return null;
    prefix = Number(bits);
  }
  if (net.includes(':') || String(address ?? '').includes(':')) return null;
  const left = ipv4ToInt(net);
  const right = ipv4ToInt(address);
  if (left === null || right === null || prefix > 32) return null;
  if (prefix === 0) return true;
  const mask = prefix === 32 ? 0xFFFFFFFF : (0xFFFFFFFF - (2 ** (32 - prefix) - 1));
  return (left & mask) >>> 0 === (right & mask) >>> 0;
}

/** Does any active entry cover this address. Pure. [state, entry]. */
export function coveredBy(entries, address) {
  if (address === null || address === undefined) return ['address-unknown', null];
  if (!entries || entries.length === 0) return ['no-entries', null];
  let inactive = null;
  let unevaluated = false;
  for (const entry of entries) {
    const hit = cidrContains(entry.value, address);
    if (hit === null) { unevaluated = true; continue; }
    if (hit && entry.active) return ['covered', entry];
    if (hit && !inactive) inactive = entry;
  }
  if (inactive) return ['covered-but-inactive', inactive];
  if (unevaluated) return ['not-covered-some-unevaluated', null];
  return ['not-covered', null];
}

/** Declared egress against the address GitHub really saw. Pure. */
export function egressAssumption(declared, address) {
  if (address === null || address === undefined) {
    return ['address-unknown', 'no address was reported, so there is nothing '
      + 'to compare your declared egress against.'];
  }
  if (!declared || declared.length === 0) {
    return ['nothing-declared', 'declare the ranges you believe this job '
      + 'leaves from and this becomes a check rather than a reading.'];
  }
  for (const cidr of declared) {
    if (cidrContains(cidr, address) === true) {
      return ['egress-as-expected', `the address GitHub saw is inside ${cidr}, `
        + 'so your egress assumption holds and the range simply is not allowed '
        + 'yet.'];
    }
  }
  return ['egress-assumption-wrong', 'the address GitHub saw is outside every '
    + `range you declared (${declared.join(', ')}), so adding those ranges `
    + 'would not have helped. Find out what this job really egresses through '
    + 'before asking for a change.'];
}

/** Two readings of the same call from two machines. Pure. [state, detail]. */
export function pairedReading(statusHere, statusElsewhere) {
  const here = Number(statusHere) || 0;
  const there = (statusElsewhere === null || statusElsewhere === undefined)
    ? null : Number(statusElsewhere);
  if (there === null) {
    return ['single-reading', 'only this machine was read. Supply the status '
      + 'the same token gets from a machine that works and the network path '
      + 'stops being a hunch.'];
  }
  if (here === 403 && there === 200) {
    return ['network-path', 'the same token is refused here and accepted '
      + 'there, so the difference is the source address and nothing else.'];
  }
  if (here === 403 && there === 403) {
    return ['refused-everywhere', 'both addresses are refused. Either the '
      + 'allow list covers neither, or the cause is the credential after all.'];
  }
  if (here === 200) {
    return ['no-refusal', 'this machine was not refused, so there is nothing '
      + 'to explain from here. Run this on the machine that fails.'];
  }
  return ['inconclusive', 'the pair of statuses does not describe an allow '
    + 'list. Sort the refusal by its body first.'];
}

/** Bare words in a GraphQL document. Pure. */
export function words(document) {
  const out = [];
  let current = '';
  for (const ch of String(document ?? '')) {
    if (/[A-Za-z0-9_]/.test(ch)) current += ch;
    else { if (current) out.push(current.toLowerCase()); current = ''; }
  }
  if (current) out.push(current.toLowerCase());
  return out;
}

/** Would this document change something. Pure. */
export function refusesMutation(document) {
  const banned = ['mutation', 'subscription'];
  return words(document).some((w) => banned.includes(w));
}

/** Normalise the GraphQL answer. Pure. [setting, appsSetting, entries, note]. */
export function allowListFromGraphql(body) {
  if (!body || typeof body !== 'object') {
    return [null, null, [], 'no readable GraphQL body came back.'];
  }
  const errors = body.errors || [];
  const org = (body.data && body.data.organization) || null;
  if (!org) {
    const detail = errors.length && errors[0] && errors[0].message
      ? errors[0].message : 'no organization in the response';
    return [null, null, [], `the organization block was not returned: ${detail}. `
      + 'Reading an IP allow list needs admin:org-class access, so an '
      + 'unreadable list here means your token, not an empty list.'];
  }
  const nodes = (org.ipAllowListEntries && org.ipAllowListEntries.nodes) || [];
  const entries = nodes.filter((n) => n && typeof n === 'object').map((n) => ({
    value: n.allowListValue,
    active: Boolean(n.isActive),
    name: n.name || '',
  }));
  return [org.ipAllowListEnabledSetting,
    org.ipAllowListForInstalledAppsEnabledSetting,
    entries,
    `read ${entries.length} entries.`];
}

/** The finding, in one state. Pure. [state, detail]. */
export function verdict(refusalState, coverageState, setting) {
  if (!['ip-allow-list', 'ip-allow-list-unaddressed'].includes(refusalState)) {
    return [refusalState, 'this refusal is not an allow-list refusal, so the '
      + 'rest of this script is not about your problem.'];
  }
  if (String(setting ?? '').toUpperCase() === 'DISABLED') {
    return ['allow-list-disabled', 'the organization reports the allow list as '
      + 'disabled, which does not agree with the refusal. Check that you read '
      + 'the same organization the failing call was made against.'];
  }
  if (coverageState === 'covered-but-inactive') {
    return ['entry-exists-but-is-off', 'an entry covering this address exists '
      + 'and is switched off. Somebody already did the work; it just is not '
      + 'active.'];
  }
  if (coverageState === 'covered') {
    return ['covered-yet-refused', 'an active entry covers this address, so '
      + 'either the refusal predates the entry or the call was against a '
      + 'different organization. Re-run the probe before escalating.'];
  }
  if (['not-covered', 'not-covered-some-unevaluated'].includes(coverageState)) {
    return ['address-not-covered', 'no active entry covers the address GitHub '
      + 'saw. This is the ordinary case and the repair is one entry.'];
  }
  return ['rule-unreadable', 'the refusal is an allow-list refusal and the list '
    + 'itself could not be read, which needs admin:org-class access. The cause '
    + 'is established; the entry that would have covered you is not.'];
}

/** The sentence a reader has to act on. Pure. Nothing here is executed. */
export function repair(state, address, org) {
  if (state === 'entry-exists-but-is-off') {
    return `ask an owner of ${org} to switch the existing entry back on. Adding `
      + 'a second entry for the same range will not help while the first one is '
      + 'inactive.';
  }
  if (['address-not-covered', 'rule-unreadable'].includes(state)) {
    const what = address ? `${address}${address.includes('.') ? '/32' : ''}`
      : "this job's egress range";
    return `ask an owner of ${org} to add ${what}, or the documented egress `
      + 'range of this runner pool, to the organization IP allow list. For a '
      + 'GitHub App, enabling the App-managed allow list contributes its ranges '
      + 'for installation tokens. Nothing here adds anything.';
  }
  if (state === 'covered-yet-refused') {
    return 're-run the probe from this machine. A covered address that is still '
      + 'refused usually means the reading and the refusal came from different '
      + 'places or different organizations.';
  }
  if (state === 'allow-list-disabled') {
    return 'confirm which organization the failing call names. A disabled list '
      + 'cannot produce this refusal.';
  }
  return 'sort the refusal by its body before doing anything about addresses. '
    + 'This script found no allow-list refusal to repair.';
}

function headers(token) {
  return {
    Authorization: `Bearer ${token}`,
    Accept: 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
    'Content-Type': 'application/json',
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
  const readList = process.env.GITHUB_READ_LIST === '1';
  const declared = (process.env.GITHUB_EGRESS || '').split(',')
    .map((s) => s.trim()).filter(Boolean);
  const elsewhere = process.env.GITHUB_ELSEWHERE
    ? Number(process.env.GITHUB_ELSEWHERE) : null;
  const [rest, points] = readCost(readList);
  console.log(`read cost: ${rest} REST request(s) against the core hourly quota, `
    + `${points} GraphQL point(s)`);

  const kind = tokenKind(token);
  const [whichList, whichDetail] = listThatApplies(kind);
  console.log(`token: ${kind}. ${whichList}: ${whichDetail}`);

  const path = process.env.GITHUB_PROBE_PATH || `/orgs/${org}/repos?per_page=1`;
  const probe = await fetch(`${API}${path}`, { headers: headers(token) });
  const bodyText = await probe.text();
  console.log(`probe: GET ${path} -> HTTP ${probe.status}`);

  const headerBag = {};
  probe.headers.forEach((value, key) => { headerBag[key] = value; });
  const [refusalState, refusalDetail] = classifyRefusal(probe.status, bodyText, headerBag);
  console.log(`refusal: ${refusalState}. ${refusalDetail}`);

  const address = addressInMessage(bodyText);
  if (address) console.log(`address GitHub saw: ${address}`);
  const [egressState, egressDetail] = egressAssumption(declared, address);
  console.log(`${egressState}: ${egressDetail}`);

  let setting = null;
  let appsSetting = null;
  let entries = [];
  let coverageState = 'rule-unread';
  if (readList) {
    if (refusesMutation(ALLOW_LIST_QUERY)) {
      console.error('the allow-list document is not a read; refusing to send it');
      process.exitCode = 2;
      return;
    }
    const graph = await fetch(`${API}/graphql`, {
      // A GraphQL query is a read. This is only how the document travels, and
      // refusesMutation() has already rejected anything that is not a read.
      method: 'POST',
      headers: headers(token),
      body: JSON.stringify({ query: ALLOW_LIST_QUERY, variables: { login: org } }),
    });
    let payload = null;
    try { payload = await graph.json(); } catch { payload = null; }
    [setting, appsSetting, entries] = allowListFromGraphql(payload);
    [coverageState] = coveredBy(entries, address);
    console.log(`allow list: setting=${setting}, apps=${appsSetting}, `
      + `entries=${entries.length}, coverage=${coverageState}`);
  }

  const [pairedState, pairedDetail] = pairedReading(probe.status, elsewhere);
  console.log(`paired reading: ${pairedState}. ${pairedDetail}`);
  const [state, detail] = verdict(refusalState, coverageState, setting);
  console.log(`${state}: ${detail}`);
  console.log(`repair: ${repair(state, address, org)}`);

  console.log(JSON.stringify({
    organization: org,
    probe_path: path,
    probe_status: probe.status,
    token_kind: kind,
    list_that_applies: whichList,
    refusal_state: refusalState,
    address_github_saw: address,
    declared_egress: declared,
    egress_state: egressState,
    allow_list_setting: setting,
    entries_read: entries.length,
    coverage_state: coverageState,
    paired_state: pairedState,
    state,
    detail,
    repair: repair(state, address, org),
  }, null, 2));
  process.exitCode = ['address-not-covered', 'entry-exists-but-is-off',
    'rule-unreadable'].includes(state) ? 1 : 0;
}

// Guarded so importing this file from the test runner does not start a run.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The suite is mostly recorded refusals, because the refusal you need to handle is the one you cannot conveniently produce: you would have to be on the blocked runner to get it. So the bodies are held as fixtures and the classifier is asserted against all five causes, including the one where the sentence has been reworded and the classification survives because it keys on the presence of an address rather than on the English. Then the address scan against a sentence with a full stop attached to the address, the CIDR arithmetic including the boundary cases people get wrong, and the deliberate three-valued result where an unevaluated entry is not reported as a miss. The last group is the note's headline: refused here, 200 there, same token.",
"test_py_file": "test_github_ip_allow_list.py",
"test_py": '''from github_ip_allow_list import (
    ALLOW_LIST_QUERY, address_in_message, allow_list_from_graphql,
    cidr_contains, classify_refusal, covered_by, egress_assumption,
    ipv4_to_int, list_that_applies, looks_like_ipv4, looks_like_ipv6,
    paired_reading, read_cost, refuses_mutation, repair, token_kind, verdict,
)

ALLOW_LIST_BODY = (
    "Although you appear to have the correct authorization credentials, the "
    "ACME organization has an IP allow list enabled, and 203.0.113.9 is not "
    "permitted to access this resource."
)
UA_BODY = ("Request forbidden by administrative rules. Please make sure your "
           "request has a User-Agent header.")
QUOTA_BODY = "API rate limit exceeded for user ID 12345."
SECONDARY_BODY = "You have exceeded a secondary rate limit."
PERMISSION_BODY = "Resource not accessible by integration"

ENTRIES = [
    {"value": "198.51.100.0/24", "active": True, "name": "office"},
    {"value": "203.0.113.0/24", "active": False, "name": "old ci"},
    {"value": "2001:db8::/32", "active": True, "name": "ipv6 office"},
]


def test_the_allow_list_refusal_is_the_only_one_naming_an_address():
    state, detail = classify_refusal(403, ALLOW_LIST_BODY, {})
    assert state == "ip-allow-list"
    assert "names an IP address" in detail
    assert classify_refusal(403, UA_BODY, {})[0] == "user-agent-rule"
    assert classify_refusal(403, PERMISSION_BODY, {})[0] == "permission-or-role"


def test_quota_and_secondary_limits_are_sorted_out_first():
    assert classify_refusal(403, QUOTA_BODY, {})[0] == "primary-quota-exhausted"
    assert classify_refusal(429, SECONDARY_BODY, {})[0] == "secondary-limit"
    # The header is enough on its own, because a proxy can replace the body.
    assert classify_refusal(403, "", {"X-RateLimit-Remaining": "0"})[0] == (
        "primary-quota-exhausted")


def test_a_reworded_allow_list_message_still_classifies():
    # The English is corroboration. The address is the signal, so GitHub can
    # rewrite the sentence without this becoming a permission problem.
    reworded = "Access from 198.51.100.77 is blocked by policy for this org."
    assert classify_refusal(403, reworded, {})[0] == "ip-allow-list"


def test_an_allow_list_message_with_no_address_is_kept_apart():
    state, _ = classify_refusal(403, "This org has an IP allow list enabled.", {})
    assert state == "ip-allow-list-unaddressed"


def test_a_200_is_not_a_refusal_to_sort():
    assert classify_refusal(200, "[]", {})[0] == "not-a-refusal"
    assert classify_refusal(401, "Bad credentials", {})[0] == "credential-rejected"


def test_the_address_survives_the_full_stop_at_the_end_of_the_sentence():
    assert address_in_message(ALLOW_LIST_BODY) == "203.0.113.9"
    assert address_in_message("from (2001:db8::1) today") == "2001:db8::1"
    assert address_in_message("no address at all here") is None
    # A version number is four groups but not four bytes.
    assert address_in_message("version 1.2.3.400 shipped") is None


def test_what_an_address_looks_like():
    assert looks_like_ipv4("203.0.113.9") is True
    assert looks_like_ipv4("203.0.113") is False
    assert looks_like_ipv4("203.0.113.256") is False
    assert looks_like_ipv6("2001:db8::1") is True
    assert looks_like_ipv6("203.0.113.9") is False


def test_cidr_arithmetic_at_the_edges():
    assert cidr_contains("203.0.113.0/24", "203.0.113.9") is True
    assert cidr_contains("203.0.113.0/24", "203.0.114.9") is False
    assert cidr_contains("203.0.113.9", "203.0.113.9") is True
    assert cidr_contains("0.0.0.0/0", "8.8.8.8") is True
    assert ipv4_to_int("0.0.0.1") == 1


def test_an_unevaluated_entry_is_none_and_not_false():
    # Reporting an IPv6 entry as a miss would tell somebody their address is
    # uncovered when the entry covering it was one this script cannot read.
    assert cidr_contains("2001:db8::/32", "203.0.113.9") is None
    assert cidr_contains("not-a-cidr", "203.0.113.9") is None
    assert cidr_contains("203.0.113.0/xx", "203.0.113.9") is None


def test_an_entry_that_exists_but_is_switched_off_is_its_own_finding():
    state, entry = covered_by(ENTRIES, "203.0.113.9")
    assert state == "covered-but-inactive"
    assert entry["name"] == "old ci"
    assert verdict("ip-allow-list", state, "ENABLED")[0] == "entry-exists-but-is-off"


def test_coverage_reports_the_entries_it_could_not_evaluate():
    state, entry = covered_by(ENTRIES, "192.0.2.5")
    assert state == "not-covered-some-unevaluated"
    assert entry is None
    assert covered_by(ENTRIES, "198.51.100.4")[0] == "covered"
    assert covered_by([], "198.51.100.4")[0] == "no-entries"


def test_a_wrong_egress_assumption_is_named_before_anybody_files_a_ticket():
    state, detail = egress_assumption(["198.51.100.0/24"], "203.0.113.9")
    assert state == "egress-assumption-wrong"
    assert "would not have helped" in detail
    assert egress_assumption(["203.0.113.0/24"], "203.0.113.9")[0] == (
        "egress-as-expected")
    assert egress_assumption([], "203.0.113.9")[0] == "nothing-declared"


def test_the_pair_of_readings_is_the_headline():
    state, detail = paired_reading(403, 200)
    assert state == "network-path"
    assert "source address" in detail
    assert paired_reading(403, 403)[0] == "refused-everywhere"
    assert paired_reading(403, None)[0] == "single-reading"
    assert paired_reading(200, 200)[0] == "no-refusal"


def test_an_installation_token_and_a_user_token_are_judged_differently():
    which, _ = list_that_applies("App installation token")
    assert which == "org-list-plus-app-managed"
    which, detail = list_that_applies("App user-to-server token")
    assert which == "org-list-only"
    assert "background sync works" in detail
    assert token_kind("ghs_x") == "App installation token"
    assert token_kind("ghu_x") == "App user-to-server token"


def test_an_unreadable_list_is_not_an_empty_one():
    body = {"data": {"organization": None},
            "errors": [{"message": "Resource not accessible"}]}
    setting, apps, entries, note = allow_list_from_graphql(body)
    assert setting is None and entries == []
    assert "admin:org" in note
    state, detail = verdict("ip-allow-list", "rule-unread", None)
    assert state == "rule-unreadable"
    assert "cause is established" in detail


def test_the_entries_are_normalised_off_the_graphql_shape():
    body = {"data": {"organization": {
        "ipAllowListEnabledSetting": "ENABLED",
        "ipAllowListForInstalledAppsEnabledSetting": "DISABLED",
        "ipAllowListEntries": {"nodes": [
            {"allowListValue": "198.51.100.0/24", "isActive": True, "name": "office"},
        ]}}}}
    setting, apps, entries, _ = allow_list_from_graphql(body)
    assert setting == "ENABLED" and apps == "DISABLED"
    assert entries == [{"value": "198.51.100.0/24", "active": True, "name": "office"}]


def test_the_query_this_script_sends_is_a_read():
    assert refuses_mutation(ALLOW_LIST_QUERY) is False
    assert refuses_mutation("mutation M { createIpAllowListEntry { id } }") is True
    assert refuses_mutation("subscription S { x }") is True


def test_the_repair_asks_a_human_and_adds_nothing():
    fix = repair("address-not-covered", "203.0.113.9", "acme")
    assert "ask an owner of acme" in fix
    assert "203.0.113.9/32" in fix
    assert "adds anything" in fix
    assert "switch the existing entry back on" in repair(
        "entry-exists-but-is-off", "203.0.113.9", "acme")


def test_the_two_budgets_are_counted_separately():
    assert read_cost() == (2, 0)
    assert read_cost(True) == (2, 1)
''',
"test_js_file": "github-ip-allow-list.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  ALLOW_LIST_QUERY, addressInMessage, allowListFromGraphql, cidrContains,
  classifyRefusal, coveredBy, egressAssumption, ipv4ToInt, listThatApplies,
  looksLikeIpv4, looksLikeIpv6, pairedReading, readCost, refusesMutation,
  repair, tokenKind, verdict,
} from './github-ip-allow-list.mjs';

const ALLOW_LIST_BODY = 'Although you appear to have the correct authorization '
  + 'credentials, the ACME organization has an IP allow list enabled, and '
  + '203.0.113.9 is not permitted to access this resource.';
const UA_BODY = 'Request forbidden by administrative rules. Please make sure '
  + 'your request has a User-Agent header.';

const ENTRIES = [
  { value: '198.51.100.0/24', active: true, name: 'office' },
  { value: '203.0.113.0/24', active: false, name: 'old ci' },
  { value: '2001:db8::/32', active: true, name: 'ipv6 office' },
];

test('the allow list refusal is the only one naming an address', () => {
  const [state, detail] = classifyRefusal(403, ALLOW_LIST_BODY, {});
  assert.equal(state, 'ip-allow-list');
  assert.match(detail, /names an IP address/);
  assert.equal(classifyRefusal(403, UA_BODY, {})[0], 'user-agent-rule');
  assert.equal(
    classifyRefusal(403, 'Resource not accessible by integration', {})[0],
    'permission-or-role',
  );
});

test('quota and secondary limits are sorted out first', () => {
  assert.equal(
    classifyRefusal(403, 'API rate limit exceeded for user ID 1.', {})[0],
    'primary-quota-exhausted',
  );
  assert.equal(
    classifyRefusal(429, 'You have exceeded a secondary rate limit.', {})[0],
    'secondary-limit',
  );
  assert.equal(
    classifyRefusal(403, '', { 'X-RateLimit-Remaining': '0' })[0],
    'primary-quota-exhausted',
  );
});

test('a reworded allow list message still classifies', () => {
  const reworded = 'Access from 198.51.100.77 is blocked by policy for this org.';
  assert.equal(classifyRefusal(403, reworded, {})[0], 'ip-allow-list');
});

test('an allow list message with no address is kept apart', () => {
  assert.equal(
    classifyRefusal(403, 'This org has an IP allow list enabled.', {})[0],
    'ip-allow-list-unaddressed',
  );
});

test('the address survives the full stop at the end of the sentence', () => {
  assert.equal(addressInMessage(ALLOW_LIST_BODY), '203.0.113.9');
  assert.equal(addressInMessage('from (2001:db8::1) today'), '2001:db8::1');
  assert.equal(addressInMessage('no address at all here'), null);
  assert.equal(addressInMessage('version 1.2.3.400 shipped'), null);
});

test('what an address looks like', () => {
  assert.equal(looksLikeIpv4('203.0.113.9'), true);
  assert.equal(looksLikeIpv4('203.0.113.256'), false);
  assert.equal(looksLikeIpv6('2001:db8::1'), true);
  assert.equal(looksLikeIpv6('203.0.113.9'), false);
});

test('cidr arithmetic at the edges', () => {
  assert.equal(cidrContains('203.0.113.0/24', '203.0.113.9'), true);
  assert.equal(cidrContains('203.0.113.0/24', '203.0.114.9'), false);
  assert.equal(cidrContains('203.0.113.9', '203.0.113.9'), true);
  assert.equal(cidrContains('0.0.0.0/0', '8.8.8.8'), true);
  assert.equal(ipv4ToInt('0.0.0.1'), 1);
});

test('an unevaluated entry is null and not false', () => {
  assert.equal(cidrContains('2001:db8::/32', '203.0.113.9'), null);
  assert.equal(cidrContains('not-a-cidr', '203.0.113.9'), null);
  assert.equal(cidrContains('203.0.113.0/xx', '203.0.113.9'), null);
});

test('an entry that exists but is switched off is its own finding', () => {
  const [state, entry] = coveredBy(ENTRIES, '203.0.113.9');
  assert.equal(state, 'covered-but-inactive');
  assert.equal(entry.name, 'old ci');
  assert.equal(verdict('ip-allow-list', state, 'ENABLED')[0], 'entry-exists-but-is-off');
});

test('coverage reports the entries it could not evaluate', () => {
  assert.equal(coveredBy(ENTRIES, '192.0.2.5')[0], 'not-covered-some-unevaluated');
  assert.equal(coveredBy(ENTRIES, '198.51.100.4')[0], 'covered');
  assert.equal(coveredBy([], '198.51.100.4')[0], 'no-entries');
});

test('a wrong egress assumption is named before anybody files a ticket', () => {
  const [state, detail] = egressAssumption(['198.51.100.0/24'], '203.0.113.9');
  assert.equal(state, 'egress-assumption-wrong');
  assert.match(detail, /would not have helped/);
  assert.equal(egressAssumption(['203.0.113.0/24'], '203.0.113.9')[0], 'egress-as-expected');
  assert.equal(egressAssumption([], '203.0.113.9')[0], 'nothing-declared');
});

test('the pair of readings is the headline', () => {
  const [state, detail] = pairedReading(403, 200);
  assert.equal(state, 'network-path');
  assert.match(detail, /source address/);
  assert.equal(pairedReading(403, 403)[0], 'refused-everywhere');
  assert.equal(pairedReading(403, null)[0], 'single-reading');
  assert.equal(pairedReading(200, 200)[0], 'no-refusal');
});

test('an installation token and a user token are judged differently', () => {
  assert.equal(listThatApplies('App installation token')[0], 'org-list-plus-app-managed');
  const [which, detail] = listThatApplies('App user-to-server token');
  assert.equal(which, 'org-list-only');
  assert.match(detail, /background sync works/);
  assert.equal(tokenKind('ghs_x'), 'App installation token');
  assert.equal(tokenKind('ghu_x'), 'App user-to-server token');
});

test('an unreadable list is not an empty one', () => {
  const [setting, , entries, note] = allowListFromGraphql({
    data: { organization: null },
    errors: [{ message: 'Resource not accessible' }],
  });
  assert.equal(setting, null);
  assert.deepEqual(entries, []);
  assert.match(note, /admin:org/);
  assert.equal(verdict('ip-allow-list', 'rule-unread', null)[0], 'rule-unreadable');
});

test('the entries are normalised off the graphql shape', () => {
  const [setting, apps, entries] = allowListFromGraphql({
    data: {
      organization: {
        ipAllowListEnabledSetting: 'ENABLED',
        ipAllowListForInstalledAppsEnabledSetting: 'DISABLED',
        ipAllowListEntries: {
          nodes: [{ allowListValue: '198.51.100.0/24', isActive: true, name: 'office' }],
        },
      },
    },
  });
  assert.equal(setting, 'ENABLED');
  assert.equal(apps, 'DISABLED');
  assert.deepEqual(entries, [{ value: '198.51.100.0/24', active: true, name: 'office' }]);
});

test('the query this script sends is a read', () => {
  assert.equal(refusesMutation(ALLOW_LIST_QUERY), false);
  assert.equal(refusesMutation('mutation M { createIpAllowListEntry { id } }'), true);
  assert.equal(refusesMutation('subscription S { x }'), true);
});

test('the repair asks a human and adds nothing', () => {
  const fix = repair('address-not-covered', '203.0.113.9', 'acme');
  assert.match(fix, /ask an owner of acme/);
  assert.match(fix, /203\\.0\\.113\\.9\\/32/);
  assert.match(fix, /adds anything/);
});

test('the two budgets are counted separately', () => {
  assert.deepEqual(readCost(), [2, 0]);
  assert.deepEqual(readCost(true), [2, 1]);
});
''',
"faq": [
 ("The same token works on my laptop. Does that not prove the token is fine?",
  "It proves the token is fine <em>from your laptop</em>. An IP allow list is a check on the connection, not on the credential, so the two readings are answering different questions and only look like the same experiment. That is why this is the one diagnostic in the section whose result depends on which machine you run it from: the whole finding is the difference between two locations holding one token. Take the reading on the runner, and pass the laptop's status in so the pair is stated rather than remembered."),
 ("Anonymous requests from the same runner still work. How?",
  "An organization allow list governs access to that organization's resources. Unauthenticated reads of a public repository are not access to the organization in that sense, so they keep answering 200 from an address the organization refuses. It is a genuinely confusing signal, because it makes the network look healthy from exactly the machine that is being refused, and it is why people conclude the problem must be the credential."),
 ("How is this different from the User-Agent 403 that also names its own rule?",
  "Both name a rule in the body, and that note owns the general sort of a 403 into its causes. This is a fifth cause with a signal none of the others has: an IP address in the message. The script keys on that structurally rather than on the wording, so a rewritten sentence still classifies. The repairs have nothing in common either — one is a header your client sends, the other is an entry somebody with organization admin has to add."),
 ("Our GitHub App has an allow list of its own and calls are still refused. Why?",
  "Check which token the failing call carries. The App-managed allow list contributes the App's ranges for <em>installation</em> tokens where the organization has enabled that setting. A user-to-server token acts for a person and is judged against the organization's own list regardless, so an App can have a background sync that works perfectly and interactive calls that are refused, from the same process on the same machine."),
 ("Can the script add the range for me if I give it an admin token?",
  "No. Nothing in this section writes, and this is a case where that rule earns its keep: an allow-list entry is a security control, adding one is a decision about who may reach the organization, and a diagnostic tool is not the thing that should make it. The script reads the list, names the address that was refused, says which entry would have covered it, and prints the request for an owner to action."),
],
"related": [
 ("/github/user-agent-missing/", "The other 403 that names its own rule in the body"),
 ("/github/webhook-ip-allowlist-drift/", "The same idea in the other direction"),
 ("/github/404-masking-403/", "When the refusal arrives as a 404 instead"),
],
"citations": [CITE_IP_ALLOW_LIST, CITE_APP_IP_ALLOW_LIST, CITE_GRAPHQL_ORG, CITE_REST_BEST],
},
{
"slug": "org-2fa-requirement-removed-member",
"title": "Enforcing 2FA removed the machine account from the org",
"description": "Turning on required two-factor authentication removes members who do not comply. The token stays valid, the account stops being a member, and org repos 404.",
"h1": "Enforcing 2FA removed the machine account from the org",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github org required 2fa removed members",
             "github machine account removed from organization",
             "github api 404 org repos after 2fa",
             "github orgs members endpoint 204 404 302",
             "github two_factor_requirement_enabled api"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "On Tuesday the sync job read forty repositories. On Wednesday it reads none of them, and every call comes back 404 rather than 403. The token is checked first, because it always is: <code>GET /user</code> answers 200, the login is right, the expiry is months away, the scopes are unchanged. Nothing was rotated and nothing was deployed. What happened is that an owner turned on required two-factor authentication, and the accounts that did not have 2FA were <em>removed from the organization</em> — which for a machine account created in a hurry three years ago means all of them.",
"short_answer": """<p>Enabling a 2FA requirement does not refuse non-compliant members, it removes them. Members and outside collaborators without two-factor authentication are taken out of the organization, and nothing tells the integration holding their token.</p>
<p>Two reads settle it. <code>GET /user</code> proves the token is alive and names the login. <code>GET /orgs/{org}/members/{login}</code>, <strong>without following redirects</strong>, answers <code>204</code> if the account is a member and <code>302</code> if the <em>requester</em> is not one — and after a removal the requester is you. A client that follows that redirect lands on the public-members endpoint and answers a different question entirely. <code>GET /orgs/{org}</code> supplies the motive in <code>two_factor_requirement_enabled</code>, when you can still read it.</p>""",
"problem": """<p>The first hour goes on the token, because the token is the thing that usually breaks and the thing that can be checked in one call. That call passes. So does the next one, and the next: the credential authenticates, it has not expired, its scopes are the same as they were on Tuesday, and it can still read public repositories and the account's own gists. Everything about the credential is healthy, which is precisely the shape that makes this hard: the credential really is healthy. It just belongs to an account that is no longer in the organization.</p>
<p>The second hour goes on the 404s. A 404 on a private repository has a long list of causes, and the list is somebody else's note. What sends people down it is the belief that the repository is the subject. It is not; the subject is the account, and one read of the membership answers for all forty repositories at once instead of triaging them one at a time.</p>
<p>Then there is the part that makes it look like an outage rather than a policy change: it is not uniform. The requirement removes only the accounts that do not comply, so the two humans on the team, who have had 2FA on for years, notice nothing at all. Their tokens keep working. Only the bot went, and bots do not read email, so the notification that an owner enabled the requirement went to people for whom nothing changed.</p>""",
"why": """<p><strong>The policy removes, it does not refuse.</strong> This is the sentence the whole note turns on. Most policy in this API produces a refusal you can read: a 403 with a rule named in the body, a header naming what would have been accepted. This one changes the membership graph. Once the account is out, there is no policy left to report, because policy is not what is being applied any more — the account simply has no relationship to that organization, and its private repositories are invisible in the ordinary way.</p>
<p><strong>Which is why the symptom is 404 and not 403.</strong> GitHub answers 404 rather than 403 for private resources a caller cannot see, so a removed member gets exactly the response a caller who never had access gets, and exactly the response somebody would get for a repository that was deleted. The <a href="/github/404-masking-403/">404 triage note</a> is the one that sorts those causes generally. This note is the specific cause you can confirm with a single membership read, and it is worth checking early because it explains an entire organization's worth of 404s in one call.</p>
<p><strong>The membership endpoint answers with a redirect, and the redirect is the finding.</strong> <code>GET /orgs/{org}/members/{username}</code> returns 204 when the account is a member, 404 when the requester is a member and the named account is not, and <strong>302</strong> when the requester is not a member of the organization at all. When you are asking about yourself after being removed, the answer is that 302. Almost every HTTP client follows redirects by default, and the redirect goes to the <em>public</em> members endpoint, which asks whether the account's membership is publicly listed. A publicly-listed former member is not a thing, but the two endpoints can and do disagree in the other direction, so a client that follows the redirect quietly swaps one question for another. Turn redirect-following off for this call.</p>
<p><strong>The motive becomes unreadable at the moment you need it.</strong> <code>two_factor_requirement_enabled</code> on the organization object is only returned to a caller with enough organization access. Being removed is what takes that access away, so the field that would explain the removal is frequently absent <em>because of</em> the removal. That is not a bug to work around, it is a fact to report: the script says the field was unreadable and names the removal as the finding rather than pretending the requirement is off.</p>
<p><strong>Removal and never having joined are indistinguishable from here.</strong> A read-only observer sees the current graph, not its history. There is an audit log that records the removal, and reading it needs organization admin. So the honest finding is "this account is not a member, and the organization requires 2FA", which is a cause and a motive rather than a proof, and it is enough to act on. The script says so in those terms rather than claiming to have watched it happen.</p>""",
"steps": [
 {"h": "Prove the token is healthy, so that stops being the search",
  "body": """<p>The script reads <code>GET /user</code> first and prints that it succeeded, with the login it resolved. That line exists to close the investigation everyone runs first: the credential is fine, and every further minute spent on it is wasted. The same response carries <code>two_factor_authentication</code> when the token has the <code>user</code> scope, which becomes useful two steps later.</p>"""},
 {"h": "Ask the membership question without letting the client rewrite it",
  "body": """<p><code>GET /orgs/{org}/members/{login}</code> is sent with redirects disabled. 204 means the account is still a member. 302 means the requester is not one, which — when the requester is the account you are asking about — is the removal. A client that follows the redirect gets an answer from the public-members endpoint instead, and that answer is about a different property. The script reports which question was actually answered.</p>"""},
 {"h": "Read the motive while you still can",
  "body": """<p><code>GET /orgs/{org}</code> carries <code>two_factor_requirement_enabled</code> for callers with organization access. If it is <code>true</code>, the removal has a name. If the field is absent, the script says it was unreadable rather than reporting the requirement as off, because the most common reason for it to be missing is the removal itself.</p>"""},
 {"h": "Check whether you are the next one out",
  "body": """<p>When the account <em>is</em> still a member and the organization requires 2FA, the script compares that against <code>two_factor_authentication</code> on the account. A member with 2FA off inside an organization that requires it is a removal that has not happened yet — usually because the requirement was enabled after a grace conversation, or because the account joined a different organization with the same policy. That is the one reading here that is worth having before anything breaks.</p>"""},
 {"h": "Take the repair to the account, or past it",
  "body": """<p>The printed repair is either "enable 2FA on this account and have an owner re-invite it" or, better, "replace the machine account with a GitHub App installation". An installation is not a member and is not subject to member 2FA policy, so the same class of change cannot remove it. The script re-invites nobody and enables nothing; it prints and exits.</p>"""},
],
"verify": """<p>After the account is re-invited with 2FA enabled, the membership read stops redirecting and answers 204.</p>
<pre><code class="language-bash">GITHUB_TOKEN=$READ_ONLY_TOKEN python3 github_org_membership_lost.py acme
# read cost: 4 request(s) against the core hourly quota
# token: healthy — GET /user answered 200 as octobot. Nothing about the
#   credential explains what follows.
# membership: GET /orgs/acme/members/octobot -> HTTP 302 (redirects disabled)
#   requester-not-a-member: the 302 says the account asking is not a member of
#   acme. Asking about yourself, that is the removal.
# question answered: membership. Following the redirect would have answered a
#   question about public membership instead.
# motive: two_factor_requirement_enabled was not returned. Reading it needs org
#   access, and losing that access is what this finding is.
# state: not-a-member-motive-unreadable
# symptom: every private repository in acme answers 404, not 403, because a
#   non-member cannot see them at all.
# repair: enable 2FA on octobot and ask an owner of acme to re-invite it, or
#   replace the machine account with a GitHub App installation, which is not a
#   member and is unaffected by member 2FA policy.</code></pre>""",
"code_intro": "Three of the four reads are one line each; the work is in refusing to let an HTTP client answer a question you did not ask. The membership call goes out with redirect-following disabled and the script reports which question the status code it got is actually about, because a followed 302 produces a confident answer to a different one. Everything after that is pure: the status-to-state mapping, the three-valued readings where an absent field means unreadable rather than false, and the combination that turns a membership, a requirement and an account's own 2FA into one finding.",
"py_file": "github_org_membership_lost.py",
"py": '''"""Say whether an account was removed from an organization by a 2FA rule.

Read only. Four GETs and nothing else. Re-inviting a removed member is a write
and a decision for an organization owner, so this script does not make it: it
establishes the removal from readable state and prints the request.

The point of the note: enabling required two-factor authentication does not
refuse non-compliant members, it removes them. The token keeps working, the
account stops being a member, and every private repository in the organization
answers 404 rather than 403.

What this can and cannot see: the current graph, not its history. Removal and
never having joined look identical from here; the audit log that records the
removal needs organization admin. So the finding is a cause and a motive rather
than a proof, and it is reported in those terms.

Environment:

    GITHUB_TOKEN    the token the failing integration holds
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_org_membership_lost")

API = "https://api.github.com"
UA = "github-org-membership-lost/1.0"

# GET /orgs/{org}/members/{username} answers with a status and no body. The 302
# is the one that matters and the one a default HTTP client hides.
MEMBERSHIP_STATUS = {
    204: "member",
    302: "requester-not-a-member",
    404: "not-a-member",
    403: "membership-unreadable",
}


def read_cost():
    """Requests this run will spend against the core quota. Pure."""
    return 4


def membership_state(status):
    """What one membership status means. Pure. (state, detail).

    The 302 is documented as "requester is not an organization member". When
    the requester and the subject are the same account, that redirect is the
    whole finding, and it is the reading a redirect-following client destroys.
    """
    code = int(status or 0)
    state = MEMBERSHIP_STATUS.get(code, "unclear")
    if state == "member":
        return (state, "204 means the account is a member of this organization.")
    if state == "requester-not-a-member":
        return (state, "the 302 says the account asking is not a member of the "
                       "organization. Asking about yourself, that is the removal.")
    if state == "not-a-member":
        return (state, "404 here means the requester is a member and the named "
                       "account is not.")
    if state == "membership-unreadable":
        return (state, "403 on the membership read itself. The credential "
                       "reached GitHub and was refused; sort that refusal first.")
    return ("unclear", "HTTP %s is not one of the documented answers for this "
                       "endpoint." % status)


def question_answered(followed_redirect):
    """Which question the status code is about. Pure. (state, detail).

    A followed 302 lands on the public-members endpoint, which asks whether a
    membership is publicly listed. That is a different property, and the answer
    looks exactly as authoritative as the one you wanted.
    """
    if followed_redirect:
        return ("public-membership-instead",
                "the client followed the redirect, so this answer came from "
                "the public members endpoint and is about whether membership "
                "is publicly listed. Send the call again with redirects off.")
    return ("membership",
            "redirects were disabled, so the status describes membership "
            "rather than public membership.")


def own_two_factor(user_payload):
    """Whether this account has 2FA on. Pure. True, False or None.

    None means unreadable: the field is only present on the authenticated
    user's own record and only when the token carries the user scope. Reporting
    an absent field as False would invent a compliance failure.
    """
    if not isinstance(user_payload, dict):
        return None
    if "two_factor_authentication" not in user_payload:
        return None
    value = user_payload.get("two_factor_authentication")
    return None if value is None else bool(value)


def requirement_state(org_payload):
    """Whether the org requires 2FA. Pure. True, False or None.

    None means unreadable, and the most common reason for that is the removal
    itself: the field is returned to callers with organization access, and
    being removed is what takes it away.
    """
    if not isinstance(org_payload, dict):
        return None
    if "two_factor_requirement_enabled" not in org_payload:
        return None
    value = org_payload.get("two_factor_requirement_enabled")
    return None if value is None else bool(value)


def listed_in_orgs(orgs, org):
    """Is the organization in GET /user/orgs. Pure.

    Weaker evidence than it looks. Without read:org a classic token sees only
    the organizations whose membership the account has made public, so absence
    here is corroboration and never the finding.
    """
    wanted = str(org or "").strip().lower()
    for entry in orgs or []:
        login = entry.get("login") if isinstance(entry, dict) else entry
        if str(login or "").strip().lower() == wanted:
            return True
    return False


def combine(membership, requirement, own_2fa):
    """Turn three readings into one finding. Pure. (state, detail)."""
    gone = membership in ("requester-not-a-member", "not-a-member")
    if gone and requirement is True:
        return ("not-a-member-2fa-required",
                "the account is not a member and the organization requires "
                "two-factor authentication. That is the cause and its motive. "
                "Removal and never having joined are indistinguishable through "
                "the API, so this is a finding to act on rather than a proof.")
    if gone and requirement is None:
        return ("not-a-member-motive-unreadable",
                "the account is not a member and the 2FA requirement could not "
                "be read. Reading it needs organization access, and losing that "
                "access is what this finding is.")
    if gone:
        return ("not-a-member-no-requirement",
                "the account is not a member and the organization does not "
                "require 2FA, so something else removed it. An owner can read "
                "the audit log; a read-only token cannot.")
    if membership == "member" and requirement is True and own_2fa is False:
        return ("member-at-risk",
                "still a member, the organization requires 2FA, and this "
                "account reports two-factor authentication off. That is a "
                "removal that has not happened yet.")
    if membership == "member" and requirement is True and own_2fa is None:
        return ("member-compliance-unreadable",
                "still a member of an organization that requires 2FA, and this "
                "token cannot read whether the account complies. The user scope "
                "is what exposes that field.")
    if membership == "member" and requirement is True:
        return ("member-compliant",
                "a member, the requirement is on, and this account has 2FA. "
                "Nothing here explains a 404.")
    if membership == "member":
        return ("member-no-requirement",
                "a member of an organization with no 2FA requirement. This "
                "note is not your problem; sort the 404 another way.")
    return ("membership-unreadable",
            "the membership question was not answered, so nothing can be "
            "concluded about a removal.")


def symptom(state):
    """What the integration is seeing, given the finding. Pure."""
    if state.startswith("not-a-member"):
        return ("every private repository in the organization answers 404, not "
                "403, because a non-member cannot see them at all. Public "
                "repositories keep answering, which is what makes the token "
                "look healthy.")
    if state == "member-at-risk":
        return ("nothing yet. The reads still work and will keep working until "
                "the requirement is enforced against this account.")
    return ("nothing that this note explains.")


def token_health(status):
    """State the credential's health explicitly. Pure. (state, detail)."""
    if int(status or 0) == 200:
        return ("healthy",
                "GET /user answered 200, so the credential authenticates. "
                "Nothing about the token explains what follows, and this line "
                "exists to end that search early.")
    if int(status or 0) == 401:
        return ("rejected",
                "401 means the credential itself was not accepted, which is a "
                "different note. This one starts from a token that works.")
    return ("unclear", "GET /user answered %s, which is neither of the two "
                       "cases this note starts from." % status)


def repair(state, org, login):
    """The request a human has to make. Pure. Nothing here is executed."""
    if state.startswith("not-a-member"):
        return ("enable 2FA on %s and ask an owner of %s to re-invite it, or "
                "replace the machine account with a GitHub App installation, "
                "which is not a member and is unaffected by member 2FA policy. "
                "Nothing here re-invites anybody." % (login, org))
    if state == "member-at-risk":
        return ("enable 2FA on %s now, before the requirement is enforced "
                "against it. Removal is silent when it comes." % login)
    if state == "member-compliance-unreadable":
        return ("read this with a token carrying the user scope, or check the "
                "account's security settings directly, to confirm it complies.")
    if state == "member-compliant":
        return ("nothing on membership. Take the 404 to the repository-level "
                "causes instead.")
    return ("answer the membership question first: send the members call with "
            "redirects disabled and read the status rather than the body.")


def get(session, path, allow_redirects=True):
    """One GET. Redirect following is a parameter because one call needs it off."""
    return session.get(API + path, timeout=30, allow_redirects=allow_redirects)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("org", help="the organization whose repositories 404")
    parser.add_argument("--login",
                        help="ask about this account instead of the token's own")
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_TOKEN (the token the failing integration holds)")
        return 2

    log.info("read cost: %d request(s) against the core hourly quota", read_cost())

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": UA,
    })

    me = get(session, "/user")
    health, health_detail = token_health(me.status_code)
    payload = me.json() if me.status_code == 200 else {}
    login = args.login or payload.get("login") or "unknown"
    log.info("token: %s — %s", health, health_detail)
    if health != "healthy":
        return 2

    members = get(session, "/orgs/%s/members/%s" % (args.org, login),
                  allow_redirects=False)
    state, detail = membership_state(members.status_code)
    log.info("membership: GET /orgs/%s/members/%s -> HTTP %s (redirects disabled)",
             args.org, login, members.status_code)
    log.info("%s: %s", state, detail)
    asked, asked_detail = question_answered(False)
    log.info("question answered: %s. %s", asked, asked_detail)

    org_response = get(session, "/orgs/" + args.org)
    org_payload = org_response.json() if org_response.status_code == 200 else {}
    requirement = requirement_state(org_payload)
    log.info("motive: two_factor_requirement_enabled=%s",
             "unreadable" if requirement is None else requirement)

    orgs_response = get(session, "/user/orgs?per_page=100")
    orgs = orgs_response.json() if orgs_response.status_code == 200 else []
    listed = listed_in_orgs(orgs, args.org)
    log.info("corroboration: the organization is %s in GET /user/orgs, which "
             "without read:org only lists publicly-visible membership",
             "listed" if listed else "absent")

    own = own_two_factor(payload) if not args.login else None
    finding, finding_detail = combine(state, requirement, own)
    log.info("state: %s — %s", finding, finding_detail)
    log.info("symptom: %s", symptom(finding))
    log.info("repair: %s", repair(finding, args.org, login))

    print(json.dumps({
        "organization": args.org,
        "login": login,
        "token_health": health,
        "membership_status": members.status_code,
        "membership_state": state,
        "question_answered": asked,
        "two_factor_requirement_enabled": requirement,
        "account_two_factor": own,
        "listed_in_user_orgs": listed,
        "state": finding,
        "detail": finding_detail,
        "symptom": symptom(finding),
        "repair": repair(finding, args.org, login),
    }, indent=2, default=str))
    return 1 if finding.startswith("not-a-member") or finding == "member-at-risk" else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-org-membership-lost.mjs",
"js": '''/**
 * Say whether an account was removed from an organization by a 2FA rule.
 *
 * Read only. Four GETs. Re-inviting a removed member is a write and an
 * organization owner's decision, so this script establishes the removal from
 * readable state and prints the request instead of making it.
 *
 * Enabling required two-factor authentication removes non-compliant members
 * rather than refusing them. The token keeps working, the account stops being
 * a member, and every private repository in the organization answers 404.
 *
 * Environment:
 *   GITHUB_TOKEN    the token the failing integration holds
 *   GITHUB_ORG      the organization whose repositories 404
 *   GITHUB_LOGIN    optional, ask about this account instead of the token's own
 */
const API = 'https://api.github.com';
const UA = 'github-org-membership-lost/1.0';

/** The documented answers of GET /orgs/{org}/members/{username}. */
export const MEMBERSHIP_STATUS = {
  204: 'member',
  302: 'requester-not-a-member',
  404: 'not-a-member',
  403: 'membership-unreadable',
};

/** Requests this run will spend against the core quota. Pure. */
export function readCost() {
  return 4;
}

/** What one membership status means. Pure. [state, detail]. */
export function membershipState(status) {
  const code = Number(status) || 0;
  const state = MEMBERSHIP_STATUS[code] || 'unclear';
  if (state === 'member') {
    return [state, '204 means the account is a member of this organization.'];
  }
  if (state === 'requester-not-a-member') {
    return [state, 'the 302 says the account asking is not a member of the '
      + 'organization. Asking about yourself, that is the removal.'];
  }
  if (state === 'not-a-member') {
    return [state, '404 here means the requester is a member and the named '
      + 'account is not.'];
  }
  if (state === 'membership-unreadable') {
    return [state, '403 on the membership read itself. The credential reached '
      + 'GitHub and was refused; sort that refusal first.'];
  }
  return ['unclear', `HTTP ${status} is not one of the documented answers for `
    + 'this endpoint.'];
}

/** Which question the status code is about. Pure. [state, detail]. */
export function questionAnswered(followedRedirect) {
  if (followedRedirect) {
    return ['public-membership-instead', 'the client followed the redirect, so '
      + 'this answer came from the public members endpoint and is about whether '
      + 'membership is publicly listed. Send the call again with redirects off.'];
  }
  return ['membership', 'redirects were disabled, so the status describes '
    + 'membership rather than public membership.'];
}

/** Whether this account has 2FA on. Pure. true, false or null for unreadable. */
export function ownTwoFactor(userPayload) {
  if (!userPayload || typeof userPayload !== 'object') return null;
  if (!Object.prototype.hasOwnProperty.call(userPayload, 'two_factor_authentication')) {
    return null;
  }
  const value = userPayload.two_factor_authentication;
  return value === null || value === undefined ? null : Boolean(value);
}

/** Whether the org requires 2FA. Pure. true, false or null for unreadable. */
export function requirementState(orgPayload) {
  if (!orgPayload || typeof orgPayload !== 'object') return null;
  if (!Object.prototype.hasOwnProperty.call(orgPayload, 'two_factor_requirement_enabled')) {
    return null;
  }
  const value = orgPayload.two_factor_requirement_enabled;
  return value === null || value === undefined ? null : Boolean(value);
}

/** Is the organization in GET /user/orgs. Pure. Corroboration, never a finding. */
export function listedInOrgs(orgs, org) {
  const wanted = String(org ?? '').trim().toLowerCase();
  for (const entry of orgs || []) {
    const login = entry && typeof entry === 'object' ? entry.login : entry;
    if (String(login ?? '').trim().toLowerCase() === wanted) return true;
  }
  return false;
}

/** Turn three readings into one finding. Pure. [state, detail]. */
export function combine(membership, requirement, ownTwoFa) {
  const gone = ['requester-not-a-member', 'not-a-member'].includes(membership);
  if (gone && requirement === true) {
    return ['not-a-member-2fa-required', 'the account is not a member and the '
      + 'organization requires two-factor authentication. That is the cause and '
      + 'its motive. Removal and never having joined are indistinguishable '
      + 'through the API, so this is a finding to act on rather than a proof.'];
  }
  if (gone && (requirement === null || requirement === undefined)) {
    return ['not-a-member-motive-unreadable', 'the account is not a member and '
      + 'the 2FA requirement could not be read. Reading it needs organization '
      + 'access, and losing that access is what this finding is.'];
  }
  if (gone) {
    return ['not-a-member-no-requirement', 'the account is not a member and the '
      + 'organization does not require 2FA, so something else removed it. An '
      + 'owner can read the audit log; a read-only token cannot.'];
  }
  if (membership === 'member' && requirement === true && ownTwoFa === false) {
    return ['member-at-risk', 'still a member, the organization requires 2FA, '
      + 'and this account reports two-factor authentication off. That is a '
      + 'removal that has not happened yet.'];
  }
  if (membership === 'member' && requirement === true
      && (ownTwoFa === null || ownTwoFa === undefined)) {
    return ['member-compliance-unreadable', 'still a member of an organization '
      + 'that requires 2FA, and this token cannot read whether the account '
      + 'complies. The user scope is what exposes that field.'];
  }
  if (membership === 'member' && requirement === true) {
    return ['member-compliant', 'a member, the requirement is on, and this '
      + 'account has 2FA. Nothing here explains a 404.'];
  }
  if (membership === 'member') {
    return ['member-no-requirement', 'a member of an organization with no 2FA '
      + 'requirement. This note is not your problem; sort the 404 another way.'];
  }
  return ['membership-unreadable', 'the membership question was not answered, '
    + 'so nothing can be concluded about a removal.'];
}

/** What the integration is seeing, given the finding. Pure. */
export function symptom(state) {
  if (String(state).startsWith('not-a-member')) {
    return 'every private repository in the organization answers 404, not 403, '
      + 'because a non-member cannot see them at all. Public repositories keep '
      + 'answering, which is what makes the token look healthy.';
  }
  if (state === 'member-at-risk') {
    return 'nothing yet. The reads still work and will keep working until the '
      + 'requirement is enforced against this account.';
  }
  return 'nothing that this note explains.';
}

/** State the credential's health explicitly. Pure. [state, detail]. */
export function tokenHealth(status) {
  const code = Number(status) || 0;
  if (code === 200) {
    return ['healthy', 'GET /user answered 200, so the credential '
      + 'authenticates. Nothing about the token explains what follows, and this '
      + 'line exists to end that search early.'];
  }
  if (code === 401) {
    return ['rejected', '401 means the credential itself was not accepted, '
      + 'which is a different note. This one starts from a token that works.'];
  }
  return ['unclear', `GET /user answered ${status}, which is neither of the two `
    + 'cases this note starts from.'];
}

/** The request a human has to make. Pure. Nothing here is executed. */
export function repair(state, org, login) {
  if (String(state).startsWith('not-a-member')) {
    return `enable 2FA on ${login} and ask an owner of ${org} to re-invite it, `
      + 'or replace the machine account with a GitHub App installation, which is '
      + 'not a member and is unaffected by member 2FA policy. Nothing here '
      + 're-invites anybody.';
  }
  if (state === 'member-at-risk') {
    return `enable 2FA on ${login} now, before the requirement is enforced `
      + 'against it. Removal is silent when it comes.';
  }
  if (state === 'member-compliance-unreadable') {
    return 'read this with a token carrying the user scope, or check the '
      + "account's security settings directly, to confirm it complies.";
  }
  if (state === 'member-compliant') {
    return 'nothing on membership. Take the 404 to the repository-level causes '
      + 'instead.';
  }
  return 'answer the membership question first: send the members call with '
    + 'redirects disabled and read the status rather than the body.';
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
    console.error('set GITHUB_TOKEN (the failing token) and GITHUB_ORG');
    process.exitCode = 2;
    return;
  }
  console.log(`read cost: ${readCost()} request(s) against the core hourly quota`);

  const me = await fetch(`${API}/user`, { headers: headers(token) });
  const [health, healthDetail] = tokenHealth(me.status);
  console.log(`token: ${health} — ${healthDetail}`);
  if (health !== 'healthy') { process.exitCode = 2; return; }
  const payload = await me.json();
  const login = process.env.GITHUB_LOGIN || payload.login || 'unknown';

  // redirect: manual, because the 302 is the finding and following it answers
  // a question about public membership instead.
  const members = await fetch(`${API}/orgs/${org}/members/${login}`, {
    headers: headers(token), redirect: 'manual',
  });
  const [state, detail] = membershipState(members.status);
  console.log(`membership: GET /orgs/${org}/members/${login} -> HTTP ${members.status} `
    + '(redirects disabled)');
  console.log(`${state}: ${detail}`);
  const [asked, askedDetail] = questionAnswered(false);
  console.log(`question answered: ${asked}. ${askedDetail}`);

  const orgResponse = await fetch(`${API}/orgs/${org}`, { headers: headers(token) });
  const orgPayload = orgResponse.status === 200 ? await orgResponse.json() : {};
  const requirement = requirementState(orgPayload);
  console.log(`motive: two_factor_requirement_enabled=`
    + `${requirement === null ? 'unreadable' : requirement}`);

  const orgsResponse = await fetch(`${API}/user/orgs?per_page=100`, {
    headers: headers(token),
  });
  const orgs = orgsResponse.status === 200 ? await orgsResponse.json() : [];
  const listed = listedInOrgs(orgs, org);
  console.log(`corroboration: the organization is ${listed ? 'listed' : 'absent'} `
    + 'in GET /user/orgs, which without read:org only lists publicly-visible '
    + 'membership');

  const own = process.env.GITHUB_LOGIN ? null : ownTwoFactor(payload);
  const [finding, findingDetail] = combine(state, requirement, own);
  console.log(`state: ${finding} — ${findingDetail}`);
  console.log(`symptom: ${symptom(finding)}`);
  console.log(`repair: ${repair(finding, org, login)}`);

  console.log(JSON.stringify({
    organization: org,
    login,
    token_health: health,
    membership_status: members.status,
    membership_state: state,
    question_answered: asked,
    two_factor_requirement_enabled: requirement,
    account_two_factor: own,
    listed_in_user_orgs: listed,
    state: finding,
    detail: findingDetail,
    symptom: symptom(finding),
    repair: repair(finding, org, login),
  }, null, 2));
  process.exitCode = (String(finding).startsWith('not-a-member')
    || finding === 'member-at-risk') ? 1 : 0;
}

// Guarded so importing this file from the test runner does not start a run.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The status table comes first, because the 302 is the reading this note exists to rescue and it is the one every default HTTP client throws away. Then the three-valued fields, twice, in both directions: an absent <code>two_factor_requirement_enabled</code> has to be unreadable rather than false, or the script would report a removal as unexplained at exactly the moment the removal is what made the field unreadable; and an absent <code>two_factor_authentication</code> has to be unreadable rather than false, or it would invent a compliance failure. The combination table is asserted state by state, including the pre-emptive one — a member with 2FA off inside an organization that requires it — and the repair is asserted to name a GitHub App, because that is the repair that makes the same change impossible next time.",
"test_py_file": "test_github_org_membership_lost.py",
"test_py": '''from github_org_membership_lost import (
    combine, listed_in_orgs, membership_state, own_two_factor,
    question_answered, read_cost, repair, requirement_state, symptom,
    token_health,
)


def test_the_redirect_is_the_finding_and_not_an_error():
    state, detail = membership_state(302)
    assert state == "requester-not-a-member"
    assert "that is the removal" in detail
    assert membership_state(204)[0] == "member"
    assert membership_state(404)[0] == "not-a-member"
    assert membership_state(418)[0] == "unclear"


def test_following_the_redirect_answers_a_different_question():
    state, detail = question_answered(True)
    assert state == "public-membership-instead"
    assert "publicly listed" in detail
    assert question_answered(False)[0] == "membership"


def test_an_absent_requirement_field_is_unreadable_not_false():
    # The field is returned to callers with org access, and being removed is
    # what takes that away. Reading absence as False would report the removal
    # as unexplained precisely when the removal is the explanation.
    assert requirement_state({}) is None
    assert requirement_state({"two_factor_requirement_enabled": None}) is None
    assert requirement_state({"two_factor_requirement_enabled": True}) is True
    assert requirement_state({"two_factor_requirement_enabled": False}) is False


def test_an_absent_two_factor_field_does_not_invent_a_violation():
    assert own_two_factor({"login": "octobot"}) is None
    assert own_two_factor({"two_factor_authentication": False}) is False
    assert own_two_factor({"two_factor_authentication": True}) is True
    assert own_two_factor(None) is None


def test_the_removal_and_its_motive_are_reported_together():
    state, detail = combine("requester-not-a-member", True, None)
    assert state == "not-a-member-2fa-required"
    assert "cause and its motive" in detail
    assert "indistinguishable" in detail


def test_an_unreadable_motive_is_still_a_finding():
    state, detail = combine("requester-not-a-member", None, None)
    assert state == "not-a-member-motive-unreadable"
    assert "losing that access is what this finding is" in detail


def test_a_removal_with_no_requirement_is_sent_to_the_audit_log():
    state, detail = combine("not-a-member", False, None)
    assert state == "not-a-member-no-requirement"
    assert "audit log" in detail


def test_a_member_with_2fa_off_is_flagged_before_anything_breaks():
    state, detail = combine("member", True, False)
    assert state == "member-at-risk"
    assert "has not happened yet" in detail


def test_a_compliant_member_is_sent_somewhere_else():
    assert combine("member", True, True)[0] == "member-compliant"
    assert combine("member", True, None)[0] == "member-compliance-unreadable"
    assert combine("member", False, True)[0] == "member-no-requirement"
    assert combine("membership-unreadable", True, True)[0] == "membership-unreadable"


def test_the_symptom_is_404_and_not_403():
    text = symptom("not-a-member-2fa-required")
    assert "404, not 403" in text
    assert "Public repositories keep answering" in text
    assert "nothing yet" in symptom("member-at-risk")


def test_a_healthy_token_is_stated_so_the_search_can_move_on():
    state, detail = token_health(200)
    assert state == "healthy"
    assert "end that search early" in detail
    assert token_health(401)[0] == "rejected"


def test_user_orgs_is_corroboration_and_matches_case_insensitively():
    orgs = [{"login": "ACME"}, {"login": "other"}]
    assert listed_in_orgs(orgs, "acme") is True
    assert listed_in_orgs(orgs, "missing") is False
    assert listed_in_orgs([], "acme") is False


def test_the_repair_offers_the_change_that_cannot_happen_again():
    fix = repair("not-a-member-2fa-required", "acme", "octobot")
    assert "octobot" in fix and "acme" in fix
    assert "GitHub App installation" in fix
    assert "re-invites anybody" in fix
    assert "before the requirement is enforced" in repair(
        "member-at-risk", "acme", "octobot")


def test_the_run_costs_four_reads():
    assert read_cost() == 4
''',
"test_js_file": "github-org-membership-lost.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  combine, listedInOrgs, membershipState, ownTwoFactor, questionAnswered,
  readCost, repair, requirementState, symptom, tokenHealth,
} from './github-org-membership-lost.mjs';

test('the redirect is the finding and not an error', () => {
  const [state, detail] = membershipState(302);
  assert.equal(state, 'requester-not-a-member');
  assert.match(detail, /that is the removal/);
  assert.equal(membershipState(204)[0], 'member');
  assert.equal(membershipState(404)[0], 'not-a-member');
  assert.equal(membershipState(418)[0], 'unclear');
});

test('following the redirect answers a different question', () => {
  const [state, detail] = questionAnswered(true);
  assert.equal(state, 'public-membership-instead');
  assert.match(detail, /publicly listed/);
  assert.equal(questionAnswered(false)[0], 'membership');
});

test('an absent requirement field is unreadable not false', () => {
  assert.equal(requirementState({}), null);
  assert.equal(requirementState({ two_factor_requirement_enabled: null }), null);
  assert.equal(requirementState({ two_factor_requirement_enabled: true }), true);
  assert.equal(requirementState({ two_factor_requirement_enabled: false }), false);
});

test('an absent two factor field does not invent a violation', () => {
  assert.equal(ownTwoFactor({ login: 'octobot' }), null);
  assert.equal(ownTwoFactor({ two_factor_authentication: false }), false);
  assert.equal(ownTwoFactor({ two_factor_authentication: true }), true);
  assert.equal(ownTwoFactor(null), null);
});

test('the removal and its motive are reported together', () => {
  const [state, detail] = combine('requester-not-a-member', true, null);
  assert.equal(state, 'not-a-member-2fa-required');
  assert.match(detail, /cause and its motive/);
  assert.match(detail, /indistinguishable/);
});

test('an unreadable motive is still a finding', () => {
  const [state, detail] = combine('requester-not-a-member', null, null);
  assert.equal(state, 'not-a-member-motive-unreadable');
  assert.match(detail, /losing that access is what this finding is/);
});

test('a removal with no requirement is sent to the audit log', () => {
  const [state, detail] = combine('not-a-member', false, null);
  assert.equal(state, 'not-a-member-no-requirement');
  assert.match(detail, /audit log/);
});

test('a member with 2fa off is flagged before anything breaks', () => {
  const [state, detail] = combine('member', true, false);
  assert.equal(state, 'member-at-risk');
  assert.match(detail, /has not happened yet/);
});

test('a compliant member is sent somewhere else', () => {
  assert.equal(combine('member', true, true)[0], 'member-compliant');
  assert.equal(combine('member', true, null)[0], 'member-compliance-unreadable');
  assert.equal(combine('member', false, true)[0], 'member-no-requirement');
  assert.equal(combine('membership-unreadable', true, true)[0], 'membership-unreadable');
});

test('the symptom is 404 and not 403', () => {
  const text = symptom('not-a-member-2fa-required');
  assert.match(text, /404, not 403/);
  assert.match(text, /Public repositories keep answering/);
  assert.match(symptom('member-at-risk'), /nothing yet/);
});

test('a healthy token is stated so the search can move on', () => {
  const [state, detail] = tokenHealth(200);
  assert.equal(state, 'healthy');
  assert.match(detail, /end that search early/);
  assert.equal(tokenHealth(401)[0], 'rejected');
});

test('user orgs is corroboration and matches case insensitively', () => {
  const orgs = [{ login: 'ACME' }, { login: 'other' }];
  assert.equal(listedInOrgs(orgs, 'acme'), true);
  assert.equal(listedInOrgs(orgs, 'missing'), false);
  assert.equal(listedInOrgs([], 'acme'), false);
});

test('the repair offers the change that cannot happen again', () => {
  const fix = repair('not-a-member-2fa-required', 'acme', 'octobot');
  assert.match(fix, /octobot/);
  assert.match(fix, /GitHub App installation/);
  assert.match(fix, /re-invites anybody/);
  assert.match(repair('member-at-risk', 'acme', 'octobot'),
    /before the requirement is enforced/);
});

test('the run costs four reads', () => {
  assert.equal(readCost(), 4);
});
''',
"faq": [
 ("Why would a policy remove accounts rather than just refuse them?",
  "Because a two-factor requirement is a statement about who is in the organization, not about what a request may do. GitHub applies it to the membership graph: when it is enabled, members and outside collaborators without 2FA are removed. That is documented behaviour and it is the reason the symptom is so strange from the inside — there is no refusal to read, no rule named in a body, no header. The account's relationship to the organization simply ended, and everything downstream of that is the ordinary behaviour of a caller with no access."),
 ("Everyone else's tokens still work. Does that not rule out an org-wide change?",
  "It rules out an org-wide <em>outage</em>, which is not the same thing. The requirement removes only the accounts that do not comply, so colleagues who have had 2FA on for years see nothing at all. That asymmetry is the signature: humans unaffected, machine account gone. It is also why the notification did not reach anybody who would act on it, since the announcement goes to people, and the account that broke does not read email."),
 ("Why does the members endpoint answer with a redirect at all?",
  "Because the question changes depending on who is asking. To a member, <code>GET /orgs/{org}/members/{username}</code> answers about membership: 204 yes, 404 no. To a non-member it redirects to the public-members endpoint, which is the version of the question a stranger is allowed to ask. Once you have been removed you are the stranger, so the redirect is the answer. Send the call with redirect-following disabled, or your HTTP library will quietly go and answer the stranger's question and hand you back a status about public listing."),
 ("The organization object does not include two_factor_requirement_enabled. Is the requirement off?",
  "No, and the script deliberately does not say it is. That field is returned to callers with organization access, and losing organization access is exactly the event being investigated, so the field is often missing <em>because</em> of the thing you are trying to confirm. Absence is reported as unreadable. If you need the motive on the record, ask an owner: they can also read the audit log entry for the removal, which a read-only token cannot see at all."),
 ("What stops this happening again after we re-invite the account?",
  "Enabling 2FA on the machine account stops this particular rule from removing it again, but the underlying fragility remains: a personal account acting as a robot is subject to every policy that governs people, and there are more of those every year. The durable repair is a GitHub App installation. An installation is not a member of the organization, so member policy does not apply to it, its permissions are declared rather than inherited, and its tokens are short-lived by design."),
],
"related": [
 ("/github/404-masking-403/", "Why the symptom arrives as 404 rather than 403"),
 ("/github/collaborator-permission-insufficient/", "When the account is present but the role is too low"),
 ("/github/installation-suspended/", "The App equivalent: the record survives and the capability does not"),
],
"citations": [CITE_ORG_MEMBERS, CITE_2FA, CITE_ORGS, CITE_USERS],
},
{
"slug": "org-base-permission-changed",
"title": "The org's base permission dropped and repos vanished",
"description": "default_repository_permission is one org-wide field. Moving it from read to none removes implicit access for every member at once, machine accounts included.",
"h1": "The org's base permission dropped and repos vanished",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github default_repository_permission none",
             "github org base permission changed api",
             "github integration sees fewer repositories",
             "github org base permissions read to none",
             "github user repos affiliation organization_member"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The inventory job used to report on four hundred repositories. This morning it reported on nine, and reported them cheerfully: no errors, no refusals, no retries, a clean run in a tenth of the usual time. Nothing was revoked from the account — it is still a member of the organization, its token is unchanged, and the nine repositories it can see are ones somebody added it to explicitly, years ago. What changed is one field on the organization. Somebody moved the base permission from read to none, which is a good and normal thing to do, and every member's implicit access to every repository they were never explicitly added to ended in the same instant.",
"short_answer": """<p>An organization's <code>default_repository_permission</code> is the role every member gets on repositories they have <em>not</em> been added to individually or through a team. Tightening it from <code>read</code> to <code>none</code> is a standard hardening step and it takes effect everywhere at once.</p>
<p>Read the field and then measure the damage. <code>GET /orgs/{org}</code> returns <code>default_repository_permission</code> alongside <code>public_repos</code> and <code>total_private_repos</code>. Then count what your account can actually see: request <code>GET /user/repos?affiliation=organization_member&amp;per_page=1</code> and read the <code>page</code> number out of the <code>rel="last"</code> link — with one item per page, the last page number <em>is</em> the count, and it costs one request rather than four hundred. The gap between the two numbers is the finding.</p>""",
"problem": """<p>The expensive part is that nothing fails. A permission problem that produces a 403 gets fixed, because a 403 is loud, has a stack trace attached to it and lands in an alert. This produces shorter lists. The job succeeds, the report is well formed, the dashboard is green, and the number on it is wrong in a direction nobody looks at. Coverage loss is the failure mode that survives longest in production, because every part of the system agrees that it went fine.</p>
<p>When somebody does notice, the search starts in the wrong place, because the natural question is "which repositories are missing" and the natural next step is to check one of them. That check is about a repository: does it exist, is it private, was it archived, was it renamed. Every one of those answers comes back normal, because nothing is wrong with the repositories. The subject of this failure is the organization, and it is one field wide.</p>
<p>The other trap is that it does not look org-wide from the inside, because it is not uniform. Repositories the account was explicitly added to keep working perfectly. So the surviving nine are a distraction: they look like proof that access is basically fine and the problem must be with the other four hundred, when they are actually the only ones whose access never depended on the default in the first place.</p>""",
"why": """<p><strong>Base permission is a default, and defaults are invisible until they move.</strong> Every member of an organization has a role on every repository, and for most people on most repositories that role was never granted to them by name — it came from <code>default_repository_permission</code>. That is what makes a change to it feel like something else entirely: there is no grant to look for and no revocation event, because nothing was ever granted or revoked at the repository level. The floor moved.</p>
<p><strong>This is an organization-wide object, which is what separates it from a role on one repository.</strong> The section already publishes the case where <a href="/github/collaborator-permission-insufficient/">an account's role on a single repository is too low for the write it is attempting</a>. That note reads a <code>permissions</code> object per repository and answers about one of them. This one reads a single field that re-grades every repository in the organization simultaneously, and its symptom is not a refused write at all — it is a list that got shorter while every call in it succeeded.</p>
<p><strong>Counting with <code>rel="last"</code> makes the measurement affordable.</strong> Asking for one item per page and reading the last page number out of the <code>Link</code> header gives you the size of a collection in a single request. That is the difference between a check you run on a schedule and one you never run at all. It has one failure mode worth knowing: when the result fits on a single page there is no <code>rel="last"</code>, which is <a href="/github/rel-last-absent/">its own note</a>, and the script reports the count as coming from a single page rather than pretending the collection is empty.</p>
<p><strong>The two numbers you are comparing are not the same kind of number, and the script says so.</strong> <code>public_repos</code> plus <code>total_private_repos</code> on the organization is what the organization contains. The affiliation count is what your account can reach through membership. A gap is expected the moment base permission is <code>none</code>; the question is whether the gap is the one you intended. A drop from four hundred to nine with base permission at <code>none</code> and nine explicit grants is a correctly-configured organization and a badly-configured integration.</p>
<p><strong>The repair is not to put the default back.</strong> Base permissions are a security control, and a member of an organization that sets it to <code>none</code> should be given access to what it needs by name. Reversing the hardening to fix one integration re-grants implicit access to everybody, which is a much larger change than the one that broke you. The script prints the narrow repair: add the account, or the team it belongs to, to the repositories the job is supposed to cover.</p>""",
"steps": [
 {"h": "Read the field that moved",
  "body": """<p>One call to <code>GET /orgs/{org}</code> gives <code>default_repository_permission</code>. The script prints what that value implies for a member with no explicit grants: at <code>none</code>, private repositories are invisible; at <code>read</code>, all of them are readable. Reading the field needs organization access, so an unreadable value is reported as unreadable rather than assumed.</p>"""},
 {"h": "Count what the account can actually see, in one request",
  "body": """<p><code>GET /user/repos?affiliation=organization_member&amp;per_page=1</code> with the <code>rel="last"</code> page number gives the count without paging through it. The script reports where the number came from — the <code>Link</code> header, or a single page with no <code>rel="last"</code> — because those two are the same number for different reasons and only one of them is a count.</p>"""},
 {"h": "Count what the organization holds",
  "body": """<p><code>public_repos</code> plus <code>total_private_repos</code> from the same organization read is the size of the organization. The script compares the two numbers and grades the coverage: full, partial, shrunken or collapsed. A collapsed coverage beside a base permission of <code>none</code> is this note; a collapsed coverage beside a base permission of <code>read</code> is something else and the script says so rather than blaming the field it just read.</p>"""},
 {"h": "Alert on drift rather than rediscovering it",
  "body": """<p>Pass <code>--expect read</code> with the base permission your integration was designed against. The script compares and reports tightened, loosened or unchanged. That turns this from a thing you work out during an incident into a line in a scheduled check, which is the only form in which a coverage problem gets caught early.</p>"""},
 {"h": "Take the repair to the account, not to the default",
  "body": """<p>The printed repair adds the account or its team to the repositories it is supposed to cover. It explicitly does not suggest raising the base permission back, because that re-grants implicit access to every member of the organization to fix one integration. The script changes nothing: it reads three things, prints a comparison and exits.</p>"""},
],
"verify": """<p>Once the account or its team is added to the repositories it should cover, the affiliation count rises to meet them and the coverage stops being collapsed.</p>
<pre><code class="language-bash">GITHUB_TOKEN=$READ_ONLY_TOKEN python3 github_org_base_permission.py acme --expect read
# read cost: 3 request(s) against the core hourly quota
# base permission: none — members get no role on repositories they were not
#   added to individually or through a team. Every private repository in the
#   organization is invisible to a member with no explicit grants.
# drift: base-tightened — configured for 'read', the organization now says
#   'none'. That is one field and it re-graded every repository at once.
# visible through membership: 9 (from rel="last" with per_page=1)
# organization holds: 412 repositories (public 12 + private 400)
# coverage: collapsed — 9 of 412
# state: base-none-implicit-access-gone
# repair: add this account, or a team it belongs to, to the repositories the
#   job is meant to cover. Do not raise the base permission back: that
#   re-grants implicit access to every member to fix one integration.</code></pre>""",
"code_intro": "Three reads, and the only clever one is a counting trick: ask for a single item per page and the last page number is the size of the collection, so a four-hundred-repository organization is measured in one request rather than four hundred. Everything else is pure — the <code>Link</code> header parse, which is written without a regular expression because a header with a comma inside a URL is exactly the input a hasty pattern gets wrong; the grading of coverage; the drift comparison against the base permission you configured for; and a repair that deliberately refuses to recommend the easy fix.",
"py_file": "github_org_base_permission.py",
"py": '''"""Say whether an organization's base permission is why the repository list shrank.

Read only. Three GETs. Granting an account access to a repository is a write
and a decision somebody with admin has to make, so this script measures the
loss and prints the narrow repair.

The point of the note: default_repository_permission is the role every member
holds on repositories they were never explicitly added to. Moving it from read
to none is ordinary hardening and it removes implicit access everywhere at
once, so a read-only integration keeps succeeding and covers a tenth of what
it did yesterday.

What this can and cannot see: the field is readable with organization access,
and the account's reachable repositories are countable in one request. What is
not visible is which repositories were reachable yesterday. This measures the
gap now and compares it against the base permission you say you configured
for; it cannot replay history.

Environment:

    GITHUB_TOKEN    a read-only token for the account whose coverage shrank
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_org_base_permission")

API = "https://api.github.com"
UA = "github-org-base-permission/1.0"

# Weakest first. The documented values of default_repository_permission.
BASE_PERMISSIONS = ("none", "read", "write", "admin")

# What a member with no explicit grants gets, per base permission.
IMPLIES = {
    "none": "members get no role on repositories they were not added to "
            "individually or through a team. Every private repository in the "
            "organization is invisible to a member with no explicit grants.",
    "read": "every member can read every repository in the organization "
            "without being added to it.",
    "write": "every member can push to every repository in the organization "
             "without being added to it.",
    "admin": "every member administers every repository in the organization. "
             "This is rare and worth questioning on its own.",
}


def read_cost():
    """Requests this run will spend against the core quota. Pure."""
    return 3


def base_rank(value):
    """Position in the hierarchy, or -1 for something unrecognised. Pure."""
    try:
        return BASE_PERMISSIONS.index(str(value or "").strip().lower())
    except ValueError:
        return -1


def base_state(org_payload):
    """The organization's base permission. Pure. (value, detail).

    An absent field is "unreadable" rather than a default. The field is
    returned to callers with organization access, and a token without it would
    otherwise be reported as an organization that grants nothing.
    """
    if not isinstance(org_payload, dict):
        return (None, "no organization payload was read.")
    if "default_repository_permission" not in org_payload:
        return (None, "default_repository_permission was not returned. Reading "
                      "it needs organization access, so this is unreadable "
                      "rather than absent.")
    value = str(org_payload.get("default_repository_permission") or "").strip().lower()
    if base_rank(value) < 0:
        return (value or None, "the value %r is not one of the four documented "
                               "base permissions." % value)
    return (value, IMPLIES[value])


def link_parts(link_header):
    """Split a Link header into its entries. Pure. No regular expression.

    Split on the commas that separate entries and not on the ones inside a
    URL, because a URL in a Link header can carry commas of its own -- a
    search query, a list of fields -- and splitting the whole header throws
    away the half that holds the page number.
    """
    parts, current, depth = [], "", 0
    for ch in str(link_header or ""):
        if ch == "<":
            depth += 1
        elif ch == ">":
            depth = max(0, depth - 1)
        if ch == "," and depth == 0:
            parts.append(current)
            current = ""
        else:
            current += ch
    if current.strip():
        parts.append(current)
    return parts


def last_page_from_link(link_header):
    """The page number of rel="last", or None. Pure. No regular expression."""
    if not link_header:
        return None
    for part in link_parts(link_header):
        if 'rel="last"' not in part and "rel=last" not in part:
            continue
        start = part.find("<")
        end = part.find(">", start + 1)
        if start < 0 or end < 0:
            continue
        url = part[start + 1:end]
        query = url.partition("?")[2]
        for field in query.split("&"):
            name, _, value = field.partition("=")
            if name == "page" and value.isdigit():
                return int(value)
    return None


def count_from_link(link_header, returned):
    """How many items the collection holds, at per_page=1. Pure. (count, how).

    With one item per page the last page number is the count. When everything
    fits on one page there is no rel="last" at all, and that case is reported
    as what it is rather than as a count of zero.
    """
    last = last_page_from_link(link_header)
    if last is not None:
        return (last, 'from rel="last" with per_page=1')
    if not returned:
        return (0, "the first page came back empty and carried no rel=\\"last\\"")
    return (int(returned), 'a single page with no rel="last", so this is what '
                           'came back rather than a measured count')


def org_total(org_payload):
    """How many repositories the organization holds. Pure. (count, detail)."""
    if not isinstance(org_payload, dict):
        return (None, "no organization payload was read.")
    public = org_payload.get("public_repos")
    private = org_payload.get("total_private_repos")
    if public is None and private is None:
        return (None, "neither repository count was returned, which needs "
                      "organization access.")
    total = int(public or 0) + int(private or 0)
    return (total, "public %s + private %s"
            % ("unreadable" if public is None else public,
               "unreadable" if private is None else private))


def coverage_state(visible, total):
    """Grade what the account can see against what the org holds. Pure."""
    if total is None or visible is None:
        return "unknown"
    if total <= 0:
        return "nothing-to-cover"
    if visible >= total:
        return "full"
    if visible == 0 or visible * 20 < total:
        return "collapsed"
    if visible * 2 < total:
        return "shrunken"
    return "partial"


def drift(expected, actual):
    """Compare the configured base permission against the live one. Pure."""
    if not expected or actual is None:
        return ("drift-unknown",
                "no expected base permission was supplied, or the live one "
                "could not be read, so there is nothing to compare.")
    want, have = base_rank(expected), base_rank(actual)
    if want < 0 or have < 0:
        return ("drift-unknown",
                "one of the two values is not a documented base permission.")
    if want == have:
        return ("base-unchanged",
                "the organization still reports the base permission this "
                "integration was configured against.")
    if have < want:
        return ("base-tightened",
                "configured for %r, the organization now says %r. That is one "
                "field and it re-graded every repository at once."
                % (expected, actual))
    return ("base-loosened",
            "configured for %r, the organization now says %r, which grants "
            "more implicit access than you expected rather than less."
            % (expected, actual))


def verdict(base, coverage):
    """The finding, in one state. Pure. (state, detail)."""
    if base is None:
        return ("base-unreadable",
                "the base permission could not be read, so the coverage number "
                "stands on its own. Read it with a token that has organization "
                "access before concluding anything about the default.")
    if base == "none" and coverage in ("collapsed", "shrunken"):
        return ("base-none-implicit-access-gone",
                "base permission is none and this account reaches a fraction "
                "of the organization. The repositories it still reaches are "
                "the ones it was added to explicitly; the rest were never "
                "granted, only defaulted.")
    if base == "none" and coverage in ("full", "partial"):
        return ("base-none-explicit-grants-hold",
                "base permission is none and coverage is largely intact, which "
                "means this account's access is explicit. It is not exposed to "
                "this change.")
    if base != "none" and coverage in ("collapsed", "shrunken"):
        return ("coverage-lost-elsewhere",
                "the base permission still grants implicit access and the "
                "coverage is short anyway, so the loss is not this field. "
                "Membership, SSO authorization and an App's repository "
                "selection are the other ways a list gets shorter.")
    if coverage == "nothing-to-cover":
        return ("nothing-to-cover",
                "the organization reports no repositories, so there is no "
                "coverage question to answer.")
    return ("coverage-as-expected",
            "the account reaches what the base permission implies it should. "
            "Nothing here explains a shorter list.")


def repair(state, org):
    """The narrow repair. Pure. Nothing here is executed."""
    if state == "base-none-implicit-access-gone":
        return ("add this account, or a team it belongs to, to the "
                "repositories the job is meant to cover in %s. Do not raise "
                "the base permission back: that re-grants implicit access to "
                "every member of the organization to fix one integration."
                % org)
    if state == "coverage-lost-elsewhere":
        return ("look past the base permission. Check that the account is "
                "still a member, that the token is SSO-authorized where that "
                "applies, and, for a GitHub App, that the installation covers "
                "the repositories you expect.")
    if state == "base-unreadable":
        return ("re-read the organization with a token that has organization "
                "access. Until then the coverage number is a measurement "
                "without an explanation.")
    if state == "base-none-explicit-grants-hold":
        return ("nothing. Keep it that way: explicit grants are what makes "
                "this account immune to the next change to the default.")
    return ("nothing on the base permission. The shorter list, if there is "
            "one, has another cause.")


def get(session, path):
    """One GET. Returns the response object."""
    return session.get(API + path, timeout=30)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("org", help="the organization whose repositories shrank")
    parser.add_argument("--expect",
                        help="the base permission this integration was "
                             "configured against, e.g. read")
    args = parser.parse_args()

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
        "User-Agent": UA,
    })

    org_response = get(session, "/orgs/" + args.org)
    org_payload = org_response.json() if org_response.status_code == 200 else {}
    base, base_detail = base_state(org_payload)
    log.info("base permission: %s — %s", base or "unreadable", base_detail)

    drift_state, drift_detail = drift(args.expect, base)
    log.info("drift: %s — %s", drift_state, drift_detail)

    mine = get(session, "/user/repos?affiliation=organization_member&per_page=1")
    body = mine.json() if mine.status_code == 200 else []
    visible, how = count_from_link(mine.headers.get("Link"),
                                   len(body) if isinstance(body, list) else 0)
    log.info("visible through membership: %s (%s)", visible, how)

    total, total_detail = org_total(org_payload)
    log.info("organization holds: %s repositories (%s)",
             "unreadable" if total is None else total, total_detail)

    also = get(session, "/orgs/%s/repos?per_page=1" % args.org)
    also_body = also.json() if also.status_code == 200 else []
    listed, listed_how = count_from_link(
        also.headers.get("Link"), len(also_body) if isinstance(also_body, list) else 0)
    log.info("listed by /orgs/%s/repos: %s (%s)", args.org, listed, listed_how)

    coverage = coverage_state(visible, total)
    log.info("coverage: %s — %s of %s", coverage, visible,
             "unreadable" if total is None else total)

    state, detail = verdict(base, coverage)
    log.info("state: %s — %s", state, detail)
    log.info("repair: %s", repair(state, args.org))

    print(json.dumps({
        "organization": args.org,
        "default_repository_permission": base,
        "expected_base_permission": args.expect,
        "drift_state": drift_state,
        "visible_through_membership": visible,
        "visible_source": how,
        "listed_by_org_repos": listed,
        "organization_total": total,
        "coverage": coverage,
        "state": state,
        "detail": detail,
        "repair": repair(state, args.org),
    }, indent=2, default=str))
    return 1 if state in ("base-none-implicit-access-gone",
                          "coverage-lost-elsewhere") else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-org-base-permission.mjs",
"js": '''/**
 * Say whether an organization's base permission is why the repository list shrank.
 *
 * Read only. Three GETs. Granting access to a repository is a write and
 * somebody with admin has to make it, so this script measures the loss and
 * prints the narrow repair.
 *
 * default_repository_permission is the role every member holds on
 * repositories they were never explicitly added to. Moving it from read to
 * none removes implicit access everywhere at once, so the integration keeps
 * succeeding while covering a fraction of what it did yesterday.
 *
 * Environment:
 *   GITHUB_TOKEN    a read-only token for the account whose coverage shrank
 *   GITHUB_ORG      the organization whose repositories shrank
 *   GITHUB_EXPECT   optional base permission you configured against
 */
const API = 'https://api.github.com';
const UA = 'github-org-base-permission/1.0';

/** Weakest first. The documented values of default_repository_permission. */
export const BASE_PERMISSIONS = ['none', 'read', 'write', 'admin'];

/** What a member with no explicit grants gets, per base permission. */
export const IMPLIES = {
  none: 'members get no role on repositories they were not added to '
    + 'individually or through a team. Every private repository in the '
    + 'organization is invisible to a member with no explicit grants.',
  read: 'every member can read every repository in the organization without '
    + 'being added to it.',
  write: 'every member can push to every repository in the organization '
    + 'without being added to it.',
  admin: 'every member administers every repository in the organization. This '
    + 'is rare and worth questioning on its own.',
};

/** Requests this run will spend against the core quota. Pure. */
export function readCost() {
  return 3;
}

/** Position in the hierarchy, or -1 for something unrecognised. Pure. */
export function baseRank(value) {
  return BASE_PERMISSIONS.indexOf(String(value ?? '').trim().toLowerCase());
}

/** The organization's base permission. Pure. [value, detail]. */
export function baseState(orgPayload) {
  if (!orgPayload || typeof orgPayload !== 'object') {
    return [null, 'no organization payload was read.'];
  }
  if (!Object.prototype.hasOwnProperty.call(orgPayload, 'default_repository_permission')) {
    return [null, 'default_repository_permission was not returned. Reading it '
      + 'needs organization access, so this is unreadable rather than absent.'];
  }
  const value = String(orgPayload.default_repository_permission ?? '')
    .trim().toLowerCase();
  if (baseRank(value) < 0) {
    return [value || null, `the value '${value}' is not one of the four `
      + 'documented base permissions.'];
  }
  return [value, IMPLIES[value]];
}

/** Split a Link header into its entries. Pure. No regular expression.
 *
 * Split on the commas that separate entries and not on the ones inside a URL,
 * because a URL in a Link header can carry commas of its own.
 */
export function linkParts(linkHeader) {
  const parts = [];
  let current = '';
  let depth = 0;
  for (const ch of String(linkHeader ?? '')) {
    if (ch === '<') depth += 1;
    else if (ch === '>') depth = Math.max(0, depth - 1);
    if (ch === ',' && depth === 0) { parts.push(current); current = ''; } else current += ch;
  }
  if (current.trim()) parts.push(current);
  return parts;
}

/** The page number of rel="last", or null. Pure. No regular expression. */
export function lastPageFromLink(linkHeader) {
  if (!linkHeader) return null;
  for (const part of linkParts(linkHeader)) {
    if (!part.includes('rel="last"') && !part.includes('rel=last')) continue;
    const start = part.indexOf('<');
    const end = part.indexOf('>', start + 1);
    if (start < 0 || end < 0) continue;
    const url = part.slice(start + 1, end);
    const query = url.includes('?') ? url.slice(url.indexOf('?') + 1) : '';
    for (const field of query.split('&')) {
      const cut = field.indexOf('=');
      const name = cut < 0 ? field : field.slice(0, cut);
      const value = cut < 0 ? '' : field.slice(cut + 1);
      if (name === 'page' && value.length && [...value].every((c) => c >= '0' && c <= '9')) {
        return Number(value);
      }
    }
  }
  return null;
}

/** How many items the collection holds, at per_page=1. Pure. [count, how]. */
export function countFromLink(linkHeader, returned) {
  const last = lastPageFromLink(linkHeader);
  if (last !== null) return [last, 'from rel="last" with per_page=1'];
  if (!returned) return [0, 'the first page came back empty and carried no rel="last"'];
  return [Number(returned), 'a single page with no rel="last", so this is what '
    + 'came back rather than a measured count'];
}

/** How many repositories the organization holds. Pure. [count, detail]. */
export function orgTotal(orgPayload) {
  if (!orgPayload || typeof orgPayload !== 'object') {
    return [null, 'no organization payload was read.'];
  }
  const pub = orgPayload.public_repos;
  const priv = orgPayload.total_private_repos;
  if ((pub === null || pub === undefined) && (priv === null || priv === undefined)) {
    return [null, 'neither repository count was returned, which needs '
      + 'organization access.'];
  }
  const total = Number(pub || 0) + Number(priv || 0);
  return [total, `public ${pub ?? 'unreadable'} + private ${priv ?? 'unreadable'}`];
}

/** Grade what the account can see against what the org holds. Pure. */
export function coverageState(visible, total) {
  if (total === null || total === undefined || visible === null
      || visible === undefined) {
    return 'unknown';
  }
  if (total <= 0) return 'nothing-to-cover';
  if (visible >= total) return 'full';
  if (visible === 0 || visible * 20 < total) return 'collapsed';
  if (visible * 2 < total) return 'shrunken';
  return 'partial';
}

/** Compare the configured base permission against the live one. Pure. */
export function drift(expected, actual) {
  if (!expected || actual === null || actual === undefined) {
    return ['drift-unknown', 'no expected base permission was supplied, or the '
      + 'live one could not be read, so there is nothing to compare.'];
  }
  const want = baseRank(expected);
  const have = baseRank(actual);
  if (want < 0 || have < 0) {
    return ['drift-unknown', 'one of the two values is not a documented base '
      + 'permission.'];
  }
  if (want === have) {
    return ['base-unchanged', 'the organization still reports the base '
      + 'permission this integration was configured against.'];
  }
  if (have < want) {
    return ['base-tightened', `configured for '${expected}', the organization `
      + `now says '${actual}'. That is one field and it re-graded every `
      + 'repository at once.'];
  }
  return ['base-loosened', `configured for '${expected}', the organization now `
    + `says '${actual}', which grants more implicit access than you expected `
    + 'rather than less.'];
}

/** The finding, in one state. Pure. [state, detail]. */
export function verdict(base, coverage) {
  if (base === null || base === undefined) {
    return ['base-unreadable', 'the base permission could not be read, so the '
      + 'coverage number stands on its own. Read it with a token that has '
      + 'organization access before concluding anything about the default.'];
  }
  if (base === 'none' && ['collapsed', 'shrunken'].includes(coverage)) {
    return ['base-none-implicit-access-gone', 'base permission is none and this '
      + 'account reaches a fraction of the organization. The repositories it '
      + 'still reaches are the ones it was added to explicitly; the rest were '
      + 'never granted, only defaulted.'];
  }
  if (base === 'none' && ['full', 'partial'].includes(coverage)) {
    return ['base-none-explicit-grants-hold', 'base permission is none and '
      + "coverage is largely intact, which means this account's access is "
      + 'explicit. It is not exposed to this change.'];
  }
  if (base !== 'none' && ['collapsed', 'shrunken'].includes(coverage)) {
    return ['coverage-lost-elsewhere', 'the base permission still grants '
      + 'implicit access and the coverage is short anyway, so the loss is not '
      + "this field. Membership, SSO authorization and an App's repository "
      + 'selection are the other ways a list gets shorter.'];
  }
  if (coverage === 'nothing-to-cover') {
    return ['nothing-to-cover', 'the organization reports no repositories, so '
      + 'there is no coverage question to answer.'];
  }
  return ['coverage-as-expected', 'the account reaches what the base permission '
    + 'implies it should. Nothing here explains a shorter list.'];
}

/** The narrow repair. Pure. Nothing here is executed. */
export function repair(state, org) {
  if (state === 'base-none-implicit-access-gone') {
    return `add this account, or a team it belongs to, to the repositories the `
      + `job is meant to cover in ${org}. Do not raise the base permission `
      + 'back: that re-grants implicit access to every member of the '
      + 'organization to fix one integration.';
  }
  if (state === 'coverage-lost-elsewhere') {
    return 'look past the base permission. Check that the account is still a '
      + 'member, that the token is SSO-authorized where that applies, and, for '
      + 'a GitHub App, that the installation covers the repositories you expect.';
  }
  if (state === 'base-unreadable') {
    return 're-read the organization with a token that has organization access. '
      + 'Until then the coverage number is a measurement without an explanation.';
  }
  if (state === 'base-none-explicit-grants-hold') {
    return 'nothing. Keep it that way: explicit grants are what makes this '
      + 'account immune to the next change to the default.';
  }
  return 'nothing on the base permission. The shorter list, if there is one, '
    + 'has another cause.';
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
  const expect = process.env.GITHUB_EXPECT || '';
  console.log(`read cost: ${readCost()} request(s) against the core hourly quota`);

  const orgResponse = await fetch(`${API}/orgs/${org}`, { headers: headers(token) });
  const orgPayload = orgResponse.status === 200 ? await orgResponse.json() : {};
  const [base, baseDetail] = baseState(orgPayload);
  console.log(`base permission: ${base || 'unreadable'} — ${baseDetail}`);

  const [driftState, driftDetail] = drift(expect, base);
  console.log(`drift: ${driftState} — ${driftDetail}`);

  const mine = await fetch(
    `${API}/user/repos?affiliation=organization_member&per_page=1`,
    { headers: headers(token) },
  );
  const body = mine.status === 200 ? await mine.json() : [];
  const [visible, how] = countFromLink(mine.headers.get('link'),
    Array.isArray(body) ? body.length : 0);
  console.log(`visible through membership: ${visible} (${how})`);

  const [total, totalDetail] = orgTotal(orgPayload);
  console.log(`organization holds: ${total ?? 'unreadable'} repositories (${totalDetail})`);

  const coverage = coverageState(visible, total);
  console.log(`coverage: ${coverage} — ${visible} of ${total ?? 'unreadable'}`);

  const [state, detail] = verdict(base, coverage);
  console.log(`state: ${state} — ${detail}`);
  console.log(`repair: ${repair(state, org)}`);

  console.log(JSON.stringify({
    organization: org,
    default_repository_permission: base,
    expected_base_permission: expect || null,
    drift_state: driftState,
    visible_through_membership: visible,
    visible_source: how,
    organization_total: total,
    coverage,
    state,
    detail,
    repair: repair(state, org),
  }, null, 2));
  process.exitCode = ['base-none-implicit-access-gone',
    'coverage-lost-elsewhere'].includes(state) ? 1 : 0;
}

// Guarded so importing this file from the test runner does not start a run.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Two things are worth testing hard here and the suite spends most of its length on them. The first is the counting trick, because it is the thing that makes the check affordable and the thing that is quietly wrong when a collection fits on one page: a missing <code>rel=\"last\"</code> has to be reported as a single page rather than as a count of zero, and the parse has to survive a URL with commas in it. The second is the refusal to blame the field the script happens to have read: a collapsed coverage beside a base permission of <code>read</code> is asserted to come back as somebody else's problem, with the alternatives named. The drift comparison is asserted in both directions, because a base permission that got <em>looser</em> than your configuration is also worth an alert.",
"test_py_file": "test_github_org_base_permission.py",
"test_py": '''from github_org_base_permission import (
    base_rank, base_state, count_from_link, coverage_state, drift,
    last_page_from_link, org_total, read_cost, repair, verdict,
)

LINK = ('<https://api.github.com/user/repos?per_page=1&page=2>; rel="next", '
        '<https://api.github.com/user/repos?per_page=1&page=9>; rel="last"')
ORG = {"default_repository_permission": "none",
       "public_repos": 12, "total_private_repos": 400}


def test_the_last_page_number_is_the_count_at_one_per_page():
    assert last_page_from_link(LINK) == 9
    count, how = count_from_link(LINK, 1)
    assert count == 9
    assert 'rel="last"' in how


def test_a_single_page_is_not_a_count_of_zero():
    # The collection fits on one page, so there is no rel="last" at all. Saying
    # zero here would report a working integration as having lost everything.
    count, how = count_from_link(None, 1)
    assert count == 1
    assert "single page" in how
    assert count_from_link("", 0) == (0, 'the first page came back empty and '
                                         'carried no rel="last"')


def test_the_link_parse_survives_a_url_with_commas_in_it():
    header = ('<https://api.github.com/search?q=a,b&per_page=1&page=3>; rel="last"')
    assert last_page_from_link(header) == 3
    assert last_page_from_link('<https://x/?page=notanumber>; rel="last"') is None
    assert last_page_from_link('<https://x/?page=2>; rel="next"') is None


def test_the_base_permission_says_what_it_implies():
    value, detail = base_state(ORG)
    assert value == "none"
    assert "were not added to" in detail
    assert base_state({"default_repository_permission": "read"})[1].startswith(
        "every member can read")
    assert base_rank("none") < base_rank("read") < base_rank("write")


def test_an_absent_base_permission_is_unreadable_not_none():
    value, detail = base_state({"login": "acme"})
    assert value is None
    assert "unreadable rather than absent" in detail
    assert verdict(None, "collapsed")[0] == "base-unreadable"


def test_the_organization_total_adds_both_halves():
    total, detail = org_total(ORG)
    assert total == 412
    assert "public 12" in detail
    assert org_total({"login": "acme"})[0] is None


def test_coverage_is_graded_rather_than_reported_as_a_ratio():
    assert coverage_state(9, 412) == "collapsed"
    assert coverage_state(0, 412) == "collapsed"
    assert coverage_state(150, 412) == "shrunken"
    assert coverage_state(300, 412) == "partial"
    assert coverage_state(412, 412) == "full"
    assert coverage_state(5, None) == "unknown"
    assert coverage_state(0, 0) == "nothing-to-cover"


def test_the_finding_names_the_field_only_when_the_field_fits():
    state, detail = verdict("none", "collapsed")
    assert state == "base-none-implicit-access-gone"
    assert "never granted, only defaulted" in detail


def test_a_collapsed_coverage_under_read_is_somebody_elses_problem():
    # The script has just read the base permission, which makes it the easiest
    # thing in the room to blame. It refuses.
    state, detail = verdict("read", "collapsed")
    assert state == "coverage-lost-elsewhere"
    assert "not this field" in detail
    assert "repository selection" in detail


def test_explicit_grants_are_reported_as_immunity():
    state, detail = verdict("none", "full")
    assert state == "base-none-explicit-grants-hold"
    assert "not exposed to this change" in detail


def test_drift_is_reported_in_both_directions():
    state, detail = drift("read", "none")
    assert state == "base-tightened"
    assert "re-graded every repository at once" in detail
    assert drift("read", "write")[0] == "base-loosened"
    assert drift("read", "read")[0] == "base-unchanged"
    assert drift(None, "read")[0] == "drift-unknown"
    assert drift("read", None)[0] == "drift-unknown"


def test_the_repair_refuses_to_recommend_the_easy_fix():
    fix = repair("base-none-implicit-access-gone", "acme")
    assert "add this account" in fix and "acme" in fix
    assert "Do not raise the base permission back" in fix
    assert "still a member" in repair("coverage-lost-elsewhere", "acme")


def test_the_run_costs_three_reads():
    assert read_cost() == 3
''',
"test_js_file": "github-org-base-permission.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  baseRank, baseState, countFromLink, coverageState, drift, lastPageFromLink,
  orgTotal, readCost, repair, verdict,
} from './github-org-base-permission.mjs';

const LINK = '<https://api.github.com/user/repos?per_page=1&page=2>; rel="next", '
  + '<https://api.github.com/user/repos?per_page=1&page=9>; rel="last"';
const ORG = {
  default_repository_permission: 'none',
  public_repos: 12,
  total_private_repos: 400,
};

test('the last page number is the count at one per page', () => {
  assert.equal(lastPageFromLink(LINK), 9);
  const [count, how] = countFromLink(LINK, 1);
  assert.equal(count, 9);
  assert.match(how, /rel="last"/);
});

test('a single page is not a count of zero', () => {
  const [count, how] = countFromLink(null, 1);
  assert.equal(count, 1);
  assert.match(how, /single page/);
  assert.equal(countFromLink('', 0)[0], 0);
});

test('the link parse survives a url with commas in it', () => {
  const header = '<https://api.github.com/search?q=a,b&per_page=1&page=3>; rel="last"';
  assert.equal(lastPageFromLink(header), 3);
  assert.equal(lastPageFromLink('<https://x/?page=notanumber>; rel="last"'), null);
  assert.equal(lastPageFromLink('<https://x/?page=2>; rel="next"'), null);
});

test('the base permission says what it implies', () => {
  const [value, detail] = baseState(ORG);
  assert.equal(value, 'none');
  assert.match(detail, /were not added to/);
  assert.ok(baseRank('none') < baseRank('read'));
  assert.ok(baseRank('read') < baseRank('write'));
});

test('an absent base permission is unreadable not none', () => {
  const [value, detail] = baseState({ login: 'acme' });
  assert.equal(value, null);
  assert.match(detail, /unreadable rather than absent/);
  assert.equal(verdict(null, 'collapsed')[0], 'base-unreadable');
});

test('the organization total adds both halves', () => {
  const [total, detail] = orgTotal(ORG);
  assert.equal(total, 412);
  assert.match(detail, /public 12/);
  assert.equal(orgTotal({ login: 'acme' })[0], null);
});

test('coverage is graded rather than reported as a ratio', () => {
  assert.equal(coverageState(9, 412), 'collapsed');
  assert.equal(coverageState(0, 412), 'collapsed');
  assert.equal(coverageState(150, 412), 'shrunken');
  assert.equal(coverageState(300, 412), 'partial');
  assert.equal(coverageState(412, 412), 'full');
  assert.equal(coverageState(5, null), 'unknown');
  assert.equal(coverageState(0, 0), 'nothing-to-cover');
});

test('the finding names the field only when the field fits', () => {
  const [state, detail] = verdict('none', 'collapsed');
  assert.equal(state, 'base-none-implicit-access-gone');
  assert.match(detail, /never granted, only defaulted/);
});

test('a collapsed coverage under read is somebody elses problem', () => {
  const [state, detail] = verdict('read', 'collapsed');
  assert.equal(state, 'coverage-lost-elsewhere');
  assert.match(detail, /not this field/);
  assert.match(detail, /repository selection/);
});

test('explicit grants are reported as immunity', () => {
  const [state, detail] = verdict('none', 'full');
  assert.equal(state, 'base-none-explicit-grants-hold');
  assert.match(detail, /not exposed to this change/);
});

test('drift is reported in both directions', () => {
  const [state, detail] = drift('read', 'none');
  assert.equal(state, 'base-tightened');
  assert.match(detail, /re-graded every repository at once/);
  assert.equal(drift('read', 'write')[0], 'base-loosened');
  assert.equal(drift('read', 'read')[0], 'base-unchanged');
  assert.equal(drift(null, 'read')[0], 'drift-unknown');
  assert.equal(drift('read', null)[0], 'drift-unknown');
});

test('the repair refuses to recommend the easy fix', () => {
  const fix = repair('base-none-implicit-access-gone', 'acme');
  assert.match(fix, /add this account/);
  assert.match(fix, /Do not raise the base permission back/);
  assert.match(repair('coverage-lost-elsewhere', 'acme'), /still a member/);
});

test('the run costs three reads', () => {
  assert.equal(readCost(), 3);
});
''',
"faq": [
 ("Nothing was revoked from our account. How can it have lost access?",
  "Because most of that access was never granted to the account in the first place. A member's role on a repository they were not added to comes from the organization's default, and a default is not a grant — there is no record on the repository naming your account, nothing to revoke and nothing in an audit trail about your account at all. The change is one field on the organization, and it applies to every member and every repository the moment it is saved."),
 ("How is this different from a role being too low on one repository?",
  "Different object, different symptom. A role that is too low on one repository refuses one action on one repository, loudly, with a 403 you can catch. A base permission is organization-wide and re-grades every repository at once, and its symptom is that a list came back shorter while every call in it returned 200. That is why the diagnostic here is a count rather than a permissions object: there is no single failing call to inspect."),
 ("Why count with rel=\"last\" instead of listing everything?",
  "Because the affordable version of a check is the one that gets run. Asking for one item per page and reading the last page number gives you the size of a collection in a single request, so a four-hundred-repository organization costs one unit of quota to measure rather than four hundred. The catch is that a collection which fits on one page has no <code>rel=\"last\"</code> at all, and a script that reads that as zero has just invented a catastrophe. The count is reported with its source for exactly that reason."),
 ("Should we set the base permission back to read?",
  "Almost certainly not. Base permission at <code>read</code> means every member of the organization can read every repository in it, which is a much bigger grant than the one your integration needs, and moving it back to fix one job undoes a deliberate security decision for everybody. Add the account, or a team it belongs to, to the repositories the job covers. Explicit grants also make the integration immune to the next change to the default, which is the real win."),
 ("Our coverage collapsed and the base permission is still read. Then what?",
  "Then it is not this. The script says so rather than blaming the field it happens to have read. A list gets shorter for several other reasons: the account may no longer be a member of the organization, the token may not be SSO-authorized for it, or — for a GitHub App — the installation may cover only selected repositories. Each of those is its own note, and each has a different single reading that confirms it."),
],
"related": [
 ("/github/collaborator-permission-insufficient/", "The same question about one repository and one account"),
 ("/github/rel-last-absent/", "When the counting trick has no last page to read"),
 ("/github/installation-repository-selection-partial/", "The App version of silently partial coverage"),
],
"citations": [CITE_BASE_PERMISSIONS, CITE_ORGS, CITE_REPOS, CITE_PAGINATION],
},
{
"slug": "app-installation-request-pending",
"title": "The App installation was requested and never approved",
"description": "A non-owner's install becomes a request an owner has to approve. Until they do there is no installation at all, while the product still shows connected.",
"h1": "The App installation was requested and never approved",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github app installation request pending approval",
             "github app installed but no events",
             "github app installations list missing org",
             "orgs org installation 404 github app",
             "github app request owner approval organization"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The customer says they installed the App. Your product agrees: the connection screen is green, the account is on the list, the onboarding checklist is ticked. And nothing has ever arrived — no webhook deliveries, no repositories, no first sync — and every support thread ends with somebody asking them to uninstall and install it again, which they cannot do either, because they never installed it in the first place. They asked for it. They were not an owner of the organization, so the install button quietly became a request, and it is still sitting in a queue behind somebody who has never been told it is there.",
"short_answer": """<p>Only an organization owner can install a GitHub App. When anybody else goes through the flow, GitHub turns it into a <em>request</em>: the user sees a confirmation that looks like success, an owner has to approve it, and until they do the App has no installation on that account at all.</p>
<p>Ask the App itself. <code>GET /app/installations</code> with the App's JWT lists every installation the App actually has; a pending account is simply absent. <code>GET /orgs/{org}/installation</code> answers 404 for the same reason. Neither of those distinguishes pending from declined or from never-started, and no endpoint publishes the request queue to the App — so the finding comes from reconciling that list against <em>your own</em> record of who began a flow and when.</p>""",
"problem": """<p>The reason this one runs for weeks is that both sides are telling the truth. The customer did complete a flow, saw a confirmation page and has an email about it. Your product recorded a connection, because the OAuth leg completed and the callback fired. The only party that disagrees is GitHub, and nobody asks GitHub, because from the product's point of view the connection already exists and the thing to debug is why it is not delivering.</p>
<p>So the support thread goes to webhooks. Is the delivery URL right, is the secret right, are the events subscribed, is the endpoint returning 200. All of those are answerable and all of the answers are fine, because a hook with no installation behind it has nothing to deliver and no failures to show. Then it goes to permissions, and those are fine too. Every diagnostic in the section that starts from "the App is installed" is being run against an account where it is not.</p>
<p>The final trap is the retry advice. "Uninstall and reinstall" is the standard remedy for a broken installation and it is unavailable here: there is nothing to uninstall, and the user going through the flow a second time produces a second request in the same queue, which is why some accounts arrive with four of them. The person who can end it is an owner who received one notification, weeks ago, about a product they had not heard of.</p>""",
"why": """<p><strong>Requested is a third state, and most code has room for two.</strong> Integrations model an App as installed or not installed. This is neither: the account has expressed intent, GitHub has recorded it, and the App has no capability whatsoever. Your product's state machine almost certainly has no square for it, which is why it renders as connected — <em>connected</em> is the state it moves to when a flow completes, and the flow did complete.</p>
<p><strong>It is a different absence from the one the section already publishes.</strong> <a href="/github/app-not-installed-on-repo/">An App that is installed on an organization but not on one repository</a> answers 404 for that repository and works everywhere else, and <code>GET /repos/{owner}/{repo}/installation</code> settles it. This is the account-level absence: there is no installation to select repositories within, so the repository question cannot even be asked. Ask the account-level one instead, and expect a 404 that means "not yet" rather than "not this repo".</p>
<p><strong>The API will not tell you it is pending.</strong> This is the honest limit and it shapes the whole script. There is no endpoint that lists an App's pending installation requests, so absence from <code>GET /app/installations</code> covers pending, declined, abandoned halfway and never attempted, all with the same silence. What separates them is information you already hold: the moment a user started a flow. Reconciling GitHub's list against your own connection records is therefore not a shortcut, it is the only method, and the script is built around it rather than pretending a single call answers this.</p>
<p><strong>The reconciliation is worth doing in both directions.</strong> The obvious direction finds accounts your product calls connected that GitHub has never heard of. The other direction finds installations GitHub has that your product does not know about, which is the same bug seen from the far side: an owner approved the request three weeks after the user gave up, the App has been installed and delivering ever since, and nothing in your product ever noticed. Both are silent, and one scheduled pass over the list catches both.</p>
<p><strong>An installation that exists and is suspended is a different note.</strong> If the account is on the list with a <code>suspended_at</code>, it was installed and then switched off, which is <a href="/github/installation-suspended/">its own diagnosis and its own repair</a>. The script separates that case out rather than folding it into a headline about approvals, because telling somebody to chase an approval that already happened is worse than saying nothing.</p>""",
"steps": [
 {"h": "Ask the App what it actually has",
  "body": """<p>With the App's JWT, <code>GET /app/installations</code> lists every installation. The script pages it at 100 per page and reports how many pages it read, because a large App that reads only the first page will confidently report every account after the hundredth as missing. The list is turned into an index keyed by account login, with each installation's id, creation time and suspension state.</p>"""},
 {"h": "Bring your own record of who started a flow",
  "body": """<p>Pass <code>--record connections.json</code>: a list of accounts, when each began an installation flow, and whether your product currently shows them as connected. This is the half GitHub cannot supply. Without it the script can only say an account is absent; with it, it can say the account is absent <em>and</em> your product has been showing it as connected for nineteen days.</p>"""},
 {"h": "Confirm the account-level absence directly",
  "body": """<p>For each account, <code>GET /orgs/{org}/installation</code> under the JWT answers 200 with the installation or 404 without one. It is the same fact the list gives, asked about one account, and it is worth asking because it is the call that fails in exactly the way the pending state produces — and because it distinguishes an account that is genuinely absent from one your paging missed.</p>"""},
 {"h": "Sort the absences by what your own record says",
  "body": """<p>The script reconciles each account into one state: your product says connected and GitHub has nothing, a flow started recently and is plausibly still awaiting approval, a flow started long enough ago that the request has almost certainly been forgotten, or an installation exists that your product never recorded. Suspended installations are handed to their own note instead of being counted as approvals.</p>"""},
 {"h": "Print the step; never take it",
  "body": """<p>The output for a pending account is the sentence to put in front of the user: an owner of that organization has to approve the request from the organization's GitHub Apps settings. The script does not request an installation, does not approve one, and cannot — it holds a read path only. Its job is to stop the product from claiming a connection it does not have.</p>"""},
],
"verify": """<p>After an owner approves the request, the account appears in the App's own installation list and the per-account probe stops answering 404.</p>
<pre><code class="language-bash">GITHUB_APP_JWT=$JWT python3 github_app_installation_pending.py \\
    --record connections.json
# read cost: up to 4 request(s) against the core quota (1 app + up to 1 list
#   page + 2 account probe(s))
# app: acme-sync (JWT accepted)
# installations: 37 read from 1 page(s)
# globex: HTTP 404 from GET /orgs/globex/installation
#   false-connected — your record says connected since 2026-08-10 and this App
#   has no installation on globex. Absence covers pending, declined and never
#   started; the API publishes no request queue, so your record is what makes
#   this readable.
#   step: an owner of globex has to approve the pending installation request
#   from the organization's GitHub Apps settings. Nothing here requests or
#   approves anything.
# initech: installed 2026-07-02, and your record does not show it as connected
#   unrecorded-installation — approved after the user gave up. Your product has
#   been ignoring a working installation.</code></pre>""",
"code_intro": "The live half is a paged list and one probe per account, and the script says how many pages it read because a partial list turns every account past the first hundred into a false finding. The half that produces the answer is pure and takes two inputs: what the App has, and what you believe it has. That is the shape the note argues for — the API cannot tell you a request is pending, so the reconciliation against your own record is the method rather than a convenience. Note what the reconciler does with a suspended installation: it refuses to count it either way and hands it to the note that owns it.",
"py_file": "github_app_installation_pending.py",
"py": '''"""Find accounts where a GitHub App was requested and never approved.

Read only. GETs against the App's own records with the App JWT, and a local
JSON file of your own connection state. This script never requests an
installation and never approves one: approving is an organization owner's
decision, and asking for one is a write. It detects the state and prints the
step for a human to take.

The point of the note: only an owner can install an App on an organization.
Anybody else going through the flow creates a *request*, which sits in a queue
until an owner approves it. Until then the App has no installation on that
account at all, while the product that started the flow shows it as connected.

What this can and cannot see: absence. GET /app/installations does not list
pending requests, and no endpoint publishes the queue to the App, so an absent
account is pending, declined, abandoned or never attempted with the same
silence. Your own record of who began a flow and when is what separates them,
which is why this script takes one as input rather than pretending a single
call answers the question.

Environment:

    GITHUB_APP_JWT    the JWT your own signing code produced
"""
import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_app_installation_pending")

API = "https://api.github.com"
UA = "github-app-installation-pending/1.0"

# How long a request can sit before it is more likely forgotten than pending.
# A default rather than a rule: it decides only which sentence is printed.
STALE_AFTER_DAYS = 7

# Said once, in one place, because it is the honest core of the note and every
# state that reports an absence has to carry it.
ABSENCE_MEANING = ("absence covers pending, declined and never started; the "
                   "API publishes no request queue, so your record is what "
                   "makes this readable.")


def read_cost(accounts, pages=1):
    """Requests this run will spend against the core quota. Pure."""
    return 1 + max(1, int(pages)) + len(accounts or [])


def installation_index(installations):
    """Index the App's installations by account login. Pure.

    Lower-cased keys because logins are compared case-insensitively everywhere
    else in this API and a record file written by hand will not match the
    casing GitHub returns.
    """
    index = {}
    for item in installations or []:
        if not isinstance(item, dict):
            continue
        account = item.get("account") or {}
        login = account.get("login") if isinstance(account, dict) else None
        if not login:
            continue
        index[str(login).strip().lower()] = {
            "id": item.get("id"),
            "created_at": item.get("created_at"),
            "repository_selection": item.get("repository_selection"),
            "suspended": item.get("suspended_at") not in (None, "", "null"),
        }
    return index


def probe_state(status):
    """What GET /orgs/{org}/installation means. Pure. (state, detail)."""
    code = int(status or 0)
    if code == 200:
        return ("installed", "the App has an installation on this account.")
    if code == 404:
        return ("no-installation",
                "the App has no installation on this account. " + ABSENCE_MEANING)
    if code in (401, 403):
        return ("unreadable",
                "the JWT was refused on this probe, so nothing can be "
                "concluded about the account.")
    return ("unclear", "HTTP %s is not one of the answers this probe gives."
            % status)


def parsed_time(text):
    """An ISO 8601 timestamp as an aware datetime, or None. Pure."""
    if not text:
        return None
    value = str(text).strip()
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def age_days(started_at, now):
    """How long ago the flow started, in days. Pure. None if unparseable."""
    start = parsed_time(started_at)
    if start is None or now is None:
        return None
    return (now - start).total_seconds() / 86400.0


def request_age_state(days, stale_after=STALE_AFTER_DAYS):
    """Is this request plausibly still in flight. Pure. (state, detail)."""
    if days is None:
        return ("age-unknown",
                "your record does not say when the flow started, so the "
                "request cannot be aged.")
    if days <= stale_after:
        return ("awaiting-approval",
                "the flow started %.1f day(s) ago, which is recent enough that "
                "an owner may simply not have looked yet." % days)
    return ("stale-request",
            "the flow started %.1f day(s) ago. A request that old is more "
            "likely forgotten than pending, and the owner who could approve it "
            "was notified once." % days)


def reconcile(entry, installation, now, stale_after=STALE_AFTER_DAYS):
    """One account, two sources of truth. Pure. (state, detail).

    entry is your own record: account, started_at, connected. installation is
    what the App's own list holds for that account, or None.
    """
    account = str((entry or {}).get("account") or "unknown")
    connected = bool((entry or {}).get("connected"))
    started_at = (entry or {}).get("started_at")

    if installation:
        if installation.get("suspended"):
            return ("installed-but-suspended",
                    "an installation exists on %s and is suspended, which is a "
                    "different diagnosis and a different repair. Do not chase "
                    "an approval that already happened." % account)
        if connected:
            return ("agreed-connected",
                    "an installation exists and your record agrees. Nothing to "
                    "reconcile.")
        return ("unrecorded-installation",
                "an installation exists on %s and your record does not show it "
                "as connected. An owner approved it after the fact and nothing "
                "in your product noticed." % account)
    if connected:
        return ("false-connected",
                "your record says connected%s and this App has no installation "
                "on %s. %s"
                % (" since " + str(started_at) if started_at else "",
                   account, ABSENCE_MEANING))
    age_state, age_detail = request_age_state(age_days(started_at, now), stale_after)
    if age_state in ("awaiting-approval", "stale-request"):
        return (age_state, age_detail + " " + ABSENCE_MEANING)
    return ("agreed-disconnected",
            "no installation, and your record does not claim one. There is "
            "nothing here to explain.")


def actionable(state):
    """Is this a state somebody has to do something about. Pure."""
    return state in ("false-connected", "awaiting-approval", "stale-request",
                     "unrecorded-installation", "installed-but-suspended")


def printed_step(state, account):
    """The step to put in front of a human. Pure. Nothing here is executed.

    This script holds a read path only. It cannot request an installation and
    cannot approve one, and it should not: approving is a decision about what
    reaches an organization's code, and it belongs to an owner.
    """
    if state in ("false-connected", "awaiting-approval", "stale-request"):
        return ("an owner of %s has to approve the pending installation "
                "request from the organization's GitHub Apps settings. "
                "Nothing here requests or approves anything." % account)
    if state == "unrecorded-installation":
        return ("reconcile your stored connection state for %s: the "
                "installation is real and your product is ignoring it."
                % account)
    if state == "installed-but-suspended":
        return ("ask an owner of %s to unsuspend the installation. The "
                "approval is not what is missing." % account)
    return "nothing for this account."


def product_repair(states):
    """What to change in the product, given everything seen. Pure."""
    if any(s == "false-connected" for s in states):
        return ("stop rendering a completed flow as a connection. Show the "
                "requested state explicitly, prompt the user to ask an owner "
                "to approve it, and reconcile against GET /app/installations "
                "on a schedule rather than trusting the callback.")
    if any(s in ("awaiting-approval", "stale-request") for s in states):
        return ("surface the pending state in the product and re-check it on a "
                "schedule. A request that nobody is reminded about is a "
                "request that expires by neglect.")
    if any(s == "unrecorded-installation" for s in states):
        return ("reconcile in the other direction too: an installation "
                "approved after the user gave up delivers nothing if your "
                "product never records it.")
    return "nothing. The App's installations and your record agree."


def load_record(path, accounts):
    """Your own connection state. Not part of the API and not a write.

    Accepts a JSON list of {account, started_at, connected}. Accounts named on
    the command line are added as ones you believe are connected, which is the
    common case: somebody says a customer is connected and you want to know.
    """
    entries = []
    if path:
        with open(path, "r", encoding="utf-8") as handle:
            loaded = json.load(handle)
        for item in loaded if isinstance(loaded, list) else []:
            if isinstance(item, dict) and item.get("account"):
                entries.append(item)
    for account in accounts or []:
        entries.append({"account": account, "connected": True})
    return entries


def get(session, path):
    """One GET. Returns the response object."""
    return session.get(API + path, timeout=30)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--record",
                        help="JSON list of {account, started_at, connected}")
    parser.add_argument("--account", action="append", default=[],
                        help="an account you believe is connected; repeatable")
    parser.add_argument("--max-pages", type=int, default=5,
                        help="pages of /app/installations to read")
    parser.add_argument("--stale-after", type=int, default=STALE_AFTER_DAYS,
                        help="days after which a request is called stale")
    args = parser.parse_args()

    jwt = os.environ.get("GITHUB_APP_JWT")
    if not jwt:
        log.error("set GITHUB_APP_JWT (the JWT your own signing code produced)")
        return 2

    entries = load_record(args.record, args.account)
    if not entries:
        log.error("nothing to reconcile: pass --record or --account. This "
                  "script compares GitHub's list against your own, and the "
                  "second half is the half GitHub cannot supply.")
        return 2

    log.info("read cost: up to %d request(s) against the core quota "
             "(1 app + up to %d list page(s) + %d account probe(s))",
             read_cost(entries, args.max_pages), max(1, args.max_pages),
             len(entries))

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + jwt,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": UA,
    })

    app = get(session, "/app")
    if app.status_code != 200:
        log.error("GET /app returned HTTP %s: the JWT was not accepted, which "
                  "is a different note", app.status_code)
        return 2
    log.info("app: %s (JWT accepted)", (app.json() or {}).get("slug"))

    installations, pages = [], 0
    for page in range(1, max(1, args.max_pages) + 1):
        response = get(session, "/app/installations?per_page=100&page=%d" % page)
        if response.status_code != 200:
            log.warning("installation list page %d returned HTTP %s; the list "
                        "below is partial", page, response.status_code)
            break
        batch = response.json() or []
        pages = page
        installations.extend(batch)
        if len(batch) < 100:
            break
    log.info("installations: %d read from %d page(s)", len(installations), pages)

    index = installation_index(installations)
    now = datetime.now(timezone.utc)
    results, states = [], []

    for entry in entries:
        account = str(entry.get("account"))
        probe = get(session, "/orgs/%s/installation" % account)
        probe_result, probe_detail = probe_state(probe.status_code)
        installation = index.get(account.strip().lower())
        if probe_result == "installed" and installation is None:
            installation = {"id": None, "created_at": None,
                            "repository_selection": None, "suspended": False}
        if probe_result == "no-installation":
            installation = None
        state, detail = reconcile(entry, installation, now, args.stale_after)
        log.info("%s: HTTP %s from GET /orgs/%s/installation",
                 account, probe.status_code, account)
        log.info("  %s — %s", state, detail)
        log.info("  step: %s", printed_step(state, account))
        states.append(state)
        results.append({
            "account": account,
            "probe_status": probe.status_code,
            "probe_state": probe_result,
            "probe_detail": probe_detail,
            "installation_id": (installation or {}).get("id"),
            "state": state,
            "detail": detail,
            "actionable": actionable(state),
            "step": printed_step(state, account),
        })

    log.info("product repair: %s", product_repair(states))
    print(json.dumps({
        "installations_read": len(installations),
        "pages_read": pages,
        "accounts": results,
        "product_repair": product_repair(states),
    }, indent=2, default=str))
    return 1 if any(actionable(s) for s in states) else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-app-installation-pending.mjs",
"js": '''/**
 * Find accounts where a GitHub App was requested and never approved.
 *
 * Read only. GETs against the App's own records with the App JWT, plus a local
 * JSON file of your own connection state. This script never requests an
 * installation and never approves one: approving belongs to an organization
 * owner. It detects the state and prints the step.
 *
 * Only an owner can install an App on an organization. Anybody else going
 * through the flow creates a request that waits in a queue, and until it is
 * approved the App has no installation on that account at all.
 *
 * The API does not list pending requests, so an absent account is pending,
 * declined, abandoned or never attempted with the same silence. Your own
 * record of who began a flow is what separates them.
 *
 * Environment:
 *   GITHUB_APP_JWT    the JWT your own signing code produced
 *   GITHUB_RECORD     path to a JSON list of {account, started_at, connected}
 *   GITHUB_ACCOUNTS   comma-separated accounts you believe are connected
 */
import { readFileSync } from 'node:fs';

const API = 'https://api.github.com';
const UA = 'github-app-installation-pending/1.0';

/** How long a request can sit before it is more likely forgotten than pending. */
export const STALE_AFTER_DAYS = 7;

/** The honest core of the note, said once. */
export const ABSENCE_MEANING = 'absence covers pending, declined and never '
  + 'started; the API publishes no request queue, so your record is what makes '
  + 'this readable.';

/** Requests this run will spend against the core quota. Pure. */
export function readCost(accounts, pages = 1) {
  return 1 + Math.max(1, Number(pages) || 1) + (accounts ? accounts.length : 0);
}

/** Index the App's installations by account login. Pure. */
export function installationIndex(installations) {
  const index = {};
  for (const item of installations || []) {
    if (!item || typeof item !== 'object') continue;
    const account = item.account && typeof item.account === 'object' ? item.account : {};
    const login = account.login;
    if (!login) continue;
    index[String(login).trim().toLowerCase()] = {
      id: item.id,
      created_at: item.created_at,
      repository_selection: item.repository_selection,
      suspended: !['', null, undefined, 'null'].includes(item.suspended_at),
    };
  }
  return index;
}

/** What GET /orgs/{org}/installation means. Pure. [state, detail]. */
export function probeState(status) {
  const code = Number(status) || 0;
  if (code === 200) return ['installed', 'the App has an installation on this account.'];
  if (code === 404) {
    return ['no-installation', `the App has no installation on this account. ${ABSENCE_MEANING}`];
  }
  if ([401, 403].includes(code)) {
    return ['unreadable', 'the JWT was refused on this probe, so nothing can '
      + 'be concluded about the account.'];
  }
  return ['unclear', `HTTP ${status} is not one of the answers this probe gives.`];
}

/** An ISO 8601 timestamp as a Date, or null. Pure. */
export function parsedTime(text) {
  if (!text) return null;
  const ms = Date.parse(String(text));
  return Number.isNaN(ms) ? null : new Date(ms);
}

/** How long ago the flow started, in days. Pure. null if unparseable. */
export function ageDays(startedAt, now) {
  const start = parsedTime(startedAt);
  if (start === null || !now) return null;
  return (now.getTime() - start.getTime()) / 86400000;
}

/** Is this request plausibly still in flight. Pure. [state, detail]. */
export function requestAgeState(days, staleAfter = STALE_AFTER_DAYS) {
  if (days === null || days === undefined) {
    return ['age-unknown', 'your record does not say when the flow started, so '
      + 'the request cannot be aged.'];
  }
  if (days <= staleAfter) {
    return ['awaiting-approval', `the flow started ${days.toFixed(1)} day(s) `
      + 'ago, which is recent enough that an owner may simply not have looked '
      + 'yet.'];
  }
  return ['stale-request', `the flow started ${days.toFixed(1)} day(s) ago. A `
    + 'request that old is more likely forgotten than pending, and the owner '
    + 'who could approve it was notified once.'];
}

/** One account, two sources of truth. Pure. [state, detail]. */
export function reconcile(entry, installation, now, staleAfter = STALE_AFTER_DAYS) {
  const record = entry || {};
  const account = String(record.account ?? 'unknown');
  const connected = Boolean(record.connected);
  const startedAt = record.started_at;

  if (installation) {
    if (installation.suspended) {
      return ['installed-but-suspended', `an installation exists on ${account} `
        + 'and is suspended, which is a different diagnosis and a different '
        + 'repair. Do not chase an approval that already happened.'];
    }
    if (connected) {
      return ['agreed-connected', 'an installation exists and your record '
        + 'agrees. Nothing to reconcile.'];
    }
    return ['unrecorded-installation', `an installation exists on ${account} `
      + 'and your record does not show it as connected. An owner approved it '
      + 'after the fact and nothing in your product noticed.'];
  }
  if (connected) {
    return ['false-connected', `your record says connected`
      + `${startedAt ? ` since ${startedAt}` : ''} and this App has no `
      + `installation on ${account}. ${ABSENCE_MEANING}`];
  }
  const [ageState, ageDetail] = requestAgeState(ageDays(startedAt, now), staleAfter);
  if (['awaiting-approval', 'stale-request'].includes(ageState)) {
    return [ageState, `${ageDetail} ${ABSENCE_MEANING}`];
  }
  return ['agreed-disconnected', 'no installation, and your record does not '
    + 'claim one. There is nothing here to explain.'];
}

/** Is this a state somebody has to do something about. Pure. */
export function actionable(state) {
  return ['false-connected', 'awaiting-approval', 'stale-request',
    'unrecorded-installation', 'installed-but-suspended'].includes(state);
}

/** The step to put in front of a human. Pure. Nothing here is executed. */
export function printedStep(state, account) {
  if (['false-connected', 'awaiting-approval', 'stale-request'].includes(state)) {
    return `an owner of ${account} has to approve the pending installation `
      + "request from the organization's GitHub Apps settings. Nothing here "
      + 'requests or approves anything.';
  }
  if (state === 'unrecorded-installation') {
    return `reconcile your stored connection state for ${account}: the `
      + 'installation is real and your product is ignoring it.';
  }
  if (state === 'installed-but-suspended') {
    return `ask an owner of ${account} to unsuspend the installation. The `
      + 'approval is not what is missing.';
  }
  return 'nothing for this account.';
}

/** What to change in the product, given everything seen. Pure. */
export function productRepair(states) {
  const seen = states || [];
  if (seen.includes('false-connected')) {
    return 'stop rendering a completed flow as a connection. Show the requested '
      + 'state explicitly, prompt the user to ask an owner to approve it, and '
      + 'reconcile against GET /app/installations on a schedule rather than '
      + 'trusting the callback.';
  }
  if (seen.some((s) => ['awaiting-approval', 'stale-request'].includes(s))) {
    return 'surface the pending state in the product and re-check it on a '
      + 'schedule. A request that nobody is reminded about is a request that '
      + 'expires by neglect.';
  }
  if (seen.includes('unrecorded-installation')) {
    return 'reconcile in the other direction too: an installation approved '
      + 'after the user gave up delivers nothing if your product never records '
      + 'it.';
  }
  return "nothing. The App's installations and your record agree.";
}

function headers(jwt) {
  return {
    Authorization: `Bearer ${jwt}`,
    Accept: 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
    'User-Agent': UA,
  };
}

async function main() {
  const jwt = process.env.GITHUB_APP_JWT;
  if (!jwt) {
    console.error('set GITHUB_APP_JWT (the JWT your own signing code produced)');
    process.exitCode = 2;
    return;
  }
  const entries = [];
  if (process.env.GITHUB_RECORD) {
    const loaded = JSON.parse(readFileSync(process.env.GITHUB_RECORD, 'utf-8'));
    for (const item of Array.isArray(loaded) ? loaded : []) {
      if (item && item.account) entries.push(item);
    }
  }
  for (const account of (process.env.GITHUB_ACCOUNTS || '').split(',')
    .map((s) => s.trim()).filter(Boolean)) {
    entries.push({ account, connected: true });
  }
  if (entries.length === 0) {
    console.error('nothing to reconcile: set GITHUB_RECORD or GITHUB_ACCOUNTS. '
      + "This script compares GitHub's list against your own, and the second "
      + 'half is the half GitHub cannot supply.');
    process.exitCode = 2;
    return;
  }

  const maxPages = Number(process.env.GITHUB_MAX_PAGES || 5) || 5;
  console.log(`read cost: up to ${readCost(entries, maxPages)} request(s) against `
    + 'the core quota');

  const app = await fetch(`${API}/app`, { headers: headers(jwt) });
  if (app.status !== 200) {
    console.error(`GET /app returned HTTP ${app.status}: the JWT was not accepted`);
    process.exitCode = 2;
    return;
  }
  console.log(`app: ${(await app.json()).slug} (JWT accepted)`);

  const installations = [];
  let pages = 0;
  for (let page = 1; page <= Math.max(1, maxPages); page += 1) {
    const response = await fetch(`${API}/app/installations?per_page=100&page=${page}`,
      { headers: headers(jwt) });
    if (response.status !== 200) {
      console.warn(`installation list page ${page} returned HTTP ${response.status}; `
        + 'the list below is partial');
      break;
    }
    const batch = await response.json();
    pages = page;
    installations.push(...batch);
    if (batch.length < 100) break;
  }
  console.log(`installations: ${installations.length} read from ${pages} page(s)`);

  const index = installationIndex(installations);
  const now = new Date();
  const results = [];
  const states = [];

  for (const entry of entries) {
    const account = String(entry.account);
    // eslint-disable-next-line no-await-in-loop
    const probe = await fetch(`${API}/orgs/${account}/installation`,
      { headers: headers(jwt) });
    const [probeResult] = probeState(probe.status);
    let installation = index[account.trim().toLowerCase()] || null;
    if (probeResult === 'no-installation') installation = null;
    const [state, detail] = reconcile(entry, installation, now);
    console.log(`${account}: HTTP ${probe.status} from GET /orgs/${account}/installation`);
    console.log(`  ${state} — ${detail}`);
    console.log(`  step: ${printedStep(state, account)}`);
    states.push(state);
    results.push({
      account,
      probe_status: probe.status,
      probe_state: probeResult,
      installation_id: installation ? installation.id : null,
      state,
      detail,
      actionable: actionable(state),
      step: printedStep(state, account),
    });
  }

  console.log(`product repair: ${productRepair(states)}`);
  console.log(JSON.stringify({
    installations_read: installations.length,
    pages_read: pages,
    accounts: results,
    product_repair: productRepair(states),
  }, null, 2));
  process.exitCode = states.some((s) => actionable(s)) ? 1 : 0;
}

// Guarded so importing this file from the test runner does not start a run.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The reconciler is the whole note, so the suite is a table of the four combinations of what GitHub has and what you believe, plus the two that do not fit in that table. The important assertions are the ones about silence: an absent account has to carry the sentence saying that absence covers pending, declined and never started, because a state name on its own invites somebody to read <em>pending</em> as a fact GitHub reported. A suspended installation has to come back as its own state rather than as an approval, since telling somebody to chase an approval that already happened is worse than saying nothing. And the step printed for every pending account is asserted to be a request addressed to a human, in those words, because a script in this section must never be the thing that asks GitHub for an installation.",
"test_py_file": "test_github_app_installation_pending.py",
"test_py": '''from datetime import datetime, timezone

from github_app_installation_pending import (
    ABSENCE_MEANING, actionable, age_days, installation_index, printed_step,
    probe_state, product_repair, read_cost, reconcile, request_age_state,
)

NOW = datetime(2026, 8, 29, 12, 0, 0, tzinfo=timezone.utc)

INSTALLATIONS = [
    {"id": 41, "account": {"login": "Initech"}, "created_at": "2026-07-02T09:00:00Z",
     "repository_selection": "all", "suspended_at": None},
    {"id": 42, "account": {"login": "umbrella"}, "created_at": "2026-05-01T09:00:00Z",
     "repository_selection": "selected", "suspended_at": "2026-08-01T09:00:00Z"},
]


def test_the_index_is_case_insensitive_because_records_are_hand_written():
    index = installation_index(INSTALLATIONS)
    assert index["initech"]["id"] == 41
    assert index["umbrella"]["suspended"] is True
    assert index["initech"]["suspended"] is False
    assert installation_index([{"id": 1}]) == {}


def test_the_probe_says_what_a_404_does_and_does_not_mean():
    state, detail = probe_state(404)
    assert state == "no-installation"
    assert ABSENCE_MEANING in detail
    assert probe_state(200)[0] == "installed"
    assert probe_state(401)[0] == "unreadable"


def test_a_product_that_says_connected_against_nothing_is_the_headline():
    state, detail = reconcile(
        {"account": "globex", "connected": True, "started_at": "2026-08-10T00:00:00Z"},
        None, NOW)
    assert state == "false-connected"
    assert "globex" in detail
    assert ABSENCE_MEANING in detail
    assert actionable(state) is True


def test_a_fresh_request_and_a_forgotten_one_are_different_sentences():
    fresh, detail = reconcile(
        {"account": "globex", "connected": False,
         "started_at": "2026-08-27T12:00:00Z"}, None, NOW)
    assert fresh == "awaiting-approval"
    assert "may simply not have looked yet" in detail
    stale, detail = reconcile(
        {"account": "globex", "connected": False,
         "started_at": "2026-07-01T12:00:00Z"}, None, NOW)
    assert stale == "stale-request"
    assert "notified once" in detail


def test_the_reconciliation_runs_in_the_other_direction_too():
    state, detail = reconcile({"account": "initech", "connected": False},
                              installation_index(INSTALLATIONS)["initech"], NOW)
    assert state == "unrecorded-installation"
    assert "nothing in your product noticed" in detail


def test_a_suspended_installation_is_handed_to_its_own_note():
    # Telling somebody to chase an approval that already happened is worse than
    # saying nothing, so this never counts as a pending request.
    state, detail = reconcile({"account": "umbrella", "connected": True},
                              installation_index(INSTALLATIONS)["umbrella"], NOW)
    assert state == "installed-but-suspended"
    assert "already happened" in detail
    assert "unsuspend" in printed_step(state, "umbrella")


def test_agreement_in_either_direction_is_quiet():
    assert reconcile({"account": "initech", "connected": True},
                     installation_index(INSTALLATIONS)["initech"], NOW)[0] == (
        "agreed-connected")
    assert reconcile({"account": "globex", "connected": False}, None, NOW)[0] == (
        "agreed-disconnected")
    assert actionable("agreed-connected") is False


def test_an_unaged_request_does_not_pretend_to_know_when_it_started():
    state, detail = request_age_state(None)
    assert state == "age-unknown"
    assert "does not say when the flow started" in detail
    assert age_days(None, NOW) is None
    assert age_days("not-a-date", NOW) is None
    assert round(age_days("2026-08-27T12:00:00Z", NOW), 1) == 2.0


def test_the_step_is_addressed_to_a_human_and_never_taken():
    step = printed_step("false-connected", "globex")
    assert "an owner of globex has to approve" in step
    assert "Nothing here requests or approves anything" in step
    assert printed_step("agreed-connected", "globex") == "nothing for this account."


def test_the_product_repair_is_about_the_state_machine_not_the_api():
    fix = product_repair(["false-connected", "agreed-connected"])
    assert "stop rendering a completed flow as a connection" in fix
    assert "on a schedule" in fix
    assert "expires by neglect" in product_repair(["stale-request"])
    assert product_repair(["agreed-connected"]).startswith("nothing")


def test_the_cost_counts_the_list_pages_and_one_probe_each():
    assert read_cost([{"account": "a"}, {"account": "b"}], 1) == 4
    assert read_cost([{"account": "a"}], 3) == 5
    assert read_cost([], 1) == 2
''',
"test_js_file": "github-app-installation-pending.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  ABSENCE_MEANING, actionable, ageDays, installationIndex, printedStep,
  probeState, productRepair, readCost, reconcile, requestAgeState,
} from './github-app-installation-pending.mjs';

const NOW = new Date('2026-08-29T12:00:00Z');

const INSTALLATIONS = [
  {
    id: 41,
    account: { login: 'Initech' },
    created_at: '2026-07-02T09:00:00Z',
    repository_selection: 'all',
    suspended_at: null,
  },
  {
    id: 42,
    account: { login: 'umbrella' },
    created_at: '2026-05-01T09:00:00Z',
    repository_selection: 'selected',
    suspended_at: '2026-08-01T09:00:00Z',
  },
];

test('the index is case insensitive because records are hand written', () => {
  const index = installationIndex(INSTALLATIONS);
  assert.equal(index.initech.id, 41);
  assert.equal(index.umbrella.suspended, true);
  assert.equal(index.initech.suspended, false);
  assert.deepEqual(installationIndex([{ id: 1 }]), {});
});

test('the probe says what a 404 does and does not mean', () => {
  const [state, detail] = probeState(404);
  assert.equal(state, 'no-installation');
  assert.ok(detail.includes(ABSENCE_MEANING));
  assert.equal(probeState(200)[0], 'installed');
  assert.equal(probeState(401)[0], 'unreadable');
});

test('a product that says connected against nothing is the headline', () => {
  const [state, detail] = reconcile(
    { account: 'globex', connected: true, started_at: '2026-08-10T00:00:00Z' },
    null, NOW,
  );
  assert.equal(state, 'false-connected');
  assert.match(detail, /globex/);
  assert.ok(detail.includes(ABSENCE_MEANING));
  assert.equal(actionable(state), true);
});

test('a fresh request and a forgotten one are different sentences', () => {
  const [fresh, freshDetail] = reconcile(
    { account: 'globex', connected: false, started_at: '2026-08-27T12:00:00Z' },
    null, NOW,
  );
  assert.equal(fresh, 'awaiting-approval');
  assert.match(freshDetail, /may simply not have looked yet/);
  const [stale, staleDetail] = reconcile(
    { account: 'globex', connected: false, started_at: '2026-07-01T12:00:00Z' },
    null, NOW,
  );
  assert.equal(stale, 'stale-request');
  assert.match(staleDetail, /notified once/);
});

test('the reconciliation runs in the other direction too', () => {
  const [state, detail] = reconcile(
    { account: 'initech', connected: false },
    installationIndex(INSTALLATIONS).initech, NOW,
  );
  assert.equal(state, 'unrecorded-installation');
  assert.match(detail, /nothing in your product noticed/);
});

test('a suspended installation is handed to its own note', () => {
  const [state, detail] = reconcile(
    { account: 'umbrella', connected: true },
    installationIndex(INSTALLATIONS).umbrella, NOW,
  );
  assert.equal(state, 'installed-but-suspended');
  assert.match(detail, /already happened/);
  assert.match(printedStep(state, 'umbrella'), /unsuspend/);
});

test('agreement in either direction is quiet', () => {
  assert.equal(reconcile({ account: 'initech', connected: true },
    installationIndex(INSTALLATIONS).initech, NOW)[0], 'agreed-connected');
  assert.equal(reconcile({ account: 'globex', connected: false }, null, NOW)[0],
    'agreed-disconnected');
  assert.equal(actionable('agreed-connected'), false);
});

test('an unaged request does not pretend to know when it started', () => {
  const [state, detail] = requestAgeState(null);
  assert.equal(state, 'age-unknown');
  assert.match(detail, /does not say when the flow started/);
  assert.equal(ageDays(null, NOW), null);
  assert.equal(ageDays('not-a-date', NOW), null);
  assert.equal(Math.round(ageDays('2026-08-27T12:00:00Z', NOW) * 10) / 10, 2.0);
});

test('the step is addressed to a human and never taken', () => {
  const step = printedStep('false-connected', 'globex');
  assert.match(step, /an owner of globex has to approve/);
  assert.match(step, /Nothing here requests or approves anything/);
  assert.equal(printedStep('agreed-connected', 'globex'), 'nothing for this account.');
});

test('the product repair is about the state machine not the api', () => {
  const fix = productRepair(['false-connected', 'agreed-connected']);
  assert.match(fix, /stop rendering a completed flow as a connection/);
  assert.match(fix, /on a schedule/);
  assert.match(productRepair(['stale-request']), /expires by neglect/);
  assert.match(productRepair(['agreed-connected']), /^nothing/);
});

test('the cost counts the list pages and one probe each', () => {
  assert.equal(readCost([{ account: 'a' }, { account: 'b' }], 1), 4);
  assert.equal(readCost([{ account: 'a' }], 3), 5);
  assert.equal(readCost([], 1), 2);
});
''',
"faq": [
 ("Can the script just look up the pending request and tell me it is pending?",
  "No, and that limit is the reason the note is shaped the way it is. There is no endpoint that lists an App's pending installation requests, so from the App's side a pending account is indistinguishable from one that declined, one that closed the tab halfway and one that never started. What you do have is the moment your product recorded the beginning of a flow. Reconciling that against <code>GET /app/installations</code> is the method, not a workaround for a missing call."),
 ("How is this different from the App not being installed on a repository?",
  "Scope. That case is an installation that exists on the account but does not include the repository you asked about, and <code>GET /repos/{owner}/{repo}/installation</code> settles it. This is the account-level absence: there is no installation, so there are no selected repositories to be outside of. The two produce the same 404 and have completely different repairs — one is a repository being added to an existing installation, the other is an owner approving something they have not seen."),
 ("Why does the user see a success page if nothing was installed?",
  "Because from the user's side the flow did succeed: they authorised the App and GitHub recorded their request. What follows is out of their hands, and the confirmation is not lying so much as describing a different event from the one your product cares about. This is exactly why the reconciliation belongs on a schedule rather than in the callback: the callback fires on the user's action, and the state you actually need changes later, if at all, when somebody else acts."),
 ("Some accounts have four pending requests. Does that make approval more likely?",
  "It makes it less likely, in practice. Each attempt notifies the owners once, and repeated identical requests read as noise rather than urgency. It happens because &ldquo;uninstall and reinstall&rdquo; is the standard advice for a broken integration and it is unavailable here — there is nothing installed to remove — so the user does the only thing they can, which is start again. Showing the pending state, and who has to approve it, is what stops that loop."),
 ("Should the script request the installation itself if it can see one is missing?",
  "Never, and not only because this section is read-only. Approving an App is a decision about what gets access to an organization's code, made by somebody accountable for that organization. A tool that asks on the user's behalf turns a considered approval into a notification storm, and one that could approve would be a privilege-escalation path wearing a diagnostic's clothes. The script reads, reconciles, and prints the sentence for a human to act on."),
],
"related": [
 ("/github/app-not-installed-on-repo/", "The other absence: installed, but not on that repository"),
 ("/github/app-installation-id-hardcoded/", "When the installation exists and the stored id does not match it"),
 ("/github/installation-suspended/", "When the installation exists and has been switched off"),
],
"citations": [CITE_REQUESTING_APP, CITE_APPS, CITE_INSTALLING_APP, CITE_APP_AUTH],
},
]
