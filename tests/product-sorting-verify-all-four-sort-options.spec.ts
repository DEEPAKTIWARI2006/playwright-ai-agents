import { test, expect } from '@playwright/test';

test.describe('Product Sorting', () => {
  test('Product Sorting – Verify All Four Sort Options', async ({ page }) => {
    // Preconditions: User is on inventory page with default product order
    await page.goto('https://www.saucedemo.com/');
    
    // Login to access the inventory page
    await page.locator('[data-test="username"]').fill('standard_user');
    await page.locator('[data-test="password"]').fill('secret_sauce');
    await page.locator('[data-test="login-button"]').click();

    // Ensure we are on the inventory page
    await expect(page).toHaveURL(/.*inventory.html/);

    const sortDropdown = page.locator('[data-test="product_sort_container"]');
    const productNames = page.locator('.inventory_item_name');

    // 1. Select "Name (A to Z)" from the sort dropdown
    await sortDropdown.selectOption({ label: 'Name (A to Z)' });
    // Verification: Products reorder alphabetically ascending
    let namesAZ = await productNames.allInnerTexts();
    expect(namesAZ).toEqual([...namesAZ].sort());

    // 2. Select "Name (Z to A)"
    await sortDropdown.selectOption({ label: 'Name (Z to A)' });
    // Verification: Products reorder alphabetically descending
    let namesZA = await productNames.allInnerTexts();
    expect(namesZA).toEqual([...namesZA].sort().reverse());

    // 3. Select "Price (low to high)"
    await sortDropdown.selectOption({ label: 'Price (low to high)' });
    // Verification: Products reorder by price ascending
    const pricesLowHigh = await page.locator('.inventory_item_price').allInnerTexts();
    const sortedPricesLowHigh = [...pricesLowHigh]
      .map(p => parseFloat(p.replace('$', '')))
      .sort((a, b) => a - b);
    
    const actualPricesLowHigh = pricesLowHigh.map(p => parseFloat(p.replace('$', '')));
    expect(actualPricesLowHigh).toEqual(sortedPricesLowHigh);

    // 4. Select "Price (high to low)"
    await sortDropdown.selectOption({ label: 'Price (high to low)' });
    // Verification: Products reorder by price descending
    const pricesHighLow = await page.locator('.inventory_item_price').allInnerTexts();
    const sortedPricesHighLow = [...pricesHighLow]
      .map(p => parseFloat(p.replace('$', '')))
      .sort((a, b) => b - a);
    
    const actualPricesHighLow = pricesHighLow.map(p => parseFloat(p.replace('$', '')));
    expect(actualPricesHighLow).toEqual(sortedPricesHighLow);
  });
});
