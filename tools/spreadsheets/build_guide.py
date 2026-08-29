#!/usr/bin/env python3
"""Guide articles for /spreadsheets/ — the pages that have no product behind them.

Why this is a separate renderer and not a flag on build_product.render():

  build_product is shaped end to end around a paid workbook. It reads BY_KEY[g["key"]]
  on its first line, prices the chips, renders a tabs table off the real .xlsx, emits a
  Product node with an Offer, and closes with two buy blocks. A guide has no key, no
  price, no tabs and nothing to offer — bending one template to serve both would have
  meant a truthy check on almost every line, and the Product schema would have had to be
  faked or conditionally dropped from a graph that is otherwise a fixed shape.

  What IS shared, deliberately: _header, _footer, the head conventions, the site
  constants and the title/description length gate — imported, not copied, so the two page
  types cannot drift apart visually.

The commercial difference matters too. A product page answers "should I buy this?". A
guide answers a question someone typed into Google at the moment their data broke, and
its job is to be correct and then offer the free kit. There is no Offer node because
nothing here is for sale, and marking up a free download as a priced Product would be
a lie to the search engines as well as the reader.

Usage: imported by build.py; not run directly.
"""
import json

from build_product import (SITE, SEC, GA, ADS, ROOT, esc, q, url_for,
                           _header, _footer, _person, table)

KIT_NAME = "Excel-Data-Cleanup-Kit.zip"
KIT = f"/{SEC}/downloads/{KIT_NAME}"
KIT_PATH = ROOT / SEC / "downloads" / KIT_NAME


def kit_kb() -> int:
    """Real size of the zip on disk, so the stated figure cannot drift from the file.

    Hard-coding it was wrong within an hour: the block said 122 KB for a 121 KB file.
    A missing kit is a hard failure rather than a 0 KB label — a download block whose
    link 404s is worse than no download block."""
    if not KIT_PATH.exists():
        raise SystemExit(f"free kit missing at {KIT_PATH} — every guide links to it.")
    return round(KIT_PATH.stat().st_size / 1024)


def dl(second: bool = False) -> str:
    """The free-download block. Stands where buy() stands on a product page.

    No email gate and no price: the file is genuinely free, so the block says so plainly
    rather than performing scarcity. `download` on the anchor makes the browser save it
    instead of navigating, and the size is stated because an unlabelled zip link is the
    kind of thing people do not click.
    """
    lead = ("Everything on this page, as a workbook you can use on your own data"
            if not second else
            "Take the workbook with you")
    return f'''<div class="buy" id="download{'-2' if second else ''}">
<h3>{esc(lead)}</h3>
<p>The <strong>Excel Data Cleanup Kit</strong> &mdash; a seven-tab workbook that finds all
nine of these faults in a pasted column and hands back a cleaned version, a five-page PDF
guide, and a short read-me. Free, no email required.</p>
<ul>
<li><strong>Excel-Data-Cleanup-Workbook-Free.xlsx</strong> &mdash; paste a column, read the diagnosis, take the cleaned output</li>
<li><strong>Excel-Data-Survival-Guide.pdf</strong> &mdash; the eight failures, the import routine that prevents them, every formula explained</li>
</ul>
<p><a class="repo-cta" href="{KIT}" download>Download the kit &mdash; free ({kit_kb()}&nbsp;KB .zip)</a></p>
<p class="lead">Plain <code>.xlsx</code>: no macros, no add-ins. Opens in Excel, Google Sheets,
Apple Numbers and LibreOffice Calc.</p>
</div>'''


def symptom_table(rows: list[list[str]]) -> str:
    return table("What you are seeing, and what actually happened",
                 ["What you see", "What actually happened", "What fixes it"], rows)


def fx(label: str, formula: str, note: str) -> str:
    """A formula with its explanation. `formula` is pre-escaped by the caller if needed."""
    return (f'<div class="code-block"><div class="code-block__bar">'
            f'<span class="code-filename">{esc(label)}</span></div>'
            f'<div class="code-pane"><pre><code>{esc(formula)}</code></pre></div></div>'
            f'<p>{note}</p>')


def _graph(cfg: dict, g: dict) -> dict:
    """Article + HowTo + FAQ + Breadcrumb. No Product and no Offer — nothing is for sale.

    The free kit is marked up as a DownloadAction target on the Article rather than as a
    zero-price Product: a Product node with price 0 renders as a shopping result and
    misrepresents what the page is.
    """
    url = url_for(g["slug"])
    img = f"{SITE}/{SEC}/assets/img/guides/{g['slug']}.png"
    nodes = [
        {"@type": "Article", "@id": url + "#article",
         "headline": g["title"], "description": g["description"], "url": url,
         "mainEntityOfPage": {"@type": "WebPage", "@id": url},
         "datePublished": cfg["date"], "dateModified": cfg["date"],
         "inLanguage": "en", "articleSection": g["category"],
         "keywords": ", ".join(g["keywords"]),
         "image": [img],
         "author": {"@id": SITE + "/#person"},
         "publisher": {"@id": SITE + "/#person"}},
        {"@type": "HowTo", "@id": url + "#howto",
         "name": g["howto_name"], "description": g["howto_desc"],
         "step": [{"@type": "HowToStep", "position": i + 1,
                   "name": s["h"], "text": s["plain"]}
                  for i, s in enumerate(g["steps"])]},
        {"@type": "FAQPage", "@id": url + "#faq",
         "mainEntity": [{"@type": "Question", "name": qq,
                         "acceptedAnswer": {"@type": "Answer", "text": aa}}
                        for qq, aa in g["faq"]]},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Spreadsheets",
             "item": f"{SITE}/{SEC}/"},
            {"@type": "ListItem", "position": 3, "name": g["h1"], "item": url}]},
        _person(),
    ]
    return {"@context": "https://schema.org", "@graph": nodes}


def _head(cfg: dict, g: dict) -> str:
    url = url_for(g["slug"])
    img = f"{SITE}/{SEC}/assets/img/guides/{g['slug']}.png"
    graph = _graph(cfg, g)
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(g["title"])}</title>
<meta name="description" content="{q(g["description"])}">
<link rel="canonical" href="{url}">
<meta name="robots" content="index, follow, max-image-preview:large">
<meta name="author" content="Allan Ni&ntilde;al">
<meta property="og:type" content="article">
<meta property="og:site_name" content="allanninal.dev">
<meta property="og:title" content="{q(g["title"])}">
<meta property="og:description" content="{q(g["description"])}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{img}">
<meta property="og:image:width" content="1280">
<meta property="og:image:height" content="800">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{q(g["title"])}">
<meta name="twitter:description" content="{q(g["description"])}">
<meta name="twitter:image" content="{img}">
<meta name="google-adsense-account" content="{ADS}">
<script async src="https://www.googletagmanager.com/gtag/js?id={GA}"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','{GA}');</script>
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={ADS}" crossorigin="anonymous"></script>
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="/{SEC}/assets/{SEC}.css">
<script type="application/ld+json">{json.dumps(graph, ensure_ascii=False, separators=(",", ":"))}</script>
</head>'''


def render(cfg: dict, g: dict) -> str:
    chips = "\n".join(f'<span class="chip">{esc(c)}</span>' for c in g["chips"])

    steps = "\n".join(
        f'<div class="step"><div class="step__n">{i + 1}</div>'
        f'<div><h3>{esc(s["h"])}</h3>{s["body"]}</div></div>'
        for i, s in enumerate(g["steps"]))

    faq = "\n".join(
        f"<details><summary>{esc(qq)}</summary><p>{esc(aa)}</p></details>"
        for qq, aa in g["faq"])

    related = "\n".join(f'<a href="/{SEC}/{s}/">{esc(l)}</a>' for s, l in g["related"])

    body = g.get("body", "")
    extra = g.get("after_steps", "")

    return f'''{_head(cfg, g)}
{_header()}
<section class="hero">
<div class="container prose">
<p class="breadcrumbs"><a href="/{SEC}/">Spreadsheets</a> / {esc(g["category"])}</p>
<p class="eyebrow"><span class="pill pill--repair">Guide</span> {esc(g["category"])}</p>
<h1>{esc(g["h1"])}</h1>
<p class="lead">{g["lead"]}</p>
<div class="meta">
{chips}
</div>
</div>
</section>

<div class="container prose">
<figure class="feature-img">
<img src="/{SEC}/assets/img/guides/{g["slug"]}.png" alt="{q(g["h1"])}"
     width="1280" height="800" loading="eager" decoding="async">
</figure>
<div class="callout callout--note" id="short-answer">
<div class="callout__title">The short answer</div>
{g["short_answer"]}
</div>

<h2>{esc(g["problem_h"])}</h2>
{g["problem"]}
{g.get("diagram_problem", "")}

{g.get("symptoms", "")}

<h2>{esc(g["howto_name"])}</h2>
{g.get("diagram_fix", "")}
{steps}
{extra}

{dl()}

<div class="depth">Below here is why it happens</div>

{body}

<h2>Questions people ask</h2>
<div class="faq">
{faq}
</div>

<h2>Related guides</h2>
<div class="related">
{related}
</div>

{dl(second=True)}
</div>
{_footer()}'''
