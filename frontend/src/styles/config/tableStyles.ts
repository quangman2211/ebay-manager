/**
 * Table styles - SOLID S: Single Responsibility (styling only)
 * All styling logic for OrderTableColumns component
 */

import { colors } from '../common/colors';
import { spacing } from '../common/spacing';

export const tableStyles = {
  // Order number cell
  orderNumber: {
    fontSize: '13px',
    fontWeight: 600
  },

  // Item number cell
  itemNumber: {
    fontSize: '12px',
    color: colors.textSecondary
  },

  // Customer info container
  customerContainer: {
    py: spacing.sm
  },

  // Customer info row
  customerInfoRow: {
    display: 'flex',
    alignItems: 'center',
    gap: spacing.sm,
    mb: spacing.xs
  },

  // Customer info text
  customerText: {
    fontSize: '11px',
    color: colors.textSecondary
  },

  // Customer name text (slightly different styling)
  customerNameText: {
    fontSize: '12px',
    color: colors.textPrimary,
    fontWeight: 500
  },

  // Customer icons
  customerIcon: {
    fontSize: 12,
    color: colors.textSecondary
  },

  // Customer name icon (slightly different)
  customerNameIcon: {
    fontSize: 12,
    color: colors.textPrimary
  },

  // Item title text
  itemTitle: {
    fontSize: '13px',
    lineHeight: 1.4,
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    display: '-webkit-box',
    WebkitLineClamp: 2,
    WebkitBoxOrient: 'vertical' as const
  },

  // Option text
  optionText: {
    fontSize: '12px',
    color: colors.textSecondary
  },

  // Sale date text
  saleDateText: {
    fontSize: '12px',
    color: colors.textSecondary
  },

  // Ship by date container
  shipByContainer: {
    display: 'flex',
    alignItems: 'center',
    gap: spacing.sm
  },

  // Ship by date text
  shipByText: {
    fontSize: '12px'
  },

  // Ship by icon base style
  shipByIcon: {
    fontSize: 16
  },

  // Amount text
  amountText: {
    fontSize: '14px',
    fontWeight: 600,
    color: colors.success
  },

  // Status chip
  statusChip: {
    fontWeight: 600,
    fontSize: '12px',
    height: '28px'
  }
} as const;

// Type for TypeScript intellisense
export type TableStylesType = typeof tableStyles;