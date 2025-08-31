/**
 * Spacing constants - SOLID D: Depend on abstractions, not concretions  
 * Standardized spacing values following Material-UI 8px grid system
 */

export const spacing = {
  // Base spacing (8px increments)
  xs: 0.25,  // 2px
  sm: 0.5,   // 4px
  md: 1,     // 8px
  lg: 2,     // 16px
  xl: 3,     // 24px
  xxl: 4,    // 32px
  xxxl: 8,   // 64px
  
  // Semantic spacing
  containerGap: 3,        // 24px - main container spacing
  sectionGap: 2,          // 16px - between sections
  componentGap: 1,        // 8px - between related components
  elementGap: 0.5,        // 4px - between small elements
  textGap: 0.25,          // 2px - between text lines
  
  // Layout specific
  headerPadding: 4,       // 32px - header/card padding
  contentPadding: 2,      // 16px - content padding
  formGap: 2,             // 16px - form field spacing
  buttonSpacing: 3,       // 24px - button top margin
  
  // Search specific spacing
  searchPadding: 1.5,     // 12px - search input padding
  searchGap: 1,           // 8px - gap between search elements
  searchResults: 1,       // 8px - search results padding
  
  // DataGrid specific
  rowHeight: 120,         // Current row height
  cellPadding: 1,         // 8px - cell padding
  
  // Special cases
  loginTopMargin: 8,      // 64px - login form top margin
  dropzonePadding: 4      // 32px - dropzone padding
} as const;

// Type for TypeScript intellisense
export type SpacingType = typeof spacing;