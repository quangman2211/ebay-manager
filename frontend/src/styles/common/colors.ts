/**
 * Color constants - SOLID D: Depend on abstractions, not concretions
 * Centralized color definitions to eliminate hardcoded values
 */

export const colors = {
  // Status colors
  success: '#2e7d32',
  warning: '#f57c00', 
  error: '#d32f2f',
  
  // Text colors
  textPrimary: '#333',
  textSecondary: '#666',
  textHeader: '#424242',
  textPlaceholder: '#999',
  
  // Background colors  
  bgPrimary: '#ffffff',
  bgSecondary: '#fafafa',
  bgHover: '#f8f9fa',
  bgHoverAlt: '#f0f0f0',
  bgSelected: '#e3f2fd',
  bgDemo: '#f5f5f5',
  bgDropzone: '#f9f9f9',
  bgSearch: '#f8fafc',
  
  // Border colors
  borderLight: '#f5f5f5',
  borderMedium: '#e0e0e0',
  borderDrag: '#ccc',
  borderSearch: '#e1e5e9',
  
  // Primary colors (Blue palette for modern UI)
  primary: {
    50: '#eff6ff',
    100: '#dbeafe', 
    200: '#bfdbfe',
    300: '#93c5fd',
    400: '#60a5fa',
    500: '#3b82f6',
    600: '#2563eb',
    700: '#1d4ed8',
    800: '#1e40af',
    900: '#1e3a8a',
  },
  
  // DataGrid specific colors
  dataGrid: {
    cellBorder: '#f5f5f5',
    headerBg: '#fafafa',
    headerBorder: '#e0e0e0',
    rowEvenBg: '#fafafa',
    rowHover: '#f8f9fa',
    rowHoverEven: '#f0f0f0',
    footerBorder: '#e0e0e0',
    footerBg: '#fafafa'
  }
} as const;

// Type for TypeScript intellisense
export type ColorsType = typeof colors;