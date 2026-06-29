import { test, expect } from '@playwright/test';

// Asserts the canonical TemplateInfo download bar. Edition-aware: the Pro
// edition swaps the bar for a "Pro edition — live preview" strip with a locked
// Get-Pro link. Requires playwright.config.ts to set PUBLIC_TEMPLATE_HUB_URL.

const isPro = process.env.PUBLIC_EDITION === 'pro';
const barName = isPro
  ? /Pro edition — live preview/i
  : /Free template — download or fork/i;

test.describe('TemplateInfo download bar', () => {
  test('renders the canonical links with correct hrefs', async ({ page }) => {
    await page.goto('/');
    const bar = page.getByRole('complementary', { name: barName });
    await expect(bar).toBeVisible();

    const slug = 'indie-hacker-portfolio';
    await expect(bar.getByRole('link', { name: /All 365/i })).toHaveAttribute(
      'href',
      /templates\.allanninal\.dev/
    );

    if (isPro) {
      await expect(bar.getByRole('link', { name: /Get Pro static/i })).toHaveAttribute(
        'href',
        'https://www.linkedin.com/in/allanninal/'
      );
      await expect(bar.getByRole('link', { name: /Download free/i })).toHaveAttribute(
        'href',
        new RegExp(`/downloads/${slug}-static\\.zip$`)
      );
      return;
    }

    await expect(bar.getByRole('link', { name: /Download static/i })).toHaveAttribute(
      'href',
      new RegExp(`/downloads/${slug}-static\\.zip$`)
    );
    await expect(bar.getByRole('link', { name: /Source \(Astro\)/i })).toHaveAttribute(
      'href',
      new RegExp(`/downloads/${slug}-source\\.zip$`)
    );
    await expect(bar.getByRole('link', { name: /Build with me/i })).toHaveAttribute(
      'href',
      'https://www.linkedin.com/in/allanninal/'
    );
  });

  test('contains zero github.com links', async ({ page }) => {
    await page.goto('/');
    const bar = page.getByRole('complementary', { name: barName });
    const hrefs = await bar
      .locator('a')
      .evaluateAll((els) => els.map((e) => e.getAttribute('href') || ''));
    expect(hrefs.filter((h) => h.includes('github.com'))).toEqual([]);
  });
});
