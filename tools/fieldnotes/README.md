# Field-notes generator

Generates `/email/`, `/aws/`, `/ci/`, `/cloudflare/` and `/seo/` — one HTML page per
problem, plus the section index.

    cd tools/fieldnotes/cloudflare && python3 build.py

Writes straight into the section directory at the repo root.

## Why it is here

The eight ecommerce sections were each built separately and drifted: different title
lengths, some with JSON-LD and some without, some with diagrams. This generator
exists so the next section cannot drift again — which only works if the generator
lives with the site instead of in a scratch directory that disappears.

## Layout

- `build_section.py` — page and index templates, and the metadata length checks
- `extras.py` — feature image figure, and the "fix, as a flow" section
- `diagrams.py` — `chain()` and `branch()`, which compute SVG geometry rather than
  taking hand-written coordinates
- `visuals_*.py` — the per-guide diagram content
- `img_picks.json` — which already-licensed photo each guide reuses, with its credit
- `<section>/guides*.py` — the writing
- `<section>/build.py` — the section's config

## Images

Photos are reused from the ones already licensed and published elsewhere on this
site. Each credit in `img_picks.json` was copied verbatim from the page the photo
already appears on, never re-derived — a wrong attribution is worse than no photo.
