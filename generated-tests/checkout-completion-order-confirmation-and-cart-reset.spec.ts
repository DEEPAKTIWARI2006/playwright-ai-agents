import { test, expect } from '@playwright/test';

/**
 * Test Case: TC-E2E-004
 * Title: Checkout Completion – Order Confirmation and Cart Reset
 * Requirement: REQ-CHK-004
 */

test.describe('Checkout Completion', () => {
  test('Order Confirmation and Cart Reset', async ({ page }) => {
    // Precondition: User is on Checkout Step 2 page with valid summary
    // Since the provided snapshot is only for the Login page, we must navigate and 
    // perform the necessary setup to reach Checkout Step 2.
    await page.goto('https://www.saucedemo.com/');
    await page.locator('[data-test="username"]').fill('standard_user');
    await page.locator('[data-test="password"]').fill('secret_sauce');
    await page.locator('[data-test="login-button"]').click();
    
    // Add an item to the cart to ensure it's not empty
    await page.locator('[data-test="add-to-cart-sauce-labs-backpack"]').click();
    await page.locator('.shopping_cart_link').click();
    await page.locator('[data-test="checkout"]').click();
    
    // Fill checkout information
    await page.locator('[data-test="firstName"]').fill('John');
    await page.locator('[data-test="lastName"]').fill('Doe');
    await page.locator('[data-test="postalCode"]').fill('12345');
    await page.locator('[data-test="continue"]').click();

    // 1. Click the "Finish" button
    await page.locator('[data-test="finish"]').click();

    // 2. Verify header reads "Thank you for your order!"
    const confirmationHeader = page.locator('.complete-header');
    await expect(confirmationHeader).toBeVisible();
    await expect(confirmationHeader).toHaveText('Thank you for your order!');

    // 3. Observe cart badge on the top navigation
    // Expected result: Badge is cleared (no number shown).
    const cartBadge = page.locator('.shopping_cart_badge');
    await expect(cartBadge).not.toBeVisible();
  });
});
