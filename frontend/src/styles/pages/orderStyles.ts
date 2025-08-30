/**
 * Orders page styles - SOLID S: Single Responsibility (styling only)  
 * All styling logic for Orders component
 */

import { colors } from '../common/colors';
import { spacing } from '../common/spacing';

export const orderStyles = {
  // Page header container
  headerContainer: {
    mb: spacing.containerGap,
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center'
  },

  // Filters container
  filtersContainer: {
    display: 'flex',
    gap: spacing.sectionGap
  },

  // Account select form control
  accountSelect: {
    minWidth: 200
  },

  // Status filter form control  
  statusSelect: {
    minWidth: 150
  },

  // DataGrid container styles
  dataGrid: {
    '& .MuiDataGrid-root': {
      border: 'none'
    },
    '& .MuiDataGrid-cell': {
      borderRight: `1px solid ${colors.dataGrid.cellBorder}`,
      borderBottom: `1px solid ${colors.dataGrid.cellBorder}`,
      padding: `${spacing.cellPadding * 8}px`
    },
    '& .MuiDataGrid-columnHeader': {
      backgroundColor: colors.dataGrid.headerBg,
      fontWeight: 600,
      fontSize: '13px',
      borderRight: `1px solid ${colors.dataGrid.headerBorder}`,
      color: colors.textHeader
    },
    '& .MuiDataGrid-row': {
      '&:hover': {
        backgroundColor: colors.dataGrid.rowHover
      },
      '&.Mui-selected': {
        backgroundColor: colors.bgSelected
      }
    },
    '& .MuiDataGrid-row:nth-of-type(even)': {
      backgroundColor: colors.dataGrid.rowEvenBg,
      '&:hover': {
        backgroundColor: colors.dataGrid.rowHoverEven
      }
    },
    '& .MuiDataGrid-footer': {
      borderTop: `2px solid ${colors.dataGrid.footerBorder}`,
      backgroundColor: colors.dataGrid.footerBg
    }
  }
} as const;

// Type for TypeScript intellisense
export type OrderStylesType = typeof orderStyles;