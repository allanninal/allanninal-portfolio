"""Build the eight pages of one /build series from a spec dict."""
import pathlib

from . import layouts as L
from .pages import BASE, PERSON, e, fmt_date, head, page, plain, t
from .svgkit import figure

ROOT = pathlib.Path(__file__).resolve().parents[2] / "build"

LAYOUT = {"system": L.system, "chain": L.chain, "lanes": L.lanes,
          "bars": L.bars, "strip": L.strip}


# --------------------------------------------------------------------------
# content blocks
# --------------------------------------------------------------------------
def render_blocks(blocks, fignum=None):
    fignum = fignum or [0]
    out = []
    for b in blocks:
        kind = b[0]
        if kind == "h2":
            out.append(f'<h2 id="{slugify(b[1])}">{t(b[1])}</h2>')
        elif kind == "h3":
            out.append(f'<h3 id="{slugify(b[1])}">{t(b[1])}</h3>')
        elif kind == "p":
            out.append(f"<p>{t(b[1])}</p>")
        elif kind == "ul":
            items = "".join(f"<li>{t(i)}</li>" for i in b[1])
            out.append(f"<ul>{items}</ul>")
        elif kind == "ol":
            items = "".join(f"<li>{t(i)}</li>" for i in b[1])
            out.append(f"<ol>{items}</ol>")
        elif kind == "callout":
            items = "".join(f"<li>{t(i)}</li>" for i in b[2])
            out.append(f'<div class="callout"><p class="callout__label">{t(b[1])}</p>'
                       f"<ul>{items}</ul></div>")
        elif kind == "fig":
            _, spec, caption, title, desc = b
            fignum[0] += 1
            c = LAYOUT[spec[0]](**spec[1])
            svg = c.render(title, desc)
            out.append(figure(svg, f"Fig {fignum[0]}. {t(caption)}", c.cats))
        elif kind == "table":
            _, cols, rows = b
            th = "".join(f"<th scope=\"col\">{t(c)}</th>" for c in cols)
            tr = "".join("<tr>" + "".join(f"<td>{t(c)}</td>" for c in r) + "</tr>"
                         for r in rows)
            out.append('<div class="table-wrap"><table><thead><tr>' + th +
                       "</tr></thead><tbody>" + tr + "</tbody></table></div>")
        elif kind == "pre":
            out.append(f"<pre><code>{t(b[1])}</code></pre>")
        else:
            raise ValueError(f"unknown block {kind}")
    return "\n\n        ".join(out)


def slugify(s):
    import re
    s = re.sub(r"[^a-z0-9]+", "-", plain(s).lower()).strip("-")
    return s[:64]


# --------------------------------------------------------------------------
def progress(spec, idx):
    """Where-you-are strip: seven numbered chips, the current one marked."""
    chips = []
    for i, p in enumerate(spec["parts"]):
        n = f"{i + 1:02d}"
        if i == idx:
            chips.append(f'<li class="sp__step sp__step--here" aria-current="true">'
                         f'<span class="sp__n">{n}</span>'
                         f'<span class="sp__t">{t(p["nav"])}</span></li>')
        else:
            chips.append(f'<li class="sp__step"><a href="/build/{p["slug"]}/">'
                         f'<span class="sp__n">{n}</span>'
                         f'<span class="sp__t">{t(p["nav"])}</span></a></li>')
    return ('<nav class="sp" aria-label="Series progress">'
            f'<p class="sp__label">{t(spec["name"])} series &middot; part {idx + 1} of 7</p>'
            f'<ol class="sp__list">{"".join(chips)}</ol></nav>')


def feature(spec, part):
    img = part.get("image") or spec.get("image")
    if not img:
        return ""
    c = img["credit"]
    return ('<figure class="feature-img">'
            f'<img src="{img["src"]}" alt="{e(img["alt"])}" width="1200" height="630" '
            'loading="eager" decoding="async">'
            f'<figcaption>Photo by <a href="{c["profile"]}" rel="noopener nofollow" '
            f'target="_blank">{e(c["name"])}</a> on <a href="{c["site_url"]}" '
            f'rel="noopener nofollow" target="_blank">{e(c["site"])}</a></figcaption>'
            "</figure>")


ASIDES = ('\n        <aside class="support">\n'
          '          <p class="support__label">Build with me</p>\n'
          '          <p>Want one of these designed (or built) for your business &mdash; or have '
          'another automation in mind? See how we could <a href="/build/work-with-me/">build it '
          'together</a>.</p>\n        </aside>\n\n'
          '        <aside class="support">\n'
          '          <p class="support__label">Support this work</p>\n'
          '          <p>If a post here saved you time or sparked an idea, you can '
          '<a href="https://ko-fi.com/allanninal" rel="noopener">buy me a coffee on Ko-fi</a>. '
          'It keeps new posts coming.</p>\n        </aside>\n')


def series_nav(spec, idx):
    parts = spec["parts"]
    prev = parts[idx - 1] if idx else None
    nxt = parts[idx + 1] if idx + 1 < len(parts) else None
    items = []
    if prev:
        items.append(f'<li class="series-nav__prev"><a href="/build/{prev["slug"]}/" rel="prev">'
                     f'<span class="series-nav__direction">Previous</span>'
                     f'<span class="series-nav__title">{t(prev["title"])}</span></a></li>')
    else:
        items.append('<li class="series-nav__placeholder" aria-hidden="true"></li>')
    if nxt:
        items.append(f'<li class="series-nav__next"><a href="/build/{nxt["slug"]}/" rel="next">'
                     f'<span class="series-nav__direction">Next</span>'
                     f'<span class="series-nav__title">{t(nxt["title"])}</span></a></li>')
    else:
        items.append('<li class="series-nav__placeholder" aria-hidden="true"></li>')
    return ('<nav class="series-nav" aria-label="Series navigation">'
            f'<ul class="series-nav__pager">{"".join(items)}</ul>'
            f'<p class="series-nav__index"><a href="/build/series/{spec["slug"]}/">'
            f'All 7 parts in {t(spec["name"])} series &rarr;</a></p></nav>')


# --------------------------------------------------------------------------
def article(spec, idx, offer_block):
    p = spec["parts"][idx]
    url = f"{BASE}/{p['slug']}/"
    parts = spec["parts"]
    prev = f"{BASE}/{parts[idx-1]['slug']}/" if idx else None
    nxt = f"{BASE}/{parts[idx+1]['slug']}/" if idx + 1 < len(parts) else None
    img = p.get("image") or spec.get("image")
    og = img["og"] if img else None

    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "BlogPosting",
         "@id": f"{url}#article",
         "headline": plain(p["title"]),
         "description": plain(p.get("og") or p["desc"]),
         "url": url,
         "datePublished": spec["date"],
         "dateModified": spec["date"],
         "inLanguage": "en",
         "author": {"@id": f"{BASE}/#person"},
         "publisher": {"@id": f"{BASE}/#person"},
         "wordCount": p.get("words", 900),
         "keywords": list(p.get("tags", spec.get("keywords", []))),
         "mainEntityOfPage": {"@type": "WebPage", "@id": url},
         "isPartOf": {"@type": "CreativeWorkSeries",
                      "name": f"{plain(spec['name'])} series",
                      "url": f"{BASE}/series/{spec['slug']}/"},
         "articleSection": f"{plain(spec['name'])} series",
         "position": idx + 1,
         "speakable": {"@type": "SpeakableSpecification",
                       "cssSelector": ["h1", ".article-header__lede"]}},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Posts", "item": f"{BASE}/"},
            {"@type": "ListItem", "position": 2, "name": f"{plain(spec['name'])} series",
             "item": f"{BASE}/series/{spec['slug']}/"},
            {"@type": "ListItem", "position": 3, "name": plain(p["title"])}]},
        PERSON]}
    if og:
        ld["@graph"][0]["image"] = og

    h = head(title=p["title"], desc=p["desc"], og_desc=p.get("og"), url=url, image=og,
             kind="article", date=spec["date"], tags=p.get("tags", ()), jsonld=ld,
             prev=prev, nxt=nxt, alt=p.get("alt") or plain(p["title"]))

    takeaways = "".join(f"<li>{t(i)}</li>" for i in p["takeaways"])
    body = render_blocks(p["blocks"])

    main = f'''  <main id="main">
    <article>
      <header class="article-header">
        <div class="container prose">
          <p class="article-header__meta">
            <time datetime="{spec["date"]}">{fmt_date(spec["date"])}</time>
            <span>Part {idx + 1} of 7 &middot; <a href="/build/series/{spec["slug"]}/">{t(spec["name"])} series</a></span>
            <span>~{p.get("read", 5)} min read</span>
          </p>
          <h1>{t(p["title"])}</h1>
          <p class="article-header__lede">{t(p["lede"])}</p>
        </div>
      </header>

      <div class="container prose">
        {feature(spec, p)}
        {progress(spec, idx)}

        <div class="callout" aria-label="Key takeaways">
          <p class="callout__label">Key takeaways</p>
          <ul>{takeaways}</ul>
        </div>

        {body}
        {offer_block}
{ASIDES}
        {series_nav(spec, idx)}

        <a class="back-link" href="/build/">All posts</a>

      </div>
    </article>
  </main>
'''
    return page(h, main)


# --------------------------------------------------------------------------
def index_page(spec, related, offer_block):
    url = f"{BASE}/series/{spec['slug']}/"
    items = []
    for i, p in enumerate(spec["parts"]):
        items.append(f'<li class="series-index__item"><span class="series-index__num">'
                     f'{i + 1:02d}</span><div class="series-index__body">'
                     f'<h2 class="series-index__title"><a href="/build/{p["slug"]}/">'
                     f'{t(p["title"])}</a></h2>'
                     f'<p class="series-index__abstract">{t(p["abstract"])}</p></div></li>')
    faq = "".join(f"<dt><strong>{t(q)}</strong></dt><dd>{t(a)}</dd>"
                  for q, a in spec.get("faq", []))
    rel = "".join(f'<li class="related-series__item"><h3 class="related-series__title">'
                  f'<a href="/build/series/{s["slug"]}/">{t(s["name"])}</a></h3>'
                  f'<p class="related-series__tagline">{t(s["tagline"])}</p></li>'
                  for s in related)

    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "CreativeWorkSeries",
         "@id": f"{url}#series",
         "name": f"{plain(spec['name'])} series",
         "description": plain(spec["lede"]),
         "url": url,
         "inLanguage": "en",
         "author": {"@id": f"{BASE}/#person"},
         "publisher": {"@id": f"{BASE}/#person"},
         "hasPart": [{"@type": "BlogPosting", "position": i + 1,
                      "name": plain(p["title"]),
                      "url": f"{BASE}/{p['slug']}/"}
                     for i, p in enumerate(spec["parts"])]},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Posts", "item": f"{BASE}/"},
            {"@type": "ListItem", "position": 2, "name": f"{plain(spec['name'])} series"}]},
        PERSON]}
    if spec.get("faq"):
        ld["@graph"].append({"@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": plain(q),
             "acceptedAnswer": {"@type": "Answer", "text": plain(a)}}
            for q, a in spec["faq"]]})

    h = head(title=f"{spec['name']} series &mdash; allanninal.dev/build",
             desc=spec["lede"], url=url, kind="website",
             image=spec.get("image", {}).get("og"),
             jsonld=ld, alt=f"{plain(spec['name'])} series")

    main = f'''  <main id="main">
    <header class="article-header">
      <div class="container prose">
        <p class="article-header__meta">
          <span>Series &middot; 7 parts</span>
          <span>Published {fmt_date(spec["date"])}</span>
        </p>
        <h1>{t(spec["name"])}</h1>
        <p class="article-header__lede">{t(spec["lede"])}</p>
      </div>
    </header>

    <div class="container prose">
      <ol class="series-index">{"".join(items)}</ol>

      <section class="faq" aria-labelledby="faq-heading">
        <h2 id="faq-heading" class="related-series__heading">Frequently asked questions</h2>
        <dl>{faq}</dl>
      </section>

      {offer_block}

      <section class="related-series" aria-labelledby="related-series-heading">
        <h2 id="related-series-heading" class="related-series__heading">Other series</h2>
        <ul class="related-series__list">{rel}</ul>
      </section>

      <a class="back-link" href="/build/">All posts</a>
    </div>
  </main>
'''
    return page(h, main)


# --------------------------------------------------------------------------
def write(spec, related, offer_block, root=None):
    root = pathlib.Path(root or ROOT)
    written = []
    for i in range(len(spec["parts"])):
        d = root / spec["parts"][i]["slug"]
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(article(spec, i, offer_block), encoding="utf-8")
        written.append(f"{spec['parts'][i]['slug']}/")
    d = root / "series" / spec["slug"]
    d.mkdir(parents=True, exist_ok=True)
    (d / "index.html").write_text(index_page(spec, related, offer_block), encoding="utf-8")
    written.append(f"series/{spec['slug']}/")
    return written
