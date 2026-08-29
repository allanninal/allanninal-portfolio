#!/usr/bin/env python3
"""Page and index templates for /spreadsheets/.

A sibling of tools/fieldnotes/build_section.py rather than an extension of it.
The field-notes template is shaped for a code guide — tabbed Python/Node blocks,
an "Add a test" section, TechArticle schema with citations and dependencies. A
product article needs a different body and different structured data, and
bending one template to do both would have made both worse.

What IS shared, deliberately: the head conventions, the site constants, the
title/description length gate, and diagrams.py — imported unchanged, so the two
sections cannot drift apart visually.

The page is built in two halves. Above `.depth` everything is plain language:
the problem as a story, a diagram, a table of what the mistake costs. Below it
is the arithmetic, the verifier result and the comparison a professional buyer
needs before spending $59-$119. Neither half works alone.
"""
import html as H
import json
import sys
from pathlib import Path

from catalog import BY_KEY

# The site header is shared by every page on allanninal.dev; see tools/nav/.
# Generating it here rather than writing markup means a rebuilt section can no
# longer drift into having its own menu, which is how the site ended up with a
# different bar on nearly every page.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "nav"))
import header as NAV

SITE = "https://www.allanninal.dev"
SEC = "spreadsheets"
GA = "G-DLRBEQ85ZN"
ADS = "ca-pub-3474747237489350"
ROOT = Path.home() / "Projects/allanninal.dev"
STORE = "https://thecalmdeskco.gumroad.com"
BRAND = "The Calm Desk"


def esc(t) -> str:
    return H.escape(str(t), quote=False)


def q(t) -> str:
    return H.escape(str(t), quote=True)


def url_for(slug: str) -> str:
    return f"{SITE}/{SEC}/{slug}/"


# --------------------------------------------------------------------------- #
# blocks
# --------------------------------------------------------------------------- #

def table(caption: str, head: list, rows: list[list], foot: list | None = None) -> str:
    """A data table. `head` cells ending in '#' are right-aligned number columns.

    Cells may be a plain string, or a (text, css_class) pair.
    """
    aligns = ["num" if str(h).endswith("#") else "" for h in head]
    ths = "".join(f'<th class="{a}">{esc(str(h).rstrip("#"))}</th>'
                  for h, a in zip(head, aligns))

    def cell(v, align, tag="td"):
        cls = align
        if isinstance(v, tuple):
            v, extra = v
            cls = f"{align} {extra}".strip()
        return f'<{tag} class="{cls}">{v}</{tag}>' if cls else f"<{tag}>{v}</{tag}>"

    body = "".join(
        "<tr>" + "".join(cell(v, a) for v, a in zip(r, aligns)) + "</tr>" for r in rows)
    tfoot = ""
    if foot:
        tfoot = "<tfoot><tr>" + "".join(
            cell(v, a) for v, a in zip(foot, aligns)) + "</tr></tfoot>"
    # Four or more columns will not fit the prose column, so it is told to
    # break out on wide screens instead of being squeezed to illegibility.
    wide = " tbl--wide" if len(head) >= 4 else ""
    return (f'<div class="tbl{wide}"><table><caption>{esc(caption)}</caption>'
            f"<thead><tr>{ths}</tr></thead><tbody>{body}</tbody>{tfoot}</table></div>")


def shot(g: dict, p: dict) -> str:
    """The workbook screenshot — a real render of a real tab, not a mockup."""
    sheet = g.get("shot_tab") or p["tabs"][1]
    return (f'<figure class="shot">\n'
            f'<img src="/{SEC}/assets/img/{p["key"]}/tab.png" '
            f'alt="{q(g["shot_alt"])}" width="1200" height="620" '
            f'loading="lazy" decoding="async">\n'
            f'<figcaption>The <strong>{esc(sheet)}</strong> tab of the workbook you '
            # shot_note carries entities like &minus; and inline <strong>, so it is
            # HTML like every other body field. Escaping it printed "&minus;$115,000".
            f'download, with the sample data it ships with. {g["shot_note"]}'
            f"</figcaption>\n</figure>")


def cover(g: dict, p: dict) -> str:
    return (f'<figure class="feature-img">\n'
            f'<img src="/{SEC}/assets/img/{p["key"]}/cover.png" '
            f'alt="{q(g["h1"])} — Excel and Google Sheets workbook" '
            f'width="1280" height="800" loading="eager" decoding="async">\n</figure>')


def tabs_table(g: dict, p: dict) -> str:
    """Every tab in the workbook, one plain sentence each.

    The tab list comes from catalog.py — read out of the shipped .xlsx — so the
    page cannot claim a tab the file does not have. A missing blurb is a build
    error rather than a silently short table.
    """
    blurbs = g["tabs"]
    missing = [t for t in p["tabs"] if t not in blurbs]
    extra = [t for t in blurbs if t not in p["tabs"]]
    if missing or extra:
        raise SystemExit(
            f"{g['slug']}: tab blurbs do not match the workbook.\n"
            f"  in the .xlsx but undescribed: {missing}\n"
            f"  described but not in the .xlsx: {extra}")
    rows = [[(esc(t), "tab-name"), blurbs[t]] for t in p["tabs"]]
    return table(f"All {len(p['tabs'])} tabs in {p['gumroad_name'].split(' — ')[0]}",
                 ["Tab", "What it does"], rows)


def buy(g: dict, p: dict, *, second: bool = False) -> str:
    """Price and Gumroad link, emitted from catalog.py in one place.

    Both CTAs on a page render through here, so the price shown and the product
    linked can never disagree with each other or with Gumroad.
    """
    items = "".join(f"<li>{b}</li>" for b in g["includes"])
    head = ("Get the workbook" if not second
            else f"Ready to stop doing this by hand?")
    return f'''<div class="buy">
<h3>{esc(head)}</h3>
<p class="price">${p["price"]} <small>one-off &middot; no subscription</small></p>
<ul>
{items}
</ul>
<a class="cta" href="{p["url"]}" target="_blank" rel="noopener noreferrer">Get it on Gumroad &rarr;</a>
<p class="fine">Instant download from Gumroad. {esc(g["fine"])}</p>
</div>'''


def open_in(g: dict, p: dict) -> str:
    """How to open the file in Excel, Google Sheets, Numbers or LibreOffice.

    The same four apps for every product, but the compatibility sentence is
    generated from the functions that workbook actually calls (catalog.py reads
    them out of the formulas). That is the difference between "works
    everywhere", which is a claim, and naming the nine statistical functions
    this particular file uses and where each one exists, which is checkable.
    """
    notable = p["notable_functions"]
    if notable:
        names = ", ".join(notable[:-1]) + " and " + notable[-1] if len(notable) > 1 \
            else notable[0]
        note = (f"<p>This one leans on {esc(names)} &mdash; the functions people most "
                f"often worry about losing in another app. All of them exist in "
                f"Excel, Google Sheets, Apple Numbers and LibreOffice Calc, so the "
                f"file works the same in all four.</p>")
    else:
        note = ("<p>Every formula in this workbook uses ordinary functions &mdash; "
                "SUM, IF, INDEX, MATCH and their relatives. Nothing here is "
                "Excel-only.</p>")

    rows = [
        [("Microsoft Excel", "tab-name"),
         "Double-click the file. Excel 2016 and later, and Microsoft 365, on Windows or Mac. "
         "Nothing to enable and nothing to install."],
        [("Google Sheets", "tab-name"),
         "Go to Google Drive, click <strong>New &rarr; File upload</strong> and pick the "
         ".xlsx. Then double-click it in Drive and choose <strong>Open with &rarr; Google "
         "Sheets</strong>. To keep a native copy, use <strong>File &rarr; Save as Google "
         "Sheets</strong>. Formatting and formulas both carry over."],
        [("Apple Numbers (Mac, iPad, iPhone)", "tab-name"),
         "Numbers opens .xlsx directly &mdash; double-click it, or in Numbers use "
         "<strong>File &rarr; Open</strong> and select the file. Numbers converts it on "
         "open and will list anything it changed. To send a copy back to someone on Excel, "
         "use <strong>File &rarr; Export To &rarr; Excel</strong>."],
        [("LibreOffice Calc", "tab-name"),
         "Free, and opens the file as-is on Windows, Mac and Linux. This is what I use to "
         "recalculate every workbook when I check the maths, so it is the app these files "
         "are tested hardest in."],
    ]
    return (f'<h2>Opening it in Excel, Google Sheets or Numbers</h2>\n'
            f'<p>It is one <code>.xlsx</code> file. There are no macros, no add-ins and '
            f'nothing to install, which is what makes it portable &mdash; a macro-driven '
            f'template would be Excel-only.</p>\n'
            + table("Where the file opens, and how", ["App", "How to open it"], rows)
            + "\n" + note)


# --------------------------------------------------------------------------- #
# head
# --------------------------------------------------------------------------- #

def _person() -> dict:
    return {"@type": "Person", "@id": SITE + "/#person", "name": "Allan Niñal",
            "jobTitle": "AI and Software Engineer", "url": SITE + "/",
            "sameAs": ["https://www.linkedin.com/in/allanninal/",
                       "https://github.com/allanninal"]}


def _graph(cfg: dict, g: dict, p: dict) -> dict:
    url = url_for(g["slug"])
    imgs = [f"{SITE}/{SEC}/assets/img/{p['key']}/cover.png",
            f"{SITE}/{SEC}/assets/img/{p['key']}/tab.png"]
    return {
        "@context": "https://schema.org",
        "@graph": [
            # No aggregateRating and no review anywhere: these products have no
            # sales yet, so there is nothing real to mark up and inventing it
            # would be fabricated social proof.
            {"@type": "Product", "@id": url + "#product",
             "name": p["gumroad_name"], "description": p["summary"],
             "image": imgs, "category": g["category"],
             "brand": {"@type": "Brand", "name": BRAND},
             "url": url,
             "offers": {"@type": "Offer", "price": str(p["price"]),
                        "priceCurrency": "USD",
                        "availability": "https://schema.org/InStock",
                        "url": p["url"],
                        "seller": {"@type": "Organization", "name": BRAND,
                                   "url": STORE + "/"}}},
            {"@type": "Article", "@id": url + "#article",
             "headline": g["title"], "description": g["description"], "url": url,
             "mainEntityOfPage": {"@type": "WebPage", "@id": url},
             "datePublished": cfg["date"], "dateModified": cfg["date"],
             "inLanguage": "en", "articleSection": g["category"],
             "keywords": ", ".join(g["keywords"]),
             "image": imgs,
             "author": {"@id": SITE + "/#person"},
             "publisher": {"@id": SITE + "/#person"},
             "about": {"@id": url + "#product"}},
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
        ],
    }


def _head(cfg: dict, g: dict, p: dict) -> str:
    url = url_for(g["slug"])
    img = f"{SITE}/{SEC}/assets/img/{p['key']}/cover.png"
    graph = _graph(cfg, g, p)
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
<link rel="stylesheet" href="/assets/site-nav.css">\n<link rel="stylesheet" href="/assets/site-mobile.css">
<script type="application/ld+json">{json.dumps(graph, ensure_ascii=False, separators=(",", ":"))}</script>
</head>'''


def _header() -> str:
    """The site-wide bar, shared with every other section; see tools/nav/."""
    return "<body>\n" + NAV.render(SEC, "main") + '\n<main id="main">'


def _footer() -> str:
    return f'''</main>
<footer class="site-footer">
<div class="container">
<p>Spreadsheets by <a href="https://www.linkedin.com/in/allanninal/" rel="noopener">Allan Ni&ntilde;al</a> &middot; <a href="/">Portfolio</a> &middot; <a href="/{SEC}/">All spreadsheets</a> &middot; <a href="/templates/">Templates</a> &middot; <a href="{STORE}/" target="_blank" rel="noopener noreferrer">The Calm Desk on Gumroad</a></p>
<p class="site-footer__fine">Every workbook is a one-off purchase with free lifetime updates. Prices in USD. Excel 2016 or later, Microsoft 365, LibreOffice Calc, or Google Sheets &mdash; no add-ins and no macros.</p>
</div>
</footer>
<script src="/{SEC}/assets/{SEC}.js" defer></script>
<script defer src="/assets/site-nav.js"></script>
</body>
</html>'''


# --------------------------------------------------------------------------- #
# article
# --------------------------------------------------------------------------- #

def render(cfg: dict, g: dict) -> str:
    p = BY_KEY[g["key"]]

    chips = [f"${p['price']} one-off", f"{len(p['tabs'])} tabs",
             "Excel + Google Sheets"] + g.get("chips", [])
    chip_html = "\n".join(f'<span class="chip">{esc(c)}</span>' for c in chips)

    steps = "\n".join(
        f'<div class="step"><div class="step__n">{i + 1}</div>'
        f'<div><h3>{esc(s["h"])}</h3>{s["body"]}</div></div>'
        for i, s in enumerate(g["steps"]))

    faq = "\n".join(
        f"<details><summary>{esc(qq)}</summary><p>{esc(aa)}</p></details>"
        for qq, aa in g["faq"])

    related = "\n".join(f'<a href="/{SEC}/{s}/">{esc(l)}</a>' for s, l in g["related"])

    return f'''{_head(cfg, g, p)}
{_header()}
<section class="hero">
<div class="container prose">
<p class="breadcrumbs"><a href="/{SEC}/">Spreadsheets</a> / {esc(g["category"])}</p>
<p class="eyebrow"><span class="pill pill--diag">{esc(g["pill"])}</span> {esc(g["category"])}</p>
<h1>{esc(g["h1"])}</h1>
<p class="lead">{g["lead"]}</p>
<div class="meta">
{chip_html}
</div>
</div>
</section>

<div class="container prose">
{cover(g, p)}
<div class="callout callout--note" id="short-answer">
<div class="callout__title">The short answer</div>
{g["short_answer"]}
</div>

<h2>{esc(g["problem_h"])}</h2>
{g["problem"]}
{g.get("diagram_problem", "")}

<h2>{esc(g["cost_h"])}</h2>
{g["cost_intro"]}
{g["cost_table"]}
{g.get("cost_after", "")}

<h2>{esc(g["why_h"])}</h2>
{g["why"]}
{g.get("diagram_fix", "")}

<h2>{esc(g["howto_name"])}</h2>
{steps}

<h2>What is inside the file</h2>
{g["inside_intro"]}
{tabs_table(g, p)}
{shot(g, p)}

{open_in(g, p)}

{buy(g, p)}

<div class="depth">Below here is the arithmetic</div>

<h2>{esc(g["math_h"])}</h2>
{g["math"]}

<h2>How I know the numbers are right</h2>
{g["proof"]}

<h2>{esc(g["versus_h"])}</h2>
{g["versus_table"]}

<h2>Questions people ask before buying</h2>
<div class="faq">
{faq}
</div>

<h2>Related spreadsheets</h2>
<div class="related">
{related}
</div>

{buy(g, p, second=True)}
</div>
{_footer()}'''


# --------------------------------------------------------------------------- #
# index
# --------------------------------------------------------------------------- #

def render_index(cfg: dict, guides: list, articles: list | None = None) -> str:
    url = f"{SITE}/{SEC}/"
    groups: dict[str, list] = {}
    for g in guides:
        groups.setdefault(g["group"], []).append(g)

    products_block, guides_block, kits_block, soon_block = [], [], [], []

    # Travels with the paid products, because that is what it is about.
    products_block.append(
        f'<div class="callout callout--note">'
        f'<div class="callout__title">{esc(cfg["scope_title"])}</div>'
        f'{cfg["scope_body"]}</div>')

    sections = products_block
    for name in cfg["group_order"]:
        gs = groups.get(name, [])
        if not gs:
            continue
        cards = "\n".join(f'''<a class="card" href="/{SEC}/{g["slug"]}/">
<div class="card__meta"><span class="chip chip--cat">{esc(g["category"])}</span></div>
<h3>{esc(g["card_title"])}</h3>
<p>{esc(g["card_blurb"])}</p>
<div class="card__foot"><span class="card__price">${BY_KEY[g["key"]]["price"]}</span>
<span class="card__tabs">{len(BY_KEY[g["key"]]["tabs"])} tabs &middot; Excel + Sheets</span></div>
</a>''' for g in gs)
        sections.append(f'<h2>{esc(name)}</h2>\n<p>{esc(cfg["group_blurb"][name])}</p>\n'
                        f'<div class="cards">\n{cards}\n</div>')

    # Guide articles. Same card markup, but no price and no tab count — there is nothing
    # to buy, so a price chip would be a lie. The foot carries "Free guide" instead, which
    # is also the honest thing to show a reader scanning the index.
    articles = articles or []
    sections = guides_block
    for name in cfg.get("guide_group_order", []):
        gs = [a for a in articles if a["group"] == name]
        if not gs:
            continue
        cards = "\n".join(f'''<a class="card" href="/{SEC}/{a["slug"]}/">
<div class="card__meta"><span class="chip chip--cat">{esc(a["category"])}</span></div>
<h3>{esc(a["card_title"])}</h3>
<p>{esc(a["card_blurb"])}</p>
<div class="card__foot"><span class="card__price">Free</span>
<span class="card__tabs">Guide &middot; free workbook</span></div>
</a>''' for a in gs)
        sections.append(f'<h2>{esc(name)}</h2>\n<p>{esc(cfg["guide_group_blurb"][name])}</p>\n'
                        f'<div class="cards">\n{cards}\n</div>')

    # Free kits. Each is a zip on this domain, never a Gumroad product: a $0 listing
    # burns a create slot from the 10-per-24h quota and returns nothing. Where a paid
    # edition already exists but is not published, the card says so as INERT TEXT —
    # never a link, because a button that goes nowhere is worse than no button.
    sections = kits_block
    for group in cfg.get("kit_groups", []):
        cards = []
        for k in group["kits"]:
            soon = ""
            if k.get("pro"):
                soon = (f'<div class="card__soon"><span class="pill pill--soon">Pro coming soon</span>'
                        f'<span>{esc(k["pro"]["name"])}</span></div>')
            cards.append(
                f'<div class="card card--kit">'
                f'<div class="card__meta"><span class="chip chip--cat">{esc(k["audience"])}</span></div>'
                f'<h3>{esc(k["name"])}</h3><p>{esc(k["blurb"])}</p>{soon}'
                f'<div class="card__foot">'
                f'<a class="card__dl" href="/{SEC}/downloads/{esc(k["zip"])}" download>Download free</a>'
                f'<span class="card__tabs">{len(k["tabs"])} tabs &middot; Excel + Sheets</span></div>'
                f'</div>')
        sections.append(f'<h2>{esc(group["title"])}</h2>\n<p>{esc(group["blurb"])}</p>\n'
                        f'<div class="cards">\n' + "\n".join(cards) + '\n</div>')

    # The Pro edition that does not exist yet. Stated as coming soon rather than omitted,
    # because the free workbook's read-me already tells buyers it is being built — and a
    # promise made in a download should be visible on the site too.
    sections = soon_block
    if cfg.get("soon"):
        s_ = cfg["soon"]
        sections.append(
            f'<h2>{esc(s_["group"])}</h2>\n<p>{esc(s_["blurb"])}</p>\n'
            f'<div class="cards">\n<div class="card card--soon">'
            f'<div class="card__meta"><span class="pill pill--soon">In development</span></div>'
            f'<h3>{esc(s_["title"])}</h3><p>{esc(s_["body"])}</p>'
            f'<div class="card__foot"><span class="card__tabs">No date promised</span></div>'
            f'</div>\n</div>')

    # Section order is configuration, not the order the code happens to build things in.
    # The page opens with what costs the reader nothing and closes with the ask; putting
    # the paid products first buried the free downloads at 82% page depth, where nobody
    # scrolls (measured 2026-08-29: the free block began at y=8868 of 10,759px).
    blocks = {"kits": kits_block, "guides": guides_block,
              "products": products_block, "soon": soon_block}
    order = cfg.get("section_order", ["products", "guides", "kits", "soon"])
    missing = set(blocks) - set(order)
    if missing:
        raise SystemExit(f"section_order omits {missing} — those sections would vanish "
                         f"silently from the page.")
    sections = [x for key in order for x in blocks[key]]

    graph = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "CollectionPage", "@id": url, "url": url,
             "name": cfg["index_title"], "description": cfg["index_desc"],
             "isPartOf": {"@type": "WebSite", "name": "allanninal.dev",
                          "url": SITE + "/"},
             "hasPart": [{"@type": "Product", "name": BY_KEY[g["key"]]["gumroad_name"],
                          "url": url_for(g["slug"]),
                          "offers": {"@type": "Offer",
                                     "price": str(BY_KEY[g["key"]]["price"]),
                                     "priceCurrency": "USD",
                                     "availability": "https://schema.org/InStock",
                                     "url": BY_KEY[g["key"]]["url"]}}
                         for g in guides]},
            {"@type": "ItemList", "@id": url + "#list",
             "numberOfItems": len(guides) + len(articles),
             "itemListElement": [{"@type": "ListItem", "position": i + 1,
                                  "name": x["card_title"], "url": url_for(x["slug"])}
                                 for i, x in enumerate(list(guides) + list(articles))]},
            {"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
                {"@type": "ListItem", "position": 2, "name": "Spreadsheets",
                 "item": url}]},
            _person(),
        ],
    }
    # The featured image. Regenerated every build from live counts (see build.py), so it
    # cannot drift the way a hand-made graphic would.
    hero_img = (f'<figure class="feature-img">\n'
                f'<img src="/{SEC}/assets/img/guides/index.png" '
                f'alt="Spreadsheets that do the part everyone gets wrong — '
                f'free workbooks and guides for Excel and Google Sheets" '
                f'width="1280" height="800" loading="eager" decoding="async">\n</figure>')
    body = hero_img + "\n\n" + "\n\n".join(sections)
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(cfg["index_title"])}</title>
<meta name="description" content="{q(cfg["index_desc"])}">
<link rel="canonical" href="{url}">
<meta name="robots" content="index, follow, max-image-preview:large">
<meta name="author" content="Allan Ni&ntilde;al">
<meta property="og:type" content="website">
<meta property="og:site_name" content="allanninal.dev">
<meta property="og:title" content="{q(cfg["index_title"])}">
<meta property="og:description" content="{q(cfg["index_desc"])}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}/{SEC}/assets/img/guides/index.png">
<meta property="og:image:width" content="1280">
<meta property="og:image:height" content="800">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{q(cfg["index_title"])}">
<meta name="twitter:description" content="{q(cfg["index_desc"])}">
<meta name="twitter:image" content="{SITE}/{SEC}/assets/img/guides/index.png">
<meta name="google-adsense-account" content="{ADS}">
<script async src="https://www.googletagmanager.com/gtag/js?id={GA}"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','{GA}');</script>
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={ADS}" crossorigin="anonymous"></script>
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="/{SEC}/assets/{SEC}.css">
<link rel="stylesheet" href="/assets/site-nav.css">\n<link rel="stylesheet" href="/assets/site-mobile.css">
<script type="application/ld+json">{json.dumps(graph, ensure_ascii=False, separators=(",", ":"))}</script>
</head>
{_header()}
<section class="hero">
<div class="container prose">
<p class="eyebrow">Spreadsheets</p>
<h1>{esc(cfg["index_h1"])}</h1>
<p class="lead">{cfg["index_lead"]}</p>
<div class="meta">
{"".join(f'<span class="chip">{esc(c)}</span>' for c in cfg["index_chips"])}
</div>
</div>
</section>

<div class="container prose">
{body}

<div class="callout callout--cta">
<div class="callout__title">Not sure which one you need?</div>
<p>Tell me what you are trying to work out and I will point you at the right one &mdash; or tell you that none of these fit. <a href="https://www.linkedin.com/in/allanninal/" rel="noopener">Message me on LinkedIn</a>.</p>
</div>
</div>
{_footer()}'''


# --------------------------------------------------------------------------- #
# sitemap + build
# --------------------------------------------------------------------------- #

def render_sitemap(cfg: dict, guides: list, articles: list | None = None) -> str:
    """Generate the section sitemap.

    Every other section on this site has a hand-written sitemap.xml, and the
    field-notes generator never wrote one at all. That is exactly how a page
    ends up published and unindexed, so this one is generated with the pages.
    """
    def entry(loc, pri):
        return (f"  <url>\n    <loc>{loc}</loc>\n"
                f"    <lastmod>{cfg['date']}</lastmod>\n"
                f"    <changefreq>monthly</changefreq>\n"
                f"    <priority>{pri}</priority>\n  </url>")

    urls = [entry(f"{SITE}/{SEC}/", "0.9")]
    urls += [entry(url_for(g["slug"]), "0.8") for g in guides]
    # Guides go in at the same priority as products. They are the pages most likely to be
    # found cold from a search, so leaving them out of the sitemap would be backwards.
    urls += [entry(url_for(a["slug"]), "0.8") for a in (articles or [])]
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "\n".join(urls) + "\n</urlset>\n")


def render_llms(cfg: dict, guides: list, articles: list | None = None) -> str:
    lines = [f"# {cfg['index_title']}", "",
             f"> {cfg['index_desc']}", ""]
    for name in cfg["group_order"]:
        gs = [g for g in guides if g["group"] == name]
        if not gs:
            continue
        lines += [f"## {name}", ""]
        for g in gs:
            p = BY_KEY[g["key"]]
            lines.append(
                f"- [{g['card_title']}]({url_for(g['slug'])}): {g['card_blurb']} "
                f"${p['price']}, {len(p['tabs'])} tabs, Excel and Google Sheets. "
                f"Buy: {p['url']}")
        lines.append("")
    for name in cfg.get("guide_group_order", []):
        gs = [a for a in (articles or []) if a["group"] == name]
        if not gs:
            continue
        lines += [f"## {name}", ""]
        for a in gs:
            lines.append(f"- [{a['card_title']}]({url_for(a['slug'])}): {a['card_blurb']} "
                         f"Free guide, no signup. Includes a free Excel workbook.")
        lines.append("")
    return "\n".join(lines)


def stamp_root_sitemap(cfg: dict) -> None:
    """Update this section's lastmod in the site-wide sitemap index.

    The section sitemap is regenerated with the pages, so it is always current. The ROOT
    index is a separate file that nothing was updating, so its lastmod for /spreadsheets/
    only happened to be right because somebody edited it by hand the same day. A search
    engine reads the index first, so a stale date there is what stops a recrawl.

    Refuses loudly rather than guessing if the entry is not found — a silent no-op here
    would be indistinguishable from working.
    """
    import re
    root = ROOT / "sitemap.xml"
    if not root.exists():
        print("  ⚠ root sitemap.xml not found — section lastmod NOT stamped")
        return
    t = root.read_text(encoding="utf-8")
    pat = re.compile(r'(<loc>' + re.escape(f"{SITE}/{SEC}/sitemap.xml") +
                     r'</loc>\s*<lastmod>)([\d-]+)(</lastmod>)')
    m = pat.search(t)
    if not m:
        print(f"  ⚠ no <loc> for {SEC}/sitemap.xml in the root index — NOT stamped")
        return
    if m.group(2) == cfg["date"]:
        print(f"  ok   root sitemap lastmod already {cfg['date']}")
        return
    root.write_text(pat.sub(rf"\g<1>{cfg['date']}\g<3>", t, count=1), encoding="utf-8")
    print(f"  ok   root sitemap lastmod {m.group(2)} -> {cfg['date']}")


def build(cfg: dict, guides: list, articles: list | None = None) -> int:
    out = ROOT / SEC
    out.mkdir(parents=True, exist_ok=True)
    fails = 0

    seen = set()
    for g in guides:
        if g["slug"] in seen:
            raise SystemExit(f"duplicate slug: {g['slug']}")
        seen.add(g["slug"])
        if g["key"] not in BY_KEY:
            raise SystemExit(f"{g['slug']}: key {g['key']!r} is not in catalog.py")

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
        fails += bool(flags)
        print(f"  {'FAIL' if flags else 'ok  '} {g['slug']:<38} {len(page):>7,}b "
              f"t[{len(g['title'])}] d[{len(g['description'])}] {' '.join(flags)}")

    articles = articles or []
    if articles:
        import build_guide
        seen_a = set()
        for a in articles:
            if a["slug"] in seen or a["slug"] in seen_a:
                raise SystemExit(f"duplicate slug: {a['slug']}")
            seen_a.add(a["slug"])
        for a in articles:
            d = out / a["slug"]
            d.mkdir(parents=True, exist_ok=True)
            page = build_guide.render(cfg, a)
            d.joinpath("index.html").write_text(page, encoding="utf-8")
            flags = []
            if len(a["title"]) > 65:
                flags.append(f"TITLE {len(a['title'])}")
            if len(a["description"]) > 160:
                flags.append(f"DESC {len(a['description'])}")
            # A guide whose featured image is missing would ship with a broken og:image
            # and an empty figure — cheaper to fail here than to find it in a search result.
            if not (ROOT / SEC / "assets" / "img" / "guides" / f"{a['slug']}.png").exists():
                flags.append("NO COVER")
            fails += bool(flags)
            print(f"  {'FAIL' if flags else 'ok  '} {a['slug']:<38} {len(page):>7,}b "
                  f"t[{len(a['title'])}] d[{len(a['description'])}] {' '.join(flags)}")

    idx = render_index(cfg, guides, articles)
    out.joinpath("index.html").write_text(idx, encoding="utf-8")
    iflags = []
    if len(cfg["index_title"]) > 65:
        iflags.append(f"TITLE {len(cfg['index_title'])}")
    if len(cfg["index_desc"]) > 160:
        iflags.append(f"DESC {len(cfg['index_desc'])}")
    fails += bool(iflags)
    print(f"  {'FAIL' if iflags else 'ok  '} {'index.html':<38} {len(idx):>7,}b "
          f"t[{len(cfg['index_title'])}] d[{len(cfg['index_desc'])}] {' '.join(iflags)}")

    out.joinpath("sitemap.xml").write_text(render_sitemap(cfg, guides, articles), encoding="utf-8")
    stamp_root_sitemap(cfg)
    out.joinpath("llms.txt").write_text(render_llms(cfg, guides, articles), encoding="utf-8")
    print(f"  ok   sitemap.xml + llms.txt ({len(guides) + len(articles) + 1} URLs)")
    return fails
