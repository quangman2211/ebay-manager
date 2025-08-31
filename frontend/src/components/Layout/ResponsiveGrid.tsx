/**
 * Responsive Grid Component - SOLID S: Single Responsibility (grid layout only)
 * Progressive enhancement with CSS Grid fallbacks for better browser compatibility
 */

import React from 'react';
import { Box } from '@mui/material';
import { dashboardStyles } from '../../styles/pages/dashboardStyles';

interface ResponsiveGridProps {
  children: React.ReactNode;
  useNativeGrid?: boolean;
}

const ResponsiveGrid: React.FC<ResponsiveGridProps> = ({ 
  children, 
  useNativeGrid = false 
}) => {
  // Feature detection for CSS Grid support
  const supportsGrid = typeof window !== 'undefined' && 
    CSS.supports('display', 'grid');

  // Use CSS Grid for modern browsers, fallback to Material-UI Grid for older ones
  if (useNativeGrid && supportsGrid) {
    return (
      <Box 
        sx={{
          ...dashboardStyles.cssGridContainer,
          // Container queries for progressive enhancement
          '@supports (container-type: inline-size)': {
            containerType: 'inline-size',
            ...dashboardStyles.containerQueries
          }
        }}
      >
        {children}
      </Box>
    );
  }

  // Fallback: Use Material-UI Grid system
  return (
    <Box>
      {children}
    </Box>
  );
};

export default ResponsiveGrid;