"""Render the eight pages of a /build series from one spec.

A series is seven posts plus its index. The chrome (analytics head, the shared
site nav, the footer) is lifted verbatim from a hand-written page so a
generated post is byte-comparable with one; everything else comes from the
spec. Diagrams come from layouts.py, so every post is diagram-first by
construction rather than by discipline.
"""
import datetime as dt
import html
import json
import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent
CH = HERE / "chrome"
HEAD_TOP = (CH / "head_top.html").read_text(encoding="utf-8")
NAV = (CH / "nav.html").read_text(encoding="utf-8")
FOOT = (CH / "foot.html").read_text(encoding="utf-8")

BASE = "https://www.allanninal.dev/build"
AUTHOR = "Allan Ni&ntilde;al"


def e(s):
    """Escape for an HTML attribute, keeping the site's entity style."""
    return html.escape(str(s), quote=True)


def t(s):
    """Typographic pass: the site writes real punctuation as entities."""
    s = str(s)
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    s = s.replace("--", "&mdash;")
    s = re.sub(r"(\w)'(\w)", r"\1&rsquo;\2", s)
    s = re.sub(r'"([^"]*)"', r"&ldquo;\1&rdquo;", s)
    s = s.replace("'", "&rsquo;")
    return s


def plain(s):
    """Entity-free text for meta descriptions and JSON-LD."""
    s = re.sub(r"<[^>]+>", "", str(s))
    return s.replace("--", "—").replace("&", "and")


def fmt_date(iso):
    d = dt.date.fromisoformat(iso)
    return d.strftime("%B %-d, %Y")


PERSON = {
    "@type": "Person",
    "@id": f"{BASE}/#person",
    "name": "Allan Niñal",
    "url": f"{BASE}/",
    "jobTitle": "Builder, founder, and software engineer",
    "description": ("Builds small AWS systems and writes diagram-first walkthroughs of how "
                    "each one works. Open to builds, collabs, and design reviews."),
    "knowsAbout": ["AWS", "serverless architecture", "AWS Bedrock", "AWS Lambda", "AI agents",
                   "small business automation", "DevOps", "cloud infrastructure"],
    "sameAs": ["https://github.com/allanninal", "https://ko-fi.com/allanninal",
               "https://www.linkedin.com/in/allanninal/"],
}


def head(*, title, desc, url, og_desc=None, image=None, kind="article", date=None,
         tags=(), jsonld=None, prev=None, nxt=None, alt=None):
    og_desc = og_desc or desc
    img = image or f"{BASE}/assets/og/default.png"
    rows = [HEAD_TOP,
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1, '
            'viewport-fit=cover">',
            '<meta name="color-scheme" content="dark">',
            '<meta name="theme-color" content="#0f1b2a">',
            "",
            f"<title>{t(title)}</title>",
            f'<meta name="description" content="{e(plain(desc))}">',
            f'<meta name="author" content="{AUTHOR}">',
            "",
            f'<link rel="canonical" href="{url}">',
            "",
            f'<meta property="og:type" content="{kind}">',
            '<meta property="og:locale" content="en_US">',
            f'<meta property="og:title" content="{e(plain(title))}">',
            f'<meta property="og:description" content="{e(plain(og_desc))}">',
            f'<meta property="og:url" content="{url}">',
            f'<meta property="og:image" content="{img}">',
            '<meta property="og:image:width" content="1200">',
            '<meta property="og:image:height" content="630">',
            f'<meta property="og:image:alt" content="{e(alt or plain(title))}">',
            '<meta property="og:site_name" content="allanninal.dev/build">']
    if date:
        rows += [f'<meta property="article:published_time" content="{date}">',
                 f'<meta property="article:author" content="{AUTHOR}">',
                 f'<meta property="article:modified_time" content="{date}">']
    for tag in tags:
        rows.append(f'<meta property="article:tag" content="{e(tag)}">')
    rows += ["",
             '<meta name="twitter:card" content="summary_large_image">',
             f'<meta name="twitter:title" content="{e(plain(title))}">',
             f'<meta name="twitter:description" content="{e(plain(og_desc))}">',
             f'<meta name="twitter:image" content="{img}">',
             "",
             '<link rel="icon" type="image/svg+xml" href="/build/assets/favicon.svg">',
             '<link rel="apple-touch-icon" href="/build/assets/apple-touch-icon.png">',
             '<link rel="stylesheet" href="/build/assets/style.css">']
    if prev:
        rows.append(f'<link rel="prev" href="{prev}">')
    if nxt:
        rows.append(f'<link rel="next" href="{nxt}">')
    rows += ['<link rel="alternate" type="application/atom+xml" href="/build/feed.xml" '
             'title="allanninal.dev/build — Atom feed">',
             '<link rel="me" href="https://github.com/allanninal">',
             '<link rel="me" href="https://www.linkedin.com/in/allanninal/">']
    if jsonld:
        rows.append('\n<script type="application/ld+json">\n'
                    + json.dumps(jsonld, indent=2, ensure_ascii=False)
                    + "\n  </script>")
    rows += ['<link rel="stylesheet" href="/assets/site-nav.css">',
             '<link rel="stylesheet" href="/assets/site-mobile.css">']
    return ('<!DOCTYPE html>\n<html lang="en">\n<head>\n  '
            + "\n  ".join(r for r in rows if r is not None)
            + "\n</head>\n<body>\n" + NAV)


def page(head_html, main_html):
    return head_html + main_html + "\n  " + FOOT
