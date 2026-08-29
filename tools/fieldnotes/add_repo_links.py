#!/usr/bin/env python3
"""Link every field note to the script that goes with it.

The situation this fixes, found 2026-08-29: there are nine PUBLIC repos of runnable
Python and Node scripts — one per platform, 652 folders in total — organised with one
folder per article slug, matching the site's slugs exactly. Their READMEs link to the
site. The site linked back **zero times**, in any section.

So a reader finished a 54KB article containing the full script, and had no idea a tested,
CI-checked copy of it existed one click away. The `.repo-cta` CSS was already present in
all nine stylesheets, unused — the link was always intended and never added.

There is no generator for these sections' HTML (the platform repos hold scripts only), so
this patches the built pages, in the same spirit as update_pro_links.py for the template
demos. It is idempotent: pages already carrying the block are skipped.

Only slugs that actually exist in the local clone are linked, and the clones are clean and
pushed, so a linked folder is a folder that exists. Four DNS notes have no script folder —
they are advisory rather than automatable — and they are left alone rather than pointed at
a 404.

Usage: add_repo_links.py [--apply] [platform ...]
"""
import re
import sys
from pathlib import Path

SITE = Path.home() / "Projects/allanninal.dev"
REPOS = Path.home() / "Projects"
GH = "https://github.com/allanninal"
# section -> repo name. Nine follow the <section>-fixes convention; the five added later
# are named for what people would actually search GitHub for, which matters because the
# point of this section is to be found.
REPO = {"woocommerce": "woocommerce-fixes", "shopify": "shopify-fixes",
        "bigcommerce": "bigcommerce-fixes", "medusa": "medusa-fixes",
        "shopware": "shopware-fixes", "saleor": "saleor-fixes",
        "prestashop": "prestashop-fixes", "magento": "magento-fixes",
        "dns": "dns-fixes", "seo": "technical-seo-fixes",
        "cloudflare": "cloudflare-fixes", "ci": "github-actions-fixes",
        "aws": "aws-cost-fixes", "email": "email-ses-fixes",
        "stripe": "stripe-fixes"}
PLATFORMS = list(REPO)

# Sections whose scripts hold a credential to a live payments or messaging account.
# Those never write at all, so "dry run by default" would understate it — there is
# no second mode to be careful about.
READ_ONLY = {"stripe"}
APPLY = "--apply" in sys.argv

# The `.repo-cta` rule in every one of the nine stylesheets styles a WRAPPER whose <a>
# children become buttons. Putting the class on the anchor leaves it an unstyled link — a
# mistake made and shipped elsewhere on this site the same day, so it is spelled out.
#
# Two anchors, deliberately. The stated purpose of Field Notes is to promote the GitHub
# profile, so every one of the 652 notes now offers the script AND the profile. A link to
# a repo grows one repo; a link to the profile is what turns a reader into a follower.
ART = ('<div class="repo-cta" data-repo-cta>\n'
       '<a href="{gh}/{repo}/tree/main/{slug}" rel="noopener" target="_blank">'
       'Get this script on GitHub</a>\n'
       '<a href="{gh}" rel="noopener" target="_blank">Follow @allanninal</a>\n'
       '<span>Python and Node.js, with tests. {safety}. '
       '{count_phrase}, free and open source.</span>\n'
       '</div>\n')

IDX = ('<div class="repo-cta" data-repo-cta>\n'
       '<a href="{gh}/{repo}" rel="noopener" target="_blank">'
       'Browse {browse} on GitHub</a>\n'
       '<a href="{gh}/{repo}/archive/refs/heads/main.zip">Download them all as a zip</a>\n'
       '{pdf}'
       '<a href="{gh}" rel="noopener" target="_blank">Follow @allanninal</a>\n'
       '<span>Every fix on this page has a tested Python and Node.js script in the repo. '
       'Free, and MIT as stated in its README.</span>\n'
       '</div>\n')

PDF = ('<a href="/assets/field-guides/allanninal-{repo}-field-guide.pdf" download>'
       'Field guide PDF ({n} {fixes}, {kb}&nbsp;KB)</a>\n')


# "fix" pluralises to "fixes", not "fixs".
PLURALS = {"fix": "fixes", "script": "scripts"}


def plural(n: int, word: str) -> str:
    """Every section had more than one note when these strings were written, so the
    templates hard-coded the plural. A new section starts at one."""
    return word if n == 1 else PLURALS[word]


def note_count(plat: str) -> int:
    """Notes published in the section, which is what the PDF covers.

    Not the same as the number of script folders in the repo: /dns/ has 58 notes
    and 54 scripts, because four of its fixes live in a registrar's console and no
    script can perform them. Labelling the field guide with the repo count made it
    claim 54.
    """
    d = SITE / plat
    return len([p for p in d.iterdir()
                if p.is_dir() and p.name not in ("assets", "downloads")
                and (p / "index.html").is_file()])


def pdf_anchor(plat: str, n: int) -> str:
    """The printable field guide, if one has been built for this section.

    This anchor used to be pasted in by hand after each build. It was therefore
    the first thing lost whenever a section was regenerated — which is exactly
    what happened to /seo/. Deriving it here means a rebuild restores it.
    """
    f = SITE / "assets" / "field-guides" / f"allanninal-{REPO[plat]}-field-guide.pdf"
    if not f.is_file():
        return ""
    notes = note_count(plat)
    return PDF.format(repo=REPO[plat], n=notes, fixes=plural(notes, "fix"),
                      kb=f.stat().st_size // 1024)

# Shown in the copy, so it has to read like the platform is written elsewhere on the page.
LABEL = {"woocommerce": "WooCommerce", "shopify": "Shopify", "bigcommerce": "BigCommerce",
         "medusa": "Medusa", "shopware": "Shopware", "saleor": "Saleor",
         "prestashop": "PrestaShop", "magento": "Magento", "dns": "DNS and domain",
         "seo": "technical SEO", "cloudflare": "Cloudflare", "ci": "GitHub Actions",
         "aws": "AWS cost", "email": "email and SES", "stripe": "Stripe"}


def folders(plat: str) -> set[str]:
    d = REPOS / REPO[plat]
    if not d.is_dir():
        return set()
    return {p.name for p in d.iterdir()
            if p.is_dir() and not p.name.startswith(".")
            and p.name not in ("node_modules", "__pycache__")}


ARTICLE_BLOCK = re.compile(r'<div class="repo-cta" data-repo-cta>.*?</div>\s*', re.S)


def patch_article(path: Path, plat: str, slug: str, n: int) -> str:
    html = path.read_text(encoding="utf-8")
    # Refreshed, not skipped: the block names how many fixes the section has, and
    # that number moves every time a note is added.
    had = "data-repo-cta" in html
    html = ARTICLE_BLOCK.sub("", html, count=1)
    # Sit it between the intro paragraph and the code itself, so the reader learns the
    # script is downloadable BEFORE scrolling past 200 lines of it.
    m = re.search(r'(<h2>The full code</h2>\s*<p>.*?</p>\s*)(<div class="code-block")',
                  html, re.S)
    if not m:
        return "no anchor"
    phrase = (f"The only {LABEL[plat]} fix here so far" if n == 1
              else f"One of {n} {LABEL[plat]} fixes")
    block = ART.format(gh=GH, repo=REPO[plat], slug=slug, n=n, label=LABEL[plat],
                       count_phrase=phrase,
                       safety=("Read only, it never writes" if plat in READ_ONLY
                               else "Dry run by default"))
    out = html[:m.end(1)] + block + html[m.end(1):]
    if APPLY:
        path.write_text(out, encoding="utf-8")
    return "already" if had and out == path.read_text(encoding="utf-8") else ("refreshed" if had else "patched")


INDEX_BLOCK = re.compile(
    r'<div class="container prose">\s*<div class="repo-cta" data-repo-cta>.*?</div>\s*</div>\s*',
    re.S)


def patch_index(path: Path, plat: str, n: int) -> str:
    html = path.read_text(encoding="utf-8")
    # Unlike the article block, this one carries a script count and a PDF size that both
    # move. Strip any existing copy and re-emit rather than returning "already", so the
    # numbers on the section index cannot drift away from the repo and the file.
    had = "data-repo-cta" in html
    html = INDEX_BLOCK.sub("", html, count=1)
    # After the hero, before the first content block on the page.
    m = re.search(r'(</section>\s*)(<div class="container)', html, re.S)
    if not m:
        return "no anchor"
    block = IDX.format(gh=GH, repo=REPO[plat], n=n, pdf=pdf_anchor(plat, n),
                       browse="the script" if n == 1 else f"all {n} scripts")
    out = html[:m.end(1)] + '<div class="container prose">\n' + block + '</div>\n' + html[m.end(1):]
    if APPLY:
        path.write_text(out, encoding="utf-8")
    return "refreshed" if had else "patched"


if __name__ == "__main__":
    want = [a for a in sys.argv[1:] if not a.startswith("--")] or PLATFORMS
    grand = {}
    for plat in want:
        repo = folders(plat)
        if not repo:
            print(f"  ⚠ {plat}: no local clone at {REPOS/REPO[plat]} — skipped")
            continue
        sec = SITE / plat
        stats = {"patched": 0, "already": 0, "no anchor": 0, "no script": 0}
        for d in sorted(p for p in sec.iterdir() if p.is_dir() and p.name != "assets"):
            if d.name not in repo:
                stats["no script"] += 1
                continue
            stats[patch_article(d / "index.html", plat, d.name, len(repo))] += 1
        idx = patch_index(sec / "index.html", plat, len(repo))
        grand[plat] = stats
        print(f"  {plat:<13} patched={stats['patched']:<4} already={stats['already']:<4} "
              f"no-anchor={stats['no anchor']:<3} no-script={stats['no script']:<3} index={idx}")
    t = {k: sum(s[k] for s in grand.values()) for k in
         ("patched", "already", "no anchor", "no script")}
    print(f"\n  TOTAL patched={t['patched']} already={t['already']} "
          f"no-anchor={t['no anchor']} no-script={t['no script']}")
    print("APPLIED" if APPLY else "DRY RUN — pass --apply to write")
