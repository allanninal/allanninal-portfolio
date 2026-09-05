#!/usr/bin/env python3
"""Render each project's citations onto its page, and check they stay correct.

    .venv/bin/python tools/pages/sources.py          # rewrite every page
    .venv/bin/python tools/pages/sources.py --check  # fail if any is stale

Why this exists. A reader could not find the sources for these pages, and where
a source line did exist it was wrong: the electricity page's footer credited the
World Food Programme, the Department of Agriculture and the DOH Epidemiology
Bureau -- none of which it uses -- because the footer had been copied from the
rice page. Twenty of twenty-seven project pages had no citation line at all.

So citations are declared once per project in data/<project>/sources.csv and
rendered from there into two places on the page:

  * a visible "Sources & Citations" section, with what each source covers and
    whether it is primary, secondary or tertiary
  * the footer line

Neither is hand-edited, and --check fails the build if a page drifts from its
data. The tier column matters: several of these pages rest on a transcription of
a record that refuses automated requests, and a reader deserves to see that
without reading the method section.
"""
import csv
import glob
import os
import re
import sys

MARK_START = "<!-- sources:start -->"
MARK_END = "<!-- sources:end -->"
TIER_LABEL = {
    "primary": "Primary",
    "secondary": "Secondary",
    "tertiary": "Tertiary",
}
TIER_NOTE = {
    "primary": "the body that produced the record",
    "secondary": "a compiler that redistributes the primary record",
    "tertiary": "a transcription of a record this analysis cannot fetch directly",
}


def project_for(page):
    """data/<project> whose facts.sql declares this page."""
    stem = os.path.splitext(os.path.basename(page))[0]
    for d in sorted(glob.glob("data/*")):
        f = os.path.join(d, "facts.sql")
        if os.path.isdir(d) and os.path.exists(f) and stem in open(f).read(400):
            return d
    return None


def theme_of(src):
    """Per-role class names, resolved against this page's own stylesheet.

    Shares _common.theme_for so the Sources block cannot drift from the sections
    above it. An earlier two-family version emitted grid-3 on pages that define
    only insights-grid, so the citations this file exists to surface arrived
    unstyled on exactly the pages that most needed them.
    """
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from _common import theme_for
    t = theme_for(src)
    return dict(wrap=t["wrap"], grid=t["cards_grid"], desc=t["sec_desc"],
                head=t["card_head"], body=t["card_body"])


def render(project, t=None):
    t = t or dict(wrap="section fade-up", grid="grid-3",
                  desc="section-description", head="h4", body="p")
    rows = list(csv.DictReader(open(os.path.join(project, "sources.csv"))))
    if not rows:
        raise SystemExit("%s/sources.csv is empty" % project)
    cards = []
    for r in rows:
        tier = (r.get("tier") or "").strip().lower()
        badge = ""
        if tier in TIER_LABEL:
            badge = ('<span style="display:inline-block;font-size:0.72rem;'
                     'letter-spacing:0.06em;text-transform:uppercase;padding:2px 8px;'
                     'border-radius:99px;background:rgba(148,163,184,0.15);'
                     'color:#94a3b8;margin-left:8px;" title="%s">%s</span>'
                     % (TIER_NOTE[tier], TIER_LABEL[tier]))
        note = (r.get("note") or "").strip()
        hc = t["head"].split()[0]
        bc = t["body"].split()[0]
        cards.append(
            '                    <div class="insight-card">\n'
            '                        <%s><a href="%s" target="_blank" rel="noopener" '
            'style="color:inherit;text-decoration:underline;'
            'text-underline-offset:3px;text-decoration-color:rgba(148,163,184,0.5);">%s</a>%s</%s>\n'
            '                        <%s>%s%s</%s>\n'
            '                    </div>'
            % (t["head"], r["url"], r["name"], badge, hc,
               t["body"], r["covers"], (" &mdash; " + note) if note else "", bc))
    return ('''        <section class="%s">
            <div class="container">
                <div class="section-header fade-up">
                    <h2>Sources &amp; Citations</h2>
                    <p class="%s">
                        Every figure on this page traces to one of these, through a CSV in
                        <code>%s/</code>. Each is checked against its source query on every
                        build.
                    </p>
                </div>

                <div class="%s fade-up">
%s
                </div>
            </div>
        </section>
''' % (t["wrap"], t["desc"], project, t["grid"], "\n".join(cards)),
            ", ".join(
                '<a href="%s" class="footer-link" target="_blank" rel="noopener">%s</a>'
                % (r["url"], r["name"]) for r in rows))


def apply_to(page, check):
    project = project_for(page)
    if not project:
        return 0, 0
    src = open(page).read()
    sec, footer = render(project, theme_of(src))
    before = src

    block = MARK_START + "\n" + sec + "        " + MARK_END
    if MARK_START in src:
        src = re.sub(re.escape(MARK_START) + r".*?" + re.escape(MARK_END),
                     lambda _: block, src, count=1, flags=re.S)
    else:
        # Anchor before whichever closing block this page actually has. The
        # older hand-built pages end at "How This Was Built" and have no Related
        # Projects section at all, which is why a single hard-coded anchor threw.
        i = None
        for anchor in ("<h2>Related Projects</h2>", '<div class="project-link-box">',
                       "<h2>Let&rsquo;s Discuss", "<h2>Let's Discuss"):
            k = src.find(anchor)
            if k >= 0:
                j = src.rfind("<section", 0, k)
                if j < 0:
                    j = src.rfind("<div", 0, k)
                i = src.rfind("\n", 0, j) + 1
                break
        if i is None:
            # Every page has a footer; the oldest ones have nothing else in
            # common -- no Related Projects, no link box, not even a </main>.
            k = src.rindex("<footer")
            i = src.rfind("\n", 0, k) + 1
        src = src[:i] + block + "\n" + src[i:]

    # Footer line, replaced or inserted after the byline.
    if re.search(r"Sources:\s*<a", src):
        src = re.sub(r"Sources:\s*<a.*?(?=</p>)", "Sources: " + footer, src,
                     count=1, flags=re.S)
    else:
        m = re.search(r"(Data Analysis by Allan Ni&ntilde;al[^<]*)", src)
        if m:
            src = src[:m.end()] + "\n                Sources: " + footer + src[m.end():]

    if src == before:
        return 0, 0
    if not check:
        open(page, "w").write(src)
    return 1, 0 if check else 1


def main():
    check = "--check" in sys.argv
    stale = changed = skipped = 0
    for page in sorted(glob.glob("projects/*.html")):
        s, c = apply_to(page, check)
        if s:
            stale += 1
            changed += c
            print("  %-46s %s" % (page, "STALE" if check else "updated"))
        elif project_for(page) is None:
            skipped += 1
    print("%d page(s) %s, %d without a declared project"
          % (stale, "stale" if check else "updated", skipped))
    sys.exit(1 if (check and stale) else 0)


if __name__ == "__main__":
    main()
