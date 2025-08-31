import React, { useState, useCallback } from 'react';
import {
  AppBar,
  Toolbar,
  InputBase,
  IconButton,
  Box,
  Typography,
  Avatar,
  Menu,
  MenuItem,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Chip,
  useTheme,
  alpha,
} from '@mui/material';
import {
  Search as SearchIcon,
  AccountCircle,
  Logout as LogoutIcon,
  ShoppingCart,
  Inventory,
  Receipt,
  Close as CloseIcon,
  Menu as MenuIcon,
} from '@mui/icons-material';
import { useAuth } from '../../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { searchAPI } from '../../services/api';
import { colors, spacing } from '../../styles';

interface SearchResult {
  type: 'order' | 'listing' | 'item';
  id: string;
  title: string;
  subtitle?: string;
  status?: string;
}

interface HeaderWithSearchProps {
  drawerWidth: number;
  isExpanded: boolean;
  onToggleSidebar: () => void;
  onToggleMobileSidebar: () => void;
  isMobile: boolean;
}

const HeaderWithSearch: React.FC<HeaderWithSearchProps> = ({ 
  drawerWidth, 
  isExpanded, 
  onToggleSidebar, 
  onToggleMobileSidebar, 
  isMobile 
}) => {
  const theme = useTheme();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showResults, setShowResults] = useState(false);

  const handleProfileMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = () => {
    handleMenuClose();
    logout();
    navigate('/login');
  };

  const performSearch = useCallback(async (query: string) => {
    if (query.trim().length < 2) {
      setSearchResults([]);
      setShowResults(false);
      return;
    }

    setIsSearching(true);
    try {
      const results = await searchAPI.globalSearch(query);
      setSearchResults(results);
      setShowResults(true);
    } catch (error) {
      console.error('Search failed:', error);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  }, []);

  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const query = event.target.value;
    setSearchQuery(query);
    
    // Debounce search
    const timeoutId = setTimeout(() => {
      performSearch(query);
    }, 300);
    
    return () => clearTimeout(timeoutId);
  };

  const handleResultClick = (result: SearchResult) => {
    setShowResults(false);
    setSearchQuery('');
    
    switch (result.type) {
      case 'order':
        navigate(`/orders?search=${result.id}`);
        break;
      case 'listing':
        navigate(`/listings?search=${result.id}`);
        break;
      case 'item':
        navigate(`/listings?search=${result.id}`);
        break;
    }
  };

  const getResultIcon = (type: string) => {
    switch (type) {
      case 'order':
        return <Receipt fontSize="small" />;
      case 'listing':
        return <Inventory fontSize="small" />;
      case 'item':
        return <ShoppingCart fontSize="small" />;
      default:
        return null;
    }
  };

  const getStatusColor = (status?: string) => {
    if (!status) return 'default';
    switch (status.toLowerCase()) {
      case 'completed':
      case 'delivered':
      case 'active':
        return 'success';
      case 'processing':
      case 'shipped':
        return 'info';
      case 'pending':
        return 'warning';
      case 'cancelled':
      case 'returned':
      case 'inactive':
        return 'error';
      default:
        return 'default';
    }
  };

  return (
    <AppBar
      position="fixed"
      sx={{
        width: isMobile ? '100%' : `calc(100% - ${drawerWidth}px)`,
        ml: isMobile ? 0 : `${drawerWidth}px`,
        backgroundColor: colors.bgPrimary,
        color: colors.textPrimary,
        boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.1)',
        transition: theme.transitions.create(['margin', 'width'], {
          easing: theme.transitions.easing.sharp,
          duration: theme.transitions.duration.leavingScreen,
        }),
      }}
    >
      <Toolbar sx={{ justifyContent: 'space-between', px: spacing.xl }}>
        {/* Hamburger Menu */}
        <IconButton
          color="inherit"
          aria-label={isMobile ? "open drawer" : (isExpanded ? "collapse sidebar" : "expand sidebar")}
          onClick={isMobile ? onToggleMobileSidebar : onToggleSidebar}
          edge="start"
          sx={{
            mr: spacing.lg,
            display: 'flex',
            '&:hover': {
              backgroundColor: alpha(colors.primary[500], 0.08),
            },
            transition: theme.transitions.create('background-color'),
          }}
        >
          <MenuIcon />
        </IconButton>
        
        {/* Search Bar */}
        <Box sx={{ position: 'relative', flexGrow: 1, maxWidth: '100%', mr: spacing.xl }}>
          <Box
            sx={{
              position: 'relative',
              borderRadius: spacing.xl,
              backgroundColor: colors.bgSearch,
              border: `1px solid ${colors.borderSearch}`,
              '&:hover': {
                backgroundColor: colors.bgHover,
                borderColor: alpha(colors.primary[500], 0.3),
              },
              '&:focus-within': {
                backgroundColor: colors.bgPrimary,
                borderColor: colors.primary[500],
                boxShadow: `0 0 0 3px ${alpha(colors.primary[500], 0.1)}`,
              },
              width: '100%',
              minHeight: 48,
            }}
          >
            <Box
              sx={{
                padding: theme.spacing(0, spacing.lg),
                height: '100%',
                position: 'absolute',
                pointerEvents: 'none',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <SearchIcon sx={{ color: colors.textSecondary }} />
            </Box>
            <InputBase
              placeholder="Search orders, items, or listings..."
              inputProps={{ 'aria-label': 'search' }}
              value={searchQuery}
              onChange={handleSearchChange}
              sx={{
                color: 'inherit',
                width: '100%',
                fontSize: '16px',
                '& .MuiInputBase-input': {
                  padding: theme.spacing(spacing.searchPadding, spacing.md, spacing.searchPadding, 0),
                  paddingLeft: `calc(1em + ${theme.spacing(spacing.xxl)})`,
                  paddingRight: searchQuery ? theme.spacing(spacing.xl + spacing.lg) : theme.spacing(spacing.md),
                  transition: theme.transitions.create(['width', 'padding']),
                  width: '100%',
                  fontSize: '16px',
                  '&::placeholder': {
                    color: colors.textPlaceholder,
                    fontSize: '16px',
                  },
                },
              }}
            />
            {searchQuery && (
              <IconButton
                size="small"
                sx={{
                  position: 'absolute',
                  right: theme.spacing(spacing.searchGap),
                  top: '50%',
                  transform: 'translateY(-50%)',
                }}
                onClick={() => {
                  setSearchQuery('');
                  setSearchResults([]);
                  setShowResults(false);
                }}
              >
                <CloseIcon fontSize="small" />
              </IconButton>
            )}
          </Box>

          {/* Search Results Dropdown */}
          {showResults && (
            <Paper
              sx={{
                position: 'absolute',
                top: '100%',
                left: 0,
                right: 0,
                mt: spacing.md,
                maxHeight: 500,
                overflow: 'auto',
                zIndex: theme.zIndex.modal,
                boxShadow: '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 10px 10px -5px rgb(0 0 0 / 0.04)',
                borderRadius: spacing.xl,
                border: `1px solid ${colors.borderLight}`,
              }}
            >
              {isSearching ? (
                <Box sx={{ p: spacing.lg, textAlign: 'center' }}>
                  <Typography variant="body2" color="text.secondary">
                    Searching...
                  </Typography>
                </Box>
              ) : searchResults.length > 0 ? (
                <List>
                  {searchResults.map((result, index) => (
                    <React.Fragment key={`${result.type}-${result.id}`}>
                      {index > 0 && <Divider />}
                      <ListItem
                        button
                        onClick={() => handleResultClick(result)}
                        sx={{
                          py: spacing.searchPadding,
                          px: spacing.lg,
                          '&:hover': {
                            backgroundColor: colors.bgHover,
                          },
                          transition: theme.transitions.create('background-color'),
                        }}
                      >
                        <ListItemIcon>{getResultIcon(result.type)}</ListItemIcon>
                        <ListItemText
                          primary={result.title}
                          secondary={result.subtitle}
                        />
                        <Box sx={{ display: 'flex', gap: spacing.md }}>
                          <Chip
                            label={result.type.toUpperCase()}
                            size="small"
                            variant="outlined"
                          />
                          {result.status && (
                            <Chip
                              label={result.status}
                              size="small"
                              color={getStatusColor(result.status) as any}
                            />
                          )}
                        </Box>
                      </ListItem>
                    </React.Fragment>
                  ))}
                </List>
              ) : (
                <Box sx={{ p: spacing.lg, textAlign: 'center' }}>
                  <Typography variant="body2" color="text.secondary">
                    No results found for "{searchQuery}"
                  </Typography>
                </Box>
              )}
            </Paper>
          )}
        </Box>

        {/* User Menu */}
        <Box sx={{ display: 'flex', alignItems: 'center', minWidth: 'max-content' }}>
          <Typography 
            variant="body2" 
            sx={{ 
              mr: spacing.lg, 
              display: { xs: 'none', md: 'block' },
              fontWeight: 500,
              color: colors.textSecondary,
            }}
          >
            {user?.username}
          </Typography>
          <IconButton
            edge="end"
            onClick={handleProfileMenuOpen}
            color="inherit"
            sx={{
              p: spacing.sm,
              '&:hover': {
                backgroundColor: alpha(colors.primary[500], 0.08),
              },
            }}
          >
            <Avatar sx={{ 
              width: 36, 
              height: 36, 
              bgcolor: colors.primary[500],
              fontSize: '16px',
              fontWeight: 600,
            }}>
              {user?.username?.charAt(0).toUpperCase()}
            </Avatar>
          </IconButton>
          <Menu
            anchorEl={anchorEl}
            open={Boolean(anchorEl)}
            onClose={handleMenuClose}
            transformOrigin={{ horizontal: 'right', vertical: 'top' }}
            anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
          >
            <MenuItem onClick={handleMenuClose}>
              <AccountCircle sx={{ mr: spacing.md }} />
              Profile
            </MenuItem>
            <Divider />
            <MenuItem onClick={handleLogout}>
              <LogoutIcon sx={{ mr: spacing.md }} />
              Logout
            </MenuItem>
          </Menu>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default HeaderWithSearch;