/**
 * Header styles - SOLID S: Single Responsibility (styling only)
 * All styling logic for HeaderWithSearch component
 * SOLID D: Depend on abstractions, not concretions
 */

import { colors } from '../common/colors';
import { spacing } from '../common/spacing';

export const headerStyles = {
  // AppBar styles
  appBar: {
    backgroundColor: colors.bgPrimary, // '#ffffff'
    color: colors.textPrimary, // '#333'
    boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.1)',
  },

  // Toolbar styles
  toolbar: {
    justifyContent: 'space-between',
    px: spacing.xl, // 24px
  },

  // Hamburger menu button
  hamburgerButton: {
    mr: spacing.md, // 8px
    color: colors.textSecondary, // '#666'
    '&:hover': {
      backgroundColor: colors.bgHover, // '#f8f9fa'
    },
  },

  // Search container
  searchContainer: {
    position: 'relative' as const,
    flexGrow: 1,
    maxWidth: '100%',
    mr: spacing.xl, // 24px
  },

  // Search box
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
      padding: `${spacing.searchPadding * 8}px ${spacing.md * 8}px ${spacing.searchPadding * 8}px 0`, // 12px 8px 12px 0
      paddingLeft: `calc(1em + ${spacing.xxl * 8}px)`, // calc(1em + 32px)
      transition: 'width 0.3s ease, padding 0.3s ease',
      width: '100%',
      fontSize: '16px',
      '&::placeholder': {
        color: colors.textPlaceholder, // '#999'
        fontSize: '16px',
      },
    },
  },

  // Clear search button
  clearButton: {
    position: 'absolute' as const,
    right: spacing.searchGap * 8, // 8px
    top: '50%',
    transform: 'translateY(-50%)',
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

  // Search result item
  searchResultItem: {
    py: spacing.searchPadding, // 12px
    px: spacing.lg, // 16px
    '&:hover': {
      backgroundColor: colors.bgHover, // '#f8f9fa'
    },
    transition: 'background-color 0.2s ease',
  },

  // Loading/no results text
  searchStatusText: {
    p: spacing.lg, // 16px
    textAlign: 'center' as const,
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
      backgroundColor: `${colors.primary[500]}14`, // '#3b82f6' with 8% opacity
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

  // Menu item with icon
  menuItemWithIcon: {
    mr: spacing.md, // 8px
  },
} as const;

// Type for TypeScript intellisense
export type HeaderStylesType = typeof headerStyles;