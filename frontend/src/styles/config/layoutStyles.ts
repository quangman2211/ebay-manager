/**
 * Layout styles - SOLID S: Single Responsibility (styling only)
 * All styling logic for Layout and Header components  
 * SOLID D: Depend on abstractions, not concretions
 */

import { colors } from '../common/colors';
import { spacing } from '../common/spacing';

export const layoutStyles = {
  // Main layout container
  container: {
    display: 'flex',
    height: '100%',
    backgroundColor: colors.bgSearch, // '#f8fafc'
    overflow: 'hidden',
  },

  // Main content area
  mainContent: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column' as const,
    overflow: 'hidden',
  },

  // Page content area (scrollable)
  pageContent: {
    flex: 1,
    overflowY: 'auto' as const,
    overflowX: 'hidden' as const,
    p: spacing.xl, // 24px
    mt: spacing.xxxl, // 64px (8 * 8px)
  },

  // Header styles
  header: {
    backgroundColor: colors.bgPrimary, // '#ffffff'
    color: colors.textPrimary, // '#333'
    boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.1)',
  },

  // Toolbar styles
  toolbar: {
    justifyContent: 'space-between',
    px: spacing.xl, // 24px
  },

  // Search container styles
  searchContainer: {
    position: 'relative' as const,
    flexGrow: 1,
    maxWidth: '100%',
    mr: spacing.xl,
  },

  // Search box styles
  searchBox: {
    position: 'relative' as const,
    borderRadius: spacing.xl, // 24px
    backgroundColor: colors.bgSearch, // '#f8fafc'
    border: `1px solid ${colors.borderSearch}`, // '#e1e5e9'
    '&:hover': {
      backgroundColor: colors.bgHover, // '#f8f9fa'
      borderColor: `${colors.primary[500]}30`, // '#3b82f6' with 30% opacity
    },
    '&:focus-within': {
      backgroundColor: colors.bgPrimary, // '#ffffff'
      borderColor: colors.primary[500], // '#3b82f6'
      boxShadow: `0 0 0 3px ${colors.primary[500]}1A`, // '#3b82f6' with 10% opacity
    },
    width: '100%',
    minHeight: 48,
  },

  // Search icon container
  searchIconContainer: {
    padding: `0 ${spacing.lg * 8}px`, // 16px
    height: '100%',
    position: 'absolute' as const,
    pointerEvents: 'none' as const,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },

  // Search icon
  searchIcon: {
    color: colors.textSecondary, // '#666'
  },

  // Search input
  searchInput: {
    color: 'inherit',
    width: '100%',
    fontSize: '16px',
    '& .MuiInputBase-input': {
      fontSize: '16px',
      '&::placeholder': {
        color: colors.textPlaceholder, // '#999'
        fontSize: '16px',
      },
    },
  },

  // Search results dropdown
  searchResults: {
    position: 'absolute' as const,
    top: '100%',
    left: 0,
    right: 0,
    mt: spacing.md, // 8px
    maxHeight: 500,
    overflow: 'auto' as const,
    zIndex: 1300, // MUI modal z-index
    boxShadow: '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 10px 10px -5px rgb(0 0 0 / 0.04)',
    borderRadius: spacing.xl, // 24px
    border: `1px solid ${colors.borderLight}`, // '#f5f5f5'
  },

  // User menu container
  userMenuContainer: {
    display: 'flex',
    alignItems: 'center',
    minWidth: 'max-content',
  },

  // Username text
  usernameText: {
    mr: spacing.lg, // 16px
    display: { xs: 'none', md: 'block' },
    fontWeight: 500,
    color: colors.textSecondary, // '#666'
  },

  // Profile button
  profileButton: {
    p: spacing.sm, // 4px
    '&:hover': {
      backgroundColor: `${colors.primary[500]}14`, // '#3b82f6' with 8% opacity (14 hex = ~8%)
    },
  },

  // Profile avatar
  profileAvatar: {
    width: 36,
    height: 36,
    bgcolor: colors.primary[500], // '#3b82f6'
    fontSize: '16px',
    fontWeight: 600,
  },

  // Hamburger menu button
  hamburgerButton: {
    mr: spacing.md, // 8px
    color: colors.textSecondary, // '#666'
    '&:hover': {
      backgroundColor: colors.bgHover, // '#f8f9fa'
    },
  },

  // Transitions
  transitions: {
    duration: 300, // 0.3s in milliseconds
    easing: 'cubic-bezier(0.4, 0, 0.2, 1)', // MUI easing.sharp
  }
} as const;

// Type for TypeScript intellisense
export type LayoutStylesType = typeof layoutStyles;