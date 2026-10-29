import { test, expect } from '@playwright/test';

test.describe('AuthPage', () => {
  test('Valid Login with Standard User', async ({ page }) => {
    // 1. Navigate to https://www.saucedemo.com/
    await page.goto('https://www.saucedemo.com/');
    await expect(page.getByPlaceholder('Username')).toBeVisible();
    await expect(page.getByPlaceholder('Password')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Login' })).toBeVisible();

    // 2. Enter username "standard_user" and password "secret_sauce"
    await page.getByPlaceholder('Username').fill('standard_user');
    await page.getByPlaceholder('Password').fill('secret_sauce');

    // 3. Click the Login button
    await page.getByRole('button', { name: 'Login' }).click();

    // Expected Results: URL changes to https://www.saucedemo.com/inventory.html
    await expect(page).toHaveURL('https://www.saucedemo.com/inventory.html');
    
    // Expected Results: Inventory page loads
    // Note: Inventory page elements were not provided in the snapshot, 
    // verifying via URL and absence of login page.
    await expect(page.getByPlaceholder('Username')).not.toBeVisible();
  });
});
