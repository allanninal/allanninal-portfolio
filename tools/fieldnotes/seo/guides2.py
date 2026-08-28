#!/usr/bin/env python3
"""Technical SEO field notes, second half. Separate file for the same reason as
everywhere else: editing a large Python literal in place is how these get broken."""

CITE_CANONICAL = ("Consolidate duplicate URLs with canonicals — Google Search Central",
                  "https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls")
CITE_CANONICAL_TROUBLE = ("Canonicalization troubleshooting — Google Search Central",
                          "https://developers.google.com/search/docs/crawling-indexing/canonicalization")
CITE_SOFT404 = ("Soft 404 errors — Google Search Console Help",
                "https://support.google.com/webmasters/answer/181708")
CITE_HTTP_STATUS = ("How HTTP status codes affect Google Search — Google Search Central",
                    "https://developers.google.com/search/docs/crawling-indexing/http-network-errors")
CITE_INDEXING_REPORT = ("Page indexing report — Google Search Console Help",
                        "https://support.google.com/webmasters/answer/7440203")
CITE_REMOVALS = ("Removals tool — Google Search Console Help",
                 "https://support.google.com/webmasters/answer/9689846")

GUIDES2 = [

{
"slug": "canonical-points-at-staging-or-a-redirect",
"title": "A Canonical Tag Pointing at Staging, a Redirect or Nothing",
"description": "Canonicals are generated from a base URL. When that base is wrong, every page on the site quietly nominates the wrong URL.",
"h1": "a canonical tag pointing at staging, a redirect or nothing",
"category": "Technical SEO",
"pill": "Repair",
"chips": ["No API key needed", "Python and Node.js", "Rewrites your HTML"],
"keywords": ["canonical tag wrong", "canonical points to staging", "duplicate canonical",
             "alternate page with proper canonical tag", "rel canonical"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Search Console says <em>Alternate page with proper canonical tag</em> for pages you very much want indexed, or your live pages are nominating a staging host nobody can reach. Canonical tags are almost always generated from a single base URL, so when that base is wrong the whole site is wrong at once &mdash; and the page looks completely normal in a browser, because a canonical is invisible.",
"short_answer": """<p>Check three things on every page: that the canonical exists, that there is <strong>exactly one</strong> of them, and that it points at a URL on the live origin that returns <code>200</code>.</p>
<p>Two canonicals on a page is the worst case &mdash; Google ignores all of them, so the tag you added does nothing at all. That usually means a layout and a page template are both emitting one.</p>""",
"problem": """<p>The failure is invisible from the browser and uniform across the site, which is a bad combination. Nothing looks broken, every page is affected equally, and the only symptom is a Search Console category most people read as informational.</p>
<p>The usual causes are environment configuration: a build-time base URL that was not set in CI, a <code>.env</code> that defaults to <code>localhost</code>, or a staging host that was copied to production. A close second is a path variable being concatenated onto a base that already contains it, producing a canonical with the path twice.</p>""",
"why": """<p><strong>A canonical is a hint, not a directive.</strong> Google may pick a different URL if your signals conflict, so a wrong canonical does not always produce an obvious error &mdash; sometimes it just quietly loses you the page you wanted ranked.</p>
<p><strong>Multiple canonicals cancel.</strong> If a page has more than one <code>rel="canonical"</code>, Google ignores all of them and works it out from other signals. Adding a second one to be safe is strictly worse than having one.</p>
<p><strong>A canonical to a redirect or a 404 is a contradiction.</strong> You are nominating a URL that the server says is not the right one, or does not exist. Chains behave the same way: point at the final destination.</p>
<p><strong>Origin and path get conflated in configuration.</strong> One variable holds the scheme and host; another holds the path prefix. Combining them in the wrong order, or using the one that already includes the path, produces a doubled path &mdash; and it is consistent across every page, which makes it look deliberate.</p>""",
"steps": [
 {"h": "Audit the built HTML, not the templates",
  "body": """<p>Templates look right. The build is where the base URL is substituted, so the audit has to run against the output or the live site. This is the same reason a source review keeps missing it.</p>"""},
 {"h": "Count the canonicals per page",
  "body": """<p>Zero and two are both failures, and two is worse than zero. The script reports the count first because it changes what the other checks mean.</p>"""},
 {"h": "Resolve each canonical target",
  "body": """<p>It must be absolute, on your live origin, and return <code>200</code> without redirecting. A relative canonical is legal but resolves against the page's own URL, which produces surprises on paginated or parameterised URLs.</p>"""},
 {"h": "Repair the origin, in place",
  "body": """<p>Because the base URL is the usual culprit, the fix is a mechanical origin swap across the built files. The script does that with <code>--apply</code>, replacing only the scheme-and-host portion &mdash; never the path, which is how a greedy rewrite turns a URL into a bare origin.</p>"""},
 {"h": "Fix the build variable so it does not come back",
  "body": """<p>The rewrite fixes this deploy. Set the base URL in the build environment, or the next build reproduces it exactly.</p>"""},
],
"verify": """<p>Ask the live page what it claims:</p>
<pre><code class="language-bash">curl -s https://example.com/some-page/ | grep -c 'rel="canonical"'   # must be 1
curl -s https://example.com/some-page/ | grep -o 'rel="canonical" href="[^"]*"'
curl -sIL "$(curl -s https://example.com/some-page/ | sed -n 's/.*rel="canonical" href="\\([^"]*\\)".*/\\1/p')" | head -1</code></pre>
<p>Then use URL Inspection in Search Console, which reports the canonical you declared and the canonical Google chose as two separate lines. When they differ, that gap is the finding.</p>""",
"code_intro": "The script reads local built HTML files or live URLs, counts canonicals, resolves each target, and classifies the result. With <code>--apply</code> and <code>--live-origin</code> it rewrites the origin portion of every canonical in place. The origin swap is deliberately narrow — it matches scheme and host only, because a greedy rewrite is how you turn a good URL into a bare origin.",
"py_file": "canonical_audit.py",
"py": '''"""Audit and repair rel=canonical tags in built HTML.

Canonicals are generated from one base URL, so when the base is wrong every page is
wrong at once -- and the page looks entirely normal in a browser, because a canonical
is invisible.
"""
import argparse
import logging
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("canonical_audit")

CANON = re.compile(r'<link[^>]+rel=["\\']canonical["\\'][^>]*>', re.I)
HREF = re.compile(r'href=["\\']([^"\\']+)["\\']', re.I)


def classify(canonicals, page_url, live_origin):
    """Pure decision function over the canonical tags found on one page.

    canonicals: list of href strings, in document order.
    Returns a list of problems; empty means the page is fine.
    """
    problems = []
    if not canonicals:
        return ["no canonical tag"]
    if len(canonicals) > 1:
        # Worse than none: Google ignores all of them when there is more than one.
        problems.append(f"{len(canonicals)} canonical tags -- Google ignores all of them")
    href = canonicals[0]
    if not href.startswith(("http://", "https://")):
        problems.append(f"relative canonical {href!r} -- resolves against the page URL, "
                        "which surprises on parameterised URLs")
        return problems
    parts = urlsplit(href)
    origin = urlunsplit((parts.scheme, parts.netloc, "", "", ""))
    if live_origin and origin != live_origin.rstrip("/"):
        problems.append(f"origin {origin} is not the live origin {live_origin}")
    if parts.scheme == "http":
        problems.append("canonical uses http; it should match the served scheme")
    # A path repeated back to back is the classic base-plus-prefix concatenation bug.
    segs = [s for s in parts.path.split("/") if s]
    for i in range(len(segs) - 1):
        if segs[i] and segs[i] == segs[i + 1]:
            problems.append(f"path segment {segs[i]!r} appears twice -- a base URL and a "
                            "path prefix were probably concatenated")
            break
    if page_url and href.rstrip("/") != page_url.rstrip("/") and not problems:
        problems.append(f"canonical {href} differs from the page URL {page_url}; "
                        "correct for a duplicate, wrong for a page you want indexed")
    return problems


def swap_origin(html, old_origin, new_origin):
    """Replace only the scheme-and-host portion of canonical hrefs.

    Narrow on purpose. A greedy origin rewrite is how a good URL becomes a bare
    origin and a sitemap reference becomes nonsense.
    """
    def fix(m):
        return m.group(0).replace(old_origin.rstrip("/"), new_origin.rstrip("/"))
    return CANON.sub(fix, html)


def hrefs_in(html):
    return [HREF.search(tag).group(1) for tag in CANON.findall(html) if HREF.search(tag)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True, help="directory of built HTML")
    ap.add_argument("--live-origin", help="https://example.com")
    ap.add_argument("--from-origin", help="origin to replace when using --apply")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    files = sorted(Path(args.dir).rglob("*.html"))
    log.info("%d file(s)", len(files))
    bad = 0
    for f in files:
        html = f.read_text(encoding="utf-8", errors="replace")
        found = hrefs_in(html)
        problems = classify(found, None, args.live_origin)
        if problems:
            bad += 1
            log.warning("%s -- %s", f, "; ".join(problems))
        if args.apply and args.from_origin and args.live_origin:
            fixed = swap_origin(html, args.from_origin, args.live_origin)
            if fixed != html:
                f.write_text(fixed, encoding="utf-8")
                log.info("rewrote canonical origin in %s", f)
    if not args.apply and args.from_origin:
        log.info("WOULD rewrite origins -- pass --apply")
    log.info("%d file(s) with problems", bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "canonical-audit.mjs",
"js": '''/**
 * Audit and repair rel=canonical tags in built HTML.
 *
 * Canonicals are generated from one base URL, so when the base is wrong every page
 * is wrong at once -- and looks entirely normal in a browser.
 */
import { readdirSync, readFileSync, writeFileSync, statSync } from 'node:fs';
import { join } from 'node:path';

const CANON = /<link[^>]+rel=["']canonical["'][^>]*>/gi;
const HREF = /href=["']([^"']+)["']/i;

/**
 * Pure decision function over the canonical tags found on one page.
 * Returns a list of problems; empty means fine.
 */
export function classify(canonicals, pageUrl, liveOrigin) {
  const problems = [];
  if (!canonicals.length) return ['no canonical tag'];
  if (canonicals.length > 1) {
    // Worse than none: Google ignores all of them when there is more than one.
    problems.push(`${canonicals.length} canonical tags -- Google ignores all of them`);
  }
  const href = canonicals[0];
  if (!/^https?:\\/\\//.test(href)) {
    problems.push(`relative canonical "${href}" -- resolves against the page URL, `
      + 'which surprises on parameterised URLs');
    return problems;
  }
  const u = new URL(href);
  const origin = `${u.protocol}//${u.host}`;
  if (liveOrigin && origin !== liveOrigin.replace(/\\/$/, '')) {
    problems.push(`origin ${origin} is not the live origin ${liveOrigin}`);
  }
  if (u.protocol === 'http:') problems.push('canonical uses http; it should match the served scheme');
  const segs = u.pathname.split('/').filter(Boolean);
  for (let i = 0; i < segs.length - 1; i += 1) {
    if (segs[i] && segs[i] === segs[i + 1]) {
      problems.push(`path segment "${segs[i]}" appears twice -- a base URL and a path `
        + 'prefix were probably concatenated');
      break;
    }
  }
  if (pageUrl && href.replace(/\\/$/, '') !== pageUrl.replace(/\\/$/, '') && !problems.length) {
    problems.push(`canonical ${href} differs from the page URL ${pageUrl}; `
      + 'correct for a duplicate, wrong for a page you want indexed');
  }
  return problems;
}

/**
 * Replace only the scheme-and-host portion of canonical hrefs. Narrow on purpose:
 * a greedy origin rewrite is how a good URL becomes a bare origin.
 */
export function swapOrigin(html, oldOrigin, newOrigin) {
  return html.replace(CANON, (tag) =>
    tag.replaceAll(oldOrigin.replace(/\\/$/, ''), newOrigin.replace(/\\/$/, '')));
}

export const hrefsIn = (html) =>
  (html.match(CANON) ?? []).map((t) => t.match(HREF)?.[1]).filter(Boolean);

const walk = (dir) => readdirSync(dir).flatMap((n) => {
  const p = join(dir, n);
  return statSync(p).isDirectory() ? walk(p) : (p.endsWith('.html') ? [p] : []);
});

async function main() {
  const arg = (n) => process.argv[process.argv.indexOf(n) + 1];
  const dir = arg('--dir');
  const liveOrigin = process.argv.includes('--live-origin') ? arg('--live-origin') : null;
  const fromOrigin = process.argv.includes('--from-origin') ? arg('--from-origin') : null;
  const apply = process.argv.includes('--apply');

  const files = walk(dir).sort();
  console.log(`${files.length} file(s)`);
  let bad = 0;
  for (const f of files) {
    const html = readFileSync(f, 'utf8');
    const problems = classify(hrefsIn(html), null, liveOrigin);
    if (problems.length) { bad += 1; console.warn(`${f} -- ${problems.join('; ')}`); }
    if (apply && fromOrigin && liveOrigin) {
      const fixed = swapOrigin(html, fromOrigin, liveOrigin);
      if (fixed !== html) { writeFileSync(f, fixed); console.log(`rewrote canonical origin in ${f}`); }
    }
  }
  if (!apply && fromOrigin) console.log('WOULD rewrite origins -- pass --apply');
  console.log(`${bad} file(s) with problems`);
  process.exit(bad ? 1 : 0);
}

if (import.meta.url === `file://${process.argv[1]}`) main();
''',
"test_intro": "The origin swap is the test that matters. It must change the host and leave the path alone — the failure mode is a greedy replace that eats the path and leaves every page canonicalising to the homepage, which is far worse than the bug it was fixing.",
"test_py_file": "test_canonical_audit.py",
"test_py": '''from canonical_audit import classify, hrefs_in, swap_origin

LIVE = "https://example.com"
TAG = '<link rel="canonical" href="{}">'


def test_a_single_correct_canonical_is_clean():
    assert classify(["https://example.com/a/"], None, LIVE) == []


def test_no_canonical_is_reported():
    assert classify([], None, LIVE) == ["no canonical tag"]


def test_two_canonicals_are_worse_than_none():
    """Google ignores all of them when there is more than one."""
    p = classify(["https://example.com/a/", "https://example.com/b/"], None, LIVE)
    assert any("ignores all of them" in x for x in p)


def test_a_staging_origin_is_reported():
    p = classify(["https://staging.example.net/a/"], None, LIVE)
    assert any("is not the live origin" in x for x in p)


def test_a_doubled_path_segment_is_reported():
    p = classify(["https://example.com/blog/blog/post/"], None, LIVE)
    assert any("appears twice" in x for x in p)


def test_a_relative_canonical_is_reported():
    p = classify(["/a/"], None, LIVE)
    assert any("relative canonical" in x for x in p)


def test_swap_origin_changes_the_host_and_keeps_the_path():
    """The failure mode is a greedy replace that eats the path."""
    html = TAG.format("http://localhost:4321/blog/post/")
    out = swap_origin(html, "http://localhost:4321", LIVE)
    assert out == TAG.format("https://example.com/blog/post/")


def test_swap_origin_leaves_other_links_alone():
    html = ('<a href="http://localhost:4321/x">x</a>'
            + TAG.format("http://localhost:4321/y"))
    out = swap_origin(html, "http://localhost:4321", LIVE)
    assert 'href="http://localhost:4321/x"' in out
    assert 'href="https://example.com/y"' in out


def test_hrefs_in_finds_the_tag():
    assert hrefs_in(TAG.format("https://example.com/a/")) == ["https://example.com/a/"]
''',
"test_js_file": "canonical-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { classify, hrefsIn, swapOrigin } from './canonical-audit.mjs';

const LIVE = 'https://example.com';
const tag = (h) => `<link rel="canonical" href="${h}">`;

test('a single correct canonical is clean', () => {
  assert.deepEqual(classify(['https://example.com/a/'], null, LIVE), []);
});

test('no canonical is reported', () => {
  assert.deepEqual(classify([], null, LIVE), ['no canonical tag']);
});

test('two canonicals are worse than none', () => {
  const p = classify(['https://example.com/a/', 'https://example.com/b/'], null, LIVE);
  assert.ok(p.some((x) => x.includes('ignores all of them')));
});

test('a doubled path segment is reported', () => {
  const p = classify(['https://example.com/blog/blog/post/'], null, LIVE);
  assert.ok(p.some((x) => x.includes('appears twice')));
});

test('swapOrigin changes the host and keeps the path', () => {
  const out = swapOrigin(tag('http://localhost:4321/blog/post/'), 'http://localhost:4321', LIVE);
  assert.equal(out, tag('https://example.com/blog/post/'));
});

test('swapOrigin leaves other links alone', () => {
  const html = `<a href="http://localhost:4321/x">x</a>${tag('http://localhost:4321/y')}`;
  const out = swapOrigin(html, 'http://localhost:4321', LIVE);
  assert.ok(out.includes('href="http://localhost:4321/x"'));
  assert.ok(out.includes('href="https://example.com/y"'));
});

test('hrefsIn finds the tag', () => {
  assert.deepEqual(hrefsIn(tag('https://example.com/a/')), ['https://example.com/a/']);
});
''',
"faq": [
 ("What does 'Alternate page with proper canonical tag' mean?",
  "Google found the page, read its canonical, and is indexing the nominated URL instead. That is correct for a genuine duplicate and a problem when the page is one you wanted indexed on its own."),
 ("Can a page have two canonical tags?",
  "It can, and it should not. When Google finds more than one rel=canonical it ignores all of them and decides from other signals. Adding a second one to be safe is strictly worse than having one."),
 ("Is a canonical a directive?",
  "No, it is a hint. Google can pick a different URL when your signals conflict, which is why a wrong canonical does not always surface as an obvious error — sometimes it just quietly loses you the page."),
 ("Why do all my canonicals point at localhost or staging?",
  "The base URL was not set in the build environment, so the default was used. Every page is affected identically, which makes it look deliberate. Fix the build variable, not just this deploy's output."),
 ("Should a canonical point at a redirecting URL?",
  "No. You would be nominating a URL the server says is not the right one. Point at the final destination, and treat a canonical to a 404 as the same class of contradiction."),
],
"related": [
 ("/seo/sitemap-lists-urls-that-must-not-be-indexed/", "A sitemap listing URLs that redirect, 404 or say noindex"),
 ("/seo/soft-404-returns-200/", "A missing page that returns 200"),
 ("/seo/", "Technical SEO field notes"),
],
"citations": [CITE_CANONICAL, CITE_CANONICAL_TROUBLE, CITE_INDEXING_REPORT],
},

{
"slug": "soft-404-returns-200",
"title": "A Missing Page That Returns 200 Instead of 404",
"description": "Client-side routing and catch-all handlers answer every URL with 200. Google calls it a soft 404 and it fills the index with nothing.",
"h1": "a missing page that returns 200 instead of 404",
"category": "Technical SEO",
"pill": "Diagnostic",
"chips": ["No API key needed", "Python and Node.js", "Probes real URLs"],
"keywords": ["soft 404", "returns 200 instead of 404", "SPA 404 status code",
             "catch-all route indexing", "404 vs 410"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Search Console is reporting <em>Soft 404</em> on pages that look fine, or your index count is far higher than the number of pages you actually have. Somewhere a catch-all is answering every request with <code>200 OK</code> and a page that says &ldquo;not found&rdquo; in the body. To a crawler that is a real page with thin content, so it gets crawled, judged and sometimes indexed.",
"short_answer": """<p>Request a URL that certainly does not exist and read the status line. If it is <code>200</code>, your not-found page is lying to crawlers.</p>
<p>Serve a real <code>404</code>, or <code>410</code> for something you deliberately removed. Both are correct; <code>410</code> signals permanence and tends to be dropped a little faster. What matters is that the status line and the page content agree.</p>""",
"problem": """<p>It looks right to a person. The page says the thing was not found, so nobody thinks to check the status code &mdash; and browsers do not show it. Only a crawler, or a <code>curl -I</code>, notices the disagreement.</p>
<p>The cost is real: crawl budget spent on URLs that do not exist, thin pages competing with your actual content, and an index count that stops meaning anything. On a large site with a parameterised catch-all, the set of fake URLs is effectively unbounded.</p>""",
"why": """<p><strong>Client-side routing decides after the response.</strong> The server sends <code>200</code> and the shell, and JavaScript works out later that the route is unknown. The status code was already committed before anyone knew the page did not exist.</p>
<p><strong>Catch-all rules are written for the happy path.</strong> A rewrite that sends everything to <code>index.html</code> is what makes deep links work on a static host. The same rule sends every typo there too.</p>
<p><strong>Redirecting to the homepage is the same bug wearing a hat.</strong> A missing page that <code>302</code>s to <code>/</code> also reports success for something that does not exist, and Google treats it as a soft 404 too. It is a common well-meant fix that makes the problem harder to see.</p>
<p><strong>An empty page is also a soft 404.</strong> A category with no products, a search with no results, a profile that was emptied &mdash; these return <code>200</code> honestly and still have nothing on them. The classification is about substance, not just status.</p>""",
"steps": [
 {"h": "Probe a URL that cannot exist",
  "body": """<p>Add a random segment to a real path. The status line is the whole answer.</p>
<pre><code class="language-bash">curl -sI https://example.com/definitely-not-a-real-page-9f3a | head -1
# HTTP/2 404   <- correct
# HTTP/2 200   <- soft 404</code></pre>"""},
 {"h": "Probe several shapes, not one",
  "body": """<p>A missing top-level path, a missing path under a real section, and a missing item with a real-looking ID often go through different handlers. Sites commonly get one right and two wrong.</p>"""},
 {"h": "Fix the status at the layer that owns the route",
  "body": """<p>For server-rendered apps, return the status from the route handler. For static hosts, configure a 404 document rather than a catch-all rewrite to the index. For client-side routing, prerender or serve a real 404 for unknown paths &mdash; JavaScript cannot change a status code that has already been sent.</p>"""},
 {"h": "Use 410 for things you removed on purpose",
  "body": """<p><code>404</code> means &ldquo;not here&rdquo;; <code>410</code> means &ldquo;gone, do not come back&rdquo;. Both work, and <code>410</code> tends to be dropped from the index slightly faster.</p>"""},
 {"h": "Do not redirect missing pages to the homepage",
  "body": """<p>It reports success for something that does not exist, and it wastes the visitor's time too &mdash; they wanted a specific thing and got a front page with no explanation.</p>"""},
],
"verify": """<p>Re-probe and check both the status and the body:</p>
<pre><code class="language-bash">curl -si https://example.com/definitely-not-a-real-page-9f3a | head -1
curl -s  https://example.com/definitely-not-a-real-page-9f3a | grep -io 'not found' | head -1</code></pre>
<p>A correct not-found page returns <code>404</code> <em>and</em> says so. Then use URL Inspection on a URL Search Console flagged, and confirm it now reports the 404.</p>""",
"code_intro": "The script probes each path you give it plus a generated nonsense URL under each, and classifies the response by status, redirect behaviour and body length together. The classification is a pure function, because the interesting cases — a 200 with not-found text, a redirect to the homepage, a 200 with almost no content — are judgement calls that deserve to be visible and tested rather than buried in a request loop.",
"py_file": "soft_404_probe.py",
"py": '''"""Find URLs that report success for a page that does not exist.

Browsers do not show status codes, so a not-found page that returns 200 looks
correct to everyone except a crawler. Google calls it a soft 404.
"""
import argparse
import logging
import re
import sys
from urllib.parse import urlsplit

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("soft_404_probe")

NOT_FOUND_TEXT = re.compile(
    r"\\b(not found|doesn.t exist|does not exist|no longer available|page missing|404)\\b", re.I)
THIN_BYTES = 2_000  # visible text below this is thin enough to be worth reporting


def classify(status, final_path, requested_path, visible_text):
    """Pure decision function for one probe.

    Returns (is_problem, message). The judgement calls live here on purpose: a 200
    carrying not-found text and a redirect to the homepage are both soft 404s, and
    both look like success from a request loop.
    """
    said_missing = bool(NOT_FOUND_TEXT.search(visible_text[:4000]))
    if status in (404, 410):
        return False, f"{status} -- correct"
    if status >= 500:
        return True, f"{status} -- server error, not a 404; crawlers retry these"
    if 300 <= status < 400 or final_path != requested_path:
        if final_path in ("/", "", "/index.html"):
            return True, (f"redirects to the homepage -- a soft 404. Return 404 or 410 "
                          "so the crawler knows the URL is dead.")
        return True, f"redirects to {final_path} -- reports success for a missing page"
    if status == 200 and said_missing:
        return True, ("200 with not-found text -- a soft 404. The status line and the "
                      "page content disagree.")
    if status == 200 and len(visible_text.strip()) < THIN_BYTES:
        return True, (f"200 with {len(visible_text.strip())} bytes of text -- thin enough "
                      "that Google may treat it as a soft 404")
    return False, f"{status} -- looks like a real page"


def visible(html):
    """Crude text extraction. Good enough to tell 'empty' from 'has content'."""
    body = re.sub(r"(?is)<(script|style|template)[^>]*>.*?</\\1>", " ", html)
    return re.sub(r"\\s+", " ", re.sub(r"(?s)<[^>]+>", " ", body))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", nargs="+", required=True,
                    help="real section URLs; a nonsense child is probed under each")
    ap.add_argument("--nonce", default="zz-not-a-real-page-9f3a",
                    help="segment appended to build a URL that cannot exist")
    args = ap.parse_args()

    s = requests.Session()
    s.headers.update({"User-Agent": "soft-404-probe/1.0"})

    problems = 0
    for base in args.url:
        probe = base.rstrip("/") + "/" + args.nonce
        try:
            r = s.get(probe, timeout=30, allow_redirects=True)
        except requests.RequestException as e:
            log.error("%s -- request failed: %s", probe, e.__class__.__name__)
            problems += 1
            continue
        status = r.history[0].status_code if r.history else r.status_code
        bad, msg = classify(status, urlsplit(r.url).path,
                            urlsplit(probe).path, visible(r.text))
        (log.error if bad else log.info)("%s -- %s", probe, msg)
        problems += bool(bad)
    log.info("%d problem(s)", problems)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "soft-404-probe.mjs",
"js": '''/**
 * Find URLs that report success for a page that does not exist.
 *
 * Browsers do not show status codes, so a not-found page returning 200 looks correct
 * to everyone except a crawler. Google calls it a soft 404.
 */
const NOT_FOUND_TEXT =
  /\\b(not found|doesn.t exist|does not exist|no longer available|page missing|404)\\b/i;
const THIN_BYTES = 2000;

/**
 * Pure decision function for one probe. Returns [isProblem, message].
 * The judgement calls live here: a 200 carrying not-found text and a redirect to the
 * homepage are both soft 404s, and both look like success from a request loop.
 */
export function classify(status, finalPath, requestedPath, visibleText) {
  const saidMissing = NOT_FOUND_TEXT.test(visibleText.slice(0, 4000));
  if (status === 404 || status === 410) return [false, `${status} -- correct`];
  if (status >= 500) return [true, `${status} -- server error, not a 404; crawlers retry these`];
  if ((status >= 300 && status < 400) || finalPath !== requestedPath) {
    if (['/', '', '/index.html'].includes(finalPath)) {
      return [true, 'redirects to the homepage -- a soft 404. Return 404 or 410 so the '
        + 'crawler knows the URL is dead.'];
    }
    return [true, `redirects to ${finalPath} -- reports success for a missing page`];
  }
  if (status === 200 && saidMissing) {
    return [true, '200 with not-found text -- a soft 404. The status line and the page '
      + 'content disagree.'];
  }
  if (status === 200 && visibleText.trim().length < THIN_BYTES) {
    return [true, `200 with ${visibleText.trim().length} bytes of text -- thin enough that `
      + 'Google may treat it as a soft 404'];
  }
  return [false, `${status} -- looks like a real page`];
}

/** Crude text extraction. Good enough to tell 'empty' from 'has content'. */
export const visible = (html) => html
  .replace(/<(script|style|template)[^>]*>[\\s\\S]*?<\\/\\1>/gi, ' ')
  .replace(/<[^>]+>/g, ' ')
  .replace(/\\s+/g, ' ');

async function main() {
  const ui = process.argv.indexOf('--url');
  const bases = process.argv.slice(ui + 1).filter((a) => !a.startsWith('--'));
  const nonce = process.argv.includes('--nonce')
    ? process.argv[process.argv.indexOf('--nonce') + 1] : 'zz-not-a-real-page-9f3a';

  let problems = 0;
  for (const base of bases) {
    const probe = `${base.replace(/\\/$/, '')}/${nonce}`;
    let r;
    try { r = await fetch(probe, { redirect: 'follow' }); }
    catch (e) { console.error(`${probe} -- request failed: ${e.name}`); problems += 1; continue; }
    const text = visible(await r.text());
    const status = r.redirected ? 302 : r.status;
    const [bad, msg] = classify(status, new URL(r.url).pathname, new URL(probe).pathname, text);
    (bad ? console.error : console.log)(`${probe} -- ${msg}`);
    if (bad) problems += 1;
  }
  console.log(`${problems} problem(s)`);
  process.exit(problems ? 1 : 0);
}

if (import.meta.url === `file://${process.argv[1]}`) main();
''',
"test_intro": "The tests hold the line on what counts as correct. A real 404 with a short body is fine — a not-found page is supposed to be short — so the thin-content rule must not fire on it, or the check reports every well-behaved site as broken.",
"test_py_file": "test_soft_404_probe.py",
"test_py": '''from soft_404_probe import classify, visible

LONG = "real content " * 400


def test_a_real_404_is_correct():
    bad, msg = classify(404, "/missing", "/missing", "Not found")
    assert not bad and "correct" in msg


def test_a_410_is_correct():
    assert not classify(410, "/gone", "/gone", "Gone")[0]


def test_a_short_404_body_is_not_flagged_as_thin():
    """A not-found page is supposed to be short. Flagging it reports every good site."""
    assert not classify(404, "/missing", "/missing", "Not found")[0]


def test_200_with_not_found_text_is_a_soft_404():
    bad, msg = classify(200, "/missing", "/missing", "Sorry, page not found. " + LONG)
    assert bad and "soft 404" in msg


def test_a_redirect_to_the_homepage_is_a_soft_404():
    bad, msg = classify(302, "/", "/missing", LONG)
    assert bad and "homepage" in msg


def test_a_thin_200_is_reported():
    bad, msg = classify(200, "/empty", "/empty", "   ")
    assert bad and "thin" in msg


def test_a_real_page_passes():
    assert not classify(200, "/real", "/real", LONG)[0]


def test_a_500_is_not_treated_as_a_404():
    bad, msg = classify(500, "/x", "/x", "")
    assert bad and "server error" in msg


def test_visible_strips_scripts():
    assert "alert" not in visible("<script>alert(1)</script><p>hi</p>")
''',
"test_js_file": "soft-404-probe.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { classify, visible } from './soft-404-probe.mjs';

const LONG = 'real content '.repeat(400);

test('a real 404 is correct', () => {
  const [bad, msg] = classify(404, '/missing', '/missing', 'Not found');
  assert.equal(bad, false);
  assert.ok(msg.includes('correct'));
});

test('a short 404 body is not flagged as thin', () => {
  assert.equal(classify(404, '/missing', '/missing', 'Not found')[0], false);
});

test('200 with not-found text is a soft 404', () => {
  const [bad, msg] = classify(200, '/missing', '/missing', `Sorry, page not found. ${LONG}`);
  assert.equal(bad, true);
  assert.ok(msg.includes('soft 404'));
});

test('a redirect to the homepage is a soft 404', () => {
  const [bad, msg] = classify(302, '/', '/missing', LONG);
  assert.equal(bad, true);
  assert.ok(msg.includes('homepage'));
});

test('a real page passes', () => {
  assert.equal(classify(200, '/real', '/real', LONG)[0], false);
});

test('visible strips scripts', () => {
  assert.ok(!visible('<script>alert(1)</script><p>hi</p>').includes('alert'));
});
''',
"faq": [
 ("What is a soft 404?",
  "A URL that returns 200 OK for a page that does not exist, or that has effectively no content. To a crawler it is a real page with thin content, so it gets crawled, assessed and sometimes indexed."),
 ("Why does my SPA return 200 for missing routes?",
  "The server sends the shell before anything knows the route is unknown, and JavaScript decides afterwards. A status code cannot be changed once it has been sent — the fix has to happen at the server or host layer."),
 ("Should I use 404 or 410?",
  "Both are correct. 404 means not here; 410 means gone and not coming back. Use 410 for something you deliberately removed — it tends to be dropped from the index slightly faster."),
 ("Is redirecting missing pages to the homepage a good fix?",
  "No. It is the same problem in a different form: you are reporting success for a URL that does not exist, and Google treats it as a soft 404. It also wastes the visitor's time."),
 ("Can a page that returns 200 honestly still be a soft 404?",
  "Yes. An empty category, a search with no results, or a profile with nothing on it all return 200 truthfully and still have nothing to show. The classification is about substance, not just the status line."),
 ("Does this waste crawl budget?",
  "Yes, and unboundedly on a site with a parameterised catch-all — every typo becomes a crawlable URL. That is the practical reason to fix it even if nothing is being indexed."),
],
"related": [
 ("/seo/sitemap-lists-urls-that-must-not-be-indexed/", "A sitemap listing URLs that redirect, 404 or say noindex"),
 ("/seo/canonical-points-at-staging-or-a-redirect/", "A canonical pointing at staging or a redirect"),
 ("/seo/robots-txt-blocks-the-noindex-you-added/", "robots.txt blocking the noindex it was meant to enforce"),
],
"citations": [CITE_SOFT404, CITE_HTTP_STATUS, CITE_INDEXING_REPORT, CITE_REMOVALS],
},

]
