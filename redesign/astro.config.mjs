import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';
import tailwind from '@astrojs/tailwind';

const SITE = process.env.PUBLIC_SITE_URL || 'https://www.allanninal.dev';
const BASE = process.env.PUBLIC_BASE_PATH || '/';
const siteUrl = SITE.endsWith('/') ? SITE.slice(0, -1) : SITE;
const baseUrl = BASE.endsWith('/') ? BASE : `${BASE}/`;

export default defineConfig({
  site: siteUrl,
  base: BASE,
  output: 'static',
  trailingSlash: 'always',
  build: { format: 'directory' },
  integrations: [
    tailwind({ applyBaseStyles: false }),
    sitemap({ customPages: [`${siteUrl}${baseUrl}`] }),
  ],
});
