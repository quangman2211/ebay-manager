import { accountsAPI } from './api';
import type { Account } from '../types';

/**
 * Account Synchronization Service - Sprint 7
 * 
 * SOLID Principles Implementation:
 * - Single Responsibility: Only handles account synchronization operations
 * - Open/Closed: Extensible via new sync strategies
 * - Interface Segregation: Focused interface for sync operations
 * - Dependency Inversion: Depends on API abstractions
 */
export class AccountSyncService {
  private syncInterval: NodeJS.Timeout | null = null;
  private readonly SYNC_INTERVAL_MS = 5 * 60 * 1000; // 5 minutes

  /**
   * Start automatic synchronization
   */
  startAutoSync(onSyncUpdate: (accounts: Account[]) => void, onError: (error: string) => void): void {
    // Clear existing interval
    this.stopAutoSync();

    // Start periodic sync
    this.syncInterval = setInterval(async () => {
      try {
        await this.syncAccounts(onSyncUpdate, onError);
      } catch (error) {
        console.error('Auto-sync failed:', error);
        onError(error instanceof Error ? error.message : 'Auto-sync failed');
      }
    }, this.SYNC_INTERVAL_MS);

    // Initial sync
    this.syncAccounts(onSyncUpdate, onError);
  }

  /**
   * Stop automatic synchronization
   */
  stopAutoSync(): void {
    if (this.syncInterval) {
      clearInterval(this.syncInterval);
      this.syncInterval = null;
    }
  }

  /**
   * Manual account synchronization
   */
  async syncAccounts(
    onSyncUpdate: (accounts: Account[]) => void, 
    onError: (error: string) => void
  ): Promise<void> {
    try {
      // Fetch latest accounts from API
      const accounts = await accountsAPI.getAccounts();
      
      // Update last sync timestamp
      const syncTimestamp = new Date().toISOString();
      localStorage.setItem('lastAccountSync', syncTimestamp);
      
      // Notify about successful sync
      onSyncUpdate(accounts);
      
      console.log('Account sync completed successfully');
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to sync accounts';
      onError(errorMessage);
      console.error('Account sync failed:', error);
    }
  }

  /**
   * Sync specific account details
   */
  async syncAccountDetails(accountId: number): Promise<Account | null> {
    try {
      const accountDetails = await accountsAPI.getAccountDetails(accountId);
      return accountDetails;
    } catch (error) {
      console.error('Failed to sync account details:', error);
      return null;
    }
  }

  /**
   * Get last sync timestamp
   */
  getLastSyncTimestamp(): string | null {
    return localStorage.getItem('lastAccountSync');
  }

  /**
   * Check if sync is needed based on time threshold
   */
  isSyncNeeded(thresholdMinutes: number = 10): boolean {
    const lastSync = this.getLastSyncTimestamp();
    if (!lastSync) return true;

    const lastSyncTime = new Date(lastSync).getTime();
    const now = Date.now();
    const timeDifference = now - lastSyncTime;
    const thresholdMs = thresholdMinutes * 60 * 1000;

    return timeDifference > thresholdMs;
  }

  /**
   * Force immediate sync
   */
  async forcSync(
    onSyncUpdate: (accounts: Account[]) => void,
    onError: (error: string) => void
  ): Promise<void> {
    console.log('Forcing account sync...');
    await this.syncAccounts(onSyncUpdate, onError);
  }
}

// Export singleton instance
export const accountSyncService = new AccountSyncService();