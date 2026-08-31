"""Rebuild /build/resources/ -- the honest page behind every "Coming soon" link.

Every blueprint links here, so the page has to say plainly what exists, what
does not, and where a Gumroad link will appear when one does. It is generated
from the same products.json the offer blocks read, so the two can never
disagree about what is on sale.
"""
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from awsbuild import registry  # noqa: E402
from awsbuild.pages import BASE, PERSON, head, page, t  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
BUILD = HERE.parents[1] / "build"
PRODUCTS = json.loads((HERE / "products.json").read_text(encoding="utf-8"))["series"]


def build():
    reg = registry.load()
    order = sorted(reg.values(), key=lambda e: (e["date"], e["slug"]), reverse=True)
    live = [e for e in order if any(PRODUCTS.get(e["slug"], {}).values())]
    soon = [e for e in order if e not in live]

    def row(e):
        p = PRODUCTS.get(e["slug"], {})
        cells = []
        for key, label in (("guide", "Guide"), ("starter", "CDK starter"),
                           ("bundle", "Bundle")):
            url = p.get(key)
            cells.append(f'<td><a class="offer__buy" href="{url}" rel="noopener" '
                         f'target="_blank">Get it</a></td>' if url
                         else '<td><span class="offer__state">Coming soon</span></td>')
        return (f'<tr><td><a href="/build/series/{e["slug"]}/">{e["name"]}</a></td>'
                + "".join(cells) + "</tr>")

    live_html = ""
    if live:
        live_html = (
            '<h2 id="on-sale">On sale now</h2>'
            '<div class="table-wrap"><table><thead><tr><th scope="col">Blueprint</th>'
            '<th scope="col">Guide</th><th scope="col">CDK starter</th>'
            '<th scope="col">Bundle</th></tr></thead><tbody>'
            + "".join(row(e) for e in live) + "</tbody></table></div>")

    soon_html = (
        '<h2 id="in-progress">Everything else</h2>'
        f"<p>{t('All ' + str(len(soon)) + ' of these are free to read in full today. The paid companions are not written yet, and this table is the honest state of each one. When a product ships, its row here becomes a link and every page in that series does the same, automatically.')}</p>"
        '<div class="table-wrap"><table><thead><tr><th scope="col">Blueprint</th>'
        '<th scope="col">Guide</th><th scope="col">CDK starter</th>'
        '<th scope="col">Bundle</th></tr></thead><tbody>'
        + "".join(row(e) for e in soon) + "</tbody></table></div>")

    url = f"{BASE}/resources/"
    lede = ("Every blueprint on this site is free to read, end to end &mdash; the architecture, "
            "the cost breakdown and the engineering reference. The paid companions are a "
            "step-by-step workflow guide and a deployable AWS CDK starter for each one. This "
            "page is the honest state of all of them.")
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "WebPage", "@id": f"{url}#page",
         "name": "Guides & starters", "url": url,
         "description": ("What is on sale, what is not, and what is planned for each of the "
                         f"{len(order)} AWS blueprints on allanninal.dev/build."),
         "inLanguage": "en", "isPartOf": {"@id": f"{BASE}/#website"}},
        PERSON]}

    h = head(title="Guides &amp; starters &mdash; allanninal.dev/build",
             desc=("What is on sale, what is not, and what is planned for each of the "
                   f"{len(order)} AWS blueprints. Every blueprint itself is free to read."),
             url=url, kind="website", jsonld=ld, alt="Guides and starters")

    main = f'''  <main id="main">
    <header class="article-header">
      <div class="container prose">
        <p class="article-header__meta"><span>Guides &amp; starters</span>
          <span>{len(order)} blueprints</span></p>
        <h1>Guides &amp; starters</h1>
        <p class="article-header__lede">{t(lede)}</p>
      </div>
    </header>

    <div class="container prose">
      <div class="callout"><p class="callout__label">The short version</p>
        <ul>
          <li>{t('Every blueprint is free. Nothing on this site is paywalled and there is no download gate anywhere.')}</li>
          <li>{t('Nothing is on sale yet. The table below says so per blueprint rather than in general.')}</li>
          <li>{t('There are no zip downloads. The starters will be sold through Gumroad when they exist, and until then every link says Coming soon.')}</li>
          <li>{t('Want one first? Tell me which on LinkedIn and it moves up the queue.')}</li>
        </ul>
      </div>

      <h2 id="what-is-coming">What each one will be</h2>
      <ul>
        <li><strong>Workflow guide</strong> &mdash; {t('the build step by step, with the decisions and the dead ends, so you can put it together yourself.')}</li>
        <li><strong>AWS CDK starter</strong> &mdash; {t('the same system as infrastructure-as-code you can deploy and adapt.')}</li>
        <li><strong>Bundle</strong> &mdash; {t('both together.')}</li>
      </ul>

      {live_html}
      {soon_html}

      <h2 id="why-no-downloads">Why there are no downloads here</h2>
      <p>{t('These pages used to link at a storefront that has been retired, so every one of those links was dead. Rather than replace them with a zip file that would drift out of date the day after it was published, each blueprint now links here, and each row becomes a real product link as that product ships. A dead link is worse than an honest Coming soon.')}</p>

      <aside class="support">
        <p class="support__label">Build with me</p>
        <p>{t('Would you rather skip the guide and have the system designed for you? See how we could')} <a href="/build/work-with-me/">build it together</a>.</p>
      </aside>

      <a class="back-link" href="/build/">All posts</a>
    </div>
  </main>
'''
    (BUILD / "resources").mkdir(parents=True, exist_ok=True)
    (BUILD / "resources" / "index.html").write_text(page(h, main), encoding="utf-8")
    return len(order), len(live)


if __name__ == "__main__":
    total, live = build()
    print(f"resources page: {total} blueprints, {live} with products")
