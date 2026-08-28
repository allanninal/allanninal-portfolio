#!/usr/bin/env python3
"""Cloudflare field notes. Pairs with /dns/ — that section covers records, this one
covers what Cloudflare does to traffic once the records point at it."""

CITE_SSL = ("Encryption modes — Cloudflare docs",
            "https://developers.cloudflare.com/ssl/origin-configuration/ssl-modes/")
CITE_API = ("Cloudflare API documentation",
            "https://developers.cloudflare.com/api/")
CITE_RULES = ("Page Rules migration — Cloudflare docs",
              "https://developers.cloudflare.com/rules/reference/page-rules-migration/")
CITE_PROXY = ("Proxy status — Cloudflare DNS docs",
              "https://developers.cloudflare.com/dns/proxy-status/")

GUIDES = [

{
"slug": "too-many-redirects-flexible-ssl",
"title": "ERR_TOO_MANY_REDIRECTS Is Almost Always Flexible SSL",
"description": "Cloudflare connects to the origin over HTTP, the origin redirects to HTTPS, Cloudflare follows it back. One setting causes the loop.",
"h1": "ERR_TOO_MANY_REDIRECTS is almost always Flexible SSL",
"category": "Cloudflare",
"pill": "Diagnostic",
"chips": ["Cloudflare API", "Python and Node.js", "One setting"],
"keywords": ["ERR_TOO_MANY_REDIRECTS", "Cloudflare Flexible SSL", "redirect loop",
             "SSL encryption mode", "Full Strict"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The site was fine yesterday. Now every request ends in <code>ERR_TOO_MANY_REDIRECTS</code> and the origin logs show the same request arriving over and over. Nothing changed on the server. What changed is that the origin started forcing HTTPS &mdash; a plugin, a new vhost, a security header &mdash; while Cloudflare is still set to <strong>Flexible</strong>, which means it talks to the origin over plain HTTP. The origin redirects to HTTPS, Cloudflare answers that redirect, and the two of them loop until the browser gives up.",
"short_answer": """<p><strong>Flexible</strong> encrypts the visitor-to-Cloudflare hop and uses plain HTTP from Cloudflare to your origin. If the origin redirects HTTP to HTTPS, that redirect comes back through Cloudflare, which requests over HTTP again. That is the loop.</p>
<p>Set the zone's SSL mode to <strong>Full (strict)</strong> if the origin has a valid certificate, or <strong>Full</strong> if it has a self-signed one. It is one API call, and it fixes the majority of these.</p>""",
"problem": """<p>The browser reports a redirect loop and nothing else. Server logs show repeated requests for the same path with a 301 or 302 response, which reads as the origin misbehaving. It is not; it is doing exactly what it was configured to do, to a request that arrives over HTTP because Cloudflare sent it that way.</p>
<p>What makes it confusing is that it appears without a deploy. Enabling a "force HTTPS" option in a CMS, installing a security plugin, or a hosting provider turning on HTTPS redirection by default will all trigger it against a Cloudflare zone that has been on Flexible for years.</p>""",
"why": """<p><strong>Flexible exists for origins that cannot do TLS at all.</strong> It was a reasonable option when certificates were expensive and awkward. With free certificates everywhere it is now mostly a trap, and it is still selectable.</p>
<p><strong>The padlock lies about the second hop.</strong> Visitors see HTTPS and assume the connection is encrypted end to end. Between Cloudflare and the origin it is plaintext, which is a security problem independent of the redirect loop.</p>
<p><strong>Both ends are behaving correctly.</strong> Cloudflare is honouring your setting; the origin is honouring its configuration. Nothing is broken in isolation, which is why the cause is hard to see from either side alone.</p>""",
"steps": [
 {"h": "Read the zone's SSL mode",
  "body": """<p>One call answers the question, and it is worth checking before touching the origin at all.</p>
<pre><code class="language-bash">curl -s -H "Authorization: Bearer $CF_API_TOKEN" \\
  "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/settings/ssl" \\
  | python3 -c "import sys,json; print(json.load(sys.stdin)['result']['value'])"
# "flexible" is the answer you are looking for</code></pre>"""},
 {"h": "Pick the right mode rather than the permissive one",
  "body": """<p><strong>Full (strict)</strong> validates the origin certificate and is what you want with any real certificate, including a free Cloudflare Origin CA one. <strong>Full</strong> encrypts but does not validate, which is right only for a self-signed certificate you have not replaced yet. Never go back to Flexible to make an error go away.</p>"""},
 {"h": "Check for redirect rules stacking on top",
  "body": """<p>An "Always Use HTTPS" setting or a redirect rule in Cloudflare, combined with an origin that also redirects, can produce a loop even after the SSL mode is right. The script reports both so you see the whole picture rather than fixing one and rediscovering the other.</p>"""},
 {"h": "Purge the cache afterwards",
  "body": """<p>A cached 301 outlives the fix. Browsers also cache permanent redirects aggressively, so test in a private window or with <code>curl</code> rather than trusting a reload.</p>"""},
],
"verify": """<p>Follow the redirects yourself and count them:</p>
<pre><code class="language-bash">curl -sIL https://example.com | grep -E '^(HTTP|location)'
# one 200, or at most a single 301 to the canonical host</code></pre>
<p>Then confirm the second hop is actually encrypted: with Full (strict), a deliberately broken origin certificate should produce a 526 rather than a silent fallback.</p>""",
"code_intro": "The script reads the SSL mode, the Always Use HTTPS setting and any redirect rules, and reports the combinations that produce a loop. Changing the mode requires <code>--apply</code> because it affects every request to the zone immediately.",
"py_file": "cloudflare_ssl_mode_check.py",
"py": '''"""Detect the Cloudflare settings combination that causes a redirect loop.

Flexible SSL plus an origin that forces HTTPS is the classic cause: Cloudflare
requests over HTTP, the origin redirects to HTTPS, Cloudflare follows it back. Both
ends are behaving correctly, which is why it is hard to see from either one.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("cloudflare_ssl_mode_check")

API = "https://api.cloudflare.com/client/v4"


def diagnose(ssl_mode, always_https, origin_forces_https):
    """Pure decision function over three settings.

    The loop needs a plaintext hop AND something redirecting it back. Either alone
    is fine, which is why this checks the combination rather than the SSL mode on
    its own.
    """
    problems = []
    if ssl_mode == "off":
        problems.append("SSL is off entirely; visitors are unencrypted")
    if ssl_mode == "flexible":
        if origin_forces_https:
            problems.append("Flexible SSL with an origin that forces HTTPS -- this is "
                            "the redirect loop. Set Full (strict).")
        else:
            problems.append("Flexible SSL: the Cloudflare-to-origin hop is plaintext "
                            "even though visitors see a padlock")
    if ssl_mode == "full":
        problems.append("Full (not strict) does not validate the origin certificate; "
                        "use Full (strict) unless the origin is self-signed")
    if always_https and origin_forces_https and ssl_mode in ("flexible", "off"):
        problems.append("Always Use HTTPS and an origin redirect are stacked on a "
                        "plaintext origin hop")
    return problems


def get(session, url):
    r = session.get(url, timeout=30)
    r.raise_for_status()
    return r.json().get("result", {})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zone-id", required=True)
    ap.add_argument("--origin-forces-https", action="store_true",
                    help="set if the origin redirects http to https")
    ap.add_argument("--set-mode", choices=["full", "strict"],
                    help="'strict' maps to Cloudflare's full(strict)")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    token = os.environ.get("CF_API_TOKEN")
    if not token:
        log.error("set CF_API_TOKEN")
        return 2
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {token}"})

    ssl_mode = get(s, f"{API}/zones/{args.zone_id}/settings/ssl").get("value")
    always = get(s, f"{API}/zones/{args.zone_id}/settings/always_use_https").get("value") == "on"
    log.info("ssl mode=%s  always_use_https=%s  origin_forces_https=%s",
             ssl_mode, always, args.origin_forces_https)

    problems = diagnose(ssl_mode, always, args.origin_forces_https)
    for p in problems:
        log.error(p)

    if args.set_mode:
        value = "strict" if args.set_mode == "strict" else "full"
        if args.apply:
            s.patch(f"{API}/zones/{args.zone_id}/settings/ssl",
                    json={"value": value}, timeout=30).raise_for_status()
            log.info("ssl mode set to %s -- purge the cache, a 301 outlives the fix", value)
        else:
            log.info("WOULD set ssl mode to %s -- pass --apply", value)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "cloudflare-ssl-mode-check.mjs",
"js": '''/**
 * Detect the Cloudflare settings combination that causes a redirect loop.
 *
 * Flexible SSL plus an origin that forces HTTPS is the classic cause. Both ends are
 * behaving correctly, which is why it is hard to see from either one.
 */
const API = 'https://api.cloudflare.com/client/v4';

/**
 * Pure decision function over three settings.
 *
 * The loop needs a plaintext hop AND something redirecting it back. Either alone is
 * fine, which is why this checks the combination.
 */
export function diagnose(sslMode, alwaysHttps, originForcesHttps) {
  const problems = [];
  if (sslMode === 'off') problems.push('SSL is off entirely; visitors are unencrypted');
  if (sslMode === 'flexible') {
    problems.push(originForcesHttps
      ? 'Flexible SSL with an origin that forces HTTPS -- this is the redirect loop. Set Full (strict).'
      : 'Flexible SSL: the Cloudflare-to-origin hop is plaintext even though visitors see a padlock');
  }
  if (sslMode === 'full') {
    problems.push('Full (not strict) does not validate the origin certificate; '
      + 'use Full (strict) unless the origin is self-signed');
  }
  if (alwaysHttps && originForcesHttps && ['flexible', 'off'].includes(sslMode)) {
    problems.push('Always Use HTTPS and an origin redirect are stacked on a plaintext origin hop');
  }
  return problems;
}

async function main() {
  const zone = process.argv[process.argv.indexOf('--zone-id') + 1];
  const originForces = process.argv.includes('--origin-forces-https');
  const apply = process.argv.includes('--apply');
  const setMode = process.argv[process.argv.indexOf('--set-mode') + 1];
  const token = process.env.CF_API_TOKEN;
  if (!token) { console.error('set CF_API_TOKEN'); process.exit(2); }
  const headers = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' };

  const get = async (path) => (await (await fetch(`${API}${path}`, { headers })).json()).result ?? {};
  const sslMode = (await get(`/zones/${zone}/settings/ssl`)).value;
  const always = (await get(`/zones/${zone}/settings/always_use_https`)).value === 'on';
  console.log(`ssl mode=${sslMode}  always_use_https=${always}  origin_forces_https=${originForces}`);

  const problems = diagnose(sslMode, always, originForces);
  problems.forEach((p) => console.error(p));

  if (process.argv.includes('--set-mode')) {
    const value = setMode === 'strict' ? 'strict' : 'full';
    if (apply) {
      await fetch(`${API}/zones/${zone}/settings/ssl`,
        { method: 'PATCH', headers, body: JSON.stringify({ value }) });
      console.log(`ssl mode set to ${value} -- purge the cache, a 301 outlives the fix`);
    } else {
      console.log(`WOULD set ssl mode to ${value} -- pass --apply`);
    }
  }
  process.exit(problems.length ? 1 : 0);
}

if (import.meta.url === `file://${process.argv[1]}`) main();
''',
"test_intro": "The point of the rule is that neither setting is wrong on its own. Flexible without an origin redirect is insecure but works; an origin redirect without Flexible is correct. Only the pair loops, and the tests say so.",
"test_py_file": "test_cloudflare_ssl_mode_check.py",
"test_py": '''from cloudflare_ssl_mode_check import diagnose


def test_strict_with_a_redirecting_origin_is_fine():
    assert diagnose("strict", True, True) == []


def test_flexible_plus_origin_redirect_is_the_loop():
    problems = diagnose("flexible", False, True)
    assert any("redirect loop" in p for p in problems)


def test_flexible_alone_is_still_flagged_as_insecure():
    """It works, but the second hop is plaintext behind a padlock."""
    problems = diagnose("flexible", False, False)
    assert problems and not any("redirect loop" in p for p in problems)


def test_full_without_strict_is_flagged():
    assert any("does not validate" in p for p in diagnose("full", False, False))


def test_ssl_off_is_reported():
    assert any("SSL is off" in p for p in diagnose("off", False, False))
''',
"test_js_file": "cloudflare-ssl-mode-check.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { diagnose } from './cloudflare-ssl-mode-check.mjs';

test('strict with a redirecting origin is fine', () => {
  assert.deepEqual(diagnose('strict', true, true), []);
});

test('flexible plus an origin redirect is the loop', () => {
  assert.ok(diagnose('flexible', false, true).some((p) => p.includes('redirect loop')));
});

test('flexible alone is still flagged as insecure', () => {
  const p = diagnose('flexible', false, false);
  assert.ok(p.length && !p.some((x) => x.includes('redirect loop')));
});

test('full without strict is flagged', () => {
  assert.ok(diagnose('full', false, false).some((p) => p.includes('does not validate')));
});
''',
"faq": [
 ("Why does Flexible SSL cause a redirect loop?",
  "Flexible means Cloudflare talks to your origin over plain HTTP. If the origin redirects HTTP to HTTPS, that redirect travels back through Cloudflare, which makes the same HTTP request again. Both ends are behaving correctly; the pairing is what loops."),
 ("Which mode should I use?",
  "Full (strict) if the origin has a valid certificate, including a free Cloudflare Origin CA one. Full only if it is self-signed and you have not replaced it yet. Flexible is a trap now that certificates are free."),
 ("Is Flexible insecure even when it works?",
  "Yes. Visitors see a padlock, but the hop between Cloudflare and your origin is plaintext. Anyone able to observe that path sees the traffic in the clear, which is a problem independent of the redirect loop."),
 ("It appeared without a deploy. How?",
  "Something on the origin started forcing HTTPS — a CMS setting, a security plugin, or a host enabling redirection by default. The Cloudflare side had been on Flexible for years and only became a problem when the origin changed."),
 ("I fixed the mode and it still loops. Why?",
  "Check for an Always Use HTTPS setting or a redirect rule in Cloudflare stacking on top of the origin's own redirect, and purge the cache — browsers cache a permanent redirect aggressively, so test with curl or a private window."),
],
"related": [
 ("/cloudflare/rule-not-applying-record-not-proxied/", "A rule that never applies because the record is grey-clouded"),
 ("/dns/www-apex-mismatch/", "www and apex configured inconsistently"),
 ("/cloudflare/purge-by-url-silently-does-nothing/", "A cache purge that reports success and clears nothing"),
],
"citations": [CITE_SSL, CITE_API,
 ("Troubleshooting redirect loops — Cloudflare docs",
  "https://developers.cloudflare.com/ssl/troubleshooting/too-many-redirects/")],
},

{
"slug": "rule-not-applying-record-not-proxied",
"title": "A Cloudflare Rule That Never Applies Because DNS Is Grey-Clouded",
"description": "Cache rules, redirects and WAF only run on proxied records. A grey-clouded hostname bypasses Cloudflare entirely, so the rule is never consulted.",
"h1": "a Cloudflare rule that never applies because the record is grey-clouded",
"category": "Cloudflare",
"pill": "Diagnostic",
"chips": ["Cloudflare API", "Python and Node.js", "Proxy status"],
"keywords": ["Cloudflare rule not working", "proxied vs DNS only", "orange cloud",
             "grey cloud bypass", "page rules not applying"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The redirect rule is right. The cache rule is right. You have re-read them four times and the syntax is fine. They never fire because the hostname they apply to is set to <strong>DNS only</strong> &mdash; the grey cloud &mdash; so requests go straight to your origin and never pass through Cloudflare at all. There is nothing wrong with the rule. Cloudflare is simply not in the path.",
"short_answer": """<p>Cloudflare rules &mdash; redirects, cache rules, WAF, page rules &mdash; only apply to traffic that is <strong>proxied</strong>. A DNS record with proxy status off resolves straight to your origin IP and skips every rule you have written.</p>
<p>The dashboard shows this as a small grey cloud next to an orange one, which is easy to miss. The API states it plainly as <code>proxied: false</code>, and that is what to check first when a rule appears to do nothing.</p>""",
"problem": """<p>Rules give no feedback about whether they matched. A rule that never fires looks exactly like a rule that fires and does nothing, so debugging starts with the rule expression and stays there. People rewrite the pattern, test it against the matcher, and conclude Cloudflare is broken.</p>
<p>It is common on hostnames that were deliberately unproxied at some point &mdash; a mail subdomain, an SSH host, something behind a VPN &mdash; and then reused for HTTP traffic later without anyone flipping the cloud back on.</p>""",
"why": """<p><strong>Proxying is a per-record choice, and both settings are legitimate.</strong> Mail servers and SSH hosts should be grey-clouded; proxying them would break them. So Cloudflare cannot warn you that unproxied is wrong, because usually it is right.</p>
<p><strong>The proxy status is also what exposes the origin.</strong> A grey-clouded record publishes your origin IP in public DNS, so this is not only a rules problem &mdash; it removes the DDoS protection people assume they have.</p>
<p><strong>Rules are configured somewhere else entirely.</strong> The record lives in DNS, the rule lives in Rules. Nothing on either screen mentions the other, and the dependency between them is only in the documentation.</p>""",
"steps": [
 {"h": "Check the proxy status of the exact hostname",
  "body": """<p>Not the apex, the hostname in the rule. They are configured independently and often differ.</p>
<pre><code class="language-bash">curl -s -H "Authorization: Bearer $CF_API_TOKEN" \\
  "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records?name=app.example.com" \\
  | python3 -c "import sys,json; [print(r['name'], r['type'], 'proxied' if r['proxied'] else 'DNS ONLY') for r in json.load(sys.stdin)['result']]"</code></pre>"""},
 {"h": "Confirm from outside whether traffic reaches Cloudflare",
  "body": """<p>A proxied hostname resolves to a Cloudflare address and its responses carry <code>cf-ray</code>. If that header is absent, nothing you configure in Cloudflare will ever run.</p>
<pre><code class="language-bash">curl -sI https://app.example.com | grep -i 'cf-ray\\|server'</code></pre>"""},
 {"h": "Only proxy what should be proxied",
  "body": """<p>Turn the cloud orange for HTTP and HTTPS hostnames. Leave MX targets, SSH hosts and anything on a non-standard port grey &mdash; proxying those breaks them, and Cloudflare only proxies a specific set of ports.</p>"""},
 {"h": "Treat an exposed origin IP as its own problem",
  "body": """<p>Once the record was grey-clouded, the origin IP was published. Proxying it now hides it from DNS but anyone who recorded it can still reach the origin directly. Firewall the origin to Cloudflare's ranges if that matters.</p>"""},
],
"verify": """<p>The <code>cf-ray</code> header is the definitive answer &mdash; if it is present, traffic is going through Cloudflare and the rules will be evaluated:</p>
<pre><code class="language-bash">curl -sI https://app.example.com | grep -i cf-ray
# cf-ray: 8a1b2c3d4e5f6789-LHR</code></pre>
<p>Then exercise the rule itself and confirm it now does what it was always supposed to.</p>""",
"code_intro": "The script lists every DNS record in a zone, flags the ones serving HTTP that are not proxied, and cross-references them against the hostnames your rules target &mdash; so it can say which specific rule is dead rather than just listing grey clouds. It leaves mail and non-HTTP records alone, because those are correctly unproxied.",
"py_file": "cloudflare_proxy_audit.py",
"py": '''"""Find Cloudflare rules that can never fire because the record is not proxied.

Rules only apply to proxied traffic. A grey-clouded record resolves straight to the
origin, so the rule is never consulted -- which looks identical to a rule that
matches and does nothing.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("cloudflare_proxy_audit")

API = "https://api.cloudflare.com/client/v4"
# Records that SHOULD be unproxied. Proxying these breaks them, so they are not
# findings -- reporting them would train people to ignore the output.
NEVER_PROXY = {"MX", "TXT", "NS", "SRV", "CAA", "PTR"}


def unproxied_http_records(records):
    """Pure decision function.

    Only A, AAAA and CNAME records can be proxied at all. Mail and metadata records
    are correctly grey and must not be reported.
    """
    return [r for r in records
            if r.get("type") in {"A", "AAAA", "CNAME"}
            and r.get("type") not in NEVER_PROXY
            and not r.get("proxied", False)]


def dead_rules(rule_targets, unproxied_names):
    """Which configured hostnames point at something Cloudflare never sees?"""
    grey = {r["name"] for r in unproxied_names}
    return [t for t in rule_targets if t in grey]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zone-id", required=True)
    ap.add_argument("--rule-target", nargs="*", default=[],
                    help="hostnames your rules apply to")
    args = ap.parse_args()

    token = os.environ.get("CF_API_TOKEN")
    if not token:
        log.error("set CF_API_TOKEN")
        return 2
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {token}"})

    r = s.get(f"{API}/zones/{args.zone_id}/dns_records",
              params={"per_page": 500}, timeout=30)
    r.raise_for_status()
    records = r.json().get("result", [])

    grey = unproxied_http_records(records)
    log.info("%d record(s); %d HTTP record(s) not proxied", len(records), len(grey))
    for rec in grey:
        log.warning("DNS ONLY  %-40s %s -> %s  (origin IP is public; rules will not run)",
                    rec["name"], rec["type"], rec.get("content"))

    dead = dead_rules(args.rule_target, grey)
    for t in dead:
        log.error("RULE DEAD  a rule targeting %s can never fire -- that hostname "
                  "bypasses Cloudflare entirely", t)
    return 1 if dead else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "cloudflare-proxy-audit.mjs",
"js": '''/**
 * Find Cloudflare rules that can never fire because the record is not proxied.
 *
 * Rules only apply to proxied traffic. A grey-clouded record resolves straight to
 * the origin, so the rule is never consulted.
 */
const API = 'https://api.cloudflare.com/client/v4';
// Records that SHOULD be unproxied. Reporting them would train people to ignore output.
const NEVER_PROXY = new Set(['MX', 'TXT', 'NS', 'SRV', 'CAA', 'PTR']);

/**
 * Pure decision function. Only A, AAAA and CNAME can be proxied at all; mail and
 * metadata records are correctly grey.
 */
export function unproxiedHttpRecords(records) {
  return records.filter((r) => ['A', 'AAAA', 'CNAME'].includes(r.type)
    && !NEVER_PROXY.has(r.type) && !r.proxied);
}

export function deadRules(ruleTargets, unproxied) {
  const grey = new Set(unproxied.map((r) => r.name));
  return ruleTargets.filter((t) => grey.has(t));
}

async function main() {
  const zone = process.argv[process.argv.indexOf('--zone-id') + 1];
  const at = process.argv.indexOf('--rule-target');
  const targets = at === -1 ? [] : process.argv.slice(at + 1).filter((a) => !a.startsWith('--'));
  const token = process.env.CF_API_TOKEN;
  if (!token) { console.error('set CF_API_TOKEN'); process.exit(2); }

  const res = await fetch(`${API}/zones/${zone}/dns_records?per_page=500`,
    { headers: { Authorization: `Bearer ${token}` } });
  const { result: records = [] } = await res.json();

  const grey = unproxiedHttpRecords(records);
  console.log(`${records.length} record(s); ${grey.length} HTTP record(s) not proxied`);
  for (const rec of grey) {
    console.warn(`DNS ONLY  ${rec.name.padEnd(40)} ${rec.type} -> ${rec.content}  (origin IP is public)`);
  }
  const dead = deadRules(targets, grey);
  for (const t of dead) {
    console.error(`RULE DEAD  a rule targeting ${t} can never fire -- that hostname bypasses Cloudflare`);
  }
  process.exit(dead.length ? 1 : 0);
}

if (import.meta.url === `file://${process.argv[1]}`) main();
''',
"test_intro": "The important behaviour is what the audit stays quiet about. An MX record is supposed to be grey, and reporting it as a finding is how a report becomes noise nobody reads.",
"test_py_file": "test_cloudflare_proxy_audit.py",
"test_py": '''from cloudflare_proxy_audit import unproxied_http_records, dead_rules


def rec(name, rtype="A", proxied=True):
    return {"name": name, "type": rtype, "proxied": proxied, "content": "203.0.113.1"}


def test_a_proxied_record_is_not_reported():
    assert unproxied_http_records([rec("app.example.com")]) == []


def test_a_grey_clouded_a_record_is_reported():
    out = unproxied_http_records([rec("app.example.com", proxied=False)])
    assert len(out) == 1


def test_mx_records_are_never_reported():
    """MX must be grey. Reporting it is how a report becomes noise."""
    assert unproxied_http_records([rec("example.com", "MX", proxied=False)]) == []


def test_txt_records_are_never_reported():
    assert unproxied_http_records([rec("example.com", "TXT", proxied=False)]) == []


def test_a_rule_on_a_grey_hostname_is_dead():
    grey = unproxied_http_records([rec("app.example.com", proxied=False)])
    assert dead_rules(["app.example.com"], grey) == ["app.example.com"]


def test_a_rule_on_a_proxied_hostname_is_live():
    grey = unproxied_http_records([rec("app.example.com", proxied=True)])
    assert dead_rules(["app.example.com"], grey) == []
''',
"test_js_file": "cloudflare-proxy-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { unproxiedHttpRecords, deadRules } from './cloudflare-proxy-audit.mjs';

const rec = (name, type = 'A', proxied = true) => ({ name, type, proxied, content: '203.0.113.1' });

test('a proxied record is not reported', () => {
  assert.deepEqual(unproxiedHttpRecords([rec('app.example.com')]), []);
});

test('a grey-clouded A record is reported', () => {
  assert.equal(unproxiedHttpRecords([rec('app.example.com', 'A', false)]).length, 1);
});

test('MX records are never reported', () => {
  assert.deepEqual(unproxiedHttpRecords([rec('example.com', 'MX', false)]), []);
});

test('a rule on a grey hostname is dead', () => {
  const grey = unproxiedHttpRecords([rec('app.example.com', 'A', false)]);
  assert.deepEqual(deadRules(['app.example.com'], grey), ['app.example.com']);
});
''',
"faq": [
 ("Why does my Cloudflare rule do nothing?",
  "Most often because the hostname it targets is set to DNS only. Rules apply to proxied traffic; a grey-clouded record resolves straight to your origin and never passes through Cloudflare, so the rule is never consulted."),
 ("How do I check without the dashboard?",
  "The DNS records API states proxied: true or false plainly. From outside, a proxied hostname returns a cf-ray header — if that header is missing, nothing you configure in Cloudflare will run."),
 ("Should everything be proxied?",
  "No. MX targets, SSH hosts and anything on a non-standard port must stay grey, because Cloudflare only proxies a specific set of ports and proxying those would break them. Proxy HTTP and HTTPS hostnames."),
 ("Does grey-clouding affect anything besides rules?",
  "Yes, and it is the bigger problem. A grey-clouded record publishes your origin IP in public DNS, so the DDoS protection people assume they have is not there. Turning the cloud orange hides it going forward but does not un-publish it."),
 ("The record is proxied and the rule still does not fire. Now what?",
  "Check rule ordering and any earlier rule that terminates evaluation, and confirm the expression matches the exact hostname and path. Once cf-ray is present the traffic is reaching Cloudflare, so the problem really is the rule."),
],
"related": [
 ("/cloudflare/too-many-redirects-flexible-ssl/", "ERR_TOO_MANY_REDIRECTS is almost always Flexible SSL"),
 ("/dns/proxied-record-forces-ttl/", "A proxied record overrides your configured TTL"),
 ("/cloudflare/only-one-page-rule-applies/", "Only one Page Rule applies, and it is the one at the top"),
],
"citations": [CITE_PROXY, CITE_RULES, CITE_API],
},

]
