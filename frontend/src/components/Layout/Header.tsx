import React from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
  Chip,
} from '@mui/material';
import { LogoutOutlined, AccountCircle } from '@mui/icons-material';
import { useAuth } from '../../context/AuthContext';

const Header: React.FC = () => {
  const { user, logout } = useAuth();

  return (
    <AppBar position="static" elevation={1}>
      <Toolbar>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          eBay Manager
        </Typography>
        
        {user && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <AccountCircle />
              <Typography variant="body2">
                {user.username}
              </Typography>
              <Chip 
                label={user.role} 
                size="small" 
                color={user.role === 'admin' ? 'secondary' : 'default'}
              />
            </Box>
            
            <Button 
              color="inherit" 
              onClick={logout}
              startIcon={<LogoutOutlined />}
            >
              Logout
            </Button>
          </Box>
        )}
      </Toolbar>
    </AppBar>
  );
};

export default Header;