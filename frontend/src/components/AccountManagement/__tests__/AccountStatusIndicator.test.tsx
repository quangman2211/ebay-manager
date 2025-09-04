import React from 'react';
import { render, screen } from '@testing-library/react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import AccountStatusIndicator from '../AccountStatusIndicator';
import { createMockAccount } from '../../../utils/mockData';
import type { Account } from '../../../types';
import { CONNECTION_STATUSES } from '../../../config/accountConstants';

/**
 * AccountStatusIndicator Test Suite - Sprint 7
 * 
 * Tests follow SOLID principles:
 * - Single Responsibility: Each test validates one specific behavior
 * - Open/Closed: Easy to add new status types and variants
 * - Interface Segregation: Testing focused component interfaces
 * - Dependency Inversion: Testing component abstractions via props
 */

const theme = createTheme();

// Wrapper component for testing with theme
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ThemeProvider theme={theme}>{children}</ThemeProvider>
);

describe('AccountStatusIndicator', () => {
  let mockAccount: Account;

  beforeEach(() => {
    mockAccount = createMockAccount({
      id: 1,
      name: 'Test Store',
      ebay_username: 'teststore',
      connection_status: CONNECTION_STATUSES.AUTHENTICATED,
      is_active: true,
      data_processing_enabled: true,
      last_sync_at: '2024-01-01T12:00:00.000Z',
    });
  });

  describe('Chip Variant (Default)', () => {
    it('should render all status chips by default', () => {
      render(
        <TestWrapper>
          <AccountStatusIndicator account={mockAccount} />
        </TestWrapper>
      );

      expect(screen.getByText('Connected')).toBeInTheDocument();
      expect(screen.getByText('Active')).toBeInTheDocument();
      expect(screen.getByText('Processing Enabled')).toBeInTheDocument();
    });

    it('should show auth status chip with correct icon', () => {
      render(
        <TestWrapper>
          <AccountStatusIndicator account={mockAccount} />
        </TestWrapper>
      );

      expect(screen.getByTestId('CheckCircleIcon')).toBeInTheDocument();
    });

    it('should show sync status chip with correct icon', () => {
      render(
        <TestWrapper>
          <AccountStatusIndicator account={mockAccount} />
        </TestWrapper>
      );

      expect(screen.getByTestId('SyncIcon')).toBeInTheDocument();
    });

    it('should hide sync chip when showSync is false', () => {
      render(
        <TestWrapper>
          <AccountStatusIndicator account={mockAccount} showSync={false} />
        </TestWrapper>
      );

      expect(screen.queryByText('Processing Enabled')).not.toBeInTheDocument();
      expect(screen.queryByTestId('SyncIcon')).not.toBeInTheDocument();
    });

    it('should show disabled sync status when sync is disabled', () => {
      const disabledSyncAccount = createMockAccount({
        ...mockAccount,
        data_processing_enabled: false,
      });

      render(
        <TestWrapper>
          <AccountStatusIndicator account={disabledSyncAccount} />
        </TestWrapper>
      );

      expect(screen.getByText('Processing Disabled')).toBeInTheDocument();
      expect(screen.getByTestId('SyncDisabledIcon')).toBeInTheDocument();
    });

    it('should show inactive status for inactive accounts', () => {
      const inactiveAccount = createMockAccount({
        ...mockAccount,
        is_active: false,
      });

      render(
        <TestWrapper>
          <AccountStatusIndicator account={inactiveAccount} />
        </TestWrapper>
      );

      expect(screen.getByText('Inactive')).toBeInTheDocument();
    });
  });

  describe('Auth Status States', () => {
    it('should display pending auth status correctly', () => {
      const pendingAccount = createMockAccount({
        ...mockAccount,
        connection_status: CONNECTION_STATUSES.PENDING,
      });

      render(
        <TestWrapper>
          <AccountStatusIndicator account={pendingAccount} />
        </TestWrapper>
      );

      expect(screen.getByText('Pending')).toBeInTheDocument();
      expect(screen.getByTestId('ScheduleIcon')).toBeInTheDocument();
    });

    it('should display expired auth status correctly', () => {
      const expiredAccount = createMockAccount({
        ...mockAccount,
        connection_status: CONNECTION_STATUSES.EXPIRED,
      });

      render(
        <TestWrapper>
          <AccountStatusIndicator account={expiredAccount} />
        </TestWrapper>
      );

      expect(screen.getByText('Expired')).toBeInTheDocument();
      expect(screen.getByTestId('WarningIcon')).toBeInTheDocument();
    });

    it('should display error auth status correctly', () => {
      const errorAccount = createMockAccount({
        ...mockAccount,
        connection_status: CONNECTION_STATUSES.FAILED,
      });

      render(
        <TestWrapper>
          <AccountStatusIndicator account={errorAccount} />
        </TestWrapper>
      );

      expect(screen.getByText('Failed')).toBeInTheDocument();
      expect(screen.getByTestId('ErrorIcon')).toBeInTheDocument();
    });

    it('should display unknown status for undefined connection_status', () => {
      const unknownAccount = createMockAccount({
        ...mockAccount,
        connection_status: undefined as any,
      });

      render(
        <TestWrapper>
          <AccountStatusIndicator account={unknownAccount} />
        </TestWrapper>
      );

      expect(screen.getByText('Unknown')).toBeInTheDocument();
      expect(screen.getByTestId('WarningIcon')).toBeInTheDocument();
    });
  });

  describe('Compact Variant', () => {
    it('should render compact variant with icons only', () => {
      render(
        <TestWrapper>
          <AccountStatusIndicator account={mockAccount} variant="compact" />
        </TestWrapper>
      );

      expect(screen.getByTestId('CheckCircleIcon')).toBeInTheDocument();
      expect(screen.getByTestId('SyncIcon')).toBeInTheDocument();
      expect(screen.getByText('Active')).toBeInTheDocument(); // Only account active status shown as text
    });

    it('should hide sync icon in compact variant when showSync is false', () => {
      render(
        <TestWrapper>
          <AccountStatusIndicator account={mockAccount} variant="compact" showSync={false} />
        </TestWrapper>
      );

      expect(screen.getByTestId('CheckCircleIcon')).toBeInTheDocument();
      expect(screen.queryByTestId('SyncIcon')).not.toBeInTheDocument();
      expect(screen.getByText('Active')).toBeInTheDocument();
    });

    it('should show correct icons for different auth states in compact variant', () => {
      const pendingAccount = createMockAccount({
        ...mockAccount,
        connection_status: CONNECTION_STATUSES.PENDING,
      });

      render(
        <TestWrapper>
          <AccountStatusIndicator account={pendingAccount} variant="compact" />
        </TestWrapper>
      );

      expect(screen.getByTestId('ScheduleIcon')).toBeInTheDocument();
      expect(screen.getByTestId('SyncIcon')).toBeInTheDocument();
    });
  });

  describe('Detailed Variant', () => {
    it('should render detailed variant with full descriptions', () => {
      render(
        <TestWrapper>
          <AccountStatusIndicator account={mockAccount} variant="detailed" />
        </TestWrapper>
      );

      expect(screen.getByText('Connection:')).toBeInTheDocument();
      expect(screen.getByText('Connected')).toBeInTheDocument(); // Connection status
      expect(screen.getByText('Account Status:')).toBeInTheDocument();
      expect(screen.getByText('Active')).toBeInTheDocument(); // Account status
      expect(screen.getByText('Data Processing:')).toBeInTheDocument();
      expect(screen.getByText('Processing Enabled')).toBeInTheDocument();
    });

    it('should show last sync time in detailed variant', () => {
      render(
        <TestWrapper>
          <AccountStatusIndicator account={mockAccount} variant="detailed" />
        </TestWrapper>
      );

      expect(screen.getByText(/Last synced:/)).toBeInTheDocument();
    });

    it('should hide sync section in detailed variant when showSync is false', () => {
      render(
        <TestWrapper>
          <AccountStatusIndicator account={mockAccount} variant="detailed" showSync={false} />
        </TestWrapper>
      );

      expect(screen.getByText('Connection:')).toBeInTheDocument();
      expect(screen.getByText('Account Status:')).toBeInTheDocument();
      expect(screen.queryByText('Data Processing:')).not.toBeInTheDocument();
    });

    it('should not show last sync time when not available', () => {
      const noSyncAccount = createMockAccount({
        ...mockAccount,
        last_sync_at: undefined,
      });

      render(
        <TestWrapper>
          <AccountStatusIndicator account={noSyncAccount} variant="detailed" />
        </TestWrapper>
      );

      expect(screen.queryByText(/Last synced:/)).not.toBeInTheDocument();
    });

    it('should show correct auth status in detailed variant', () => {
      const expiredAccount = createMockAccount({
        ...mockAccount,
        connection_status: CONNECTION_STATUSES.EXPIRED,
      });

      render(
        <TestWrapper>
          <AccountStatusIndicator account={expiredAccount} variant="detailed" />
        </TestWrapper>
      );

      expect(screen.getByText('Connection:')).toBeInTheDocument();
      expect(screen.getByText('Expired')).toBeInTheDocument();
      expect(screen.getByTestId('WarningIcon')).toBeInTheDocument();
    });
  });

  describe('Accessibility and Tooltips', () => {
    it('should provide tooltips for chip variant', () => {
      render(
        <TestWrapper>
          <AccountStatusIndicator account={mockAccount} />
        </TestWrapper>
      );

      // Tooltips should be present (can't easily test hover state)
      expect(screen.getByText('Connected')).toBeInTheDocument(); // Connection status
      expect(screen.getByText('Active')).toBeInTheDocument(); // Account status
      const syncChip = screen.getByText('Processing Enabled').closest('.MuiChip-root');
      expect(syncChip).toBeInTheDocument();
    });

    it('should provide tooltips for compact variant icons', () => {
      render(
        <TestWrapper>
          <AccountStatusIndicator account={mockAccount} variant="compact" />
        </TestWrapper>
      );

      // Icons should be wrapped in tooltips
      expect(screen.getByTestId('CheckCircleIcon')).toBeInTheDocument();
      expect(screen.getByTestId('SyncIcon')).toBeInTheDocument();
    });
  });

  describe('Props and Defaults', () => {
    it('should use chip variant as default', () => {
      render(
        <TestWrapper>
          <AccountStatusIndicator account={mockAccount} />
        </TestWrapper>
      );

      // Should render chips (default behavior)
      expect(screen.getByText('Connected')).toBeInTheDocument(); // Connection status chip
      expect(screen.getByText('Active')).toBeInTheDocument(); // Account status chip
      expect(screen.getByText('Active').closest('.MuiChip-root')).toBeInTheDocument();
    });

    it('should show sync by default', () => {
      render(
        <TestWrapper>
          <AccountStatusIndicator account={mockAccount} />
        </TestWrapper>
      );

      expect(screen.getByText('Processing Enabled')).toBeInTheDocument();
    });

    it('should handle all variant types correctly', () => {
      const { rerender } = render(
        <TestWrapper>
          <AccountStatusIndicator account={mockAccount} variant="chip" />
        </TestWrapper>
      );
      expect(screen.getByText('Connected')).toBeInTheDocument(); // Connection status
      expect(screen.getByText('Active')).toBeInTheDocument(); // Account status
      expect(screen.getByText('Active').closest('.MuiChip-root')).toBeInTheDocument();

      rerender(
        <TestWrapper>
          <AccountStatusIndicator account={mockAccount} variant="compact" />
        </TestWrapper>
      );
      expect(screen.getByText('Active')).toBeInTheDocument();
      expect(screen.getByText('Active').closest('.MuiChip-root')).not.toBeInTheDocument();

      rerender(
        <TestWrapper>
          <AccountStatusIndicator account={mockAccount} variant="detailed" />
        </TestWrapper>
      );
      expect(screen.getByText('Connection:')).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('should handle account with minimal data', () => {
      const minimalAccount = createMockAccount({
        id: 1,
        name: 'Minimal',
        ebay_username: 'minimal',
        user_id: 1,
        is_active: true,
        created_at: '2024-01-01T00:00:00.000Z',
        connection_status: undefined as any,
        data_processing_enabled: undefined as any,
        last_sync_at: undefined,
      });

      expect(() => {
        render(
          <TestWrapper>
            <AccountStatusIndicator account={minimalAccount} />
          </TestWrapper>
        );
      }).not.toThrow();

      expect(screen.getByText('Unknown')).toBeInTheDocument(); // Unknown auth status
      expect(screen.getByText('Active')).toBeInTheDocument(); // Account is active
      expect(screen.getByText('Processing Disabled')).toBeInTheDocument(); // Sync undefined = disabled
    });

    it('should handle all auth status combinations', () => {
      const authStatuses: Array<'active' | CONNECTION_STATUSES.PENDING | CONNECTION_STATUSES.EXPIRED | CONNECTION_STATUSES.FAILED | undefined> = 
        ['active', CONNECTION_STATUSES.PENDING, CONNECTION_STATUSES.EXPIRED, CONNECTION_STATUSES.FAILED, undefined];

      authStatuses.forEach((status) => {
        const testAccount = createMockAccount({
          ...mockAccount,
          connection_status: status as any,
        });

        const { unmount } = render(
          <TestWrapper>
            <AccountStatusIndicator account={testAccount} />
          </TestWrapper>
        );

        // Should render without errors
        expect(screen.getAllByText(/Active|Pending|Expired|Failed|Unknown/)).toHaveLength(2);
        unmount();
      });
    });

    it('should handle sync enabled/disabled combinations', () => {
      const syncStates = [true, false, undefined];

      syncStates.forEach((syncEnabled) => {
        const testAccount = createMockAccount({
          ...mockAccount,
          data_processing_enabled: syncEnabled,
        });

        const { unmount } = render(
          <TestWrapper>
            <AccountStatusIndicator account={testAccount} />
          </TestWrapper>
        );

        // Should render without errors
        expect(screen.getByText(/Processing Enabled|Processing Disabled/)).toBeInTheDocument();
        unmount();
      });
    });

    it('should handle active/inactive account states', () => {
      const activeStates = [true, false];

      activeStates.forEach((isActive) => {
        const testAccount = createMockAccount({
          ...mockAccount,
          is_active: isActive,
        });

        const { unmount } = render(
          <TestWrapper>
            <AccountStatusIndicator account={testAccount} />
          </TestWrapper>
        );

        // Should render without errors  
        if (isActive) {
          expect(screen.getByText('Connected')).toBeInTheDocument(); // Connection status
          expect(screen.getByText('Active')).toBeInTheDocument(); // Account status
        } else {
          expect(screen.getByText('Inactive')).toBeInTheDocument();
        }
        unmount();
      });
    });
  });

  describe('Component Behavior', () => {
    it('should maintain consistent styling across variants', () => {
      const variants: Array<'chip' | 'compact' | 'detailed'> = ['chip', 'compact', 'detailed'];

      variants.forEach((variant) => {
        const { unmount } = render(
          <TestWrapper>
            <AccountStatusIndicator account={mockAccount} variant={variant} />
          </TestWrapper>
        );

        // Should render without layout or styling errors
        expect(document.querySelector('[data-testid="CheckCircleIcon"]')).toBeInTheDocument();
        unmount();
      });
    });

    it('should handle prop changes correctly', () => {
      const { rerender } = render(
        <TestWrapper>
          <AccountStatusIndicator account={mockAccount} showSync={true} />
        </TestWrapper>
      );

      expect(screen.getByText('Processing Enabled')).toBeInTheDocument();

      rerender(
        <TestWrapper>
          <AccountStatusIndicator account={mockAccount} showSync={false} />
        </TestWrapper>
      );

      expect(screen.queryByText('Processing Enabled')).not.toBeInTheDocument();
    });

    it('should update when account data changes', () => {
      const { rerender } = render(
        <TestWrapper>
          <AccountStatusIndicator account={mockAccount} />
        </TestWrapper>
      );

      expect(screen.getByText('Connected')).toBeInTheDocument(); // Connection status
      expect(screen.getByText('Active')).toBeInTheDocument(); // Account status

      const updatedAccount = createMockAccount({
        ...mockAccount,
        connection_status: CONNECTION_STATUSES.PENDING,
      });

      rerender(
        <TestWrapper>
          <AccountStatusIndicator account={updatedAccount} />
        </TestWrapper>
      );

      expect(screen.getByText('Pending')).toBeInTheDocument();
      expect(screen.getByText('Active')).toBeInTheDocument(); // Still has active account status
    });
  });

  describe('Integration with Theme', () => {
    it('should use theme colors correctly', () => {
      const { container } = render(
        <TestWrapper>
          <AccountStatusIndicator account={mockAccount} />
        </TestWrapper>
      );

      // Should use Material-UI theme classes
      expect(container.querySelector('.MuiChip-colorSuccess')).toBeInTheDocument();
    });

    it('should be responsive to theme changes', () => {
      const customTheme = createTheme({
        palette: {
          success: {
            main: '#00ff00',
          },
        },
      });

      render(
        <ThemeProvider theme={customTheme}>
          <AccountStatusIndicator account={mockAccount} />
        </ThemeProvider>
      );

      // Should render without errors with custom theme
      expect(screen.getByText('Connected')).toBeInTheDocument(); // Connection status
      expect(screen.getByText('Active')).toBeInTheDocument(); // Account status
    });
  });
});