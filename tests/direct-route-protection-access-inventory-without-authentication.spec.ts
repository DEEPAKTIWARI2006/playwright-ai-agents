import { test, expect } from '@playwright/test';

test.describe('Direct Route Protection', () => {
  test('Access Inventory Without Authentication', async ({ page }) => {
    // 1. Enter URL https://www.saucedemo.com/inventory.html directly in the browser address bar
    await page.goto('https://www.saucedemo.com/inventory.html');

    // Application detects missing session and redirects to login page.
    await expect(page).toHaveURL('https://www.saucedemo.com/');

    // 2. Observe any displayed error message
    // Error banner indicates access requires login.
    // Based on Swag Labs behavior, an error message typically appears in a container with class 'error-message-container'
    const errorMessage = page.locator('[data-test="error"]');
    await expect(errorMessage).toBeVisible();
    await expect(errorMessage).toContainText('Epic sadface: Users must be logged in');
  });
});
