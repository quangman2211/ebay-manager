/**
 * Styles index - SOLID I: Interface Segregation
 * Single import point for all styling constants and utilities
 */

// Export all constants
export { colors, type ColorsType } from './common/colors';
export { spacing, type SpacingType } from './common/spacing';
export { themeConfig, type ThemeConfigType } from './common/theme';

// Export component styles
export { sidebarStyles, type SidebarStylesType } from './config/sidebarStyles';
export { layoutStyles, type LayoutStylesType } from './config/layoutStyles';
export { headerStyles, type HeaderStylesType } from './config/headerStyles';
export { tableStyles, type TableStylesType } from './config/tableStyles';

// Re-export everything for convenience
export * from './common/colors';
export * from './common/spacing';
export * from './common/theme';
export * from './config/sidebarStyles';
export * from './config/layoutStyles';
export * from './config/headerStyles';
export * from './config/tableStyles';