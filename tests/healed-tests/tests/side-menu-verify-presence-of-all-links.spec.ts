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

    // 2. Locate the side navigation menu (updated selector)
    const menu = page.getByRole('navigation');
    // Ensure the menu is visible before checking its items
    await expect(menu).toBeVisible();

    // Verify that the menu contains the expected links
    await expect(menu.getByText('All Items')).toBeVisible();
    await expect(menu.getByText('About')).toBeVisible();
    await expect(menu.getByText('Logout')).toBeVisible();
    await expect(menu.getByText('Reset App State')).toBeVisible();
  });
});
