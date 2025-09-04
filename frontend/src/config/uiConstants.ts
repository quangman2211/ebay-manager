/**
 * UI configuration constants
 * Centralized to eliminate hardcoded values (SOLID compliance)
 * 
 * Following SOLID principles:
 * - Single Responsibility: Only UI-related constants
 * - Open/Closed: Extensible for new UI configurations
 * - Interface Segregation: Focused constant groups for different UI aspects
 */

// Test Timeouts (for test files)
export const TEST_CONFIG = {
  DEFAULT_TIMEOUT: 3000,
  ASYNC_TIMEOUT: 5000,
  NETWORK_TIMEOUT: 10000,
} as const;

// Table Configuration
export const TABLE_CONFIG = {
  DEFAULT_PAGE_SIZE: 10,
  PAGE_SIZE_OPTIONS: [5, 10, 25, 50],
  MAX_BULK_SELECTION: 100,
  ROW_HEIGHT: 52,
} as const;

// Form Configuration
export const FORM_CONFIG = {
  DEBOUNCE_DELAY: 300,
  VALIDATION_DELAY: 500,
  AUTO_SAVE_DELAY: 2000,
  MIN_PASSWORD_LENGTH: 8,
  MAX_INPUT_LENGTH: 255,
} as const;

// Animation and Transition
export const ANIMATION = {
  DURATION: {
    FAST: 150,
    NORMAL: 300,
    SLOW: 500,
  },
  EASING: {
    EASE_IN: 'ease-in',
    EASE_OUT: 'ease-out',
    EASE_IN_OUT: 'ease-in-out',
  },
} as const;

// Spacing and Layout
export const LAYOUT = {
  HEADER_HEIGHT: 64,
  SIDEBAR_WIDTH: 240,
  SIDEBAR_MINI_WIDTH: 60,
  FOOTER_HEIGHT: 48,
  CONTENT_MAX_WIDTH: 1200,
} as const;

// Z-Index Layers
export const Z_INDEX = {
  DRAWER: 1200,
  APP_BAR: 1100,
  MODAL: 1300,
  SNACKBAR: 1400,
  TOOLTIP: 1500,
} as const;

// Breakpoints (should align with MUI theme)
export const BREAKPOINTS = {
  XS: 0,
  SM: 600,
  MD: 900,
  LG: 1200,
  XL: 1536,
} as const;

// CSV Upload UI Configuration
export const CSV_UPLOAD = {
  DROPZONE_HEIGHT: 200,
  MAX_FILE_DISPLAY_SIZE: 5, // Show max 5 files in suggestions
  SUGGESTION_DELAY: 1000, // Delay before showing suggestions
  PREVIEW_ROWS: 5, // Preview first 5 rows of CSV
} as const;

// Account Management UI
export const ACCOUNT_UI = {
  CARD_HEIGHT: 300,
  AVATAR_SIZE: 48,
  STATUS_INDICATOR_SIZE: 16,
  METRICS_CHART_HEIGHT: 200,
} as const;

// Notification Configuration  
export const NOTIFICATIONS = {
  AUTO_HIDE_DURATION: 6000,
  MAX_STACK_SIZE: 3,
  DEFAULT_POSITION: 'bottom-right' as const,
} as const;

// Colors (for when MUI theme colors aren't available)
export const COLORS = {
  SUCCESS: '#4caf50',
  WARNING: '#ff9800', 
  ERROR: '#f44336',
  INFO: '#2196f3',
  GREY: {
    50: '#fafafa',
    100: '#f5f5f5',
    200: '#eeeeee',
    300: '#e0e0e0',
    400: '#bdbdbd',
    500: '#9e9e9e',
  },
} as const;

// Data Validation UI
export const VALIDATION = {
  REQUIRED_INDICATOR: ' *',
  ERROR_ICON: 'error',
  SUCCESS_ICON: 'check_circle',
  WARNING_ICON: 'warning',
} as const;