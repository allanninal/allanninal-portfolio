#!/usr/bin/env python3
"""Second half of the Cloudflare field notes. Kept in its own file because editing
a large Python literal in place is how guides_ses.py got broken twice."""

CITE_PAGE_RULES = ("Page Rules — Cloudflare docs",
                   "https://developers.cloudflare.com/rules/page-rules/")
CITE_API = ("Cloudflare API documentation",
            "https://developers.cloudflare.com/api/")
CITE_PURGE_SINGLE = ("Purge by single file: limitations and alternatives — Cloudflare docs",
                     "https://developers.cloudflare.com/cache/how-to/purge-cache/purge-by-single-file/")
CITE_PURGE_PREFIX = ("Purge cache by prefix — Cloudflare docs",
                     "https://developers.cloudflare.com/cache/how-to/purge-cache/purge_by_prefix/")
CITE_CACHE_RULES = ("Cache Rules — Cloudflare docs",
                    "https://developers.cloudflare.com/cache/how-to/cache-rules/")
CITE_CACHE_KEYS = ("Cache keys — Cloudflare docs",
                   "https://developers.cloudflare.com/cache/how-to/cache-keys/")
CITE_STATUS = ("Cache responses and CF-Cache-Status — Cloudflare docs",
               "https://developers.cloudflare.com/cache/concepts/cache-responses/")

GUIDES2 = [

{
"slug": "only-one-page-rule-applies",
"title": "Only One Page Rule Applies, and It Is the One at the Top",
"description": "Page Rules do not stack. The highest-priority match wins and every other matching rule is skipped, silently.",
"h1": "only one Page Rule applies, and it is the one at the top",
"category": "Cloudflare",
"pill": "Diagnostic",
"chips": ["Cloudflare API", "Python and Node.js", "Rule ordering"],
"keywords": ["Cloudflare Page Rules not working", "page rule priority", "page rules order",
             "only one page rule applies", "page rules vs cache rules"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "You have a broad rule near the top that caches everything, and a specific rule further down that adds a redirect. Both patterns match the URL, so you expect both actions. You get one. <strong>Only the highest-priority matching Page Rule takes effect on a request</strong> &mdash; every other match is discarded, with no log line, no warning, and no indication in the dashboard that a rule was skipped.",
"short_answer": """<p>Page Rules are not a list of things that all happen. They are a first-match-wins lookup: Cloudflare finds the highest-priority rule whose pattern matches and applies <em>only</em> that one.</p>
<p>So a broad pattern like <code>example.com/*</code> sitting above a specific one shadows it permanently. Order most specific to least specific &mdash; or move the behaviour to the modern rule types, which are evaluated per phase and genuinely do stack.</p>""",
"problem": """<p>The symptom is a rule that is present, enabled, correctly written and does nothing. Testing it in isolation works. Testing it on the live zone does not, because a broader rule above it is winning every request.</p>
<p>Two smaller traps compound it. A pattern with no scheme matches both <code>http://</code> and <code>https://</code>, so it is broader than it looks. And a <em>disabled</em> rule still counts against the rule quota for your plan, so a zone can be full of rules that do nothing while refusing to let you add the one you need.</p>""",
"why": """<p><strong>First-match-wins is a reasonable model that reads like a stack.</strong> The dashboard shows a vertical list with drag handles, which is exactly how an additive rule engine looks. Nothing on the screen says the rules below the first match will not run.</p>
<p><strong>Patterns are broader than they appear.</strong> The five-segment form is <code>&lt;SCHEME&gt;://&lt;HOSTNAME&gt;:&lt;PORT&gt;/&lt;PATH&gt;?&lt;QUERY_STRING&gt;</code>, and both scheme and port are optional. Omitting them widens the match rather than narrowing it, so a rule written to be tidy ends up shadowing more than intended.</p>
<p><strong>The modern rule types behave differently.</strong> Cache Rules, Redirect Rules, Configuration Rules and Origin Rules run in separate phases and do combine. Advice written for one model is wrong for the other, and both sets of advice are in circulation.</p>""",
"steps": [
 {"h": "List the rules in priority order",
  "body": """<p>The API returns them with an explicit priority, which is more reliable than reading the dashboard's visual order.</p>
<pre><code class="language-bash">curl -s -H "Authorization: Bearer $CF_API_TOKEN" \\
  "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/pagerules" \\
  | python3 -c "import sys,json; [print(r['priority'], r['status'], r['targets'][0]['constraint']['value']) for r in sorted(json.load(sys.stdin)['result'], key=lambda x: -x['priority'])]"</code></pre>"""},
 {"h": "Find which rule actually wins for a given URL",
  "body": """<p>Walk the rules from highest priority down and stop at the first pattern that matches. That rule is the only one applied; everything after it is dead for that URL. This is what the script does, and it is the piece the dashboard will not tell you.</p>"""},
 {"h": "Reorder specific above general",
  "body": """<p>The general rule belongs at the bottom. If two rules genuinely need to both apply, Page Rules cannot express that &mdash; you need either one combined rule or the modern rule types.</p>"""},
 {"h": "Delete disabled rules instead of leaving them",
  "body": """<p>A disabled rule occupies a slot in your quota while doing nothing. If you are near the limit, this is usually where the space is.</p>"""},
 {"h": "Move the behaviour to the modern rule types",
  "body": """<p>Redirect Rules, Cache Rules, Configuration Rules and Origin Rules are evaluated in separate phases, so a cache setting and a redirect can both apply to the same request. That is the fix for wanting two actions at once, not a cleverer pattern.</p>"""},
],
"verify": """<p>Request a URL you expect the specific rule to affect and look at what actually happened:</p>
<pre><code class="language-bash">curl -sI "https://example.com/promo?utm_source=x" | grep -i 'cf-cache-status\\|location'</code></pre>
<p>Cloudflare's Trace tool will also show which rule triggered for a specific URL, which settles the argument faster than reasoning about patterns.</p>""",
"code_intro": "The script fetches the Page Rules, sorts them by priority, and for each URL you give it reports the winning rule and every rule that matched but was skipped. That second list is the interesting one — it is the set of rules you believe are running and are not. It also flags disabled rules consuming quota.",
"py_file": "cloudflare_page_rule_shadow.py",
"py": '''"""Find Page Rules that match but never run.

Only the highest-priority matching rule takes effect. Every other match is
discarded silently, so a rule can be present, enabled, correct and dead.
"""
import argparse
import fnmatch
import logging
import os
import sys
from urllib.parse import urlsplit

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("cloudflare_page_rule_shadow")

API = "https://api.cloudflare.com/client/v4"


def normalise(pattern, url):
    """Strip the optional scheme from both sides before comparing.

    A pattern with no scheme matches http and https. Comparing raw strings would
    make such a pattern look narrower than it is -- the opposite of the truth.
    """
    if "://" not in pattern:
        url = urlsplit(url).netloc + urlsplit(url).path + (
            "?" + urlsplit(url).query if urlsplit(url).query else "")
    return pattern, url


def matches(pattern, url):
    pat, target = normalise(pattern, url)
    return fnmatch.fnmatch(target, pat)


def evaluate(rules, url):
    """Return (winner, shadowed) for one URL.

    rules: list of dicts with 'priority', 'pattern', 'enabled', 'actions'.
    Higher priority wins. Disabled rules never match at all.
    """
    active = sorted((r for r in rules if r.get("enabled", True)),
                    key=lambda r: -r["priority"])
    hits = [r for r in active if matches(r["pattern"], url)]
    if not hits:
        return None, []
    return hits[0], hits[1:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zone-id", required=True)
    ap.add_argument("--url", nargs="+", required=True)
    args = ap.parse_args()

    token = os.environ.get("CF_API_TOKEN")
    if not token:
        log.error("set CF_API_TOKEN")
        return 2

    r = requests.get(f"{API}/zones/{args.zone_id}/pagerules",
                     headers={"Authorization": f"Bearer {token}"}, timeout=30)
    r.raise_for_status()
    raw = r.json().get("result", [])

    rules = [{
        "priority": item.get("priority", 0),
        "pattern": item["targets"][0]["constraint"]["value"],
        "enabled": item.get("status") == "active",
        "actions": [a.get("id") for a in item.get("actions", [])],
    } for item in raw]

    disabled = [x for x in rules if not x["enabled"]]
    for d in disabled:
        log.warning("DISABLED  %s -- still counts against your rule quota", d["pattern"])

    shadowed_any = False
    for url in args.url:
        winner, shadowed = evaluate(rules, url)
        if not winner:
            log.info("%s -- no Page Rule matches", url)
            continue
        log.info("%s -> %s  actions=%s", url, winner["pattern"], winner["actions"])
        for s in shadowed:
            shadowed_any = True
            log.error("  SHADOWED  %s (actions=%s) matches but never runs -- only the "
                      "highest-priority match applies", s["pattern"], s["actions"])
    return 1 if shadowed_any else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "cloudflare-page-rule-shadow.mjs",
"js": '''/**
 * Find Page Rules that match but never run.
 *
 * Only the highest-priority matching rule takes effect. Every other match is
 * discarded silently, so a rule can be present, enabled, correct and dead.
 */
const API = 'https://api.cloudflare.com/client/v4';

const toRegExp = (pattern) => new RegExp(
  `^${pattern.replace(/[.+^${}()|[\\]\\\\]/g, '\\\\$&').replace(/\\*/g, '.*')}$`);

/**
 * Strip the optional scheme from both sides before comparing. A pattern with no
 * scheme matches http and https, so a raw string compare makes it look narrower
 * than it is -- the opposite of the truth.
 */
export function matches(pattern, url) {
  const target = pattern.includes('://') ? url : url.replace(/^https?:\\/\\//, '');
  return toRegExp(pattern).test(target);
}

/** Return { winner, shadowed } for one URL. Disabled rules never match at all. */
export function evaluate(rules, url) {
  const active = rules.filter((r) => r.enabled !== false).sort((a, b) => b.priority - a.priority);
  const hits = active.filter((r) => matches(r.pattern, url));
  return { winner: hits[0] ?? null, shadowed: hits.slice(1) };
}

async function main() {
  const zone = process.argv[process.argv.indexOf('--zone-id') + 1];
  const ui = process.argv.indexOf('--url');
  const urls = process.argv.slice(ui + 1).filter((a) => !a.startsWith('--'));
  const token = process.env.CF_API_TOKEN;
  if (!token) { console.error('set CF_API_TOKEN'); process.exit(2); }

  const res = await fetch(`${API}/zones/${zone}/pagerules`,
    { headers: { Authorization: `Bearer ${token}` } });
  const { result: raw = [] } = await res.json();

  const rules = raw.map((item) => ({
    priority: item.priority ?? 0,
    pattern: item.targets[0].constraint.value,
    enabled: item.status === 'active',
    actions: (item.actions ?? []).map((a) => a.id),
  }));

  for (const d of rules.filter((r) => !r.enabled)) {
    console.warn(`DISABLED  ${d.pattern} -- still counts against your rule quota`);
  }

  let shadowedAny = false;
  for (const url of urls) {
    const { winner, shadowed } = evaluate(rules, url);
    if (!winner) { console.log(`${url} -- no Page Rule matches`); continue; }
    console.log(`${url} -> ${winner.pattern}  actions=${winner.actions}`);
    for (const s of shadowed) {
      shadowedAny = true;
      console.error(`  SHADOWED  ${s.pattern} (actions=${s.actions}) matches but never runs`);
    }
  }
  process.exit(shadowedAny ? 1 : 0);
}

if (import.meta.url === `file://${process.argv[1]}`) main();
''',
"test_intro": "The tests pin the two things that make this counter-intuitive: a broad rule above a specific one shadows it rather than combining with it, and a pattern written without a scheme is wider than the same pattern with one.",
"test_py_file": "test_cloudflare_page_rule_shadow.py",
"test_py": '''from cloudflare_page_rule_shadow import evaluate, matches


def rule(priority, pattern, enabled=True):
    return {"priority": priority, "pattern": pattern, "enabled": enabled, "actions": ["x"]}


def test_broad_rule_above_specific_shadows_it():
    rules = [rule(2, "example.com/*"), rule(1, "example.com/promo*")]
    winner, shadowed = evaluate(rules, "https://example.com/promo")
    assert winner["pattern"] == "example.com/*"
    assert [s["pattern"] for s in shadowed] == ["example.com/promo*"]


def test_specific_above_broad_is_the_fix():
    rules = [rule(2, "example.com/promo*"), rule(1, "example.com/*")]
    winner, _ = evaluate(rules, "https://example.com/promo")
    assert winner["pattern"] == "example.com/promo*"


def test_a_pattern_without_a_scheme_matches_https():
    """Omitting the scheme widens the match rather than narrowing it."""
    assert matches("example.com/*", "https://example.com/x")


def test_a_pattern_with_a_scheme_does_not_match_the_other_one():
    assert not matches("http://example.com/*", "https://example.com/x")


def test_a_disabled_rule_never_wins():
    rules = [rule(2, "example.com/*", enabled=False), rule(1, "example.com/promo*")]
    winner, shadowed = evaluate(rules, "https://example.com/promo")
    assert winner["pattern"] == "example.com/promo*"
    assert shadowed == []


def test_no_match_is_not_an_error():
    assert evaluate([rule(1, "other.com/*")], "https://example.com/") == (None, [])
''',
"test_js_file": "cloudflare-page-rule-shadow.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { evaluate, matches } from './cloudflare-page-rule-shadow.mjs';

const rule = (priority, pattern, enabled = true) => ({ priority, pattern, enabled, actions: ['x'] });

test('a broad rule above a specific one shadows it', () => {
  const { winner, shadowed } = evaluate(
    [rule(2, 'example.com/*'), rule(1, 'example.com/promo*')], 'https://example.com/promo');
  assert.equal(winner.pattern, 'example.com/*');
  assert.deepEqual(shadowed.map((s) => s.pattern), ['example.com/promo*']);
});

test('specific above broad is the fix', () => {
  const { winner } = evaluate(
    [rule(2, 'example.com/promo*'), rule(1, 'example.com/*')], 'https://example.com/promo');
  assert.equal(winner.pattern, 'example.com/promo*');
});

test('a pattern without a scheme matches https', () => {
  assert.ok(matches('example.com/*', 'https://example.com/x'));
});

test('a disabled rule never wins', () => {
  const { winner } = evaluate(
    [rule(2, 'example.com/*', false), rule(1, 'example.com/promo*')], 'https://example.com/promo');
  assert.equal(winner.pattern, 'example.com/promo*');
});
''',
"faq": [
 ("Do Cloudflare Page Rules stack?",
  "No. Only the highest-priority matching Page Rule takes effect on a request; every other matching rule is skipped with no warning. If you need two actions on the same request, use one combined rule or move to the modern rule types."),
 ("Why does my Page Rule do nothing?",
  "Usually a broader rule above it is winning. Order rules most specific to least specific — a pattern like example.com/* at the top shadows everything below it permanently."),
 ("Does a pattern without https:// only match http?",
  "It matches both. Scheme and port are optional segments, and omitting them widens the match rather than narrowing it, which is how tidy-looking patterns end up shadowing more than intended."),
 ("Do disabled Page Rules count against my limit?",
  "Yes. A disabled rule still appears in the dashboard, is still editable, and still occupies a slot in your plan's quota. If you cannot add a rule, that is usually where the space went."),
 ("What should I use instead of Page Rules?",
  "Redirect Rules, Cache Rules, Configuration Rules and Origin Rules. They run in separate phases, so a cache setting and a redirect can both apply to one request — which is what people expect Page Rules to do."),
],
"related": [
 ("/cloudflare/rule-not-applying-record-not-proxied/", "A rule that never applies because the record is grey-clouded"),
 ("/cloudflare/purge-by-url-silently-does-nothing/", "A cache purge that reports success and clears nothing"),
 ("/cloudflare/", "Cloudflare field notes"),
],
"citations": [CITE_PAGE_RULES, CITE_API,
 ("Cache Rules — Cloudflare docs",
  "https://developers.cloudflare.com/cache/how-to/cache-rules/")],
},

{
"slug": "purge-by-url-silently-does-nothing",
"title": "A Cache Purge That Reports Success and Clears Nothing",
"description": "Single-file purge misses objects cached under a custom cache key or with certain request headers. The API returns success either way.",
"h1": "a cache purge that reports success and clears nothing",
"category": "Cloudflare",
"pill": "Diagnostic",
"chips": ["Cloudflare API", "Python and Node.js", "Cache keys"],
"keywords": ["Cloudflare purge not working", "single file purge", "custom cache key",
             "CF-Cache-Status HIT", "purge by prefix"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "You deployed, you purged the URL, the API returned <code>success: true</code>, and the old version is still being served. Purge by single file matches on the full <em>cache key</em>, not on the URL you typed. If the object was stored under a key that includes a header or a cookie, your purge request describes a different object &mdash; and clearing an object that does not exist is not an error, so the API says it worked.",
"short_answer": """<p>Single-file purge only clears an object whose cache key exactly matches what you sent. A custom cache key that includes headers or cookies, or an object cached with a header like <code>Origin</code> or <code>X-Forwarded-Host</code>, will not be cleared by a plain URL purge from the dashboard.</p>
<p>Send the headers in the API purge request, or fall back to purge by prefix, hostname or tag &mdash; none of which are affected by custom cache keys. Then confirm with <code>CF-Cache-Status</code> rather than trusting the response body.</p>""",
"problem": """<p>The purge API is idempotent by design: asking to remove something that is not there succeeds. That is the right behaviour and it also means a purge that names the wrong key is indistinguishable from one that worked. There is no count of objects removed to compare against.</p>
<p>The second layer is that the object may be cached in more than one place. With tiered cache, a lower tier revalidates against an upper tier, so a partial purge shows up as <code>EXPIRED</code> rather than <code>MISS</code> and the content can still look stale for a moment. And none of this touches the browser's own cache, which is holding whatever <code>Cache-Control</code> you sent it.</p>""",
"why": """<p><strong>The cache key is not the URL.</strong> Even with no Cache Rules at all, Cloudflare's default key includes certain request headers. A Cache Rule that sets a custom key makes the gap explicit, but the gap was always there.</p>
<p><strong>A dashboard purge cannot send headers.</strong> There is nowhere in that form to supply the cookie or header that is part of the key, so for those objects the dashboard is structurally unable to do the job. Only the API can.</p>
<p><strong>A rule that matches only GET does not match a purge.</strong> Purge requests use a different method internally, so a Cache Rule expression like <code>http.request.method eq &quot;GET&quot;</code> will not match during a single-file purge. Adding <code>or http.request.method eq &quot;PURGE&quot;</code> is the documented fix.</p>
<p><strong>Prefix purge has its own edges.</strong> It ignores query strings and fragments &mdash; purging <code>/bar</code> clears <code>/bar?good=bad</code>, but purging <code>/bar?good=bad</code> does not work at all &mdash; and it is limited to 100 prefixes per request and 31 path separators.</p>""",
"steps": [
 {"h": "Confirm the object is actually still cached",
  "body": """<p>Before purging again, check what the edge thinks. <code>CF-Cache-Status</code> is the only honest signal here.</p>
<pre><code class="language-bash">curl -sI https://example.com/app.js | grep -i 'cf-cache-status\\|age\\|cache-control'
# HIT means the edge served a stored copy; MISS means it went to origin</code></pre>"""},
 {"h": "Check whether a Cache Rule sets a custom cache key",
  "body": """<p>If it includes headers, cookies or other request properties, dashboard single-file purge cannot work for those objects. That is the answer, not a symptom to keep investigating.</p>"""},
 {"h": "Purge through the API with the headers included",
  "body": """<p>The API accepts a <code>headers</code> object alongside the URL. Any header that is part of the cache key and is missing from the purge request is treated as an empty value &mdash; which is why an incomplete purge silently misses.</p>
<pre><code class="language-bash">curl -s -X POST -H "Authorization: Bearer $CF_API_TOKEN" \\
  -H "Content-Type: application/json" \\
  "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/purge_cache" \\
  --data '{"files":[{"url":"https://example.com/app.js","headers":{"Origin":"https://example.com"}}]}'</code></pre>"""},
 {"h": "Fall back to a purge type that ignores cache keys",
  "body": """<p>Purge by prefix, by hostname and by tag are all unaffected by custom cache keys. Prefix is usually the pragmatic choice for a deploy; tags are the right answer if you can set <code>Cache-Tag</code> at the origin.</p>"""},
 {"h": "Remember the browser cache is separate",
  "body": """<p>Purging the edge does nothing to a copy already sitting in a visitor's browser under your <code>Cache-Control: max-age</code>. Fingerprinted filenames solve this properly; a purge never will.</p>"""},
],
"verify": """<p>Purge, then request the URL twice. The first request should report <code>MISS</code> (or <code>EXPIRED</code> if tiered cache is on), and the second should report <code>HIT</code> with a small <code>Age</code>:</p>
<pre><code class="language-bash">curl -sI https://example.com/app.js | grep -i 'cf-cache-status'
curl -sI https://example.com/app.js | grep -i 'cf-cache-status\\|^age'</code></pre>
<p>If the first request still says <code>HIT</code> with a large <code>Age</code>, the purge did not reach that object regardless of what the API returned.</p>""",
"code_intro": "The script purges a URL, then re-requests it and reads <code>CF-Cache-Status</code> to decide whether anything actually happened — because the API response cannot tell you. It also inspects the zone's Cache Rules first and warns when a custom cache key or a GET-only expression means single-file purge cannot work, so you skip straight to prefix or tag.",
"py_file": "cloudflare_purge_verify.py",
"py": '''"""Purge a URL and verify from CF-Cache-Status that it actually cleared.

The purge API is idempotent: clearing an object that is not there succeeds. So a
purge that names the wrong cache key is indistinguishable from one that worked,
unless you go and look.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("cloudflare_purge_verify")

API = "https://api.cloudflare.com/client/v4"
# Objects cached with any of these in the key are not cleared by a dashboard
# single-file purge. Documented list, not a guess.
KEY_HEADERS = {"origin", "x-forwarded-host", "x-host", "x-forwarded-scheme",
               "x-original-url", "x-rewrite-url", "forwarded"}


def purge_will_miss(cache_rule):
    """Pure decision function: can single-file purge clear objects under this rule?

    Two documented reasons it cannot: a custom cache key containing headers or
    cookies (the purge request cannot supply them), and an expression that matches
    only GET (purge uses a different method internally).
    """
    reasons = []
    key = cache_rule.get("cache_key", {}) or {}
    custom = key.get("custom_key", {}) or {}
    if custom.get("header") or custom.get("cookie"):
        reasons.append("custom cache key includes headers or cookies -- dashboard "
                       "single-file purge cannot supply them; use the API with "
                       "headers, or purge by prefix/tag")
    expr = cache_rule.get("expression", "")
    if 'http.request.method eq "GET"' in expr and "PURGE" not in expr:
        reasons.append('expression matches only GET -- purge uses a different method; '
                       'add or http.request.method eq "PURGE"')
    return reasons


def interpret(status, age):
    """What CF-Cache-Status means after a purge.

    EXPIRED is not a failure with tiered cache on: the lower tier is revalidating
    against the upper tier.
    """
    s = (status or "").upper()
    if s in ("MISS", "EXPIRED"):
        return True, f"{s} -- purge took effect"
    if s == "HIT":
        return (False, f"HIT with age={age} -- still serving a stored copy; the purge "
                       "did not match this object's cache key")
    if s in ("DYNAMIC", "BYPASS"):
        return True, f"{s} -- this URL is not cached at all"
    return True, f"{s or 'no CF-Cache-Status'} -- nothing to purge here"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zone-id", required=True)
    ap.add_argument("--url", required=True)
    ap.add_argument("--header", action="append", default=[],
                    help="Name:Value that is part of the cache key; repeatable")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    token = os.environ.get("CF_API_TOKEN")
    if not token:
        log.error("set CF_API_TOKEN")
        return 2
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {token}"})

    headers = {}
    for h in args.header:
        name, _, value = h.partition(":")
        headers[name.strip()] = value.strip()
        if name.strip().lower() in KEY_HEADERS:
            log.info("%s is a known cache-key header -- good that you passed it", name.strip())

    if not args.apply:
        log.info("WOULD purge %s with headers=%s -- pass --apply", args.url, headers or "{}")
        return 0

    body = {"files": [{"url": args.url, "headers": headers} if headers else args.url]}
    r = s.post(f"{API}/zones/{args.zone_id}/purge_cache", json=body, timeout=30)
    r.raise_for_status()
    log.info("purge API returned success=%s (this does NOT mean anything was removed)",
             r.json().get("success"))

    probe = requests.get(args.url, headers=headers, timeout=30)
    ok, msg = interpret(probe.headers.get("CF-Cache-Status"), probe.headers.get("Age"))
    (log.info if ok else log.error)(msg)
    if not ok:
        log.error("try purge by prefix, hostname or tag -- none of those are affected "
                  "by custom cache keys")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "cloudflare-purge-verify.mjs",
"js": '''/**
 * Purge a URL and verify from CF-Cache-Status that it actually cleared.
 *
 * The purge API is idempotent: clearing an object that is not there succeeds. So a
 * purge that names the wrong cache key looks exactly like one that worked.
 */
const API = 'https://api.cloudflare.com/client/v4';
// Objects cached with any of these in the key are not cleared by a dashboard
// single-file purge. Documented list, not a guess.
const KEY_HEADERS = new Set(['origin', 'x-forwarded-host', 'x-host',
  'x-forwarded-scheme', 'x-original-url', 'x-rewrite-url', 'forwarded']);

/**
 * Pure decision function: can single-file purge clear objects under this rule?
 * Two documented reasons it cannot -- a custom cache key containing headers or
 * cookies, and an expression matching only GET.
 */
export function purgeWillMiss(cacheRule) {
  const reasons = [];
  const custom = cacheRule.cache_key?.custom_key ?? {};
  if (custom.header || custom.cookie) {
    reasons.push('custom cache key includes headers or cookies -- dashboard single-file '
      + 'purge cannot supply them; use the API with headers, or purge by prefix/tag');
  }
  const expr = cacheRule.expression ?? '';
  if (expr.includes('http.request.method eq "GET"') && !expr.includes('PURGE')) {
    reasons.push('expression matches only GET -- purge uses a different method; '
      + 'add or http.request.method eq "PURGE"');
  }
  return reasons;
}

/** What CF-Cache-Status means after a purge. EXPIRED is fine with tiered cache. */
export function interpret(status, age) {
  const s = (status ?? '').toUpperCase();
  if (s === 'MISS' || s === 'EXPIRED') return [true, `${s} -- purge took effect`];
  if (s === 'HIT') {
    return [false, `HIT with age=${age} -- still serving a stored copy; the purge did `
      + "not match this object's cache key"];
  }
  if (s === 'DYNAMIC' || s === 'BYPASS') return [true, `${s} -- this URL is not cached at all`];
  return [true, `${s || 'no CF-Cache-Status'} -- nothing to purge here`];
}

async function main() {
  const arg = (n) => process.argv[process.argv.indexOf(n) + 1];
  const zone = arg('--zone-id');
  const url = arg('--url');
  const apply = process.argv.includes('--apply');
  const headers = {};
  process.argv.forEach((a, i) => {
    if (a !== '--header') return;
    const [name, ...rest] = process.argv[i + 1].split(':');
    headers[name.trim()] = rest.join(':').trim();
    if (KEY_HEADERS.has(name.trim().toLowerCase())) {
      console.log(`${name.trim()} is a known cache-key header -- good that you passed it`);
    }
  });
  const token = process.env.CF_API_TOKEN;
  if (!token) { console.error('set CF_API_TOKEN'); process.exit(2); }

  if (!apply) {
    console.log(`WOULD purge ${url} with headers=${JSON.stringify(headers)} -- pass --apply`);
    process.exit(0);
  }

  const files = [Object.keys(headers).length ? { url, headers } : url];
  const res = await fetch(`${API}/zones/${zone}/purge_cache`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ files }),
  });
  const { success } = await res.json();
  console.log(`purge API returned success=${success} (this does NOT mean anything was removed)`);

  const probe = await fetch(url, { headers });
  const [ok, msg] = interpret(probe.headers.get('cf-cache-status'), probe.headers.get('age'));
  (ok ? console.log : console.error)(msg);
  if (!ok) {
    console.error('try purge by prefix, hostname or tag -- none are affected by custom cache keys');
  }
  process.exit(ok ? 0 : 1);
}

if (import.meta.url === `file://${process.argv[1]}`) main();
''',
"test_intro": "The subtle case is <code>EXPIRED</code>. With tiered cache it is what a successful purge looks like while the lower tier revalidates, so treating it as a failure would send people chasing a purge that already worked.",
"test_py_file": "test_cloudflare_purge_verify.py",
"test_py": '''from cloudflare_purge_verify import interpret, purge_will_miss


def test_miss_means_the_purge_worked():
    ok, _ = interpret("MISS", None)
    assert ok


def test_expired_is_success_under_tiered_cache():
    """The lower tier is revalidating against the upper tier. Not a failure."""
    ok, _ = interpret("EXPIRED", "3")
    assert ok


def test_hit_with_a_large_age_is_a_failed_purge():
    ok, msg = interpret("HIT", "86400")
    assert not ok and "cache key" in msg


def test_dynamic_is_not_a_failure():
    ok, _ = interpret("DYNAMIC", None)
    assert ok


def test_a_custom_key_with_headers_blocks_single_file_purge():
    rule = {"cache_key": {"custom_key": {"header": {"include": ["Origin"]}}}}
    assert any("custom cache key" in r for r in purge_will_miss(rule))


def test_a_get_only_expression_is_flagged():
    rule = {"expression": 'http.request.method eq "GET"'}
    assert any("only GET" in r for r in purge_will_miss(rule))


def test_an_expression_that_allows_purge_is_not_flagged():
    rule = {"expression": '(http.request.method eq "GET" or http.request.method eq "PURGE")'}
    assert purge_will_miss(rule) == []


def test_a_plain_rule_is_clean():
    assert purge_will_miss({"expression": 'http.host eq "example.com"'}) == []
''',
"test_js_file": "cloudflare-purge-verify.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { interpret, purgeWillMiss } from './cloudflare-purge-verify.mjs';

test('MISS means the purge worked', () => {
  assert.equal(interpret('MISS', null)[0], true);
});

test('EXPIRED is success under tiered cache', () => {
  assert.equal(interpret('EXPIRED', '3')[0], true);
});

test('HIT with a large age is a failed purge', () => {
  const [ok, msg] = interpret('HIT', '86400');
  assert.equal(ok, false);
  assert.ok(msg.includes('cache key'));
});

test('a custom key with headers blocks single-file purge', () => {
  const rule = { cache_key: { custom_key: { header: { include: ['Origin'] } } } };
  assert.ok(purgeWillMiss(rule).some((r) => r.includes('custom cache key')));
});

test('an expression that allows PURGE is not flagged', () => {
  const rule = { expression: '(http.request.method eq "GET" or http.request.method eq "PURGE")' };
  assert.deepEqual(purgeWillMiss(rule), []);
});
''',
"faq": [
 ("Why does Cloudflare purge return success but not clear anything?",
  "The purge API is idempotent — asking to remove an object that is not there succeeds. If your purge names a cache key that does not exist, the response is identical to a purge that worked. Check CF-Cache-Status instead of the response body."),
 ("What is a custom cache key and why does it break purging?",
  "A Cache Rule can index cached objects by more than the URL — headers, cookies, other request properties. A dashboard purge form has nowhere to supply those, so for such objects it structurally cannot work. Use the API with a headers object, or purge by prefix, hostname or tag."),
 ("Can I purge a URL with a query string by prefix?",
  "No. Prefix purge ignores query strings and fragments. Purging /bar clears /bar?good=bad, but purging /bar?good=bad directly does not work. Prefix purge is also limited to 100 prefixes per request and 31 path separators."),
 ("Why do I see EXPIRED instead of MISS after purging?",
  "That is tiered cache working normally: the lower tier is revalidating against the upper tier to reduce load on it. Depending on which tier the request reaches, either EXPIRED or MISS is correct, and both mean the purge took effect."),
 ("The edge is clear but visitors still see the old file. Why?",
  "Their browser cached it under the Cache-Control max-age you sent. Purging Cloudflare does not reach into a browser cache. Fingerprinted filenames are the real fix; a purge never will be."),
],
"related": [
 ("/cloudflare/only-one-page-rule-applies/", "Only one Page Rule applies, and it is the one at the top"),
 ("/cloudflare/too-many-redirects-flexible-ssl/", "ERR_TOO_MANY_REDIRECTS is almost always Flexible SSL"),
 ("/cloudflare/", "Cloudflare field notes"),
],
"citations": [CITE_PURGE_SINGLE, CITE_PURGE_PREFIX, CITE_CACHE_RULES, CITE_CACHE_KEYS,
              CITE_STATUS, CITE_API],
},

]
