import { test, expect } from '@playwright/test';

/**
 * Test Case: TC-CRT-004
 * Requirement: REQ-CRT-004
 * Title: Cart View – Verify Item Breakdown
 */
test.describe('Cart Management', () => {
  test('Cart View – Verify Item Breakdown', async ({ page }) => {
    // Preconditions: User has added a single product to the cart
    // Since the current snapshot only shows the login page, we must first authenticate and add an item
    await page.goto('https://www.saucedemo.com/');
    await page.locator('[data-test="username"]').fill('standard_user');
    await page.locator('[data-test="password"]').fill('secret_sauce');
    await page.locator('[data-test="login-button"]').click();

    // Add a single product to the cart to satisfy precondition
    // Using data-test attributes common to SauceDemo
    await page.locator('[data-test="add-to-cart-sauce-labs-backpack"]').click();

    // 1. Click the shopping cart badge to open /cart.html
    await page.locator('.shopping_cart_link').click();

    // Verify Cart page loads and contains expected elements
    await expect(page).toHaveURL(/.*cart.html/);
    
    // Verify quantity (1) is displayed in the cart item
    await expect(page.locator('.cart_item')).toBeVisible();
    await expect(page.locator('.cart_item').locator('.inventory_item_name')).toBeVisible();
    await expect(page.locator('.cart_item').locator('.inventory_item_desc')).toBeVisible();
    await expect(page.locator('.cart_item').locator('.inventory_item_price')).toBeVisible();
    
    // Verify the badge quantity is 1
    await expect(page.locator('.shopping_cart_badge')).toHaveText('1');

    // Verify "Continue Shopping" and "Checkout" buttons are present
    await expect(page.locator('[data-test="continue-shopping"]')).toBeVisible();
    await expect(page.locator('[data-test="checkout"]')).toBeVisible();

    // Final expectation: Displayed item details match the product added from inventory
    // We added the backpack, so we verify the name contains 'Backpack'
    await expect(page.locator('.inventory_item_name')).toContainText('Sauce Labs Backpack');
  });
});
