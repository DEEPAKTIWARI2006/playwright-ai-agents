import { test, expect } from '@playwright/test';

// spec: Swag Labs E-Commerce Application – Test Plan
// seed: N/A (Precondition: User has at least one item in the cart and is on /cart.html)

test.describe('Checkout Step 1 – Enter Valid Customer Information', () => {
  test('TC-E2E-001: Checkout Step 1 – Enter Valid Customer Information', async ({ page }) => {
    // Precondition: User has at least one item in the cart and is on /cart.html
    // Since the snapshot only covers the login page, we must first authenticate and add an item to the cart
    await page.goto('https://www.saucedemo.com/');
    await page.getByPlaceholder('Username').fill('standard_user');
    await page.getByPlaceholder('Password').fill('secret_sauce');
    // Updated selector for the login button – the site uses an <input> with id="login-button"
    await page.click('#login-button');
    
    // Add an item to cart to satisfy precondition
    await page.click('button[data-test="add-to-cart-sauce-labs-backpack"]');
    await page.click('a.shopping_cart_link');

    // 1. Click the "Checkout" button
    await page.click('button[data-test="checkout"]');
    await expect(page).toHaveURL(/.*checkout\.html/);

    // 2. Enter First Name "John", Last Name "Doe", and Zip/Postal Code "12345"
    // Locators based on standard SauceDemo accessible labels
    await page.getByPlaceholder('First Name').fill('John');
    await page.getByPlaceholder('Last Name').fill('Doe');
    await page.getByPlaceholder('Zip/Postal Code').fill('12345');

    // 3. Click "Continue"
    await page.click('button[data-test="continue"]');

    // Expected results: User reaches step-2 summary without errors.
    await expect(page).toHaveURL(/.*checkout-step-two\.html/);
    await expect(page.getByText('Your Checkout Summary')).toBeVisible();
  });
});
