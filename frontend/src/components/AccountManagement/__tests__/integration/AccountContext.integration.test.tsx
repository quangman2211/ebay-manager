import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { server } from '../../../../mocks/server';
import { rest } from 'msw';
import { AccountProvider, useAccount } from '../../../../context/AccountContext';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { BrowserRouter } from 'react-router-dom';
import { createMockAccount } from '../../../../utils/mockData';

/**
 * Account Context Integration Tests - Sprint 7
 * 
 * Tests the integration between:
 * - AccountContext and API services
 * - Context state management
 * - Component re-rendering
 * - Error handling
 * 
 * Following SOLID Principles:
 * - Single Responsibility: Each test focuses on one integration aspect
 * - Dependency Inversion: Tests context abstractions, not implementation details
 */

const theme = createTheme();

// Test component that uses AccountContext
const TestConsumer: React.FC = () => {
  const {
    accounts,
    loading,
    error,
    selectedAccount,
    fetchAccounts,
    selectAccount,
    addAccount,
    updateAccount,
    deleteAccount,
    clearError,
  } = useAccount();

  return (
    <div>
      <div data-testid="loading">{loading ? 'loading' : 'not-loading'}</div>
      <div data-testid="error">{error || 'no-error'}</div>
      <div data-testid="accounts-count">{accounts.length}</div>
      <div data-testid="selected-account">
        {selectedAccount ? selectedAccount.name : 'none'}
      </div>

      <button onClick={fetchAccounts}>Fetch Accounts</button>
      <button onClick={() => selectAccount(accounts[0])}>Select First Account</button>
      <button onClick={clearError}>Clear Error</button>

      <div data-testid="accounts-list">
        {accounts.map(account => (
          <div key={account.id} data-testid={`account-${account.id}`}>
            {account.name}
          </div>
        ))}
      </div>
    </div>
  );
};

// Test wrapper with providers
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <BrowserRouter>
    <ThemeProvider theme={theme}>
      <AccountProvider>
        {children}
      </AccountProvider>
    </ThemeProvider>
  </BrowserRouter>
);

// Setup MSW server
beforeAll(() => server.listen());
afterEach(() => {
  server.resetHandlers();
  jest.clearAllMocks();
});
afterAll(() => server.close());

describe('AccountContext - Integration Tests', () => {
  describe('API Integration', () => {
    it('should fetch accounts from API successfully', async () => {
      render(
        <TestWrapper>
          <TestConsumer />
        </TestWrapper>
      );

      // Initially should have no accounts
      expect(screen.getByTestId('accounts-count')).toHaveTextContent('0');
      expect(screen.getByTestId('loading')).toHaveTextContent('not-loading');

      // Fetch accounts
      fireEvent.click(screen.getByText('Fetch Accounts'));

      // Should show loading state
      expect(screen.getByTestId('loading')).toHaveTextContent('loading');

      // Wait for accounts to load
      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('not-loading');
      });

      // Should have loaded accounts
      expect(screen.getByTestId('accounts-count')).toHaveTextContent('3'); // Based on mock data
      expect(screen.getByTestId('error')).toHaveTextContent('no-error');
    });

    it('should handle API errors gracefully', async () => {
      // Mock API error
      server.use(
        rest.get('/api/accounts', (req, res, ctx) => {
          return res(
            ctx.status(500),
            ctx.json({ error: 'Internal server error' })
          );
        })
      );

      render(
        <TestWrapper>
          <TestConsumer />
        </TestWrapper>
      );

      // Fetch accounts
      fireEvent.click(screen.getByText('Fetch Accounts'));

      // Wait for error
      await waitFor(() => {
        expect(screen.getByTestId('error')).not.toHaveTextContent('no-error');
      });

      // Should show error and stop loading
      expect(screen.getByTestId('loading')).toHaveTextContent('not-loading');
      expect(screen.getByTestId('accounts-count')).toHaveTextContent('0');
    });

    it('should handle network failures', async () => {
      // Mock network error
      server.use(
        rest.get('/api/accounts', (req, res) => {
          return res.networkError('Network connection failed');
        })
      );

      render(
        <TestWrapper>
          <TestConsumer />
        </TestWrapper>
      );

      fireEvent.click(screen.getByText('Fetch Accounts'));

      await waitFor(() => {
        expect(screen.getByTestId('error')).not.toHaveTextContent('no-error');
      });

      expect(screen.getByTestId('loading')).toHaveTextContent('not-loading');
    });
  });

  describe('State Management Integration', () => {
    it('should manage selected account state correctly', async () => {
      render(
        <TestWrapper>
          <TestConsumer />
        </TestWrapper>
      );

      // Initially no account selected
      expect(screen.getByTestId('selected-account')).toHaveTextContent('none');

      // Fetch accounts first
      fireEvent.click(screen.getByText('Fetch Accounts'));
      
      await waitFor(() => {
        expect(screen.getByTestId('accounts-count')).toHaveTextContent('3');
      });

      // Select first account
      fireEvent.click(screen.getByText('Select First Account'));

      // Should have selected account
      await waitFor(() => {
        expect(screen.getByTestId('selected-account')).not.toHaveTextContent('none');
      });
    });

    it('should clear errors when requested', async () => {
      // Mock API error
      server.use(
        rest.get('/api/accounts', (req, res, ctx) => {
          return res(
            ctx.status(400),
            ctx.json({ error: 'Bad request' })
          );
        })
      );

      render(
        <TestWrapper>
          <TestConsumer />
        </TestWrapper>
      );

      // Trigger error
      fireEvent.click(screen.getByText('Fetch Accounts'));

      await waitFor(() => {
        expect(screen.getByTestId('error')).not.toHaveTextContent('no-error');
      });

      // Clear error
      fireEvent.click(screen.getByText('Clear Error'));

      await waitFor(() => {
        expect(screen.getByTestId('error')).toHaveTextContent('no-error');
      });
    });
  });

  describe('CRUD Operations Integration', () => {
    it('should add new account via API', async () => {
      const newAccount = createMockAccount({
        id: 999,
        name: 'New Test Account',
        ebay_username: 'newtestaccount',
      });

      // Mock successful create
      server.use(
        rest.post('/api/accounts', (req, res, ctx) => {
          return res(ctx.status(201), ctx.json(newAccount));
        })
      );

      const TestCreateConsumer: React.FC = () => {
        const { accounts, addAccount } = useAccount();

        return (
          <div>
            <div data-testid="accounts-count">{accounts.length}</div>
            <button onClick={() => addAccount(newAccount)}>Add Account</button>
          </div>
        );
      };

      render(
        <TestWrapper>
          <TestCreateConsumer />
        </TestWrapper>
      );

      const initialCount = parseInt(screen.getByTestId('accounts-count').textContent || '0');

      // Add account
      fireEvent.click(screen.getByText('Add Account'));

      // Should increase account count
      await waitFor(() => {
        const newCount = parseInt(screen.getByTestId('accounts-count').textContent || '0');
        expect(newCount).toBe(initialCount + 1);
      });
    });

    it('should update existing account via API', async () => {
      const updatedAccount = createMockAccount({
        id: 1,
        name: 'Updated Account Name',
        ebay_username: 'updatedaccount',
      });

      // Mock successful update
      server.use(
        rest.put('/api/accounts/1', (req, res, ctx) => {
          return res(ctx.status(200), ctx.json(updatedAccount));
        })
      );

      const TestUpdateConsumer: React.FC = () => {
        const { accounts, updateAccount, fetchAccounts } = useAccount();

        return (
          <div>
            <button onClick={fetchAccounts}>Fetch Accounts</button>
            <button onClick={() => updateAccount(1, { name: 'Updated Account Name' })}>
              Update Account
            </button>
            <div data-testid="account-1-name">
              {accounts.find(a => a.id === 1)?.name || 'Not found'}
            </div>
          </div>
        );
      };

      render(
        <TestWrapper>
          <TestUpdateConsumer />
        </TestWrapper>
      );

      // Fetch accounts first
      fireEvent.click(screen.getByText('Fetch Accounts'));
      
      await waitFor(() => {
        expect(screen.getByTestId('account-1-name')).not.toHaveTextContent('Not found');
      });

      // Update account
      fireEvent.click(screen.getByText('Update Account'));

      // Should update account name
      await waitFor(() => {
        expect(screen.getByTestId('account-1-name')).toHaveTextContent('Updated Account Name');
      });
    });

    it('should delete account via API', async () => {
      // Mock successful delete
      server.use(
        rest.delete('/api/accounts/1', (req, res, ctx) => {
          return res(ctx.status(204));
        })
      );

      const TestDeleteConsumer: React.FC = () => {
        const { accounts, deleteAccount, fetchAccounts } = useAccount();

        return (
          <div>
            <button onClick={fetchAccounts}>Fetch Accounts</button>
            <button onClick={() => deleteAccount(1)}>Delete Account</button>
            <div data-testid="accounts-count">{accounts.length}</div>
            <div data-testid="account-1-exists">
              {accounts.find(a => a.id === 1) ? 'exists' : 'not-exists'}
            </div>
          </div>
        );
      };

      render(
        <TestWrapper>
          <TestDeleteConsumer />
        </TestWrapper>
      );

      // Fetch accounts first
      fireEvent.click(screen.getByText('Fetch Accounts'));
      
      await waitFor(() => {
        expect(screen.getByTestId('account-1-exists')).toHaveTextContent('exists');
      });

      const initialCount = parseInt(screen.getByTestId('accounts-count').textContent || '0');

      // Delete account
      fireEvent.click(screen.getByText('Delete Account'));

      // Should remove account
      await waitFor(() => {
        expect(screen.getByTestId('account-1-exists')).toHaveTextContent('not-exists');
      });

      const newCount = parseInt(screen.getByTestId('accounts-count').textContent || '0');
      expect(newCount).toBe(initialCount - 1);
    });
  });

  describe('Concurrent Operations Integration', () => {
    it('should handle concurrent API calls correctly', async () => {
      const TestConcurrentConsumer: React.FC = () => {
        const { accounts, fetchAccounts, loading } = useAccount();

        const handleMultipleFetches = () => {
          // Trigger multiple concurrent fetches
          fetchAccounts();
          fetchAccounts();
          fetchAccounts();
        };

        return (
          <div>
            <button onClick={handleMultipleFetches}>Multiple Fetches</button>
            <div data-testid="loading">{loading ? 'loading' : 'not-loading'}</div>
            <div data-testid="accounts-count">{accounts.length}</div>
          </div>
        );
      };

      render(
        <TestWrapper>
          <TestConcurrentConsumer />
        </TestWrapper>
      );

      // Trigger multiple concurrent fetches
      fireEvent.click(screen.getByText('Multiple Fetches'));

      // Should eventually resolve to stable state
      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('not-loading');
      });

      // Should have loaded accounts (not duplicated)
      expect(screen.getByTestId('accounts-count')).toHaveTextContent('3');
    });
  });

  describe('Memory Management Integration', () => {
    it('should cleanup subscriptions on unmount', async () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

      const { unmount } = render(
        <TestWrapper>
          <TestConsumer />
        </TestWrapper>
      );

      // Fetch data to create subscriptions
      fireEvent.click(screen.getByText('Fetch Accounts'));

      // Unmount component
      unmount();

      // Should not cause memory leaks or console errors
      expect(consoleSpy).not.toHaveBeenCalled();

      consoleSpy.mockRestore();
    });
  });
});