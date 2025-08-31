/**
 * Test data fixtures for eBay Manager Playwright tests
 */

export const testCredentials = {
  admin: {
    username: 'admin',
    password: 'admin123'
  },
  staff: {
    username: 'staff',
    password: 'staff123'
  }
};

export const testAccount = {
  name: 'Test eBay Account',
  ebay_username: 'test_ebay_user',
  is_active: true
};

export const apiEndpoints = {
  backend: 'http://localhost:8000',
  login: '/api/v1/login',
  accounts: '/api/v1/accounts',
  orders: '/api/v1/orders',
  listings: '/api/v1/listings',
  csvUpload: '/api/v1/csv/upload',
  docs: '/docs'
};

export const testFiles = {
  orderCSV: '../../Docs/DATA/ebay-order.csv',
  listingCSV: '../../Docs/DATA/ebay-listing.csv'
};

export const selectors = {
  // Login page
  loginForm: '[data-testid=login-form]',
  usernameInput: 'input[name="username"]',
  passwordInput: 'input[name="password"]',
  loginButton: 'button[type="submit"]',
  
  // Navigation
  sidebarNav: '[data-testid=sidebar-nav]',
  dashboardNav: 'text=Dashboard',
  ordersNav: 'text=Orders',
  listingsNav: 'text=Listings',
  uploadNav: 'text=CSV Upload',
  
  // Dashboard
  totalOrdersCard: '[data-testid=total-orders]',
  pendingOrdersCard: '[data-testid=pending-orders]',
  accountSelect: '[data-testid=account-select]',
  
  // Orders page
  ordersGrid: '[data-testid=orders-grid]',
  statusFilter: '[data-testid=status-filter]',
  statusUpdateDialog: '[data-testid=status-dialog]',
  
  // Listings page
  listingsGrid: '[data-testid=listings-grid]',
  searchInput: '[data-testid=search-input]',
  
  // CSV Upload
  uploadDropzone: '[data-testid=upload-dropzone]',
  dataTypeSelect: '[data-testid=data-type-select]',
  uploadResult: '[data-testid=upload-result]'
};