import { test, expect } from '@playwright/test';

// spec: Swag Labs E-Commerce Application – Test Plan
// seed: N/A (Manual Login)

test.describe('Product Catalog', () => {
  test('Navigate to Product Detail Page and Return', async ({ page }) => {
    // Preconditions: User is logged in and on inventory page
    await page.goto('https://www.saucedemo.com/');
    await page.locator('[data-test="username"]').fill('standard_user');
    await page.locator('[data-test="password"]').fill('secret_sauce');
    await page.locator('[data-test="login-button"]').click();

    // 1. Click on a product title or image (e.g., "Sauce Labs Backpack")
    await page.locator('.inventory_item_name', { hasText: 'Sauce Labs Backpack' }).click();

    // 2. Verify that the detail page shows a high‑resolution image, product name, description, and price.
    await expect(page).toHaveURL(/.*inventory-item.html/);
    await expect(page.locator('.inventory_details_img')).toBeVisible();
    await expect(page.locator('.inventory_details_name')).toContainText('Sauce Labs Backpack');
    await expect(page.locator('.inventory_details_desc')).toBeVisible();
    await expect(page.locator('.inventory_details_price')).toBeVisible();

    // 3. Click the browser back button or the "Back to products" link
    await page.locator('[data-test="back-to-products"]').click();

    // Expected result: User returns to the inventory list, preserving previous sort order.
    await expect(page).toHaveURL(/.*inventory.html/);
    await expect(page.locator('.inventory_list')).toBeVisible();
  });
});
