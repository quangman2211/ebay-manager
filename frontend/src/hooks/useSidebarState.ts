import { useState, useEffect } from 'react';
import { useTheme, useMediaQuery } from '@mui/material';

interface SidebarState {
  isExpanded: boolean;
  isMobileOpen: boolean;
}

interface UseSidebarStateReturn {
  isExpanded: boolean;
  isMobileOpen: boolean;
  toggleSidebar: () => void;
  toggleMobileSidebar: () => void;
  closeMobileSidebar: () => void;
}

const SIDEBAR_STATE_KEY = 'ebay-manager-sidebar-state';

export const useSidebarState = (): UseSidebarStateReturn => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  // Initialize state from localStorage or default values
  const [sidebarState, setSidebarState] = useState<SidebarState>(() => {
    try {
      const savedState = localStorage.getItem(SIDEBAR_STATE_KEY);
      if (savedState) {
        const parsed = JSON.parse(savedState);
        return {
          isExpanded: parsed.isExpanded ?? true, // Default to expanded on desktop
          isMobileOpen: false, // Always start closed on mobile
        };
      }
    } catch (error) {
      console.warn('Failed to load sidebar state from localStorage:', error);
    }
    
    return {
      isExpanded: true, // Default to expanded on desktop
      isMobileOpen: false, // Always start closed on mobile
    };
  });

  // Auto-collapse on mobile, restore desktop state when switching back
  useEffect(() => {
    if (isMobile) {
      // On mobile, close the mobile drawer if it's open
      if (sidebarState.isMobileOpen) {
        setSidebarState(prev => ({ ...prev, isMobileOpen: false }));
      }
    }
  }, [isMobile, sidebarState.isMobileOpen]);

  // Save expanded state to localStorage (only for desktop)
  useEffect(() => {
    if (!isMobile) {
      try {
        localStorage.setItem(SIDEBAR_STATE_KEY, JSON.stringify({
          isExpanded: sidebarState.isExpanded,
        }));
      } catch (error) {
        console.warn('Failed to save sidebar state to localStorage:', error);
      }
    }
  }, [sidebarState.isExpanded, isMobile]);

  const toggleSidebar = () => {
    setSidebarState(prev => ({
      ...prev,
      isExpanded: !prev.isExpanded,
    }));
  };

  const toggleMobileSidebar = () => {
    setSidebarState(prev => ({
      ...prev,
      isMobileOpen: !prev.isMobileOpen,
    }));
  };

  const closeMobileSidebar = () => {
    setSidebarState(prev => ({
      ...prev,
      isMobileOpen: false,
    }));
  };

  // Add keyboard event listener for Esc key
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        if (isMobile && sidebarState.isMobileOpen) {
          closeMobileSidebar();
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isMobile, sidebarState.isMobileOpen]);

  return {
    isExpanded: isMobile ? true : sidebarState.isExpanded, // Always expanded on mobile when open
    isMobileOpen: sidebarState.isMobileOpen,
    toggleSidebar,
    toggleMobileSidebar,
    closeMobileSidebar,
  };
};