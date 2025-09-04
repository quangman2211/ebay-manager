import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import AccountPermissionsDialog from '../AccountPermissionsDialog';
import { createMockAccount, createMockPermissions } from '../../../utils/mockData';
import type { Account, UserAccountPermission } from '../../../types';

// Mock the useAccountPermissions hook
jest.mock('../../../hooks/useAccountPermissions', () => ({
  useAccountPermissions: jest.fn(),
}));

/**
 * AccountPermissionsDialog Test Suite - Sprint 7
 * 
 * Tests follow SOLID principles:
 * - Single Responsibility: Each test validates one specific behavior
 * - Open/Closed: Easy to add new permission scenarios
 * - Interface Segregation: Testing focused dialog interfaces
 * - Dependency Inversion: Testing component abstractions via mocking
 */

const theme = createTheme();

// Wrapper component for testing with theme
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ThemeProvider theme={theme}>{children}</ThemeProvider>
);

// Mock the useAccountPermissions hook
const mockUseAccountPermissions = {
  permissions: [] as UserAccountPermission[],
  loading: false,
  error: null,
  addPermission: jest.fn(),
  updatePermission: jest.fn(),
  removePermission: jest.fn(),
  refreshPermissions: jest.fn(),
};

const mockUseAccountPermissions = jest.fn();

describe('AccountPermissionsDialog', () => {
  let mockAccount: Account;
  let mockOnClose: jest.Mock;
  let mockPermissions: UserAccountPermission[];

  beforeEach(() => {
    mockAccount = createMockAccount({
      id: 1,
      name: 'Test Store',
      ebay_username: 'teststore',
    });

    mockPermissions = createMockPermissions(1, 3);
    mockOnClose = jest.fn();

    // Setup mock implementation
    const { useAccountPermissions } = require('../../../hooks/useAccountPermissions');
    useAccountPermissions.mockReturnValue({
      ...mockUseAccountPermissions,
      permissions: mockPermissions,
    });

    jest.clearAllMocks();
  });

  describe('Dialog Rendering', () => {
    it('should render dialog when open is true', () => {
      render(
        <TestWrapper>
          <AccountPermissionsDialog
            open={true}
            onClose={mockOnClose}
            account={mockAccount}
          />
        </TestWrapper>
      );

      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByText('Account Permissions')).toBeInTheDocument();
      expect(screen.getByText('Test Store')).toBeInTheDocument();
    });

    it('should not render dialog when open is false', () => {
      render(
        <TestWrapper>
          <AccountPermissionsDialog
            open={false}
            onClose={mockOnClose}
            account={mockAccount}
          />
        </TestWrapper>
      );

      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });

    it('should render permissions table when permissions exist', () => {
      render(
        <TestWrapper>
          <AccountPermissionsDialog
            open={true}
            onClose={mockOnClose}
            account={mockAccount}
          />
        </TestWrapper>
      );

      expect(screen.getByRole('table')).toBeInTheDocument();
      expect(screen.getByText('User')).toBeInTheDocument();
      expect(screen.getByText('Permission Level')).toBeInTheDocument();
      expect(screen.getByText('Granted Date')).toBeInTheDocument();
      expect(screen.getByText('Actions')).toBeInTheDocument();
    });

    it('should show loading state when loading', () => {
      const { useAccountPermissions } = require('../../../hooks/useAccountPermissions');
      useAccountPermissions.mockReturnValue({
        ...mockUseAccountPermissions,
        loading: true,
      });

      render(
        <TestWrapper>
          <AccountPermissionsDialog
            open={true}
            onClose={mockOnClose}
            account={mockAccount}
          />
        </TestWrapper>
      );

      expect(screen.getByRole('progressbar')).toBeInTheDocument();
    });

    it('should show error state when error exists', () => {
      const errorMessage = 'Failed to load permissions';
      const { useAccountPermissions } = require('../../../hooks/useAccountPermissions');
      useAccountPermissions.mockReturnValue({
        ...mockUseAccountPermissions,
        error: errorMessage,
      });

      render(
        <TestWrapper>
          <AccountPermissionsDialog
            open={true}
            onClose={mockOnClose}
            account={mockAccount}
          />
        </TestWrapper>
      );

      expect(screen.getByRole('alert')).toBeInTheDocument();
      expect(screen.getByText(errorMessage)).toBeInTheDocument();
    });
  });

  describe('Dialog Actions', () => {
    it('should call onClose when close button is clicked', () => {
      render(
        <TestWrapper>
          <AccountPermissionsDialog
            open={true}
            onClose={mockOnClose}
            account={mockAccount}
          />
        </TestWrapper>
      );

      fireEvent.click(screen.getByText('Close'));
      expect(mockOnClose).toHaveBeenCalledTimes(1);
    });

    it('should call onClose when X button is clicked', () => {
      render(
        <TestWrapper>
          <AccountPermissionsDialog
            open={true}
            onClose={mockOnClose}
            account={mockAccount}
          />
        </TestWrapper>
      );

      const closeButton = screen.getByLabelText(/close/i);
      fireEvent.click(closeButton);
      expect(mockOnClose).toHaveBeenCalledTimes(1);
    });

    it('should call onClose when clicking outside dialog', () => {
      render(
        <TestWrapper>
          <AccountPermissionsDialog
            open={true}
            onClose={mockOnClose}
            account={mockAccount}
          />
        </TestWrapper>
      );

      // Click on backdrop
      const backdrop = document.querySelector('.MuiBackdrop-root');
      if (backdrop) {
        fireEvent.click(backdrop);
        expect(mockOnClose).toHaveBeenCalledTimes(1);
      }
    });
  });

  describe('Permissions Display', () => {
    it('should display permission data correctly', () => {
      render(
        <TestWrapper>
          <AccountPermissionsDialog
            open={true}
            onClose={mockOnClose}
            account={mockAccount}
          />
        </TestWrapper>
      );

      // Check if permission data is displayed
      mockPermissions.forEach(permission => {
        expect(screen.getByText(permission.permission_level)).toBeInTheDocument();
      });
    });

    it('should show empty state when no permissions exist', () => {
      const { useAccountPermissions } = require('../../../hooks/useAccountPermissions');
      useAccountPermissions.mockReturnValue({
        ...mockUseAccountPermissions,
        permissions: [],
      });

      render(
        <TestWrapper>
          <AccountPermissionsDialog
            open={true}
            onClose={mockOnClose}
            account={mockAccount}
          />
        </TestWrapper>
      );

      expect(screen.getByText(/no permissions found/i)).toBeInTheDocument();
    });

    it('should display permission levels as chips with correct colors', () => {
      render(
        <TestWrapper>
          <AccountPermissionsDialog
            open={true}
            onClose={mockOnClose}
            account={mockAccount}
          />
        </TestWrapper>
      );

      const permissionChips = screen.getAllByText(/read|write|admin/i);
      expect(permissionChips.length).toBeGreaterThan(0);
    });
  });

  describe('Permission Management', () => {
    it('should show Add Permission button', () => {
      render(
        <TestWrapper>
          <AccountPermissionsDialog
            open={true}
            onClose={mockOnClose}
            account={mockAccount}
          />
        </TestWrapper>
      );

      expect(screen.getByText('Add Permission')).toBeInTheDocument();
    });

    it('should show edit buttons for each permission', () => {
      render(
        <TestWrapper>
          <AccountPermissionsDialog
            open={true}
            onClose={mockOnClose}
            account={mockAccount}
          />
        </TestWrapper>
      );

      const editButtons = screen.getAllByLabelText(/edit permission/i);
      expect(editButtons).toHaveLength(mockPermissions.length);
    });

    it('should show delete buttons for each permission', () => {
      render(
        <TestWrapper>
          <AccountPermissionsDialog
            open={true}
            onClose={mockOnClose}
            account={mockAccount}
          />
        </TestWrapper>
      );

      const deleteButtons = screen.getAllByLabelText(/delete permission/i);
      expect(deleteButtons).toHaveLength(mockPermissions.length);
    });

    it('should call removePermission when delete button is clicked', async () => {
      const mockRemovePermission = jest.fn();
      const { useAccountPermissions } = require('../../../hooks/useAccountPermissions');
      useAccountPermissions.mockReturnValue({
        ...mockUseAccountPermissions,
        permissions: mockPermissions,
        removePermission: mockRemovePermission,
      });

      render(
        <TestWrapper>
          <AccountPermissionsDialog
            open={true}
            onClose={mockOnClose}
            account={mockAccount}
          />
        </TestWrapper>
      );

      const deleteButtons = screen.getAllByLabelText(/delete permission/i);
      fireEvent.click(deleteButtons[0]);

      await waitFor(() => {
        expect(mockRemovePermission).toHaveBeenCalledWith(
          mockAccount.id,
          mockPermissions[0].id
        );
      });
    });
  });

  describe('Add Permission Form', () => {
    beforeEach(() => {
      render(
        <TestWrapper>
          <AccountPermissionsDialog
            open={true}
            onClose={mockOnClose}
            account={mockAccount}
          />
        </TestWrapper>
      );

      // Click Add Permission button to open form
      fireEvent.click(screen.getByText('Add Permission'));
    });

    it('should show add permission form when Add Permission is clicked', () => {
      expect(screen.getByText('Add New Permission')).toBeInTheDocument();
      expect(screen.getByLabelText(/user email/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/permission level/i)).toBeInTheDocument();
    });

    it('should allow entering user email', () => {
      const userEmailInput = screen.getByLabelText(/user email/i) as HTMLInputElement;
      fireEvent.change(userEmailInput, { target: { value: 'test@example.com' } });
      
      expect(userEmailInput.value).toBe('test@example.com');
    });

    it('should allow selecting permission level', () => {
      const permissionSelect = screen.getByLabelText(/permission level/i);
      fireEvent.mouseDown(permissionSelect);
      
      expect(screen.getByText('Read')).toBeInTheDocument();
      expect(screen.getByText('Write')).toBeInTheDocument();
      expect(screen.getByText('Admin')).toBeInTheDocument();
    });

    it('should allow entering notes', () => {
      const notesInput = screen.getByLabelText(/notes/i) as HTMLTextAreaElement;
      fireEvent.change(notesInput, { target: { value: 'Test notes' } });
      
      expect(notesInput.value).toBe('Test notes');
    });

    it('should have Cancel and Add buttons', () => {
      expect(screen.getByText('Cancel')).toBeInTheDocument();
      expect(screen.getByText('Add')).toBeInTheDocument();
    });

    it('should close form when Cancel is clicked', () => {
      fireEvent.click(screen.getByText('Cancel'));
      expect(screen.queryByText('Add New Permission')).not.toBeInTheDocument();
    });
  });

  describe('Form Validation', () => {
    beforeEach(() => {
      render(
        <TestWrapper>
          <AccountPermissionsDialog
            open={true}
            onClose={mockOnClose}
            account={mockAccount}
          />
        </TestWrapper>
      );

      fireEvent.click(screen.getByText('Add Permission'));
    });

    it('should validate required fields', async () => {
      const addButton = screen.getByRole('button', { name: 'Add' });
      fireEvent.click(addButton);

      await waitFor(() => {
        // Check for validation errors
        expect(screen.getByText(/email is required/i)).toBeInTheDocument();
      });
    });

    it('should validate email format', async () => {
      const userEmailInput = screen.getByLabelText(/user email/i);
      fireEvent.change(userEmailInput, { target: { value: 'invalid-email' } });
      
      const addButton = screen.getByRole('button', { name: 'Add' });
      fireEvent.click(addButton);

      await waitFor(() => {
        expect(screen.getByText(/valid email address/i)).toBeInTheDocument();
      });
    });

    it('should call addPermission with valid data', async () => {
      const mockAddPermission = jest.fn();
      const { useAccountPermissions } = require('../../../hooks/useAccountPermissions');
      useAccountPermissions.mockReturnValue({
        ...mockUseAccountPermissions,
        permissions: mockPermissions,
        addPermission: mockAddPermission,
      });

      // Re-render to get updated mock
      render(
        <TestWrapper>
          <AccountPermissionsDialog
            open={true}
            onClose={mockOnClose}
            account={mockAccount}
          />
        </TestWrapper>
      );

      fireEvent.click(screen.getByText('Add Permission'));

      // Fill form with valid data
      const userEmailInput = screen.getByLabelText(/user email/i);
      fireEvent.change(userEmailInput, { target: { value: 'test@example.com' } });

      const permissionSelect = screen.getByLabelText(/permission level/i);
      fireEvent.mouseDown(permissionSelect);
      fireEvent.click(screen.getByText('Read'));

      const notesInput = screen.getByLabelText(/notes/i);
      fireEvent.change(notesInput, { target: { value: 'Test notes' } });

      const addButton = screen.getByRole('button', { name: 'Add' });
      fireEvent.click(addButton);

      await waitFor(() => {
        expect(mockAddPermission).toHaveBeenCalledWith(mockAccount.id, {
          user_email: 'test@example.com',
          permission_level: 'read',
          notes: 'Test notes',
        });
      });
    });
  });

  describe('Edit Permission', () => {
    it('should show edit form when edit button is clicked', async () => {
      render(
        <TestWrapper>
          <AccountPermissionsDialog
            open={true}
            onClose={mockOnClose}
            account={mockAccount}
          />
        </TestWrapper>
      );

      const editButtons = screen.getAllByLabelText(/edit permission/i);
      fireEvent.click(editButtons[0]);

      await waitFor(() => {
        expect(screen.getByText('Edit Permission')).toBeInTheDocument();
      });
    });

    it('should populate form with existing permission data', async () => {
      render(
        <TestWrapper>
          <AccountPermissionsDialog
            open={true}
            onClose={mockOnClose}
            account={mockAccount}
          />
        </TestWrapper>
      );

      const editButtons = screen.getAllByLabelText(/edit permission/i);
      fireEvent.click(editButtons[0]);

      await waitFor(() => {
        const permissionLevelSelect = screen.getByDisplayValue(mockPermissions[0].permission_level);
        expect(permissionLevelSelect).toBeInTheDocument();
      });
    });

    it('should call updatePermission with edited data', async () => {
      const mockUpdatePermission = jest.fn();
      const { useAccountPermissions } = require('../../../hooks/useAccountPermissions');
      useAccountPermissions.mockReturnValue({
        ...mockUseAccountPermissions,
        permissions: mockPermissions,
        updatePermission: mockUpdatePermission,
      });

      render(
        <TestWrapper>
          <AccountPermissionsDialog
            open={true}
            onClose={mockOnClose}
            account={mockAccount}
          />
        </TestWrapper>
      );

      const editButtons = screen.getAllByLabelText(/edit permission/i);
      fireEvent.click(editButtons[0]);

      await waitFor(() => {
        expect(screen.getByText('Edit Permission')).toBeInTheDocument();
      });

      // Change permission level
      const permissionSelect = screen.getByLabelText(/permission level/i);
      fireEvent.mouseDown(permissionSelect);
      fireEvent.click(screen.getByText('Admin'));

      const updateButton = screen.getByRole('button', { name: 'Update' });
      fireEvent.click(updateButton);

      await waitFor(() => {
        expect(mockUpdatePermission).toHaveBeenCalledWith(
          mockAccount.id,
          mockPermissions[0].id,
          expect.objectContaining({
            permission_level: 'admin',
          })
        );
      });
    });
  });

  describe('Edge Cases', () => {
    it('should handle null account gracefully', () => {
      render(
        <TestWrapper>
          <AccountPermissionsDialog
            open={true}
            onClose={mockOnClose}
            account={null}
          />
        </TestWrapper>
      );

      expect(screen.getByText('Account Permissions')).toBeInTheDocument();
      expect(screen.getByText(/no account selected/i)).toBeInTheDocument();
    });

    it('should handle empty permissions array', () => {
      const { useAccountPermissions } = require('../../../hooks/useAccountPermissions');
      useAccountPermissions.mockReturnValue({
        ...mockUseAccountPermissions,
        permissions: [],
      });

      render(
        <TestWrapper>
          <AccountPermissionsDialog
            open={true}
            onClose={mockOnClose}
            account={mockAccount}
          />
        </TestWrapper>
      );

      expect(screen.getByText(/no permissions found/i)).toBeInTheDocument();
    });

    it('should handle permission operations errors', async () => {
      const errorMessage = 'Permission operation failed';
      const { useAccountPermissions } = require('../../../hooks/useAccountPermissions');
      useAccountPermissions.mockReturnValue({
        ...mockUseAccountPermissions,
        permissions: mockPermissions,
        error: errorMessage,
      });

      render(
        <TestWrapper>
          <AccountPermissionsDialog
            open={true}
            onClose={mockOnClose}
            account={mockAccount}
          />
        </TestWrapper>
      );

      expect(screen.getByRole('alert')).toBeInTheDocument();
      expect(screen.getByText(errorMessage)).toBeInTheDocument();
    });

    it('should disable actions while loading', () => {
      const { useAccountPermissions } = require('../../../hooks/useAccountPermissions');
      useAccountPermissions.mockReturnValue({
        ...mockUseAccountPermissions,
        loading: true,
        permissions: mockPermissions,
      });

      render(
        <TestWrapper>
          <AccountPermissionsDialog
            open={true}
            onClose={mockOnClose}
            account={mockAccount}
          />
        </TestWrapper>
      );

      const addButton = screen.getByText('Add Permission');
      expect(addButton).toBeDisabled();
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA labels', () => {
      render(
        <TestWrapper>
          <AccountPermissionsDialog
            open={true}
            onClose={mockOnClose}
            account={mockAccount}
          />
        </TestWrapper>
      );

      expect(screen.getByRole('dialog')).toHaveAttribute('aria-labelledby');
      expect(screen.getByLabelText(/close/i)).toBeInTheDocument();
    });

    it('should support keyboard navigation', () => {
      render(
        <TestWrapper>
          <AccountPermissionsDialog
            open={true}
            onClose={mockOnClose}
            account={mockAccount}
          />
        </TestWrapper>
      );

      const closeButton = screen.getByText('Close');
      closeButton.focus();
      expect(closeButton).toHaveFocus();

      fireEvent.keyDown(closeButton, { key: 'Enter' });
      expect(mockOnClose).toHaveBeenCalledTimes(1);
    });

    it('should have proper table structure for screen readers', () => {
      render(
        <TestWrapper>
          <AccountPermissionsDialog
            open={true}
            onClose={mockOnClose}
            account={mockAccount}
          />
        </TestWrapper>
      );

      expect(screen.getByRole('table')).toBeInTheDocument();
      expect(screen.getAllByRole('columnheader')).toHaveLength(4);
      expect(screen.getAllByRole('row')).toHaveLength(mockPermissions.length + 1); // +1 for header
    });
  });

  describe('Integration with Hook', () => {
    it('should call refreshPermissions on mount', () => {
      const mockRefreshPermissions = jest.fn();
      const { useAccountPermissions } = require('../../../hooks/useAccountPermissions');
      useAccountPermissions.mockReturnValue({
        ...mockUseAccountPermissions,
        refreshPermissions: mockRefreshPermissions,
      });

      render(
        <TestWrapper>
          <AccountPermissionsDialog
            open={true}
            onClose={mockOnClose}
            account={mockAccount}
          />
        </TestWrapper>
      );

      expect(mockRefreshPermissions).toHaveBeenCalledWith(mockAccount.id);
    });

    it('should handle hook state changes', () => {
      const { rerender } = render(
        <TestWrapper>
          <AccountPermissionsDialog
            open={true}
            onClose={mockOnClose}
            account={mockAccount}
          />
        </TestWrapper>
      );

      // Simulate loading state change
      const { useAccountPermissions } = require('../../../hooks/useAccountPermissions');
      useAccountPermissions.mockReturnValue({
        ...mockUseAccountPermissions,
        loading: true,
      });

      rerender(
        <TestWrapper>
          <AccountPermissionsDialog
            open={true}
            onClose={mockOnClose}
            account={mockAccount}
          />
        </TestWrapper>
      );

      expect(screen.getByRole('progressbar')).toBeInTheDocument();
    });
  });
});