import { test, expect } from '@playwright/test';

// Mock data for testing
const mockOrders = [
  {
    id: 1,
    item_id: 'ORD-001',
    order_status: { status: 'pending' },
    csv_row: { 
      'Order Number': 'ORD-001',
      'Buyer Username': 'buyer1',
      'Sale Amount': '$29.99',
      'Order Date': '2024-01-15'
    }
  },
  {
    id: 2, 
    item_id: 'ORD-002',
    order_status: { status: 'pending' },
    csv_row: {
      'Order Number': 'ORD-002',
      'Buyer Username': 'buyer2', 
      'Sale Amount': '$45.50',
      'Order Date': '2024-01-15'
    }
  },
  {
    id: 3,
    item_id: 'ORD-003', 
    order_status: { status: 'processing' },
    csv_row: {
      'Order Number': 'ORD-003',
      'Buyer Username': 'buyer3',
      'Sale Amount': '$67.25',
      'Order Date': '2024-01-16'
    }
  }
];

test.describe('Bulk Order Operations E2E', () => {
  test.beforeEach(async ({ page }) => {
    // Set up authentication token in localStorage before navigation
    await page.addInitScript(() => {
      localStorage.setItem('token', 'mock-jwt-token-for-testing');
    });

    // Mock authentication endpoints
    await page.route('**/api/auth/login', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'mock-jwt-token-for-testing',
          token_type: 'bearer',
          user: {
            id: 1,
            username: 'testuser',
            role: 'admin',
            email: 'test@example.com',
            is_active: true
          }
        })
      });
    });

    await page.route('**/api/auth/me', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 1,
          username: 'testuser',
          role: 'admin',
          email: 'test@example.com',
          is_active: true
        })
      });
    });

    // Mock accounts endpoint
    await page.route('**/api/accounts', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          { id: 1, name: 'Test Account', username: 'testaccount' }
        ])
      });
    });

    await page.route('**/api/orders*', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockOrders)
      });
    });

    await page.route('**/api/orders/bulk/status', async route => {
      const request = route.request();
      const payload = await request.postDataJSON();
      
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          successful: payload.order_ids,
          failed: [],
          totalProcessed: payload.order_ids.length,
          errors: []
        })
      });
    });

    // Navigate to orders page (should not redirect to login now)
    await page.goto('/orders');
    
    // Wait for the page to load and authentication to complete
    await page.waitForLoadState('networkidle');
    
    // Wait for orders to load
    await page.waitForSelector('[data-testid="orders-datagrid"]', { timeout: 15000 });
  });

  test('should display bulk operations toolbar when orders are selected', async ({ page }) => {
    // Initially, bulk operations toolbar should be hidden
    await expect(page.locator('[data-testid="bulk-operations-toolbar"]')).toBeHidden();
    
    // Select first order by clicking DataGrid row checkbox
    // Material-UI DataGrid creates checkboxes with generic selectors
    await page.locator('.MuiDataGrid-checkboxInput').first().click();
    
    // Bulk operations toolbar should now be visible
    await expect(page.locator('[data-testid="bulk-operations-toolbar"]')).toBeVisible();
    
    // Should show "1 order selected"
    await expect(page.locator('[data-testid="selected-count"]')).toContainText('1 order selected');
  });

  test('should select multiple orders using checkboxes', async ({ page }) => {
    // Select first two orders by clicking DataGrid row checkboxes
    const checkboxes = page.locator('.MuiDataGrid-checkboxInput');
    await checkboxes.nth(1).click(); // First row checkbox (nth(0) is header)
    await checkboxes.nth(2).click(); // Second row checkbox
    
    // Should show "2 orders selected"
    await expect(page.locator('[data-testid="selected-count"]')).toContainText('2 orders selected');
    
    // Deselect first order
    await checkboxes.nth(1).click();
    
    // Should show "1 order selected"
    await expect(page.locator('[data-testid="selected-count"]')).toContainText('1 order selected');
  });

  test('should select all orders using header checkbox', async ({ page }) => {
    // Click "Select All" checkbox in DataGrid header
    await page.locator('.MuiDataGrid-checkboxInput').first().click();
    
    // Should show "3 orders selected"
    await expect(page.locator('[data-testid="selected-count"]')).toContainText('3 orders selected');
    
    // All individual checkboxes should be checked
    const checkboxes = page.locator('.MuiDataGrid-checkboxInput');
    await expect(checkboxes.nth(1)).toBeChecked(); // First row
    await expect(checkboxes.nth(2)).toBeChecked(); // Second row
    await expect(checkboxes.nth(3)).toBeChecked(); // Third row
  });

  test('should perform bulk status update with confirmation dialog', async ({ page }) => {
    // Select first two orders (both pending)
    const checkboxes = page.locator('.MuiDataGrid-checkboxInput');
    await checkboxes.nth(1).click(); // First row
    await checkboxes.nth(2).click(); // Second row
    
    // Click bulk status update button
    await page.locator('[data-testid="bulk-status-update-btn"]').click();
    
    // Status dropdown should appear
    await expect(page.locator('[data-testid="status-select"]')).toBeVisible();
    
    // Select "processing" status
    await page.locator('[data-testid="status-select"]').click();
    await page.locator('[data-testid="status-option-processing"]').click();
    
    // The update button is the same as bulk-status-update-btn, no separate update-status-btn
    // Status select should trigger after selecting a status
    
    // Confirmation dialog should appear
    await expect(page.locator('[data-testid="confirmation-dialog"]')).toBeVisible();
    
    // Should show preview of affected orders
    await expect(page.locator('[data-testid="confirmation-dialog"]')).toContainText('ORD-001');
    await expect(page.locator('[data-testid="confirmation-dialog"]')).toContainText('ORD-002');
    await expect(page.locator('[data-testid="confirmation-dialog"]')).toContainText('pending → processing');
    
    // Confirm the operation
    await page.locator('[data-testid="confirm-bulk-operation"]').click();
    
    // Should show progress dialog
    await expect(page.locator('[data-testid="progress-dialog"]')).toBeVisible();
    
    // Wait for operation to complete
    await page.waitForSelector('[data-testid="success-message"]', { timeout: 5000 });
    
    // Should show success notification (Snackbar)
    await expect(page.locator('.MuiAlert-root')).toContainText('2 orders updated successfully');
  });

  test('should handle bulk operation errors gracefully', async ({ page }) => {
    // Mock API to return partial failure
    await page.route('**/api/orders/bulk/status', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          successful: [1],
          failed: [2],
          totalProcessed: 2,
          errors: ['Order 2: Invalid status transition']
        })
      });
    });

    // Select first two orders
    const checkboxes = page.locator('.MuiDataGrid-checkboxInput');
    await checkboxes.nth(1).click();
    await checkboxes.nth(2).click();
    
    // Perform bulk update
    await page.locator('[data-testid="bulk-status-update-btn"]').click();
    await page.locator('[data-testid="status-select"]').click();
    await page.locator('[data-testid="status-option-shipped"]').click();
    await page.locator('[data-testid="confirm-bulk-operation"]').click();
    
    // Wait for operation to complete - check for notification instead of specific message
    await page.waitForSelector('.MuiAlert-root', { timeout: 5000 });
    
    // Should show partial success message with error details
    await expect(page.locator('.MuiAlert-root')).toContainText('1 orders, 1 failed');
    await expect(page.locator('[data-testid="error-details"]')).toContainText('Order 2: Invalid status transition');
  });

  test('should clear selection after bulk operation', async ({ page }) => {
    // Select orders and perform bulk update
    const checkboxes = page.locator('.MuiDataGrid-checkboxInput');
    await checkboxes.nth(1).click();
    await checkboxes.nth(2).click();
    
    await page.locator('[data-testid="bulk-status-update-btn"]').click();
    await page.locator('[data-testid="status-select"]').click();
    await page.locator('[data-testid="status-option-processing"]').click();
    await page.locator('[data-testid="confirm-bulk-operation"]').click();
    
    // Wait for success notification
    await page.waitForSelector('.MuiAlert-root', { timeout: 5000 });
    
    // Wait for the notification to auto-hide and selection to clear
    await page.waitForTimeout(1000);
    
    // Selection should be cleared
    await expect(page.locator('[data-testid="bulk-operations-toolbar"]')).toBeHidden();
    await expect(checkboxes.nth(1)).not.toBeChecked();
    await expect(checkboxes.nth(2)).not.toBeChecked();
  });

  test('should show only valid status transitions for selected orders', async ({ page }) => {
    // Select order with "pending" status
    const checkboxes = page.locator('.MuiDataGrid-checkboxInput');
    await checkboxes.nth(1).click();
    
    await page.locator('[data-testid="bulk-status-update-btn"]').click();
    await page.locator('[data-testid="status-select"]').click();
    
    // Should show valid next statuses for pending orders
    await expect(page.locator('[data-testid="status-option-processing"]')).toBeVisible();
    await expect(page.locator('[data-testid="status-option-shipped"]')).toBeVisible();
    
    // Should not show "pending" as it's current status (based on statusTransitions logic)
    // Pending can only go to processing and shipped, not completed or back to pending
    await expect(page.locator('[data-testid="status-option-pending"]')).toHaveCount(0);
  });

  test('should handle selection limits', async ({ page }) => {
    // Mock many orders
    const manyOrders = Array.from({ length: 150 }, (_, i) => ({
      id: i + 1,
      item_id: `ORD-${String(i + 1).padStart(3, '0')}`,
      order_status: { status: 'pending' },
      csv_row: { 
        'Order Number': `ORD-${String(i + 1).padStart(3, '0')}`,
        'Buyer Username': `buyer${i + 1}`,
        'Sale Amount': `$${(Math.random() * 100 + 10).toFixed(2)}`,
        'Order Date': '2024-01-15'
      }
    }));

    await page.route('**/api/orders*', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(manyOrders)
      });
    });

    await page.reload();
    await page.waitForSelector('[data-testid="orders-datagrid"]', { timeout: 10000 });
    
    // Click "Select All" in DataGrid header
    await page.locator('.MuiDataGrid-checkboxInput').first().click();
    
    // Should show limit warning in notification
    await expect(page.locator('.MuiAlert-root')).toContainText('Maximum 100 orders can be selected');
    
    // Should show "100 orders selected"
    await expect(page.locator('[data-testid="selected-count"]')).toContainText('100 orders selected');
  });

  test('should be responsive on mobile devices', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.reload();
    await page.waitForSelector('[data-testid="orders-datagrid"]', { timeout: 10000 });
    
    // Select an order
    const checkboxes = page.locator('.MuiDataGrid-checkboxInput');
    await checkboxes.nth(1).click();
    
    // Bulk operations toolbar should be visible and responsive
    await expect(page.locator('[data-testid="bulk-operations-toolbar"]')).toBeVisible();
    
    // Buttons should be touch-friendly (minimum 44px)
    const updateBtn = page.locator('[data-testid="bulk-status-update-btn"]');
    const bbox = await updateBtn.boundingBox();
    expect(bbox?.height).toBeGreaterThanOrEqual(44);
    
    // Should be able to perform bulk operations on mobile
    await updateBtn.click();
    await expect(page.locator('[data-testid="status-select"]')).toBeVisible();
  });

  test('should provide keyboard accessibility', async ({ page }) => {
    // Click on DataGrid to focus it, then use keyboard navigation
    await page.locator('[data-testid="orders-datagrid"]').click();
    
    // Navigate to first data row and select with Space
    await page.keyboard.press('ArrowDown'); // Move from header to first row
    await page.keyboard.press('Space'); // Select order
    
    // Bulk toolbar should appear
    await expect(page.locator('[data-testid="bulk-operations-toolbar"]')).toBeVisible();
    
    // Tab to bulk update button and activate
    await page.locator('[data-testid="bulk-status-update-btn"]').focus();
    await page.keyboard.press('Enter');
    
    // Status dropdown should open
    await expect(page.locator('[data-testid="status-select"]')).toBeVisible();
    
    // Select status with keyboard
    await page.locator('[data-testid="status-select"]').click();
    await page.keyboard.press('ArrowDown');
    await page.keyboard.press('Enter');
    
    // Confirmation dialog should appear
    await expect(page.locator('[data-testid="confirmation-dialog"]')).toBeVisible();
    
    // Navigate to confirm button with Tab and activate
    await page.locator('[data-testid="confirm-bulk-operation"]').focus();
    await page.keyboard.press('Enter');
  });
});

test.describe('Performance Tests', () => {
  test('should handle large datasets efficiently', async ({ page }) => {
    // Mock 1000 orders
    const largeDataset = Array.from({ length: 1000 }, (_, i) => ({
      id: i + 1,
      item_id: `ORD-${String(i + 1).padStart(4, '0')}`,
      order_status: { status: i % 4 === 0 ? 'pending' : i % 4 === 1 ? 'processing' : i % 4 === 2 ? 'shipped' : 'completed' },
      csv_row: { 
        'Order Number': `ORD-${String(i + 1).padStart(4, '0')}`,
        'Buyer Username': `buyer${i + 1}`,
        'Sale Amount': `$${(Math.random() * 100 + 10).toFixed(2)}`,
        'Order Date': '2024-01-15'
      }
    }));

    await page.route('**/api/orders*', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(largeDataset)
      });
    });

    const startTime = Date.now();
    await page.goto('/orders');
    await page.waitForSelector('[data-testid="orders-datagrid"]', { timeout: 15000 });
    
    // Select all (limited to 100)
    await page.locator('.MuiDataGrid-checkboxInput').first().click();
    const selectionTime = Date.now();
    
    // Should complete selection within reasonable time
    expect(selectionTime - startTime).toBeLessThan(5000);
    
    // Should handle bulk operations efficiently
    await page.locator('[data-testid="bulk-status-update-btn"]').click();
    await page.locator('[data-testid="status-select"]').click();
    await page.locator('[data-testid="status-option-processing"]').click();
    
    const operationStartTime = Date.now();
    await page.locator('[data-testid="update-status-btn"]').click();
    await page.locator('[data-testid="confirm-bulk-operation"]').click();
    
    // Wait for operation to complete
    await page.waitForSelector('[data-testid="success-message"]', { timeout: 10000 });
    const operationEndTime = Date.now();
    
    // Bulk operation should complete within 30 seconds
    expect(operationEndTime - operationStartTime).toBeLessThan(30000);
  });
});