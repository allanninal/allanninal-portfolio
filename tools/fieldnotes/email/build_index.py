#!/usr/bin/env python3
"""Build the /email/ section index."""
import html as H
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from build_email import HEADER, FOOTER, GA, ADS, SITE, OUT   # noqa: E402
from guides_ses import GUIDES as A                            # noqa: E402
from guides_ses2 import GUIDES as B                           # noqa: E402

GUIDES = A + B
URL = f"{SITE}/email/"
TITLE = "Email Deliverability and Amazon SES Fix Guides"
DESC = ("Researched guides for email sending problems you can detect and repair with a "
        "small Python or Node.js script against the provider API.")

cards = "\n".join(f'''<a class="card" href="/email/{g["slug"]}/">
<div class="card__meta"><span class="chip chip--cat">{H.escape(g["category"])}</span><span class="chip">{H.escape(g["pill"])}</span></div>
<h3>{H.escape(g["h1"][0].upper() + g["h1"][1:])}</h3>
<p>{H.escape(g["description"])}</p>
</a>''' for g in GUIDES)

graph = {
    "@context": "https://schema.org",
    "@graph": [
        {"@type": "CollectionPage", "@id": URL, "url": URL, "name": TITLE,
         "description": DESC,
         "isPartOf": {"@type": "WebSite", "name": "allanninal.dev", "url": SITE + "/"},
         "hasPart": [{"@type": "TechArticle", "headline": g["title"],
                      "url": f"{SITE}/email/{g['slug']}/"} for g in GUIDES]},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Email field notes", "item": URL}]},
    ],
}

page = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{TITLE}</title>
<meta name="description" content="{DESC}">
<link rel="canonical" href="{URL}">
<meta name="robots" content="index, follow">
<meta name="author" content="Allan Ni&ntilde;al">
<meta property="og:type" content="website">
<meta property="og:title" content="{TITLE}">
<meta property="og:description" content="{DESC}">
<meta property="og:url" content="{URL}">
<meta property="og:image" content="{SITE}/og-image.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{TITLE}">
<meta name="twitter:description" content="{DESC}">
<meta name="twitter:image" content="{SITE}/og-image.png">
<meta name="google-adsense-account" content="{ADS}">
<script async src="https://www.googletagmanager.com/gtag/js?id={GA}"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','{GA}');</script>
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={ADS}" crossorigin="anonymous"></script>
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="/email/assets/email.css">
<script type="application/ld+json">{json.dumps(graph, ensure_ascii=False, separators=(",", ":"))}</script>
</head>
{HEADER}
<section class="hero">
<div class="container prose">
<p class="eyebrow">Field notes</p>
<h1>Email deliverability fix guides</h1>
<p class="lead">Sending problems that look like nothing is wrong. The API returns a message ID, the logs say success, and the mail never arrives. Each note takes one of those, explains what is actually happening, and gives you a script in Python and Node.js that detects it &mdash; and repairs it where the API allows.</p>
<div class="meta">
<span class="chip">Python and Node.js</span>
<span class="chip">Amazon SES v2 API</span>
<span class="chip">Detect, then repair</span>
<span class="chip">Tests included</span>
</div>
</div>
</section>

<div class="container prose">
<div class="callout callout--note">
<div class="callout__title">Where this sits next to /dns/</div>
<p><a href="/dns/">DNS &amp; domains</a> covers the record layer &mdash; SPF syntax, DKIM selectors, DMARC policy, MX targets. This section covers the layer above it, where the sending platform's own API is what finds and fixes the problem. If your records are wrong, start there. If your records are right and mail still is not arriving, start here.</p>
</div>

<h2>Amazon SES</h2>
<div class="cards">
{cards}
</div>

<div class="callout callout--cta">
<div class="callout__title">Something not covered here?</div>
<p>These are the ones I keep hitting. If your sending setup is broken in a way none of them describes, <a href="https://www.linkedin.com/in/allanninal/" rel="noopener">tell me on LinkedIn</a> &mdash; it is usually how the next note gets written.</p>
</div>
</div>
{FOOTER}'''

OUT.mkdir(parents=True, exist_ok=True)
(OUT / "index.html").write_text(page, encoding="utf-8")
print(f"  email/index.html  ({len(page):,} bytes)  {len(GUIDES)} cards  title[{len(TITLE)}] desc[{len(DESC)}]")
