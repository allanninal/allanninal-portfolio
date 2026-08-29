#!/usr/bin/env python3
"""Generate the /email/ field-notes section.

Same shape as /dns/ and the eight ecommerce sections: one page per problem, each
with the symptom in plain words, why it happens, a fix you can run, the full script
in Python and Node.js, a test, and an FAQ. Structure and CSS are lifted from /dns/
so the section reads as part of the same body of work rather than a bolt-on.

Scope note: /dns/ already covers the RECORD layer — SPF syntax, DKIM selectors,
DMARC policy, MX targets. This section covers the layer above it, where the sending
platform's own API is what detects and repairs the problem. Every guide here is
fixable with a small script against a provider API, which is the line that decides
whether a topic belongs in this section at all.
"""
import html as H
import json
import re
import sys
from pathlib import Path

# The site header is shared by every page on allanninal.dev; see tools/nav/.
# Generating it here rather than writing markup means a rebuilt section can no
# longer drift into having its own menu, which is how the site ended up with a
# different bar on nearly every page.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "nav"))
import header as NAV

SITE = "https://www.allanninal.dev"
OUT = Path.home() / "Projects/allanninal.dev/email"
GA = "G-DLRBEQ85ZN"
ADS = "ca-pub-3474747237489350"


def esc(t: str) -> str:
    return H.escape(t, quote=False)


def code_block(filename_py: str, py: str, filename_js: str, js: str) -> str:
    return f'''<div class="code-block" data-code>
<div class="code-block__bar">
<button class="code-tab" data-lang="python" aria-selected="true" type="button">Python</button>
<button class="code-tab" data-lang="node" aria-selected="false" type="button">Node.js</button>
<button class="code-block__copy" type="button">Copy</button>
</div>
<div class="code-pane" data-lang="python" data-active="true">
<div class="code-filename">{filename_py}</div>
<pre><code class="language-python">{H.escape(py)}</code></pre>
</div>
<div class="code-pane" data-lang="node">
<div class="code-filename">{filename_js}</div>
<pre><code class="language-javascript">{H.escape(js)}</code></pre>
</div>
</div>'''


def head(g: dict) -> str:
    url = f"{SITE}/email/{g['slug']}/"
    graph = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "TechArticle",
                "@id": url + "#article",
                "headline": g["title"],
                "description": g["description"],
                "url": url,
                "mainEntityOfPage": {"@type": "WebPage", "@id": url},
                "datePublished": "2026-08-28",
                "dateModified": "2026-08-28",
                "inLanguage": "en",
                "articleSection": g["category"],
                "keywords": ", ".join(g["keywords"]),
                "author": {"@id": SITE + "/#person"},
                "publisher": {"@id": SITE + "/#person"},
                "proficiencyLevel": "Intermediate",
                "dependencies": g["deps"],
            },
            {
                "@type": "Person",
                "@id": SITE + "/#person",
                "name": "Allan Niñal",
                "jobTitle": "AI and Software Engineer",
                "url": SITE + "/",
                "sameAs": ["https://www.linkedin.com/in/allanninal/",
                           "https://github.com/allanninal"],
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Field notes",
                     "item": SITE + "/email/"},
                    {"@type": "ListItem", "position": 2, "name": g["category"],
                     "item": SITE + "/email/"},
                    {"@type": "ListItem", "position": 3, "name": g["title"], "item": url},
                ],
            },
            {
                "@type": "FAQPage",
                "@id": url + "#faq",
                "mainEntity": [
                    {"@type": "Question", "name": q,
                     "acceptedAnswer": {"@type": "Answer", "text": a}}
                    for q, a in g["faq"]
                ],
            },
        ],
    }
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(g["title"])}</title>
<meta name="description" content="{H.escape(g["description"], quote=True)}">
<link rel="canonical" href="{url}">
<meta name="robots" content="index, follow">
<meta name="author" content="Allan Ni&ntilde;al">
<meta property="og:type" content="article">
<meta property="og:title" content="{H.escape(g["title"], quote=True)}">
<meta property="og:description" content="{H.escape(g["description"], quote=True)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}/og-image.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{H.escape(g["title"], quote=True)}">
<meta name="twitter:description" content="{H.escape(g["description"], quote=True)}">
<meta name="twitter:image" content="{SITE}/og-image.png">
<meta name="google-adsense-account" content="{ADS}">
<script async src="https://www.googletagmanager.com/gtag/js?id={GA}"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','{GA}');</script>
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={ADS}" crossorigin="anonymous"></script>
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="/email/assets/email.css">
<link rel="stylesheet" href="/assets/site-nav.css">\n<link rel="stylesheet" href="/assets/site-mobile.css">
<script type="application/ld+json">{json.dumps(graph, ensure_ascii=False, separators=(",", ":"))}</script>
</head>'''


# The site-wide bar, shared with every other section; see tools/nav/.
HEADER = '<body>\n' + NAV.render("email", "main") + '\n<main id="main">'

FOOTER = '''</main>
<footer class="site-footer">
<div class="container">
<p>Field notes by <a href="https://www.linkedin.com/in/allanninal/" rel="noopener">Allan Ni&ntilde;al</a> &middot; <a href="/">Portfolio</a> &middot; <a href="/dns/">DNS &amp; domains</a> &middot; <a href="/email/">Email &amp; deliverability</a></p>
<p class="site-footer__fine">Every script here is a starting point, not a substitute for reading your own logs. Test against a non-production identity first.</p>
</div>
</footer>
<script src="/email/assets/email.js" defer></script>
<script defer src="/assets/site-nav.js"></script>
</body>
</html>'''


def render(g: dict) -> str:
    steps = "\n".join(
        f"<h3>{esc(s['h'])}</h3>\n{s['body']}" for s in g["steps"])
    faq = "\n".join(
        f'<details class="faq-item"><summary>{esc(q)}</summary><p>{esc(a)}</p></details>'
        for q, a in g["faq"])
    related = "\n".join(
        f'<li><a href="{href}">{esc(label)}</a></li>' for href, label in g["related"])
    cites = "\n".join(
        f'<li><a href="{u}" rel="noopener nofollow" target="_blank">{esc(t)}</a></li>'
        for t, u in g["citations"])
    chips = "\n".join(f'<span class="chip">{esc(c)}</span>' for c in g["chips"])

    return f'''{head(g)}
{HEADER}
<section class="hero">
<div class="container prose">
<p class="breadcrumbs"><a href="/email/">Field notes</a> / {esc(g["category"])}</p>
<p class="eyebrow"><span class="pill pill--diag">{esc(g["pill"])}</span> {esc(g["category"])}</p>
<h1>{esc(g["h1"])}</h1>
<p class="lead">{g["lead"]}</p>
<div class="meta">
{chips}
</div>
</div>
</section>

<div class="container prose">
<div class="callout callout--note" id="short-answer">
<div class="callout__title">The short answer</div>
{g["short_answer"]}
</div>

<h2>The problem in plain words</h2>
{g["problem"]}

<h2>Why it happens</h2>
{g["why"]}

<h2>How to fix it</h2>
{steps}

<h2>How to check it worked</h2>
{g["verify"]}

<h2>The full code</h2>
<p>{g["code_intro"]}</p>
{code_block(g["py_file"], g["py"], g["js_file"], g["js"])}

<h2>Add a test</h2>
<p>{g["test_intro"]}</p>
{code_block(g["test_py_file"], g["test_py"], g["test_js_file"], g["test_js"])}

<h2>FAQ</h2>
{faq}

<h2>Related field notes</h2>
<ul>
{related}
</ul>

<h3>Citations</h3>
<ul class="citations">
{cites}
</ul>

<div class="callout callout--cta">
<div class="callout__title">Stuck on a tricky one?</div>
<p>If your sending setup is misbehaving in a way this note does not cover, <a href="https://www.linkedin.com/in/allanninal/" rel="noopener">message me on LinkedIn</a> with what you are seeing. I read every one.</p>
</div>
</div>
{FOOTER}'''


def write_all(guides: list) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for g in guides:
        d = OUT / g["slug"]
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(render(g), encoding="utf-8")
        print(f"  {g['slug']}  ({len(render(g)):,} bytes)  title[{len(g['title'])}] desc[{len(g['description'])}]")
