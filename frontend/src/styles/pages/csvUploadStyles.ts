/**
 * CSV Upload page styles - SOLID S: Single Responsibility (styling only)
 * All styling logic for CSVUpload component
 */

import { colors } from '../common/colors';
import { spacing } from '../common/spacing';

export const csvUploadStyles = {
  // Page title
  pageTitle: {
    mb: spacing.containerGap
  },

  // Configuration container
  configContainer: {
    mb: spacing.containerGap,
    display: 'flex',
    gap: spacing.sectionGap
  },

  // Account select form control
  accountSelect: {
    minWidth: 200
  },

  // Data type select form control
  dataTypeSelect: {
    minWidth: 150
  },

  // Upload card container
  uploadCard: {
    mb: spacing.containerGap
  },

  // Upload dropzone area
  dropzoneArea: (selectedAccount: boolean, uploading: boolean, isDragActive: boolean) => ({
    border: `2px dashed ${colors.borderDrag}`,
    borderRadius: spacing.sectionGap,
    p: spacing.dropzonePadding,
    textAlign: 'center' as const,
    cursor: selectedAccount && !uploading ? 'pointer' : 'not-allowed',
    backgroundColor: isDragActive ? colors.bgSecondary : 'transparent',
    opacity: selectedAccount && !uploading ? 1 : 0.5,
    transition: 'all 0.2s ease',
    '&:hover': {
      backgroundColor: selectedAccount && !uploading ? colors.bgDropzone : 'transparent'
    }
  }),

  // Upload progress container
  uploadProgressContainer: {},

  // Upload progress spinner
  progressSpinner: {
    mb: spacing.sectionGap
  },

  // Upload content container
  uploadContentContainer: {},

  // Cloud upload icon
  cloudIcon: {
    fontSize: 48,
    color: colors.borderDrag,
    mb: spacing.sectionGap
  },

  // Upload title text
  uploadTitle: {
    mb: spacing.md
  },

  // Upload subtitle text
  uploadSubtitle: {},

  // Account error text
  accountErrorText: {
    mt: spacing.md
  },

  // Upload result alert
  resultAlert: {
    mb: spacing.sectionGap
  },

  // Upload result message
  resultMessage: (hasDetails: boolean) => ({
    mb: hasDetails ? spacing.md : 0
  }),

  // Result chips container
  chipContainer: {
    display: 'flex',
    gap: spacing.md,
    flexWrap: 'wrap'
  },

  // Instructions section
  instructionsTitle: {
    mb: spacing.sectionGap
  },

  // Instruction text
  instructionText: {
    mb: spacing.sectionGap
  },

  // Instruction details text
  instructionDetails: {
    mb: spacing.sectionGap,
    ml: spacing.sectionGap
  },

  // Final instruction text
  finalInstructionText: {
    ml: spacing.sectionGap
  }
} as const;

// Type for TypeScript intellisense
export type CsvUploadStylesType = typeof csvUploadStyles;