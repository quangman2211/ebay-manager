/**
 * Login page styles - SOLID S: Single Responsibility (styling only)
 * All styling logic for Login component
 */

import { colors } from '../common/colors';
import { spacing } from '../common/spacing';

export const loginStyles = {
  // Main container
  container: {
    maxWidth: 'sm' as const,
    mt: spacing.loginTopMargin
  },

  // Card content
  cardContent: {
    p: spacing.headerPadding
  },

  // Header container
  headerContainer: {
    textAlign: 'center' as const,
    mb: spacing.containerGap
  },

  // Error alert
  errorAlert: {
    mb: spacing.sectionGap
  },

  // Login button
  loginButton: {
    mt: spacing.buttonSpacing
  },

  // Demo credentials container
  demoContainer: {
    mt: spacing.sectionGap,
    p: spacing.sectionGap,
    backgroundColor: colors.bgDemo,
    borderRadius: spacing.md
  }
} as const;

// Type for TypeScript intellisense
export type LoginStylesType = typeof loginStyles;