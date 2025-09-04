import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { server } from '../../../../mocks/server';
import { rest } from 'msw';
import { AllProviders } from '../../../../utils/test-utils';
import AccountForm from '../AccountForm';
import { createMockAccount } from '../../../../utils/mockData';
import { CONNECTION_STATUSES, PLATFORMS } from '../../../../config/accountConstants';

/**
 * Account Form Integration Tests - Sprint 7
 * 
 * Tests the integration between:
 * - Form validation and submission
 * - API communication
 * - User interactions
 * - Error handling and feedback
 * 
 * Following SOLID Principles:
 * - Single Responsibility: Each test validates one form integration scenario
 * - Interface Segregation: Tests form interfaces without implementation details
 * - Dependency Inversion: Tests form abstractions via mocking
 */

// Setup MSW server
beforeAll(() => server.listen());
afterEach(() => {
  server.resetHandlers();
  jest.clearAllMocks();
});
afterAll(() => server.close());

describe('Account Form - Integration Tests', () => {
  let mockOnSubmit: jest.Mock;
  let mockOnCancel: jest.Mock;

  beforeEach(() => {
    mockOnSubmit = jest.fn();
    mockOnCancel = jest.fn();
  });

  describe('Form Submission Integration', () => {
    it('should submit valid form data to API', async () => {
      const user = userEvent.setup();

      // Mock successful API response
      server.use(
        rest.post('/api/accounts', (req, res, ctx) => {
          return res(
            ctx.status(201),
            ctx.json(createMockAccount({ id: 123, name: 'New Test Account' }))
          );
        })
      );

      render(
        <AllProviders>
          <AccountForm
            open={true}
            onSubmit={mockOnSubmit}
            onCancel={mockOnCancel}
            mode="create"
          />
        </AllProviders>
      );

      // Fill in form fields
      await user.type(screen.getByLabelText(/account name/i), 'New Test Account');
      await user.type(screen.getByLabelText(/ebay username/i), 'newtestaccount');
      await user.selectOptions(screen.getByLabelText(/account type/i), PLATFORMS.EBAY);

      // Submit form
      fireEvent.click(screen.getByRole('button', { name: /create account/i }));

      // Wait for API call and form submission
      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith(
          expect.objectContaining({
            name: 'New Test Account',
            ebay_username: 'newtestaccount',
            account_type: PLATFORMS.EBAY,
          })
        );
      });
    });

    it('should handle API errors during submission', async () => {
      const user = userEvent.setup();

      // Mock API error
      server.use(
        rest.post('/api/accounts', (req, res, ctx) => {
          return res(
            ctx.status(400),
            ctx.json({ error: 'Username already exists' })
          );
        })
      );

      render(
        <AllProviders>
          <AccountForm
            open={true}
            onSubmit={mockOnSubmit}
            onCancel={mockOnCancel}
            mode="create"
          />
        </AllProviders>
      );

      // Fill and submit form
      await user.type(screen.getByLabelText(/account name/i), 'Duplicate Account');
      await user.type(screen.getByLabelText(/ebay username/i), 'existinguser');
      await user.selectOptions(screen.getByLabelText(/account type/i), PLATFORMS.EBAY);

      fireEvent.click(screen.getByRole('button', { name: /create account/i }));

      // Should show error message
      await waitFor(() => {
        expect(screen.getByText(/username already exists/i)).toBeInTheDocument();
      });

      // Should not call onSubmit callback
      expect(mockOnSubmit).not.toHaveBeenCalled();
    });

    it('should update existing account via API', async () => {
      const user = userEvent.setup();
      const existingAccount = createMockAccount({
        id: 1,
        name: 'Existing Account',
        ebay_username: 'existing',
        account_type: 'business',
      });

      // Mock successful update
      server.use(
        rest.put('/api/accounts/1', (req, res, ctx) => {
          return res(
            ctx.status(200),
            ctx.json({ ...existingAccount, name: 'Updated Account' })
          );
        })
      );

      render(
        <AllProviders>
          <AccountForm
            open={true}
            onSubmit={mockOnSubmit}
            onCancel={mockOnCancel}
            mode="edit"
            account={existingAccount}
          />
        </AllProviders>
      );

      // Form should be pre-filled
      expect(screen.getByDisplayValue('Existing Account')).toBeInTheDocument();
      expect(screen.getByDisplayValue('existing')).toBeInTheDocument();

      // Update account name
      const nameInput = screen.getByLabelText(/account name/i);
      await user.clear(nameInput);
      await user.type(nameInput, 'Updated Account');

      // Submit form
      fireEvent.click(screen.getByRole('button', { name: /update account/i }));

      // Should call onSubmit with updated data
      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith(
          expect.objectContaining({
            name: 'Updated Account',
            ebay_username: 'existing',
            account_type: PLATFORMS.EBAY,
          })
        );
      });
    });
  });

  describe('Form Validation Integration', () => {
    it('should validate required fields before submission', async () => {
      const user = userEvent.setup();

      render(
        <AllProviders>
          <AccountForm
            open={true}
            onSubmit={mockOnSubmit}
            onCancel={mockOnCancel}
            mode="create"
          />
        </AllProviders>
      );

      // Try to submit without filling required fields
      fireEvent.click(screen.getByRole('button', { name: /create account/i }));

      // Should show validation errors
      await waitFor(() => {
        expect(screen.getByText(/account name is required/i)).toBeInTheDocument();
        expect(screen.getByText(/ebay username is required/i)).toBeInTheDocument();
      });

      // Should not submit
      expect(mockOnSubmit).not.toHaveBeenCalled();
    });

    it('should validate username format', async () => {
      const user = userEvent.setup();

      render(
        <AllProviders>
          <AccountForm
            open={true}
            onSubmit={mockOnSubmit}
            onCancel={mockOnCancel}
            mode="create"
          />
        </AllProviders>
      );

      // Fill with invalid username
      await user.type(screen.getByLabelText(/account name/i), 'Valid Name');
      await user.type(screen.getByLabelText(/ebay username/i), 'invalid username!@#');

      // Submit form
      fireEvent.click(screen.getByRole('button', { name: /create account/i }));

      // Should show username validation error
      await waitFor(() => {
        expect(screen.getByText(/invalid username format/i)).toBeInTheDocument();
      });

      expect(mockOnSubmit).not.toHaveBeenCalled();
    });

    it('should validate username uniqueness via API', async () => {
      const user = userEvent.setup();

      // Mock API call to check username availability
      server.use(
        rest.get('/api/accounts/check-username', (req, res, ctx) => {
          const username = req.url.searchParams.get('username');
          if (username === 'taken') {
            return res(ctx.status(200), ctx.json({ available: false }));
          }
          return res(ctx.status(200), ctx.json({ available: true }));
        })
      );

      render(
        <AllProviders>
          <AccountForm
            open={true}
            onSubmit={mockOnSubmit}
            onCancel={mockOnCancel}
            mode="create"
          />
        </AllProviders>
      );

      // Fill with taken username
      await user.type(screen.getByLabelText(/ebay username/i), 'taken');
      
      // Trigger validation (blur event)
      fireEvent.blur(screen.getByLabelText(/ebay username/i));

      // Should show availability error
      await waitFor(() => {
        expect(screen.getByText(/username is already taken/i)).toBeInTheDocument();
      });
    });
  });

  describe('User Interaction Integration', () => {
    it('should handle form cancellation', async () => {
      render(
        <AllProviders>
          <AccountForm
            open={true}
            onSubmit={mockOnSubmit}
            onCancel={mockOnCancel}
            mode="create"
          />
        </AllProviders>
      );

      // Click cancel button
      fireEvent.click(screen.getByRole('button', { name: /cancel/i }));

      // Should call onCancel
      expect(mockOnCancel).toHaveBeenCalledTimes(1);
    });

    it('should handle form reset', async () => {
      const user = userEvent.setup();

      render(
        <AllProviders>
          <AccountForm
            open={true}
            onSubmit={mockOnSubmit}
            onCancel={mockOnCancel}
            mode="create"
          />
        </AllProviders>
      );

      // Fill form
      await user.type(screen.getByLabelText(/account name/i), 'Test Name');
      await user.type(screen.getByLabelText(/ebay username/i), 'testuser');

      // Reset form
      fireEvent.click(screen.getByRole('button', { name: /reset/i }));

      // Form should be cleared
      expect(screen.getByLabelText(/account name/i)).toHaveValue('');
      expect(screen.getByLabelText(/ebay username/i)).toHaveValue('');
    });

    it('should handle keyboard navigation', async () => {
      const user = userEvent.setup();

      render(
        <AllProviders>
          <AccountForm
            open={true}
            onSubmit={mockOnSubmit}
            onCancel={mockOnCancel}
            mode="create"
          />
        </AllProviders>
      );

      // Tab through form fields
      await user.tab();
      expect(screen.getByLabelText(/account name/i)).toHaveFocus();

      await user.tab();
      expect(screen.getByLabelText(/ebay username/i)).toHaveFocus();

      await user.tab();
      expect(screen.getByLabelText(/account type/i)).toHaveFocus();
    });
  });

  describe('Loading States Integration', () => {
    it('should show loading state during submission', async () => {
      const user = userEvent.setup();

      // Mock slow API response
      server.use(
        rest.post('/api/accounts', (req, res, ctx) => {
          return res(
            ctx.delay(1000), // 1 second delay
            ctx.status(201),
            ctx.json(createMockAccount({ id: 123 }))
          );
        })
      );

      render(
        <AllProviders>
          <AccountForm
            open={true}
            onSubmit={mockOnSubmit}
            onCancel={mockOnCancel}
            mode="create"
          />
        </AllProviders>
      );

      // Fill and submit form
      await user.type(screen.getByLabelText(/account name/i), 'Test Account');
      await user.type(screen.getByLabelText(/ebay username/i), 'testaccount');
      
      fireEvent.click(screen.getByRole('button', { name: /create account/i }));

      // Should show loading indicator
      expect(screen.getByRole('progressbar')).toBeInTheDocument();

      // Submit button should be disabled
      expect(screen.getByRole('button', { name: /creating/i })).toBeDisabled();

      // Wait for completion
      await waitFor(() => {
        expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
      });
    });

    it('should handle timeout during submission', async () => {
      const user = userEvent.setup();

      // Mock timeout
      server.use(
        rest.post('/api/accounts', (req, res, ctx) => {
          return res(ctx.delay('infinite'));
        })
      );

      render(
        <AllProviders>
          <AccountForm
            open={true}
            onSubmit={mockOnSubmit}
            onCancel={mockOnCancel}
            mode="create"
            timeout={1000} // 1 second timeout
          />
        </AllProviders>
      );

      // Fill and submit form
      await user.type(screen.getByLabelText(/account name/i), 'Test Account');
      await user.type(screen.getByLabelText(/ebay username/i), 'testaccount');
      
      fireEvent.click(screen.getByRole('button', { name: /create account/i }));

      // Should eventually show timeout error
      await waitFor(
        () => {
          expect(screen.getByText(/request timeout/i)).toBeInTheDocument();
        },
        { timeout: 2000 }
      );
    });
  });

  describe('Accessibility Integration', () => {
    it('should announce validation errors to screen readers', async () => {
      const user = userEvent.setup();

      render(
        <AllProviders>
          <AccountForm
            open={true}
            onSubmit={mockOnSubmit}
            onCancel={mockOnCancel}
            mode="create"
          />
        </AllProviders>
      );

      // Submit invalid form
      fireEvent.click(screen.getByRole('button', { name: /create account/i }));

      // Error should have proper ARIA attributes
      await waitFor(() => {
        const errorElement = screen.getByText(/account name is required/i);
        expect(errorElement).toHaveAttribute('role', 'alert');
      });
    });

    it('should associate error messages with form fields', async () => {
      render(
        <AllProviders>
          <AccountForm
            open={true}
            onSubmit={mockOnSubmit}
            onCancel={mockOnCancel}
            mode="create"
          />
        </AllProviders>
      );

      // Submit to trigger validation
      fireEvent.click(screen.getByRole('button', { name: /create account/i }));

      await waitFor(() => {
        const nameInput = screen.getByLabelText(/account name/i);
        const errorId = nameInput.getAttribute('aria-describedby');
        expect(errorId).toBeTruthy();
        expect(screen.getByText(/account name is required/i)).toHaveAttribute('id', errorId);
      });
    });
  });
});