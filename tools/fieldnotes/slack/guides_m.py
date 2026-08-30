#!/usr/bin/env python3
"""/slack/ field notes, batch M - the writing.

Four notes about delivery: whether a call is allowed to leave your network at
all, whether an event was ever asked for, whether an event that was asked for
can be handed over, and what an event actually is once it arrives.

One is the only note in the section where nothing about the app is wrong. The
token is valid, the scopes are right, the bot is in the channel, and an
organisation policy refuses the call because of the address it came from. Two
are the two halves of the same 2x2 and are deliberately written as a pair: an
app with zero subscriptions receives nothing because nobody ever asked, and an
app with a subscription whose scope is missing receives everything except that
one event, silently, with no error anywhere to read. And one is about the
payload, where a single `message` event turns out to be nine different kinds of
thing wearing one name.

Read only throughout. Two of these scripts read an app manifest, which is a
read of the app configuration and not a change to it, and the note says plainly
which credential that needs and what happens when you do not have it.
"""

CITE_EVENTS = ("Events API - Slack Docs", "https://docs.slack.dev/apis/events-api/")
CITE_EVENT_TYPES = ("Event types - Slack Docs", "https://docs.slack.dev/reference/events/")
CITE_MESSAGE_EVENT = ("message event reference - Slack Docs",
                      "https://docs.slack.dev/reference/events/message")
CITE_APP_MENTION = ("app_mention event reference - Slack Docs",
                    "https://docs.slack.dev/reference/events/app_mention")
CITE_SCOPES = ("Scopes - Slack Docs", "https://docs.slack.dev/reference/scopes/")
CITE_MANIFEST = ("apps.manifest.export method reference - Slack Docs",
                 "https://docs.slack.dev/reference/methods/apps.manifest.export")
CITE_AUTH_TEST = ("auth.test method reference - Slack Docs",
                  "https://docs.slack.dev/reference/methods/auth.test")
CITE_POSTMESSAGE = ("chat.postMessage method reference - Slack Docs",
                    "https://docs.slack.dev/reference/methods/chat.postMessage")
CITE_RATE_LIMITS = ("Rate limits - Slack Docs",
                    "https://docs.slack.dev/apis/web-api/rate-limits")
CITE_GRID = ("Enterprise Grid - Slack Docs", "https://docs.slack.dev/enterprise-grid/")
CITE_CONV_HISTORY = ("conversations.history method reference - Slack Docs",
                     "https://docs.slack.dev/reference/methods/conversations.history")
CITE_RETRIEVING = ("Retrieving messages - Slack Docs",
                   "https://docs.slack.dev/messaging/retrieving-messages")

GUIDES = []

GUIDES.append({
"slug": "accesslimited-ip-allowlist",
"title": "accesslimited: the right token from the wrong network",
"description": "Nothing about the app is wrong. Grid IP allowlisting refuses the call by network origin, and two vantage points prove it before anyone touches a scope.",
"h1": "accesslimited: the right token from the wrong network",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack accesslimited", "slack ip allowlist api",
             "slack enterprise grid ip restriction", "slack api works locally fails in production",
             "slack invalid_auth from server"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The token works. Someone pastes the same <code>curl</code> into their laptop terminal and it comes back <code>ok: true</code>, in front of witnesses. The identical command in the production container answers <code>{\"ok\": false, \"error\": \"accesslimited\"}</code>, and the deploy that shipped an hour earlier gets blamed for it.</p><p>This is the one note in this section where nothing about the app is wrong. Not the scopes, not the install, not the channel, not the code. Somebody added an IP range to an organisation policy, or an autoscaler replaced a NAT gateway, and Slack is refusing the call on the strength of where it came from.",
"short_answer": """<p><code>accesslimited</code> means "access to this method is limited on the current network". An Enterprise Grid administrator can restrict API access to a set of IP ranges, and a call whose egress address falls outside them is refused regardless of how valid the token is or how complete its scopes are.</p>
<p>The diagnosis needs two things a single failing call cannot give you. First, <strong>your own public egress address</strong>, which is not the address of the host and is frequently not the address anybody wrote down: the script fetches it from a plain-text echo service, without your Slack token attached. Second, <strong>a second vantage point</strong>. The same token succeeding from one network and returning <code>accesslimited</code> from another is conclusive; a token that fails from everywhere is a credential problem wearing an unusual error string. The script below records one vantage point at a time and combines it with the one you supply from the other network.</p>""",
"problem": """<p>The shape of this failure is what makes it expensive. It is total: every method, every channel, every call from that host. It is environment-specific: staging is fine, production is not, or the reverse. And it appeared without a deploy, which means the first hour of the investigation is spent reading a diff that has nothing in it.</p>
<p>So the team reaches for the things that usually explain a total failure. The token gets rotated, which does nothing. The app gets reinstalled, which does nothing and costs an approval. Scopes get added, which does nothing and leaves the app holding more permission than it needs afterwards. Every one of those is a reasonable guess and every one of them is aimed at the app, and the app is not what changed. What changed is that the cluster moved to a new availability zone, or the platform team replaced a NAT gateway, or a Grid admin tightened an allowlist on Tuesday and told a distribution list that does not include you.</p>
<p>It gets worse when the error is not <code>accesslimited</code>. Slack's own documentation notes that a request coming from a disallowed address can surface as <code>invalid_auth</code> instead, and <code>invalid_auth</code> reads unambiguously as "your token is bad". A team that sees it will rotate the credential, and the rotation will not help, and the second rotation will not help either. The only thing that separates those two readings is running the same credential from somewhere else.</p>""",
"why": """<p><strong>The policy lives above the app, and the app cannot read it.</strong> There is no Web API method that returns the organisation's allowlist. A read-scoped token cannot enumerate the ranges, cannot tell you when they changed, and cannot tell you who changed them. What it can do is establish the two facts that make the case: this address, this outcome.</p>
<p><strong>Your egress address is not a property of your code.</strong> It belongs to the NAT gateway, the load balancer, the VPN, or the office router, and in most cloud setups it can change without anybody deploying anything. That is why the finding has to name the address observed at the moment of the failing call rather than the address in the runbook.</p>
<p><strong>One vantage point cannot distinguish a network refusal from a bad token.</strong> A single failing call is compatible with both. Two calls with the same credential from two networks, with one succeeding, is compatible with exactly one. The script is built around that comparison because the comparison is the whole proof.</p>
<p><strong><code>invalid_auth</code> is ambiguous here and should be reported as ambiguous.</strong> A detector that maps it straight to "credential" will send a team to rotate a perfectly good token. This one returns a distinct state and says what would resolve it, which is the second vantage point rather than a new secret.</p>
<p><strong>The repair belongs to two teams, and both need the same number.</strong> The Grid admin needs a CIDR to add. The platform team needs to pin egress so the CIDR keeps being true next month. A finding that says "IP allowlisting" without naming an address makes both of those conversations start from scratch.</p>""",
"steps": [
 {"h": "Read the body, not the status line",
  "body": """<p><code>accesslimited</code> arrives as <code>HTTP 200</code> with <code>ok: false</code>, like every other Slack failure. A client that trusts the status code sees a healthy response and an empty result. The script asserts on <code>body.ok</code> and records <code>body.error</code> verbatim before it does anything else.</p>"""},
 {"h": "Observe your own egress address, without sending the token to do it",
  "body": """<p>The script fetches a plain-text echo service on a bare request with no Slack credential attached, deliberately: the address is public information and the token is not, and there is no reason for one to travel with the other. Point <code>--egress-url</code> at your own echo endpoint if you would rather not use a third party at all.</p>"""},
 {"h": "Classify the refusal before you interpret it",
  "body": """<p><code>refusal_kind</code> sorts the answer into <code>network</code>, <code>ambiguous</code>, <code>credential</code>, <code>scope</code> or <code>clear</code>. The value of the classifier is mostly in refusing to collapse <code>invalid_auth</code> into the credential bucket, because that collapse is what costs afternoons.</p>"""},
 {"h": "Hold the address against the allowlist you were given",
  "body": """<p>If somebody can tell you the ranges, pass them with <code>--allow</code> and <code>cidr_verdict</code> does the arithmetic. An address outside every supplied range turns a suspicion into a sentence with a number in it. A malformed range is reported as malformed rather than quietly skipped.</p>"""},
 {"h": "Run it again from a second network and feed the result back in",
  "body": """<p>Run the script on the failing host and on a laptop. Take the second run's address and error and pass them as <code>--peer-egress</code> and <code>--peer-error</code>. <code>vantage_verdict</code> combines them, and <code>confirmed</code> is the only state that closes this case rather than suggesting a next step.</p>"""},
 {"h": "Print a repair addressed to the two people who can act on it",
  "body": """<p>The Grid admin adds the CIDR under Organization settings, Security, IP allowlisting. The platform team pins egress to a stable NAT gateway so the entry stays true. The script prints both, with the observed address in them, so neither conversation starts by asking what the address is.</p>"""},
],
"verify": """<p>Once the CIDR is allowlisted, re-run on the host that was failing. The address should be unchanged and the outcome should not be.</p>
<pre><code class="language-bash">python3 slack_egress_allowlist.py --allow 203.0.113.0/24 --allow 198.51.100.7/32
# egress     observed       203.0.113.44 via https://checkip.amazonaws.com
# auth.test  clear          ok: true, U0APPBOT11 in acme
# allowlist  inside         203.0.113.44 is inside 203.0.113.0/24
# vantage    clear          this network is not being refused</code></pre>""",
"code_intro": "One authenticated GET, one unauthenticated one, and three pure functions that carry the whole argument. <code>refusal_kind</code> is a five-way sort whose only interesting row is <code>invalid_auth</code>, which it refuses to call a credential problem. <code>cidr_verdict</code> is IPv4 arithmetic against the ranges you were handed. <code>vantage_verdict</code> is the proof: two observations of one token from two networks, reduced to whether this case is closed or still a suspicion.",
"py_file": "slack_egress_allowlist.py",
"py": '''"""Decide whether Slack is refusing this host by network origin.

Read only. One auth.test, and one unauthenticated GET to an echo service to
learn the caller's public egress address. Nothing is changed anywhere: an IP
allowlist lives in Enterprise Grid organisation settings and no API method can
edit it, so this reports the address, the refusal and the comparison, and
prints the entry an administrator would add.
"""
import argparse
import ipaddress
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_egress_allowlist")

API = "https://slack.com/api/"

# Errors that are unambiguously about the credential rather than the network.
# invalid_auth is deliberately not in here: Slack documents that a request from
# a disallowed address can surface as invalid_auth, so mapping it to
# "credential" is how a team ends up rotating a working token twice.
CREDENTIAL_ERRORS = {
    "not_authed", "token_revoked", "token_expired",
    "account_inactive", "not_allowed_token_type",
}

# invalid_auth sits in here as well as outside CREDENTIAL_ERRORS on purpose: it
# is a credential reading when both networks agree, and an allowlist reading
# when they do not.
CREDENTIAL_KINDS = {"credential", "ambiguous"}


def refusal_kind(ok, error):
    """Sort one Slack answer into the kind of refusal it is. Pure.

    Returns (kind, detail). The kinds are clear, network, ambiguous,
    credential, scope and other, and the one that earns its place is
    ambiguous, because collapsing it into credential is the mistake this
    whole note exists to prevent.
    """
    if ok is True:
        return ("clear", "the call succeeded, so this network is not being refused")
    err = str(error or "").strip()
    if not err:
        return ("other", "ok was not true and no error string came back, which is "
                         "worth capturing verbatim before anything is concluded")
    if err == "accesslimited":
        return ("network", "accesslimited: the method is limited on the current "
                           "network, which is an organisation policy about where "
                           "the call came from and not about the token")
    if err == "invalid_auth":
        return ("ambiguous", "invalid_auth usually means a bad token, and Slack "
                             "documents that a request from a disallowed address "
                             "can surface here too. A second vantage point "
                             "separates them; rotating the token does not")
    if err in CREDENTIAL_ERRORS:
        return ("credential", "%s is about the credential itself, not the network" % err)
    if err == "missing_scope":
        return ("scope", "missing_scope is a grant problem and has its own note; "
                         "the token reached Slack and was understood")
    return ("other", "%s is neither a network nor a credential refusal" % err)


def cidr_verdict(ip, allowlist):
    """Hold an observed egress address against the ranges you were given. Pure.

    Returns (verdict, detail). IPv4 only and says so: Slack's allowlists are
    expressed as IPv4 ranges, and a guess about an IPv6 address would be a
    confident wrong answer in a report somebody is going to act on.
    """
    text = str(ip or "").strip()
    if not text:
        return ("unknown", "no egress address was observed, so there is nothing "
                           "to hold against an allowlist")
    if ":" in text:
        return ("unsupported", "%s is IPv6 and this check does IPv4 ranges only; "
                               "compare it against the policy by hand" % text)
    try:
        addr = ipaddress.IPv4Address(text)
    except ValueError:
        return ("malformed", "%s is not an address this check can parse" % text)

    ranges, skipped = [], []
    for entry in allowlist or []:
        raw = str(entry or "").strip()
        if not raw:
            continue
        try:
            ranges.append(ipaddress.IPv4Network(raw, strict=False))
        except ValueError:
            skipped.append(raw)

    note = ""
    if skipped:
        note = "; %d supplied range(s) could not be parsed and were not checked: %s" % (
            len(skipped), ", ".join(skipped))
    if not ranges:
        return ("unlisted", "%s observed, and no usable allowlist was supplied, so "
                            "the address is reported rather than judged%s" % (text, note))
    for net in ranges:
        if addr in net:
            return ("inside", "%s is inside %s%s" % (text, net.with_prefixlen, note))
    return ("outside", "%s is outside all %d supplied range(s): %s%s" % (
        text, len(ranges), ", ".join(n.with_prefixlen for n in ranges), note))


def vantage_verdict(here, there):
    """Combine two observations of one token from two networks. Pure.

    Each side is a dict with kind and egress. One failing call proves nothing;
    the same credential succeeding from one address and refused from another
    proves this exactly.
    """
    mine = (here or {}).get("kind") or "unknown"
    if not there or not (there.get("kind") or "").strip():
        if mine == "network":
            return ("unconfirmed", "accesslimited from %s, and no second vantage "
                                   "point was supplied. Run this again from another "
                                   "network to turn a strong reading into a proof"
                    % ((here or {}).get("egress") or "an unknown address"))
        if mine == "ambiguous":
            return ("unresolved", "invalid_auth from one network only. This is the "
                                  "state that gets a good token rotated; run the "
                                  "same token from elsewhere before touching it")
        if mine == "clear":
            return ("clear", "this network is not being refused")
        return ("unconfirmed", "one vantage point is not enough to attribute this")

    theirs = there.get("kind")
    a = (here or {}).get("egress") or "an unknown address"
    b = there.get("egress") or "an unknown address"
    if mine in ("network", "ambiguous") and theirs == "clear":
        return ("confirmed", "the same token is refused from %s and succeeds from "
                             "%s. That is an IP restriction and not a credential "
                             "problem; %s is the address to allowlist" % (a, b, a))
    if mine == "network" and theirs in ("network", "ambiguous"):
        return ("both-refused", "both %s and %s are refused. Either the allowlist "
                                "excludes both, or it was emptied; ask the Grid "
                                "admin for the current ranges before changing "
                                "anything on the app" % (a, b))
    if mine in CREDENTIAL_KINDS and theirs in CREDENTIAL_KINDS:
        return ("credential", "the same failure from two networks is the credential, "
                              "not the allowlist")
    if mine == "clear" and theirs in ("network", "ambiguous"):
        return ("confirmed", "this network is fine and %s is refused; %s is the "
                             "address to allowlist" % (b, b))
    if mine == "clear" and theirs == "clear":
        return ("clear", "both vantage points succeeded")
    return ("mixed", "the two vantage points disagree in a way this script will not "
                     "guess at: %s here, %s there" % (mine, theirs))


def observe_egress(url):
    """Fetch the caller's public address from a plain-text echo service.

    Sent with no Authorization header on purpose. The address is public and the
    Slack token is not, and there is no reason for the two to travel together.
    """
    if not url:
        return ""
    try:
        r = requests.get(url, timeout=10)
        first = (r.text or "").strip().split()
        return first[0] if first else ""
    except requests.RequestException as exc:
        log.info("egress     unknown        %s did not answer (%s)", url, exc)
        return ""


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN",
                    help="environment variable holding the token to test")
    ap.add_argument("--egress-url", default="https://checkip.amazonaws.com",
                    help="plain-text echo service; pass an empty string to skip it")
    ap.add_argument("--allow", action="append", default=[],
                    help="an allowlisted CIDR you were given; repeatable")
    ap.add_argument("--peer-egress", default="",
                    help="the egress address this script reported on another network")
    ap.add_argument("--peer-error", default="",
                    help="the Slack error from that other network, or ok for success")
    args = ap.parse_args()

    token = os.environ.get(args.token_env)
    if not token:
        log.error("set %s; any read scope is enough, the point is the network",
                  args.token_env)
        return 2

    egress = observe_egress(args.egress_url)
    if egress:
        log.info("egress     observed       %s via %s", egress, args.egress_url)
    else:
        log.info("egress     unobserved     no address; the finding will be "
                 "weaker for it")

    r = requests.get(API + "auth.test", timeout=30,
                     headers={"Authorization": "Bearer " + token})
    body = r.json()
    kind, why = refusal_kind(body.get("ok") is True, body.get("error"))
    (log.info if kind == "clear" else log.warning)("auth.test  %-14s %s", kind, why)
    if kind == "clear":
        log.info("identity   %s in %s", body.get("user_id"), body.get("team"))

    verdict, detail = cidr_verdict(egress, args.allow)
    (log.warning if verdict == "outside" else log.info)(
        "allowlist  %-14s %s", verdict, detail)

    peer = None
    if args.peer_error:
        peer_kind, _ = refusal_kind(args.peer_error.strip().lower() == "ok",
                                    "" if args.peer_error.strip().lower() == "ok"
                                    else args.peer_error)
        peer = {"kind": peer_kind, "egress": args.peer_egress}
    proof, proof_detail = vantage_verdict({"kind": kind, "egress": egress}, peer)
    (log.info if proof == "clear" else log.warning)(
        "vantage    %-14s %s", proof, proof_detail)

    if kind in ("network", "ambiguous") or verdict == "outside":
        log.warning("  repair: ask the Grid admin to add %s to the API allowlist "
                    "under Organization settings, Security, IP allowlisting",
                    ("%s/32" % egress) if egress else "this host's egress CIDR")
        log.warning("  repair: pin egress to a stable NAT gateway or static address "
                    "so the allowlist entry stays true after the next scale event")
        log.warning("  repair: do not rotate the token or add scopes for this; "
                    "neither changes where the request came from")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-egress-allowlist.mjs",
"js": '''/**
 * Decide whether Slack is refusing this host by network origin.
 *
 * Read only. One auth.test, and one unauthenticated GET to an echo service to
 * learn the caller's public egress address. An IP allowlist lives in
 * Enterprise Grid organisation settings and no API method can edit it, so this
 * reports the address, the refusal and the comparison, and prints the entry an
 * administrator would add.
 */

const API = 'https://slack.com/api/';

// invalid_auth is deliberately absent: Slack documents that a request from a
// disallowed address can surface there, so treating it as a credential fault
// is how a working token gets rotated twice.
const CREDENTIAL_ERRORS = new Set([
  'not_authed', 'token_revoked', 'token_expired',
  'account_inactive', 'not_allowed_token_type',
]);

const CREDENTIAL_KINDS = new Set(['credential', 'ambiguous']);

/**
 * Sort one Slack answer into the kind of refusal it is. Pure.
 * The kind that earns its place is ambiguous.
 */
export function refusalKind(ok, error) {
  if (ok === true) {
    return ['clear', 'the call succeeded, so this network is not being refused'];
  }
  const err = String(error ?? '').trim();
  if (!err) {
    return ['other', 'ok was not true and no error string came back, which is worth ' +
      'capturing verbatim before anything is concluded'];
  }
  if (err === 'accesslimited') {
    return ['network', 'accesslimited: the method is limited on the current network, ' +
      'which is an organisation policy about where the call came from and not ' +
      'about the token'];
  }
  if (err === 'invalid_auth') {
    return ['ambiguous', 'invalid_auth usually means a bad token, and Slack documents ' +
      'that a request from a disallowed address can surface here too. A second ' +
      'vantage point separates them; rotating the token does not'];
  }
  if (CREDENTIAL_ERRORS.has(err)) {
    return ['credential', `${err} is about the credential itself, not the network`];
  }
  if (err === 'missing_scope') {
    return ['scope', 'missing_scope is a grant problem and has its own note; the ' +
      'token reached Slack and was understood'];
  }
  return ['other', `${err} is neither a network nor a credential refusal`];
}

function toInt(ip) {
  const parts = ip.split('.');
  if (parts.length !== 4) return null;
  let out = 0;
  for (const part of parts) {
    if (!/^\\d{1,3}$/.test(part)) return null;
    const n = Number(part);
    if (n > 255) return null;
    out = out * 256 + n;
  }
  return out;
}

function parseCidr(raw) {
  const [base, len] = raw.split('/');
  const addr = toInt(String(base ?? '').trim());
  if (addr === null) return null;
  const bits = len === undefined ? 32 : Number(len);
  if (!Number.isInteger(bits) || bits < 0 || bits > 32) return null;
  const mask = bits === 0 ? 0 : (2 ** 32 - 2 ** (32 - bits));
  return { network: addr - (addr % (2 ** (32 - bits))), mask, bits, label: `${base}/${bits}` };
}

/**
 * Hold an observed egress address against the ranges you were given. Pure.
 * IPv4 only and says so, because a guess about an IPv6 address would be a
 * confident wrong answer in a report somebody is going to act on.
 */
export function cidrVerdict(ip, allowlist) {
  const text = String(ip ?? '').trim();
  if (!text) {
    return ['unknown', 'no egress address was observed, so there is nothing to hold ' +
      'against an allowlist'];
  }
  if (text.includes(':')) {
    return ['unsupported', `${text} is IPv6 and this check does IPv4 ranges only; ` +
      'compare it against the policy by hand'];
  }
  const addr = toInt(text);
  if (addr === null) {
    return ['malformed', `${text} is not an address this check can parse`];
  }

  const ranges = [];
  const skipped = [];
  for (const entry of allowlist ?? []) {
    const raw = String(entry ?? '').trim();
    if (!raw) continue;
    const net = parseCidr(raw);
    if (net) ranges.push(net); else skipped.push(raw);
  }

  const note = skipped.length
    ? `; ${skipped.length} supplied range(s) could not be parsed and were not ` +
      `checked: ${skipped.join(', ')}`
    : '';
  if (!ranges.length) {
    return ['unlisted', `${text} observed, and no usable allowlist was supplied, so ` +
      `the address is reported rather than judged${note}`];
  }
  for (const net of ranges) {
    const size = 2 ** (32 - net.bits);
    if (addr >= net.network && addr < net.network + size) {
      return ['inside', `${text} is inside ${net.label}${note}`];
    }
  }
  return ['outside', `${text} is outside all ${ranges.length} supplied range(s): ` +
    `${ranges.map((n) => n.label).join(', ')}${note}`];
}

/**
 * Combine two observations of one token from two networks. Pure.
 * One failing call proves nothing; the same credential succeeding from one
 * address and refused from another proves this exactly.
 */
export function vantageVerdict(here, there) {
  const mine = here?.kind || 'unknown';
  if (!there || !String(there.kind ?? '').trim()) {
    if (mine === 'network') {
      return ['unconfirmed', `accesslimited from ${here?.egress || 'an unknown address'}` +
        ', and no second vantage point was supplied. Run this again from another ' +
        'network to turn a strong reading into a proof'];
    }
    if (mine === 'ambiguous') {
      return ['unresolved', 'invalid_auth from one network only. This is the state ' +
        'that gets a good token rotated; run the same token from elsewhere before ' +
        'touching it'];
    }
    if (mine === 'clear') return ['clear', 'this network is not being refused'];
    return ['unconfirmed', 'one vantage point is not enough to attribute this'];
  }

  const theirs = there.kind;
  const a = here?.egress || 'an unknown address';
  const b = there.egress || 'an unknown address';
  if ((mine === 'network' || mine === 'ambiguous') && theirs === 'clear') {
    return ['confirmed', `the same token is refused from ${a} and succeeds from ${b}. ` +
      `That is an IP restriction and not a credential problem; ${a} is the address ` +
      'to allowlist'];
  }
  if (mine === 'network' && (theirs === 'network' || theirs === 'ambiguous')) {
    return ['both-refused', `both ${a} and ${b} are refused. Either the allowlist ` +
      'excludes both, or it was emptied; ask the Grid admin for the current ranges ' +
      'before changing anything on the app'];
  }
  if (CREDENTIAL_KINDS.has(mine) && CREDENTIAL_KINDS.has(theirs)) {
    return ['credential', 'the same failure from two networks is the credential, not ' +
      'the allowlist'];
  }
  if (mine === 'clear' && (theirs === 'network' || theirs === 'ambiguous')) {
    return ['confirmed', `this network is fine and ${b} is refused; ${b} is the ` +
      'address to allowlist'];
  }
  if (mine === 'clear' && theirs === 'clear') {
    return ['clear', 'both vantage points succeeded'];
  }
  return ['mixed', 'the two vantage points disagree in a way this script will not ' +
    `guess at: ${mine} here, ${theirs} there`];
}

async function observeEgress(url) {
  if (!url) return '';
  try {
    // No Authorization header on purpose: the address is public, the token is not.
    const res = await fetch(url);
    const text = (await res.text()).trim().split(/\\s+/);
    return text[0] ?? '';
  } catch (err) {
    console.log(`egress     unknown        ${url} did not answer (${err.message})`);
    return '';
  }
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

async function main() {
  const args = process.argv.slice(2);
  const tokenEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
  const token = process.env[tokenEnv];
  if (!token) {
    console.error(`set ${tokenEnv}; any read scope is enough, the point is the network`);
    process.exitCode = 2;
    return;
  }
  const egressUrl = arg(args, '--egress-url', 'https://checkip.amazonaws.com');

  const egress = await observeEgress(egressUrl);
  if (egress) console.log(`egress     observed       ${egress} via ${egressUrl}`);
  else console.log('egress     unobserved     no address; the finding will be weaker for it');

  const res = await fetch(`${API}auth.test`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const body = await res.json();
  const [kind, why] = refusalKind(body.ok === true, body.error);
  (kind === 'clear' ? console.log : console.warn)(`auth.test  ${kind.padEnd(14)} ${why}`);
  if (kind === 'clear') console.log(`identity   ${body.user_id} in ${body.team}`);

  const [verdict, detail] = cidrVerdict(egress, argAll(args, '--allow'));
  (verdict === 'outside' ? console.warn : console.log)(
    `allowlist  ${verdict.padEnd(14)} ${detail}`);

  const peerError = String(arg(args, '--peer-error', '') ?? '').trim();
  let peer = null;
  if (peerError) {
    const ok = peerError.toLowerCase() === 'ok';
    const [peerKind] = refusalKind(ok, ok ? '' : peerError);
    peer = { kind: peerKind, egress: arg(args, '--peer-egress', '') };
  }
  const [proof, proofDetail] = vantageVerdict({ kind, egress }, peer);
  (proof === 'clear' ? console.log : console.warn)(
    `vantage    ${proof.padEnd(14)} ${proofDetail}`);

  if (kind === 'network' || kind === 'ambiguous' || verdict === 'outside') {
    console.warn(`  repair: ask the Grid admin to add ${egress ? `${egress}/32` : "this host's egress CIDR"} ` +
      'to the API allowlist under Organization settings, Security, IP allowlisting');
    console.warn('  repair: pin egress to a stable NAT gateway or static address so the ' +
      'allowlist entry stays true after the next scale event');
    console.warn('  repair: do not rotate the token or add scopes for this; neither ' +
      'changes where the request came from');
    process.exitCode = 1;
  }
}

// Only run when invoked directly, so importing this module in the tests does
// not execute main() and fail the file on a missing token.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Two assertions decide whether this script is worth running. The first is that <code>invalid_auth</code> comes back as <code>ambiguous</code> and never as <code>credential</code>, because the whole cost of this failure is the rotation that gets done instead of the second run. The second is that one vantage point is never allowed to say <code>confirmed</code>: a single refused call is compatible with a bad token, and the script has to keep saying so until somebody supplies the other half.",
"test_py_file": "test_slack_egress_allowlist.py",
"test_py": '''from slack_egress_allowlist import cidr_verdict, refusal_kind, vantage_verdict


def test_accesslimited_is_a_network_refusal():
    kind, detail = refusal_kind(False, "accesslimited")
    assert kind == "network"
    assert "not about the token" in detail


def test_invalid_auth_is_ambiguous_and_never_credential():
    kind, detail = refusal_kind(False, "invalid_auth")
    assert kind == "ambiguous"
    assert "Rotating" in detail or "rotating" in detail


def test_real_credential_errors_are_still_credential_errors():
    assert refusal_kind(False, "token_revoked")[0] == "credential"
    assert refusal_kind(False, "account_inactive")[0] == "credential"
    assert refusal_kind(False, "not_authed")[0] == "credential"


def test_a_scope_error_is_somebody_elses_note():
    assert refusal_kind(False, "missing_scope")[0] == "scope"


def test_success_and_a_silent_failure_are_different_states():
    assert refusal_kind(True, None)[0] == "clear"
    assert refusal_kind(False, None)[0] == "other"


def test_an_address_inside_a_range_is_named_with_the_range():
    verdict, detail = cidr_verdict("203.0.113.44", ["203.0.113.0/24"])
    assert verdict == "inside"
    assert "203.0.113.0/24" in detail


def test_an_address_outside_every_range_lists_what_was_checked():
    verdict, detail = cidr_verdict("198.51.100.7", ["203.0.113.0/24", "192.0.2.0/24"])
    assert verdict == "outside"
    assert "203.0.113.0/24" in detail and "192.0.2.0/24" in detail


def test_a_bare_address_is_treated_as_a_single_host_range():
    assert cidr_verdict("198.51.100.7", ["198.51.100.7"])[0] == "inside"
    assert cidr_verdict("198.51.100.8", ["198.51.100.7/32"])[0] == "outside"


def test_a_malformed_range_is_reported_rather_than_silently_dropped():
    verdict, detail = cidr_verdict("203.0.113.44", ["not-a-range", "203.0.113.0/24"])
    assert verdict == "inside"
    assert "not-a-range" in detail


def test_no_usable_allowlist_reports_the_address_without_judging_it():
    assert cidr_verdict("203.0.113.44", [])[0] == "unlisted"
    assert cidr_verdict("203.0.113.44", ["nonsense"])[0] == "unlisted"


def test_ipv6_and_rubbish_are_kept_apart_from_each_other():
    assert cidr_verdict("2001:db8::1", ["203.0.113.0/24"])[0] == "unsupported"
    assert cidr_verdict("300.1.1.1", ["203.0.113.0/24"])[0] == "malformed"
    assert cidr_verdict("", ["203.0.113.0/24"])[0] == "unknown"


def test_one_vantage_point_is_never_a_proof():
    verdict, detail = vantage_verdict({"kind": "network", "egress": "203.0.113.44"}, None)
    assert verdict == "unconfirmed"
    assert "another" in detail


def test_a_lone_invalid_auth_is_reported_as_unresolved_not_as_a_bad_token():
    verdict, detail = vantage_verdict({"kind": "ambiguous", "egress": "203.0.113.44"}, {})
    assert verdict == "unresolved"
    assert "before touching it" in detail


def test_refused_here_and_fine_there_closes_the_case():
    verdict, detail = vantage_verdict(
        {"kind": "network", "egress": "203.0.113.44"},
        {"kind": "clear", "egress": "198.51.100.7"})
    assert verdict == "confirmed"
    assert "203.0.113.44 is the address to allowlist" in detail


def test_invalid_auth_here_and_success_there_is_also_the_allowlist():
    assert vantage_verdict({"kind": "ambiguous", "egress": "a"},
                           {"kind": "clear", "egress": "b"})[0] == "confirmed"


def test_the_same_failure_from_both_networks_is_the_credential():
    assert vantage_verdict({"kind": "credential"}, {"kind": "credential"})[0] == "credential"
    assert vantage_verdict({"kind": "network", "egress": "a"},
                           {"kind": "network", "egress": "b"})[0] == "both-refused"
''',
"test_js_file": "slack-egress-allowlist.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { cidrVerdict, refusalKind, vantageVerdict } from './slack-egress-allowlist.mjs';

test('accesslimited is a network refusal', () => {
  const [kind, detail] = refusalKind(false, 'accesslimited');
  assert.equal(kind, 'network');
  assert.match(detail, /not about the token/);
});

test('invalid_auth is ambiguous and never credential', () => {
  const [kind, detail] = refusalKind(false, 'invalid_auth');
  assert.equal(kind, 'ambiguous');
  assert.match(detail, /rotating the token does not/);
});

test('real credential errors are still credential errors', () => {
  assert.equal(refusalKind(false, 'token_revoked')[0], 'credential');
  assert.equal(refusalKind(false, 'account_inactive')[0], 'credential');
  assert.equal(refusalKind(false, 'not_authed')[0], 'credential');
});

test('a scope error is somebody elses note', () => {
  assert.equal(refusalKind(false, 'missing_scope')[0], 'scope');
});

test('success and a silent failure are different states', () => {
  assert.equal(refusalKind(true, null)[0], 'clear');
  assert.equal(refusalKind(false, null)[0], 'other');
});

test('an address inside a range is named with the range', () => {
  const [verdict, detail] = cidrVerdict('203.0.113.44', ['203.0.113.0/24']);
  assert.equal(verdict, 'inside');
  assert.match(detail, /203\\.0\\.113\\.0\\/24/);
});

test('an address outside every range lists what was checked', () => {
  const [verdict, detail] = cidrVerdict('198.51.100.7',
    ['203.0.113.0/24', '192.0.2.0/24']);
  assert.equal(verdict, 'outside');
  assert.match(detail, /203\\.0\\.113\\.0\\/24/);
  assert.match(detail, /192\\.0\\.2\\.0\\/24/);
});

test('a bare address is treated as a single host range', () => {
  assert.equal(cidrVerdict('198.51.100.7', ['198.51.100.7'])[0], 'inside');
  assert.equal(cidrVerdict('198.51.100.8', ['198.51.100.7/32'])[0], 'outside');
});

test('a malformed range is reported rather than silently dropped', () => {
  const [verdict, detail] = cidrVerdict('203.0.113.44', ['not-a-range', '203.0.113.0/24']);
  assert.equal(verdict, 'inside');
  assert.match(detail, /not-a-range/);
});

test('no usable allowlist reports the address without judging it', () => {
  assert.equal(cidrVerdict('203.0.113.44', [])[0], 'unlisted');
  assert.equal(cidrVerdict('203.0.113.44', ['nonsense'])[0], 'unlisted');
});

test('ipv6 and rubbish are kept apart from each other', () => {
  assert.equal(cidrVerdict('2001:db8::1', ['203.0.113.0/24'])[0], 'unsupported');
  assert.equal(cidrVerdict('300.1.1.1', ['203.0.113.0/24'])[0], 'malformed');
  assert.equal(cidrVerdict('', ['203.0.113.0/24'])[0], 'unknown');
});

test('one vantage point is never a proof', () => {
  const [verdict, detail] = vantageVerdict({ kind: 'network', egress: '203.0.113.44' }, null);
  assert.equal(verdict, 'unconfirmed');
  assert.match(detail, /another/);
});

test('a lone invalid_auth is reported as unresolved not as a bad token', () => {
  const [verdict, detail] = vantageVerdict({ kind: 'ambiguous', egress: '203.0.113.44' }, {});
  assert.equal(verdict, 'unresolved');
  assert.match(detail, /before touching it/);
});

test('refused here and fine there closes the case', () => {
  const [verdict, detail] = vantageVerdict(
    { kind: 'network', egress: '203.0.113.44' },
    { kind: 'clear', egress: '198.51.100.7' });
  assert.equal(verdict, 'confirmed');
  assert.match(detail, /203\\.0\\.113\\.44 is the address to allowlist/);
});

test('invalid_auth here and success there is also the allowlist', () => {
  assert.equal(vantageVerdict({ kind: 'ambiguous', egress: 'a' },
    { kind: 'clear', egress: 'b' })[0], 'confirmed');
});

test('the same failure from both networks is the credential', () => {
  assert.equal(vantageVerdict({ kind: 'credential' }, { kind: 'credential' })[0],
    'credential');
  assert.equal(vantageVerdict({ kind: 'network', egress: 'a' },
    { kind: 'network', egress: 'b' })[0], 'both-refused');
});
''',
"faq": [
 ("Can I read the organisation's IP allowlist through the API?",
  "No. There is no Web API method that returns the allowed ranges, no method that reports when they last changed, and no method that tells you whether your address is in them. That asymmetry is the reason this script observes its own egress address and asks you for the ranges: the half Slack will tell you is the refusal, and the half it will not is the policy."),
 ("Why does the script fetch my IP from an outside service instead of reading the interface?",
  "Because the address on the interface is almost never the address Slack sees. Containers, NAT gateways, load balancers and VPNs all rewrite it, and the whole question here is what the far end observed. An echo service answers that directly. Point --egress-url at an endpoint you run yourself if a third party in the path is not acceptable; the check works the same way."),
 ("It fails from production and works from my laptop. Is that always the allowlist?",
  "It is strong evidence and it is not the only explanation. A different token in the two environments produces the same asymmetry, so check that the credential really is byte-identical before concluding. Once it is the same token, the same method and two different egress addresses with two different outcomes, there is nothing left that varies except the network."),
 ("We are not on Enterprise Grid. Can we still see accesslimited?",
  "The IP allowlisting feature that produces it is a Grid organisation policy, so the usual answer is no. If it appears anyway, treat it as evidence that the workspace you are calling belongs to a Grid organisation you did not know about, which is worth knowing for other reasons: several of the notes in this section behave differently under Grid."),
 ("Should we allowlist a wide range to stop this recurring?",
  "That trades one problem for a quieter one. A wide range makes the allowlist stop meaning anything, which is a security decision somebody else owns. The durable repair on your side is a stable egress address, so that a narrow entry keeps being correct: pin the NAT gateway, and treat an egress change as a Slack-affecting change in the runbook rather than as an infrastructure detail."),
],
"related": [
 ("/slack/invalid-auth-wrong-token-type/", "the credential error this one impersonates"),
 ("/slack/ratelimited-retry-after-ignored/", "the other refusal that is not about your code"),
 ("/slack/http-200-ok-false/", "why the refusal arrived looking like a success"),
],
"citations": [CITE_POSTMESSAGE, CITE_AUTH_TEST, CITE_GRID, CITE_RATE_LIMITS],
})

GUIDES.append({
"slug": "no-event-subscriptions",
"title": "The app subscribes to no events, so nothing is delivered",
"description": "The scope is not the subscription. An app with app_mentions:read and an empty bot_events list is inert, and has been since the day it was installed.",
"h1": "The app subscribes to no events, so nothing is delivered",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack bot not responding to mentions", "slack app_mention not firing",
             "slack event subscriptions empty", "slack bot_events manifest",
             "app_mentions:read scope no event"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The bot is installed. It is in the channel, which somebody has checked four times. The token is valid, the scopes include <code>app_mentions:read</code>, the request URL is up and returns 200 to a browser. Someone types <code>@deploybot status</code> and nothing happens, and nothing appears in the logs, because nothing arrived.</p><p>The handler is fine. It has never been called. Being in a channel does not cause Slack to send you what happens in it, and the scope that makes an event available is not the switch that turns it on.",
"short_answer": """<p>Event subscriptions are opt-in, one event type at a time, in the app configuration. Adding <code>app_mentions:read</code> to the scopes makes the <code>app_mention</code> event <em>available</em> to subscribe to. It does not subscribe you. Those are two separate screens and two separate steps, and an app that did the first and not the second is completely inert with nothing wrong anywhere in it.</p>
<p>The direct read needs an <strong>app configuration token</strong>, which is a different credential class from your bot token: <code>apps.manifest.export</code> returns <code>settings.event_subscriptions.bot_events[]</code>, and an empty array beside a populated scope list is the finding, full stop. Without that token the script falls back to evidence: the bot is a member, humans are addressing it, and it has <strong>never</strong> replied, ever. That last word is the one that matters, because an app that used to reply and stopped is a different note.</p>""",
"problem": """<p>Nothing about this failure looks like a failure. Every screen a developer thinks to open is green. The app is installed, the OAuth flow completed, <code>auth.test</code> returns <code>ok: true</code> with the right team, <code>conversations.members</code> lists the bot, and the scope list contains exactly the scope the documentation named. The hosting is healthy. The handler compiles. The only symptom is an absence.</p>
<p>An absence is the hardest symptom to work with, because it gives you nothing to search for. There is no error string, no status code, no log line, no <code>ok: false</code>. Teams spend days on the handler, adding print statements to a function that is never entered, before somebody thinks to prove that a request ever reached the process at all. When they do, the request URL is quiet, and then the search moves to networking and TLS and load balancers, which is another day.</p>
<p>The confusion underneath is a genuinely good-faith one. Slack's scope names are written in the language of events. <code>app_mentions:read</code> reads exactly like "receive mentions". <code>channels:history</code> reads like "receive channel messages". They do not mean that. They are permissions attached to the token, describing what the app is allowed to see; the subscription is a separate list in the app configuration describing what Slack should actually push to you. The two lists have to agree, and only one of them is in the place people look.</p>""",
"why": """<p><strong>The subscription list is not visible to a bot token.</strong> No Web API method available to a runtime bot token returns which events an app subscribes to. That is why this note asks for an app configuration token: it is the only credential that reads the manifest, and the manifest is where the answer is written down.</p>
<p><strong>An unreadable manifest must never be reported as an empty one.</strong> If the script cannot read the configuration, the honest answer is that it could not check. Reporting "no subscriptions" because it did not look is how an audit sends somebody to add subscriptions that were already there.</p>
<p><strong>Never replied and stopped replying are two different findings with two different repairs.</strong> An app whose delivery Slack disabled after sustained failures has a history of replies and then a cliff, and the repair is a switch in the app configuration plus whatever caused the failures. An app that has never once replied since installation almost certainly never subscribed to anything. The script separates them explicitly and hands the second case to the note that owns it.</p>
<p><strong>Adding an event can change the grant, so subscribing is often not one step either.</strong> Subscribing to an event whose scope the token does not hold requires adding that scope, and adding a scope requires a reinstall. That is the sibling failure to this one, and the script names it rather than pretending subscription alone is always enough.</p>
<p><strong>A quiet channel is not evidence of anything.</strong> If nobody has addressed the app, its silence is correct. The script refuses to produce a finding in that case, because an audit that fires on an unused app in an unused channel will be switched off within a week.</p>""",
"steps": [
 {"h": "Get an app configuration token, or accept a weaker answer",
  "body": """<p>App configuration tokens are issued from the app management screen and are separate from the bot token. Put one in <code>SLACK_CONFIG_TOKEN</code>. They expire after twelve hours, which is its own note. Without one the script still runs, and says out loud that its answer is inferred rather than read.</p>"""},
 {"h": "Read the subscription list and treat an empty one as the answer",
  "body": """<p><code>subscription_state</code> reduces the manifest to <code>none</code>, <code>configured</code> or <code>unreadable</code>. Those three are kept strictly apart: <code>none</code> is a finding, <code>unreadable</code> is a gap in the audit, and merging them is the one way this script could confidently mislead you.</p>"""},
 {"h": "Diff the scopes against the subscriptions, in that direction",
  "body": """<p><code>scope_without_subscription</code> takes each granted scope that exists to make events available and reports the events it enables that nobody subscribed to. A token holding <code>app_mentions:read</code> with no <code>app_mention</code> subscription is this note in one line, and it is the line that explains the confusion rather than just stating the outcome.</p>"""},
 {"h": "Establish that somebody is actually addressing the app",
  "body": """<p>The behavioural half reads <code>conversations.history</code> for mentions of the bot's user ID. No mentions means no evidence, and the script says so rather than manufacturing a finding out of a quiet channel.</p>"""},
 {"h": "Separate never replied from stopped replying",
  "body": """<p><code>reply_shape</code> returns <code>never-replied</code>, <code>stopped-replying</code>, <code>answering</code> or <code>not-addressed</code>. The second one is not this note, and the script says which note it is instead. Getting that boundary wrong sends a team to re-enable a subscription that was never enabled.</p>"""},
 {"h": "Print the events to subscribe, then the reinstall",
  "body": """<p>The repair is a list: <code>app_mention</code> for mentions, <code>message.channels</code>, <code>message.groups</code>, <code>message.im</code> and <code>message.mpim</code> per channel type, and whatever else the handler switches on. Then reinstall if any of them needed a scope you do not hold, because the subscription and the grant have to arrive together.</p>"""},
],
"verify": """<p>After subscribing and reinstalling, run it again with the same configuration token. The manifest read should change state, and the behavioural half should stop being the only evidence you have.</p>
<pre><code class="language-bash">python3 slack_event_subscription_audit.py --app-id A01ABCDE9 --channel C01ABCDE9
# identity   U0APPBOT11 in acme
# manifest   configured     3 subscribed event(s): app_mention, message.im, reaction_added
# scopes     matched        every event scope on this token has a subscription behind it
# history    answering      12 mention(s), 12 reply(ies), most recent reply after the last mention
# verdict    healthy        events are subscribed and the app is answering them</code></pre>""",
"code_intro": "Two credentials, three reads and four pure functions. <code>subscription_state</code> is nine lines and the entire point of the script, because it is the one place where <em>could not check</em> has to stay distinct from <em>nothing is there</em>. <code>scope_without_subscription</code> walks the scope table in the direction that explains the confusion. <code>reply_shape</code> is the boundary against the auto-disabled note, and <code>finding</code> is the small matrix that combines the read half with the inferred half.",
"py_file": "slack_event_subscription_audit.py",
"py": '''"""Find out whether this app subscribes to any events at all.

Read only. auth.test and conversations.history on a bot token, plus one
apps.manifest.export on an app configuration token if you have one, which is a
read of the app's configuration and not a change to it. Nothing is subscribed,
enabled or installed by this script: it reports what the manifest says, what
the workspace shows, and prints the events you would add.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_event_subscription_audit")

API = "https://slack.com/api/"

# Scopes that exist to make an event available, and the events they unlock.
# This table is walked scope-first on purpose: the confusion this note is about
# runs in that direction, from "I granted app_mentions:read" to "so I will
# receive app_mention", and the table makes the missing step visible.
SCOPE_EVENTS = {
    "app_mentions:read": ["app_mention"],
    "channels:history": ["message.channels"],
    "groups:history": ["message.groups"],
    "im:history": ["message.im"],
    "mpim:history": ["message.mpim"],
    "reactions:read": ["reaction_added", "reaction_removed"],
    "channels:read": ["channel_created", "channel_archive", "channel_rename",
                      "member_joined_channel", "member_left_channel"],
    "files:read": ["file_created", "file_shared"],
    "users:read": ["team_join", "user_change"],
    "pins:read": ["pin_added", "pin_removed"],
    "emoji:read": ["emoji_changed"],
}


def subscription_state(manifest):
    """Reduce an exported manifest to what it says about event subscriptions. Pure.

    Returns (state, events, detail) where state is none, configured or
    unreadable. Those three never collapse into two. "I could not look" is not
    "there is nothing there", and an audit that confuses them will tell a team
    to add subscriptions that already exist.
    """
    if not manifest:
        return ("unreadable", [],
                "no manifest was available, so the subscription list was not read. "
                "This is a gap in the audit and not a finding: an app configuration "
                "token is what closes it")
    settings = (manifest.get("settings") or {}).get("event_subscriptions") or {}
    events = sorted({str(e).strip() for e in
                     list(settings.get("bot_events") or []) +
                     list(settings.get("user_events") or []) if str(e).strip()})
    if not events:
        return ("none", [],
                "the manifest was read and subscribes to zero events. Nothing has "
                "ever been delivered to this app, and no amount of scope, "
                "membership or uptime changes that")
    return ("configured", events,
            "%d subscribed event(s): %s" % (len(events), ", ".join(events)))


def scope_without_subscription(scopes, events):
    """Granted scopes whose events nobody subscribed to. Pure.

    Returns rows of (scope, [unsubscribed events]). A token holding
    app_mentions:read with no app_mention subscription is this whole note in
    one row, and it names the step that was skipped rather than only the
    outcome.
    """
    have = {str(s).strip() for s in scopes or [] if str(s).strip()}
    subscribed = {str(e).strip() for e in events or [] if str(e).strip()}
    rows = []
    for scope in sorted(have):
        enabled = SCOPE_EVENTS.get(scope)
        if not enabled:
            continue
        idle = [e for e in enabled if e not in subscribed]
        if idle:
            rows.append((scope, idle))
    return rows


def reply_shape(messages, bot_id, bot_user, min_unanswered=3):
    """Has this app never replied, or did it reply and then stop? Pure.

    Returns (shape, detail). never-replied points at this note.
    stopped-replying points at the auto-disabled note instead, and keeping
    those two apart is the reason this function exists rather than a counter.
    """
    mention = "<@%s>" % bot_user if bot_user else None
    triggers, replies = [], []
    for m in messages or []:
        ts = float(m.get("ts") or 0)
        ours = bool(bot_id and m.get("bot_id") == bot_id) or bool(
            bot_user and m.get("user") == bot_user)
        if ours:
            replies.append(ts)
        elif mention and mention in (m.get("text") or ""):
            triggers.append(ts)
    triggers.sort()
    replies.sort()

    if not triggers:
        return ("not-addressed",
                "nobody has addressed this app in the sampled history, so its "
                "silence is correct and proves nothing")
    if not replies:
        return ("never-replied",
                "%d mention(s) and not one reply, ever. An app that has never "
                "answered is usually one that was never subscribed, rather than "
                "one whose delivery was switched off" % len(triggers))
    after = [t for t in triggers if t > replies[-1]]
    if len(after) >= int(min_unanswered):
        return ("stopped-replying",
                "%d reply(ies) and then %d unanswered mention(s). This app worked "
                "and stopped, which is the auto-disabled note rather than this "
                "one" % (len(replies), len(after)))
    return ("answering",
            "%d mention(s), %d reply(ies), most recent reply after the last mention"
            % (len(triggers), len(replies)))


def finding(state, shape):
    """Combine what was read with what was inferred. Pure.

    Returns (verdict, action). The read half outranks the inferred half where
    they overlap, because a manifest that says zero is evidence and a quiet
    channel is not.
    """
    if state == "none":
        return ("no-subscriptions",
                "subscribe the events this app handles under Event Subscriptions, "
                "then reinstall if any of them needed a scope you do not hold")
    if shape == "stopped-replying":
        return ("delivery-stopped",
                "this is not a subscription problem: the app answered and then "
                "stopped, so read the note on Slack disabling event delivery")
    if state == "configured":
        if shape == "never-replied":
            return ("subscribed-but-inert",
                    "events are subscribed and nothing has ever been answered, so "
                    "the gap is downstream: the request URL, or an event whose "
                    "scope the token was never granted")
        if shape == "answering":
            return ("healthy", "events are subscribed and the app is answering them")
        return ("no-evidence",
                "events are subscribed and nobody has addressed the app, so there "
                "is nothing to judge")
    if shape == "never-replied":
        return ("probably-unsubscribed",
                "the manifest was not read and the app has never once answered. "
                "Get an app configuration token and check bot_events before "
                "changing any code")
    return ("not-assessed",
            "the manifest was not read and the workspace evidence is inconclusive")


def get(session, method, params, label):
    """One GET, asserting on the body rather than the status line."""
    r = session.get(API + method, params=params or {}, timeout=30)
    body = r.json()
    if body.get("ok") is not True:
        log.warning("%-10s %-14s %s", label, "unavailable", body.get("error"))
        return None, r.headers.get("X-OAuth-Scopes", "")
    return body, r.headers.get("X-OAuth-Scopes", "")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN",
                    help="environment variable holding the bot token")
    ap.add_argument("--config-token-env", default="SLACK_CONFIG_TOKEN",
                    help="environment variable holding an app configuration token")
    ap.add_argument("--app-id", default="", help="app ID, for the manifest read")
    ap.add_argument("--channel", action="append", default=[],
                    help="a channel the app is expected to answer in; repeatable")
    ap.add_argument("--limit", type=int, default=200, help="messages sampled per channel")
    args = ap.parse_args()

    token = os.environ.get(args.token_env)
    if not token:
        log.error("set %s (channels:history and channels:read are enough)",
                  args.token_env)
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + token})

    who, scope_header = get(s, "auth.test", {}, "auth.test")
    if not who:
        return 2
    bot_user, bot_id = who.get("user_id") or "", who.get("bot_id") or ""
    log.info("identity   %s in %s", bot_user, who.get("team"))
    scopes = [p.strip() for p in (scope_header or "").split(",") if p.strip()]

    manifest = None
    config_token = os.environ.get(args.config_token_env)
    if config_token and args.app_id:
        c = requests.Session()
        c.headers.update({"Authorization": "Bearer " + config_token})
        body, _ = get(c, "apps.manifest.export", {"app_id": args.app_id}, "manifest")
        manifest = (body or {}).get("manifest")
    elif not config_token:
        log.info("manifest   skipped        %s is unset, so the subscription list "
                 "cannot be read directly", args.config_token_env)

    state, events, detail = subscription_state(manifest)
    (log.info if state == "configured" else log.warning)(
        "manifest   %-14s %s", state, detail)

    idle = scope_without_subscription(scopes, events)
    if state == "configured" and not idle:
        log.info("scopes     matched        every event scope on this token has a "
                 "subscription behind it")
    for scope, unsubscribed in idle:
        log.warning("scopes     idle           %s is granted and none of %s is "
                    "subscribed; the scope makes the event available, it does not "
                    "turn it on", scope, ", ".join(unsubscribed))

    shape, why = ("not-addressed", "no channel was sampled")
    for channel in args.channel:
        body, _ = get(s, "conversations.history",
                      {"channel": channel, "limit": str(args.limit)}, "history")
        if not body:
            continue
        shape, why = reply_shape(body.get("messages") or [], bot_id, bot_user)
        (log.info if shape in ("answering", "not-addressed") else log.warning)(
            "history    %-14s %s in %s", shape, why, channel)
        if shape in ("never-replied", "stopped-replying"):
            break

    verdict, action = finding(state, shape)
    (log.info if verdict == "healthy" else log.warning)(
        "verdict    %-14s %s", verdict, action)

    if verdict in ("no-subscriptions", "probably-unsubscribed"):
        log.warning("  repair: Event Subscriptions, Subscribe to bot events, add "
                    "app_mention for mentions and message.channels, message.groups, "
                    "message.im or message.mpim per channel type")
        log.warning("  repair: in a manifest-managed app, populate "
                    "settings.event_subscriptions.bot_events and redeploy the manifest")
        log.warning("  repair: reinstall afterwards if any added event needed a "
                    "scope this token does not already hold")
        return 1
    return 1 if verdict in ("subscribed-but-inert", "delivery-stopped") else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-event-subscription-audit.mjs",
"js": '''/**
 * Find out whether this app subscribes to any events at all.
 *
 * Read only. auth.test and conversations.history on a bot token, plus one
 * apps.manifest.export on an app configuration token if you have one, which is
 * a read of the app's configuration and not a change to it. Nothing is
 * subscribed, enabled or installed here: this reports what the manifest says,
 * what the workspace shows, and prints the events you would add.
 */

const API = 'https://slack.com/api/';

// Walked scope-first on purpose: the confusion this note is about runs in that
// direction, from "I granted app_mentions:read" to "so I will receive
// app_mention", and the table makes the missing step visible.
const SCOPE_EVENTS = new Map([
  ['app_mentions:read', ['app_mention']],
  ['channels:history', ['message.channels']],
  ['groups:history', ['message.groups']],
  ['im:history', ['message.im']],
  ['mpim:history', ['message.mpim']],
  ['reactions:read', ['reaction_added', 'reaction_removed']],
  ['channels:read', ['channel_created', 'channel_archive', 'channel_rename',
    'member_joined_channel', 'member_left_channel']],
  ['files:read', ['file_created', 'file_shared']],
  ['users:read', ['team_join', 'user_change']],
  ['pins:read', ['pin_added', 'pin_removed']],
  ['emoji:read', ['emoji_changed']],
]);

/**
 * Reduce an exported manifest to what it says about event subscriptions. Pure.
 * none, configured and unreadable never collapse into two states: "I could not
 * look" is not "there is nothing there".
 */
export function subscriptionState(manifest) {
  if (!manifest) {
    return ['unreadable', [],
      'no manifest was available, so the subscription list was not read. This is ' +
      'a gap in the audit and not a finding: an app configuration token is what ' +
      'closes it'];
  }
  const settings = manifest.settings?.event_subscriptions ?? {};
  const events = [...new Set([
    ...(settings.bot_events ?? []), ...(settings.user_events ?? []),
  ].map((e) => String(e).trim()).filter(Boolean))].sort();
  if (!events.length) {
    return ['none', [],
      'the manifest was read and subscribes to zero events. Nothing has ever been ' +
      'delivered to this app, and no amount of scope, membership or uptime ' +
      'changes that'];
  }
  return ['configured', events,
    `${events.length} subscribed event(s): ${events.join(', ')}`];
}

/**
 * Granted scopes whose events nobody subscribed to. Pure.
 * Names the step that was skipped rather than only the outcome.
 */
export function scopeWithoutSubscription(scopes, events) {
  const have = [...new Set((scopes ?? []).map((s) => String(s).trim()).filter(Boolean))];
  const subscribed = new Set((events ?? []).map((e) => String(e).trim()).filter(Boolean));
  const rows = [];
  for (const scope of have.sort()) {
    const enabled = SCOPE_EVENTS.get(scope);
    if (!enabled) continue;
    const idle = enabled.filter((e) => !subscribed.has(e));
    if (idle.length) rows.push([scope, idle]);
  }
  return rows;
}

/**
 * Has this app never replied, or did it reply and then stop? Pure.
 * never-replied points here. stopped-replying points at the auto-disabled note.
 */
export function replyShape(messages, botId, botUser, minUnanswered = 3) {
  const mention = botUser ? `<@${botUser}>` : null;
  const triggers = [];
  const replies = [];
  for (const m of messages ?? []) {
    const ts = Number(m.ts ?? 0);
    const ours = (botId && m.bot_id === botId) || (botUser && m.user === botUser);
    if (ours) replies.push(ts);
    else if (mention && String(m.text ?? '').includes(mention)) triggers.push(ts);
  }
  triggers.sort((a, b) => a - b);
  replies.sort((a, b) => a - b);

  if (!triggers.length) {
    return ['not-addressed',
      'nobody has addressed this app in the sampled history, so its silence is ' +
      'correct and proves nothing'];
  }
  if (!replies.length) {
    return ['never-replied',
      `${triggers.length} mention(s) and not one reply, ever. An app that has never ` +
      'answered is usually one that was never subscribed, rather than one whose ' +
      'delivery was switched off'];
  }
  const last = replies[replies.length - 1];
  const after = triggers.filter((t) => t > last);
  if (after.length >= Number(minUnanswered)) {
    return ['stopped-replying',
      `${replies.length} reply(ies) and then ${after.length} unanswered mention(s). ` +
      'This app worked and stopped, which is the auto-disabled note rather than ' +
      'this one'];
  }
  return ['answering',
    `${triggers.length} mention(s), ${replies.length} reply(ies), most recent reply ` +
    'after the last mention'];
}

/**
 * Combine what was read with what was inferred. Pure.
 * The read half outranks the inferred half where they overlap.
 */
export function finding(state, shape) {
  if (state === 'none') {
    return ['no-subscriptions',
      'subscribe the events this app handles under Event Subscriptions, then ' +
      'reinstall if any of them needed a scope you do not hold'];
  }
  if (shape === 'stopped-replying') {
    return ['delivery-stopped',
      'this is not a subscription problem: the app answered and then stopped, so ' +
      'read the note on Slack disabling event delivery'];
  }
  if (state === 'configured') {
    if (shape === 'never-replied') {
      return ['subscribed-but-inert',
        'events are subscribed and nothing has ever been answered, so the gap is ' +
        'downstream: the request URL, or an event whose scope the token was never ' +
        'granted'];
    }
    if (shape === 'answering') {
      return ['healthy', 'events are subscribed and the app is answering them'];
    }
    return ['no-evidence',
      'events are subscribed and nobody has addressed the app, so there is nothing ' +
      'to judge'];
  }
  if (shape === 'never-replied') {
    return ['probably-unsubscribed',
      'the manifest was not read and the app has never once answered. Get an app ' +
      'configuration token and check bot_events before changing any code'];
  }
  return ['not-assessed',
    'the manifest was not read and the workspace evidence is inconclusive'];
}

async function get(token, method, params, label) {
  const qs = new URLSearchParams(params ?? {});
  const res = await fetch(`${API}${method}?${qs}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const body = await res.json();
  if (body.ok !== true) {
    console.warn(`${label.padEnd(10)} ${'unavailable'.padEnd(14)} ${body.error}`);
    return [null, res.headers.get('x-oauth-scopes') ?? ''];
  }
  return [body, res.headers.get('x-oauth-scopes') ?? ''];
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

async function main() {
  const args = process.argv.slice(2);
  const tokenEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
  const token = process.env[tokenEnv];
  if (!token) {
    console.error(`set ${tokenEnv} (channels:history and channels:read are enough)`);
    process.exitCode = 2;
    return;
  }
  const configTokenEnv = arg(args, '--config-token-env', 'SLACK_CONFIG_TOKEN');
  const appId = arg(args, '--app-id', '');
  const limit = arg(args, '--limit', '200');

  const [who, scopeHeader] = await get(token, 'auth.test', {}, 'auth.test');
  if (!who) { process.exitCode = 2; return; }
  const botUser = who.user_id ?? '';
  const botId = who.bot_id ?? '';
  console.log(`identity   ${botUser} in ${who.team}`);
  const scopes = String(scopeHeader ?? '').split(',').map((p) => p.trim()).filter(Boolean);

  let manifest = null;
  const configToken = process.env[configTokenEnv];
  if (configToken && appId) {
    const [body] = await get(configToken, 'apps.manifest.export', { app_id: appId },
      'manifest');
    manifest = body?.manifest ?? null;
  } else if (!configToken) {
    console.log(`manifest   skipped        ${configTokenEnv} is unset, so the ` +
      'subscription list cannot be read directly');
  }

  const [state, events, detail] = subscriptionState(manifest);
  (state === 'configured' ? console.log : console.warn)(
    `manifest   ${state.padEnd(14)} ${detail}`);

  const idle = scopeWithoutSubscription(scopes, events);
  if (state === 'configured' && !idle.length) {
    console.log('scopes     matched        every event scope on this token has a ' +
      'subscription behind it');
  }
  for (const [scope, unsubscribed] of idle) {
    console.warn(`scopes     idle           ${scope} is granted and none of ` +
      `${unsubscribed.join(', ')} is subscribed; the scope makes the event ` +
      'available, it does not turn it on');
  }

  let shape = 'not-addressed';
  let why = 'no channel was sampled';
  for (const channel of argAll(args, '--channel')) {
    const [body] = await get(token, 'conversations.history',
      { channel, limit: String(limit) }, 'history');
    if (!body) continue;
    [shape, why] = replyShape(body.messages ?? [], botId, botUser);
    (shape === 'answering' || shape === 'not-addressed' ? console.log : console.warn)(
      `history    ${shape.padEnd(14)} ${why} in ${channel}`);
    if (shape === 'never-replied' || shape === 'stopped-replying') break;
  }

  const [verdict, action] = finding(state, shape);
  (verdict === 'healthy' ? console.log : console.warn)(
    `verdict    ${verdict.padEnd(14)} ${action}`);

  if (verdict === 'no-subscriptions' || verdict === 'probably-unsubscribed') {
    console.warn('  repair: Event Subscriptions, Subscribe to bot events, add ' +
      'app_mention for mentions and message.channels, message.groups, message.im ' +
      'or message.mpim per channel type');
    console.warn('  repair: in a manifest-managed app, populate ' +
      'settings.event_subscriptions.bot_events and redeploy the manifest');
    console.warn('  repair: reinstall afterwards if any added event needed a scope ' +
      'this token does not already hold');
    process.exitCode = 1;
  } else if (verdict === 'subscribed-but-inert' || verdict === 'delivery-stopped') {
    process.exitCode = 1;
  }
}

// Only run when invoked directly, so importing this module in the tests does
// not execute main() and fail the file on a missing token.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The test that keeps this script honest is the one about the manifest it could not read. <code>unreadable</code> and <code>none</code> have to stay two states, because collapsing them turns a missing credential into a confident instruction to add subscriptions that are already there. The other one that carries weight is the split between <code>never-replied</code> and <code>stopped-replying</code>: the same channel history, read with one extra reply in it, has to change which note the reader is sent to.",
"test_py_file": "test_slack_event_subscription_audit.py",
"test_py": '''from slack_event_subscription_audit import (
    finding, reply_shape, scope_without_subscription, subscription_state)


def manifest(bot_events=None, user_events=None):
    return {"settings": {"event_subscriptions": {
        "bot_events": bot_events or [], "user_events": user_events or []}}}


def msg(ts, text="", user="", bot_id=""):
    return {"ts": str(ts), "text": text, "user": user, "bot_id": bot_id}


def test_an_empty_bot_events_list_is_the_finding():
    state, events, detail = subscription_state(manifest([]))
    assert state == "none"
    assert events == []
    assert "zero events" in detail


def test_a_manifest_that_could_not_be_read_is_never_reported_as_empty():
    state, events, detail = subscription_state(None)
    assert state == "unreadable"
    assert events == []
    assert "not a finding" in detail


def test_subscribed_events_are_deduplicated_and_sorted():
    state, events, _ = subscription_state(
        manifest(["message.im", "app_mention"], ["app_mention", "  "]))
    assert state == "configured"
    assert events == ["app_mention", "message.im"]


def test_the_scope_that_reads_like_a_subscription_is_reported_as_idle():
    rows = scope_without_subscription(["app_mentions:read", "chat:write"], [])
    assert rows == [("app_mentions:read", ["app_mention"])]


def test_a_scope_whose_event_is_subscribed_is_not_a_row():
    assert scope_without_subscription(["app_mentions:read"], ["app_mention"]) == []


def test_a_scope_with_several_events_reports_only_the_unsubscribed_ones():
    rows = scope_without_subscription(["reactions:read"], ["reaction_added"])
    assert rows == [("reactions:read", ["reaction_removed"])]


def test_scopes_that_unlock_no_events_are_left_out_of_the_diff():
    assert scope_without_subscription(["chat:write", "commands", ""], []) == []


def test_mentions_with_no_reply_ever_is_the_shape_this_note_owns():
    shape, detail = reply_shape(
        [msg(10, "<@U1> status"), msg(20, "<@U1> status"), msg(30, "<@U1> ping")],
        "B1", "U1")
    assert shape == "never-replied"
    assert "not one reply" in detail


def test_replies_followed_by_unanswered_mentions_belongs_to_the_other_note():
    shape, detail = reply_shape(
        [msg(10, "<@U1> a"), msg(11, bot_id="B1"),
         msg(20, "<@U1> b"), msg(30, "<@U1> c"), msg(40, "<@U1> d")], "B1", "U1")
    assert shape == "stopped-replying"
    assert "auto-disabled" in detail


def test_one_unanswered_mention_after_a_reply_is_not_a_cliff():
    shape, _ = reply_shape(
        [msg(10, "<@U1> a"), msg(11, bot_id="B1"), msg(20, "<@U1> b")], "B1", "U1")
    assert shape == "answering"


def test_a_channel_nobody_addressed_produces_no_evidence():
    assert reply_shape([msg(10, "morning"), msg(11, "morning")], "B1", "U1")[0] \\
        == "not-addressed"


def test_the_apps_own_mention_of_itself_is_a_reply_not_a_trigger():
    assert reply_shape([msg(10, "<@U1> hello", bot_id="B1")], "B1", "U1")[0] \\
        == "not-addressed"


def test_zero_subscriptions_outranks_every_behavioural_reading():
    assert finding("none", "answering")[0] == "no-subscriptions"
    assert finding("none", "not-addressed")[0] == "no-subscriptions"


def test_a_cliff_is_handed_to_the_note_that_owns_it():
    verdict, action = finding("configured", "stopped-replying")
    assert verdict == "delivery-stopped"
    assert "not a subscription problem" in action


def test_subscribed_and_never_answering_points_downstream_instead():
    assert finding("configured", "never-replied")[0] == "subscribed-but-inert"
    assert finding("configured", "answering")[0] == "healthy"


def test_an_unread_manifest_gives_a_hedged_verdict_not_a_confident_one():
    verdict, action = finding("unreadable", "never-replied")
    assert verdict == "probably-unsubscribed"
    assert "before changing any code" in action
    assert finding("unreadable", "not-addressed")[0] == "not-assessed"
''',
"test_js_file": "slack-event-subscription-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  finding, replyShape, scopeWithoutSubscription, subscriptionState,
} from './slack-event-subscription-audit.mjs';

const manifest = (botEvents = [], userEvents = []) => ({
  settings: { event_subscriptions: { bot_events: botEvents, user_events: userEvents } },
});

const msg = (ts, text = '', user = '', botId = '') => ({
  ts: String(ts), text, user, bot_id: botId,
});

test('an empty bot_events list is the finding', () => {
  const [state, events, detail] = subscriptionState(manifest([]));
  assert.equal(state, 'none');
  assert.deepEqual(events, []);
  assert.match(detail, /zero events/);
});

test('a manifest that could not be read is never reported as empty', () => {
  const [state, events, detail] = subscriptionState(null);
  assert.equal(state, 'unreadable');
  assert.deepEqual(events, []);
  assert.match(detail, /not a finding/);
});

test('subscribed events are deduplicated and sorted', () => {
  const [state, events] = subscriptionState(
    manifest(['message.im', 'app_mention'], ['app_mention', '  ']));
  assert.equal(state, 'configured');
  assert.deepEqual(events, ['app_mention', 'message.im']);
});

test('the scope that reads like a subscription is reported as idle', () => {
  assert.deepEqual(scopeWithoutSubscription(['app_mentions:read', 'chat:write'], []),
    [['app_mentions:read', ['app_mention']]]);
});

test('a scope whose event is subscribed is not a row', () => {
  assert.deepEqual(scopeWithoutSubscription(['app_mentions:read'], ['app_mention']), []);
});

test('a scope with several events reports only the unsubscribed ones', () => {
  assert.deepEqual(scopeWithoutSubscription(['reactions:read'], ['reaction_added']),
    [['reactions:read', ['reaction_removed']]]);
});

test('scopes that unlock no events are left out of the diff', () => {
  assert.deepEqual(scopeWithoutSubscription(['chat:write', 'commands', ''], []), []);
});

test('mentions with no reply ever is the shape this note owns', () => {
  const [shape, detail] = replyShape(
    [msg(10, '<@U1> status'), msg(20, '<@U1> status'), msg(30, '<@U1> ping')],
    'B1', 'U1');
  assert.equal(shape, 'never-replied');
  assert.match(detail, /not one reply/);
});

test('replies followed by unanswered mentions belongs to the other note', () => {
  const [shape, detail] = replyShape(
    [msg(10, '<@U1> a'), msg(11, '', '', 'B1'),
      msg(20, '<@U1> b'), msg(30, '<@U1> c'), msg(40, '<@U1> d')], 'B1', 'U1');
  assert.equal(shape, 'stopped-replying');
  assert.match(detail, /auto-disabled/);
});

test('one unanswered mention after a reply is not a cliff', () => {
  const [shape] = replyShape(
    [msg(10, '<@U1> a'), msg(11, '', '', 'B1'), msg(20, '<@U1> b')], 'B1', 'U1');
  assert.equal(shape, 'answering');
});

test('a channel nobody addressed produces no evidence', () => {
  assert.equal(replyShape([msg(10, 'morning'), msg(11, 'morning')], 'B1', 'U1')[0],
    'not-addressed');
});

test('the apps own mention of itself is a reply not a trigger', () => {
  assert.equal(replyShape([msg(10, '<@U1> hello', '', 'B1')], 'B1', 'U1')[0],
    'not-addressed');
});

test('zero subscriptions outranks every behavioural reading', () => {
  assert.equal(finding('none', 'answering')[0], 'no-subscriptions');
  assert.equal(finding('none', 'not-addressed')[0], 'no-subscriptions');
});

test('a cliff is handed to the note that owns it', () => {
  const [verdict, action] = finding('configured', 'stopped-replying');
  assert.equal(verdict, 'delivery-stopped');
  assert.match(action, /not a subscription problem/);
});

test('subscribed and never answering points downstream instead', () => {
  assert.equal(finding('configured', 'never-replied')[0], 'subscribed-but-inert');
  assert.equal(finding('configured', 'answering')[0], 'healthy');
});

test('an unread manifest gives a hedged verdict not a confident one', () => {
  const [verdict, action] = finding('unreadable', 'never-replied');
  assert.equal(verdict, 'probably-unsubscribed');
  assert.match(action, /before changing any code/);
  assert.equal(finding('unreadable', 'not-addressed')[0], 'not-assessed');
});
''',
"faq": [
 ("I added app_mentions:read. Why is the bot still silent?",
  "Because that scope is a permission, not a subscription. It makes the app_mention event available to your app; it does not ask Slack to send it. The subscription is a separate list under Event Subscriptions, Subscribe to bot events, and until app_mention appears there nothing is delivered. The naming is genuinely misleading and this is the most common way into this failure."),
 ("Do I really need an app configuration token to check this?",
  "To read the answer, yes: no bot token can see which events an app subscribes to, so the manifest export is the only direct route. Without it the script still runs and gives you a hedged verdict from workspace evidence. It will say probably-unsubscribed rather than no-subscriptions, and the difference in wording is deliberate, because one is a reading and the other is a fact."),
 ("The bot is in the channel. Doesn't that mean it receives the messages?",
  "No. Membership controls what the app is allowed to read through the Web API and where it can post. Delivery of events is a separate mechanism entirely, driven by the subscription list and the request URL. An app can be in a thousand channels and receive nothing at all, which is exactly the state this note is about."),
 ("How is this different from Slack disabling my event subscriptions?",
  "History. An app whose delivery Slack disabled has a record of replies and then a cliff, because it worked until the failures crossed the threshold. An app that was never subscribed has no replies at all, from installation to now. The script reports those as stopped-replying and never-replied and sends the first case to the other note, because the repairs are unrelated: one re-enables a switch, the other adds a list that was always empty."),
 ("Once I subscribe the events, is that the whole fix?",
  "Usually not quite. An event whose required scope the token does not hold will still never arrive, silently, even though the subscription is now present. That is the sibling failure to this one. Add the scope alongside the subscription, keep them together in the manifest so they cannot drift, and reinstall so the token actually carries the new grant."),
],
"related": [
 ("/slack/event-subscriptions-auto-disabled/", "when delivery worked and then stopped"),
 ("/slack/event-scope-mismatch/", "when the subscription exists and the scope does not"),
 ("/slack/config-token-expired/", "the credential this script needs, and how it dies"),
],
"citations": [CITE_EVENTS, CITE_MANIFEST, CITE_APP_MENTION, CITE_SCOPES],
})

GUIDES.append({
"slug": "event-scope-mismatch",
"title": "A subscribed event whose scope the token never received",
"description": "message.groups without groups:history is never delivered and never errors. Diff the subscribed events against the grant, because Slack will not.",
"h1": "A subscribed event whose scope the token never received",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack message.groups not received", "slack event not firing scope",
             "groups:history missing event", "slack events api scopes",
             "slack reaction_added not delivered"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The app handles messages in public channels perfectly. In private channels it is deaf. The subscription is there, on the same screen, one line below the one that works; the handler is the same function; the logs have nothing in them because there is nothing to log.</p><p>No method refused anything. No error was returned, because no request was made. The Events API is gated by the same scopes as the Web API, and an event whose scope the token does not hold is simply never sent.",
"short_answer": """<p>Subscribing to an event does not entitle you to receive it. Delivery is gated by the authorizing token's scopes: <code>message.groups</code> needs <code>groups:history</code>, <code>message.im</code> needs <code>im:history</code>, <code>reaction_added</code> needs <code>reactions:read</code>. Subscribe without the scope and the event is quietly not delivered, forever, with nothing anywhere to read.</p>
<p>That silence is why this is a diff and not a probe. Set A is the subscribed events, from <code>apps.manifest.export</code>. Set B is the granted scopes, from the <code>X-OAuth-Scopes</code> header that Slack returns on every Web API response. The script maps each event to the scopes that would satisfy it, treats that list as an <strong>OR</strong>, and reports the subscriptions that can never fire. Without a configuration token it runs the same check against the list of events your code handles, where a handler for an unscoped event is dead code.</p>""",
"problem": """<p>What makes this one expensive is that the app mostly works. If nothing arrived, somebody would question the whole setup on day one. Instead, mentions arrive and reactions do not; public channels are fine and private ones are not; the app answers direct messages and ignores group DMs. A partial failure gets attributed to the part of the system that varies, and the part that varies looks like the channel type, so the investigation goes into channel visibility, membership and Slack Connect before it gets anywhere near the token.</p>
<p>The two ways in are both ordinary. The first is drift: an app is installed with a broad grant, somebody later trims the scope list as part of a security pass, the subscription stays behind, and delivery of that one event stops on the next reinstall with nothing to connect the two events months apart. The second is that the app configuration will let you subscribe to an event whose scope you never requested, and the install proceeds normally, and the feature has simply never worked since the day it shipped.</p>
<p>Either way there is no artefact. No <code>missing_scope</code>, because <code>missing_scope</code> comes from a method call and this is not a method call. No delivery failure, because there was no delivery. No entry in any log on your side or anything you can query on Slack's. The only evidence is a subscription that has never produced traffic, and absence of traffic is not something an application notices about itself.</p>""",
"why": """<p><strong>This is not <code>missing_scope</code>.</strong> That error is Slack refusing a method you called and telling you exactly what was <code>needed</code> and <code>provided</code>. Here nobody calls anything: Slack decides not to send an event, and there is no request to answer. Same underlying grant, opposite direction, and no error string to search for.</p>
<p><strong>The mapping is per event and lives on each event's reference page.</strong> There is no method that returns "the scopes this event requires", so a detector has to carry a table. The script's table is explicit and reports an event it does not recognise as unknown rather than assuming it is fine, because a silent pass is exactly the failure mode being audited.</p>
<p><strong>The requirement is frequently an OR, and treating it as an AND creates false findings.</strong> <code>member_joined_channel</code> is satisfied by <code>channels:read</code> or <code>groups:read</code> depending on the channel type. An audit that demands both will tell a team to widen a grant that was already correct.</p>
<p><strong>Subscription and scope are two switches and neither implies the other.</strong> That gives four states, not two: both present is live, both absent is simply not a feature, subscribed without the scope is this note, and scoped without the subscription is the note next door. Reporting the last two as one thing produces the wrong repair half the time.</p>
<p><strong>An undeliverable event that your code handles is worse than one nobody handles.</strong> The first is a feature somebody wrote, tested against a mock, shipped and believes is running. The script ranks it above the other, because that is the row that has a person behind it.</p>""",
"steps": [
 {"h": "Read the grant from a header rather than from the app config screen",
  "body": """<p><code>X-OAuth-Scopes</code> comes back on every Web API response and carries the calling token's complete current scope list. One <code>auth.test</code> gets it. The scope list on the configuration screen describes what will be requested at the next install, which is a different thing and is precisely the gap that produces this failure.</p>"""},
 {"h": "Read the subscribed events, or supply what your code handles",
  "body": """<p>With an app configuration token, <code>apps.manifest.export</code> gives you <code>settings.event_subscriptions.bot_events[]</code>. Without one, pass <code>--handles</code> for each event type your code has a handler for. The second list is often the more interesting one anyway, because it is what somebody believed was running.</p>"""},
 {"h": "Resolve each event against the table, as an OR",
  "body": """<p><code>pair_state</code> takes one event and asks two questions: is it subscribed, and is any of its scopes granted. Any single scope in the list satisfies the event. An event the table does not know is returned as <code>unknown-event</code> and is never quietly counted as deliverable.</p>"""},
 {"h": "Sort the four states apart and keep them apart",
  "body": """<p><code>live</code>, <code>undeliverable</code>, <code>idle-scope</code> and <code>absent</code>. Only <code>undeliverable</code> is this note. <code>idle-scope</code> is a scope you hold with no subscription behind it, which belongs to the note on an app that subscribes to nothing, and the script says so instead of merging them.</p>"""},
 {"h": "Rank by whether somebody wrote code for it",
  "body": """<p><code>severity</code> puts an undeliverable event with a handler above one without, then unknown events, then everything else. A feature that was written, reviewed and shipped and has never once run is a different conversation from a subscription somebody left behind.</p>"""},
 {"h": "Print the scope, and then the reinstall",
  "body": """<p>Adding the scope in the app configuration changes nothing about tokens already issued. The printed repair names the scope, names the reinstall, and says to put the scope and the subscription in the manifest together so they cannot drift apart again.</p>"""},
],
"verify": """<p>Re-run after the reinstall. The scope header should have changed, and every subscribed event should resolve to <code>live</code>.</p>
<pre><code class="language-bash">python3 slack_event_scope_gap.py --app-id A01ABCDE9 --handles message.groups
# identity   U0APPBOT11 in acme
# grant      11 scope(s) on this token
# events     4 subscribed, 1 handled by your code
# message.groups        live           groups:history is granted and the event is subscribed
# app_mention           live           app_mentions:read is granted and the event is subscribed
# verdict    clear          no subscribed event is missing the scope it needs</code></pre>""",
"code_intro": "One GET for the header, one optional GET for the manifest, and a table. <code>pair_state</code> is the function to read first: it takes the two switches that govern whether an event ever arrives and returns the four states they produce, which is the difference between this note and the one next door written down in code. <code>audit</code> walks the union of what is subscribed and what your code handles, and <code>severity</code> ranks the result by whether a person is waiting on it.",
"py_file": "slack_event_scope_gap.py",
"py": '''"""Find subscribed events that can never be delivered to this token.

Read only. One auth.test to read the X-OAuth-Scopes header, and one optional
apps.manifest.export on an app configuration token to read the subscribed
events. Nothing is subscribed, granted or reinstalled here: this diffs two
lists and prints the scope you would add.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_event_scope_gap")

API = "https://slack.com/api/"

# Each event mapped to the scopes that would satisfy its delivery. The list is
# an OR: any one of them is enough. member_joined_channel is the row that makes
# that matter, because which scope applies depends on the channel type, and an
# audit that demanded both would tell a team to widen a correct grant.
EVENT_SCOPES = {
    "app_mention": ["app_mentions:read"],
    "message.channels": ["channels:history"],
    "message.groups": ["groups:history"],
    "message.im": ["im:history"],
    "message.mpim": ["mpim:history"],
    "reaction_added": ["reactions:read"],
    "reaction_removed": ["reactions:read"],
    "file_created": ["files:read"],
    "file_shared": ["files:read"],
    "file_public": ["files:read"],
    "member_joined_channel": ["channels:read", "groups:read"],
    "member_left_channel": ["channels:read", "groups:read"],
    "channel_created": ["channels:read"],
    "channel_archive": ["channels:read"],
    "channel_unarchive": ["channels:read"],
    "channel_rename": ["channels:read"],
    "group_open": ["groups:read"],
    "team_join": ["users:read"],
    "user_change": ["users:read"],
    "pin_added": ["pins:read"],
    "pin_removed": ["pins:read"],
    "emoji_changed": ["emoji:read"],
    "app_home_opened": [],
    "app_uninstalled": [],
    "tokens_revoked": [],
}

# Ordering for the report. An undeliverable event somebody wrote a handler for
# outranks one nobody uses, because that row has a person behind it who thinks
# the feature is running.
RANK = {"undeliverable-handled": 0, "undeliverable": 1, "unknown-event": 2,
        "idle-scope": 3, "live": 4, "absent": 5}


def scope_set(header):
    """Split the X-OAuth-Scopes header into a set. Pure."""
    return {p.strip() for p in str(header or "").split(",") if p.strip()}


def pair_state(event, subscribed, scopes):
    """The two switches that govern whether an event ever arrives. Pure.

    Returns (state, detail). Subscription and scope are independent, so there
    are four states and not two, and only one of them is this note:

      live         subscribed and scoped, so delivery happens
      undeliverable  subscribed with the scope missing, silently never sent
      idle-scope   scoped with no subscription, which is a different note
      absent       neither, which is simply not a feature of this app
    """
    name = str(event or "").strip()
    if not name:
        return ("absent", "no event name was given")
    needed = EVENT_SCOPES.get(name)
    if needed is None:
        return ("unknown-event",
                "%s is not in this script's table, so its scope requirement was "
                "not checked. Read the event's reference page rather than "
                "assuming it is fine" % name)

    have = {str(s).strip() for s in scopes or [] if str(s).strip()}
    satisfied = [s for s in needed if s in have]
    if not needed:
        return ("live" if subscribed else "absent",
                "%s requires no scope; it is %s" % (
                    name, "subscribed" if subscribed else "not subscribed"))
    if subscribed and satisfied:
        return ("live", "%s is granted and the event is subscribed" % satisfied[0])
    if subscribed and not satisfied:
        return ("undeliverable",
                "subscribed, and none of %s is on this token, so %s is never "
                "delivered and never errors" % (" or ".join(needed), name))
    if satisfied:
        return ("idle-scope",
                "%s is granted and %s is not subscribed, which is a subscription "
                "gap rather than a scope gap" % (satisfied[0], name))
    return ("absent", "%s is neither subscribed nor scoped" % name)


def audit(subscribed, handled, scopes, subscriptions_known=True):
    """Walk every event either configured or handled by your code. Pure.

    Returns rows of (event, state, detail, handled). subscriptions_known is
    the difference between the script's two modes. With a configuration token
    the subscription list is a fact, and an event you handle but never
    subscribed to is the note next door. Without one there is no list, so a
    handler is taken as the declaration of intent it obviously is.
    """
    subs = {str(e).strip() for e in subscribed or [] if str(e).strip()}
    mine = {str(e).strip() for e in handled or [] if str(e).strip()}
    rows = []
    for name in sorted(subs | mine):
        claimed = name in subs or (not subscriptions_known and name in mine)
        state, detail = pair_state(name, claimed, scopes)
        if state == "undeliverable" and name in mine:
            detail += ". Your code handles this event, so that handler has never run"
        rows.append((name, state, detail, name in mine))
    return rows


def severity(rows):
    """Order the rows so the worst finding is read first. Pure."""
    def key(row):
        name, state, _, handled = row
        bucket = "undeliverable-handled" if (state == "undeliverable" and handled) \\
            else state
        return (RANK.get(bucket, 6), name)
    return sorted(rows or [], key=key)


def get(session, method, params, label):
    """One GET, asserting on the body rather than the status line."""
    r = session.get(API + method, params=params or {}, timeout=30)
    body = r.json()
    if body.get("ok") is not True:
        log.warning("%-10s %-14s %s", label, "unavailable", body.get("error"))
        return None, r.headers.get("X-OAuth-Scopes", "")
    return body, r.headers.get("X-OAuth-Scopes", "")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN",
                    help="environment variable holding the bot token")
    ap.add_argument("--config-token-env", default="SLACK_CONFIG_TOKEN",
                    help="environment variable holding an app configuration token")
    ap.add_argument("--app-id", default="", help="app ID, for the manifest read")
    ap.add_argument("--handles", action="append", default=[],
                    help="an event type your code has a handler for; repeatable")
    args = ap.parse_args()

    token = os.environ.get(args.token_env)
    if not token:
        log.error("set %s; any read scope works, the header is what matters",
                  args.token_env)
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + token})
    who, header = get(s, "auth.test", {}, "auth.test")
    if not who:
        return 2
    scopes = scope_set(header)
    log.info("identity   %s in %s", who.get("user_id"), who.get("team"))
    log.info("grant      %d scope(s) on this token", len(scopes))

    subscribed, known = [], False
    config_token = os.environ.get(args.config_token_env)
    if config_token and args.app_id:
        c = requests.Session()
        c.headers.update({"Authorization": "Bearer " + config_token})
        body, _ = get(c, "apps.manifest.export", {"app_id": args.app_id}, "manifest")
        if body:
            settings = ((body or {}).get("manifest") or {}).get("settings") or {}
            subs = settings.get("event_subscriptions") or {}
            subscribed = list(subs.get("bot_events") or []) + \
                list(subs.get("user_events") or [])
            known = True
    if not known:
        log.info("manifest   skipped        no subscription list was read, so each "
                 "--handles event is taken as an intent to receive it")

    rows = severity(audit(subscribed, args.handles, scopes, known))
    log.info("events     %d subscribed, %d handled by your code",
             len(subscribed), len(args.handles))

    bad = 0
    for name, state, detail, handled in rows:
        if state in ("undeliverable", "unknown-event"):
            bad += 1 if state == "undeliverable" else 0
            log.warning("%-21s %-14s %s", name, state, detail)
        else:
            log.info("%-21s %-14s %s", name, state, detail)

    if bad:
        needed = sorted({sc for name, state, _, _ in rows if state == "undeliverable"
                         for sc in EVENT_SCOPES.get(name, [])})
        log.warning("  repair: add one of %s under OAuth and Permissions, Bot Token "
                    "Scopes", ", ".join(needed))
        log.warning("  repair: reinstall the app and replace the stored token; a "
                    "token is a snapshot of the grant at install time")
        log.warning("  repair: keep the scope and the subscription together in the "
                    "manifest, because neither one implies the other")
        return 1
    log.info("verdict    clear          no subscribed event is missing the scope "
             "it needs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-event-scope-gap.mjs",
"js": '''/**
 * Find subscribed events that can never be delivered to this token.
 *
 * Read only. One auth.test to read the X-OAuth-Scopes header, and one optional
 * apps.manifest.export on an app configuration token to read the subscribed
 * events. Nothing is subscribed, granted or reinstalled here: this diffs two
 * lists and prints the scope you would add.
 */

const API = 'https://slack.com/api/';

// Each event mapped to the scopes that would satisfy its delivery. The list is
// an OR: any one of them is enough. member_joined_channel is the row that makes
// that matter, because which scope applies depends on the channel type.
const EVENT_SCOPES = new Map([
  ['app_mention', ['app_mentions:read']],
  ['message.channels', ['channels:history']],
  ['message.groups', ['groups:history']],
  ['message.im', ['im:history']],
  ['message.mpim', ['mpim:history']],
  ['reaction_added', ['reactions:read']],
  ['reaction_removed', ['reactions:read']],
  ['file_created', ['files:read']],
  ['file_shared', ['files:read']],
  ['file_public', ['files:read']],
  ['member_joined_channel', ['channels:read', 'groups:read']],
  ['member_left_channel', ['channels:read', 'groups:read']],
  ['channel_created', ['channels:read']],
  ['channel_archive', ['channels:read']],
  ['channel_unarchive', ['channels:read']],
  ['channel_rename', ['channels:read']],
  ['group_open', ['groups:read']],
  ['team_join', ['users:read']],
  ['user_change', ['users:read']],
  ['pin_added', ['pins:read']],
  ['pin_removed', ['pins:read']],
  ['emoji_changed', ['emoji:read']],
  ['app_home_opened', []],
  ['app_uninstalled', []],
  ['tokens_revoked', []],
]);

const RANK = {
  'undeliverable-handled': 0, undeliverable: 1, 'unknown-event': 2,
  'idle-scope': 3, live: 4, absent: 5,
};

/** Split the X-OAuth-Scopes header into a set. Pure. */
export function scopeSet(header) {
  return new Set(String(header ?? '').split(',').map((p) => p.trim()).filter(Boolean));
}

/**
 * The two switches that govern whether an event ever arrives. Pure.
 * Subscription and scope are independent, so there are four states and not
 * two, and only undeliverable is this note.
 */
export function pairState(event, subscribed, scopes) {
  const name = String(event ?? '').trim();
  if (!name) return ['absent', 'no event name was given'];
  const needed = EVENT_SCOPES.get(name);
  if (needed === undefined) {
    return ['unknown-event',
      `${name} is not in this script's table, so its scope requirement was not ` +
      'checked. Read the event\\u2019s reference page rather than assuming it is fine'];
  }

  const have = new Set([...(scopes ?? [])].map((s) => String(s).trim()).filter(Boolean));
  const satisfied = needed.filter((s) => have.has(s));
  if (!needed.length) {
    return [subscribed ? 'live' : 'absent',
      `${name} requires no scope; it is ${subscribed ? 'subscribed' : 'not subscribed'}`];
  }
  if (subscribed && satisfied.length) {
    return ['live', `${satisfied[0]} is granted and the event is subscribed`];
  }
  if (subscribed) {
    return ['undeliverable',
      `subscribed, and none of ${needed.join(' or ')} is on this token, so ${name} ` +
      'is never delivered and never errors'];
  }
  if (satisfied.length) {
    return ['idle-scope',
      `${satisfied[0]} is granted and ${name} is not subscribed, which is a ` +
      'subscription gap rather than a scope gap'];
  }
  return ['absent', `${name} is neither subscribed nor scoped`];
}

/**
 * Walk every event either configured or handled by your code. Pure.
 * subscriptionsKnown is the difference between the script's two modes: with a
 * configuration token the subscription list is a fact, and an event you handle
 * but never subscribed to is the note next door; without one, a handler is
 * taken as the declaration of intent it obviously is.
 */
export function audit(subscribed, handled, scopes, subscriptionsKnown = true) {
  const subs = new Set((subscribed ?? []).map((e) => String(e).trim()).filter(Boolean));
  const mine = new Set((handled ?? []).map((e) => String(e).trim()).filter(Boolean));
  const rows = [];
  for (const name of [...new Set([...subs, ...mine])].sort()) {
    const claimed = subs.has(name) || (!subscriptionsKnown && mine.has(name));
    const [state, base] = pairState(name, claimed, scopes);
    const detail = (state === 'undeliverable' && mine.has(name))
      ? `${base}. Your code handles this event, so that handler has never run`
      : base;
    rows.push([name, state, detail, mine.has(name)]);
  }
  return rows;
}

/** Order the rows so the worst finding is read first. Pure. */
export function severity(rows) {
  const bucket = ([, state, , handled]) => (
    state === 'undeliverable' && handled ? 'undeliverable-handled' : state);
  return [...(rows ?? [])].sort((a, b) => {
    const ra = RANK[bucket(a)] ?? 6;
    const rb = RANK[bucket(b)] ?? 6;
    return ra - rb || a[0].localeCompare(b[0]);
  });
}

async function get(token, method, params, label) {
  const qs = new URLSearchParams(params ?? {});
  const res = await fetch(`${API}${method}?${qs}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const body = await res.json();
  if (body.ok !== true) {
    console.warn(`${label.padEnd(10)} ${'unavailable'.padEnd(14)} ${body.error}`);
    return [null, res.headers.get('x-oauth-scopes') ?? ''];
  }
  return [body, res.headers.get('x-oauth-scopes') ?? ''];
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

async function main() {
  const args = process.argv.slice(2);
  const tokenEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
  const token = process.env[tokenEnv];
  if (!token) {
    console.error(`set ${tokenEnv}; any read scope works, the header is what matters`);
    process.exitCode = 2;
    return;
  }
  const configTokenEnv = arg(args, '--config-token-env', 'SLACK_CONFIG_TOKEN');
  const appId = arg(args, '--app-id', '');
  const handles = argAll(args, '--handles');

  const [who, header] = await get(token, 'auth.test', {}, 'auth.test');
  if (!who) { process.exitCode = 2; return; }
  const scopes = scopeSet(header);
  console.log(`identity   ${who.user_id} in ${who.team}`);
  console.log(`grant      ${scopes.size} scope(s) on this token`);

  let subscribed = [];
  let known = false;
  const configToken = process.env[configTokenEnv];
  if (configToken && appId) {
    const [body] = await get(configToken, 'apps.manifest.export', { app_id: appId },
      'manifest');
    if (body) {
      const subs = body?.manifest?.settings?.event_subscriptions ?? {};
      subscribed = [...(subs.bot_events ?? []), ...(subs.user_events ?? [])];
      known = true;
    }
  }
  if (!known) {
    console.log('manifest   skipped        no subscription list was read, so each ' +
      '--handles event is taken as an intent to receive it');
  }

  const rows = severity(audit(subscribed, handles, scopes, known));
  console.log(`events     ${subscribed.length} subscribed, ${handles.length} ` +
    'handled by your code');

  let bad = 0;
  for (const [name, state, detail] of rows) {
    if (state === 'undeliverable' || state === 'unknown-event') {
      if (state === 'undeliverable') bad += 1;
      console.warn(`${name.padEnd(21)} ${state.padEnd(14)} ${detail}`);
    } else {
      console.log(`${name.padEnd(21)} ${state.padEnd(14)} ${detail}`);
    }
  }

  if (bad) {
    const needed = [...new Set(rows
      .filter(([, state]) => state === 'undeliverable')
      .flatMap(([name]) => EVENT_SCOPES.get(name) ?? []))].sort();
    console.warn(`  repair: add one of ${needed.join(', ')} under OAuth and ` +
      'Permissions, Bot Token Scopes');
    console.warn('  repair: reinstall the app and replace the stored token; a token ' +
      'is a snapshot of the grant at install time');
    console.warn('  repair: keep the scope and the subscription together in the ' +
      'manifest, because neither one implies the other');
    process.exitCode = 1;
  } else {
    console.log('verdict    clear          no subscribed event is missing the scope ' +
      'it needs');
  }
}

// Only run when invoked directly, so importing this module in the tests does
// not execute main() and fail the file on a missing token.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Three assertions do the work. The scope requirement is an OR, so <code>member_joined_channel</code> has to pass on <code>channels:read</code> alone and on <code>groups:read</code> alone. A scope held with no subscription behind it has to come back as <code>idle-scope</code> and not as a finding, because that row belongs to a different note and a different repair. And an event the table does not recognise has to be reported rather than waved through, since waving it through is the exact behaviour this script exists to catch Slack doing.",
"test_py_file": "test_slack_event_scope_gap.py",
"test_py": '''from slack_event_scope_gap import audit, pair_state, scope_set, severity


def test_the_scope_header_is_split_and_trimmed():
    assert scope_set("channels:read, groups:history ,users:read") == {
        "channels:read", "groups:history", "users:read"}
    assert scope_set("") == set()
    assert scope_set(None) == set()


def test_subscribed_and_scoped_is_live():
    state, detail = pair_state("message.groups", True, {"groups:history"})
    assert state == "live"
    assert "groups:history is granted" in detail


def test_subscribed_without_the_scope_is_the_finding():
    state, detail = pair_state("message.groups", True, {"channels:history"})
    assert state == "undeliverable"
    assert "never delivered and never errors" in detail


def test_a_scope_with_no_subscription_belongs_to_the_other_note():
    state, detail = pair_state("message.groups", False, {"groups:history"})
    assert state == "idle-scope"
    assert "subscription gap rather than a scope gap" in detail


def test_neither_switch_is_simply_not_a_feature():
    assert pair_state("message.groups", False, set())[0] == "absent"


def test_the_scope_requirement_is_an_or_and_either_option_satisfies_it():
    assert pair_state("member_joined_channel", True, {"channels:read"})[0] == "live"
    assert pair_state("member_joined_channel", True, {"groups:read"})[0] == "live"
    assert pair_state("member_joined_channel", True, {"users:read"})[0] == "undeliverable"


def test_an_or_list_is_printed_as_a_choice_not_a_requirement():
    _, detail = pair_state("member_joined_channel", True, set())
    assert "channels:read or groups:read" in detail


def test_an_event_needing_no_scope_is_live_on_subscription_alone():
    assert pair_state("app_home_opened", True, set())[0] == "live"
    assert pair_state("app_home_opened", False, set())[0] == "absent"


def test_an_unrecognised_event_is_reported_rather_than_waved_through():
    state, detail = pair_state("message.channels.somethingnew", True, set())
    assert state == "unknown-event"
    assert "reference page" in detail
    assert pair_state("", True, set())[0] == "absent"


def test_the_audit_covers_the_union_of_subscribed_and_handled():
    rows = audit(["app_mention"], ["message.groups"], {"app_mentions:read"})
    assert [r[0] for r in rows] == ["app_mention", "message.groups"]
    assert rows[0][1] == "live"


def test_without_a_subscription_list_a_handler_stands_in_for_one():
    rows = audit([], ["message.groups"], set(), subscriptions_known=False)
    assert rows[0][1] == "undeliverable"
    assert "has never run" in rows[0][2]


def test_with_a_subscription_list_a_handler_is_not_evidence_of_a_subscription():
    rows = audit([], ["message.groups"], {"groups:history"})
    assert rows[0][1] == "idle-scope"


def test_a_handled_undeliverable_event_says_the_handler_has_never_run():
    rows = audit(["message.groups"], ["message.groups"], set())
    assert "has never run" in rows[0][2]
    assert rows[0][3] is True


def test_an_unhandled_undeliverable_event_does_not_claim_a_handler():
    rows = audit(["message.groups"], [], set())
    assert "has never run" not in rows[0][2]


def test_the_handled_gap_is_ranked_above_the_unhandled_one():
    rows = severity(audit(["message.groups", "reaction_added"],
                          ["reaction_added"], set()))
    assert [r[0] for r in rows] == ["reaction_added", "message.groups"]


def test_healthy_rows_sort_below_every_finding():
    rows = severity(audit(["app_mention", "message.groups"], [],
                          {"app_mentions:read"}))
    assert rows[0][1] == "undeliverable"
    assert rows[-1][1] == "live"
''',
"test_js_file": "slack-event-scope-gap.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { audit, pairState, scopeSet, severity } from './slack-event-scope-gap.mjs';

test('the scope header is split and trimmed', () => {
  assert.deepEqual([...scopeSet('channels:read, groups:history ,users:read')].sort(),
    ['channels:read', 'groups:history', 'users:read']);
  assert.equal(scopeSet('').size, 0);
  assert.equal(scopeSet(null).size, 0);
});

test('subscribed and scoped is live', () => {
  const [state, detail] = pairState('message.groups', true, ['groups:history']);
  assert.equal(state, 'live');
  assert.match(detail, /groups:history is granted/);
});

test('subscribed without the scope is the finding', () => {
  const [state, detail] = pairState('message.groups', true, ['channels:history']);
  assert.equal(state, 'undeliverable');
  assert.match(detail, /never delivered and never errors/);
});

test('a scope with no subscription belongs to the other note', () => {
  const [state, detail] = pairState('message.groups', false, ['groups:history']);
  assert.equal(state, 'idle-scope');
  assert.match(detail, /subscription gap rather than a scope gap/);
});

test('neither switch is simply not a feature', () => {
  assert.equal(pairState('message.groups', false, [])[0], 'absent');
});

test('the scope requirement is an or and either option satisfies it', () => {
  assert.equal(pairState('member_joined_channel', true, ['channels:read'])[0], 'live');
  assert.equal(pairState('member_joined_channel', true, ['groups:read'])[0], 'live');
  assert.equal(pairState('member_joined_channel', true, ['users:read'])[0],
    'undeliverable');
});

test('an or list is printed as a choice not a requirement', () => {
  const [, detail] = pairState('member_joined_channel', true, []);
  assert.match(detail, /channels:read or groups:read/);
});

test('an event needing no scope is live on subscription alone', () => {
  assert.equal(pairState('app_home_opened', true, [])[0], 'live');
  assert.equal(pairState('app_home_opened', false, [])[0], 'absent');
});

test('an unrecognised event is reported rather than waved through', () => {
  const [state, detail] = pairState('message.channels.somethingnew', true, []);
  assert.equal(state, 'unknown-event');
  assert.match(detail, /reference page/);
  assert.equal(pairState('', true, [])[0], 'absent');
});

test('the audit covers the union of subscribed and handled', () => {
  const rows = audit(['app_mention'], ['message.groups'], ['app_mentions:read']);
  assert.deepEqual(rows.map((r) => r[0]), ['app_mention', 'message.groups']);
  assert.equal(rows[0][1], 'live');
});

test('without a subscription list a handler stands in for one', () => {
  const rows = audit([], ['message.groups'], [], false);
  assert.equal(rows[0][1], 'undeliverable');
  assert.match(rows[0][2], /has never run/);
});

test('with a subscription list a handler is not evidence of a subscription', () => {
  const rows = audit([], ['message.groups'], ['groups:history']);
  assert.equal(rows[0][1], 'idle-scope');
});

test('a handled undeliverable event says the handler has never run', () => {
  const rows = audit(['message.groups'], ['message.groups'], []);
  assert.match(rows[0][2], /has never run/);
  assert.equal(rows[0][3], true);
});

test('an unhandled undeliverable event does not claim a handler', () => {
  const rows = audit(['message.groups'], [], []);
  assert.doesNotMatch(rows[0][2], /has never run/);
});

test('the handled gap is ranked above the unhandled one', () => {
  const rows = severity(audit(['message.groups', 'reaction_added'],
    ['reaction_added'], []));
  assert.deepEqual(rows.map((r) => r[0]), ['reaction_added', 'message.groups']);
});

test('healthy rows sort below every finding', () => {
  const rows = severity(audit(['app_mention', 'message.groups'], [],
    ['app_mentions:read']));
  assert.equal(rows[0][1], 'undeliverable');
  assert.equal(rows[rows.length - 1][1], 'live');
});
''',
"faq": [
 ("Why is there no missing_scope error for an event that never arrives?",
  "Because missing_scope is a response, and a response needs a request. When you call a method without the scope, Slack refuses the call and names what was needed and what was provided. When an event lacks the scope, Slack simply does not send it: there is no call, no response and nothing to attach an error to. Same grant, opposite direction, and only one of the two directions is loud."),
 ("Where is the scope for each event documented?",
  "On the event's own reference page, which names the scopes that make it deliverable. There is no method that returns the mapping, which is why any detector has to carry a table and why this one reports an event it does not recognise instead of assuming it is fine. If you add an event type this script has not heard of, it will say so rather than pass it."),
 ("I removed a scope during a security review. Could that have done this?",
  "Yes, and it is the most common way in, because the two halves are separated by months. Trimming the grant does not touch the subscription list, so the subscription stays and delivery of that event stops at the next reinstall. Nothing logs it on either side. That is why the repair is to keep the scope and the subscription together in the manifest, where a diff will show one moving without the other."),
 ("The subscription is there and the scope is there. Why is the event still missing?",
  "Then this is not your problem and the next place to look is delivery rather than entitlement. Either the app subscribes to nothing that fires in that conversation type, or the request URL is not receiving, or Slack disabled delivery after sustained failures. Each of those is a separate note, and the script's clear verdict is meant to move you on rather than leave you rereading the scope list."),
 ("Does adding the scope fix it immediately?",
  "No. A token carries the grant it was issued with, so the app has to be reinstalled and the stored token replaced before anything changes. For a distributed app that means every installation re-authorizes, which is a rollout rather than a config change. Check the X-OAuth-Scopes header afterwards, because that header is the only thing that tells you the new grant actually landed."),
],
"related": [
 ("/slack/missing-scope-on-read/", "the same gap on a method call, where Slack tells you"),
 ("/slack/no-event-subscriptions/", "the other half of the pair: scope held, nothing subscribed"),
 ("/slack/over-broad-scopes/", "the same grant read for surplus rather than for gaps"),
],
"citations": [CITE_EVENTS, CITE_EVENT_TYPES, CITE_SCOPES, CITE_MANIFEST],
})

GUIDES.append({
"slug": "message-subtypes-ignored",
"title": "Edits, joins and deletes handled as brand new messages",
"description": "A message event with a subtype is not a new message. message_changed hides the text under event.message, and joins arrive with text a handler will answer.",
"h1": "Edits, joins and deletes handled as brand new messages",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack message subtype", "slack message_changed event",
             "slack channel_join event handler", "slack bot replies to edits",
             "slack event.text undefined"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Somebody fixes a typo in a message they posted an hour ago, and the bot answers it again. Somebody joins the channel, and the ticket pipeline opens a ticket for &ldquo;Ana has joined the channel&rdquo;. Somebody deletes a message, and it turns up in the archive anyway, which is the version of this bug that ends up in a compliance conversation.</p><p>The handler is reading <code>event.text</code> on every <code>message</code> event it receives. Most <code>message</code> events are not new messages.",
"short_answer": """<p><code>message</code> is not one event. It is a family, distinguished by a <code>subtype</code> field: <code>message_changed</code>, <code>message_deleted</code>, <code>channel_join</code>, <code>channel_leave</code>, <code>bot_message</code>, <code>file_share</code>, <code>thread_broadcast</code>, <code>message_replied</code>, <code>tombstone</code> and more. A handler that reads <code>event.text</code> and replies treats every one of them as a person saying something new.</p>
<p>The nastiest member is <code>message_changed</code>, because the payload is a different shape: the current text is at <code>event.message.text</code> and the previous version at <code>event.previous_message.text</code>, so <code>event.text</code> is missing entirely and code that reads it gets <code>None</code> rather than an error. The script reads <code>conversations.history</code>, where the same edit shows up as an <code>edited</code> block on the message, counts what share of recent traffic is not a plain new message, and then looks for the proof: app replies clustered after an <code>edited.ts</code> instead of the original <code>ts</code>.</p>""",
"problem": """<p>The first version of a Slack handler is four lines long and it works. It subscribes to <code>message.channels</code>, reads <code>event.text</code>, matches a keyword and replies. Every message anybody sends in the test channel is a plain new message, so the four lines are correct for the entire time anybody is watching.</p>
<p>Then the app meets a real channel. People join and leave, and Slack writes those into the conversation as messages with a <code>subtype</code> and a <code>text</code> that reads "Ana has joined the channel" - which means a keyword matcher will happily match on it. People edit messages, and the edit arrives as a whole new delivery with a nested payload, so the reply pipeline fires a second time on content it has already answered. People delete messages, and an archiver that treats the deletion as an arrival stores the thing that was just withdrawn. Files get shared, and a message with an empty <code>text</code> and everything of interest in <code>event.files</code> gets logged as a blank line.</p>
<p>None of this errors. Every one of those payloads is a valid <code>message</code> event, delivered correctly, and the handler processes each of them without complaint. The symptom is downstream and looks like a data problem: the archive has three copies of one message, the ticket queue has an entry with somebody's join line in it, the reply log has a response to a message nobody sent. By the time it is noticed the pipeline has months of it, and reconstructing which rows are real means knowing which subtypes were being swallowed.</p>""",
"why": """<p><strong>This is not the echo loop.</strong> The echo loop is the app reacting to its own output, and it is loud, fast and visible as a run of self-authored messages. This is the app mis-reading traffic from people, one message at a time, at a rate nobody notices. The two overlap on exactly one subtype, <code>bot_message</code>, and this script hands that row to the other note rather than claiming it.</p>
<p><strong><code>message_changed</code> is a different payload shape, not a flag on the same one.</strong> The text moves to <code>event.message.text</code>, the prior version appears at <code>event.previous_message.text</code>, and <code>event.text</code> is simply not there. In Python that is a <code>None</code>; in JavaScript it is <code>undefined</code>, which then gets concatenated into a string and stored. Neither one raises.</p>
<p><strong>Join and leave lines carry text a matcher will match.</strong> They are not empty and they are not marked in any way that a naive read notices. Anything doing keyword matching, sentiment, indexing or ticket creation will act on them, which is why joins show up as the first reported symptom more often than edits do.</p>
<p><strong>History shows edits differently from the event stream, and that is what makes this detectable.</strong> Over the Events API an edit arrives as <code>message_changed</code>. In <code>conversations.history</code> the same edit is a plain message carrying an <code>edited: {user, ts}</code> object. So a read-only script can find the edits and then check whether your app replied at the edit time rather than the original time, which is the closest thing to proof available without seeing your handler.</p>
<p><strong>Bolt filters one of these for you and not the rest.</strong> <code>app.message()</code> drops <code>bot_message</code>, which is enough to stop the loop and is frequently mistaken for subtype handling in general. Joins, leaves, edits and deletions all still arrive.</p>""",
"steps": [
 {"h": "Sample real history rather than a test channel",
  "body": """<p>A test channel is all plain messages, which is why this survives review. <code>conversations.history</code> on a channel people actually use will contain joins, edits and file shares within the first two hundred messages, and those are the payload shapes your handler has been seeing.</p>"""},
 {"h": "Classify every message and say where its text actually lives",
  "body": """<p><code>classify</code> returns the kind, the field the real content is in, and what a handler should do with it. The <code>text_path</code> is the useful column: <code>message.text</code> for an edit, <code>previous_message.text</code> for a deletion, <code>files</code> for a share. It is the list somebody needs open while they write the branch.</p>"""},
 {"h": "Count the share of traffic that is not a plain new message",
  "body": """<p><code>profile</code> turns the sample into one number. A channel where a fifth of recent messages carry a subtype or an edit is a channel where a handler with no subtype branch is wrong a fifth of the time, and that number is what makes the case to prioritise the fix.</p>"""},
 {"h": "Look for replies that land at the edit time instead of the original time",
  "body": """<p><code>edit_echo</code> is the proof. If your app replied within a short window after an <code>edited.ts</code> but not after the original <code>ts</code>, it processed the edit as a new message. If it replied after both, that is inconclusive and gets reported as inconclusive rather than as a finding.</p>"""},
 {"h": "Hand bot_message to the note that owns it",
  "body": """<p>Self-authored messages are classified as <code>elsewhere</code>, with a pointer. Two audits reporting the same row is how a team ends up fixing it twice, or arguing about which report is right, so this one declines the overlap explicitly.</p>"""},
 {"h": "Print the branch, with the default at the bottom",
  "body": """<p>The repair is a switch on <code>subtype</code> where the <em>absent</em> case is the plain new message and everything else is named: read <code>message.text</code> for <code>message_changed</code>, ignore <code>channel_join</code>, <code>channel_leave</code> and <code>message_deleted</code> unless you want them, and treat <code>file_share</code> and <code>thread_broadcast</code> as real content.</p>"""},
],
"verify": """<p>After the branch ships, re-run against the same channel. The profile will be unchanged, because it describes the workspace rather than your code, and the edit correlation should be the part that goes quiet.</p>
<pre><code class="language-bash">python3 slack_message_subtypes.py --channel C01ABCDE9
# identity   U0APPBOT11 in acme
# profile    200 message(s): 148 plain, 41 subtyped, 11 edited, 26.0% not a new message
# kind       channel_join    22  ignore     joins carry text a keyword matcher will match
# kind       file_share       9  content    real content, and event.text is often empty
# kind       message_changed  0  branch     the text is at event.message.text
# kind       bot_message     10  elsewhere  self authored; the echo loop note owns this row
# edits      clean          0 of 11 edit(s) were followed by a reply</code></pre>""",
"code_intro": "One read method and three pure functions. <code>classify</code> is the table somebody wants open while writing the branch: for each subtype, where the content actually lives and what to do with it. <code>profile</code> reduces a page of history to the share of traffic a subtype-blind handler gets wrong. <code>edit_echo</code> is the only part that tries to prove anything, correlating your app's replies against edit timestamps rather than original ones, and it is written to return inconclusive far more often than it returns a finding.",
"py_file": "slack_message_subtypes.py",
"py": '''"""Measure how much of a channel's traffic is not a plain new message.

Read only. auth.test for identity and conversations.history per channel.
Nothing is posted, edited or deleted: this reports which subtypes your handler
has been receiving, where the real content lives in each of them, and whether
your app's replies line up with edit timestamps rather than original ones.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_message_subtypes")

API = "https://slack.com/api/"

# subtype -> (where the real content is, what to do with it, why).
# The disposition column is the one to read. "elsewhere" appears once, for
# bot_message, because the loop that subtype causes is a different note and two
# audits reporting one row is how a team fixes it twice.
SUBTYPES = {
    "message_changed": ("message.text", "branch",
                        "the current text is at event.message.text and the previous "
                        "version at event.previous_message.text; event.text is absent"),
    "message_deleted": ("previous_message.text", "ignore",
                        "the message was withdrawn; an archiver that stores this "
                        "stores the thing that was just deleted"),
    "message_replied": ("message.text", "ignore",
                        "a metadata update on a thread parent, not a new message"),
    "channel_join": ("text", "ignore",
                     "joins carry text a keyword matcher will match"),
    "channel_leave": ("text", "ignore", "the same, for leaving"),
    "channel_topic": ("text", "ignore", "a topic change written as a message"),
    "channel_purpose": ("text", "ignore", "a purpose change written as a message"),
    "channel_name": ("text", "ignore", "a rename written as a message"),
    "channel_archive": ("text", "ignore", "an archive written as a message"),
    "channel_unarchive": ("text", "ignore", "an unarchive written as a message"),
    "tombstone": ("text", "ignore", "a placeholder left where a message was removed"),
    "bot_message": ("text", "elsewhere",
                    "an app authored message; the loop this causes has its own note "
                    "and this script does not claim the row"),
    "file_share": ("files", "content",
                   "real content, and event.text is often empty because the point "
                   "of the message is in event.files"),
    "thread_broadcast": ("text", "content",
                         "a real threaded message also sent to the channel; expect "
                         "to see it twice if you read replies as well"),
    "me_message": ("text", "content", "a real message typed with /me"),
}


def classify(message):
    """What kind of message event is this, and where is its content? Pure.

    Returns (kind, text_path, disposition, note). The kind that matters most is
    edited-in-place: in conversations.history an edit appears as a plain
    message carrying an edited block, while the Events API delivered the very
    same edit to your handler as a message_changed with a different shape.
    """
    m = message or {}
    subtype = str(m.get("subtype") or "").strip()
    if not subtype:
        if m.get("edited"):
            return ("edited-in-place", "message.text", "branch",
                    "history shows this as a plain message with an edited block; "
                    "over the Events API the same edit arrived as message_changed, "
                    "which is the payload your handler actually saw")
        return ("plain", "text", "new-message",
                "a genuine new message from a person, and the only kind event.text "
                "is the right field for")
    known = SUBTYPES.get(subtype)
    if not known:
        return (subtype, "text", "unknown-subtype",
                "not in this script's table; read the message event reference "
                "before letting it fall through to the new message path")
    path, disposition, note = known
    return (subtype, path, disposition, note)


def profile(messages):
    """Reduce a page of history to the share a subtype-blind handler gets wrong. Pure.

    Returns a dict with the counts and one percentage. The percentage is the
    argument: a handler with no subtype branch is wrong that often, in this
    channel, today.
    """
    kinds = {}
    plain = subtyped = edited = 0
    rows = list(messages or [])
    for m in rows:
        kind, _, disposition, note = classify(m)
        entry = kinds.setdefault(kind, {"count": 0, "disposition": disposition,
                                        "note": note})
        entry["count"] += 1
        if kind == "plain":
            plain += 1
        elif kind == "edited-in-place":
            edited += 1
        else:
            subtyped += 1
    total = len(rows)
    off = total - plain
    return {"total": total, "plain": plain, "subtyped": subtyped, "edited": edited,
            "share_percent": round(off * 100.0 / total, 1) if total else 0.0,
            "kinds": kinds}


def edit_echo(messages, bot_id, bot_user, window=90.0):
    """Did the app reply at the edit time rather than at the original time? Pure.

    Returns rows of (edited_ts, original_ts, verdict, detail). Written to
    return inconclusive readily: a reply after both timestamps proves nothing,
    and an edit made seconds after the original cannot be separated from it at
    all.
    """
    replies = []
    edits = []
    for m in messages or []:
        ts = float(m.get("ts") or 0)
        ours = bool(bot_id and m.get("bot_id") == bot_id) or bool(
            bot_user and m.get("user") == bot_user)
        if ours:
            replies.append(ts)
            continue
        edited = m.get("edited") or {}
        if edited.get("ts"):
            edits.append((float(edited["ts"]), ts))
    replies.sort()

    w = float(window)
    out = []
    for edited_ts, original_ts in sorted(edits):
        if edited_ts - original_ts <= w:
            out.append((edited_ts, original_ts, "too-close",
                        "the edit landed within the correlation window of the "
                        "original, so a reply cannot be attributed to either"))
            continue
        after_edit = [r for r in replies if edited_ts <= r <= edited_ts + w]
        after_original = [r for r in replies if original_ts <= r <= original_ts + w]
        if after_edit and not after_original:
            out.append((edited_ts, original_ts, "reprocessed",
                        "%d reply(ies) within %.0fs of the edit and none within "
                        "%.0fs of the original message: the edit was handled as a "
                        "new message" % (len(after_edit), w, w)))
        elif after_edit and after_original:
            out.append((edited_ts, original_ts, "inconclusive",
                        "replies near both timestamps; a long thread can produce "
                        "this without any subtype bug"))
        else:
            out.append((edited_ts, original_ts, "clean",
                        "no reply followed this edit"))
    return out


def get(session, method, params, label):
    """One GET, asserting on the body rather than the status line."""
    r = session.get(API + method, params=params or {}, timeout=30)
    body = r.json()
    if body.get("ok") is not True:
        log.warning("%-10s %-14s %s", label, "unavailable", body.get("error"))
        return None
    return body


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN",
                    help="environment variable holding the bot token")
    ap.add_argument("--channel", action="append", default=[],
                    help="a channel ID your handler serves; repeatable")
    ap.add_argument("--limit", type=int, default=200,
                    help="messages sampled per channel")
    ap.add_argument("--window", type=float, default=90.0,
                    help="seconds after an edit in which a reply counts as caused by it")
    args = ap.parse_args()

    token = os.environ.get(args.token_env)
    if not token:
        log.error("set %s (channels:history is enough)", args.token_env)
        return 2
    if not args.channel:
        log.error("pass at least one --channel; a test channel is all plain "
                  "messages and will show you nothing")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + token})
    who = get(s, "auth.test", {}, "auth.test")
    if not who:
        return 2
    bot_user, bot_id = who.get("user_id") or "", who.get("bot_id") or ""
    log.info("identity   %s in %s", bot_user, who.get("team"))

    findings = 0
    for channel in args.channel:
        body = get(s, "conversations.history",
                   {"channel": channel, "limit": str(args.limit)}, "history")
        if not body:
            continue
        messages = body.get("messages") or []
        p = profile(messages)
        (log.warning if p["share_percent"] >= 10.0 else log.info)(
            "profile    %d message(s): %d plain, %d subtyped, %d edited, %.1f%% "
            "not a new message", p["total"], p["plain"], p["subtyped"],
            p["edited"], p["share_percent"])
        for kind, info in sorted(p["kinds"].items(),
                                 key=lambda kv: (-kv[1]["count"], kv[0])):
            if kind == "plain":
                continue
            (log.warning if info["disposition"] in ("branch", "unknown-subtype")
             else log.info)("kind       %-16s %3d  %-10s %s", kind, info["count"],
                            info["disposition"], info["note"])
            if info["disposition"] in ("branch", "unknown-subtype"):
                findings += 1

        rows = edit_echo(messages, bot_id, bot_user, args.window)
        caught = [r for r in rows if r[2] == "reprocessed"]
        if caught:
            findings += len(caught)
            for edited_ts, original_ts, _, detail in caught:
                log.warning("edits      reprocessed    edit at %.6f of a message "
                            "posted at %.6f: %s", edited_ts, original_ts, detail)
        else:
            log.info("edits      clean          %d of %d edit(s) were followed by "
                     "a reply", 0, len(rows))

    if findings:
        log.warning("  repair: switch on event.subtype with the absent case as the "
                    "plain new message, and name every other branch explicitly")
        log.warning("  repair: for message_changed read event.message.text and "
                    "compare it against event.previous_message.text; event.text "
                    "is not there")
        log.warning("  repair: ignore channel_join, channel_leave and "
                    "message_deleted unless you specifically want them, and treat "
                    "file_share and thread_broadcast as real content")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-message-subtypes.mjs",
"js": '''/**
 * Measure how much of a channel's traffic is not a plain new message.
 *
 * Read only. auth.test for identity and conversations.history per channel.
 * Nothing is posted, edited or deleted: this reports which subtypes your
 * handler has been receiving, where the real content lives in each of them,
 * and whether your app's replies line up with edit timestamps rather than
 * original ones.
 */

const API = 'https://slack.com/api/';

// subtype -> [where the real content is, what to do with it, why].
// "elsewhere" appears once, for bot_message, because the loop that subtype
// causes is a different note and two audits reporting one row is how a team
// fixes it twice.
const SUBTYPES = new Map([
  ['message_changed', ['message.text', 'branch',
    'the current text is at event.message.text and the previous version at ' +
    'event.previous_message.text; event.text is absent']],
  ['message_deleted', ['previous_message.text', 'ignore',
    'the message was withdrawn; an archiver that stores this stores the thing ' +
    'that was just deleted']],
  ['message_replied', ['message.text', 'ignore',
    'a metadata update on a thread parent, not a new message']],
  ['channel_join', ['text', 'ignore', 'joins carry text a keyword matcher will match']],
  ['channel_leave', ['text', 'ignore', 'the same, for leaving']],
  ['channel_topic', ['text', 'ignore', 'a topic change written as a message']],
  ['channel_purpose', ['text', 'ignore', 'a purpose change written as a message']],
  ['channel_name', ['text', 'ignore', 'a rename written as a message']],
  ['channel_archive', ['text', 'ignore', 'an archive written as a message']],
  ['channel_unarchive', ['text', 'ignore', 'an unarchive written as a message']],
  ['tombstone', ['text', 'ignore', 'a placeholder left where a message was removed']],
  ['bot_message', ['text', 'elsewhere',
    'an app authored message; the loop this causes has its own note and this ' +
    'script does not claim the row']],
  ['file_share', ['files', 'content',
    'real content, and event.text is often empty because the point of the ' +
    'message is in event.files']],
  ['thread_broadcast', ['text', 'content',
    'a real threaded message also sent to the channel; expect to see it twice ' +
    'if you read replies as well']],
  ['me_message', ['text', 'content', 'a real message typed with /me']],
]);

/**
 * What kind of message event is this, and where is its content? Pure.
 * edited-in-place is the kind that matters most: history shows an edit as a
 * plain message with an edited block, while the Events API delivered that same
 * edit to your handler as a message_changed with a different shape.
 */
export function classify(message) {
  const m = message ?? {};
  const subtype = String(m.subtype ?? '').trim();
  if (!subtype) {
    if (m.edited) {
      return ['edited-in-place', 'message.text', 'branch',
        'history shows this as a plain message with an edited block; over the ' +
        'Events API the same edit arrived as message_changed, which is the payload ' +
        'your handler actually saw'];
    }
    return ['plain', 'text', 'new-message',
      'a genuine new message from a person, and the only kind event.text is the ' +
      'right field for'];
  }
  const known = SUBTYPES.get(subtype);
  if (!known) {
    return [subtype, 'text', 'unknown-subtype',
      "not in this script's table; read the message event reference before letting " +
      'it fall through to the new message path'];
  }
  const [path, disposition, note] = known;
  return [subtype, path, disposition, note];
}

/**
 * Reduce a page of history to the share a subtype-blind handler gets wrong. Pure.
 * The percentage is the argument.
 */
export function profile(messages) {
  const kinds = new Map();
  let plain = 0;
  let subtyped = 0;
  let edited = 0;
  const rows = [...(messages ?? [])];
  for (const m of rows) {
    const [kind, , disposition, note] = classify(m);
    if (!kinds.has(kind)) kinds.set(kind, { count: 0, disposition, note });
    kinds.get(kind).count += 1;
    if (kind === 'plain') plain += 1;
    else if (kind === 'edited-in-place') edited += 1;
    else subtyped += 1;
  }
  const total = rows.length;
  const off = total - plain;
  return {
    total,
    plain,
    subtyped,
    edited,
    sharePercent: total ? Math.round((off * 1000.0) / total) / 10 : 0.0,
    kinds,
  };
}

/**
 * Did the app reply at the edit time rather than at the original time? Pure.
 * Written to return inconclusive readily: a reply after both timestamps proves
 * nothing, and an edit made seconds after the original cannot be separated.
 */
export function editEcho(messages, botId, botUser, window = 90.0) {
  const replies = [];
  const edits = [];
  for (const m of messages ?? []) {
    const ts = Number(m.ts ?? 0);
    const ours = (botId && m.bot_id === botId) || (botUser && m.user === botUser);
    if (ours) { replies.push(ts); continue; }
    const edited = m.edited ?? {};
    if (edited.ts) edits.push([Number(edited.ts), ts]);
  }
  replies.sort((a, b) => a - b);

  const w = Number(window);
  const out = [];
  for (const [editedTs, originalTs] of edits.sort((a, b) => a[0] - b[0])) {
    if (editedTs - originalTs <= w) {
      out.push([editedTs, originalTs, 'too-close',
        'the edit landed within the correlation window of the original, so a reply ' +
        'cannot be attributed to either']);
      continue;
    }
    const afterEdit = replies.filter((r) => r >= editedTs && r <= editedTs + w);
    const afterOriginal = replies.filter((r) => r >= originalTs && r <= originalTs + w);
    if (afterEdit.length && !afterOriginal.length) {
      out.push([editedTs, originalTs, 'reprocessed',
        `${afterEdit.length} reply(ies) within ${w.toFixed(0)}s of the edit and none ` +
        `within ${w.toFixed(0)}s of the original message: the edit was handled as a ` +
        'new message']);
    } else if (afterEdit.length) {
      out.push([editedTs, originalTs, 'inconclusive',
        'replies near both timestamps; a long thread can produce this without any ' +
        'subtype bug']);
    } else {
      out.push([editedTs, originalTs, 'clean', 'no reply followed this edit']);
    }
  }
  return out;
}

async function get(token, method, params, label) {
  const qs = new URLSearchParams(params ?? {});
  const res = await fetch(`${API}${method}?${qs}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const body = await res.json();
  if (body.ok !== true) {
    console.warn(`${label.padEnd(10)} ${'unavailable'.padEnd(14)} ${body.error}`);
    return null;
  }
  return body;
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

async function main() {
  const args = process.argv.slice(2);
  const tokenEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
  const token = process.env[tokenEnv];
  if (!token) {
    console.error(`set ${tokenEnv} (channels:history is enough)`);
    process.exitCode = 2;
    return;
  }
  const channels = argAll(args, '--channel');
  if (!channels.length) {
    console.error('pass at least one --channel; a test channel is all plain messages ' +
      'and will show you nothing');
    process.exitCode = 2;
    return;
  }
  const limit = arg(args, '--limit', '200');
  const window = Number(arg(args, '--window', 90));

  const who = await get(token, 'auth.test', {}, 'auth.test');
  if (!who) { process.exitCode = 2; return; }
  const botUser = who.user_id ?? '';
  const botId = who.bot_id ?? '';
  console.log(`identity   ${botUser} in ${who.team}`);

  let findings = 0;
  for (const channel of channels) {
    const body = await get(token, 'conversations.history',
      { channel, limit: String(limit) }, 'history');
    if (!body) continue;
    const messages = body.messages ?? [];
    const p = profile(messages);
    (p.sharePercent >= 10.0 ? console.warn : console.log)(
      `profile    ${p.total} message(s): ${p.plain} plain, ${p.subtyped} subtyped, ` +
      `${p.edited} edited, ${p.sharePercent}% not a new message`);
    const kinds = [...p.kinds.entries()]
      .sort((a, b) => b[1].count - a[1].count || a[0].localeCompare(b[0]));
    for (const [kind, info] of kinds) {
      if (kind === 'plain') continue;
      const loud = info.disposition === 'branch' || info.disposition === 'unknown-subtype';
      (loud ? console.warn : console.log)(
        `kind       ${kind.padEnd(16)} ${String(info.count).padStart(3)}  ` +
        `${info.disposition.padEnd(10)} ${info.note}`);
      if (loud) findings += 1;
    }

    const rows = editEcho(messages, botId, botUser, window);
    const caught = rows.filter((r) => r[2] === 'reprocessed');
    if (caught.length) {
      findings += caught.length;
      for (const [editedTs, originalTs, , detail] of caught) {
        console.warn(`edits      reprocessed    edit at ${editedTs} of a message ` +
          `posted at ${originalTs}: ${detail}`);
      }
    } else {
      console.log(`edits      clean          0 of ${rows.length} edit(s) were ` +
        'followed by a reply');
    }
  }

  if (findings) {
    console.warn('  repair: switch on event.subtype with the absent case as the plain ' +
      'new message, and name every other branch explicitly');
    console.warn('  repair: for message_changed read event.message.text and compare it ' +
      'against event.previous_message.text; event.text is not there');
    console.warn('  repair: ignore channel_join, channel_leave and message_deleted ' +
      'unless you specifically want them, and treat file_share and thread_broadcast ' +
      'as real content');
    process.exitCode = 1;
  }
}

// Only run when invoked directly, so importing this module in the tests does
// not execute main() and fail the file on a missing token.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The assertions worth arguing about are the two that decline to fire. <code>bot_message</code> has to come back as <code>elsewhere</code>, because the echo loop is a different note and a row reported twice gets fixed twice or not at all. And an edit made seconds after the original message has to come back as <code>too-close</code> rather than as a finding: the correlation this script rests on needs the two timestamps to be separable, and pretending otherwise would turn a typo fixed on the spot into a bug report.",
"test_py_file": "test_slack_message_subtypes.py",
"test_py": '''from slack_message_subtypes import classify, edit_echo, profile


def msg(ts, subtype=None, text="", user="U9", bot_id="", edited_ts=None):
    m = {"ts": str(ts), "text": text, "user": user}
    if subtype:
        m["subtype"] = subtype
    if bot_id:
        m["bot_id"] = bot_id
    if edited_ts is not None:
        m["edited"] = {"user": user, "ts": str(edited_ts)}
    return m


def test_a_plain_message_is_the_only_kind_event_text_is_right_for():
    kind, path, disposition, note = classify(msg(10, text="deploy please"))
    assert (kind, path, disposition) == ("plain", "text", "new-message")
    assert "event.text" in note


def test_message_changed_hides_the_text_one_level_down():
    kind, path, disposition, note = classify({"subtype": "message_changed"})
    assert (kind, path, disposition) == ("message_changed", "message.text", "branch")
    assert "previous_message" in note


def test_a_history_message_with_an_edited_block_is_the_same_bug_seen_from_history():
    kind, path, disposition, note = classify(msg(10, text="typo", edited_ts=99))
    assert kind == "edited-in-place"
    assert path == "message.text"
    assert disposition == "branch"
    assert "message_changed" in note


def test_joins_and_leaves_carry_text_and_must_be_ignored_deliberately():
    assert classify(msg(10, "channel_join", "Ana has joined the channel"))[2] == "ignore"
    assert classify(msg(11, "channel_leave"))[2] == "ignore"
    assert classify(msg(12, "message_deleted"))[2] == "ignore"


def test_a_deletion_points_at_the_previous_message_for_its_content():
    assert classify(msg(10, "message_deleted"))[1] == "previous_message.text"


def test_bot_message_is_handed_to_the_echo_loop_note_not_claimed():
    kind, _, disposition, note = classify(msg(10, "bot_message", bot_id="B1"))
    assert kind == "bot_message"
    assert disposition == "elsewhere"
    assert "own note" in note


def test_file_shares_and_broadcasts_are_real_content():
    assert classify(msg(10, "file_share"))[2] == "content"
    assert classify(msg(10, "file_share"))[1] == "files"
    assert classify(msg(11, "thread_broadcast"))[2] == "content"


def test_an_unrecognised_subtype_is_reported_rather_than_treated_as_new():
    kind, _, disposition, note = classify(msg(10, "some_future_subtype"))
    assert kind == "some_future_subtype"
    assert disposition == "unknown-subtype"
    assert "reference" in note


def test_the_profile_counts_the_share_a_blind_handler_gets_wrong():
    p = profile([msg(1), msg(2), msg(3, "channel_join"), msg(4, text="x", edited_ts=9)])
    assert p["total"] == 4
    assert p["plain"] == 2
    assert p["subtyped"] == 1
    assert p["edited"] == 1
    assert p["share_percent"] == 50.0


def test_an_empty_sample_does_not_divide_by_zero():
    p = profile([])
    assert p["total"] == 0 and p["share_percent"] == 0.0 and p["kinds"] == {}


def test_the_profile_keeps_the_disposition_with_each_kind():
    p = profile([msg(1, "channel_join"), msg(2, "channel_join")])
    assert p["kinds"]["channel_join"]["count"] == 2
    assert p["kinds"]["channel_join"]["disposition"] == "ignore"


def test_a_reply_after_the_edit_and_not_the_original_is_the_proof():
    rows = edit_echo([msg(1000, text="typo", edited_ts=5000),
                      msg(5010, bot_id="B1", user="U1")], "B1", "U1")
    assert rows[0][2] == "reprocessed"
    assert "handled as a new message" in rows[0][3]


def test_a_reply_to_the_original_and_to_the_edit_is_inconclusive():
    rows = edit_echo([msg(1000, text="typo", edited_ts=5000),
                      msg(1010, bot_id="B1", user="U1"),
                      msg(5010, bot_id="B1", user="U1")], "B1", "U1")
    assert rows[0][2] == "inconclusive"


def test_an_edit_with_no_reply_after_it_is_clean():
    rows = edit_echo([msg(1000, text="typo", edited_ts=5000)], "B1", "U1")
    assert rows[0][2] == "clean"


def test_an_edit_made_seconds_later_cannot_be_separated_from_the_original():
    rows = edit_echo([msg(1000, text="typo", edited_ts=1020),
                      msg(1030, bot_id="B1", user="U1")], "B1", "U1")
    assert rows[0][2] == "too-close"


def test_another_apps_reply_is_not_counted_as_ours():
    rows = edit_echo([msg(1000, text="typo", edited_ts=5000),
                      msg(5010, bot_id="B_OTHER", user="U_OTHER")], "B1", "U1")
    assert rows[0][2] == "clean"


def test_history_with_no_edits_produces_no_rows():
    assert edit_echo([msg(1), msg(2, "channel_join")], "B1", "U1") == []
''',
"test_js_file": "slack-message-subtypes.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { classify, editEcho, profile } from './slack-message-subtypes.mjs';

function msg(ts, subtype = null, text = '', user = 'U9', botId = '', editedTs = null) {
  const m = { ts: String(ts), text, user };
  if (subtype) m.subtype = subtype;
  if (botId) m.bot_id = botId;
  if (editedTs !== null) m.edited = { user, ts: String(editedTs) };
  return m;
}

test('a plain message is the only kind event.text is right for', () => {
  const [kind, path, disposition, note] = classify(msg(10, null, 'deploy please'));
  assert.deepEqual([kind, path, disposition], ['plain', 'text', 'new-message']);
  assert.match(note, /event\\.text/);
});

test('message_changed hides the text one level down', () => {
  const [kind, path, disposition, note] = classify({ subtype: 'message_changed' });
  assert.deepEqual([kind, path, disposition],
    ['message_changed', 'message.text', 'branch']);
  assert.match(note, /previous_message/);
});

test('a history message with an edited block is the same bug seen from history', () => {
  const [kind, path, disposition, note] = classify(msg(10, null, 'typo', 'U9', '', 99));
  assert.equal(kind, 'edited-in-place');
  assert.equal(path, 'message.text');
  assert.equal(disposition, 'branch');
  assert.match(note, /message_changed/);
});

test('joins and leaves carry text and must be ignored deliberately', () => {
  assert.equal(classify(msg(10, 'channel_join', 'Ana has joined the channel'))[2],
    'ignore');
  assert.equal(classify(msg(11, 'channel_leave'))[2], 'ignore');
  assert.equal(classify(msg(12, 'message_deleted'))[2], 'ignore');
});

test('a deletion points at the previous message for its content', () => {
  assert.equal(classify(msg(10, 'message_deleted'))[1], 'previous_message.text');
});

test('bot_message is handed to the echo loop note not claimed', () => {
  const [kind, , disposition, note] = classify(msg(10, 'bot_message', '', 'U9', 'B1'));
  assert.equal(kind, 'bot_message');
  assert.equal(disposition, 'elsewhere');
  assert.match(note, /own note/);
});

test('file shares and broadcasts are real content', () => {
  assert.equal(classify(msg(10, 'file_share'))[2], 'content');
  assert.equal(classify(msg(10, 'file_share'))[1], 'files');
  assert.equal(classify(msg(11, 'thread_broadcast'))[2], 'content');
});

test('an unrecognised subtype is reported rather than treated as new', () => {
  const [kind, , disposition, note] = classify(msg(10, 'some_future_subtype'));
  assert.equal(kind, 'some_future_subtype');
  assert.equal(disposition, 'unknown-subtype');
  assert.match(note, /reference/);
});

test('the profile counts the share a blind handler gets wrong', () => {
  const p = profile([msg(1), msg(2), msg(3, 'channel_join'),
    msg(4, null, 'x', 'U9', '', 9)]);
  assert.equal(p.total, 4);
  assert.equal(p.plain, 2);
  assert.equal(p.subtyped, 1);
  assert.equal(p.edited, 1);
  assert.equal(p.sharePercent, 50.0);
});

test('an empty sample does not divide by zero', () => {
  const p = profile([]);
  assert.equal(p.total, 0);
  assert.equal(p.sharePercent, 0.0);
  assert.equal(p.kinds.size, 0);
});

test('the profile keeps the disposition with each kind', () => {
  const p = profile([msg(1, 'channel_join'), msg(2, 'channel_join')]);
  assert.equal(p.kinds.get('channel_join').count, 2);
  assert.equal(p.kinds.get('channel_join').disposition, 'ignore');
});

test('a reply after the edit and not the original is the proof', () => {
  const rows = editEcho([msg(1000, null, 'typo', 'U9', '', 5000),
    msg(5010, null, '', 'U1', 'B1')], 'B1', 'U1');
  assert.equal(rows[0][2], 'reprocessed');
  assert.match(rows[0][3], /handled as a new message/);
});

test('a reply to the original and to the edit is inconclusive', () => {
  const rows = editEcho([msg(1000, null, 'typo', 'U9', '', 5000),
    msg(1010, null, '', 'U1', 'B1'), msg(5010, null, '', 'U1', 'B1')], 'B1', 'U1');
  assert.equal(rows[0][2], 'inconclusive');
});

test('an edit with no reply after it is clean', () => {
  const rows = editEcho([msg(1000, null, 'typo', 'U9', '', 5000)], 'B1', 'U1');
  assert.equal(rows[0][2], 'clean');
});

test('an edit made seconds later cannot be separated from the original', () => {
  const rows = editEcho([msg(1000, null, 'typo', 'U9', '', 1020),
    msg(1030, null, '', 'U1', 'B1')], 'B1', 'U1');
  assert.equal(rows[0][2], 'too-close');
});

test('another apps reply is not counted as ours', () => {
  const rows = editEcho([msg(1000, null, 'typo', 'U9', '', 5000),
    msg(5010, null, '', 'U_OTHER', 'B_OTHER')], 'B1', 'U1');
  assert.equal(rows[0][2], 'clean');
});

test('history with no edits produces no rows', () => {
  assert.deepEqual(editEcho([msg(1), msg(2, 'channel_join')], 'B1', 'U1'), []);
});
''',
"faq": [
 ("How is this different from the bot replying to its own messages?",
  "Direction. The echo loop is the app reacting to its own output and it is loud: a run of self-authored messages seconds apart, usually noticed within minutes. This is the app mis-reading traffic from people, one message at a time, and it can run for months. They meet at exactly one subtype, bot_message, and this script classifies that row as elsewhere so the two audits do not both claim it."),
 ("Why does event.text come back empty on an edit instead of raising?",
  "Because message_changed is a differently shaped payload rather than the same payload with a flag. The current text moved to event.message.text and the previous version sits at event.previous_message.text, so event.text simply is not a key. Reading an absent key gives you None in Python and undefined in JavaScript, both of which flow onward and get stored rather than throwing."),
 ("Does Bolt handle subtypes for me?",
  "Partly, and the part it handles is the one that makes people think the rest is handled too. app.message() filters bot_message, which stops the echo loop. Joins, leaves, edits, deletions, file shares and thread broadcasts all still reach your listener as message events, and you still have to branch on subtype yourself."),
 ("Can this script tell me for certain that my handler is broken?",
  "No, and it says so in the output. Nothing in the Web API reports what your handler did with an event. What the script can show is the share of traffic that is not a plain new message, which is how often a subtype-blind handler is wrong, and one correlation: replies clustered after an edit timestamp and not after the original. That correlation is evidence, and the script reports inconclusive whenever it is not clean evidence."),
 ("Should I subscribe to message.channels at all?",
  "Only if you genuinely want every message in every channel the app is in. If what you actually want is to be addressed, app_mention is a much smaller and much better-behaved firehose: it fires when somebody names the app, it does not fire on joins and leaves, and it does not fire on your own posts. Most handlers that struggle with subtypes are subscribed one level too broadly."),
],
"related": [
 ("/slack/bot-message-echo-loop/", "the one subtype this note hands over"),
 ("/slack/duplicate-messages-no-dedupe/", "duplicates that come from delivery, not from subtypes"),
 ("/slack/non-marketplace-history-clamp/", "the fifteen message clamp that shrinks this sample"),
],
"citations": [CITE_MESSAGE_EVENT, CITE_CONV_HISTORY, CITE_EVENTS, CITE_RETRIEVING],
})
