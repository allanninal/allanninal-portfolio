# Indie Hacker Portfolio — Day 14

**Live demo:** https://templates.allanninal.dev/indie-hacker-portfolio/

A personal portfolio template for indie hackers who build and ship multiple products in public. Features real revenue stats, product cards with status badges (live/sunset/sold), a "what I'm building now" section, and a Buttondown newsletter signup.

## Visual register

- **Palette:** Warm paper `#F8F6F1` base · Electric blue `#2563EB` accent · Light-only
- **Typography:** Plus Jakarta Sans (headings + body) · JetBrains Mono (numeric stats only)
- **Persona:** Builder shipping micro-SaaS in public — not a corporate developer portfolio

## Key sections

| Section | Description |
|---------|-------------|
| Hero | Avatar, name, tagline, social links, dual CTA |
| Revenue Stats | Live MRR · Lifetime revenue · Active users — monospace big numbers |
| Products Grid | 5 cards with status badges (Live/Sunset/Sold), MRR, users, launch date, tech stack |
| Building Now | Current project with status, description, and beta link |
| About / Story | First-person founder-journey bio + values grid |
| Newsletter | Buttondown embed with subscriber count and cadence signal |
| Contact | LinkedIn primary, email secondary, Ko-fi support link |

## Customisation

Edit `src/data/maker.ts` to personalise:
- `maker` — your name, bio, socials, email
- `products[]` — your shipped products with metrics
- `currentProject` — what you're building right now
- `stats` — update when MRR changes (push to redeploy)
- `newsletter` — your Buttondown slug and subscriber count

## Newsletter provider

Defaults to **Buttondown** (free tier, open archive, privacy-friendly). Change `newsletter.buttondown.slug` in `src/data/maker.ts` to your Buttondown username.

## Deploy to GitHub Pages

```bash
# 1. Install dependencies
npm install

# 2. Build for your sub-path
PUBLIC_BASE_PATH=/your-slug/ npm run build

# 3. Preview locally
npm run preview
```

Or use the root `.github/workflows/pages.yml` in this monorepo — the template is wired into the CI pipeline.

## Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `PUBLIC_SITE_URL` | `https://templates.allanninal.dev` | Canonical site URL for sitemap |
| `PUBLIC_BASE_PATH` | `/indie-hacker-portfolio/` | Sub-path for GH Pages deploy |
| `PUBLIC_BUTTONDOWN_SLUG` | `allanninal` | Buttondown username (informational — form uses hardcoded action URL) |

## Stack

- [Astro](https://astro.build) v4 — static output
- [Tailwind CSS](https://tailwindcss.com) v3
- [Plus Jakarta Sans](https://fonts.google.com/specimen/Plus+Jakarta+Sans) — variable font via `@fontsource-variable`
- [JetBrains Mono](https://www.jetbrains.com/lp/mono/) — for numeric displays via `@fontsource`
- [Buttondown](https://buttondown.email) — newsletter embed
- Playwright — E2E + a11y tests
- LHCI — Lighthouse CI

## License

MIT — free to use, modify, and deploy commercially. Attribution appreciated but not required.
