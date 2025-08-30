/**
 * Dashboard page styles - SOLID S: Single Responsibility (styling only)
 * All styling logic for Dashboard component  
 */

import { spacing } from '../common/spacing';

export const dashboardStyles = {
  // Loading container
  loadingContainer: {
    display: 'flex',
    justifyContent: 'center',
    mt: spacing.xxl
  },

  // Page header container
  headerContainer: {
    mb: spacing.containerGap,
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center'
  },

  // Account select form control
  accountSelect: {
    minWidth: 200
  },

  // Grid container
  gridContainer: {
    spacing: spacing.containerGap
  },

  // Status chip
  statusChip: {
    mt: spacing.md
  }
} as const;

// Type for TypeScript intellisense  
export type DashboardStylesType = typeof dashboardStyles;