# Pro edition — Indie Hacker Portfolio

This template's Pro edition is **content-only** — there is no bundled
photography (the maker persona keeps the initials-avatar design). Build it with
`PUBLIC_EDITION=pro npm run build`.

## Pro-only content
- `src/pages/teardowns.astro` — a standalone **product teardowns** page: a
  post-mortem deep-dive of every product (live, sunset, and sold) — the bet,
  the stack, the numbers, and the honest lesson. Built from the existing
  `products` data in `src/data/maker.ts` plus a `teardowns` map of extra
  per-product detail. The Pro nav adds a "Teardowns" link; the free edition
  redirects `/teardowns/` → `/#products`.
- `src/data/teardowns.ts` — the extra per-product narrative (`theBet`,
  `whatWorked`, `whatBroke`) keyed by product id.
- `LICENSE-PRO.md` — commercial, no-attribution license.

## Icons — `src/components/icons/*.astro`
Original 24×24 / 2px / `currentColor` SVG (`IconDownload`).
