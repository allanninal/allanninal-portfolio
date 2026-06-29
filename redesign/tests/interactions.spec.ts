import { test, expect } from '@playwright/test';

test.describe('Indie Hacker Portfolio — interactions', () => {
  test('nav links scroll to sections', async ({ page }) => {
    await page.goto('/');

    // Click Products nav link
    await page.locator('header a[href="#products"]').click();
    // Products section should be in view
    await expect(page.locator('#products')).toBeInViewport({ ratio: 0.1 });
  });

  test('hero CTA scrolls to newsletter', async ({ page }) => {
    await page.goto('/');
    await page.locator('a[href="#newsletter"]').first().click();
    await expect(page.locator('#newsletter')).toBeInViewport({ ratio: 0.1 });
  });

  test('header subscribe button scrolls to newsletter', async ({ page }) => {
    await page.goto('/');
    await page.locator('header a[href="#newsletter"]').first().click();
    await expect(page.locator('#newsletter')).toBeInViewport({ ratio: 0.1 });
  });

  test('subscribe form validates email', async ({ page }) => {
    await page.goto('/');
    // Scroll to newsletter
    await page.locator('#newsletter').scrollIntoViewIfNeeded();
    const form = page.locator('form[aria-label="Subscribe to newsletter"]');
    const submit = form.locator('button[type="submit"]');
    // Try submitting without email — browser validation should fire
    await submit.click();
    const emailInput = form.locator('input[type="email"]');
    // The input should be marked invalid by the browser
    const isValid = await emailInput.evaluate((el: HTMLInputElement) => el.validity.valid);
    expect(isValid).toBe(false);
  });

  test('product cards have hover state (CSS)', async ({ page }) => {
    await page.goto('/');
    const firstCard = page.locator('#products article').first();
    await expect(firstCard).toBeVisible();
    // Verify the card element exists and has the product-card class
    const hasClass = await firstCard.evaluate(el => el.classList.contains('product-card'));
    expect(hasClass).toBe(true);
  });

  test('social links open correctly', async ({ page }) => {
    await page.goto('/');
    const githubLink = page.locator('a[aria-label="GitHub profile"]').first();
    await expect(githubLink).toHaveAttribute('href', 'https://github.com/allanninal');
    await expect(githubLink).toHaveAttribute('target', '_blank');
  });

  test('404 page has go home link', async ({ page }) => {
    await page.goto('/404/');
    // Find the "Go home" link specifically (not the header CTA)
    const homeLink = page.locator('a.btn-primary[href="/"]');
    await expect(homeLink).toBeVisible();
  });
});
