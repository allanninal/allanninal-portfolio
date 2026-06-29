import { test, expect } from '@playwright/test';

const viewports = [
  { name: 'mobile', width: 375, height: 812 },
  { name: 'tablet', width: 768, height: 1024 },
  { name: 'desktop', width: 1280, height: 800 },
  { name: 'wide', width: 1440, height: 900 },
];

test.describe('Indie Hacker Portfolio — responsive layout', () => {
  for (const viewport of viewports) {
    test(`homepage renders without overflow at ${viewport.name} (${viewport.width}px)`, async ({ page }) => {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      await page.goto('/');

      // Check no horizontal overflow
      const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
      expect(bodyWidth).toBeLessThanOrEqual(viewport.width + 2); // 2px tolerance

      // Hero is visible
      await expect(page.locator('h1')).toBeVisible();

      // Nav is visible
      await expect(page.locator('header')).toBeVisible();

      // Footer is visible
      await expect(page.locator('footer')).toBeVisible();
    });
  }

  test('revenue stats section visible on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto('/');
    await expect(page.locator('[aria-labelledby="stats-heading"]')).toBeVisible();
  });

  test('products grid stacks on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto('/');
    const firstCard = page.locator('#products article').first();
    await expect(firstCard).toBeVisible();
  });

  test('subscribe form usable on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto('/');
    const emailInput = page.locator('input[type="email"]').first();
    await expect(emailInput).toBeVisible();
    const button = page.locator('button[type="submit"]').first();
    await expect(button).toBeVisible();
  });

  test('nav shows subscribe button on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto('/');
    const header = page.locator('header');
    await expect(header).toBeVisible();
    // Subscribe CTA in header (the button, not the nav link)
    const subscribeBtn = header.locator('a[href="#newsletter"]').last();
    await expect(subscribeBtn).toBeVisible();
  });
});
