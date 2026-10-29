import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
  test('Login Validation – Empty Username and Password Fields', async ({ page }) => {
    // Step 1: Navigate to the login page
    await page.goto('https://www.saucedemo.com/');
    // Verify the login button is visible as an indication the page loaded
    await expect(page.getByRole('button', { name: 'Login' })).toBeVisible();

    // Step 2: Leave both Username and Password fields empty and click Login
    await page.getByRole('button', { name: 'Login' }).click();
    const usernameError = page.getByText('Epic sadface: Username is required', { exact: true });
    await expect(usernameError).toBeVisible();

    // Step 3: Enter a valid username, keep Password empty, click Login
    await page.getByRole('textbox', { name: 'Username' }).fill('standard_user');
    // Password field remains empty
    await page.getByRole('button', { name: 'Login' }).click();
    const passwordError = page.getByText('Epic sadface: Password is required', { exact: true });
    await expect(passwordError).toBeVisible();
  });
});