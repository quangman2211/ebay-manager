/**
 * Account management configuration constants
 * Centralized to eliminate hardcoded values (SOLID compliance)
 * 
 * Following SOLID principles:
 * - Single Responsibility: Only account-related constants
 * - Open/Closed: Extensible for new platforms and statuses
 * - Dependency Inversion: Components depend on abstractions via constants
 */

// Platform Types
export const PLATFORMS = {
  EBAY: 'ebay',
  ETSY: 'etsy',
  SYSTEM: 'system',
} as const;

export type Platform = typeof PLATFORMS[keyof typeof PLATFORMS];

// Connection Status Constants
export const CONNECTION_STATUSES = {
  AUTHENTICATED: 'authenticated',
  PENDING: 'pending',
  EXPIRED: 'expired',
  FAILED: 'failed',
  SYSTEM: 'system',
} as const;

export type ConnectionStatus = typeof CONNECTION_STATUSES[keyof typeof CONNECTION_STATUSES];

// Default Values
export const ACCOUNT_DEFAULTS = {
  PLATFORM: PLATFORMS.EBAY,
  CONNECTION_STATUS: CONNECTION_STATUSES.AUTHENTICATED,
  DATA_PROCESSING_ENABLED: true,
  IS_ACTIVE: true,
  USER_ID: 1, // Should be replaced with actual current user context
} as const;

// Status Labels for UI Display
export const CONNECTION_STATUS_LABELS: Record<ConnectionStatus, string> = {
  [CONNECTION_STATUSES.AUTHENTICATED]: 'Authenticated',
  [CONNECTION_STATUSES.PENDING]: 'Pending',
  [CONNECTION_STATUSES.EXPIRED]: 'Expired',
  [CONNECTION_STATUSES.FAILED]: 'Failed',
  [CONNECTION_STATUSES.SYSTEM]: 'System',
};

export const PLATFORM_LABELS: Record<Platform, string> = {
  [PLATFORMS.EBAY]: 'eBay',
  [PLATFORMS.ETSY]: 'Etsy',
  [PLATFORMS.SYSTEM]: 'System',
};

// Status Color Mappings for MUI Components
export const CONNECTION_STATUS_COLORS: Record<ConnectionStatus, 'success' | 'warning' | 'error' | 'default'> = {
  [CONNECTION_STATUSES.AUTHENTICATED]: 'success',
  [CONNECTION_STATUSES.PENDING]: 'warning',
  [CONNECTION_STATUSES.EXPIRED]: 'error',
  [CONNECTION_STATUSES.FAILED]: 'error',
  [CONNECTION_STATUSES.SYSTEM]: 'default',
};

// Helper Functions
export const getConnectionStatusLabel = (status: ConnectionStatus): string => {
  return CONNECTION_STATUS_LABELS[status] || status;
};

export const getConnectionStatusColor = (status: ConnectionStatus | undefined): 'success' | 'warning' | 'error' | 'default' => {
  return status ? CONNECTION_STATUS_COLORS[status] : 'default';
};

export const getPlatformLabel = (platform: Platform): string => {
  return PLATFORM_LABELS[platform] || platform;
};

export const isValidPlatform = (platform: string): platform is Platform => {
  return Object.values(PLATFORMS).includes(platform as Platform);
};

export const isValidConnectionStatus = (status: string): status is ConnectionStatus => {
  return Object.values(CONNECTION_STATUSES).includes(status as ConnectionStatus);
};

// Form Options for Select Components
export const CONNECTION_STATUS_OPTIONS = Object.entries(CONNECTION_STATUS_LABELS).map(([value, label]) => ({
  value: value as ConnectionStatus,
  label,
}));

export const PLATFORM_OPTIONS = Object.entries(PLATFORM_LABELS).map(([value, label]) => ({
  value: value as Platform,
  label,
}));