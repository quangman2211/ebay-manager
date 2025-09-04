import React, { useState, useEffect, useCallback } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  Divider,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Chip,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  CircularProgress,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Person as PersonIcon,
  Close as CloseIcon,
} from '@mui/icons-material';
import { SelectChangeEvent } from '@mui/material/Select';

import { useAccountPermissions } from '../../hooks/useAccountPermissions';
import { Account, UserAccountPermission, PermissionLevel } from '../../types';
import { colors, spacing } from '../../styles';

/**
 * Account Permissions Dialog Props - Interface Segregation Principle
 */
interface AccountPermissionsDialogProps {
  open: boolean;
  onClose: () => void;
  account: Account | null;
}

/**
 * Permission Form Interface - Single Responsibility
 */
interface PermissionFormData {
  user_id: number;
  permission_level: PermissionLevel;
  notes?: string;
}

/**
 * Account Permissions Management Dialog - Sprint 7
 * 
 * SOLID Principles Implementation:
 * - Single Responsibility: Only manages account permissions UI
 * - Open/Closed: Extensible via props, closed for modification
 * - Liskov Substitution: Can be used as any Dialog component
 * - Interface Segregation: Focused props and internal interfaces
 * - Dependency Inversion: Depends on permission abstractions via hooks
 */
const AccountPermissionsDialog: React.FC<AccountPermissionsDialogProps> = ({
  open,
  onClose,
  account,
}) => {
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingPermission, setEditingPermission] = useState<UserAccountPermission | null>(null);
  const [formData, setFormData] = useState<PermissionFormData>({
    user_id: 0,
    permission_level: 'viewer',
    notes: '',
  });

  // Permission management hook - Dependency Injection
  const {
    permissions,
    availableUsers,
    loading,
    error,
    fetchPermissions,
    createPermission,
    updatePermission,
    deletePermission,
    clearError,
  } = useAccountPermissions(account?.id);

  // Load permissions when account changes
  useEffect(() => {
    if (open && account) {
      fetchPermissions();
    }
  }, [open, account, fetchPermissions]);

  // Reset form when dialog opens/closes
  useEffect(() => {
    if (!open) {
      setShowAddForm(false);
      setEditingPermission(null);
      resetForm();
    }
  }, [open]);

  const resetForm = useCallback(() => {
    setFormData({
      user_id: 0,
      permission_level: 'viewer',
      notes: '',
    });
  }, []);

  const handleAddPermission = useCallback(() => {
    setEditingPermission(null);
    setShowAddForm(true);
    resetForm();
  }, [resetForm]);

  const handleEditPermission = useCallback((permission: UserAccountPermission) => {
    setEditingPermission(permission);
    setFormData({
      user_id: permission.user_id,
      permission_level: permission.permission_level,
      notes: permission.notes || '',
    });
    setShowAddForm(true);
  }, []);

  const handleDeletePermission = useCallback(async (permissionId: number) => {
    if (!account || !window.confirm('Are you sure you want to remove this permission?')) {
      return;
    }

    try {
      await deletePermission(account.id, permissionId);
      await fetchPermissions(); // Refresh the list
    } catch (error) {
      console.error('Failed to delete permission:', error);
    }
  }, [account, deletePermission, fetchPermissions]);

  const handleFormSubmit = useCallback(async () => {
    if (!account || formData.user_id === 0) {
      return;
    }

    try {
      if (editingPermission) {
        // Update existing permission
        await updatePermission(account.id, editingPermission.id, {
          permission_level: formData.permission_level,
          notes: formData.notes,
        });
      } else {
        // Create new permission
        await createPermission(account.id, {
          user_id: formData.user_id,
          permission_level: formData.permission_level,
          notes: formData.notes,
        });
      }

      setShowAddForm(false);
      setEditingPermission(null);
      resetForm();
      await fetchPermissions(); // Refresh the list
    } catch (error) {
      console.error('Failed to save permission:', error);
    }
  }, [account, formData, editingPermission, updatePermission, createPermission, fetchPermissions, resetForm]);

  const handleFormCancel = useCallback(() => {
    setShowAddForm(false);
    setEditingPermission(null);
    resetForm();
  }, [resetForm]);

  const handleUserChange = useCallback((event: SelectChangeEvent<number>) => {
    setFormData(prev => ({ ...prev, user_id: event.target.value as number }));
  }, []);

  const handlePermissionLevelChange = useCallback((event: SelectChangeEvent<PermissionLevel>) => {
    setFormData(prev => ({ ...prev, permission_level: event.target.value as PermissionLevel }));
  }, []);

  const handleNotesChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({ ...prev, notes: event.target.value }));
  }, []);

  const getPermissionLevelColor = useCallback((level: PermissionLevel) => {
    switch (level) {
      case 'admin':
        return 'error';
      case 'manager':
        return 'warning';
      case 'editor':
        return 'info';
      case 'viewer':
        return 'success';
      default:
        return 'default';
    }
  }, []);

  const getPermissionLevelLabel = useCallback((level: PermissionLevel) => {
    switch (level) {
      case 'admin':
        return 'Administrator';
      case 'manager':
        return 'Manager';
      case 'editor':
        return 'Editor';
      case 'viewer':
        return 'Viewer';
      default:
        return level;
    }
  }, []);

  // Get user name by ID
  const getUserName = useCallback((userId: number) => {
    const user = availableUsers.find(u => u.id === userId);
    return user ? user.username : `User #${userId}`;
  }, [availableUsers]);

  if (!account) {
    return null;
  }

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: {
          borderRadius: spacing.xl,
          boxShadow: '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 10px 10px -5px rgb(0 0 0 / 0.04)',
        },
      }}
    >
      <DialogTitle sx={{ pb: spacing.sm }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <PersonIcon sx={{ mr: spacing.md, color: colors.primary[500] }} />
            <Box>
              <Typography variant="h6" fontWeight={600}>
                Manage Permissions
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {account.name}
              </Typography>
            </Box>
          </Box>
          <IconButton onClick={onClose} sx={{ color: colors.textSecondary }}>
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>

      <Divider />

      <DialogContent sx={{ px: 3, py: spacing.lg }}>
        {/* Error Display */}
        {error && (
          <Alert 
            severity="error" 
            sx={{ mb: spacing.lg }} 
            onClose={clearError}
          >
            {error}
          </Alert>
        )}

        {/* Add Permission Form */}
        {showAddForm && (
          <Paper
            sx={{
              p: spacing.lg,
              mb: spacing.lg,
              border: `1px solid ${colors.primary[200]}`,
              backgroundColor: colors.primary[50],
            }}
          >
            <Typography variant="subtitle1" fontWeight={600} sx={{ mb: spacing.lg }}>
              {editingPermission ? 'Edit Permission' : 'Add New Permission'}
            </Typography>

            <Box sx={{ display: 'flex', gap: spacing.lg, mb: spacing.lg }}>
              <FormControl fullWidth>
                <InputLabel>User</InputLabel>
                <Select
                  value={formData.user_id}
                  onChange={handleUserChange}
                  label="User"
                  disabled={!!editingPermission} // Can't change user when editing
                >
                  <MenuItem value={0} disabled>Select a user</MenuItem>
                  {availableUsers
                    .filter(user => !editingPermission || user.id === editingPermission.user_id)
                    .map((user) => (
                      <MenuItem key={user.id} value={user.id}>
                        {user.username} ({user.email})
                      </MenuItem>
                    ))}
                </Select>
              </FormControl>

              <FormControl fullWidth>
                <InputLabel>Permission Level</InputLabel>
                <Select
                  value={formData.permission_level}
                  onChange={handlePermissionLevelChange}
                  label="Permission Level"
                >
                  <MenuItem value="viewer">Viewer</MenuItem>
                  <MenuItem value="editor">Editor</MenuItem>
                  <MenuItem value="manager">Manager</MenuItem>
                  <MenuItem value="admin">Administrator</MenuItem>
                </Select>
              </FormControl>
            </Box>

            <TextField
              fullWidth
              label="Notes (Optional)"
              value={formData.notes}
              onChange={handleNotesChange}
              multiline
              rows={2}
              sx={{ mb: spacing.lg }}
            />

            <Box sx={{ display: 'flex', gap: spacing.md, justifyContent: 'flex-end' }}>
              <Button variant="outlined" onClick={handleFormCancel}>
                Cancel
              </Button>
              <Button
                variant="contained"
                onClick={handleFormSubmit}
                disabled={formData.user_id === 0 || loading}
              >
                {loading ? <CircularProgress size={16} /> : (editingPermission ? 'Update' : 'Add')}
              </Button>
            </Box>
          </Paper>
        )}

        {/* Permissions Table */}
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: spacing.lg }}>
          <Typography variant="h6" fontWeight={600}>
            Current Permissions ({permissions.length})
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleAddPermission}
            disabled={loading}
          >
            Add Permission
          </Button>
        </Box>

        {loading && !showAddForm ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: spacing.xxl }}>
            <CircularProgress />
          </Box>
        ) : permissions.length === 0 ? (
          <Paper
            sx={{
              p: spacing.xxl,
              textAlign: 'center',
              backgroundColor: colors.bgSecondary,
              border: `1px dashed ${colors.borderMedium}`,
            }}
          >
            <PersonIcon sx={{ fontSize: 48, color: colors.textSecondary, mb: spacing.md }} />
            <Typography variant="h6" color="text.secondary" gutterBottom>
              No permissions assigned
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: spacing.lg }}>
              Add permissions to control who can access this account
            </Typography>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={handleAddPermission}
            >
              Add First Permission
            </Button>
          </Paper>
        ) : (
          <TableContainer component={Paper} sx={{ boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.1)' }}>
            <Table>
              <TableHead>
                <TableRow sx={{ backgroundColor: colors.bgSecondary }}>
                  <TableCell sx={{ fontWeight: 600 }}>User</TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>Permission Level</TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>Granted</TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>Status</TableCell>
                  <TableCell sx={{ fontWeight: 600 }} align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {permissions.map((permission) => (
                  <TableRow
                    key={permission.id}
                    sx={{
                      '&:hover': { backgroundColor: colors.bgHover },
                      opacity: permission.is_active ? 1 : 0.6,
                    }}
                  >
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <PersonIcon sx={{ mr: spacing.sm, color: colors.textSecondary }} />
                        <Box>
                          <Typography variant="body2" fontWeight={500}>
                            {getUserName(permission.user_id)}
                          </Typography>
                          {permission.notes && (
                            <Typography variant="caption" color="text.secondary">
                              {permission.notes}
                            </Typography>
                          )}
                        </Box>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={getPermissionLevelLabel(permission.permission_level)}
                        color={getPermissionLevelColor(permission.permission_level) as any}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" color="text.secondary">
                        {new Date(permission.granted_at).toLocaleDateString()}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={permission.is_active ? 'Active' : 'Inactive'}
                        color={permission.is_active ? 'success' : 'error'}
                        size="small"
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell align="right">
                      <IconButton
                        size="small"
                        onClick={() => handleEditPermission(permission)}
                        sx={{ mr: spacing.sm }}
                      >
                        <EditIcon fontSize="small" />
                      </IconButton>
                      <IconButton
                        size="small"
                        onClick={() => handleDeletePermission(permission.id)}
                        color="error"
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </DialogContent>

      <Divider />

      <DialogActions sx={{ px: 3, py: spacing.lg }}>
        <Button variant="outlined" onClick={onClose}>
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default AccountPermissionsDialog;