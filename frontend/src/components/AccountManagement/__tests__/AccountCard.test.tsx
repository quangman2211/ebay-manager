import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import AccountCard from '../AccountCard';
import { createMockAccount } from '../../../utils/mockData';
import type { Account } from '../../../types';
import { CONNECTION_STATUSES, PLATFORMS } from '../../../config/accountConstants';

/**
 * AccountCard Test Suite - Sprint 7
 * 
 * Tests follow SOLID principles:
 * - Single Responsibility: Each test validates one specific behavior
 * - Open/Closed: Easy to add new test scenarios
 * - Interface Segregation: Testing focused component interfaces
 * - Dependency Inversion: Testing component abstractions via props
 */

const theme = createTheme();

// Wrapper component for testing with theme
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ThemeProvider theme={theme}>{children}</ThemeProvider>
);

describe('AccountCard', () => {
  let mockAccount: Account;
  let mockOnEdit: jest.Mock;
  let mockOnSettings: jest.Mock;
  let mockOnSelect: jest.Mock;

  beforeEach(() => {
    mockAccount = createMockAccount({
      id: 1,
      name: 'Test Store',
      ebay_username: 'teststore',
      connection_status: CONNECTION_STATUSES.AUTHENTICATED,
      is_active: true,
      account_type: PLATFORMS.EBAY,
      data_processing_enabled: true,
    });

    mockOnEdit = jest.fn();
    mockOnSettings = jest.fn();
    mockOnSelect = jest.fn();
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('Component Rendering', () => {
    it('should render account information correctly', () => {
      render(
        <TestWrapper>
          <AccountCard
            account={mockAccount}
            onEdit={mockOnEdit}
            onSettings={mockOnSettings}
            onSelect={mockOnSelect}
          />
        </TestWrapper>
      );

      expect(screen.getByText('Test Store')).toBeInTheDocument();
      expect(screen.getByText('@teststore')).toBeInTheDocument();
      expect(screen.getByText('ebay')).toBeInTheDocument();
    });

    it('should display auth status and activity status chips', () => {
      render(
        <TestWrapper>
          <AccountCard
            account={mockAccount}
            onEdit={mockOnEdit}
            onSettings={mockOnSettings}
            onSelect={mockOnSelect}
          />
        </TestWrapper>
      );

      expect(screen.getByText('Connected')).toBeInTheDocument(); // Connection status
      expect(screen.getByText('Active')).toBeInTheDocument(); // Activity status
    });

    it('should render action buttons', () => {
      render(
        <TestWrapper>
          <AccountCard
            account={mockAccount}
            onEdit={mockOnEdit}
            onSettings={mockOnSettings}
            onSelect={mockOnSelect}
          />
        </TestWrapper>
      );

      expect(screen.getByLabelText('Edit Account')).toBeInTheDocument();
      expect(screen.getByLabelText('Account Settings')).toBeInTheDocument();
      expect(screen.getByText('View Details')).toBeInTheDocument();
      expect(screen.getByText('Settings')).toBeInTheDocument();
    });

    it('should show sync status information', () => {
      render(
        <TestWrapper>
          <AccountCard
            account={mockAccount}
            onEdit={mockOnEdit}
            onSettings={mockOnSettings}
            onSelect={mockOnSelect}
          />
        </TestWrapper>
      );

      expect(screen.getByText('Processing Enabled')).toBeInTheDocument();
      expect(screen.getByTestId('SyncIcon')).toBeInTheDocument();
    });

    it('should show sync disabled when sync is disabled', () => {
      const syncDisabledAccount = createMockAccount({
        ...mockAccount,
        data_processing_enabled: false,
      });

      render(
        <TestWrapper>
          <AccountCard
            account={syncDisabledAccount}
            onEdit={mockOnEdit}
            onSettings={mockOnSettings}
            onSelect={mockOnSelect}
          />
        </TestWrapper>
      );

      expect(screen.getByText('Processing Disabled')).toBeInTheDocument();
      expect(screen.getByTestId('SyncDisabledIcon')).toBeInTheDocument();
    });

    it('should display account initials in avatar', () => {
      render(
        <TestWrapper>
          <AccountCard
            account={mockAccount}
            onEdit={mockOnEdit}
            onSettings={mockOnSettings}
            onSelect={mockOnSelect}
          />
        </TestWrapper>
      );

      expect(screen.getByText('TS')).toBeInTheDocument(); // Test Store -> TS
    });
  });

  describe('Auth Status Display', () => {
    it('should display capitalized auth status for active', () => {
      const activeAccount = createMockAccount({
        ...mockAccount,
        connection_status: CONNECTION_STATUSES.AUTHENTICATED,
      });

      render(
        <TestWrapper>
          <AccountCard
            account={activeAccount}
            onEdit={mockOnEdit}
            onSettings={mockOnSettings}
            onSelect={mockOnSelect}
          />
        </TestWrapper>
      );

      expect(screen.getByText('Connected')).toBeInTheDocument(); // Connection status
      expect(screen.getByText('Active')).toBeInTheDocument(); // Activity status
    });

    it('should display capitalized auth status for pending', () => {
      const pendingAccount = createMockAccount({
        ...mockAccount,
        connection_status: CONNECTION_STATUSES.PENDING,
      });

      render(
        <TestWrapper>
          <AccountCard
            account={pendingAccount}
            onEdit={mockOnEdit}
            onSettings={mockOnSettings}
            onSelect={mockOnSelect}
          />
        </TestWrapper>
      );

      expect(screen.getByText('Pending')).toBeInTheDocument();
    });

    it('should display capitalized auth status for expired', () => {
      const expiredAccount = createMockAccount({
        ...mockAccount,
        connection_status: CONNECTION_STATUSES.EXPIRED,
      });

      render(
        <TestWrapper>
          <AccountCard
            account={expiredAccount}
            onEdit={mockOnEdit}
            onSettings={mockOnSettings}
            onSelect={mockOnSelect}
          />
        </TestWrapper>
      );

      expect(screen.getByText('Expired')).toBeInTheDocument();
    });

    it('should display Unknown for undefined auth status', () => {
      const undefinedStatusAccount = createMockAccount({
        ...mockAccount,
        connection_status: undefined as any,
      });

      render(
        <TestWrapper>
          <AccountCard
            account={undefinedStatusAccount}
            onEdit={mockOnEdit}
            onSettings={mockOnSettings}
            onSelect={mockOnSelect}
          />
        </TestWrapper>
      );

      expect(screen.getByText('Unknown')).toBeInTheDocument();
    });
  });

  describe('User Interactions', () => {
    it('should call onEdit when edit button is clicked', () => {
      render(
        <TestWrapper>
          <AccountCard
            account={mockAccount}
            onEdit={mockOnEdit}
            onSettings={mockOnSettings}
            onSelect={mockOnSelect}
          />
        </TestWrapper>
      );

      fireEvent.click(screen.getByLabelText('Edit Account'));
      expect(mockOnEdit).toHaveBeenCalledWith(mockAccount);
      expect(mockOnEdit).toHaveBeenCalledTimes(1);
    });

    it('should call onSettings when settings icon button is clicked', () => {
      render(
        <TestWrapper>
          <AccountCard
            account={mockAccount}
            onEdit={mockOnEdit}
            onSettings={mockOnSettings}
            onSelect={mockOnSelect}
          />
        </TestWrapper>
      );

      fireEvent.click(screen.getByLabelText('Account Settings'));
      expect(mockOnSettings).toHaveBeenCalledWith(mockAccount);
      expect(mockOnSettings).toHaveBeenCalledTimes(1);
    });

    it('should call onSettings when Settings button is clicked', () => {
      render(
        <TestWrapper>
          <AccountCard
            account={mockAccount}
            onEdit={mockOnEdit}
            onSettings={mockOnSettings}
            onSelect={mockOnSelect}
          />
        </TestWrapper>
      );

      fireEvent.click(screen.getByText('Settings'));
      expect(mockOnSettings).toHaveBeenCalledWith(mockAccount);
      expect(mockOnSettings).toHaveBeenCalledTimes(1);
    });

    it('should call onSelect when View Details button is clicked', () => {
      render(
        <TestWrapper>
          <AccountCard
            account={mockAccount}
            onEdit={mockOnEdit}
            onSettings={mockOnSettings}
            onSelect={mockOnSelect}
          />
        </TestWrapper>
      );

      fireEvent.click(screen.getByText('View Details'));
      expect(mockOnSelect).toHaveBeenCalledWith(mockAccount);
      expect(mockOnSelect).toHaveBeenCalledTimes(1);
    });

    it('should call onSelect when card is clicked', () => {
      render(
        <TestWrapper>
          <AccountCard
            account={mockAccount}
            onEdit={mockOnEdit}
            onSettings={mockOnSettings}
            onSelect={mockOnSelect}
          />
        </TestWrapper>
      );

      fireEvent.click(screen.getByText('Test Store'));
      expect(mockOnSelect).toHaveBeenCalledWith(mockAccount);
      expect(mockOnSelect).toHaveBeenCalledTimes(1);
    });

    it('should prevent event bubbling when icon buttons are clicked', () => {
      render(
        <TestWrapper>
          <AccountCard
            account={mockAccount}
            onEdit={mockOnEdit}
            onSettings={mockOnSettings}
            onSelect={mockOnSelect}
          />
        </TestWrapper>
      );

      fireEvent.click(screen.getByLabelText('Edit Account'));
      expect(mockOnEdit).toHaveBeenCalledTimes(1);
      expect(mockOnSelect).toHaveBeenCalledTimes(0); // Should not be called due to stopPropagation
    });
  });

  describe('Selection State', () => {
    it('should apply selected styling when isSelected is true', () => {
      const { container } = render(
        <TestWrapper>
          <AccountCard
            account={mockAccount}
            onEdit={mockOnEdit}
            onSettings={mockOnSettings}
            onSelect={mockOnSelect}
            isSelected={true}
          />
        </TestWrapper>
      );

      const card = container.querySelector('.MuiCard-root');
      expect(card).toHaveStyle('border-width: 2px');
    });

    it('should not apply selected styling when isSelected is false', () => {
      const { container } = render(
        <TestWrapper>
          <AccountCard
            account={mockAccount}
            onEdit={mockOnEdit}
            onSettings={mockOnSettings}
            onSelect={mockOnSelect}
            isSelected={false}
          />
        </TestWrapper>
      );

      const card = container.querySelector('.MuiCard-root');
      expect(card).toHaveStyle('border-width: 1px');
    });

    it('should default isSelected to false when not provided', () => {
      const { container } = render(
        <TestWrapper>
          <AccountCard
            account={mockAccount}
            onEdit={mockOnEdit}
            onSettings={mockOnSettings}
            onSelect={mockOnSelect}
          />
        </TestWrapper>
      );

      const card = container.querySelector('.MuiCard-root');
      expect(card).toHaveStyle('border-width: 1px');
    });
  });

  describe('Account Types and States', () => {
    it('should display personal account type correctly', () => {
      const personalAccount = createMockAccount({
        ...mockAccount,
        account_type: PLATFORMS.EBAY,
      });

      render(
        <TestWrapper>
          <AccountCard
            account={personalAccount}
            onEdit={mockOnEdit}
            onSettings={mockOnSettings}
            onSelect={mockOnSelect}
          />
        </TestWrapper>
      );

      expect(screen.getByText('ebay')).toBeInTheDocument();
    });

    it('should display Inactive status for inactive accounts', () => {
      const inactiveAccount = createMockAccount({
        ...mockAccount,
        is_active: false,
      });

      render(
        <TestWrapper>
          <AccountCard
            account={inactiveAccount}
            onEdit={mockOnEdit}
            onSettings={mockOnSettings}
            onSelect={mockOnSelect}
          />
        </TestWrapper>
      );

      expect(screen.getByText('Inactive')).toBeInTheDocument();
    });

    it('should handle missing account_type gracefully', () => {
      const noTypeAccount = createMockAccount({
        ...mockAccount,
        account_type: undefined as any,
      });

      render(
        <TestWrapper>
          <AccountCard
            account={noTypeAccount}
            onEdit={mockOnEdit}
            onSettings={mockOnSettings}
            onSelect={mockOnSelect}
          />
        </TestWrapper>
      );

      expect(screen.getByText('eBay')).toBeInTheDocument(); // Default fallback
    });
  });

  describe('Sync Information Display', () => {
    it('should display last sync date when available', () => {
      const syncedAccount = createMockAccount({
        ...mockAccount,
        last_sync_at: '2024-01-01T12:00:00.000Z',
      });

      render(
        <TestWrapper>
          <AccountCard
            account={syncedAccount}
            onEdit={mockOnEdit}
            onSettings={mockOnSettings}
            onSelect={mockOnSelect}
          />
        </TestWrapper>
      );

      expect(screen.getByText(/Last sync:/)).toBeInTheDocument();
    });

    it('should not display sync info when last_sync_at is undefined', () => {
      const neverSyncedAccount = createMockAccount({
        ...mockAccount,
        last_sync_at: undefined,
      });

      render(
        <TestWrapper>
          <AccountCard
            account={neverSyncedAccount}
            onEdit={mockOnEdit}
            onSettings={mockOnSettings}
            onSelect={mockOnSelect}
          />
        </TestWrapper>
      );

      expect(screen.queryByText(/Last sync:/)).not.toBeInTheDocument();
    });
  });

  describe('Performance Metrics', () => {
    it('should show performance data indicator when metrics are available', () => {
      const metricsAccount = createMockAccount({
        ...mockAccount,
        performance_metrics: { revenue: 1000, orders: 50 },
      });

      render(
        <TestWrapper>
          <AccountCard
            account={metricsAccount}
            onEdit={mockOnEdit}
            onSettings={mockOnSettings}
            onSelect={mockOnSelect}
          />
        </TestWrapper>
      );

      expect(screen.getByText('Performance Data Available')).toBeInTheDocument();
    });

    it('should not show performance indicator when metrics are empty', () => {
      const noMetricsAccount = createMockAccount({
        ...mockAccount,
        performance_metrics: {},
      });

      render(
        <TestWrapper>
          <AccountCard
            account={noMetricsAccount}
            onEdit={mockOnEdit}
            onSettings={mockOnSettings}
            onSelect={mockOnSelect}
          />
        </TestWrapper>
      );

      expect(screen.queryByText('Performance Data Available')).not.toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA labels for icon buttons', () => {
      render(
        <TestWrapper>
          <AccountCard
            account={mockAccount}
            onEdit={mockOnEdit}
            onSettings={mockOnSettings}
            onSelect={mockOnSelect}
          />
        </TestWrapper>
      );

      expect(screen.getByLabelText('Edit Account')).toBeInTheDocument();
      expect(screen.getByLabelText('Account Settings')).toBeInTheDocument();
    });

    it('should support keyboard navigation', () => {
      render(
        <TestWrapper>
          <AccountCard
            account={mockAccount}
            onEdit={mockOnEdit}
            onSettings={mockOnSettings}
            onSelect={mockOnSelect}
          />
        </TestWrapper>
      );

      const editButton = screen.getByLabelText('Edit Account');
      editButton.focus();
      expect(editButton).toHaveFocus();

      // Click should work for icon buttons (keyDown doesn't trigger onClick for IconButton)
      fireEvent.click(editButton);
      expect(mockOnEdit).toHaveBeenCalledWith(mockAccount);
    });
  });

  describe('Edge Cases', () => {
    it('should handle very long account names gracefully', () => {
      const longNameAccount = createMockAccount({
        ...mockAccount,
        name: 'This is a very long account name that might cause layout issues if not handled properly',
      });

      render(
        <TestWrapper>
          <AccountCard
            account={longNameAccount}
            onEdit={mockOnEdit}
            onSettings={mockOnSettings}
            onSelect={mockOnSelect}
          />
        </TestWrapper>
      );

      expect(screen.getByText('This is a very long account name that might cause layout issues if not handled properly')).toBeInTheDocument();
    });

    it('should handle special characters in names', () => {
      const specialCharAccount = createMockAccount({
        ...mockAccount,
        name: 'Store & Co. (Main)',
        ebay_username: 'store-co_main',
      });

      render(
        <TestWrapper>
          <AccountCard
            account={specialCharAccount}
            onEdit={mockOnEdit}
            onSettings={mockOnSettings}
            onSelect={mockOnSelect}
          />
        </TestWrapper>
      );

      expect(screen.getByText('Store & Co. (Main)')).toBeInTheDocument();
      expect(screen.getByText('@store-co_main')).toBeInTheDocument();
    });

    it('should generate correct initials for single word names', () => {
      const singleWordAccount = createMockAccount({
        ...mockAccount,
        name: 'Amazon',
      });

      render(
        <TestWrapper>
          <AccountCard
            account={singleWordAccount}
            onEdit={mockOnEdit}
            onSettings={mockOnSettings}
            onSelect={mockOnSelect}
          />
        </TestWrapper>
      );

      expect(screen.getByText('A')).toBeInTheDocument(); // Single initial
    });

    it('should generate correct initials for multiple word names', () => {
      const multiWordAccount = createMockAccount({
        ...mockAccount,
        name: 'Super Awesome Store Company',
      });

      render(
        <TestWrapper>
          <AccountCard
            account={multiWordAccount}
            onEdit={mockOnEdit}
            onSettings={mockOnSettings}
            onSelect={mockOnSelect}
          />
        </TestWrapper>
      );

      expect(screen.getByText('SA')).toBeInTheDocument(); // First two initials
    });
  });

  describe('Component Props Validation', () => {
    it('should handle all callback functions correctly', () => {
      const callbackTests = {
        onEdit: jest.fn(),
        onSettings: jest.fn(),
        onSelect: jest.fn(),
      };

      render(
        <TestWrapper>
          <AccountCard
            account={mockAccount}
            {...callbackTests}
          />
        </TestWrapper>
      );

      // Test edit callback
      fireEvent.click(screen.getByLabelText('Edit Account'));
      expect(callbackTests.onEdit).toHaveBeenCalledWith(mockAccount);

      // Test settings callbacks (both icon and button)
      fireEvent.click(screen.getByLabelText('Account Settings'));
      expect(callbackTests.onSettings).toHaveBeenCalledWith(mockAccount);

      fireEvent.click(screen.getByText('Settings'));
      expect(callbackTests.onSettings).toHaveBeenCalledTimes(2);

      // Test select callback
      fireEvent.click(screen.getByText('View Details'));
      expect(callbackTests.onSelect).toHaveBeenCalledWith(mockAccount);
    });

    it('should render without errors with minimal account data', () => {
      const minimalAccount = createMockAccount({
        id: 1,
        name: 'Minimal',
        ebay_username: 'minimal',
        user_id: 1,
        is_active: true,
        created_at: '2024-01-01T00:00:00.000Z',
      });

      expect(() => {
        render(
          <TestWrapper>
            <AccountCard
              account={minimalAccount}
              onEdit={mockOnEdit}
              onSettings={mockOnSettings}
              onSelect={mockOnSelect}
            />
          </TestWrapper>
        );
      }).not.toThrow();

      expect(screen.getByText('Minimal')).toBeInTheDocument();
      expect(screen.getByText('@minimal')).toBeInTheDocument();
    });
  });
});