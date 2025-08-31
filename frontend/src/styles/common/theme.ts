/**
 * Theme constants - SOLID D: Depend on abstractions, not concretions
 * Material-UI theme configuration abstraction
 */

import { colors } from './colors';

export const themeConfig = {
  palette: {
    primary: {
      main: colors.primary[600], // '#2563eb' instead of hardcoded '#1976d2'
    },
    secondary: {
      main: colors.error, // '#d32f2f' instead of hardcoded '#dc004e'
    },
  },
  
  // Breakpoints
  breakpoints: {
    xs: 0,
    sm: 600,
    md: 960,
    lg: 1280,
    xl: 1920,
  },

  // Typography
  typography: {
    fontFamily: [
      '-apple-system',
      'BlinkMacSystemFont',
      '"Segoe UI"',
      'Roboto',
      '"Helvetica Neue"',
      'Arial',
      'sans-serif',
    ].join(','),
  },

  // Shadows
  shadows: {
    header: '0 1px 3px 0 rgb(0 0 0 / 0.1)',
    dropdown: '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 10px 10px -5px rgb(0 0 0 / 0.04)',
    focus: '0 0 0 3px',
  },

  // Z-index values
  zIndex: {
    modal: 1300,
    drawer: 1200,
    appBar: 1100,
  },

  // Transitions
  transitions: {
    duration: {
      shortest: 150,
      shorter: 200,
      short: 250,
      standard: 300,
      complex: 375,
      enteringScreen: 225,
      leavingScreen: 195,
    },
    easing: {
      easeInOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
      easeOut: 'cubic-bezier(0.0, 0, 0.2, 1)',
      easeIn: 'cubic-bezier(0.4, 0, 1, 1)',
      sharp: 'cubic-bezier(0.4, 0, 0.6, 1)',
    },
  },
} as const;

// Type for TypeScript intellisense
export type ThemeConfigType = typeof themeConfig;