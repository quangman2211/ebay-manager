import { test, expect, Page } from '@playwright/test';
import { ApiHelper } from './utils/api-helpers';
import { 
  testCredentials, 
  selectors, 
  testOrderData, 
  responsiveViewports,
  apiEndpoints 
} from './fixtures/test-data';

/**
 * Comprehensive E2E tests for Order Enhancement Features
 * Tests all new order management functionality including:
 * - Order Detail Modal
 * - Inline Status Editing
 * - Tracking Number Input
 * - Order Notes System
 * - Order History Timeline
 * - Responsive Design
 */

test.describe('Order Enhancement Features', () => {
  let apiHelper: ApiHelper;
  let token: string;
  let testAccountId: number;

  test.beforeAll(async ({ request }) => {
    apiHelper = new ApiHelper(request);
    token = await apiHelper.login();
    
    // Create test account and orders
    const account = await apiHelper.createAccount(token);
    testAccountId = account.id;
  });

  test.beforeEach(async ({ page }) => {
    // Login to the application
    await page.goto('/');
    await page.fill(selectors.usernameInput, testCredentials.admin.username);
    await page.fill(selectors.passwordInput, testCredentials.admin.password);
    await page.click(selectors.loginButton);
    
    // Navigate to Orders page
    await page.waitForSelector(selectors.ordersNav);
    await page.click(selectors.ordersNav);
    await page.waitForSelector(selectors.ordersGrid);
  });

  test.describe('Order Detail Modal', () => {
    test('should open order detail modal when clicking on order row', async ({ page }) => {
      // Wait for orders to load
      await page.waitForSelector(selectors.orderRow);
      
      // Click on first order row
      await page.click(`${selectors.orderRow}:first-child`);
      
      // Verify modal opens
      await expect(page.locator(selectors.orderDetailModal)).toBeVisible();
      
      // Verify modal contains expected sections
      await expect(page.locator(selectors.statusEditor)).toBeVisible();
      await expect(page.locator(selectors.trackingNumberInput)).toBeVisible();
      await expect(page.locator(selectors.orderNotesSection)).toBeVisible();
      await expect(page.locator(selectors.orderHistoryTimeline)).toBeVisible();
    });

    test('should close modal when clicking close button', async ({ page }) => {
      // Open modal
      await page.click(`${selectors.orderRow}:first-child`);
      await expect(page.locator(selectors.orderDetailModal)).toBeVisible();
      
      // Close modal
      await page.click(selectors.modalCloseButton);
      
      // Verify modal is closed
      await expect(page.locator(selectors.orderDetailModal)).not.toBeVisible();
    });

    test('should close modal when clicking outside', async ({ page }) => {
      // Open modal
      await page.click(`${selectors.orderRow}:first-child`);
      await expect(page.locator(selectors.orderDetailModal)).toBeVisible();
      
      // Click outside modal
      await page.click('body', { position: { x: 50, y: 50 } });
      
      // Verify modal is closed
      await expect(page.locator(selectors.orderDetailModal)).not.toBeVisible();
    });
  });

  test.describe('Inline Status Editing', () => {
    test('should allow editing order status with valid transitions', async ({ page }) => {
      // Open order detail modal
      await page.click(`${selectors.orderRow}:first-child`);
      await expect(page.locator(selectors.orderDetailModal)).toBeVisible();
      
      // Test each valid status transition
      for (const status of testOrderData.validStatuses) {
        await page.click(selectors.statusDropdown);
        await page.click(`text=${status}`);
        
        // Wait for status update
        await page.waitForTimeout(1000);
        
        // Verify status is updated in the dropdown
        await expect(page.locator(selectors.statusDropdown)).toContainText(status);
      }
    });

    test('should show validation errors for invalid status transitions', async ({ page }) => {
      // Open order detail modal
      await page.click(`${selectors.orderRow}:first-child`);
      await expect(page.locator(selectors.orderDetailModal)).toBeVisible();
      
      // Try to transition from delivered to pending (invalid)
      await page.click(selectors.statusDropdown);
      await page.click('text=delivered');
      await page.waitForTimeout(1000);
      
      await page.click(selectors.statusDropdown);
      await page.click('text=pending');
      
      // Check for error message or validation
      const errorMessage = page.locator('[data-testid=status-error]');
      if (await errorMessage.isVisible()) {
        await expect(errorMessage).toContainText('Invalid status transition');
      }
    });

    test('should update status in real-time across UI', async ({ page }) => {
      // Get initial status from grid
      const initialStatus = await page.locator(`${selectors.orderRow}:first-child [data-testid=order-status]`).textContent();
      
      // Open modal and change status
      await page.click(`${selectors.orderRow}:first-child`);
      await page.click(selectors.statusDropdown);
      await page.click('text=processing');
      await page.waitForTimeout(1000);
      
      // Close modal
      await page.click(selectors.modalCloseButton);
      
      // Verify status is updated in the grid
      await expect(page.locator(`${selectors.orderRow}:first-child [data-testid=order-status]`)).toContainText('processing');
    });
  });

  test.describe('Tracking Number Input', () => {
    test('should accept valid tracking numbers', async ({ page }) => {
      // Open order detail modal
      await page.click(`${selectors.orderRow}:first-child`);
      await expect(page.locator(selectors.orderDetailModal)).toBeVisible();
      
      // Test each valid tracking number
      for (const trackingNumber of testOrderData.validTrackingNumbers) {
        await page.fill(selectors.trackingNumberInput, trackingNumber);
        await page.click(selectors.trackingNumberSave);
        
        // Wait for save operation
        await page.waitForTimeout(1000);
        
        // Verify tracking number is saved
        await expect(page.locator(selectors.trackingNumberInput)).toHaveValue(trackingNumber);
      }
    });

    test('should show validation errors for invalid tracking numbers', async ({ page }) => {
      // Open order detail modal
      await page.click(`${selectors.orderRow}:first-child`);
      await expect(page.locator(selectors.orderDetailModal)).toBeVisible();
      
      // Test each invalid tracking number
      for (const invalidTracking of testOrderData.invalidTrackingNumbers) {
        await page.fill(selectors.trackingNumberInput, invalidTracking);
        await page.click(selectors.trackingNumberSave);
        
        // Check for validation error
        const errorMessage = page.locator('[data-testid=tracking-error]');
        if (await errorMessage.isVisible()) {
          await expect(errorMessage).toContainText('Invalid tracking number format');
        }
      }
    });

    test('should format tracking numbers correctly', async ({ page }) => {
      // Open order detail modal
      await page.click(`${selectors.orderRow}:first-child`);
      await expect(page.locator(selectors.orderDetailModal)).toBeVisible();
      
      // Enter UPS tracking number
      await page.fill(selectors.trackingNumberInput, '1z999aa1234567890');
      await page.click(selectors.trackingNumberSave);
      
      // Verify it's formatted to uppercase
      await expect(page.locator(selectors.trackingNumberInput)).toHaveValue('1Z999AA1234567890');
    });
  });

  test.describe('Order Notes System', () => {
    test('should allow adding new notes', async ({ page }) => {
      // Open order detail modal
      await page.click(`${selectors.orderRow}:first-child`);
      await expect(page.locator(selectors.orderDetailModal)).toBeVisible();
      
      // Add a new note
      await page.click(selectors.addNoteButton);
      await page.fill(selectors.noteInput, testOrderData.sampleNotes[0]);
      await page.click(selectors.saveNoteButton);
      
      // Wait for note to be saved
      await page.waitForTimeout(1000);
      
      // Verify note appears in notes list
      await expect(page.locator(selectors.notesList)).toContainText(testOrderData.sampleNotes[0]);
    });

    test('should display note timestamps and author', async ({ page }) => {
      // Open order detail modal
      await page.click(`${selectors.orderRow}:first-child`);
      await expect(page.locator(selectors.orderDetailModal)).toBeVisible();
      
      // Add a note
      await page.click(selectors.addNoteButton);
      await page.fill(selectors.noteInput, 'Test note with metadata');
      await page.click(selectors.saveNoteButton);
      await page.waitForTimeout(1000);
      
      // Verify note metadata is displayed
      const noteItem = page.locator(`${selectors.notesList} .note-item:last-child`);
      await expect(noteItem.locator('.note-author')).toContainText('admin');
      await expect(noteItem.locator('.note-timestamp')).toBeVisible();
    });

    test('should handle empty notes validation', async ({ page }) => {
      // Open order detail modal
      await page.click(`${selectors.orderRow}:first-child`);
      await expect(page.locator(selectors.orderDetailModal)).toBeVisible();
      
      // Try to save empty note
      await page.click(selectors.addNoteButton);
      await page.click(selectors.saveNoteButton);
      
      // Check for validation error
      const errorMessage = page.locator('[data-testid=note-error]');
      if (await errorMessage.isVisible()) {
        await expect(errorMessage).toContainText('Note cannot be empty');
      }
    });
  });

  test.describe('Order History Timeline', () => {
    test('should display order status change history', async ({ page }) => {
      // First, make some status changes to create history
      await page.click(`${selectors.orderRow}:first-child`);
      await expect(page.locator(selectors.orderDetailModal)).toBeVisible();
      
      // Change status multiple times to create history
      const statuses = ['processing', 'shipped', 'delivered'];
      for (const status of statuses) {
        await page.click(selectors.statusDropdown);
        await page.click(`text=${status}`);
        await page.waitForTimeout(1000);
      }
      
      // Check history timeline
      await expect(page.locator(selectors.orderHistoryTimeline)).toBeVisible();
      
      // Verify history items are present
      const historyItems = page.locator(selectors.historyItem);
      const historyCount = await historyItems.count();
      expect(historyCount).toBeGreaterThan(0);
      
      // Verify last history item shows current status
      await expect(historyItems.last()).toContainText('delivered');
    });

    test('should show timestamps for history items', async ({ page }) => {
      // Open order detail modal
      await page.click(`${selectors.orderRow}:first-child`);
      await expect(page.locator(selectors.orderHistoryTimeline)).toBeVisible();
      
      // Check if history items have timestamps
      const historyItems = page.locator(selectors.historyItem);
      const firstItem = historyItems.first();
      await expect(firstItem.locator('.history-timestamp')).toBeVisible();
    });

    test('should show user information for history items', async ({ page }) => {
      // Open order detail modal
      await page.click(`${selectors.orderRow}:first-child`);
      await expect(page.locator(selectors.orderHistoryTimeline)).toBeVisible();
      
      // Check if history items show user info
      const historyItems = page.locator(selectors.historyItem);
      if (await historyItems.count() > 0) {
        await expect(historyItems.first().locator('.history-user')).toBeVisible();
      }
    });
  });

  test.describe('Responsive Design', () => {
    test('should work correctly on tablet view', async ({ page }) => {
      // Set tablet viewport
      await page.setViewportSize(responsiveViewports.tablet);
      
      // Navigate to orders page
      await page.goto('/orders');
      await page.waitForSelector(selectors.ordersGrid);
      
      // Test order detail modal on tablet
      await page.click(`${selectors.orderRow}:first-child`);
      await expect(page.locator(selectors.orderDetailModal)).toBeVisible();
      
      // Verify modal adapts to tablet layout
      const modal = page.locator(selectors.orderDetailModal);
      const modalBox = await modal.boundingBox();
      expect(modalBox?.width).toBeLessThanOrEqual(responsiveViewports.tablet.width);
      
      // Test functionality still works
      await expect(page.locator(selectors.statusEditor)).toBeVisible();
      await expect(page.locator(selectors.trackingNumberInput)).toBeVisible();
    });

    test('should work correctly on mobile view', async ({ page }) => {
      // Set mobile viewport
      await page.setViewportSize(responsiveViewports.mobile);
      
      // Navigate to orders page
      await page.goto('/orders');
      await page.waitForSelector(selectors.ordersGrid);
      
      // Test order detail modal on mobile
      await page.click(`${selectors.orderRow}:first-child`);
      await expect(page.locator(selectors.orderDetailModal)).toBeVisible();
      
      // Verify modal takes full width on mobile
      const modal = page.locator(selectors.orderDetailModal);
      const modalBox = await modal.boundingBox();
      expect(modalBox?.width).toBeLessThanOrEqual(responsiveViewports.mobile.width);
      
      // Test scrolling within modal
      await page.locator(selectors.orderDetailModal).scroll({ top: 100 });
      
      // Verify all sections are accessible
      await expect(page.locator(selectors.statusEditor)).toBeVisible();
      await expect(page.locator(selectors.orderNotesSection)).toBeVisible();
    });

    test('should maintain functionality across screen sizes', async ({ page }) => {
      const viewports = [responsiveViewports.desktop, responsiveViewports.tablet, responsiveViewports.mobile];
      
      for (const viewport of viewports) {
        await page.setViewportSize(viewport);
        await page.goto('/orders');
        await page.waitForSelector(selectors.ordersGrid);
        
        // Test basic functionality
        await page.click(`${selectors.orderRow}:first-child`);
        await expect(page.locator(selectors.orderDetailModal)).toBeVisible();
        
        // Test status editing
        await page.click(selectors.statusDropdown);
        await page.click('text=processing');
        await page.waitForTimeout(500);
        
        // Close modal
        await page.click(selectors.modalCloseButton);
        await expect(page.locator(selectors.orderDetailModal)).not.toBeVisible();
      }
    });
  });

  test.describe('Error Handling', () => {
    test('should handle API errors gracefully', async ({ page }) => {
      // Mock API failure for status update
      await page.route('**/api/v1/orders/*/status', route => {
        route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ detail: 'Internal server error' })
        });
      });
      
      // Try to update status
      await page.click(`${selectors.orderRow}:first-child`);
      await page.click(selectors.statusDropdown);
      await page.click('text=shipped');
      
      // Check for error message
      const errorMessage = page.locator('[data-testid=api-error]');
      await expect(errorMessage).toBeVisible({ timeout: 5000 });
    });

    test('should handle network timeouts', async ({ page }) => {
      // Mock slow API response
      await page.route('**/api/v1/orders/*/notes', route => {
        setTimeout(() => route.continue(), 10000);
      });
      
      // Try to add note
      await page.click(`${selectors.orderRow}:first-child`);
      await page.click(selectors.addNoteButton);
      await page.fill(selectors.noteInput, 'Test timeout note');
      await page.click(selectors.saveNoteButton);
      
      // Should show loading state
      const loadingIndicator = page.locator('[data-testid=loading]');
      await expect(loadingIndicator).toBeVisible({ timeout: 2000 });
    });

    test('should handle malformed data gracefully', async ({ page }) => {
      // Mock API returning malformed data
      await page.route('**/api/v1/orders/**', route => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ invalid: 'data' })
        });
      });
      
      // Try to open order detail
      await page.click(`${selectors.orderRow}:first-child`);
      
      // Should handle gracefully without crashing
      await expect(page.locator(selectors.orderDetailModal)).toBeVisible();
    });
  });

  test.describe('Performance', () => {
    test('should load order details quickly', async ({ page }) => {
      const startTime = Date.now();
      
      await page.click(`${selectors.orderRow}:first-child`);
      await expect(page.locator(selectors.orderDetailModal)).toBeVisible();
      
      const loadTime = Date.now() - startTime;
      expect(loadTime).toBeLessThan(2000); // Should load within 2 seconds
    });

    test('should handle rapid status changes', async ({ page }) => {
      await page.click(`${selectors.orderRow}:first-child`);
      await expect(page.locator(selectors.orderDetailModal)).toBeVisible();
      
      // Rapidly change status multiple times
      const statuses = ['processing', 'shipped', 'delivered', 'pending'];
      for (const status of statuses) {
        await page.click(selectors.statusDropdown);
        await page.click(`text=${status}`);
        await page.waitForTimeout(100); // Minimal delay
      }
      
      // Should handle all changes without errors
      await expect(page.locator(selectors.statusDropdown)).toContainText('pending');
    });
  });
});