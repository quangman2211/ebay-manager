/**
 * Styles index - SOLID I: Interface Segregation
 * Single import point for all styling constants and utilities
 */

// Export all constants
export { colors, type ColorsType } from './common/colors';
export { spacing, type SpacingType } from './common/spacing';

// Re-export everything for convenience
export * from './common/colors';
export * from './common/spacing';

// Future: Export style objects and styled components when created
// export * from './pages';
// export * from './config';
// export * from './common/components';