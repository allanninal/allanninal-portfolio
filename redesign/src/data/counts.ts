/**
 * Live counts, read off the deployed tree at build time.
 *
 * Nothing in this file is typed by hand. Every figure the homepage shows —
 * guides published, templates shipped — is counted from the directories that
 * actually exist, so a number on the page cannot drift away from the site it
 * describes. Astro runs this once per build, on the server, so there is no
 * runtime cost.
 */
import fs from 'node:fs';
import path from 'node:path';

const siteRoot = path.resolve(process.cwd(), '..');

/** Sub-directories of a section, which is one per published page. */
function dirCount(rel: string, skip: string[] = ['assets', 'downloads', 'pro', '_astro']): number {
  try {
    return fs
      .readdirSync(path.join(siteRoot, rel), { withFileTypes: true })
      .filter(
        (e) =>
          e.isDirectory() &&
          !e.name.startsWith('_') &&
          !skip.includes(e.name) &&
          fs.existsSync(path.join(siteRoot, rel, e.name, 'index.html'))
      ).length;
  } catch {
    return 0;
  }
}

export const guideSections = [
  { href: '/woocommerce/', name: 'WooCommerce', group: 'commerce' as const },
  { href: '/shopify/', name: 'Shopify', group: 'commerce' as const },
  { href: '/bigcommerce/', name: 'BigCommerce', group: 'commerce' as const },
  { href: '/medusa/', name: 'Medusa', group: 'commerce' as const },
  { href: '/shopware/', name: 'Shopware', group: 'commerce' as const },
  { href: '/saleor/', name: 'Saleor', group: 'commerce' as const },
  { href: '/prestashop/', name: 'PrestaShop', group: 'commerce' as const },
  { href: '/magento/', name: 'Magento', group: 'commerce' as const },
  { href: '/aws/', name: 'AWS cost', group: 'platform' as const },
  { href: '/cloudflare/', name: 'Cloudflare', group: 'platform' as const },
  { href: '/ci/', name: 'GitHub Actions', group: 'platform' as const },
  { href: '/email/', name: 'Email & SES', group: 'platform' as const },
  { href: '/dns/', name: 'DNS & Domains', group: 'platform' as const },
  { href: '/seo/', name: 'Technical SEO', group: 'platform' as const },
  { href: '/stripe/', name: 'Stripe', group: 'api' as const },
];

export const guideCounts = guideSections.map((s) => ({ ...s, count: dirCount(s.href.replace(/\//g, '')) }));

export const counts = {
  guides: guideCounts.reduce((n, s) => n + s.count, 0),
  guideSections: guideSections.length,
  templates: dirCount('templates'),
  spreadsheets: dirCount('spreadsheets'),
  buildGuides: dirCount('build'),
};
