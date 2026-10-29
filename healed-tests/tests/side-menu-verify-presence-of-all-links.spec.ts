import { test, expect } from '@playwright/test';

// spec: Swag Labs E-Commerce Application – Test Plan
// test case: TC-GLB-001 Side Menu – Verify Presence of All Links

test.describe('Global Navigation', () => {
  test('Side Menu – Verify Presence of All Links', async ({ page }) => {
    // Preconditions: User is logged in and on any internal page
    await page.goto('https://www.saucedemo.com/');
    await page.locator('[data-test="username"]').fill('standard_user');
    await page.locator('[data-test="password"]').fill('secret_sauce');
    await page.locator('[data-test="login-button"]').click();

    // 1. Click the hamburger (menu) icon
    await page.locator('#react-burger-menu-btn').click();

    // 2. Verify that the side menu contains the expected links.
    // Using role-based locators makes the test resilient to DOM class changes.
    await expect(page.getByRole('link', { name: 'All Items' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'About' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Logout' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Reset App State' })).toBeVisible();
  });
});
