import { test, expect } from '@playwright/test';

/**
 * Test Case: TC-E2E-003
 * Title: Checkout Step 2 – Verify Summary Calculations and Tax
 * Requirement: REQ-CHK-003
 */
test.describe('Checkout Flow', () => {
  test('Checkout Step 2 – Verify Summary Calculations and Tax', async ({ page }) => {
    // Preconditions: User has completed Step 1 with valid info and has items in cart
    // Note: Since this is a standalone test, we must perform the setup to reach step 2.
    await page.goto('https://www.saucedemo.com/');
    await page.fill('#user-name', 'standard_user');
    await page.fill('#password', 'secret_sauce');
    await page.click('#login-button');

    // Add an item to the cart to ensure calculations have data
    await page.click('[data-test="add-to-cart-sauce-labs-backpack"]');
    await page.click('.shopping_cart_link');
    await page.click('[data-test="checkout"]');

    // Complete Step 1
    await page.fill('[data-test="firstName"]', 'Test');
    await page.fill('[data-test="lastName"]', 'User');
    await page.fill('[data-test="postalCode"]', '12345');
    await page.click('[data-test="continue"]');

    // 1. On /checkout-step-two.html, capture the listed item total
    const itemTotalText = await page.locator('.summary_subtotal_label').innerText();
    const itemTotal = parseFloat(itemTotalText.replace('Item total: $', ''));
    expect(itemTotal).toBeGreaterThan(0);

    // 2. Verify tax displayed as 8% of item total
    const taxText = await page.locator('.summary_tax_label').innerText();
    const taxValue = parseFloat(taxText.replace('Tax: $', ''));
    const expectedTax = itemTotal * 0.08;
    
    // Using toBeCloseTo to handle floating point precision for currency
    expect(taxValue).toBeCloseTo(expectedTax, 2);

    // 3. Verify total amount = Item total + Tax
    const totalText = await page.locator('.summary_total_label').innerText();
    const totalValue = parseFloat(totalText.replace('Total: $', ''));
    const expectedTotal = itemTotal + taxValue;
    
    expect(totalValue).toBeCloseTo(expectedTotal, 2);
  });
});
