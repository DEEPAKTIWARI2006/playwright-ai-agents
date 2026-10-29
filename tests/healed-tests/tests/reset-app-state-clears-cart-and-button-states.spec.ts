import { test, expect } from '@playwright/test';

// spec: Swag Labs E-Commerce Application – Test Plan
// seed: N/A (Precondition: User has added multiple items to the cart)

test.describe('Global Navigation', () => {
  test('Reset App State – Clears Cart and Button States', async ({ page }) => {
    // Setup: Login and add items to cart to satisfy preconditions
    await page.goto('https://www.saucedemo.com/');
    await page.fill('[data-test="username"]', 'standard_user');
    await page.fill('[data-test="password"]', 'secret_sauce');
    await page.click('[data-test="login-button"]');

    // Add multiple items to the cart
    await page.click('[data-test="add-to-cart-sauce-labs-backpack"]');
    await page.click('[data-test="add-to-cart-sauce-labs-bike-light"]');

    // 1. Open side menu and click "Reset App State"
    await page.click('#react-burger-menu-btn');
    // Wait for the reset button to become visible before clicking to avoid timeout
    await page.waitForSelector('[data-test="reset-app-state"]', { state: 'visible' });
    await page.click('[data-test="reset-app-state"]');

    // Verify "Add to cart" buttons revert on inventory page
    await expect(page.locator('[data-test="add-to-cart-sauce-labs-backpack"]')).toHaveText('Add to cart');
    await expect(page.locator('[data-test="add-to-cart-sauce-labs-bike-light"]')).toHaveText('Add to cart');

    // 2. Verify cart badge is no longer displayed
    const cartBadge = page.locator('.shopping_cart_badge');
    await expect(cartBadge).not.toBeVisible();
  });
});
