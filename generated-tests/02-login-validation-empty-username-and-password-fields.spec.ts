import { test, expect } from '@playwright/test';

test.describe('Login Validation', () => {
  test('Login Validation – Empty Username and Password Fields', async ({ page }) => {
    // 1. Navigate to the login page
    await page.goto('https://www.saucedemo.com/');
    await expect(page.getByRole('form', { name: 'Login' })).toBeVisible();

    // 2. Leave both Username and Password fields empty and click Login
    await page.getByRole('button', { name: 'Login' }).click();
    
    // Verification: Error banner displayed with message "Epic sadface: Username is required".
    const errorBanner = page.locator('[data-test="error"]');
    await expect(errorBanner).toBeVisible();
    await expect(errorBanner).toContainText('Epic sadface: Username is required');

    // 3. Enter a valid username, keep Password empty, click Login
    await page.getByPlaceholder('Username').fill('standard_user');
    await page.getByRole('button', { name: 'Login' }).click();

    // Verification: Error banner displayed with message "Epic sadface: Password is required".
    await expect(errorBanner).toBeVisible();
    await expect(errorBanner).toContainText('Epic sadface: Password is required');
  });
});
