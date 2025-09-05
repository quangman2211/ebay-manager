import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Tabs,
  Tab,
  Alert,
  Snackbar,
  Paper,
} from '@mui/material';
import {
  Add as AddIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { GridRowSelectionModel } from '@mui/x-data-grid';

import { useAccountManagement } from '../hooks/useAccountManagement';
import { useAccount } from '../context/AccountContext';
import AccountDataGrid from '../components/AccountManagement/AccountDataGrid';
import AccountForm from '../components/AccountManagement/AccountForm';
import AccountPermissionsDialog from '../components/AccountManagement/AccountPermissionsDialog';
import AccountDeletionDialog from '../components/AccountManagement/AccountDeletionDialog';
import { Account } from '../types';

/**
 * Account Management Page - Sprint 7
 * Follows Single Responsibility Principle - orchestrates account management UI
 * Integrates all account management components following SOLID principles
 */
const AccountManagement: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [selectedAccountIds, setSelectedAccountIds] = useState<number[]>([]);
  const [formOpen, setFormOpen] = useState(false);
  const [editingAccount, setEditingAccount] = useState<Account | null>(null);
  const [permissionsDialogOpen, setPermissionsDialogOpen] = useState(false);
  const [permissionsAccount, setPermissionsAccount] = useState<Account | null>(null);
  const [deletionDialogOpen, setDeletionDialogOpen] = useState(false);
  const [deletionAccount, setDeletionAccount] = useState<Account | null>(null);
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' | 'info' | 'warning' }>({
    open: false,
    message: '',
    severity: 'success'
  });

  // Custom hooks for account management
  const {
    accounts,
    loading,
    error,
    fetchAccounts,
    createAccount,
    updateAccount,
    deactivateAccount,
    switchAccount,
    clearError,
  } = useAccountManagement();

  // Account context for global state
  const { state: accountState, setAccounts, setCurrentAccount } = useAccount();

  // Load accounts on component mount
  useEffect(() => {
    fetchAccounts().then(() => {
      setAccounts(accounts);
    });
  }, []);

  // Update context when accounts change
  useEffect(() => {
    setAccounts(accounts);
  }, [accounts, setAccounts]);

  const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };


  const handleCreateAccount = () => {
    setEditingAccount(null);
    setFormOpen(true);
  };

  const handleEditAccount = (account: Account) => {
    setEditingAccount(account);
    setFormOpen(true);
  };

  const handleFormSubmit = async (accountData: any) => {
    try {
      if (editingAccount) {
        // Update existing account
        await updateAccount(editingAccount.id, accountData);
        setSnackbar({
          open: true,
          message: 'Account updated successfully',
          severity: 'success'
        });
      } else {
        // Create new account
        await createAccount(accountData);
        setSnackbar({
          open: true,
          message: 'Account created successfully',
          severity: 'success'
        });
      }
      setFormOpen(false);
      setEditingAccount(null);
    } catch (error) {
      setSnackbar({
        open: true,
        message: error instanceof Error ? error.message : 'Operation failed',
        severity: 'error'
      });
    }
  };

  const handleDeleteAccount = async (accountId: number) => {
    const account = accounts.find(acc => acc.id === accountId);
    if (account) {
      setDeletionAccount(account);
      setDeletionDialogOpen(true);
    }
  };

  const handleDeletionConfirm = async (action: 'transfer' | 'delete') => {
    if (!deletionAccount) return;

    try {
      const result = await deactivateAccount(deletionAccount.id, action);
      
      setSnackbar({
        open: true,
        message: result.message,
        severity: 'success'
      });

      // Show additional info if needed
      if (result.next_action) {
        setTimeout(() => {
          setSnackbar({
            open: true,
            message: result.next_action || '',
            severity: 'info'
          });
        }, 3000);
      }
      
    } catch (error) {
      setSnackbar({
        open: true,
        message: error instanceof Error ? error.message : 'Failed to process account deletion',
        severity: 'error'
      });
    }
  };

  const handleDeletionDialogClose = () => {
    setDeletionDialogOpen(false);
    setDeletionAccount(null);
  };

  const handleSwitchAccount = async (account: Account) => {
    try {
      await switchAccount(account.id);
      setCurrentAccount(account);
      setSnackbar({
        open: true,
        message: `Switched to ${account.name}`,
        severity: 'success'
      });
    } catch (error) {
      setSnackbar({
        open: true,
        message: error instanceof Error ? error.message : 'Failed to switch account',
        severity: 'error'
      });
    }
  };

  const handleRefresh = () => {
    fetchAccounts();
  };

  const handleSelectionChange = (selectionModel: GridRowSelectionModel) => {
    setSelectedAccountIds(selectionModel as number[]);
  };

  const handleCloseSnackbar = () => {
    setSnackbar(prev => ({ ...prev, open: false }));
  };

  const handleManagePermissions = (account: Account) => {
    setPermissionsAccount(account);
    setPermissionsDialogOpen(true);
  };

  const handleClosePermissionsDialog = () => {
    setPermissionsDialogOpen(false);
    setPermissionsAccount(null);
  };




  const activeAccounts = accounts.filter(account => account.is_active);
  const inactiveAccounts = accounts.filter(account => !account.is_active);

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Account Management
        </Typography>
        
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <Button
            startIcon={<RefreshIcon />}
            onClick={handleRefresh}
            disabled={loading}
          >
            Refresh
          </Button>
          
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleCreateAccount}
          >
            Add Account
          </Button>
        </Box>
      </Box>

      {/* Error Display */}
      {error && (
        <Alert 
          severity="error" 
          sx={{ mb: 2 }} 
          onClose={clearError}
        >
          {error}
        </Alert>
      )}

      {/* Tabs */}
      <Paper sx={{ width: '100%', mb: 3 }}>
        <Tabs value={tabValue} onChange={handleTabChange}>
          <Tab label={`Active Accounts (${activeAccounts.length})`} />
          <Tab label={`Inactive Accounts (${inactiveAccounts.length})`} />
          <Tab label={`All Accounts (${accounts.length})`} />
        </Tabs>
      </Paper>

      {/* Content */}
      <Box sx={{ mt: 2 }}>
        {tabValue === 0 && (
          <AccountDataGrid
            accounts={activeAccounts}
            loading={loading}
            onEditAccount={handleEditAccount}
            onDeleteAccount={handleDeleteAccount}
            selectedAccountIds={selectedAccountIds}
            onSelectionChange={handleSelectionChange}
          />
        )}

        {tabValue === 1 && (
          <AccountDataGrid
            accounts={inactiveAccounts}
            loading={loading}
            onEditAccount={handleEditAccount}
            onDeleteAccount={handleDeleteAccount}
            selectedAccountIds={selectedAccountIds}
            onSelectionChange={handleSelectionChange}
          />
        )}

        {tabValue === 2 && (
          <AccountDataGrid
            accounts={accounts}
            loading={loading}
            onEditAccount={handleEditAccount}
            onDeleteAccount={handleDeleteAccount}
            selectedAccountIds={selectedAccountIds}
            onSelectionChange={handleSelectionChange}
          />
        )}
      </Box>

      {/* Account Form Dialog */}
      <AccountForm
        open={formOpen}
        onClose={() => {
          setFormOpen(false);
          setEditingAccount(null);
        }}
        onSubmit={handleFormSubmit}
        account={editingAccount}
        loading={loading}
      />

      {/* Account Permissions Dialog */}
      <AccountPermissionsDialog
        open={permissionsDialogOpen}
        onClose={handleClosePermissionsDialog}
        account={permissionsAccount}
      />

      {/* Account Deletion Dialog */}
      <AccountDeletionDialog
        open={deletionDialogOpen}
        account={deletionAccount}
        onClose={handleDeletionDialogClose}
        onConfirm={handleDeletionConfirm}
        loading={loading}
      />

      {/* Success/Error Snackbar */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
      >
        <Alert 
          onClose={handleCloseSnackbar} 
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default AccountManagement;