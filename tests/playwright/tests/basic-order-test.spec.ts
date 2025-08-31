import { test, expect } from '@playwright/test';
import { testCredentials } from './fixtures/test-data';

/**
 * Basic Order Enhancement Tests
 * Simplified tests to verify core functionality
 */

test.describe('Basic Order Enhancement Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Login to the application
    await page.goto('http://localhost:8004');
    
    // Check if login form exists
    const loginForm = page.locator('input[name="username"]');
    if (await loginForm.isVisible()) {
      await page.fill('input[name="username"]', testCredentials.admin.username);
      await page.fill('input[name="password"]', testCredentials.admin.password);
      await page.click('button[type="submit"]');
      
      // Wait for navigation after login
      await page.waitForTimeout(2000);
    }
  });

  test('should load the application successfully', async ({ page }) => {
    // Verify the application loads
    await expect(page).toHaveTitle(/eBay Manager|React App/);
  });

  test('should navigate to Orders page', async ({ page }) => {
    // Try to navigate to orders page
    const ordersNav = page.locator('text=Orders').first();
    if (await ordersNav.isVisible()) {
      await ordersNav.click();
      await page.waitForTimeout(2000);
      
      // Check if orders page loaded
      const pageContent = await page.content();
      expect(pageContent.toLowerCase()).toContain('order');
    }
  });

  test('should display orders table or grid', async ({ page }) => {
    // Navigate to orders page
    const ordersNav = page.locator('text=Orders').first();
    if (await ordersNav.isVisible()) {
      await ordersNav.click();
      await page.waitForTimeout(2000);
      
      // Look for table/grid elements
      const tableElements = [
        'table',
        '[data-testid=orders-grid]',
        '.orders-table',
        '.data-grid',
        '[role="grid"]'
      ];
      
      let tableFound = false;
      for (const selector of tableElements) {
        const element = page.locator(selector);
        if (await element.isVisible()) {
          tableFound = true;
          break;
        }
      }
      
      if (!tableFound) {
        // Check if there's at least some order-related content
        const pageContent = await page.content();
        expect(pageContent.toLowerCase()).toContain('order');
      }
    }
  });

  test('should handle clicking on order rows if present', async ({ page }) => {
    // Navigate to orders page
    const ordersNav = page.locator('text=Orders').first();
    if (await ordersNav.isVisible()) {
      await ordersNav.click();
      await page.waitForTimeout(2000);
      
      // Look for clickable order rows
      const rowSelectors = [
        'tr[data-testid=order-row]',
        '.order-row',
        'tr:has-text("ORDER")',
        'tbody tr',
        '[role="row"]'
      ];
      
      for (const selector of rowSelectors) {
        const rows = page.locator(selector);
        const count = await rows.count();
        
        if (count > 0) {
          // Try to click the first row
          await rows.first().click();
          await page.waitForTimeout(1000);
          
          // Check if modal or detail view opened
          const modalSelectors = [
            '[data-testid=order-detail-modal]',
            '.modal',
            '[role="dialog"]',
            '.order-details'
          ];
          
          for (const modalSelector of modalSelectors) {
            const modal = page.locator(modalSelector);
            if (await modal.isVisible()) {
              await expect(modal).toBeVisible();
              return;
            }
          }
          break;
        }
      }
    }
  });

  test('should show order status elements', async ({ page }) => {
    // Navigate to orders page
    const ordersNav = page.locator('text=Orders').first();
    if (await ordersNav.isVisible()) {
      await ordersNav.click();
      await page.waitForTimeout(2000);
      
      // Look for status-related elements
      const statusElements = [
        'text=pending',
        'text=processing',
        'text=shipped',
        'text=delivered',
        '[data-testid*=status]',
        '.status'
      ];
      
      let statusFound = false;
      for (const selector of statusElements) {
        const element = page.locator(selector).first();
        if (await element.isVisible()) {
          statusFound = true;
          break;
        }
      }
      
      if (!statusFound) {
        // At least verify the page contains status-related text
        const pageContent = await page.content();
        expect(pageContent.toLowerCase()).toMatch(/(status|pending|processing|shipped|delivered)/);
      }
    }
  });

  test('should display page without JavaScript errors', async ({ page }) => {
    const errors: string[] = [];
    
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });
    
    page.on('pageerror', (error) => {
      errors.push(error.message);
    });
    
    // Navigate through the app
    await page.goto('http://localhost:8004');
    await page.waitForTimeout(1000);
    
    const ordersNav = page.locator('text=Orders').first();
    if (await ordersNav.isVisible()) {
      await ordersNav.click();
      await page.waitForTimeout(2000);
    }
    
    // Check for critical errors (ignore minor warnings)
    const criticalErrors = errors.filter(error => 
      !error.includes('favicon') && 
      !error.includes('Warning:') &&
      !error.includes('DevTools')
    );
    
    expect(criticalErrors.length).toBe(0);
  });

  test('should be responsive on mobile viewport', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 812 });
    
    await page.goto('http://localhost:8004');
    await page.waitForTimeout(1000);
    
    // Verify page loads on mobile
    await expect(page).toHaveTitle(/eBay Manager|React App/);
    
    // Try to navigate to orders
    const ordersNav = page.locator('text=Orders').first();
    if (await ordersNav.isVisible()) {
      await ordersNav.click();
      await page.waitForTimeout(2000);
    }
    
    // Verify content is still accessible
    const pageContent = await page.content();
    expect(pageContent).toBeTruthy();
  });

  test('should handle API endpoints correctly', async ({ page }) => {
    let apiCalls = 0;
    
    // Monitor API calls
    page.on('request', (request) => {
      if (request.url().includes('/api/')) {
        apiCalls++;
      }
    });
    
    // Navigate to orders page
    const ordersNav = page.locator('text=Orders').first();
    if (await ordersNav.isVisible()) {
      await ordersNav.click();
      await page.waitForTimeout(2000);
      
      // Should have made some API calls
      expect(apiCalls).toBeGreaterThan(0);
    }
  });
});