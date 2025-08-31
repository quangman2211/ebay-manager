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
  Divider
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
  mobileOpen: boolean;
  onDrawerToggle: () => void;
}

const ModernSidebar: React.FC<ModernSidebarProps> = ({
  drawerWidth,
  mobileOpen,
  onDrawerToggle,
}) => {
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    { text: 'Dashboard', icon: <DashboardIcon />, path: '/' },
    { text: 'Orders', icon: <ReceiptIcon />, path: '/orders' },
    { text: 'Listings', icon: <InventoryIcon />, path: '/listings' },
    { text: 'CSV Upload', icon: <UploadFileIcon />, path: '/upload' },
    { text: 'Settings', icon: <SettingsIcon />, path: '/settings' },
  ];

  const isActive = (path: string) => location.pathname === path;

  const drawerContent = (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', background: '#f8fafc' }}>
      {/* Logo Section */}
      <Box sx={{ p: 3, borderBottom: '1px solid #e2e8f0' }}>
        <Typography variant="h6" sx={{ fontWeight: 600, color: '#1e293b', letterSpacing: '-0.025em' }}>
          eBay Manager
        </Typography>
      </Box>

      {/* Navigation */}
      <Box sx={{ flex: 1, px: 1.5, py: 2 }}>
        <List sx={{ gap: 0.5 }}>
          {menuItems.map((item) => (
            <ListItem
              key={item.text}
              onClick={() => navigate(item.path)}
              sx={{
                borderRadius: 1,
                cursor: 'pointer',
                mb: 0.5,
                px: 1.5,
                py: 1.25,
                backgroundColor: isActive(item.path) ? '#3b82f6' : 'transparent',
                color: isActive(item.path) ? 'white' : '#475569',
                '&:hover': {
                  backgroundColor: isActive(item.path) ? '#3b82f6' : '#e2e8f0',
                },
                transition: 'all 0.2s ease-in-out',
              }}
            >
              <ListItemIcon
                sx={{
                  color: 'inherit',
                  minWidth: 32,
                  '& .MuiSvgIcon-root': { fontSize: 20 },
                }}
              >
                {item.icon}
              </ListItemIcon>
              <ListItemText
                primary={item.text}
                sx={{
                  '& .MuiTypography-root': {
                    fontSize: '0.875rem',
                    fontWeight: 500,
                  },
                }}
              />
            </ListItem>
          ))}
        </List>
      </Box>

      {/* User Profile Section */}
      <Box sx={{ 
        p: 2.5, 
        borderTop: '1px solid #e2e8f0', 
        backgroundColor: '#ffffff',
      }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 1.5 }}>
          <Avatar sx={{ 
            width: 36, 
            height: 36, 
            backgroundColor: '#3b82f6',
            fontSize: '0.875rem',
            fontWeight: 600,
          }}>
            A
          </Avatar>
          <Box>
            <Typography variant="body2" sx={{ fontWeight: 600, color: '#1e293b', fontSize: '0.875rem' }}>
              Admin User
            </Typography>
            <Typography variant="caption" sx={{ color: '#64748b', fontSize: '0.75rem' }}>
              Administrator
            </Typography>
          </Box>
        </Box>
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
          }}
        />
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
        ModalProps={{ keepMounted: true }}
        sx={{
          display: { xs: 'block', sm: 'none' },
          '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
        }}
      >
        {drawerContent}
      </Drawer>
      
      {/* Desktop drawer */}
      <Drawer
        variant="permanent"
        sx={{
          display: { xs: 'none', sm: 'block' },
          '& .MuiDrawer-paper': { 
            boxSizing: 'border-box', 
            width: drawerWidth,
            border: 'none',
            borderRight: '1px solid #e2e8f0',
          },
        }}
        open
      >
        {drawerContent}
      </Drawer>
    </>
  );
};

export default ModernSidebar;