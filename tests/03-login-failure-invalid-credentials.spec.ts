import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
  test('Login Failure – Invalid Credentials', async ({ page }) => {
    // 1. Open login page
    await page.goto('https://www.saucedemo.com/');
    await expect(page.getByRole('form', { name: 'Login' })).toBeVisible();

    // 2. Enter username "standard_user" and an incorrect password "wrong_pass"
    await page.getByPlaceholder('Username').fill('standard_user');
    await page.getByPlaceholder('Password').fill('wrong_pass');

    // 3. Click Login
    await page.getByRole('button', { name: 'Login' }).click();

    // Expected Result: Error banner displayed
    const errorBanner = page.locator('[data-test="error"]');
    await expect(errorBanner).toBeVisible();
    await expect(errorBanner).toContainText('Epic sadface: Username and password do not match any user in this service');

    // Expected Result: User remains on login page; no redirection occurs.
    await expect(page).toHaveURL('https://www.saucedemo.com/');
  });
});
