"""The list of every /build series, read back off the site itself.

The 74 hand-written series predate any spec files, so their name, tagline,
date and part list are recovered from the pages rather than duplicated into a
data file that could drift. New series register themselves from their spec.
"""
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
BUILD = ROOT / "build"
STORE = pathlib.Path(__file__).resolve().parent / "registry.json"

CARD = re.compile(
    r'<li class="card">.*?href="/build/series/([a-z0-9-]+)/".*?'
    r'<h2 class="card__title"><a href="[^"]*">([^<]+)</a></h2>\s*'
    r'<p class="card__tagline">(.*?)</p>\s*'
    r'<p class="card__meta"><time datetime="(\d{4}-\d{2}-\d{2})">', re.S)

PART = re.compile(r'<h2 class="series-index__title"[^>]*><a href="/build/([a-z0-9-]+)/">(.*?)</a>')


def scan():
    idx = (BUILD / "index.html").read_text(encoding="utf-8")
    out = {}
    for slug, name, tagline, date in CARD.findall(idx):
        sidx = BUILD / "series" / slug / "index.html"
        parts = []
        if sidx.exists():
            parts = [{"slug": s, "title": ti}
                     for s, ti in PART.findall(sidx.read_text(encoding="utf-8"))]
        out[slug] = {"slug": slug, "name": name.strip(), "tagline": tagline.strip(),
                     "date": date, "parts": parts}
    return out


def load():
    return json.loads(STORE.read_text(encoding="utf-8")) if STORE.exists() else scan()


def save(reg):
    STORE.write_text(json.dumps(reg, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    reg = scan()
    save(reg)
    print(len(reg), "series;", sum(len(v["parts"]) for v in reg.values()), "parts")
