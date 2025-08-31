import React from 'react';
import { 
  Drawer, 
  List, 
  ListItem, 
  ListItemIcon, 
  ListItemText, 
  Typography, 
  Box,
  Avatar,
  Chip,
  Divider,
  useTheme,
  Tooltip
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Receipt as ReceiptIcon,
  Inventory as InventoryIcon,
  UploadFile as UploadFileIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';

interface ModernSidebarProps {
  drawerWidth: number;
  collapsedWidth: number;
  mobileOpen: boolean;
  isExpanded: boolean;
  onDrawerToggle: () => void;
}

const ModernSidebar: React.FC<ModernSidebarProps> = ({
  drawerWidth,
  collapsedWidth,
  mobileOpen,
  isExpanded,
  onDrawerToggle,
}) => {
  const navigate = useNavigate();
  const location = useLocation();
  const theme = useTheme();
  
  const currentWidth = isExpanded ? drawerWidth : collapsedWidth;

  const menuItems = [
    { text: 'Dashboard', icon: <DashboardIcon />, path: '/' },
    { text: 'Orders', icon: <ReceiptIcon />, path: '/orders' },
    { text: 'Listings', icon: <InventoryIcon />, path: '/listings' },
    { text: 'CSV Upload', icon: <UploadFileIcon />, path: '/upload' },
    { text: 'Settings', icon: <SettingsIcon />, path: '/settings' },
  ];

  const isActive = (path: string) => location.pathname === path;

  const drawerContent = (
    <Box sx={{ 
      height: '100%', 
      display: 'flex', 
      flexDirection: 'column', 
      background: '#f8fafc',
      transition: theme.transitions.create('width', {
        easing: theme.transitions.easing.sharp,
        duration: theme.transitions.duration.enteringScreen,
      }),
    }}>
      {/* Logo Section */}
      <Box sx={{ 
        p: isExpanded ? 3 : 1.5, 
        borderBottom: '1px solid #e2e8f0',
        display: 'flex',
        alignItems: 'center',
        justifyContent: isExpanded ? 'flex-start' : 'center',
        minHeight: 64,
      }}>
        {isExpanded ? (
          <Typography variant="h6" sx={{ 
            fontWeight: 600, 
            color: '#1e293b', 
            letterSpacing: '-0.025em',
            opacity: 1,
            transition: theme.transitions.create('opacity', {
              delay: theme.transitions.duration.shorter,
            }),
          }}>
            eBay Manager
          </Typography>
        ) : (
          <Box sx={{ 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center',
            width: 40,
            height: 40,
            borderRadius: 1,
            backgroundColor: '#3b82f6',
            color: 'white',
            fontSize: '1rem',
            fontWeight: 700,
          }}>
            EB
          </Box>
        )}
      </Box>

      {/* Navigation */}
      <Box sx={{ flex: 1, px: isExpanded ? 1.5 : 0.5, py: 2 }}>
        <List sx={{ gap: 0.5 }}>
          {menuItems.map((item) => {
            const menuItem = (
              <ListItem
                key={item.text}
                onClick={() => navigate(item.path)}
                sx={{
                  borderRadius: 1,
                  cursor: 'pointer',
                  mb: 0.5,
                  px: isExpanded ? 1.5 : 1,
                  py: 1.25,
                  backgroundColor: isActive(item.path) ? '#3b82f6' : 'transparent',
                  color: isActive(item.path) ? 'white' : '#475569',
                  '&:hover': {
                    backgroundColor: isActive(item.path) ? '#3b82f6' : '#e2e8f0',
                  },
                  transition: theme.transitions.create(['background-color', 'padding'], {
                    duration: theme.transitions.duration.shorter,
                  }),
                  justifyContent: isExpanded ? 'flex-start' : 'center',
                  minHeight: 48,
                }}
              >
                <ListItemIcon
                  sx={{
                    color: 'inherit',
                    minWidth: isExpanded ? 32 : 'auto',
                    mr: isExpanded ? 2 : 0,
                    justifyContent: 'center',
                    '& .MuiSvgIcon-root': { fontSize: 20 },
                  }}
                >
                  {item.icon}
                </ListItemIcon>
                {isExpanded && (
                  <ListItemText
                    primary={item.text}
                    sx={{
                      '& .MuiTypography-root': {
                        fontSize: '0.875rem',
                        fontWeight: 500,
                        opacity: 1,
                        transition: theme.transitions.create('opacity', {
                          delay: theme.transitions.duration.shorter,
                        }),
                      },
                    }}
                  />
                )}
              </ListItem>
            );

            return isExpanded ? menuItem : (
              <Tooltip key={item.text} title={item.text} placement="right">
                {menuItem}
              </Tooltip>
            );
          })}
        </List>
      </Box>

      {/* User Profile Section */}
      <Box sx={{ 
        p: isExpanded ? 2.5 : 1, 
        borderTop: '1px solid #e2e8f0', 
        backgroundColor: '#ffffff',
        display: 'flex',
        flexDirection: 'column',
        alignItems: isExpanded ? 'flex-start' : 'center',
      }}>
        <Box sx={{ 
          display: 'flex', 
          alignItems: 'center', 
          gap: isExpanded ? 1.5 : 0, 
          mb: isExpanded ? 1.5 : 1,
          justifyContent: 'center',
        }}>
          <Avatar sx={{ 
            width: 36, 
            height: 36, 
            backgroundColor: '#3b82f6',
            fontSize: '0.875rem',
            fontWeight: 600,
          }}>
            A
          </Avatar>
          {isExpanded && (
            <Box>
              <Typography variant="body2" sx={{ 
                fontWeight: 600, 
                color: '#1e293b', 
                fontSize: '0.875rem',
                opacity: 1,
                transition: theme.transitions.create('opacity', {
                  delay: theme.transitions.duration.shorter,
                }),
              }}>
                Admin User
              </Typography>
              <Typography variant="caption" sx={{ 
                color: '#64748b', 
                fontSize: '0.75rem',
                opacity: 1,
                transition: theme.transitions.create('opacity', {
                  delay: theme.transitions.duration.shorter,
                }),
              }}>
                Administrator
              </Typography>
            </Box>
          )}
        </Box>
        {isExpanded && (
          <Chip
            label="30 accounts"
            size="small"
            sx={{
              backgroundColor: '#f1f5f9',
              color: '#475569',
              border: '1px solid #e2e8f0',
              fontSize: '0.6875rem',
              fontWeight: 500,
              height: '24px',
              opacity: 1,
              transition: theme.transitions.create('opacity', {
                delay: theme.transitions.duration.shorter,
              }),
            }}
          />
        )}
      </Box>
    </Box>
  );

  return (
    <>
      {/* Mobile drawer */}
      <Drawer
        variant="temporary"
        open={mobileOpen}
        onClose={onDrawerToggle}
        ModalProps={{ 
          keepMounted: true,
          'aria-labelledby': 'mobile-navigation-drawer',
        }}
        sx={{
          display: { xs: 'block', md: 'none' },
          '& .MuiDrawer-paper': { 
            boxSizing: 'border-box', 
            width: drawerWidth,
            transition: theme.transitions.create('width', {
              easing: theme.transitions.easing.sharp,
              duration: theme.transitions.duration.enteringScreen,
            }),
          },
        }}
        PaperProps={{
          'aria-label': 'Mobile navigation sidebar',
          role: 'navigation',
          id: 'mobile-navigation-drawer',
        }}
      >
        {drawerContent}
      </Drawer>
      
      {/* Desktop drawer */}
      <Drawer
        variant="permanent"
        sx={{
          display: { xs: 'none', md: 'block' },
          '& .MuiDrawer-paper': { 
            boxSizing: 'border-box', 
            width: currentWidth,
            border: 'none',
            borderRight: '1px solid #e2e8f0',
            overflowX: 'hidden',
            transition: theme.transitions.create('width', {
              easing: theme.transitions.easing.sharp,
              duration: theme.transitions.duration.enteringScreen,
            }),
          },
        }}
        open
        PaperProps={{
          'aria-label': isExpanded ? 'Expanded navigation sidebar' : 'Collapsed navigation sidebar',
          role: 'navigation',
        }}
      >
        {drawerContent}
      </Drawer>
    </>
  );
};

export default ModernSidebar;