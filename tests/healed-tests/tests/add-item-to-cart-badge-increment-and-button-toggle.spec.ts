import { test, expect } from '@playwright/test';

/**
 * Test Case: TC-CRT-001
 * Requirement: REQ-CRT-001
 * Title: Add Item to Cart – Badge Increment and Button Toggle
 */
test.describe('Cart Management', () => {
  test('Add Item to Cart – Badge Increment and Button Toggle', async ({ page }) => {
    // Precondition: User is on inventory page
    await page.goto('https://www.saucedemo.com/');
    await page.locator('[data-test="username"]').fill('standard_user');
    await page.locator('[data-test="password"]').fill('secret_sauce');
    await page.locator('[data-test="login-button"]').click();

    // 1. Click "Add to cart" on a product card
    const firstAddToCartBtn = page.locator('[data-test="add-to-cart-sauce-labs-backpack"]');
    await firstAddToCartBtn.click();

    // Expected Result: Button label changes to "Remove" and cart badge displays "1"
    // After clicking, the button's data-test attribute changes to "remove-sauce-labs-backpack".
    const firstRemoveBtn = page.locator('[data-test="remove-sauce-labs-backpack"]');
    await expect(firstRemoveBtn).toHaveText('Remove');
    const cartBadge = page.locator('.shopping_cart_badge');
    await expect(cartBadge).toHaveText('1');

    // 2. Click "Add to cart" on a second product
    const secondAddToCartBtn = page.locator('[data-test="add-to-cart-sauce-labs-bike-light"]');
    await secondAddToCartBtn.click();

    // Expected Result: Cart badge updates to "2"
    await expect(cartBadge).toHaveText('2');
  });
});
