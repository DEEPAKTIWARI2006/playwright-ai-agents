import { test, expect } from '@playwright/test';

/**
 * Test Case: TC-CRT-003 - Cart Persistence Across Refresh and Navigation
 * Requirement: REQ-CRT-003
 * Description: Verifies that items added to the cart persist after page refresh and navigation.
 */

test.describe('Cart Management', () => {
  test('Cart Persistence Across Refresh and Navigation', async ({ page }) => {
    // Preconditions: User has added at least one item to the cart
    // Since no seed file was provided for this specific scenario, we perform the setup actions
    await page.goto('https://www.saucedemo.com/');
    await page.fill('[data-test="username"]', 'standard_user');
    await page.fill('[data-test="password"]', 'secret_sauce');
    await page.click('[data-test="login-button"]');

    // Add an item to the cart to satisfy preconditions
    // Note: Locators for inventory page are based on standard SauceDemo patterns as they are not in the provided snapshot
    await page.click('[data-test="add-to-cart-sauce-labs-backpack"]');
    
    // Verify initial cart badge count
    const cartBadge = page.locator('.shopping_cart_badge');
    await expect(cartBadge).toHaveText('1');

    // 1. Refresh the browser (F5)
    await page.reload();

    // Expected Result: Cart badge still shows the same count; added items remain in cart.
    await expect(cartBadge).toHaveText('1');

    // 2. Navigate to a different page (e.g., open the sidebar, go to "About"), then return to inventory
    await page.click('#react-burger-menu-btn');
    // Note: SauceDemo does not have a literal "About" page in the standard demo, navigating to 'Logout' or 'All Items'
    await page.click('#logout_sidebar_link'); 
    
    // Return to inventory by logging back in
    await page.fill('[data-test="username"]', 'standard_user');
    await page.fill('[data-test="password"]', 'secret_sauce');
    await page.click('[data-test="login-button"]');

    // Expected Result: Cart state is unchanged.
    await expect(cartBadge).toHaveText('1');
    
    // Final verification: Navigate to cart to ensure item is actually there
    await page.click('.shopping_cart_link');
    await expect(page.locator('.cart_item')).toHaveCount(1);
  });
});
