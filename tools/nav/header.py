"""Canonical site header for allanninal.dev.

One bar, one markup, every first-party page. `render()` is the single source of
truth; the Astro homepage component mirrors it byte-for-byte so the header a
visitor sees never changes shape as they move between the built homepage and
the generated sections.

Counts in the Guides panel are read off disk, never typed in — a number written
by hand is a number that goes stale the next time a note is published.
"""

from __future__ import annotations

import os

SITE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

LINKEDIN = "https://www.linkedin.com/in/allanninal/"
GITHUB = "https://github.com/allanninal"

# Field-note sections, split the way a reader looks for them: the storefront
# platform they run, or the infrastructure underneath it.
COMMERCE = [
    ("/woocommerce/", "WooCommerce"),
    ("/shopify/", "Shopify"),
    ("/bigcommerce/", "BigCommerce"),
    ("/medusa/", "Medusa"),
    ("/shopware/", "Shopware"),
    ("/saleor/", "Saleor"),
    ("/prestashop/", "PrestaShop"),
    ("/magento/", "Magento"),
]

PLATFORM = [
    ("/aws/", "AWS cost"),
    ("/cloudflare/", "Cloudflare"),
    ("/ci/", "GitHub Actions"),
    ("/email/", "Email &amp; SES"),
    ("/dns/", "DNS &amp; Domains"),
    ("/seo/", "Technical SEO"),
]

WORK = [
    ("/#products", "Products", "live"),
    ("/templates/", "Templates", ""),
    ("/spreadsheets/", "Spreadsheets", ""),
    ("/build/", "Build on AWS", ""),
    ("/#data", "Data &amp; AI", ""),
]

# Short suffix shown after the wordmark, so a section still says where you are.
SECTION_LABEL = {
    "woocommerce": "/woo",
    "shopify": "/shopify",
    "bigcommerce": "/bigcommerce",
    "medusa": "/medusa",
    "shopware": "/shopware",
    "saleor": "/saleor",
    "prestashop": "/prestashop",
    "magento": "/magento",
    "aws": "/aws",
    "cloudflare": "/cloudflare",
    "ci": "/ci",
    "email": "/email",
    "dns": "/dns",
    "seo": "/seo",
    "spreadsheets": "/spreadsheets",
    "build": "/build",
    "blog": "/blog",
    "projects": "/projects",
    "templates": "/templates",
}


def note_count(href: str) -> int:
    """Directories under a section, which is one per published note."""
    d = os.path.join(SITE_ROOT, href.strip("/"))
    try:
        return len(
            [
                e
                for e in os.scandir(d)
                if e.is_dir() and e.name not in ("assets", "downloads")
            ]
        )
    except OSError:
        return 0


MARK_SVG = (
    '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true">'
    '<path d="M9.5 7 5 12l4.5 5" stroke="currentColor" stroke-width="2.1" '
    'stroke-linecap="round" stroke-linejoin="round"/>'
    '<path d="M14.5 7 19 12l-4.5 5" stroke="currentColor" stroke-width="2.1" '
    'stroke-linecap="round" stroke-linejoin="round" opacity=".55"/>'
    "</svg>"
)

GITHUB_SVG = (
    '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 2C6.48 2 2 '
    "6.48 2 12.02c0 4.42 2.87 8.17 6.84 9.5.5.09.68-.22.68-.48 0-.24 0-.87-.01-1.7-2.78.6-3.37-"
    "1.34-3.37-1.34-.45-1.16-1.11-1.47-1.11-1.47-.91-.62.07-.61.07-.61 1 .07 1.53 1.03 1.53 "
    "1.03.89 1.53 2.34 1.09 2.91.83.09-.65.35-1.09.63-1.34-2.22-.25-4.56-1.11-4.56-4.95 0-1.09"
    ".39-1.99 1.03-2.69-.1-.25-.45-1.27.1-2.65 0 0 .84-.27 2.75 1.03A9.56 9.56 0 0 1 12 6.84c."
    "85 0 1.71.12 2.5.34 1.91-1.3 2.75-1.03 2.75-1.03.55 1.38.2 2.4.1 2.65.64.7 1.03 1.6 1.03 "
    '2.69 0 3.85-2.34 4.7-4.57 4.94.36.31.68.92.68 1.86 0 1.34-.01 2.42-.01 2.75 0 .27.18.58.'
    '69.48A10.02 10.02 0 0 0 22 12.02C22 6.48 17.52 2 12 2Z"/></svg>'
)

CHEV_SVG = (
    '<svg class="anx-link__chev" viewBox="0 0 24 24" fill="none" aria-hidden="true">'
    '<path d="m6 9 6 6 6-6" stroke="currentColor" stroke-width="2.4" '
    'stroke-linecap="round" stroke-linejoin="round"/></svg>'
)


def _items(pairs, active, with_counts=False):
    out = []
    for href, name in pairs:
        note = ""
        if with_counts:
            n = note_count(href)
            if n:
                note = f'<span class="anx-item__note">{n}</span>'
        cur = ' aria-current="page"' if href.strip("/") == active else ""
        out.append(f'<a class="anx-item" href="{href}"{cur}>{name}{note}</a>')
    return "".join(out)


def _work_items(active):
    out = []
    for href, name, tag in WORK:
        note = f'<span class="anx-item__note">{tag}</span>' if tag else ""
        cur = ' aria-current="page"' if href.strip("/#") == active else ""
        out.append(f'<a class="anx-item" href="{href}"{cur}>{name}{note}</a>')
    return "".join(out)


def render(section: str = "", main_id: str = "main") -> str:
    """The header for one page. `section` is the top-level directory, or ''."""
    label = SECTION_LABEL.get(section, "")
    section_html = (
        f'<span class="anx-brand__section">{label}</span>' if label else ""
    )
    home_active = ' aria-current="page"' if not section else ""
    blog_active = ' aria-current="page"' if section == "blog" else ""

    guides_panel = (
        '<div class="anx-panel anx-panel--wide" id="anx-guides" hidden>'
        '<div class="anx-panel__group"><p class="anx-panel__title">Commerce platforms</p>'
        f"{_items(COMMERCE, section, with_counts=True)}</div>"
        '<div class="anx-panel__group"><p class="anx-panel__title">Platform &amp; infra</p>'
        f"{_items(PLATFORM, section, with_counts=True)}</div></div>"
    )

    work_panel = (
        '<div class="anx-panel" id="anx-work" hidden>'
        '<p class="anx-panel__title">What I build</p>'
        f"{_work_items(section)}</div>"
    )

    return f"""<div class="anx-root">
<a class="anx-skip" href="#{main_id}">Skip to content</a>
<header class="anx-header">
  <div class="anx-bar">
    <a class="anx-brand" href="/" aria-label="Allan Ni&ntilde;al &mdash; home">
      <span class="anx-brand__mark">{MARK_SVG}</span>
      <span class="anx-brand__text">allanninal<span class="anx-brand__dim">.dev</span>{section_html}</span>
    </a>

    <nav class="anx-nav" aria-label="Primary">
      <a class="anx-link" href="/"{home_active}>Home</a>
      <div class="anx-menu">
        <button class="anx-link" type="button" data-anx-menu aria-expanded="false" aria-controls="anx-work" aria-haspopup="true">Work{CHEV_SVG}</button>
        {work_panel}
      </div>
      <div class="anx-menu">
        <button class="anx-link" type="button" data-anx-menu aria-expanded="false" aria-controls="anx-guides" aria-haspopup="true">Guides{CHEV_SVG}</button>
        {guides_panel}
      </div>
      <a class="anx-link" href="/blog/"{blog_active}>Blog</a>
      <a class="anx-link" href="/#about">About</a>
    </nav>

    <div class="anx-actions">
      <a class="anx-icon" href="{GITHUB}" rel="me noopener" target="_blank" aria-label="GitHub">{GITHUB_SVG}</a>
      <a class="anx-cta" href="/#contact"><span class="anx-cta__dot" aria-hidden="true"></span>Collaborate</a>
      <button class="anx-burger" type="button" aria-expanded="false" aria-controls="anx-drawer" aria-label="Open menu">
        <span class="anx-burger__box" aria-hidden="true"><span></span><span></span><span></span></span>
      </button>
    </div>
  </div>

  <div class="anx-drawer" id="anx-drawer" hidden>
    <a class="anx-drawer__cta" href="/#contact"><span class="anx-cta__dot" aria-hidden="true"></span>Open for collaboration</a>
    <div class="anx-acc"><a class="anx-acc__btn" href="/">Home</a></div>
    <div class="anx-acc">
      <button class="anx-acc__btn" type="button" data-anx-acc aria-expanded="false" aria-controls="anx-d-work">Work{CHEV_SVG}</button>
      <div class="anx-acc__panel" id="anx-d-work" hidden>{_work_items(section)}</div>
    </div>
    <div class="anx-acc">
      <button class="anx-acc__btn" type="button" data-anx-acc aria-expanded="false" aria-controls="anx-d-guides">Guides{CHEV_SVG}</button>
      <div class="anx-acc__panel" id="anx-d-guides" hidden>
        <p class="anx-panel__title">Commerce platforms</p>{_items(COMMERCE, section, with_counts=True)}
        <p class="anx-panel__title">Platform &amp; infra</p>{_items(PLATFORM, section, with_counts=True)}
      </div>
    </div>
    <div class="anx-acc"><a class="anx-acc__btn" href="/blog/">Blog</a></div>
    <div class="anx-acc"><a class="anx-acc__btn" href="/#about">About</a></div>
    <div class="anx-drawer__foot">
      <a href="{GITHUB}" rel="me noopener" target="_blank">{GITHUB_SVG}GitHub</a>
      <a href="{LINKEDIN}" rel="noopener" target="_blank">LinkedIn</a>
      <a href="https://ko-fi.com/allanninal" rel="noopener" target="_blank">Ko-fi</a>
    </div>
  </div>
</header>
</div>"""


if __name__ == "__main__":
    print(render("woocommerce"))
