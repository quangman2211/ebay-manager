import React from 'react';
import { Box, useTheme, useMediaQuery } from '@mui/material';
import ModernSidebar from './ModernSidebar';
import HeaderWithSearch from './HeaderWithSearch';
import { useSidebarState } from '../../hooks/useSidebarState';
import { layoutStyles } from '../../styles';

interface LayoutProps {
  children: React.ReactNode;
}

const drawerWidth = 260;
const collapsedWidth = 64;

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  
  const {
    isExpanded,
    isMobileOpen,
    toggleSidebar,
    toggleMobileSidebar,
    closeMobileSidebar,
  } = useSidebarState();
  
  const currentDrawerWidth = isMobile ? 0 : (isExpanded ? drawerWidth : collapsedWidth);

  return (
    <Box sx={layoutStyles.container}>
      {/* Modern Sidebar - no overflow */}
      <ModernSidebar
        drawerWidth={drawerWidth}
        collapsedWidth={collapsedWidth}
        mobileOpen={isMobileOpen}
        isExpanded={isExpanded}
        onDrawerToggle={closeMobileSidebar}
      />

      {/* Main content area - single scroll container */}
      <Box
        component="main"
        sx={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          width: { xs: '100%', md: `calc(100% - ${currentDrawerWidth}px)` },
          ml: { xs: 0, md: `${currentDrawerWidth}px` },
          overflow: 'hidden',
          transition: theme.transitions.create(['margin', 'width'], {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.enteringScreen,
          }),
        }}
      >
        {/* Header with Search - fixed */}
        <HeaderWithSearch 
          drawerWidth={currentDrawerWidth}
          isExpanded={isExpanded}
          onToggleSidebar={toggleSidebar}
          onToggleMobileSidebar={toggleMobileSidebar}
          isMobile={isMobile}
        />

        {/* Page content - scrollable area */}
        <Box sx={layoutStyles.pageContent}>
          {children}
        </Box>
      </Box>
    </Box>
  );
};

export default Layout;