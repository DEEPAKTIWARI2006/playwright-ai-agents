import { test, expect } from '@playwright/test';

// spec: Swag Labs E-Commerce Application – Test Plan
// seed: None provided

test.describe('Cart Management', () => {
  test('Remove Item from Cart – Badge Decrement', async ({ page }) => {
    // Precondition: Login and add two items to cart
    await page.goto('https://www.saucedemo.com/');
    await page.fill('[data-test="username"]', 'standard_user');
    await page.fill('[data-test="password"]', 'secret_sauce');
    await page.click('[data-test="login-button"]');

    // Adding two items to satisfy precondition
    await page.click('[data-test="add-to-cart-sauce-labs-backpack"]');
    await page.click('[data-test="add-to-cart-sauce-labs-bike-light"]');
    
    const cartBadge = page.locator('.shopping_cart_badge');
    await expect(cartBadge).toHaveText('2');

    // 1. Click "Remove" on one of the added product cards
    await page.click('[data-test="remove-sauce-labs-backpack"]');
    
    // Expected: Button reverts to "Add to cart" and cart badge decrements to "1"
    await expect(page.locator('[data-test="add-to-cart-sauce-labs-backpack"]')).toBeVisible();
    await expect(cartBadge).toHaveText('1');

    // 2. Navigate to Cart page and click "Remove" for the remaining item
    await page.click('.shopping_cart_link');
    await page.click('[data-test="remove-sauce-labs-bike-light"]');

    // Expected: Cart badge disappears (count 0) and cart list is empty
    await expect(cartBadge).not.toBeVisible();
    await expect(page.locator('.cart_item')).toHaveCount(0);
  });
});
