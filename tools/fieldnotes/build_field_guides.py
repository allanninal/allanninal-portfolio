#!/usr/bin/env python3
"""One printable field guide PDF per platform, generated from the notes themselves.

Fourteen guides, from four fixes to 138, so the page count is not knowable in advance.
That rules out the Chromium path in the pdf-design skill, which needs one hand-authored
page div per sheet; Typst paginates on its own and is the tool the skill points at for
exactly this case.

Each guide is a catalogue rather than a reprint of the notes. It carries, for every fix:
the problem in one line, the script filename, and the URL of both the full write-up and
the folder in the public repo. Someone can keep it open next to a terminal, or print it,
and get to the right script without searching the site.

Everything is read from the built pages and the local clones. Nothing is typed, so a guide
cannot claim a fix that no longer exists or miss one that was added.

Usage: build_field_guides.py [--apply] [section ...]
"""
import html as H
import re
import subprocess
import sys
from pathlib import Path

SITE = Path.home() / "Projects/allanninal.dev"
REPOS = Path.home() / "Projects"
OUT = SITE / "assets" / "field-guides"
SKILL = Path.home() / ".claude/skills/pdf-design"
TYPST = "/opt/homebrew/bin/typst"
APPLY = "--apply" in sys.argv

sys.path.insert(0, str(Path(__file__).resolve().parent))
from add_repo_links import REPO, LABEL  # noqa: E402  one source of truth for the mapping

BLURB = {
    "seo": "Sitemaps of dead URLs, blocked noindex, wrong canonicals and soft 404s.",
    "cloudflare": "Shadowed page rules, purges that clear nothing and Flexible SSL loops.",
    "ci": "Empty secrets in fork PRs, silent cache misses and redundant billed runs.",
    "aws": "Idle NAT gateways, unattached EBS, log retention and tag coverage.",
    "email": "Amazon SES suppression, bounce rate, DKIM and DMARC alignment.",
    "woocommerce": "WooCommerce, Subscriptions and Stripe order, renewal and payment fixes.",
    "shopify": "Shopify order, inventory and payout reconciliation fixes.",
    "bigcommerce": "BigCommerce order, webhook and catalog fixes.",
    "medusa": "Medusa v2 storefront, inventory and workflow fixes.",
    "shopware": "Shopware 6 order, stock and message queue fixes.",
    "saleor": "Saleor checkout, channel and stock fixes.",
    "prestashop": "PrestaShop stock, order state and Webservice API fixes.",
    "magento": "Magento 2 indexing, cron and MSI inventory fixes.",
    "dns": "DNS records, email authentication, DNSSEC and certificate fixes.",
    "stripe": "Stripe fails quietly. A webhook endpoint stops delivering and the payments "
              "still succeed, so revenue looks normal while everything that should happen "
              "after a payment stops. Every script here is read only.",
}


def esc(t: str) -> str:
    """Escape for a Typst string literal.

    Only backslash and double quote are special inside "...". The first version also
    escaped markup characters (_ * # etc.), which are not special there, and printed a
    literal backslash on the page: canonical\\_audit.py.
    """
    return t.replace("\\", "\\\\").replace('"', '\\"')


def strip(t: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", t)).strip()


def notes_for(section: str) -> list[dict]:
    out = []
    repo_dir = REPOS / REPO[section]
    for d in sorted(p for p in (SITE / section).iterdir()
                    if p.is_dir() and p.name != "assets"):
        h = (d / "index.html").read_text(encoding="utf-8")
        m = re.search(r"<h1[^>]*>(.*?)</h1>", h, re.S)
        title = strip(m.group(1)) if m else d.name
        lm = re.search(r'<p class="lead">(.*?)</p>', h, re.S)
        lead = H.unescape(strip(lm.group(1))) if lm else ""
        fm = re.search(r'<h2>The full code</h2>.*?<div class="code-filename">(.*?)</div>',
                       h, re.S)
        script = strip(fm.group(1)) if fm else ""
        out.append({"slug": d.name, "title": H.unescape(title), "lead": lead,
                    "script": script, "has_repo": (repo_dir / d.name).is_dir()})
    return out


def document(section: str, notes: list[dict]) -> str:
    repo = REPO[section]
    # LABEL is phrased for mid-sentence use ("one of 4 technical SEO fixes"), so it needs
    # its first letter lifted for a title. .title() would wreck WooCommerce and SES.
    label = LABEL[section][0].upper() + LABEL[section][1:]
    n = len(notes)
    with_script = sum(1 for x in notes if x["has_repo"])
    body = []
    for i, x in enumerate(notes, 1):
        body.append(
            f'#fix(\n'
            f'  n: {i},\n'
            f'  title: "{esc(x["title"])}",\n'
            f'  lead: "{esc(x["lead"])}",\n'
            f'  script: "{esc(x["script"])}",\n'
            f'  guide: "https://www.allanninal.dev/{section}/{x["slug"]}/",\n'
            f'  code: {"\"https://github.com/allanninal/" + repo + "/tree/main/" + x["slug"] + "\"" if x["has_repo"] else "none"},\n'
            f')')
    fixes = "\n".join(body)
    return f'''#import "{SKILL}/assets/base.typ": *

#show: doc.with(
  title: "{esc(label)} Field Guide",
  palette: blueprint,
  pairing: documentation,
  paper-size: "us-letter",
)

// The documentation pairing's body face is IBM Plex Mono, which set every paragraph in
// monospace. Headings keep the pairing; prose gets a face meant for reading.
#set text(font: "IBM Plex Sans", size: ts.base)

#let fix(n: 0, title: "", lead: "", script: "", guide: "", code: none) = block(
  breakable: false,
  inset: (top: sp.sm, bottom: sp.sm),
  stroke: (bottom: 0.5pt + rgb("#D7DDE4")),
  width: 100%,
)[
  #grid(columns: (auto, 1fr), column-gutter: sp.sm,
    text(size: ts.xs, fill: rgb("#7C8794"), font: "IBM Plex Mono")[#n],
    [
      #text(size: ts.sm, weight: 600)[#title]
      #linebreak()
      #text(size: ts.xs, fill: rgb("#4B5563"))[#lead]
      #linebreak()
      #text(size: 7.5pt, font: "IBM Plex Mono", fill: rgb("#0F5F8A"))[#script]
      #linebreak()
      #text(size: 7pt, font: "IBM Plex Mono", fill: rgb("#7C8794"))[#guide]
      #if code != none [
        #linebreak()
        #text(size: 7pt, font: "IBM Plex Mono", fill: rgb("#7C8794"))[#code]
      ]
    ]
  )
]

#eyebrow(palette: blueprint)[Field Notes]
#v(sp.xs)
#text(size: ts.xxl, weight: 700)[{esc(label)} Field Guide]
#accent-rule(palette: blueprint)
#lede(palette: blueprint)[{esc(BLURB[section])}]

#v(sp.sm)
#text(size: ts.sm)[
  *{n} fixes*, each one a written note with diagrams and a small Python and Node.js
  script that finds the problem and repairs it.
  {"All " + str(with_script) if with_script == n else str(with_script) + " of " + str(n)}
  have a script in the public repo.
]

#v(sp.md)
#card(palette: blueprint)[
  *Before you run anything.* Every script starts in a dry run: it reports what it
  would change and writes nothing. Read that output first, then set `DRY_RUN=false`
  when you are satisfied it has understood your data.

  #v(sp.xs)
  Scripts: #link("https://github.com/allanninal/{repo}")[github.com/allanninal/{repo}]
  #linebreak()
  Guides: #link("https://www.allanninal.dev/{section}/")[allanninal.dev/{section}]
  #linebreak()
  All 14 repos: #link("https://github.com/allanninal")[github.com/allanninal]
]

#v(sp.lg)
#text(size: ts.md, weight: 700)[The fixes]
#v(sp.xs)

{fixes}

#v(sp.md)
#text(size: 8pt, fill: rgb("#7C8794"))[
  MIT licensed. Free to use, change and ship.
  Written by Allan Ni\\u{{00F1}}al \\u{{2014}} allanninal.dev
]
'''


def build(section: str) -> tuple[bool, str]:
    notes = notes_for(section)
    if not notes:
        return False, "no notes"
    src = document(section, notes)
    OUT.mkdir(parents=True, exist_ok=True)
    typ = OUT / f"{section}.typ"
    pdf = OUT / f"allanninal-{REPO[section]}-field-guide.pdf"
    if not APPLY:
        return True, f"{len(notes)} fixes (dry run)"
    typ.write_text(src, encoding="utf-8")
    r = subprocess.run([TYPST, "compile", "--root", "/",
                        "--font-path", str(SKILL / "assets"), str(typ), str(pdf)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return False, (r.stderr or r.stdout).strip().splitlines()[0][:120]
    typ.unlink()
    kb = pdf.stat().st_size // 1024
    pages = subprocess.run(
        [str(Path.home() / ".venvs/pdf-studio/bin/python"), "-c",
         f"import pypdf;print(len(pypdf.PdfReader('{pdf}').pages))"],
        capture_output=True, text=True).stdout.strip()
    return True, f"{len(notes)} fixes, {pages} pages, {kb} KB"


if __name__ == "__main__":
    want = [a for a in sys.argv[1:] if not a.startswith("--")] or list(REPO)
    ok = fail = 0
    for s in want:
        good, msg = build(s)
        ok += good; fail += (not good)
        print(f"  {'ok  ' if good else 'FAIL'} {s:<13} {msg}")
    print(f"\n  {ok} guide(s), {fail} failed")
    print("APPLIED" if APPLY else "DRY RUN — pass --apply to write")
    sys.exit(1 if fail else 0)
