#!/usr/bin/env python3
"""Email field notes beyond SES: provider onboarding and bulk-sender compliance.

These are provider-agnostic where they can be. The DNS traps behave the same whether
the records came from Resend, Postmark, SendGrid or Mailgun, so the scripts take the
expected records as input rather than hard-coding one vendor's API.
"""

CITE_RFC8058 = ("RFC 8058 — Signalling one-click functional unsubscribe",
                "https://www.rfc-editor.org/rfc/rfc8058.html")
CITE_GMAIL = ("Email sender guidelines — Google Workspace Admin Help",
              "https://support.google.com/a/answer/81126")

GUIDES = [

{
"slug": "provider-records-added-to-the-root-domain",
"title": "Email Provider Records Added to the Root Instead of the Subdomain",
"description": "Verification never completes because the CNAMEs were added at the apex. The provider is looking for them one label deeper, on the sending subdomain.",
"h1": "provider records added to the root instead of the sending subdomain",
"category": "Deliverability",
"pill": "Diagnostic",
"chips": ["Any provider", "Python and Node.js", "Detect through DNS"],
"keywords": ["domain verification not completing", "Resend domain not verifying",
             "SendGrid CNAME not found", "Postmark DKIM pending", "send subdomain"],
"deps": "Python 3.9+ with dnspython, or Node.js 18+ (node:dns is built in)",
"lead": "The provider gave you three CNAMEs. You pasted them into your DNS host, waited, and verification is still pending an hour later. <code>dig</code> says the records exist and resolve correctly. They do &mdash; they are just not where the provider is looking. The records were meant for <code>send.yourdomain.com</code> and they went on <code>yourdomain.com</code>, one label short.",
"short_answer": """<p>Most providers issue records for a <strong>sending subdomain</strong>, not the apex. If the record name is <code>s1._domainkey.send.example.com</code> and you created <code>s1._domainkey.example.com</code>, verification will never pass no matter how long you wait.</p>
<p>Resolve the exact name the provider expects and compare. The script takes the expected records, checks each one at the precise name, and tells you whether it is missing, wrong, or present at the wrong depth &mdash; which is a different fix from the other two.</p>""",
"problem": """<p>Nothing errors. The DNS host accepted the records, they resolve, and a spot check with <code>dig</code> looks fine. The provider dashboard just sits at <em>pending</em> indefinitely, which reads as slow propagation rather than a mistake, so people wait days before questioning it.</p>
<p>The subdomain detail is easy to lose because DNS hosts differ in how they treat the name field. Some want the full name, some want only the part before your domain, and pasting a full name into a host that appends your domain gives you a record one label too deep instead of one too shallow &mdash; the same failure from the opposite direction.</p>""",
"why": """<p><strong>Providers separate sending from your main domain on purpose.</strong> A dedicated subdomain keeps sending reputation apart from the rest of your mail, and it lets them put an MX record for the Return-Path without touching the MX that receives your mail.</p>
<p><strong>DNS hosts disagree about the name field.</strong> Cloudflare wants the full name, most cPanel-style hosts want the relative part. The same paste produces different results, and neither errors.</p>
<p><strong>Verification failure looks like latency.</strong> Nothing distinguishes 'not propagated yet' from 'looking in the wrong place', so the natural response is to wait, which never resolves it.</p>""",
"steps": [
 {"h": "Get the exact names from the provider",
  "body": """<p>Not from the docs, from your own account &mdash; the tokens are per domain. Every provider exposes this: Postmark returns <code>DKIMPendingHost</code> and <code>DKIMPendingTextValue</code>, SendGrid returns the CNAME set from the domain authentication endpoint, Resend and Mailgun expose the same on their domain objects.</p>"""},
 {"h": "Resolve that exact name, not a shortened one",
  "body": """<p>Query the fully qualified name character for character. A record at a different depth resolves perfectly and is still useless.</p>
<pre><code class="language-bash">dig +short s1._domainkey.send.example.com CNAME
dig +short s1._domainkey.example.com CNAME    # the wrong-depth version</code></pre>"""},
 {"h": "Work out which way your DNS host wants the name",
  "body": """<p>Create one test record and resolve it. If you entered <code>send</code> and got <code>send.example.com</code>, the host appends. If you entered <code>send.example.com</code> and got <code>send.example.com.example.com</code>, it appends and you have just found your bug.</p>"""},
 {"h": "Fix the depth rather than adding more records",
  "body": """<p>Delete the wrong-depth record. Leaving it costs nothing but makes the next person's diagnosis harder, and a stray <code>_domainkey</code> at the apex will confuse anyone auditing DKIM later.</p>"""},
],
"verify": """<p>The provider is the authority. Re-trigger verification and read its own status rather than trusting DNS to look right:</p>
<pre><code class="language-bash">python provider_dns_check.py --expect expected.json
# every record: OK

# then ask the provider to re-check
curl -sX POST https://api.provider.example/domains/&lt;id&gt;/verify \\
  -H "Authorization: Bearer $API_KEY"</code></pre>""",
"code_intro": "The script takes the expected records as JSON &mdash; name, type and value, exactly as the provider gave them &mdash; and resolves each one. It distinguishes three failures that need different fixes: missing entirely, present with the wrong value, and present at the wrong depth, which is the one people misdiagnose as propagation delay.",
"py_file": "provider_dns_check.py",
"py": '''"""Check an email provider's expected DNS records actually exist, exactly.

Takes the records the provider issued and resolves each at its precise name. The
useful part is distinguishing three failures that look identical in a dashboard:
missing, wrong value, and right record at the WRONG DEPTH -- the last of which is
usually mistaken for slow propagation and waited out for days.
"""
import argparse
import json
import logging
import sys

import dns.resolver

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("provider_dns_check")


def resolve(name, rtype):
    try:
        answers = dns.resolver.resolve(name, rtype)
        return [str(a).strip('"').rstrip(".") for a in answers]
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
        return []


def diagnose(expected, resolver=resolve):
    """Pure-ish decision function; the resolver is injected so tests run offline.

    `expected` is {name, type, value}. Checks the exact name first, then two common
    wrong depths, so the message can say what actually happened rather than just
    'not found'.
    """
    name, rtype, want = expected["name"], expected["type"], expected["value"].rstrip(".")
    got = resolver(name, rtype)
    if want in got:
        return "OK", f"{name} -> {want}"
    if got:
        return "WRONG VALUE", f"{name} resolves to {got[0]}, expected {want}"

    # Not at the exact name. Is it one label short, or doubled up? Both are common
    # and both are entered by a human who did not know which their DNS host wanted.
    labels = name.split(".")
    apex = ".".join(labels[-2:])
    shallow = labels[0] + "." + apex if len(labels) > 3 else None
    doubled = f"{name}.{apex}"
    if shallow and want in resolver(shallow, rtype):
        return "WRONG DEPTH", f"found at {shallow}, provider wants {name}"
    if want in resolver(doubled, rtype):
        return "WRONG DEPTH", f"found at {doubled}; your DNS host appended the domain"
    return "MISSING", f"{name} does not resolve"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--expect", required=True,
                    help='JSON file: [{"name":..., "type":"CNAME", "value":...}]')
    args = ap.parse_args()

    expected = json.loads(open(args.expect).read())
    failed = False
    for rec in expected:
        state, detail = diagnose(rec)
        if state == "OK":
            log.info("OK          %s", detail)
        else:
            failed = True
            log.error("%-11s %s", state, detail)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "provider-dns-check.mjs",
"js": '''/**
 * Check an email provider's expected DNS records actually exist, exactly.
 *
 * The useful part is distinguishing three failures that look identical in a
 * dashboard: missing, wrong value, and right record at the WRONG DEPTH -- the last
 * of which is usually mistaken for slow propagation and waited out for days.
 */
import { promises as dns } from 'node:dns';
import { readFile } from 'node:fs/promises';

async function resolve(name, rtype) {
  try {
    if (rtype === 'CNAME') return (await dns.resolveCname(name)).map((v) => v.replace(/\\.$/, ''));
    if (rtype === 'TXT') return (await dns.resolveTxt(name)).map((c) => c.join(''));
    if (rtype === 'MX') return (await dns.resolveMx(name)).map((m) => m.exchange);
    return [];
  } catch {
    return [];
  }
}

/**
 * Pure-ish decision function; the resolver is injected so tests run offline.
 * `expected` is {name, type, value}.
 */
export async function diagnose(expected, resolver = resolve) {
  const { name, type } = expected;
  const want = expected.value.replace(/\\.$/, '');
  const got = await resolver(name, type);
  if (got.includes(want)) return { state: 'OK', detail: `${name} -> ${want}` };
  if (got.length) {
    return { state: 'WRONG VALUE', detail: `${name} resolves to ${got[0]}, expected ${want}` };
  }

  // Not at the exact name. One label short, or doubled up? Both are common and both
  // are entered by a human who did not know which their DNS host wanted.
  const labels = name.split('.');
  const apex = labels.slice(-2).join('.');
  const shallow = labels.length > 3 ? `${labels[0]}.${apex}` : null;
  const doubled = `${name}.${apex}`;
  if (shallow && (await resolver(shallow, type)).includes(want)) {
    return { state: 'WRONG DEPTH', detail: `found at ${shallow}, provider wants ${name}` };
  }
  if ((await resolver(doubled, type)).includes(want)) {
    return { state: 'WRONG DEPTH', detail: `found at ${doubled}; your DNS host appended the domain` };
  }
  return { state: 'MISSING', detail: `${name} does not resolve` };
}

async function main() {
  const file = process.argv[process.argv.indexOf('--expect') + 1];
  const expected = JSON.parse(await readFile(file, 'utf8'));
  let failed = false;
  for (const rec of expected) {
    const { state, detail } = await diagnose(rec);
    if (state === 'OK') console.log(`OK          ${detail}`);
    else { failed = true; console.error(`${state.padEnd(11)} ${detail}`); }
  }
  process.exit(failed ? 1 : 0);
}

if (import.meta.url === `file://${process.argv[1]}`) main();
''',
"test_intro": "Both wrong-depth cases are worth pinning down, because they are the ones a dashboard cannot distinguish from propagation delay and the ones people wait out for days.",
"test_py_file": "test_provider_dns_check.py",
"test_py": '''from provider_dns_check import diagnose

EXPECT = {"name": "s1._domainkey.send.example.com", "type": "CNAME",
          "value": "s1.dkim.provider.net"}


def fake(mapping):
    return lambda name, rtype: mapping.get(name, [])


def test_correct_record_passes():
    state, _ = diagnose(EXPECT, fake({EXPECT["name"]: ["s1.dkim.provider.net"]}))
    assert state == "OK"


def test_wrong_value_is_distinguished_from_missing():
    state, detail = diagnose(EXPECT, fake({EXPECT["name"]: ["s1.dkim.other.net"]}))
    assert state == "WRONG VALUE"
    assert "expected" in detail


def test_record_one_label_too_shallow():
    """Added at the apex instead of the sending subdomain."""
    state, detail = diagnose(EXPECT, fake({"s1._domainkey.example.com": ["s1.dkim.provider.net"]}))
    assert state == "WRONG DEPTH"
    assert "provider wants" in detail


def test_dns_host_appended_the_domain():
    doubled = "s1._domainkey.send.example.com.example.com"
    state, detail = diagnose(EXPECT, fake({doubled: ["s1.dkim.provider.net"]}))
    assert state == "WRONG DEPTH"
    assert "appended" in detail


def test_nothing_anywhere_is_missing():
    state, _ = diagnose(EXPECT, fake({}))
    assert state == "MISSING"
''',
"test_js_file": "provider-dns-check.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { diagnose } from './provider-dns-check.mjs';

const EXPECT = {
  name: 's1._domainkey.send.example.com', type: 'CNAME', value: 's1.dkim.provider.net',
};
const fake = (map) => async (name) => map[name] ?? [];

test('a correct record passes', async () => {
  const r = await diagnose(EXPECT, fake({ [EXPECT.name]: ['s1.dkim.provider.net'] }));
  assert.equal(r.state, 'OK');
});

test('wrong value is distinguished from missing', async () => {
  const r = await diagnose(EXPECT, fake({ [EXPECT.name]: ['s1.dkim.other.net'] }));
  assert.equal(r.state, 'WRONG VALUE');
});

test('a record one label too shallow', async () => {
  const r = await diagnose(EXPECT, fake({ 's1._domainkey.example.com': ['s1.dkim.provider.net'] }));
  assert.equal(r.state, 'WRONG DEPTH');
});

test('the DNS host appended the domain', async () => {
  const doubled = 's1._domainkey.send.example.com.example.com';
  const r = await diagnose(EXPECT, fake({ [doubled]: ['s1.dkim.provider.net'] }));
  assert.match(r.detail, /appended/);
});

test('nothing anywhere is missing', async () => {
  assert.equal((await diagnose(EXPECT, fake({}))).state, 'MISSING');
});
''',
"faq": [
 ("The records resolve, so why will the domain not verify?",
  "Because they resolve at the wrong name. Providers usually issue records for a sending subdomain such as send.example.com, and a record created at example.com resolves perfectly while being invisible to the check."),
 ("Why do providers use a subdomain at all?",
  "It keeps sending reputation separate from your main domain, and it lets them put an MX record for the Return-Path without disturbing the MX that receives your mail."),
 ("My DNS host doubled the domain. Why?",
  "Some hosts want the full record name and some want only the part before your domain, and neither errors on the wrong one. Pasting a fully qualified name into a host that appends your domain produces name.example.com.example.com."),
 ("How long should verification take?",
  "Minutes to a few hours once the records are correct. If it has been more than a day, it is almost never propagation — check the exact name before waiting any longer."),
 ("Should I delete the record I added at the wrong depth?",
  "Yes. It costs nothing to leave but it makes the next person's diagnosis harder, and a stray _domainkey record at the apex will confuse anyone auditing DKIM later."),
],
"related": [
 ("/email/list-unsubscribe-missing/", "Missing List-Unsubscribe now gets mail rejected outright"),
 ("/email/ses-identity-verified-but-dkim-drifted/", "DKIM records drift after a DNS migration"),
 ("/dns/dkim-selector-missing/", "DKIM selector record missing from the zone"),
],
"citations": [
 ("How do I manage domains using the API? — Postmark",
  "https://postmarkapp.com/support/article/1113-how-do-i-manage-domains-using-the-api"),
 ("Configure domain authentication — SendGrid docs",
  "https://www.twilio.com/docs/sendgrid/ui/account-and-settings/how-to-set-up-domain-authentication"),
 ("What if my domain is not verifying? — Resend",
  "https://resend.com/docs/knowledge-base/what-if-my-domain-is-not-verifying"),
],
},

{
"slug": "list-unsubscribe-missing",
"title": "Missing List-Unsubscribe Now Gets Bulk Mail Rejected",
"description": "Gmail and Yahoo moved from soft deferrals to permanent 550 rejections. Bulk marketing mail without one-click unsubscribe headers is refused outright.",
"h1": "missing List-Unsubscribe now gets bulk mail rejected outright",
"category": "Deliverability",
"pill": "Compliance",
"chips": ["RFC 8058", "Python and Node.js", "Check before you send"],
"keywords": ["List-Unsubscribe header", "RFC 8058 one-click unsubscribe",
             "Gmail bulk sender requirements", "550 rejection", "Yahoo sender rules"],
"deps": "Python 3.9+ (email is stdlib), or Node.js 18+",
"lead": "This one changed underneath everyone. When Google and Yahoo introduced their bulk-sender rules in February 2024, non-compliant mail was <em>deferred</em> with a 4xx &mdash; annoying, retryable, survivable. Since November 2025 it is a permanent <strong>550 rejection</strong>. Mail that was merely slow last year does not arrive at all now, and the fix is two headers most templates never had.",
"short_answer": """<p>If you send more than <strong>5,000 messages a day</strong> to personal Gmail or Yahoo accounts, marketing and promotional mail must carry <code>List-Unsubscribe</code> <em>and</em> <code>List-Unsubscribe-Post: List-Unsubscribe=One-Click</code>, per RFC 8058.</p>
<p>The link must work without making the recipient log in, and you must honour it within two days. Transactional mail is exempt. The script checks a rendered message for both headers and for the mistakes that make them non-compliant even when present.</p>""",
"problem": """<p>The failure is at the gateway, so it never reaches your bounce handling in a form that reads as 'you are missing a header'. You see a rise in hard bounces from two providers who between them are most of your consumer list.</p>
<p>Having the header is not the same as complying. <code>List-Unsubscribe</code> with only a <code>mailto:</code> and no HTTPS URL does not satisfy one-click. An HTTPS URL that lands on a login page does not either. And <code>List-Unsubscribe-Post</code> is a separate header that a lot of templates omit entirely, which turns a valid one-click into an ordinary link.</p>""",
"why": """<p><strong>The requirement arrived quietly and hardened later.</strong> February 2024 brought the rules with soft enforcement; November 2025 turned deferrals into rejections. Teams that saw no problem in 2024 concluded they were compliant.</p>
<p><strong>Two headers, not one.</strong> <code>List-Unsubscribe</code> alone predates the one-click standard by decades. RFC 8058 adds <code>List-Unsubscribe-Post</code>, and without it the receiver will not treat the link as one-click.</p>
<p><strong>The unsubscribe endpoint is usually built for humans.</strong> One-click sends an HTTP POST with no session and no cookies. An endpoint that expects a logged-in user, or a GET with a confirmation page, fails a check nobody tested.</p>""",
"steps": [
 {"h": "Check a rendered message, not the template",
  "body": """<p>Headers are often added by the sending layer rather than the template, so inspect what actually went out. Send one to a mailbox you control and read the raw source.</p>
<pre><code class="language-bash">grep -i '^List-Unsubscribe' raw-message.eml</code></pre>"""},
 {"h": "Make sure both headers are present and shaped right",
  "body": """<p><code>List-Unsubscribe</code> needs an HTTPS URL in angle brackets; a <code>mailto:</code> may be included as well but cannot be the only entry. <code>List-Unsubscribe-Post</code> must read exactly <code>List-Unsubscribe=One-Click</code>.</p>
<pre><code class="language-text">List-Unsubscribe: &lt;https://example.com/u/abc123&gt;, &lt;mailto:unsub@example.com&gt;
List-Unsubscribe-Post: List-Unsubscribe=One-Click</code></pre>"""},
 {"h": "Test the endpoint the way a receiver will",
  "body": """<p>POST to it with no cookies and no auth. It must return a 2xx and actually unsubscribe. If it redirects to a login, or only works as a GET, it fails for Gmail even though it works for a person clicking in a browser.</p>"""},
 {"h": "Do not add it to transactional mail",
  "body": """<p>One-click unsubscribe is required for marketing and promotional messages, not receipts, password resets or security alerts. Putting it on transactional mail invites people to unsubscribe from things they need.</p>"""},
],
"verify": """<p>Send to a Gmail address you control and read the raw source. Then exercise the endpoint the way a receiver does:</p>
<pre><code class="language-bash">curl -s -o /dev/null -w '%{http_code}\\n' -X POST \\
  -d 'List-Unsubscribe=One-Click' https://example.com/u/abc123
# 200, and the address is actually suppressed afterwards</code></pre>
<p>Watch the bounce rate from Gmail and Yahoo specifically. A 550 naming policy or unsubscribe is the signal that something is still wrong.</p>""",
"code_intro": "The script parses a raw message and checks both headers, the URL scheme, the exact <code>List-Unsubscribe-Post</code> value, and whether the message looks transactional &mdash; in which case the headers should not be there at all. It works on a file or standard input so it can sit in a template test suite.",
"py_file": "check_list_unsubscribe.py",
"py": '''"""Check a rendered message for RFC 8058 one-click unsubscribe compliance.

Since November 2025 Gmail and Yahoo reject non-compliant bulk mail with a permanent
550 rather than deferring it. Having the header is not enough: it needs an HTTPS
URL, and it needs the separate List-Unsubscribe-Post header to count as one-click.
"""
import argparse
import re
import sys
from email import policy
from email.parser import BytesParser

ONE_CLICK = "List-Unsubscribe=One-Click"


def check(headers, is_transactional=False):
    """Pure decision function over a mapping of headers.

    Returns a list of problems. Transactional mail is checked in reverse: it should
    NOT carry these headers, because inviting someone to unsubscribe from a password
    reset is its own kind of failure.
    """
    lu = headers.get("List-Unsubscribe", "") or ""
    lup = (headers.get("List-Unsubscribe-Post", "") or "").strip()

    if is_transactional:
        return ([] if not lu else
                ["transactional mail carries List-Unsubscribe; one-click is for "
                 "marketing and promotional mail only"])

    problems = []
    if not lu:
        problems.append("no List-Unsubscribe header")
    else:
        urls = re.findall(r"<([^>]+)>", lu)
        if not urls:
            problems.append("List-Unsubscribe has no value in angle brackets")
        elif not any(u.lower().startswith("https://") for u in urls):
            problems.append("List-Unsubscribe has no HTTPS URL; a mailto: alone is "
                            "not one-click")
    if not lup:
        problems.append("no List-Unsubscribe-Post header; without it the link is not "
                        "treated as one-click")
    elif lup != ONE_CLICK:
        problems.append(f"List-Unsubscribe-Post is {lup!r}, must be exactly {ONE_CLICK!r}")
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("message", nargs="?", help="raw .eml file; defaults to stdin")
    ap.add_argument("--transactional", action="store_true")
    args = ap.parse_args()

    raw = open(args.message, "rb").read() if args.message else sys.stdin.buffer.read()
    msg = BytesParser(policy=policy.default).parsebytes(raw)

    problems = check(msg, args.transactional)
    for p in problems:
        print(f"FAIL {p}", file=sys.stderr)
    if not problems:
        print("OK   one-click unsubscribe headers are compliant")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "check-list-unsubscribe.mjs",
"js": '''/**
 * Check a rendered message for RFC 8058 one-click unsubscribe compliance.
 *
 * Since November 2025 Gmail and Yahoo reject non-compliant bulk mail with a
 * permanent 550 rather than deferring it. Having the header is not enough.
 */
import { readFile } from 'node:fs/promises';

const ONE_CLICK = 'List-Unsubscribe=One-Click';

/**
 * Pure decision function over a mapping of headers.
 *
 * Transactional mail is checked in reverse: it should NOT carry these headers,
 * because inviting someone to unsubscribe from a password reset is its own failure.
 */
export function check(headers, isTransactional = false) {
  const get = (k) => headers[k] ?? headers[k.toLowerCase()] ?? '';
  const lu = get('List-Unsubscribe');
  const lup = get('List-Unsubscribe-Post').trim();

  if (isTransactional) {
    return lu ? ['transactional mail carries List-Unsubscribe; one-click is for '
      + 'marketing and promotional mail only'] : [];
  }

  const problems = [];
  if (!lu) problems.push('no List-Unsubscribe header');
  else {
    const urls = [...lu.matchAll(/<([^>]+)>/g)].map((m) => m[1]);
    if (!urls.length) problems.push('List-Unsubscribe has no value in angle brackets');
    else if (!urls.some((u) => u.toLowerCase().startsWith('https://'))) {
      problems.push('List-Unsubscribe has no HTTPS URL; a mailto: alone is not one-click');
    }
  }
  if (!lup) {
    problems.push('no List-Unsubscribe-Post header; without it the link is not treated as one-click');
  } else if (lup !== ONE_CLICK) {
    problems.push(`List-Unsubscribe-Post is "${lup}", must be exactly "${ONE_CLICK}"`);
  }
  return problems;
}

function parseHeaders(raw) {
  const head = raw.split(/\\r?\\n\\r?\\n/)[0];
  const out = {};
  for (const line of head.split(/\\r?\\n(?![ \\t])/)) {
    const i = line.indexOf(':');
    if (i > 0) out[line.slice(0, i).trim()] = line.slice(i + 1).trim().replace(/\\r?\\n[ \\t]+/g, ' ');
  }
  return out;
}

async function main() {
  const file = process.argv.slice(2).find((a) => !a.startsWith('--'));
  const raw = await readFile(file, 'utf8');
  const problems = check(parseHeaders(raw), process.argv.includes('--transactional'));
  problems.forEach((p) => console.error(`FAIL ${p}`));
  if (!problems.length) console.log('OK   one-click unsubscribe headers are compliant');
  process.exit(problems.length ? 1 : 0);
}

if (import.meta.url === `file://${process.argv[1]}`) main();
''',
"test_intro": "Three near-misses are worth locking down, because each one looks compliant at a glance: a mailto-only header, a missing Post header, and a Post header with the right idea but the wrong text.",
"test_py_file": "test_check_list_unsubscribe.py",
"test_py": '''from check_list_unsubscribe import check

GOOD = {
    "List-Unsubscribe": "<https://example.com/u/abc>, <mailto:u@example.com>",
    "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
}


def test_compliant_message_passes():
    assert check(GOOD) == []


def test_mailto_alone_is_not_one_click():
    headers = GOOD | {"List-Unsubscribe": "<mailto:u@example.com>"}
    assert any("HTTPS" in p for p in check(headers))


def test_missing_post_header_fails():
    headers = {"List-Unsubscribe": GOOD["List-Unsubscribe"]}
    assert any("List-Unsubscribe-Post" in p for p in check(headers))


def test_post_header_with_wrong_text_fails():
    """Right idea, wrong string. Receivers compare exactly."""
    headers = GOOD | {"List-Unsubscribe-Post": "One-Click"}
    assert any("must be exactly" in p for p in check(headers))


def test_transactional_mail_should_not_carry_it():
    assert check(GOOD, is_transactional=True)


def test_transactional_without_the_header_is_fine():
    assert check({}, is_transactional=True) == []
''',
"test_js_file": "check-list-unsubscribe.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { check } from './check-list-unsubscribe.mjs';

const GOOD = {
  'List-Unsubscribe': '<https://example.com/u/abc>, <mailto:u@example.com>',
  'List-Unsubscribe-Post': 'List-Unsubscribe=One-Click',
};

test('a compliant message passes', () => {
  assert.deepEqual(check(GOOD), []);
});

test('mailto alone is not one-click', () => {
  const h = { ...GOOD, 'List-Unsubscribe': '<mailto:u@example.com>' };
  assert.ok(check(h).some((p) => p.includes('HTTPS')));
});

test('a missing Post header fails', () => {
  const h = { 'List-Unsubscribe': GOOD['List-Unsubscribe'] };
  assert.ok(check(h).some((p) => p.includes('List-Unsubscribe-Post')));
});

test('a Post header with the wrong text fails', () => {
  const h = { ...GOOD, 'List-Unsubscribe-Post': 'One-Click' };
  assert.ok(check(h).some((p) => p.includes('must be exactly')));
});

test('transactional mail should not carry it', () => {
  assert.ok(check(GOOD, true).length);
});
''',
"faq": [
 ("What changed in November 2025?",
  "Enforcement hardened. Google and Yahoo introduced the bulk-sender rules in February 2024 with soft failures — 4xx deferrals that retried and often got through. Since November 2025 non-compliant mail gets a permanent 550, so it does not arrive at all."),
 ("Who has to comply?",
  "Senders of more than 5,000 messages a day to personal Gmail or Yahoo accounts. The requirement applies to marketing and promotional mail; transactional messages such as receipts and password resets are exempt."),
 ("I have List-Unsubscribe already. Is that enough?",
  "No. That header predates one-click by decades. RFC 8058 requires a second header, List-Unsubscribe-Post: List-Unsubscribe=One-Click, and without it receivers treat the link as an ordinary unsubscribe rather than one-click."),
 ("Can the unsubscribe link require a login?",
  "No. One-click sends an HTTP POST with no session and no cookies. An endpoint that expects a logged-in user, or only works as a GET with a confirmation page, fails the check even though it works fine for a person in a browser."),
 ("How quickly must an unsubscribe be honoured?",
  "Within two days. Continuing to send after that is what drives the spam complaint rate, which has its own threshold — 0.3% measured as a rolling rate."),
],
"related": [
 ("/email/provider-records-added-to-the-root-domain/", "Provider records added at the wrong depth"),
 ("/email/ses-bounce-rate-approaching-review/", "Bounce rate creeping toward account review"),
 ("/email/ses-mail-from-not-set/", "SPF and DKIM pass but DMARC fails"),
],
"citations": [CITE_RFC8058, CITE_GMAIL,
 ("Sender requirements and recommendations — Yahoo",
  "https://senders.yahooinc.com/best-practices/"),
 ("Bulk email sender requirements checklist — Red Sift",
  "https://redsift.com/guides/bulk-email-sender-requirements")],
},

]
