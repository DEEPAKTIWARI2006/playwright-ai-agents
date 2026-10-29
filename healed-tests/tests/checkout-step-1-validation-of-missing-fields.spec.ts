import { test, expect } from '@playwright/test';

// spec: Swag Labs E-Commerce Application – Test Plan
// test case: TC-E2E-002

test.describe('Checkout Step 1 – Validation of Missing Fields', () => {
  test('Checkout Step 1 – Validation of Missing Fields', async ({ page }) => {
    // Preconditions: User is on /checkout-step-one.html
    // Note: Since the provided snapshot is of the login page, we must authenticate to reach the checkout flow
    await page.goto('https://www.saucedemo.com/');
    await page.getByPlaceholder('Username').fill('standard_user');
    await page.getByPlaceholder('Password').fill('secret_sauce');
    await page.locator('[data-test="login-button"]').click();
    
    // Navigate to checkout step one (Adding an item to cart first to enable checkout flow)
    await page.locator('[data-test="add-to-cart-sauce-labs-backpack"]').click();
    await page.locator('.shopping_cart_link').click();
    await page.locator('[data-test="checkout"]').click();

    // 1. Leave all fields empty and click "Continue"
    await page.locator('[data-test="continue"]').click();
    await expect(page.locator('[data-test="error"]')).toContainText('Error: First Name is required');

    // 2. Enter First Name only, leave Last Name and Postal Code empty, click "Continue"
    await page.locator('[data-test="firstName"]').fill('John');
    await page.locator('[data-test="continue"]').click();
    await expect(page.locator('[data-test="error"]')).toContainText('Error: Last Name is required');

    // 3. Enter First and Last Name, leave Postal Code empty, click "Continue"
    await page.locator('[data-test="lastName"]').fill('Doe');
    await page.locator('[data-test="continue"]').click();
    await expect(page.locator('[data-test="error"]')).toContainText('Error: Postal Code is required');
  });
});