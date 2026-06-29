import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.describe('Indie Hacker Portfolio — accessibility', () => {
  test('homepage passes axe a11y checks', async ({ page }) => {
    await page.goto('/');
    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze();
    expect(results.violations).toEqual([]);
  });

  test('404 page passes axe a11y checks', async ({ page }) => {
    await page.goto('/404/');
    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze();
    expect(results.violations).toEqual([]);
  });

  // Pro-only page — present only when PUBLIC_EDITION=pro.
  test('teardowns page passes axe a11y checks (Pro)', async ({ page }) => {
    test.skip(process.env.PUBLIC_EDITION !== 'pro', 'Pro-only page');
    await page.goto('/teardowns/');
    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze();
    expect(results.violations).toEqual([]);
  });

  test('homepage has skip to content link', async ({ page }) => {
    await page.goto('/');
    const skip = page.locator('a[href="#main-content"]');
    await expect(skip).toBeAttached();
  });

  test('homepage main landmark exists', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('main#main-content')).toBeVisible();
  });

  test('all images have alt text', async ({ page }) => {
    await page.goto('/');
    const images = await page.locator('img').all();
    for (const img of images) {
      const alt = await img.getAttribute('alt');
      expect(alt, `Image missing alt text`).not.toBeNull();
    }
  });

  test('interactive elements have accessible names', async ({ page }) => {
    await page.goto('/');
    // All links must have accessible text
    const links = await page.locator('a').all();
    for (const link of links) {
      const text = await link.textContent();
      const ariaLabel = await link.getAttribute('aria-label');
      const ariaLabelledBy = await link.getAttribute('aria-labelledby');
      const hasAccessibleName = (text?.trim() || ariaLabel || ariaLabelledBy);
      expect(hasAccessibleName, `Link missing accessible name`).toBeTruthy();
    }
  });

  test('subscribe form has labeled email input', async ({ page }) => {
    await page.goto('/');
    const emailInput = page.locator('input[type="email"]#newsletter-email');
    await expect(emailInput).toBeVisible();
    // Verify the label is associated
    const label = page.locator('label[for="newsletter-email"]');
    await expect(label).toBeAttached();
  });
});
