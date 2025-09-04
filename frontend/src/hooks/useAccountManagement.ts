import { useCallback, useEffect } from 'react';
import { accountsAPI } from '../services/api';
import { accountSyncService } from '../services/accountSync';
import { useAccount } from '../context/AccountContext';
import type { Account, EnhancedAccount, AccountSwitchRequest } from '../types';

interface UseAccountManagementReturn {
  accounts: Account[];
  currentAccount: Account | null;
  loading: boolean;
  error: string | null;
  syncStatus: 'idle' | 'syncing' | 'success' | 'error';
  lastSyncAt: string | null;
  fetchAccounts: () => Promise<void>;
  getAccountDetails: (accountId: number) => Promise<EnhancedAccount>;
  createAccount: (accountData: Omit<Account, 'id' | 'created_at'>) => Promise<Account>;
  updateAccount: (accountId: number, updates: Partial<Account>) => Promise<Account>;
  deactivateAccount: (accountId: number) => Promise<void>;
  switchAccount: (accountId: number) => Promise<void>;
  syncAccounts: () => Promise<void>;
  startAutoSync: () => void;
  stopAutoSync: () => void;
  clearError: () => void;
}

/**
 * Custom hook for account management operations
 * 
 * Enhanced with Context Integration - Sprint 7 Task 5
 * - Integrates with AccountContext for global state management
 * - Uses AccountSyncService for automated synchronization
 * - Follows SOLID principles with proper dependency injection
 */
export const useAccountManagement = (): UseAccountManagementReturn => {
  const {
    state,
    setAccounts,
    setCurrentAccount,
    setLoading,
    setError,
    setSyncStatus,
    setLastSyncAt,
    addAccount,
    updateAccount: updateAccountInContext,
    removeAccount,
    clearError: clearContextError,
  } = useAccount();

  // Fetch accounts initially on mount
  useEffect(() => {
    if (state.accounts.length === 0) {
      const initializeAccounts = async () => {
        try {
          setLoading(true);
          clearContextError();
          setSyncStatus('syncing');
          const data = await accountsAPI.getAccounts();
          setAccounts(data);
          setSyncStatus('success');
          setLastSyncAt(new Date().toISOString());
        } catch (err) {
          const errorMessage = err instanceof Error ? err.message : 'Failed to fetch accounts';
          setError(errorMessage);
          setSyncStatus('error');
        } finally {
          setLoading(false);
        }
      };
      initializeAccounts();
    }
  }, [state.accounts.length, setLoading, clearContextError, setSyncStatus, setAccounts, setLastSyncAt, setError]);

  // Initialize auto-sync on mount
  useEffect(() => {
    const handleSyncUpdate = (accounts: Account[]) => {
      setAccounts(accounts);
      setSyncStatus('success');
      setLastSyncAt(new Date().toISOString());
    };

    const handleSyncError = (error: string) => {
      setError(error);
      setSyncStatus('error');
    };

    // Start auto-sync if needed
    if (accountSyncService.isSyncNeeded(10)) {
      accountSyncService.startAutoSync(handleSyncUpdate, handleSyncError);
    }

    return () => {
      accountSyncService.stopAutoSync();
    };
  }, [setAccounts, setSyncStatus, setLastSyncAt, setError]);

  const clearError = useCallback(() => {
    clearContextError();
  }, [clearContextError]);

  const fetchAccounts = useCallback(async () => {
    try {
      setLoading(true);
      clearError();
      setSyncStatus('syncing');
      const data = await accountsAPI.getAccounts();
      setAccounts(data);
      setSyncStatus('success');
      setLastSyncAt(new Date().toISOString());
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch accounts';
      setError(errorMessage);
      setSyncStatus('error');
    } finally {
      setLoading(false);
    }
  }, [setLoading, clearError, setSyncStatus, setAccounts, setLastSyncAt, setError]);

  const getAccountDetails = useCallback(async (accountId: number): Promise<EnhancedAccount> => {
    try {
      clearError();
      return await accountsAPI.getAccountDetails(accountId);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to get account details';
      setError(errorMessage);
      throw new Error(errorMessage);
    }
  }, [clearError, setError]);

  const createAccount = useCallback(async (accountData: Omit<Account, 'id' | 'created_at'>): Promise<Account> => {
    try {
      clearError();
      const newAccount = await accountsAPI.createAccount(accountData);
      addAccount(newAccount);
      return newAccount;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create account';
      setError(errorMessage);
      throw new Error(errorMessage);
    }
  }, [clearError, addAccount, setError]);

  const updateAccount = useCallback(async (accountId: number, updates: Partial<Account>): Promise<Account> => {
    try {
      clearError();
      const updatedAccount = await accountsAPI.updateAccount(accountId, updates);
      updateAccountInContext(updatedAccount);
      return updatedAccount;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update account';
      setError(errorMessage);
      throw new Error(errorMessage);
    }
  }, [clearError, updateAccountInContext, setError]);

  const deactivateAccount = useCallback(async (accountId: number): Promise<void> => {
    try {
      clearError();
      await accountsAPI.deactivateAccount(accountId);
      updateAccountInContext({ id: accountId, is_active: false } as Account);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to deactivate account';
      setError(errorMessage);
      throw new Error(errorMessage);
    }
  }, [clearError, updateAccountInContext, setError]);

  const switchAccount = useCallback(async (accountId: number): Promise<void> => {
    try {
      clearError();
      const request: AccountSwitchRequest = { account_id: accountId };
      await accountsAPI.switchAccount(request);
      
      // Update current account based on context
      const account = state.accounts.find(acc => acc.id === accountId);
      if (account) {
        setCurrentAccount(account);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to switch account';
      setError(errorMessage);
      throw new Error(errorMessage);
    }
  }, [clearError, state.accounts, setCurrentAccount, setError]);

  // Sync methods integrated with context
  const syncAccounts = useCallback(async (): Promise<void> => {
    setSyncStatus('syncing');
    const handleSyncUpdate = (accounts: Account[]) => {
      setAccounts(accounts);
      setSyncStatus('success');
      setLastSyncAt(new Date().toISOString());
    };

    const handleSyncError = (error: string) => {
      setError(error);
      setSyncStatus('error');
    };

    await accountSyncService.syncAccounts(handleSyncUpdate, handleSyncError);
  }, [setSyncStatus, setAccounts, setLastSyncAt, setError]);

  const startAutoSync = useCallback(() => {
    const handleSyncUpdate = (accounts: Account[]) => {
      setAccounts(accounts);
      setSyncStatus('success');
      setLastSyncAt(new Date().toISOString());
    };

    const handleSyncError = (error: string) => {
      setError(error);
      setSyncStatus('error');
    };

    accountSyncService.startAutoSync(handleSyncUpdate, handleSyncError);
  }, [setAccounts, setSyncStatus, setLastSyncAt, setError]);

  const stopAutoSync = useCallback(() => {
    accountSyncService.stopAutoSync();
    setSyncStatus('idle');
  }, [setSyncStatus]);

  return {
    accounts: state.accounts,
    currentAccount: state.currentAccount,
    loading: state.loading,
    error: state.error,
    syncStatus: state.syncStatus,
    lastSyncAt: state.lastSyncAt,
    fetchAccounts,
    getAccountDetails,
    createAccount,
    updateAccount,
    deactivateAccount,
    switchAccount,
    syncAccounts,
    startAutoSync,
    stopAutoSync,
    clearError,
  };
};