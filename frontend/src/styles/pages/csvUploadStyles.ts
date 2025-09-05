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

  // Upload dropzone area - Enhanced visual feedback for better UX
  dropzoneArea: (selectedAccount: boolean, uploading: boolean, isDragActive: boolean) => ({
    border: `2px dashed ${isDragActive ? colors.primary[500] : colors.primary[300]}`,
    borderRadius: spacing.sectionGap,
    p: spacing.dropzonePadding,
    textAlign: 'center' as const,
    cursor: uploading ? 'not-allowed' : 'pointer',
    backgroundColor: isDragActive ? colors.primary[50] : 'transparent',
    opacity: uploading ? 0.5 : 1,
    transition: 'all 0.3s ease',
    '&:hover': {
      backgroundColor: !uploading ? colors.primary[50] : 'transparent',
      borderColor: !uploading ? colors.primary[400] : colors.primary[300],
      transform: !uploading ? 'translateY(-1px)' : 'none',
      boxShadow: !uploading ? `0 4px 12px ${colors.primary[100]}` : 'none'
    },
    '&:active': {
      transform: !uploading ? 'translateY(0px)' : 'none',
      boxShadow: !uploading ? `0 2px 8px ${colors.primary[200]}` : 'none'
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

  // Cloud upload icon with enhanced visual feedback
  cloudIcon: {
    fontSize: 48,
    color: colors.primary[400],
    mb: spacing.sectionGap,
    transition: 'all 0.3s ease',
    '&:hover': {
      color: colors.primary[500],
      transform: 'scale(1.05)'
    }
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
  },

  // Enhanced upload progress styles
  progressContainer: {
    mb: spacing.containerGap
  },

  errorRecoveryContainer: {
    mb: spacing.containerGap
  },

  progressBarCard: {
    border: '2px solid',
    borderColor: 'primary.main',
    mb: spacing.sectionGap
  },

  errorCard: {
    border: '2px solid',
    borderColor: 'error.main',
    mb: spacing.sectionGap
  }
} as const;

// Type for TypeScript intellisense
export type CsvUploadStylesType = typeof csvUploadStyles;