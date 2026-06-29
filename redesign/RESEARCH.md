# Indie Hacker Portfolio — Research Brief

> **Assumption:** A personal portfolio for an independent software maker who builds and ships multiple SaaS/micro-SaaS products. The audience is the IndieHackers / Hacker News / Twitter/X community. The site exists to establish credibility as a "builder," attract collaborators, grow a newsletter, and signal transparency via public revenue numbers. This is emphatically NOT a developer portfolio (Day 1) — there are no "case studies," no corporate employer history, and no recruiters in the audience.

---

## Audience & primary CTA

- **Who visits:** Other indie hackers (peer credibility signal), potential customers discovering the maker behind the product, journalists/newsletter writers doing "maker spotlight" pieces, developers considering collaboration.
- **Primary CTA:** Subscribe to newsletter ("Follow the journey").
- **Secondary CTAs:** Visit a live product, follow on X/Twitter, connect on LinkedIn.

---

## Persona

Following the established convention in this repo (Days 1, 9 use Allan's canonical handles directly), the persona uses **Allan Ninal** with the canonical socials from memory:
- GitHub: allanninal
- X/Twitter: allanninal
- LinkedIn: allanninal
- Email: landix.ninal@gmail.com

**Bio framing:** Builder, maker, shipping things in public since 2021. Believer that small products with happy users beat VC-funded moonshots. Based in Southeast Asia (UTC+8).

**Products (fictional, believable MRR range $500–$20k):**
1. **FormCraft** — Drag-and-drop form builder for small businesses. Status: Live. MRR: $3,200. Users: 1,847. Launched: March 2022.
2. **PingAlert** — Uptime monitoring with SMS + Slack alerts. Status: Live. MRR: $1,450. Users: 612. Launched: September 2022.
3. **DocuFlow** — PDF generation API for web apps. Status: Live. MRR: $890. Users: 341. Launched: February 2023.
4. **ListPilot** — Email list cleaning and validation SaaS. Status: Sunset. Peak MRR: $420. Launched: June 2021, sunset December 2022. (Lesson: solved wrong problem.)
5. **ShipKit** — Astro + Tailwind SaaS boilerplate. Status: Sold. Sale price: $8,500. Launched: January 2023, sold October 2023.

**Current project:** Building **VaultNote** — encrypted personal knowledge base with offline-first Markdown editor. In public beta, waitlist open.

**Newsletter:** "Ship It Weekly" — 2,847 subscribers, every Sunday, 5-minute read on indie hacking, revenue updates, and maker tools.

**Revenue totals:** $5,540 current MRR, $142,000 total lifetime revenue, 2,800 total active users.

---

## Reference sites (real indie hackers)

- https://levels.io — Pieter Levels; dark background, monospace numbers everywhere, brutal list of all projects with status, revenue shown publicly. The canonical indie hacker site. Very raw, no polish — we do the opposite: same transparency, but designed.
- https://marc.io — Marc Lou; clean light single-column, big product grid with MRR badges, social proof via big number, conversational bio. Closest visual reference to what we're building.
- https://tonydinh.com — Tony Dinh; light background, product cards with MRR and user count, brief story, newsletter. Excellent reference for the "transparent maker" register.
- https://coryzue.com — Cory Zue; clean, product cards, revenue public, blog integrated. Another solid reference.
- https://www.indiehackers.com — The IndieHackers platform itself; profile pages with MRR + product cards + interview format. Sets community expectations.

---

## Existing templates surveyed

- **brittanychiang.com-style Astro portfolios** — All optimized for job-seeking developers. Experience timelines, skill chips, recruiter-focused copy. Wrong register entirely.
- **Astro bento portfolios** — Single-page, bento grid, but no revenue stats, no product status badges, no newsletter capture. Missing the indie-hacker-specific signals.
- **Generic "maker portfolio"** templates — Very few exist; those that do are usually a simple list page with no real design system.
- **Saturated pattern:** Avatar + intro paragraph + link grid (effectively a link-in-bio). Zero data transparency, zero product metrics, no newsletter emphasis.
- **Missing in free tier:** An Astro template with (a) a revenue stats band (live MRR, lifetime revenue, users), (b) product cards with status badges (live/sunset/sold) and concrete metrics, (c) "what I'm building now" section, (d) newsletter capture, (e) Person schema.org with product-as-offer markup, (f) first-person founder-journey bio, (g) GH Pages ready.

---

## Must-have sections (in order)

1. **Hero** — avatar, name, one-liner ("I build small software products that solve real problems"), X/GitHub/LinkedIn/email row, newsletter CTA button. No hero image — face + numbers is the hero.
2. **Revenue stats band** — Three numbers, BIG, monospace: current MRR ($5,540), lifetime revenue ($142,000), active users (2,800). This is THE differentiating section — it does not exist in any other template in this roadmap.
3. **Shipped products grid** — 5 product cards. Each: product name, one-line description, status badge (Live / Sunset / Sold), MRR or peak MRR or sale price, user count, launch date, and two buttons (Visit product, Case notes). Cards must show the full arc — successes and the one sunset.
4. **What I'm building now** — Current project (VaultNote) with status, description, and a waitlist/beta link. This is the indie convention: shipping in public = accountability.
5. **Story / About** — First-person, casual, founder-journey copy. Not corporate bio. Starts with "I quit my job in 2021..." style opening. 3–4 short paragraphs.
6. **Newsletter signup** — "Ship It Weekly" — subscriber count, cadence, sample topics. Buttondown embed (same pattern as Day 11).
7. **Contact + socials** — LinkedIn primary, email secondary per project convention. Ko-fi link (no Patreon/Sponsors per project rule).
8. **Footer** — minimal: name, current year, "built with Astro", social icons.

---

## Visual register — differentiation from Days 1–13

**Taken registers to avoid:**
- Day 1: dark-default, indigo accent, Geist body — THE closest adjacent; must be maximally different
- Day 2: light, violet/cyan, bento dense
- Day 3: dark, lime accent, Geist Sans
- Day 4: light, coral/terracotta accent, DM Sans
- Day 5: light, forest green, Newsreader serif
- Day 6: Starlight theme, cobalt, IBM Plex
- Day 7: light, magenta/pink accent, Manrope
- Day 8: light, burnt-orange accent, premium minimal
- Day 9: light, editorial serif (Source Serif 4 + Inter Tight), no strong accent
- Day 10: dark, teal accent, Outfit + Geist Mono
- Day 11: light, oxblood/cream, Lora + Work Sans
- Day 12: light, aubergine/warm-white, Fraunces serif + Space Grotesk
- Day 13: dark, amber/near-black, Bricolage Grotesque + JetBrains Mono

**Day 14 direction — "scrappy-premium light" maker register:**

- **Mode:** Light-only. This is non-negotiable — Levels.io (dark) is the only dark indie hacker site, and it's famously ugly. Marc Lou, Tony Dinh, Cory Zue: all light. The community norm is light + data transparency.
- **Background:** `#F8F6F1` — warm off-white, slightly more saturated than Day 9's near-white. Reads as "paper on a sunny desk."
- **Accent:** **Electric blue — `#2563EB` (Tailwind blue-600)** — completely untaken across Days 1–13. Blue is the trust color of numbers and data. On a warm paper background, it pops without aggression. IndieHackers.com uses a similar blue. Hover: `#1D4ED8` (blue-700). This is NOT the violet of Day 2 (which is purple-family) — it's a true blue.
- **Text:** `#0F172A` (slate-900) for headings. `#334155` (slate-700) for body. `#64748B` (slate-500) for muted/labels.
- **Revenue numbers:** Displayed in **JetBrains Mono** weight 700 — monospace reinforces "real data, not marketing." This is the ONE place mono appears; it's a deliberate signal. Day 13 used JetBrains Mono throughout; Day 14 uses it only for numeric displays — the context differs completely.
- **Status badges:** pill-shaped. Live: `#DCFCE7` bg / `#15803D` text (green). Sunset: `#FEF9C3` bg / `#854D0E` text (amber). Sold: `#EFF6FF` bg / `#1D4ED8` text (blue).
- **Surface / cards:** White (`#FFFFFF`) cards on the warm off-white page — barely perceptible lift, no heavy shadows. Thin `#E2E8F0` borders (slate-200).
- **Accent hover state:** `#1D4ED8` (blue-700).

**Typography pairing (untaken):**
- **Headlines:** **Plus Jakarta Sans** — variable weight, modern humanist sans, rounded stroke endings that feel personal not corporate. At weight 800 it's confident; at 400 it's readable prose. NOT Bricolage, NOT Manrope, NOT Geist, NOT Outfit, NOT Inter.
- **Body:** **Plus Jakarta Sans** — same family, weight 400–500. Single-family approach keeps it cohesive. No serif at all — this is a data-forward page, not editorial.
- **Monospace (numbers only):** **JetBrains Mono** weight 700, only for revenue stats and metrics. Self-hosted via @fontsource.

**Density:** Medium. Not as sparse as Day 9 (editorial) nor as dense as Day 6 (docs). The product grid is the densest element; the hero and stats band are generous with whitespace. Think: a well-formatted spreadsheet with personality.

**Imagery:** No photography. Avatar is a CSS-generated circle with initials ("AN") and blue background. Product "icons" are colored SVG initials or emoji-adjacent SVG marks. No stock photography, no device mockups.

---

## Schema.org

Type: `Person` with:
- `name`, `url`, `email`, `image`
- `knowsAbout`: ["SaaS", "Indie Hacking", "Web Development", "Astro", "Tailwind CSS", "TypeScript"]
- `makesOffer` for each live product (type: `Offer`, `itemOffered`: `SoftwareApplication`)
- `sameAs`: [GitHub, X/Twitter, LinkedIn]
- `description`: bio text

---

## Static-only fit

- Revenue stats: hardcoded in `src/data/products.ts` — owner updates when MRR changes, pushes to redeploy. No API calls.
- Newsletter: Buttondown embed (same as Day 11 — proven pattern).
- Contact: LinkedIn link + mailto.
- Ko-fi: support link in footer.
- All content: zero CMS dependency.

---

## OG image direction

`#F8F6F1` warm paper background. "Allan Ninal" in Plus Jakarta Sans 800 at ~72px, `#0F172A`. Below: "$5,540 MRR · 2,800 users" in JetBrains Mono, blue accent. Bottom strip: "Indie Hacker · Builder · allanninal.dev". SVG committed as og-image.svg, rasterized to og-image.png. Size: 1200×630.

---

## Differentiation summary (vs Day 1 developer-portfolio)

| Dimension | Day 1 developer-portfolio | Day 14 indie-hacker-portfolio |
|-----------|--------------------------|-------------------------------|
| Mode | Dark-default | Light-only |
| Accent | Indigo (#6366F1) | Electric blue (#2563EB) |
| Background | #0B0F19 (near-black) | #F8F6F1 (warm paper) |
| Headline font | Geist body | Plus Jakarta Sans |
| Primary content | MDX case studies | Revenue stats + product metrics |
| Persona goal | Get hired / freelance clients | Grow newsletter + product users |
| Key differentiating section | Experience timeline | Revenue stats band + product status badges |
| Newsletter | Secondary CTA | Primary section with sub count |
| Schema | Person + SoftwareSourceCode | Person + multiple makesOffer |
| Density | Sparse editorial | Medium (data-forward) |
