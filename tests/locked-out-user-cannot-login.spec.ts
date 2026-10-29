import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
  test('Locked Out User Cannot Login', async ({ page }) => {
    // 1. Navigate to login page
    await page.goto('https://www.saucedemo.com/');
    await expect(page.getByRole('form', { name: 'Login' })).toBeVisible();

    // 2. Enter username "locked_out_user" and password "secret_sauce"
    await page.getByPlaceholder('Username').fill('locked_out_user');
    await page.getByPlaceholder('Password').fill('secret_sauce');

    // 3. Click Login
    await page.getByRole('button', { name: 'Login' }).click();

    // Expected result: Error banner displayed: "Epic sadface: Sorry, this user has been locked out."
    const errorBanner = page.locator('[data-test="error"]');
    await expect(errorBanner).toBeVisible();
    await expect(errorBanner).toContainText('Epic sadface: Sorry, this user has been locked out.');
    
    // Verify user stays on login page
    await expect(page).toHaveURL('https://www.saucedemo.com/');
  });
});
