import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
  test('Valid Login with Standard User', async ({ page }) => {
    // Step 1: Navigate to https://www.saucedemo.com/
    await page.goto('https://www.saucedemo.com/');

    // Verify the login page is displayed
    await expect(page.getByLabel('Username')).toBeVisible();
    await expect(page.getByLabel('Password')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Login' })).toBeVisible();

    // Step 2: Enter username "standard_user" and password "secret_sauce"
    await page.getByLabel('Username').fill('standard_user');
    await page.getByLabel('Password').fill('secret_sauce');

    // Step 3: Click the Login button
    await page.getByRole('button', { name: 'Login' }).click();

    // Expected result: URL changes to the inventory page
    await expect(page).toHaveURL('https://www.saucedemo.com/inventory.html');

    // Expected result: Inventory page loads within 1.5 seconds
    // TODO: Replace the selector with a reliable locator for an element that is present
    // on the inventory page (e.g., product list container). Using a generic selector for now.
    const inventoryContainer = page.locator('.inventory_list');
    await expect(inventoryContainer).toBeVisible({ timeout: 1500 });
  });
});
