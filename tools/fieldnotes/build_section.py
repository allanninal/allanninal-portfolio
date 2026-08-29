#!/usr/bin/env python3
"""Generate a field-notes section: one page per problem, plus the section index.

Parameterised by section so /email/, /aws/ and whatever comes next share one
generator. The eight ecommerce sections were each built separately and drifted —
different title lengths, some with JSON-LD and some without — which is the thing
this avoids.

Every guide is a problem you can DETECT and REPAIR with a small script against an
API. That is the test for inclusion. Anything fixable only by clicking in a console
is covered to the point where the script tells you that is what you need, and no
further.
"""
import html as H
import json
import sys
from pathlib import Path

from extras import feature as _feature, flow as _flow

# The site header is shared by every page on allanninal.dev; see tools/nav/.
# Generating it here rather than writing markup means a rebuilt section can no
# longer drift into having its own menu, which is how the site ended up with a
# different bar on nearly every page.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "nav"))
import header as NAV

SITE = "https://www.allanninal.dev"
GA = "G-DLRBEQ85ZN"
ADS = "ca-pub-3474747237489350"
ROOT = Path.home() / "Projects/allanninal.dev"


def esc(t: str) -> str:
    return H.escape(t, quote=False)


def code_block(fn_py: str, py: str, fn_js: str, js: str) -> str:
    return f'''<div class="code-block" data-code>
<div class="code-block__bar">
<button class="code-tab" data-lang="python" aria-selected="true" type="button">Python</button>
<button class="code-tab" data-lang="node" aria-selected="false" type="button">Node.js</button>
<button class="code-block__copy" type="button">Copy</button>
</div>
<div class="code-pane" data-lang="python" data-active="true">
<div class="code-filename">{fn_py}</div>
<pre><code class="language-python">{H.escape(py)}</code></pre>
</div>
<div class="code-pane" data-lang="node">
<div class="code-filename">{fn_js}</div>
<pre><code class="language-javascript">{H.escape(js)}</code></pre>
</div>
</div>'''


def _header(cfg: dict) -> str:
    """The site-wide bar. `cfg["nav"]` is no longer read: the canonical header
    carries navigation for the whole site, not one section's shortlist."""
    return "<body>\n" + NAV.render(cfg["section"], "main") + '\n<main id="main">'


def _footer(cfg: dict) -> str:
    sec = cfg["section"]
    return f'''</main>
<footer class="site-footer">
<div class="container">
<p>Field notes by <a href="https://www.linkedin.com/in/allanninal/" rel="noopener">Allan Ni&ntilde;al</a> &middot; <a href="/">Portfolio</a> &middot; <a href="/dns/">DNS &amp; domains</a> &middot; <a href="/email/">Email &amp; SES</a> &middot; <a href="/aws/">AWS cost</a></p>
<p class="site-footer__fine">{cfg["footer_note"]}</p>
</div>
</footer>
<script src="/{sec}/assets/{sec}.js" defer></script>
<script defer src="/assets/site-nav.js"></script>
</body>
</html>'''


def _head(cfg: dict, g: dict) -> str:
    sec = cfg["section"]
    url = f"{SITE}/{sec}/{g['slug']}/"
    graph = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "TechArticle", "@id": url + "#article",
             "headline": g["title"], "description": g["description"], "url": url,
             "mainEntityOfPage": {"@type": "WebPage", "@id": url},
             "datePublished": cfg["date"], "dateModified": cfg["date"],
             "inLanguage": "en", "articleSection": g["category"],
             "keywords": ", ".join(g["keywords"]),
             "author": {"@id": SITE + "/#person"},
             "publisher": {"@id": SITE + "/#person"},
             "proficiencyLevel": "Intermediate", "dependencies": g["deps"],
             "citation": [c[1] for c in g["citations"]]},
            {"@type": "Person", "@id": SITE + "/#person", "name": "Allan Niñal",
             "jobTitle": "AI and Software Engineer", "url": SITE + "/",
             "sameAs": ["https://www.linkedin.com/in/allanninal/",
                        "https://github.com/allanninal"]},
            {"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Field notes",
                 "item": f"{SITE}/{sec}/"},
                {"@type": "ListItem", "position": 2, "name": g["category"],
                 "item": f"{SITE}/{sec}/"},
                {"@type": "ListItem", "position": 3, "name": g["title"], "item": url}]},
            {"@type": "FAQPage", "@id": url + "#faq", "mainEntity": [
                {"@type": "Question", "name": q,
                 "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in g["faq"]]},
        ],
    }
    q = lambda s: H.escape(s, quote=True)
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(g["title"])}</title>
<meta name="description" content="{q(g["description"])}">
<link rel="canonical" href="{url}">
<meta name="robots" content="index, follow">
<meta name="author" content="Allan Ni&ntilde;al">
<meta property="og:type" content="article">
<meta property="og:title" content="{q(g["title"])}">
<meta property="og:description" content="{q(g["description"])}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}/og-image.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{q(g["title"])}">
<meta name="twitter:description" content="{q(g["description"])}">
<meta name="twitter:image" content="{SITE}/og-image.png">
<meta name="google-adsense-account" content="{ADS}">
<script async src="https://www.googletagmanager.com/gtag/js?id={GA}"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','{GA}');</script>
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={ADS}" crossorigin="anonymous"></script>
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="/{sec}/assets/{sec}.css">
<link rel="stylesheet" href="/assets/site-nav.css">\n<link rel="stylesheet" href="/assets/site-mobile.css">
<script type="application/ld+json">{json.dumps(graph, ensure_ascii=False, separators=(",", ":"))}</script>
</head>'''


def render(cfg: dict, g: dict) -> str:
    sec = cfg["section"]
    steps = "\n".join(f"<h3>{esc(s['h'])}</h3>\n{s['body']}" for s in g["steps"])
    faq = "\n".join(
        f'<details class="faq-item"><summary>{esc(q)}</summary><p>{esc(a)}</p></details>'
        for q, a in g["faq"])
    related = "\n".join(f'<li><a href="{h}">{esc(l)}</a></li>' for h, l in g["related"])
    cites = "\n".join(
        f'<li><a href="{u}" rel="noopener nofollow" target="_blank">{esc(t)}</a></li>'
        for t, u in g["citations"])
    chips = "\n".join(f'<span class="chip">{esc(c)}</span>' for c in g["chips"])

    return f'''{_head(cfg, g)}
{_header(cfg)}
<section class="hero">
<div class="container prose">
<p class="breadcrumbs"><a href="/{sec}/">Field notes</a> / {esc(g["category"])}</p>
<p class="eyebrow"><span class="pill pill--diag">{esc(g["pill"])}</span> {esc(g["category"])}</p>
<h1>{esc(g["h1"])}</h1>
<p class="lead">{g["lead"]}</p>
<div class="meta">
{chips}
</div>
</div>
</section>

<div class="container prose">
{_feature(cfg, g)}
<div class="callout callout--note" id="short-answer">
<div class="callout__title">The short answer</div>
{g["short_answer"]}
</div>

<h2>The problem in plain words</h2>
{g["problem"]}
{g.get("diagram_problem", "")}

<h2>Why it happens</h2>
{g["why"]}
{_flow(g)}
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

<h3>Sources</h3>
<p class="sources-note">Every figure in this note is traced to one of these. Prices are
list rates and change &mdash; check them for your own region before acting.</p>
<ul class="citations">
{cites}
</ul>

<div class="callout callout--cta">
<div class="callout__title">Stuck on a tricky one?</div>
<p>If your setup is misbehaving in a way this note does not cover, <a href="https://www.linkedin.com/in/allanninal/" rel="noopener">message me on LinkedIn</a> with what you are seeing.</p>
</div>
</div>
{_footer(cfg)}'''


def render_index(cfg: dict, guides: list) -> str:
    sec = cfg["section"]
    url = f"{SITE}/{sec}/"
    cards = "\n".join(f'''<a class="card" href="/{sec}/{g["slug"]}/">
<div class="card__meta"><span class="chip chip--cat">{esc(g["category"])}</span><span class="chip">{esc(g["pill"])}</span></div>
<h3>{esc(g["h1"][0].upper() + g["h1"][1:])}</h3>
<p>{esc(g["description"])}</p>
</a>''' for g in guides)
    graph = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "CollectionPage", "@id": url, "url": url, "name": cfg["index_title"],
             "description": cfg["index_desc"],
             "isPartOf": {"@type": "WebSite", "name": "allanninal.dev", "url": SITE + "/"},
             "hasPart": [{"@type": "TechArticle", "headline": g["title"],
                          "url": f"{SITE}/{sec}/{g['slug']}/"} for g in guides]},
            {"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
                {"@type": "ListItem", "position": 2, "name": cfg["index_title"], "item": url}]},
        ],
    }
    q = lambda s: H.escape(s, quote=True)
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(cfg["index_title"])}</title>
<meta name="description" content="{q(cfg["index_desc"])}">
<link rel="canonical" href="{url}">
<meta name="robots" content="index, follow">
<meta name="author" content="Allan Ni&ntilde;al">
<meta property="og:type" content="website">
<meta property="og:title" content="{q(cfg["index_title"])}">
<meta property="og:description" content="{q(cfg["index_desc"])}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}/og-image.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{q(cfg["index_title"])}">
<meta name="twitter:description" content="{q(cfg["index_desc"])}">
<meta name="twitter:image" content="{SITE}/og-image.png">
<meta name="google-adsense-account" content="{ADS}">
<script async src="https://www.googletagmanager.com/gtag/js?id={GA}"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','{GA}');</script>
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={ADS}" crossorigin="anonymous"></script>
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="/{sec}/assets/{sec}.css">
<link rel="stylesheet" href="/assets/site-nav.css">\n<link rel="stylesheet" href="/assets/site-mobile.css">
<script type="application/ld+json">{json.dumps(graph, ensure_ascii=False, separators=(",", ":"))}</script>
</head>
{_header(cfg)}
<section class="hero">
<div class="container prose">
<p class="eyebrow">Field notes</p>
<h1>{esc(cfg["index_h1"])}</h1>
<p class="lead">{cfg["index_lead"]}</p>
<div class="meta">
{"".join(f'<span class="chip">{esc(c)}</span>' for c in cfg["index_chips"])}
</div>
</div>
</section>

<div class="container prose">
<div class="callout callout--note">
<div class="callout__title">{cfg["scope_title"]}</div>
{cfg["scope_body"]}
</div>

<h2>{esc(cfg["group_heading"])}</h2>
<div class="cards">
{cards}
</div>

<div class="callout callout--cta">
<div class="callout__title">Something not covered here?</div>
<p>These are the ones I keep hitting. If yours is broken in a way none of them describes, <a href="https://www.linkedin.com/in/allanninal/" rel="noopener">tell me on LinkedIn</a> &mdash; it is usually how the next note gets written.</p>
</div>
</div>
{_footer(cfg)}'''


def build(cfg: dict, guides: list) -> None:
    out = ROOT / cfg["section"]
    out.mkdir(parents=True, exist_ok=True)
    for g in guides:
        d = out / g["slug"]
        d.mkdir(parents=True, exist_ok=True)
        page = render(cfg, g)
        d.joinpath("index.html").write_text(page, encoding="utf-8")
        flags = []
        if len(g["title"]) > 65:
            flags.append(f"TITLE {len(g['title'])}")
        if len(g["description"]) > 160:
            flags.append(f"DESC {len(g['description'])}")
        print(f"  {'FAIL' if flags else 'ok  '} {g['slug']:46s} {len(page):7,}b "
              f"t[{len(g['title'])}] d[{len(g['description'])}] {' '.join(flags)}")
    idx = render_index(cfg, guides)
    out.joinpath("index.html").write_text(idx, encoding="utf-8")
    print(f"  ok   index.html {' ':43s} {len(idx):7,}b "
          f"t[{len(cfg['index_title'])}] d[{len(cfg['index_desc'])}]")
