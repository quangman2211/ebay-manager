import React, { createContext, useContext, useReducer, useEffect, ReactNode, useMemo, useCallback } from 'react';
import type { Account } from '../types';

interface AccountState {
  currentAccount: Account | null;
  accounts: Account[];
  loading: boolean;
  error: string | null;
  lastSyncAt: string | null;
  syncStatus: 'idle' | 'syncing' | 'success' | 'error';
}

type AccountAction =
  | { type: 'SET_CURRENT_ACCOUNT'; payload: Account | null }
  | { type: 'SET_ACCOUNTS'; payload: Account[] }
  | { type: 'ADD_ACCOUNT'; payload: Account }
  | { type: 'UPDATE_ACCOUNT'; payload: Account }
  | { type: 'REMOVE_ACCOUNT'; payload: number }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'SET_SYNC_STATUS'; payload: 'idle' | 'syncing' | 'success' | 'error' }
  | { type: 'SET_LAST_SYNC_AT'; payload: string | null }
  | { type: 'REFRESH_ACCOUNT'; payload: { id: number; updates: Partial<Account> } };

interface AccountContextType {
  state: AccountState;
  dispatch: React.Dispatch<AccountAction>;
  setCurrentAccount: (account: Account | null) => void;
  setAccounts: (accounts: Account[]) => void;
  addAccount: (account: Account) => void;
  updateAccount: (account: Account) => void;
  removeAccount: (accountId: number) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setSyncStatus: (status: 'idle' | 'syncing' | 'success' | 'error') => void;
  setLastSyncAt: (timestamp: string | null) => void;
  refreshAccount: (id: number, updates: Partial<Account>) => void;
  clearError: () => void;
  getAccountById: (id: number) => Account | undefined;
}

const AccountContext = createContext<AccountContextType | undefined>(undefined);

const accountReducer = (state: AccountState, action: AccountAction): AccountState => {
  switch (action.type) {
    case 'SET_CURRENT_ACCOUNT':
      return {
        ...state,
        currentAccount: action.payload,
      };
    case 'SET_ACCOUNTS':
      return {
        ...state,
        accounts: action.payload,
      };
    case 'ADD_ACCOUNT':
      return {
        ...state,
        accounts: [...state.accounts, action.payload],
      };
    case 'UPDATE_ACCOUNT':
      return {
        ...state,
        accounts: state.accounts.map(account =>
          account.id === action.payload.id ? action.payload : account
        ),
        currentAccount: state.currentAccount?.id === action.payload.id 
          ? action.payload 
          : state.currentAccount,
      };
    case 'REMOVE_ACCOUNT':
      return {
        ...state,
        accounts: state.accounts.filter(account => account.id !== action.payload),
        currentAccount: state.currentAccount?.id === action.payload 
          ? null 
          : state.currentAccount,
      };
    case 'SET_LOADING':
      return {
        ...state,
        loading: action.payload,
      };
    case 'SET_ERROR':
      return {
        ...state,
        error: action.payload,
      };
    case 'SET_SYNC_STATUS':
      return {
        ...state,
        syncStatus: action.payload,
      };
    case 'SET_LAST_SYNC_AT':
      return {
        ...state,
        lastSyncAt: action.payload,
      };
    case 'REFRESH_ACCOUNT':
      return {
        ...state,
        accounts: state.accounts.map(account =>
          account.id === action.payload.id 
            ? { ...account, ...action.payload.updates }
            : account
        ),
        currentAccount: state.currentAccount?.id === action.payload.id
          ? { ...state.currentAccount, ...action.payload.updates }
          : state.currentAccount,
      };
    default:
      return state;
  }
};

const initialState: AccountState = {
  currentAccount: null,
  accounts: [],
  loading: false,
  error: null,
  lastSyncAt: null,
  syncStatus: 'idle',
};

interface AccountProviderProps {
  children: ReactNode;
}

/**
 * Account Context Provider
 * Provides global state management for account-related data
 * Follows Dependency Inversion Principle - components depend on this abstraction
 */
export const AccountProvider: React.FC<AccountProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(accountReducer, initialState);

  // Load current account from localStorage on mount
  useEffect(() => {
    const currentAccountId = localStorage.getItem('currentAccountId');
    if (currentAccountId === 'all' || !currentAccountId) {
      // Default to "All Accounts" (null) if not set or explicitly set to 'all'
      dispatch({ type: 'SET_CURRENT_ACCOUNT', payload: null });
    } else if (currentAccountId && state.accounts.length > 0) {
      const account = state.accounts.find(acc => acc.id === parseInt(currentAccountId));
      if (account) {
        dispatch({ type: 'SET_CURRENT_ACCOUNT', payload: account });
      } else {
        // If saved account doesn't exist, default to "All Accounts"
        dispatch({ type: 'SET_CURRENT_ACCOUNT', payload: null });
        localStorage.setItem('currentAccountId', 'all');
      }
    }
  }, [state.accounts]);

  const setCurrentAccount = useCallback((account: Account | null) => {
    console.log('[AccountContext] setCurrentAccount called with:', account ? account.name : 'All Accounts (null)');
    dispatch({ type: 'SET_CURRENT_ACCOUNT', payload: account });
    if (account) {
      console.log('[AccountContext] Saving account ID to localStorage:', account.id);
      localStorage.setItem('currentAccountId', account.id.toString());
    } else {
      // Save "All Accounts" selection
      console.log('[AccountContext] Saving "All Accounts" selection to localStorage');
      localStorage.setItem('currentAccountId', 'all');
    }
    console.log('[AccountContext] Current localStorage value:', localStorage.getItem('currentAccountId'));
  }, []);

  const setAccounts = useCallback((accounts: Account[]) => {
    dispatch({ type: 'SET_ACCOUNTS', payload: accounts });
  }, []);

  const addAccount = useCallback((account: Account) => {
    dispatch({ type: 'ADD_ACCOUNT', payload: account });
  }, []);

  const updateAccount = useCallback((account: Account) => {
    dispatch({ type: 'UPDATE_ACCOUNT', payload: account });
  }, []);

  const removeAccount = useCallback((accountId: number) => {
    dispatch({ type: 'REMOVE_ACCOUNT', payload: accountId });
  }, []);

  const setLoading = useCallback((loading: boolean) => {
    dispatch({ type: 'SET_LOADING', payload: loading });
  }, []);

  const setError = useCallback((error: string | null) => {
    dispatch({ type: 'SET_ERROR', payload: error });
  }, []);

  const setSyncStatus = useCallback((status: 'idle' | 'syncing' | 'success' | 'error') => {
    dispatch({ type: 'SET_SYNC_STATUS', payload: status });
  }, []);

  const setLastSyncAt = useCallback((timestamp: string | null) => {
    dispatch({ type: 'SET_LAST_SYNC_AT', payload: timestamp });
  }, []);

  const refreshAccount = useCallback((id: number, updates: Partial<Account>) => {
    dispatch({ type: 'REFRESH_ACCOUNT', payload: { id, updates } });
  }, []);

  const clearError = useCallback(() => {
    dispatch({ type: 'SET_ERROR', payload: null });
  }, []);

  const getAccountById = useCallback((id: number): Account | undefined => {
    return state.accounts.find(account => account.id === id);
  }, [state.accounts]);

  const contextValue: AccountContextType = useMemo(() => ({
    state,
    dispatch,
    setCurrentAccount,
    setAccounts,
    addAccount,
    updateAccount,
    removeAccount,
    setLoading,
    setError,
    setSyncStatus,
    setLastSyncAt,
    refreshAccount,
    clearError,
    getAccountById,
  }), [
    state,
    setCurrentAccount,
    setAccounts,
    addAccount,
    updateAccount,
    removeAccount,
    setLoading,
    setError,
    setSyncStatus,
    setLastSyncAt,
    refreshAccount,
    clearError,
    getAccountById,
  ]);

  return (
    <AccountContext.Provider value={contextValue}>
      {children}
    </AccountContext.Provider>
  );
};

/**
 * Custom hook to use Account context
 * Throws error if used outside of AccountProvider
 */
export const useAccount = (): AccountContextType => {
  const context = useContext(AccountContext);
  if (context === undefined) {
    throw new Error('useAccount must be used within an AccountProvider');
  }
  return context;
};