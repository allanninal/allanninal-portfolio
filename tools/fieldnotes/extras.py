#!/usr/bin/env python3
"""Feature image and "fix, as a flow" blocks, matching the older field-notes sections.

Kept out of build_section.py so the generator stays readable; both are pure string
builders with no state.
"""
import html as H


def esc(t):
    return H.escape(str(t), quote=False)


def feature(cfg: dict, g: dict) -> str:
    """Feature image figure.

    Photos are reused from the ones already licensed and published elsewhere on this
    site, so each credit is carried forward verbatim from the page it came from
    rather than re-derived. A wrong attribution is worse than no photo.
    """
    f = g.get("feature")
    if not f:
        return ""
    src = "/%s/assets/img/%s/feature.jpg" % (cfg["section"], g["slug"])
    utm = "?utm_source=allanninal_dev&amp;utm_medium=referral"
    return (
        '<figure class="feature-img">\n'
        '<img src="%s" alt="%s" width="1200" height="630" loading="eager" decoding="async">\n'
        '<figcaption>Photo by <a href="%s%s" rel="noopener nofollow" target="_blank">%s</a>'
        ' on <a href="https://unsplash.com/%s" rel="noopener nofollow" target="_blank">Unsplash</a>'
        '</figcaption>\n</figure>'
        % (src, H.escape(f["alt"], quote=True), f["profile"], utm,
           esc(f["photographer"]), utm)
    )


def flow(g: dict) -> str:
    """The "fix, as a flow" section the older guides carry between why and how."""
    if not g.get("flow_intro"):
        return ""
    return ('\n<h2>The fix, as a flow</h2>\n<p>%s</p>\n%s\n'
            % (g["flow_intro"], g.get("diagram_fix", "")))
