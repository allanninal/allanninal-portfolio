#!/usr/bin/env python3
"""/stripe/ field notes, batch S — the writing.

Four more webhook-shaped problems, all of them about the gap between what an
endpoint is configured to receive and what the account actually generates. Same
constraint as every other batch: a RESTRICTED, READ-ONLY key finds all of them,
and the repair is printed for a human to run rather than performed here.
"""

CITE_WEBHOOKS = ("Receive Stripe events in your webhook endpoint — Stripe Docs",
                 "https://docs.stripe.com/webhooks")
CITE_WEBHOOK_OBJ = ("The webhook endpoint object — Stripe API reference",
                    "https://docs.stripe.com/api/webhook_endpoints/object")
CITE_WEBHOOK_UPDATE = ("Update a webhook endpoint — Stripe API reference",
                       "https://docs.stripe.com/api/webhook_endpoints/update")
CITE_WEBHOOK_CREATE = ("Create a webhook endpoint — Stripe API reference",
                       "https://docs.stripe.com/api/webhook_endpoints/create")
CITE_EVENTS_LIST = ("List all events — Stripe API reference",
                    "https://docs.stripe.com/api/events/list")
CITE_EVENT_TYPES = ("Types of events — Stripe API reference",
                    "https://docs.stripe.com/api/events/types")
CITE_CLI = ("Stripe CLI — Stripe Docs", "https://docs.stripe.com/stripe-cli")
CITE_PAYMENT_INTENTS = ("The PaymentIntents API — Stripe Docs",
                        "https://docs.stripe.com/payments/payment-intents")
CITE_FULFILL = ("Fulfill orders after a Checkout Session — Stripe Docs",
                "https://docs.stripe.com/checkout/fulfillment")
CITE_BILLING_WEBHOOKS = ("Webhooks for subscriptions — Stripe Docs",
                         "https://docs.stripe.com/billing/subscriptions/webhooks")

GUIDES = [

{
"slug": "non-https-or-tunnel-webhook-url",
"title": "A live webhook endpoint points at a dev tunnel or http",
"description": "It worked for one afternoon. The live endpoint URL is an ngrok hostname that stopped resolving, a localhost, or a plain http:// address.",
"h1": "a live webhook endpoint points at a dev tunnel or http",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe webhook localhost", "stripe webhook ngrok live mode",
             "stripe webhook unable to connect", "stripe webhook https required",
             "stripe webhook url tls"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "It worked for exactly one afternoon. The endpoint was registered during a development session, against a tunnel that happened to be running at the time; the tunnel was closed at the end of the day and the hostname stopped resolving. Every delivery attempt since then has failed before it reached any code you wrote.",
"short_answer": """<p>Read <code>GET /v1/webhook_endpoints</code> and judge the <code>url</code> of every entry with <code>livemode</code> true. Stripe delivers from its own network over HTTPS, so the host has to be a publicly resolvable name with a valid certificate. A tunnel hostname, a <code>localhost</code>, or an RFC1918 address cannot be any of those things.</p>
<p>An <code>http://</code> URL in a live configuration is the same failure written differently: deliveries go over TLS 1.2 or 1.3, and there is nothing at the other end of a plaintext port to negotiate one.</p>""",
"problem": """<p>The distinctive part of this failure is that it produces no partial success. A handler with a bug fulfils some orders and not others; an endpoint pointed at a hostname that does not resolve fulfils none, ever, from the first event onwards. Stripe reports it as a connection error rather than an application error, which means it never appears in your logs, your error tracker, or your uptime monitor &mdash; the request does not reach any of them.</p>
<p>It also has an expiry date. Stripe retries a failing destination for up to three days in live mode and then disables it, so a tunnel URL left in the live configuration turns into a disabled endpoint about seventy-two hours after the last payment that anybody was watching.</p>""",
"why": """<p><strong>A tunnel is the correct tool for local development and a terrible one to leave behind.</strong> <code>ngrok</code>, <code>loca.lt</code>, <code>trycloudflare.com</code> and friends exist precisely so Stripe can reach a laptop, and they work perfectly for that. The hostname is allocated per session on the free tiers, so it is valid for one sitting and dead afterwards. What survives is the endpoint object holding it.</p>
<p><strong>Test-mode and live-mode endpoints are separate objects, and people copy between them.</strong> The URL that is right in test mode is very often the one that gets pasted into the live configuration during a rushed launch, because the two forms look identical and the mode is a toggle somewhere else on the screen.</p>
<p><strong>Nothing validates reachability at registration time.</strong> Creating an endpoint records a string. Stripe does not have to resolve or connect to the host to accept it, so a typo, a staging hostname, or an internal address is stored without complaint and fails silently later, one event at a time.</p>
<p><strong>The host and the handshake fail identically from the outside.</strong> An expired certificate, a self-signed one, or a server that will only speak TLS 1.0 produces the same result as an unresolvable name: nothing arrives. The API tells you about the host-shaped problems, because the URL is a field you can read. The handshake-shaped ones need a TLS test against the host itself.</p>""",
"steps": [
 {"h": "List every endpoint and read url alongside livemode",
  "body": """<p>The mode matters more than usual here. A tunnel hostname on a test-mode endpoint is somebody working, exactly as intended. The same string on a live-mode endpoint is an outage.</p>"""},
 {"h": "Judge the host, not the URL string",
  "body": """<p>Parse out the hostname and decide on that. <code>https://myapp.eu.ngrok.io/stripe/webhook</code> is HTTPS, has a certificate, and looks entirely respectable as a string. It is still a tunnel. The reverse case matters too: a substring match on <code>localhost</code> flags a perfectly good <code>https://localhost-tools.example.com</code>.</p>"""},
 {"h": "Separate cannot resolve from cannot handshake",
  "body": """<p>This is where the read-only check stops. If the host is public and the scheme is right, the remaining failure modes are certificate and protocol ones, and you find those with a TLS server test against the hostname rather than through the Stripe API.</p>"""},
 {"h": "Repoint the endpoint rather than recreating it",
  "body": """<p>Updating the endpoint's <code>url</code> keeps the signing secret, so nothing has to be redeployed. Deleting and recreating gives you a new <code>whsec_</code> and an unplanned config change on the same afternoon you are already fixing an outage. If the endpoint is purely a development leftover, remove it instead of repointing it.</p>"""},
 {"h": "Use the CLI listener for local work, not a registered tunnel",
  "body": """<p><code>stripe listen --forward-to localhost:4242/stripe/webhook</code> creates an ephemeral destination and prints its own signing secret. Nothing persists in the account afterwards, which is the whole point: there is no object left behind to be found in live mode six months later.</p>"""},
],
"verify": """<p>Re-run the script. Every live endpoint should report a public HTTPS host.</p>
<pre><code class="language-bash">python3 stripe_webhook_url_check.py
# ok        https://example.com/stripe/webhook  public https host
# 2 endpoint(s), 0 unreachable</code></pre>""",
"code_intro": "One GET and no writes &mdash; a restricted key with read access to Webhook Endpoints is the whole requirement. The classifier takes the URL and the mode and nothing else, so the interesting rule is visible: the same tunnel hostname is a finding in live mode and ordinary in test mode, and that distinction is the one a grep for <code>ngrok</code> gets wrong.",
"py_file": "stripe_webhook_url_check.py",
"py": '''"""Report Stripe webhook endpoints Stripe cannot reach: tunnels, localhost, http.

Read only. One GET, no writes: give this a RESTRICTED key with read access to
Webhook Endpoints. The repair is printed, never performed, because this script
holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys
from urllib.parse import urlparse

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_webhook_url_check")

API = "https://api.stripe.com/v1"

# Hostname suffixes handed out by development tunnels. Matched as suffixes, not
# substrings: https://localhost-tools.example.com is a real production host.
TUNNELS = (".ngrok.io", ".ngrok-free.app", ".ngrok.app", ".ngrok.dev",
           ".loca.lt", ".trycloudflare.com", ".serveo.net")

LOOPBACK = {"localhost", "127.0.0.1", "0.0.0.0", "::1", "[::1]"}


def split_url(url):
    """(scheme, host) lowercased, or ('', '') when the URL is not usable."""
    try:
        parts = urlparse(url or "")
    except ValueError:
        return ("", "")
    if not parts.scheme or not parts.hostname:
        return ("", "")
    return (parts.scheme.lower(), parts.hostname.lower())


def unroutable_ip(host):
    """True for loopback and RFC1918 literals, which Stripe can never reach."""
    octets = host.split(".")
    if len(octets) != 4 or not all(o.isdigit() for o in octets):
        return False
    a, b = int(octets[0]), int(octets[1])
    return a == 10 or a == 127 or (a == 172 and 16 <= b <= 31) or (a == 192 and b == 168)


def verdict(url, livemode):
    """Classify one endpoint URL. Pure, so the rules can be tested offline.

    Returns (state, detail). The mode is part of the input on purpose: a tunnel
    hostname is how local development works and is only a fault in live mode.
    """
    scheme, host = split_url(url)
    if not host:
        return ("unparseable", "%r is not a URL with a scheme and a host" % (url,))

    if host in LOOPBACK or unroutable_ip(host):
        kind = ("unroutable",
                "%s is not reachable from outside your network, so no event has "
                "ever arrived and none will." % host)
    elif any(host == t.lstrip(".") or host.endswith(t) for t in TUNNELS):
        kind = ("tunnel",
                "%s is a development tunnel host. It resolves only while the "
                "tunnel process is running and the name changes when it restarts."
                % host)
    elif scheme != "https":
        kind = ("plaintext",
                "the scheme is %s. Stripe delivers over HTTPS with TLS 1.2 or "
                "1.3, and there is nothing to negotiate on a plaintext port."
                % scheme)
    else:
        return ("ok", "public https host")

    if not livemode:
        return ("dev",
                "test mode: %s Expected while developing. The risk is this URL "
                "being copied into the live endpoint." % kind[1])
    return kind


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--include-test-mode", action="store_true",
                    help="report test-mode endpoints too, as information")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    endpoints = get(s, "/webhook_endpoints", limit=100).get("data", [])
    if not endpoints:
        log.info("no webhook endpoints configured for this key's mode")
        return 0

    bad = 0
    for ep in endpoints:
        state, detail = verdict(ep.get("url"), bool(ep.get("livemode")))
        line = "%-11s %s  %s" % (state, ep.get("url", "?"), detail)
        if state == "ok":
            log.info(line)
            continue
        if state == "dev":
            if args.include_test_mode:
                log.info(line)
            continue
        bad += 1
        log.warning(line)
        log.warning("  repair: update %s/webhook_endpoints/%s with "
                    "url=https://<your-domain>/stripe/webhook, which keeps the "
                    "signing secret", API, ep["id"])
        log.warning("  or remove the endpoint if it is a development leftover, "
                    "and use: stripe listen --forward-to localhost:4242/webhook")

    log.info("%d endpoint(s), %d unreachable", len(endpoints), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-webhook-url-check.mjs",
"js": '''/**
 * Report Stripe webhook endpoints Stripe cannot reach: tunnels, localhost, http.
 *
 * Read only. One GET, no writes: give this a RESTRICTED key with read access to
 * Webhook Endpoints. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

// Hostname suffixes handed out by development tunnels. Matched as suffixes, not
// substrings: https://localhost-tools.example.com is a real production host.
const TUNNELS = ['.ngrok.io', '.ngrok-free.app', '.ngrok.app', '.ngrok.dev',
  '.loca.lt', '.trycloudflare.com', '.serveo.net'];

const LOOPBACK = new Set(['localhost', '127.0.0.1', '0.0.0.0', '::1', '[::1]']);

export function splitUrl(url) {
  try {
    const parsed = new URL(url ?? '');
    const host = parsed.hostname.toLowerCase().replace(/^\\[|\\]$/g, '');
    if (!host) return ['', ''];
    return [parsed.protocol.replace(':', '').toLowerCase(), host];
  } catch {
    return ['', ''];
  }
}

/** True for loopback and RFC1918 literals, which Stripe can never reach. */
export function unroutableIp(host) {
  const octets = host.split('.');
  if (octets.length !== 4 || !octets.every((o) => /^\\d+$/.test(o))) return false;
  const [a, b] = [Number(octets[0]), Number(octets[1])];
  return a === 10 || a === 127 || (a === 172 && b >= 16 && b <= 31)
    || (a === 192 && b === 168);
}

/**
 * Classify one endpoint URL. Pure, so the rules can be tested offline.
 * The mode is part of the input on purpose: a tunnel hostname is how local
 * development works and is only a fault in live mode.
 */
export function verdict(url, livemode) {
  const [scheme, host] = splitUrl(url);
  if (!host) return ['unparseable', `${JSON.stringify(url)} is not a URL with a scheme and a host`];

  let kind;
  if (LOOPBACK.has(host) || unroutableIp(host)) {
    kind = ['unroutable',
      `${host} is not reachable from outside your network, so no event has ever ` +
      'arrived and none will.'];
  } else if (TUNNELS.some((t) => host === t.slice(1) || host.endsWith(t))) {
    kind = ['tunnel',
      `${host} is a development tunnel host. It resolves only while the tunnel ` +
      'process is running and the name changes when it restarts.'];
  } else if (scheme !== 'https') {
    kind = ['plaintext',
      `the scheme is ${scheme}. Stripe delivers over HTTPS with TLS 1.2 or 1.3, ` +
      'and there is nothing to negotiate on a plaintext port.'];
  } else {
    return ['ok', 'public https host'];
  }

  if (!livemode) {
    return ['dev',
      `test mode: ${kind[1]} Expected while developing. The risk is this URL ` +
      'being copied into the live endpoint.'];
  }
  return kind;
}

async function get(key, path, params = {}) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v);
  const res = await fetch(url, { headers: { Authorization: `Bearer ${key}` } });
  if (res.status === 401) {
    throw new Error('401 from Stripe: the key is wrong, or is for the other mode');
  }
  if (!res.ok) throw new Error(`${res.status} from ${url.pathname}`);
  return res.json();
}

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }

  const { data: endpoints = [] } = await get(key, '/webhook_endpoints', { limit: 100 });
  if (endpoints.length === 0) {
    console.log("no webhook endpoints configured for this key's mode");
    return;
  }

  const includeTest = process.argv.includes('--include-test-mode');
  let bad = 0;
  for (const ep of endpoints) {
    const [state, detail] = verdict(ep.url, Boolean(ep.livemode));
    const line = `${state.padEnd(11)} ${ep.url ?? '?'}  ${detail}`;
    if (state === 'ok') { console.log(line); continue; }
    if (state === 'dev') { if (includeTest) console.log(line); continue; }
    bad += 1;
    console.warn(line);
    console.warn(`  repair: update ${API}/webhook_endpoints/${ep.id} with ` +
                 'url=https://<your-domain>/stripe/webhook, which keeps the signing secret');
    console.warn('  or remove the endpoint if it is a development leftover, and use: ' +
                 'stripe listen --forward-to localhost:4242/webhook');
  }

  console.log(`${endpoints.length} endpoint(s), ${bad} unreachable`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Two cases carry the note. The first is the same tunnel URL in both modes: in test mode it is somebody working, in live mode it is an outage, and a check that cannot tell them apart is either noisy or useless. The second is suffix matching &mdash; <code>localhost-tools.example.com</code> is a production hostname that any substring check flags, and a false positive on a working endpoint is how a check gets ignored.",
"test_py_file": "test_stripe_webhook_url_check.py",
"test_py": '''from stripe_webhook_url_check import verdict


def test_a_public_https_url_is_fine():
    state, _ = verdict("https://example.com/stripe/webhook", True)
    assert state == "ok"


def test_a_tunnel_host_in_live_mode_is_flagged():
    state, detail = verdict("https://a1b2.eu.ngrok.io/stripe/webhook", True)
    assert state == "tunnel"
    assert "ngrok.io" in detail


def test_the_same_tunnel_host_in_test_mode_is_not_a_fault():
    # The whole point of a tunnel is local development. Only live mode matters.
    state, _ = verdict("https://a1b2.eu.ngrok.io/stripe/webhook", False)
    assert state == "dev"


def test_a_private_address_is_unroutable():
    assert verdict("https://10.4.1.9/stripe/webhook", True)[0] == "unroutable"
    assert verdict("http://localhost:4242/webhook", True)[0] == "unroutable"


def test_plain_http_on_a_public_host_is_flagged():
    state, detail = verdict("http://example.com/stripe/webhook", True)
    assert state == "plaintext"
    assert "TLS 1.2" in detail


def test_a_hostname_containing_localhost_is_not_flagged():
    # Suffix matching, not substring: this is a real production host.
    assert verdict("https://localhost-tools.example.com/hook", True)[0] == "ok"


def test_a_missing_url_is_reported_not_passed():
    assert verdict(None, True)[0] == "unparseable"
    assert verdict("example.com/webhook", True)[0] == "unparseable"
''',
"test_js_file": "stripe-webhook-url-check.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict } from './stripe-webhook-url-check.mjs';

test('a public https url is fine', () => {
  assert.equal(verdict('https://example.com/stripe/webhook', true)[0], 'ok');
});

test('a tunnel host in live mode is flagged', () => {
  const [state, detail] = verdict('https://a1b2.eu.ngrok.io/stripe/webhook', true);
  assert.equal(state, 'tunnel');
  assert.match(detail, /ngrok\\.io/);
});

test('the same tunnel host in test mode is not a fault', () => {
  assert.equal(verdict('https://a1b2.eu.ngrok.io/stripe/webhook', false)[0], 'dev');
});

test('a private address is unroutable', () => {
  assert.equal(verdict('https://10.4.1.9/stripe/webhook', true)[0], 'unroutable');
  assert.equal(verdict('http://localhost:4242/webhook', true)[0], 'unroutable');
});

test('plain http on a public host is flagged', () => {
  const [state, detail] = verdict('http://example.com/stripe/webhook', true);
  assert.equal(state, 'plaintext');
  assert.match(detail, /TLS 1\\.2/);
});

test('a hostname containing localhost is not flagged', () => {
  assert.equal(verdict('https://localhost-tools.example.com/hook', true)[0], 'ok');
});

test('a missing url is reported, not passed', () => {
  assert.equal(verdict(null, true)[0], 'unparseable');
  assert.equal(verdict('example.com/webhook', true)[0], 'unparseable');
});
''',
"faq": [
 ("Can a Stripe webhook endpoint use http instead of https?",
  "Not usefully in live mode. Stripe delivers over HTTPS and supports TLS 1.2 and 1.3, so a plaintext URL has nothing to negotiate with. An http:// URL sitting in a live configuration is almost always a test-mode value that was copied across."),
 ("Why did my ngrok endpoint work once and then never again?",
  "Because the hostname was allocated for that tunnel session. On the free tiers a new hostname is issued each time the tunnel starts, so the URL stored on the endpoint object stops resolving the moment you close the terminal. The endpoint keeps trying to reach a name that no longer exists."),
 ("Can Stripe deliver to localhost or a private IP if I open a firewall port?",
  "No. Stripe delivers from its own network, so the host has to resolve publicly. 127.0.0.1 and RFC1918 addresses mean something different on every network, including Stripe's. For local work use stripe listen, which forwards from the CLI process rather than registering an endpoint."),
 ("If I fix the URL, do the missed events get delivered?",
  "No. Fixing the URL only affects future deliveries. Events are retained for 30 days and can be fetched with GET /v1/events?delivery_success=false and replayed through your own handler, but nothing is resent automatically."),
 ("Does changing the url change the signing secret?",
  "No, as long as you update the existing endpoint. The secret belongs to the endpoint object, so a URL change keeps it and needs no redeploy. Deleting and recreating issues a new whsec_ that every environment then has to be given."),
],
"related": [
 ("/stripe/webhook-endpoint-disabled/", "A webhook endpoint sits disabled after days of retries"),
 ("/stripe/no-live-webhook-endpoints/", "Live mode has no webhook endpoints at all"),
 ("/stripe/duplicate-endpoints-same-url/", "Two endpoints share one URL, so every event runs twice"),
],
"citations": [CITE_WEBHOOKS, CITE_WEBHOOK_OBJ, CITE_WEBHOOK_UPDATE, CITE_CLI],
},

{
"slug": "unsubscribed-event-types-firing",
"title": "Event types are firing that no endpoint subscribes to",
"description": "enabled_events is an allowlist and it drifts. Types generated by products you enabled later are visible in the API and delivered to nobody.",
"h1": "event types are firing that no endpoint subscribes to",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe event not received", "stripe webhook missing event type",
             "enabled_events allowlist", "stripe events list by type",
             "stripe webhook not firing for event"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "A whole class of business event is invisible to the application, and there is no error anywhere to explain it. The events exist. They are in <code>GET /v1/events</code> with the right data on them. They were never delivered, because no endpoint asked for them, and an event nobody asked for is not a failure &mdash; it is a non-event.",
"short_answer": """<p>Union the <code>enabled_events</code> arrays across every endpoint from <code>GET /v1/webhook_endpoints</code>, treating a literal <code>"*"</code> as everything. Then paginate <code>GET /v1/events</code> across the retained window and collect the distinct <code>type</code> values that actually fired.</p>
<p>Subtract the first from the second and rank what is left by occurrence count. That list is what your account generates and your application has never seen.</p>""",
"problem": """<p>Every other webhook check reports healthy while this is happening, and they are all correct. The endpoint is enabled. <code>pending_webhooks</code> is zero. <code>delivery_success=false</code> returns nothing. There is no failed delivery because there was no delivery: Stripe consulted the allowlist, found the type absent, and moved on.</p>
<p>What it feels like from the inside is a missing feature rather than a bug. Disputes are noticed when the balance moves. Renewal failures are noticed when a customer writes in. Nobody looks for a webhook problem, because the webhooks that exist are working fine.</p>""",
"why": """<p><strong>The allowlist is written once, when the account did less.</strong> <code>enabled_events</code> is set the day the endpoint is created, against whatever the integration handled that week. Every product enabled afterwards &mdash; Billing, Radar, Tax, Connect, Issuing &mdash; starts generating types that nobody went back to add, and there is no prompt anywhere that suggests they should.</p>
<p><strong>Matching is exact, and only one string is a wildcard.</strong> <code>enabled_events</code> holds literal type names plus the single special value <code>"*"</code>. A namespace-looking entry such as <code>payment_intent.*</code> is not a subscription to that namespace; it is a string that will never equal a real event type. Subscribing to <code>payment_intent.succeeded</code> gets you exactly that one type and nothing adjacent to it.</p>
<p><strong>Coverage is a property of the account, not of an endpoint.</strong> Splitting types across several endpoints is normal and fine. It also means no single endpoint's configuration answers the question, and reading one of them in the Dashboard is how people conclude they are covered when they are not.</p>
<p><strong>The inverse problem is a different note.</strong> Types that are subscribed and never fire are dead branches and rejected subscriptions; the gap here runs the other way, and a check for one will not find the other. Both are worth running, and the traffic tally you build here is the input to both.</p>""",
"steps": [
 {"h": "Union enabled_events across every endpoint, in both modes",
  "body": """<p>Merge the arrays rather than reading them one at a time. If any endpoint holds <code>"*"</code> the union is everything, and the finding for that account is the wildcard rather than the gap.</p>"""},
 {"h": "Tally what actually fires over the full retained window",
  "body": """<p>Paginate <code>GET /v1/events</code> and count distinct <code>type</code> values. Use the whole 30 days: a monthly cadence means a renewal failure or a payout event can be entirely absent from a seven-day sample and perfectly regular over a month.</p>"""},
 {"h": "Subtract, then rank by count",
  "body": """<p>The ranking is the triage. A type that fired 400 times and reached nothing is a system nobody built; a type that fired once is usually a product you turned on and are not using yet.</p>"""},
 {"h": "Subscribe to what you have a branch for, and nothing else",
  "body": """<p>The output is a list of candidates, not a list of instructions. Each type earns a subscription by having a handler branch that does something with it. Switching to <code>"*"</code> to close the gap in one move trades this problem for a flooded handler.</p>"""},
 {"h": "Add the types to an existing endpoint and re-run",
  "body": """<p>Updating <code>enabled_events</code> on the endpoint you already have preserves the signing secret. Re-running the check afterwards is the only confirmation that matters: the subtraction should now come back empty for everything your handler branches on.</p>"""},
],
"verify": """<p>Re-run the script. The types you decided to handle should no longer appear in the unsubscribed list.</p>
<pre><code class="language-bash">python3 stripe_unsubscribed_events.py
# 38 type(s) fired, 0 unsubscribed in the retained window</code></pre>""",
"code_intro": "Two GETs and no writes &mdash; a restricted key with read access to Webhook Endpoints and Events. The classifier decides one type at a time against the subscription union, which is what makes the near-miss case visible: a type whose siblings are subscribed is a different kind of finding from one whose whole namespace is unhandled, and the ranking by count is what turns the list into a plan.",
"py_file": "stripe_unsubscribed_events.py",
"py": '''"""Report Stripe event types that fire but reach no webhook endpoint.

Read only. Two GETs, no writes: give this a RESTRICTED key with read access to
Webhook Endpoints and Events. The repair is printed, never performed, because
this script holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_unsubscribed_events")

API = "https://api.stripe.com/v1"


def classify(event_type, count, subscribed):
    """Classify one fired event type against the subscription union.

    Pure, so the rules can be tested without a network. `subscribed` is the union
    of enabled_events across every endpoint. Returns (state, detail).
    """
    events = set(subscribed or [])
    if count <= 0:
        return ("unseen", "%s did not fire in the retained window" % event_type)
    if "*" in events:
        return ("wildcard",
                "%s is delivered by a wildcard subscription, along with every "
                "other type the account generates." % event_type)
    if event_type in events:
        return ("covered", "%s is subscribed on at least one endpoint" % event_type)

    namespace = event_type.split(".")[0]
    siblings = sorted(e for e in events if e.split(".")[0] == namespace)
    if siblings:
        return ("near-miss",
                "%s fired %d time(s) and is not subscribed, though %s is. "
                "enabled_events matches type names exactly: only the literal * "
                "is a wildcard, so a namespace is never covered by a sibling."
                % (event_type, count, siblings[0]))
    return ("missed",
            "%s fired %d time(s) and reached no endpoint. Nothing in the %s "
            "namespace is subscribed anywhere on this account."
            % (event_type, count, namespace))


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def subscribed_union(session):
    """Every event type any endpoint on this account asks for."""
    union = set()
    for ep in get(session, "/webhook_endpoints", limit=100).get("data", []):
        union.update(ep.get("enabled_events") or [])
    return union


def fired_counts(session, limit):
    """Distinct event types seen in the retained window, with counts."""
    counts = {}
    total = 0
    params = {"limit": 100}
    while True:
        page = get(session, "/events", **params)
        data = page.get("data", [])
        for ev in data:
            total += 1
            counts[ev.get("type")] = counts.get(ev.get("type"), 0) + 1
        if not data or not page.get("has_more") or total >= limit:
            break
        params["starting_after"] = data[-1]["id"]
    return counts


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-events", type=int, default=2000,
                    help="stop sampling after this many events")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    union = subscribed_union(s)
    if not union:
        log.warning("no endpoint subscribes to anything in this mode: "
                    "every event below is undelivered")

    counts = fired_counts(s, args.max_events)
    log.info("sampled %d event(s) across %d distinct type(s), %d subscribed type(s)",
             sum(counts.values()), len(counts), len(union))

    gaps = 0
    for event_type, count in sorted(counts.items(), key=lambda kv: -kv[1]):
        state, detail = classify(event_type, count, union)
        if state in ("covered", "wildcard", "unseen"):
            continue
        gaps += 1
        log.warning("%-9s %s", state, detail)

    if gaps:
        log.warning("repair: add the types your handler branches on to an existing "
                    "endpoint's enabled_events[] at %s/webhook_endpoints/{id}. "
                    "Adding * instead trades this for a flooded handler", API)
    log.info("%d type(s) fired, %d unsubscribed", len(counts), gaps)
    return 1 if gaps else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-unsubscribed-events.mjs",
"js": '''/**
 * Report Stripe event types that fire but reach no webhook endpoint.
 *
 * Read only. Two GETs, no writes: give this a RESTRICTED key with read access to
 * Webhook Endpoints and Events. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

/**
 * Classify one fired event type against the subscription union. Pure, so the
 * rules can be tested without a network.
 */
export function classify(eventType, count, subscribed) {
  const events = new Set(subscribed ?? []);
  if (count <= 0) return ['unseen', `${eventType} did not fire in the retained window`];
  if (events.has('*')) {
    return ['wildcard',
      `${eventType} is delivered by a wildcard subscription, along with every ` +
      'other type the account generates.'];
  }
  if (events.has(eventType)) {
    return ['covered', `${eventType} is subscribed on at least one endpoint`];
  }

  const namespace = eventType.split('.')[0];
  const siblings = [...events].filter((e) => e.split('.')[0] === namespace).sort();
  if (siblings.length > 0) {
    return ['near-miss',
      `${eventType} fired ${count} time(s) and is not subscribed, though ` +
      `${siblings[0]} is. enabled_events matches type names exactly: only the ` +
      'literal * is a wildcard, so a namespace is never covered by a sibling.'];
  }
  return ['missed',
    `${eventType} fired ${count} time(s) and reached no endpoint. Nothing in ` +
    `the ${namespace} namespace is subscribed anywhere on this account.`];
}

async function get(key, path, params = {}) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v);
  const res = await fetch(url, { headers: { Authorization: `Bearer ${key}` } });
  if (res.status === 401) {
    throw new Error('401 from Stripe: the key is wrong, or is for the other mode');
  }
  if (!res.ok) throw new Error(`${res.status} from ${url.pathname}`);
  return res.json();
}

export async function subscribedUnion(key) {
  const union = new Set();
  const { data = [] } = await get(key, '/webhook_endpoints', { limit: 100 });
  for (const ep of data) for (const t of ep.enabled_events ?? []) union.add(t);
  return union;
}

export async function firedCounts(key, limit = 2000) {
  const counts = new Map();
  let total = 0;
  const params = { limit: 100 };
  for (;;) {
    const page = await get(key, '/events', params);
    const data = page.data ?? [];
    for (const ev of data) {
      total += 1;
      counts.set(ev.type, (counts.get(ev.type) ?? 0) + 1);
    }
    if (data.length === 0 || !page.has_more || total >= limit) break;
    params.starting_after = data[data.length - 1].id;
  }
  return counts;
}

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }

  const union = await subscribedUnion(key);
  if (union.size === 0) {
    console.warn('no endpoint subscribes to anything in this mode: ' +
                 'every event below is undelivered');
  }

  const counts = await firedCounts(key);
  const sampled = [...counts.values()].reduce((a, b) => a + b, 0);
  console.log(`sampled ${sampled} event(s) across ${counts.size} distinct type(s), ` +
              `${union.size} subscribed type(s)`);

  let gaps = 0;
  for (const [eventType, count] of [...counts.entries()].sort((a, b) => b[1] - a[1])) {
    const [state, detail] = classify(eventType, count, union);
    if (state === 'covered' || state === 'wildcard' || state === 'unseen') continue;
    gaps += 1;
    console.warn(`${state.padEnd(9)} ${detail}`);
  }

  if (gaps > 0) {
    console.warn('repair: add the types your handler branches on to an existing ' +
                 `endpoint's enabled_events[] at ${API}/webhook_endpoints/{id}. ` +
                 'Adding * instead trades this for a flooded handler');
  }
  console.log(`${counts.size} type(s) fired, ${gaps} unsubscribed`);
  process.exitCode = gaps ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The case that has to hold is the namespace one. People write <code>payment_intent.*</code> into <code>enabled_events</code> and believe they are covered, and they subscribe to <code>payment_intent.succeeded</code> and believe the failure is implied. Neither is true, and both produce a subscription list that reads as complete. The tests pin the distinction between a sibling being subscribed and the type itself being subscribed.",
"test_py_file": "test_stripe_unsubscribed_events.py",
"test_py": '''from stripe_unsubscribed_events import classify

SUBSCRIBED = ["payment_intent.succeeded", "invoice.paid"]


def test_a_subscribed_type_is_covered():
    state, _ = classify("invoice.paid", 12, SUBSCRIBED)
    assert state == "covered"


def test_a_type_with_no_sibling_subscribed_is_missed():
    state, detail = classify("charge.dispute.created", 7, SUBSCRIBED)
    assert state == "missed"
    assert "7 time(s)" in detail
    assert "charge" in detail


def test_a_sibling_subscription_does_not_cover_the_type():
    # payment_intent.succeeded is subscribed; the failure is not implied by it.
    state, detail = classify("payment_intent.payment_failed", 31, SUBSCRIBED)
    assert state == "near-miss"
    assert "payment_intent.succeeded" in detail


def test_a_namespace_pattern_is_not_a_subscription():
    # Only the literal * is a wildcard. "payment_intent.*" matches nothing.
    state, _ = classify("payment_intent.succeeded", 5, ["payment_intent.*"])
    assert state != "covered"
    assert state == "near-miss"


def test_a_wildcard_covers_everything():
    state, _ = classify("radar.early_fraud_warning.created", 2, ["*"])
    assert state == "wildcard"


def test_a_type_that_never_fired_is_not_a_gap():
    state, _ = classify("invoice.paid", 0, [])
    assert state == "unseen"
''',
"test_js_file": "stripe-unsubscribed-events.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { classify } from './stripe-unsubscribed-events.mjs';

const SUBSCRIBED = ['payment_intent.succeeded', 'invoice.paid'];

test('a subscribed type is covered', () => {
  assert.equal(classify('invoice.paid', 12, SUBSCRIBED)[0], 'covered');
});

test('a type with no sibling subscribed is missed', () => {
  const [state, detail] = classify('charge.dispute.created', 7, SUBSCRIBED);
  assert.equal(state, 'missed');
  assert.match(detail, /7 time\\(s\\)/);
});

test('a sibling subscription does not cover the type', () => {
  const [state, detail] = classify('payment_intent.payment_failed', 31, SUBSCRIBED);
  assert.equal(state, 'near-miss');
  assert.match(detail, /payment_intent\\.succeeded/);
});

test('a namespace pattern is not a subscription', () => {
  const [state] = classify('payment_intent.succeeded', 5, ['payment_intent.*']);
  assert.notEqual(state, 'covered');
  assert.equal(state, 'near-miss');
});

test('a wildcard covers everything', () => {
  assert.equal(classify('radar.early_fraud_warning.created', 2, ['*'])[0], 'wildcard');
});

test('a type that never fired is not a gap', () => {
  assert.equal(classify('invoice.paid', 0, [])[0], 'unseen');
});
''',
"faq": [
 ("Why don't unsubscribed events show up as failed deliveries?",
  "Because no delivery was attempted. enabled_events is an allowlist consulted before Stripe queues anything, so an unsubscribed type never becomes a delivery, never increments pending_webhooks, and never appears under delivery_success=false. Every failure metric stays clean."),
 ("Can I subscribe to a whole namespace, like charge.* ?",
  "No. enabled_events matches type names exactly, and the only wildcard is the single literal \"*\". A value like charge.* is stored as a string that never equals a real type, which is worse than the gap it was meant to close because it looks like coverage."),
 ("Should I just set enabled_events to \"*\" and be done?",
  "It closes this gap and opens another: every type the account generates gets delivered, verified and parsed before your handler decides it has no branch for it. Stripe recommends against it for that reason. Subscribe to what you handle and re-run this check when you enable a new product."),
 ("Does this cover connected accounts on a Connect platform?",
  "Not by itself. GET /v1/events returns the events of the account the key belongs to, and connected-account events are delivered to a Connect-scoped destination. Run the check per connected account with the Stripe-Account header to see their traffic."),
 ("How far back does the comparison look?",
  "30 days, which is the event retention window. Anything with a monthly rhythm, such as a renewal failure or a payout, can be entirely absent from a shorter sample, so run the tally across the full window before concluding that a type never fires."),
],
"related": [
 ("/stripe/dead-or-rejected-enabled-events/", "enabled_events lists types that are dead or rejected"),
 ("/stripe/wildcard-enabled-events/", "An endpoint subscribes to every event and floods the handler"),
 ("/stripe/missing-subscription-deleted/", "customer.subscription.deleted is missing, so access never ends"),
],
"citations": [CITE_EVENTS_LIST, CITE_EVENT_TYPES, CITE_WEBHOOK_UPDATE, CITE_WEBHOOKS],
},

{
"slug": "charge-events-but-paymentintent-integration",
"title": "The endpoint listens for charge.succeeded, not payment_intent",
"description": "Fulfilment runs on a Charge with empty metadata and no customer, so nothing maps back to a cart. The subscription is one integration era behind.",
"h1": "the endpoint listens for charge.succeeded, not payment_intent",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["charge.succeeded vs payment_intent.succeeded",
             "stripe webhook metadata empty", "stripe fulfil order webhook",
             "checkout.session.completed not received",
             "stripe legacy charge webhook"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "This does not present as a webhook problem, because the webhook arrives. It presents as a data problem: the object in the payload has empty <code>metadata</code>, no <code>customer</code>, and nothing that maps the payment back to a cart or a user. The metadata is on the PaymentIntent. The endpoint is subscribed to the Charge.",
"short_answer": """<p>Read <code>enabled_events</code> from <code>GET /v1/webhook_endpoints</code>. If it contains <code>charge.succeeded</code> and contains neither <code>payment_intent.succeeded</code> nor <code>checkout.session.completed</code>, the subscription predates the integration.</p>
<p>Confirm which era you are actually in with <code>GET /v1/events?types[]=payment_intent.succeeded&amp;types[]=checkout.session.completed</code>. A non-empty result means the code moved to PaymentIntents or Checkout and the endpoint configuration never followed.</p>""",
"problem": """<p>The handler runs, returns 200, and the endpoint stays enabled forever, so every health check you have says this integration is fine. What arrives is a Charge: it has an amount, a status and a payment method, and it does not have the <code>metadata</code> you attached when you created the PaymentIntent or the <code>client_reference_id</code> you set on the Checkout Session. Those live on the object you did not subscribe to.</p>
<p>The workaround people reach for makes it worse. The Charge has a <code>payment_intent</code> id, so the handler grows an extra fetch to go and get the missing fields, and now fulfilment depends on a second API call inside a webhook that Stripe is timing. It works until the day it does not.</p>""",
"why": """<p><strong>The subscription is not in the repository.</strong> Migrating from Charges to PaymentIntents is a code change, and code changes get reviewed. <code>enabled_events</code> lives in the Stripe account, set through the Dashboard or a one-off script, so it never appears in the diff, never appears in the deploy, and nobody is reminded that it exists.</p>
<p><strong>Charge and PaymentIntent are different objects with different fields.</strong> Metadata set on an intent is not copied down to the charge it creates, and <code>client_reference_id</code> exists only on the Checkout Session. Keying fulfilment on the Charge means keying it on the attempt rather than on the payment: an intent can go through several charge attempts, and the identifier your order table is holding is not any of them.</p>
<p><strong>No <code>charge.*</code> subscription implies a Checkout event.</strong> Checkout completion arrives as <code>checkout.session.completed</code>, and for delayed-notification payment methods the money confirmation arrives later still as <code>checkout.session.async_payment_succeeded</code>. An endpoint subscribed only to charge events sees neither, so a Checkout integration built that way fulfils on a signal that does not carry the session.</p>
<p><strong>Subscribing to both is not the safe middle ground.</strong> One payment then arrives twice in two shapes, and unless the handler keys its side effects on a payment identifier rather than an event, it runs fulfilment twice. The safe order is to add the new type, ship the branch, verify it, and only then remove the old one.</p>""",
"steps": [
 {"h": "Read enabled_events and look for charge.succeeded",
  "body": """<p>Do it per endpoint rather than on the union: the finding is that one endpoint is configured for the wrong era, and a second, newer endpoint elsewhere does not undo that.</p>"""},
 {"h": "Establish which era the account is actually in",
  "body": """<p><code>GET /v1/events?types[]=payment_intent.succeeded&amp;types[]=checkout.session.completed</code>. If those types are firing, the integration is modern and the subscription is stale. If nothing comes back, you may genuinely still be creating Charges directly, which is a different problem with a different fix.</p>"""},
 {"h": "Decide where fulfilment belongs",
  "body": """<p>Checkout and Payment Links fulfil on <code>checkout.session.completed</code>, with <code>async_payment_succeeded</code> and <code>async_payment_failed</code> for delayed-notification methods. A direct Elements integration fulfils on <code>payment_intent.succeeded</code>. Pick the one that carries the identifier your order table already stores.</p>"""},
 {"h": "Add the new type before removing the old one",
  "body": """<p>Add the PaymentIntent or Checkout type, deploy the handler branch, and watch both fire for a day. Removing <code>charge.succeeded</code> first leaves a window with no fulfilment path at all; adding both permanently leaves you fulfilling twice.</p>"""},
 {"h": "Then drop charge.succeeded and re-run",
  "body": """<p>Keep it only if you need charge-level data such as the balance transaction or the dispute linkage, and if you do, make it explicit that it is supplementary rather than a second fulfilment trigger.</p>"""},
],
"verify": """<p>Re-run the script. The endpoint should report an aligned subscription for the era the account is in.</p>
<pre><code class="language-bash">python3 stripe_charge_event_drift.py
# aligned   https://example.com/stripe/webhook  fulfilment events match the integration</code></pre>""",
"code_intro": "Two GETs and no writes &mdash; the endpoints, and a type-filtered read of the events to establish which era the account is really in. The classifier takes both, because <code>charge.succeeded</code> on its own is not a fault: on an account that genuinely still creates Charges it is correct, and the same configuration on an account where PaymentIntents are firing is the bug.",
"py_file": "stripe_charge_event_drift.py",
"py": '''"""Report webhook endpoints subscribed to charge events on a PaymentIntent integration.

Read only. Two GETs, no writes: give this a RESTRICTED key with read access to
Webhook Endpoints and Events. The repair is printed, never performed, because
this script holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_charge_event_drift")

API = "https://api.stripe.com/v1"

CHARGE = "charge.succeeded"
INTENT = "payment_intent.succeeded"
SESSION = "checkout.session.completed"


def verdict(enabled_events, fired_types):
    """Classify one endpoint's fulfilment subscription. Pure and testable.

    `fired_types` is the set of modern success types actually seen in the
    retained window. Checked in order of how much fulfilment they cost you:
    a missing path first, then a duplicated one. Returns (state, detail).
    """
    events = set(enabled_events or [])
    fired = set(fired_types or [])
    modern = INTENT in events or SESSION in events

    if "*" in events:
        return ("wildcard",
                "a wildcard delivers both shapes of the same payment. Fulfilment "
                "has to pick one and ignore the other, explicitly.")

    if CHARGE in events and not modern:
        if fired & {INTENT, SESSION}:
            return ("stale",
                    "%s is the only success subscription, but %s fired in the "
                    "retained window. The Charge carries neither the intent "
                    "metadata nor client_reference_id."
                    % (CHARGE, ", ".join(sorted(fired & {INTENT, SESSION}))))
        return ("legacy",
                "%s only, and no PaymentIntent or Checkout events fired. This "
                "looks like a genuine Charges API integration rather than a "
                "stale subscription." % CHARGE)

    if SESSION in fired and SESSION not in events:
        return ("checkout-gap",
                "Checkout Sessions are completing and %s is not subscribed. No "
                "charge or payment_intent subscription implies it." % SESSION)

    if CHARGE in events and modern:
        return ("overlapping",
                "%s and the fulfilment event are both subscribed, so one payment "
                "arrives twice in two shapes. Fulfil on one and drop the other."
                % CHARGE)

    return ("aligned", "fulfilment events match the integration")


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def modern_types_seen(session):
    """Which of the modern success types have fired in the retained window."""
    page = get(session, "/events", limit=100, **{"types[]": [INTENT, SESSION]})
    return {ev.get("type") for ev in page.get("data", [])}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--quiet-aligned", action="store_true",
                    help="print only the endpoints that need attention")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    endpoints = get(s, "/webhook_endpoints", limit=100).get("data", [])
    if not endpoints:
        log.info("no webhook endpoints configured for this key's mode")
        return 0

    fired = modern_types_seen(s)
    log.info("modern success types seen: %s", ", ".join(sorted(fired)) or "none")

    bad = 0
    for ep in endpoints:
        state, detail = verdict(ep.get("enabled_events"), fired)
        line = "%-12s %s  %s" % (state, ep.get("url", "?"), detail)
        if state in ("aligned", "legacy"):
            if not args.quiet_aligned:
                log.info(line)
            continue
        bad += 1
        log.warning(line)
        want = SESSION if SESSION in fired else INTENT
        log.warning("  repair: add enabled_events[]=%s to %s/webhook_endpoints/%s, "
                    "ship the handler branch, then remove %s",
                    want, API, ep["id"], CHARGE)

    log.info("%d endpoint(s), %d needing attention", len(endpoints), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-charge-event-drift.mjs",
"js": '''/**
 * Report webhook endpoints subscribed to charge events on a PaymentIntent integration.
 *
 * Read only. Two GETs, no writes: give this a RESTRICTED key with read access to
 * Webhook Endpoints and Events. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

const CHARGE = 'charge.succeeded';
const INTENT = 'payment_intent.succeeded';
const SESSION = 'checkout.session.completed';

/**
 * Classify one endpoint's fulfilment subscription. Pure and testable.
 * Checked in order of how much fulfilment they cost you: a missing path first,
 * then a duplicated one.
 */
export function verdict(enabledEvents, firedTypes) {
  const events = new Set(enabledEvents ?? []);
  const fired = new Set(firedTypes ?? []);
  const modern = events.has(INTENT) || events.has(SESSION);

  if (events.has('*')) {
    return ['wildcard',
      'a wildcard delivers both shapes of the same payment. Fulfilment has to ' +
      'pick one and ignore the other, explicitly.'];
  }

  if (events.has(CHARGE) && !modern) {
    const seen = [INTENT, SESSION].filter((t) => fired.has(t));
    if (seen.length > 0) {
      return ['stale',
        `${CHARGE} is the only success subscription, but ${seen.join(', ')} ` +
        'fired in the retained window. The Charge carries neither the intent ' +
        'metadata nor client_reference_id.'];
    }
    return ['legacy',
      `${CHARGE} only, and no PaymentIntent or Checkout events fired. This ` +
      'looks like a genuine Charges API integration rather than a stale subscription.'];
  }

  if (fired.has(SESSION) && !events.has(SESSION)) {
    return ['checkout-gap',
      `Checkout Sessions are completing and ${SESSION} is not subscribed. No ` +
      'charge or payment_intent subscription implies it.'];
  }

  if (events.has(CHARGE) && modern) {
    return ['overlapping',
      `${CHARGE} and the fulfilment event are both subscribed, so one payment ` +
      'arrives twice in two shapes. Fulfil on one and drop the other.'];
  }

  return ['aligned', 'fulfilment events match the integration'];
}

async function get(key, path, params = {}) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) {
    if (Array.isArray(v)) for (const item of v) url.searchParams.append(k, item);
    else url.searchParams.set(k, v);
  }
  const res = await fetch(url, { headers: { Authorization: `Bearer ${key}` } });
  if (res.status === 401) {
    throw new Error('401 from Stripe: the key is wrong, or is for the other mode');
  }
  if (!res.ok) throw new Error(`${res.status} from ${url.pathname}`);
  return res.json();
}

export async function modernTypesSeen(key) {
  const page = await get(key, '/events', { limit: 100, 'types[]': [INTENT, SESSION] });
  return new Set((page.data ?? []).map((ev) => ev.type));
}

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }

  const { data: endpoints = [] } = await get(key, '/webhook_endpoints', { limit: 100 });
  if (endpoints.length === 0) {
    console.log("no webhook endpoints configured for this key's mode");
    return;
  }

  const fired = await modernTypesSeen(key);
  console.log(`modern success types seen: ${[...fired].sort().join(', ') || 'none'}`);

  let bad = 0;
  for (const ep of endpoints) {
    const [state, detail] = verdict(ep.enabled_events, fired);
    const line = `${state.padEnd(12)} ${ep.url ?? '?'}  ${detail}`;
    if (state === 'aligned' || state === 'legacy') { console.log(line); continue; }
    bad += 1;
    console.warn(line);
    const want = fired.has(SESSION) ? SESSION : INTENT;
    console.warn(`  repair: add enabled_events[]=${want} to ` +
                 `${API}/webhook_endpoints/${ep.id}, ship the handler branch, ` +
                 `then remove ${CHARGE}`);
  }

  console.log(`${endpoints.length} endpoint(s), ${bad} needing attention`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The pair worth pinning is <code>stale</code> against <code>legacy</code>. The endpoint configuration is byte-for-byte identical in both; the only thing that separates a broken integration from a correct one is whether PaymentIntent or Checkout events are firing on the account. A classifier that looks at <code>enabled_events</code> alone reports the same verdict for both, and one of those verdicts is wrong.",
"test_py_file": "test_stripe_charge_event_drift.py",
"test_py": '''from stripe_charge_event_drift import verdict


def test_charge_only_while_intents_fire_is_stale():
    state, detail = verdict(["charge.succeeded"], ["payment_intent.succeeded"])
    assert state == "stale"
    assert "client_reference_id" in detail


def test_the_same_config_with_no_modern_traffic_is_a_real_charges_integration():
    # Identical enabled_events. Only the account's traffic tells them apart.
    state, _ = verdict(["charge.succeeded"], [])
    assert state == "legacy"


def test_subscribing_to_both_is_double_fulfilment():
    state, detail = verdict(["charge.succeeded", "payment_intent.succeeded"],
                            ["payment_intent.succeeded"])
    assert state == "overlapping"
    assert "twice" in detail


def test_checkout_sessions_firing_with_no_session_subscription():
    state, _ = verdict(["payment_intent.succeeded"],
                       ["payment_intent.succeeded", "checkout.session.completed"])
    assert state == "checkout-gap"


def test_a_matching_subscription_is_aligned():
    state, _ = verdict(["payment_intent.succeeded", "checkout.session.completed"],
                       ["payment_intent.succeeded", "checkout.session.completed"])
    assert state == "aligned"


def test_a_wildcard_is_called_out_rather_than_passed():
    state, _ = verdict(["*"], ["payment_intent.succeeded"])
    assert state == "wildcard"
''',
"test_js_file": "stripe-charge-event-drift.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict } from './stripe-charge-event-drift.mjs';

test('charge only while intents fire is stale', () => {
  const [state, detail] = verdict(['charge.succeeded'], ['payment_intent.succeeded']);
  assert.equal(state, 'stale');
  assert.match(detail, /client_reference_id/);
});

test('the same config with no modern traffic is a real charges integration', () => {
  assert.equal(verdict(['charge.succeeded'], [])[0], 'legacy');
});

test('subscribing to both is double fulfilment', () => {
  const [state, detail] = verdict(
    ['charge.succeeded', 'payment_intent.succeeded'], ['payment_intent.succeeded']);
  assert.equal(state, 'overlapping');
  assert.match(detail, /twice/);
});

test('checkout sessions firing with no session subscription', () => {
  const [state] = verdict(['payment_intent.succeeded'],
    ['payment_intent.succeeded', 'checkout.session.completed']);
  assert.equal(state, 'checkout-gap');
});

test('a matching subscription is aligned', () => {
  const [state] = verdict(['payment_intent.succeeded', 'checkout.session.completed'],
    ['payment_intent.succeeded', 'checkout.session.completed']);
  assert.equal(state, 'aligned');
});

test('a wildcard is called out rather than passed', () => {
  assert.equal(verdict(['*'], ['payment_intent.succeeded'])[0], 'wildcard');
});
''',
"faq": [
 ("What is the practical difference between charge.succeeded and payment_intent.succeeded?",
  "The object in the payload. charge.succeeded carries a Charge, which is one attempt at a payment; payment_intent.succeeded carries the PaymentIntent, which is the payment. Metadata you set on the intent is not copied onto the charge, so a handler reading charge.metadata finds an empty object and cannot map the payment to anything."),
 ("Why is my Charge metadata empty when I definitely set metadata?",
  "Because you set it on the PaymentIntent or the Checkout Session. Those are separate objects with separate metadata bags. The Charge does carry a payment_intent id, so the data is reachable with another API call, but that turns fulfilment into a second request inside a timed webhook."),
 ("Should I subscribe to both charge.succeeded and payment_intent.succeeded?",
  "Only during the migration, and only if your handler is idempotent on a payment identifier rather than an event id. Left permanently, one payment arrives twice in two shapes and any side effect that is not deduplicated runs twice."),
 ("Which event should a Checkout integration fulfil on?",
  "checkout.session.completed, which carries the session with client_reference_id and the line items. For delayed-notification payment methods the money is not confirmed at that point, and the follow-up arrives as checkout.session.async_payment_succeeded or async_payment_failed."),
 ("Is charge.succeeded ever the right subscription?",
  "Yes, if you actually create Charges directly, or if you need charge-level detail such as the balance transaction or the linkage a dispute will later reference. Treat it as supplementary in that case, and make sure only one subscription triggers fulfilment."),
],
"related": [
 ("/stripe/legacy-charges-api-no-payment-intent/", "Charges with a null payment_intent: a legacy integration"),
 ("/stripe/checkout-sessions-unreconcilable/", "Checkout Sessions that cannot be reconciled to an order"),
 ("/stripe/wildcard-enabled-events/", "An endpoint subscribes to every event and floods the handler"),
],
"citations": [CITE_WEBHOOK_CREATE, CITE_EVENT_TYPES, CITE_PAYMENT_INTENTS, CITE_FULFILL],
},

{
"slug": "missing-payment-failure-events",
"title": "No endpoint subscribes to any payment failure event",
"description": "The success path is wired perfectly and failures are a black hole: carts stay in processing, dunning runs unseen, delinquent subscribers keep access.",
"h1": "no endpoint subscribes to any payment failure event",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["payment_intent.payment_failed not received",
             "invoice.payment_failed webhook", "stripe failed payment notification",
             "stripe dunning webhook", "stripe declined payment handler"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Every payment that succeeds is handled. Every payment that fails is nothing at all: no event, no branch, no row, no email. The cart stays in <em>processing</em> until somebody writes in, and on the billing side a declined renewal starts a dunning sequence that the application knows nothing about while it is happening.",
"short_answer": """<p>Union <code>enabled_events</code> across every endpoint. Flag the one-off surface if <code>payment_intent.succeeded</code> is subscribed and <code>payment_intent.payment_failed</code> is not. Flag the billing surface separately if the account has active subscriptions and <code>invoice.payment_failed</code> is not subscribed.</p>
<p>Then quantify it: <code>GET /v1/events?types[]=invoice.payment_failed</code>. A non-empty result is the number of failures that have already happened without anybody being told.</p>""",
"problem": """<p>Failure is the same shape as silence here, which is why this survives. A PaymentIntent that fails does not disappear or error; it drops back to <code>requires_payment_method</code> and sits there. A subscription invoice that fails moves to <code>past_due</code> and starts a retry schedule. Both states are perfectly visible in the Dashboard and completely invisible to an application that was only ever told about successes.</p>
<p>The consequences separate along the same two surfaces. On the one-off side, orders stay in an intermediate state forever and nobody ever asks the customer for a different card. On the billing side the retries run, the customer receives whatever Stripe is configured to send, and your application keeps them fully provisioned throughout &mdash; and then, if you also lack the cancellation event, keeps them provisioned afterwards too.</p>""",
"why": """<p><strong>You subscribe to what you tested.</strong> The integration is built against a card that succeeds, the event that proves it works is the success event, and that is the one that goes into <code>enabled_events</code>. The declining test card gets used once to check the error message in the UI, which is client-side and needs no webhook at all.</p>
<p><strong>Failure is two separate surfaces, and neither implies the other.</strong> <code>payment_intent.payment_failed</code> covers a payment attempt that did not go through. <code>invoice.payment_failed</code> covers a billing attempt: a renewal declined, a soft decline that will be retried, or an invoice with no payment method available to charge. Subscribing to one leaves the other blind, and neither is implied by any success subscription.</p>
<p><strong>Nothing pushes when nothing happens.</strong> There is no event for "this cart has been in processing for six days". The failure event is the only push signal you get, and if it is not subscribed the only way to find these is a periodic sweep of intent and invoice states that somebody has to write.</p>
<p><strong>Authentication failures on renewals look like a third thing.</strong> A renewal that needs 3D Secure produces <code>invoice.payment_action_required</code>, not a decline. Without it, subscriptions freeze part-way through a payment that the customer could complete in one click if anything told them to.</p>""",
"steps": [
 {"h": "Union enabled_events across every endpoint, both modes",
  "body": """<p>Coverage is an account-level property. Payment events and billing events often live on different endpoints, and reading either one alone gives the wrong answer.</p>"""},
 {"h": "Check the one-off surface",
  "body": """<p><code>payment_intent.succeeded</code> present and <code>payment_intent.payment_failed</code> absent is the signature: a success path that was wired up deliberately and a failure path that was never considered.</p>"""},
 {"h": "Check the billing surface, but only if it applies",
  "body": """<p><code>GET /v1/subscriptions?limit=1&amp;status=active</code>. If the account has recurring billing at all, <code>invoice.payment_failed</code> is mandatory and its absence is a finding; on an account with no subscriptions it is noise.</p>"""},
 {"h": "Count the failures that already happened",
  "body": """<p><code>GET /v1/events?types[]=invoice.payment_failed</code> over the retained window. This is what turns a configuration gap into a number of customers, and it is usually the sentence that gets the fix prioritised.</p>"""},
 {"h": "Subscribe to both, then decide what the handler does",
  "body": """<p>Add <code>payment_intent.payment_failed</code> and <code>invoice.payment_failed</code>, plus <code>invoice.payment_action_required</code> if you take renewals with 3D Secure. Then write the branches: mark the order failed and prompt for another card, and on the billing side start warning rather than revoking, because the retries may still succeed.</p>"""},
],
"verify": """<p>Re-run the script. Both surfaces should report covered.</p>
<pre><code class="language-bash">python3 stripe_payment_failure_events.py
# covered   both payment and invoice failure events are subscribed</code></pre>""",
"code_intro": "Three GETs and no writes &mdash; the endpoints, one subscription to establish whether billing applies, and a type-filtered event read to size it. The classifier takes all three, because the same missing subscription is a tidy-up on an account with no recurring billing and an incident on one where invoices are already failing.",
"py_file": "stripe_payment_failure_events.py",
"py": '''"""Report whether anything subscribes to Stripe payment and invoice failure events.

Read only. Three GETs, no writes: give this a RESTRICTED key with read access to
Webhook Endpoints, Subscriptions and Events. The repair is printed, never
performed, because this script holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_payment_failure_events")

API = "https://api.stripe.com/v1"

PI_OK = "payment_intent.succeeded"
PI_FAIL = "payment_intent.payment_failed"
INV_FAIL = "invoice.payment_failed"


def verdict(subscribed, has_active_subscriptions, failed_invoices):
    """Classify payment-failure coverage across both surfaces. Pure and testable.

    `subscribed` is the union of enabled_events across every endpoint. The
    billing surface only counts when the account actually has recurring billing,
    and failures already seen turn a gap into an incident. Returns (state, detail).
    """
    events = set(subscribed or [])
    if "*" in events:
        return ("wildcard",
                "a wildcard covers both failure events, and every other type "
                "along with them.")

    one_off_gap = PI_OK in events and PI_FAIL not in events
    billing_gap = bool(has_active_subscriptions) and INV_FAIL not in events

    if billing_gap and failed_invoices:
        return ("blind",
                "%d invoice payment(s) already failed and %s is not subscribed. "
                "Dunning is running right now and nothing is being told."
                % (failed_invoices, INV_FAIL))
    if one_off_gap and billing_gap:
        return ("exposed",
                "neither %s nor %s is subscribed. Both the one-off and the "
                "billing failure paths are silent." % (PI_FAIL, INV_FAIL))
    if one_off_gap:
        return ("one-sided",
                "%s is subscribed and %s is not: the success path is wired and "
                "declines go nowhere." % (PI_OK, PI_FAIL))
    if billing_gap:
        return ("billing-gap",
                "the account has active subscriptions and %s is not subscribed. "
                "Renewal declines and exhausted retries are invisible." % INV_FAIL)
    if PI_FAIL in events or INV_FAIL in events:
        return ("covered", "both applicable failure events are subscribed")
    return ("no-payment-events",
            "nothing subscribes to payment success or failure at all. The gap "
            "here is the endpoint configuration rather than one event type.")


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def subscribed_union(session):
    """Every event type any endpoint on this account asks for."""
    union = set()
    for ep in get(session, "/webhook_endpoints", limit=100).get("data", []):
        union.update(ep.get("enabled_events") or [])
    return union


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-events", type=int, default=100,
                    help="how many failure events to count when sizing the gap")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    union = subscribed_union(s)
    active = get(s, "/subscriptions", limit=1, status="active").get("data", [])
    failures = get(s, "/events", limit=args.max_events,
                   **{"types[]": [INV_FAIL]}).get("data", [])

    state, detail = verdict(union, bool(active), len(failures))
    line = "%-17s %s" % (state, detail)
    if state in ("covered", "wildcard"):
        log.info(line)
        return 0

    log.warning(line)
    log.warning("  repair: add enabled_events[]=%s and enabled_events[]=%s to an "
                "existing endpoint at %s/webhook_endpoints/{id}", PI_FAIL, INV_FAIL, API)
    log.warning("  add invoice.payment_action_required as well if renewals use 3D Secure")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-payment-failure-events.mjs",
"js": '''/**
 * Report whether anything subscribes to Stripe payment and invoice failure events.
 *
 * Read only. Three GETs, no writes: give this a RESTRICTED key with read access
 * to Webhook Endpoints, Subscriptions and Events. The repair is printed, never
 * performed.
 */
const API = 'https://api.stripe.com/v1';

const PI_OK = 'payment_intent.succeeded';
const PI_FAIL = 'payment_intent.payment_failed';
const INV_FAIL = 'invoice.payment_failed';

/**
 * Classify payment-failure coverage across both surfaces. Pure and testable.
 * The billing surface only counts when the account actually has recurring
 * billing, and failures already seen turn a gap into an incident.
 */
export function verdict(subscribed, hasActiveSubscriptions, failedInvoices) {
  const events = new Set(subscribed ?? []);
  if (events.has('*')) {
    return ['wildcard',
      'a wildcard covers both failure events, and every other type along with them.'];
  }

  const oneOffGap = events.has(PI_OK) && !events.has(PI_FAIL);
  const billingGap = Boolean(hasActiveSubscriptions) && !events.has(INV_FAIL);

  if (billingGap && failedInvoices) {
    return ['blind',
      `${failedInvoices} invoice payment(s) already failed and ${INV_FAIL} is ` +
      'not subscribed. Dunning is running right now and nothing is being told.'];
  }
  if (oneOffGap && billingGap) {
    return ['exposed',
      `neither ${PI_FAIL} nor ${INV_FAIL} is subscribed. Both the one-off and ` +
      'the billing failure paths are silent.'];
  }
  if (oneOffGap) {
    return ['one-sided',
      `${PI_OK} is subscribed and ${PI_FAIL} is not: the success path is wired ` +
      'and declines go nowhere.'];
  }
  if (billingGap) {
    return ['billing-gap',
      `the account has active subscriptions and ${INV_FAIL} is not subscribed. ` +
      'Renewal declines and exhausted retries are invisible.'];
  }
  if (events.has(PI_FAIL) || events.has(INV_FAIL)) {
    return ['covered', 'both applicable failure events are subscribed'];
  }
  return ['no-payment-events',
    'nothing subscribes to payment success or failure at all. The gap here is ' +
    'the endpoint configuration rather than one event type.'];
}

async function get(key, path, params = {}) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) {
    if (Array.isArray(v)) for (const item of v) url.searchParams.append(k, item);
    else url.searchParams.set(k, v);
  }
  const res = await fetch(url, { headers: { Authorization: `Bearer ${key}` } });
  if (res.status === 401) {
    throw new Error('401 from Stripe: the key is wrong, or is for the other mode');
  }
  if (!res.ok) throw new Error(`${res.status} from ${url.pathname}`);
  return res.json();
}

export async function subscribedUnion(key) {
  const union = new Set();
  const { data = [] } = await get(key, '/webhook_endpoints', { limit: 100 });
  for (const ep of data) for (const t of ep.enabled_events ?? []) union.add(t);
  return union;
}

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }

  const union = await subscribedUnion(key);
  const { data: active = [] } = await get(key, '/subscriptions',
    { limit: 1, status: 'active' });
  const { data: failures = [] } = await get(key, '/events',
    { limit: 100, 'types[]': [INV_FAIL] });

  const [state, detail] = verdict(union, active.length > 0, failures.length);
  const line = `${state.padEnd(17)} ${detail}`;
  if (state === 'covered' || state === 'wildcard') {
    console.log(line);
    return;
  }

  console.warn(line);
  console.warn(`  repair: add enabled_events[]=${PI_FAIL} and ` +
               `enabled_events[]=${INV_FAIL} to an existing endpoint at ` +
               `${API}/webhook_endpoints/{id}`);
  console.warn('  add invoice.payment_action_required as well if renewals use 3D Secure');
  process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The tests exist to keep the two surfaces from collapsing into one. A missing <code>invoice.payment_failed</code> means nothing on an account that has never sold a subscription and means a live dunning incident on one where invoices are already failing, and the same subscription list produces both verdicts depending on inputs that have nothing to do with webhooks.",
"test_py_file": "test_stripe_payment_failure_events.py",
"test_py": '''from stripe_payment_failure_events import verdict


def test_success_subscribed_without_the_failure_is_one_sided():
    state, detail = verdict(["payment_intent.succeeded"], False, 0)
    assert state == "one-sided"
    assert "payment_intent.payment_failed" in detail


def test_active_subscriptions_with_failures_already_seen_is_an_incident():
    # Same missing subscription as the gap below; the failures make it live.
    state, detail = verdict(["payment_intent.succeeded",
                             "payment_intent.payment_failed"], True, 9)
    assert state == "blind"
    assert "9 invoice" in detail


def test_no_subscriptions_means_the_invoice_event_is_not_required():
    state, _ = verdict(["payment_intent.succeeded",
                        "payment_intent.payment_failed"], False, 0)
    assert state == "covered"


def test_both_surfaces_missing_is_reported_as_one_finding():
    state, _ = verdict(["payment_intent.succeeded", "invoice.paid"], True, 0)
    assert state == "exposed"


def test_an_account_with_no_payment_events_at_all():
    state, _ = verdict(["customer.created"], False, 0)
    assert state == "no-payment-events"


def test_a_wildcard_covers_both_surfaces():
    state, _ = verdict(["*"], True, 40)
    assert state == "wildcard"
''',
"test_js_file": "stripe-payment-failure-events.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict } from './stripe-payment-failure-events.mjs';

test('success subscribed without the failure is one sided', () => {
  const [state, detail] = verdict(['payment_intent.succeeded'], false, 0);
  assert.equal(state, 'one-sided');
  assert.match(detail, /payment_intent\\.payment_failed/);
});

test('active subscriptions with failures already seen is an incident', () => {
  const [state, detail] = verdict(
    ['payment_intent.succeeded', 'payment_intent.payment_failed'], true, 9);
  assert.equal(state, 'blind');
  assert.match(detail, /9 invoice/);
});

test('no subscriptions means the invoice event is not required', () => {
  const [state] = verdict(
    ['payment_intent.succeeded', 'payment_intent.payment_failed'], false, 0);
  assert.equal(state, 'covered');
});

test('both surfaces missing is reported as one finding', () => {
  const [state] = verdict(['payment_intent.succeeded', 'invoice.paid'], true, 0);
  assert.equal(state, 'exposed');
});

test('an account with no payment events at all', () => {
  assert.equal(verdict(['customer.created'], false, 0)[0], 'no-payment-events');
});

test('a wildcard covers both surfaces', () => {
  assert.equal(verdict(['*'], true, 40)[0], 'wildcard');
});
''',
"faq": [
 ("Isn't a failed payment already visible in the Dashboard?",
  "Yes, and nowhere in your application. The Dashboard shows the intent sitting in requires_payment_method and the invoice sitting past_due; your order table shows processing, your emails do not go out, and your access checks keep returning true. The event is what closes that gap."),
 ("What is the difference between payment_intent.payment_failed and invoice.payment_failed?",
  "The surface. payment_intent.payment_failed fires when a payment attempt does not go through, which is what a one-off checkout produces. invoice.payment_failed fires when a billing attempt fails, which is what a subscription renewal produces, including the case where there is no payment method available to charge at all."),
 ("Do I need both if I only sell subscriptions?",
  "invoice.payment_failed is the one that matters for renewals. Keep payment_intent.payment_failed as well if any first payment or one-off charge happens outside the billing flow, which on most accounts it does eventually."),
 ("Does Stripe retry a failed subscription payment on its own?",
  "Yes. Smart Retries reattempt the invoice on a schedule, so a single failure is not a cancellation and revoking access on the first one is wrong. The failure events tell you where in that sequence you are; the end of it arrives as customer.subscription.deleted, which is a separate subscription of its own."),
 ("What about renewals that need 3D Secure?",
  "That is invoice.payment_action_required rather than a decline. Without it, the subscription stalls waiting for an authentication the customer has not been asked for, which reads as a failure that no failure event explains."),
],
"related": [
 ("/stripe/dunning-retries-exhausted/", "Dunning retries exhausted with nothing left to try"),
 ("/stripe/missing-subscription-deleted/", "customer.subscription.deleted is missing, so access never ends"),
 ("/stripe/stale-requires-payment-method-intents/", "PaymentIntents sitting in requires_payment_method for weeks"),
],
"citations": [CITE_WEBHOOK_CREATE, CITE_EVENT_TYPES, CITE_BILLING_WEBHOOKS, CITE_WEBHOOKS],
},

]
