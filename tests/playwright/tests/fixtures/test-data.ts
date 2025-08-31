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
  backend: 'http://localhost:3004',
  login: '/api/v1/login',
  accounts: '/api/v1/accounts',
  orders: '/api/v1/orders',
  listings: '/api/v1/listings',
  csvUpload: '/api/v1/csv/upload',
  docs: '/docs',
  // Order enhancement endpoints
  orderHistory: '/api/v1/orders/{id}/history',
  orderNotes: '/api/v1/orders/{id}/notes',
  orderTracking: '/api/v1/orders/{id}/tracking'
};

export const testFiles = {
  orderCSV: '../../Docs/DATA/ebay-order.csv',
  listingCSV: '../../Docs/DATA/ebay-listing.csv'
};

export const testOrderData = {
  validStatuses: ['pending', 'processing', 'shipped', 'delivered', 'cancelled'],
  validTrackingNumbers: [
    '1Z999AA1234567890',
    'TBA123456789',
    '9400109699938123456789'
  ],
  invalidTrackingNumbers: [
    'invalid123',
    '123',
    ''
  ],
  sampleNotes: [
    'Customer requested expedited shipping',
    'Package damaged during transit - replacement sent',
    'Customer satisfied with product quality'
  ]
};

export const responsiveViewports = {
  desktop: { width: 1920, height: 1080 },
  tablet: { width: 768, height: 1024 },
  mobile: { width: 375, height: 812 }
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
  
  // Order Enhancement Features
  orderRow: '[data-testid=order-row]',
  orderDetailModal: '[data-testid=order-detail-modal]',
  statusEditor: '[data-testid=status-editor]',
  statusDropdown: '[data-testid=status-dropdown]',
  trackingNumberInput: '[data-testid=tracking-number-input]',
  trackingNumberSave: '[data-testid=tracking-save-button]',
  orderNotesSection: '[data-testid=order-notes-section]',
  addNoteButton: '[data-testid=add-note-button]',
  noteInput: '[data-testid=note-input]',
  saveNoteButton: '[data-testid=save-note-button]',
  notesList: '[data-testid=notes-list]',
  orderHistoryTimeline: '[data-testid=order-history-timeline]',
  historyItem: '[data-testid=history-item]',
  modalCloseButton: '[data-testid=modal-close-button]',
  
  // Listings page
  listingsGrid: '[data-testid=listings-grid]',
  searchInput: '[data-testid=search-input]',
  
  // CSV Upload
  uploadDropzone: '[data-testid=upload-dropzone]',
  dataTypeSelect: '[data-testid=data-type-select]',
  uploadResult: '[data-testid=upload-result]'
};