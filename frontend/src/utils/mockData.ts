import type { 
  Account, 
  User, 
  UserAccountPermission, 
  AccountSettings, 
  AccountMetrics,
  PermissionLevel 
} from '../types';
import { PLATFORMS, CONNECTION_STATUSES, ACCOUNT_DEFAULTS } from '../config/accountConstants';

/**
 * Mock Data Factory - Sprint 7 Testing
 * 
 * Following SOLID Principles:
 * - Single Responsibility: Only creates mock data
 * - Open/Closed: Extensible with new mock types
 * - Interface Segregation: Focused factory methods
 */

/**
 * Mock User Data Factory
 */
export const createMockUser = (overrides: Partial<User> = {}): User => ({
  id: 1,
  username: 'testuser',
  email: 'test@example.com',
  role: 'admin',
  is_active: true,
  created_at: '2024-01-01T00:00:00.000Z',
  ...overrides,
});

export const createMockUsers = (count: number = 3): User[] => [
  createMockUser({ id: 1, username: 'admin', email: 'admin@company.com', role: 'admin' }),
  createMockUser({ id: 2, username: 'staff1', email: 'staff1@company.com', role: 'staff' }),
  createMockUser({ id: 3, username: 'staff2', email: 'staff2@company.com', role: 'staff' }),
].slice(0, count);

/**
 * Mock Account Data Factory
 */
export const createMockAccount = (overrides: Partial<Account> = {}): Account => ({
  id: 1,
  user_id: 1,
  platform_username: 'testaccount',
  name: 'Test Account',
  is_active: true,
  created_at: '2024-01-01T00:00:00.000Z',
  account_type: PLATFORMS.EBAY,
  connection_status: CONNECTION_STATUSES.AUTHENTICATED,
  last_sync_at: '2024-01-01T12:00:00.000Z',
  data_processing_enabled: true,
  settings: {},
  performance_metrics: {},
  ...overrides,
});

export const createMockAccounts = (count: number = 5): Account[] => [
  createMockAccount({ 
    id: 1, 
    name: 'Primary Store', 
    platform_username: 'primarystore', 
    is_active: true,
    connection_status: CONNECTION_STATUSES.AUTHENTICATED 
  }),
  createMockAccount({ 
    id: 2, 
    name: 'Secondary Store', 
    platform_username: 'secondarystore', 
    is_active: true,
    connection_status: CONNECTION_STATUSES.AUTHENTICATED 
  }),
  createMockAccount({ 
    id: 3, 
    name: 'Inactive Store', 
    platform_username: 'inactivestore', 
    is_active: false,
    connection_status: CONNECTION_STATUSES.EXPIRED 
  }),
  createMockAccount({ 
    id: 4, 
    name: 'Electronics Store', 
    platform_username: 'electronicsstore', 
    is_active: true,
    connection_status: CONNECTION_STATUSES.AUTHENTICATED 
  }),
  createMockAccount({ 
    id: 5, 
    name: 'Fashion Store', 
    platform_username: 'fashionstore', 
    is_active: true,
    connection_status: CONNECTION_STATUSES.PENDING 
  }),
].slice(0, count);

/**
 * Mock Permission Data Factory
 */
export const createMockPermission = (overrides: Partial<UserAccountPermission> = {}): UserAccountPermission => ({
  id: 1,
  user_id: 1,
  account_id: 1,
  permission_level: 'viewer',
  granted_by: 1,
  granted_at: '2024-01-01T00:00:00.000Z',
  is_active: true,
  notes: 'Test permission',
  ...overrides,
});

export const createMockPermissions = (accountId: number = 1, count: number = 4): UserAccountPermission[] => {
  const levels: PermissionLevel[] = ['admin', 'manager', 'editor', 'viewer'];
  
  return levels.slice(0, count).map((level, index) => createMockPermission({
    id: index + 1,
    user_id: index + 1,
    account_id: accountId,
    permission_level: level,
    granted_by: 1,
    granted_at: new Date(Date.now() - (index * 24 * 60 * 60 * 1000)).toISOString(),
    notes: `${level} access for user ${index + 1}`,
  }));
};

/**
 * Mock Settings Data Factory
 */
export const createMockSetting = (overrides: Partial<AccountSettings> = {}): AccountSettings => ({
  id: 1,
  account_id: 1,
  setting_key: 'data_processing_enabled',
  setting_value: 'true',
  setting_type: 'boolean',
  updated_by: 1,
  updated_at: '2024-01-01T00:00:00.000Z',
  ...overrides,
});

export const createMockSettings = (accountId: number = 1): AccountSettings[] => [
  createMockSetting({ 
    id: 1, 
    account_id: accountId, 
    setting_key: 'data_processing_enabled', 
    setting_value: 'true', 
    setting_type: 'boolean' 
  }),
  createMockSetting({ 
    id: 2, 
    account_id: accountId, 
    setting_key: 'sync_interval', 
    setting_value: '300', 
    setting_type: 'number' 
  }),
  createMockSetting({ 
    id: 3, 
    account_id: accountId, 
    setting_key: 'notification_email', 
    setting_value: 'admin@example.com', 
    setting_type: 'string' 
  }),
  createMockSetting({ 
    id: 4, 
    account_id: accountId, 
    setting_key: 'api_config', 
    setting_value: '{"endpoint": "https://api.ebay.com", "version": "v1"}', 
    setting_type: 'json' 
  }),
  createMockSetting({ 
    id: 5, 
    account_id: accountId, 
    setting_key: 'rate_limit', 
    setting_value: '1000', 
    setting_type: 'number' 
  }),
  createMockSetting({ 
    id: 6, 
    account_id: accountId, 
    setting_key: 'auth_token_refresh', 
    setting_value: 'false', 
    setting_type: 'boolean' 
  }),
];

/**
 * Mock Metrics Data Factory
 */
export const createMockMetric = (overrides: Partial<AccountMetrics> = {}): AccountMetrics => ({
  id: 1,
  account_id: 1,
  metric_date: '2024-01-01',
  total_orders: 150,
  total_revenue: 15000,
  active_listings: 500,
  total_views: 25000,
  watchers: 1200,
  conversion_rate: 6.0,
  created_at: '2024-01-01T00:00:00.000Z',
  updated_at: '2024-01-01T00:00:00.000Z',
  ...overrides,
});

export const createMockMetrics = (accountId: number = 1, days: number = 30): AccountMetrics[] => {
  return Array.from({ length: days }, (_, index) => {
    const date = new Date();
    date.setDate(date.getDate() - (days - 1 - index));
    
    // Generate realistic trending data
    const baseOrders = 100 + Math.random() * 100;
    const baseRevenue = baseOrders * (80 + Math.random() * 40);
    const baseViews = baseOrders * (15 + Math.random() * 10);
    const baseWatchers = Math.floor(baseViews * (0.04 + Math.random() * 0.02));
    const conversionRate = (baseOrders / baseViews) * 100;
    
    return createMockMetric({
      id: index + 1,
      account_id: accountId,
      metric_date: date.toISOString().split('T')[0],
      total_orders: Math.floor(baseOrders),
      total_revenue: Math.floor(baseRevenue),
      active_listings: 450 + Math.floor(Math.random() * 100),
      total_views: Math.floor(baseViews),
      watchers: baseWatchers,
      conversion_rate: Math.round(conversionRate * 100) / 100,
      created_at: date.toISOString(),
      updated_at: date.toISOString(),
    });
  });
};

/**
 * Mock API Response Factories
 */
export const createMockApiResponse = <T>(data: T, success: boolean = true) => ({
  data,
  status: success ? 200 : 400,
  statusText: success ? 'OK' : 'Bad Request',
  headers: {},
  config: {},
});

export const createMockApiError = (message: string = 'API Error', status: number = 400) => {
  const error = new Error(message) as any;
  error.response = {
    status,
    statusText: status === 400 ? 'Bad Request' : status === 401 ? 'Unauthorized' : 'Server Error',
    data: { message },
  };
  return error;
};

/**
 * Test Scenario Factories
 */
export const createEmptyState = () => ({
  accounts: [],
  users: [],
  permissions: [],
  settings: [],
  metrics: [],
});

export const createLoadingState = () => ({
  loading: true,
  error: null,
});

export const createErrorState = (message: string = 'Something went wrong') => ({
  loading: false,
  error: message,
});

export const createSuccessState = <T>(data: T) => ({
  loading: false,
  error: null,
  data,
});

/**
 * Form Data Factories
 */
export const createMockAccountFormData = () => ({
  name: 'New Test Account',
  platform_username: 'newtestaccount',
  user_id: 1,
  is_active: true,
  account_type: PLATFORMS.EBAY,
});

export const createMockPermissionFormData = () => ({
  user_id: 2,
  permission_level: 'editor' as PermissionLevel,
  notes: 'Test permission creation',
});

export const createMockSettingFormData = () => ({
  setting_key: 'test_setting',
  setting_value: 'test_value',
  setting_type: 'string' as const,
});

/**
 * Utility functions for testing
 */
export const generateMockId = () => Math.floor(Math.random() * 10000) + 1;

export const generateMockTimestamp = (daysAgo: number = 0) => {
  const date = new Date();
  date.setDate(date.getDate() - daysAgo);
  return date.toISOString();
};