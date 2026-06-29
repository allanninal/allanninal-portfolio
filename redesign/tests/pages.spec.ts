import { test, expect } from '@playwright/test';

test.describe('Indie Hacker Portfolio — page structure', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('page has correct title', async ({ page }) => {
    await expect(page).toHaveTitle(/Allan Ninal.*Indie Hacker/i);
  });

  test('page has meta description', async ({ page }) => {
    const desc = await page.getAttribute('meta[name="description"]', 'content');
    expect(desc).toBeTruthy();
    expect(desc!.length).toBeGreaterThan(20);
  });

  test('page has canonical link', async ({ page }) => {
    const canonical = await page.getAttribute('link[rel="canonical"]', 'href');
    expect(canonical).toBeTruthy();
  });

  test('page has OG image meta', async ({ page }) => {
    const ogImage = await page.getAttribute('meta[property="og:image"]', 'content');
    expect(ogImage).toBeTruthy();
    expect(ogImage).toContain('og-image.png');
  });

  test('page has twitter card meta', async ({ page }) => {
    const card = await page.getAttribute('meta[name="twitter:card"]', 'content');
    expect(card).toBe('summary_large_image');
  });

  test('page has JSON-LD Person schema', async ({ page }) => {
    const ldJson = await page.evaluate(() => {
      const scripts = Array.from(document.querySelectorAll('script[type="application/ld+json"]'));
      return scripts.map(s => JSON.parse(s.textContent || '{}'));
    });
    const person = ldJson.find(s => s['@type'] === 'Person');
    expect(person).toBeTruthy();
    expect(person.name).toBe('Allan Ninal');
    expect(Array.isArray(person.makesOffer)).toBe(true);
    expect(person.makesOffer.length).toBeGreaterThan(0);
  });

  test('favicon is present', async ({ page }) => {
    const favicon = await page.getAttribute('link[rel="icon"]', 'href');
    expect(favicon).toContain('favicon.svg');
  });
});

test.describe('Indie Hacker Portfolio — sections', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('hero section is visible with name', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('Allan Ninal');
  });

  test('revenue stats section is visible', async ({ page }) => {
    await expect(page.locator('[aria-labelledby="stats-heading"]')).toBeVisible();
  });

  test('revenue stats show MRR', async ({ page }) => {
    const statsSection = page.locator('[aria-labelledby="stats-heading"]');
    await expect(statsSection).toContainText('$5,540');
    await expect(statsSection).toContainText('MRR');
  });

  test('products grid section is visible', async ({ page }) => {
    await expect(page.locator('#products')).toBeVisible();
  });

  test('products grid shows 5 products', async ({ page }) => {
    const cards = page.locator('[role="listitem"][class*="product-card"]');
    // Actually check articles in the products grid
    const articles = page.locator('#products article');
    await expect(articles).toHaveCount(5);
  });

  test('product cards show status badges', async ({ page }) => {
    const liveBadges = page.locator('.badge-live');
    const sunsetBadges = page.locator('.badge-sunset');
    const soldBadges = page.locator('.badge-sold');
    await expect(liveBadges).toHaveCount(3);
    await expect(sunsetBadges).toHaveCount(1);
    await expect(soldBadges).toHaveCount(1);
  });

  test('building now section is visible', async ({ page }) => {
    await expect(page.locator('#building')).toBeVisible();
    await expect(page.locator('[aria-labelledby="building-heading"]')).toContainText('VaultNote');
  });

  test('about section is visible', async ({ page }) => {
    await expect(page.locator('#about')).toBeVisible();
  });

  test('newsletter section is visible', async ({ page }) => {
    await expect(page.locator('#newsletter')).toBeVisible();
    await expect(page.locator('[aria-labelledby="newsletter-heading"]')).toBeVisible();
  });

  test('newsletter has subscribe form', async ({ page }) => {
    const form = page.locator('form[aria-label="Subscribe to newsletter"]');
    await expect(form).toBeVisible();
    await expect(form.locator('input[type="email"]')).toBeVisible();
    await expect(form.locator('button[type="submit"]')).toBeVisible();
  });

  test('contact section is visible', async ({ page }) => {
    await expect(page.locator('#contact')).toBeVisible();
  });
});
