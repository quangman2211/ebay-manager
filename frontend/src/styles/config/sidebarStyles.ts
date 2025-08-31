/**
 * Sidebar styles - SOLID S: Single Responsibility (styling only)
 * All styling logic for ModernSidebar component
 * SOLID D: Depend on abstractions, not concretions
 */

import { colors } from '../common/colors';
import { spacing } from '../common/spacing';

export const sidebarStyles = {
  // Dimensions
  dimensions: {
    expanded: 260,
    collapsed: 64,
    logoHeight: 64,
    itemHeight: 48,
    avatarSize: 36,
    chipHeight: 24,
    borderWidth: 1,
  },

  // Main container styles
  container: {
    background: colors.bgSearch, // '#f8fafc'
    height: '100%',
    display: 'flex',
    flexDirection: 'column' as const,
  },

  // Logo section styles
  logoSection: {
    expanded: {
      p: spacing.xl, // 24px
      borderBottom: `1px solid ${colors.borderMedium}`, // '#e2e8f0'
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'flex-start',
      minHeight: 64,
    },
    collapsed: {
      p: spacing.lg, // 16px -> 1.5 for 12px
      borderBottom: `1px solid ${colors.borderMedium}`,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: 64,
    }
  },

  // Logo text styles
  logoText: {
    expanded: {
      fontWeight: 600,
      color: colors.textHeader, // '#424242' close to '#1e293b'
      letterSpacing: '-0.025em',
      opacity: 1,
    }
  },

  // Logo icon styles (collapsed state)
  logoIcon: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    width: 40,
    height: 40,
    borderRadius: spacing.md, // 8px -> 1
    backgroundColor: colors.primary[500], // '#3b82f6'
    color: 'white',
    fontSize: '1rem',
    fontWeight: 700,
  },

  // Navigation container styles
  navigation: {
    expanded: {
      flex: 1,
      px: spacing.lg, // 16px -> 1.5
      py: spacing.xl, // 24px
    },
    collapsed: {
      flex: 1,
      px: spacing.sm, // 4px -> 0.5
      py: spacing.xl,
    }
  },

  // Menu item styles
  menuItem: {
    base: {
      borderRadius: spacing.md,
      cursor: 'pointer',
      mb: spacing.sm,
      py: 1.25,
      minHeight: 48,
    },
    expanded: {
      px: spacing.lg, // 16px -> 1.5
      justifyContent: 'flex-start',
    },
    collapsed: {
      px: spacing.md, // 8px -> 1
      justifyContent: 'center',
    },
    active: {
      backgroundColor: colors.primary[500], // '#3b82f6'
      color: 'white',
    },
    inactive: {
      backgroundColor: 'transparent',
      color: colors.textSecondary, // '#666' close to '#475569'
    },
    hover: {
      active: colors.primary[500],
      inactive: colors.borderMedium, // '#e0e0e0' close to '#e2e8f0'
    }
  },

  // Menu item icon styles
  menuIcon: {
    expanded: {
      color: 'inherit',
      minWidth: 32,
      mr: spacing.xl, // 24px
      justifyContent: 'center',
      '& .MuiSvgIcon-root': { fontSize: 20 },
    },
    collapsed: {
      color: 'inherit',
      minWidth: 'auto',
      mr: 0,
      justifyContent: 'center',
      '& .MuiSvgIcon-root': { fontSize: 20 },
    }
  },

  // Menu item text styles
  menuText: {
    '& .MuiTypography-root': {
      fontSize: '0.875rem',
      fontWeight: 500,
      opacity: 1,
    }
  },

  // User profile section styles
  profileSection: {
    expanded: {
      p: spacing.containerGap, // 24px -> 2.5 close
      borderTop: `1px solid ${colors.borderMedium}`,
      backgroundColor: colors.bgPrimary, // '#ffffff'
      display: 'flex',
      flexDirection: 'column' as const,
      alignItems: 'flex-start',
    },
    collapsed: {
      p: spacing.md, // 8px -> 1
      borderTop: `1px solid ${colors.borderMedium}`,
      backgroundColor: colors.bgPrimary,
      display: 'flex',
      flexDirection: 'column' as const,
      alignItems: 'center',
    }
  },

  // Profile container styles
  profileContainer: {
    expanded: {
      display: 'flex',
      alignItems: 'center',
      gap: spacing.lg, // 16px -> 1.5
      mb: spacing.lg,
      justifyContent: 'center',
    },
    collapsed: {
      display: 'flex',
      alignItems: 'center',
      gap: 0,
      mb: spacing.md, // 8px -> 1
      justifyContent: 'center',
    }
  },

  // Avatar styles
  avatar: {
    width: 36,
    height: 36,
    backgroundColor: colors.primary[500], // '#3b82f6'
    fontSize: '0.875rem',
    fontWeight: 600,
  },

  // Profile text styles
  profileText: {
    username: {
      fontWeight: 600,
      color: colors.textHeader, // '#424242' close to '#1e293b'
      fontSize: '0.875rem',
      opacity: 1,
    },
    role: {
      color: colors.textSecondary, // '#666' close to '#64748b'
      fontSize: '0.75rem',
      opacity: 1,
    }
  },

  // Profile chip styles
  profileChip: {
    backgroundColor: colors.bgSecondary, // '#fafafa' close to '#f1f5f9'
    color: colors.textSecondary, // '#666' close to '#475569'
    border: `1px solid ${colors.borderMedium}`, // '#e0e0e0' close to '#e2e8f0'
    fontSize: '0.6875rem',
    fontWeight: 500,
    height: '24px',
    opacity: 1,
  },

  // Drawer styles
  drawer: {
    mobile: {
      display: { xs: 'block', md: 'none' },
      '& .MuiDrawer-paper': {
        boxSizing: 'border-box',
        width: 260, // Using dimension constant implicitly
      },
    },
    desktop: {
      display: { xs: 'none', md: 'block' },
      '& .MuiDrawer-paper': {
        boxSizing: 'border-box',
        border: 'none',
        borderRight: `1px solid ${colors.borderMedium}`,
        overflowX: 'hidden',
      },
    }
  },

  // Transitions
  transitions: {
    duration: 300, // 0.3s in milliseconds
    easing: 'cubic-bezier(0.4, 0, 0.2, 1)', // MUI easing.sharp
  }
} as const;

// Type for TypeScript intellisense
export type SidebarStylesType = typeof sidebarStyles;