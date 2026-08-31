"""Feature photos for /build articles: local, credited, and used exactly once.

Sourcing is a two-step split because unsplash.com sits behind a JavaScript
proof-of-work challenge that curl cannot pass but a real browser clears in a
few seconds:

  1. a browser navigates a search page and hands back a pool of candidates
     (CDN photo id, alt text, photographer name and username) into pool.json
  2. this module assigns pool entries to articles, downloads each at 1200x630
     straight from images.unsplash.com -- which is NOT challenged -- and wires
     the figure, og:image, twitter:image and the JSON-LD image field

Every photo is used on exactly one article, ever. `used.json` is the record.
"""
import json
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BUILD = ROOT / "build"
IMG = BUILD / "assets" / "img"
POOL = HERE / "pool.json"
USED = HERE / "used.json"

CDN = ("https://images.unsplash.com/photo-{id}"
       "?w=1200&h=630&fit=crop&crop=entropy&q=72&auto=format")
UTM = "utm_source=allanninal_dev&utm_medium=referral"


def _load(p, default):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default


def load_pool():
    return _load(POOL, {})


def save_pool(pool):
    POOL.write_text(json.dumps(pool, indent=1, ensure_ascii=False), encoding="utf-8")


def load_used():
    return _load(USED, {})


def save_used(used):
    USED.write_text(json.dumps(used, indent=1, ensure_ascii=False), encoding="utf-8")


def add_candidates(topic, items):
    """Merge a browser harvest into the pool, keyed by topic."""
    pool = load_pool()
    seen = {c["id"] for group in pool.values() for c in group}
    fresh = [c for c in items if c.get("id") and c["id"] not in seen
             and c.get("user") and c.get("alt")]
    pool.setdefault(topic, []).extend(fresh)
    save_pool(pool)
    return len(fresh)


def _download(pid, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(["curl", "-sfL", "-o", str(dest), CDN.format(id=pid)],
                       capture_output=True)
    return r.returncode == 0 and dest.exists() and dest.stat().st_size > 20000


# --------------------------------------------------------------------------
FIG_RE = re.compile(r'<figure class="feature-img">.*?</figure>\s*', re.S)


def figure_html(slug, cand):
    prof = f"https://unsplash.com/@{cand['user']}?{UTM}"
    site = f"https://unsplash.com/?{UTM}"
    alt = cand["alt"].replace('"', "&quot;")
    name = cand.get("name") or cand["user"]
    return ('<figure class="feature-img">'
            f'<img src="/build/assets/img/{slug}/feature.jpg" alt="{alt}" '
            'width="1200" height="630" loading="eager" decoding="async">'
            f'<figcaption>Photo by <a href="{prof}" rel="noopener nofollow" '
            f'target="_blank">{name}</a> on <a href="{site}" rel="noopener nofollow" '
            'target="_blank">Unsplash</a></figcaption></figure>')


def wire(slug, cand):
    """Put the figure and the og/JSON-LD image into one article."""
    f = BUILD / slug / "index.html"
    if not f.exists():
        return False
    s = f.read_text(encoding="utf-8")
    url = f"https://www.allanninal.dev/build/assets/img/{slug}/feature.jpg"
    s = FIG_RE.sub("", s)

    # the figure goes first inside the prose column, above the progress strip
    fig = figure_html(slug, cand)
    if '<nav class="sp"' in s:
        s = s.replace('<nav class="sp"', fig + '\n        <nav class="sp"', 1)
    elif '<div class="callout" aria-label="Key takeaways">' in s:
        s = s.replace('<div class="callout" aria-label="Key takeaways">',
                      fig + '\n        <div class="callout" aria-label="Key takeaways">', 1)
    else:
        return False

    s = re.sub(r'(<meta property="og:image" content=")[^"]*(")', rf"\g<1>{url}\g<2>", s)
    s = re.sub(r'(<meta name="twitter:image" content=")[^"]*(")', rf"\g<1>{url}\g<2>", s)
    alt = cand["alt"].replace('"', "&quot;")
    s = re.sub(r'(<meta property="og:image:alt" content=")[^"]*(")', rf"\g<1>{alt}\g<2>", s)
    if '"image":' in s:
        s = re.sub(r'"image": "[^"]*"', f'"image": "{url}"', s, count=1)
    else:
        s = s.replace('"datePublished"', f'"image": "{url}",\n      "datePublished"', 1)
    f.write_text(s, encoding="utf-8")
    return True


def assign(topic, slugs):
    """Give each slug an unused photo from a topic pool, download it, wire it."""
    pool = load_pool()
    used = load_used()
    taken = {v["id"] for v in used.values()}
    cands = [c for c in pool.get(topic, []) if c["id"] not in taken]
    done, missing = [], []
    for slug in slugs:
        if slug in used:
            continue
        if not cands:
            missing.append(slug)
            continue
        cand = cands.pop(0)
        if not _download(cand["id"], IMG / slug / "feature.jpg"):
            continue
        if wire(slug, cand):
            used[slug] = {**cand, "topic": topic}
            taken.add(cand["id"])
            done.append(slug)
    save_used(used)
    return done, missing


def status():
    pool, used = load_pool(), load_used()
    total = sum(len(v) for v in pool.values())
    return {"pool_topics": len(pool), "pool_photos": total,
            "assigned": len(used), "free": total - len(used)}


if __name__ == "__main__":
    print(json.dumps(status(), indent=1))
