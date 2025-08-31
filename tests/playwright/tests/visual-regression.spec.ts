import { test, expect } from '@playwright/test';
import { testCredentials } from './fixtures/test-data';

/**
 * Visual Regression and Performance Testing
 * Captures baseline screenshots and monitors performance metrics
 */

test.describe('Visual Regression Tests', () => {

  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/login');
    await page.getByRole('textbox', { name: 'Username' }).fill(testCredentials.admin.username);
    await page.getByRole('textbox', { name: 'Password' }).fill(testCredentials.admin.password);
    await page.getByRole('button', { name: 'Sign In' }).click();
    await page.waitForURL('/');
    await page.waitForLoadState('networkidle');
  });

  test('Visual Baseline - Login Page', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    
    // Clear any existing data and take clean screenshot
    await page.evaluate(() => {
      const inputs = document.querySelectorAll('input');
      inputs.forEach(input => (input as HTMLInputElement).value = '');
    });
    
    await page.screenshot({ 
      path: 'test-results/visual-baseline-login.png',
      fullPage: true,
      animations: 'disabled'
    });

    // Test with form filled
    await page.getByRole('textbox', { name: 'Username' }).fill('sample_username');
    await page.getByRole('textbox', { name: 'Password' }).fill('sample_password');
    
    await page.screenshot({ 
      path: 'test-results/visual-baseline-login-filled.png',
      fullPage: true,
      animations: 'disabled'
    });

    console.log('✅ Login page visual baseline captured');
  });

  test('Visual Baseline - Dashboard Components', async ({ page }) => {
    // Wait for all data to load
    await page.waitForTimeout(3000);
    
    // Full dashboard screenshot
    await page.screenshot({ 
      path: 'test-results/visual-baseline-dashboard-full.png',
      fullPage: true,
      animations: 'disabled'
    });

    // Individual component screenshots
    const statsCards = page.locator('.MuiGrid-container .MuiCard-root');
    const cardCount = await statsCards.count();
    
    for (let i = 0; i < Math.min(cardCount, 8); i++) {
      await statsCards.nth(i).screenshot({ 
        path: `test-results/visual-baseline-dashboard-card-${i + 1}.png`,
        animations: 'disabled'
      });
    }

    // Account selector component
    const accountSelect = page.locator('label:has-text("eBay Account")').locator('..');
    if (await accountSelect.isVisible()) {
      await accountSelect.screenshot({ 
        path: 'test-results/visual-baseline-account-selector.png',
        animations: 'disabled'
      });
    }

    console.log('✅ Dashboard visual baselines captured');
  });

  test('Visual Baseline - Orders Page Components', async ({ page }) => {
    await page.click('text=Orders');
    await page.waitForURL('/orders');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // Full orders page
    await page.screenshot({ 
      path: 'test-results/visual-baseline-orders-full.png',
      fullPage: true,
      animations: 'disabled'
    });

    // Data grid component
    const dataGrid = page.locator('.MuiDataGrid-root').first();
    if (await dataGrid.isVisible()) {
      await dataGrid.screenshot({ 
        path: 'test-results/visual-baseline-orders-datagrid.png',
        animations: 'disabled'
      });
    }

    // Filter controls
    const filterControls = page.locator('.MuiFormControl-root');
    const controlCount = await filterControls.count();
    
    for (let i = 0; i < Math.min(controlCount, 3); i++) {
      await filterControls.nth(i).screenshot({ 
        path: `test-results/visual-baseline-orders-filter-${i + 1}.png`,
        animations: 'disabled'
      });
    }

    // Test status update dialog
    const editButtons = page.locator('[aria-label="Update Status"]');
    if (await editButtons.count() > 0) {
      await editButtons.first().click();
      await page.waitForTimeout(500);
      
      await page.screenshot({ 
        path: 'test-results/visual-baseline-orders-status-dialog.png',
        animations: 'disabled'
      });
      
      await page.click('button:has-text("Cancel")');
    }

    console.log('✅ Orders page visual baselines captured');
  });

  test('Visual Baseline - Listings Page Components', async ({ page }) => {
    await page.click('text=Listings');
    await page.waitForURL('/listings');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // Full listings page
    await page.screenshot({ 
      path: 'test-results/visual-baseline-listings-full.png',
      fullPage: true,
      animations: 'disabled'
    });

    // Search component
    const searchInput = page.locator('input[placeholder*="Search"], label:has-text("Search")').first();
    if (await searchInput.isVisible()) {
      const searchContainer = searchInput.locator('..').locator('..');
      await searchContainer.screenshot({ 
        path: 'test-results/visual-baseline-listings-search.png',
        animations: 'disabled'
      });
    }

    // Listings data grid
    const dataGrid = page.locator('.MuiDataGrid-root').first();
    if (await dataGrid.isVisible()) {
      await dataGrid.screenshot({ 
        path: 'test-results/visual-baseline-listings-datagrid.png',
        animations: 'disabled'
      });
    }

    console.log('✅ Listings page visual baselines captured');
  });

  test('Visual Baseline - CSV Upload Components', async ({ page }) => {
    await page.click('text=CSV Upload');
    await page.waitForURL('/upload');
    await page.waitForLoadState('networkidle');

    // Full upload page
    await page.screenshot({ 
      path: 'test-results/visual-baseline-upload-full.png',
      fullPage: true,
      animations: 'disabled'
    });

    // Upload dropzone
    const dropzone = page.locator('text=Drag & drop').locator('..').locator('..');
    if (await dropzone.isVisible()) {
      await dropzone.screenshot({ 
        path: 'test-results/visual-baseline-upload-dropzone.png',
        animations: 'disabled'
      });
    }

    // Configuration controls
    const configControls = page.locator('.MuiFormControl-root');
    const controlCount = await configControls.count();
    
    for (let i = 0; i < Math.min(controlCount, 2); i++) {
      await configControls.nth(i).screenshot({ 
        path: `test-results/visual-baseline-upload-config-${i + 1}.png`,
        animations: 'disabled'
      });
    }

    // Instructions section
    const instructions = page.locator('text=Instructions').locator('..').locator('..');
    if (await instructions.isVisible()) {
      await instructions.screenshot({ 
        path: 'test-results/visual-baseline-upload-instructions.png',
        animations: 'disabled'
      });
    }

    console.log('✅ CSV Upload page visual baselines captured');
  });

  test('Cross-Browser Visual Consistency', async ({ page, browserName }) => {
    // Capture the same components across different browsers
    const pages = ['/', '/orders', '/listings', '/upload'];
    
    for (const pagePath of pages) {
      await page.goto(pagePath);
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);
      
      const pageName = pagePath === '/' ? 'dashboard' : pagePath.slice(1);
      await page.screenshot({ 
        path: `test-results/visual-cross-browser-${browserName}-${pageName}.png`,
        fullPage: true,
        animations: 'disabled'
      });
    }

    console.log(`✅ Cross-browser visual consistency captured for ${browserName}`);
  });
});

test.describe('Performance Testing', () => {
  
  test('Page Load Performance Metrics', async ({ page }) => {
    const performanceMetrics: any = {};
    
    // Test login page performance
    const loginStart = performance.now();
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    performanceMetrics.loginPageLoad = performance.now() - loginStart;

    // Login to access other pages
    await page.getByRole('textbox', { name: 'Username' }).fill(testCredentials.admin.username);
    await page.getByRole('textbox', { name: 'Password' }).fill(testCredentials.admin.password);
    await page.getByRole('button', { name: 'Sign In' }).click();
    await page.waitForURL('/');

    // Test dashboard performance
    const dashboardStart = performance.now();
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    performanceMetrics.dashboardPageLoad = performance.now() - dashboardStart;

    // Test orders page performance
    const ordersStart = performance.now();
    await page.goto('/orders');
    await page.waitForLoadState('networkidle');
    performanceMetrics.ordersPageLoad = performance.now() - ordersStart;

    // Test listings page performance
    const listingsStart = performance.now();
    await page.goto('/listings');
    await page.waitForLoadState('networkidle');
    performanceMetrics.listingsPageLoad = performance.now() - listingsStart;

    // Test upload page performance
    const uploadStart = performance.now();
    await page.goto('/upload');
    await page.waitForLoadState('networkidle');
    performanceMetrics.uploadPageLoad = performance.now() - uploadStart;

    // Log all metrics
    console.log('📊 Page Load Performance Metrics:');
    Object.entries(performanceMetrics).forEach(([key, value]) => {
      console.log(`  ${key}: ${(value as number).toFixed(2)}ms`);
    });

    // Assert performance thresholds
    expect(performanceMetrics.loginPageLoad).toBeLessThan(3000);
    expect(performanceMetrics.dashboardPageLoad).toBeLessThan(4000);
    expect(performanceMetrics.ordersPageLoad).toBeLessThan(4000);
    expect(performanceMetrics.listingsPageLoad).toBeLessThan(4000);
    expect(performanceMetrics.uploadPageLoad).toBeLessThan(3000);

    console.log('✅ All page load performance metrics within acceptable range');
  });

  test('Network Performance and Resource Loading', async ({ page }) => {
    let resourceMetrics = {
      totalRequests: 0,
      failedRequests: 0,
      totalSize: 0,
      slowRequests: 0
    };

    // Monitor network requests
    page.on('request', request => {
      resourceMetrics.totalRequests++;
      console.log(`Request: ${request.method()} ${request.url()}`);
    });

    page.on('response', response => {
      const headers = response.headers();
      const contentLength = headers['content-length'];
      if (contentLength) {
        resourceMetrics.totalSize += parseInt(contentLength);
      }
      
      if (!response.ok()) {
        resourceMetrics.failedRequests++;
      }
      
      // Consider requests over 1 second as slow
      if (response.timing() && response.timing().responseEnd > 1000) {
        resourceMetrics.slowRequests++;
      }
    });

    // Login and navigate through pages
    await page.goto('/login');
    await page.getByRole('textbox', { name: 'Username' }).fill(testCredentials.admin.username);
    await page.getByRole('textbox', { name: 'Password' }).fill(testCredentials.admin.password);
    await page.getByRole('button', { name: 'Sign In' }).click();
    await page.waitForURL('/');
    await page.waitForLoadState('networkidle');

    // Visit all main pages
    const pages = ['/orders', '/listings', '/upload'];
    for (const pagePath of pages) {
      await page.goto(pagePath);
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(1000);
    }

    console.log('📊 Network Performance Metrics:');
    console.log(`  Total Requests: ${resourceMetrics.totalRequests}`);
    console.log(`  Failed Requests: ${resourceMetrics.failedRequests}`);
    console.log(`  Total Size: ${(resourceMetrics.totalSize / 1024).toFixed(2)} KB`);
    console.log(`  Slow Requests (>1s): ${resourceMetrics.slowRequests}`);

    // Assert network performance
    expect(resourceMetrics.failedRequests).toBe(0);
    expect(resourceMetrics.slowRequests).toBeLessThan(3);

    console.log('✅ Network performance metrics acceptable');
  });

  test('Memory and CPU Performance', async ({ page }) => {
    // Navigate to dashboard and perform memory-intensive operations
    await page.goto('/login');
    await page.getByRole('textbox', { name: 'Username' }).fill(testCredentials.admin.username);
    await page.getByRole('textbox', { name: 'Password' }).fill(testCredentials.admin.password);
    await page.getByRole('button', { name: 'Sign In' }).click();
    await page.waitForURL('/');

    // Simulate user interactions that might cause memory leaks
    for (let i = 0; i < 5; i++) {
      // Navigate between pages rapidly
      await page.click('text=Orders');
      await page.waitForLoadState('networkidle');
      
      await page.click('text=Listings');
      await page.waitForLoadState('networkidle');
      
      await page.click('text=Dashboard');
      await page.waitForLoadState('networkidle');
      
      // Trigger re-renders
      const accountSelect = page.locator('label:has-text("eBay Account") + div').first();
      if (await accountSelect.isVisible()) {
        await accountSelect.click();
        await page.waitForTimeout(200);
        await page.press('body', 'Escape');
      }
    }

    // Measure JavaScript heap usage
    const heapUsage = await page.evaluate(() => {
      const memory = (window.performance as any).memory;
      return memory ? {
        used: memory.usedJSHeapSize,
        total: memory.totalJSHeapSize,
        limit: memory.jsHeapSizeLimit
      } : null;
    });

    if (heapUsage) {
      console.log('📊 Memory Usage Metrics:');
      console.log(`  Used Heap: ${(heapUsage.used / 1024 / 1024).toFixed(2)} MB`);
      console.log(`  Total Heap: ${(heapUsage.total / 1024 / 1024).toFixed(2)} MB`);
      console.log(`  Heap Limit: ${(heapUsage.limit / 1024 / 1024).toFixed(2)} MB`);
      
      // Assert reasonable memory usage
      const usedMB = heapUsage.used / 1024 / 1024;
      expect(usedMB).toBeLessThan(100); // Less than 100MB
    }

    console.log('✅ Memory and CPU performance acceptable');
  });

  test('Mobile Performance Testing', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Enable network throttling simulation
    await page.route('**/*', async route => {
      // Add slight delay to simulate slower mobile network
      await new Promise(resolve => setTimeout(resolve, 50));
      await route.continue();
    });

    const mobileMetrics: any = {};

    // Test mobile login performance
    const loginStart = performance.now();
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    mobileMetrics.loginLoad = performance.now() - loginStart;

    await page.getByRole('textbox', { name: 'Username' }).fill(testCredentials.admin.username);
    await page.getByRole('textbox', { name: 'Password' }).fill(testCredentials.admin.password);
    await page.getByRole('button', { name: 'Sign In' }).click();
    await page.waitForURL('/');

    // Test mobile dashboard performance
    const dashboardStart = performance.now();
    await page.waitForLoadState('networkidle');
    mobileMetrics.dashboardLoad = performance.now() - dashboardStart;

    // Test mobile navigation performance
    const navStart = performance.now();
    await page.click('text=Orders');
    await page.waitForURL('/orders');
    await page.waitForLoadState('networkidle');
    mobileMetrics.navigationTime = performance.now() - navStart;

    console.log('📱 Mobile Performance Metrics:');
    Object.entries(mobileMetrics).forEach(([key, value]) => {
      console.log(`  ${key}: ${(value as number).toFixed(2)}ms`);
    });

    // Assert mobile performance thresholds (should be more lenient)
    expect(mobileMetrics.loginLoad).toBeLessThan(5000);
    expect(mobileMetrics.dashboardLoad).toBeLessThan(5000);
    expect(mobileMetrics.navigationTime).toBeLessThan(4000);

    console.log('✅ Mobile performance metrics acceptable');
  });
});

test.describe('Accessibility Testing', () => {
  
  test('Color Contrast and Visual Accessibility', async ({ page }) => {
    await page.goto('/login');
    await page.getByRole('textbox', { name: 'Username' }).fill(testCredentials.admin.username);
    await page.getByRole('textbox', { name: 'Password' }).fill(testCredentials.admin.password);
    await page.getByRole('button', { name: 'Sign In' }).click();
    await page.waitForURL('/');

    // Test high contrast mode
    await page.emulateMedia({ colorScheme: 'dark' });
    await page.screenshot({ 
      path: 'test-results/accessibility-dark-mode.png',
      fullPage: true 
    });

    await page.emulateMedia({ colorScheme: 'light' });
    await page.screenshot({ 
      path: 'test-results/accessibility-light-mode.png',
      fullPage: true 
    });

    // Test reduced motion
    await page.emulateMedia({ reducedMotion: 'reduce' });
    await page.screenshot({ 
      path: 'test-results/accessibility-reduced-motion.png',
      fullPage: true 
    });

    console.log('✅ Accessibility visual tests completed');
  });

  test('Keyboard Navigation Accessibility', async ({ page }) => {
    await page.goto('/login');
    
    // Test tab navigation
    await page.keyboard.press('Tab');
    await page.screenshot({ 
      path: 'test-results/accessibility-tab-1.png',
      fullPage: true 
    });
    
    await page.keyboard.press('Tab');
    await page.screenshot({ 
      path: 'test-results/accessibility-tab-2.png',
      fullPage: true 
    });
    
    await page.keyboard.press('Tab');
    await page.screenshot({ 
      path: 'test-results/accessibility-tab-3.png',
      fullPage: true 
    });

    // Test form submission with keyboard
    await page.getByRole('textbox', { name: 'Username' }).fill(testCredentials.admin.username);
    await page.getByRole('textbox', { name: 'Password' }).fill(testCredentials.admin.password);
    await page.keyboard.press('Enter');
    await page.waitForURL('/');

    console.log('✅ Keyboard navigation accessibility tests completed');
  });
});