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
    <Box sx={{ display: 'flex', minHeight: '100vh', backgroundColor: '#f8fafc' }}>
      {/* Modern Sidebar */}
      <ModernSidebar
        drawerWidth={drawerWidth}
        mobileOpen={mobileOpen}
        onDrawerToggle={handleDrawerToggle}
      />

      {/* Main content area */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          width: { xs: '100%', sm: `calc(100% - ${drawerWidth}px)` },
          ml: { xs: 0, sm: `${drawerWidth}px` },
        }}
      >
        {/* Header with Search */}
        <HeaderWithSearch drawerWidth={isMobile ? 0 : drawerWidth} />

        {/* Page content */}
        <Box sx={{ p: 3, mt: 8 }}>
          {children}
        </Box>
      </Box>
    </Box>
  );
};

export default Layout;