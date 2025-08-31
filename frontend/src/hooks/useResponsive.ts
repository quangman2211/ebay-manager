/**
 * useResponsive Hook - SOLID S: Single Responsibility (responsive detection only)
 * Custom hook for responsive breakpoint detection and optimization
 */

import { useState, useEffect } from 'react';
import { useTheme } from '@mui/material/styles';
import useMediaQuery from '@mui/material/useMediaQuery';

interface ResponsiveState {
  isMini: boolean;
  isMobile: boolean;
  isTablet: boolean;
  isDesktop: boolean;
  isLargeScreen: boolean;
  screenWidth: number;
  breakpoint: 'mini' | 'xs' | 'sm' | 'md' | 'lg' | 'xl';
}

export const useResponsive = (): ResponsiveState => {
  const theme = useTheme();
  const [screenWidth, setScreenWidth] = useState(
    typeof window !== 'undefined' ? window.innerWidth : 1024
  );

  // Enhanced breakpoint queries including mini mode
  const isMini = useMediaQuery('(max-width: 375px)') || screenWidth <= 375;
  const isMobile = useMediaQuery(theme.breakpoints.down('sm')) && screenWidth > 375;
  const isTablet = useMediaQuery(theme.breakpoints.between('sm', 'md'));
  const isDesktop = useMediaQuery(theme.breakpoints.between('md', 'lg'));
  const isLargeScreen = useMediaQuery(theme.breakpoints.up('lg'));

  // Determine current breakpoint including mini mode
  const getBreakpoint = (): 'mini' | 'xs' | 'sm' | 'md' | 'lg' | 'xl' => {
    if (screenWidth <= 375) return 'mini';  // Mini browser mode
    if (screenWidth < 600) return 'xs';     // Extra small
    if (screenWidth < 900) return 'sm';     // Small
    if (screenWidth < 1200) return 'md';    // Medium
    if (screenWidth < 1536) return 'lg';    // Large
    return 'xl';                            // Extra large
  };

  useEffect(() => {
    const handleResize = () => {
      setScreenWidth(window.innerWidth);
    };

    // Throttle resize events for performance
    let timeoutId: NodeJS.Timeout;
    const throttledResize = () => {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(handleResize, 16); // ~60fps
    };

    if (typeof window !== 'undefined') {
      window.addEventListener('resize', throttledResize);
      return () => {
        window.removeEventListener('resize', throttledResize);
        clearTimeout(timeoutId);
      };
    }
  }, []);

  return {
    isMini,
    isMobile,
    isTablet,
    isDesktop,
    isLargeScreen,
    screenWidth,
    breakpoint: getBreakpoint()
  };
};