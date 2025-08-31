import '@testing-library/jest-dom';

// Mock colors and spacing
jest.mock('./styles/common/colors', () => ({
  colors: {
    primary: '#1976d2',
    secondary: '#dc004e',
    error: '#d32f2f',
    warning: '#ed6c02',
    info: '#0288d1',
    success: '#2e7d32',
    text: {
      primary: '#000000',
      secondary: '#666666',
    },
    background: {
      default: '#fafafa',
      paper: '#ffffff',
    },
    divider: '#e0e0e0',
  },
}));

jest.mock('./styles/common/spacing', () => ({
  spacing: {
    xsmall: '4px',
    small: '8px',
    medium: '16px',
    large: '24px',
    rowHeight: 80,
  },
}));

// Mock axios
jest.mock('axios', () => ({
  create: jest.fn(() => ({
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
    interceptors: {
      request: { use: jest.fn() },
      response: { use: jest.fn() },
    },
  })),
}));

// Mock OrderDataService
jest.mock('./services/OrderDataService', () => ({
  __esModule: true,
  default: {
    fetchOrders: jest.fn(),
    updateOrderStatus: jest.fn(),
    updateTrackingNumber: jest.fn(),
    addOrderNote: jest.fn(),
  },
}));

// Mock API services
jest.mock('./services/api', () => ({
  authAPI: {
    login: jest.fn(),
    getCurrentUser: jest.fn(),
  },
  accountsAPI: {
    getAccounts: jest.fn(),
    createAccount: jest.fn(),
  },
  ordersAPI: {
    getOrders: jest.fn(),
    updateOrderStatus: jest.fn(),
    updateTrackingNumber: jest.fn(),
    addOrderNote: jest.fn(),
  },
  listingsAPI: {
    getListings: jest.fn(),
  },
  csvAPI: {
    uploadCSV: jest.fn(),
  },
  searchAPI: {
    globalSearch: jest.fn(),
  },
}));