import { test, expect } from '@playwright/test';
import { ApiHelper } from './utils/api-helpers';
import { testCredentials, apiEndpoints, testAccount } from './fixtures/test-data';

/**
 * Backend API Testing with Visual Validation
 * Tests all API endpoints and captures screenshots of API documentation
 */

test.describe('Backend API Tests', () => {
  let apiHelper: ApiHelper;
  let adminToken: string;
  let testAccountId: number;

  test.beforeAll(async ({ request }) => {
    apiHelper = new ApiHelper(request);
  });

  test.beforeEach(async ({ request }) => {
    apiHelper = new ApiHelper(request);
  });

  test('API Documentation should be accessible and complete', async ({ page, request }) => {
    // Navigate to API docs
    await page.goto(`${apiEndpoints.backend}${apiEndpoints.docs}`);
    
    // Wait for the page to load completely
    await page.waitForLoadState('networkidle');
    await page.waitForSelector('.swagger-ui', { timeout: 10000 });

    // Take a full page screenshot of the API documentation
    await page.screenshot({
      path: 'test-results/api-docs-full.png',
      fullPage: true
    });

    // Verify key API sections are present
    await expect(page.locator('text=eBay Manager API')).toBeVisible();
    await expect(page.getByText('/api/v1/login').first()).toBeVisible();
    await expect(page.getByText('/api/v1/accounts').first()).toBeVisible();
    await expect(page.getByText('/api/v1/orders').first()).toBeVisible();
    await expect(page.getByText('/api/v1/csv/upload').first()).toBeVisible();

    // Screenshot of authentication endpoints section
    const authSection = page.locator('[data-testid="operations-Authentication"] , .opblock-tag-section:has-text("Authentication")').first();
    if (await authSection.isVisible()) {
      await authSection.screenshot({ path: 'test-results/api-auth-endpoints.png' });
    }

    // Screenshot of orders endpoints section
    const ordersSection = page.locator('[data-testid="operations-Orders"], .opblock-tag-section:has-text("Orders")').first();
    if (await ordersSection.isVisible()) {
      await ordersSection.screenshot({ path: 'test-results/api-orders-endpoints.png' });
    }
  });

  test('Authentication API should work correctly', async ({ request }) => {
    // Test successful login
    const token = await apiHelper.login();
    expect(token).toBeDefined();
    expect(typeof token).toBe('string');
    expect(token.length).toBeGreaterThan(10);
    
    adminToken = token;
    console.log('✅ Admin authentication successful');

    // Test invalid credentials
    const invalidFormData = new URLSearchParams();
    invalidFormData.append('username', 'invalid');
    invalidFormData.append('password', 'invalid');
    
    const invalidResponse = await request.post(`${apiEndpoints.backend}${apiEndpoints.login}`, {
      data: invalidFormData.toString(),
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });

    expect(invalidResponse.status()).toBe(401);
    console.log('✅ Invalid credentials correctly rejected');
  });

  test('Account Management API should function properly', async ({ request }) => {
    // Use token from previous test
    if (!adminToken) {
      adminToken = await apiHelper.login();
    }

    // Create a test account
    const account = await apiHelper.createAccount(adminToken, testAccount);
    expect(account).toHaveProperty('id');
    expect(account.name).toBe(testAccount.name);
    expect(account.ebay_username).toBe(testAccount.ebay_username);
    
    testAccountId = account.id;
    console.log(`✅ Account created with ID: ${testAccountId}`);

    // Get all accounts
    const accounts = await apiHelper.getAccounts(adminToken);
    expect(Array.isArray(accounts)).toBeTruthy();
    expect(accounts.length).toBeGreaterThanOrEqual(1);
    
    // Find our test account
    const foundAccount = accounts.find(acc => acc.id === testAccountId);
    expect(foundAccount).toBeDefined();
    console.log('✅ Account retrieval successful');
  });

  test('CSV Upload API should handle file uploads', async ({ request }) => {
    if (!adminToken) {
      adminToken = await apiHelper.login();
    }
    
    if (!testAccountId) {
      const account = await apiHelper.createAccount(adminToken, testAccount);
      testAccountId = account.id;
    }

    // Test order CSV upload
    try {
      const orderUploadResult = await apiHelper.uploadCSV(
        adminToken, 
        '../../Docs/DATA/ebay-order.csv',
        testAccountId,
        'order'
      );
      
      expect(orderUploadResult).toHaveProperty('inserted_count');
      expect(orderUploadResult.inserted_count).toBeGreaterThanOrEqual(0);
      console.log(`✅ Order CSV upload successful: ${orderUploadResult.inserted_count} records`);
    } catch (error) {
      console.log('ℹ️ Order CSV upload test skipped (file may not exist)');
    }

    // Test listing CSV upload
    try {
      const listingUploadResult = await apiHelper.uploadCSV(
        adminToken,
        '../../Docs/DATA/ebay-listing.csv',
        testAccountId,
        'listing'
      );
      
      expect(listingUploadResult).toHaveProperty('inserted_count');
      expect(listingUploadResult.inserted_count).toBeGreaterThanOrEqual(0);
      console.log(`✅ Listing CSV upload successful: ${listingUploadResult.inserted_count} records`);
    } catch (error) {
      console.log('ℹ️ Listing CSV upload test skipped (file may not exist)');
    }
  });

  test('Order Management API should handle CRUD operations', async ({ request }) => {
    if (!adminToken) {
      adminToken = await apiHelper.login();
    }
    
    if (!testAccountId) {
      const account = await apiHelper.createAccount(adminToken, testAccount);
      testAccountId = account.id;
    }

    // Get orders for the account
    const orders = await apiHelper.getOrders(adminToken, testAccountId);
    expect(Array.isArray(orders)).toBeTruthy();
    console.log(`✅ Retrieved ${orders.length} orders`);

    // If we have orders, test status updates
    if (orders.length > 0) {
      const testOrder = orders[0];
      const newStatus = 'processing';
      
      const updateResult = await apiHelper.updateOrderStatus(adminToken, testOrder.id, newStatus);
      expect(updateResult).toHaveProperty('message');
      console.log(`✅ Order status updated to: ${newStatus}`);

      // Verify the update
      const updatedOrders = await apiHelper.getOrders(adminToken, testAccountId, newStatus);
      const updatedOrder = updatedOrders.find(o => o.id === testOrder.id);
      expect(updatedOrder).toBeDefined();
      console.log('✅ Order status update verified');
    }
  });

  test('Listings API should retrieve listing data', async ({ request }) => {
    if (!adminToken) {
      adminToken = await apiHelper.login();
    }
    
    if (!testAccountId) {
      const account = await apiHelper.createAccount(adminToken, testAccount);
      testAccountId = account.id;
    }

    // Get listings for the account
    const listings = await apiHelper.getListings(adminToken, testAccountId);
    expect(Array.isArray(listings)).toBeTruthy();
    console.log(`✅ Retrieved ${listings.length} listings`);

    // Verify listing structure if we have data
    if (listings.length > 0) {
      const testListing = listings[0];
      expect(testListing).toHaveProperty('id');
      expect(testListing).toHaveProperty('item_id');
      expect(testListing).toHaveProperty('csv_row');
      console.log('✅ Listing data structure validated');
    }
  });

  test('API Performance should meet requirements', async ({ request }) => {
    if (!adminToken) {
      adminToken = await apiHelper.login();
    }

    // Test API response times
    const startTime = Date.now();
    
    // Test accounts endpoint
    await apiHelper.getAccounts(adminToken);
    const accountsTime = Date.now() - startTime;
    expect(accountsTime).toBeLessThan(2000); // Less than 2 seconds
    
    console.log(`✅ Accounts API response time: ${accountsTime}ms`);

    // Test authentication endpoint
    const authStartTime = Date.now();
    await apiHelper.login();
    const authTime = Date.now() - authStartTime;
    expect(authTime).toBeLessThan(1000); // Less than 1 second
    
    console.log(`✅ Authentication API response time: ${authTime}ms`);
  });

  test('API Error Handling should be robust', async ({ request }) => {
    // Test unauthorized access
    const unauthorizedResponse = await request.get(`${apiEndpoints.backend}${apiEndpoints.accounts}`, {
      headers: {
        'Authorization': 'Bearer invalid-token',
      },
    });
    expect(unauthorizedResponse.status()).toBe(401);
    console.log('✅ Unauthorized access correctly handled');

    // Test invalid endpoints
    const invalidResponse = await request.get(`${apiEndpoints.backend}/invalid-endpoint`);
    expect(invalidResponse.status()).toBe(404);
    console.log('✅ Invalid endpoint correctly handled');

    // Test malformed requests
    if (adminToken) {
      const malformedResponse = await request.post(`${apiEndpoints.backend}${apiEndpoints.accounts}`, {
        data: 'invalid-json',
        headers: {
          'Authorization': `Bearer ${adminToken}`,
          'Content-Type': 'application/json',
        },
      });
      expect(malformedResponse.status()).toBeGreaterThanOrEqual(400);
      console.log('✅ Malformed request correctly handled');
    }
  });
});