import React, { useEffect } from 'react';
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
import { sidebarStyles } from '../../styles';

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
  const styles = sidebarStyles;

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
      ...styles.container,
      transition: theme.transitions.create('width', {
        easing: theme.transitions.easing.sharp,
        duration: theme.transitions.duration.enteringScreen,
      }),
    }}>
      {/* Logo Section */}
      <Box sx={isExpanded ? styles.logoSection.expanded : styles.logoSection.collapsed}>
        {isExpanded ? (
          <Typography variant="h6" sx={{
            ...styles.logoText.expanded,
            transition: theme.transitions.create('opacity', {
              delay: theme.transitions.duration.shorter,
            }),
          }}>
            eBay Manager
          </Typography>
        ) : (
          <Box sx={styles.logoIcon}>
            EB
          </Box>
        )}
      </Box>

      {/* Navigation */}
      <Box sx={isExpanded ? styles.navigation.expanded : styles.navigation.collapsed}>
        <List sx={{ gap: 0.5 }}>
          {menuItems.map((item) => {
            const menuItem = (
              <ListItem
                key={item.text}
                onClick={() => {
                  navigate(item.path);
                  // Auto-close mobile drawer when navigation item is clicked
                  if (mobileOpen) {
                    onDrawerToggle();
                  }
                }}
                sx={{
                  ...styles.menuItem.base,
                  ...(isExpanded ? styles.menuItem.expanded : styles.menuItem.collapsed),
                  ...(isActive(item.path) ? styles.menuItem.active : styles.menuItem.inactive),
                  '&:hover': {
                    backgroundColor: isActive(item.path) ? styles.menuItem.hover.active : styles.menuItem.hover.inactive,
                  },
                  transition: theme.transitions.create(['background-color', 'padding'], {
                    duration: theme.transitions.duration.shorter,
                  }),
                }}
              >
                <ListItemIcon sx={isExpanded ? styles.menuIcon.expanded : styles.menuIcon.collapsed}>
                  {item.icon}
                </ListItemIcon>
                {isExpanded && (
                  <ListItemText
                    primary={item.text}
                    sx={{
                      ...styles.menuText,
                      '& .MuiTypography-root': {
                        ...styles.menuText['& .MuiTypography-root'],
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
      <Box sx={isExpanded ? styles.profileSection.expanded : styles.profileSection.collapsed}>
        <Box sx={isExpanded ? styles.profileContainer.expanded : styles.profileContainer.collapsed}>
          <Avatar sx={styles.avatar}>
            A
          </Avatar>
          {isExpanded && (
            <Box>
              <Typography variant="body2" sx={{
                ...styles.profileText.username,
                transition: theme.transitions.create('opacity', {
                  delay: theme.transitions.duration.shorter,
                }),
              }}>
                Admin User
              </Typography>
              <Typography variant="caption" sx={{
                ...styles.profileText.role,
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
              ...styles.profileChip,
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
        }}
        sx={{
          ...styles.drawer.mobile,
          '& .MuiDrawer-paper': { 
            ...styles.drawer.mobile['& .MuiDrawer-paper'],
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
        }}
      >
        {drawerContent}
      </Drawer>
      
      {/* Desktop drawer */}
      <Drawer
        variant="permanent"
        sx={{
          ...styles.drawer.desktop,
          '& .MuiDrawer-paper': { 
            ...styles.drawer.desktop['& .MuiDrawer-paper'],
            width: currentWidth,
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