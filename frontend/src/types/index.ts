export interface User {
  id: number;
  username: string;
  email: string;
  role: 'admin' | 'staff';
  is_active: boolean;
  created_at: string;
}

export interface Account {
  id: number;
  user_id: number;
  platform_username: string;  // Primary platform username (eBay, Etsy, etc.)
  name: string;
  is_active: boolean;
  created_at: string;
  // Sprint 7 enhancements - REDESIGNED STATUS FIELDS
  account_type?: 'ebay' | 'etsy';
  connection_status?: 'authenticated' | 'pending' | 'expired' | 'failed';
  last_sync_at?: string;
  data_processing_enabled?: boolean;
  settings?: Record<string, any>;
  performance_metrics?: Record<string, any>;
}

export interface OrderStatus {
  id: number;
  csv_data_id: number;
  status: 'pending' | 'processing' | 'shipped' | 'completed';
  updated_by: number;
  updated_at: string;
}

export interface Order {
  id: number;
  item_id: string;
  csv_row: Record<string, any>;
  order_status?: OrderStatus;
  account_id: number;
  created_at: string;
}

export interface Listing {
  id: number;
  item_id: string;
  csv_row: Record<string, any>;
  account_id: number;
  created_at: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface BulkOperationResult {
  successful: number[];
  failed: number[];
  totalProcessed: number;
  errors: string[];
  audit?: {
    userId: number;
    timestamp: string;
    operation: string;
  };
}

// Sprint 7: Account Management Types
export type PermissionLevel = 'viewer' | 'editor' | 'manager' | 'admin';
export type AuthStatus = 'pending' | 'active' | 'expired' | 'error';

export interface EnhancedAccount extends Account {
  settings: Record<string, any>;
  performance_metrics: Record<string, any>;
  user_permissions: UserAccountPermission[];
}

export interface UserAccountPermission {
  id: number;
  user_id: number;
  account_id: number;
  permission_level: PermissionLevel;
  granted_by: number;
  granted_at: string;
  is_active: boolean;
  notes?: string;
}

export interface AccountSettings {
  id: number;
  account_id: number;
  setting_key: string;
  setting_value: string;
  setting_type: 'string' | 'number' | 'boolean' | 'json';
  updated_by: number;
  updated_at: string;
}

export interface AccountMetrics {
  id: number;
  account_id: number;
  metric_date: string;
  total_orders: number;
  total_revenue: number;
  active_listings: number;
  total_views: number;
  watchers: number;
  conversion_rate: number;
  created_at: string;
  updated_at: string;
}

export interface AccountSwitchRequest {
  account_id: number;
}

export interface AccountSwitchResponse {
  message: string;
  active_account: {
    id: number;
    name: string;
    ebay_username: string;
  };
}

export interface BulkPermissionRequest {
  account_id: number;
  permissions: UserAccountPermissionCreate[];
}

export interface BulkPermissionResponse {
  account_id: number;
  updated_count: number;
  errors: string[];
}

export interface UserAccountPermissionCreate {
  user_id: number;
  permission_level: PermissionLevel;
  notes?: string;
}

export interface AccountSettingsUpdate {
  setting_key: string;
  setting_value?: string;
  setting_type?: string;
}