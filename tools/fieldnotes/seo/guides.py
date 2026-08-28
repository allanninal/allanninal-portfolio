#!/usr/bin/env python3
"""Technical SEO field notes, first half.

Inclusion test is the same as every other section: the problem must be one a script
can DETECT and, wherever the artifact is a file you own, REPAIR. The sitemap and your
built HTML are yours, so those repairs are real.
"""

CITE_SITEMAP = ("Build and submit a sitemap — Google Search Central",
                "https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap")
CITE_SITEMAP_ORG = ("Sitemaps XML format — sitemaps.org",
                    "https://www.sitemaps.org/protocol.html")
CITE_NOINDEX = ("Block search indexing with noindex — Google Search Central",
                "https://developers.google.com/search/docs/crawling-indexing/block-indexing")
CITE_ROBOTS = ("Robots.txt specification — Google Search Central",
               "https://developers.google.com/search/docs/crawling-indexing/robots/robots_txt")
CITE_ROBOTS_INTRO = ("Introduction to robots.txt — Google Search Central",
                     "https://developers.google.com/search/docs/crawling-indexing/robots/intro")
CITE_INDEXING_REPORT = ("Page indexing report — Google Search Console Help",
                        "https://support.google.com/webmasters/answer/7440203")

GUIDES = [

{
"slug": "sitemap-lists-urls-that-must-not-be-indexed",
"title": "Your Sitemap Lists URLs That Redirect, 404 or Say noindex",
"description": "A sitemap is a recommendation. Listing a noindex or 404 URL contradicts itself, and Search Console reports it as an error.",
"h1": "your sitemap lists URLs that redirect, 404 or say noindex",
"category": "Technical SEO",
"pill": "Repair",
"chips": ["No API key needed", "Python and Node.js", "Rewrites the file"],
"keywords": ["submitted URL marked noindex", "sitemap 404", "sitemap redirect",
             "sitemap errors Search Console", "sitemap best practices"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Search Console is reporting <em>Submitted URL marked &lsquo;noindex&rsquo;</em>, or <em>Submitted URL not found (404)</em>, and the count keeps growing. A sitemap is a statement that these URLs are worth indexing. Listing a URL that returns 404, redirects elsewhere, or carries a <code>noindex</code> is a contradiction &mdash; you are recommending a page and simultaneously telling the crawler to ignore it.",
"short_answer": """<p>Fetch every URL in your sitemap and keep only the ones that return <code>200</code>, are not <code>noindex</code>, and whose canonical points at themselves. Everything else comes out.</p>
<p>Two related facts worth knowing while you are in there: a sitemap is capped at <strong>50,000 URLs and 50&nbsp;MB uncompressed</strong>, and Google <strong>ignores <code>changefreq</code> and <code>priority</code> entirely</strong>. Only <code>lastmod</code> matters, and only if it is a real W3C datetime and honestly reflects a change.</p>""",
"problem": """<p>Sitemaps are usually generated, which is exactly why they drift. The generator walks a route manifest or a content directory; the <code>noindex</code> lives in a template; the redirect lives in a host config. Nothing joins those three sources, so a page can be excluded from indexing in one place and recommended in another indefinitely.</p>
<p>The errors are also not fatal, so they accumulate. Google carries on crawling the rest. You get a growing count in a report you might check monthly, attached to URLs you removed a year ago.</p>""",
"why": """<p><strong>The sitemap and the page are written by different things.</strong> A static-site generator emits the sitemap from its routes; the <code>noindex</code> is a decision made in a layout or a CMS field. Neither validates against the other.</p>
<p><strong>Deleted content leaves the sitemap last.</strong> Removing a page removes the route, but a cached, committed or manually maintained sitemap keeps naming it. If your sitemap is checked into the repo rather than generated at build, this is guaranteed eventually.</p>
<p><strong>A redirect in a sitemap is a weaker signal than it looks.</strong> You are telling Google the old URL is canonical while the server says it is not. Listing the destination directly removes the ambiguity, and costs nothing.</p>
<p><strong>Nobody reads a sitemap.</strong> It is 50,000 lines of XML that no human opens. A generator bug can put every URL in twice, or use the wrong origin, and the only symptom is a number in a report.</p>""",
"steps": [
 {"h": "Fetch the sitemap and expand any index",
  "body": """<p>A sitemap index points at child sitemaps; the problem is usually in one child. The script follows one level, which is the depth the protocol allows.</p>"""},
 {"h": "Check each URL for the four disqualifiers",
  "body": """<p>Non-200 status, a <code>noindex</code> in either the meta robots tag or the <code>X-Robots-Tag</code> header, a canonical pointing at a different URL, and a host that does not match the sitemap's own host. That last one matters: sitemap URLs must be on the same site as the sitemap unless you have cross-submitted through <code>robots.txt</code>.</p>"""},
 {"h": "Rewrite the sitemap without them",
  "body": """<p>This is a file you own, so the repair is real rather than a report. The script writes a new sitemap and leaves the original in place until you have compared them.</p>"""},
 {"h": "Fix the generator, not just the output",
  "body": """<p>If the sitemap is generated at build time, the same URLs come back on the next deploy. Use the script's report to find which rule is wrong &mdash; usually a route list that does not consult the same flag the template does.</p>"""},
 {"h": "Drop changefreq and priority while you are here",
  "body": """<p>Google ignores both. They add bytes to a size-capped file and give a false impression that you are steering crawl behaviour. Keep <code>lastmod</code>, and only if it is accurate &mdash; a <code>lastmod</code> that updates on every build is noise.</p>"""},
],
"verify": """<p>Re-run the script against the new file; it should report zero removals. Then resubmit in Search Console and watch the error count fall &mdash; it will take a few crawl cycles rather than a few minutes.</p>
<pre><code class="language-bash">python3 sitemap_prune.py --sitemap https://example.com/sitemap.xml --out /dev/null
# 0 URL(s) to remove</code></pre>""",
"code_intro": "The script fetches the sitemap, expands one level of index, requests every URL, and classifies each one. With <code>--out</code> it writes a cleaned sitemap; without it, it only reports. The classification is a pure function so the rules are visible and tested, rather than buried in the fetch loop.",
"py_file": "sitemap_prune.py",
"py": '''"""Remove URLs from a sitemap that contradict it: 404s, redirects, noindex.

A sitemap says "these pages are worth indexing". Listing a page that 404s or carries
a noindex says the opposite in the same breath, and Search Console reports it.
"""
import argparse
import logging
import re
import sys
import xml.etree.ElementTree as ET
from urllib.parse import urlsplit

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("sitemap_prune")

NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
MAX_URLS = 50_000          # protocol limit
MAX_BYTES = 50 * 1024 ** 2  # 50 MB uncompressed


def verdict(url, sitemap_host, status, final_url, head_noindex, meta_noindex, canonical):
    """Pure decision function: why should this URL not be in the sitemap?

    Returns a list of reasons; empty means keep. Kept separate from the fetching so
    the rules can be read and tested without a network.
    """
    reasons = []
    if status >= 400:
        reasons.append(f"returns {status}")
    elif status >= 300 or (final_url and final_url != url):
        reasons.append(f"redirects to {final_url or 'elsewhere'}; list the destination")
    if head_noindex:
        reasons.append("X-Robots-Tag: noindex")
    if meta_noindex:
        reasons.append("meta robots noindex")
    if canonical and canonical.rstrip("/") != url.rstrip("/"):
        reasons.append(f"canonical points to {canonical}")
    if urlsplit(url).netloc != sitemap_host:
        reasons.append(f"host {urlsplit(url).netloc} is not the sitemap's host "
                       f"{sitemap_host}; cross-submission needs robots.txt")
    return reasons


def parse_urls(xml_text):
    """Return (child_sitemaps, urls). One level of index expansion is the protocol max."""
    root = ET.fromstring(xml_text)
    children = [e.text.strip() for e in root.findall(".//sm:sitemap/sm:loc", NS) if e.text]
    urls = [e.text.strip() for e in root.findall(".//sm:url/sm:loc", NS) if e.text]
    return children, urls


def inspect(session, url):
    r = session.get(url, timeout=30, allow_redirects=True)
    body = r.text[:200_000]
    head_noindex = "noindex" in (r.headers.get("X-Robots-Tag", "").lower())
    m = re.search(r'<meta[^>]+name=["\\']robots["\\'][^>]*>', body, re.I)
    meta_noindex = bool(m and "noindex" in m.group(0).lower())
    c = re.search(r'<link[^>]+rel=["\\']canonical["\\'][^>]*href=["\\']([^"\\']+)', body, re.I)
    status = r.history[0].status_code if r.history else r.status_code
    return status, r.url, head_noindex, meta_noindex, (c.group(1) if c else None)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sitemap", required=True)
    ap.add_argument("--out", help="write the cleaned sitemap here")
    args = ap.parse_args()

    s = requests.Session()
    s.headers.update({"User-Agent": "sitemap-prune/1.0"})

    top = s.get(args.sitemap, timeout=30)
    top.raise_for_status()
    if len(top.content) > MAX_BYTES:
        log.warning("sitemap is over the 50 MB uncompressed limit")
    children, urls = parse_urls(top.text)
    for child in children:
        r = s.get(child, timeout=30)
        urls.extend(parse_urls(r.text)[1])
    if len(urls) > MAX_URLS:
        log.warning("%d URLs -- over the %d limit; split into an index", len(urls), MAX_URLS)

    host = urlsplit(args.sitemap).netloc
    keep, drop = [], []
    for u in urls:
        try:
            reasons = verdict(u, host, *inspect(s, u))
        except requests.RequestException as e:
            reasons = [f"request failed: {e.__class__.__name__}"]
        if reasons:
            drop.append((u, reasons))
            log.warning("DROP %s -- %s", u, "; ".join(reasons))
        else:
            keep.append(u)

    log.info("%d keep, %d to remove", len(keep), len(drop))
    if args.out and args.out != "/dev/null":
        body = "\\n".join(f"  <url>\\n    <loc>{u}</loc>\\n  </url>" for u in keep)
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write('<?xml version="1.0" encoding="UTF-8"?>\\n'
                     '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\\n'
                     f"{body}\\n</urlset>\\n")
        log.info("wrote %s -- compare it against the original before replacing", args.out)
    return 1 if drop else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "sitemap-prune.mjs",
"js": '''/**
 * Remove URLs from a sitemap that contradict it: 404s, redirects, noindex.
 *
 * A sitemap says "these pages are worth indexing". Listing a page that 404s or
 * carries a noindex says the opposite in the same breath.
 */
import { writeFileSync } from 'node:fs';

const MAX_URLS = 50_000;                 // protocol limit
const MAX_BYTES = 50 * 1024 ** 2;        // 50 MB uncompressed

/**
 * Pure decision function: why should this URL not be in the sitemap?
 * Empty array means keep. Separate from fetching so the rules can be tested.
 */
export function verdict({ url, sitemapHost, status, finalUrl, headNoindex, metaNoindex, canonical }) {
  const reasons = [];
  if (status >= 400) reasons.push(`returns ${status}`);
  else if (status >= 300 || (finalUrl && finalUrl !== url)) {
    reasons.push(`redirects to ${finalUrl ?? 'elsewhere'}; list the destination`);
  }
  if (headNoindex) reasons.push('X-Robots-Tag: noindex');
  if (metaNoindex) reasons.push('meta robots noindex');
  if (canonical && canonical.replace(/\\/$/, '') !== url.replace(/\\/$/, '')) {
    reasons.push(`canonical points to ${canonical}`);
  }
  const host = new URL(url).host;
  if (host !== sitemapHost) {
    reasons.push(`host ${host} is not the sitemap's host ${sitemapHost}; `
      + 'cross-submission needs robots.txt');
  }
  return reasons;
}

/** Return { children, urls }. One level of index expansion is the protocol max. */
export function parseUrls(xml) {
  const locs = (block) => [...block.matchAll(/<loc>\\s*([^<\\s]+)\\s*<\\/loc>/g)].map((m) => m[1]);
  const sitemapBlocks = xml.match(/<sitemap>[\\s\\S]*?<\\/sitemap>/g) ?? [];
  const urlBlocks = xml.match(/<url>[\\s\\S]*?<\\/url>/g) ?? [];
  return { children: sitemapBlocks.flatMap(locs), urls: urlBlocks.flatMap(locs) };
}

async function inspect(url) {
  const r = await fetch(url, { redirect: 'follow' });
  const body = (await r.text()).slice(0, 200_000);
  const headNoindex = (r.headers.get('x-robots-tag') ?? '').toLowerCase().includes('noindex');
  const meta = body.match(/<meta[^>]+name=["']robots["'][^>]*>/i);
  const canon = body.match(/<link[^>]+rel=["']canonical["'][^>]*href=["']([^"']+)/i);
  return {
    status: r.redirected ? 301 : r.status,
    finalUrl: r.url,
    headNoindex,
    metaNoindex: Boolean(meta && meta[0].toLowerCase().includes('noindex')),
    canonical: canon?.[1] ?? null,
  };
}

async function main() {
  const arg = (n) => process.argv[process.argv.indexOf(n) + 1];
  const sitemap = arg('--sitemap');
  const out = process.argv.includes('--out') ? arg('--out') : null;

  const top = await fetch(sitemap);
  const xml = await top.text();
  if (Buffer.byteLength(xml) > MAX_BYTES) console.warn('sitemap is over the 50 MB limit');
  const { children, urls } = parseUrls(xml);
  for (const child of children) urls.push(...parseUrls(await (await fetch(child)).text()).urls);
  if (urls.length > MAX_URLS) console.warn(`${urls.length} URLs -- over the ${MAX_URLS} limit`);

  const sitemapHost = new URL(sitemap).host;
  const keep = []; const drop = [];
  for (const url of urls) {
    let reasons;
    try { reasons = verdict({ url, sitemapHost, ...(await inspect(url)) }); }
    catch (e) { reasons = [`request failed: ${e.name}`]; }
    if (reasons.length) { drop.push([url, reasons]); console.warn(`DROP ${url} -- ${reasons.join('; ')}`); }
    else keep.push(url);
  }

  console.log(`${keep.length} keep, ${drop.length} to remove`);
  if (out && out !== '/dev/null') {
    const body = keep.map((u) => `  <url>\\n    <loc>${u}</loc>\\n  </url>`).join('\\n');
    writeFileSync(out, '<?xml version="1.0" encoding="UTF-8"?>\\n'
      + '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\\n'
      + `${body}\\n</urlset>\\n`);
    console.log(`wrote ${out} -- compare it against the original before replacing`);
  }
  process.exit(drop.length ? 1 : 0);
}

if (import.meta.url === `file://${process.argv[1]}`) main();
''',
"test_intro": "The case worth pinning is the trailing slash. A canonical of <code>/about</code> against a sitemap entry of <code>/about/</code> is the same page, and treating it as a mismatch would delete good URLs from a file people then deploy.",
"test_py_file": "test_sitemap_prune.py",
"test_py": '''from sitemap_prune import verdict, parse_urls

HOST = "example.com"
SM = '<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' \\
     "<url><loc>https://example.com/a</loc></url></urlset>"


def ok(url="https://example.com/a", **kw):
    args = dict(status=200, final_url=url, head_noindex=False,
                meta_noindex=False, canonical=url)
    args.update(kw)
    return verdict(url, HOST, args["status"], args["final_url"], args["head_noindex"],
                   args["meta_noindex"], args["canonical"])


def test_a_healthy_url_is_kept():
    assert ok() == []


def test_a_404_is_dropped():
    assert any("returns 404" in r for r in ok(status=404))


def test_a_redirect_is_dropped_with_the_destination():
    r = ok(status=301, final_url="https://example.com/b")
    assert any("redirects to https://example.com/b" in x for x in r)


def test_meta_noindex_is_dropped():
    assert any("meta robots noindex" in r for r in ok(meta_noindex=True))


def test_x_robots_tag_noindex_is_dropped():
    assert any("X-Robots-Tag" in r for r in ok(head_noindex=True))


def test_a_trailing_slash_is_not_a_canonical_mismatch():
    """Same page. Treating this as a mismatch deletes good URLs."""
    assert ok(url="https://example.com/a/", canonical="https://example.com/a") == []


def test_a_real_canonical_mismatch_is_dropped():
    assert any("canonical points to" in r
               for r in ok(canonical="https://example.com/other"))


def test_a_foreign_host_is_dropped():
    assert any("is not the sitemap's host" in r
               for r in ok(url="https://cdn.example.net/a"))


def test_parse_urls_reads_locs():
    assert parse_urls(SM)[1] == ["https://example.com/a"]
''',
"test_js_file": "sitemap-prune.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict, parseUrls } from './sitemap-prune.mjs';

const ok = (over = {}) => {
  const url = over.url ?? 'https://example.com/a';
  return verdict({
    url, sitemapHost: 'example.com', status: 200, finalUrl: url,
    headNoindex: false, metaNoindex: false, canonical: url, ...over,
  });
};

test('a healthy URL is kept', () => assert.deepEqual(ok(), []));

test('a 404 is dropped', () => {
  assert.ok(ok({ status: 404 }).some((r) => r.includes('returns 404')));
});

test('a redirect is dropped with the destination', () => {
  assert.ok(ok({ status: 301, finalUrl: 'https://example.com/b' })
    .some((r) => r.includes('redirects to https://example.com/b')));
});

test('a trailing slash is not a canonical mismatch', () => {
  assert.deepEqual(ok({ url: 'https://example.com/a/', canonical: 'https://example.com/a' }), []);
});

test('a foreign host is dropped', () => {
  assert.ok(ok({ url: 'https://cdn.example.net/a' })
    .some((r) => r.includes("is not the sitemap's host")));
});

test('parseUrls reads locs', () => {
  const xml = '<urlset><url><loc>https://example.com/a</loc></url></urlset>';
  assert.deepEqual(parseUrls(xml).urls, ['https://example.com/a']);
});
''',
"faq": [
 ("What does 'Submitted URL marked noindex' mean?",
  "Your sitemap recommends a URL for indexing while the page itself tells crawlers not to index it. One of the two is wrong. Decide which, then fix that source — usually the sitemap generator, which does not consult the same flag the template does."),
 ("Should a sitemap list redirecting URLs?",
  "No. You are telling Google the old URL is canonical while the server says it is not. List the destination directly; it costs nothing and removes the ambiguity."),
 ("Do changefreq and priority do anything?",
  "Google ignores both. They consume bytes in a size-capped file and create a false impression that you are steering crawl behaviour. Keep lastmod, and only if it reflects a real content change rather than every build."),
 ("How big can a sitemap be?",
  "50,000 URLs and 50 MB uncompressed. Past either limit, split it and reference the parts from a sitemap index — which is also the cleaner structure once a site has distinct sections."),
 ("Can my sitemap list URLs on another domain?",
  "Not by default. Sitemap URLs must be on the same site as the sitemap itself unless you cross-submit by referencing the sitemap from that site's robots.txt."),
],
"related": [
 ("/seo/robots-txt-blocks-the-noindex-you-added/", "robots.txt blocking the noindex it was meant to enforce"),
 ("/seo/canonical-points-at-staging-or-a-redirect/", "A canonical pointing at staging or a redirect"),
 ("/seo/soft-404-returns-200/", "A missing page that returns 200"),
],
"citations": [CITE_SITEMAP, CITE_SITEMAP_ORG, CITE_NOINDEX, CITE_INDEXING_REPORT],
},

{
"slug": "robots-txt-blocks-the-noindex-you-added",
"title": "robots.txt Blocks the noindex It Was Meant to Enforce",
"description": "Disallow stops the crawl, so the noindex on the page is never read. The URL can still be indexed, without a snippet.",
"h1": "robots.txt blocks the noindex it was meant to enforce",
"category": "Technical SEO",
"pill": "Diagnostic",
"chips": ["No API key needed", "Python and Node.js", "Rule conflicts"],
"keywords": ["noindex not working", "indexed though blocked by robots.txt",
             "robots.txt disallow noindex", "robots.txt conflict", "crawl vs index"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "You added <code>noindex</code> to a page and blocked it in <code>robots.txt</code> for good measure. Weeks later it is still in the results, listed without a description, and Search Console says <em>Indexed, though blocked by robots.txt</em>. The two rules cancelled each other out. <strong>Disallow prevents the crawl, so the crawler never fetches the page and never sees the <code>noindex</code>.</strong> Belt and braces removed the belt.",
"short_answer": """<p><code>robots.txt</code> controls <em>crawling</em>. <code>noindex</code> controls <em>indexing</em>. A URL that is blocked from crawling can still be indexed from links pointing at it &mdash; Google just has no content to show, hence the missing snippet.</p>
<p>To remove a page: <strong>allow the crawl and serve <code>noindex</code></strong>. Once it has dropped out of the index you can block it again, if you still want to.</p>""",
"problem": """<p>The two mechanisms sound like they do the same job, and stacking them feels safer than picking one. It is the specific combination that fails, so the more cautious you are, the more likely you are to hit it.</p>
<p>The same trap catches resources. Blocking your CSS or JavaScript directory stops Google rendering the page as a visitor sees it, which affects how the page is assessed. That block is usually years old and made for a reason that no longer exists.</p>""",
"why": """<p><strong>Crawling and indexing are separate stages and the controls live in different places.</strong> One is a file at the root of the host, the other is a tag in the document. Nothing cross-checks them, and the failure is silent for weeks because it only shows up as a page that will not leave the index.</p>
<p><strong>Google states the dependency explicitly:</strong> for the <code>noindex</code> rule to work, the page must not be blocked by <code>robots.txt</code> and must otherwise be reachable by the crawler. It is documented, and it is still the most common way a removal fails.</p>
<p><strong>Matching is not first-match-wins.</strong> Google uses the <em>most specific</em> rule &mdash; the longest matching path &mdash; and on a tie, <code>Allow</code> beats <code>Disallow</code>. Reading the file top to bottom gives you the wrong answer, which is how people conclude a page is allowed when it is not.</p>
<p><strong>The file has limits.</strong> Google parses the first 500&nbsp;KiB and ignores the rest, so a generated <code>robots.txt</code> that has grown for years may have rules that are simply not read.</p>""",
"steps": [
 {"h": "Decide which outcome you actually want",
  "body": """<p>Out of the index: allow the crawl, serve <code>noindex</code>. Off the crawl budget but indexing is fine: <code>Disallow</code> alone. Gone entirely and urgently: remove the page and return <code>410</code>, plus the Search Console removal tool for the short term.</p>"""},
 {"h": "Test every noindex page against the live robots.txt",
  "body": """<p>This is what the script does: for each URL, it evaluates the <code>robots.txt</code> rules the way Google does &mdash; longest match wins, <code>Allow</code> wins ties &mdash; and reports any page that is both blocked and carries a <code>noindex</code>.</p>"""},
 {"h": "Unblock, wait for the recrawl, then reblock if you want",
  "body": """<p>The crawler has to fetch the page once to learn it should be dropped. That is a crawl cycle, not an instant change; days to weeks depending on the URL.</p>"""},
 {"h": "Check you are not blocking CSS or JS",
  "body": """<p>An old <code>Disallow: /assets/</code> or <code>/static/</code> stops the page rendering the way a visitor sees it. The script flags these separately because the fix is different: you almost always just remove the rule.</p>"""},
 {"h": "Confirm robots.txt is under 500 KiB",
  "body": """<p>Anything past that is not parsed. If your file is generated and large, the rules you care about may be in the part Google never reads.</p>"""},
],
"verify": """<p>Confirm the page is fetchable and still says <code>noindex</code>:</p>
<pre><code class="language-bash">curl -sI https://example.com/private/ | grep -i x-robots-tag
curl -s  https://example.com/private/ | grep -i 'name="robots"'</code></pre>
<p>Then use the URL Inspection tool in Search Console, which reports crawl permission and the indexing decision as two separate lines &mdash; which is the distinction the whole problem turns on.</p>""",
"code_intro": "The script fetches <code>robots.txt</code>, implements Google's matching rules (longest match wins, <code>Allow</code> breaks ties), and tests each URL you give it. It reports the conflict that matters — blocked <em>and</em> noindex — plus blocked CSS and JS, and warns if the file exceeds the parsed size.",
"py_file": "robots_conflict.py",
"py": '''"""Find pages that are both Disallowed in robots.txt and marked noindex.

Those two rules cancel: the crawler never fetches the page, so it never reads the
noindex, and the URL can stay indexed without a snippet indefinitely.
"""
import argparse
import logging
import re
import sys
from urllib.parse import urlsplit

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("robots_conflict")

MAX_ROBOTS_BYTES = 500 * 1024  # Google parses the first 500 KiB
ASSET = re.compile(r"\\.(css|js|mjs|woff2?|svg|png|jpe?g|webp)$", re.I)


def parse_robots(text, agent="*"):
    """Return the (allow, disallow) path lists for one user-agent group.

    A specific group wins over * entirely -- Google does not merge them.
    """
    groups, current = {}, None
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        field, _, value = line.partition(":")
        field, value = field.strip().lower(), value.strip()
        if field == "user-agent":
            current = value.lower()
            groups.setdefault(current, {"allow": [], "disallow": []})
        elif field in ("allow", "disallow") and current is not None:
            groups[current][field].append(value)
    g = groups.get(agent.lower()) or groups.get("*") or {"allow": [], "disallow": []}
    return g["allow"], g["disallow"]


def _match_len(pattern, path):
    """Length of the match, or -1. Supports * and $ as Google does."""
    if pattern == "":
        return -1
    rx = "^" + re.escape(pattern).replace(r"\\*", ".*").replace(r"\\$", "$")
    return len(pattern) if re.match(rx, path) else -1


def is_blocked(path, allow, disallow):
    """Google's rule: the longest matching path wins; Allow breaks a tie.

    Reading the file top to bottom gives the wrong answer, which is how people
    conclude a page is allowed when it is not.
    """
    best_allow = max((_match_len(p, path) for p in allow), default=-1)
    best_disallow = max((_match_len(p, path) for p in disallow), default=-1)
    if best_disallow < 0:
        return False
    return best_disallow > best_allow


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", required=True, help="https://example.com")
    ap.add_argument("--url", nargs="+", required=True)
    ap.add_argument("--agent", default="Googlebot")
    args = ap.parse_args()

    s = requests.Session()
    r = s.get(args.site.rstrip("/") + "/robots.txt", timeout=30)
    if len(r.content) > MAX_ROBOTS_BYTES:
        log.warning("robots.txt is over 500 KiB -- Google ignores the rest of the file")
    allow, disallow = parse_robots(r.text, args.agent)
    log.info("%d allow rule(s), %d disallow rule(s)", len(allow), len(disallow))

    conflicts = 0
    for url in args.url:
        path = urlsplit(url).path or "/"
        blocked = is_blocked(path, allow, disallow)
        if blocked and ASSET.search(path):
            log.warning("%s is a blocked asset -- Google cannot render the page as a "
                        "visitor sees it", url)
            continue
        if not blocked:
            log.info("%s crawlable", url)
            continue
        page = s.get(url, timeout=30)
        meta = re.search(r'<meta[^>]+name=["\\']robots["\\'][^>]*>', page.text, re.I)
        noindex = bool(meta and "noindex" in meta.group(0).lower()) or \\
            "noindex" in page.headers.get("X-Robots-Tag", "").lower()
        if noindex:
            conflicts += 1
            log.error("%s is BLOCKED and marked noindex -- the crawler never reads the "
                      "noindex. Unblock it, wait for the recrawl, then reblock.", url)
        else:
            log.info("%s blocked, no noindex -- may still be indexed without a snippet", url)
    return 1 if conflicts else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "robots-conflict.mjs",
"js": '''/**
 * Find pages that are both Disallowed in robots.txt and marked noindex.
 *
 * Those two rules cancel: the crawler never fetches the page, so it never reads the
 * noindex, and the URL can stay indexed without a snippet indefinitely.
 */
const MAX_ROBOTS_BYTES = 500 * 1024; // Google parses the first 500 KiB
const ASSET = /\\.(css|js|mjs|woff2?|svg|png|jpe?g|webp)$/i;

/**
 * Return { allow, disallow } for one user-agent group.
 * A specific group wins over * entirely -- Google does not merge them.
 */
export function parseRobots(text, agent = '*') {
  const groups = {};
  let current = null;
  for (const raw of text.split(/\\r?\\n/)) {
    const line = raw.split('#')[0].trim();
    if (!line || !line.includes(':')) continue;
    const [field, ...rest] = line.split(':');
    const key = field.trim().toLowerCase();
    const value = rest.join(':').trim();
    if (key === 'user-agent') {
      current = value.toLowerCase();
      groups[current] ??= { allow: [], disallow: [] };
    } else if ((key === 'allow' || key === 'disallow') && current !== null) {
      groups[current][key].push(value);
    }
  }
  return groups[agent.toLowerCase()] ?? groups['*'] ?? { allow: [], disallow: [] };
}

const matchLen = (pattern, path) => {
  if (pattern === '') return -1;
  const rx = new RegExp(`^${pattern.replace(/[.+^${}()|[\\]\\\\]/g, '\\\\$&')
    .replace(/\\*/g, '.*').replace(/\\\\\\$$/, '$')}`);
  return rx.test(path) ? pattern.length : -1;
};

/**
 * Google's rule: the longest matching path wins; Allow breaks a tie. Reading the
 * file top to bottom gives the wrong answer.
 */
export function isBlocked(path, allow, disallow) {
  const bestAllow = Math.max(-1, ...allow.map((p) => matchLen(p, path)));
  const bestDisallow = Math.max(-1, ...disallow.map((p) => matchLen(p, path)));
  if (bestDisallow < 0) return false;
  return bestDisallow > bestAllow;
}

async function main() {
  const arg = (n) => process.argv[process.argv.indexOf(n) + 1];
  const site = arg('--site');
  const ui = process.argv.indexOf('--url');
  const urls = process.argv.slice(ui + 1).filter((a) => !a.startsWith('--'));
  const agent = process.argv.includes('--agent') ? arg('--agent') : 'Googlebot';

  const res = await fetch(`${site.replace(/\\/$/, '')}/robots.txt`);
  const text = await res.text();
  if (Buffer.byteLength(text) > MAX_ROBOTS_BYTES) {
    console.warn('robots.txt is over 500 KiB -- Google ignores the rest of the file');
  }
  const { allow, disallow } = parseRobots(text, agent);
  console.log(`${allow.length} allow rule(s), ${disallow.length} disallow rule(s)`);

  let conflicts = 0;
  for (const url of urls) {
    const path = new URL(url).pathname || '/';
    const blocked = isBlocked(path, allow, disallow);
    if (blocked && ASSET.test(path)) {
      console.warn(`${url} is a blocked asset -- Google cannot render the page as a visitor sees it`);
      continue;
    }
    if (!blocked) { console.log(`${url} crawlable`); continue; }
    const page = await fetch(url);
    const body = await page.text();
    const meta = body.match(/<meta[^>]+name=["']robots["'][^>]*>/i);
    const noindex = Boolean(meta && meta[0].toLowerCase().includes('noindex'))
      || (page.headers.get('x-robots-tag') ?? '').toLowerCase().includes('noindex');
    if (noindex) {
      conflicts += 1;
      console.error(`${url} is BLOCKED and marked noindex -- the crawler never reads the `
        + 'noindex. Unblock it, wait for the recrawl, then reblock.');
    } else {
      console.log(`${url} blocked, no noindex -- may still be indexed without a snippet`);
    }
  }
  process.exit(conflicts ? 1 : 0);
}

if (import.meta.url === `file://${process.argv[1]}`) main();
''',
"test_intro": "These tests encode the matching rule that trips people up. A specific <code>Allow</code> under a broad <code>Disallow</code> wins because it is longer, not because of where it sits in the file — and an equal-length tie goes to <code>Allow</code>.",
"test_py_file": "test_robots_conflict.py",
"test_py": '''from robots_conflict import is_blocked, parse_robots

TXT = """
User-agent: *
Disallow: /private/
Allow: /private/public-page

User-agent: Googlebot
Disallow: /admin/
"""


def test_a_specific_agent_group_wins_over_star():
    """Google does not merge groups; the specific one replaces the wildcard."""
    allow, disallow = parse_robots(TXT, "Googlebot")
    assert disallow == ["/admin/"]


def test_the_star_group_is_used_for_an_unknown_agent():
    allow, disallow = parse_robots(TXT, "SomeOtherBot")
    assert disallow == ["/private/"]


def test_an_unmatched_path_is_allowed():
    assert not is_blocked("/about", [], ["/private/"])


def test_a_disallowed_path_is_blocked():
    assert is_blocked("/private/x", [], ["/private/"])


def test_a_longer_allow_beats_a_shorter_disallow():
    """Position in the file is irrelevant; length decides."""
    assert not is_blocked("/private/public-page", ["/private/public-page"], ["/private/"])


def test_a_tie_goes_to_allow():
    assert not is_blocked("/x/", ["/x/"], ["/x/"])


def test_an_empty_disallow_blocks_nothing():
    assert not is_blocked("/anything", [], [""])


def test_a_wildcard_pattern_matches():
    assert is_blocked("/search?q=1", [], ["/*?"])
''',
"test_js_file": "robots-conflict.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { isBlocked, parseRobots } from './robots-conflict.mjs';

const TXT = `
User-agent: *
Disallow: /private/
Allow: /private/public-page

User-agent: Googlebot
Disallow: /admin/
`;

test('a specific agent group wins over *', () => {
  assert.deepEqual(parseRobots(TXT, 'Googlebot').disallow, ['/admin/']);
});

test('the * group is used for an unknown agent', () => {
  assert.deepEqual(parseRobots(TXT, 'SomeOtherBot').disallow, ['/private/']);
});

test('a disallowed path is blocked', () => {
  assert.equal(isBlocked('/private/x', [], ['/private/']), true);
});

test('a longer allow beats a shorter disallow', () => {
  assert.equal(isBlocked('/private/public-page', ['/private/public-page'], ['/private/']), false);
});

test('a tie goes to allow', () => {
  assert.equal(isBlocked('/x/', ['/x/'], ['/x/']), false);
});

test('an empty disallow blocks nothing', () => {
  assert.equal(isBlocked('/anything', [], ['']), false);
});
''',
"faq": [
 ("Why is my noindex page still in Google?",
  "Most often because robots.txt blocks it. The crawler never fetches the page, so it never reads the noindex. Allow the crawl, wait for a recrawl, and it will drop out — then you can block it again if you want."),
 ("What does 'Indexed, though blocked by robots.txt' mean?",
  "Google learned the URL exists from links pointing at it, but was not allowed to fetch it. It can list the URL without a description, because it has no content to show."),
 ("Does robots.txt stop a page being indexed?",
  "No. It stops crawling. Indexing is controlled by noindex, which requires a crawl to be read. They are separate stages, which is exactly why stacking both rules fails."),
 ("How does Google resolve conflicting rules?",
  "The most specific rule wins — the longest matching path — and on a tie, Allow beats Disallow. Position in the file does not matter, so reading top to bottom gives the wrong answer."),
 ("Is there a size limit on robots.txt?",
  "Google parses the first 500 KiB and ignores the rest. A large generated file may have rules that are simply never read."),
 ("Should I block my CSS and JavaScript?",
  "No. Blocking them stops Google rendering the page the way a visitor sees it. These rules are usually years old and made for a reason that no longer applies."),
],
"related": [
 ("/seo/sitemap-lists-urls-that-must-not-be-indexed/", "A sitemap listing URLs that redirect, 404 or say noindex"),
 ("/seo/canonical-points-at-staging-or-a-redirect/", "A canonical pointing at staging or a redirect"),
 ("/seo/", "Technical SEO field notes"),
],
"citations": [CITE_ROBOTS, CITE_ROBOTS_INTRO, CITE_NOINDEX, CITE_INDEXING_REPORT],
},

]
