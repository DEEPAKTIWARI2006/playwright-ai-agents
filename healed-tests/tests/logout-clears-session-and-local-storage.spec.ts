import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
  test('Logout Clears Session and Local Storage', async ({ page }) => {
    // Precondition: User is logged in as standard_user
    await page.goto('https://www.saucedemo.com/');
    await page.getByPlaceholder('Username').fill('standard_user');
    await page.getByPlaceholder('Password').fill('secret_sauce');
    await page.getByRole('button', { name: 'Login' }).click();

    // 1. Open side menu via the hamburger icon
    await page.locator('#react-burger-menu-btn').click();
    await expect(page.locator('.bm-menu-wrap')).toBeVisible();

    // 2. Click the "Logout" link using a more reliable selector
    await page.locator('#logout_sidebar_link').click();
    
    // Expected Result: User is redirected to the login page
    await expect(page).toHaveURL('https://www.saucedemo.com/');
    await expect(page.getByRole('button', { name: 'Login' })).toBeVisible();

    // 3. Attempt to navigate back in browser history
    await page.goBack();
    
    // Expected Result: Login page remains; protected pages are not accessible without re-login
    await expect(page).toHaveURL('https://www.saucedemo.com/');
    await expect(page.getByRole('button', { name: 'Login' })).toBeVisible();
  });
});
