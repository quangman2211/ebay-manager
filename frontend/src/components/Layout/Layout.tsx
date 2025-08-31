import React, { useState } from 'react';
import { Box, useTheme, useMediaQuery } from '@mui/material';
import ModernSidebar from './ModernSidebar';
import HeaderWithSearch from './HeaderWithSearch';

interface LayoutProps {
  children: React.ReactNode;
}

const drawerWidth = 260;

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [mobileOpen, setMobileOpen] = useState(false);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  return (
    <Box sx={{ 
      display: 'flex', 
      height: '100%', 
      backgroundColor: '#f8fafc',
      overflow: 'hidden'
    }}>
      {/* Modern Sidebar - no overflow */}
      <ModernSidebar
        drawerWidth={drawerWidth}
        mobileOpen={mobileOpen}
        onDrawerToggle={handleDrawerToggle}
      />

      {/* Main content area - single scroll container */}
      <Box
        component="main"
        sx={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          width: { xs: '100%', sm: `calc(100% - ${drawerWidth}px)` },
          ml: { xs: 0, sm: `${drawerWidth}px` },
          overflow: 'hidden'
        }}
      >
        {/* Header with Search - fixed */}
        <HeaderWithSearch drawerWidth={isMobile ? 0 : drawerWidth} />

        {/* Page content - scrollable area */}
        <Box sx={{ 
          flex: 1,
          overflowY: 'auto',
          overflowX: 'hidden',
          p: 3, 
          mt: 8 
        }}>
          {children}
        </Box>
      </Box>
    </Box>
  );
};

export default Layout;