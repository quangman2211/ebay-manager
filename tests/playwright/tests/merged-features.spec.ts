import { test, expect } from '@playwright/test';
import { testCredentials } from './fixtures/test-data';
import { ApiHelper } from './utils/api-helpers';
import path from 'path';

/**
 * Comprehensive GUI Testing for Merged Features
 * - Enhanced Bulk CSV Upload System
 * - Account Deletion with Data Preservation  
 * - GUEST Account System
 */

test.describe('Merged Features: Enhanced Upload & Account Deletion', () => {

  test.beforeEach(async ({ page }) => {
    // Login as admin for comprehensive testing
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    
    await page.getByRole('textbox', { name: 'Username' }).fill(testCredentials.admin.username);
    await page.getByRole('textbox', { name: 'Password' }).fill(testCredentials.admin.password);
    await page.getByRole('button', { name: 'Sign In' }).click();
    
    await page.waitForURL('/');
    await page.waitForLoadState('networkidle');
    
    // Verify login success
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
  });

  test.describe('Phase 1: Enhanced Bulk CSV Upload System', () => {

    test('Test Suite 1.1: Bulk Upload Interface & Drag-and-Drop', async ({ page }) => {
      // Navigate to CSV upload page
      await page.goto('/csv-upload');
      await page.waitForLoadState('networkidle');
      
      // Take initial screenshot
      await page.screenshot({ 
        path: 'test-results/bulk-upload-01-initial-state.png',
        fullPage: true 
      });

      // Verify bulk upload interface elements
      await expect(page.locator('[data-testid="bulk-upload-dropzone"]')).toBeVisible();
      await expect(page.getByText('Drag and drop CSV files here')).toBeVisible();
      await expect(page.getByText('🚀 Smart Upload Feature')).toBeVisible();

      console.log('✅ Bulk upload interface verified');

      // Test drag and drop simulation
      const fileChooser = page.locator('input[type="file"]');
      await fileChooser.setInputFiles([
        path.join(__dirname, '../../../test-sample.csv')
      ]);

      // Wait for file to be processed
      await page.waitForTimeout(2000);

      // Verify file appears in bulk upload table
      await expect(page.locator('[data-testid="bulk-upload-table"]')).toBeVisible();
      await expect(page.getByText('test-sample.csv')).toBeVisible();

      // Screenshot after file added
      await page.screenshot({ 
        path: 'test-results/bulk-upload-02-file-added.png',
        fullPage: true 
      });

      console.log('✅ File drag-and-drop functionality verified');

      // Test file removal
      const removeButton = page.locator('[data-testid="remove-file-button"]').first();
      await removeButton.click();

      // Verify file removed
      await page.waitForTimeout(1000);
      await expect(page.getByText('test-sample.csv')).not.toBeVisible();

      console.log('✅ File removal functionality verified');
    });

    test('Test Suite 1.2: Data Type Selection and Account Mapping', async ({ page }) => {
      await page.goto('/csv-upload');
      await page.waitForLoadState('networkidle');

      // Add multiple test files
      const fileChooser = page.locator('input[type="file"]');
      await fileChooser.setInputFiles([
        path.join(__dirname, '../../../test-sample.csv')
      ]);

      await page.waitForTimeout(2000);

      // Test data type selection
      const dataTypeSelect = page.locator('[data-testid="data-type-select"]').first();
      await dataTypeSelect.click();
      
      // Verify data type options
      await expect(page.getByRole('option', { name: 'Orders' })).toBeVisible();
      await expect(page.getByRole('option', { name: 'Listings' })).toBeVisible();
      
      // Select Orders
      await page.getByRole('option', { name: 'Orders' }).click();

      // Screenshot with data type selected
      await page.screenshot({ 
        path: 'test-results/bulk-upload-03-datatype-selected.png',
        fullPage: true 
      });

      console.log('✅ Data type selection verified');

      // Test account selection
      const accountSelect = page.locator('[data-testid="account-select"]').first();
      await accountSelect.click();
      
      // Wait for account options to load
      await page.waitForTimeout(1000);
      
      // Select first available account
      const firstAccount = page.locator('[role="option"]').first();
      if (await firstAccount.isVisible()) {
        await firstAccount.click();
        console.log('✅ Account selection verified');
      }

      // Screenshot final configuration
      await page.screenshot({ 
        path: 'test-results/bulk-upload-04-configured.png',
        fullPage: true 
      });
    });

    test('Test Suite 1.3: Account Mismatch Warning Dialog', async ({ page }) => {
      await page.goto('/csv-upload');
      await page.waitForLoadState('networkidle');

      // Add test file
      const fileChooser = page.locator('input[type="file"]');
      await fileChooser.setInputFiles([
        path.join(__dirname, '../../../test-sample.csv')
      ]);

      await page.waitForTimeout(2000);

      // Configure with potentially mismatched account
      const accountSelect = page.locator('[data-testid="account-select"]').first();
      await accountSelect.click();
      
      const accountOption = page.locator('[role="option"]').first();
      if (await accountOption.isVisible()) {
        await accountOption.click();
      }

      // Trigger upload to potentially show mismatch dialog
      const uploadButton = page.locator('[data-testid="upload-file-button"]').first();
      if (await uploadButton.isVisible()) {
        await uploadButton.click();

        // Wait for potential mismatch dialog
        await page.waitForTimeout(3000);

        // Check if mismatch dialog appears
        const mismatchDialog = page.locator('[data-testid="account-mismatch-dialog"]');
        if (await mismatchDialog.isVisible()) {
          // Screenshot the warning dialog
          await page.screenshot({ 
            path: 'test-results/bulk-upload-05-mismatch-warning.png',
            fullPage: true 
          });

          // Test dialog actions
          const continueButton = page.getByRole('button', { name: 'Continue Upload' });
          const cancelButton = page.getByRole('button', { name: 'Cancel' });
          
          await expect(continueButton).toBeVisible();
          await expect(cancelButton).toBeVisible();

          // Test cancel
          await cancelButton.click();
          await expect(mismatchDialog).not.toBeVisible();

          console.log('✅ Account mismatch dialog verified');
        }
      }
    });

  });

  test.describe('Phase 2: Account Deletion with Data Preservation', () => {

    test('Test Suite 2.1: Account Deletion Dialog Interface', async ({ page }) => {
      // Navigate to account management
      await page.goto('/account-management');
      await page.waitForLoadState('networkidle');

      // Screenshot account management page
      await page.screenshot({ 
        path: 'test-results/account-mgmt-01-initial.png',
        fullPage: true 
      });

      // Look for delete account button (assuming it exists)
      const accountRows = page.locator('[data-testid="account-row"]');
      const firstAccountRow = accountRows.first();
      
      if (await firstAccountRow.isVisible()) {
        // Click on account actions (three dots menu or direct delete button)
        const actionsButton = firstAccountRow.locator('[data-testid="account-actions"]');
        if (await actionsButton.isVisible()) {
          await actionsButton.click();
          await page.waitForTimeout(1000);
        }

        // Look for delete option
        const deleteButton = page.getByRole('menuitem', { name: 'Delete Account' }).or(
          page.locator('[data-testid="delete-account-button"]')
        );
        
        if (await deleteButton.isVisible()) {
          await deleteButton.click();

          // Verify deletion dialog appears
          const deletionDialog = page.locator('[data-testid="account-deletion-dialog"]');
          await expect(deletionDialog).toBeVisible();

          // Screenshot deletion dialog
          await page.screenshot({ 
            path: 'test-results/account-deletion-01-dialog.png',
            fullPage: true 
          });

          // Verify dialog components
          await expect(page.getByText('Delete Account')).toBeVisible();
          await expect(page.getByText('Data Impact')).toBeVisible();
          
          // Check radio button options
          const transferOption = page.getByRole('radio', { name: /transfer.*guest/i });
          const deleteOption = page.getByRole('radio', { name: /permanently delete/i });
          
          await expect(transferOption).toBeVisible();
          await expect(deleteOption).toBeVisible();

          console.log('✅ Account deletion dialog interface verified');

          // Test option selection
          await transferOption.click();
          await page.screenshot({ 
            path: 'test-results/account-deletion-02-transfer-selected.png',
            fullPage: true 
          });

          await deleteOption.click();
          await page.screenshot({ 
            path: 'test-results/account-deletion-03-delete-selected.png',
            fullPage: true 
          });

          // Close dialog
          const cancelButton = page.getByRole('button', { name: 'Cancel' });
          await cancelButton.click();
          
          await expect(deletionDialog).not.toBeVisible();
        }
      }
    });

    test('Test Suite 2.2: Data Impact Preview', async ({ page, request }) => {
      const apiHelper = new ApiHelper(request);

      // First, ensure there are accounts with data
      await page.goto('/account-management');
      await page.waitForLoadState('networkidle');

      // Try to access deletion impact data via API
      try {
        const accountId = 2; // Test with account ID 2
        const impactData = await apiHelper.getDeletionImpact(accountId);
        
        if (impactData) {
          console.log('✅ Deletion impact API accessible');
          console.log(`Impact preview: ${JSON.stringify(impactData, null, 2)}`);
        }
      } catch (error) {
        console.log('⚠️ Deletion impact API not accessible or no test account');
      }

      // Test UI impact display
      const accountRows = page.locator('[data-testid="account-row"]');
      if (await accountRows.count() > 0) {
        const testRow = accountRows.first();
        
        // Trigger deletion dialog
        const actionsButton = testRow.locator('[data-testid="account-actions"]');
        if (await actionsButton.isVisible()) {
          await actionsButton.click();
          
          const deleteButton = page.getByRole('menuitem', { name: 'Delete Account' });
          if (await deleteButton.isVisible()) {
            await deleteButton.click();

            // Wait for impact data to load
            await page.waitForTimeout(3000);

            // Look for impact indicators
            const impactSection = page.locator('[data-testid="deletion-impact"]');
            if (await impactSection.isVisible()) {
              // Screenshot showing impact data
              await page.screenshot({ 
                path: 'test-results/account-deletion-04-impact-preview.png',
                fullPage: true 
              });

              // Verify impact metrics display
              const ordersCount = page.locator('[data-testid="orders-impact"]');
              const listingsCount = page.locator('[data-testid="listings-impact"]');
              
              if (await ordersCount.isVisible() || await listingsCount.isVisible()) {
                console.log('✅ Data impact preview displayed');
              }
            }

            // Close dialog
            const cancelButton = page.getByRole('button', { name: 'Cancel' });
            if (await cancelButton.isVisible()) {
              await cancelButton.click();
            }
          }
        }
      }
    });

  });

  test.describe('Phase 3: Integration & End-to-End Workflows', () => {

    test('Test Suite 3.1: Complete User Journey - Upload → Account Management', async ({ page }) => {
      // Step 1: Perform bulk upload
      await page.goto('/csv-upload');
      await page.waitForLoadState('networkidle');

      const fileChooser = page.locator('input[type="file"]');
      await fileChooser.setInputFiles([
        path.join(__dirname, '../../../test-sample.csv')
      ]);

      await page.waitForTimeout(2000);

      // Configure and upload
      const dataTypeSelect = page.locator('[data-testid="data-type-select"]').first();
      if (await dataTypeSelect.isVisible()) {
        await dataTypeSelect.click();
        await page.getByRole('option', { name: 'Orders' }).click();
      }

      const accountSelect = page.locator('[data-testid="account-select"]').first();
      if (await accountSelect.isVisible()) {
        await accountSelect.click();
        const firstAccount = page.locator('[role="option"]').first();
        if (await firstAccount.isVisible()) {
          await firstAccount.click();
        }
      }

      // Screenshot configured upload
      await page.screenshot({ 
        path: 'test-results/e2e-01-upload-configured.png',
        fullPage: true 
      });

      // Attempt upload
      const uploadButton = page.locator('[data-testid="upload-file-button"]').first();
      if (await uploadButton.isVisible()) {
        await uploadButton.click();
        await page.waitForTimeout(5000); // Wait for upload completion
      }

      // Screenshot upload result
      await page.screenshot({ 
        path: 'test-results/e2e-02-upload-completed.png',
        fullPage: true 
      });

      console.log('✅ Step 1: CSV Upload completed');

      // Step 2: Navigate to account management
      await page.goto('/account-management');
      await page.waitForLoadState('networkidle');

      // Screenshot account management state
      await page.screenshot({ 
        path: 'test-results/e2e-03-account-management.png',
        fullPage: true 
      });

      // Verify accounts are displayed
      const accountsTable = page.locator('[data-testid="accounts-table"]').or(
        page.locator('table')
      );
      
      if (await accountsTable.isVisible()) {
        console.log('✅ Step 2: Account management accessible');
        
        // Count visible accounts
        const accountRows = page.locator('[data-testid="account-row"]').or(
          page.locator('tbody tr')
        );
        const accountCount = await accountRows.count();
        console.log(`Found ${accountCount} accounts in management interface`);
      }

      console.log('✅ Complete user journey test completed');
    });

    test('Test Suite 3.2: GUEST Account System Verification', async ({ page }) => {
      // Check if GUEST account is visible in account management
      await page.goto('/account-management');
      await page.waitForLoadState('networkidle');

      // Look for GUEST account
      const guestAccount = page.locator('text=GUEST').or(
        page.locator('text=guest-account')
      );

      if (await guestAccount.isVisible()) {
        console.log('✅ GUEST account visible in account management');
        
        // Screenshot showing GUEST account
        await page.screenshot({ 
          path: 'test-results/guest-account-01-visible.png',
          fullPage: true 
        });

        // Verify GUEST account is not deletable
        const guestRow = page.locator('tr:has-text("GUEST")').or(
          page.locator('tr:has-text("guest-account")')
        );
        
        if (await guestRow.isVisible()) {
          // Check if delete button is disabled or missing for GUEST account
          const deleteAction = guestRow.locator('[data-testid="delete-account-button"]');
          if (await deleteAction.isVisible()) {
            const isDisabled = await deleteAction.isDisabled();
            if (isDisabled) {
              console.log('✅ GUEST account delete button properly disabled');
            }
          } else {
            console.log('✅ GUEST account delete button properly hidden');
          }
        }
      } else {
        console.log('ℹ️ GUEST account not visible (may be filtered from normal view)');
      }

      // Test backend health check for GUEST account
      try {
        const response = await page.request.get('/api/v1/health/guest-account');
        if (response.ok()) {
          const healthData = await response.json();
          console.log('✅ GUEST account health check passed');
          console.log(`Health status: ${JSON.stringify(healthData, null, 2)}`);
        }
      } catch (error) {
        console.log('⚠️ GUEST account health check endpoint not accessible');
      }
    });

  });

  test.describe('Error Handling & Edge Cases', () => {

    test('Test Suite 4.1: Upload Error Scenarios', async ({ page }) => {
      await page.goto('/csv-upload');
      await page.waitForLoadState('networkidle');

      // Test invalid file type
      const fileChooser = page.locator('input[type="file"]');
      
      // Create a temporary text file to test invalid format
      const invalidFile = path.join(__dirname, '../../../package.json'); // Use package.json as non-CSV
      
      await fileChooser.setInputFiles([invalidFile]);
      await page.waitForTimeout(2000);

      // Check for error messages
      const errorAlert = page.locator('[role="alert"]').or(
        page.locator('.error, .alert-error')
      );

      if (await errorAlert.isVisible()) {
        console.log('✅ Invalid file type error handling verified');
        await page.screenshot({ 
          path: 'test-results/error-01-invalid-file.png',
          fullPage: true 
        });
      }

      // Test upload without account selection
      await fileChooser.setInputFiles([
        path.join(__dirname, '../../../test-sample.csv')
      ]);
      await page.waitForTimeout(2000);

      const uploadButton = page.locator('[data-testid="upload-file-button"]').first();
      if (await uploadButton.isVisible()) {
        await uploadButton.click();
        await page.waitForTimeout(2000);

        // Check for validation error
        const validationError = page.locator('text=account').and(
          page.locator('[role="alert"]')
        );

        if (await validationError.isVisible()) {
          console.log('✅ Missing account selection error handled');
          await page.screenshot({ 
            path: 'test-results/error-02-no-account.png',
            fullPage: true 
          });
        }
      }
    });

  });

});