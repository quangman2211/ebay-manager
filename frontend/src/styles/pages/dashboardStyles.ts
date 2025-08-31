/**
 * Dashboard page styles - SOLID S: Single Responsibility (styling only)
 * All styling logic for Dashboard component with responsive grid enhancements
 */

import { spacing } from '../common/spacing';

export const dashboardStyles = {
  // Main dashboard container with responsive layout including mini mode
  dashboardContainer: {
    width: '100%',
    padding: {
      mini: spacing.xs,  // 2px on mini screens (browser mini mode)
      xs: spacing.md,    // 8px on mobile  
      sm: spacing.lg,    // 16px on small screens  
      md: spacing.xl,    // 24px on medium screens
      lg: spacing.xxl,   // 32px on large screens
    }
  },

  // Loading container
  loadingContainer: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    minHeight: '50vh',
    mt: spacing.xxl
  },

  // Enhanced page header container with responsive behavior including mini mode
  headerContainer: {
    mb: {
      mini: spacing.sm,      // 4px on mini screens
      xs: spacing.lg,        // 16px on mobile
      sm: spacing.xl,        // 24px on small screens
      md: spacing.containerGap // 24px on medium+ screens
    },
    display: 'flex',
    flexDirection: {
      mini: 'column',        // Stack vertically on mini screens
      xs: 'column',          // Stack vertically on mobile
      sm: 'row'              // Side by side on small screens+
    },
    justifyContent: 'space-between',
    alignItems: {
      mini: 'stretch',       // Full width on mini screens
      xs: 'stretch',         // Full width on mobile
      sm: 'center'           // Center aligned on small screens+
    },
    gap: {
      mini: spacing.xs,      // 2px gap on mini screens
      xs: spacing.lg,        // 16px gap on mobile
      sm: spacing.md         // 8px gap on small screens+
    }
  },

  // Responsive page title including mini mode
  pageTitle: {
    fontSize: {
      mini: '1.25rem',       // 20px on mini screens
      xs: '1.75rem',         // 28px on mobile
      sm: '2rem',            // 32px on small screens
      md: '2.125rem'         // 34px on medium+ screens
    },
    fontWeight: 600,
    textAlign: {
      mini: 'center',        // Center on mini screens
      xs: 'center',          // Center on mobile
      sm: 'left'             // Left align on small screens+
    }
  },

  // Enhanced account select with responsive sizing including mini mode
  accountSelect: {
    minWidth: {
      mini: '100%',          // Full width on mini screens
      xs: '100%',            // Full width on mobile
      sm: 250,               // Fixed width on small screens
      md: 300                // Larger width on medium+ screens
    },
    maxWidth: {
      mini: '100%',
      xs: '100%',
      sm: 350,
      md: 400
    },
    '& .MuiInputLabel-root': {
      fontSize: {
        mini: '0.75rem',     // Smaller label on mini screens
        xs: '1rem'
      }
    }
  },

  // Responsive grid container with enhanced spacing including mini mode
  gridContainer: {
    spacing: {
      mini: spacing.xs,      // 2px spacing on mini screens
      xs: spacing.lg,        // 16px spacing on mobile
      sm: spacing.xl,        // 24px spacing on small screens  
      md: spacing.containerGap, // 24px spacing on medium screens
      lg: spacing.xxl,       // 32px spacing on large screens
      xl: spacing.xxl        // 32px spacing on extra large screens
    },
    mt: {
      mini: spacing.xs,
      xs: spacing.lg,
      sm: spacing.xl,
      md: spacing.containerGap,
      lg: spacing.containerGap,
      xl: spacing.containerGap
    }
  },

  // Enhanced metric cards with responsive design including mini mode
  metricCard: {
    height: {
      mini: 100,             // Compact height for mini screens
      xs: 140,               // Smaller height on mobile
      sm: 160,               // Medium height on small screens
      md: 180                // Full height on medium+ screens
    },
    minHeight: {
      mini: 90,              // Minimum height for mini screens
      xs: 120
    },
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'space-between',
    transition: 'transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out',
    '&:hover': {
      transform: 'translateY(-4px)',
      boxShadow: '0 8px 24px rgba(0,0,0,0.12)'
    }
  },

  // Responsive card content including mini mode
  cardContent: {
    padding: {
      mini: `${spacing.xs * 8}px !important`,  // 2px on mini screens
      xs: `${spacing.lg * 8}px !important`,    // 16px on mobile
      sm: `${spacing.xl * 8}px !important`,    // 24px on small screens
      md: `${spacing.xxl * 8}px !important`    // 32px on medium+ screens
    },
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
    justifyContent: 'space-between',
    '&:last-child': {
      paddingBottom: {
        mini: `${spacing.xs * 8}px !important`,
        xs: `${spacing.lg * 8}px !important`
      }
    }
  },

  // Responsive metric value typography including mini mode
  metricValue: {
    fontSize: {
      mini: '1.25rem',       // 20px on mini screens - smaller for space
      xs: '1.75rem',         // 28px on mobile
      sm: '2.25rem',         // 36px on small screens
      md: '2.5rem'           // 40px on medium+ screens
    },
    fontWeight: 700,
    lineHeight: {
      mini: 1.1,             // Tighter line height for mini screens
      xs: 1.2
    },
    color: 'primary.main',
    wordBreak: 'break-word', // Prevent text overflow
    overflow: 'hidden'
  },

  // Responsive metric label including mini mode
  metricLabel: {
    fontSize: {
      mini: '0.625rem',      // 10px on mini screens - very compact
      xs: '0.75rem',         // 12px on mobile
      sm: '0.875rem',        // 14px on small screens
      md: '1rem'             // 16px on medium+ screens
    },
    fontWeight: 500,
    color: 'text.secondary',
    textTransform: 'uppercase' as const,
    letterSpacing: '0.05em',
    mb: {
      mini: spacing.xs,      // Less margin on mini screens
      xs: spacing.md
    },
    lineHeight: {
      mini: 1.2,
      xs: 1.4
    }
  },

  // Enhanced status chip with responsive sizing
  statusChip: {
    mt: spacing.md,
    fontSize: {
      xs: '0.6875rem',       // 11px on mobile
      sm: '0.75rem',         // 12px on small screens+
    },
    height: {
      xs: 20,                // Smaller height on mobile
      sm: 24                 // Standard height on small screens+
    }
  },

  // Grid item responsive configurations including mini mode
  gridItemConfig: {
    // Mini screens: 1 column (12/12) - for browser mini mode
    mini: {
      xs: 12
    },
    // Mobile: 1 column (12/12)
    mobile: {
      xs: 12
    },
    // Small screens: 2 columns (6/12 each)  
    small: {
      xs: 12,
      sm: 6
    },
    // Medium screens: 3 columns (4/12 each)
    medium: {
      xs: 12,
      sm: 6,
      md: 4
    },
    // Large screens: 4 columns (3/12 each)
    large: {
      xs: 12,
      sm: 6,
      md: 4,
      lg: 3
    }
  },

  // Container queries for modern browsers (progressive enhancement)
  containerQueries: {
    '@container (max-width: 480px)': {
      gridTemplateColumns: '1fr',
      gap: spacing.lg
    },
    '@container (min-width: 481px) and (max-width: 768px)': {
      gridTemplateColumns: 'repeat(2, 1fr)',
      gap: spacing.xl
    },
    '@container (min-width: 769px) and (max-width: 1024px)': {
      gridTemplateColumns: 'repeat(3, 1fr)',
      gap: spacing.containerGap
    },
    '@container (min-width: 1025px)': {
      gridTemplateColumns: 'repeat(4, 1fr)',
      gap: spacing.xxl
    }
  },

  // CSS Grid fallback for modern browsers
  cssGridContainer: {
    display: 'grid',
    gridTemplateColumns: {
      xs: '1fr',                          // 1 column on mobile
      sm: 'repeat(2, 1fr)',              // 2 columns on small screens
      md: 'repeat(3, 1fr)',              // 3 columns on medium screens
      lg: 'repeat(4, 1fr)',              // 4 columns on large screens
      xl: 'repeat(4, 1fr)'               // 4 columns on extra large screens
    },
    gap: {
      xs: spacing.lg,
      sm: spacing.xl,
      md: spacing.containerGap,
      lg: spacing.xxl
    },
    mt: {
      xs: spacing.lg,
      sm: spacing.xl,
      md: spacing.containerGap
    }
  }
} as const;

// Type for TypeScript intellisense  
export type DashboardStylesType = typeof dashboardStyles;