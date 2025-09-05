import React from 'react';
import { renderHook, act } from '@testing-library/react';
import { AccountProvider, useAccount } from '../AccountContext';
import { createMockAccount, createMockAccounts } from '../../utils/mockData';
import type { Account } from '../../types';

/**
 * AccountContext Test Suite - Sprint 7
 * 
 * Tests follow SOLID principles:
 * - Single Responsibility: Each test has one clear purpose
 * - Interface Segregation: Testing focused interfaces
 * - Dependency Inversion: Testing abstractions not implementations
 */

// Wrapper component for testing hooks
const wrapper = ({ children }: { children: React.ReactNode }) => (
  <AccountProvider>{children}</AccountProvider>
);

describe('AccountContext', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear();
    jest.clearAllMocks();
  });

  describe('Provider Initialization', () => {
    it('should provide initial state correctly', () => {
      const { result } = renderHook(() => useAccount(), { wrapper });

      expect(result.current.state).toEqual({
        currentAccount: null,
        accounts: [],
        loading: false,
        error: null,
        lastSyncAt: null,
        syncStatus: 'idle',
      });
    });

    it('should throw error when used outside provider', () => {
      // Suppress console.error for this test
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
      
      expect(() => {
        renderHook(() => useAccount());
      }).toThrow('useAccount must be used within an AccountProvider');
      
      consoleSpy.mockRestore();
    });
  });

  describe('Account Management Actions', () => {
    it('should set accounts correctly', () => {
      const { result } = renderHook(() => useAccount(), { wrapper });
      const mockAccounts = createMockAccounts(3);

      act(() => {
        result.current.setAccounts(mockAccounts);
      });

      expect(result.current.state.accounts).toEqual(mockAccounts);
    });

    it('should set current account correctly', () => {
      const { result } = renderHook(() => useAccount(), { wrapper });
      const mockAccount = createMockAccount();

      act(() => {
        result.current.setCurrentAccount(mockAccount);
      });

      expect(result.current.state.currentAccount).toEqual(mockAccount);
    });

    it('should add account correctly', () => {
      const { result } = renderHook(() => useAccount(), { wrapper });
      const initialAccounts = createMockAccounts(2);
      const newAccount = createMockAccount({ id: 3, name: 'New Account' });

      act(() => {
        result.current.setAccounts(initialAccounts);
      });

      act(() => {
        result.current.addAccount(newAccount);
      });

      expect(result.current.state.accounts).toHaveLength(3);
      expect(result.current.state.accounts).toContainEqual(newAccount);
    });

    it('should update account correctly', () => {
      const { result } = renderHook(() => useAccount(), { wrapper });
      const accounts = createMockAccounts(2);
      const updatedAccount = { ...accounts[0], name: 'Updated Account' };

      act(() => {
        result.current.setAccounts(accounts);
      });

      act(() => {
        result.current.updateAccount(updatedAccount);
      });

      expect(result.current.state.accounts[0]).toEqual(updatedAccount);
    });

    it('should update current account when it matches updated account', () => {
      const { result } = renderHook(() => useAccount(), { wrapper });
      const account = createMockAccount();
      const updatedAccount = { ...account, name: 'Updated Current Account' };

      act(() => {
        result.current.setCurrentAccount(account);
      });

      act(() => {
        result.current.updateAccount(updatedAccount);
      });

      expect(result.current.state.currentAccount).toEqual(updatedAccount);
    });

    it('should remove account correctly', () => {
      const { result } = renderHook(() => useAccount(), { wrapper });
      const accounts = createMockAccounts(3);

      act(() => {
        result.current.setAccounts(accounts);
      });

      act(() => {
        result.current.removeAccount(accounts[1].id);
      });

      expect(result.current.state.accounts).toHaveLength(2);
      expect(result.current.state.accounts.find(a => a.id === accounts[1].id)).toBeUndefined();
    });

    it('should clear current account when removed', () => {
      const { result } = renderHook(() => useAccount(), { wrapper });
      const account = createMockAccount();

      act(() => {
        result.current.setCurrentAccount(account);
      });

      act(() => {
        result.current.removeAccount(account.id);
      });

      expect(result.current.state.currentAccount).toBeNull();
    });
  });

  describe('State Management Actions', () => {
    it('should set loading state correctly', () => {
      const { result } = renderHook(() => useAccount(), { wrapper });

      act(() => {
        result.current.setLoading(true);
      });

      expect(result.current.state.loading).toBe(true);

      act(() => {
        result.current.setLoading(false);
      });

      expect(result.current.state.loading).toBe(false);
    });

    it('should set error state correctly', () => {
      const { result } = renderHook(() => useAccount(), { wrapper });
      const errorMessage = 'Test error message';

      act(() => {
        result.current.setError(errorMessage);
      });

      expect(result.current.state.error).toBe(errorMessage);
    });

    it('should clear error correctly', () => {
      const { result } = renderHook(() => useAccount(), { wrapper });

      act(() => {
        result.current.setError('Test error');
      });

      act(() => {
        result.current.clearError();
      });

      expect(result.current.state.error).toBeNull();
    });

    it('should set sync status correctly', () => {
      const { result } = renderHook(() => useAccount(), { wrapper });

      act(() => {
        result.current.setSyncStatus('syncing');
      });

      expect(result.current.state.syncStatus).toBe('syncing');

      act(() => {
        result.current.setSyncStatus('success');
      });

      expect(result.current.state.syncStatus).toBe('success');
    });

    it('should set last sync timestamp correctly', () => {
      const { result } = renderHook(() => useAccount(), { wrapper });
      const timestamp = new Date().toISOString();

      act(() => {
        result.current.setLastSyncAt(timestamp);
      });

      expect(result.current.state.lastSyncAt).toBe(timestamp);
    });
  });

  describe('Helper Functions', () => {
    it('should get account by ID correctly', () => {
      const { result } = renderHook(() => useAccount(), { wrapper });
      const accounts = createMockAccounts(3);

      act(() => {
        result.current.setAccounts(accounts);
      });

      const foundAccount = result.current.getAccountById(accounts[1].id);
      expect(foundAccount).toEqual(accounts[1]);
    });

    it('should return undefined for non-existent account ID', () => {
      const { result } = renderHook(() => useAccount(), { wrapper });
      const accounts = createMockAccounts(2);

      act(() => {
        result.current.setAccounts(accounts);
      });

      const foundAccount = result.current.getAccountById(999);
      expect(foundAccount).toBeUndefined();
    });

    it('should refresh account with partial updates', () => {
      const { result } = renderHook(() => useAccount(), { wrapper });
      const accounts = createMockAccounts(2);

      act(() => {
        result.current.setAccounts(accounts);
      });

      act(() => {
        result.current.refreshAccount(accounts[0].id, { name: 'Refreshed Name' });
      });

      const updatedAccount = result.current.state.accounts.find(a => a.id === accounts[0].id);
      expect(updatedAccount?.name).toBe('Refreshed Name');
      expect(updatedAccount?.platform_username).toBe(accounts[0].platform_username); // Other props preserved
    });

    it('should refresh current account when it matches', () => {
      const { result } = renderHook(() => useAccount(), { wrapper });
      const account = createMockAccount();

      act(() => {
        result.current.setCurrentAccount(account);
      });

      act(() => {
        result.current.refreshAccount(account.id, { name: 'Refreshed Current' });
      });

      expect(result.current.state.currentAccount?.name).toBe('Refreshed Current');
    });
  });

  describe('LocalStorage Integration', () => {
    it('should persist current account to localStorage', () => {
      const { result } = renderHook(() => useAccount(), { wrapper });
      const account = createMockAccount();

      act(() => {
        result.current.setCurrentAccount(account);
      });

      expect(localStorage.setItem).toHaveBeenCalledWith(
        'currentAccountId',
        account.id.toString()
      );
    });

    it('should clear localStorage when current account is set to null', () => {
      const { result } = renderHook(() => useAccount(), { wrapper });

      act(() => {
        result.current.setCurrentAccount(null);
      });

      expect(localStorage.removeItem).toHaveBeenCalledWith('currentAccountId');
    });

    it('should restore current account from localStorage on initialization', () => {
      const account = createMockAccount();
      const accounts = [account];
      
      // Mock localStorage to return the account ID
      (localStorage.getItem as jest.Mock).mockReturnValue(account.id.toString());

      const { result } = renderHook(() => useAccount(), { wrapper });

      // Set accounts first to trigger the useEffect
      act(() => {
        result.current.setAccounts(accounts);
      });

      // Check that the account was restored from localStorage
      expect(result.current.state.currentAccount).toEqual(account);
    });

    it('should handle invalid localStorage data gracefully', () => {
      const accounts = createMockAccounts(2);
      
      // Mock localStorage to return invalid account ID
      (localStorage.getItem as jest.Mock).mockReturnValue('999');

      const { result } = renderHook(() => useAccount(), { wrapper });

      act(() => {
        result.current.setAccounts(accounts);
      });

      // Should not set any current account for invalid ID
      expect(result.current.state.currentAccount).toBeNull();
    });
  });

  describe('Reducer Edge Cases', () => {
    it('should handle unknown action types gracefully', () => {
      const { result } = renderHook(() => useAccount(), { wrapper });
      const initialState = result.current.state;

      // This should not change the state for unknown actions
      act(() => {
        // @ts-ignore - Testing unknown action type
        result.current.dispatch({ type: 'UNKNOWN_ACTION', payload: 'test' });
      });

      expect(result.current.state).toEqual(initialState);
    });

    it('should maintain referential equality for unchanged state parts', () => {
      const { result } = renderHook(() => useAccount(), { wrapper });
      const initialAccounts = result.current.state.accounts;

      act(() => {
        result.current.setLoading(true);
      });

      // Accounts array should remain the same reference
      expect(result.current.state.accounts).toBe(initialAccounts);
    });
  });

  describe('Complex State Interactions', () => {
    it('should handle multiple state updates correctly', () => {
      const { result } = renderHook(() => useAccount(), { wrapper });
      const accounts = createMockAccounts(3);
      const currentAccount = accounts[1];
      const errorMessage = 'Test error';

      act(() => {
        result.current.setAccounts(accounts);
        result.current.setCurrentAccount(currentAccount);
        result.current.setLoading(true);
        result.current.setError(errorMessage);
        result.current.setSyncStatus('syncing');
      });

      expect(result.current.state).toEqual({
        accounts,
        currentAccount,
        loading: true,
        error: errorMessage,
        syncStatus: 'syncing',
        lastSyncAt: null,
      });
    });

    it('should handle account operations with complex state', () => {
      const { result } = renderHook(() => useAccount(), { wrapper });
      const accounts = createMockAccounts(3);
      const newAccount = createMockAccount({ id: 4, name: 'New Account' });

      // Set up initial complex state
      act(() => {
        result.current.setAccounts(accounts);
        result.current.setCurrentAccount(accounts[0]);
        result.current.setError('Initial error');
        result.current.setSyncStatus('success');
      });

      // Add new account - should preserve other state
      act(() => {
        result.current.addAccount(newAccount);
      });

      expect(result.current.state.accounts).toHaveLength(4);
      expect(result.current.state.currentAccount).toEqual(accounts[0]);
      expect(result.current.state.error).toBe('Initial error');
      expect(result.current.state.syncStatus).toBe('success');
    });
  });
});