import { test, expect } from '@playwright/test';

test.describe('Dark Mode Display', () => {
  test('login page should respond to dark mode', async ({ page }) => {
    // Go to login page
    await page.goto('/login');
    
    // Set dark mode
    await page.evaluate(() => {
      localStorage.setItem('vite-ui-theme', 'dark');
    });
    await page.reload();
    
    // Check background color
    const mainContainer = page.locator('.h-screen.p-0.m-0');
    const bgColor = await mainContainer.evaluate((el) => window.getComputedStyle(el).backgroundColor);
    console.log('Main container background color in dark mode:', bgColor);
    expect(bgColor).not.toBe('rgb(255, 255, 255)');
    expect(bgColor).not.toBe('rgb(248, 250, 252)'); // bg-slate-50
    
    // Check card color
    const card = page.locator('.rounded-\\[2rem\\]');
    const cardBgColor = await card.evaluate((el) => window.getComputedStyle(el).backgroundColor);
    console.log('Card background color in dark mode:', cardBgColor);
    expect(cardBgColor).not.toBe('rgb(255, 255, 255)');
  });
  
  test('basic layout sidebar should respond to dark mode', async ({ page }) => {
    // Mock token to bypass ProtectedRoute
    await page.goto('/login');
    await page.evaluate(() => {
      localStorage.setItem('token', 'mock-token');
      localStorage.setItem('token_expire', (Date.now() + 3600000).toString());
      localStorage.setItem('vite-ui-theme', 'dark');
    });
    
    await page.goto('/');
    
    // Check if html has 'dark' class
    const html = page.locator('html');
    await expect(html).toHaveClass(/dark/);
    
    // Sidebar should be present
    const sidebar = page.locator('aside');
    await expect(sidebar).toBeVisible();
    
    const sidebarBg = await sidebar.evaluate((el) => window.getComputedStyle(el).backgroundColor);
    console.log('Sidebar background color in dark mode:', sidebarBg);
    expect(sidebarBg).not.toBe('rgb(255, 255, 255)');
    
    // Header should be present
    const header = page.locator('header');
    const headerBg = await header.evaluate((el) => window.getComputedStyle(el).backgroundColor);
    console.log('Header background color in dark mode:', headerBg);
    expect(headerBg).not.toBe('rgb(255, 255, 255)');
  });
});
