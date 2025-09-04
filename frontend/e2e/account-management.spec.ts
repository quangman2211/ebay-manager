import { test, expect } from '@playwright/test';

/**
 * Account Management E2E Tests - Sprint 7
 * 
 * Tests critical user workflows end-to-end:
 * - Account listing and selection
 * - Account creation and editing  
 * - Account settings management
 * - Account permissions management
 * - Bulk operations
 * 
 * Following SOLID Principles:
 * - Single Responsibility: Each test validates one complete user workflow
 * - Open/Closed: Easy to add new workflow scenarios
 * - Interface Segregation: Tests user interfaces, not internal implementation
 */

// Test configuration
const BASE_URL = process.env.REACT_APP_BASE_URL || 'http://localhost:3000';
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001';

test.beforeEach(async ({ page }) => {
  // Set up test data and authentication
  await page.goto(`${BASE_URL}/login`);
  
  // Login with test credentials
  await page.fill('[data-testid="email-input"]', 'admin@test.com');
  await page.fill('[data-testid="password-input"]', 'password123');
  await page.click('[data-testid="login-button"]');
  
  // Wait for navigation to account management
  await page.waitForURL(`${BASE_URL}/accounts`);
});

test.describe('Account Management - Critical Workflows', () => {
  test.describe('Account Listing and Navigation', () => {
    test('should display account list and allow navigation', async ({ page }) => {
      // Verify page loaded correctly
      await expect(page.locator('h1')).toContainText('Account Management');
      
      // Should show account cards
      const accountCards = page.locator('[data-testid="account-card"]');
      await expect(accountCards).toHaveCount.atLeast(1);
      
      // Should show account information
      await expect(accountCards.first()).toContainText('Test Store');
      await expect(accountCards.first()).toContainText('@teststore');
    });

    test('should filter accounts using search', async ({ page }) => {
      // Wait for accounts to load
      await page.waitForSelector('[data-testid="account-card"]');
      
      const searchInput = page.locator('[data-testid="search-input"]');
      await searchInput.fill('Test Store');
      
      // Should filter results
      const visibleCards = page.locator('[data-testid="account-card"]:visible');
      await expect(visibleCards).toHaveCount.atLeast(1);
      
      // Clear search
      await searchInput.fill('');
      
      // Should show all accounts again
      await expect(page.locator('[data-testid="account-card"]')).toHaveCount.atLeast(1);
    });

    test('should handle empty search results', async ({ page }) => {
      const searchInput = page.locator('[data-testid="search-input"]');
      await searchInput.fill('nonexistent_account');
      
      // Should show no results message
      await expect(page.locator('[data-testid="no-results"]')).toContainText('No accounts found');
    });
  });

  test.describe('Account Creation Workflow', () => {
    test('should create new account successfully', async ({ page }) => {
      // Click create account button
      await page.click('[data-testid="create-account-button"]');
      
      // Verify create account dialog opened
      await expect(page.locator('[data-testid="account-form-dialog"]')).toBeVisible();
      
      // Fill account form
      await page.fill('[data-testid="account-name-input"]', 'New Test Account');
      await page.fill('[data-testid="ebay-username-input"]', 'newtestaccount');
      await page.selectOption('[data-testid="account-type-select"]', 'business');
      
      // Submit form
      await page.click('[data-testid="create-account-submit"]');
      
      // Should show success message
      await expect(page.locator('[data-testid="success-message"]')).toContainText('Account created successfully');
      
      // Dialog should close
      await expect(page.locator('[data-testid="account-form-dialog"]')).not.toBeVisible();
      
      // New account should appear in list
      await expect(page.locator('[data-testid="account-card"]').filter({ hasText: 'New Test Account' })).toBeVisible();
    });

    test('should validate required fields', async ({ page }) => {
      await page.click('[data-testid="create-account-button"]');
      
      // Try to submit empty form
      await page.click('[data-testid="create-account-submit"]');
      
      // Should show validation errors
      await expect(page.locator('[data-testid="name-error"]')).toContainText('Account name is required');
      await expect(page.locator('[data-testid="username-error"]')).toContainText('eBay username is required');
    });

    test('should handle duplicate username error', async ({ page }) => {
      await page.click('[data-testid="create-account-button"]');
      
      // Fill form with existing username
      await page.fill('[data-testid="account-name-input"]', 'Duplicate Account');
      await page.fill('[data-testid="ebay-username-input"]', 'existinguser');
      await page.selectOption('[data-testid="account-type-select"]', 'personal');
      
      await page.click('[data-testid="create-account-submit"]');
      
      // Should show error message
      await expect(page.locator('[data-testid="error-message"]')).toContainText('Username already exists');
    });
  });

  test.describe('Account Editing Workflow', () => {
    test('should edit existing account', async ({ page }) => {
      // Find first account and click edit
      const firstCard = page.locator('[data-testid="account-card"]').first();
      await firstCard.locator('[data-testid="edit-account-button"]').click();
      
      // Verify edit dialog opened with pre-filled data
      await expect(page.locator('[data-testid="account-form-dialog"]')).toBeVisible();
      await expect(page.locator('[data-testid="account-name-input"]')).toHaveValue('Test Store');
      
      // Update account name
      await page.fill('[data-testid="account-name-input"]', 'Updated Test Store');
      
      // Submit changes
      await page.click('[data-testid="update-account-submit"]');
      
      // Should show success message
      await expect(page.locator('[data-testid="success-message"]')).toContainText('Account updated successfully');
      
      // Updated name should appear in list
      await expect(page.locator('[data-testid="account-card"]').filter({ hasText: 'Updated Test Store' })).toBeVisible();
    });
  });

  test.describe('Account Settings Workflow', () => {
    test('should open and manage account settings', async ({ page }) => {
      // Click settings for first account
      const firstCard = page.locator('[data-testid="account-card"]').first();
      await firstCard.locator('[data-testid="settings-button"]').click();
      
      // Verify settings dialog opened
      await expect(page.locator('[data-testid="account-settings-dialog"]')).toBeVisible();
      await expect(page.locator('h2')).toContainText('Account Settings');
      
      // Test sync settings
      const syncToggle = page.locator('[data-testid="sync-enabled-toggle"]');
      const initialState = await syncToggle.isChecked();
      
      // Toggle sync setting
      await syncToggle.click();
      
      // Save changes
      await page.click('[data-testid="save-settings-button"]');
      
      // Should show success message
      await expect(page.locator('[data-testid="success-message"]')).toContainText('Settings saved successfully');
      
      // Setting should be persisted - reopen dialog and verify
      await firstCard.locator('[data-testid="settings-button"]').click();
      await expect(syncToggle).toHaveValue(!initialState ? 'on' : 'off');
    });

    test('should manage notification preferences', async ({ page }) => {
      const firstCard = page.locator('[data-testid="account-card"]').first();
      await firstCard.locator('[data-testid="settings-button"]').click();
      
      // Navigate to notifications section
      await page.click('[data-testid="notifications-section"]');
      
      // Toggle email notifications
      await page.click('[data-testid="email-notifications-toggle"]');
      
      // Save settings
      await page.click('[data-testid="save-settings-button"]');
      
      await expect(page.locator('[data-testid="success-message"]')).toContainText('Settings saved successfully');
    });
  });

  test.describe('Account Permissions Workflow', () => {
    test('should manage account permissions', async ({ page }) => {
      // Click permissions for first account
      const firstCard = page.locator('[data-testid="account-card"]').first();
      await firstCard.locator('[data-testid="permissions-button"]').click();
      
      // Verify permissions dialog opened
      await expect(page.locator('[data-testid="account-permissions-dialog"]')).toBeVisible();
      await expect(page.locator('h2')).toContainText('Manage Permissions');
      
      // Add new permission
      await page.click('[data-testid="add-permission-button"]');
      
      // Fill permission form
      await page.fill('[data-testid="user-email-input"]', 'newuser@test.com');
      await page.selectOption('[data-testid="permission-level-select"]', 'editor');
      await page.fill('[data-testid="notes-input"]', 'Test permission');
      
      // Submit permission
      await page.click('[data-testid="add-permission-submit"]');
      
      // Should show in permissions table
      await expect(page.locator('[data-testid="permissions-table"]')).toContainText('newuser@test.com');
      await expect(page.locator('[data-testid="permissions-table"]')).toContainText('Editor');
    });

    test('should edit existing permission', async ({ page }) => {
      const firstCard = page.locator('[data-testid="account-card"]').first();
      await firstCard.locator('[data-testid="permissions-button"]').click();
      
      // Edit first permission
      await page.locator('[data-testid="edit-permission-button"]').first().click();
      
      // Change permission level
      await page.selectOption('[data-testid="permission-level-select"]', 'admin');
      
      // Submit changes
      await page.click('[data-testid="update-permission-submit"]');
      
      // Should show updated permission
      await expect(page.locator('[data-testid="permissions-table"]')).toContainText('Administrator');
    });

    test('should delete permission', async ({ page }) => {
      const firstCard = page.locator('[data-testid="account-card"]').first();
      await firstCard.locator('[data-testid="permissions-button"]').click();
      
      // Get initial permission count
      const initialCount = await page.locator('[data-testid="permission-row"]').count();
      
      // Delete first permission
      await page.locator('[data-testid="delete-permission-button"]').first().click();
      
      // Confirm deletion
      await page.click('[data-testid="confirm-delete-button"]');
      
      // Should have one less permission
      const newCount = await page.locator('[data-testid="permission-row"]').count();
      expect(newCount).toBe(initialCount - 1);
    });
  });

  test.describe('Bulk Operations Workflow', () => {
    test('should perform bulk sync operation', async ({ page }) => {
      // Select multiple accounts
      await page.locator('[data-testid="account-checkbox"]').first().check();
      await page.locator('[data-testid="account-checkbox"]').nth(1).check();
      
      // Should show bulk operations toolbar
      await expect(page.locator('[data-testid="bulk-operations-toolbar"]')).toBeVisible();
      await expect(page.locator('[data-testid="selected-count"]')).toContainText('2 selected');
      
      // Perform bulk sync
      await page.click('[data-testid="bulk-sync-button"]');
      
      // Should show sync confirmation dialog
      await expect(page.locator('[data-testid="sync-confirmation-dialog"]')).toBeVisible();
      
      // Confirm sync
      await page.click('[data-testid="confirm-sync-button"]');
      
      // Should show sync progress
      await expect(page.locator('[data-testid="sync-progress"]')).toBeVisible();
      
      // Wait for sync completion
      await expect(page.locator('[data-testid="sync-success"]')).toBeVisible();
    });

    test('should perform bulk status update', async ({ page }) => {
      // Select accounts
      await page.locator('[data-testid="account-checkbox"]').first().check();
      await page.locator('[data-testid="account-checkbox"]').nth(1).check();
      
      // Change status via bulk operations
      await page.click('[data-testid="bulk-status-button"]');
      await page.selectOption('[data-testid="status-select"]', 'inactive');
      await page.click('[data-testid="apply-status-button"]');
      
      // Should show status update success
      await expect(page.locator('[data-testid="success-message"]')).toContainText('Status updated for 2 accounts');
    });

    test('should clear selection', async ({ page }) => {
      // Select accounts
      await page.locator('[data-testid="account-checkbox"]').first().check();
      await page.locator('[data-testid="account-checkbox"]').nth(1).check();
      
      // Clear selection
      await page.click('[data-testid="clear-selection-button"]');
      
      // Should hide bulk operations toolbar
      await expect(page.locator('[data-testid="bulk-operations-toolbar"]')).not.toBeVisible();
      
      // All checkboxes should be unchecked
      await expect(page.locator('[data-testid="account-checkbox"]:checked')).toHaveCount(0);
    });
  });

  test.describe('Account Metrics Workflow', () => {
    test('should view account metrics', async ({ page }) => {
      // Click metrics for first account
      const firstCard = page.locator('[data-testid="account-card"]').first();
      await firstCard.locator('[data-testid="metrics-button"]').click();
      
      // Verify metrics dialog opened
      await expect(page.locator('[data-testid="account-metrics-dialog"]')).toBeVisible();
      await expect(page.locator('h2')).toContainText('Performance Metrics');
      
      // Should show key metrics
      await expect(page.locator('[data-testid="total-revenue"]')).toBeVisible();
      await expect(page.locator('[data-testid="total-orders"]')).toBeVisible();
      await expect(page.locator('[data-testid="total-listings"]')).toBeVisible();
      
      // Should have refresh button
      await expect(page.locator('[data-testid="refresh-metrics-button"]')).toBeVisible();
    });

    test('should refresh metrics data', async ({ page }) => {
      const firstCard = page.locator('[data-testid="account-card"]').first();
      await firstCard.locator('[data-testid="metrics-button"]').click();
      
      // Click refresh
      await page.click('[data-testid="refresh-metrics-button"]');
      
      // Should show loading state
      await expect(page.locator('[data-testid="metrics-loading"]')).toBeVisible();
      
      // Should eventually show updated data
      await expect(page.locator('[data-testid="metrics-loading"]')).not.toBeVisible();
      await expect(page.locator('[data-testid="last-updated"]')).toBeVisible();
    });
  });

  test.describe('Error Handling Workflow', () => {
    test('should handle network errors gracefully', async ({ page }) => {
      // Simulate network failure
      await page.route(`${API_URL}/**`, route => route.abort());
      
      // Try to refresh accounts
      await page.click('[data-testid="refresh-accounts-button"]');
      
      // Should show error message
      await expect(page.locator('[data-testid="error-message"]')).toContainText('Unable to connect to server');
      
      // Should provide retry option
      await expect(page.locator('[data-testid="retry-button"]')).toBeVisible();
    });

    test('should handle validation errors', async ({ page }) => {
      await page.click('[data-testid="create-account-button"]');
      
      // Fill invalid data
      await page.fill('[data-testid="account-name-input"]', ''); // Empty required field
      await page.fill('[data-testid="ebay-username-input"]', 'invalid username!@#'); // Invalid format
      
      await page.click('[data-testid="create-account-submit"]');
      
      // Should show multiple validation errors
      await expect(page.locator('[data-testid="validation-errors"]')).toBeVisible();
      await expect(page.locator('[data-testid="name-error"]')).toBeVisible();
      await expect(page.locator('[data-testid="username-error"]')).toBeVisible();
    });
  });

  test.describe('Responsive Design Workflow', () => {
    test('should work on mobile devices', async ({ page }) => {
      // Set mobile viewport
      await page.setViewportSize({ width: 375, height: 667 });
      
      // Should show mobile-optimized layout
      await expect(page.locator('[data-testid="mobile-menu-button"]')).toBeVisible();
      
      // Account cards should stack vertically
      const cards = page.locator('[data-testid="account-card"]');
      await expect(cards).toHaveCount.atLeast(1);
      
      // Mobile navigation should work
      await page.click('[data-testid="mobile-menu-button"]');
      await expect(page.locator('[data-testid="mobile-nav"]')).toBeVisible();
    });

    test('should work on tablet devices', async ({ page }) => {
      // Set tablet viewport
      await page.setViewportSize({ width: 768, height: 1024 });
      
      // Should show tablet-optimized layout
      await expect(page.locator('[data-testid="account-grid"]')).toHaveClass(/tablet-grid/);
      
      // All functionality should remain accessible
      await page.click('[data-testid="create-account-button"]');
      await expect(page.locator('[data-testid="account-form-dialog"]')).toBeVisible();
    });
  });

  test.describe('Performance Workflow', () => {
    test('should load page within performance budget', async ({ page }) => {
      const startTime = Date.now();
      
      await page.goto(`${BASE_URL}/accounts`);
      await page.waitForSelector('[data-testid="account-card"]');
      
      const loadTime = Date.now() - startTime;
      
      // Should load within 3 seconds
      expect(loadTime).toBeLessThan(3000);
    });

    test('should handle large account lists efficiently', async ({ page }) => {
      // Assume test environment has many accounts
      const accountCards = page.locator('[data-testid="account-card"]');
      
      // Should implement virtualization for large lists
      if (await accountCards.count() > 50) {
        // Check if virtual scrolling is working
        await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
        
        // Should only render visible items
        const visibleCards = await accountCards.evaluateAll(
          elements => elements.filter(el => {
            const rect = el.getBoundingClientRect();
            return rect.top >= 0 && rect.bottom <= window.innerHeight;
          }).length
        );
        
        // Should not render all items at once for performance
        expect(visibleCards).toBeLessThan(await accountCards.count());
      }
    });
  });
});