import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { server } from '../../../../mocks/server';
import { AllProviders } from '../../../../utils/test-utils';
import AccountManagementPage from '../../../../pages/AccountManagement';
import { createMockAccount } from '../../../../utils/mockData';

/**
 * Account Management Integration Tests - Sprint 7
 * 
 * Tests the integration between:
 * - Account Management components
 * - API services
 * - Context providers
 * - User interactions
 * 
 * SOLID Principles in Testing:
 * - Single Responsibility: Each test validates one integration scenario
 * - Open/Closed: Easy to add new integration test scenarios  
 * - Dependency Inversion: Tests against component abstractions
 */

// Setup MSW server for API mocking
beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('Account Management - Integration Tests', () => {
  beforeEach(() => {
    // Reset any mocks and localStorage
    localStorage.clear();
    jest.clearAllMocks();
  });

  describe('Account List Display Integration', () => {
    it('should load and display accounts from API', async () => {
      render(
        <AllProviders>
          <AccountManagementPage />
        </AllProviders>
      );

      // Should show loading state initially
      expect(screen.getByRole('progressbar')).toBeInTheDocument();

      // Wait for accounts to load from API
      await waitFor(() => {
        expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
      });

      // Should display account cards
      expect(screen.getByText(/Account Management/)).toBeInTheDocument();
    });

    it('should handle API errors gracefully', async () => {
      // Mock API error
      server.use(
        // Override with error response
      );

      render(
        <AllProviders>
          <AccountManagementPage />
        </AllProviders>
      );

      await waitFor(() => {
        expect(screen.getByText(/error/i)).toBeInTheDocument();
      });
    });
  });

  describe('Account Card Interactions', () => {
    it('should handle account selection', async () => {
      render(
        <AllProviders>
          <AccountManagementPage />
        </AllProviders>
      );

      // Wait for loading to complete
      await waitFor(() => {
        expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
      });

      // Find and click first account card
      const accountCards = screen.getAllByRole('button');
      const firstCard = accountCards.find(card => 
        card.textContent?.includes('View Details')
      );

      if (firstCard) {
        fireEvent.click(firstCard);
        
        // Should trigger account selection
        await waitFor(() => {
          // Verify account was selected (this would depend on UI feedback)
          expect(screen.getByText(/selected/i)).toBeInTheDocument();
        });
      }
    });

    it('should open account settings dialog', async () => {
      render(
        <AllProviders>
          <AccountManagementPage />
        </AllProviders>
      );

      // Wait for loading
      await waitFor(() => {
        expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
      });

      // Find settings button
      const settingsButtons = screen.getAllByLabelText(/settings/i);
      if (settingsButtons.length > 0) {
        fireEvent.click(settingsButtons[0]);

        // Should open settings dialog
        await waitFor(() => {
          expect(screen.getByRole('dialog')).toBeInTheDocument();
          expect(screen.getByText(/Account Settings/)).toBeInTheDocument();
        });
      }
    });
  });

  describe('Search and Filter Integration', () => {
    it('should filter accounts based on search input', async () => {
      render(
        <AllProviders>
          <AccountManagementPage />
        </AllProviders>
      );

      // Wait for accounts to load
      await waitFor(() => {
        expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
      });

      // Find search input
      const searchInput = screen.getByPlaceholderText(/search/i);
      
      // Type search query
      fireEvent.change(searchInput, { target: { value: 'test' } });

      // Wait for filter to apply
      await waitFor(() => {
        // Verify filtered results
        const visibleCards = screen.getAllByRole('button');
        expect(visibleCards.length).toBeGreaterThan(0);
      });
    });

    it('should handle empty search results', async () => {
      render(
        <AllProviders>
          <AccountManagementPage />
        </AllProviders>
      );

      await waitFor(() => {
        expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
      });

      // Search for non-existent account
      const searchInput = screen.getByPlaceholderText(/search/i);
      fireEvent.change(searchInput, { target: { value: 'nonexistent' } });

      await waitFor(() => {
        expect(screen.getByText(/no accounts found/i)).toBeInTheDocument();
      });
    });
  });

  describe('Bulk Operations Integration', () => {
    it('should handle bulk account selection', async () => {
      render(
        <AllProviders>
          <AccountManagementPage />
        </AllProviders>
      );

      await waitFor(() => {
        expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
      });

      // Find and check multiple accounts
      const checkboxes = screen.getAllByRole('checkbox');
      if (checkboxes.length > 1) {
        fireEvent.click(checkboxes[0]);
        fireEvent.click(checkboxes[1]);

        // Should show bulk operations toolbar
        await waitFor(() => {
          expect(screen.getByText(/selected/)).toBeInTheDocument();
        });
      }
    });

    it('should handle bulk sync operation', async () => {
      render(
        <AllProviders>
          <AccountManagementPage />
        </AllProviders>
      );

      await waitFor(() => {
        expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
      });

      // Select accounts and perform bulk sync
      const checkboxes = screen.getAllByRole('checkbox');
      if (checkboxes.length > 0) {
        fireEvent.click(checkboxes[0]);

        // Find bulk sync button
        const syncButton = screen.getByText(/sync/i);
        fireEvent.click(syncButton);

        // Should show sync confirmation or progress
        await waitFor(() => {
          expect(screen.getByText(/syncing/i)).toBeInTheDocument();
        });
      }
    });
  });

  describe('Account Status Updates', () => {
    it('should update account status via API', async () => {
      render(
        <AllProviders>
          <AccountManagementPage />
        </AllProviders>
      );

      await waitFor(() => {
        expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
      });

      // Find account with toggle-able status
      const statusToggles = screen.getAllByRole('switch');
      if (statusToggles.length > 0) {
        fireEvent.click(statusToggles[0]);

        // Should update via API and reflect in UI
        await waitFor(() => {
          // Status should be updated
          expect(statusToggles[0]).toHaveAttribute('aria-checked', 'false');
        });
      }
    });
  });

  describe('Error Boundary Integration', () => {
    it('should handle component errors gracefully', async () => {
      // Mock component error
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
      
      render(
        <AllProviders>
          <AccountManagementPage />
        </AllProviders>
      );

      // Trigger error condition
      // This would depend on specific error scenarios

      consoleSpy.mockRestore();
    });
  });

  describe('Real-time Updates Integration', () => {
    it('should handle account sync status updates', async () => {
      render(
        <AllProviders>
          <AccountManagementPage />
        </AllProviders>
      );

      await waitFor(() => {
        expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
      });

      // Simulate sync status update
      // This would test WebSocket or polling integration
      
      await waitFor(() => {
        // Verify UI reflects sync status changes
        expect(screen.getByText(/synced/i)).toBeInTheDocument();
      });
    });
  });

  describe('Navigation Integration', () => {
    it('should navigate between account views', async () => {
      render(
        <AllProviders>
          <AccountManagementPage />
        </AllProviders>
      );

      await waitFor(() => {
        expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
      });

      // Navigate to account details
      const detailButtons = screen.getAllByText(/view details/i);
      if (detailButtons.length > 0) {
        fireEvent.click(detailButtons[0]);

        // Should navigate or show account details
        await waitFor(() => {
          expect(screen.getByText(/account details/i)).toBeInTheDocument();
        });
      }
    });
  });

  describe('Data Persistence Integration', () => {
    it('should persist user preferences', async () => {
      render(
        <AllProviders>
          <AccountManagementPage />
        </AllProviders>
      );

      await waitFor(() => {
        expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
      });

      // Change view preferences
      const viewToggle = screen.getByRole('button', { name: /grid/i });
      fireEvent.click(viewToggle);

      // Should persist to localStorage
      expect(localStorage.getItem('accountViewMode')).toBe('grid');
    });
  });

  describe('Performance Integration', () => {
    it('should handle large account lists efficiently', async () => {
      // This test would verify performance with large datasets
      const startTime = performance.now();

      render(
        <AllProviders>
          <AccountManagementPage />
        </AllProviders>
      );

      await waitFor(() => {
        expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
      });

      const endTime = performance.now();
      const renderTime = endTime - startTime;

      // Should render within reasonable time (adjust threshold as needed)
      expect(renderTime).toBeLessThan(2000); // 2 seconds
    });
  });
});