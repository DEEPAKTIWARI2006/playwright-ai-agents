import { test, expect } from '@playwright/test';

test.describe('Login Failure – Invalid Credentials', () => {
  test('Login Failure – Invalid Credentials', async ({ page }) => {
    // 1. Open login page
    await page.goto('https://www.saucedemo.com/');

    // 2. Enter username "standard_user" and an incorrect password "wrong_pass"
    await page.getByLabel('Username').fill('standard_user');
    await page.getByLabel('Password').fill('wrong_pass');

    // 3. Click Login
    await page.getByRole('button', { name: 'Login' }).click();

    // Verify error banner displayed with expected text
    const errorBanner = page.getByText(
      'Epic sadface: Username and password do not match any user in this service'
    );
    await expect(errorBanner).toBeVisible();

    // Verify user remains on the login page (no redirection)
    await expect(page).toHaveURL('https://www.saucedemo.com/');

    // Verify login form is still visible
    await expect(page.getByLabel('Username')).toBeVisible();
    await expect(page.getByLabel('Password')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Login' })).toBeVisible();
  });
});
