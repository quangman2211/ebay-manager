import { useState, useCallback, useEffect } from 'react';
import { permissionsAPI, usersAPI } from '../services/api';
import type { 
  User,
  UserAccountPermission, 
  UserAccountPermissionCreate, 
  BulkPermissionRequest, 
  BulkPermissionResponse 
} from '../types';

interface UseAccountPermissionsReturn {
  permissions: UserAccountPermission[];
  availableUsers: User[];
  loading: boolean;
  error: string | null;
  fetchPermissions: () => Promise<void>;
  createPermission: (accountId: number, permission: UserAccountPermissionCreate) => Promise<UserAccountPermission>;
  updatePermission: (accountId: number, permissionId: number, updates: Partial<UserAccountPermissionCreate>) => Promise<UserAccountPermission>;
  deletePermission: (accountId: number, permissionId: number) => Promise<void>;
  clearError: () => void;
}

/**
 * Custom hook for account permissions management
 * Follows Interface Segregation Principle - focused only on permission operations
 */
export const useAccountPermissions = (accountId?: number): UseAccountPermissionsReturn => {
  const [permissions, setPermissions] = useState<UserAccountPermission[]>([]);
  const [availableUsers, setAvailableUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load available users on mount
  useEffect(() => {
    const loadUsers = async () => {
      try {
        const users = await usersAPI.getAllUsers();
        setAvailableUsers(users);
      } catch (err) {
        console.error('Failed to load users:', err);
      }
    };
    loadUsers();
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const fetchPermissions = useCallback(async (): Promise<void> => {
    if (!accountId) return;
    
    try {
      setLoading(true);
      setError(null);
      const accountPermissions = await permissionsAPI.getAccountPermissions(accountId);
      setPermissions(accountPermissions);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to get account permissions';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [accountId]);

  const createPermission = useCallback(async (
    accountId: number, 
    permission: UserAccountPermissionCreate
  ): Promise<UserAccountPermission> => {
    try {
      setLoading(true);
      setError(null);
      const newPermission = await permissionsAPI.createUserPermission(accountId, permission);
      setPermissions(prev => [...prev, newPermission]);
      return newPermission;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create permission';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  const updatePermission = useCallback(async (
    accountId: number, 
    permissionId: number, 
    updates: Partial<UserAccountPermissionCreate>
  ): Promise<UserAccountPermission> => {
    try {
      setLoading(true);
      setError(null);
      const updatedPermission = await permissionsAPI.updateUserPermission(accountId, permissionId, updates);
      setPermissions(prev => prev.map(p => p.id === permissionId ? updatedPermission : p));
      return updatedPermission;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update permission';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  const deletePermission = useCallback(async (
    accountId: number, 
    permissionId: number
  ): Promise<void> => {
    try {
      setLoading(true);
      setError(null);
      await permissionsAPI.deleteUserPermission(accountId, permissionId);
      setPermissions(prev => prev.filter(p => p.id !== permissionId));
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete permission';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    permissions,
    availableUsers,
    loading,
    error,
    fetchPermissions,
    createPermission,
    updatePermission,
    deletePermission,
    clearError,
  };
};