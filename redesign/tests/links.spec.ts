// Link checking is handled by `npm run test:links` via linkinator.
// This spec verifies that critical internal links resolve correctly.
import { test, expect } from '@playwright/test';

test.describe('Indie Hacker Portfolio — internal links', () => {
  test('homepage loads with 200', async ({ page }) => {
    const response = await page.goto('/');
    expect(response?.status()).toBe(200);
  });

  test('404 page loads', async ({ page }) => {
    // Astro static 404 — accessed directly
    const response = await page.goto('/404/');
    expect(response?.status()).toBe(200); // static file serves 200 locally
  });

  test('sitemap.xml exists', async ({ page }) => {
    const response = await page.goto('/sitemap-index.xml');
    expect(response?.status()).toBe(200);
  });

  test('favicon.svg is accessible', async ({ page }) => {
    const response = await page.goto('/favicon.svg');
    expect(response?.status()).toBe(200);
  });

  test('og-image.png is accessible', async ({ page }) => {
    const response = await page.goto('/og-image.png');
    expect(response?.status()).toBe(200);
  });
});
