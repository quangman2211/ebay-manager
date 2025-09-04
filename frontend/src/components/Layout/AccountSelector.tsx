import React, { useState, useCallback } from 'react';
import {
  Box,
  FormControl,
  Select,
  MenuItem,
  Typography,
  Avatar,
  ListItemIcon,
  ListItemText,
  Divider,
  Chip,
  CircularProgress,
  SelectChangeEvent,
  alpha,
} from '@mui/material';
import {
  AccountCircle as AccountIcon,
  CheckCircle as ActiveIcon,
  Cancel as InactiveIcon,
  ViewList as AllAccountsIcon,
} from '@mui/icons-material';
import { Account } from '../../types';
import { colors, spacing } from '../../styles';

/**
 * AccountSelector Props Interface - Following Interface Segregation Principle
 * Focused interface with only necessary props
 */
interface AccountSelectorProps {
  accounts: Account[];
  currentAccount?: Account | null;
  onAccountChange: (account: Account | null) => void; // Allow null for "All Accounts"
  loading?: boolean;
  disabled?: boolean;
  compact?: boolean;
}

/**
 * Account Selector Component - Sprint 7
 * 
 * SOLID Principles Implementation:
 * - Single Responsibility: Only handles account selection UI
 * - Open/Closed: Extensible via props, closed for modification
 * - Liskov Substitution: Can be used anywhere React.FC is expected
 * - Interface Segregation: Focused props interface
 * - Dependency Inversion: Depends on Account interface abstraction
 */
const AccountSelector: React.FC<AccountSelectorProps> = ({
  accounts,
  currentAccount,
  onAccountChange,
  loading = false,
  disabled = false,
  compact = false,
}) => {
  // Handle account selection with proper error boundary
  const handleAccountChange = useCallback((event: SelectChangeEvent<number | string>) => {
    console.log('[AccountSelector] *** ONCHANGE EVENT FIRED ***');
    console.log('[AccountSelector] Event object:', event);
    console.log('[AccountSelector] Event target:', event.target);
    console.log('[AccountSelector] Event type:', event.type);
    
    const selectedValue = event.target.value;
    console.log('[AccountSelector] Selection changed, value:', selectedValue, 'type:', typeof selectedValue);
    console.log('[AccountSelector] Current accounts array:', accounts.map(acc => ({ id: acc.id, name: acc.name })));
    console.log('[AccountSelector] Current currentAccount:', currentAccount?.id, currentAccount?.name);
    
    if (selectedValue === 'all') {
      // "All Accounts" selected
      console.log('[AccountSelector] "All Accounts" selected, calling onAccountChange(null)');
      onAccountChange(null);
    } else {
      // Convert string back to number for account lookup
      const selectedAccountId = parseInt(selectedValue as string, 10);
      const selectedAccount = accounts.find(account => account.id === selectedAccountId);
      console.log('[AccountSelector] Individual account selected:', selectedAccount?.name, 'ID:', selectedAccountId);
      
      if (selectedAccount) {
        console.log('[AccountSelector] Calling onAccountChange with account:', selectedAccount.name);
        onAccountChange(selectedAccount);
      } else {
        console.error('[AccountSelector] Selected account not found in accounts list! ID:', selectedAccountId);
      }
    }
  }, [accounts, onAccountChange, currentAccount]);

  // Get account status indicator
  const getAccountStatusIcon = useCallback((account: Account) => {
    return account.is_active ? (
      <ActiveIcon sx={{ color: colors.success[500], fontSize: 16 }} />
    ) : (
      <InactiveIcon sx={{ color: colors.error[500], fontSize: 16 }} />
    );
  }, []);

  // Get account status color
  const getAccountStatusColor = useCallback((account: Account) => {
    return account.is_active ? 'success' : 'error';
  }, []);

  // Filter active accounts for primary display
  const activeAccounts = accounts.filter(account => account.is_active);
  const inactiveAccounts = accounts.filter(account => !account.is_active);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', minWidth: compact ? 120 : 200 }}>
        <CircularProgress size={16} sx={{ mr: 1 }} />
        <Typography variant="body2">Loading accounts...</Typography>
      </Box>
    );
  }

  if (accounts.length === 0) {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', minWidth: compact ? 120 : 200 }}>
        <AccountIcon sx={{ mr: 1, color: colors.textSecondary }} />
        <Typography variant="body2" color="text.secondary">
          No accounts
        </Typography>
      </Box>
    );
  }

  return (
    <FormControl
      size={compact ? 'small' : 'medium'}
      sx={{
        minWidth: compact ? 120 : 200,
        maxWidth: compact ? 180 : 280,
      }}
    >
      <Select
        value={currentAccount?.id?.toString() || 'all'}
        onChange={handleAccountChange}
        disabled={disabled}
        displayEmpty
        sx={{
          '& .MuiSelect-select': {
            display: 'flex',
            alignItems: 'center',
            py: compact ? spacing.sm : spacing.md,
            px: spacing.md,
            borderRadius: spacing.xl,
            backgroundColor: colors.bgSearch,
            border: `1px solid ${colors.borderSearch}`,
            minHeight: 56,
            '&:hover': {
              backgroundColor: colors.bgHover,
              borderColor: alpha(colors.primary[500], 0.3),
            },
            '&.Mui-focused': {
              backgroundColor: colors.bgPrimary,
              borderColor: colors.primary[500],
              boxShadow: `0 0 0 3px ${alpha(colors.primary[500], 0.1)}`,
            },
          },
          '& .MuiOutlinedInput-notchedOutline': {
            border: 'none',
          },
        }}
        renderValue={(selected) => {
          if (!selected) {
            return (
              <Box sx={{ display: 'flex', alignItems: 'center', color: colors.textSecondary }}>
                <AccountIcon sx={{ mr: 1, fontSize: compact ? 18 : 20 }} />
                <Typography variant="body2">Select Account</Typography>
              </Box>
            );
          }

          // Handle "All Accounts" selection
          if (selected === 'all' || !currentAccount) {
            return (
              <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                <Avatar
                  sx={{
                    width: compact ? 24 : 32,
                    height: compact ? 24 : 32,
                    mr: spacing.md,
                    bgcolor: colors.primary[500],
                    fontSize: compact ? 10 : 12,
                    fontWeight: 600,
                  }}
                >
                  ALL
                </Avatar>
                <Box sx={{ flex: 1, minWidth: 0 }}>
                  <Typography
                    variant={compact ? 'body2' : 'body1'}
                    sx={{
                      fontWeight: 500,
                      color: colors.textPrimary,
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    All Accounts eBay
                  </Typography>
                  {!compact && (
                    <Typography
                      variant="caption"
                      sx={{
                        color: colors.textSecondary,
                        fontWeight: 400,
                      }}
                    >
                      View data from all accounts
                    </Typography>
                  )}
                </Box>
                {compact && (
                  <Chip
                    size="small"
                    label="All"
                    color="primary"
                    sx={{ ml: spacing.sm, height: 20, fontSize: 10 }}
                  />
                )}
              </Box>
            );
          }

          return (
            <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
              <Avatar
                sx={{
                  width: compact ? 24 : 32,
                  height: compact ? 24 : 32,
                  mr: spacing.md,
                  bgcolor: colors.primary[500],
                  fontSize: compact ? 12 : 14,
                  fontWeight: 600,
                }}
              >
                {currentAccount.name.charAt(0).toUpperCase()}
              </Avatar>
              <Box sx={{ flex: 1, minWidth: 0 }}>
                <Typography
                  variant={compact ? 'body2' : 'body1'}
                  sx={{
                    fontWeight: 500,
                    color: colors.textPrimary,
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {currentAccount.name}
                </Typography>
                {!compact && (
                  <Box sx={{ display: 'flex', alignItems: 'center', mt: 0.25 }}>
                    {getAccountStatusIcon(currentAccount)}
                    <Typography
                      variant="caption"
                      sx={{
                        ml: 0.5,
                        color: currentAccount.is_active ? colors.success[600] : colors.error[600],
                        fontWeight: 500,
                      }}
                    >
                      {currentAccount.is_active ? 'Active' : 'Inactive'}
                    </Typography>
                  </Box>
                )}
              </Box>
              {compact && (
                <Chip
                  size="small"
                  label={currentAccount.is_active ? 'Active' : 'Inactive'}
                  color={getAccountStatusColor(currentAccount) as any}
                  sx={{ ml: spacing.sm, height: 20, fontSize: 10 }}
                />
              )}
            </Box>
          );
        }}
      >
        {/* All Accounts Option */}
        <MenuItem
          value="all"
          sx={{
            py: spacing.md,
            px: spacing.lg,
            backgroundColor: 'all' === (currentAccount?.id || 'all') ? colors.primary[50] : 'transparent',
            '&:hover': {
              backgroundColor: colors.primary[100],
            },
            '&.Mui-selected': {
              backgroundColor: colors.primary[100],
              '&:hover': {
                backgroundColor: colors.primary[200],
              },
            },
          }}
        >
          <ListItemIcon sx={{ minWidth: 40 }}>
            <Avatar
              sx={{
                width: 28,
                height: 28,
                bgcolor: colors.primary[500],
                fontSize: 12,
                fontWeight: 600,
              }}
            >
              ALL
            </Avatar>
          </ListItemIcon>
          <ListItemText
            primary={
              <Typography variant="body2" fontWeight={600} color={colors.primary[700]}>
                All Accounts eBay
              </Typography>
            }
            secondary={
              <Typography variant="caption" color={colors.textSecondary}>
                View data from all accounts ({accounts.length} total)
              </Typography>
            }
          />
        </MenuItem>

        {/* Divider after All Accounts */}
        {accounts.length > 0 && <Divider sx={{ my: spacing.sm }} />}

        {/* Active Accounts Section */}
        {activeAccounts.length > 0 && (
          <>
            <Typography
              variant="overline"
              sx={{
                px: spacing.lg,
                py: spacing.sm,
                color: colors.textSecondary,
                fontWeight: 600,
                fontSize: 11,
              }}
            >
              Active Accounts
            </Typography>
            {activeAccounts.map((account) => (
              <MenuItem
                key={account.id}
                value={account.id.toString()}
                onClick={() => {
                  console.log('[AccountSelector] Manual onClick - Account:', account.name, 'ID:', account.id);
                  onAccountChange(account);
                }}
                sx={{
                  py: spacing.md,
                  px: spacing.lg,
                  '&:hover': {
                    backgroundColor: colors.bgHover,
                  },
                  '&.Mui-selected': {
                    backgroundColor: colors.primary[50],
                    '&:hover': {
                      backgroundColor: colors.primary[100],
                    },
                  },
                }}
              >
                <ListItemIcon sx={{ minWidth: 40 }}>
                  <Avatar
                    sx={{
                      width: 28,
                      height: 28,
                      bgcolor: colors.success[500],
                      fontSize: 12,
                      fontWeight: 600,
                    }}
                  >
                    {account.name.charAt(0).toUpperCase()}
                  </Avatar>
                </ListItemIcon>
                <ListItemText
                  primary={
                    <Typography variant="body2" fontWeight={500} color={colors.textPrimary}>
                      {account.name}
                    </Typography>
                  }
                  secondary={
                    <Box sx={{ display: 'flex', alignItems: 'center', mt: 0.25 }}>
                      {getAccountStatusIcon(account)}
                      <Typography
                        variant="caption"
                        sx={{
                          ml: 0.5,
                          color: colors.success[600],
                          fontWeight: 500,
                        }}
                      >
                        Active
                      </Typography>
                    </Box>
                  }
                />
              </MenuItem>
            ))}
          </>
        )}

        {/* Divider between active and inactive */}
        {activeAccounts.length > 0 && inactiveAccounts.length > 0 && <Divider />}

        {/* Inactive Accounts Section */}
        {inactiveAccounts.length > 0 && (
          <>
            <Typography
              variant="overline"
              sx={{
                px: spacing.lg,
                py: spacing.sm,
                color: colors.textSecondary,
                fontWeight: 600,
                fontSize: 11,
              }}
            >
              Inactive Accounts
            </Typography>
            {inactiveAccounts.map((account) => (
              <MenuItem
                key={account.id}
                value={account.id.toString()}
                onClick={() => {
                  console.log('[AccountSelector] Manual onClick - Inactive Account:', account.name, 'ID:', account.id);
                  onAccountChange(account);
                }}
                sx={{
                  py: spacing.md,
                  px: spacing.lg,
                  opacity: 0.7,
                  '&:hover': {
                    backgroundColor: colors.bgHover,
                    opacity: 1,
                  },
                  '&.Mui-selected': {
                    backgroundColor: colors.error[50],
                    opacity: 1,
                    '&:hover': {
                      backgroundColor: colors.error[100],
                    },
                  },
                }}
              >
                <ListItemIcon sx={{ minWidth: 40 }}>
                  <Avatar
                    sx={{
                      width: 28,
                      height: 28,
                      bgcolor: colors.error[500],
                      fontSize: 12,
                      fontWeight: 600,
                    }}
                  >
                    {account.name.charAt(0).toUpperCase()}
                  </Avatar>
                </ListItemIcon>
                <ListItemText
                  primary={
                    <Typography variant="body2" fontWeight={500} color={colors.textPrimary}>
                      {account.name}
                    </Typography>
                  }
                  secondary={
                    <Box sx={{ display: 'flex', alignItems: 'center', mt: 0.25 }}>
                      {getAccountStatusIcon(account)}
                      <Typography
                        variant="caption"
                        sx={{
                          ml: 0.5,
                          color: colors.error[600],
                          fontWeight: 500,
                        }}
                      >
                        Inactive
                      </Typography>
                    </Box>
                  }
                />
              </MenuItem>
            ))}
          </>
        )}

        {/* Empty state */}
        {accounts.length === 0 && (
          <MenuItem disabled sx={{ py: spacing.lg, px: spacing.lg }}>
            <Typography variant="body2" color="text.secondary">
              No accounts available
            </Typography>
          </MenuItem>
        )}
      </Select>
    </FormControl>
  );
};

export default AccountSelector;